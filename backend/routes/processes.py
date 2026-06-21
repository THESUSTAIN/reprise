"""Processus Métier — CRUD des processus de l'entreprise."""
import uuid, json, logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from deps import get_current_user, User

logger = logging.getLogger(__name__)
processes_router = APIRouter(prefix="/processes", tags=["Processes"])

class ProcessCreate(BaseModel):
    id: Optional[str] = None
    label: str
    icon: Optional[str] = "📋"
    color: Optional[str] = "#1D4E8A"
    steps: Optional[list] = []
    progress: Optional[int] = 0

class ProcessUpdate(BaseModel):
    label: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    steps: Optional[list] = None
    progress: Optional[int] = None

@processes_router.get("")
async def list_processes(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Retourne tous les processus de l'utilisateur (stockés en mémoire utilisateur)."""
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT id, data FROM user_processes WHERE user_id = :uid ORDER BY created_at DESC"),
            {"uid": user.id}
        )
        rows = result.fetchall()
        return [json.loads(r[1]) for r in rows]
    except Exception:
        # Table may not exist yet
        return []

@processes_router.post("")
async def create_process(data: ProcessCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Crée ou sauvegarde un processus."""
    try:
        from sqlalchemy import text
        # Ensure table exists
        await db.execute(text(
            "CREATE TABLE IF NOT EXISTS user_processes ("
            "id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, "
            "data JSON NOT NULL, created_at DATETIME DEFAULT NOW(), "
            "updated_at DATETIME DEFAULT NOW() ON UPDATE NOW())"
        ))
        process_id = data.id or str(uuid.uuid4())
        process_data = {
            "id": process_id, "label": data.label, "icon": data.icon,
            "color": data.color, "steps": data.steps or [], "progress": data.progress or 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.execute(text(
            "INSERT INTO user_processes (id, user_id, data) VALUES (:id, :uid, :data) "
            "ON DUPLICATE KEY UPDATE data = :data, updated_at = NOW()"
        ), {"id": process_id, "uid": user.id, "data": json.dumps(process_data)})
        await db.commit()
        return process_data
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Erreur: {str(e)[:200]}")

@processes_router.put("/{process_id}")
async def update_process(process_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Met à jour un processus."""
    try:
        from sqlalchemy import text
        await db.execute(text(
            "UPDATE user_processes SET data = :data, updated_at = NOW() "
            "WHERE id = :id AND user_id = :uid"
        ), {"id": process_id, "uid": user.id, "data": json.dumps(data)})
        await db.commit()
        return {"ok": True}
    except Exception as e:
        await db.rollback()
        return {"ok": False, "error": str(e)[:100]}

@processes_router.delete("/{process_id}")
async def delete_process(process_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Supprime un processus."""
    try:
        from sqlalchemy import text
        await db.execute(text(
            "DELETE FROM user_processes WHERE id = :id AND user_id = :uid"
        ), {"id": process_id, "uid": user.id})
        await db.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False}
