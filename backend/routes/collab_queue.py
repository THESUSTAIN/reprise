"""
File IA — livrables IA en attente de validation (FileIAValidation sur le Dashboard).
À ajouter dans server.py :
    from routes.collab_queue import queue_router
    app.include_router(queue_router, prefix="/api")
"""
import json, uuid as _uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

queue_router = APIRouter(prefix="/collaborateur", tags=["IA Queue"])


async def _ensure_table(db: AsyncSession):
    try:
        await db.execute(text(
            "CREATE TABLE IF NOT EXISTS ia_queue_items ("
            " id VARCHAR(36) PRIMARY KEY,"
            " user_id VARCHAR(36) NOT NULL,"
            " tag VARCHAR(40) NOT NULL,"
            " title VARCHAR(255) NOT NULL,"
            " excerpt TEXT,"
            " status VARCHAR(20) NOT NULL DEFAULT 'pending',"
            " created_at DATETIME DEFAULT CURRENT_TIMESTAMP,"
            " INDEX ix_queue_user_status (user_id, status)"
            ")"
        ))
        await db.commit()
    except Exception:
        pass


class QueueItemIn(BaseModel):
    tag: str
    title: str
    excerpt: str = ""


@queue_router.get("/queue")
async def list_queue(
    limit: int = 3,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Livrables IA en attente de validation pour l'utilisateur (FileIAValidation)."""
    await _ensure_table(db)
    rows = (await db.execute(
        text(
            "SELECT id, tag, title, excerpt, created_at FROM ia_queue_items "
            "WHERE user_id = :uid AND status = 'pending' "
            "ORDER BY created_at DESC LIMIT :lim"
        ),
        {"uid": user.id, "lim": limit},
    )).fetchall()

    items = []
    now = datetime.now(timezone.utc)
    for r in rows:
        created = r[4]
        delta_min = max(0, int((now - created.replace(tzinfo=timezone.utc)).total_seconds() // 60)) if created else 0
        if delta_min < 60:
            time_str = f"Il y a {delta_min} min"
        elif delta_min < 1440:
            time_str = f"Il y a {delta_min // 60}h"
        else:
            time_str = f"Il y a {delta_min // 1440} j"
        items.append({
            "id": r[0], "tag": r[1], "title": r[2],
            "excerpt": r[3] or "", "time": time_str,
        })

    total = (await db.execute(
        text("SELECT COUNT(*) FROM ia_queue_items WHERE user_id = :uid AND status = 'pending'"),
        {"uid": user.id},
    )).scalar() or 0

    return {"items": items, "total_pending": total}


@queue_router.post("/queue")
async def create_queue_item(
    body: QueueItemIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permet au Collaborateur IA d'ajouter un livrable à valider."""
    await _ensure_table(db)
    item_id = str(_uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO ia_queue_items (id, user_id, tag, title, excerpt, status) "
            "VALUES (:id, :uid, :tag, :title, :excerpt, 'pending')"
        ),
        {"id": item_id, "uid": user.id, "tag": body.tag, "title": body.title, "excerpt": body.excerpt},
    )
    await db.commit()
    return {"ok": True, "id": item_id}


@queue_router.post("/queue/{item_id}/validate")
async def validate_queue_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_table(db)
    result = await db.execute(
        text("UPDATE ia_queue_items SET status='validated' WHERE id=:id AND user_id=:uid"),
        {"id": item_id, "uid": user.id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, "Élément introuvable.")
    return {"ok": True}


@queue_router.post("/queue/{item_id}/dismiss")
async def dismiss_queue_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_table(db)
    result = await db.execute(
        text("UPDATE ia_queue_items SET status='dismissed' WHERE id=:id AND user_id=:uid"),
        {"id": item_id, "uid": user.id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, "Élément introuvable.")
    return {"ok": True}
