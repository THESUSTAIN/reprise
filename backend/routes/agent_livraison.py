"""
agent_livraison.py — Agent Livraison (Hub IA) : messages proactifs
contextualisés (backlog #10).

Ma recommandation, faute de spec fonctionnelle détaillée reçue : plutôt
qu'un "agent" conversationnel séparé (LLM qui déciderait quoi dire), on
réutilise ce qui existe déjà et fonctionne — heuristiques déjà éprouvées
(cf. dashboard.py::_compute_dashboard pour le Cockpit) + Web Push (#11,
maintenant fonctionnel) — pour livrer PROACTIVEMENT, sans que l'utilisateur
ait besoin d'ouvrir l'app, les 3 signaux qui ont le plus de valeur à être
sus tout de suite plutôt qu'au prochain login :

  1. Nouveaux prospects détectés (Reddit/HN/Sirene) depuis la dernière visite
  2. Tâches en retard (créées il y a plus de 3 jours, jamais terminées)
  3. Score bien-être bas plusieurs jours de suite (signal de surcharge)

Pas de nouvel appel LLM par notification (coût/latence non justifiés pour
un message court factuel) — seulement des règles sur des données déjà en
base, comme pour les Insights Cockpit (#7). Si un jour un vrai "agent" au
sens conversationnel est voulu (rédaction du message par IA plutôt que
gabarit), le point d'insertion est `_build_notifications()` ci-dessous.

Idempotence : chaque notification envoyée est journalisée (user_data,
clé `agent_livraison_sent`, liste des derniers ids envoyés) pour ne
jamais notifier deux fois le même événement.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import text

from database import async_session_factory
from models import User
from sqlalchemy import select, update
from routes.push import send_push_to_user, _get_user_data, _set_user_data
from routes.kairos import get_kairos_settings, should_send_nudge, build_nudge_message

logger = logging.getLogger("agent_livraison")

INTERVAL_SECONDS = 6 * 3600  # toutes les 6h, cohérent avec hot_opportunities_scan_loop
STARTUP_DELAY = 240  # 4 min après démarrage — laisse les autres crons s'initialiser


async def _already_sent(db, user_id: str, event_id: str) -> bool:
    log = await _get_user_data(db, user_id, "agent_livraison_sent") or {"ids": []}
    return event_id in (log.get("ids") or [])


async def _mark_sent(db, user_id: str, event_id: str):
    log = await _get_user_data(db, user_id, "agent_livraison_sent") or {"ids": []}
    ids = (log.get("ids") or [])
    ids.append(event_id)
    await _set_user_data(db, user_id, "agent_livraison_sent", {"ids": ids[-200:]})  # garde les 200 derniers


async def _build_notifications(db, user_id: str) -> list:
    """Renvoie une liste de (event_id, title, body, url, family) à notifier
    pour cet utilisateur, en excluant ce qui a déjà été envoyé."""
    out = []
    now = datetime.now(timezone.utc)

    # 1) Nouveaux prospects détectés (dernières 24h, tous canaux : reddit/hackernews/sirene)
    try:
        rows = (await db.execute(text(
            "SELECT id, data, created_at FROM user_leads WHERE user_id=:uid "
            "AND created_at >= :since ORDER BY created_at DESC LIMIT 20"
        ), {"uid": user_id, "since": now - timedelta(hours=24)})).fetchall()
        if rows:
            n = len(rows)
            event_id = f"leads:{now.date().isoformat()}:{n}"
            if not await _already_sent(db, user_id, event_id):
                out.append((
                    event_id,
                    f"{n} nouveau{'x' if n > 1 else ''} prospect{'s' if n > 1 else ''} détecté{'s' if n > 1 else ''}",
                    "Votre agent de prospection a trouvé de nouvelles opportunités. Jetez-y un œil.",
                    "/croissance", "business",
                ))
    except Exception as e:
        logger.warning(f"[AGENT_LIVRAISON] leads check failed for {user_id}: {e}")

    # 2) Tâches en retard (créées il y a >3j, jamais terminées)
    try:
        rows = (await db.execute(text(
            "SELECT data FROM user_tasks WHERE user_id=:uid AND created_at <= :threshold"
        ), {"uid": user_id, "threshold": now - timedelta(days=3)})).fetchall()
        late = 0
        for r in rows:
            d = r[0]
            if isinstance(d, str):
                try:
                    d = json.loads(d)
                except Exception:
                    d = {}
            if isinstance(d, dict) and not d.get("done"):
                late += 1
        if late > 0:
            event_id = f"tasks:{now.isocalendar()[1]}:{late}"  # 1 rappel max par semaine par palier
            if not await _already_sent(db, user_id, event_id):
                out.append((
                    event_id,
                    f"{late} tâche{'s' if late > 1 else ''} en attente depuis plus de 3 jours",
                    "Un petit coup d'œil à votre liste de tâches ? Rien d'urgent, juste un rappel.",
                    "/bureau", "reminders",
                ))
    except Exception as e:
        logger.warning(f"[AGENT_LIVRAISON] tasks check failed for {user_id}: {e}")

    # 3) Bien-être bas plusieurs jours de suite (3 derniers check-ins < 45/100)
    try:
        rows = (await db.execute(text(
            "SELECT score, date FROM wellness_checkins WHERE user_id=:uid ORDER BY date DESC LIMIT 3"
        ), {"uid": user_id})).fetchall()
        if len(rows) == 3 and all((r[0] or 100) < 45 for r in rows):
            event_id = f"wellbeing_low:{rows[0][1]}"
            if not await _already_sent(db, user_id, event_id):
                out.append((
                    event_id,
                    "On a remarqué que ça semble difficile en ce moment",
                    "Vos 3 derniers check-ins bien-être sont bas. Prenez un moment pour souffler — votre cockpit peut attendre.",
                    "/bien-etre", "wellbeing",
                ))
    except Exception as e:
        logger.warning(f"[AGENT_LIVRAISON] wellbeing check failed for {user_id}: {e}")

    # 4) Kairos — rappel valeurs, 100% opt-in (backlog #19)
    try:
        user_row = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user_row:
            kairos = get_kairos_settings(user_row)
            if should_send_nudge(kairos):
                title, body = build_nudge_message(kairos)
                event_id = f"kairos:{now.date().isocalendar()[1]}"  # 1 max par semaine ISO
                if not await _already_sent(db, user_id, event_id):
                    out.append((event_id, title, body, "/vision-board", "wellbeing"))
    except Exception as e:
        logger.warning(f"[AGENT_LIVRAISON] kairos check failed for {user_id}: {e}")

    return out


async def agent_livraison_loop():
    """Background loop — vérifie périodiquement les signaux proactifs pour
    chaque utilisateur ayant une souscription push active, et livre les
    notifications pertinentes."""
    await asyncio.sleep(STARTUP_DELAY)
    logger.info("[AGENT_LIVRAISON] Loop started")

    while True:
        try:
            async with async_session_factory() as db:
                # Ne traite que les utilisateurs ayant une subscription push active —
                # inutile de calculer des insights pour quelqu'un qu'on ne peut pas notifier.
                rows = (await db.execute(text(
                    "SELECT DISTINCT user_id FROM user_data WHERE \"key\"='push_subscription'"
                ))).fetchall()
                for row in rows:
                    user_id = row[0]
                    try:
                        notifs = await _build_notifications(db, user_id)
                        for event_id, title, body, url, family in notifs:
                            sent = await send_push_to_user(db, user_id, title, body, url=url, family=family)
                            if sent:
                                await _mark_sent(db, user_id, event_id)
                                if event_id.startswith("kairos:"):
                                    u = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
                                    if u:
                                        s = u.settings or {}
                                        s["kairos"] = {**(s.get("kairos") or {}), "last_nudge_at": datetime.now(timezone.utc).isoformat()}
                                        await db.execute(update(User).where(User.id == user_id).values(settings=s))
                                        await db.commit()
                    except Exception as e:
                        logger.warning(f"[AGENT_LIVRAISON] failed for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"[AGENT_LIVRAISON] loop error: {e}")

        await asyncio.sleep(INTERVAL_SECONDS)
