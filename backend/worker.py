"""Worker dédié aux tâches planifiées (crons), hors du process web.

En production multi-replica :
  - Replicas web : lancer uvicorn avec RUN_CRONS=false (aucun cron).
  - UN worker    : `python worker.py` (ce fichier) → exécute tous les crons.
Cela évite que chaque replica web relance les mêmes crons (doublons).
"""
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

from database import init_db
import server as s


async def main():
    logger.info("[WORKER] Démarrage du worker crons")
    try:
        await init_db()
    except Exception as e:
        logger.error("[WORKER] init_db a échoué (on continue): %s", e)

    loops = (
        s._auto_migrate_on_startup,
        s._weekly_cron_loop,
        s._rate_limiter_cleanup_loop,
        s._weekly_email_report_loop,
        s._workflow_scheduler_loop,
        s._monthly_credit_reset_loop,
        s.monthly_swot_loop,
        s.inactivity_alerts_loop,
        s._gdpr_purge_loop,
        s.hot_opportunities_scan_loop,
        s.automations_cron_loop,
        s.vision_weekly_email_loop,
        s._sync_react_to_wp_on_startup,
    )
    logger.info("[WORKER] %d tâches planifiées lancées", len(loops))
    await asyncio.gather(*(fn() for fn in loops))


if __name__ == "__main__":
    asyncio.run(main())
