"""
Audit 360 Biblique Routes — TheSustain module
Stores audit data (metrics, member comments, AI insights) per user.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import json
import os
import logging

from database import get_db
from deps import get_current_user
from models import User

logger = logging.getLogger(__name__)
audit_router = APIRouter(prefix="/audit", tags=["Audit"])

# In-memory store per user (production would use DB table)
_audit_store: Dict[str, Dict] = {}


class AuditMetrics(BaseModel):
    engagement_global: float = 0
    sentiment_positif: float = 0
    sentiment_neutre: float = 0
    sentiment_negatif: float = 0
    nouveaux_visiteurs: int = 0
    score_sante: float = 0
    engagement_physique: List[float] = []
    engagement_digital: List[float] = []
    labels_mois: List[str] = []


class MemberComment(BaseModel):
    author: str = ""
    text: str = ""
    source: str = "sondage"
    sentiment: str = "positif"
    date: str = ""


class AuditSaveRequest(BaseModel):
    org_name: str = ""
    org_type: str = "eglise"
    metrics: Optional[AuditMetrics] = None
    comments: Optional[List[MemberComment]] = None
    social_links: Optional[Dict[str, str]] = None


class AuditAnalyzeRequest(BaseModel):
    org_name: str = ""
    metrics: Optional[AuditMetrics] = None
    comments: Optional[List[Dict[str, str]]] = None


@audit_router.get("/data")
async def get_audit_data(user=Depends(get_current_user)):
    uid = str(user.id)
    data = _audit_store.get(uid, _default_audit_data())
    return data


@audit_router.post("/save")
async def save_audit_data(req: AuditSaveRequest, user=Depends(get_current_user)):
    uid = str(user.id)
    existing = _audit_store.get(uid, _default_audit_data())
    if req.org_name:
        existing["org_name"] = req.org_name
    if req.org_type:
        existing["org_type"] = req.org_type
    if req.metrics:
        existing["metrics"] = req.metrics.dict()
    if req.comments is not None:
        existing["comments"] = [c.dict() for c in req.comments]
    if req.social_links:
        existing["social_links"] = req.social_links
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    _audit_store[uid] = existing
    return {"status": "ok", "data": existing}


@audit_router.post("/comment")
async def add_comment(data: MemberComment, user=Depends(get_current_user)):
    uid = str(user.id)
    existing = _audit_store.get(uid, _default_audit_data())
    comment = data.dict()
    comment["date"] = comment["date"] or datetime.now(timezone.utc).isoformat()
    existing.setdefault("comments", []).append(comment)
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    _audit_store[uid] = existing
    return {"status": "ok", "comments": existing["comments"]}


@audit_router.delete("/comment/{index}")
async def delete_comment(index: int, user=Depends(get_current_user)):
    uid = str(user.id)
    existing = _audit_store.get(uid, _default_audit_data())
    comments = existing.get("comments", [])
    if 0 <= index < len(comments):
        comments.pop(index)
        existing["comments"] = comments
        _audit_store[uid] = existing
    return {"status": "ok", "comments": existing.get("comments", [])}


@audit_router.post("/analyze")
async def analyze_audit(req: AuditAnalyzeRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Generate AI biblical insights from audit data."""
    metrics = req.metrics.dict() if req.metrics else {}
    comments_text = ""
    if req.comments:
        for c in req.comments[:20]:
            comments_text += f"- [{c.get('source','sondage')}] {c.get('text','')}\n"

    prompt = f"""Tu es un conseiller pastoral expert et analyste de donnees pour les eglises.
Organisation: {req.org_name or 'Communaute'}
Metriques: Engagement={metrics.get('engagement_global',0)}%, Sentiment positif={metrics.get('sentiment_positif',0)}%, Nouveaux visiteurs={metrics.get('nouveaux_visiteurs',0)}, Score sante IA={metrics.get('score_sante',0)}/10
Commentaires des fideles:
{comments_text or 'Aucun commentaire fourni.'}

Analyse ces donnees et genere EXACTEMENT 3 recommandations bibliques concretes.
Reponds UNIQUEMENT en JSON valide (pas de markdown, pas de ```):
[{{"category":"ACCUEIL|JEUNESSE|ENSEIGNEMENT|COMMUNION|ADORATION|PRIERE","observation":"observation detaillee","verse":"verset biblique complet avec reference","action":"action concrete a mettre en place","source":"Detecte via Sondage|Instagram|Youtube|Observation"}}]"""

    try:
        from mammouth_client import chat as mammouth_chat, MammouthError, MAMMOUTH_API_KEY
        if not MAMMOUTH_API_KEY:
            raise HTTPException(400, "Cle API requise pour l'analyse IA")
        raw = await mammouth_chat(
            messages=[
                {"role": "system", "content": "Tu es un conseiller pastoral expert. Reponds uniquement en JSON valide."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.3,
        )
        # Clean markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        insights = json.loads(raw)

        # Store insights
        uid = str(user.id)
        existing = _audit_store.get(uid, _default_audit_data())
        existing["insights"] = insights
        existing["last_analysis"] = datetime.now(timezone.utc).isoformat()
        _audit_store[uid] = existing

        return {"status": "ok", "insights": insights}
    except json.JSONDecodeError:
        return {"status": "ok", "insights": [{"category": "GLOBAL", "observation": raw, "verse": "", "action": "", "source": "IA"}]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit analysis error: {e}")
        raise HTTPException(500, f"Erreur analyse IA: {str(e)}")


def _default_audit_data():
    return {
        "org_name": "",
        "org_type": "eglise",
        "metrics": {
            "engagement_global": 0,
            "sentiment_positif": 0,
            "sentiment_neutre": 0,
            "sentiment_negatif": 0,
            "nouveaux_visiteurs": 0,
            "score_sante": 0,
            "engagement_physique": [65, 59, 80, 81, 56, 55, 72],
            "engagement_digital": [28, 48, 40, 19, 86, 27, 90],
            "labels_mois": ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun", "Jul"],
        },
        "comments": [],
        "social_links": {},
        "insights": [],
        "last_analysis": None,
        "updated_at": None,
    }
