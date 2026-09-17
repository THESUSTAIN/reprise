"""
Routes mémoire conversationnelle — /api/collaborateur/history
À ajouter dans server.py :
    from routes.collab_memory import memory_router
    app.include_router(memory_router, prefix="/api")

Permet au backend de stocker/lire les 10 derniers échanges par user_id.
Utilisé par CollaborateurPanel pour injecter le contexte dans chaque session.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

memory_router = APIRouter(prefix="/collaborateur", tags=["Collab Memory"])

MAX_TURNS = 10   # Nombre de tours (user+ai) à conserver

# ── Modèles ──────────────────────────────────────────────────────────────

class MemoryMessage(BaseModel):
    role: str         # "user" | "assistant"
    content: str
    ts: Optional[str] = None

class MemorySave(BaseModel):
    messages: list[MemoryMessage]

# ── Helpers DB ────────────────────────────────────────────────────────────
async def _get_collab_table(db):
    """Crée la table collab_memory si elle n'existe pas (simple JSON column)."""
    try:
        await db.execute(text(
            "CREATE TABLE IF NOT EXISTS collab_memory ("
            "  user_id  VARCHAR(36) PRIMARY KEY,"
            "  messages JSON NOT NULL,"
            "  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        ))
        await db.commit()
    except Exception:
        pass  # Table déjà créée ou moteur différent

async def _load(db, user_id: str) -> list:
    try:
        result = await db.execute(
            text("SELECT messages FROM collab_memory WHERE user_id = :uid"),
            {"uid": user_id}
        )
        row = result.fetchone()
        if not row:
            return []
        raw = row[0]
        return json.loads(raw) if isinstance(raw, str) else (raw or [])
    except Exception:
        return []

async def _save(db, user_id: str, messages: list):
    msgs_json = json.dumps(messages, ensure_ascii=False)
    now = datetime.now(timezone.utc).isoformat()
    try:
        await db.execute(
            text("INSERT INTO collab_memory (user_id, messages, updated_at) VALUES (:uid, :msgs, :ts) "
                 "ON DUPLICATE KEY UPDATE messages = :msgs, updated_at = :ts"),
            {"uid": user_id, "msgs": msgs_json, "ts": now}
        )
        await db.commit()
    except Exception:
        # SQLite UPSERT fallback
        try:
            await db.execute(
                text("INSERT OR REPLACE INTO collab_memory (user_id, messages, updated_at) VALUES (:uid, :msgs, :ts)"),
                {"uid": user_id, "msgs": msgs_json, "ts": now}
            )
            await db.commit()
        except Exception:
            pass

# ── Routes ────────────────────────────────────────────────────────────────

@memory_router.get("/history")
async def get_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retourne les MAX_TURNS derniers échanges de l'utilisateur."""
    await _get_collab_table(db)
    messages = await _load(db, user.id)
    # Ne retourner que les MAX_TURNS derniers tours (user+ai = 2 msgs/tour)
    return {"messages": messages[-(MAX_TURNS * 2):]}


@memory_router.post("/history")
async def save_history(
    payload: MemorySave,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sauvegarde l'historique de conversation (MAX_TURNS derniers)."""
    await _get_collab_table(db)
    # Tronquer côté serveur aussi
    to_save = [m.dict() for m in payload.messages][-(MAX_TURNS * 2):]
    await _save(db, user.id, to_save)
    return {"ok": True, "saved": len(to_save)}


@memory_router.delete("/history")
async def clear_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Efface la mémoire conversationnelle de l'utilisateur."""
    try:
        await db.execute(
            text("DELETE FROM collab_memory WHERE user_id = :uid"),
            {"uid": user.id}
        )
        await db.commit()
    except Exception:
        pass
    return {"ok": True}
