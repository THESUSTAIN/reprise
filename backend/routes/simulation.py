"""Routes Simulation — clients virtuels IA adaptatifs à n'importe quel programme
(licence, licence pro, bachelor, master, MBA...).

Bêta gratuite : pas de plafond de plan (contrairement à Studio), mais un garde-fou
anti-abus (MAX_TASKS_PER_DAY) pour protéger le budget LLM pendant le test bêta.

Endpoints :
- POST /api/simulation/start          → crée le profil + 3 clients virtuels + 1ère tâche chacun
- GET  /api/simulation/state          → profil, clients, progression
- GET  /api/simulation/clients/{id}/task  → tâche en cours du client (en génère une si besoin)
- POST /api/simulation/tasks/{id}/submit  → soumet une réponse, reçoit le feedback IA
- GET  /api/simulation/history         → historique complet des réponses + feedback IA (le plus récent d'abord)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, SimuProfile, SimuClient, SimuTask, SimuResponse
from deps import get_current_user
import simulation_service as sim

log = logging.getLogger(__name__)
simulation_router = APIRouter(prefix="/simulation", tags=["Simulation"])

MAX_TASKS_PER_DAY = 20  # garde-fou anti-abus pendant la bêta gratuite illimitée


# ─────────── Schemas ─────────────────────────────────────
class StartRequest(BaseModel):
    programme_label: str = Field(min_length=3, max_length=255)
    diploma_level: Optional[str] = "master"  # licence | licence_pro | bachelor | master | mba


class SubmitRequest(BaseModel):
    response_text: str = Field(min_length=10, max_length=8000)


# ─────────── Helpers ─────────────────────────────────────
async def _get_profile(db: AsyncSession, user_id: str) -> Optional[SimuProfile]:
    r = await db.execute(select(SimuProfile).where(SimuProfile.user_id == user_id))
    return r.scalar_one_or_none()


async def _tasks_created_today(db: AsyncSession, user_id: str) -> int:
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    r = await db.execute(
        select(func.count(SimuTask.id)).where(SimuTask.user_id == user_id, SimuTask.created_at >= start_of_day)
    )
    return r.scalar() or 0


async def _ensure_task_for_client(db: AsyncSession, user: User, profile: SimuProfile, client: SimuClient) -> SimuTask:
    """Retourne la tâche pending du client, ou en génère une nouvelle."""
    r = await db.execute(
        select(SimuTask).where(SimuTask.client_id == client.id, SimuTask.status == "pending").order_by(SimuTask.created_at.desc())
    )
    existing = r.scalar_one_or_none()
    if existing:
        return existing

    if await _tasks_created_today(db, str(user.id)) >= MAX_TASKS_PER_DAY:
        raise HTTPException(429, "Limite quotidienne de tâches atteinte pour la bêta gratuite. Revenez demain !")

    r2 = await db.execute(
        select(SimuTask.title).where(SimuTask.client_id == client.id).order_by(SimuTask.created_at.desc()).limit(3)
    )
    previous_titles = [row[0] for row in r2.all()]

    try:
        data = await sim.generate_task_for_client(
            client={"name": client.name, "industry": client.industry, "company_size": client.company_size,
                    "personality": client.personality, "budget": client.budget},
            domain=profile.domain or profile.programme_label,
            day=profile.current_day,
            previous_task_titles=previous_titles,
        )
    except Exception as e:
        log.exception("Génération de tâche échouée")
        raise HTTPException(502, f"Génération de la tâche impossible : {e}")

    task = SimuTask(
        client_id=client.id, user_id=str(user.id),
        title=data.get("title", "Nouvelle demande"),
        description=data.get("description", ""),
        difficulty=int(data.get("difficulty", 1)),
        key_points=data.get("key_points", []),
        rubric=data.get("rubric", {}),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


def _task_out(task: SimuTask, client: SimuClient) -> dict:
    return {
        "id": task.id, "client_id": client.id, "client_name": client.name,
        "title": task.title, "description": task.description,
        "difficulty": task.difficulty, "status": task.status,
    }


# ─────────── Endpoints ─────────────────────────────────────
@simulation_router.post("/start")
async def start_simulation(payload: StartRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    existing = await _get_profile(db, str(user.id))
    if existing:
        raise HTTPException(409, "Simulation déjà démarrée. Utilisez GET /simulation/state.")

    try:
        gen = await sim.generate_initial_clients(payload.programme_label, n=3)
    except Exception as e:
        log.exception("Génération des clients initiaux échouée")
        raise HTTPException(502, f"Génération des clients impossible : {e}")

    profile = SimuProfile(
        user_id=str(user.id),
        programme_label=payload.programme_label,
        diploma_level=payload.diploma_level or "master",
        domain=gen.get("domain", payload.programme_label),
    )
    db.add(profile)
    await db.flush()  # pour avoir profile.id sans commit prématuré

    clients_out = []
    for c in gen.get("clients", [])[:3]:
        client = SimuClient(
            user_id=str(user.id), name=c.get("name", "Client"), industry=c.get("industry", "Général"),
            company_size=c.get("company_size", "small"), personality=c.get("personality", "collaborative"),
            budget=int(c.get("budget", 10000)), initial_problem=c.get("initial_problem", ""),
        )
        db.add(client)
        clients_out.append(client)
    await db.commit()
    for c in clients_out:
        await db.refresh(c)
    await db.refresh(profile)

    # Première tâche pour chaque client
    tasks_out = []
    for client in clients_out:
        task = await _ensure_task_for_client(db, user, profile, client)
        tasks_out.append(_task_out(task, client))

    return {"domain": profile.domain, "clients": [{"id": c.id, "name": c.name, "industry": c.industry} for c in clients_out], "tasks": tasks_out}


@simulation_router.get("/state")
async def get_state(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile(db, str(user.id))
    if not profile:
        return {"started": False}

    r = await db.execute(select(SimuClient).where(SimuClient.user_id == str(user.id), SimuClient.is_active == True))
    clients = r.scalars().all()

    clients_out = []
    for client in clients:
        r2 = await db.execute(
            select(SimuTask).where(SimuTask.client_id == client.id, SimuTask.status == "pending").order_by(SimuTask.created_at.desc())
        )
        pending = r2.scalar_one_or_none()
        clients_out.append({
            "id": client.id, "name": client.name, "industry": client.industry,
            "personality": client.personality,
            "current_task": _task_out(pending, client) if pending else None,
        })

    return {
        "started": True,
        "programme_label": profile.programme_label,
        "domain": profile.domain,
        "current_day": profile.current_day,
        "tasks_completed": profile.tasks_completed,
        "average_score": round(profile.average_score, 1),
        "clients": clients_out,
    }


@simulation_router.get("/clients/{client_id}/task")
async def get_client_task(client_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile(db, str(user.id))
    if not profile:
        raise HTTPException(404, "Simulation non démarrée. Appelez POST /simulation/start.")

    r = await db.execute(select(SimuClient).where(SimuClient.id == client_id, SimuClient.user_id == str(user.id)))
    client = r.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client introuvable.")

    task = await _ensure_task_for_client(db, user, profile, client)
    return _task_out(task, client)


@simulation_router.get("/history")
async def get_history(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Historique complet des réponses + feedback IA de l'utilisateur, du plus récent au plus ancien.
    Les données existaient déjà en base (SimuResponse) mais n'étaient jusqu'ici jamais exposées :
    le feedback disparaissait dès qu'on changeait de client ou qu'on rechargeait la page.
    """
    r = await db.execute(
        select(SimuResponse, SimuTask, SimuClient)
        .join(SimuTask, SimuTask.id == SimuResponse.task_id)
        .join(SimuClient, SimuClient.id == SimuTask.client_id)
        .where(SimuResponse.user_id == str(user.id))
        .order_by(SimuResponse.submitted_at.desc())
    )
    rows = r.all()
    return {
        "count": len(rows),
        "items": [
            {
                "response_id": resp.id,
                "submitted_at": resp.submitted_at.isoformat() if resp.submitted_at else None,
                "client_name": client.name,
                "client_industry": client.industry,
                "task_title": task.title,
                "response_text": resp.response_text,
                "score": resp.score,
                "feedback": resp.ai_feedback,
            }
            for resp, task, client in rows
        ],
    }


@simulation_router.post("/tasks/{task_id}/submit")
async def submit_task(task_id: str, payload: SubmitRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(SimuTask).where(SimuTask.id == task_id, SimuTask.user_id == str(user.id)))
    task = r.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Tâche introuvable.")
    if task.status != "pending":
        raise HTTPException(409, "Cette tâche a déjà été soumise.")

    r2 = await db.execute(select(SimuClient).where(SimuClient.id == task.client_id))
    client = r2.scalar_one_or_none()
    profile = await _get_profile(db, str(user.id))

    try:
        evaluation = await sim.evaluate_response(
            task={"title": task.title, "key_points": task.key_points, "rubric": task.rubric},
            client={"name": client.name, "industry": client.industry, "personality": client.personality},
            domain=profile.domain or profile.programme_label,
            user_response=payload.response_text,
        )
    except Exception as e:
        log.exception("Évaluation échouée")
        raise HTTPException(502, f"Évaluation impossible : {e}")

    score = int(evaluation.get("score", 0))
    response = SimuResponse(task_id=task.id, user_id=str(user.id), response_text=payload.response_text, score=score, ai_feedback=evaluation)
    db.add(response)

    task.status = "reviewed"

    # Mise à jour progression
    profile.tasks_completed += 1
    profile.average_score = ((profile.average_score * (profile.tasks_completed - 1)) + score) / profile.tasks_completed
    if profile.tasks_completed % 1 == 0:  # jour +1 à chaque tâche complétée (rythme simple pour la bêta)
        profile.current_day += 1

    await db.commit()

    # Génère immédiatement la prochaine mission de ce client pour un entraînement continu
    # (échec silencieux : la tâche sera régénérée à la demande via GET /clients/{id}/task).
    next_task_out = None
    try:
        next_task = await _ensure_task_for_client(db, user, profile, client)
        next_task_out = _task_out(next_task, client)
    except HTTPException:
        pass
    except Exception:
        log.exception("Génération de la tâche suivante échouée (non bloquant)")

    return {
        "score": score,
        "comments": evaluation.get("comments"),
        "what_went_well": evaluation.get("what_went_well", []),
        "improvements_needed": evaluation.get("improvements_needed", []),
        "learning_point": evaluation.get("learning_point"),
        "client_reaction": evaluation.get("client_reaction"),
        "next_task": next_task_out,
        "progress": {"tasks_completed": profile.tasks_completed, "average_score": round(profile.average_score, 1)},
    }
