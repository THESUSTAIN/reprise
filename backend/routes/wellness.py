"""
Routes Wellness / Bien-etre — Check-in quotidien, score, tendances, micro-actions IA.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, WellnessCheckin, Project, UserFocusSession
from deps import get_current_user

wellness_router = APIRouter(prefix="/wellness", tags=["Wellness"])


class CheckinSchema(BaseModel):
    energy: int = Field(ge=1, le=5)
    mood: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    sleep: int = Field(ge=1, le=5)
    notes: Optional[str] = None


def compute_score(energy: int, mood: int, stress: int, sleep: int) -> int:
    """Score bien-etre 0-100. Stress est inverse (1=bien, 5=mal)."""
    raw = (energy + mood + (6 - stress) + sleep) / 4  # 1-5 scale
    return round((raw - 1) / 4 * 100)


def get_micro_actions(energy: int, mood: int, stress: int, sleep: int, trend_days: int = 0) -> list:
    """Retourne 2-3 micro-actions personnalisees basees sur l'etat actuel."""
    actions = []

    if stress >= 4:
        actions.append({
            "type": "breathing",
            "title": "Respiration 4-7-8",
            "desc": "Inspirez 4s, retenez 7s, expirez 8s. Repetez 3 fois pour calmer le systeme nerveux.",
            "duration": "2 min",
            "icon": "wind",
        })

    if energy <= 2:
        actions.append({
            "type": "movement",
            "title": "Micro-pause active",
            "desc": "Levez-vous, etirez-vous 30s, faites 10 squats. L'oxygene relance l'energie.",
            "duration": "3 min",
            "icon": "activity",
        })

    if sleep <= 2:
        actions.append({
            "type": "tip",
            "title": "Ameliorer votre sommeil ce soir",
            "desc": "Pas d'ecran 1h avant. Temperature fraiche (18-19 C). Relaxation progressive.",
            "duration": "conseil",
            "icon": "moon",
        })

    if mood <= 2:
        actions.append({
            "type": "gratitude",
            "title": "Exercice de gratitude express",
            "desc": "Notez 3 choses positives d'aujourd'hui, meme petites. Recadrage cognitif prouve.",
            "duration": "2 min",
            "icon": "heart",
        })

    if stress >= 3 and energy <= 3:
        actions.append({
            "type": "boundary",
            "title": "Priorisez seulement 2 taches",
            "desc": "Quand l'energie est basse et le stress haut, reduisez votre liste. Qualite > Quantite.",
            "duration": "conseil",
            "icon": "target",
        })

    if mood >= 4 and energy >= 4:
        actions.append({
            "type": "leverage",
            "title": "Capitalisez sur votre energie",
            "desc": "Vous etes en forme ! Attaquez la tache la plus importante maintenant.",
            "duration": "conseil",
            "icon": "zap",
        })

    if trend_days >= 3 and stress >= 3:
        actions.insert(0, {
            "type": "alert",
            "title": "Attention : stress prolonge detecte",
            "desc": f"Votre stress est eleve depuis {trend_days} jours. Prenez une vraie pause ou deleguer une tache.",
            "duration": "important",
            "icon": "alert-triangle",
        })

    return actions[:3]


def detect_burnout_risk(checkins: list) -> dict:
    """Analyse les 14 derniers check-ins pour detecter ET predire le risque de burnout."""
    if len(checkins) < 3:
        return {"risk": "insufficient_data", "level": 0, "message": "Continuez vos check-ins pour obtenir une analyse",
                "prediction": None}

    recent = checkins[:14]  # 14 derniers jours
    avg_energy = sum(c.energy for c in recent) / len(recent)
    avg_stress = sum(c.stress for c in recent) / len(recent)
    avg_mood = sum(c.mood for c in recent) / len(recent)
    avg_sleep = sum(c.sleep for c in recent) / len(recent)

    # Trend analysis: compare first half vs second half
    half = max(1, len(recent) // 2)
    first_half = recent[half:]   # older
    second_half = recent[:half]  # more recent

    def avg(lst, attr): return sum(getattr(c, attr) for c in lst) / max(1, len(lst))

    energy_trend = avg(second_half, 'energy') - avg(first_half, 'energy')  # negative = declining
    stress_trend = avg(second_half, 'stress') - avg(first_half, 'stress')  # positive = increasing stress
    mood_trend = avg(second_half, 'mood') - avg(first_half, 'mood')
    sleep_trend = avg(second_half, 'sleep') - avg(first_half, 'sleep')

    # Scoring: current state
    score = 0
    if avg_energy <= 2: score += 25
    elif avg_energy <= 3: score += 12
    if avg_stress >= 4: score += 25
    elif avg_stress >= 3: score += 12
    if avg_mood <= 2: score += 15
    if avg_sleep <= 2: score += 15

    # Scoring: trends (weighted higher for prediction)
    if energy_trend < -0.5: score += 20
    elif energy_trend < -0.2: score += 10
    if stress_trend > 0.5: score += 20
    elif stress_trend > 0.2: score += 10
    if mood_trend < -0.3: score += 10
    if sleep_trend < -0.3: score += 10

    # Prediction: estimate days until burnout threshold
    prediction = None
    if len(recent) >= 5:
        # Project energy trend forward
        daily_energy_drop = energy_trend / max(1, half)
        daily_stress_rise = stress_trend / max(1, half)
        projected_energy = avg(second_half, 'energy')
        projected_stress = avg(second_half, 'stress')

        days_to_burnout = None
        for day in range(1, 30):
            pe = projected_energy + (daily_energy_drop * day)
            ps = projected_stress + (daily_stress_rise * day)
            if pe <= 1.5 or ps >= 4.5:
                days_to_burnout = day
                break

        if days_to_burnout:
            prediction = {
                "days_until_risk": days_to_burnout,
                "projected_date": (datetime.now(timezone.utc) + timedelta(days=days_to_burnout)).strftime("%Y-%m-%d"),
                "confidence": "high" if len(recent) >= 10 else "moderate",
                "message": f"A ce rythme, risque de burnout estime dans {days_to_burnout} jours."
            }
        elif score >= 50:
            prediction = {
                "days_until_risk": 0,
                "projected_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "confidence": "high",
                "message": "Signes de burnout deja presents. Action immediate recommandee."
            }

    # Trend summary for display
    trends = {
        "energy": "declining" if energy_trend < -0.2 else "stable" if abs(energy_trend) <= 0.2 else "improving",
        "stress": "increasing" if stress_trend > 0.2 else "stable" if abs(stress_trend) <= 0.2 else "decreasing",
        "mood": "declining" if mood_trend < -0.2 else "stable" if abs(mood_trend) <= 0.2 else "improving",
        "sleep": "declining" if sleep_trend < -0.2 else "stable" if abs(sleep_trend) <= 0.2 else "improving",
    }

    if score >= 60:
        return {"risk": "high", "level": score, "message": "Risque eleve de burnout. Pensez a consulter ou prendre du recul.",
                "prediction": prediction, "trends": trends}
    elif score >= 35:
        return {"risk": "moderate", "level": score, "message": "Signes de fatigue accumules. Prevoyez une pause regeneratrice.",
                "prediction": prediction, "trends": trends}
    else:
        return {"risk": "low", "level": score, "message": "Votre equilibre semble bon. Continuez vos bonnes habitudes !",
                "prediction": prediction, "trends": trends}


@wellness_router.post("/checkin")
async def create_checkin(body: CheckinSchema, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Creer un check-in quotidien."""
    score = compute_score(body.energy, body.mood, body.stress, body.sleep)

    # Get recent checkins for trend analysis
    result = await db.execute(
        select(WellnessCheckin)
        .where(WellnessCheckin.user_id == user.id)
        .order_by(WellnessCheckin.date.desc())
        .limit(7)
    )
    recent = list(result.scalars().all())

    # Count consecutive high-stress days
    stress_streak = 0
    for c in recent:
        if c.stress >= 3:
            stress_streak += 1
        else:
            break

    actions = get_micro_actions(body.energy, body.mood, body.stress, body.sleep, stress_streak)
    burnout = detect_burnout_risk(recent)

    # AI insight based on current state
    insights = []
    if body.energy <= 2 and body.stress >= 4:
        insights.append("Votre energie est basse et votre stress eleve. C'est un signal d'alerte important.")
    if body.sleep <= 2:
        insights.append("Un sommeil insuffisant impacte tout le reste. C'est votre levier numero 1.")
    if body.mood >= 4 and body.energy >= 4:
        insights.append("Excellent etat aujourd'hui ! Profitez-en pour avancer sur vos projets strategiques.")
    if score < 40:
        insights.append("Score bas aujourd'hui. Soyez indulgent avec vous-meme et reduisez vos objectifs.")

    ai_insight = " ".join(insights) if insights else "Journee equilibree. Maintenez vos routines !"

    checkin = WellnessCheckin(
        user_id=user.id, energy=body.energy, mood=body.mood,
        stress=body.stress, sleep=body.sleep, notes=body.notes,
        score=score, ai_insight=ai_insight,
    )
    db.add(checkin)
    await db.commit()
    await db.refresh(checkin)

    return {
        "id": checkin.id,
        "score": score,
        "ai_insight": ai_insight,
        "micro_actions": actions,
        "burnout_risk": burnout,
        "date": checkin.date.isoformat() if checkin.date else None,
    }


@wellness_router.get("/today")
async def get_today_checkin(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Recuperer le check-in du jour s'il existe."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(WellnessCheckin)
        .where(WellnessCheckin.user_id == user.id, WellnessCheckin.date >= today_start)
        .order_by(WellnessCheckin.date.desc())
        .limit(1)
    )
    checkin = result.scalar_one_or_none()
    if not checkin:
        return {"has_checkin": False}

    return {
        "has_checkin": True,
        "id": checkin.id,
        "energy": checkin.energy, "mood": checkin.mood,
        "stress": checkin.stress, "sleep": checkin.sleep,
        "notes": checkin.notes, "score": checkin.score,
        "ai_insight": checkin.ai_insight,
        "date": checkin.date.isoformat() if checkin.date else None,
    }


@wellness_router.get("/history")
async def get_wellness_history(days: int = 30, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Historique des check-ins."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(WellnessCheckin)
        .where(WellnessCheckin.user_id == user.id, WellnessCheckin.date >= since)
        .order_by(WellnessCheckin.date.desc())
    )
    checkins = result.scalars().all()

    data = []
    for c in checkins:
        d = c.date if c.date else c.created_at
        data.append({
            "id": c.id, "energy": c.energy, "mood": c.mood,
            "stress": c.stress, "sleep": c.sleep, "score": c.score,
            "notes": c.notes, "ai_insight": c.ai_insight,
            "date": d.isoformat() if d else None,
        })

    # Compute averages
    if checkins:
        avg_score = round(sum(c.score or 0 for c in checkins) / len(checkins))
        avg_energy = round(sum(c.energy for c in checkins) / len(checkins), 1)
        avg_stress = round(sum(c.stress for c in checkins) / len(checkins), 1)
    else:
        avg_score = avg_energy = avg_stress = 0

    burnout = detect_burnout_risk(list(checkins))

    return {
        "checkins": data,
        "stats": {
            "total_checkins": len(checkins),
            "avg_score": avg_score,
            "avg_energy": avg_energy,
            "avg_stress": avg_stress,
        },
        "burnout_risk": burnout,
    }


@wellness_router.get("/weekly-report")
async def get_weekly_report(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Bilan bien-etre de la semaine."""
    week_start = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(WellnessCheckin)
        .where(WellnessCheckin.user_id == user.id, WellnessCheckin.date >= week_start)
        .order_by(WellnessCheckin.date.asc())
    )
    checkins = list(result.scalars().all())

    if not checkins:
        return {"has_data": False, "message": "Aucun check-in cette semaine. Commencez demain matin !"}

    scores = [c.score or 0 for c in checkins]
    energies = [c.energy for c in checkins]
    stresses = [c.stress for c in checkins]

    # Trends
    energy_trend = "stable"
    if len(energies) >= 3:
        first_half = sum(energies[:len(energies)//2]) / max(1, len(energies)//2)
        second_half = sum(energies[len(energies)//2:]) / max(1, len(energies) - len(energies)//2)
        if second_half > first_half + 0.5: energy_trend = "hausse"
        elif second_half < first_half - 0.5: energy_trend = "baisse"

    stress_trend = "stable"
    if len(stresses) >= 3:
        first_half = sum(stresses[:len(stresses)//2]) / max(1, len(stresses)//2)
        second_half = sum(stresses[len(stresses)//2:]) / max(1, len(stresses) - len(stresses)//2)
        if second_half > first_half + 0.5: stress_trend = "hausse"
        elif second_half < first_half - 0.5: stress_trend = "baisse"

    best_day = max(checkins, key=lambda c: c.score or 0)
    worst_day = min(checkins, key=lambda c: c.score or 0)

    advice = []
    avg_stress = sum(stresses) / len(stresses)
    avg_energy = sum(energies) / len(energies)
    if avg_stress >= 3.5:
        advice.append("Votre stress moyen est eleve cette semaine. Planifiez des pauses regulieres.")
    if avg_energy <= 2.5:
        advice.append("Energie basse en moyenne. Verifiez votre sommeil et votre alimentation.")
    if energy_trend == "baisse":
        advice.append("Votre energie est en baisse. Allegez votre planning la semaine prochaine.")
    if stress_trend == "hausse":
        advice.append("Le stress augmente. Identifiez la source et agissez avant que ca s'accumule.")
    if avg_energy >= 3.5 and avg_stress <= 2.5:
        advice.append("Excellente semaine ! Vous etes dans un bon equilibre. Maintenez ces habitudes.")

    return {
        "has_data": True,
        "nb_checkins": len(checkins),
        "avg_score": round(sum(scores) / len(scores)),
        "avg_energy": round(avg_energy, 1),
        "avg_stress": round(avg_stress, 1),
        "energy_trend": energy_trend,
        "stress_trend": stress_trend,
        "best_day": {"date": best_day.date.isoformat() if best_day.date else None, "score": best_day.score},
        "worst_day": {"date": worst_day.date.isoformat() if worst_day.date else None, "score": worst_day.score},
        "daily_scores": [{"date": c.date.strftime("%a") if c.date else "?", "score": c.score or 0, "energy": c.energy, "stress": c.stress} for c in checkins],
        "advice": advice,
        "burnout_risk": detect_burnout_risk(checkins),
    }


@wellness_router.get("/activity")
async def get_activity_correlation(days: int = 30, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Correlation productivite <-> bien-etre : heures travaillees vs score."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # 1. Wellness check-ins by date
    checkin_result = await db.execute(
        select(WellnessCheckin)
        .where(WellnessCheckin.user_id == user.id, WellnessCheckin.date >= since)
        .order_by(WellnessCheckin.date.asc())
    )
    checkins = list(checkin_result.scalars().all())
    wellness_by_date = {}
    for c in checkins:
        d = (c.date or c.created_at).strftime("%Y-%m-%d")
        wellness_by_date[d] = {"score": c.score or 0, "energy": c.energy, "stress": c.stress, "mood": c.mood, "sleep": c.sleep}

    # 2. Focus sessions by date (from UserFocusSession)
    focus_result = await db.execute(
        select(UserFocusSession)
        .where(UserFocusSession.user_id == user.id, UserFocusSession.created_at >= since)
        .order_by(UserFocusSession.created_at.asc())
    )
    sessions = list(focus_result.scalars().all())
    work_by_date = {}
    for s in sessions:
        d = s.created_at.strftime("%Y-%m-%d")
        if d not in work_by_date:
            work_by_date[d] = {"minutes": 0, "sessions": 0}
        work_by_date[d]["minutes"] += (s.duration or 0)
        work_by_date[d]["sessions"] += 1

    # 3. Project total time (aggregate)
    proj_result = await db.execute(
        select(Project).where(Project.user_id == user.id)
    )
    projects = list(proj_result.scalars().all())
    total_project_hours = sum((p.total_time_seconds or 0) for p in projects) / 3600

    # 4. Build daily timeline
    all_dates = sorted(set(list(wellness_by_date.keys()) + list(work_by_date.keys())))
    daily = []
    for d in all_dates:
        w = wellness_by_date.get(d, {})
        wk = work_by_date.get(d, {"minutes": 0, "sessions": 0})
        daily.append({
            "date": d,
            "score": w.get("score", None),
            "energy": w.get("energy", None),
            "stress": w.get("stress", None),
            "work_minutes": wk["minutes"],
            "work_sessions": wk["sessions"],
        })

    # 5. Correlation analysis
    alerts = []
    if len(daily) >= 3:
        # Check last 7 days for negative correlation
        recent = daily[-7:]
        days_overwork = [d for d in recent if d["work_minutes"] > 480]  # > 8h
        days_low_energy = [d for d in recent if d["score"] is not None and d["score"] < 40]
        if len(days_overwork) >= 3:
            alerts.append({"type": "overwork", "message": f"Vous avez travaille plus de 8h sur {len(days_overwork)} jours cette semaine. Risque de fatigue."})
        if len(days_low_energy) >= 2 and len(days_overwork) >= 2:
            alerts.append({"type": "burnout_risk", "message": "Votre bien-etre baisse alors que vos heures augmentent. Pensez a lever le pied."})

        # Check trend: if work increases and score decreases
        work_trend = [d["work_minutes"] for d in recent if d["work_minutes"] > 0]
        score_trend = [d["score"] for d in recent if d["score"] is not None]
        if len(work_trend) >= 3 and len(score_trend) >= 3:
            work_increasing = work_trend[-1] > work_trend[0] * 1.2
            score_decreasing = score_trend[-1] < score_trend[0] * 0.8
            if work_increasing and score_decreasing:
                alerts.append({"type": "inverse_trend", "message": "Attention : vos heures de travail augmentent mais votre score bien-etre diminue."})

    # 6. Summary stats
    total_work_minutes = sum(d["work_minutes"] for d in daily)
    avg_work_per_day = round(total_work_minutes / max(1, len([d for d in daily if d["work_minutes"] > 0])))
    avg_score = round(sum(d["score"] for d in daily if d["score"] is not None) / max(1, len([d for d in daily if d["score"] is not None]))) if any(d["score"] is not None for d in daily) else None

    return {
        "daily": daily,
        "summary": {
            "total_work_hours": round(total_work_minutes / 60, 1),
            "total_project_hours": round(total_project_hours, 1),
            "avg_work_minutes_per_day": avg_work_per_day,
            "avg_wellness_score": avg_score,
            "total_sessions": sum(d["work_sessions"] for d in daily),
            "total_checkins": len(checkins),
        },
        "alerts": alerts,
        "projects": [{"name": p.name, "hours": round((p.total_time_seconds or 0) / 3600, 1), "color": p.color or "#1E3A8A"} for p in projects],
    }
