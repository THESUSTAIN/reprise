"""Endpoints manquants identifiés au test de branchement (10/02/2026).

Frontend appelait ces routes qui retournaient 404 :
- POST /api/contact/send       (formulaire Contact public-site)
- GET  /api/quote/today        (citation du jour, dashboard SaaS)
- GET  /api/me/profile         (profil utilisateur)
- PATCH /api/me/profile        (mise à jour profil)
- Plusieurs /api/admin/* stubs pour ne pas casser Admin.js
"""
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user, get_admin_user as require_admin
from models import User, ContactMessage

logger = logging.getLogger(__name__)

missing_router = APIRouter(tags=["missing-endpoints"])

# ─────────────────────────────────────────────────────────────────────
# POST /api/contact/send — formulaire Contact public-site
# ─────────────────────────────────────────────────────────────────────
class ContactSendReq(BaseModel):
    name: str
    email: str
    subject: Optional[str] = "general"
    message: str


@missing_router.post("/contact/send")
async def contact_send(body: ContactSendReq, db: AsyncSession = Depends(get_db)):
    """Enregistre un message de contact (table contact_messages) + best-effort Brevo notify."""
    try:
        msg = ContactMessage(
            name=body.name.strip()[:120] or "Anonyme",
            email=body.email.strip().lower()[:200],
            subject=(body.subject or "general")[:50],
            message=body.message.strip()[:5000],
            created_at=datetime.now(timezone.utc),
        )
        db.add(msg)
        await db.commit()

        # Best-effort : notify admin via Brevo if available (brand Zayado car site public)
        try:
            from utils import send_brevo_email
            send_brevo_email(
                to_email="contact@zayado.net",
                subject=f"[Contact Zayado] {body.subject} — {body.name}",
                html_content=f"<p><b>De :</b> {body.name} &lt;{body.email}&gt;</p>"
                             f"<p><b>Sujet :</b> {body.subject}</p>"
                             f"<p>{body.message}</p>",
                brand="zayado",
            )
        except Exception as e:
            logger.info(f"[contact.send] Brevo notify skipped: {e}")

        return {"status": "ok", "message": "Message reçu"}
    except Exception as e:
        logger.error(f"[contact.send] {e}")
        raise HTTPException(status_code=500, detail="Impossible d'enregistrer le message.")


# ─────────────────────────────────────────────────────────────────────
# GET /api/quote/today — citation du jour
# ─────────────────────────────────────────────────────────────────────
_QUOTES = [
    {"text": "La clarté précède la croissance.", "author": "James Clear", "source": "Atomic Habits"},
    {"text": "La sagesse, c'est de prévoir.", "author": "Sénèque", "source": "Lettres à Lucilius"},
    {"text": "L'obstacle est la voie.", "author": "Marc Aurèle", "source": "Pensées"},
    {"text": "On ne devient pas ce qu'on veut, on devient ce qu'on est.", "author": "Carl Jung", "source": ""},
    {"text": "La discipline est le pont entre les objectifs et les accomplissements.", "author": "Jim Rohn", "source": ""},
    {"text": "Ce qui nous arrive importe moins que la façon dont nous y répondons.", "author": "Épictète", "source": "Manuel"},
    {"text": "Les grandes œuvres se font avec patience et obstination.", "author": "Voltaire", "source": ""},
    {"text": "Ce que nous faisons aujourd'hui détermine ce que nous serons demain.", "author": "Anonyme", "source": ""},
    {"text": "Agir avec constance vaut mieux qu'agir avec brio.", "author": "Sénèque", "source": ""},
    {"text": "La meilleure façon de prévoir l'avenir, c'est de le créer.", "author": "Peter Drucker", "source": ""},
]


@missing_router.get("/quote/today")
async def quote_today():
    """Retourne la citation du jour (déterministe par date, varie selon spiritualité user pour V2)."""
    day_idx = datetime.now(timezone.utc).timetuple().tm_yday
    q = _QUOTES[day_idx % len(_QUOTES)]
    return {**q, "date": datetime.now(timezone.utc).date().isoformat()}


# ─────────────────────────────────────────────────────────────────────
# GET/PATCH /api/me/profile — profil utilisateur (lecture / écriture)
# ─────────────────────────────────────────────────────────────────────
class ProfilePatch(BaseModel):
    name: Optional[str] = None
    memory: Optional[str] = None
    settings: Optional[dict] = None


@missing_router.get("/me/profile")
async def get_my_profile(user=Depends(get_current_user)):
    """Retourne le profil utilisateur courant (subset de /api/auth/me)."""
    s = user.settings or {}
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "plan": user.plan,
        "memory": user.memory,
        "first_name": s.get("first_name"),
        "why": s.get("why"),
        "spirituality": s.get("spirituality"),
        "onboarding_completed": bool(s.get("onboarding_completed")),
        "settings": s,
    }


@missing_router.patch("/me/profile")
async def patch_my_profile(
    body: ProfilePatch,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Met à jour name, memory et settings (merge)."""
    if body.name is not None:
        user.name = body.name[:120]
    if body.memory is not None:
        user.memory = body.memory[:5000]
    if body.settings is not None:
        cur = dict(user.settings or {})
        cur.update(body.settings)
        user.settings = cur
    await db.commit()
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────
# Admin stubs — pour que Admin.js ne crashe pas sur les onglets vides
# (à enrichir si vous voulez piloter ces données réellement)
# ─────────────────────────────────────────────────────────────────────
@missing_router.get("/admin/services-status")
async def admin_services_status(admin=Depends(require_admin)):
    """Statut des services externes (Brevo, Stripe/Mollie, DB, Make…)."""
    import os
    return {
        "services": [
            {"name": "Database", "status": "ok"},
            {"name": "Brevo", "status": "ok" if os.environ.get("BREVO_API_KEY") else "missing_key"},
            {"name": "Mollie", "status": "ok" if os.environ.get("MOLLIE_API_KEY") else "missing_key"},
            {"name": "OpenAI", "status": "ok" if os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY") else "missing_key"},
            {"name": "Make/Zapier", "status": "ok" if os.environ.get("MAKE_WEBHOOK_URL") else "not_configured"},
        ],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@missing_router.get("/admin/quotes")
async def admin_quotes(admin=Depends(require_admin)):
    """Liste des citations utilisées par /api/quote/today."""
    return {"quotes": _QUOTES, "total": len(_QUOTES)}


@missing_router.get("/admin/security/summary")
async def admin_security_summary(admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Synthèse sécurité : 2FA actifs, derniers logins, etc."""
    total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    twofa = (await db.execute(select(func.count(User.id)).where(User.two_factor_enabled == True))).scalar() or 0
    return {
        "users_total": total,
        "users_2fa_enabled": twofa,
        "users_2fa_coverage_pct": round((twofa / total * 100) if total else 0, 1),
        "failed_logins_24h": 0,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@missing_router.get("/admin/tickets")
async def admin_tickets(admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Tickets de support — pour l'instant on remonte les messages contact en file."""
    result = await db.execute(
        select(ContactMessage).order_by(ContactMessage.created_at.desc()).limit(50)
    )
    rows = result.scalars().all()
    return {
        "tickets": [{
            "id": r.id,
            "from": r.email,
            "name": r.name,
            "subject": r.subject,
            "message": r.message[:200],
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "status": "open",
        } for r in rows],
        "total": len(rows),
    }


@missing_router.get("/admin/logs/recent")
async def admin_logs_recent(limit: int = 100, admin=Depends(require_admin)):
    """Récents logs serveur — stub simple."""
    return {"logs": [], "limit": limit, "note": "Endpoint stub — connectez votre source de logs ici (Loki/Datadog/etc.)"}


@missing_router.get("/admin/ai/config")
async def admin_ai_config(admin=Depends(require_admin)):
    """Config IA actuelle (modèles utilisés, clés masquées)."""
    import os
    return {
        "default_text_model": os.environ.get("DEFAULT_TEXT_MODEL", "gpt-5.2"),
        "default_image_model": os.environ.get("DEFAULT_IMAGE_MODEL", "nano-banana"),
        "emergent_llm_key": "***" if os.environ.get("EMERGENT_LLM_KEY") else None,
        "openai_key": "***" if os.environ.get("OPENAI_API_KEY") else None,
    }


@missing_router.get("/admin/ai/stats")
async def admin_ai_stats(admin=Depends(require_admin)):
    return {"calls_24h": 0, "tokens_24h": 0, "cost_24h_eur": 0, "note": "Stub — branchez votre log d'usage IA"}


@missing_router.get("/admin/legacy/stats")
async def admin_legacy_stats(admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Stats legacy (compat ancien dashboard) — shape attendu par Admin.js DashboardSection."""
    from datetime import datetime, timezone, timedelta
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    by_plan_rows = (await db.execute(
        select(User.plan, func.count(User.id)).group_by(User.plan)
    )).all()
    by_plan = {p or "free": int(c) for p, c in by_plan_rows}
    paying = sum(v for k, v in by_plan.items() if k != "free")
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    active_30d = (await db.execute(
        select(func.count(User.id)).where(User.last_login_at >= cutoff)
    )).scalar() or 0
    new_30d = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= cutoff)
    )).scalar() or 0
    return {
        # ── Legacy flat keys (compat éventuelle) ──────────────────
        "users_total": int(total_users),
        "users_pro": int(by_plan.get("pro", 0)),
        "users_free": int(by_plan.get("free", 0)),
        "signups_30d": int(new_30d),
        "mrr_eur": 0,
        # ── Nested shape attendu par Admin.js DashboardSection ───
        "users": {
            "total": int(total_users),
            "active_30d": int(active_30d),
            "new_30d": int(new_30d),
            "paying": int(paying),
            "by_plan": by_plan,
        },
        "revenue": {"total_30d": 0.0, "currency": "EUR"},
        "newsletters": {"incoming_total": 0, "prepared_total": 0, "drafts": 0},
    }


@missing_router.get("/admin/legacy/users")
async def admin_legacy_users(
    search: str = "",
    limit: int = 200,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(User).order_by(User.created_at.desc())
    if search:
        like = f"%{search}%"
        q = q.where((User.email.ilike(like)) | (User.name.ilike(like)))
    q = q.limit(min(limit, 500))
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "user_id": u.id,
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "plan": u.plan or "free",
            "role": u.role or "user",
            "provider": getattr(u, "provider", None) or ("google" if getattr(u, "google_id", None) else "email"),
            "is_admin": (u.role in ("admin", "super_admin")),
            "credits": u.credits or 0,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in rows
    ]


@missing_router.get("/admin/legacy/users/stats")
async def admin_legacy_users_stats(admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timezone, timedelta
    total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    # by plan
    by_plan_rows = (await db.execute(
        select(User.plan, func.count(User.id)).group_by(User.plan)
    )).all()
    by_plan = {p or "free": int(c) for p, c in by_plan_rows}
    # active last 30d
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    active_30d = (await db.execute(
        select(func.count(User.id)).where(User.last_login_at >= cutoff)
    )).scalar() or 0
    # signups last 30d
    new_30d = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= cutoff)
    )).scalar() or 0
    paying = sum(v for k, v in by_plan.items() if k != "free")
    return {
        "total": total,
        "active_30d": int(active_30d),
        "new_30d": int(new_30d),
        "paying": int(paying),
        "by_plan": by_plan,
        "users": {
            "total": total,
            "active_30d": int(active_30d),
            "new_30d": int(new_30d),
            "paying": int(paying),
            "by_plan": by_plan,
        },
    }


@missing_router.get("/admin/legacy/transactions")
async def admin_legacy_transactions(admin=Depends(require_admin)):
    return {"transactions": [], "total": 0}
