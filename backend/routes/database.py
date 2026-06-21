import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Build database URL
# MySQL in production (NODE_ENV=production + credentials), SQLite otherwise
DB_HOST = os.environ.get('DB_HOST') or os.environ.get('DB_HOST_PROD') or 'localhost'
DB_USER = os.environ.get('DB_USER') or os.environ.get('DB_USER_PROD')
DB_PASSWORD = os.environ.get('DB_PASSWORD') or os.environ.get('DB_PASSWORD_PROD')
DB_PORT = os.environ.get('DB_PORT') or os.environ.get('DB_PORT_PROD', '3306')
DB_NAME = (os.environ.get('DB_NAME') or os.environ.get('DB_DATABASE')
           or os.environ.get('DB_NAME_CUSTOM') or os.environ.get('DB_NAME_PROD'))
NODE_ENV = os.environ.get('NODE_ENV', 'development')

# ── Priorité 1 : DATABASE_URL fourni directement (Railway MySQL natif ou Hostinger)
_raw_url = os.environ.get('DATABASE_URL', '')
if _raw_url:
    # Railway fournit mysql:// mais asyncmy requiert mysql+asyncmy://
    if _raw_url.startswith('mysql://'):
        _raw_url = _raw_url.replace('mysql://', 'mysql+asyncmy://', 1)
    elif _raw_url.startswith('postgres://'):
        _raw_url = _raw_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    DATABASE_URL = _raw_url
    DB_TYPE = "mysql" if "mysql" in _raw_url else "postgres" if "postgres" in _raw_url else "sqlite"

# ── Priorité 2 : Variables séparées (Hostinger remote ou Railway custom)
elif NODE_ENV == 'production' and DB_USER and DB_PASSWORD and DB_NAME:
    DATABASE_URL = f"mysql+asyncmy://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DB_TYPE = "mysql"

# ── Priorité 3 : SQLite local (dev / fallback)
else:
    db_path = ROOT_DIR / "zayado.db"
    DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
    DB_TYPE = "sqlite"

import logging as _db_logging
_db_logger = _db_logging.getLogger("database")
_db_logger.info(f"Database mode: {DB_TYPE}")

_engine_kwargs = {"echo": False, "pool_pre_ping": True}
if DB_TYPE != "sqlite":
    _engine_kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_recycle": 1800, "pool_timeout": 30})
engine = create_async_engine(DATABASE_URL, **_engine_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async_session_factory = async_session

class Base(DeclarativeBase):
    pass

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Verify critical tables exist and migrate columns
    import logging
    logger = logging.getLogger("database")
    try:
        async with async_session() as session:
            from sqlalchemy import text as sa_text
            for table in ["feedbacks", "support_tickets"]:
                try:
                    await session.execute(sa_text(f"SELECT 1 FROM {table} LIMIT 1"))
                except Exception:
                    logger.warning(f"Table {table} not found, creating...")
                    async with engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)
                    break
    except Exception as e:
        logger.error(f"Table verification error: {e}")

    # Ensure all columns exist on teams/team_members (critical for MySQL prod)
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text as sa_text, inspect as sa_inspect
            def _check_and_add_columns(connection):
                insp = sa_inspect(connection)
                # Teams table columns
                if "teams" in insp.get_table_names():
                    existing = {c["name"] for c in insp.get_columns("teams")}
                    migrations = {
                        "team_code": "VARCHAR(32)",
                        "bot_name": "VARCHAR(100) DEFAULT 'Assistant'",
                        "bot_tone": "VARCHAR(30) DEFAULT 'professional'",
                        "bot_context": "TEXT",
                        "credit_limit_per_member": "INTEGER DEFAULT 50",
                        "auto_recharge": "BOOLEAN DEFAULT 0",
                        "chrome_link": "BOOLEAN DEFAULT 0",
                        "chatbot_enabled": "BOOLEAN DEFAULT 1",
                        "settings": "JSON",
                    }
                    for col, typedef in migrations.items():
                        if col not in existing:
                            try:
                                connection.execute(sa_text(f"ALTER TABLE teams ADD COLUMN {col} {typedef}"))
                                logger.info(f"Added column teams.{col}")
                            except Exception as ae:
                                logger.warning(f"Could not add teams.{col}: {ae}")
                # Team members table columns
                if "team_members" in insp.get_table_names():
                    existing = {c["name"] for c in insp.get_columns("team_members")}
                    tm_migrations = {
                        "invite_token": "VARCHAR(64)",
                        "credits_allocated": "INTEGER DEFAULT 0",
                    }
                    for col, typedef in tm_migrations.items():
                        if col not in existing:
                            try:
                                connection.execute(sa_text(f"ALTER TABLE team_members ADD COLUMN {col} {typedef}"))
                                logger.info(f"Added column team_members.{col}")
                            except Exception as ae:
                                logger.warning(f"Could not add team_members.{col}: {ae}")
                # Folders table - ensure team_id exists
                if "folders" in insp.get_table_names():
                    existing = {c["name"] for c in insp.get_columns("folders")}
                    if "team_id" not in existing:
                        try:
                            connection.execute(sa_text("ALTER TABLE folders ADD COLUMN team_id VARCHAR(36)"))
                            logger.info("Added column folders.team_id")
                        except Exception as ae:
                            logger.warning(f"Could not add folders.team_id: {ae}")
                # Projects table - ensure all columns exist
                if "projects" in insp.get_table_names():
                    existing = {c["name"] for c in insp.get_columns("projects")}
                    proj_migrations = {
                        "color": "VARCHAR(7) DEFAULT '#1E3A8A'",
                        "hourly_rate": "FLOAT DEFAULT 0",
                        "total_time_seconds": "INTEGER DEFAULT 0",
                        "is_running": "BOOLEAN DEFAULT 0",
                        "timer_started_at": "DATETIME",
                        "updated_at": "DATETIME",
                    }
                    for col, typedef in proj_migrations.items():
                        if col not in existing:
                            try:
                                connection.execute(sa_text(f"ALTER TABLE projects ADD COLUMN {col} {typedef}"))
                                logger.info(f"Added column projects.{col}")
                            except Exception as ae:
                                logger.warning(f"Could not add projects.{col}: {ae}")
                # Credit logs table - ensure conversation_id exists and team_id is nullable
                if "credit_logs" in insp.get_table_names():
                    existing = {c["name"] for c in insp.get_columns("credit_logs")}
                    cl_migrations = {
                        "conversation_id": "VARCHAR(36)",
                    }
                    for col, typedef in cl_migrations.items():
                        if col not in existing:
                            try:
                                connection.execute(sa_text(f"ALTER TABLE credit_logs ADD COLUMN {col} {typedef}"))
                                logger.info(f"Added column credit_logs.{col}")
                            except Exception as ae:
                                logger.warning(f"Could not add credit_logs.{col}: {ae}")
                    # Fix team_id to be nullable (was NOT NULL in some MySQL deployments)
                    if "team_id" in existing:
                        try:
                            connection.execute(sa_text("ALTER TABLE credit_logs MODIFY COLUMN team_id VARCHAR(36) NULL"))
                            logger.info("Fixed credit_logs.team_id to nullable")
                        except Exception:
                            pass  # SQLite doesn't support MODIFY, ignore
                # Api costs table - ensure conversation_id exists
                if "api_costs" in insp.get_table_names():
                    existing = {c["name"] for c in insp.get_columns("api_costs")}
                    ac_migrations = {
                        "conversation_id": "VARCHAR(36)",
                    }
                    for col, typedef in ac_migrations.items():
                        if col not in existing:
                            try:
                                connection.execute(sa_text(f"ALTER TABLE api_costs ADD COLUMN {col} {typedef}"))
                                logger.info(f"Added column api_costs.{col}")
                            except Exception as ae:
                                logger.warning(f"Could not add api_costs.{col}: {ae}")
            await conn.run_sync(_check_and_add_columns)
    except Exception as e:
        logger.error(f"Column migration error: {e}")

    # Ensure app_logs table exists (monitoring system)
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text as sa_text, inspect as sa_inspect
            def _ensure_app_logs(connection):
                insp = sa_inspect(connection)
                if "app_logs" not in insp.get_table_names():
                    connection.execute(sa_text("""
                        CREATE TABLE IF NOT EXISTS app_logs (
                            id VARCHAR(36) NOT NULL PRIMARY KEY,
                            level VARCHAR(10) NOT NULL,
                            feature VARCHAR(50) NOT NULL,
                            action VARCHAR(100),
                            user_id VARCHAR(36),
                            user_email VARCHAR(255),
                            message TEXT NOT NULL,
                            details TEXT,
                            ip_address VARCHAR(50),
                            duration_ms INTEGER,
                            created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                            INDEX idx_app_logs_level (level),
                            INDEX idx_app_logs_feature (feature),
                            INDEX idx_app_logs_created_at (created_at),
                            INDEX idx_app_logs_user_id (user_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """))
                    logger.info("Created table app_logs")
            await conn.run_sync(_ensure_app_logs)
    except Exception as e:
        logger.warning(f"app_logs table check error: {e}")

async def get_db():
    async with async_session() as session:
        yield session
