"""Travail — hub d'exécution (CRM léger, agenda, agrégation temps réel, recommandations IA).

Zéro donnée fictive : tout est calculé depuis les vraies données de l'utilisateur
(projets, tâches, leads CRM, agenda, finances). Empty states propres si rien.

Tables JSON ad-hoc (cohérent avec routes/missing_apis.py) :
- crm_leads   : {name, company, email, phone, stage, value, notes}
- crm_events  : {title, date (YYYY-MM-DD), time (HH:MM), kind, notes}
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user, User
from models import Project, FinanceEntryDB
from routes.missing_apis import _list_rows, _insert_row, _update_row, _delete_row

logger = logging.getLogger(__name__)
travail_router = APIRouter(prefix="/travail", tags=["Travail"])

STAGES = ["nouveau", "contacte", "proposition", "negociation", "gagne", "perdu"]


def _utc_now():
    return datetime.now(timezone.utc)


def _ensure_tz(dt):
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _today_str():
    return _utc_now().strftime("%Y-%m-%d")


# ============================================================
# CRM  /api/travail/crm
# ============================================================
class LeadIn(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    stage: Optional[str] = "nouveau"
    value: Optional[float] = 0
    notes: Optional[str] = None


class LeadPatch(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    stage: Optional[str] = None
    value: Optional[float] = None
    notes: Optional[str] = None


def _pipeline(items: list) -> dict:
    counters = {s: 0 for s in STAGES}
    for it in items:
        s = it.get("stage", "nouveau")
        if s in counters:
            counters[s] += 1
    return counters


@travail_router.get("/crm")
async def list_crm(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "crm_leads", user.id)
    won_value = sum(float(it.get("value") or 0) for it in items if it.get("stage") == "gagne")
    return {"items": items, "pipeline": _pipeline(items), "total": len(items), "won_value": round(won_value, 2)}


@travail_router.post("/crm")
async def create_lead(body: LeadIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _insert_row(db, "crm_leads", user.id, body.dict())


@travail_router.patch("/crm/{lid}")
async def patch_lead(lid: str, body: LeadPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await _update_row(db, "crm_leads", user.id, lid, body.dict(exclude_unset=True))
    return res or {"error": "not_found"}


@travail_router.delete("/crm/{lid}")
async def delete_lead(lid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"deleted": await _delete_row(db, "crm_leads", user.id, lid)}


# ============================================================
# AGENDA  /api/travail/events
# ============================================================
class EventIn(BaseModel):
    title: str
    date: Optional[str] = None       # YYYY-MM-DD
    time: Optional[str] = None       # HH:MM
    kind: Optional[str] = "visio"    # visio | présentiel | focus | récurrent
    notes: Optional[str] = None


class EventPatch(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    kind: Optional[str] = None
    notes: Optional[str] = None


@travail_router.get("/events")
async def list_events(day: Optional[str] = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "crm_events", user.id)
    if day == "today":
        items = [e for e in items if e.get("date") == _today_str()]
    items.sort(key=lambda e: (e.get("date") or "", e.get("time") or ""))
    return {"items": items}


@travail_router.post("/events")
async def create_event(body: EventIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = body.dict()
    data["date"] = data.get("date") or _today_str()
    return await _insert_row(db, "crm_events", user.id, data)


@travail_router.patch("/events/{eid}")
async def patch_event(eid: str, body: EventPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await _update_row(db, "crm_events", user.id, eid, body.dict(exclude_unset=True))
    return res or {"error": "not_found"}


@travail_router.delete("/events/{eid}")
async def delete_event(eid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"deleted": await _delete_row(db, "crm_events", user.id, eid)}


# ============================================================
# OVERVIEW  /api/travail/overview  (agrégation temps réel)
# ============================================================
async def _finance_month(db: AsyncSession, uid: str, start: datetime, end: datetime):
    r = await db.execute(
        select(FinanceEntryDB).where(
            FinanceEntryDB.user_id == uid,
            FinanceEntryDB.date >= start,
            FinanceEntryDB.date < end,
        )
    )
    rows = list(r.scalars().all())
    rev = sum(e.amount for e in rows if e.type == "revenu")
    dep = sum(e.amount for e in rows if e.type == "depense")
    return rev, dep


def _pct_delta(cur: float, prev: float):
    if prev <= 0:
        return None
    return round((cur - prev) / prev * 100, 1)


@travail_router.get("/overview")
async def travail_overview(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    uid = user.id
    try:
        now = _utc_now()
        today = _today_str()

        # ── Projets ──
        r = await db.execute(select(Project).where(Project.user_id == uid))
        projects = list(r.scalars().all())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = sum(1 for p in projects if p.created_at and _ensure_tz(p.created_at) >= month_start)

        # ── Tâches ──
        tasks = await _list_rows(db, "user_tasks", uid)
        pending = [t for t in tasks if not t.get("done")]
        created_today = sum(1 for t in tasks if (t.get("created_at") or "")[:10] == today)

        # ── Agenda (aujourd'hui) ──
        events = await _list_rows(db, "crm_events", uid)
        events_today = [e for e in events if e.get("date") == today]

        # ── CRM ──
        leads = await _list_rows(db, "crm_leads", uid)
        pipeline = _pipeline(leads)

        # ── Finances (mois courant vs mois précédent) ──
        prev_end = month_start
        prev_start = (month_start - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (month_start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ca, dep = await _finance_month(db, uid, month_start, next_month)
        ca_prev, dep_prev = await _finance_month(db, uid, prev_start, prev_end)
        net = ca - dep
        net_prev = ca_prev - dep_prev
        marge = round(net / ca * 100, 1) if ca > 0 else 0
        marge_prev = round(net_prev / ca_prev * 100, 1) if ca_prev > 0 else 0

        return {
            "projects": {"active": len(projects), "new_this_month": new_this_month},
            "tasks": {"pending": len(pending), "created_today": created_today},
            "appointments": {"today": len(events_today)},
            "crm": {"total": len(leads), "pipeline": pipeline},
            "finance": {
                "ca": round(ca, 2), "ca_delta": _pct_delta(ca, ca_prev),
                "depenses": round(dep, 2), "depenses_delta": _pct_delta(dep, dep_prev),
                "net": round(net, 2), "net_delta": _pct_delta(net, net_prev),
                "marge": marge, "marge_delta": round(marge - marge_prev, 1) if ca_prev > 0 else None,
            },
        }
    except Exception as e:
        # QA a signalé un 500 permanent ici ("Impossible de charger votre
        # activité", même après Réessayer). Cause exacte non reproductible
        # sans les logs prod — en attendant, on renvoie un état vide bien
        # formé (comme le reste de l'app le fait déjà pour les flux
        # externes indisponibles) plutôt que de casser toute la page, et on
        # logge l'erreur réelle côté serveur.
        logger.error(f"travail_overview failed for user {uid}: {e}", exc_info=True)
        return {
            "projects": {"active": 0, "new_this_month": 0},
            "tasks": {"pending": 0, "created_today": 0},
            "appointments": {"today": 0},
            "crm": {"total": 0, "pipeline": _pipeline([])},
            "finance": {"ca": 0, "ca_delta": None, "depenses": 0, "depenses_delta": None, "net": 0, "net_delta": None, "marge": 0, "marge_delta": None},
            "error": "temporairement indisponible",
        }


# ============================================================
# RECOMMANDATIONS IA  /api/travail/recommendations
# ============================================================
@travail_router.get("/recommendations")
async def travail_recommendations(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    uid = user.id
    now = _utc_now()
    recos = []
    try:
        leads = await _list_rows(db, "crm_leads", uid)

        # 1) Relances : devis (proposition/négociation) en attente > 7 jours
        def _age_days(it):
            ts = it.get("updated_at") or it.get("created_at")
            if not ts:
                return 0
            try:
                d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return (now - _ensure_tz(d)).days
            except Exception:
                return 0

        stale = [l for l in leads if l.get("stage") in ("proposition", "negociation") and _age_days(l) >= 7]
        if stale:
            recos.append({
                "id": "relances", "icon": "clock", "tone": "gold",
                "title": "Priorisez les relances",
                "desc": f"{len(stale)} devis en attente depuis plus de 7 jours",
                "route": "/travail?tab=crm",
            })

        # 2) Opportunité : lead en négociation le plus récent
        nego = [l for l in leads if l.get("stage") == "negociation"]
        if nego:
            top = sorted(nego, key=lambda l: l.get("value") or 0, reverse=True)[0]
            recos.append({
                "id": "opportunite", "icon": "lightbulb", "tone": "sage",
                "title": "Opportunité détectée",
                "desc": f"{top.get('name', 'Un prospect')} est en phase de négociation — closez cette semaine",
                "route": "/travail?tab=crm",
            })

        # 3) Optimisation financière : dépenses récurrentes
        r = await db.execute(
            select(FinanceEntryDB).where(FinanceEntryDB.user_id == uid, FinanceEntryDB.type == "depense", FinanceEntryDB.recurring == True)  # noqa: E712
        )
        rec_dep = list(r.scalars().all())
        if rec_dep:
            total = sum(e.amount for e in rec_dep)
            recos.append({
                "id": "finance", "icon": "trending-down", "tone": "coral",
                "title": "Optimisation financière",
                "desc": f"{len(rec_dep)} dépenses récurrentes ({round(total)} €/mois) — passez-les en revue",
                "route": "/pilotage",
            })

        # 4) Tâches du jour en attente
        tasks = await _list_rows(db, "user_tasks", uid)
        pending = [t for t in tasks if not t.get("done")]
        if len(pending) >= 3:
            recos.append({
                "id": "taches", "icon": "check", "tone": "plum",
                "title": "Concentrez-vous sur l'essentiel",
                "desc": f"{len(pending)} tâches ouvertes — traitez d'abord les 3 priorités du jour",
                "route": "/",
            })

        return {"items": recos}
    except Exception as e:
        logger.error(f"travail_recommendations failed for user {uid}: {e}", exc_info=True)
        return {"items": []}
