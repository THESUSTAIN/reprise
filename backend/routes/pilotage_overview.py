"""Pilotage — vue d'ensemble financière RÉELLE pour le frontend Pilotage.jsx.
Agrège les FinanceEntryDB de l'utilisateur (aucune valeur fictive : 0/vide si pas
de données). Données financières sensibles : toujours scopées sur le JWT
(get_current_user) — jamais sur un user_id fourni par le client, invité ou non,
pour éviter qu'une requête sans authentification valide (ou avec un ?user_id=
falsifié) puisse lire la trésorerie d'un autre compte (IDOR)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, FinanceEntryDB, BudgetGoalDB
from deps import get_current_user

router = APIRouter(prefix="/pilotage", tags=["pilotage-overview"])


def _tz(dt):
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class PilotageEntryIn(BaseModel):
    type: str            # "revenu" | "depense"
    label: str
    amount: float
    category: str = "Général"
    date: Optional[str] = None


@router.get("/overview")
async def pilotage_overview(period: str = "mois",
                            auth_user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    uid = auth_user.id
    now = datetime.now(timezone.utc)
    days = {"semaine": 7, "trimestre": 90, "annee": 365}.get(period, 31)
    start = now - timedelta(days=days)

    all_entries = list((await db.execute(
        select(FinanceEntryDB).where(FinanceEntryDB.user_id == uid)
    )).scalars().all())
    period_entries = [e for e in all_entries if e.date and _tz(e.date) >= start]

    revenus = round(sum(e.amount for e in period_entries if e.type == "revenu"), 2)
    depenses = round(sum(e.amount for e in period_entries if e.type == "depense"), 2)
    net = round(revenus - depenses, 2)
    marge = round((net / revenus * 100) if revenus > 0 else 0, 1)

    # Objectif CA + trésorerie déclarés (BudgetGoalDB), sinon 0 → "à définir"
    async def _goal(cat):
        g = (await db.execute(select(BudgetGoalDB).where(
            BudgetGoalDB.user_id == uid, BudgetGoalDB.category == cat))).scalar_one_or_none()
        return g.amount if g else 0
    ca_objective = await _goal("objectif_confort")
    tresorerie = await _goal("tresorerie")
    salary_target = ca_objective  # même repère tant qu'aucun objectif salaire dédié

    # Trend mensuel réel (6 derniers mois) → deltas honnêtes (0 si pas d'historique)
    monthly = []
    for m in range(5, -1, -1):
        ms = (now - timedelta(days=30 * m)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        me = (ms + timedelta(days=32)).replace(day=1)
        me_entries = [e for e in all_entries if e.date and ms <= _tz(e.date) < me]
        monthly.append({
            "month": ms.strftime("%b"),
            "ca": round(sum(e.amount for e in me_entries if e.type == "revenu"), 2),
            "dep": round(sum(e.amount for e in me_entries if e.type == "depense"), 2),
        })

    def _delta(cur, prev):
        if prev and prev > 0:
            return round((cur - prev) / prev * 100)
        return 0
    ca_cur, ca_prev = monthly[-1]["ca"], monthly[-2]["ca"] if len(monthly) >= 2 else 0
    dep_cur, dep_prev = monthly[-1]["dep"], monthly[-2]["dep"] if len(monthly) >= 2 else 0

    kpis = [
        {"id": "ca", "label": "Chiffre d'affaires", "value": revenus, "delta": _delta(ca_cur, ca_prev), "tone": "gold"},
        {"id": "depenses", "label": "Dépenses", "value": depenses, "delta": _delta(dep_cur, dep_prev), "tone": "danger"},
        {"id": "net", "label": "Résultat net", "value": net, "delta": _delta(net, round(ca_prev - dep_prev, 2)), "tone": "sage"},
        {"id": "treso", "label": "Trésorerie déclarée", "value": tresorerie, "delta": 0, "tone": "navy"},
    ]

    # Sources : reflètent l'usage réel (aucune source "connectée" fictive)
    imported = any((e.category or "") == "import" for e in all_entries)
    last_sync = None
    if all_entries:
        last = max(all_entries, key=lambda e: _tz(e.date) if e.date else datetime.min.replace(tzinfo=timezone.utc))
        last_sync = _tz(last.date).strftime("%d/%m") if last.date else None
    sources = [
        {"id": "manuel", "name": "Saisie manuelle", "color": "#4a6a9e", "letter": "M",
         "connected": len(all_entries) > 0, "last_sync": last_sync},
        {"id": "csv", "name": "Import relevé", "color": "#5e8a5a", "letter": "C",
         "connected": imported, "last_sync": last_sync if imported else None},
    ]

    # Coach / verdict / alertes : dérivés HONNÊTEMENT des chiffres (pas de blabla inventé)
    if not all_entries:
        coach_msg = "Ajoute ta première entrée (revenu ou dépense) pour activer ton pilotage financier."
        verdict = {"level": "À démarrer", "message": "Pas encore de données financières."}
    elif net >= 0:
        coach_msg = f"Résultat net positif de {round(net)} € sur la période. Continue à suivre tes dépenses."
        verdict = {"level": "Sain", "message": f"Marge nette de {marge} %."}
    else:
        coach_msg = f"Tes dépenses dépassent tes revenus de {abs(round(net))} € sur la période. Priorise tes rentrées."
        verdict = {"level": "Vigilance", "message": "Résultat net négatif sur la période."}

    alerts = []
    if not all_entries:
        alerts.append({"tone": "warn", "text": "Aucune donnée financière pour l'instant."})
    else:
        if net < 0:
            alerts.append({"tone": "danger", "text": "Résultat net négatif sur la période."})
        if tresorerie == 0:
            alerts.append({"tone": "warn", "text": "Trésorerie non déclarée — renseigne-la pour un suivi précis."})
        if ca_objective == 0:
            alerts.append({"tone": "warn", "text": "Objectif de CA non défini."})
        if not alerts:
            alerts.append({"tone": "ok", "text": "Aucune alerte : situation sous contrôle."})

    recent = sorted(period_entries,
                    key=lambda e: _tz(e.date) if e.date else datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True)[:15]
    entries = [{
        "id": e.id, "type": e.type, "label": e.label, "amount": e.amount,
        "category": e.category or "Général",
        "date": _tz(e.date).strftime("%d/%m/%Y") if e.date else "",
    } for e in recent]

    recurring_dep = round(sum(e.amount for e in all_entries if e.type == "depense" and e.recurring), 2)

    return {
        "period": period,
        "ca_month": revenus,
        "ca_objective": ca_objective,
        "salary_possible": max(0, net),
        "salary_target": salary_target,
        "summary": {"score": None, "revenus": revenus, "marge": marge, "tresorerie": tresorerie},
        "sources": sources,
        "kpis": kpis,
        "coach": {"message": coach_msg},
        "verdict": verdict,
        "alerts": alerts,
        "monthly": [{"month": m["month"], "ca": m["ca"]} for m in monthly],
        "entries": entries,
        "pending_invoices": 0,
        "charges_next_date": "—",
        "charges_due": recurring_dep,
    }


@router.post("/entry")
async def pilotage_add_entry(body: PilotageEntryIn, user: User = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    if body.type not in ("revenu", "depense"):
        raise HTTPException(status_code=400, detail="Type invalide")
    if body.amount is None or body.amount < 0:
        raise HTTPException(status_code=400, detail="Montant invalide")
    entry_date = datetime.now(timezone.utc)
    if body.date:
        try:
            entry_date = datetime.fromisoformat(body.date)
            if entry_date.tzinfo is None:
                entry_date = entry_date.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    entry = FinanceEntryDB(user_id=user.id, type=body.type, label=body.label,
                           amount=body.amount, category=body.category or "Général",
                           date=entry_date, recurring=False)
    db.add(entry)
    await db.commit()
    return {"status": "ok"}
