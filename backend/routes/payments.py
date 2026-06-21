"""
Routes Paiements Mollie — Achat de packs de crédits
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database import get_db
from models import User, Team, TeamMember, CreditLog

logger = logging.getLogger("payments")
payments_router = APIRouter(prefix="/payments", tags=["Payments"])
bearer = HTTPBearer(auto_error=False)

MOLLIE_API_KEY = os.environ.get("MOLLIE_API_KEY", "")

# Credit packs
CREDIT_PACKS = [
    {"id": "pack_1000", "credits": 1000, "price": "29.00", "label": "1 000 credits", "currency": "EUR"},
    {"id": "pack_3000", "credits": 3000, "price": "79.00", "label": "3 000 credits", "currency": "EUR"},
    {"id": "pack_5000", "credits": 5000, "price": "119.00", "label": "5 000 credits", "currency": "EUR"},
]


async def get_user(creds: HTTPAuthorizationCredentials, db: AsyncSession) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Non authentifie")
    from jose import jwt, JWTError
    from deps import JWT_SECRET
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = str(payload.get("user_id") or payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


async def get_user_team(user: User, db: AsyncSession) -> Team:
    result = await db.execute(select(Team).where(Team.owner_id == user.id))
    team = result.scalar_one_or_none()
    if team:
        return team
    result2 = await db.execute(
        select(Team).join(TeamMember).where(TeamMember.user_id == user.id, TeamMember.status == "active")
    )
    return result2.scalar_one_or_none()


@payments_router.get("/packs")
async def get_credit_packs():
    """Retourne les packs de crédits disponibles."""
    return CREDIT_PACKS


class CreatePaymentRequest(BaseModel):
    pack_id: str
    redirect_url: str


@payments_router.post("/create")
async def create_payment(
    body: CreatePaymentRequest,
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    """Crée un paiement Mollie pour un pack de crédits."""
    user = await get_user(creds, db)
    team = await get_user_team(user, db)
    if not team:
        raise HTTPException(status_code=404, detail="Aucune equipe trouvee")

    pack = next((p for p in CREDIT_PACKS if p["id"] == body.pack_id), None)
    if not pack:
        raise HTTPException(status_code=400, detail="Pack invalide")

    if not MOLLIE_API_KEY:
        raise HTTPException(status_code=503, detail="Paiement non configure. Contactez l'administrateur.")

    try:
        from mollie.api.client import Client
        mollie = Client()
        mollie.set_api_key(MOLLIE_API_KEY)

        payment = mollie.payments.create({
            "amount": {"currency": pack["currency"], "value": pack["price"]},
            "description": f"Extension IA by Zayado - {pack['label']}",
            "redirectUrl": body.redirect_url,
            "webhookUrl": f"{os.environ.get('BACKEND_URL', body.redirect_url.split('/app')[0])}/api/payments/webhook",
            "metadata": {
                "team_id": team.id,
                "user_id": user.id,
                "pack_id": pack["id"],
                "credits": pack["credits"],
            },
        })

        logger.info(f"Mollie payment created: {payment.id} for team {team.id} ({pack['label']})")

        return {
            "payment_id": payment.id,
            "checkout_url": payment.checkout_url,
            "status": payment.status,
        }
    except Exception as e:
        logger.error(f"Mollie payment creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur creation paiement: {str(e)}")


@payments_router.post("/webhook")
async def mollie_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Webhook Mollie — appelé quand un paiement change de statut."""
    try:
        form = await request.form()
        payment_id = form.get("id")
        if not payment_id:
            return {"status": "ignored"}

        if not MOLLIE_API_KEY:
            logger.error("MOLLIE_API_KEY not set, cannot verify webhook")
            return {"status": "error"}

        from mollie.api.client import Client
        mollie = Client()
        mollie.set_api_key(MOLLIE_API_KEY)
        payment = mollie.payments.get(payment_id)

        if payment.is_paid():
            meta = payment.metadata or {}
            team_id = meta.get("team_id")
            user_id = meta.get("user_id")
            credits = int(meta.get("credits", 0))
            pack_id = meta.get("pack_id")

            if not team_id or credits <= 0:
                logger.warning(f"Invalid metadata for payment {payment_id}")
                return {"status": "invalid_metadata"}

            # Add credits to team pool
            await db.execute(
                update(Team).where(Team.id == team_id).values(shared_credits=Team.shared_credits + credits)
            )

            # Log
            db.add(CreditLog(
                id=str(uuid.uuid4()), team_id=team_id, user_id=user_id,
                amount=credits, log_type="purchase",
                description=f"Achat Mollie: +{credits} credits ({pack_id})"
            ))
            await db.commit()

            logger.info(f"Payment {payment_id} confirmed: +{credits} credits for team {team_id}")
            return {"status": "paid", "credits_added": credits}
        else:
            logger.info(f"Payment {payment_id} status: {payment.status}")
            return {"status": payment.status}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}


@payments_router.get("/status/{payment_id}")
async def check_payment_status(
    payment_id: str,
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    """Vérifie le statut d'un paiement."""
    await get_user(creds, db)

    if not MOLLIE_API_KEY:
        raise HTTPException(status_code=503, detail="Paiement non configure")

    try:
        from mollie.api.client import Client
        mollie = Client()
        mollie.set_api_key(MOLLIE_API_KEY)
        payment = mollie.payments.get(payment_id)

        return {
            "id": payment.id,
            "status": payment.status,
            "is_paid": payment.is_paid(),
            "amount": payment.amount,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
