"""Document revision (track changes) routes."""
import logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import os
import httpx

from database import get_db
from models import User
from deps import get_current_user
from utils import MAMMOTH_BASE_URL

revision_router = APIRouter(prefix="/revision", tags=["Revision"])

@revision_router.post("/suggest")
async def suggest_revisions(data: Dict[str, Any], user: User = Depends(get_current_user)):
    """Analyze text and suggest tracked changes (additions, deletions, modifications)."""
    text = data.get("text", "").strip()
    instructions = data.get("instructions", "").strip()
    style = data.get("style", "professional")

    if not text:
        raise HTTPException(status_code=400, detail="Texte requis")

    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(status_code=500, detail="IA non configuree")

    style_prompts = {
        "professional": "Rends le texte plus professionnel et formel",
        "concise": "Rends le texte plus concis sans perdre le sens",
        "friendly": "Rends le texte plus accessible et amical",
        "academic": "Adapte le texte au style academique avec rigueur",
        "marketing": "Rends le texte plus percutant et oriente marketing",
    }
    style_instruction = style_prompts.get(style, style_prompts["professional"])

    system_prompt = f"""Tu es un editeur de texte professionnel. Tu dois analyser le texte fourni et proposer des modifications.
    
Instruction de style: {style_instruction}
{f"Instructions supplementaires: {instructions}" if instructions else ""}

Tu dois retourner un JSON avec exactement cette structure:
{{
  "changes": [
    {{
      "type": "replace",
      "original": "texte original exact",
      "suggestion": "texte modifie propose",
      "reason": "raison courte de la modification"
    }},
    {{
      "type": "delete", 
      "original": "texte a supprimer",
      "reason": "raison de la suppression"
    }},
    {{
      "type": "insert",
      "after": "texte apres lequel inserer",
      "suggestion": "nouveau texte a inserer",
      "reason": "raison de l'ajout"
    }}
  ],
  "summary": "resume des modifications proposees",
  "improved_text": "le texte complet avec toutes les modifications appliquees"
}}

Detecte la langue du texte et reponds dans cette meme langue. Retourne UNIQUEMENT le JSON, sans aucun texte avant ou apres."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{MAMMOTH_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-6",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.3
                }
            )

        if response.status_code == 200:
            ai_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            import json, re
            json_match = re.search(r'\{[\s\S]*\}', ai_text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    # Valider que le résultat a la structure attendue
                    if isinstance(result, dict):
                        return result
                except (json.JSONDecodeError, ValueError):
                    pass
            # Fallback propre si l'IA ne renvoie pas du JSON valide (bug #9)
            return {
                "changes": [],
                "summary": ai_text[:500] if ai_text else "Révision effectuée",
                "improved_text": text,
                "error": "Format IA non JSON — texte brut retourné"
            }
        else:
            raise HTTPException(status_code=502, detail=f"Erreur IA: {response.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@revision_router.post("/apply")
async def apply_revision(data: Dict[str, Any], user: User = Depends(get_current_user)):
    """Apply selected changes to the original text."""
    original = data.get("original_text", "")
    changes = data.get("changes", [])

    if not original or not changes:
        raise HTTPException(status_code=400, detail="Texte original et modifications requis")

    result = original
    for change in sorted(changes, key=lambda c: original.find(c.get("original", "")), reverse=True):
        if change.get("type") == "replace" and change.get("original"):
            result = result.replace(change["original"], change.get("suggestion", ""), 1)
        elif change.get("type") == "delete" and change.get("original"):
            result = result.replace(change["original"], "", 1)
        elif change.get("type") == "insert" and change.get("after"):
            idx = result.find(change["after"])
            if idx >= 0:
                insert_pos = idx + len(change["after"])
                result = result[:insert_pos] + " " + change.get("suggestion", "") + result[insert_pos:]

    return {"revised_text": result, "changes_applied": len(changes)}

@revision_router.post("/compare")
async def compare_texts(data: Dict[str, Any], user: User = Depends(get_current_user)):
    """Compare two versions of text and return differences."""
    original = data.get("original", "")
    revised = data.get("revised", "")

    if not original or not revised:
        raise HTTPException(status_code=400, detail="Les deux versions du texte sont requises")

    import difflib
    differ = difflib.unified_diff(
        original.splitlines(keepends=True),
        revised.splitlines(keepends=True),
        fromfile="Original",
        tofile="Revise",
        lineterm=""
    )
    diff_lines = list(differ)

    additions = sum(1 for l in diff_lines if l.startswith('+') and not l.startswith('+++'))
    deletions = sum(1 for l in diff_lines if l.startswith('-') and not l.startswith('---'))

    return {
        "diff": "\n".join(diff_lines),
        "additions": additions,
        "deletions": deletions,
        "total_changes": additions + deletions
    }
