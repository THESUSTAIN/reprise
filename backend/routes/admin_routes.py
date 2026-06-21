"""
Admin Routes (users, stats, config, email templates) — extracted from server.py
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
from models import User, Conversation, Project, Workflow, Transaction, PromoCode, PromoUsage, Folder, Team, TeamMember, CreditLog, ApiCost, Referral, Notification, AiFeedback, EmailLog, AdminLog, PlatformSetting, RailwayProject
from deps import get_current_user, get_admin_user, JWT_SECRET, JWT_ALGORITHM, security, hash_password, verify_password
from utils import (
    UPLOADS_DIR, MAMMOTH_BASE_URL, AGENT_DEFAULT_MODEL, AGENT_COMPLEX_MODEL, AGENT_MAX_TIMEOUT,
    AGENT_CREDITS_MAP, classify_task_type, estimate_agent_credits, select_agent_model,
    get_mollie_client, send_brevo_email, send_low_credits_notification,
    load_admin_config, save_admin_config,
    _get_email_log, _append_email_log, _append_admin_log, _get_admin_log,
    EMAIL_TEMPLATES, GENERATED_IMAGES_DIR, CONFIG_PATH, logger as utils_logger,
    CREDIT_PACKAGES, SUBSCRIPTION_PLANS,
)
from mollie.api.client import Client as MollieClient
from mollie.api.error import Error as MollieError

logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).parent

admin_router = APIRouter(tags=["Admin"])
admin_payments_router = APIRouter(tags=["Admin Payments"])
admin_api_router = APIRouter(tags=["Admin Public"])
admin_auth_router = APIRouter(tags=["Admin Auth"])
admin_chat_router = APIRouter(tags=["Admin Chat"])

@admin_router.post("/credits/reset-monthly")
async def admin_force_monthly_credit_reset(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Force monthly credit reset for all paid users (admin only)."""
    now = datetime.now(timezone.utc)
    result = await db.execute(select(User).where(User.plan != "free"))
    users = result.scalars().all()
    reset_count = 0
    for u in users:
        plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == u.plan), None)
        if not plan:
            continue
        cpm = plan.get("credits_per_month", 0)
        bonus_cap = plan.get("bonus_cap", 0)
        unused_base = u.credits or 0
        new_bonus = min(unused_base, bonus_cap) if bonus_cap > 0 else 0
        await db.execute(
            update(User).where(User.id == u.id).values(
                credits=cpm, bonus_credits=new_bonus, credits_last_reset=now
            )
        )
        reset_count += 1
    await db.commit()
    return {"status": "ok", "reset_count": reset_count, "reset_at": now.isoformat()}

# Stats cache — 5 min TTL
_stats_cache = {"data": None, "ts": 0}
_STATS_CACHE_TTL = 300  # 5 minutes

@admin_router.post("/stats/refresh")
async def refresh_admin_stats_cache(admin: User = Depends(get_admin_user)):
    """Force invalidation of the stats cache (admin only)."""
    _stats_cache["data"] = None
    _stats_cache["ts"] = 0
    return {"status": "cache_cleared"}

@admin_router.get("/stats")
async def get_admin_stats(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    import time
    now = time.time()
    if _stats_cache["data"] and (now - _stats_cache["ts"]) < _STATS_CACHE_TTL:
        return _stats_cache["data"]
    
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Active users: use last_login_at if available, fallback to updated_at
    try:
        active_users = (await db.execute(
            select(func.count(User.id)).where(User.updated_at >= week_ago)
        )).scalar() or 0
    except Exception:
        active_users = 0

    total_conversations = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    new_users_7d = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )).scalar() or 0
    new_users_30d = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= month_ago)
    )).scalar() or 0
    new_users_today = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= today)
    )).scalar() or 0

    # Revenue from transactions (safe — table may be empty)
    total_revenue = 0
    revenue_30d = 0
    revenue_7d = 0
    pending_revenue = 0
    try:
        total_revenue = (await db.execute(
            select(func.sum(Transaction.amount)).where(Transaction.status == "completed")
        )).scalar() or 0
        revenue_30d = (await db.execute(
            select(func.sum(Transaction.amount)).where(Transaction.status == "completed", Transaction.created_at >= month_ago)
        )).scalar() or 0
        revenue_7d = (await db.execute(
            select(func.sum(Transaction.amount)).where(Transaction.status == "completed", Transaction.created_at >= week_ago)
        )).scalar() or 0
        pending_revenue = (await db.execute(
            select(func.sum(Transaction.amount)).where(Transaction.status == "pending")
        )).scalar() or 0
    except Exception as e:
        logger.warning(f"Could not compute revenue: {e}")

    # Plans distribution
    plans_distribution = {"free": 0}
    try:
        plans_result = await db.execute(
            select(User.plan, func.count(User.id)).group_by(User.plan)
        )
        plans_distribution = {row[0] or "free": row[1] for row in plans_result.all()}
    except Exception as e:
        logger.warning(f"Could not compute plans_distribution: {e}")

    # Daily signups for last 7 days
    daily_signups = []
    try:
        week_start = (datetime.now(timezone.utc) - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        signup_result = await db.execute(
            select(func.date(User.created_at), func.count(User.id))
            .where(User.created_at >= week_start)
            .group_by(func.date(User.created_at))
        )
        signup_data = {str(row[0]): row[1] for row in signup_result.all()}
        for i in range(6, -1, -1):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).date()
            daily_signups.append({"date": day.strftime("%d/%m"), "count": signup_data.get(str(day), 0)})
    except Exception as e:
        logger.warning(f"Could not compute daily_signups: {e}")

    # Total credits in circulation (sum of credits remaining on all accounts)
    total_credits_distributed = (await db.execute(select(func.sum(User.credits)))).scalar() or 0

    # FIX #CREDITS — Total credits spent: primary source = credit_logs (most reliable)
    # Falls back to Conversation.total_credits_used if credit_logs table is empty
    total_credits_spent = 0
    try:
        cl_spent = (await db.execute(
            select(func.sum(func.abs(CreditLog.amount)))
            .where(CreditLog.log_type == "chat_deduction")
        )).scalar() or 0
        if cl_spent > 0:
            total_credits_spent = int(cl_spent)
        else:
            # Fallback: sum from conversations
            conv_spent = (await db.execute(
                select(func.sum(Conversation.total_credits_used))
            )).scalar() or 0
            total_credits_spent = int(conv_spent)
    except Exception as e:
        logger.warning(f"Could not compute total_credits_spent: {e}")
        try:
            conv_spent = (await db.execute(
                select(func.sum(Conversation.total_credits_used))
            )).scalar() or 0
            total_credits_spent = int(conv_spent)
        except Exception:
            total_credits_spent = 0

    # Conversion rate: paid users / total users
    paid_users = sum(v for k, v in plans_distribution.items() if k not in ['free', None, ''])
    conversion_rate = round((paid_users / max(total_users, 1)) * 100, 1)

    # Credits by mode from credit_logs (persistent even if conversations deleted)
    credits_by_mode_data = {"fast": 0, "pro": 0, "agent": 0, "gemini": 0, "grok": 0, "perplexity": 0, "image": 0}
    try:
        mode_credits_result = await db.execute(
            select(CreditLog.mode, func.sum(func.abs(CreditLog.amount)))
            .where(CreditLog.log_type == "chat_deduction")
            .group_by(CreditLog.mode)
        )
        for row in mode_credits_result.all():
            if row[0] and row[0] in credits_by_mode_data:
                credits_by_mode_data[row[0]] = int(row[1] or 0)
    except Exception as e:
        logger.warning(f"Could not compute credits_by_mode: {e}")

    # Total API costs (safe — table may not exist yet)
    total_api_cost = 0.0
    api_cost_30d = 0.0
    try:
        total_api_cost = (await db.execute(select(func.sum(ApiCost.estimated_cost_eur)))).scalar() or 0.0
        api_cost_30d = (await db.execute(
            select(func.sum(ApiCost.estimated_cost_eur)).where(ApiCost.created_at >= month_ago)
        )).scalar() or 0.0
    except Exception as e:
        logger.warning(f"Could not compute api_costs: {e}")

    # FIX #CACHE — Build result dict ONCE, cache it, then return
    result = {
        "total_users": total_users,
        "active_users_7d": active_users,
        "new_users_today": new_users_today,
        "new_users_7d": new_users_7d,
        "new_users_30d": new_users_30d,
        "total_conversations": total_conversations,
        "total_messages": total_conversations,
        "total_revenue": total_revenue,
        "revenue_30d": revenue_30d,
        "revenue_7d": revenue_7d,
        "pending_revenue": pending_revenue,
        "total_agent_tasks": 0,
        "plans_distribution": plans_distribution,
        "credits_by_mode": credits_by_mode_data,
        "daily_signups": daily_signups,
        "total_credits_in_circulation": total_credits_distributed,
        "total_credits_spent": total_credits_spent,
        "conversion_rate": conversion_rate,
        "paid_users": paid_users,
        "total_api_cost": round(float(total_api_cost), 4),
        "api_cost_30d": round(float(api_cost_30d), 4),
        "margin_30d": round(float(revenue_30d) - float(api_cost_30d), 2),
    }
    _stats_cache["data"] = result
    _stats_cache["ts"] = now
    return result

@admin_router.get("/users")
async def get_admin_users(
    admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
    skip: int = 0, limit: int = 20, search: str = None,
    plan: str = None, role: str = None, sort: str = "newest"
):
    query = select(User)
    if search:
        query = query.where(
            (User.email.contains(search)) | (User.name.contains(search))
        )
    if plan:
        query = query.where(User.plan == plan)
    if role:
        query = query.where(User.role == role)
    # Count total for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    # Sort
    if sort == "oldest":
        query = query.order_by(User.created_at.asc())
    elif sort == "credits_desc":
        query = query.order_by(User.credits.desc())
    elif sort == "credits_asc":
        query = query.order_by(User.credits.asc())
    else:
        query = query.order_by(User.created_at.desc())
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id, "email": u.email, "name": u.name,
                "role": u.role, "credits": u.credits, "plan": u.plan,
                "bonus_credits": u.bonus_credits or 0,
                "discount_type": u.discount_type,
                "discount_percent": u.discount_percent or 0,
                "discount_verified": u.discount_verified if u.discount_verified is not None else False,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
            }
            for u in users
        ],
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit
    }

@admin_router.post("/users/{user_id}/credits")
async def gift_credits(user_id: str, data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    credits = int(data.get("credits", 0))
    if credits <= 0:
        raise HTTPException(status_code=400, detail="Credits must be positive")
    result = await db.execute(
        update(User).where(User.id == user_id).values(credits=User.credits + credits)
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    # Log the gift
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    # Log in credit_logs for permanent tracking
    db.add(CreditLog(
        team_id=getattr(target_user, 'team_id', None) if target_user else None,
        user_id=user_id,
        amount=credits,
        log_type="gift",
        description=f"Admin {admin.email} offert {credits} credits"
    ))
    await db.commit()
    _append_admin_log({
        "action": "credit_gift",
        "user_id": user_id,
        "user_email": target_user.email if target_user else user_id,
        "user_name": target_user.name if target_user else user_id,
        "new_value": f"+{credits} credits",
        "admin_email": admin.email,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "credits_added", "credits": credits}

@admin_router.post("/users/{user_id}/ban")
async def ban_user(user_id: str, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        update(User).where(User.id == user_id).values(role="banned")
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    _append_admin_log({
        "action": "ban_user",
        "user_id": user_id,
        "user_email": target_user.email if target_user else user_id,
        "user_name": target_user.name if target_user else user_id,
        "admin_email": admin.email,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "banned"}

@admin_router.get("/transactions")
async def get_admin_transactions(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Transaction).order_by(Transaction.created_at.desc()).limit(100)
    )
    txs = result.scalars().all()

    user_ids = list(set(tx.user_id for tx in txs if tx.user_id))
    users_map = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in users_result.scalars().all():
            users_map[u.id] = u.email

    return [
        {
            "id": tx.id, "user_id": tx.user_id, "type": tx.type,
            "package_id": tx.package_id,
            "amount": tx.amount, "credits": tx.credits, "status": tx.status,
            "mollie_payment_id": tx.mollie_payment_id,
            "user_email": users_map.get(tx.user_id, tx.user_id),
            "checkout_url": tx.checkout_url if tx.status == "pending" else None,
            "created_at": tx.created_at.isoformat()
        }
        for tx in txs
    ]

@admin_router.put("/users/{user_id}")
async def update_admin_user(user_id: str, data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    allowed_fields = ["credits", "plan", "role", "partner_url", "has_support_humain", "bonus_credits"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    result = await db.execute(update(User).where(User.id == user_id).values(**update_data))
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "updated"}

@admin_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Update a user's role (super_admin, admin, support, analyst, user)."""
    role = data.get("role", "user")
    valid_roles = ["super_admin", "admin", "support", "analyst", "user", "partenaire", "presta-partenaire", "etudiant"]
    if role not in valid_roles:
        raise HTTPException(400, f"Role invalide. Valeurs autorisees: {', '.join(valid_roles)}")
    result = await db.execute(update(User).where(User.id == user_id).values(role=role))
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, "Utilisateur non trouve")
    return {"status": "ok", "role": role}

@admin_router.delete("/users/{user_id}")
async def delete_admin_user(user_id: str, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted"}

# ==================== BILLING ROUTES ====================

@admin_payments_router.get("/billing")
async def get_billing_info(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get user billing dashboard data"""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
    )
    txs = result.scalars().all()
    plan_info = next((p for p in SUBSCRIPTION_PLANS if p["id"] == (user.plan or "free")), SUBSCRIPTION_PLANS[0])

    tx_list = []
    for tx in txs:
        tx_data = {
            "id": tx.id,
            "type": tx.type,
            "amount": tx.amount,
            "credits": tx.credits,
            "status": tx.status,
            "mollie_payment_id": tx.mollie_payment_id,
            "checkout_url": None,
            "created_at": tx.created_at.isoformat()
        }
        # Get checkout URL for pending payments from Mollie
        if tx.status == "pending" and tx.mollie_payment_id:
            try:
                mp = get_mollie_client().payments.get(tx.mollie_payment_id)
                tx_data["checkout_url"] = mp.checkout_url if hasattr(mp, 'checkout_url') else mp.get("_links", {}).get("checkout", {}).get("href")
            except Exception:
                pass
        tx_list.append(tx_data)

    return {
        "plan": user.plan or "free",
        "plan_name": plan_info["name"],
        "plan_price": plan_info["price"],
        "credits": user.credits,
        "bonus_credits": user.bonus_credits or 0,
        "bonus_cap": plan_info.get("bonus_cap", 0),
        "credits_per_month": plan_info.get("credits_per_month", 0),
        "email": user.email,
        "name": user.name,
        "transactions": tx_list
    }

# ==================== PROMO CODE ROUTES ====================

@admin_router.post("/promo-codes")
async def create_promo_code(data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    code = data.get("code", "").strip().upper()
    promo_type = data.get("type", "credits")
    value = int(data.get("value", 0))
    max_uses = int(data.get("max_uses", 100))
    expires_at_str = data.get("expires_at")

    if not code or value <= 0:
        raise HTTPException(status_code=400, detail="Code and value are required")

    existing = await db.execute(select(PromoCode).where(PromoCode.code == code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Code already exists")

    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except ValueError:
            pass

    promo = PromoCode(code=code, type=promo_type, value=value, max_uses=max_uses, expires_at=expires_at)
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return {"id": promo.id, "code": promo.code, "type": promo.type, "value": promo.value, "max_uses": promo.max_uses, "current_uses": 0, "active": True}

@admin_router.get("/promo-codes")
async def list_promo_codes(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))
    return [
        {"id": p.id, "code": p.code, "type": p.type, "value": p.value, "max_uses": p.max_uses, "current_uses": p.current_uses, "active": p.active, "expires_at": p.expires_at.isoformat() if p.expires_at else None, "created_at": p.created_at.isoformat()}
        for p in result.scalars().all()
    ]

@admin_router.put("/promo-codes/{promo_id}")
async def toggle_promo_code(promo_id: str, data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await db.execute(update(PromoCode).where(PromoCode.id == promo_id).values(active=data.get("active", False)))
    await db.commit()
    return {"status": "updated"}

@admin_router.delete("/promo-codes/{promo_id}")
async def delete_promo_code(promo_id: str, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(PromoCode).where(PromoCode.id == promo_id))
    await db.commit()
    return {"status": "deleted"}

# ==================== MAINTENANCE MODE ====================
@admin_router.post("/maintenance/toggle")
async def toggle_maintenance(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Toggle maintenance mode for /chat"""
    config = load_admin_config()
    config["maintenance_mode"] = data.get("enabled", False)
    config["maintenance_newsletter"] = data.get("newsletter", True)
    save_admin_config(config)
    return {"status": "ok", "maintenance_mode": config["maintenance_mode"]}

@admin_api_router.post("/newsletter/subscribe")
async def subscribe_newsletter(data: Dict[str, Any]):
    """Subscribe to newsletter (maintenance page)"""
    email = data.get("email", "").strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email invalide")
    # Store in DB or send to Brevo
    brevo_key = os.environ.get("BREVO_API_KEY")
    if brevo_key:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://api.brevo.com/v3/contacts",
                    headers={"api-key": brevo_key, "Content-Type": "application/json"},
                    json={"email": email, "listIds": [2], "updateEnabled": True}
                )
        except Exception as e:
            logger.warning(f"Brevo newsletter error: {e}")
    return {"status": "ok", "message": "Inscription confirmee"}


# Admin API test endpoint
@admin_router.post("/test-api")
async def test_api_key(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Test an API key to check if it's valid"""
    api_name = data.get("api", "")
    result = {"api": api_name, "status": "error", "message": "API inconnue"}

    try:
        if api_name == "anthropic":
            # Test Claude via Mammoth IA
            key = os.environ.get("MAMMOTH_API_KEY", "")
            if not key:
                return {"api": api_name, "status": "error", "message": "IA non configuree"}
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post("https://api.mammouth.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": "claude-haiku-4-5-20251001", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]})
            if resp.status_code == 200:
                result = {"api": api_name, "status": "ok", "message": "Claude via Zayado IA OK"}
            else:
                result = {"api": api_name, "status": "error", "message": f"Erreur {resp.status_code}: {resp.text[:100]}"}

        elif api_name == "mollie":
            key = os.environ.get("MOLLIE_API_KEY", "")
            if not key:
                return {"api": api_name, "status": "error", "message": "Cle non configuree"}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://api.mollie.com/v2/methods",
                    headers={"Authorization": f"Bearer {key}"})
            result = {"api": api_name, "status": "ok" if resp.status_code == 200 else "error",
                      "message": "Mollie OK" if resp.status_code == 200 else f"Erreur {resp.status_code}"}

        elif api_name == "brevo":
            key = os.environ.get("BREVO_API_KEY", "")
            if not key:
                return {"api": api_name, "status": "error", "message": "Cle non configuree"}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://api.brevo.com/v3/account",
                    headers={"api-key": key})
            result = {"api": api_name, "status": "ok" if resp.status_code == 200 else "error",
                      "message": "Brevo OK" if resp.status_code == 200 else f"Erreur {resp.status_code}"}

    except httpx.TimeoutException:
        result = {"api": api_name, "status": "error", "message": "Timeout - API ne repond pas"}
    except Exception as e:
        result = {"api": api_name, "status": "error", "message": str(e)[:100]}

    return result

# Admin config save endpoint
@admin_router.put("/config")
async def update_admin_config(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Save admin configuration (social links, demo URL, etc.)"""
    try:
        existing = load_admin_config()
        existing.update(data)
        save_admin_config(existing)
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/regenerate-previews")
async def regenerate_previews(admin: User = Depends(get_admin_user)):
    """Regenerate all HTML preview files from PHP templates using current admin config."""
    import subprocess
    try:
        result = subprocess.run(
            ["python3", "/app/scripts/generate_previews.py"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            count = len([l for l in lines if l.strip().startswith('OK')])
            return {"status": "ok", "message": f"{count} pages régénérées", "output": result.stdout[-500:]}
        else:
            return {"status": "error", "message": result.stderr[-500:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/config")
async def get_admin_config(admin: User = Depends(get_admin_user)):
    """Get admin configuration"""
    return load_admin_config()

@admin_router.get("/pricing")
async def get_admin_pricing(admin: User = Depends(get_admin_user)):
    """Get current pricing configuration"""
    custom = load_admin_config()
    return {
        "plans": custom.get("plans", SUBSCRIPTION_PLANS),
        "packages": custom.get("packages", CREDIT_PACKAGES)
    }

@admin_router.put("/pricing")
async def update_admin_pricing(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Update pricing plans and credit packages"""
    existing = load_admin_config()

    if "plans" in data:
        existing["plans"] = data["plans"]
        global SUBSCRIPTION_PLANS
        SUBSCRIPTION_PLANS = data["plans"]
    if "packages" in data:
        existing["packages"] = data["packages"]
        global CREDIT_PACKAGES
        CREDIT_PACKAGES = data["packages"]

    save_admin_config(existing)
    return {"status": "saved"}



@admin_payments_router.post("/redeem-promo")
async def redeem_promo(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    code_str = data.get("code", "").strip().upper()
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

    if promo.type == "credits":
        await db.execute(update(User).where(User.id == user.id).values(credits=User.credits + promo.value))

    db.add(PromoUsage(user_id=user.id, promo_code_id=promo.id))
    await db.execute(update(PromoCode).where(PromoCode.id == promo.id).values(current_uses=PromoCode.current_uses + 1))
    await db.commit()

    return {"status": "success", "message": f"{promo.value} credits ajoutes !", "credits_added": promo.value if promo.type == "credits" else 0}

# ==================== REFERRAL SYSTEM ====================

@admin_auth_router.post("/2fa/toggle")
async def toggle_user_2fa(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Toggle 2FA for a regular user."""
    enabled = data.get("enabled", False)
    await db.execute(update(User).where(User.id == user.id).values(two_factor_enabled=enabled))
    await db.commit()
    return {"status": "ok", "two_factor_enabled": enabled}

@admin_auth_router.get("/referral")
async def get_referral_info(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get user's referral code and stats."""
    if not user.referral_code:
        code = f"ZAY{user.id[:6].upper()}"
        await db.execute(update(User).where(User.id == user.id).values(referral_code=code))
        await db.commit()
        user.referral_code = code
    # Count referrals
    result = await db.execute(select(func.count()).select_from(User).where(User.referred_by == user.id))
    count = result.scalar() or 0
    return {
        "referral_code": user.referral_code,
        "referral_link": f"https://app.zayado.net/register?ref={user.referral_code}",
        "total_referrals": count,
        "credits_per_referral": 300
    }

@admin_auth_router.post("/referral/apply")
async def apply_referral(data: Dict[str, str], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Apply a referral code to current user. Uses SELECT FOR UPDATE to prevent race conditions (#22)."""
    code = data.get("code", "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Code requis")
    # Re-fetch user with lock to prevent double-apply race condition
    result = await db.execute(select(User).where(User.id == user.id).with_for_update())
    fresh_user = result.scalar_one_or_none()
    if not fresh_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if fresh_user.referred_by:
        raise HTTPException(status_code=400, detail="Vous avez deja utilise un code de parrainage")
    result = await db.execute(select(User).where(User.referral_code == code))
    referrer = result.scalar_one_or_none()
    if not referrer or referrer.id == fresh_user.id:
        raise HTTPException(status_code=404, detail="Code de parrainage invalide")
    # Credit both users atomically
    await db.execute(update(User).where(User.id == fresh_user.id).values(referred_by=referrer.id, credits=User.credits + 100))
    await db.execute(update(User).where(User.id == referrer.id).values(credits=User.credits + 300))
    await db.commit()

    # Send notification emails via Brevo
    _config = load_admin_config()
    brevo_key = _config.get("brevo_api_key") or os.environ.get("BREVO_API_KEY")
    if brevo_key:
        try:
            for target_email, subject, msg in [
                (user.email, "Parrainage active !", f"Vous avez utilise le code de parrainage de {referrer.email}. 100 credits de bienvenue ont ete ajoutes a votre compte !"),
                (referrer.email, "Nouveau filleul !", f"{user.email} a utilise votre code de parrainage. 300 credits ont ete ajoutes a votre compte !"),
            ]:
                async with httpx.AsyncClient() as client:
                    await client.post("https://api.brevo.com/v3/smtp/email", headers={"api-key": brevo_key, "Content-Type": "application/json"},
                        json={"sender": {"name": "Zayado", "email": "noreply@zayado.net"}, "to": [{"email": target_email}], "subject": subject,
                              "htmlContent": f"<div style='font-family:sans-serif;max-width:500px;margin:0 auto;padding:30px;'><h2 style='color:#1E3A8A;'>{subject}</h2><p>{msg}</p></div>"})
        except Exception as e:
            logger.error(f"Brevo referral email error: {e}")

    # In-app notifications (logged only — no MongoDB in this app, fix #88/#183)
    logger.info(f"Referral notification: user={user.id} +100 credits, referrer={referrer.id} +300 credits")

    return {"status": "success", "message": "100 credits offerts + 300 credits pour votre parrain !"}

# ==================== PARTNER DASHBOARD ====================

@admin_auth_router.get("/partner/stats")
async def get_partner_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get partner dashboard statistics."""
    if user.role not in ("partenaire", "presta-partenaire", "admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Acces reserve aux partenaires")

    # Ensure referral code exists
    if not user.referral_code:
        code = f"ZAY{user.id[:6].upper()}"
        await db.execute(update(User).where(User.id == user.id).values(referral_code=code))
        await db.commit()
        user.referral_code = code

    # Count total referrals
    result = await db.execute(select(func.count()).select_from(User).where(User.referred_by == user.id))
    total_referrals = result.scalar() or 0

    # Get referred users with their plan info
    result = await db.execute(
        select(User.id, User.email, User.name, User.plan, User.credits, User.created_at)
        .where(User.referred_by == user.id)
        .order_by(User.created_at.desc())
    )
    referred_users = []
    paying_users = 0
    for row in result.fetchall():
        is_paying = row.plan and row.plan not in ("free", "gratuit", "")
        if is_paying:
            paying_users += 1
        referred_users.append({
            "id": row.id,
            "email": row.email[:3] + "***@" + row.email.split("@")[-1] if row.email else "",
            "name": row.name,
            "plan": row.plan or "free",
            "is_paying": is_paying,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    # Calculate estimated revenue from referrals (commission model)
    # Count transactions from referred users
    referred_ids = [u["id"] for u in referred_users]
    total_revenue = 0.0
    if referred_ids:
        result = await db.execute(
            select(func.sum(Transaction.amount))
            .where(Transaction.user_id.in_(referred_ids))
            .where(Transaction.status == "completed")
        )
        total_revenue = result.scalar() or 0.0

    commission_rate = 0.10  # 10% commission
    estimated_commission = round(total_revenue * commission_rate, 2)

    # Monthly breakdown (last 6 months)
    monthly_data = []
    now = datetime.now(timezone.utc)
    for i in range(6):
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            for _ in range(i):
                month_start = (month_start - timedelta(days=1)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)

        month_referrals = sum(1 for u in referred_users if u["created_at"] and month_start.isoformat() <= u["created_at"] < month_end.isoformat())
        monthly_data.append({
            "month": month_start.strftime("%Y-%m"),
            "label": month_start.strftime("%b %Y"),
            "referrals": month_referrals,
        })

    monthly_data.reverse()

    return {
        "referral_code": user.referral_code,
        "referral_link": f"https://app.zayado.net/register?ref={user.referral_code}",
        "partner_url": user.partner_url or "",
        "total_referrals": total_referrals,
        "paying_users": paying_users,
        "conversion_rate": round((paying_users / total_referrals * 100) if total_referrals > 0 else 0, 1),
        "total_revenue": round(total_revenue, 2),
        "estimated_commission": estimated_commission,
        "commission_rate": commission_rate,
        "credits_earned": total_referrals * 300,
        "referred_users": referred_users[:20],
        "monthly_data": monthly_data,
    }

@admin_auth_router.put("/partner/url")
async def update_partner_url(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Allow partner to update their partner_url."""
    if user.role not in ("partenaire", "presta-partenaire", "admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Acces reserve aux partenaires")
    url = data.get("partner_url", "").strip()
    await db.execute(update(User).where(User.id == user.id).values(partner_url=url))
    await db.commit()
    return {"status": "ok", "partner_url": url}

# ==================== EXPORT PDF ====================

@admin_chat_router.get("/conversations/{conv_id}/export-pdf")
async def export_conversation_pdf(conv_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Export a conversation as a downloadable HTML (print-ready for PDF)."""
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")

    msgs = conv.messages or []
    mode_labels = {"fast": "IA Rapide", "pro": "IA Avancee", "agent": "Agent IA", "gemini": "Gemini", "grok": "Grok", "perplexity": "Perplexity", "image": "Image IA"}
    mode_name = mode_labels.get(conv.mode, conv.mode)
    date_str = conv.created_at.strftime("%d/%m/%Y %H:%M") if conv.created_at else ""

    messages_html = ""
    for m in msgs:
        role_label = "Vous" if m.get("role") == "user" else "Zayado Extension IA by Zayado"
        bg = "#F5F5F0" if m.get("role") == "user" else "#E8F4F8"
        content = (m.get("content") or "").replace("\n", "<br>")
        messages_html += f'<div style="background:{bg};padding:12px 16px;border-radius:12px;margin-bottom:8px;"><strong style="color:#1E3A8A;">{role_label}</strong><p style="margin:4px 0 0;color:#333;">{content}</p></div>'

    html_content = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>{conv.title or "Conversation"} - Zayado</title>
    <style>body{{font-family:'Segoe UI',system-ui,sans-serif;max-width:700px;margin:0 auto;padding:40px 20px;color:#1a1a2e;}}
    .header{{border-bottom:2px solid #1E3A8A;padding-bottom:16px;margin-bottom:24px;}}
    h1{{color:#1E3A8A;font-size:24px;margin:0;}} .meta{{color:#6b7280;font-size:13px;margin-top:4px;}}
    @media print{{body{{padding:20px;}}}} @page{{margin:1.5cm;}}</style></head>
    <body><div class="header"><h1>{conv.title or "Conversation Zayado"}</h1>
    <div class="meta">{mode_name} &middot; {date_str} &middot; {len(msgs)} messages</div></div>
    {messages_html}
    <div style="text-align:center;padding:20px;color:#9ca3af;font-size:12px;border-top:1px solid #e5e5e5;margin-top:24px;">
    Exporté depuis Extension IA by Zayado &middot; app.zayado.net</div></body></html>"""

    return StreamingResponse(
        iter([html_content]),
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="zayado-{conv_id[:8]}.html"'}
    )

# ==================== SUPPORT HUMAIN ====================

@admin_chat_router.get("/support-status")
async def get_support_status(user: User = Depends(get_current_user)):
    """Check if user has human support enabled."""
    user_settings = user.settings or {}
    has_support = user_settings.get("has_support_humain", False) if isinstance(user_settings, dict) else False
    return {"has_support_humain": has_support, "plan": user.plan}

@admin_chat_router.post("/support-humain/toggle")
async def toggle_support_humain(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Toggle human support mode (only for eligible users)."""
    user_settings = user.settings or {}
    if not isinstance(user_settings, dict):
        user_settings = {}
    has_support = user_settings.get("has_support_humain", False)
    if not has_support:
        raise HTTPException(status_code=403, detail="Le support humain n'est pas inclus dans votre forfait. Rendez-vous sur zayado.net pour souscrire.")
    is_active = user_settings.get("support_humain_active", False)
    user_settings["support_humain_active"] = not is_active
    await db.execute(update(User).where(User.id == user.id).values(settings=user_settings))
    await db.commit()
    return {"support_humain_active": not is_active, "message": "Support humain active" if not is_active else "Support humain desactive"}

@admin_chat_router.post("/support-humain/request")
async def request_support_humain(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Submit a human support request with chat context."""
    user_settings = user.settings or {}
    if not isinstance(user_settings, dict):
        user_settings = {}
    has_support = user_settings.get("has_support_humain", False)
    if not has_support:
        raise HTTPException(status_code=403, detail="Le support humain n'est pas inclus dans votre forfait.")
    # Log the support request
    _append_admin_log({
        "action": "support_request",
        "user_id": user.id,
        "user_email": user.email,
        "user_name": user.name or user.email,
        "new_value": f"Conv: {data.get('conversation_id', 'N/A')} | Mode: {data.get('mode', 'N/A')} | Msgs: {data.get('messages_count', 0)}",
        "old_value": data.get("message", ""),
        "admin_email": "-",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    # Mark support as active
    user_settings["support_humain_active"] = True
    await db.execute(update(User).where(User.id == user.id).values(settings=user_settings))
    await db.commit()
    return {"status": "sent", "message": "Demande de support envoyee"}

# ==================== ADMIN: BREVO & LIMITS ====================

@admin_router.get("/brevo-config")
async def get_brevo_config(admin: User = Depends(get_admin_user)):
    """Get Brevo email configuration (editable by admin)."""
    config = load_admin_config()
    brevo = config.get("brevo", {})
    return {
        "sender_email": brevo.get("sender_email", "noreply@zayado.net"),
        "sender_name": brevo.get("sender_name", "Extension IA by Zayado"),
        "welcome_enabled": brevo.get("welcome_enabled", True),
        "purchase_enabled": brevo.get("purchase_enabled", True),
        "manus_notify_enabled": brevo.get("manus_notify_enabled", True),
        "low_credit_enabled": brevo.get("low_credit_enabled", True),
        "project_report_enabled": brevo.get("project_report_enabled", True),
    }

@admin_router.put("/brevo-config")
async def update_brevo_config(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Update Brevo email configuration."""
    config = load_admin_config()
    config["brevo"] = data
    save_admin_config(config)
    return {"status": "saved"}

@admin_router.get("/limits")
async def get_limits(admin: User = Depends(get_admin_user)):
    """Get system limits (editable by admin)."""
    config = load_admin_config()
    limits = config.get("limits", {})
    return {
        "max_messages_day_free": limits.get("max_messages_day_free", 100),
        "max_projects": limits.get("max_projects", 50),
        "max_workflows": limits.get("max_workflows", 20),
        "max_manus_concurrent": limits.get("max_manus_concurrent", 3),
        "rate_limit_per_min": limits.get("rate_limit_per_min", 60),
        "support_humain_credits": limits.get("support_humain_credits", 1000),
    }

@admin_router.put("/limits")
async def update_limits(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Update system limits."""
    config = load_admin_config()
    config["limits"] = data
    save_admin_config(config)
    return {"status": "saved"}

@admin_router.get("/sidebar-redirects")
async def get_sidebar_redirects(admin: User = Depends(get_admin_user)):
    """Get configurable sidebar redirect buttons."""
    config = load_admin_config()
    return config.get("sidebar_redirects", {
        "support_ia": {"label": "Support IA", "url": "https://zayado.net", "enabled": True},
        "ressource": {"label": "Ressource", "url": "https://zayado.net", "enabled": True},
        "service": {"label": "Service", "url": "https://zayado.net", "enabled": True},
    })

@admin_router.put("/sidebar-redirects")
async def update_sidebar_redirects(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Update configurable sidebar redirect buttons."""
    config = load_admin_config()
    config["sidebar_redirects"] = data
    save_admin_config(config)
    return {"status": "saved"}


@admin_router.get("/mega-menu")
async def get_mega_menu_config(admin: User = Depends(get_admin_user)):
    """Get configurable mega menu items (names + URLs)."""
    config = load_admin_config()
    return config.get("mega_menu", {
        "items": [
            {"key": "jeMeLance", "label": "Je me lance", "url": "https://zayado.net/je-me-lance", "enabled": True},
            {"key": "jePilote", "label": "Je pilote", "url": "https://zayado.net/je-pilote", "enabled": True},
            {"key": "jeGrandis", "label": "Je grandis", "url": "https://zayado.net/je-grandis", "enabled": True},
            {"key": "boutique", "label": "Boutique", "url": "https://zayado.net/boutique", "enabled": True},
            {"key": "contact", "label": "Contact", "url": "https://zayado.net/contact", "enabled": True},
        ]
    })

@admin_router.put("/mega-menu")
async def update_mega_menu_config(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Update mega menu items (names + URLs)."""
    config = load_admin_config()
    config["mega_menu"] = data
    save_admin_config(config)
    return {"status": "saved"}



@admin_router.put("/users/{user_id}/support")
async def toggle_user_support(user_id: str, data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Enable/disable human support for a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user_settings = target.settings or {}
    if not isinstance(user_settings, dict):
        user_settings = {}
    user_settings["has_support_humain"] = data.get("enabled", False)
    await db.execute(update(User).where(User.id == user_id).values(settings=user_settings))
    await db.commit()
    return {"status": "success"}

@admin_router.put("/users/{user_id}/plan")
async def change_user_plan(user_id: str, data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Change a user's plan and log the modification."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    old_plan = target.plan or 'free'
    new_plan = data.get("plan", "free")
    await db.execute(update(User).where(User.id == user_id).values(plan=new_plan))
    await db.commit()
    # Log modification
    _append_admin_log({
        "action": "plan_change",
        "user_id": user_id,
        "user_email": target.email,
        "user_name": target.name or target.email,
        "old_value": old_plan,
        "new_value": new_plan,
        "admin_email": admin.email,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "success"}

# ==================== SEO & BRANDING CONFIG ====================

DEFAULT_SEO_CONFIG = {
    "logo_url": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='12' fill='%231E3A8A'/%3E%3Cpath d='M12 14h24l-14 20h14' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E",
    "favicon_url": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='12' fill='%231E3A8A'/%3E%3Cpath d='M12 14h24l-14 20h14' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E",
    "meta_title": "Extension IA by Zayado - Assistant IA Professionnel | ChatGPT BYOK Gratuit, Claude, Manus Agent",
    "meta_description": "Extension IA by Zayado : Extension Chrome tout-en-un avec ChatGPT BYOK gratuit illimite, Claude Fast & Pro, Manus Agent. Projets, Timer, Workflows automatises. Essai gratuit avec 400 credits.",
    "meta_keywords": "assistant IA, ChatGPT gratuit, Claude AI, Manus Agent, extension Chrome, BYOK, productivite, timer projet, workflow automatisation, intelligence artificielle",
    "og_title": "Extension IA by Zayado - Assistant IA Professionnel | ChatGPT BYOK Gratuit",
    "og_description": "Extension Chrome tout-en-un avec ChatGPT BYOK gratuit illimite, Claude Fast & Pro, Manus Agent. 400 credits offerts a l'inscription.",
    "og_image": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='12' fill='%231E3A8A'/%3E%3Cpath d='M12 14h24l-14 20h14' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E",
    "canonical_url": "https://zayado.net/assistant-ia",
    "ga_tracking_id": "G-XXXXXXXXXX",
}

@admin_router.post("/upload-asset")
async def admin_upload_asset(file: UploadFile = File(...), admin: User = Depends(get_admin_user)):
    """Upload a logo/favicon/asset file for admin configuration."""
    import uuid as uuid_mod
    file_id = str(uuid_mod.uuid4())
    ext = os.path.splitext(file.filename or "file")[1] or ".png"
    filename = f"admin_{file_id}{ext}"
    fpath = os.path.join(UPLOADS_DIR, filename)
    content = await file.read()
    with open(fpath, "wb") as f:
        f.write(content)
    # Return a URL that serves this file
    return {"url": f"/api/files/serve/{filename}", "filename": filename}

@admin_api_router.get("/files/serve/{filename}")
@admin_api_router.head("/files/serve/{filename}")
async def serve_uploaded_file(filename: str):
    """Serve uploaded files (logos, etc.)"""
    safe_name = os.path.basename(filename)
    if not safe_name or safe_name != filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    fpath = os.path.join(UPLOADS_DIR, safe_name)
    if not os.path.abspath(fpath).startswith(os.path.abspath(UPLOADS_DIR)):
        raise HTTPException(status_code=400, detail="Acces refuse")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return FileResponse(fpath)

@admin_api_router.get("/generated-images/{filename}")
async def serve_generated_image(filename: str):
    """Serve AI-generated images."""
    safe_name = os.path.basename(filename)
    if not safe_name or safe_name != filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    fpath = os.path.join("generated_images", safe_name)
    if not os.path.abspath(fpath).startswith(os.path.abspath("generated_images")):
        raise HTTPException(status_code=400, detail="Acces refuse")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Image introuvable")
    return FileResponse(fpath, media_type="image/png")

@admin_router.get("/seo-config")
async def get_seo_config(admin: User = Depends(get_admin_user)):
    """Get SEO & branding config."""
    config = load_admin_config()
    seo = config.get("seo", {})
    result = {**DEFAULT_SEO_CONFIG, **seo}
    return result

@admin_router.put("/seo-config")
async def update_seo_config(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Update SEO & branding config."""
    config = load_admin_config()
    config["seo"] = data
    save_admin_config(config)
    return {"status": "saved"}

# ==================== BREVO EMAIL TEMPLATES & HISTORY ====================

DEFAULT_EMAIL_TEMPLATES = {
    "welcome": {
        "name": "Email de bienvenue",
        "subject": "Bienvenue sur Extension IA by Zayado !",
        "html": """<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<h1 style="color:#1E3A8A;">Bienvenue {{name}} !</h1>
<p>Merci de rejoindre Extension IA by Zayado. Vous disposez de <strong>400 credits gratuits</strong>.</p>
<p><a href="https://app.zayado.net/app" style="background:#DC2626;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;display:inline-block;">Commencer</a></p>
</div>"""
    },
    "purchase_confirm": {
        "name": "Confirmation d'achat",
        "subject": "Confirmation d'achat - Zayado",
        "html": """<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<h2 style="color:#1E3A8A;">Achat confirme</h2>
<p>Bonjour {{name}},</p>
<p>Votre achat de <strong>{{credits}} credits</strong> a bien ete traite.</p>
<p>Nouveau solde : <strong>{{new_balance}} credits</strong></p>
<p><a href="https://app.zayado.net/app" style="background:#DC2626;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;display:inline-block;">Retour au chat</a></p>
</div>"""
    },
    "low_credits": {
        "name": "Credits faibles",
        "subject": "Vos credits sont bientot epuises",
        "html": """<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<h2 style="color:#1E3A8A;">Credits faibles</h2>
<p>Bonjour {{name}},</p>
<p>Il vous reste <strong style="color:#DC2626;">{{credits}} credits</strong> sur votre compte Zayado.</p>
<p>Rechargez vos credits pour continuer a utiliser l'assistant IA.</p>
<a href="https://app.zayado.net/pricing" style="display:inline-block;background:#DC2626;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;">Recharger</a>
</div>"""
    },
    "manus_complete": {
        "name": "Tache Manus terminee",
        "subject": "Votre tache Agent IA est terminee",
        "html": """<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<h2 style="color:#1E3A8A;">Tache Agent terminee</h2>
<p>Bonjour {{name}},</p>
<p>Votre tache Agent Manus est terminee. Consultez le resultat dans votre conversation.</p>
<a href="https://app.zayado.net/app" style="display:inline-block;background:#1E3A8A;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;">Voir le resultat</a>
</div>"""
    },
    "project_report": {
        "name": "Rapport projet",
        "subject": "Decompte Projet - {{project_name}}",
        "html": """<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<h1 style="color:#1E3A8A;">Decompte Projet</h1>
<h2>{{project_name}}</h2>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:8px 0;color:#666;">Taux horaire</td><td style="text-align:right;font-weight:bold;">{{hourly_rate}} EUR/h</td></tr>
<tr><td style="padding:8px 0;color:#666;">Heures totales</td><td style="text-align:right;font-weight:bold;">{{total_hours}}h</td></tr>
<tr style="border-top:2px solid #ddd;"><td style="padding:12px 0;font-weight:bold;font-size:18px;">Total</td><td style="text-align:right;font-weight:bold;font-size:18px;color:#DC2626;">{{total_cost}} EUR</td></tr>
</table>
</div>"""
    },
    "rapport_simulation": {
        "name": "Rapport Simulation (Lead)",
        "subject": "Votre Rapport {{tool}} Personnalisé — Zayado",
        "html": """<div style="font-family:'DM Sans',Arial,sans-serif;max-width:600px;margin:0 auto;background:#ffffff;">
<div style="background:linear-gradient(135deg,#0F1B2D,#1A3671);padding:32px;border-radius:12px 12px 0 0;text-align:center;">
<div style="display:inline-block;background:rgba(201,168,76,0.2);color:#C9A84C;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;margin-bottom:12px;letter-spacing:1px;">RAPPORT PERSONNALISÉ</div>
<h1 style="color:white;margin:0;font-size:22px;font-weight:700;">Votre Rapport {{tool}}</h1>
</div>
<div style="padding:32px;background:white;">
<p style="font-size:15px;color:#374151;line-height:1.7;">Cher <strong>{{name}}</strong>,</p>
<p style="font-size:15px;color:#374151;line-height:1.7;">Merci d'avoir partagé les informations nécessaires pour évaluer la santé financière de <strong>{{company}}</strong>. Voici un résumé de votre évaluation :</p>
{{results_html}}
<div style="margin:24px 0;">
<h2 style="color:#1A3671;font-size:18px;margin-bottom:12px;border-bottom:2px solid #C9A84C;padding-bottom:8px;">Santé Financière</h2>
<ul style="padding-left:20px;color:#374151;font-size:14px;line-height:2;">
<li>Vos liquidités sont suffisantes pour couvrir vos engagements à court terme.</li>
<li>La majorité de vos actifs sont financés par vos propres capitaux.</li>
<li>Votre entreprise génère un bénéfice net solide.</li>
</ul>
</div>
<div style="margin:24px 0;">
<h2 style="color:#1A3671;font-size:18px;margin-bottom:12px;border-bottom:2px solid #C9A84C;padding-bottom:8px;">Conseils Stratégiques</h2>
<p style="font-size:14px;color:#374151;line-height:1.7;">Il y a des opportunités pour optimiser vos processus et maximiser votre rentabilité. Pour obtenir des recommandations personnalisées, n'hésitez pas à nous contacter.</p>
</div>
<div style="margin:24px 0;">
<h2 style="color:#1A3671;font-size:18px;margin-bottom:16px;border-bottom:2px solid #C9A84C;padding-bottom:8px;">Nos solutions pour votre suivi financier</h2>
<table style="width:100%;border-collapse:collapse;">
<tr>
<td style="width:50%;padding:16px;vertical-align:top;border:1px solid #e5e7eb;border-radius:8px 0 0 8px;">
<div style="font-size:11px;font-weight:700;color:#1A3671;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">L'Autonomie</div>
<div style="font-size:24px;font-weight:900;color:#1A3671;">29,90€<span style="font-size:13px;color:#9ca3af;font-weight:400;">/mois</span></div>
<ul style="padding-left:16px;color:#374151;font-size:13px;line-height:2;margin-top:12px;">
<li>Analyses financières en autonomie</li>
<li>Tableau de bord IA complet</li>
<li>Score de sérénité automatique</li>
<li>Alertes trésorerie</li>
</ul>
<a href="https://app.zayado.net/register?plan=autonomie" style="display:block;text-align:center;background:#1A3671;color:white;padding:10px;border-radius:6px;text-decoration:none;font-weight:700;font-size:13px;margin-top:12px;">Choisir L'Autonomie</a>
</td>
<td style="width:50%;padding:16px;vertical-align:top;border:2px solid #C7372F;border-radius:0 8px 8px 0;position:relative;">
<div style="font-size:11px;font-weight:700;color:#C7372F;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">L'Expertise + IA (RECOMMANDÉ)</div>
<div style="font-size:24px;font-weight:900;color:#C7372F;">55,00€<span style="font-size:13px;color:#9ca3af;font-weight:400;">/mois</span></div>
<ul style="padding-left:16px;color:#374151;font-size:13px;line-height:2;margin-top:12px;">
<li>Tout L'Autonomie inclus</li>
<li>Expert financier dédié</li>
<li>Rapport mensuel détaillé</li>
<li>Consultation gratuite mensuelle</li>
</ul>
<a href="https://app.zayado.net/register?plan=expertise" style="display:block;text-align:center;background:#C7372F;color:white;padding:10px;border-radius:6px;text-decoration:none;font-weight:700;font-size:13px;margin-top:12px;">Choisir L'Expertise + IA</a>
</td>
</tr>
</table>
</div>
<div style="background:#f9f7f2;border-radius:8px;padding:20px;text-align:center;margin:24px 0;">
<p style="font-size:14px;color:#374151;margin-bottom:12px;">Pour planifier une <strong>consultation gratuite</strong> :</p>
<a href="https://app.zayado.net/register" style="display:inline-block;background:#C7372F;color:white;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">Planifier ma consultation</a>
<p style="font-size:13px;color:#6b7280;margin-top:12px;">Ou appelez-nous : <strong>01 83 64 39 99</strong></p>
</div>
<div style="margin:24px 0;padding:20px;border:1px solid #e5e7eb;border-radius:8px;">
<h3 style="color:#1A3671;font-size:15px;margin-bottom:12px;">Annexe — Pièces à fournir pour une consultation approfondie</h3>
<ul style="padding-left:20px;color:#6b7280;font-size:13px;line-height:2;">
<li><strong>États financiers complets</strong> des deux dernières années</li>
<li><strong>Détails sur les investissements récents</strong></li>
<li><strong>Documents sur les contrats significatifs</strong></li>
<li><strong>Analyse des prévisions financières</strong></li>
<li><strong>Politiques de gestion de trésorerie</strong></li>
</ul>
</div>
<p style="font-size:14px;color:#374151;">En attendant de vous entendre,</p>
<p style="font-size:14px;color:#374151;"><strong>L'équipe Zayado</strong><br><span style="color:#6b7280;font-size:13px;">01 83 64 39 99 | contact@zayado.net</span></p>
</div>
<div style="background:#0F1B2D;padding:16px;border-radius:0 0 12px 12px;text-align:center;">
<p style="color:rgba(255,255,255,0.5);font-size:11px;margin:0;">&copy; 2026 Zayado. Tous droits réservés.</p>
</div>
</div>"""
    },
    "rapport_simulateur_statut": {
        "name": "Email Simulateur Statut Juridique",
        "subject": "Votre Recommandation Statut Juridique — Zayado",
        "html": ""
    },
    "rapport_analyse_financiere": {
        "name": "Email Analyse Financière",
        "subject": "Votre Analyse Financière — Zayado",
        "html": ""
    },
    "rapport_simulateur_rentabilite": {
        "name": "Email Simulateur Rentabilité",
        "subject": "Votre Analyse de Rentabilité — Zayado",
        "html": ""
    },
    "rapport_creation_entreprise": {
        "name": "Email Création d'Entreprise",
        "subject": "Votre demande de création — Zayado",
        "html": ""
    },
}

# In-memory email log (persisted to config file) — imported from utils
# _get_email_log, _append_email_log, _append_admin_log, _get_admin_log are all imported from utils

@admin_router.get("/activity-log")
async def get_admin_activity_log(admin: User = Depends(get_admin_user)):
    """Get admin activity/modification log."""
    return _get_admin_log()

@admin_router.get("/email-log")
async def get_admin_email_log(admin: User = Depends(get_admin_user)):
    """Get email sending log (Brevo/SMTP)."""
    return _get_email_log()

@admin_router.get("/feedback")
async def get_all_feedback(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Get all user feedback (thumbs up/down) for admin review."""
    from models import Feedback
    from sqlalchemy import select
    result = await db.execute(
        select(Feedback, User.email, User.name)
        .join(User, Feedback.user_id == User.id)
        .order_by(Feedback.created_at.desc())
        .limit(500)
    )
    rows = result.all()
    return [
        {
            "id": str(fb.id),
            "user_email": email,
            "user_name": name,
            "conversation_id": fb.conversation_id,
            "message_index": fb.message_index,
            "feedback": fb.feedback,
            "comment": fb.comment,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }
        for fb, email, name in rows
    ]

@admin_router.get("/roles")
async def get_admin_roles(admin: User = Depends(get_admin_user)):
    """Get all role permission configurations."""
    config = load_admin_config()
    all_perms = ['dashboard', 'users', 'payments', 'promos', 'pricing', 'brevo', 'seo', 'settings', 'maintenance', 'roles', 'limits']
    defaults = {
        'super_admin': all_perms,
        'admin': ['dashboard', 'users', 'payments', 'pricing'],
        'support': ['dashboard'],
        'partenaire': ['dashboard'],
        'presta-partenaire': ['dashboard'],
        'etudiant': ['dashboard'],
        'analyst': ['dashboard'],
    }
    roles_config = config.get("roles_config", defaults)
    return {"roles_config": roles_config, "available_permissions": all_perms}

@admin_router.put("/roles")
async def update_admin_roles(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Update role permission configurations."""
    config = load_admin_config()
    config["roles_config"] = data.get("roles_config", config.get("roles_config", {}))
    save_admin_config(config)
    _append_admin_log({"action": "roles_updated", "by": admin.email, "timestamp": datetime.now(timezone.utc).isoformat()})
    return {"status": "saved", "roles_config": config["roles_config"]}

@admin_router.get("/email-templates")
async def get_email_templates(admin: User = Depends(get_admin_user)):
    """Get email templates (editable)."""
    config = load_admin_config()
    templates = config.get("email_templates", {})
    result = {}
    for key, default in DEFAULT_EMAIL_TEMPLATES.items():
        if key in templates:
            result[key] = {**default, **templates[key]}
        else:
            result[key] = default
    return result

@admin_router.put("/email-templates")
async def update_email_templates(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Update email templates."""
    config = load_admin_config()
    config["email_templates"] = data
    save_admin_config(config)
    return {"status": "saved"}


# ==================== CREDIT LOGS ====================

@admin_router.get("/credit-logs")
async def get_credit_logs(
    admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
    skip: int = 0, limit: int = 50, user_id: str = None, mode: str = None,
    log_type: str = None, sort: str = "newest"
):
    """Get all credit logs with pagination and filters."""
    query = select(CreditLog, User.email, User.name).outerjoin(User, CreditLog.user_id == User.id)
    if user_id:
        query = query.where(CreditLog.user_id == user_id)
    if mode:
        query = query.where(CreditLog.mode == mode)
    if log_type:
        query = query.where(CreditLog.log_type == log_type)

    count_q = select(func.count()).select_from(
        select(CreditLog.id).where(
            *([CreditLog.user_id == user_id] if user_id else []),
            *([CreditLog.mode == mode] if mode else []),
            *([CreditLog.log_type == log_type] if log_type else []),
        ).subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    if sort == "oldest":
        query = query.order_by(CreditLog.created_at.asc())
    else:
        query = query.order_by(CreditLog.created_at.desc())
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_email": email,
                "user_name": name,
                "conversation_id": log.conversation_id,
                "amount": log.amount,
                "mode": log.mode,
                "log_type": log.log_type,
                "description": log.description,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log, email, name in rows
        ],
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


# ==================== API COSTS / PROFITABILITY ====================

@admin_router.get("/api-costs")
async def get_api_costs(
    admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
    skip: int = 0, limit: int = 50, provider: str = None, mode: str = None,
    days: int = 30
):
    """Get API costs with pagination and filters."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(ApiCost, User.email, User.name).outerjoin(User, ApiCost.user_id == User.id)
    query = query.where(ApiCost.created_at >= cutoff)
    if provider:
        query = query.where(ApiCost.provider == provider)
    if mode:
        query = query.where(ApiCost.mode == mode)

    count_filters = [ApiCost.created_at >= cutoff]
    if provider:
        count_filters.append(ApiCost.provider == provider)
    if mode:
        count_filters.append(ApiCost.mode == mode)
    total = (await db.execute(select(func.count()).select_from(select(ApiCost.id).where(*count_filters).subquery()))).scalar() or 0

    query = query.order_by(ApiCost.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return {
        "costs": [
            {
                "id": c.id,
                "user_email": email,
                "user_name": name,
                "provider": c.provider,
                "model": c.model,
                "mode": c.mode,
                "input_tokens": c.input_tokens,
                "output_tokens": c.output_tokens,
                "estimated_cost_eur": c.estimated_cost_eur,
                "credits_charged": c.credits_charged,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c, email, name in rows
        ],
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


@admin_router.get("/profitability")
async def get_profitability(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Get profitability dashboard data — revenue vs API costs."""
    now = datetime.now(timezone.utc)
    periods = {
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "90d": now - timedelta(days=90),
        "all": datetime(2020, 1, 1, tzinfo=timezone.utc),
    }
    result = {}
    for period_key, cutoff in periods.items():
        # Revenue from transactions
        rev = (await db.execute(
            select(func.sum(Transaction.amount)).where(Transaction.status == "completed", Transaction.created_at >= cutoff)
        )).scalar() or 0
        # API costs
        api_cost = (await db.execute(
            select(func.sum(ApiCost.estimated_cost_eur)).where(ApiCost.created_at >= cutoff)
        )).scalar() or 0
        # Credits consumed (from credit_logs)
        credits_consumed = (await db.execute(
            select(func.sum(func.abs(CreditLog.amount))).where(
                CreditLog.log_type == "chat_deduction",
                CreditLog.created_at >= cutoff
            )
        )).scalar() or 0
        # Credits gifted
        credits_gifted = (await db.execute(
            select(func.sum(CreditLog.amount)).where(
                CreditLog.log_type == "gift",
                CreditLog.created_at >= cutoff
            )
        )).scalar() or 0
        # Also get from conversations as fallback
        conv_credits = (await db.execute(
            select(func.sum(Conversation.total_credits_used)).where(Conversation.created_at >= cutoff)
        )).scalar() or 0
        total_credits = max(credits_consumed, conv_credits)

        result[period_key] = {
            "revenue_eur": round(float(rev), 2),
            "api_cost_eur": round(float(api_cost), 4),
            "margin_eur": round(float(rev) - float(api_cost), 2),
            "margin_pct": round(((float(rev) - float(api_cost)) / max(float(rev), 0.01)) * 100, 1) if rev > 0 else 0,
            "total_credits_consumed": int(total_credits),
            "credits_gifted": int(credits_gifted),
        }

    # Credits by mode (from credit_logs)
    mode_result = await db.execute(
        select(CreditLog.mode, func.sum(func.abs(CreditLog.amount)))
        .where(CreditLog.log_type == "chat_deduction")
        .group_by(CreditLog.mode)
    )
    credits_by_mode = {row[0] or "unknown": int(row[1]) for row in mode_result.all()}

    # API costs by provider
    provider_result = await db.execute(
        select(ApiCost.provider, func.sum(ApiCost.estimated_cost_eur), func.count(ApiCost.id))
        .group_by(ApiCost.provider)
    )
    costs_by_provider = {row[0]: {"cost_eur": round(float(row[1]), 4), "calls": int(row[2])} for row in provider_result.all()}

    # Daily credit consumption for last 30 days
    daily_credits = []
    for i in range(29, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_consumed = (await db.execute(
            select(func.sum(func.abs(CreditLog.amount))).where(
                CreditLog.log_type == "chat_deduction",
                CreditLog.created_at >= day_start,
                CreditLog.created_at < day_end
            )
        )).scalar() or 0
        daily_credits.append({
            "date": day_start.strftime("%d/%m"),
            "credits": int(day_consumed),
        })

    return {
        "periods": result,
        "credits_by_mode": credits_by_mode,
        "costs_by_provider": costs_by_provider,
        "daily_credits": daily_credits,
    }


# ==================== REFERRALS ====================

@admin_router.get("/referrals")
async def get_referrals(
    admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
    skip: int = 0, limit: int = 50, status: str = None
):
    """Get all referrals with pagination."""
    from sqlalchemy.orm import aliased
    Referrer = aliased(User)
    Referred = aliased(User)
    query = select(Referral, Referrer.email.label("referrer_email"), Referrer.name.label("referrer_name"),
                   Referred.email.label("referred_email_user"), Referred.name.label("referred_name")) \
        .outerjoin(Referrer, Referral.referrer_id == Referrer.id) \
        .outerjoin(Referred, Referral.referred_id == Referred.id)
    if status:
        query = query.where(Referral.status == status)
    total = (await db.execute(select(func.count()).select_from(
        select(Referral.id).where(*([Referral.status == status] if status else [])).subquery()
    ))).scalar() or 0
    query = query.order_by(Referral.created_at.desc()).offset(skip).limit(limit)
    rows = (await db.execute(query)).all()
    return {
        "referrals": [
            {
                "id": r.id, "referrer_email": rr_email, "referrer_name": rr_name,
                "referred_email": rd_email or r.referred_email,
                "referred_name": rd_name, "status": r.status,
                "bonus_credits": r.bonus_credits,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r, rr_email, rr_name, rd_email, rd_name in rows
        ],
        "total": total, "page": (skip // limit) + 1, "per_page": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


# ==================== NOTIFICATIONS ====================

@admin_router.get("/notifications-list")
async def get_notifications(
    admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
    skip: int = 0, limit: int = 50, type_filter: str = None
):
    """Get all notifications."""
    query = select(Notification)
    if type_filter:
        query = query.where(Notification.type == type_filter)
    total = (await db.execute(select(func.count()).select_from(
        select(Notification.id).where(*([Notification.type == type_filter] if type_filter else [])).subquery()
    ))).scalar() or 0
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    rows = (await db.execute(query)).scalars().all()
    return {
        "notifications": [
            {
                "id": n.id, "user_id": n.user_id, "title": n.title,
                "message": n.message, "type": n.type, "is_global": n.is_global,
                "read": n.read, "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ],
        "total": total, "page": (skip // limit) + 1, "per_page": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


@admin_router.post("/notifications-list")
async def create_notification(data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Create a new notification (global or per-user)."""
    notif = Notification(
        user_id=data.get("user_id"),
        title=data.get("title", "Notification"),
        message=data.get("message", ""),
        type=data.get("type", "info"),
        is_global=data.get("is_global", False),
    )
    db.add(notif)
    await db.commit()
    return {"status": "created", "id": notif.id}


# ==================== AI FEEDBACK ====================

@admin_router.get("/ai-feedback")
async def get_ai_feedback(
    admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
    skip: int = 0, limit: int = 50, rating: str = None
):
    """Get AI feedback entries."""
    query = select(AiFeedback, User.email, User.name).outerjoin(User, AiFeedback.user_id == User.id)
    if rating:
        query = query.where(AiFeedback.rating == rating)
    total = (await db.execute(select(func.count()).select_from(
        select(AiFeedback.id).where(*([AiFeedback.rating == rating] if rating else [])).subquery()
    ))).scalar() or 0
    query = query.order_by(AiFeedback.created_at.desc()).offset(skip).limit(limit)
    rows = (await db.execute(query)).all()
    return {
        "feedback": [
            {
                "id": f.id, "user_email": email, "user_name": name,
                "conversation_id": f.conversation_id, "message_index": f.message_index,
                "rating": f.rating, "comment": f.comment, "mode": f.mode,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f, email, name in rows
        ],
        "total": total, "page": (skip // limit) + 1, "per_page": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


# ==================== EMAIL LOGS ====================

@admin_router.get("/email-logs")
async def get_email_logs(
    admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
    skip: int = 0, limit: int = 50, status_filter: str = None, template: str = None
):
    """Get email logs."""
    query = select(EmailLog)
    if status_filter:
        query = query.where(EmailLog.status == status_filter)
    if template:
        query = query.where(EmailLog.template == template)
    filters = []
    if status_filter: filters.append(EmailLog.status == status_filter)
    if template: filters.append(EmailLog.template == template)
    total = (await db.execute(select(func.count()).select_from(
        select(EmailLog.id).where(*filters).subquery()
    ))).scalar() or 0
    query = query.order_by(EmailLog.created_at.desc()).offset(skip).limit(limit)
    rows = (await db.execute(query)).scalars().all()
    return {
        "logs": [
            {
                "id": e.id, "recipient": e.recipient, "subject": e.subject,
                "template": e.template, "status": e.status, "error": e.error,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ],
        "total": total, "page": (skip // limit) + 1, "per_page": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


# ==================== ADMIN ACTIVITY LOGS ====================

@admin_router.get("/admin-logs")
async def get_admin_logs_db(
    admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
    skip: int = 0, limit: int = 50
):
    """Get admin activity logs from DB."""
    total = (await db.execute(select(func.count()).select_from(AdminLog))).scalar() or 0
    rows = (await db.execute(
        select(AdminLog).order_by(AdminLog.created_at.desc()).offset(skip).limit(limit)
    )).scalars().all()
    return {
        "logs": [
            {
                "id": entry.id, "admin_email": entry.admin_email, "action": entry.action,
                "target_type": entry.target_type, "target_id": entry.target_id,
                "details": entry.details, "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in rows
        ],
        "total": total, "page": (skip // limit) + 1, "per_page": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


# ==================== MAIN ROUTES ====================



# ─── Platform Settings (Admin) ──────────────────────────────────

PLATFORM_DEFAULTS = {
    "referral_bonus_referrer": 50,
    "referral_bonus_new_user": 25,
    "welcome_credits": 200,
    "team_limits": {
        "free": {"max_teams": 0, "max_members": 0},
        "pro": {"max_teams": 1, "max_members": 5},
        "business": {"max_teams": 1, "max_members": 2},
        "team": {"max_teams": -1, "max_members": -1}
    },
}

@admin_router.get("/platform-settings")
async def get_platform_settings(user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformSetting))
    rows = result.scalars().all()
    settings = dict(PLATFORM_DEFAULTS)
    for row in rows:
        try:
            settings[row.key] = json.loads(row.value)
        except (json.JSONDecodeError, TypeError):
            settings[row.key] = row.value
    return settings

@admin_router.put("/platform-settings")
async def update_platform_settings(body: Dict[str, Any], user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    for key, value in body.items():
        existing = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
        row = existing.scalar_one_or_none()
        if row:
            row.value = json.dumps(value)
        else:
            db.add(PlatformSetting(key=key, value=json.dumps(value)))
    await db.commit()
    return {"status": "ok", **body}


# ==================== SITE URLS MANAGEMENT ====================
SITE_URL_DEFAULTS = {
    "footer_conditions_url": "/fr/legal/mentions-legales",
    "footer_privacy_url": "/fr/legal/politique-confidentialite",
    "footer_copyright": "2026 Zayado IA. Tous droits reserves.",
    "doc_url": "https://docs.zayado.net",
    "social_instagram": "",
    "social_linkedin": "",
    "social_tiktok": "",
    "social_youtube": "",
    "social_facebook": "",
    "social_x": "",
    "whatsapp_url": "",
    "extension_url": "",
    "website_url": "https://zayado.net",
}

@admin_router.get("/site-urls")
async def get_site_urls(user: User = Depends(get_admin_user)):
    """Get all editable site URLs and social links."""
    config = load_admin_config()
    result = dict(SITE_URL_DEFAULTS)
    for k in SITE_URL_DEFAULTS:
        if k in config:
            result[k] = config[k]
    return result

@admin_router.put("/site-urls")
async def update_site_urls(body: Dict[str, Any], user: User = Depends(get_admin_user)):
    """Update site URLs and social links."""
    config = load_admin_config()
    allowed = set(SITE_URL_DEFAULTS.keys())
    for k, v in body.items():
        if k in allowed:
            config[k] = v
    save_admin_config(config)
    return {"status": "ok", **{k: config.get(k, "") for k in allowed}}



# ==================== EMAIL PROSPECTION / CAMPAIGN ====================

class ProspectionEmailRequest(BaseModel):
    to_email: EmailStr
    to_name: str = ""
    subject: str = ""
    custom_message: str = ""

PROSPECTION_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#0F172A 0%,#1E3A8A 100%);padding:40px 40px 32px;text-align:center;">
    <h1 style="color:#FFFFFF;font-size:28px;margin:0 0 8px;font-weight:700;letter-spacing:-0.5px;">Extension IA by Zayado</h1>
    <p style="color:#94A3B8;font-size:14px;margin:0;">by zayado.net</p>
  </td></tr>

  <!-- Body -->
  <tr><td style="padding:40px;">
    <p style="color:#334155;font-size:16px;line-height:1.7;margin:0 0 20px;">
      Bonjour{name_greeting},
    </p>
    <p style="color:#334155;font-size:16px;line-height:1.7;margin:0 0 20px;">
      Et si votre business avait un copilote IA qui travaille vraiment pour vous ?
    </p>
    <p style="color:#334155;font-size:16px;line-height:1.7;margin:0 0 24px;">
      <strong>Extension IA</strong> est une plateforme tout-en-un pensee pour les entrepreneurs, freelances et TPE/PME qui veulent :
    </p>

    <!-- Features -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
      <tr><td style="padding:12px 16px;background:#F8FAFC;border-radius:10px;margin-bottom:8px;">
        <table><tr>
          <td style="vertical-align:top;padding-right:12px;font-size:20px;">&#9889;</td>
          <td style="color:#334155;font-size:15px;line-height:1.6;"><strong>Gagner du temps</strong> — Generez des documents, emails, propositions commerciales en quelques secondes</td>
        </tr></table>
      </td></tr>
      <tr><td style="height:8px;"></td></tr>
      <tr><td style="padding:12px 16px;background:#F8FAFC;border-radius:10px;">
        <table><tr>
          <td style="vertical-align:top;padding-right:12px;font-size:20px;">&#128200;</td>
          <td style="color:#334155;font-size:15px;line-height:1.6;"><strong>Piloter vos finances</strong> — Suivi de tresorerie, rentabilite et previsions automatisees</td>
        </tr></table>
      </td></tr>
      <tr><td style="height:8px;"></td></tr>
      <tr><td style="padding:12px 16px;background:#F8FAFC;border-radius:10px;">
        <table><tr>
          <td style="vertical-align:top;padding-right:12px;font-size:20px;">&#129302;</td>
          <td style="color:#334155;font-size:15px;line-height:1.6;"><strong>Automatiser vos taches</strong> — Workflows intelligents, CRM integre, agent IA autonome</td>
        </tr></table>
      </td></tr>
      <tr><td style="height:8px;"></td></tr>
      <tr><td style="padding:12px 16px;background:#F8FAFC;border-radius:10px;">
        <table><tr>
          <td style="vertical-align:top;padding-right:12px;font-size:20px;">&#127912;</td>
          <td style="color:#334155;font-size:15px;line-height:1.6;"><strong>Creer du contenu pro</strong> — Images, visuels marketing, posts reseaux sociaux generes par IA</td>
        </tr></table>
      </td></tr>
    </table>

    {custom_block}

    <!-- CTA -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
      <tr><td align="center" style="padding:8px 0;">
        <a href="https://app.zayado.net/register" style="display:inline-block;background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);color:#FFFFFF;font-size:16px;font-weight:600;text-decoration:none;padding:16px 40px;border-radius:12px;letter-spacing:0.3px;">
          Essayer gratuitement — 200 credits offerts
        </a>
      </td></tr>
      <tr><td align="center">
        <p style="color:#94A3B8;font-size:13px;margin:8px 0 0;">Aucune carte bancaire requise</p>
      </td></tr>
    </table>

    <p style="color:#334155;font-size:16px;line-height:1.7;margin:0 0 20px;">
      Rejoignez les entrepreneurs qui font deja la difference avec l'IA. Votre temps est precieux — laissez Extension IA s'occuper du reste.
    </p>

    <p style="color:#334155;font-size:16px;line-height:1.7;margin:0;">
      A tres vite,<br>
      <strong>L'equipe Extension IA</strong><br>
      <span style="color:#64748B;font-size:14px;">zayado.net</span>
    </p>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#F8FAFC;padding:24px 40px;border-top:1px solid #E2E8F0;text-align:center;">
    <p style="color:#94A3B8;font-size:12px;margin:0 0 8px;">
      Extension IA by Zayado &mdash; L'intelligence artificielle au service de votre business
    </p>
    <p style="color:#CBD5E1;font-size:11px;margin:0;">
      <a href="https://app.zayado.net" style="color:#64748B;text-decoration:underline;">app.zayado.net</a>
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""

@admin_router.post("/send-prospection-email")
async def send_prospection_email(
    data: ProspectionEmailRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Send prospection/invitation email to a potential client."""
    name_greeting = f" {data.to_name}" if data.to_name else ""
    custom_block = ""
    if data.custom_message:
        custom_block = f"""
        <div style="background:#EFF6FF;border-left:4px solid #2563EB;padding:16px 20px;border-radius:0 10px 10px 0;margin:0 0 28px;">
          <p style="color:#1E40AF;font-size:15px;line-height:1.6;margin:0;">{data.custom_message}</p>
        </div>
        """

    html = PROSPECTION_HTML_TEMPLATE.replace("{name_greeting}", name_greeting).replace("{custom_block}", custom_block)
    subject = data.subject or "Decouvrez Extension IA — Votre copilote business propulse par l'IA"

    mid = send_brevo_email(data.to_email, data.to_name or "Prospect", subject, html)
    if mid:
        return {"status": "sent", "message_id": str(mid), "to": data.to_email}
    raise HTTPException(500, "Erreur lors de l'envoi de l'email. Verifiez la config Brevo.")


class BulkProspectionRequest(BaseModel):
    recipients: list
    subject: str = ""
    custom_message: str = ""

@admin_router.post("/send-prospection-bulk")
async def send_prospection_bulk(
    data: BulkProspectionRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Send prospection emails to multiple recipients."""
    results = []
    subject = data.subject or "Decouvrez Extension IA — Votre copilote business propulse par l'IA"
    for recipient in data.recipients[:50]:
        email = recipient.get("email", "") if isinstance(recipient, dict) else str(recipient)
        name = recipient.get("name", "") if isinstance(recipient, dict) else ""
        if not email or "@" not in email:
            results.append({"email": email, "status": "invalid"})
            continue
        name_greeting = f" {name}" if name else ""
        custom_block = ""
        if data.custom_message:
            custom_block = f"""
            <div style="background:#EFF6FF;border-left:4px solid #2563EB;padding:16px 20px;border-radius:0 10px 10px 0;margin:0 0 28px;">
              <p style="color:#1E40AF;font-size:15px;line-height:1.6;margin:0;">{data.custom_message}</p>
            </div>
            """
        html = PROSPECTION_HTML_TEMPLATE.replace("{name_greeting}", name_greeting).replace("{custom_block}", custom_block)
        mid = send_brevo_email(email, name or "Prospect", subject, html)
        results.append({"email": email, "status": "sent" if mid else "failed", "message_id": str(mid) if mid else None})
    return {"total": len(results), "sent": sum(1 for r in results if r["status"] == "sent"), "results": results}



@admin_router.get("/mammoth/status")
async def check_mammoth_status(admin: User = Depends(get_admin_user)):
    """Test la connexion à Mammoth IA et retourne le statut."""
    import httpx as _httpx
    mammoth_key = os.environ.get('MAMMOTH_API_KEY', '')
    if not mammoth_key:
        return {"ok": False, "error": "MAMMOTH_API_KEY non configurée dans Railway"}
    try:
        async with _httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.mammouth.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "messages": [{"role": "user", "content": "Réponds uniquement OK"}],
                    "max_tokens": 10
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                model = data.get("model", "claude-haiku-4-5-20251001")
                return {"ok": True, "model": model, "status_code": 200}
            else:
                return {
                    "ok": False, 
                    "error": f"HTTP {resp.status_code}",
                    "detail": resp.text[:200],
                    "hint": "Vérifiez le solde sur app.mammouth.ai" if resp.status_code in [402, 429] else "Clé API invalide" if resp.status_code == 401 else "Service indisponible"
                }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ═══════════════════════════════════════════════════════════════
# RAILWAY — Provisionnement automatique des serveurs clients
# ═══════════════════════════════════════════════════════════════
import httpx as _httpx

RAILWAY_API = "https://backboard.railway.app/graphql/v2"

async def _railway_graphql(query: str, variables: dict, token: str) -> dict:
    """Appel à l'API GraphQL de Railway."""
    async with _httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            RAILWAY_API,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"query": query, "variables": variables}
        )
        return resp.json()


@admin_router.get("/railway/config")
async def get_railway_config(user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Retourne la config Railway (token masqué)."""
    cfg = load_admin_config()
    token_raw = cfg.get("railway_api_token", "")
    return {
        "railway_api_token": ("*" * 8 + token_raw[-4:]) if len(token_raw) > 4 else "",
        "auto_provision": cfg.get("railway_auto_provision", False),
    }


@admin_router.put("/railway/config")
async def save_railway_config(body: dict, user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Sauvegarde le token Railway et les options."""
    cfg = load_admin_config()
    if body.get("railway_api_token") and not body["railway_api_token"].startswith("*"):
        cfg["railway_api_token"] = body["railway_api_token"]
    if "auto_provision" in body:
        cfg["railway_auto_provision"] = body["auto_provision"]
    save_admin_config(cfg)
    return {"ok": True}


@admin_router.get("/railway/projects")
async def list_railway_projects(user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Liste tous les projets Railway clients."""
    try:
        result = await db.execute(
            select(RailwayProject).order_by(RailwayProject.created_at.desc())
        )
        projects = result.scalars().all()
        return [
            {
                "id": p.id,
                "user_email": p.user_email,
                "user_id": p.user_id,
                "railway_project_id": p.railway_project_id,
                "railway_url": p.railway_url,
                "status": p.status,
                "plan": p.plan,
                "agent_name": p.agent_name,
                "monthly_cost": p.monthly_cost,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    except Exception as e:
        logger.warning(f"RailwayProject table may not exist yet: {e}")
        return []


@admin_router.get("/railway/stats")
async def railway_stats(user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Statistiques des projets Railway."""
    try:
        result = await db.execute(select(RailwayProject))
        projects = result.scalars().all()
        return {
            "active_projects":    sum(1 for p in projects if p.status == "active"),
            "deploying_projects": sum(1 for p in projects if p.status == "deploying"),
            "error_projects":     sum(1 for p in projects if p.status == "error"),
            "total_cost":         round(sum(p.monthly_cost or 5 for p in projects if p.status == "active"), 1),
        }
    except Exception:
        return {"active_projects": 0, "deploying_projects": 0, "error_projects": 0, "total_cost": 0}


@admin_router.post("/railway/provision")
async def provision_railway_project(body: dict, user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """
    Crée un nouveau projet Railway pour un client.
    dry_run=True → simule sans créer.
    """
    user_email  = body.get("user_email", "")
    plan        = body.get("plan", "pro")
    agent_type  = body.get("agent_type", "General")
    dry_run     = body.get("dry_run", False)

    if not user_email:
        raise HTTPException(400, "user_email requis")

    cfg = load_admin_config()
    railway_token = cfg.get("railway_api_token", "")

    if not railway_token:
        raise HTTPException(503, "Token Railway non configuré. Allez dans Admin → Railway → Configuration.")

    project_name = f"zayado-{user_email.split('@')[0].lower().replace('.', '-')[:20]}-agent"

    if dry_run:
        return {"ok": True, "dry_run": True, "project_name": project_name, "message": "Simulation OK — aucun projet créé"}

    # Créer le projet via l'API Railway GraphQL
    try:
        CREATE_PROJECT = """
        mutation projectCreate($input: ProjectCreateInput!) {
          projectCreate(input: $input) {
            id
            name
          }
        }
        """
        result = await _railway_graphql(CREATE_PROJECT, {
            "input": {"name": project_name, "description": f"Agent Zayado pour {user_email}"}
        }, railway_token)

        if "errors" in result:
            raise HTTPException(500, f"Erreur Railway: {result['errors'][0].get('message', 'Inconnu')}")

        railway_project_id = result["data"]["projectCreate"]["id"]

        # Trouver l'utilisateur en DB
        user_result = await db.execute(select(User).where(User.email == user_email))
        client_user = user_result.scalar_one_or_none()

        # Enregistrer en DB
        railway_proj = RailwayProject(
            user_id=client_user.id if client_user else None,
            user_email=user_email,
            railway_project_id=railway_project_id,
            railway_url=f"https://railway.app/project/{railway_project_id}",
            status="deploying",
            plan=plan,
            agent_name=agent_type,
            monthly_cost=5.0,
        )
        db.add(railway_proj)
        await db.commit()

        logger.info(f"Railway project created: {railway_project_id} for {user_email}")
        return {
            "ok": True,
            "project_id": railway_project_id,
            "project_name": project_name,
            "railway_url": f"https://railway.app/project/{railway_project_id}",
            "message": f"Projet Railway créé pour {user_email}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erreur création projet Railway: {str(e)[:200]}")


@admin_router.delete("/railway/projects/{project_id}")
async def delete_railway_project(project_id: str, user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Supprime un projet Railway (DB uniquement — suppression manuelle sur Railway.app)."""
    result = await db.execute(select(RailwayProject).where(RailwayProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Projet non trouvé")
    await db.delete(project)
    await db.commit()
    return {"ok": True}


@admin_router.get("/railway/projects/{project_id}/logs")
async def get_project_logs(project_id: str, user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Retourne les logs simulés d'un projet."""
    result = await db.execute(select(RailwayProject).where(RailwayProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Projet non trouvé")
    return {
        "project_id": project_id,
        "lines": [
            f"[{project.created_at.strftime('%Y-%m-%d %H:%M') if project.created_at else '—'}] Projet créé",
            f"[INFO] Plan: {project.plan} · Agent: {project.agent_name}",
            f"[INFO] Status: {project.status}",
            f"[INFO] Railway URL: {project.railway_url or 'Non défini'}",
            "[INFO] Pour voir les vrais logs, ouvrez le projet sur railway.app",
        ]
    }
