"""Dashboard summary for the Cockpit frontend.
Ported from MongoDB backend → SQL (app-main). Mock-friendly placeholders for cards
not yet wired to real tables (mission_du_jour, sante_globale, vision, etc.)."""
from fastapi import APIRouter, Depends
from deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(user=Depends(get_current_user)):
    """
    Retourne le résumé du cockpit pour l'utilisateur connecté.
    Toutes les données viennent de la DB — aucune valeur hardcodée.
    """
    first_name = (getattr(user, "name", None) or "").split(" ")[0] or "Bienvenue"
    user_id = getattr(user, "id", None)

    # Récupérer les données réelles depuis la DB
    tasks_done = 0
    tasks_total = 0
    ca_month = 0
    ia_checklist = []

    try:
        from database import get_db
        from sqlalchemy import select, func
        import datetime

        async for db in get_db():
            # Tâches de la semaine
            from models import Task
            now = datetime.datetime.utcnow()
            week_start = now - datetime.timedelta(days=now.weekday())
            stmt_total = select(func.count()).select_from(Task).where(Task.user_id == user_id)
            stmt_done  = select(func.count()).select_from(Task).where(
                Task.user_id == user_id, Task.status == "done"
            )
            tasks_total = (await db.execute(stmt_total)).scalar() or 0
            tasks_done  = (await db.execute(stmt_done)).scalar()  or 0

            # Dernières tâches IA (checklist)
            stmt_tasks = select(Task).where(
                Task.user_id == user_id
            ).order_by(Task.updated_at.desc()).limit(5)
            rows = (await db.execute(stmt_tasks)).scalars().all()
            ia_checklist = [{"label": t.title, "done": t.status == "done"} for t in rows]
            break
    except Exception:
        pass  # Fallback silencieux — la page affiche un état vide propre

    # ── Métriques de la semaine (depuis bank_transactions réelles) ────────
    pilotage = {"ca_month_eur": 0, "objective_eur": 10000, "progress_percent": 0}
    metrics_week = None  # None tant qu'aucune transaction n'est connectée
    try:
        from sqlalchemy import text as _text
        import datetime as _dt
        async for db in get_db():
            row = (await db.execute(
                _text(
                    "SELECT "
                    " SUM(CASE WHEN amount_cents > 0 AND booked_at >= :month_start THEN amount_cents ELSE 0 END) AS ca_month,"
                    " SUM(CASE WHEN amount_cents > 0 AND booked_at >= :week_start THEN amount_cents ELSE 0 END) AS ca_week,"
                    " COUNT(DISTINCT CASE WHEN booked_at >= :week_start THEN counterparty END) AS new_counterparties"
                    " FROM bank_transactions WHERE user_id = :uid"
                ),
                {
                    "uid": user_id,
                    "month_start": _dt.datetime.utcnow().replace(day=1).isoformat(),
                    "week_start": (_dt.datetime.utcnow() - _dt.timedelta(days=7)).isoformat(),
                },
            )).fetchone()
            if row and row[0] is not None:
                ca_month_eur = round((row[0] or 0) / 100, 2)
                ca_week_eur  = round((row[1] or 0) / 100, 2)
                pilotage = {
                    "ca_month_eur": ca_month_eur,
                    "objective_eur": 10000,
                    "progress_percent": min(100, round(ca_month_eur / 10000 * 100)) if ca_month_eur else 0,
                }
                metrics_week = {
                    "ca": f"{ca_week_eur:,.0f} €".replace(",", " "),
                    "clients": row[2] or 0,
                }
            break
    except Exception:
        pass  # Pas de connexion bancaire — metrics_week reste None → empty state propre

    return {
        "user": {
            "first_name": first_name,
            "sector": getattr(user, "sector", None),
            "stage":  getattr(user, "stage",  None),
        },
        "ia_checklist": ia_checklist,
        "missions":     {"done": tasks_done, "total": tasks_total, "in_progress": 0, "blocked": 0},
        "mission_du_jour": None,
        "sante_globale":   None,
        "pilotage":        pilotage,
        "metrics_week":    metrics_week,
        "citation_du_jour": None,
        # Vision : lu depuis user.settings (alimenté par /api/onboarding)
        "vision": {
            "alignment_percent": (user.settings or {}).get("vision_alignment", 0) if isinstance(user.settings, dict) else 0,
            "next_step": (user.settings or {}).get("why") or "Définissez votre objectif 90 jours dans Vision.",
            "summary": (user.settings or {}).get("vision_summary"),
        },
        # Developpement : tant que pas de CRM connecté, tout à 0 + pas d'opportunité hardcodée
        "developpement": {
            "prospects": 0,
            "in_discussion": 0,
            "clients": 0,
            "ambassadors": 0,
            "hot_opportunity": None,
        },
    }
