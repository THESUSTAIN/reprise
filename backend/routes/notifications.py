"""Notifications broadcast — admin CRUD + endpoint public 'active'.

Surfaces:
 - app_modal     : modal au démarrage du SaaS (utilisateurs connectés)
 - shop_modal    : modal sur la boutique publique
 - shop_banner   : bandeau sur la boutique publique

Audience:
 - all | logged | guests | shop_visitors

Le frontend filtre l'affichage (1x par notif via localStorage).
Supporte un embed_url (Canva iframe, etc.) pour rendu visuel riche.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_admin_user, get_current_user_optional
from models import BroadcastNotification

logger = logging.getLogger(__name__)
notif_router = APIRouter(tags=["notifications"])


class NotifIn(BaseModel):
    title: str
    body_html: Optional[str] = None
    embed_url: Optional[str] = None
    cta_label: Optional[str] = None
    cta_url: Optional[str] = None
    surface: str = "app_modal"   # app_modal | shop_modal | shop_banner
    audience: str = "all"        # all | logged | guests | shop_visitors
    active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


def _serialize(n: BroadcastNotification) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "body_html": n.body_html,
        "embed_url": n.embed_url,
        "cta_label": n.cta_label,
        "cta_url": n.cta_url,
        "surface": n.surface,
        "audience": n.audience,
        "active": n.active,
        "starts_at": n.starts_at.isoformat() if n.starts_at else None,
        "ends_at": n.ends_at.isoformat() if n.ends_at else None,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


# ───────────── Admin CRUD ─────────────
@notif_router.get("/admin/broadcast-notifications")
async def list_notifs(admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(BroadcastNotification).order_by(BroadcastNotification.created_at.desc())
    )).scalars().all()
    return {"notifications": [_serialize(n) for n in rows]}


@notif_router.post("/admin/broadcast-notifications")
async def create_notif(body: NotifIn, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    n = BroadcastNotification(**body.dict())
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return _serialize(n)


@notif_router.patch("/admin/broadcast-notifications/{nid}")
async def update_notif(nid: str, body: NotifIn, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    n = (await db.execute(
        select(BroadcastNotification).where(BroadcastNotification.id == nid)
    )).scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(n, k, v)
    await db.commit()
    await db.refresh(n)
    return _serialize(n)


@notif_router.delete("/admin/broadcast-notifications/{nid}")
async def delete_notif(nid: str, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    n = (await db.execute(
        select(BroadcastNotification).where(BroadcastNotification.id == nid)
    )).scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    await db.delete(n)
    await db.commit()
    return {"status": "deleted"}


# ───────────── Gel global des notifications (maintenance / correction) ─────────────
class GateIn(BaseModel):
    hold: bool


@notif_router.get("/admin/notifications/gate")
async def get_notif_gate(admin=Depends(get_admin_user)):
    from notif_gate import get_state
    return get_state()


@notif_router.post("/admin/notifications/gate")
async def set_notif_gate(body: GateIn, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Active/désactive le gel global. À la réactivation (hold=false), la DERNIÈRE
    notification bloquée est renvoyée (une seule, pas d'avalanche)."""
    from notif_gate import set_hold, pop_last
    resent = None
    if body.hold:
        state = set_hold(True)
        return {**state, "message": "Notifications gelées — seule la dernière sera renvoyée à la réactivation."}
    # Réactivation
    state = set_hold(False)
    last = pop_last()
    if last and last.get("kind") == "push":
        p = last.get("payload", {})
        try:
            from routes.push import send_push_to_user
            ok = await send_push_to_user(
                db, p.get("user_id"), p.get("title", "MyExtension AI"),
                p.get("body", ""), image=p.get("image"), url=p.get("url", "/"),
                family=p.get("family", "ai_tasks"),
            )
            resent = {"kind": "push", "sent": ok, "title": p.get("title")}
        except Exception as e:
            logger.warning(f"gate resend push KO: {e}")
            resent = {"kind": "push", "sent": False, "error": str(e)}
    return {**state, "resent": resent,
            "message": "Notifications réactivées." + (" Dernière notification renvoyée." if resent else "")}


# ───────────── Public endpoint (user/shop visitor) ─────────────
@notif_router.get("/broadcast-notifications/active")
async def get_active_notif(
    surface: str = "app_modal",
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Retourne la 1ère notif active correspondant à la surface + audience.
    Le frontend filtre l'affichage via localStorage (1 fois par notif id)."""
    # Gel global (correction en cours) : on ne montre AUCUNE modale/bandeau.
    try:
        from notif_gate import is_held
        if is_held():
            return None
    except Exception:
        pass
    now = datetime.now(timezone.utc)
    q = select(BroadcastNotification).where(
        BroadcastNotification.active == True,  # noqa: E712
        BroadcastNotification.surface == surface,
    ).order_by(BroadcastNotification.created_at.desc())
    rows = (await db.execute(q)).scalars().all()
    for n in rows:
        # Time window filter (handle naive datetimes from MySQL)
        if n.starts_at:
            sa = n.starts_at if n.starts_at.tzinfo else n.starts_at.replace(tzinfo=timezone.utc)
            if sa > now:
                continue
        if n.ends_at:
            ea = n.ends_at if n.ends_at.tzinfo else n.ends_at.replace(tzinfo=timezone.utc)
            if ea < now:
                continue
        # Audience filter
        if n.audience == "logged" and not user:
            continue
        if n.audience == "guests" and user:
            continue
        # shop_visitors: tolerant — always shown on shop surfaces
        return _serialize(n)
    return None
