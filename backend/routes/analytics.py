"""
analytics.py — Métriques activation & rétention (backlog #16).

Choix technique : table interne (`analytics_events`) plutôt qu'un outil
tiers (Mixpanel/PostHog/Amplitude) — évite de bloquer sur "lequel choisir"
et sur la création d'un compte externe. C'est un vrai point de départ,
pas un jouet : les événements sont horodatés, attribués à un utilisateur,
et interrogeables pour un funnel d'activation et une rétention par cohorte
D1/D7/D30. Migrable vers un outil dédié plus tard si besoin (le point
d'insertion est `track_event()`, un seul endroit à brancher sur un SDK
tiers en plus/à la place de l'écriture DB).

Vocabulaire d'événements fixe (voir EVENT_NAMES) — pas de texte libre,
pour que les agrégations restent fiables dans le temps.
"""
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, async_session_factory
from deps import get_admin_user
from models import User, AnalyticsEvent

logger = logging.getLogger("analytics")
router = APIRouter(prefix="/api/admin/analytics", tags=["analytics"])

# Vocabulaire fixe — étendre ici plutôt qu'avec du texte libre ailleurs.
EVENT_NAMES = [
    "signup",              # compte créé
    "onboarding_completed", # onboarding terminé
    "first_task_created",  # première tâche créée
    "first_ai_response",   # première réponse IA reçue (chat/copilote)
    "first_lead_detected", # premier lead détecté (Croissance)
    "login",                # connexion (pour la rétention D1/D7/D30)
    "subscription_upgraded", # passage à un plan payant
]


async def track_event(db: AsyncSession, user_id: str, event_name: str, properties: dict = None):
    """Enregistre un événement produit. Best-effort : ne doit jamais faire
    échouer le flux appelant (un événement raté n'est pas une raison de
    bloquer une inscription ou une connexion)."""
    if event_name not in EVENT_NAMES:
        logger.warning(f"[analytics] event_name inconnu ignoré: {event_name}")
        return
    try:
        db.add(AnalyticsEvent(user_id=user_id, event_name=event_name, properties=properties or {}))
        await db.commit()
    except Exception as e:
        logger.warning(f"[analytics] track_event failed ({event_name}, user={user_id}): {e}")


async def track_event_standalone(user_id: str, event_name: str, properties: dict = None):
    """Variante avec sa propre session DB — pour les points d'instrumentation
    qui n'ont pas déjà une session `db` sous la main (ex: dans un cron)."""
    try:
        async with async_session_factory() as db:
            await track_event(db, user_id, event_name, properties)
    except Exception as e:
        logger.warning(f"[analytics] track_event_standalone failed: {e}")


@router.get("/funnel")
async def get_funnel(days: int = 30, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Compte, pour chaque événement du vocabulaire, le nombre d'utilisateurs
    distincts l'ayant déclenché au moins une fois dans la fenêtre — un
    funnel d'activation basique (signup → onboarding → 1re tâche → 1re
    réponse IA → 1er lead) plutôt qu'un simple compte d'événements bruts."""
    since = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    rows = (await db.execute(
        select(AnalyticsEvent.event_name, func.count(func.distinct(AnalyticsEvent.user_id)))
        .where(AnalyticsEvent.created_at >= since)
        .group_by(AnalyticsEvent.event_name)
    )).all()
    counts = {name: 0 for name in EVENT_NAMES}
    for name, count in rows:
        counts[name] = count
    return {"days": days, "counts": counts}


@router.get("/retention")
async def get_retention(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Rétention par cohorte hebdomadaire, basée sur l'événement `login`.
    Pour chaque cohorte (semaine d'inscription), % d'utilisateurs ayant eu
    au moins un événement `login` en semaine+1 (≈ D7) et semaine+4 (≈ D30).
    Calcul simple et honnête plutôt qu'un vrai moteur de cohortes — suffisant
    pour un premier tableau de bord, à faire évoluer si besoin plus fin."""
    since = datetime.now(timezone.utc) - timedelta(days=90)
    signups = (await db.execute(
        select(User.id, User.created_at).where(User.created_at >= since)
    )).all()
    if not signups:
        return {"cohorts": []}

    logins = (await db.execute(
        select(AnalyticsEvent.user_id, AnalyticsEvent.created_at)
        .where(AnalyticsEvent.event_name == "login", AnalyticsEvent.created_at >= since)
    )).all()
    login_dates: dict = {}
    for uid, at in logins:
        login_dates.setdefault(uid, []).append(at)

    cohorts: dict = {}
    for uid, created_at in signups:
        week_key = created_at.date().isocalendar()[:2]  # (année, semaine ISO)
        cohorts.setdefault(week_key, {"users": [], "size": 0})
        cohorts[week_key]["users"].append((uid, created_at))
        cohorts[week_key]["size"] += 1

    out = []
    for week_key, data in sorted(cohorts.items()):
        d7_active = 0
        d30_active = 0
        for uid, created_at in data["users"]:
            dates = login_dates.get(uid, [])
            if any(created_at + timedelta(days=6) <= d <= created_at + timedelta(days=8) for d in dates):
                d7_active += 1
            if any(created_at + timedelta(days=28) <= d <= created_at + timedelta(days=32) for d in dates):
                d30_active += 1
        size = data["size"]
        out.append({
            "week": f"{week_key[0]}-W{week_key[1]:02d}",
            "size": size,
            "d7_retention_pct": round(100 * d7_active / size) if size else 0,
            "d30_retention_pct": round(100 * d30_active / size) if size else 0,
        })
    return {"cohorts": out}
