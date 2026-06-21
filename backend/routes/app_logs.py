"""
App Logs — Système de monitoring par fonctionnalité pour l'admin Zayado.
Enregistre automatiquement les événements clés : chat, auth, paiements, extension, affiliations.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from typing import Optional
import json
import logging
import asyncio

from database import get_db, async_session_factory
from models import AppLog, User
from deps import get_admin_user

logger = logging.getLogger(__name__)

app_logs_router = APIRouter(tags=["App Logs"])


# ─── Helper : enregistrer un log applicatif ────────────────────────────────────

async def log_event(
    level: str,          # INFO | WARNING | ERROR | CRITICAL
    feature: str,        # chat | auth | payment | extension | affiliate | admin | agent | oauth
    message: str,
    action: str = None,
    user_id: str = None,
    user_email: str = None,
    details: dict = None,
    ip_address: str = None,
    duration_ms: int = None,
):
    """Enregistre un événement dans app_logs. Non-bloquant — fire-and-forget."""
    try:
        async with async_session_factory() as db:
            entry = AppLog(
                level=level.upper(),
                feature=feature,
                action=action,
                user_id=user_id,
                user_email=user_email,
                message=message,
                details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
                ip_address=ip_address,
                duration_ms=duration_ms,
            )
            db.add(entry)
            await db.commit()
    except Exception as e:
        logger.warning(f"[AppLog] Impossible d'enregistrer le log : {e}")


def log_event_sync(level: str, feature: str, message: str, **kwargs):
    """Version synchrone — crée une tâche asyncio si une boucle est active."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(log_event(level, feature, message, **kwargs))
        else:
            loop.run_until_complete(log_event(level, feature, message, **kwargs))
    except Exception:
        pass  # Ne jamais bloquer l'app à cause des logs


# ─── Routes Admin ──────────────────────────────────────────────────────────────

@app_logs_router.get("/app-logs")
async def get_app_logs(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None,        # INFO, WARNING, ERROR, CRITICAL
    feature: Optional[str] = None,      # chat, auth, payment, extension, affiliate...
    search: Optional[str] = None,       # recherche dans message
    hours: Optional[int] = None,        # dernières N heures
):
    """Récupère les logs applicatifs avec filtres. Admin uniquement."""
    filters = []
    if level:
        filters.append(AppLog.level == level.upper())
    if feature:
        filters.append(AppLog.feature == feature)
    if search:
        filters.append(AppLog.message.contains(search))
    if hours:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        filters.append(AppLog.created_at >= since)

    query = select(AppLog)
    if filters:
        query = query.where(and_(*filters))
    query = query.order_by(AppLog.created_at.desc())

    total_q = select(func.count()).select_from(AppLog)
    if filters:
        total_q = total_q.where(and_(*filters))

    total = (await db.execute(total_q)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()

    return {
        "logs": [
            {
                "id": r.id,
                "level": r.level,
                "feature": r.feature,
                "action": r.action,
                "user_id": r.user_id,
                "user_email": r.user_email,
                "message": r.message,
                "details": r.details,
                "ip_address": r.ip_address,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


@app_logs_router.get("/app-logs/summary")
async def get_app_logs_summary(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Résumé des logs des dernières 24h par feature et level."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    # Compte par feature
    by_feature = {}
    for feature in ["chat", "auth", "payment", "extension", "affiliate", "admin", "agent", "oauth"]:
        count = (await db.execute(
            select(func.count()).select_from(AppLog).where(
                and_(AppLog.feature == feature, AppLog.created_at >= since)
            )
        )).scalar() or 0
        errors = (await db.execute(
            select(func.count()).select_from(AppLog).where(
                and_(AppLog.feature == feature, AppLog.level.in_(["ERROR", "CRITICAL"]), AppLog.created_at >= since)
            )
        )).scalar() or 0
        by_feature[feature] = {"total": count, "errors": errors}

    # Compte par level
    by_level = {}
    for level in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
        count = (await db.execute(
            select(func.count()).select_from(AppLog).where(
                and_(AppLog.level == level, AppLog.created_at >= since)
            )
        )).scalar() or 0
        by_level[level] = count

    # Dernières erreurs critiques
    last_errors = (await db.execute(
        select(AppLog).where(
            and_(AppLog.level.in_(["ERROR", "CRITICAL"]), AppLog.created_at >= since)
        ).order_by(AppLog.created_at.desc()).limit(5)
    )).scalars().all()

    return {
        "period_hours": 24,
        "by_feature": by_feature,
        "by_level": by_level,
        "last_errors": [
            {
                "id": r.id, "level": r.level, "feature": r.feature,
                "message": r.message, "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in last_errors
        ],
    }


@app_logs_router.delete("/app-logs/purge")
async def purge_old_logs(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    days: int = 30,
):
    """Supprime les logs de plus de N jours (défaut 30 jours)."""
    from sqlalchemy import delete
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(delete(AppLog).where(AppLog.created_at < cutoff))
    await db.commit()
    return {"deleted": result.rowcount, "cutoff": cutoff.isoformat()}
