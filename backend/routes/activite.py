"""
Routes pour Mon Activite — tableau de bord structure en 6 sections.
Persistance en base de donnees via UserData (key-value generique).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database import get_db
from deps import get_current_user
from models import UserData

activite_router = APIRouter(prefix="/activite", tags=["Activite"])


async def _get_data(db: AsyncSession, uid: str, key: str, default=None):
    result = await db.execute(
        select(UserData).where(and_(UserData.user_id == uid, UserData.key == key))
    )
    row = result.scalar_one_or_none()
    if row:
        try:
            return json.loads(row.value)
        except (json.JSONDecodeError, TypeError):
            return row.value
    return default


async def _set_data(db: AsyncSession, uid: str, key: str, val):
    result = await db.execute(
        select(UserData).where(and_(UserData.user_id == uid, UserData.key == key))
    )
    row = result.scalar_one_or_none()
    serialized = json.dumps(val, default=str)
    if row:
        row.value = serialized
    else:
        row = UserData(user_id=uid, key=key, value=serialized)
        db.add(row)
    await db.commit()


class UpdateBlocker(BaseModel):
    tension: str
    detail: Optional[str] = None

class SetPriority(BaseModel):
    title: str
    why: Optional[str] = None

class ChecklistItem(BaseModel):
    id: Optional[str] = None
    text: str
    done: bool = False

class SuiviEntry(BaseModel):
    day: int
    note: str
    status: str = "en_cours"


@activite_router.get("/summary")
async def get_activite_summary(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    uid = user.id
    diagnostic = await _get_data(db, uid, "diagnostic", {})
    score = diagnostic.get("score", None) if diagnostic else None
    blocker = await _get_data(db, uid, "blocker", None)
    priority = await _get_data(db, uid, "act_priority", None)
    checklist = await _get_data(db, uid, "checklist", [])
    suivi = await _get_data(db, uid, "suivi", [])
    ia_context = await _get_data(db, uid, "ia_context", None)
    current_day = await _get_data(db, uid, "current_day", 1)

    total_items = len(checklist) if isinstance(checklist, list) else 0
    done_items = sum(1 for c in checklist if c.get("done")) if isinstance(checklist, list) else 0
    progress = round(done_items / total_items * 100) if total_items > 0 else 0

    return {
        "ou_tu_en_es": {
            "score": score,
            "phase": diagnostic.get("phase", "decouverte") if diagnostic else "decouverte",
            "resume": diagnostic.get("resume", "Complete ton diagnostic pour obtenir une vision claire de ta situation.") if diagnostic else "Complete ton diagnostic pour obtenir une vision claire de ta situation.",
            "last_diagnostic": diagnostic.get("date", None) if diagnostic else None,
        },
        "ce_qui_te_bloque": blocker,
        "ton_action_prioritaire": priority,
        "fais_le_maintenant": {
            "checklist": checklist if isinstance(checklist, list) else [],
            "progress": progress,
            "total": total_items,
            "done": done_items,
        },
        "suivi": {
            "entries": suivi if isinstance(suivi, list) else [],
            "current_day": current_day,
        },
        "ia_contextuelle": ia_context,
    }


@activite_router.post("/diagnostic")
async def save_diagnostic_result(body: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _set_data(db, user.id, "diagnostic", {
        "score": body.get("score"),
        "phase": body.get("phase", "decouverte"),
        "resume": body.get("resume", ""),
        "date": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "ok"}


@activite_router.post("/blocker")
async def set_blocker(body: UpdateBlocker, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _set_data(db, user.id, "blocker", {
        "tension": body.tension,
        "detail": body.detail,
        "date": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "ok"}


@activite_router.post("/priority")
async def set_activity_priority(body: SetPriority, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _set_data(db, user.id, "act_priority", {
        "title": body.title,
        "why": body.why,
        "date": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "ok"}


@activite_router.post("/checklist")
async def update_checklist(items: List[ChecklistItem], user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    checklist = []
    for i, item in enumerate(items):
        checklist.append({"id": item.id or f"chk_{i}", "text": item.text, "done": item.done})
    await _set_data(db, user.id, "checklist", checklist)
    return {"status": "ok", "checklist": checklist}


@activite_router.post("/checklist/toggle/{item_id}")
async def toggle_checklist_item(item_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    checklist = await _get_data(db, user.id, "checklist", [])
    if isinstance(checklist, list):
        for item in checklist:
            if item.get("id") == item_id:
                item["done"] = not item.get("done", False)
                break
        await _set_data(db, user.id, "checklist", checklist)
    return {"status": "ok", "checklist": checklist}


@activite_router.post("/suivi")
async def add_suivi_entry(body: SuiviEntry, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    suivi = await _get_data(db, user.id, "suivi", [])
    if not isinstance(suivi, list):
        suivi = []
    suivi.append({
        "day": body.day,
        "note": body.note,
        "status": body.status,
        "date": datetime.now(timezone.utc).isoformat(),
    })
    await _set_data(db, user.id, "suivi", suivi)
    await _set_data(db, user.id, "current_day", body.day)
    return {"status": "ok"}


@activite_router.post("/ia-context")
async def save_ia_context(body: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _set_data(db, user.id, "ia_context", {
        "recommendation": body.get("recommendation", ""),
        "type": body.get("type", "general"),
        "date": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "ok"}
