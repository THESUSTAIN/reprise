"""
Complexity Detection Routes
Automatically analyzes user messages to suggest the appropriate model.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
import re

from deps import get_current_user
from models import User
from utils import load_admin_config  # cache intégré dans utils — pas de I/O bloquant par requête

complexity_router = APIRouter(prefix="/complexity", tags=["Complexity"])

# Default complexity rules (can be overridden via admin_config.json)
DEFAULT_COMPLEXITY_RULES = {
    "simple": {
        "max_words": 80,
        "max_exchanges": 5,
        "keywords": ["traduis", "translate", "résume", "resume", "summarize", "corrige", "correct", "réponds", "answer", "explique simplement", "explain simply"],
        "no_files": True,
        "recommended_model": "fast",
        "credits": 2
    },
    "medium": {
        "min_words": 80,
        "max_words": 300,
        "max_file_pages": 10,
        "keywords": ["analyse", "analyze", "rédige", "redige", "write", "draft", "structure", "code", "script", "python", "javascript", "document", "proposition", "contrat", "contract"],
        "recommended_model": "pro",
        "credits": 4
    },
    "complex": {
        "min_words": 300,
        "min_file_pages": 10,
        "keywords": ["business plan", "audit", "rapport complet", "complete report", "full analysis", "analyse financière", "financial analysis", "plusieurs fichiers", "multiple files"],
        "recommended_model": "pro",
        "credits": 4,
        "suggest_upgrade": True
    },
    "agent": {
        "keywords": ["va sur", "go to", "cherche et compile", "search and compile", "automatiquement", "automatically", "en autonomie", "autonomously", "veille", "monitoring", "compare les prix", "compare prices", "plusieurs sites", "multiple sites", "urls"],
        "multi_step": True,
        "recommended_model": "agent",
        "credits_range": [60, 600]
    }
}


class ComplexityAnalysisRequest(BaseModel):
    message: str
    file_count: int = 0
    file_pages: int = 0
    exchange_count: int = 0
    current_model: Optional[str] = None


class ComplexityAnalysisResponse(BaseModel):
    level: str  # simple, medium, complex, agent
    detected_keywords: List[str]
    word_count: int
    recommended_model: str
    recommended_credits: int
    current_model_ok: bool
    suggestion: Optional[str] = None
    upgrade_hint: bool = False


def get_complexity_rules() -> dict:
    """Get complexity rules from admin config or use defaults."""
    config = load_admin_config()
    return config.get("complexity_rules", DEFAULT_COMPLEXITY_RULES)


def analyze_complexity(
    message: str,
    file_count: int = 0,
    file_pages: int = 0,
    exchange_count: int = 0,
    current_model: str = None
) -> ComplexityAnalysisResponse:
    """
    Analyze message complexity and return recommendation.
    
    Level 1 — Simple (Claude Fast recommandé, 2 crédits/message)
    - Message court (moins de 80 mots)
    - Verbes simples : traduis, résume, corrige
    - Pas de fichier joint
    - Moins de 5 échanges dans la conversation
    
    Level 2 — Moyen (Claude Pro recommandé, 4 crédits/message)
    - Message entre 80 et 300 mots
    - Mots-clés : analyse, rédige, structure, code
    - Fichier joint de moins de 10 pages
    - Demande de contenu structuré
    
    Level 3 — Complexe (Suggestion de passer à Claude Pro si sur Claude Fast)
    - Message de plus de 300 mots
    - Fichier de plus de 10 pages
    - Mots-clés : business plan, audit, rapport complet
    - Plusieurs fichiers joints simultanément
    
    Level 4 — Agent requis (Agent IA recommandé, 60 à 600 crédits/tâche)
    - Verbes multi-étapes : va sur, cherche et compile
    - Demande impliquant plusieurs URLs
    - Mots-clés : automatiquement, en autonomie
    - Veille ou comparaison de plusieurs sites
    """
    rules = get_complexity_rules()
    message_lower = message.lower()
    words = message.split()
    word_count = len(words)
    detected_keywords = []
    
    # Check for Agent-level keywords first (highest priority)
    agent_rules = rules.get("agent", DEFAULT_COMPLEXITY_RULES["agent"])
    for kw in agent_rules.get("keywords", []):
        if kw.lower() in message_lower:
            detected_keywords.append(kw)
    
    if detected_keywords or (file_count > 2 and "url" in message_lower):
        return ComplexityAnalysisResponse(
            level="agent",
            detected_keywords=detected_keywords,
            word_count=word_count,
            recommended_model="agent",
            recommended_credits=60,  # Base agent cost
            current_model_ok=(current_model == "agent"),
            suggestion="Cette tâche semble nécessiter un Agent IA autonome pour des actions multi-étapes." if current_model != "agent" else None,
            upgrade_hint=current_model not in ["agent", None]
        )
    
    # Check for Complex level
    complex_rules = rules.get("complex", DEFAULT_COMPLEXITY_RULES["complex"])
    complex_keywords = []
    for kw in complex_rules.get("keywords", []):
        if kw.lower() in message_lower:
            complex_keywords.append(kw)
    
    is_complex = (
        word_count > complex_rules.get("min_words", 300) or
        file_pages > complex_rules.get("min_file_pages", 10) or
        file_count > 2 or
        len(complex_keywords) > 0
    )
    
    if is_complex:
        detected_keywords = complex_keywords
        current_ok = current_model in ["pro", "agent"]
        return ComplexityAnalysisResponse(
            level="complex",
            detected_keywords=detected_keywords,
            word_count=word_count,
            recommended_model="pro",
            recommended_credits=4,
            current_model_ok=current_ok,
            suggestion="Cette demande est complexe. Claude Pro est recommandé pour de meilleurs résultats." if not current_ok else None,
            upgrade_hint=not current_ok
        )
    
    # Check for Medium level
    medium_rules = rules.get("medium", DEFAULT_COMPLEXITY_RULES["medium"])
    medium_keywords = []
    for kw in medium_rules.get("keywords", []):
        if kw.lower() in message_lower:
            medium_keywords.append(kw)
    
    is_medium = (
        (word_count >= medium_rules.get("min_words", 80) and word_count <= medium_rules.get("max_words", 300)) or
        (file_pages > 0 and file_pages <= medium_rules.get("max_file_pages", 10)) or
        len(medium_keywords) > 0
    )
    
    if is_medium:
        detected_keywords = medium_keywords
        current_ok = current_model in ["pro", "agent", "gemini", "grok", "perplexity"]
        return ComplexityAnalysisResponse(
            level="medium",
            detected_keywords=detected_keywords,
            word_count=word_count,
            recommended_model="pro",
            recommended_credits=4,
            current_model_ok=current_ok or current_model == "fast",  # Fast is acceptable but Pro recommended
            suggestion="Claude Pro est recommandé pour cette demande de complexité moyenne." if current_model == "fast" else None,
            upgrade_hint=current_model == "fast"
        )
    
    # Default: Simple level
    simple_rules = rules.get("simple", DEFAULT_COMPLEXITY_RULES["simple"])
    simple_keywords = []
    for kw in simple_rules.get("keywords", []):
        if kw.lower() in message_lower:
            simple_keywords.append(kw)
    
    return ComplexityAnalysisResponse(
        level="simple",
        detected_keywords=simple_keywords,
        word_count=word_count,
        recommended_model="fast",
        recommended_credits=2,
        current_model_ok=True,  # All models are OK for simple tasks
        suggestion=None,
        upgrade_hint=False
    )


@complexity_router.post("/analyze", response_model=ComplexityAnalysisResponse)
async def analyze_message_complexity(
    request: ComplexityAnalysisRequest,
    user: User = Depends(get_current_user)
):
    """
    Analyze the complexity of a user message and return recommendations.
    
    This endpoint is called before sending a message to suggest the optimal model.
    """
    return analyze_complexity(
        message=request.message,
        file_count=request.file_count,
        file_pages=request.file_pages,
        exchange_count=request.exchange_count,
        current_model=request.current_model
    )


@complexity_router.get("/rules")
async def get_rules(user: User = Depends(get_current_user)):
    """Get the current complexity detection rules."""
    rules = get_complexity_rules()
    return {
        "rules": rules,
        "summary": {
            "simple": {"max_words": 80, "credits": 2, "model": "Claude Fast"},
            "medium": {"words": "80-300", "credits": 4, "model": "Claude Pro"},
            "complex": {"min_words": 300, "credits": 4, "model": "Claude Pro", "hint": "Suggestion upgrade"},
            "agent": {"credits": "60-600", "model": "Agent IA", "hint": "Tâches multi-étapes"}
        }
    }
