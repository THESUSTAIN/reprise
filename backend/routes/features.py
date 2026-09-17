"""
Routes pour les fonctionnalites Diagnostic, Capture, Priorite, Structuration, Focus, Energie.
Persistance en base de donnees (SQLAlchemy).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from database import get_db
from deps import get_current_user
from models import (
    Capture, UserPriority, UserEnergy, UserFocusSession,
    UserStructuration, DiagnosticResult, UserOnboarding
)
# Email transactionnel Brevo (marque "myextension" pour l'app SaaS).
# Import protégé : si Brevo n'est pas configuré (dev sans clé), l'onboarding
# doit rester fonctionnel — l'envoi d'email est simplement sauté.
try:
    from utils import send_brevo_email  # type: ignore
except Exception:
    send_brevo_email = None  # noqa: N816

features_router = APIRouter(tags=["features"])
onboarding_alias_router = APIRouter(tags=["features"])


# ── Pydantic Models ───────────────────────────────────────────────

class CaptureCreate(BaseModel):
    content: str
    category: str = "idee"
    source: str = "text"

class CaptureUpdate(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

class PrioritySet(BaseModel):
    title: str
    why: Optional[str] = None
    estimated_time: Optional[str] = None

class EnergySet(BaseModel):
    level: int
    note: Optional[str] = None

class FocusSession(BaseModel):
    task: str
    duration: int
    completed: bool = True

class StructurationAction(BaseModel):
    pillar: str
    action_index: int
    done: bool

class DiagnosticSubmit(BaseModel):
    answers: dict
    scores: dict = None

class OnboardingData(BaseModel):
    status: str = ""
    sector: str = ""
    objective: str = ""
    challenge: str = ""
    budget: str = ""
    experience: str = ""
    wellbeing_score: int = 5
    wellbeing_mood: str = ""
    wellbeing_note: str = ""
    monthly_revenue: str = ""
    has_recurring_expenses: str = ""


def _row_to_dict(row, exclude=None):
    d = {}
    exclude = exclude or set()
    for col in row.__table__.columns:
        if col.name in exclude or col.name == "_id":
            continue
        val = getattr(row, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        d[col.name] = val
    return d


# ── Captures ──────────────────────────────────────────────────────

@features_router.get("/captures")
async def get_captures(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Capture).where(Capture.user_id == user.id).order_by(Capture.created_at.desc()).limit(100)
    )
    return [_row_to_dict(r) for r in result.scalars().all()]

@features_router.post("/captures")
async def create_capture(body: CaptureCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cap = Capture(user_id=user.id, content=body.content, category=body.category, source=body.source)
    db.add(cap)
    await db.commit()
    await db.refresh(cap)
    return _row_to_dict(cap)

@features_router.put("/captures/{capture_id}")
async def update_capture(capture_id: str, body: CaptureUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Capture).where(and_(Capture.id == capture_id, Capture.user_id == user.id)))
    cap = result.scalar_one_or_none()
    if not cap:
        raise HTTPException(404, "Capture introuvable")
    if body.content is not None:
        cap.content = body.content
    if body.category is not None:
        cap.category = body.category
    if body.status is not None:
        cap.status = body.status
    await db.commit()
    await db.refresh(cap)
    return _row_to_dict(cap)

@features_router.delete("/captures/{capture_id}")
async def delete_capture(capture_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Capture).where(and_(Capture.id == capture_id, Capture.user_id == user.id)))
    await db.commit()
    return {"status": "deleted"}


# ── Priority of the Day ──────────────────────────────────────────

@features_router.get("/priority")
async def get_priority(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = datetime.now(timezone.utc).date().isoformat()
    result = await db.execute(
        select(UserPriority).where(and_(UserPriority.user_id == user.id, UserPriority.date == today))
    )
    p = result.scalar_one_or_none()
    if not p:
        return {
            "title": "Definir votre priorite du jour",
            "why": "Choisissez la tache qui aura le plus d'impact aujourd'hui",
            "estimated_time": "2h",
            "badge": "ESSENTIEL",
            "value": "Haute Valeur",
            "set_by": "default",
            "date": today,
        }
    return {**_row_to_dict(p), "badge": "ESSENTIEL", "value": "Haute Valeur", "set_by": "user"}

@features_router.post("/priority")
async def set_priority(body: PrioritySet, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = datetime.now(timezone.utc).date().isoformat()
    result = await db.execute(
        select(UserPriority).where(and_(UserPriority.user_id == user.id, UserPriority.date == today))
    )
    p = result.scalar_one_or_none()
    if p:
        p.title = body.title
        p.why = body.why or ""
        p.estimated_time = body.estimated_time or "2h"
    else:
        p = UserPriority(user_id=user.id, title=body.title, why=body.why or "", estimated_time=body.estimated_time or "2h", date=today)
        db.add(p)
    await db.commit()
    await db.refresh(p)
    return {**_row_to_dict(p), "badge": "ESSENTIEL", "value": "Haute Valeur", "set_by": "user"}

@features_router.get("/priority/history")
async def get_priority_history(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserPriority).where(UserPriority.user_id == user.id).order_by(UserPriority.created_at.desc()).limit(30)
    )
    return [{**_row_to_dict(p), "badge": "ESSENTIEL", "value": "Haute Valeur", "set_by": "user"} for p in result.scalars().all()]


# ── Energy ────────────────────────────────────────────────────────

@features_router.get("/energy")
async def get_energy(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = datetime.now(timezone.utc).date().isoformat()
    result = await db.execute(
        select(UserEnergy).where(and_(UserEnergy.user_id == user.id, UserEnergy.date == today))
    )
    e = result.scalar_one_or_none()
    if not e:
        return {"level": 0, "note": "", "date": today, "set": False}
    return {"level": e.level, "note": e.note or "", "date": today, "set": True}

@features_router.post("/energy")
async def set_energy(body: EnergySet, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = datetime.now(timezone.utc).date().isoformat()
    result = await db.execute(
        select(UserEnergy).where(and_(UserEnergy.user_id == user.id, UserEnergy.date == today))
    )
    e = result.scalar_one_or_none()
    if e:
        e.level = body.level
        e.note = body.note or ""
    else:
        e = UserEnergy(user_id=user.id, level=body.level, note=body.note or "", date=today)
        db.add(e)
    await db.commit()
    await db.refresh(e)
    return {"level": e.level, "note": e.note or "", "date": today, "set": True}

@features_router.get("/energy/history")
async def get_energy_history(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserEnergy).where(UserEnergy.user_id == user.id).order_by(UserEnergy.created_at.desc()).limit(90)
    )
    return [{"level": e.level, "note": e.note or "", "date": e.date, "set": True} for e in result.scalars().all()]


# ── Focus Sessions ───────────────────────────────────────────────

@features_router.get("/focus/sessions")
async def get_focus_sessions(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserFocusSession).where(UserFocusSession.user_id == user.id).order_by(UserFocusSession.created_at.desc()).limit(100)
    )
    return [_row_to_dict(r) for r in result.scalars().all()]

@features_router.post("/focus/sessions")
async def create_focus_session(body: FocusSession, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = UserFocusSession(user_id=user.id, task=body.task, duration=body.duration, completed=body.completed)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _row_to_dict(session)

@features_router.get("/focus/stats")
async def get_focus_stats(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserFocusSession).where(UserFocusSession.user_id == user.id)
    )
    sessions = result.scalars().all()
    today = datetime.now(timezone.utc).date().isoformat()
    today_sessions = [s for s in sessions if s.created_at.date().isoformat() == today]
    return {
        "today_sessions": len(today_sessions),
        "today_minutes": round(sum(s.duration for s in today_sessions) / 60),
        "total_sessions": len(sessions),
        "total_minutes": round(sum(s.duration for s in sessions) / 60),
    }


# ── Structuration Progress ───────────────────────────────────────

@features_router.get("/structuration")
async def get_structuration(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserStructuration).where(UserStructuration.user_id == user.id)
    )
    rows = result.scalars().all()
    return {f"{r.pillar}_{r.action_index}": r.done for r in rows}

@features_router.post("/structuration")
async def update_structuration(body: StructurationAction, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserStructuration).where(and_(
            UserStructuration.user_id == user.id,
            UserStructuration.pillar == body.pillar,
            UserStructuration.action_index == body.action_index
        ))
    )
    row = result.scalar_one_or_none()
    if row:
        row.done = body.done
    else:
        row = UserStructuration(user_id=user.id, pillar=body.pillar, action_index=body.action_index, done=body.done)
        db.add(row)
    await db.commit()
    # Return full progress
    result2 = await db.execute(select(UserStructuration).where(UserStructuration.user_id == user.id))
    rows = result2.scalars().all()
    return {f"{r.pillar}_{r.action_index}": r.done for r in rows}


# ── Diagnostic Score ─────────────────────────────────────────────

@features_router.get("/diagnostic/score")
async def get_diagnostic_score(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = datetime.now(timezone.utc).date().isoformat()
    # Captures count
    cap_result = await db.execute(select(Capture).where(Capture.user_id == user.id))
    captures = len(cap_result.scalars().all())
    # Priority
    pri_result = await db.execute(select(UserPriority).where(and_(UserPriority.user_id == user.id, UserPriority.date == today)))
    priority = pri_result.scalar_one_or_none()
    # Energy
    ene_result = await db.execute(select(UserEnergy).where(and_(UserEnergy.user_id == user.id, UserEnergy.date == today)))
    energy = ene_result.scalar_one_or_none()
    # Structuration
    str_result = await db.execute(select(UserStructuration).where(and_(UserStructuration.user_id == user.id, UserStructuration.done.is_(True))))
    struct_rows = str_result.scalars().all()
    # Focus sessions
    foc_result = await db.execute(select(UserFocusSession).where(UserFocusSession.user_id == user.id))
    focus_sessions = foc_result.scalars().all()
    today_sessions = [s for s in focus_sessions if s.created_at.date().isoformat() == today]

    clarity = min(100, len([r for r in struct_rows if r.pillar == "clarity"]) * 25)
    energy_score = min(100, (energy.level * 20 if energy else 0))
    alignment = min(100, len([r for r in struct_rows if r.pillar == "alignment"]) * 25)
    revenue = min(100, len([r for r in struct_rows if r.pillar == "revenue"]) * 25)

    if priority:
        clarity = min(100, clarity + 15)
    if captures > 0:
        clarity = min(100, clarity + 10)
    if len(focus_sessions) > 0:
        energy_score = min(100, energy_score + 15)

    global_score = round((clarity + energy_score + alignment + revenue) / 4)

    return {
        "score": global_score,
        "pillars": {"clarity": clarity, "energy": energy_score, "alignment": alignment, "revenue": revenue},
        "captures_count": captures,
        "has_priority": priority is not None,
        "has_energy": energy is not None,
        "focus_sessions_today": len(today_sessions),
    }


@features_router.post("/diagnostic/submit")
async def submit_diagnostic(data: DiagnosticSubmit, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    a = data.answers
    scores = data.scores if data.scores else None

    if scores and 'pillars' in scores:
        global_score = scores.get('overall', 0)
        clarity = scores['pillars'].get('clarity', 0)
        energy_score = scores['pillars'].get('energy', 0)
        alignment = scores['pillars'].get('alignment', 0)
    else:
        clarity_qs = ['q1_capture', 'q2_deepwork', 'q3_essentialism', 'q4_habits', 'q5_onething']
        energy_qs = ['q6_energy_level', 'q7_morning', 'q8_burnout', 'q9_rest', 'q10_boundaries']
        alignment_qs = ['q11_emyth', 'q12_purpose', 'q13_companyofone', 'q14_values', 'q15_sabbath']

        def calc_pillar(qs):
            total = sum(a.get(q, 3) if isinstance(a.get(q), (int, float)) else 3 for q in qs)
            return round((total / (len(qs) * 5)) * 100)

        clarity = calc_pillar(clarity_qs)
        energy_score = calc_pillar(energy_qs)
        alignment = calc_pillar(alignment_qs)
        global_score = round((clarity + energy_score + alignment) / 3)

    dr = DiagnosticResult(
        user_id=user.id,
        answers=json.dumps(a),
        score=global_score,
        clarity=clarity,
        energy=energy_score,
        alignment=alignment,
    )
    db.add(dr)
    await db.commit()

    return {
        "score": global_score,
        "overall": global_score,
        "pillars": {"clarity": clarity, "energy": energy_score, "alignment": alignment},
    }


# ── Onboarding ────────────────────────────────────────────────────

@features_router.post("/onboarding/complete")
async def complete_onboarding(body: OnboardingData, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserOnboarding).where(UserOnboarding.user_id == user.id))
    ob = result.scalar_one_or_none()
    if ob:
        ob.status = body.status
        ob.sector = body.sector
        ob.objective = body.objective
        ob.challenge = body.challenge
        ob.budget = body.budget
        ob.experience = body.experience
        ob.completed = True
    else:
        ob = UserOnboarding(
            user_id=user.id, status=body.status, sector=body.sector,
            objective=body.objective, challenge=body.challenge,
            budget=body.budget, experience=body.experience, completed=True,
        )
        db.add(ob)

    # Save extended fields in user settings
    settings = user.settings or {}
    settings["wellbeing_score"] = body.wellbeing_score
    settings["wellbeing_mood"] = body.wellbeing_mood
    settings["wellbeing_note"] = body.wellbeing_note
    settings["monthly_revenue"] = body.monthly_revenue
    settings["has_recurring_expenses"] = body.has_recurring_expenses
    settings["onboarding_completed"] = True
    user.settings = settings
    await db.commit()
    from routes.analytics import track_event
    await track_event(db, user.id, "onboarding_completed", {"sector": body.sector})
    return {"status": "ok", "message": "Onboarding complete"}

@features_router.get("/onboarding/status")
async def get_onboarding_status(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserOnboarding).where(UserOnboarding.user_id == user.id))
    ob = result.scalar_one_or_none()
    if ob and ob.completed:
        return {"completed": True, "data": _row_to_dict(ob)}
    return {"completed": False}



# ── Onboarding alias matching frontend Onboarding.js shape ─────────
# Frontend calls POST /api/onboarding with: { first_name, why, sector, stage, objective_90d, spirituality }

class OnboardingSimple(BaseModel):
    """Accepte à la fois les clés FR du formulaire frontend (Onboarding.jsx)
    et les clés EN historiques. Avant ce correctif, seules les clés EN étaient
    reconnues → les vraies réponses de l'utilisateur (prénom, secteur, projet,
    objectif, type NET/TERRAIN) étaient silencieusement ignorées, ce qui laissait
    le Cockpit vide."""
    # Clés du formulaire frontend
    prenom: Optional[str] = None
    entreprise: Optional[str] = None
    statut: Optional[str] = None
    secteur: Optional[str] = None
    projet_description: Optional[str] = None
    objectif_90j: Optional[str] = None
    priorites: Optional[List[str]] = None
    ambiance: Optional[str] = None
    workspace_type: Optional[str] = None
    workspace_url: Optional[str] = None
    project_type: Optional[str] = None   # NET | TERRAIN
    # Clés EN historiques (compat)
    first_name: Optional[str] = None
    why: Optional[str] = None
    sector: Optional[str] = None
    stage: Optional[str] = None
    objective_90d: Optional[str] = None
    spirituality: Optional[str] = None

    class Config:
        extra = "ignore"


def _first_mission_for(project_type: str, objective: str = "") -> str:
    """1ère mission concrète déduite du type de projet + objectif d'onboarding."""
    pt = (project_type or "").upper()
    if pt == "TERRAIN":
        return "Définir clairement votre offre principale et son prix."
    if pt == "NET":
        return "Publier votre page de présentation en ligne."
    return "Définir votre prochaine étape prioritaire."


@onboarding_alias_router.post("/onboarding")
async def complete_onboarding_simple(
    body: OnboardingSimple,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Alias compatible avec le frontend Onboarding.jsx (shape FR complète)."""
    # Normalisation FR ↔ EN (le frontend envoie les clés FR)
    first_name = body.prenom or body.first_name
    stage = body.statut or body.stage
    sector = body.secteur or body.sector
    objective = body.objectif_90j or body.objective_90d
    project_type = (body.project_type or "").upper() or None
    priorites = body.priorites or []
    challenge = " · ".join(priorites) if priorites else None

    # Upsert UserOnboarding row
    result = await db.execute(select(UserOnboarding).where(UserOnboarding.user_id == user.id))
    ob = result.scalar_one_or_none()
    if ob:
        if stage: ob.status = stage
        if sector: ob.sector = sector
        if objective: ob.objective = objective
        if challenge: ob.challenge = challenge
        ob.completed = True
    else:
        ob = UserOnboarding(
            user_id=user.id,
            status=stage,
            sector=sector,
            objective=objective,
            challenge=challenge,
            completed=True,
        )
        db.add(ob)

    # Save all onboarding fields in user.settings (source de vérité du Cockpit)
    settings = dict(user.settings or {})
    if first_name:
        settings["first_name"] = first_name
        if not user.name or "@" in (user.name or ""):
            user.name = first_name
    if body.entreprise:          settings["entreprise"] = body.entreprise
    if sector:                   settings["sector"] = sector
    if stage:                    settings["stage"] = stage
    if body.projet_description:  settings["projet_description"] = body.projet_description
    if objective:
        settings["objectif_90j"] = objective
        settings["why"] = settings.get("why") or objective
    if priorites:                settings["priorites"] = priorites
    if body.ambiance:            settings["ambiance"] = body.ambiance
    if body.workspace_type:      settings["workspace_type"] = body.workspace_type
    if body.workspace_url:       settings["workspace_url"] = body.workspace_url
    if project_type:             settings["project_type"] = project_type
    if body.why:                 settings["why"] = body.why
    if body.spirituality:        settings["spirituality"] = body.spirituality
    first_mission = _first_mission_for(project_type, objective or "")
    settings["first_mission"] = first_mission
    settings["onboarding_completed"] = True

    # Email de bienvenue — envoyé UNE seule fois, à la fin de l'onboarding
    # (pas au 1er login) pour ne pas concurrencer l'attention de l'utilisateur
    # pendant qu'il complète le questionnaire. Le flag `welcome_email_sent`
    # côté settings (persisté en DB) évite tout renvoi lors d'un replay
    # d'onboarding ou d'un login sur un nouveau navigateur.
    _first_completion = not settings.get("welcome_email_sent")
    user.settings = settings

    await db.commit()

    if _first_completion and send_brevo_email and user.email:
        try:
            first_name = settings.get("first_name") or ""
            greeting = f"Bienvenue {first_name} 👋" if first_name else "Bienvenue 👋"
            html = f"""
              <h1 style="margin:0 0 12px;font-family:Manrope,sans-serif;color:#0B1F3A">{greeting}</h1>
              <p style="font-size:15px;line-height:1.55;color:#2b3648">
                Tu viens de finir ton onboarding sur <strong>myextension ai</strong>. Tout est prêt pour piloter ton activité :
              </p>
              <ul style="font-size:14px;line-height:1.7;color:#2b3648;padding-left:18px">
                <li><strong>Cockpit</strong> : tes 4 KPIs essentiels + les suggestions du Co-pilote.</li>
                <li><strong>Vision Board</strong> : ton objectif business + tes prochaines actions.</li>
                <li><strong>Bien-être</strong> : ton check-in matin, sans y penser 30 secondes/jour.</li>
              </ul>
              <p style="font-size:14px;line-height:1.5;color:#2b3648">
                Tu peux revenir à cet email et cliquer <a href="https://myextension-ai.com" style="color:#C9A449;font-weight:700">ici</a> pour revenir à ton cockpit.
              </p>
              <p style="font-size:12px;line-height:1.5;color:#6b7280;margin-top:24px">
                Une question ? Réponds à cet email — un humain te lira.
              </p>
            """
            # Best-effort : on ne casse jamais l'onboarding sur un échec Brevo.
            # L’email est utile mais ne doit jamais retarder l’accès au cockpit.
            # Brevo peut être indisponible, lent ou non configuré en préproduction.
            asyncio.get_running_loop().run_in_executor(
                None,
                lambda: send_brevo_email(
                    to_email=user.email,
                    to_name=first_name or (user.name or ""),
                    subject="Bienvenue sur myextension ai — ton cockpit est prêt",
                    html_content=html,
                    brand="myextension",
                ),
            )
            # Marque comme envoyé pour éviter tout ré-envoi
            settings["welcome_email_sent"] = datetime.now(timezone.utc).isoformat()
            user.settings = settings
            await db.commit()
        except Exception:
            # Silencieux : l'email n'est pas critique pour l'onboarding
            pass

    return {
        "status": "ok",
        "onboarding_done": True,
        "type": project_type or "NET",
        "first_mission": first_mission,
        "summary": f"{first_name or 'Votre'} cockpit est prêt — l'IA a préparé votre 1ère mission.",
    }


@onboarding_alias_router.post("/onboarding/reset")
async def reset_onboarding(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Preview/dev : remet l'utilisateur en état 'non onboardé' pour rejouer l'onboarding.
    Réinitialise les 3 sources de vérité : settings.onboarding_completed,
    UserOnboarding.completed, et la préférence KV user_prefs.onboarded."""
    settings = dict(user.settings or {})
    settings["onboarding_completed"] = False
    user.settings = settings

    result = await db.execute(select(UserOnboarding).where(UserOnboarding.user_id == user.id))
    ob = result.scalar_one_or_none()
    if ob:
        ob.completed = False

    try:
        from routes.growth import _get_kv, _save_kv
        prefs = (await _get_kv(db, user.id, "user_prefs")) or {}
        prefs["onboarded"] = False
        await _save_kv(db, user.id, "user_prefs", prefs)
    except Exception:
        pass

    await db.commit()
    return {"status": "ok", "onboarding_done": False}



@onboarding_alias_router.get("/onboarding")
async def get_onboarding_simple(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """GET compatible frontend (onboardingApi.get) — évite le 405 sur /api/onboarding."""
    result = await db.execute(select(UserOnboarding).where(UserOnboarding.user_id == user.id))
    ob = result.scalar_one_or_none()
    settings = dict(user.settings or {})
    first_name = settings.get("first_name") or (user.name if user.name and "@" not in (user.name or "") else "")
    data = _row_to_dict(ob) if ob else {}
    project_type = settings.get("project_type") or "NET"
    first_mission = settings.get("first_mission") or _first_mission_for(project_type, data.get("objective") or "")
    return {
        "completed": bool(ob and ob.completed),
        "onboarding_done": bool(settings.get("onboarding_completed")),
        "first_name": first_name,
        "profil": {"prenom": first_name, "sector": data.get("sector"), "stage": data.get("status")},
        "first_mission": first_mission,
        "project_type": project_type,
        "form": {
            "prenom": first_name,
            "entreprise": settings.get("entreprise"),
            "secteur": settings.get("sector") or data.get("sector"),
            "statut": settings.get("stage") or data.get("status"),
            "projet_description": settings.get("projet_description"),
            "objectif_90j": settings.get("objectif_90j") or data.get("objective"),
            "priorites": settings.get("priorites") or [],
            "workspace_type": settings.get("workspace_type"),
            "project_type": project_type,
        },
        "data": data,
    }


@onboarding_alias_router.get("/messages")
async def list_messages(user=Depends(get_current_user)):
    """Messagerie interne : pas encore de messages. Renvoie une liste vide (évite le 404)."""
    return {"items": []}
