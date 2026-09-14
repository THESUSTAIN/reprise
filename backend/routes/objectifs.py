"""
Objectifs — Vision.jsx. Reprend le pattern JSON déjà éprouvé et en
production sur routes/growth.py (table user_leads) — même approche,
zéro dépendance nouvelle, cohérent avec le reste du backend.
"""
import json
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/objectifs", tags=["Objectifs"])


async def _ensure_table(db: AsyncSession):
    await db.execute(text(
        "CREATE TABLE IF NOT EXISTS user_objectifs ("
        "id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, "
        "data JSON NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    ))


async def _list(db: AsyncSession, user_id: str) -> list:
    await _ensure_table(db)
    try:
        r = await db.execute(
            text("SELECT id, data FROM user_objectifs WHERE user_id = :uid ORDER BY created_at DESC"),
            {"uid": user_id},
        )
        out = []
        for row in r.fetchall():
            data = row[1]
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = {}
            data = data or {}
            data.setdefault("id", row[0])
            out.append(data)
        return out
    except Exception as e:
        logger.warning("objectifs _list failed: %s", e)
        return []


class ObjectifIn(BaseModel):
    titre: str
    categorie: str = "Liberté"
    description: str = ""
    valeur_actuelle: float = 0
    valeur_cible: float = 1
    unite: str = ""


@router.get("")
async def list_objectifs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list(db, user.id)


@router.post("")
async def create_objectif(body: ObjectifIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _ensure_table(db)
    obj = {
        "id": uuid.uuid4().hex,
        **body.dict(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.execute(
        text("INSERT INTO user_objectifs (id, user_id, data) VALUES (:id, :uid, :d)"),
        {"id": obj["id"], "uid": user.id, "d": json.dumps(obj)},
    )
    await db.commit()
    return obj


@router.put("/{objectif_id}")
async def update_objectif(objectif_id: str, body: ObjectifIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(text("SELECT data FROM user_objectifs WHERE id = :id AND user_id = :uid"), {"id": objectif_id, "uid": user.id})
    row = r.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Objectif introuvable")
    data = row[0] if isinstance(row[0], dict) else json.loads(row[0] or "{}")
    data.update(body.dict())
    data["id"] = objectif_id
    await db.execute(text("UPDATE user_objectifs SET data = :d WHERE id = :id AND user_id = :uid"), {"d": json.dumps(data), "id": objectif_id, "uid": user.id})
    await db.commit()
    return data


@router.delete("/{objectif_id}")
async def delete_objectif(objectif_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM user_objectifs WHERE id = :id AND user_id = :uid"), {"id": objectif_id, "uid": user.id})
    await db.commit()
    return {"ok": True}


@router.post("/{objectif_id}/to-action")
async def objectif_to_action(objectif_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Transforme un objectif en habitude/rituel réel — réutilise le vrai
    système (table user_habits, routes/missing_apis.py), déjà en place et
    fonctionnel, plutôt qu'un modèle Rituel qui n'existe pas."""
    r = await db.execute(text("SELECT data FROM user_objectifs WHERE id = :id AND user_id = :uid"), {"id": objectif_id, "uid": user.id})
    row = r.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Objectif introuvable")
    data = row[0] if isinstance(row[0], dict) else json.loads(row[0] or "{}")
    titre = data.get("titre", "Objectif")
    from routes.missing_apis import _insert_row
    habit = await _insert_row(db, "user_habits", user.id, {"name": f"Avancer : {titre}", "icon": "target", "done_dates": []})
    return {"ok": True, "habit_id": habit["id"]}
