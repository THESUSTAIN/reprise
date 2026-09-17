"""IA quota tracking — limite l'usage du chat Claude par mois selon le plan.

- Plan free :   10 messages/mois
- Plan start :  300 messages/mois
- Plan grow :   1500 messages/mois
- Plan serenity / business / admin : illimité

Stockage : table `ai_quota_usage` (user_id, year, month, count, updated_at).
"""
import logging
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

PLAN_LIMITS = {
    "free":       10,
    "start":      300,
    "trajectoire": 300,
    "grow":       1500,
    "serenite":   None,
    "serenity":   None,
    "business":   None,
    "admin":      None,
}


async def _ensure_table(db: AsyncSession):
    await db.execute(text(
        "CREATE TABLE IF NOT EXISTS ai_quota_usage ("
        "user_id VARCHAR(36) NOT NULL, "
        "year INT NOT NULL, "
        "month INT NOT NULL, "
        "count INT NOT NULL DEFAULT 0, "
        "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "PRIMARY KEY (user_id, year, month))"
    ))


def _plan_limit(plan: str | None, is_admin: bool = False) -> int | None:
    if is_admin:
        return None
    key = str(plan or "free").lower()
    return PLAN_LIMITS.get(key, PLAN_LIMITS["free"])


async def get_usage(db: AsyncSession, user_id: str) -> dict:
    """Retourne {used, limit, remaining, period_end} pour le mois courant."""
    await _ensure_table(db)
    now = datetime.now(timezone.utc)
    y, m = now.year, now.month
    try:
        r = await db.execute(
            text("SELECT count FROM ai_quota_usage WHERE user_id = :uid AND year = :y AND month = :m"),
            {"uid": user_id, "y": y, "m": m},
        )
        row = r.fetchone()
        used = int(row[0]) if row else 0
    except Exception as e:
        logger.warning("ai_quota get_usage failed: %s", e)
        used = 0
    return {"used": used, "year": y, "month": m}


async def check_and_increment(db: AsyncSession, user_id: str, plan: str | None, is_admin: bool = False) -> dict:
    """Vérifie la quota et incrémente. Renvoie {ok, used, limit, remaining}.

    Si la quota est dépassée, ok=False (le caller doit retourner 402/429).
    """
    await _ensure_table(db)
    limit = _plan_limit(plan, is_admin=is_admin)
    usage = await get_usage(db, user_id)
    used = usage["used"]

    if limit is not None and used >= limit:
        return {"ok": False, "used": used, "limit": limit, "remaining": 0}

    # Increment
    now = datetime.now(timezone.utc)
    y, m = now.year, now.month
    try:
        # Try update first, then insert if zero rows (avoids dialect-specific upsert)
        r = await db.execute(
            text(
                "UPDATE ai_quota_usage SET count = count + 1, updated_at = :ts "
                "WHERE user_id = :uid AND year = :y AND month = :m"
            ),
            {"uid": user_id, "y": y, "m": m, "ts": now.isoformat()},
        )
        if r.rowcount == 0:
            await db.execute(
                text(
                    "INSERT INTO ai_quota_usage (user_id, year, month, count, updated_at) "
                    "VALUES (:uid, :y, :m, 1, :ts)"
                ),
                {"uid": user_id, "y": y, "m": m, "ts": now.isoformat()},
            )
        await db.commit()
        used = used + 1
    except Exception as e:
        logger.warning("ai_quota increment failed: %s", e)
    remaining = None if limit is None else max(0, limit - used)
    return {"ok": True, "used": used, "limit": limit, "remaining": remaining}
