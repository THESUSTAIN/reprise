"""Boutique Zayado — endpoints publics : statut maintenance + waitlist."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func

from database import async_session_factory
from models import ShopWaitlist, PlatformSetting

logger = logging.getLogger(__name__)

shop_router = APIRouter(prefix="/shop", tags=["shop"])


class WaitlistRequest(BaseModel):
    email: EmailStr
    discount_optin: bool = True
    locale: str | None = None
    source: str | None = "maintenance-splash"


@shop_router.get("/status")
async def shop_status():
    """Retourne le statut de la boutique (maintenance ou catalogue).

    Piloté par la clé `shop_maintenance` dans `platform_settings`.
    Par défaut : maintenance = true (la boutique n'est pas encore lancée).
    """
    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(PlatformSetting).where(PlatformSetting.key == "shop_maintenance")
            )
            setting = result.scalar_one_or_none()
            if setting and setting.value:
                # Stored as "1"/"0" or "true"/"false"
                v = setting.value.strip().lower()
                maintenance = v in ("1", "true", "yes", "on")
            else:
                maintenance = True
        return {"maintenance": maintenance, "source": "db"}
    except Exception as e:
        logger.warning(f"[shop.status] {e}")
        return {"maintenance": True, "source": "fallback"}


@shop_router.get("/waitlist-count")
async def waitlist_count():
    """Compteur public des inscrits sur la waitlist boutique (+ baseline social proof)."""
    try:
        async with async_session_factory() as db:
            result = await db.execute(select(func.count(ShopWaitlist.id)))
            real_count = result.scalar() or 0
        # Baseline social proof (rejoint le count actuel affiché côté front)
        baseline = 247
        return {"count": baseline + real_count}
    except Exception as e:
        logger.warning(f"[shop.waitlist-count] {e}")
        return {"count": 247}


@shop_router.post("/waitlist")
async def waitlist_subscribe(body: WaitlistRequest):
    """Inscrit un email sur la waitlist boutique (idempotent)."""
    email = body.email.strip().lower()
    try:
        async with async_session_factory() as db:
            existing = await db.execute(
                select(ShopWaitlist).where(ShopWaitlist.email == email)
            )
            if existing.scalar_one_or_none():
                return {"status": "already_registered", "email": email}
            entry = ShopWaitlist(
                email=email,
                discount_optin=body.discount_optin,
                locale=body.locale,
                source=body.source,
                created_at=datetime.now(timezone.utc),
            )
            db.add(entry)
            await db.commit()
        return {"status": "subscribed", "email": email, "discount_optin": body.discount_optin}
    except Exception as e:
        logger.error(f"[shop.waitlist] {e}")
        raise HTTPException(status_code=500, detail="Inscription waitlist indisponible.")
