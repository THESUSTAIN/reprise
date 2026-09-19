"""
Payments Routes (Mollie, credits, promo, billing) — extracted from server.py
"""
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
import os
import uuid
import json
import httpx
import asyncio
import re
import base64
import logging
import random

from database import get_db, async_session_factory
from models import User, Conversation, Project, Workflow, Transaction, PromoCode, PromoUsage, Folder, Team, TeamMember
from deps import get_current_user, get_admin_user, JWT_SECRET, JWT_ALGORITHM, security, hash_password, verify_password
from utils import (
    UPLOADS_DIR, MAMMOTH_BASE_URL, AGENT_DEFAULT_MODEL, AGENT_COMPLEX_MODEL, AGENT_MAX_TIMEOUT,
    AGENT_CREDITS_MAP, classify_task_type, estimate_agent_credits, select_agent_model,
    get_mollie_client, send_brevo_email, send_low_credits_notification,
    generate_invoice_pdf, invoice_number,
    load_admin_config, save_admin_config,
    _get_email_log, _append_email_log, _append_admin_log, _get_admin_log,
    EMAIL_TEMPLATES, GENERATED_IMAGES_DIR, CONFIG_PATH, logger as utils_logger,
    CREDIT_PACKAGES, SUBSCRIPTION_PLANS,
)
from mollie.api.client import Client as MollieClient
from mollie.api.error import Error as MollieError
from routes.app_logs import log_event

logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).parent

payments_router = APIRouter(tags=["Payments"])

@payments_router.get("/packages")
async def get_packages():
    try:
        config = load_admin_config()
        packages = config.get("packages", [])
        if packages:
            return packages
    except Exception:
        pass
    return CREDIT_PACKAGES

@payments_router.get("/plans")
async def get_plans():
    try:
        config = load_admin_config()
        plans = config.get("plans", [])
        if plans:
            return plans
    except Exception:
        pass
    return SUBSCRIPTION_PLANS

@payments_router.post("/buy-credits")
async def buy_credits(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Accept package_id from query param OR JSON body (pack / package_id)
    try:
        raw = await request.body()
        bdata = json.loads(raw) if raw else {}
    except Exception:
        bdata = {}
    package_id = bdata.get("pack") or bdata.get("package_id") or ""
    if not package_id:
        raise HTTPException(status_code=422, detail="package_id ou pack requis")
    # Load packages from admin config (uses cached loader — no blocking I/O)
    packages = CREDIT_PACKAGES
    try:
        config = load_admin_config()
        custom_packages = config.get("packages", [])
        if custom_packages:
            packages = custom_packages
    except Exception:
        pass
    package = next((p for p in packages if p["id"] == package_id), None)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # #41 — Check for existing pending transaction to prevent double-buy
    pending_check = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.package_id == package_id,
            Transaction.status == "pending",
            Transaction.type == "credits"
        )
    )
    if pending_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vous avez deja un achat en attente pour ce package")

    try:
        # Create Mollie payment
        payment = get_mollie_client().payments.create({
            'amount': {
                'currency': 'EUR',
                'value': f'{package["price"]:.2f}'
            },
            'description': f'Extension IA by Zayado - {package["name"]} ({package["credits"]} credits)',
            'redirectUrl': os.environ.get('APP_BASE_URL', 'https://app.zayado.net') + '/app?payment=success',
            'webhookUrl': os.environ.get('APP_BASE_URL', 'https://app.zayado.net') + '/api/payments/webhook',
            'metadata': {
                'user_id': user.id,
                'package_id': package_id,
                'type': 'credits',
                'credits': package["credits"]
            }
        })

        # Record transaction
        tx = Transaction(
            user_id=user.id, type="credits",
            package_id=package_id, amount=package["price"],
            credits=package["credits"], status="pending",
            mollie_payment_id=payment.id,
            checkout_url=payment.checkout_url
        )
        db.add(tx)
        await db.commit()

        asyncio.ensure_future(log_event(
            'INFO', 'payment', f'Achat crédits initié : {package["credits"]} crédits ({package["price"]} EUR)',
            action='buy_credits', user_id=user.id, user_email=user.email,
            details={'package_id': package_id, 'payment_id': payment.id, 'credits': package['credits'], 'price': package['price']}
        ))
        return {"status": "redirect", "checkout_url": payment.checkout_url, "payment_id": payment.id}

    except MollieError as e:
        logger.error(f"Mollie error: {str(e)}")
        asyncio.ensure_future(log_event(
            'ERROR', 'payment', f'Erreur Mollie achat crédits : {str(e)}',
            action='buy_credits_error', user_id=user.id, user_email=user.email,
            details={'package_id': package_id, 'error': str(e)}
        ))
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@payments_router.post("/checkout")
async def checkout_creation(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """One-time checkout for creation packs, pilotage financier, etc. via Mollie."""
    try:
        raw = await request.body()
        bdata = json.loads(raw) if raw else {}
    except Exception:
        bdata = {}

    pack_name = bdata.get("pack_name", "Pack")
    amount = bdata.get("amount")
    pack_type = bdata.get("type", "creation")
    if not amount or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="Montant invalide")

    amount = float(amount)
    try:
        payment = get_mollie_client().payments.create({
            'amount': {'currency': 'EUR', 'value': f'{amount:.2f}'},
            'description': f'Extension IA by Zayado - {pack_name}',
            'redirectUrl': os.environ.get('APP_BASE_URL', 'https://app.zayado.net') + f'/app?payment=success&type={pack_type}',
            'webhookUrl': os.environ.get('APP_BASE_URL', 'https://app.zayado.net') + '/api/payments/webhook',
            'metadata': {
                'user_id': user.id,
                'type': pack_type,
                'pack_id': bdata.get("pack_id", ""),
                'pack_name': pack_name,
                'email': bdata.get("email", user.email),
                'structure': bdata.get("structure", ""),
                'add_launch': bdata.get("add_launch", False),
            }
        })
        tx = Transaction(
            user_id=user.id, type=pack_type,
            package_id=bdata.get("pack_id", "custom"), amount=amount,
            credits=0, status="pending",
            mollie_payment_id=payment.id,
            checkout_url=payment.checkout_url
        )
        db.add(tx)
        await db.commit()
        return {"checkout_url": payment.checkout_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur paiement: {str(e)}")

@payments_router.post("/public-checkout")
async def public_checkout(request: Request, db: AsyncSession = Depends(get_db)):
    """Public checkout for standalone HTML pages (no auth required). Creates a Mollie payment."""
    try:
        raw = await request.body()
        bdata = json.loads(raw) if raw else {}
    except Exception:
        bdata = {}

    email = bdata.get("email", "").strip()
    pack_name = bdata.get("pack_name", "Pack")
    amount = bdata.get("amount")
    pack_type = bdata.get("type", "creation")
    pack_id = bdata.get("pack_id", "custom")

    if not email:
        raise HTTPException(status_code=400, detail="Email requis")
    if not amount or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="Montant invalide")

    amount = float(amount)
    try:
        redirect_base = os.environ.get('APP_BASE_URL', 'https://app.zayado.net')
        # Smart redirect based on pack type
        redirect_map = {
            'chatbot': '/app/chatbot-admin?payment=success',
            'agent': '/app/agents?payment=success',
            'ltd': '/app/activate-license?payment=success',
        }
        redirect_suffix = '/app?payment=success&type=' + pack_type
        for prefix, path in redirect_map.items():
            if pack_id.startswith(prefix) or pack_type == prefix:
                redirect_suffix = path + '&pack=' + pack_id
                break
        if 'ltd' in pack_id:
            redirect_suffix = '/app/activate-license?payment=success&pack=' + pack_id

        payment = get_mollie_client().payments.create({
            'amount': {'currency': 'EUR', 'value': f'{amount:.2f}'},
            'description': f'ZAYADO - {pack_name}',
            'redirectUrl': redirect_base + redirect_suffix,
            'webhookUrl': redirect_base + '/api/payments/webhook',
            'metadata': {
                'type': pack_type,
                'pack_id': pack_id,
                'pack_name': pack_name,
                'email': email,
                'structure': bdata.get("structure", ""),
                'source': 'html_standalone',
            }
        })

        # Find or create a minimal user record for the transaction
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        user_id = user.id if user else f"guest_{uuid.uuid4().hex[:12]}"

        tx = Transaction(
            user_id=user_id, type=pack_type,
            package_id=pack_id, amount=amount,
            credits=0, status="pending",
            mollie_payment_id=payment.id,
            checkout_url=payment.checkout_url
        )
        db.add(tx)
        await db.commit()

        return {"checkout_url": payment.checkout_url, "payment_id": payment.id}
    except MollieError as e:
        logger.error(f"Mollie public checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur paiement Mollie: {str(e)}")
    except Exception as e:
        logger.error(f"Public checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur paiement: {str(e)}")


@payments_router.post("/validate-promo")
async def validate_promo(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Validate a promo code and return its type and value without redeeming it."""
    try:
        raw = await request.body()
        bdata = json.loads(raw) if raw else {}
    except Exception:
        bdata = {}
    code_str = (bdata.get("code") or "").strip().upper()
    if not code_str:
        raise HTTPException(status_code=400, detail="Code requis")

    result = await db.execute(select(PromoCode).where(PromoCode.code == code_str, PromoCode.active == True))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Code promo invalide ou expire")

    if promo.expires_at and promo.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Code promo expire")

    if promo.current_uses >= promo.max_uses:
        raise HTTPException(status_code=400, detail="Code promo epuise")

    existing_use = await db.execute(select(PromoUsage).where(PromoUsage.user_id == user.id, PromoUsage.promo_code_id == promo.id))
    if existing_use.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vous avez deja utilise ce code")

    return {
        "valid": True,
        "code": promo.code,
        "type": promo.type,
        "value": promo.value,
        "message": f"-{promo.value}% sur votre abonnement" if promo.type == "discount" else f"{promo.value} credits offerts"
    }


@payments_router.post("/subscribe")
async def subscribe(
    request: Request,
    plan_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Lire plan_id depuis query param OU body JSON ({ plan: ... } ou { plan_id: ... })
    resolved_plan = plan_id or ""
    promo_code_str = ""
    try:
        raw = await request.body()
        if raw:
            import json as _json
            bdata = _json.loads(raw)
            resolved_plan = bdata.get("plan_id") or bdata.get("plan") or resolved_plan
            promo_code_str = (bdata.get("promo_code") or "").strip().upper()
    except Exception:
        pass
    resolved_plan = (resolved_plan or "").strip()
    if not resolved_plan:
        raise HTTPException(status_code=422, detail="plan_id requis (ex: pro, business, team)")
    plan_id = resolved_plan
    plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan["price"] == 0:
        # Free plan, just update
        await db.execute(update(User).where(User.id == user.id).values(plan=plan_id))
        await db.commit()
        return {"status": "success", "plan": plan_id}

    # TheSustain association members get Pro plan for free
    if user.thesustain_member and user.thesustain_type == "association" and plan_id == "pro":
        await db.execute(update(User).where(User.id == user.id).values(
            plan="pro", credits=max(user.credits, plan["credits_per_month"])
        ))
        await db.commit()
        return {"status": "success", "plan": "pro", "thesustain_free": True}

    try:
        # Apply discount if verified (TheSustain -30%, student -20%, association -30%)
        final_price = plan["price"]
        discount_label = ""
        # #198 — Check discount_expires_at before applying discount
        if user.discount_verified and user.discount_percent > 0:
            discount_expired = user.discount_expires_at and user.discount_expires_at < datetime.now(timezone.utc)
            if not discount_expired:
                final_price = round(plan["price"] * (1 - user.discount_percent / 100), 2)
                discount_label = f" (-{user.discount_percent}%)"

        # Apply promo code discount if provided
        promo_obj = None
        if promo_code_str:
            result = await db.execute(select(PromoCode).where(PromoCode.code == promo_code_str, PromoCode.active == True))
            promo_obj = result.scalar_one_or_none()
            if promo_obj and promo_obj.type == "discount" and promo_obj.current_uses < promo_obj.max_uses:
                if not (promo_obj.expires_at and promo_obj.expires_at < datetime.now(timezone.utc)):
                    existing_use = await db.execute(select(PromoUsage).where(PromoUsage.user_id == user.id, PromoUsage.promo_code_id == promo_obj.id))
                    if not existing_use.scalars().first():
                        promo_discount = promo_obj.value
                        final_price = round(final_price * (1 - promo_discount / 100), 2)
                        discount_label += f" (code -{promo_discount}%)"

        payment = get_mollie_client().payments.create({
            'amount': {
                'currency': 'EUR',
                'value': f'{final_price:.2f}'
            },
            'description': f'Extension IA by Zayado - Abonnement {plan["name"]}{discount_label}',
            'redirectUrl': os.environ.get('APP_BASE_URL', 'https://app.zayado.net') + '/app?payment=success',
            'webhookUrl': os.environ.get('APP_BASE_URL', 'https://app.zayado.net') + '/api/payments/webhook',
            'metadata': {
                'user_id': user.id,
                'plan_id': plan_id,
                'type': 'subscription',
                'credits': plan["credits_per_month"]
            }
        })

        tx = Transaction(
            user_id=user.id, type="subscription",
            package_id=plan_id, amount=plan["price"],
            credits=plan["credits_per_month"], status="pending",
            mollie_payment_id=payment.id,
            checkout_url=payment.checkout_url
        )
        db.add(tx)
        # #22 — Do NOT record promo usage here; do it in webhook when payment confirmed
        # Store promo info in transaction metadata instead
        if promo_obj and promo_obj.type == "discount":
            tx.package_id = f"{plan_id}|promo:{promo_obj.id}"
        await db.commit()

        asyncio.ensure_future(log_event(
            'INFO', 'payment', f'Abonnement initié : plan {plan_id} ({final_price} EUR)',
            action='subscribe', user_id=user.id, user_email=user.email,
            details={'plan_id': plan_id, 'payment_id': payment.id, 'price': final_price, 'promo': promo_code_str or None}
        ))
        return {"status": "redirect", "checkout_url": payment.checkout_url, "payment_id": payment.id}

    except MollieError as e:
        logger.error(f"Mollie error: {str(e)}")
        asyncio.ensure_future(log_event(
            'ERROR', 'payment', f'Erreur Mollie abonnement : {str(e)}',
            action='subscribe_error', user_id=user.id, user_email=user.email,
            details={'plan_id': plan_id, 'error': str(e)}
        ))
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@payments_router.post("/webhook")
async def mollie_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Mollie payment status webhooks with bonus credits system"""
    if not os.environ.get('MOLLIE_API_KEY', ''):
        logger.warning("Webhook reçu mais MOLLIE_API_KEY non configurée — ignoré")
        return {"status": "ignored"}
    try:
        body = await request.form()
        payment_id = body.get("id")
        if not payment_id:
            logger.warning("Webhook received with no payment ID")
            return {"status": "ignored"}

        logger.info(f"Webhook received for payment: {payment_id}")
        mollie_payment = get_mollie_client().payments.get(payment_id)
        metadata = mollie_payment.metadata or {}
        logger.info(f"Webhook: payment {payment_id} status={mollie_payment.status}, metadata={metadata}")

        if mollie_payment.is_paid():
            user_id = metadata.get('user_id')
            credits_to_add = int(metadata.get('credits', 0))
            payment_type = metadata.get('type', '')

            # Fix #40 — Check if transaction already completed to prevent double credit
            from sqlalchemy import update as sql_update
            existing_tx = await db.execute(
                select(Transaction).where(Transaction.mollie_payment_id == payment_id)
            )
            tx = existing_tx.scalar_one_or_none()
            if tx and tx.status == "completed":
                logger.info(f"Webhook: payment {payment_id} already completed — skipping")
                return {"status": "already_processed"}

            # Fallback: get user_id and type from the Transaction record if not in metadata
            if not user_id and tx:
                user_id = tx.user_id
            if not payment_type and tx:
                payment_type = tx.type or ''

            # Resolve guest user → find by email from metadata
            if user_id and user_id.startswith("guest_"):
                email_from_meta = metadata.get('email', '')
                if email_from_meta:
                    real_user = await db.execute(select(User).where(User.email == email_from_meta))
                    real = real_user.scalar_one_or_none()
                    if real:
                        user_id = real.id
                        logger.info(f"Webhook: resolved guest to user {real.email}")

            if payment_type == 'subscription' and user_id:
                plan_id = metadata.get('plan_id', 'free')
                plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == plan_id), None)

                if plan:
                    result = await db.execute(select(User).where(User.id == user_id))
                    u = result.scalar_one_or_none()
                    if u:
                        # Transfer unused BASE credits to bonus (old bonus LOST)
                        bonus_cap = plan.get("bonus_cap", 0)
                        unused_base = u.credits or 0
                        new_bonus = min(unused_base, bonus_cap) if bonus_cap > 0 else 0

                        await db.execute(
                            update(User).where(User.id == user_id).values(
                                plan=plan_id,
                                credits=plan["credits_per_month"],
                                bonus_credits=new_bonus
                            )
                        )
                        from routes.analytics import track_event_standalone
                        await track_event_standalone(user_id, "subscription_upgraded", {"plan": plan_id})
            elif payment_type == 'credits' and user_id and credits_to_add > 0:
                # Credit pack purchase - add to plan credits
                await db.execute(
                    update(User).where(User.id == user_id).values(
                        credits=User.credits + credits_to_add
                    )
                )

            # Update transaction status
            await db.execute(
                sql_update(Transaction).where(Transaction.mollie_payment_id == payment_id).values(status="completed")
            )
            # #22 — Record promo usage ONLY after payment is confirmed
            if tx and tx.package_id and '|promo:' in (tx.package_id or ''):
                promo_id = tx.package_id.split('|promo:')[1]
                try:
                    existing_usage = await db.execute(select(PromoUsage).where(PromoUsage.user_id == user_id, PromoUsage.promo_code_id == promo_id))
                    if not existing_usage.scalars().first():
                        db.add(PromoUsage(user_id=user_id, promo_code_id=promo_id))
                        await db.execute(sql_update(PromoCode).where(PromoCode.id == promo_id).values(current_uses=PromoCode.current_uses + 1))
                except Exception as promo_err:
                    logger.warning(f"Promo usage recording error: {promo_err}")
            await db.commit()

            asyncio.ensure_future(log_event(
                'INFO', 'payment', f'Paiement confirmé : {payment_id} ({payment_type}, {credits_to_add} crédits)',
                action='payment_confirmed', user_id=user_id,
                details={'payment_id': payment_id, 'type': payment_type, 'credits': credits_to_add, 'amount': mollie_payment.amount}
            ))
            # ── Affiliate Commission Hook ──
            try:
                if user_id:
                    user_result = await db.execute(select(User).where(User.id == user_id))
                    buyer = user_result.scalar_one_or_none()
                    if buyer and buyer.referred_by:
                        from routes.affiliate import _get_tier
                        from models import AffiliateCommission
                        # Count affiliate's total sales for tier
                        aff_sales = (await db.execute(
                            select(func.count(AffiliateCommission.id))
                            .where(AffiliateCommission.affiliate_id == buyer.referred_by)
                        )).scalar() or 0
                        tier = _get_tier(aff_sales)
                        sale_amount = float(mollie_payment.amount.get("value", 0))
                        comm_rate = tier.get("commission_rate", 0.10)
                        comm_amount = round(sale_amount * comm_rate, 2)
                        if comm_amount > 0:
                            db.add(AffiliateCommission(
                                affiliate_id=buyer.referred_by,
                                customer_id=user_id,
                                transaction_id=tx.id if tx else None,
                                sale_amount=sale_amount,
                                commission_rate=comm_rate,
                                commission_amount=comm_amount,
                            ))
                            await db.commit()
                            logger.info(f"Affiliate commission: {comm_amount} EUR for affiliate {buyer.referred_by}")
            except Exception as aff_err:
                logger.warning(f"Affiliate commission error: {aff_err}")
                await db.rollback()

            # Send confirmation email with logo
            if user_id:
                result = await db.execute(select(User).where(User.id == user_id))
                u = result.scalar_one_or_none()
                if u:
                    try:
                        bonus_info = ""
                        if payment_type == 'subscription':
                            plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == (metadata.get('plan_id', ''))), None)
                            if plan:
                                bonus_info = f"<p>Credits bonus accumules : <strong>{u.bonus_credits}</strong> (plafond {plan.get('bonus_cap', 0)})</p>"
                        try:
                            import asyncio as _aio
                            import base64 as _b64
                            _em = u.email
                            _nm = u.name
                            # Génère la facture PDF et la joint à l'email (si transaction connue)
                            _attachments = None
                            try:
                                if tx:
                                    _pdf = generate_invoice_pdf(tx, u, plan_name=_plan_name_for(tx.package_id))
                                    _attachments = [{
                                        "content": _b64.b64encode(_pdf).decode("ascii"),
                                        "name": f"Facture_{invoice_number(tx)}.pdf",
                                    }]
                            except Exception as _pdf_err:
                                logger.warning(f"Invoice PDF attach skipped: {_pdf_err}")
                            _html_content = f"""<div style="font-family:Arial;max-width:600px;margin:0 auto;padding:20px;background:#fff;">
                            <div style="text-align:center;padding:20px 0;border-bottom:2px solid #F5F5F0;">
                                <img src="https://app.zayado.net/logo.png" alt="Extension IA by Zayado" style="height:40px;" />
                            </div>
                            <div style="padding:30px 0;">
                                <h1 style="color:#1E3A8A;margin:0 0 15px;">Paiement confirme !</h1>
                                <p style="color:#333;font-size:15px;">Merci {u.name}, votre paiement de <strong>{float(mollie_payment.amount['value']):.2f} EUR</strong> a ete recu.</p>
                                <p style="color:#333;font-size:15px;"><strong>{credits_to_add} credits</strong> ont ete ajoutes a votre compte.</p>
                                <p style="color:#333;font-size:14px;">Votre facture est jointe a cet email (PDF).</p>
                                {bonus_info}
                            </div>
                            <div style="border-top:1px solid #eee;padding:20px 0;text-align:center;color:#999;font-size:12px;">
                                <p>Extension IA by Zayado - Votre assistant IA personnel</p>
                                <p><a href="https://app.zayado.net" style="color:#1E3A8A;">app.zayado.net</a></p>
                            </div>
                            </div>"""
                            _aio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(
                                _em, _nm, "Confirmation de paiement - Extension IA by Zayado", _html_content,
                                attachments=_attachments
                            ))
                        except Exception as _brevo_err:
                            logger.warning(f'Brevo email skipped: {_brevo_err}')
                    except Exception:
                        pass

        elif mollie_payment.is_failed() or mollie_payment.is_expired() or mollie_payment.is_canceled():
            # Update transaction as failed
            from sqlalchemy import update as sql_update
            failed_status = "failed" if mollie_payment.is_failed() else ("expired" if mollie_payment.is_expired() else "canceled")
            await db.execute(
                sql_update(Transaction).where(Transaction.mollie_payment_id == payment_id).values(status=failed_status)
            )
            await db.commit()
            asyncio.ensure_future(log_event(
                'WARNING', 'payment', f'Paiement {failed_status} : {payment_id}',
                action='payment_failed', user_id=metadata.get('user_id'),
                details={'payment_id': payment_id, 'status': failed_status, 'type': metadata.get('type'), 'amount': mollie_payment.amount}
            ))

        logger.info(f"Webhook processed: {payment_id} -> {mollie_payment.status}")
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        try:
            from utils import log_system_event
            log_system_event("webhook_error", f"Mollie webhook: {str(e)[:200]}", "error")
        except Exception:
            pass
        import traceback
        asyncio.ensure_future(log_event(
            'ERROR', 'payment', f'Erreur webhook Mollie : {str(e)}',
            action='webhook_error',
            details={'payment_id': payment_id if 'payment_id' in dir() else None, 'error': str(e), 'traceback': traceback.format_exc()[-1000:]}
        ))
        return {"status": "received"}

@payments_router.post("/verify")
async def verify_payment(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Verify a Mollie payment status and credit user if paid (fallback when webhook is delayed)"""
    try:
        body = await request.json()
        payment_id = body.get("payment_id")
        if not payment_id:
            raise HTTPException(status_code=400, detail="payment_id requis")

        # Check if transaction exists and belongs to this user
        result = await db.execute(
            select(Transaction).where(Transaction.mollie_payment_id == payment_id, Transaction.user_id == user.id)
        )
        tx = result.scalar_one_or_none()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction non trouvée")

        # If already completed, return current credits
        if tx.status == "completed":
            await db.refresh(user)
            total = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
            return {"status": "already_completed", "credits": total, "plan": user.plan}

        # Check with Mollie
        mollie_payment = get_mollie_client().payments.get(payment_id)
        if mollie_payment.is_paid():
            metadata = mollie_payment.metadata or {}
            credits_to_add = int(metadata.get('credits', 0))
            payment_type = metadata.get('type', '')

            if payment_type == 'subscription':
                plan_id = metadata.get('plan_id', 'free')
                plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == plan_id), None)
                if plan:
                    unused_base = user.credits or 0
                    bonus_cap = plan.get("bonus_cap", 0)
                    # Bonus = unused BASE from last month, old bonus LOST
                    new_bonus = min(unused_base, bonus_cap) if bonus_cap > 0 else 0
                    new_bonus = min(new_bonus, bonus_cap)
                    await db.execute(
                        update(User).where(User.id == user.id).values(
                            plan=plan_id, credits=plan["credits_per_month"], bonus_credits=new_bonus,
                            credits_last_reset=datetime.now(timezone.utc)
                        )
                    )
            elif payment_type == 'credits' and credits_to_add > 0:
                await db.execute(
                    update(User).where(User.id == user.id).values(credits=User.credits + credits_to_add)
                )

            from sqlalchemy import update as sql_update
            await db.execute(
                sql_update(Transaction).where(Transaction.mollie_payment_id == payment_id).values(status="completed")
            )
            await db.commit()

            # Refresh user data
            result = await db.execute(select(User).where(User.id == user.id))
            refreshed = result.scalar_one_or_none()
            total = (refreshed.credits or 0) + (refreshed.bonus_credits or 0) + (refreshed.purchased_credits or 0)
            return {"status": "paid", "credits": total, "credits_added": credits_to_add, "plan": refreshed.plan}

        elif mollie_payment.is_pending() or mollie_payment.is_open():
            return {"status": "pending"}
        else:
            return {"status": mollie_payment.status}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@payments_router.post("/sync-pending")
async def sync_pending_payments(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Check all user's pending transactions with Mollie and credit if paid"""
    # #31 — Rate limit sync to prevent abuse (max 3 per minute per user)
    from deps import rate_limiter
    if rate_limiter.is_rate_limited(f"sync_pending:{user.id}", max_attempts=3, window_seconds=60):
        raise HTTPException(status_code=429, detail="Trop de tentatives de synchronisation. Reessayez dans 1 minute.")
    try:
        result = await db.execute(
            select(Transaction).where(
                Transaction.user_id == user.id,
                Transaction.status == "pending"
            ).order_by(Transaction.created_at.desc()).limit(20)
        )
        pending_txs = result.scalars().all()
        
        synced = []
        for tx in pending_txs:
            if not tx.mollie_payment_id:
                continue
            try:
                mollie_payment = get_mollie_client().payments.get(tx.mollie_payment_id)
                if mollie_payment.is_paid():
                    metadata = mollie_payment.metadata or {}
                    credits_to_add = int(metadata.get('credits', tx.credits or 0))
                    payment_type = metadata.get('type', tx.type or '')
                    
                    if payment_type == 'subscription':
                        plan_id = metadata.get('plan_id', 'free')
                        plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == plan_id), None)
                        if plan:
                            await db.execute(
                                update(User).where(User.id == user.id).values(
                                    plan=plan_id, credits=plan["credits_per_month"]
                                )
                            )
                    elif credits_to_add > 0:
                        await db.execute(
                            update(User).where(User.id == user.id).values(
                                credits=User.credits + credits_to_add
                            )
                        )
                    
                    tx.status = "completed"
                    synced.append({"id": tx.mollie_payment_id, "credits": credits_to_add, "type": payment_type})
                elif mollie_payment.is_failed() or mollie_payment.is_expired() or mollie_payment.is_canceled():
                    tx.status = mollie_payment.status
            except Exception as e:
                logger.warning(f"Sync check failed for {tx.mollie_payment_id}: {e}")
        
        await db.commit()
        
        # Return updated user credits
        result = await db.execute(select(User).where(User.id == user.id))
        refreshed = result.scalar_one_or_none()
        total = (refreshed.credits or 0) + (refreshed.bonus_credits or 0) + (refreshed.purchased_credits or 0)
        
        return {
            "synced": len(synced),
            "details": synced,
            "credits": total,
            "plan": refreshed.plan
        }
    except Exception as e:
        logger.error(f"Sync pending error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@payments_router.get("/smart-routing")
async def get_smart_routing_info():
    """Smart Routing: Auto-routes conversations to cheapest appropriate model"""
    return {
        "description": "Smart Routing optimise vos couts automatiquement",
        "routing_rules": [
            {"type": "conversations", "route_to": "Claude", "cost": "2-4 credits", "note": "Optimise"},
            {"type": "automation", "route_to": "Agent", "cost": "60-600 credits", "note": "Tache autonome"}
        ],
        "margin": "78-85% selon le plan",
        "mode_costs": {
            
            "fast": {"cost": 2, "description": "Claude Haiku - reponses rapides"},
            "pro": {"cost": 4, "description": "Claude Sonnet - analyses approfondies"},
            "agent": {"cost": "variable 60-600", "description": "Agent IA - taches autonomes"}
        },
        "dynamic_switching": True,
        "history_transfer": True
    }

# ==================== FACTURATION / INVOICES ====================

def _plan_name_for(package_id: str) -> str:
    pid = (package_id or "").split("|")[0]
    plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == pid), None)
    return plan["name"] if plan else pid.upper()

@payments_router.get("/transactions")
async def list_transactions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Historique de facturation de l'utilisateur (transactions payées)."""
    result = await db.execute(
        select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.created_at.desc()).limit(100)
    )
    txs = result.scalars().all()
    out = []
    for tx in txs:
        ttype = (tx.type or "").lower()
        if ttype == "subscription":
            desc = f"Abonnement {_plan_name_for(tx.package_id)}"
        elif ttype == "credits":
            desc = f"Pack de crédits ({tx.credits or 0} crédits)"
        else:
            desc = (tx.package_id or "Prestation Zayado")
        out.append({
            "id": tx.id,
            "invoice_number": invoice_number(tx),
            "date": tx.created_at.isoformat() if tx.created_at else None,
            "description": desc,
            "amount": float(tx.amount or 0),
            "status": tx.status,
            "type": tx.type,
            "downloadable": tx.status == "completed",
        })
    return out

@payments_router.get("/invoice/{tx_id}")
async def download_invoice(tx_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Télécharge la facture PDF d'une transaction payée appartenant à l'utilisateur."""
    result = await db.execute(
        select(Transaction).where(Transaction.id == tx_id, Transaction.user_id == user.id)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    if tx.status != "completed":
        raise HTTPException(status_code=400, detail="Facture disponible uniquement pour un paiement confirmé")
    try:
        pdf_bytes = generate_invoice_pdf(tx, user, plan_name=_plan_name_for(tx.package_id))
    except Exception as e:
        logger.error(f"Invoice PDF generation error: {e}")
        raise HTTPException(status_code=500, detail="Erreur génération de la facture")
    from io import BytesIO
    fname = f"Facture_{invoice_number(tx)}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )

# ==================== THESUSTAIN SSO ====================

@payments_router.post("/thesustain/link")
async def link_thesustain(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Link TheSustain membership to user account. Applies discount automatically."""
    body = await request.json()
    thesustain_type = body.get("type", "member")  # member or association

    if thesustain_type == "association":
        # Associations via TheSustain get FREE access (Pro plan)
        await db.execute(
            update(User).where(User.id == user.id).values(
                thesustain_member=True,
                thesustain_type="association",
                discount_type="thesustain_association",
                discount_percent=100,
                discount_verified=True,
                plan="pro",
                credits=max(user.credits, 1500)
            )
        )
        await db.commit()
        return {
            "status": "success",
            "type": "association",
            "discount": 100,
            "message": "Acces gratuit au plan Pro active via TheSustain (association)"
        }
    else:
        # TheSustain members get -30% on Pro plan
        await db.execute(
            update(User).where(User.id == user.id).values(
                thesustain_member=True,
                thesustain_type="member",
                discount_type="thesustain",
                discount_percent=30,
                discount_verified=True
            )
        )
        await db.commit()
        return {
            "status": "success",
            "type": "member",
            "discount": 30,
            "message": "Reduction -30% activee automatiquement via TheSustain"
        }

@payments_router.get("/thesustain/status")
async def thesustain_status(user: User = Depends(get_current_user)):
    """Check TheSustain membership status for current user"""
    return {
        "is_member": user.thesustain_member or False,
        "type": user.thesustain_type,
        "discount_percent": user.discount_percent if user.thesustain_member else 0,
        "plan": user.plan
    }

# ==================== ADMIN ROUTES ====================

