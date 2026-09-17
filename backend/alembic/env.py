"""Alembic env.py — compatible SQLAlchemy async (asyncmy / aiosqlite / asyncpg).

Réutilise directement DATABASE_URL et Base/models du projet (database.py, models.py)
pour rester la source de vérité unique du schéma. Fonctionne en mode offline
(génération de SQL) et online (connexion réelle, y compris moteurs async).
"""
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Permet d'importer database.py / models.py situés dans backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import DATABASE_URL, Base  # noqa: E402
import models  # noqa: E402,F401  (charge tous les modèles dans Base.metadata)

# Objet de config Alembic, donne accès aux valeurs du .ini utilisé
config = context.config

# Injecte l'URL réelle (dérivée de DATABASE_URL / variables Railway / fallback SQLite)
# — pas besoin de dupliquer la config dans alembic.ini.
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Logging Python via alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata cible pour l'autogénération (--autogenerate)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Génère le SQL des migrations sans connexion DB réelle (`alembic upgrade head --sql`)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Connexion réelle via le moteur async (asyncmy pour MySQL, aiosqlite en dev)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
