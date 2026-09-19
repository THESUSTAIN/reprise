"""Dashboard summary for the Cockpit frontend.
Ported from MongoDB backend → SQL (app-main). Mock-friendly placeholders for cards
not yet wired to real tables (mission_du_jour, sante_globale, vision, etc.)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
import datetime

from deps import get_current_user
from database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


async def _compute_dashboard(db, user_id, user=None):
    """Construit le résumé du cockpit à partir de la DB pour un user_id donné.
    `user` peut être None (mode invité / user_id=default) — dans ce cas on
    retombe sur des états vides propres."""
    settings = {}
    if user is not None and isinstance(getattr(user, "settings", None), dict):
        settings = user.settings
    else:
        # Invité : tenter de lire les settings depuis la table users si le user_id existe
        try:
            row = (await db.execute(
                text("SELECT name, settings, sector, stage FROM users WHERE id = :uid LIMIT 1"),
                {"uid": user_id},
            )).fetchone()
            if row:
                import json as _json
                raw = row[1]
                if isinstance(raw, str):
                    try:
                        settings = _json.loads(raw) or {}
                    except Exception:
                        settings = {}
                elif isinstance(raw, dict):
                    settings = raw
        except Exception:
            settings = {}

    first_name = ""
    if user is not None:
        first_name = (getattr(user, "name", None) or "").split(" ")[0]
    first_name = first_name or "Bienvenue"

    # ── Tâches de la semaine ─────────────────────────────────────────────
    tasks_done = 0
    tasks_total = 0
    ia_checklist = []
    try:
        from models import Task
        stmt_total = select(func.count()).select_from(Task).where(Task.user_id == user_id)
        stmt_done = select(func.count()).select_from(Task).where(
            Task.user_id == user_id, Task.status == "done"
        )
        tasks_total = (await db.execute(stmt_total)).scalar() or 0
        tasks_done = (await db.execute(stmt_done)).scalar() or 0
        stmt_tasks = select(Task).where(
            Task.user_id == user_id
        ).order_by(Task.updated_at.desc()).limit(5)
        rows = (await db.execute(stmt_tasks)).scalars().all()
        ia_checklist = [{"label": t.title, "done": t.status == "done"} for t in rows]
    except Exception:
        pass  # Fallback silencieux — la page affiche un état vide propre

    # ── Métriques de la semaine (depuis bank_transactions réelles) ────────
    pilotage = {"ca_month_eur": 0, "objective_eur": 10000, "progress_percent": 0}
    metrics_week = None
    try:
        row = (await db.execute(
            text(
                "SELECT "
                " SUM(CASE WHEN amount_cents > 0 AND booked_at >= :month_start THEN amount_cents ELSE 0 END) AS ca_month,"
                " SUM(CASE WHEN amount_cents > 0 AND booked_at >= :week_start THEN amount_cents ELSE 0 END) AS ca_week,"
                " COUNT(DISTINCT CASE WHEN booked_at >= :week_start THEN counterparty END) AS new_counterparties"
                " FROM bank_transactions WHERE user_id = :uid"
            ),
            {
                "uid": user_id,
                "month_start": datetime.datetime.utcnow().replace(day=1).isoformat(),
                "week_start": (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat(),
            },
        )).fetchone()
        if row and row[0] is not None:
            ca_month_eur = round((row[0] or 0) / 100, 2)
            ca_week_eur = round((row[1] or 0) / 100, 2)
            pilotage = {
                "ca_month_eur": ca_month_eur,
                "objective_eur": 10000,
                "progress_percent": min(100, round(ca_month_eur / 10000 * 100)) if ca_month_eur else 0,
            }
            metrics_week = {
                "ca": f"{ca_week_eur:,.0f} €".replace(",", " "),
                "clients": row[2] or 0,
            }
    except Exception:
        pass  # Pas de connexion bancaire — metrics_week reste None → empty state propre

    # Fallback : si aucune transaction bancaire (ca_month == 0), on utilise les
    # entrées manuelles du Pilotage (finance_entries) pour alimenter le CA du mois.
    if not pilotage.get("ca_month_eur"):
        try:
            _mstart = datetime.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            rev = (await db.execute(text(
                "SELECT COALESCE(SUM(amount),0) FROM finance_entries "
                "WHERE user_id = :uid AND type = 'revenu' AND date >= :ms"
            ), {"uid": user_id, "ms": _mstart})).scalar() or 0
            rev = round(float(rev), 2)
            if rev:
                pilotage = {
                    "ca_month_eur": rev,
                    "objective_eur": 20000,
                    "progress_percent": min(100, round(rev / 20000 * 100)),
                }
        except Exception:
            pass

    # ── Prospects réels (table user_leads) ──────────────────────────────
    prospects_total = 0
    try:
        r = (await db.execute(
            text("SELECT COUNT(*) FROM user_leads WHERE user_id = :uid"), {"uid": user_id}
        )).fetchone()
        prospects_total = (r[0] if r else 0) or 0
    except Exception:
        prospects_total = 0

    # ── Score bien-être réel (dernier check-in) ─────────────────────────
    bien_etre_score = None
    try:
        r = (await db.execute(
            text("SELECT score FROM wellness_checkins WHERE user_id = :uid ORDER BY date DESC LIMIT 1"),
            {"uid": user_id},
        )).fetchone()
        if r:
            bien_etre_score = r[0]
    except Exception:
        bien_etre_score = None

    # ── Objectif CA (défini par l'utilisateur, sinon 0 → "à définir") ────
    ca_objective = 0
    if isinstance(settings, dict):
        try:
            ca_objective = float(settings.get("ca_objective") or 0)
        except Exception:
            ca_objective = 0


    # ── Greeting dynamique + Valeur générée (ROI) — données réelles, honnêtes ──
    import datetime as _dt
    greeting_stats = {"streak_days": 0, "last_login": None, "week_done": 0, "week_total": 0}
    value_generated = {"ai_tasks": 0, "time_saved_min": 0, "automated_tasks": 0, "has_data": False}
    try:
        if user is not None and getattr(user, "last_login_at", None):
            try:
                greeting_stats["last_login"] = user.last_login_at.isoformat()
            except Exception:
                greeting_stats["last_login"] = str(user.last_login_at)
        _now = _dt.datetime.utcnow()
        _monday = (_now - _dt.timedelta(days=_now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        _weekstart = _now - _dt.timedelta(days=7)  # fenêtre glissante « 7 derniers jours »
        import json as _json2
        # Progrès de la semaine + tâches complétées (table user_tasks, data JSON).
        week_done = 0
        week_total = 0
        done_all = 0
        try:
            rows = (await db.execute(text(
                "SELECT data, created_at FROM user_tasks WHERE user_id=:uid"
            ), {"uid": user_id})).fetchall()
            for r in rows:
                d = r[0]
                if isinstance(d, str):
                    try:
                        d = _json2.loads(d)
                    except Exception:
                        d = {}
                if not isinstance(d, dict):
                    continue
                is_done = bool(d.get("done"))
                if is_done:
                    done_all += 1
                created = r[1]
                in_week = False
                try:
                    cdt = created if isinstance(created, _dt.datetime) else _dt.datetime.fromisoformat(str(created)[:19])
                    in_week = cdt >= _weekstart
                except Exception:
                    in_week = False
                if in_week:
                    week_total += 1
                    if is_done:
                        week_done += 1
            greeting_stats["week_done"] = week_done
            greeting_stats["week_total"] = week_total
        except Exception:
            pass
        # Streak : jours consécutifs (jusqu'à aujourd'hui) avec un check-in bien-être
        try:
            rows = (await db.execute(text(
                "SELECT DISTINCT date FROM wellness_checkins WHERE user_id=:uid ORDER BY date DESC LIMIT 120"
            ), {"uid": user_id})).fetchall()
            dates = set()
            for r in rows:
                v = r[0]
                dates.add((v[:10] if isinstance(v, str) else str(v)[:10]))
            streak = 0
            d = _dt.date.today()
            if d.isoformat() not in dates and (d - _dt.timedelta(days=1)).isoformat() in dates:
                d = d - _dt.timedelta(days=1)
            while d.isoformat() in dates:
                streak += 1
                d = d - _dt.timedelta(days=1)
            greeting_stats["streak_days"] = streak
        except Exception:
            pass
        # Valeur générée : interactions IA réelles + tâches complétées
        ai_count = 0
        for tbl in ("credit_logs", "api_costs", "conversations"):
            try:
                c = (await db.execute(text(f"SELECT COUNT(*) FROM {tbl} WHERE user_id=:uid"), {"uid": user_id})).scalar() or 0
                ai_count = max(ai_count, int(c))
            except Exception:
                continue
        automated = int(done_all or tasks_done or 0)
        value_generated = {
            "ai_tasks": ai_count,
            "automated_tasks": automated,
            "time_saved_min": int(ai_count * 12 + automated * 5),
            "has_data": bool(ai_count or automated),
        }
    except Exception:
        pass

    # ── Insights clés (heuristiques sur données réelles, aucune valeur inventée) ──
    # Remplace les 3 cartes codées en dur qui étaient auparavant affichées à
    # tous les utilisateurs quel que soit leur état réel (KeyInsights ne
    # recevait même pas `data` côté frontend). Ici : pas d'appel LLM (coût/
    # latence inutiles pour un résumé de dashboard), uniquement des règles
    # simples sur les métriques déjà calculées ci-dessus. Si rien de
    # significatif à signaler, la liste reste vide → le frontend affiche un
    # état vide honnête plutôt qu'un contenu de remplissage.
    insights = []
    prog = pilotage.get("progress_percent", 0)
    if ca_objective and prog >= 80:
        insights.append({
            "kind": "opportunite",
            "text": f"Vous êtes à {prog}% de votre objectif de CA du mois. Encore un effort pour l'atteindre.",
            "cta": "Voir Pilotage", "to": "/pilotage",
        })
    elif not ca_objective:
        insights.append({
            "kind": "idee", "label": "Objectif CA",
            "text": "Aucun objectif de chiffre d'affaires défini pour ce mois. Fixez-en un pour suivre votre progression.",
            "cta": "Définir un objectif", "to": "/pilotage",
        })
    elif ca_objective and prog < 30:
        insights.append({
            "kind": "attention",
            "text": f"Vous êtes à {prog}% de votre objectif de CA du mois ({pilotage.get('ca_month_eur', 0)} € sur {int(ca_objective)} €).",
            "cta": "Voir Pilotage", "to": "/pilotage",
        })

    if prospects_total == 0:
        insights.append({
            "kind": "idee", "label": "Prospection",
            "text": "Aucun prospect enregistré pour l'instant. Ajoutez vos premiers contacts pour démarrer votre pipeline commercial.",
            "cta": "Ouvrir Croissance", "to": "/croissance",
        })

    if bien_etre_score is not None and bien_etre_score < 45:
        insights.append({
            "kind": "attention",
            "text": f"Votre dernier score bien-être est bas ({bien_etre_score}/100). Pensez à souffler avant d'enchaîner.",
            "cta": "Voir Bien-être", "to": "/bien-etre",
        })

    if tasks_total and tasks_done and (tasks_done / tasks_total) < 0.3:
        insights.append({
            "kind": "attention",
            "text": f"Seulement {tasks_done} tâche(s) sur {tasks_total} terminée(s) cette semaine.",
            "cta": "Voir mes tâches", "to": "/bureau",
        })

    insights = insights[:3]

    # ── Énergie (dernier check-in) → energy_score 0-100 (fix #8) ──────────
    energy_score = None
    try:
        r = (await db.execute(text(
            "SELECT level FROM user_energy WHERE user_id = :uid AND level > 0 ORDER BY date DESC LIMIT 1"
        ), {"uid": user_id})).fetchone()
        if r and r[0]:
            energy_score = min(100, int(r[0]) * 20)
    except Exception:
        energy_score = None

    # ── Label équilibre depuis le score bien-être (fix #8) ────────────────
    bien_etre_label = None
    if isinstance(bien_etre_score, (int, float)):
        if bien_etre_score >= 75:
            bien_etre_label = "Bon équilibre"
        elif bien_etre_score >= 45:
            bien_etre_label = "Équilibre correct"
        else:
            bien_etre_label = "À surveiller"

    # ── Delta CA hebdo (semaine courante vs précédente) → ca_delta_pct ────
    ca_delta_pct = None
    try:
        _n = datetime.datetime.utcnow()
        _w0 = (_n - datetime.timedelta(days=7)).isoformat()
        _w1 = (_n - datetime.timedelta(days=14)).isoformat()
        cur_w = (await db.execute(text(
            "SELECT COALESCE(SUM(amount),0) FROM finance_entries WHERE user_id=:uid AND type='revenu' AND date >= :w0"
        ), {"uid": user_id, "w0": _w0})).scalar() or 0
        prev_w = (await db.execute(text(
            "SELECT COALESCE(SUM(amount),0) FROM finance_entries WHERE user_id=:uid AND type='revenu' AND date >= :w1 AND date < :w0"
        ), {"uid": user_id, "w1": _w1, "w0": _w0})).scalar() or 0
        if prev_w > 0:
            ca_delta_pct = round((float(cur_w) - float(prev_w)) / float(prev_w) * 100)
            # Garde-fou : en début de mois le dénominateur hebdo est petit et
            # produit des % aberrants (+1000%). On borne l'affichage.
            ca_delta_pct = max(-95, min(95, ca_delta_pct))
        elif cur_w > 0:
            ca_delta_pct = 20
    except Exception:
        ca_delta_pct = None

    # ── Score Business (composite honnête sur données réelles) → project_score ──
    project_score = None
    try:
        _vision_align = 0
        if isinstance(settings, dict):
            _vision_align = int(settings.get("vision_alignment") or 0)
        _has_ca = bool(pilotage.get("ca_month_eur"))
        _task_ratio = (tasks_done / tasks_total) if tasks_total else 0
        if _vision_align or _has_ca or energy_score or bien_etre_score:
            ca_pts = min(30, round((pilotage.get("ca_month_eur", 0) / 20000) * 30)) if _has_ca else 0
            project_score = round(
                _vision_align * 0.30
                + ca_pts
                + _task_ratio * 20
                + (energy_score or 0) * 0.10
                + (bien_etre_score or 0) * 0.10
            )
            project_score = max(0, min(100, project_score))
    except Exception:
        project_score = None

    return {
        "ca_month": pilotage["ca_month_eur"],
        "ca_objective": ca_objective,
        "energy_score": energy_score,
        "project_score": project_score,
        "ca_delta_pct": ca_delta_pct,
        "insights": insights,
        "greeting_stats": greeting_stats,
        "value_generated": value_generated,
        "treasury_30d": 0,
        "prospects_total": prospects_total,
        "prospects_active": prospects_total,
        "prospects_to_relaunch": 0,
        "bien_etre_score": bien_etre_score,
        "bien_etre_label": bien_etre_label,
        "user": {
            "first_name": first_name,
            "sector": getattr(user, "sector", None) if user is not None else settings.get("sector"),
            "stage": getattr(user, "stage", None) if user is not None else settings.get("stage"),
        },
        "ia_checklist": ia_checklist,
        "missions": {"done": tasks_done, "total": tasks_total, "in_progress": 0, "blocked": 0},
        "mission_du_jour": None,
        "sante_globale": None,
        "pilotage": pilotage,
        "metrics_week": metrics_week,
        "citation_du_jour": None,
        "vision": {
            "alignment_percent": settings.get("vision_alignment", 0) if isinstance(settings, dict) else 0,
            "next_step": (settings.get("why") if isinstance(settings, dict) else None) or "Définissez votre objectif 90 jours dans Vision.",
            "summary": settings.get("vision_summary") if isinstance(settings, dict) else None,
        },
        "developpement": {
            "prospects": 0,
            "in_discussion": 0,
            "clients": 0,
            "ambassadors": 0,
            "hot_opportunity": None,
        },
    }


@router.get("")
async def dashboard_root(auth_user=Depends(get_current_user), db=Depends(get_db)):
    """Résumé du cockpit — toujours scopé sur l'utilisateur du JWT.

    ⚠️ Avant correction : sans token valide, l'endpoint retombait silencieusement
    sur le `user_id` fourni en query string et renvoyait quand même les données
    (tâches, leads, score bien-être...) de ce compte — IDOR exploitable par une
    simple requête non authentifiée avec ?user_id=<id d'un autre utilisateur>.
    Les comptes invités reçoivent déjà un vrai JWT via /api/auth/guest, donc
    exiger l'authentification ici ne casse pas ce parcours."""
    # Compte de démo Thomas : peuple des données réalistes (idempotent, no-op sinon).
    try:
        from demo_seed import ensure_thomas_demo
        await ensure_thomas_demo(db, auth_user)
    except Exception:
        pass
    return await _compute_dashboard(db, auth_user.id, auth_user)


@router.get("/summary")
async def summary(user=Depends(get_current_user), db=Depends(get_db)):
    """Résumé du cockpit pour l'utilisateur authentifié (JWT)."""
    return await _compute_dashboard(db, getattr(user, "id", None), user)


# ─────────── #2 Dashboard fusion (engagement daily) ───────────────────
@router.get("/fusion")
async def dashboard_fusion(user=Depends(get_current_user), db=Depends(get_db)):
    """Vue fusionnée Dashboard + Inspiration : hero contextuel, snapshot Vision,
    priorité IA du jour, timeline et souvenirs — en un seul appel."""
    import json as _json
    uid = getattr(user, "id", None)
    base = await _compute_dashboard(db, uid, user)
    first_name = base["user"]["first_name"]
    now = datetime.datetime.utcnow()
    hour = now.hour
    greeting = "Bonjour" if hour < 12 else ("Bon après-midi" if hour < 18 else "Bonsoir")

    # Bien-être du jour → message hero contextuel
    wellness_score = None
    try:
        row = (await db.execute(
            text("SELECT score FROM wellness_checkins WHERE user_id = :uid ORDER BY date DESC LIMIT 1"),
            {"uid": uid},
        )).fetchone()
        if row:
            wellness_score = row[0]
    except Exception:
        pass

    if wellness_score is not None and wellness_score < 45:
        hero_msg = "Journée à énergie basse — concentrez-vous sur 1 seule priorité aujourd'hui."
    elif base["pilotage"]["progress_percent"] >= 80:
        hero_msg = "Vous êtes proche de votre objectif de CA du mois. Poussez le dernier effort !"
    else:
        hero_msg = "Une action alignée aujourd'hui vaut mieux que dix demain."

    # Priorité IA du jour : 1re tâche non terminée
    today_priority = None
    try:
        rows = (await db.execute(
            text("SELECT data FROM user_tasks WHERE user_id = :uid ORDER BY created_at DESC LIMIT 20"),
            {"uid": uid},
        )).fetchall()
        for r in rows:
            d = r[0]
            if isinstance(d, str):
                d = _json.loads(d)
            if isinstance(d, dict) and not d.get("done"):
                today_priority = {"label": d.get("label"), "priority": d.get("priority", "normal")}
                break
    except Exception:
        pass
    if not today_priority:
        today_priority = {"label": base["vision"]["next_step"], "priority": "vision"}

    # Timeline : derniers événements (tâches créées, check-ins)
    timeline = []
    try:
        rows = (await db.execute(
            text("SELECT data, created_at FROM user_tasks WHERE user_id = :uid ORDER BY created_at DESC LIMIT 5"),
            {"uid": uid},
        )).fetchall()
        for r in rows:
            d = r[0]
            if isinstance(d, str):
                d = _json.loads(d)
            timeline.append({"type": "task", "label": (d or {}).get("label", "Tâche"),
                             "at": r[1].isoformat() if r[1] else None})
    except Exception:
        pass

    # Souvenirs : jalons de piliers atteints + meilleur jour bien-être
    memories = []
    try:
        row = (await db.execute(
            text("SELECT score, date FROM wellness_checkins WHERE user_id = :uid ORDER BY score DESC LIMIT 1"),
            {"uid": uid},
        )).fetchone()
        if row and row[0] is not None:
            memories.append({"type": "wellness_best", "label": f"Meilleur score bien-être : {row[0]}/100",
                             "at": row[1].isoformat() if row[1] else None})
    except Exception:
        pass

    return {
        "hero": {"greeting": greeting, "first_name": first_name, "message": hero_msg,
                 "wellness_score": wellness_score},
        "vision_snapshot": base["vision"],
        "today_priority": today_priority,
        "timeline": timeline,
        "memories": memories,
        "pilotage": base["pilotage"],
        "missions": base["missions"],
    }
