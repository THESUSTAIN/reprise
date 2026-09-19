"""Enforcement central des compétences IA par utilisateur.

Une permission est toujours lue côté serveur depuis le bucket user_data associé au
JWT courant. Une valeur absente vaut False : l’interface ne peut donc pas activer
une compétence en contournant le backend.
"""
import json
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def _ensure_user_data(db: AsyncSession):
    await db.execute(text(
        'CREATE TABLE IF NOT EXISTS user_data ('
        'id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(255) NOT NULL, '
        '"key" VARCHAR(255) NOT NULL, value JSON, '
        'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
    ))


async def get_ai_permissions(db: AsyncSession, user_id: str) -> dict:
    await _ensure_user_data(db)
    row = (await db.execute(text(
        'SELECT value FROM user_data WHERE user_id = :uid AND "key" = :key LIMIT 1'
    ), {"uid": user_id, "key": "user_prefs"})).fetchone()
    if not row or not row[0]:
        return {}
    value = json.loads(row[0]) if isinstance(row[0], str) else row[0]
    return dict((value or {}).get("ai_permissions") or {})


async def require_ai_permission(db: AsyncSession, user_id: str, skill: str):
    permissions = await get_ai_permissions(db, user_id)
    if permissions.get(skill) is not True:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "AI_PERMISSION_REQUIRED",
                "skill": skill,
                "message": f"La compétence IA '{skill}' doit être autorisée avant cette préparation.",
            },
        )
    return True
