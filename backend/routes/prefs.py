"""Préférences utilisateur (/api/prefs) — persistance dans la table KV user_data.

Corrige le bug : sans cet endpoint, `onboarded` n'était jamais sauvegardé,
donc l'onboarding se relançait à chaque connexion.

Mode invité compatible (user_id en query param, comme le reste de l'app).
"""
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user_optional
from routes.growth import _get_kv, _save_kv

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/prefs", tags=["prefs"])

_KEY = "user_prefs"


async def _ensure_table(db: AsyncSession):
    await db.execute(text(
        "CREATE TABLE IF NOT EXISTS user_data ("
        "id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(255) NOT NULL, "
        "\"key\" VARCHAR(255) NOT NULL, value JSON, "
        "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    ))


@router.get("")
async def get_prefs(user_id: str = Query("default"), user=Depends(get_current_user_optional), db: AsyncSession = Depends(get_db)):
    try:
        await _ensure_table(db)
        # Si un token JWT valide est présent, on scope sur l'utilisateur authentifié
        # (évite de renvoyer le bucket partagé "default" d'un autre compte). Sinon on
        # retombe sur le user_id en query param (compatibilité mode invité).
        uid = user.id if user else user_id
        return (await _get_kv(db, uid, _KEY)) or {}
    except Exception as e:
        # QA a signalé un 500 silencieux ici au chargement de l'accueil.
        # On degrade en préférences vides plutôt que de casser le chargement
        # de la page pour un souci de persistance non bloquant.
        logger.error(f"get_prefs failed for user_id={user_id}: {e}", exc_info=True)
        return {}


@router.put("")
async def save_prefs(patch: dict, user_id: str = Query("default"), user=Depends(get_current_user_optional), db: AsyncSession = Depends(get_db)):
    await _ensure_table(db)
    uid = user.id if user else user_id
    current = (await _get_kv(db, uid, _KEY)) or {}
    merged = {**current, **(patch or {})}
    await _save_kv(db, uid, _KEY, merged)
    await db.commit()
    return merged
