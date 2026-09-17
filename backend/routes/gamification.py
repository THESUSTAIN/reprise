"""
gamification.py — Passeport / Gamification (backlog #17).

Ma recommandation : plutôt que d'inventer des paliers arbitraires, je relie
directement le Passeport au Score Business déjà calculé (vision_brain.py,
0-100, sur des données réelles — "score = KPI réels uniquement" était déjà
la contrainte posée dans le backlog original). Débloquer un agent
supplémentaire à un score engagé/élevé est un levier d'activation classique
(freemium hook) sans avoir à inventer un système de points séparé.

Choix commercial que je fais à ta place, à ajuster si tu n'es pas d'accord :
un utilisateur engagé (score ≥ 60) débloque 1 agent IA même sur un plan qui
n'en offre normalement aucun (free/starter/student) — un utilisateur très
engagé (score ≥ 85) en débloque 2. C'est un bonus ADDITIF au plan, jamais un
remplacement : ça ne touche pas aux plans payants eux-mêmes (pro reste à 5,
business/team restent illimités). Les seuils (60/85) et le nombre de slots
(1/2) sont mes hypothèses de départ, pas une vérité — change-les si ça ne
correspond pas à ta stratégie de conversion.
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User, VisionScoreSnapshot

router = APIRouter(prefix="/api/gamification", tags=["gamification"])

# Paliers du Passeport. `bonus_agent_slots` s'ajoute aux agents déjà permis
# par le plan (voir routes/custom_agents.py::AGENT_LIMITS) — jamais un
# remplacement du plan payant.
PASSPORT_TIERS = [
    {"id": "decouverte", "label": "Découverte",      "min_score": 0,  "bonus_agent_slots": 0},
    {"id": "actif",      "label": "Actif",            "min_score": 40, "bonus_agent_slots": 0},
    {"id": "engage",     "label": "Engagé",           "min_score": 60, "bonus_agent_slots": 1},
    {"id": "pilote",     "label": "Pilote confirmé",  "min_score": 85, "bonus_agent_slots": 2},
]


async def get_latest_score(db: AsyncSession, user_id: str) -> int:
    """Dernier Score Business connu (0 si aucun historique — cohérent avec
    le comportement "premier calcul" du panneau IA, pas de valeur inventée)."""
    last = (await db.execute(
        select(VisionScoreSnapshot)
        .where(VisionScoreSnapshot.user_id == user_id)
        .order_by(VisionScoreSnapshot.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    return last.score if last else 0


def tier_for_score(score: int) -> dict:
    current = PASSPORT_TIERS[0]
    for t in PASSPORT_TIERS:
        if score >= t["min_score"]:
            current = t
    return current


async def get_bonus_agent_slots(db: AsyncSession, user_id: str) -> int:
    """Utilisé par routes/custom_agents.py pour ajouter le bonus au plafond du plan."""
    score = await get_latest_score(db, user_id)
    return tier_for_score(score)["bonus_agent_slots"]


@router.get("/passport")
async def get_passport(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    score = await get_latest_score(db, user.id)
    current = tier_for_score(score)
    next_tier = next((t for t in PASSPORT_TIERS if t["min_score"] > score), None)
    return {
        "score": score,
        "tier": current["id"],
        "tier_label": current["label"],
        "bonus_agent_slots": current["bonus_agent_slots"],
        "next_tier": {"label": next_tier["label"], "min_score": next_tier["min_score"]} if next_tier else None,
        "tiers": PASSPORT_TIERS,
    }
