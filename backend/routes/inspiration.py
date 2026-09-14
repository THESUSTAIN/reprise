"""
inspiration.py — Citations d'inspiration planifiées.

- Deux jeux paramétrables : `christian` (chrétien) et `secular` (non chrétien).
- Chaque citation peut avoir une date de démarrage (`starts_at`) → elle devient
  "en cours" à partir de ce jour (passage à 0h UTC).
- Sans planification, rotation quotidienne déterministe (change à 0h) parmi les
  citations actives du jeu.
- L'admin voit : la citation EN COURS + celles qui DÉMARRENT dans 30 jours.

Table auto-créée : inspiration_quotes.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta, date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, async_session_factory
from deps import get_admin_user, get_current_user_optional

logger = logging.getLogger("inspiration")
inspiration_router = APIRouter(tags=["Inspiration"])

VALID_SETS = ("christian", "secular")

_SEED = {
    "christian": [
        {"text": "Je puis tout par celui qui me fortifie.", "author": "Philippiens 4:13", "source": "Bible"},
        {"text": "Remets ton sort à l'Éternel, mets en lui ta confiance, et il agira.", "author": "Psaume 37:5", "source": "Bible"},
        {"text": "Tout concourt au bien de ceux qui aiment Dieu.", "author": "Romains 8:28", "source": "Bible"},
        {"text": "Ne crains rien, car je suis avec toi.", "author": "Ésaïe 41:10", "source": "Bible"},
    ],
    "secular": [
        {"text": "La clarté précède la croissance.", "author": "James Clear", "source": "Atomic Habits"},
        {"text": "L'obstacle est la voie.", "author": "Marc Aurèle", "source": "Pensées"},
        {"text": "La discipline est le pont entre les objectifs et les accomplissements.", "author": "Jim Rohn", "source": ""},
        {"text": "La meilleure façon de prévoir l'avenir, c'est de le créer.", "author": "Peter Drucker", "source": ""},
    ],
}


async def _ensure_table(db: AsyncSession):
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS inspiration_quotes (
            id VARCHAR(36) PRIMARY KEY,
            text TEXT NOT NULL,
            author VARCHAR(160),
            source VARCHAR(255),
            set_type VARCHAR(20) NOT NULL DEFAULT 'secular',
            starts_at VARCHAR(40),
            active INTEGER DEFAULT 1,
            created_at VARCHAR(40)
        )
    """))
    await db.commit()
    # Seed idempotent (une fois si vide)
    n = (await db.execute(text("SELECT COUNT(*) FROM inspiration_quotes"))).scalar() or 0
    if n == 0:
        now = datetime.now(timezone.utc).isoformat()
        for st, items in _SEED.items():
            for it in items:
                await db.execute(text("""
                    INSERT INTO inspiration_quotes (id, text, author, source, set_type, starts_at, active, created_at)
                    VALUES (:id, :t, :a, :s, :st, NULL, 1, :ca)
                """), {"id": str(uuid.uuid4()), "t": it["text"], "a": it["author"],
                       "s": it["source"], "st": st, "ca": now})
        await db.commit()


def _row(r):
    return {"id": r[0], "text": r[1], "author": r[2], "source": r[3],
            "set_type": r[4], "starts_at": r[5], "active": bool(r[6]), "created_at": r[7]}


async def _all(db, set_type: str):
    rows = (await db.execute(text(
        "SELECT id, text, author, source, set_type, starts_at, active, created_at "
        "FROM inspiration_quotes WHERE set_type = :st ORDER BY created_at ASC"
    ), {"st": set_type})).fetchall()
    return [_row(r) for r in rows]


def _current_from(quotes: list) -> Optional[dict]:
    """Citation en cours : la plus récente planifiée dont starts_at <= aujourd'hui ;
    sinon rotation quotidienne déterministe (change à 0h UTC)."""
    active = [q for q in quotes if q["active"]]
    if not active:
        return None
    today = datetime.now(timezone.utc).date()
    scheduled_now = []
    for q in active:
        if q["starts_at"]:
            try:
                d = datetime.fromisoformat(q["starts_at"]).date()
                if d <= today:
                    scheduled_now.append((d, q))
            except Exception:
                pass
    if scheduled_now:
        scheduled_now.sort(key=lambda x: x[0])
        return scheduled_now[-1][1]
    # rotation déterministe parmi les non planifiées (ou toutes si toutes planifiées futures)
    pool = [q for q in active if not q["starts_at"]] or active
    idx = datetime.now(timezone.utc).timetuple().tm_yday % len(pool)
    return pool[idx]


def _upcoming(quotes: list, days: int) -> list:
    today = datetime.now(timezone.utc).date()
    horizon = today + timedelta(days=days)
    out = []
    for q in quotes:
        if q["active"] and q["starts_at"]:
            try:
                d = datetime.fromisoformat(q["starts_at"]).date()
                if today < d <= horizon:
                    out.append({**q, "starts_in_days": (d - today).days})
            except Exception:
                pass
    out.sort(key=lambda x: x["starts_in_days"])
    return out


# ─────────────────────────── Public / user ───────────────────────────
@inspiration_router.get("/inspiration/current")
async def current_quote(set_type: str = "secular", db: AsyncSession = Depends(get_db)):
    if set_type not in VALID_SETS:
        set_type = "secular"
    await _ensure_table(db)
    q = _current_from(await _all(db, set_type))
    return {"set_type": set_type, "date": datetime.now(timezone.utc).date().isoformat(), "quote": q}


# ─────────────────────────── Admin ───────────────────────────
@inspiration_router.get("/admin/inspiration/schedule")
async def schedule(set_type: str = "secular", days: int = 30, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Citation EN COURS + celles qui DÉMARRENT dans `days` jours, pour un jeu."""
    if set_type not in VALID_SETS:
        raise HTTPException(400, "set_type doit être 'christian' ou 'secular'")
    await _ensure_table(db)
    quotes = await _all(db, set_type)
    return {
        "set_type": set_type,
        "current": _current_from(quotes),
        "upcoming": _upcoming(quotes, days),
        "all": quotes,
        "total": len(quotes),
    }


@inspiration_router.get("/admin/inspiration/overview")
async def overview(days: int = 30, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Vue des deux jeux (chrétien + laïque) d'un coup."""
    await _ensure_table(db)
    result = {}
    for st in VALID_SETS:
        quotes = await _all(db, st)
        result[st] = {"current": _current_from(quotes), "upcoming": _upcoming(quotes, days), "all": quotes}
    return result


class QuoteIn(BaseModel):
    text: str
    author: Optional[str] = ""
    source: Optional[str] = ""
    set_type: str = "secular"
    starts_at: Optional[str] = None  # ISO date (YYYY-MM-DD) — optionnel
    active: bool = True


@inspiration_router.post("/admin/inspiration/quotes")
async def add_quote(body: QuoteIn, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    if body.set_type not in VALID_SETS:
        raise HTTPException(400, "set_type doit être 'christian' ou 'secular'")
    if not body.text.strip():
        raise HTTPException(400, "Texte requis")
    await _ensure_table(db)
    qid = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO inspiration_quotes (id, text, author, source, set_type, starts_at, active, created_at)
        VALUES (:id, :t, :a, :s, :st, :sa, :ac, :ca)
    """), {"id": qid, "t": body.text.strip()[:500], "a": (body.author or "")[:120],
           "s": (body.source or "")[:200], "st": body.set_type,
           "sa": (body.starts_at or None), "ac": 1 if body.active else 0,
           "ca": datetime.now(timezone.utc).isoformat()})
    await db.commit()
    return {"ok": True, "id": qid}


@inspiration_router.put("/admin/inspiration/quotes/{qid}")
async def update_quote(qid: str, body: QuoteIn, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _ensure_table(db)
    r = (await db.execute(text("SELECT id FROM inspiration_quotes WHERE id = :id"), {"id": qid})).fetchone()
    if not r:
        raise HTTPException(404, "Citation introuvable")
    await db.execute(text("""
        UPDATE inspiration_quotes SET text=:t, author=:a, source=:s, set_type=:st,
        starts_at=:sa, active=:ac WHERE id=:id
    """), {"t": body.text.strip()[:500], "a": (body.author or "")[:120], "s": (body.source or "")[:200],
           "st": body.set_type, "sa": (body.starts_at or None), "ac": 1 if body.active else 0, "id": qid})
    await db.commit()
    return {"ok": True}


@inspiration_router.delete("/admin/inspiration/quotes/{qid}")
async def delete_quote(qid: str, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _ensure_table(db)
    await db.execute(text("DELETE FROM inspiration_quotes WHERE id = :id"), {"id": qid})
    await db.commit()
    return {"ok": True}
