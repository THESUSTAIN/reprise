"""
Web Push notifications (VAPID + pywebpush).

Endpoints:
  POST /api/push/subscribe      → enregistre la PushSubscription du device
  POST /api/push/unsubscribe    → supprime la subscription
  POST /api/push/test           → envoie une notif de test à l'utilisateur courant
  GET  /api/push/public-key     → retourne la clé publique VAPID (alternative à env frontend)
  GET  /api/push/preferences    → récupère les préférences (familles activées)
  PUT  /api/push/preferences    → met à jour les préférences

Stockage : table `user_data` (clé `push_subscription` et `push_preferences`).
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pywebpush import webpush, WebPushException

from database import get_db
from deps import get_current_user
from models import User, UserData

logger = logging.getLogger(__name__)
push_router = APIRouter(prefix="/push", tags=["push"])

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY_PATH = os.environ.get("VAPID_PRIVATE_KEY_PATH", "")
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:hello@zayado.net")

# Familles de notifications (cf. plan utilisateur)
DEFAULT_PREFERENCES = {
    "wellbeing": True,    # 🧘 check-in matinal, encouragement, surcharge, détox, bilan hebdo
    "business": True,     # 💼 leads chauds, DMs, paiements, trésorerie, URSSAF
    "ai_tasks": True,     # 🤖 tâche terminée, doc généré, suggestion proactive, flipbook prêt
    "reminders": True,    # 🎯 souvenirs vision, série brisée, progrès marquant
}

# ─────────────────────────────────────────────────────────────────
# Helpers stockage (table user_data)
# ─────────────────────────────────────────────────────────────────

async def _get_user_data(db: AsyncSession, user_id: str, key: str) -> Optional[dict]:
    r = await db.execute(select(UserData).where(UserData.user_id == user_id, UserData.key == key))
    row = r.scalar_one_or_none()
    if not row:
        return None
    try:
        return json.loads(row.value)
    except Exception:
        return None

async def _set_user_data(db: AsyncSession, user_id: str, key: str, value: dict):
    r = await db.execute(select(UserData).where(UserData.user_id == user_id, UserData.key == key))
    row = r.scalar_one_or_none()
    if row:
        row.value = json.dumps(value)
        row.updated_at = datetime.now(timezone.utc)
    else:
        db.add(UserData(user_id=user_id, key=key, value=json.dumps(value)))
    await db.commit()

async def _delete_user_data(db: AsyncSession, user_id: str, key: str):
    r = await db.execute(select(UserData).where(UserData.user_id == user_id, UserData.key == key))
    row = r.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()

# ─────────────────────────────────────────────────────────────────
# Modèles Pydantic
# ─────────────────────────────────────────────────────────────────

class PushSubscriptionIn(BaseModel):
    subscription: dict
    user_agent: Optional[str] = None

class PushTestIn(BaseModel):
    title: Optional[str] = "Test notification"
    body: Optional[str] = "Vos notifications fonctionnent !"
    image: Optional[str] = None
    url: Optional[str] = "/"

class PushPrefsIn(BaseModel):
    wellbeing: Optional[bool] = None
    business: Optional[bool] = None
    ai_tasks: Optional[bool] = None
    reminders: Optional[bool] = None

# ─────────────────────────────────────────────────────────────────
# Envoi push (réutilisable depuis n'importe quelle route)
# ─────────────────────────────────────────────────────────────────

async def send_push_to_user(
    db: AsyncSession,
    user_id: str,
    title: str,
    body: str,
    image: Optional[str] = None,
    url: str = "/",
    family: str = "ai_tasks",
) -> bool:
    """Envoie une notification push à un utilisateur.
    Respecte les préférences (silence si la famille est désactivée).
    Retourne True si envoyé, False si pas de subscription ou famille off.
    """
    # 1. Vérifier les préférences
    prefs = await _get_user_data(db, user_id, "push_preferences") or DEFAULT_PREFERENCES
    if not prefs.get(family, True):
        return False

    # 2. Récupérer la subscription
    sub_data = await _get_user_data(db, user_id, "push_subscription")
    if not sub_data or "subscription" not in sub_data:
        return False

    # 3. Envoyer
    payload = json.dumps({
        "title": title,
        "body": body,
        "image": image,
        "url": url,
        "family": family,
    })
    try:
        webpush(
            subscription_info=sub_data["subscription"],
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY_PATH,
            vapid_claims={"sub": VAPID_SUBJECT},
        )
        return True
    except WebPushException as e:
        # 410 Gone = subscription invalide → on supprime
        if "410" in str(e) or "404" in str(e):
            await _delete_user_data(db, user_id, "push_subscription")
        logger.warning(f"WebPush failed for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"WebPush unexpected error: {e}")
        return False

# ─────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────

@push_router.get("/public-key")
async def get_public_key():
    return {"public_key": VAPID_PUBLIC_KEY}

@push_router.post("/subscribe")
async def subscribe(
    payload: PushSubscriptionIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not payload.subscription.get("endpoint"):
        raise HTTPException(400, "Subscription invalide (endpoint manquant)")
    await _set_user_data(db, user.id, "push_subscription", {
        "subscription": payload.subscription,
        "user_agent": payload.user_agent or "",
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "subscribed": True}

@push_router.post("/unsubscribe")
async def unsubscribe(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _delete_user_data(db, user.id, "push_subscription")
    return {"ok": True, "subscribed": False}

@push_router.post("/test")
async def test_push(
    payload: PushTestIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await send_push_to_user(
        db, user.id,
        title=payload.title or "Test MyExtension AI",
        body=payload.body or "Vos notifications fonctionnent !",
        image=payload.image,
        url=payload.url or "/",
        family="ai_tasks",
    )
    if not ok:
        raise HTTPException(404, "Aucune subscription active pour cet utilisateur")
    return {"ok": True, "sent": True}

@push_router.get("/preferences")
async def get_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prefs = await _get_user_data(db, user.id, "push_preferences") or DEFAULT_PREFERENCES
    sub = await _get_user_data(db, user.id, "push_subscription")
    return {
        "preferences": prefs,
        "subscribed": bool(sub and sub.get("subscription")),
    }

@push_router.put("/preferences")
async def update_preferences(
    payload: PushPrefsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current = await _get_user_data(db, user.id, "push_preferences") or DEFAULT_PREFERENCES
    updated = {**current}
    for k in ("wellbeing", "business", "ai_tasks", "reminders"):
        v = getattr(payload, k)
        if v is not None:
            updated[k] = bool(v)
    await _set_user_data(db, user.id, "push_preferences", updated)
    return {"preferences": updated}
