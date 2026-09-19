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
from routes.growth_copilote import router as growth_copilote_router
from routes.growth import router as growth_router
from routes.prospection import router as prospection_router
# Espace vendeur multi-vendeurs + publication vers Shopify
from routes.vendeur import router as vendeur_router
from routes.global_search import router as global_search_router
from routes.prefs import router as prefs_router
from routes.vision_board import router as vision_board_router
from routes.vision_cards import router as vision_cards_router
from routes.vision_events import router as vision_events_router
from routes.news_digest import router as news_digest_router
from routes.analytics import router as analytics_router
from routes.gamification import router as gamification_router
from routes.vision_ext import router as vision_ext_router
from routes.vision_brain import vision_brain_router
from routes.studio import router as studio_router
from routes.simulation import simulation_router
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
from routes.swot_cron       import swot_router, monthly_swot_loop
from routes.branding        import branding_router
from routes.churn_cron      import churn_router, inactivity_alerts_loop, _gdpr_purge_loop
from routes.agent_livraison import agent_livraison_loop
from routes.collab_memory   import memory_router as collab_memory_router
from routes.hot_opportunities import hot_opps_router, hot_opportunities_scan_loop
from routes.automations import automations_router, automations_cron_loop
from routes.travail import travail_router
from routes.pilotage_bank import pilotage_bank_router
from routes.collab_queue import queue_router
from routes.vision_weekly_email import vision_weekly_email_loop
from routes.heygen_routes import heygen_router
from routes.news_reprise import news_reprise_router
from routes.inspiration import inspiration_router
from routes.demo import demo_router

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
    except (Exception, SystemExit) as e:
        logger.warning(f"[STARTUP-SYNC] React → WP failed (non-blocking): {e}")


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan handler (replaces deprecated on_event) — fix #8."""
    try:
        await init_db()
    except Exception as _init_err:
        logger.error(f"DB init failed (server still starting): {_init_err}")
    # Migration de schéma idempotente : toujours exécutée (sécurité prod).
    asyncio.create_task(_auto_migrate_on_startup())

    # ── Crons : lancés uniquement si RUN_CRONS=true ──────────────────────
    # En multi-replica, mettre RUN_CRONS=false sur les replicas web et lancer
    # UN worker dédié (worker.py) avec RUN_CRONS=true → évite les doublons.
    if os.environ.get("RUN_CRONS", "true").strip().lower() in ("1", "true", "yes"):
        logger.info("[CRONS] RUN_CRONS actif — démarrage des tâches planifiées")
        for _cron in (
            _weekly_cron_loop,
            _rate_limiter_cleanup_loop,
            _weekly_email_report_loop,
            _workflow_scheduler_loop,
            _monthly_credit_reset_loop,
            monthly_swot_loop,
            inactivity_alerts_loop,
            _gdpr_purge_loop,
            hot_opportunities_scan_loop,
            agent_livraison_loop,
            automations_cron_loop,
            vision_weekly_email_loop,
            _sync_react_to_wp_on_startup,
        ):
            asyncio.create_task(_cron())
    else:
        logger.info("[CRONS] RUN_CRONS désactivé — aucune tâche planifiée sur ce process")
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
    title="MyExtension IA API",
    version="2.5.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

_cors_env = os.environ.get("CORS_ORIGINS", "")
_default_origins = [
    "https://app.zayado.net",
    "https://www.zayado.net",
    "https://zayado.net",
    os.environ.get("FRONTEND_URL", "http://localhost:3000"),
    os.environ.get("REACT_APP_BACKEND_URL", ""),
]
# Correction audit : "*" + allow_credentials=True est une combinaison invalide/dangereuse
# (rejetee par les navigateurs, et risquee si contournee). On ignore "*" et on retombe
# toujours sur une liste blanche stricte. CORS_ORIGINS peut fournir une liste explicite
# separee par des virgules pour AJOUTER des origines (jamais "*").
if _cors_env and _cors_env != "*":
    ALLOWED_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    if _cors_env == "*":
        logger.warning('[CORS] CORS_ORIGINS="*" ignore (incompatible avec allow_credentials=True) — liste blanche stricte utilisee a la place.')
    ALLOWED_ORIGINS = [o for o in _default_origins if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Observabilité (backlog #27, point de départ minimal) ───────────────
# Pas de vraie stack d'observabilité (Sentry/Datadog) branchée ici — ça
# dépend d'un choix d'infra qui n'est pas fait. Ce endpoint est le strict
# minimum : un check santé exploitable par un load balancer / uptime
# monitor externe (UptimeRobot, Better Uptime...) et par le smoke-test CI
# (voir .github/workflows/ci.yml). Vérifie une vraie requête DB, pas
# juste "le process tourne".
@app.get("/api/health", include_in_schema=False)
async def health_check():
    from database import async_session_factory
    from sqlalchemy import text as _text
    db_ok = False
    try:
        async with async_session_factory() as _db:
            await _db.execute(_text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.error(f"[HEALTH] DB check failed: {e}")
    status_code = 200 if db_ok else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=status_code, content={"status": "ok" if db_ok else "degraded", "db": db_ok})

# ── Mount all routers under /api ───────────────────────────────────────
app.include_router(api_router,        prefix="/api")
app.include_router(config_router,     prefix="/api/config")
app.include_router(features_router,   prefix="/api/features")
app.include_router(onboarding_alias_router, prefix="/api")
from routes.pilotage_overview import router as pilotage_overview_router
app.include_router(pilotage_overview_router, prefix="/api")
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
app.include_router(growth_copilote_router)
app.include_router(growth_router)
app.include_router(prospection_router)
app.include_router(vendeur_router)
app.include_router(global_search_router)
app.include_router(prefs_router)
app.include_router(vision_board_router)
app.include_router(vision_cards_router)
app.include_router(vision_events_router)
app.include_router(news_digest_router)
app.include_router(analytics_router)
app.include_router(gamification_router)
app.include_router(vision_brain_router, prefix="/api")
app.include_router(vision_ext_router)
app.include_router(studio_router)
app.include_router(simulation_router, prefix="/api")
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
from routes.copilot_persistence import router as copilot_persistence_router
app.include_router(copilot_persistence_router, prefix="/api")
app.include_router(wp_router,             prefix="/api")
app.include_router(missing_router,        prefix="/api")
app.include_router(swot_router,           prefix="/api")
app.include_router(branding_router,       prefix="/api")
app.include_router(churn_router,          prefix="/api")
app.include_router(collab_memory_router,  prefix="/api")
app.include_router(hot_opps_router)
app.include_router(automations_router)
app.include_router(travail_router, prefix="/api")
app.include_router(pilotage_bank_router, prefix="/api", tags=["pilotage-bank"])
app.include_router(queue_router, prefix="/api", tags=["ia-queue"])
app.include_router(agent_webhook_router,  prefix="/api")
app.include_router(heygen_router,          prefix="/api")
app.include_router(news_reprise_router,    prefix="/api")
app.include_router(inspiration_router,     prefix="/api")
app.include_router(demo_router,            prefix="/api")

# ── Static uploads (Studio images/videos + user uploads) ─────────
try:
    from routes.studio import UPLOADS_DIR as STUDIO_UPLOADS_DIR
    _uploads_parent = STUDIO_UPLOADS_DIR.parent
    _uploads_parent.mkdir(parents=True, exist_ok=True)
    app.mount("/api/uploads", StaticFiles(directory=str(_uploads_parent)), name="uploads")
except Exception as _e:
    pass

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
                    ("timer_started_at",  "TIMESTAMP NULL"),
                    ("color",             "VARCHAR(20) DEFAULT '#1E3A8A'"),
                    ("hourly_rate",       "FLOAT DEFAULT 0"),
                    ("updated_at",        "TIMESTAMP NULL"),
                ],
                "users": [
                    ("purchased_credits", "INT DEFAULT 0"),
                    ("bonus_credits",     "INT DEFAULT 0"),
                    ("credits_last_reset","TIMESTAMP NULL"),
                    ("memory",            "TEXT NULL"),
                    ("last_login_at",     "TIMESTAMP NULL"),
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
                    ("discount_expires_at","TIMESTAMP NULL"),
                    ("cancel_at_period_end","BOOLEAN DEFAULT FALSE"),
                    ("cancellation_reason","VARCHAR(500) NULL"),
                    ("partner_code",      "VARCHAR(50) NULL"),
                    ("partner_url",       "VARCHAR(500) NULL"),
                    ("thesustain_member", "BOOLEAN DEFAULT FALSE"),
                    ("thesustain_type",   "VARCHAR(30) NULL"),
                    ("updated_at",        "TIMESTAMP NULL"),
                ],
                "conversations": [
                    ("folder_id",  "VARCHAR(36) NULL"),
                    ("is_favorite","BOOLEAN DEFAULT FALSE"),
                    ("shared",     "BOOLEAN DEFAULT FALSE"),
                    ("share_id",   "VARCHAR(36) NULL"),
                    ("updated_at", "TIMESTAMP NULL"),
                ],
                "workflows": [
                    ("last_run_at", "TIMESTAMP NULL"),
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
                    ("last_used_at",        "TIMESTAMP NULL"),
                    ("revoked_at",          "TIMESTAMP NULL"),
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
    _REACT_STATIC = _STATIC_DIR / "static"
    if _REACT_STATIC.exists():
        app.mount("/static", StaticFiles(directory=str(_REACT_STATIC)), name="react-static")
    else:
        # Avant ce correctif : app.mount() levait RuntimeError si ce dossier
        # manquait (build frontend incomplet/pas encore copié), ce qui faisait
        # planter TOUT uvicorn au démarrage — API comprise. Un build frontend
        # cassé ne doit jamais empêcher l'API de répondre.
        logger.warning(f"'{_REACT_STATIC}' introuvable — assets statiques du frontend non montés, l'API reste disponible.")

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
