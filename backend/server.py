"""
Zayado IA — server.py (refactorisé)
Anciennement 5100 lignes → maintenant ~200 lignes.
Toutes les routes sont dans backend/routes/
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv
import os, asyncio, logging
from datetime import datetime, timezone
from sqlalchemy import select

from database import init_db, async_session_factory
from deps import JWT_SECRET, JWT_ALGORITHM
from utils import (
    load_admin_config,
    UPLOADS_DIR, GENERATED_IMAGES_DIR, MAMMOTH_BASE_URL,
    logger as utils_logger,
)

# ── Routers déjà dans /routes ──────────────────────────────────────────
from routes.auth       import auth_router
from routes.folders    import folders_router
from routes.projects   import projects_router
from routes.workflows  import workflows_router
from routes.oauth      import oauth_router
from routes.profile    import profile_router
from routes.revision   import revision_router
from routes.gdrive     import drive_router
from routes.onedrive   import onedrive_router
from routes.agent      import agent_router
from routes.dashboard  import router as dashboard_router
from routes.vision_board import router as vision_board_router
from routes.complexity import complexity_router
from routes.support    import support_router
from routes.team       import team_router
from routes.knowledge  import knowledge_router
from routes.payments   import payments_router as _payments_router_v1
from routes.affiliate  import affiliate_router

# ── Nouveaux modules extraits ──────────────────────────────────────────
from routes.chat_routes     import chat_router
from routes.payments_routes import payments_router
from routes.admin_routes    import admin_router, admin_payments_router, admin_api_router, admin_auth_router, admin_chat_router
from routes.public_routes   import api_router   # health, uploads, timer, seo, kyb...
from routes.agent_webhooks  import agent_webhook_router
from routes.config_routes   import config_router
from routes.features        import features_router, onboarding_alias_router
from routes.prompts         import prompts_router
from routes.finance         import finance_router
from routes.wellness        import wellness_router
from routes.activite        import activite_router
from routes.memory          import memory_router
from routes.newsletters     import newsletters_router
from routes.license         import license_router
from routes.processes       import processes_router
from routes.custom_agents   import custom_agents_router
from routes.audit           import audit_router
from routes.integrations    import integrations_router
from routes.app_logs        import app_logs_router
from routes.connections     import connections_router
from routes.shop            import shop_router
from routes.missing_endpoints import missing_router as legacy_missing_router
from routes.campaigns       import campaigns_router
from routes.notifications   import notif_router
from routes.push            import push_router
from routes.missing_apis    import missing_router
from routes.wp_sync         import wp_router
from routes.missing_apis    import missing_router
from routes.swot_cron       import swot_router, monthly_swot_loop
from routes.branding        import branding_router
from routes.churn_cron      import churn_router, inactivity_alerts_loop, _gdpr_purge_loop
from routes.collab_memory   import memory_router as collab_memory_router
from routes.hot_opportunities import hot_opps_router, hot_opportunities_scan_loop
from routes.automations import automations_router, automations_cron_loop
from routes.pilotage_bank import pilotage_bank_router
from routes.collab_queue import queue_router
from routes.collab_queue import queue_router

# ── Config ────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent
_STATIC_DIR = ROOT_DIR / "static"
load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

async def _sync_react_to_wp_on_startup():
    """Pousse les pages React seed vers WordPress automatiquement au démarrage.

    Comportement :
        - Pages absentes dans WP → CRÉÉES avec contenu seed
        - Pages existantes dans WP → MISES À JOUR avec le contenu seed (force=True)
        - Sauf si env ZAYADO_PRESERVE_WP_EDITS=1 → force=False (préserve les edits manuels)
    """
    await asyncio.sleep(15)
    try:
        import sys as _sys
        if "/app/scripts" not in _sys.path:
            _sys.path.insert(0, "/app/scripts")
        from seed_wp_pages import sync_all_pages_to_wp
        preserve = os.environ.get("ZAYADO_PRESERVE_WP_EDITS", "").strip() in ("1", "true", "yes")
        force = not preserve
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, lambda: sync_all_pages_to_wp(force=force))
        logger.info(f"[STARTUP-SYNC] React → WP : {stats}")
    except Exception as e:
        logger.warning(f"[STARTUP-SYNC] React → WP failed (non-blocking): {e}")


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan handler (replaces deprecated on_event) — fix #8."""
    try:
        await init_db()
    except Exception as _init_err:
        logger.error(f"DB init failed (server still starting): {_init_err}")
    asyncio.create_task(_weekly_cron_loop())
    asyncio.create_task(_auto_migrate_on_startup())
    asyncio.create_task(_rate_limiter_cleanup_loop())
    asyncio.create_task(_weekly_email_report_loop())
    asyncio.create_task(_workflow_scheduler_loop())
    asyncio.create_task(_monthly_credit_reset_loop())
    asyncio.create_task(monthly_swot_loop())
    asyncio.create_task(inactivity_alerts_loop())
    asyncio.create_task(_gdpr_purge_loop())
    asyncio.create_task(hot_opportunities_scan_loop())
    asyncio.create_task(automations_cron_loop())
    # ── Sync React → WP au démarrage (push automatique du contenu seed) ──
    asyncio.create_task(_sync_react_to_wp_on_startup())
    logger.info("Zayado API demarree")
    try:
        from utils import log_system_event
        log_system_event("server_start", "Zayado API v2.5.0 démarrée", "info")
    except Exception:
        pass
    yield
    logger.info("Zayado API arretee")

# ── App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Zayado IA API",
    version="2.5.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

_cors_env = os.environ.get("CORS_ORIGINS", "")
ALLOWED_ORIGINS = ["*"] if _cors_env == "*" else [
    "https://app.zayado.net",
    "https://www.zayado.net",
    "https://zayado.net",
    os.environ.get("FRONTEND_URL", "http://localhost:3000"),
    os.environ.get("REACT_APP_BACKEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount all routers under /api ───────────────────────────────────────
app.include_router(api_router,        prefix="/api")
app.include_router(config_router,     prefix="/api/config")
app.include_router(features_router,   prefix="/api/features")
app.include_router(onboarding_alias_router, prefix="/api")
app.include_router(prompts_router,    prefix="/api/prompts")
app.include_router(auth_router,       prefix="/api")
app.include_router(chat_router,       prefix="/api/chat")
app.include_router(payments_router,   prefix="/api/payments")
app.include_router(affiliate_router,  prefix="/api")
app.include_router(admin_router,      prefix="/api/admin")
app.include_router(app_logs_router,   prefix="/api/admin")
app.include_router(admin_payments_router, prefix="/api/payments")
app.include_router(admin_api_router,      prefix="/api")
app.include_router(admin_auth_router,     prefix="/api/auth")
app.include_router(admin_chat_router,     prefix="/api/chat")
app.include_router(folders_router,    prefix="/api")
app.include_router(projects_router,   prefix="/api")
app.include_router(workflows_router,  prefix="/api")
app.include_router(oauth_router,      prefix="/api")
app.include_router(profile_router,    prefix="/api")
app.include_router(revision_router,   prefix="/api")
app.include_router(drive_router,      prefix="/api")
app.include_router(onedrive_router,   prefix="/api")
app.include_router(agent_router,      prefix="/api")
# Cockpit endpoints ported from MongoDB backend
app.include_router(dashboard_router)

# ── Vision Board (reprise) — routers MongoDB/motor compatibles avec VisionBoardPage.jsx
#    (remplace l'ancien vision_board_router final-main pour éviter le conflit /api/vision/board)
from motor.motor_asyncio import AsyncIOMotorClient as _RepriseMongoClient
import vision_board as _reprise_vision
import heyzine as _reprise_heyzine
import canva as _reprise_canva
_reprise_mongo = _RepriseMongoClient(os.environ['MONGO_URL'])
_reprise_db = _reprise_mongo[os.environ['DB_NAME']]
app.include_router(_reprise_vision.build_router(_reprise_db), prefix="/api")
app.include_router(_reprise_heyzine.build_router(_reprise_db), prefix="/api")
app.include_router(_reprise_canva.build_router(_reprise_db), prefix="/api")
app.include_router(complexity_router, prefix="/api")
app.include_router(support_router,    prefix="/api")
app.include_router(team_router,       prefix="/api")
app.include_router(knowledge_router,  prefix="/api")
app.include_router(finance_router,    prefix="/api")
app.include_router(wellness_router,   prefix="/api")
app.include_router(activite_router,   prefix="/api")
app.include_router(memory_router,     prefix="/api/memory")
app.include_router(newsletters_router, prefix="/api")
app.include_router(processes_router,  prefix="/api")
app.include_router(license_router,    prefix="/api")
app.include_router(custom_agents_router, prefix="/api")
app.include_router(audit_router,          prefix="/api")
app.include_router(integrations_router,   prefix="/api")
app.include_router(connections_router,    prefix="/api")
app.include_router(shop_router,           prefix="/api")
app.include_router(legacy_missing_router, prefix="/api")
app.include_router(campaigns_router,      prefix="/api")
app.include_router(notif_router,          prefix="/api")
app.include_router(push_router,           prefix="/api")
app.include_router(missing_router,        prefix="/api")
app.include_router(wp_router,             prefix="/api")
app.include_router(missing_router,        prefix="/api")
app.include_router(swot_router,           prefix="/api")
app.include_router(branding_router,       prefix="/api")
app.include_router(churn_router,          prefix="/api")
app.include_router(collab_memory_router,  prefix="/api")
app.include_router(hot_opps_router)
app.include_router(automations_router)
app.include_router(pilotage_bank_router, prefix="/api", tags=["pilotage-bank"])
app.include_router(queue_router, prefix="/api")
app.include_router(queue_router, prefix="/api", tags=["ia-queue"])
app.include_router(agent_webhook_router,  prefix="/api")

# ── Background tasks ──────────────────────────────────────────────

async def _rate_limiter_cleanup_loop():
    """Periodic cleanup of rate limiter store (every 30 min)."""
    from utils import rate_limiter
    while True:
        await asyncio.sleep(1800)
        try:
            rate_limiter.cleanup()
        except Exception:
            pass

async def _weekly_cron_loop():
    """Weekly cleanup cron."""
    while True:
        await asyncio.sleep(7 * 24 * 3600)
        try:
            async with async_session_factory() as db:
                from sqlalchemy import text
                from datetime import datetime, timedelta, timezone
                cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
                await db.execute(text(
                    "DELETE FROM conversations WHERE created_at < :cutoff "
                    "AND is_favorite = FALSE"
                ), {"cutoff": cutoff})
                await db.commit()
                logger.info("[CRON] Old conversations cleaned")
        except Exception as e:
            logger.warning(f"[CRON] Error: {e}")

async def _auto_migrate_on_startup():
    """Safe idempotent column migration on every startup."""
    await asyncio.sleep(3)
    try:
        async with async_session_factory() as db:
            from sqlalchemy import text
            migrations = {
                "projects": [
                    ("total_time_seconds", "INT DEFAULT 0"),
                    ("is_running",        "BOOLEAN DEFAULT FALSE"),
                    ("timer_started_at",  "DATETIME NULL"),
                    ("color",             "VARCHAR(20) DEFAULT '#1E3A8A'"),
                    ("hourly_rate",       "FLOAT DEFAULT 0"),
                    ("updated_at",        "DATETIME NULL"),
                ],
                "users": [
                    ("purchased_credits", "INT DEFAULT 0"),
                    ("bonus_credits",     "INT DEFAULT 0"),
                    ("credits_last_reset","DATETIME NULL"),
                    ("memory",            "TEXT NULL"),
                    ("last_login_at",     "DATETIME NULL"),
                    ("oauth_provider",    "VARCHAR(20) NULL"),
                    ("oauth_id",          "VARCHAR(255) NULL"),
                    ("referral_code",     "VARCHAR(50) NULL"),
                    ("referred_by",       "VARCHAR(36) NULL"),
                    ("two_factor_enabled","BOOLEAN DEFAULT FALSE"),
                    ("is_active",         "BOOLEAN DEFAULT TRUE"),
                    ("discount_type",     "VARCHAR(30) NULL"),
                    ("discount_percent",  "INT DEFAULT 0"),
                    ("discount_verified", "BOOLEAN DEFAULT FALSE"),
                    ("discount_doc_url",  "VARCHAR(500) NULL"),
                    ("discount_expires_at","DATETIME NULL"),
                    ("cancel_at_period_end","BOOLEAN DEFAULT FALSE"),
                    ("cancellation_reason","VARCHAR(500) NULL"),
                    ("partner_code",      "VARCHAR(50) NULL"),
                    ("partner_url",       "VARCHAR(500) NULL"),
                    ("thesustain_member", "BOOLEAN DEFAULT FALSE"),
                    ("thesustain_type",   "VARCHAR(30) NULL"),
                    ("updated_at",        "DATETIME NULL"),
                ],
                "conversations": [
                    ("folder_id",  "VARCHAR(36) NULL"),
                    ("is_favorite","BOOLEAN DEFAULT FALSE"),
                    ("shared",     "BOOLEAN DEFAULT FALSE"),
                    ("share_id",   "VARCHAR(36) NULL"),
                    ("updated_at", "DATETIME NULL"),
                ],
                "workflows": [
                    ("last_run_at", "DATETIME NULL"),
                    ("run_count",   "INT DEFAULT 0"),
                ],
                "custom_agents": [
                    ("team_id",           "VARCHAR(36) NULL"),
                    ("deployed_channels", "JSON NULL"),
                    ("webhook_token",     "VARCHAR(64) NULL"),
                    ("usage_count",       "INT DEFAULT 0"),
                    ("is_public",         "BOOLEAN DEFAULT FALSE"),
                    ("is_active",         "BOOLEAN DEFAULT TRUE"),
                    ("temperature",       "FLOAT DEFAULT 0.7"),
                    ("max_tokens",        "INT DEFAULT 4096"),
                    ("use_user_memory",   "BOOLEAN DEFAULT TRUE"),
                ],
                "user_connections": [
                    ("label",               "VARCHAR(255) NULL"),
                    ("is_active",           "BOOLEAN DEFAULT TRUE"),
                    ("is_verified",         "BOOLEAN DEFAULT FALSE"),
                    ("verification_token",  "VARCHAR(100) NULL"),
                    ("last_used_at",        "DATETIME NULL"),
                    ("revoked_at",          "DATETIME NULL"),
                ],
                "credit_logs": [
                    ("mode",            "VARCHAR(20) NULL"),
                    ("conversation_id", "VARCHAR(36) NULL"),
                ],
            }
            for table, cols in migrations.items():
                for col, defn in cols:
                    try:
                        # Use text() with sanitized identifiers (hardcoded values only — #14 fix)
                        # SQLAlchemy text() doesn't support parameterized DDL identifiers,
                        # but table/col values are from a hardcoded dict (not user input).
                        import re as _re_migrate
                        if not _re_migrate.match(r'^[a-z_]+$', table) or not _re_migrate.match(r'^[a-z_]+$', col):
                            logger.warning(f"[AUTOMIGRATE] Skipping invalid identifier: {table}.{col}")
                            continue
                        await db.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {defn}"))
                        await db.commit()
                    except Exception:
                        await db.rollback()
        logger.info("[AUTOMIGRATE] ✅ Done")
        # Seed retention promo code RESTE30
        try:
            async with async_session_factory() as db:
                from models import PromoCode
                existing = await db.execute(select(PromoCode).where(PromoCode.code == "RESTE30"))
                if not existing.scalar_one_or_none():
                    promo = PromoCode(code="RESTE30", type="discount", value=30, max_uses=9999, active=True)
                    db.add(promo)
                    await db.commit()
                    logger.info("[SEED] Retention promo RESTE30 created")
        except Exception as seed_err:
            logger.warning(f"[SEED] RESTE30 seed error: {seed_err}")
    except Exception as e:
        logger.warning(f"[AUTOMIGRATE] {e}")

async def _weekly_email_report_loop():
    """Launch the weekly email report cron from public_routes (#15 fix)."""
    from routes.public_routes import _weekly_cron_loop as _weekly_email_cron
    await _weekly_email_cron()


async def _monthly_credit_reset_loop():
    """Reset monthly credits for all paid users on the 1st of each month.
    Runs every hour. Also carries unused credits to bonus (capped at 1 month max)."""
    await asyncio.sleep(20)
    from sqlalchemy import select, update
    from models import User
    from utils import SUBSCRIPTION_PLANS

    logger.info("[CREDIT_RESET] Monthly credit reset loop started")
    while True:
        try:
            now = datetime.now(timezone.utc)
            async with async_session_factory() as db:
                result = await db.execute(
                    select(User).where(User.plan != "free")
                )
                users = result.scalars().all()
                reset_count = 0
                for u in users:
                    try:
                        last_reset = u.credits_last_reset if hasattr(u, 'credits_last_reset') else None
                        needs_reset = False
                        if last_reset is None:
                            # Jamais reseté — utiliser created_at comme référence
                            # Si créé il y a plus de 30 jours, reset maintenant
                            created = u.created_at if hasattr(u, 'created_at') and u.created_at else None
                            if created is None:
                                needs_reset = True
                            else:
                                created_aware = created.replace(tzinfo=timezone.utc) if created.tzinfo is None else created
                                needs_reset = (now - created_aware).days >= 30
                        else:
                            # Reset 30 jours après le dernier reset (basé sur date d'inscription)
                            last_reset_aware = last_reset.replace(tzinfo=timezone.utc) if last_reset.tzinfo is None else last_reset
                            needs_reset = (now - last_reset_aware).days >= 30

                        if needs_reset:
                            plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == u.plan), None)
                            if not plan:
                                continue
                            credits_per_month = plan.get("credits_per_month", 0)
                            bonus_cap = plan.get("bonus_cap", 0)
                            # Only BASE credits (not old bonus) carry over as new bonus
                            unused_base = u.credits or 0
                            # Old bonus is LOST — does NOT accumulate
                            new_bonus = min(unused_base, bonus_cap) if bonus_cap > 0 else 0

                            await db.execute(
                                update(User).where(User.id == u.id).values(
                                    credits=credits_per_month,
                                    bonus_credits=new_bonus,
                                    credits_last_reset=now
                                )
                            )
                            reset_count += 1
                    except Exception as ue:
                        logger.warning(f"[CREDIT_RESET] Error for user {u.id}: {ue}")
                if reset_count > 0:
                    await db.commit()
                    logger.info(f"[CREDIT_RESET] Reset credits for {reset_count} users")
        except Exception as e:
            logger.warning(f"[CREDIT_RESET] Loop error: {e}")
        await asyncio.sleep(3600)  # Check every hour


async def _workflow_scheduler_loop():
    """Background scheduler for workflows with schedule (daily/weekly/monthly).
    Checks every 10 minutes for workflows that need to run."""
    await asyncio.sleep(15)  # Wait for startup to complete
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, update
    from models import Workflow, User

    logger.info("[SCHEDULER] Workflow scheduler started")
    while True:
        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    select(Workflow).where(
                        Workflow.status == "active",
                        Workflow.schedule != None
                    )
                )
                workflows = result.scalars().all()

                now = datetime.now(timezone.utc)
                for wf in workflows:
                    try:
                        schedule = wf.schedule
                        if not schedule:
                            continue
                        last_run = wf.last_run
                        should_run = False

                        if schedule == "daily":
                            should_run = not last_run or (now - last_run) >= timedelta(hours=23)
                        elif schedule == "weekly":
                            should_run = not last_run or (now - last_run) >= timedelta(days=6, hours=23)
                        elif schedule == "monthly":
                            should_run = not last_run or (now - last_run) >= timedelta(days=29)
                        elif schedule == "hourly":
                            should_run = not last_run or (now - last_run) >= timedelta(minutes=55)

                        if should_run:
                            logger.info(f"[SCHEDULER] Running workflow '{wf.name}' (id={wf.id}, schedule={schedule})")
                            # Mark as running
                            await db.execute(
                                update(Workflow).where(Workflow.id == wf.id).values(status="running")
                            )
                            await db.commit()

                            # Execute steps
                            import httpx, os
                            mammoth_key = os.environ.get('MAMMOTH_API_KEY', '')
                            step_results = []
                            for i, step in enumerate(wf.steps or []):
                                step_prompt = step.get("prompt") or step.get("content") or step.get("label") or step.get("name") or f"Step {i+1}"
                                step_name = step.get("label") or step.get("name") or step.get("prompt") or f"Etape {i+1}"
                                if mammoth_key:
                                    try:
                                        async with httpx.AsyncClient(timeout=60.0) as http_client:
                                            response = await http_client.post(
                                                f"{MAMMOTH_BASE_URL}/chat/completions",
                                                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                                                json={"model": "claude-haiku-4-5-20251001", "messages": [{"role": "system", "content": "Tu es un assistant professionnel. Execute cette etape de workflow."}, {"role": "user", "content": step_prompt}], "max_tokens": 2048, "temperature": 0.3}
                                            )
                                            if response.status_code == 200:
                                                data = response.json()
                                                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                                                step_results.append({"step": i+1, "name": step_name, "result": content, "status": "completed"})
                                            else:
                                                step_results.append({"step": i+1, "name": step_name, "result": f"Error: {response.status_code}", "status": "error"})
                                    except Exception as e:
                                        step_results.append({"step": i+1, "name": step_name, "result": str(e), "status": "error"})
                                else:
                                    step_results.append({"step": i+1, "name": step_name, "result": "MAMMOTH_API_KEY non configure", "status": "error"})

                            exec_status = "completed" if all(r.get("status") == "completed" for r in step_results) else "error"
                            combined_result = "\n\n".join([f"### {r['name']}\n{r['result']}" for r in step_results])

                            await db.execute(
                                update(Workflow).where(Workflow.id == wf.id).values(
                                    status="active",
                                    result=combined_result,
                                    last_run=now
                                )
                            )
                            await db.commit()

                            # Send notification
                            user_result = await db.execute(select(User).where(User.id == wf.user_id))
                            user = user_result.scalar_one_or_none()
                            if user:
                                from routes.workflows import _send_workflow_notification
                                _send_workflow_notification(user, wf.name, exec_status, len(step_results))

                            logger.info(f"[SCHEDULER] Workflow '{wf.name}' completed: {exec_status}")
                    except Exception as wf_err:
                        logger.warning(f"[SCHEDULER] Error running workflow {wf.id}: {wf_err}")
                        try:
                            await db.execute(update(Workflow).where(Workflow.id == wf.id).values(status="active"))
                            await db.commit()
                        except Exception:
                            await db.rollback()
        except Exception as e:
            logger.warning(f"[SCHEDULER] Loop error: {e}")
        await asyncio.sleep(600)  # Check every 10 minutes

# ── Serve React SPA ───────────────────────────────────────────────────
# Public-site Vite build (preview only) — served at /api/preview-site/*
_PUBLIC_SITE_DIST = Path("/app/public-site/dist")
if _PUBLIC_SITE_DIST.exists():
    @app.get("/api/preview-site/{full_path:path}", include_in_schema=False)
    async def preview_site(full_path: str):
        if full_path:
            requested = (_PUBLIC_SITE_DIST / full_path).resolve()
            if requested.is_file() and str(requested).startswith(str(_PUBLIC_SITE_DIST.resolve())):
                return FileResponse(str(requested))
        # SPA fallback
        return FileResponse(str(_PUBLIC_SITE_DIST / "index.html"))

    @app.get("/api/preview-site", include_in_schema=False)
    async def preview_site_root():
        return FileResponse(str(_PUBLIC_SITE_DIST / "index.html"))

if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR / "static")), name="react-static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        requested = (_STATIC_DIR / full_path).resolve()
        # Sécurité path traversal : vérifier que le chemin résolu est bien sous _STATIC_DIR
        if full_path and requested.is_file() and str(requested).startswith(str(_STATIC_DIR.resolve())):
            return FileResponse(str(requested))
        index = _STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Frontend not built")
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Zayado API v2.5", "status": "running", "docs": "/api/docs"}
