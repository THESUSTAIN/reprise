"""Affiliate / Reseller System Routes — Dokan-style."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import logging

from database import get_db
from deps import get_current_user, get_admin_user, User
from models import AffiliateCommission, AffiliatePayout, Transaction, Referral
from utils import load_admin_config

logger = logging.getLogger(__name__)

affiliate_router = APIRouter(prefix="/affiliate", tags=["Affiliate"])

# Tier thresholds (configurable via admin_config)
DEFAULT_TIERS = {
    "bronze":  {"min_sales": 0,  "commission_rate": 0.10, "label": "Bronze"},
    "silver":  {"min_sales": 5,  "commission_rate": 0.15, "label": "Silver"},
    "gold":    {"min_sales": 15, "commission_rate": 0.20, "label": "Gold"},
    "diamond": {"min_sales": 50, "commission_rate": 0.25, "label": "Diamond"},
}

def _get_tiers():
    config = load_admin_config()
    return config.get("affiliate_tiers", DEFAULT_TIERS)

def _get_tier(total_sales: int):
    tiers = _get_tiers()
    current = tiers["bronze"]
    for key in ["bronze", "silver", "gold", "diamond"]:
        tier = tiers.get(key, DEFAULT_TIERS[key])
        if total_sales >= tier["min_sales"]:
            current = {**tier, "id": key}
    return current


@affiliate_router.get("/dashboard")
async def get_affiliate_dashboard(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get affiliate dashboard stats."""
    if user.role not in ("partenaire", "presta-partenaire", "admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Acces reserve aux partenaires")

    # Ensure referral code exists
    if not user.referral_code:
        code = f"ZAY{user.id[:6].upper()}"
        await db.execute(update(User).where(User.id == user.id).values(referral_code=code))
        await db.commit()
        user.referral_code = code

    # Total referrals
    total_referrals = (await db.execute(
        select(func.count(User.id)).where(User.referred_by == user.id)
    )).scalar() or 0

    # Commissions
    total_commissions = (await db.execute(
        select(func.sum(AffiliateCommission.commission_amount))
        .where(AffiliateCommission.affiliate_id == user.id)
    )).scalar() or 0.0

    pending_commissions = (await db.execute(
        select(func.sum(AffiliateCommission.commission_amount))
        .where(AffiliateCommission.affiliate_id == user.id, AffiliateCommission.status == "pending")
    )).scalar() or 0.0

    paid_commissions = (await db.execute(
        select(func.sum(AffiliateCommission.commission_amount))
        .where(AffiliateCommission.affiliate_id == user.id, AffiliateCommission.status == "paid")
    )).scalar() or 0.0

    total_sales = (await db.execute(
        select(func.count(AffiliateCommission.id))
        .where(AffiliateCommission.affiliate_id == user.id)
    )).scalar() or 0

    # Revenue generated (total sale amounts)
    total_revenue = (await db.execute(
        select(func.sum(AffiliateCommission.sale_amount))
        .where(AffiliateCommission.affiliate_id == user.id)
    )).scalar() or 0.0

    # #82 — Monthly stats (last 6 months) — fetch raw then group in Python for DB portability
    six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_result = await db.execute(
        select(
            AffiliateCommission.created_at,
            AffiliateCommission.commission_amount
        )
        .where(AffiliateCommission.affiliate_id == user.id, AffiliateCommission.created_at >= six_months_ago)
    )
    monthly_data = {}
    try:
        for row in monthly_result.all():
            month_key = row[0].strftime("%Y-%m") if row[0] else "unknown"
            if month_key not in monthly_data:
                monthly_data[month_key] = {"sales": 0, "commission": 0.0}
            monthly_data[month_key]["sales"] += 1
            monthly_data[month_key]["commission"] += round(float(row[1] or 0), 2)
    except Exception:
        pass
    monthly_stats = []
    for i in range(5, -1, -1):
        month_date = (datetime.now(timezone.utc) - timedelta(days=30 * i)).replace(day=1)
        month_key = month_date.strftime("%Y-%m")
        data = monthly_data.get(month_key, {"sales": 0, "commission": 0.0})
        monthly_stats.append({
            "month": month_date.strftime("%b %Y"),
            "sales": data["sales"],
            "commission": data["commission"]
        })

    # Recent commissions
    recent = await db.execute(
        select(AffiliateCommission, User.email, User.name)
        .outerjoin(User, AffiliateCommission.customer_id == User.id)
        .where(AffiliateCommission.affiliate_id == user.id)
        .order_by(AffiliateCommission.created_at.desc())
        .limit(20)
    )
    recent_commissions = [
        {
            "id": str(c.id),
            "customer_email": email or "Anonyme",
            "customer_name": name or "",
            "sale_amount": round(float(c.sale_amount), 2),
            "commission_rate": round(float(c.commission_rate) * 100, 1),
            "commission_amount": round(float(c.commission_amount), 2),
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c, email, name in recent.all()
    ]

    # Tier info (check for admin override)
    tier = _get_tier(total_sales)
    try:
        import json
        mem = json.loads(user.memory) if user.memory else {}
        override = mem.get("affiliate_tier_override")
        if override and override in ["bronze", "silver", "gold", "diamond"]:
            tier = {**_get_tiers().get(override, {}), "id": override}
    except Exception:
        pass

    # Referral list
    referrals_result = await db.execute(
        select(User.email, User.name, User.plan, User.created_at)
        .where(User.referred_by == user.id)
        .order_by(User.created_at.desc())
        .limit(50)
    )
    referrals = [
        {"email": r.email, "name": r.name, "plan": r.plan, "joined": r.created_at.isoformat() if r.created_at else None}
        for r in referrals_result.all()
    ]

    # Use partner_code as the single affiliate code
    affiliate_code = user.partner_code or user.referral_code or ""
    # If partner has referral_code but no partner_code, copy it
    if not user.partner_code and user.referral_code:
        affiliate_code = user.referral_code
        await db.execute(update(User).where(User.id == user.id).values(partner_code=user.referral_code))
        await db.commit()

    return {
        "referral_code": affiliate_code,
        "referral_link": f"https://app.zayado.net/register?ref={affiliate_code}" if affiliate_code else "",
        "partner_url": user.partner_url,
        "tier": tier,
        "stats": {
            "total_referrals": total_referrals,
            "total_sales": total_sales,
            "total_commissions": round(float(total_commissions), 2),
            "pending_commissions": round(float(pending_commissions), 2),
            "paid_commissions": round(float(paid_commissions), 2),
            "total_revenue_generated": round(float(total_revenue), 2),
        },
        "monthly_stats": monthly_stats,
        "recent_commissions": recent_commissions,
        "referrals": referrals,
    }


@affiliate_router.post("/request-payout")
async def request_payout(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Request a payout for pending commissions."""
    if user.role not in ("partenaire", "presta-partenaire", "admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Acces reserve aux partenaires")

    method = data.get("method", "bank_transfer")
    if method not in ("bank_transfer", "paypal", "credits"):
        raise HTTPException(status_code=400, detail="Methode invalide")

    # Calculate pending amount
    pending = (await db.execute(
        select(func.sum(AffiliateCommission.commission_amount))
        .where(AffiliateCommission.affiliate_id == user.id, AffiliateCommission.status == "pending")
    )).scalar() or 0.0

    if pending < 10:
        raise HTTPException(status_code=400, detail="Minimum 10 EUR pour un retrait")

    # Create payout request
    payout = AffiliatePayout(
        affiliate_id=user.id,
        amount=float(pending),
        method=method,
        reference=data.get("reference", ""),
    )
    db.add(payout)

    # Mark commissions as processing
    await db.execute(
        update(AffiliateCommission)
        .where(AffiliateCommission.affiliate_id == user.id, AffiliateCommission.status == "pending")
        .values(status="approved")
    )

    # If method is credits, apply immediately
    if method == "credits":
        credits_to_add = int(pending * 100)  # 1 EUR = 100 credits
        await db.execute(
            update(User).where(User.id == user.id)
            .values(credits=User.credits + credits_to_add)
        )
        await db.execute(
            update(AffiliateCommission)
            .where(AffiliateCommission.affiliate_id == user.id, AffiliateCommission.status == "approved")
            .values(status="paid", paid_at=datetime.now(timezone.utc))
        )
        payout.status = "completed"
        payout.completed_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "status": "success",
        "payout_id": str(payout.id),
        "amount": round(float(pending), 2),
        "method": method,
        "message": f"Retrait de {pending:.2f} EUR {'converti en {0} credits'.format(int(pending * 100)) if method == 'credits' else 'demande en cours'}"
    }


# ── Admin Affiliate Management ──

@affiliate_router.get("/admin/affiliates")
async def admin_list_affiliates(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Admin: list all affiliates with stats."""
    result = await db.execute(
        select(User)
        .where(User.role.in_(["partenaire", "presta-partenaire"]))
        .order_by(User.created_at.desc())
    )
    affiliates = result.scalars().all()

    out = []
    for a in affiliates:
        total_sales = (await db.execute(
            select(func.count(AffiliateCommission.id))
            .where(AffiliateCommission.affiliate_id == a.id)
        )).scalar() or 0
        
        total_commissions = (await db.execute(
            select(func.sum(AffiliateCommission.commission_amount))
            .where(AffiliateCommission.affiliate_id == a.id)
        )).scalar() or 0.0

        total_referrals = (await db.execute(
            select(func.count(User.id)).where(User.referred_by == a.id)
        )).scalar() or 0

        tier = _get_tier(total_sales)
        # Check for admin tier override
        try:
            import json
            mem = json.loads(a.memory) if a.memory else {}
            override = mem.get("affiliate_tier_override")
            if override and override in ["bronze", "silver", "gold", "diamond"]:
                tier = {**_get_tiers().get(override, {}), "id": override}
        except Exception:
            pass

        out.append({
            "id": str(a.id),
            "email": a.email,
            "name": a.name,
            "referral_code": a.referral_code,
            "partner_code": a.partner_code or "",
            "partner_url": a.partner_url,
            "tier": tier,
            "total_referrals": total_referrals,
            "total_sales": total_sales,
            "total_commissions": round(float(total_commissions), 2),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return out


@affiliate_router.get("/admin/payouts")
async def admin_list_payouts(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Admin: list all payout requests."""
    result = await db.execute(
        select(AffiliatePayout, User.email, User.name)
        .join(User, AffiliatePayout.affiliate_id == User.id)
        .order_by(AffiliatePayout.created_at.desc())
        .limit(100)
    )
    return [
        {
            "id": str(p.id),
            "affiliate_email": email,
            "affiliate_name": name,
            "amount": round(float(p.amount), 2),
            "method": p.method,
            "reference": p.reference,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        }
        for p, email, name in result.all()
    ]


@affiliate_router.post("/admin/payout/{payout_id}/approve")
async def admin_approve_payout(payout_id: str, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Admin: approve/complete a payout."""
    result = await db.execute(select(AffiliatePayout).where(AffiliatePayout.id == payout_id))
    payout = result.scalar_one_or_none()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout non trouve")

    payout.status = "completed"
    payout.completed_at = datetime.now(timezone.utc)

    # Mark related commissions as paid
    await db.execute(
        update(AffiliateCommission)
        .where(AffiliateCommission.affiliate_id == payout.affiliate_id, AffiliateCommission.status == "approved")
        .values(status="paid", paid_at=datetime.now(timezone.utc))
    )
    await db.commit()

    return {"status": "success", "message": "Payout approuve"}


@affiliate_router.get("/admin/tiers")
async def admin_get_tiers(admin: User = Depends(get_admin_user)):
    """Admin: get current affiliate tier configuration."""
    return _get_tiers()


@affiliate_router.put("/admin/tiers")
async def admin_update_tiers(data: Dict[str, Any], admin: User = Depends(get_admin_user)):
    """Admin: update affiliate tier configuration."""
    from utils import save_admin_config
    config = load_admin_config()
    config["affiliate_tiers"] = data.get("tiers", DEFAULT_TIERS)
    save_admin_config(config)
    return {"status": "success", "tiers": config["affiliate_tiers"]}



@affiliate_router.post("/admin/create")
async def admin_create_affiliate(data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Admin: manually create or promote a user to affiliate/partner."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email requis")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    import uuid
    referral_code = data.get("referral_code") or f"REF-{uuid.uuid4().hex[:8].upper()}"
    promo_code = data.get("promo_code") or f"PROMO-{uuid.uuid4().hex[:6].upper()}"
    role = data.get("role", "partenaire")
    tier_override = data.get("tier_override", "")

    if user:
        # Promote existing user
        updates = {"role": role}
        if not user.referral_code:
            updates["referral_code"] = referral_code
        if not user.partner_code:
            updates["partner_code"] = promo_code
        if tier_override:
            memory = {}
            try:
                import json
                memory = json.loads(user.memory) if user.memory else {}
            except Exception:
                memory = {}
            memory["affiliate_tier_override"] = tier_override
            updates["memory"] = json.dumps(memory)
        await db.execute(update(User).where(User.id == user.id).values(**updates))
        await db.commit()
        return {
            "status": "promoted", "email": email, "role": role,
            "referral_code": user.referral_code or referral_code,
            "promo_code": user.partner_code or promo_code,
            "tier_override": tier_override
        }
    else:
        # Create new placeholder user (pre-registration)
        import uuid as _uuid
        from models import User as UserModel
        import bcrypt
        temp_pass = _uuid.uuid4().hex[:12]
        hashed = bcrypt.hashpw(temp_pass.encode(), bcrypt.gensalt()).decode()
        new_user = UserModel(
            id=str(_uuid.uuid4()),
            email=email,
            name=data.get("name", ""),
            password_hash=hashed,
            role=role,
            plan="free",
            credits=200,
            referral_code=referral_code,
            partner_code=promo_code,
        )
        if tier_override:
            import json
            new_user.memory = json.dumps({"affiliate_tier_override": tier_override})
        db.add(new_user)
        await db.commit()
        return {
            "status": "created", "email": email, "role": role,
            "referral_code": referral_code,
            "promo_code": promo_code,
            "temp_password": temp_pass,
            "tier_override": tier_override,
            "message": f"Compte cree. Mot de passe temporaire: {temp_pass}"
        }


@affiliate_router.put("/admin/{user_id}/tier")
async def admin_update_affiliate_tier(user_id: str, data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Admin: manually override an affiliate's tier."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    tier = data.get("tier", "bronze")
    if tier not in ["bronze", "silver", "gold", "diamond"]:
        raise HTTPException(status_code=400, detail="Tier invalide")

    import json
    memory = {}
    try:
        memory = json.loads(user.memory) if user.memory else {}
    except Exception:
        memory = {}
    memory["affiliate_tier_override"] = tier
    await db.execute(update(User).where(User.id == user_id).values(memory=json.dumps(memory)))
    await db.commit()
    return {"status": "ok", "user_id": user_id, "tier": tier}
