"""
Config Routes — public config, migration, health
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import uuid, logging

from database import get_db, async_session_factory
from deps import get_current_user
from utils import load_admin_config, save_admin_config, logger as utils_logger

logger = logging.getLogger(__name__)
config_router = APIRouter(tags=["Config"])

DEFAULT_SEO_CONFIG = {
    "site_name": "Zayado IA",
    "tagline": "Votre assistant IA professionnel",
    "description": "Zayado IA — assistant IA pour freelances et PME",
    "keywords": "IA, assistant, productivité, freelance, PME",
    "og_image": "",
    "favicon": "",
    "logo_url": "",
    "extension_logo_url": "",
    "primary_color": "#1E3A8A",
}

@config_router.get("/public")
async def get_public_config():
    """Public config for frontend (OAuth IDs, logo, SEO)."""
    config = load_admin_config()
    seo = config.get("seo", {})
    result = {**DEFAULT_SEO_CONFIG, **seo}
    # Add OAuth public IDs
    import os
    result["google_client_id"] = os.environ.get("GOOGLE_CLIENT_ID", "")
    result["microsoft_client_id"] = os.environ.get("MICROSOFT_CLIENT_ID", "")
    result["maintenance_mode"] = config.get("maintenance_mode", False)
    result["maintenance_message"] = config.get("maintenance_message", "")
    return result

@config_router.get("/migrate-db")
async def migrate_db():
    """Run safe column migrations on demand."""
    results = []
    async with async_session_factory() as db:
        from sqlalchemy import text
        all_migrations = {
            "users": [
                ("two_factor_enabled",  "BOOLEAN DEFAULT FALSE"),
                ("is_active",           "BOOLEAN DEFAULT TRUE"),
                ("discount_type",       "VARCHAR(30) DEFAULT NULL"),
                ("discount_percent",    "INT DEFAULT 0"),
                ("discount_verified",   "BOOLEAN DEFAULT FALSE"),
                ("discount_doc_url",    "VARCHAR(500) DEFAULT NULL"),
                ("partner_code",        "VARCHAR(50) DEFAULT NULL"),
                ("partner_url",         "VARCHAR(500) DEFAULT NULL"),
                ("thesustain_member",   "BOOLEAN DEFAULT FALSE"),
                ("thesustain_type",     "VARCHAR(30) DEFAULT NULL"),
                ("memory",              "TEXT DEFAULT NULL"),
                ("last_login_at",       "DATETIME DEFAULT NULL"),
                ("purchased_credits",   "INT DEFAULT 0"),
                ("bonus_credits",       "INT DEFAULT 0"),
                ("settings",            "JSON"),
                ("referral_code",       "VARCHAR(50) DEFAULT NULL"),
                ("referral_count",      "INT DEFAULT 0"),
            ],
            "folders": [
                ("description",      "TEXT DEFAULT NULL"),
                ("knowledge_notes",  "TEXT DEFAULT NULL"),
                ("ai_intro",         "TEXT DEFAULT NULL"),
                ("updated_at",       "DATETIME DEFAULT NULL"),
                ("team_id",          "VARCHAR(36) DEFAULT NULL"),
            ],
            "conversations": [
                ("folder_id",            "VARCHAR(36) DEFAULT NULL"),
                ("is_favorite",          "BOOLEAN DEFAULT FALSE"),
                ("shared",               "BOOLEAN DEFAULT FALSE"),
                ("share_id",             "VARCHAR(36) DEFAULT NULL"),
                ("manus_task_id",        "VARCHAR(255) DEFAULT NULL"),
                ("total_credits_used",   "INT DEFAULT 0"),
                ("updated_at",           "DATETIME DEFAULT NULL"),
            ],
            "projects": [
                ("total_time_seconds",   "INT DEFAULT 0"),
                ("is_running",           "BOOLEAN DEFAULT FALSE"),
                ("timer_started_at",     "DATETIME DEFAULT NULL"),
                ("color",                "VARCHAR(20) DEFAULT '#1E3A8A'"),
                ("hourly_rate",          "FLOAT DEFAULT 0"),
                ("updated_at",           "DATETIME DEFAULT NULL"),
            ],
            "workflows": [
                ("updated_at",   "DATETIME DEFAULT NULL"),
                ("last_run_at",  "DATETIME DEFAULT NULL"),
                ("run_count",    "INT DEFAULT 0"),
            ],
        }
        for table, columns in all_migrations.items():
            for col_name, col_def in columns:
                try:
                    import re as _re_m
                    if not _re_m.match(r'^[a-z_]+$', table) or not _re_m.match(r'^[a-z_]+$', col_name):
                        results.append(f"{table}.{col_name}: SKIPPED (invalid identifier)")
                        continue
                    await db.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
                    await db.commit()
                    results.append(f"{table}.{col_name}: ADDED")
                except Exception:
                    await db.rollback()
                    results.append(f"{table}.{col_name}: exists")
        # Fix credits for free users with 0
        try:
            r = await db.execute(text("UPDATE users SET credits = 180 WHERE credits = 0 AND (plan = 'free' OR plan IS NULL)"))
            await db.commit()
            results.append(f"credits fixed: {r.rowcount} users")
        except Exception as e:
            await db.rollback()
            results.append(f"credits fix error: {e}")
    return {"status": "migration complete", "results": results}
