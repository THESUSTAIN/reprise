"""Endpoints manquants — empty states bien formés + stockage léger via JSON tables.

VAGUE 1 — fournit des endpoints non-404 pour :
- /api/tasks                  (CRUD)
- /api/vision                 (GET/PATCH)
- /api/documents              (CRUD + /generate)
- /api/leads                  (CRUD)
- /api/streak                 (GET)
- /api/revenue/monthly        (GET)
- /api/energy/today           (GET)
- /api/energy/latest          (GET)
- /api/processes/templates    (GET)
- /api/analyse                (GET/POST avec Claude Sonnet 4.5)

Pattern : tables ad-hoc créées à la volée (CREATE TABLE IF NOT EXISTS),
stockage JSON simple. Cohérent avec routes/processes.py.
"""
import os
import uuid
import json
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user, User

logger = logging.getLogger(__name__)
missing_router = APIRouter(tags=["missing-apis"])


def _utc_now():
    return datetime.now(timezone.utc)


# ============================================================
# Generic JSON table helper
# ============================================================
async def _ensure_table(db: AsyncSession, table: str):
    await db.execute(text(
        f"CREATE TABLE IF NOT EXISTS {table} ("
        f"id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, "
        f"data JSON NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        f"updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    ))


async def _list_rows(db: AsyncSession, table: str, user_id: str) -> list:
    await _ensure_table(db, table)
    try:
        r = await db.execute(
            text(f"SELECT data FROM {table} WHERE user_id = :uid ORDER BY created_at DESC"),
            {"uid": user_id}
        )
        rows = r.fetchall()
        result = []
        for row in rows:
            data = row[0]
            if isinstance(data, str):
                data = json.loads(data)
            result.append(data)
        return result
    except Exception as e:
        logger.warning("list_rows %s failed: %s", table, e)
        return []


async def _insert_row(db: AsyncSession, table: str, user_id: str, data: dict) -> dict:
    await _ensure_table(db, table)
    rid = data.get("id") or str(uuid.uuid4())
    data["id"] = rid
    data["created_at"] = data.get("created_at") or _utc_now().isoformat()
    try:
        await db.execute(
            text(f"INSERT INTO {table} (id, user_id, data) VALUES (:id, :uid, :d)"),
            {"id": rid, "uid": user_id, "d": json.dumps(data)},
        )
        await db.commit()
        return data
    except Exception as e:
        await db.rollback()
        logger.warning("insert_row %s failed: %s", table, e)
        raise HTTPException(500, "Erreur de sauvegarde")


async def _update_row(db: AsyncSession, table: str, user_id: str, rid: str, patch: dict) -> Optional[dict]:
    await _ensure_table(db, table)
    r = await db.execute(
        text(f"SELECT data FROM {table} WHERE id = :id AND user_id = :uid"),
        {"id": rid, "uid": user_id},
    )
    row = r.fetchone()
    if not row:
        return None
    cur = row[0]
    if isinstance(cur, str):
        cur = json.loads(cur)
    cur.update({k: v for k, v in patch.items() if v is not None})
    cur["updated_at"] = _utc_now().isoformat()
    await db.execute(
        text(f"UPDATE {table} SET data = :d WHERE id = :id AND user_id = :uid"),
        {"id": rid, "uid": user_id, "d": json.dumps(cur)},
    )
    await db.commit()
    return cur


async def _delete_row(db: AsyncSession, table: str, user_id: str, rid: str) -> bool:
    await _ensure_table(db, table)
    r = await db.execute(
        text(f"DELETE FROM {table} WHERE id = :id AND user_id = :uid"),
        {"id": rid, "uid": user_id},
    )
    await db.commit()
    return (r.rowcount or 0) > 0


# ============================================================
# TASKS  /api/tasks
# ============================================================
class TaskIn(BaseModel):
    label: str
    type: Optional[str] = "humain"   # humain | ia
    priority: Optional[str] = "normal"
    due_at: Optional[str] = None
    project_id: Optional[str] = None
    planned_for: Optional[str] = None
    estimated_minutes: Optional[int] = None
    decision_id: Optional[str] = None
    vision_pillar_id: Optional[str] = None
    strategic_milestone_id: Optional[str] = None
    defer_reason: Optional[str] = None
    notes: Optional[str] = None


class TaskPatch(BaseModel):
    label: Optional[str] = None
    type: Optional[str] = None
    done: Optional[bool] = None
    in_progress: Optional[bool] = None
    priority: Optional[str] = None
    due_at: Optional[str] = None
    project_id: Optional[str] = None
    planned_for: Optional[str] = None
    estimated_minutes: Optional[int] = None
    decision_id: Optional[str] = None
    vision_pillar_id: Optional[str] = None
    strategic_milestone_id: Optional[str] = None
    defer_reason: Optional[str] = None
    notes: Optional[str] = None


@missing_router.get("/tasks")
async def list_tasks(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_tasks", user.id)
    return {"items": items}


@missing_router.post("/tasks")
async def create_task(body: TaskIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = body.dict()
    data["done"] = False
    data["in_progress"] = False
    result = await _insert_row(db, "user_tasks", user.id, data)
    from routes.analytics import track_event
    await track_event(db, user.id, "first_task_created")
    return result


@missing_router.post("/tasks/generate")
async def generate_tasks(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère 3 priorités du jour via l'IA (Mammouth), ancrées sur le profil réel :
    type de projet (NET/TERRAIN) + 1ère mission d'onboarding + outils connectés +
    état réel du compte. Aucune donnée fictive : repli déterministe si l'IA échoue."""
    from sqlalchemy import text as _text

    async def _count(sql):
        try:
            r = (await db.execute(_text(sql), {"uid": user.id})).fetchone()
            return (r[0] if r else 0) or 0
        except Exception:
            return 0

    settings = dict(getattr(user, "settings", None) or {})
    project_type = (settings.get("project_type") or "NET").upper()
    sector = settings.get("sector") or ""
    objective = settings.get("objectif_90j") or settings.get("why") or ""
    first_mission = settings.get("first_mission") or ""
    projet_desc = settings.get("projet_description") or ""
    freins = settings.get("priorites") or []

    # Outils connectés (services + workspace choisi à l'onboarding)
    tools = []
    try:
        rows = (await db.execute(_text(
            "SELECT provider FROM user_connections WHERE user_id = :uid"
        ), {"uid": user.id})).fetchall()
        tools = [r[0] for r in rows if r and r[0]]
    except Exception:
        tools = []
    if settings.get("workspace_type") and settings["workspace_type"] != "none":
        tools.append(settings["workspace_type"])

    leads = await _count("SELECT COUNT(*) FROM user_leads WHERE user_id = :uid")
    fin = await _count("SELECT COUNT(*) FROM finance_entries WHERE user_id = :uid")
    vision = await _count("SELECT COUNT(*) FROM user_vision WHERE user_id = :uid")
    wellness_today = await _count(
        "SELECT COUNT(*) FROM wellness_checkins WHERE user_id = :uid AND date(date) = date('now')"
    )

    existing = await _list_rows(db, "user_tasks", user.id)
    existing_open = [t for t in existing if not t.get("done")]
    existing_labels = {(t.get("label") or "").strip().lower() for t in existing}

    # ── Génération IA (Mammouth → repli Emergent, géré par le client) ──
    ai_tasks = []
    try:
        import mammouth_client
        tools_str = ", ".join(tools) if tools else "aucun outil connecté"
        type_label = "activité de terrain (local, clients physiques)" if project_type == "TERRAIN" else "activité digitale (en ligne, web)"
        system = (
            "Tu es le co-pilote business de MyExtension AI pour un solopreneur francophone. "
            "Tu génères EXACTEMENT 3 priorités concrètes et actionnables pour SA journée, "
            "adaptées à son type de projet, sa 1ère mission et ses outils. "
            "Chaque priorité doit être une action courte réalisable aujourd'hui (pas un objectif vague). "
            "Réponds UNIQUEMENT avec un tableau JSON valide, sans texte autour, au format : "
            '[{"label":"...","priority":"high|medium|normal","duration_min":10,"type":"humain|ia"}]'
        )
        user_prompt = (
            f"Type de projet : {type_label} ({project_type}).\n"
            f"Secteur : {sector or 'non précisé'}.\n"
            f"Description du projet : {projet_desc or 'non précisée'}.\n"
            f"Objectif 90 jours : {objective or 'non précisé'}.\n"
            f"1ère mission définie à l'onboarding : {first_mission or 'non précisée'}.\n"
            f"Freins principaux : {', '.join(freins) if freins else 'non précisés'}.\n"
            f"Outils connectés : {tools_str}.\n"
            f"État du compte : {leads} prospects, {fin} entrées financières, "
            f"{'vision définie' if vision else 'vision non définie'}, "
            f"check-in bien-être {'fait' if wellness_today else 'non fait'} aujourd'hui.\n\n"
            "Donne 3 priorités du jour concrètes qui font avancer son business dès aujourd'hui."
        )
        raw = await mammouth_client.chat(
            [{"role": "system", "content": system},
             {"role": "user", "content": user_prompt}],
            max_tokens=600, temperature=0.6, timeout=45.0,
        )
        # Parse JSON robuste (l'IA peut entourer de ```json ... ```)
        cleaned = (raw or "").strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1] if len(cleaned.split("```")) > 1 else cleaned
            cleaned = cleaned.replace("json", "", 1).strip()
        start, end = cleaned.find("["), cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end + 1]
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            for item in parsed[:3]:
                if not isinstance(item, dict):
                    continue
                label = (item.get("label") or "").strip()
                if not label:
                    continue
                prio = item.get("priority") or "normal"
                if prio not in ("high", "medium", "normal"):
                    prio = "normal"
                try:
                    dur = int(item.get("duration_min") or 0)
                except Exception:
                    dur = 0
                ai_tasks.append({
                    "label": label,
                    "priority": prio,
                    "duration_min": dur,
                    "type": item.get("type") if item.get("type") in ("humain", "ia") else "humain",
                })
    except Exception as e:
        logger.warning("Génération IA des priorités KO (%s) → repli déterministe", e)

    # ── Repli déterministe (ancré sur l'état réel, jamais fictif) ──
    if not ai_tasks:
        fallback = []
        if first_mission:
            fallback.append({"label": first_mission, "priority": "high", "duration_min": 30, "type": "humain"})
        if leads > 0:
            fallback.append({"label": f"Relancer tes {leads} prospects en attente", "priority": "high", "duration_min": 20, "type": "humain"})
        if vision == 0:
            fallback.append({"label": "Définir ta vision et tes objectifs dans le Vision Board", "priority": "medium", "duration_min": 15, "type": "humain"})
        if fin == 0:
            fallback.append({"label": "Ajouter tes premières données financières dans Pilotage", "priority": "medium", "duration_min": 10, "type": "humain"})
        if wellness_today == 0:
            fallback.append({"label": "Faire ton check-in bien-être du jour", "priority": "normal", "duration_min": 2, "type": "humain"})
        if not fallback:
            fallback.append({"label": "Planifier tes 3 priorités de la semaine", "priority": "normal", "duration_min": 15, "type": "humain"})
        ai_tasks = fallback

    created = []
    for t in ai_tasks[:3]:
        if t["label"].strip().lower() in existing_labels:
            continue
        row = await _insert_row(db, "user_tasks", user.id, {
            "label": t["label"], "type": t.get("type", "humain"),
            "priority": t.get("priority", "normal"),
            "duration_min": t.get("duration_min", 0),
            "done": False, "in_progress": False, "source": "ai",
        })
        created.append(row)
        existing_labels.add(t["label"].strip().lower())

    return {"items": created, "count": len(created)}



@missing_router.patch("/tasks/{tid}")
async def patch_task(tid: str, body: TaskPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await _update_row(db, "user_tasks", user.id, tid, body.dict(exclude_unset=True))
    if not res:
        # Upsert idempotent : si la tâche n'existe pas (id transitoire après reset,
        # priorité générée côté client…), on la crée avec cet id pour que l'action
        # (cocher / reporter) réussisse toujours et persiste. Évite tout 404 en UX.
        data = {k: v for k, v in body.dict(exclude_unset=True).items() if v is not None}
        data["id"] = tid
        data.setdefault("label", data.get("label") or "Priorité")
        res = await _insert_row(db, "user_tasks", user.id, data)
    return res


@missing_router.get("/roadmap")
async def get_roadmap():
    """Feuille de route publique (évite le 404 côté /roadmap). Statique + auditable."""
    return {
        "shipped": [
            {"title": "Cockpit temps réel + Vision Board", "date": "2026-Q1"},
            {"title": "Extension navigateur (miroir Gmail/Agenda)", "date": "2026-Q1"},
            {"title": "Agents IA (analyse, prospection, livraison)", "date": "2026-Q2"},
            {"title": "Back-office WordPress + rôles", "date": "2026-Q2"},
        ],
        "in_progress": [
            {"title": "Gouvernance du coût IA (routing + cache + budgets)"},
            {"title": "Observabilité prod (logs, alerting)"},
            {"title": "News-Reprise éditoriale (IA + Brevo)"},
        ],
        "planned": [
            {"title": "Publication Chrome Web Store"},
            {"title": "Timeline & KPI Vision avancés"},
            {"title": "Packs IA (Startup, Investisseur 360°, Freelance)"},
        ],
    }


# ============================================================
# ROADMAP 30/60/90 — génération IA personnalisée par utilisateur
# (distincte de la feuille de route publique statique ci-dessus)
# ============================================================
class RoadmapGenerateIn(BaseModel):
    project_description: str
    target_market: str
    main_hypothesis: str


async def _ensure_roadmap_table(db: AsyncSession):
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS roadmap_generations (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36),
            project TEXT,
            target_market TEXT,
            main_hypothesis TEXT,
            data TEXT,
            created_at VARCHAR(40)
        )
    """))
    await db.commit()


@missing_router.get("/roadmap/sprints")
async def list_roadmap_sprints(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Historique des roadmaps 30/60/90 générées par l'utilisateur (page legacy/Roadmap.jsx)."""
    await _ensure_roadmap_table(db)
    rows = (await db.execute(
        text("SELECT id, project, data, created_at FROM roadmap_generations WHERE user_id = :uid ORDER BY created_at DESC"),
        {"uid": user.id},
    )).fetchall()
    items = []
    for r in rows:
        try:
            data = json.loads(r.data)
        except Exception:
            data = {"sprints": []}
        items.append({"sprint_id": r.id, "project": r.project, "data": data, "created_at": r.created_at})
    return items


@missing_router.post("/roadmap/generate")
async def generate_roadmap(body: RoadmapGenerateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère une roadmap 30/60/90 (Build-Measure-Learn) via l'IA à partir d'un projet,
    d'un marché cible et d'une hypothèse principale à tester."""
    await _ensure_roadmap_table(db)
    system = (
        "Tu es un coach en lean startup. On te donne une description de projet, un marché cible "
        "et une hypothèse principale à tester. Construis une roadmap en 3 sprints de 30 jours "
        "(30/60/90), qui teste les hypothèses les plus risquées en premier. "
        "Réponds UNIQUEMENT en JSON valide, sans texte autour, au format exact : "
        '{"sprints":[{"phase":"Jours 1-30","hypothesis":"...","experiments":["...","..."],'
        '"metrics":["...","..."],"decision_criteria":"..."},'
        '{"phase":"Jours 31-60", ...},{"phase":"Jours 61-90", ...}]}. '
        "Chaque 'experiments' contient 2 à 4 actions concrètes et réalisables. "
        "Chaque 'metrics' contient 2 à 3 indicateurs mesurables. "
        "'decision_criteria' explique en une phrase le seuil qui déclenche un pivot ou une poursuite. "
        "En français, sans jargon inutile."
    )
    user_msg = (
        f"Projet : {body.project_description}\n"
        f"Marché cible : {body.target_market}\n"
        f"Hypothèse principale à tester : {body.main_hypothesis}"
    )
    data = None
    try:
        from mammouth_client import chat as _llm_chat
        raw = await _llm_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
            max_tokens=1500, temperature=0.6, timeout=45,
        )
        s = raw.strip()
        if s.startswith("```"):
            s = s.split("```", 2)[1].replace("json", "", 1).strip() if "```" in s else s
        start, end = s.find("{"), s.rfind("}")
        parsed = json.loads(s[start:end + 1]) if start >= 0 and end > start else {}
        if parsed.get("sprints"):
            data = parsed
    except Exception as e:
        logger.warning("roadmap generate: appel IA en échec (%s), repli sur trame par défaut", e)

    if not data:
        # Repli déterministe si l'IA échoue — la mission reste accomplie, sans page vide.
        data = {
            "sprints": [
                {"phase": "Jours 1-30", "hypothesis": body.main_hypothesis,
                 "experiments": ["Valider l'hypothèse principale avec 5 à 10 entretiens clients",
                                  "Construire un prototype minimal pour tester l'offre"],
                 "metrics": ["Taux de retour positif", "Nombre d'entretiens réalisés"],
                 "decision_criteria": "Si moins de 30% de retours positifs, revoir l'hypothèse avant le sprint suivant."},
                {"phase": "Jours 31-60", "hypothesis": "Le marché cible réagit à l'offre testée",
                 "experiments": ["Lancer une version limitée auprès d'un groupe restreint",
                                  "Mesurer l'engagement réel"],
                 "metrics": ["Taux d'activation", "Taux de rétention à J+15"],
                 "decision_criteria": "Poursuivre si le taux d'activation dépasse le seuil fixé avec l'équipe."},
                {"phase": "Jours 61-90", "hypothesis": "Le modèle est prêt à être élargi",
                 "experiments": ["Élargir progressivement l'accès", "Automatiser les étapes déjà validées"],
                 "metrics": ["Coût d'acquisition", "Marge par dossier"],
                 "decision_criteria": "Passer à l'échelle si le coût d'acquisition reste soutenable."},
            ]
        }

    rid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text("""INSERT INTO roadmap_generations (id, user_id, project, target_market, main_hypothesis, data, created_at)
                 VALUES (:id, :uid, :project, :market, :hyp, :data, :created_at)"""),
        {"id": rid, "uid": user.id, "project": body.project_description, "market": body.target_market,
         "hyp": body.main_hypothesis, "data": json.dumps(data, ensure_ascii=False), "created_at": now},
    )
    await db.commit()
    return {"sprint_id": rid, "project": body.project_description, "data": data, "created_at": now}


@missing_router.delete("/tasks/{tid}")
async def delete_task(tid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await _delete_row(db, "user_tasks", user.id, tid)
    return {"deleted": ok}


# ============================================================
# STRATEGY  /api/strategy — jalons et décisions Mon Cap
# ============================================================
STRATEGIC_WINDOWS = {"now", "next", "later"}
STRATEGIC_STATUSES = {"planned", "active", "watch", "complete", "deferred", "abandoned"}


class StrategicMilestoneIn(BaseModel):
    title: str
    pillar_id: Optional[str] = None
    time_window: str = "now"
    expected_evidence: Optional[str] = ""
    status: Optional[str] = "planned"
    project_id: Optional[str] = None
    decision_id: Optional[str] = None
    notes: Optional[str] = ""


class StrategicMilestonePatch(BaseModel):
    title: Optional[str] = None
    pillar_id: Optional[str] = None
    time_window: Optional[str] = None
    expected_evidence: Optional[str] = None
    status: Optional[str] = None
    project_id: Optional[str] = None
    decision_id: Optional[str] = None
    notes: Optional[str] = None


class StrategicDecisionIn(BaseModel):
    title: str
    detail: Optional[str] = ""
    why_now: Optional[str] = ""
    impact: Optional[str] = ""
    pillar_id: Optional[str] = None
    milestone_id: Optional[str] = None
    project_id: Optional[str] = None
    priority: Optional[str] = "normal"


class StrategicDecisionPatch(BaseModel):
    title: Optional[str] = None
    detail: Optional[str] = None
    why_now: Optional[str] = None
    impact: Optional[str] = None
    pillar_id: Optional[str] = None
    milestone_id: Optional[str] = None
    project_id: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


def _validate_strategy_values(time_window: Optional[str] = None, status: Optional[str] = None):
    if time_window is not None and time_window not in STRATEGIC_WINDOWS:
        raise HTTPException(422, "Fenêtre stratégique invalide")
    if status is not None and status not in STRATEGIC_STATUSES:
        raise HTTPException(422, "État stratégique invalide")


@missing_router.get("/strategy/milestones")
async def list_strategic_milestones(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"items": await _list_rows(db, "user_strategy_milestones", user.id)}


@missing_router.post("/strategy/milestones")
async def create_strategic_milestone(body: StrategicMilestoneIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _validate_strategy_values(body.time_window, body.status)
    return await _insert_row(db, "user_strategy_milestones", user.id, body.dict())


@missing_router.patch("/strategy/milestones/{mid}")
async def patch_strategic_milestone(mid: str, body: StrategicMilestonePatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    patch = body.dict(exclude_unset=True)
    _validate_strategy_values(patch.get("time_window"), patch.get("status"))
    res = await _update_row(db, "user_strategy_milestones", user.id, mid, patch)
    if not res:
        raise HTTPException(404, "Jalon stratégique introuvable")
    return res


@missing_router.delete("/strategy/milestones/{mid}")
async def delete_strategic_milestone(mid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"deleted": await _delete_row(db, "user_strategy_milestones", user.id, mid)}


@missing_router.get("/strategy/decisions")
async def list_strategic_decisions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"items": await _list_rows(db, "user_strategy_decisions", user.id)}


@missing_router.post("/strategy/decisions")
async def create_strategic_decision(body: StrategicDecisionIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _insert_row(db, "user_strategy_decisions", user.id, {**body.dict(), "status": "pending"})


@missing_router.patch("/strategy/decisions/{did}")
async def patch_strategic_decision(did: str, body: StrategicDecisionPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await _update_row(db, "user_strategy_decisions", user.id, did, body.dict(exclude_unset=True))
    if not res:
        raise HTTPException(404, "Décision stratégique introuvable")
    return res


@missing_router.post("/strategy/decisions/{did}/apply")
async def apply_strategic_decision(did: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    decisions = await _list_rows(db, "user_strategy_decisions", user.id)
    item = next((row for row in decisions if row.get("id") == did), None)
    if not item:
        raise HTTPException(404, "Décision stratégique introuvable")
    task = await _insert_row(db, "user_tasks", user.id, {
        "label": item.get("title") or "Mission stratégique",
        "priority": item.get("priority") or "normal",
        "notes": item.get("detail") or "",
        "project_id": item.get("project_id"),
        "decision_id": did,
        "vision_pillar_id": item.get("pillar_id"),
        "strategic_milestone_id": item.get("milestone_id"),
        "done": False, "in_progress": False, "source": "strategy-decision",
    })
    decision = await _update_row(db, "user_strategy_decisions", user.id, did, {"status": "approved", "task_id": task.get("id")})
    return {"decision": decision, "task": task}


@missing_router.get("/strategy/overview")
async def get_strategy_overview(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {
        "milestones": await _list_rows(db, "user_strategy_milestones", user.id),
        "decisions": await _list_rows(db, "user_strategy_decisions", user.id),
        "tasks": await _list_rows(db, "user_tasks", user.id),
    }


# ============================================================
# HABITUDES  /api/wellness/habits  (hub "Moi" — onglet Habitudes)
# ============================================================
class HabitIn(BaseModel):
    name: str
    icon: Optional[str] = "target"


def _today_str():
    return date.today().isoformat()


def _decorate_habit(h: dict) -> dict:
    """Ajoute les champs calculés `done_today` et `streak` à une habitude.

    Ces deux champs n'étaient calculés que dans la liste. La création et le
    basculement renvoyaient la ligne brute, sans eux : toute interface qui
    faisait confiance à la réponse voyait une habitude « non faite » avec un
    streak à 0, y compris juste après l'avoir cochée. D'où un compteur de
    rituels bloqué à 0 quel que soit le nombre de cases cochées.
    """
    if not isinstance(h, dict):
        return h
    done = h.get("done_dates") or []
    dates = set(done)
    h["done_today"] = _today_str() in dates
    # Série en cours : jours consécutifs jusqu'à aujourd'hui (ou hier, pour ne
    # pas casser la série d'un utilisateur qui n'a pas encore coché du jour).
    s = 0
    d = date.today()
    if d.isoformat() not in dates and (d - timedelta(days=1)).isoformat() in dates:
        d = d - timedelta(days=1)
    while d.isoformat() in dates:
        s += 1
        d = d - timedelta(days=1)
    h["streak"] = s
    return h


@missing_router.get("/wellness/habits")
async def list_habits(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_habits", user.id)
    return {"items": [_decorate_habit(h) for h in items]}


@missing_router.post("/wellness/habits")
async def create_habit(body: HabitIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = await _insert_row(db, "user_habits", user.id, {"name": body.name, "icon": body.icon or "target", "done_dates": []})
    return _decorate_habit(row)


CHRISTIAN_HABITS = [
    "Lecture biblique du jour",
    "Prière du matin",
    "Gratitude — 3 grâces",
    "Méditation d'un verset",
    "Acte de bonté / service",
]


@missing_router.post("/wellness/habits/seed-christian")
async def seed_christian_habits(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Parcours chrétien (SSO thesustain.net simulé) : ajoute des habitudes bibliques (idempotent)."""
    existing = await _list_rows(db, "user_habits", user.id)
    names = {(h.get("name") or "").strip().lower() for h in existing}
    created = []
    for n in CHRISTIAN_HABITS:
        if n.strip().lower() in names:
            continue
        created.append(_decorate_habit(await _insert_row(db, "user_habits", user.id, {"name": n, "icon": "cross", "done_dates": [], "source": "thesustain"})))
    return {"items": created, "count": len(created)}


@missing_router.post("/wellness/habits/{hid}/toggle")
async def toggle_habit(hid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await _list_rows(db, "user_habits", user.id)
    cur = next((r for r in rows if r.get("id") == hid), None)
    if not cur:
        raise HTTPException(404, "Habitude introuvable")
    today = _today_str()
    done = set(cur.get("done_dates") or [])
    if today in done:
        done.discard(today)
    else:
        done.add(today)
    res = await _update_row(db, "user_habits", user.id, hid, {"done_dates": sorted(done)})
    return _decorate_habit(res or {"id": hid, "done_dates": sorted(done)})


@missing_router.delete("/wellness/habits/{hid}")
async def delete_habit(hid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await _delete_row(db, "user_habits", user.id, hid)
    return {"deleted": ok}


# ============================================================
# SOMMEIL  /api/wellness/sleep  (hub "Moi" — onglet Sommeil)
# ============================================================
class SleepIn(BaseModel):
    hours: float
    quality: Optional[int] = None   # 1-5
    date: Optional[str] = None


@missing_router.get("/wellness/sleep")
async def list_sleep(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_sleep", user.id)
    items = sorted(items, key=lambda x: x.get("date", ""), reverse=True)[:30]
    avg = round(sum(float(i.get("hours") or 0) for i in items) / len(items), 1) if items else None
    return {"items": items, "avg_hours": avg}


@missing_router.post("/wellness/sleep")
async def log_sleep(body: SleepIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    d = body.date or _today_str()
    # upsert : un seul enregistrement par date
    rows = await _list_rows(db, "user_sleep", user.id)
    existing = next((r for r in rows if r.get("date") == d), None)
    if existing:
        return await _update_row(db, "user_sleep", user.id, existing["id"], {"hours": body.hours, "quality": body.quality})
    return await _insert_row(db, "user_sleep", user.id, {"date": d, "hours": body.hours, "quality": body.quality})


# ============================================================
# VISION  /api/vision  (single doc per user)
# ============================================================
class VisionPatch(BaseModel):
    why: Optional[str] = None
    where: Optional[str] = None
    what: Optional[str] = None
    who: Optional[str] = None
    when: Optional[str] = None
    how: Optional[str] = None
    progress: Optional[int] = None
    notes: Optional[str] = None


@missing_router.get("/vision")
async def get_vision(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_vision", user.id)
    if items:
        return items[0]
    # Empty state bien formé
    return {
        "id": None,
        "why": "", "where": "", "what": "", "who": "", "when": "", "how": "",
        "progress": 0, "notes": "",
        "alignment_score": None,
        "items": [],
    }


@missing_router.patch("/vision")
async def patch_vision(body: VisionPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_vision", user.id)
    if items:
        vid = items[0]["id"]
        res = await _update_row(db, "user_vision", user.id, vid, body.dict(exclude_unset=True))
        return res
    data = body.dict(exclude_unset=True)
    return await _insert_row(db, "user_vision", user.id, data)


# ============================================================
# DOCUMENTS  /api/documents
# ============================================================
class DocumentIn(BaseModel):
    name: str
    type: Optional[str] = "general"
    content: Optional[str] = ""
    url: Optional[str] = None
    source: Optional[str] = "humain"   # humain | ia


@missing_router.get("/documents")
async def list_documents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_documents", user.id)
    return {"items": items}


@missing_router.post("/documents")
async def create_document(body: DocumentIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _insert_row(db, "user_documents", user.id, body.dict())


@missing_router.delete("/documents/{did}")
async def delete_document(did: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"deleted": await _delete_row(db, "user_documents", user.id, did)}


class DocumentGenerateIn(BaseModel):
    name: str
    type: Optional[str] = "general"
    prompt: str


@missing_router.post("/documents/generate")
async def generate_document(body: DocumentGenerateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère un document via Claude Sonnet 4.5. Retourne le document créé."""
    content = await _claude_complete(
        system="Tu es un assistant rédactionnel pour solo founders. Rédige des documents professionnels, en français, en markdown clair. Sois précis et actionnable.",
        user_prompt=f"Document demandé : {body.name} (type : {body.type}).\n\nBrief utilisateur :\n{body.prompt}\n\nRédige le document complet maintenant.",
        max_tokens=2000,
    )
    data = {
        "name": body.name,
        "type": body.type,
        "content": content or "",
        "source": "ia",
    }
    return await _insert_row(db, "user_documents", user.id, data)


# ============================================================
# LEADS  /api/leads
# ============================================================
class LeadIn(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = "manuel"
    status: Optional[str] = "nouveau"   # nouveau | qualifie | rdv | client | perdu
    notes: Optional[str] = None


class LeadPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@missing_router.get("/leads")
async def list_leads(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_leads", user.id)
    # Compute basic counters
    counters = {"nouveau": 0, "qualifie": 0, "rdv": 0, "client": 0, "perdu": 0}
    for it in items:
        s = it.get("status", "nouveau")
        if s in counters:
            counters[s] += 1
    return {"items": items, "counters": counters, "total": len(items)}


@missing_router.post("/leads")
async def create_lead(body: LeadIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _insert_row(db, "user_leads", user.id, body.dict())


@missing_router.patch("/leads/{lid}")
async def patch_lead(lid: str, body: LeadPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await _update_row(db, "user_leads", user.id, lid, body.dict(exclude_unset=True))
    if not res:
        raise HTTPException(404, "Lead introuvable")
    return res


@missing_router.delete("/leads/{lid}")
async def delete_lead(lid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"deleted": await _delete_row(db, "user_leads", user.id, lid)}


# ============================================================
# STREAK  /api/streak (calculé à la volée à partir de user_energy ou last_login)
# ============================================================
@missing_router.get("/streak")
async def get_streak(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Renvoie le streak basé sur les enregistrements energy quotidiens des 30 derniers jours."""
    try:
        # Compter le nombre de jours consécutifs jusqu'à aujourd'hui où l'user a un check-in
        r = await db.execute(text(
            "SELECT DATE(created_at) AS d FROM user_energy WHERE user_id = :uid "
            "AND created_at >= NOW() - INTERVAL 60 DAY ORDER BY d DESC"
        ), {"uid": user.id})
        days = sorted({row[0] for row in r.fetchall() if row[0]}, reverse=True)
    except Exception:
        days = []

    streak = 0
    today = date.today()
    cur = today
    for d in days:
        if isinstance(d, datetime):
            d = d.date()
        if d == cur:
            streak += 1
            cur = cur - timedelta(days=1)
        elif d == cur + timedelta(days=1):
            # account already counted, skip
            continue
        else:
            break

    return {"streak": streak, "last_check_in": days[0].isoformat() if days else None}


# ============================================================
# REVENUE  /api/revenue/monthly
# ============================================================
@missing_router.get("/revenue/monthly")
async def revenue_monthly(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Stub revenu — empty state. À brancher sur Mollie/Stripe plus tard."""
    # On peut aussi sommer finance_entries si elles existent
    try:
        r = await db.execute(text(
            "SELECT DATE_FORMAT(created_at, '%Y-%m') AS m, SUM(amount) AS total "
            "FROM finance_entries WHERE user_id = :uid AND type = 'revenue' "
            "GROUP BY m ORDER BY m DESC LIMIT 12"
        ), {"uid": user.id})
        rows = r.fetchall()
        series = [{"month": row[0], "total": float(row[1] or 0)} for row in rows]
    except Exception:
        series = []

    current = series[0]["total"] if series else 0.0
    return {
        "current_month": current,
        "currency": "EUR",
        "series": series,
        "growth_6m": None,
        "source": "manual" if series else "empty",
    }


# ============================================================
# ENERGY  /api/energy/today  /api/energy/latest
# ============================================================
@missing_router.get("/energy/today")
async def energy_today(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        r = await db.execute(text(
            "SELECT physique, mentale, stress, focus, mood, created_at FROM user_energy "
            "WHERE user_id = :uid AND DATE(created_at) = CURDATE() ORDER BY created_at DESC LIMIT 1"
        ), {"uid": user.id})
        row = r.fetchone()
    except Exception:
        row = None
    if not row:
        return {"recorded": False, "physique": None, "mentale": None, "stress": None,
                "focus": None, "mood": None, "checked_in_at": None}
    return {
        "recorded": True,
        "physique": row[0], "mentale": row[1], "stress": row[2],
        "focus": row[3], "mood": row[4],
        "checked_in_at": row[5].isoformat() if row[5] else None,
    }


@missing_router.get("/energy/latest")
async def energy_latest(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        r = await db.execute(text(
            "SELECT physique, mentale, stress, focus, mood, created_at FROM user_energy "
            "WHERE user_id = :uid ORDER BY created_at DESC LIMIT 1"
        ), {"uid": user.id})
        row = r.fetchone()
    except Exception:
        row = None
    if not row:
        return None
    return {
        "physique": row[0], "mentale": row[1], "stress": row[2],
        "focus": row[3], "mood": row[4],
        "checked_in_at": row[5].isoformat() if row[5] else None,
    }


# ============================================================
# PROCESSES TEMPLATES  /api/processes/templates
# ============================================================
PROCESS_TEMPLATES = [
    {"id": "onboarding-client", "name": "Onboarding client", "category": "Commercial", "steps": 6},
    {"id": "lancement-produit", "name": "Lancement produit", "category": "Marketing", "steps": 8},
    {"id": "newsletter-hebdo", "name": "Newsletter hebdomadaire", "category": "Marketing", "steps": 4},
    {"id": "facturation", "name": "Facturation mensuelle", "category": "Finance", "steps": 5},
    {"id": "recrutement", "name": "Recrutement freelance", "category": "Équipe", "steps": 6},
    {"id": "qualif-lead", "name": "Qualification d'un lead", "category": "Commercial", "steps": 5},
    {"id": "post-vente", "name": "Post-vente / fidélisation", "category": "Commercial", "steps": 5},
    {"id": "audit-mensuel", "name": "Audit mensuel business", "category": "Pilotage", "steps": 7},
]


@missing_router.get("/processes/templates")
async def processes_templates(user: User = Depends(get_current_user)):
    return {"templates": PROCESS_TEMPLATES}


# ============================================================
# ANALYSE  /api/analyse — Claude Sonnet 4.5
# ============================================================
async def _claude_complete(system: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """Complétion texte via Mammouth (OpenAI-compatible, modèles Claude/GPT/Gemini)."""
    from mammouth_client import chat as mammouth_chat, MammouthError
    try:
        return await mammouth_chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )
    except (MammouthError, Exception) as e:
        logger.exception("Mammouth completion failed: %s", e)
        return ""


@missing_router.get("/analyse")
async def get_analyse(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_analyse", user.id)
    if items:
        return items[0]
    return {
        "id": None,
        "summary": "",
        "verdict": None,
        "score": None,
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": [],
        "next_actions": [],
        "generated_at": None,
        "source": "empty",
    }


@missing_router.post("/analyse/run")
async def run_analyse(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère une analyse marché via Claude Sonnet 4.5 à partir du profil + vision."""
    # Récupérer contexte utilisateur
    vision_items = await _list_rows(db, "user_vision", user.id)
    vision = vision_items[0] if vision_items else {}
    profile_brief = (
        f"Utilisateur : {user.name or user.email}.\n"
        f"Secteur : {getattr(user, 'sector', '') or 'inconnu'}.\n"
        f"Vision (why) : {vision.get('why', 'non renseigné')}.\n"
        f"Vision (what) : {vision.get('what', 'non renseigné')}.\n"
        f"Cible (who) : {vision.get('who', 'non renseigné')}.\n"
    )
    system = (
        "Tu es un consultant senior en stratégie business, spécialisé en pré-validation de projets entrepreneuriaux. "
        "Tu produis des analyses SWOT actionnables, en français, en JSON strict. "
        "Pas de bla-bla : factuel, court, actionnable."
    )
    prompt = (
        f"Voici le contexte du solo founder :\n\n{profile_brief}\n\n"
        "Génère une analyse SWOT au format JSON strict avec cette structure (uniquement ces clés) :\n"
        "{\"summary\": \"2 phrases\", \"verdict\": \"go\"|\"pivot\"|\"abandon\", \"score\": 0-100, "
        "\"strengths\": [\"...\", \"...\"], \"weaknesses\": [\"...\", \"...\"], "
        "\"opportunities\": [\"...\", \"...\"], \"threats\": [\"...\", \"...\"], "
        "\"next_actions\": [\"action1\", \"action2\", \"action3\"]}\n"
        "Réponds UNIQUEMENT avec le JSON, sans markdown ni texte autour."
    )
    raw = await _claude_complete(system=system, user_prompt=prompt, max_tokens=1200)
    parsed = {}
    if raw:
        # Extraire JSON si Claude a entouré
        try:
            s = raw.strip()
            if s.startswith("```"):
                s = s.strip("`").split("\n", 1)[-1]
                if s.endswith("```"):
                    s = s.rsplit("```", 1)[0]
            parsed = json.loads(s)
        except Exception as e:
            logger.warning("analyse JSON parse failed: %s", e)
            parsed = {"summary": raw[:300], "verdict": None, "score": None}
    data = {
        "summary": parsed.get("summary", ""),
        "verdict": parsed.get("verdict"),
        "score": parsed.get("score"),
        "strengths": parsed.get("strengths") or [],
        "weaknesses": parsed.get("weaknesses") or [],
        "opportunities": parsed.get("opportunities") or [],
        "threats": parsed.get("threats") or [],
        "next_actions": parsed.get("next_actions") or [],
        "generated_at": _utc_now().isoformat(),
        "source": "claude-sonnet-4-5",
    }
    # Remplace l'ancienne analyse (1 par user)
    await _ensure_table(db, "user_analyse")
    await db.execute(text("DELETE FROM user_analyse WHERE user_id = :uid"), {"uid": user.id})
    await db.commit()
    return await _insert_row(db, "user_analyse", user.id, data)


@missing_router.post("/analyse/verdict")
async def verdict_analyse(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Force juste le calcul d'un verdict synthétique (réutilise l'analyse existante)."""
    items = await _list_rows(db, "user_analyse", user.id)
    if not items:
        raise HTTPException(404, "Aucune analyse — lance d'abord /analyse/run")
    return {"verdict": items[0].get("verdict"), "score": items[0].get("score")}


@missing_router.post("/analyse/mom-test-guide")
async def mom_test_guide(user: User = Depends(get_current_user)):
    """Renvoie un guide Mom Test français court (statique, pas besoin de LLM)."""
    return {
        "title": "Mom Test — 3 règles d'or",
        "rules": [
            "Parlez de la vie du client, pas de votre idée.",
            "Posez des questions spécifiques sur le passé, pas des hypothèses sur le futur.",
            "Écoutez plus que vous ne parlez — leur silence vaut leurs mots.",
        ],
        "questions": [
            "Qu'est-ce qui est difficile pour vous en ce moment dans [domaine] ?",
            "Quand avez-vous essayé de résoudre ce problème pour la dernière fois ?",
            "Quelle solution avez-vous essayée ? Pourquoi ne marche-t-elle pas ?",
            "Combien dépensez-vous actuellement (temps/argent) pour gérer ça ?",
            "Si je vous propose [votre idée], qu'est-ce qui vous ferait dire non ?",
        ],
    }


@missing_router.get("/analyse/export")
async def export_analyse(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_analyse", user.id)
    if not items:
        return {"format": "markdown", "content": "# Aucune analyse\n\nLance d'abord une analyse depuis l'app."}
    a = items[0]
    md = [
        f"# Analyse stratégique\n\n_Généré le {a.get('generated_at', '')}_",
        f"\n## Verdict : **{(a.get('verdict') or 'à déterminer').upper()}**  ·  Score : {a.get('score') or '—'}/100",
        f"\n## Synthèse\n{a.get('summary', '')}",
        "\n## Forces\n" + "\n".join(f"- {x}" for x in (a.get("strengths") or [])),
        "\n## Faiblesses\n" + "\n".join(f"- {x}" for x in (a.get("weaknesses") or [])),
        "\n## Opportunités\n" + "\n".join(f"- {x}" for x in (a.get("opportunities") or [])),
        "\n## Menaces\n" + "\n".join(f"- {x}" for x in (a.get("threats") or [])),
        "\n## Prochaines actions\n" + "\n".join(f"1. {x}" for x in (a.get("next_actions") or [])),
    ]
    return {"format": "markdown", "content": "\n".join(md)}


# ============================================================
# COLLABORATEUR  /api/collaborateur/notify (event log léger)
#                /api/collaborateur/chat   (Claude Sonnet 4.5)
# ============================================================
class CollabNotifyIn(BaseModel):
    event: str
    title: Optional[str] = None
    duration_min: Optional[int] = None
    notes: Optional[str] = None


@missing_router.post("/collaborateur/notify")
async def collab_notify(body: CollabNotifyIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Enregistre un événement à destination du collaborateur IA (mission_started, etc.).
    Sert de fil d'événements que le chat IA peut lire pour contextualiser ses réponses."""
    data = body.dict()
    data["ts"] = _utc_now().isoformat()
    return await _insert_row(db, "user_collab_events", user.id, data)


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatIn(BaseModel):
    messages: list[ChatMessage]
    context_page: Optional[str] = None
    ui_language: Optional[str] = "fr"


@missing_router.post("/collaborateur/chat")
async def collab_chat(body: ChatIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Chat IA avec contexte utilisateur (vision, tasks, page actuelle).
    Utilise Claude Sonnet 4.5 via emergentintegrations.

    Quota par plan (mois courant) :
        free=10, start=300, grow=1500, serenity/business/admin=illimité.
    """
    # ── 1. Vérification quota IA (avant l'appel coûteux à Claude) ─────
    from routes.ai_quota import check_and_increment
    is_admin = bool(getattr(user, "is_admin", False) or getattr(user, "role", None) in ("admin", "super_admin"))
    quota = await check_and_increment(db, user.id, getattr(user, "plan", None), is_admin=is_admin)
    if not quota.get("ok"):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "ai_quota_exceeded",
                "used": quota.get("used"),
                "limit": quota.get("limit"),
                "message": f"Quota IA mensuel atteint ({quota.get('limit')} messages). Upgradez votre plan pour continuer.",
            },
        )

    # Build context : vision + 3 last tasks + page courante
    vision_items = await _list_rows(db, "user_vision", user.id)
    vision = vision_items[0] if vision_items else {}
    tasks_all = await _list_rows(db, "user_tasks", user.id)
    pending_tasks = [t for t in tasks_all if not t.get("done")][:5]

    name = (user.name or "").split()[0] if user.name else "ami"
    page = body.context_page or "Dashboard"
    lang = body.ui_language or "fr"

    sys_lang = {
        "fr": "Tu réponds toujours en français.",
        "en": "Always answer in English.",
        "es": "Responde siempre en español.",
        "de": "Antworte immer auf Deutsch.",
        "it": "Rispondi sempre in italiano.",
        "pt": "Responda sempre em português.",
    }.get(lang, "Tu réponds toujours en français.")

    system = (
        f"Tu es le Collaborateur IA personnel de {name}, intégré à son cockpit business MyExtension AI (plateforme Zayado). "
        f"{sys_lang} "
        f"Page actuelle : {page}. "
        "Style : direct, chaleureux, factuel. Pas de blabla, pas de listes interminables. "
        "Réponses courtes (3-6 phrases sauf si l'utilisateur demande plus). "
        "Tu peux poser une question de clarification si nécessaire. "
        "Tu connais le contexte business du user — utilise-le si pertinent.\n\n"
        f"=== Contexte business de {name} ===\n"
        f"Vision (why) : {vision.get('why') or 'non renseigné'}\n"
        f"Cible (who)  : {vision.get('who') or 'non renseigné'}\n"
        f"Offre (what) : {vision.get('what') or 'non renseigné'}\n"
        f"Missions en cours ({len(pending_tasks)}) : "
        + (", ".join(t.get("label", "") for t in pending_tasks) if pending_tasks else "aucune")
    )

    # Build conversation : Claude n'accepte qu'un message à la fois via emergentintegrations,
    # on concatène l'historique dans un seul message utilisateur final
    history = body.messages or []
    if not history:
        return {"reply": "Bonjour, comment puis-je vous aider ?"}

    # ── Bug #5/#18 : tronquer l'historique à 10 tours (20 messages max) ──
    # Évite le timeout 30s et le crash Chrome sur les longues conversations
    MAX_TURNS = 10
    if len(history) > MAX_TURNS * 2:
        history = history[-(MAX_TURNS * 2):]

    last_user = history[-1].content if history[-1].role == "user" else ""
    prev_turns = ""
    for m in history[:-1]:
        prefix = "User" if m.role == "user" else "Assistant"
        # Tronquer chaque message à 800 chars max pour éviter les payloads géants
        content = str(m.content)[:800]
        prev_turns += f"\n{prefix}: {content}"
    user_msg = (prev_turns + f"\nUser: {last_user}\nAssistant:").strip() if prev_turns else last_user

    try:
        # Timeout explicite 25s (< Railway 30s) pour éviter le crash Chrome
        import asyncio as _asyncio
        reply = await _asyncio.wait_for(
            _claude_complete(system=system, user_prompt=user_msg, max_tokens=600),
            timeout=25.0
        )
    except _asyncio.TimeoutError:
        logger.warning("Chat timeout after 25s — returning fallback")
        reply = ""
    except Exception as e:
        logger.exception("Chat Claude error: %s", e)
        reply = ""
    if not reply:
        reply = "Désolé, je n'ai pas pu générer de réponse. Réessayez dans un instant."
    return {
        "reply": reply,
        "quota": {
            "used": quota.get("used"),
            "limit": quota.get("limit"),
            "remaining": quota.get("remaining"),
        },
    }


# ── AI quota endpoint ────────────────────────────────────────────────
@missing_router.get("/ai/quota")
async def ai_quota_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Retourne la quota IA mensuelle du user (used / limit / remaining)."""
    from routes.ai_quota import get_usage, _plan_limit
    is_admin = bool(getattr(user, "is_admin", False) or getattr(user, "role", None) in ("admin", "super_admin"))
    plan = getattr(user, "plan", None)
    usage = await get_usage(db, user.id)
    limit = _plan_limit(plan, is_admin=is_admin)
    used = usage["used"]
    remaining = None if limit is None else max(0, limit - used)
    return {
        "plan": plan,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "unlimited": limit is None,
        "year": usage["year"],
        "month": usage["month"],
    }


# ── Stub endpoints for /settings?section=integrations to silence 404 noise ──
@missing_router.get("/whatsapp/status")
async def whatsapp_status(user=Depends(get_current_user)):
    """Stub: returns disconnected state to silence console 404 on Integrations section."""
    return {"connected": False, "phone": None, "provider": "whatsapp-cloud-api"}


@missing_router.get("/revenue/sources/status")
async def revenue_sources_status(user=Depends(get_current_user)):
    """Stub: revenue source connections (Stripe, Mollie, bank). Stub for now."""
    return {"connected_sources": [], "available_sources": ["stripe", "mollie", "manual"]}


@missing_router.get("/integrations/whatsapp-personal/status")
async def whatsapp_personal_status(user=Depends(get_current_user)):
    """Stub: WhatsApp personal QR pairing status."""
    return {"connected": False, "qr_pending": False, "session_id": None}


@missing_router.get("/integrations/brevo/status")
async def brevo_status(user=Depends(get_current_user)):
    """Stub: Brevo email integration status."""
    brevo_key_set = bool(os.environ.get("BREVO_API_KEY"))
    return {"connected": brevo_key_set, "sender_email": os.environ.get("BREVO_SENDER_EMAIL"), "personal": False}


@missing_router.post("/wellness/bilan/send")
async def wellness_bilan_send(payload: dict, user=Depends(get_current_user)):
    """Send the weekly/quarterly wellness bilan to the user + support@zayado.net via Brevo."""
    from utils import send_brevo_email
    # user can be dict (alias) or User pydantic object — handle both
    user_email = getattr(user, "email", None) or (user.get("email") if hasattr(user, "get") else None)
    phys = payload.get("physique", 0)
    ment = payload.get("mentale", 0)
    stress = payload.get("stress", 0)
    quarter = payload.get("quarter", "")
    html = f"""
    <h2>Bilan bien-être</h2>
    <p><strong>Énergie physique :</strong> {phys}/10</p>
    <p><strong>Clarté mentale :</strong> {ment}/10</p>
    <p><strong>Niveau de stress :</strong> {stress}/10</p>
    <p><strong>Trimestre :</strong> {quarter}</p>
    <p style="color:#777">— L'équipe MyExtension-ai</p>
    """
    subject = f"Votre bilan bien-être — MyExtension-ai"
    sent_user = bool(user_email) and send_brevo_email(to_email=user_email, subject=subject, html_content=html, brand="myextension")
    sent_support = send_brevo_email(to_email="support@zayado.net", subject=f"[Bilan client] {user_email or 'inconnu'}", html_content=html, brand="myextension")
    return {"ok": True, "sent_to_user": sent_user, "sent_to_support": sent_support, "message": "Bilan envoyé"}


@missing_router.post("/wellness/daily")
async def wellness_daily(payload: dict, user=Depends(get_current_user)):
    """Save the daily wellness check-in (stub for now — frontend uses localStorage too)."""
    return {"ok": True, "saved_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}


@missing_router.get("/wellness/state")
async def wellness_state(user=Depends(get_current_user)):
    """Returns full wellness state for /bien-etre page: today, history 30d, bilans, recos, weekly form."""
    uid = getattr(user, "id", None) or (user.get("id") if hasattr(user, "get") else None)
    today = {"physique": 6, "mentale": 6, "stress": 4, "verdict": "Modérée", "raison": "Énergie moyenne, stress contenu.", "rituel": ["1 décision importante max", "3 tâches IA à valider (15 min)", "Pas d'appel client à froid"], "citation": "« On ralentit pour décider juste. »"}
    try:
        from sqlalchemy import text
        from database import async_session_factory
        from datetime import datetime, timezone, timedelta
        async with async_session_factory() as s:
            r = await s.execute(text("SELECT value FROM user_data WHERE user_id = :uid AND \"key\" = 'wellness_today'"), {"uid": uid})
            row = r.fetchone()
            if row and row[0]:
                import json
                try: today = {**today, **json.loads(row[0])}
                except Exception: pass
            r = await s.execute(text("SELECT value FROM user_data WHERE user_id = :uid AND \"key\" = 'wellness_history_30d'"), {"uid": uid})
            row2 = r.fetchone()
            history = []
            if row2 and row2[0]:
                import json
                try: history = json.loads(row2[0])
                except Exception: history = []
            if not history:
                # empty state: 30 days with current today's values
                history = []
    except Exception:
        history = []
    return {
        "today": today,
        "energyHistory": history,
        "bilanHistory": [
            {"id": "q4-2025", "title": "Bilan Q4 2025", "period": "Oct-Déc 2025", "energieMoyenne": 6.8, "stressMoyen": 4.1, "verdict": "Trimestre solide.", "stable": True, "status": "current"},
            {"id": "q3-2025", "title": "Bilan Q3 2025", "period": "Jul-Sep 2025", "energieMoyenne": 5.9, "stressMoyen": 5.2, "verdict": "Trimestre difficile, charge trop forte.", "stable": False, "status": "archived"},
        ],
        "boutiqueRecos": [
            {"id": "the-adaptogene", "title": "Thé adaptogène", "price": "18€", "raison": "Stress modéré détecté"},
            {"id": "luminothérapie", "title": "Lampe luminothérapie", "price": "89€", "raison": "Énergie basse en hiver"},
            {"id": "carnet-rituel", "title": "Carnet rituel matin", "price": "24€", "raison": "Pour ancrer le rituel"},
        ],
        "weeklyReview": {"questions": ["Décision la plus stratégique cette semaine ?", "Tâche que j'aurais dû déléguer ?", "Mon vrai niveau d'énergie en moyenne (1-10) ?", "Une chose à arrêter la semaine prochaine ?", "Mon focus principal lundi ?"]}
    }
