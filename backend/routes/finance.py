"""
Routes pour le Pilotage Financier — suivi CA, depenses, previsions, transactions.
Donnees persistantes en base de donnees (SQLAlchemy).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, FinanceEntryDB, BudgetGoalDB
from deps import get_current_user

finance_router = APIRouter(prefix="/finance", tags=["Finance"])


class FinanceEntrySchema(BaseModel):
    type: str  # "revenu" | "depense"
    label: str
    amount: float
    category: str = "autre"
    date: Optional[str] = None
    recurring: bool = False


class BudgetGoalSchema(BaseModel):
    category: str
    amount: float
    period: str = "mois"


@finance_router.get("/overview")
async def get_finance_overview(period: str = "mois", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    uid = user.id
    # #79 — Filter entries in SQL with WHERE date >= start
    now = datetime.now(timezone.utc)
    if period == "semaine":
        start = now - timedelta(days=7)
    elif period == "trimestre":
        start = now - timedelta(days=90)
    elif period == "annee":
        start = now - timedelta(days=365)
    else:
        start = now - timedelta(days=31)  # #30 — Use 31 days to cover all months

    result = await db.execute(
        select(FinanceEntryDB).where(FinanceEntryDB.user_id == uid, FinanceEntryDB.date >= start)
    )
    filtered = list(result.scalars().all())
    # Also fetch all for recurring calculations
    all_result = await db.execute(select(FinanceEntryDB).where(FinanceEntryDB.user_id == uid))
    all_entries = all_result.scalars().all()
    budget_result = await db.execute(select(BudgetGoalDB).where(BudgetGoalDB.user_id == uid))
    budgets = [{"category": b.category, "amount": b.amount, "period": b.period} for b in budget_result.scalars().all()]

    def _ensure_tz(dt):
        # #64 — Consistently treat naive datetimes as UTC
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    # filtered already comes from SQL WHERE clause
    revenus = sum(e.amount for e in filtered if e.type == "revenu")
    depenses = sum(e.amount for e in filtered if e.type == "depense")
    net = revenus - depenses

    cat_rev = {}
    cat_dep = {}
    for e in filtered:
        bucket = cat_rev if e.type == "revenu" else cat_dep
        bucket[e.category] = bucket.get(e.category, 0) + e.amount

    # Weekly breakdown
    week_data = []
    day_labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    for i in range(7):
        day = now - timedelta(days=6 - i)
        day_entries = [e for e in all_entries if e.date and _ensure_tz(e.date).date() == day.date()]
        day_rev = sum(e.amount for e in day_entries if e.type == "revenu")
        day_dep = sum(e.amount for e in day_entries if e.type == "depense")
        week_data.append({
            "day": day_labels[day.weekday()],
            "date": day.strftime("%d/%m"),
            "revenus": round(day_rev, 2),
            "depenses": round(day_dep, 2),
        })

    # Monthly trend (last 6 months)
    monthly = []
    for m in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * m)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        month_entries = [e for e in all_entries if e.date and month_start <= _ensure_tz(e.date) < month_end]
        monthly.append({
            "month": month_start.strftime("%b"),
            "revenus": round(sum(e.amount for e in month_entries if e.type == "revenu"), 2),
            "depenses": round(sum(e.amount for e in month_entries if e.type == "depense"), 2),
        })

    recurring_dep = sum(e.amount for e in all_entries if e.type == "depense" and e.recurring)

    recent = sorted(filtered, key=lambda e: _ensure_tz(e.date) if e.date else datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:15]
    recent_entries = [{
        "id": e.id, "type": e.type, "label": e.label, "amount": e.amount,
        "category": e.category, "date": e.date.isoformat() if e.date else None,
        "recurring": e.recurring, "created_at": e.created_at.isoformat() if e.created_at else None,
    } for e in recent]

    return {
        "period": period,
        "revenus": round(revenus, 2),
        "depenses": round(depenses, 2),
        "net": round(net, 2),
        "seuil_equilibre": round(recurring_dep, 2),
        "taux_marge": round((net / revenus * 100) if revenus > 0 else 0, 1),
        "nb_transactions": len(filtered),
        "categories_revenus": cat_rev,
        "categories_depenses": cat_dep,
        "weekly": week_data,
        "monthly": monthly,
        "budgets": budgets,
        "recent_entries": recent_entries,
    }


@finance_router.post("/entry")
async def create_finance_entry(body: FinanceEntrySchema, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # #129 — Reject negative amounts
    if body.amount < 0:
        raise HTTPException(status_code=400, detail="Le montant ne peut pas etre negatif")
    # #148 — Validate entry type
    if body.type not in ("revenu", "depense"):
        raise HTTPException(status_code=400, detail="Le type doit etre 'revenu' ou 'depense'")
    entry_date = datetime.fromisoformat(body.date) if body.date else datetime.now(timezone.utc)
    if entry_date.tzinfo is None:
        entry_date = entry_date.replace(tzinfo=timezone.utc)
    entry = FinanceEntryDB(
        user_id=user.id, type=body.type, label=body.label, amount=body.amount,
        category=body.category, date=entry_date, recurring=body.recurring,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"status": "ok", "entry": {
        "id": entry.id, "type": entry.type, "label": entry.label, "amount": entry.amount,
        "category": entry.category, "date": entry.date.isoformat(), "recurring": entry.recurring,
    }}


@finance_router.delete("/entry/{entry_id}")
async def delete_finance_entry(entry_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FinanceEntryDB).where(FinanceEntryDB.id == entry_id, FinanceEntryDB.user_id == user.id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    await db.execute(delete(FinanceEntryDB).where(FinanceEntryDB.id == entry_id))
    await db.commit()
    return {"status": "ok"}


@finance_router.post("/budget")
async def set_budget(body: BudgetGoalSchema, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BudgetGoalDB).where(BudgetGoalDB.user_id == user.id, BudgetGoalDB.category == body.category))
    existing = result.scalar_one_or_none()
    if existing:
        await db.execute(update(BudgetGoalDB).where(BudgetGoalDB.id == existing.id).values(amount=body.amount, period=body.period))
    else:
        db.add(BudgetGoalDB(user_id=user.id, category=body.category, amount=body.amount, period=body.period))
    await db.commit()
    bres = await db.execute(select(BudgetGoalDB).where(BudgetGoalDB.user_id == user.id))
    budgets = [{"category": b.category, "amount": b.amount, "period": b.period} for b in bres.scalars().all()]
    return {"status": "ok", "budgets": budgets}


@finance_router.get("/forecast")
async def get_forecast(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Previsions financieres basees sur les donnees existantes."""
    uid = user.id
    now = datetime.now(timezone.utc)
    three_months_ago = now - timedelta(days=90)
    # #80 — Filter in SQL instead of Python
    result = await db.execute(
        select(FinanceEntryDB).where(FinanceEntryDB.user_id == uid, FinanceEntryDB.date >= three_months_ago)
    )
    last_3m = result.scalars().all()

    # #36 — Count actual distinct months with data instead of fixed /3
    months_with_data = set()
    for e in last_3m:
        if e.date:
            months_with_data.add((e.date.year, e.date.month))
    actual_months = max(1, len(months_with_data))

    monthly_rev = sum(e.amount for e in last_3m if e.type == "revenu") / actual_months
    monthly_dep = sum(e.amount for e in last_3m if e.type == "depense") / actual_months

    forecast = []
    for i in range(1, 4):
        forecast.append({
            "month": (now + timedelta(days=30 * i)).strftime("%b %Y"),
            "revenus_prevu": round(monthly_rev * (1 + 0.05 * i), 2),
            "depenses_prevu": round(monthly_dep * (1 + 0.02 * i), 2),
            "net_prevu": round(monthly_rev * (1 + 0.05 * i) - monthly_dep * (1 + 0.02 * i), 2),
        })

    return {
        "avg_monthly_revenue": round(monthly_rev, 2),
        "avg_monthly_expense": round(monthly_dep, 2),
        "forecast": forecast,
        "health": "bon" if monthly_rev > monthly_dep * 1.3 else "attention" if monthly_rev > monthly_dep else "critique",
    }


# ═══════════════════════════════════════════════════════════
# SCORE DE SERENITE FINANCIERE
# ═══════════════════════════════════════════════════════════

@finance_router.get("/serenity")
async def get_serenity_score(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Calcul du score de serenite financiere (0-100) base sur 4 piliers."""
    uid = user.id
    result = await db.execute(select(FinanceEntryDB).where(FinanceEntryDB.user_id == uid))
    entries = result.scalars().all()

    now = datetime.now(timezone.utc)
    def _tz(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    # -- Monthly data for last 3 months --
    monthly_data = []
    for m in range(3):
        start = now - timedelta(days=30 * (m + 1))
        end = now - timedelta(days=30 * m)
        month_entries = [e for e in entries if e.date and start <= _tz(e.date) < end]
        rev = sum(e.amount for e in month_entries if e.type == "revenu")
        dep = sum(e.amount for e in month_entries if e.type == "depense")
        monthly_data.append({"revenus": rev, "depenses": dep, "net": rev - dep})

    current = monthly_data[0] if monthly_data else {"revenus": 0, "depenses": 0, "net": 0}
    revenus_list = [m["revenus"] for m in monthly_data]

    # 1. RESULTAT NET (25 pts) — marge nette
    if current["revenus"] > 0:
        marge = current["net"] / current["revenus"]
        if marge >= 0.30:
            score_net = 25
        elif marge >= 0.10:
            score_net = 15
        elif marge >= 0:
            score_net = 5
        else:
            score_net = 0
    else:
        score_net = 0

    # 2. REGULARITE (25 pts) — variation des revenus sur 3 mois
    if len(revenus_list) >= 2 and max(revenus_list) > 0:
        avg_rev = sum(revenus_list) / len(revenus_list)
        if avg_rev > 0:
            variation = max(abs(r - avg_rev) for r in revenus_list) / avg_rev
        else:
            variation = 1.0
        if variation < 0.20:
            score_reg = 25
        elif variation < 0.40:
            score_reg = 15
        else:
            score_reg = 5
    else:
        score_reg = 10  # Not enough data

    # 3. COUVERTURE CHARGES (25 pts) — reserves vs charges mensuelles
    recurring_dep = sum(e.amount for e in entries if e.type == "depense" and e.recurring)
    monthly_charges = recurring_dep if recurring_dep > 0 else (current["depenses"] or 1)
    # Read user's declared treasury from budget goals (category="tresorerie")
    tres_result = await db.execute(select(BudgetGoalDB).where(BudgetGoalDB.user_id == uid, BudgetGoalDB.category == "tresorerie"))
    tres_goal = tres_result.scalar_one_or_none()
    tresorerie = tres_goal.amount if tres_goal else 0
    if monthly_charges > 0 and tresorerie > 0:
        months_covered = tresorerie / monthly_charges
        if months_covered >= 3:
            score_cov = 25
        elif months_covered >= 1:
            score_cov = 15
        else:
            score_cov = 5
    else:
        score_cov = 5  # No treasury declared

    # 4. DIVERSIFICATION (25 pts) — nombre de categories de revenus
    rev_categories = set(e.category for e in entries if e.type == "revenu" and e.date and _tz(e.date) >= now - timedelta(days=90))
    nb_sources = len(rev_categories)
    if nb_sources >= 3:
        score_div = 25
    elif nb_sources >= 2:
        score_div = 15
    else:
        score_div = 5

    total = score_net + score_reg + score_cov + score_div

    # Level and message
    if total >= 75:
        level = "serenite"
        message = "Votre situation financiere soutient votre bien-etre. Continuez ainsi."
    elif total >= 50:
        level = "vigilance"
        message = "Quelques leviers a activer pour plus de tranquillite d'esprit."
    elif total >= 25:
        level = "tension"
        message = "Votre stress financier impacte probablement votre energie. Agissez sur les points faibles."
    else:
        level = "alerte"
        message = "Priorite : securiser votre situation pour proteger votre sante."

    # Comfort goal
    comfort_result = await db.execute(select(BudgetGoalDB).where(BudgetGoalDB.user_id == uid, BudgetGoalDB.category == "objectif_confort"))
    comfort_goal = comfort_result.scalar_one_or_none()
    comfort_target = comfort_goal.amount if comfort_goal else 0
    comfort_pct = min(100, round((current["revenus"] / comfort_target) * 100)) if comfort_target > 0 else 0

    return {
        "score": total,
        "level": level,
        "message": message,
        "pillars": {
            "resultat_net": {"score": score_net, "max": 25, "detail": f"Marge nette: {round((current['net'] / current['revenus'] * 100) if current['revenus'] > 0 else 0)}%"},
            "regularite": {"score": score_reg, "max": 25, "detail": f"Variation: {round(variation * 100) if len(revenus_list) >= 2 and max(revenus_list) > 0 else 'N/A'}%"},
            "couverture": {"score": score_cov, "max": 25, "detail": f"Tresorerie: {round(tresorerie)} EUR, charges: {round(monthly_charges)} EUR/mois"},
            "diversification": {"score": score_div, "max": 25, "detail": f"{nb_sources} source(s) de revenus"},
        },
        "comfort": {"target": comfort_target, "current": round(current["revenus"], 2), "pct": comfort_pct},
        "tresorerie": tresorerie,
    }


@finance_router.post("/comfort-goal")
async def set_comfort_goal(body: BudgetGoalSchema, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Definir l'objectif de CA 'confortable' mensuel."""
    result = await db.execute(select(BudgetGoalDB).where(BudgetGoalDB.user_id == user.id, BudgetGoalDB.category == "objectif_confort"))
    existing = result.scalar_one_or_none()
    if existing:
        await db.execute(update(BudgetGoalDB).where(BudgetGoalDB.id == existing.id).values(amount=body.amount))
    else:
        db.add(BudgetGoalDB(user_id=user.id, category="objectif_confort", amount=body.amount, period="mois"))
    await db.commit()
    return {"status": "ok", "target": body.amount}


@finance_router.post("/tresorerie")
async def set_tresorerie(body: BudgetGoalSchema, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Declarer la tresorerie disponible."""
    result = await db.execute(select(BudgetGoalDB).where(BudgetGoalDB.user_id == user.id, BudgetGoalDB.category == "tresorerie"))
    existing = result.scalar_one_or_none()
    if existing:
        await db.execute(update(BudgetGoalDB).where(BudgetGoalDB.id == existing.id).values(amount=body.amount))
    else:
        db.add(BudgetGoalDB(user_id=user.id, category="tresorerie", amount=body.amount, period="mois"))
    await db.commit()
    return {"status": "ok", "tresorerie": body.amount}

# ═══════════════════════════════════════════════════════════════════════
# FIX PILOTAGE FINANCIER : Import CSV/JSON depuis source externe
# ═══════════════════════════════════════════════════════════════════════
from fastapi import UploadFile, File
import csv, io, httpx

class ImportConnectorRequest(BaseModel):
    url: str
    freq: Optional[str] = "monthly"

@finance_router.post("/finance/import-url")
async def import_from_url(
    req: ImportConnectorRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Importer des données financières depuis une URL externe (JSON/CSV)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(req.url, headers={"Accept": "application/json,text/csv"})
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            entries_added = 0

            # Essayer JSON d'abord
            if "json" in content_type:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("transactions", data.get("entries", data.get("data", [])))
                for item in items[:200]:  # max 200 entrées
                    label = item.get("label") or item.get("name") or item.get("description") or "Import"
                    amount = float(item.get("amount") or item.get("montant") or 0)
                    entry_type = "revenu" if amount > 0 else "depense"
                    amount = abs(amount)
                    if amount > 0:
                        db.add(FinanceEntryDB(
                            user_id=user.id,
                            type=entry_type,
                            label=label[:100],
                            amount=round(amount, 2),
                            category="import",
                            recurring=False
                        ))
                        entries_added += 1

            # CSV sinon
            elif "csv" in content_type or req.url.endswith(".csv"):
                reader = csv.DictReader(io.StringIO(resp.text))
                for row in reader:
                    # Colonnes communes : montant/amount, libelle/label/description
                    label = row.get("libelle") or row.get("label") or row.get("description") or "Import CSV"
                    amount_str = row.get("montant") or row.get("amount") or row.get("credit") or row.get("debit") or "0"
                    try:
                        amount = float(str(amount_str).replace(",", ".").replace(" ", ""))
                    except ValueError:
                        continue
                    entry_type = "revenu" if amount > 0 else "depense"
                    amount = abs(amount)
                    if amount > 0:
                        db.add(FinanceEntryDB(
                            user_id=user.id,
                            type=entry_type,
                            label=label[:100],
                            amount=round(amount, 2),
                            category="import",
                            recurring=False
                        ))
                        entries_added += 1

            await db.commit()
            return {"ok": True, "entries_added": entries_added, "message": f"{entries_added} transactions importées"}

    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Impossible d'accéder à l'URL : {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'import : {str(e)}")

@finance_router.post("/finance/import-csv")
async def import_csv_upload(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Importer des transactions depuis un fichier CSV uploadé."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .csv sont acceptés")
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # gère le BOM Windows
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    entries_added = 0
    for row in reader:
        label = (row.get("libelle") or row.get("label") or row.get("Libellé") or row.get("description") or "Import")[:100]
        amount_str = row.get("montant") or row.get("amount") or row.get("Montant") or row.get("credit") or row.get("debit") or "0"
        try:
            amount = float(str(amount_str).replace(",", ".").replace(" ", "").replace("€", ""))
        except ValueError:
            continue
        if amount == 0:
            continue
        entry_type = "revenu" if amount > 0 else "depense"
        db.add(FinanceEntryDB(
            user_id=user.id,
            type=entry_type,
            label=label,
            amount=round(abs(amount), 2),
            category="import",
            recurring=False
        ))
        entries_added += 1

    await db.commit()
    return {"ok": True, "entries_added": entries_added}


# ─────────── Import CSV relevé bancaire — endpoint enrichi ──────────
# (remplace l'endpoint basique existant ci-dessus ; même URL pour compatibilité)
# Nouvelles fonctionnalités :
#   • Détection auto du format (BNP, Société Générale, LCL, Crédit Agricole, générique)
#   • Catégorisation IA basée sur des règles + mots-clés
#   • Déduplication par hash(date+label+amount)
#   • Endpoint GET /finance/csv-imports pour l'historique des imports

import hashlib
import csv
import io

_CATEGORY_RULES = {
    # salaires & revenus
    "salaire":    ("revenu", "salaire"),
    "virement":   ("revenu", "virement"),
    "facture":    ("revenu", "facturation"),
    "stripe":     ("revenu", "stripe"),
    "paypal":     ("revenu", "paypal"),
    "mollie":     ("revenu", "paiement-ligne"),
    # charges fixes
    "loyer":      ("depense", "loyer"),
    "assurance":  ("depense", "assurance"),
    "edf":        ("depense", "energie"),
    "orange":     ("depense", "telecom"),
    "sfr":        ("depense", "telecom"),
    "bouygues":   ("depense", "telecom"),
    "free":       ("depense", "telecom"),
    "ovh":        ("depense", "hebergement"),
    "github":     ("depense", "outils"),
    "notion":     ("depense", "outils"),
    "openai":     ("depense", "ia"),
    "anthropic":  ("depense", "ia"),
    "railway":    ("depense", "hebergement"),
    # transport
    "sncf":       ("depense", "transport"),
    "ratp":       ("depense", "transport"),
    "uber":       ("depense", "transport"),
    "blablacar":  ("depense", "transport"),
    # alimentation
    "franprix":   ("depense", "alimentation"),
    "monoprix":   ("depense", "alimentation"),
    "carrefour":  ("depense", "alimentation"),
    "leclerc":    ("depense", "alimentation"),
    "lidl":       ("depense", "alimentation"),
    "aldi":       ("depense", "alimentation"),
    # marketing
    "google ads": ("depense", "marketing"),
    "facebook":   ("depense", "marketing"),
    "meta":       ("depense", "marketing"),
    "linkedin":   ("depense", "marketing"),
    # compta
    "urssaf":     ("depense", "charges-sociales"),
    "impots":     ("depense", "impots"),
    "tresor":     ("depense", "impots"),
}


def _categorize(label: str, amount: float, explicit_type: str | None = None) -> tuple[str, str]:
    """Retourne (type, category) depuis le libellé + montant."""
    label_lower = label.lower()
    for kw, (t, cat) in _CATEGORY_RULES.items():
        if kw in label_lower:
            return t, cat
    # Fallback par signe du montant
    if explicit_type:
        return explicit_type, "import"
    return ("revenu" if amount >= 0 else "depense"), "import"


def _parse_date_fr(s: str) -> datetime | None:
    """Parse DD/MM/YYYY ou YYYY-MM-DD ou DD-MM-YYYY."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _row_hash(date_str: str, label: str, amount: float) -> str:
    return hashlib.md5(f"{date_str}|{label}|{amount:.2f}".encode()).hexdigest()[:16]


def _detect_bank_format(headers: list[str]) -> str:
    """Devine le format de la banque pour mapper les colonnes."""
    h = [x.lower().strip() for x in headers]
    if "date opération" in h or "date operation" in h:
        return "bnp"
    if "date de valeur" in h and "libellé" in h:
        return "sg"
    if "date comptable" in h:
        return "ca"
    if "date" in h and "montant" in h:
        return "generic"
    return "generic"


def _map_row(row: dict, fmt: str) -> tuple[str, str, float, str | None]:
    """Retourne (label, date_str, amount, explicit_type) selon le format détecté."""
    def get(*keys):
        for k in keys:
            v = row.get(k) or row.get(k.lower()) or row.get(k.upper()) or ""
            if v:
                return v.strip()
        return ""

    if fmt == "bnp":
        label = get("Libellé", "libellé", "LIBELLE")
        date_str = get("Date opération", "date opération", "DATE")
        credit = get("Crédit", "crédit", "CREDIT")
        debit = get("Débit", "débit", "DEBIT")
        if credit:
            amount = float(credit.replace(",", ".").replace(" ", "").replace("€", "") or "0")
            return label, date_str, amount, "revenu"
        if debit:
            amount = float(debit.replace(",", ".").replace(" ", "").replace("€", "") or "0")
            return label, date_str, -abs(amount), "depense"
        return label, date_str, 0.0, None

    if fmt == "sg":
        label = get("Libellé", "libellé")
        date_str = get("Date de valeur", "date de valeur", "Date")
        amount_str = get("Montant", "montant")
        amount = float(amount_str.replace(",", ".").replace(" ", "").replace("€", "") or "0")
        return label, date_str, amount, None

    # generic
    label = get("Libellé", "libellé", "label", "Libelle", "description", "Description", "LIBELLE")
    date_str = get("Date", "date", "DATE", "date comptable", "Date opération")
    # Chercher colonne montant (débit/crédit séparés ou fusionnés)
    credit_str = get("Crédit", "crédit", "credit", "CREDIT", "montant crédit")
    debit_str = get("Débit", "débit", "debit", "DEBIT", "montant débit")
    amount_str = get("Montant", "montant", "MONTANT", "amount")

    if credit_str and debit_str:
        c = float(credit_str.replace(",", ".").replace(" ", "").replace("€", "") or "0")
        d = float(debit_str.replace(",", ".").replace(" ", "").replace("€", "") or "0")
        if c > 0:
            return label, date_str, c, "revenu"
        return label, date_str, -abs(d), "depense"

    amount = float(amount_str.replace(",", ".").replace(" ", "").replace("€", "") or "0")
    return label, date_str, amount, None


@finance_router.post("/import-csv-v2")
async def import_csv_v2(
    file: UploadFile = File(...),
    preview: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import CSV relevé bancaire — version enrichie.

    • preview=true → analyse sans écriture en base (pour prévisualisation frontend)
    • Détection auto BNP / SG / CA / générique
    • Catégorisation IA par mots-clés
    • Déduplication : ignore les lignes déjà importées (même hash)
    • Retourne: { ok, entries_added, duplicates_skipped, preview_rows, bank_format }
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Seuls les fichiers .csv sont acceptés")

    content = await file.read()
    try:
        raw = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raw = content.decode("latin-1")

    # Détecter séparateur
    sep = ";" if raw.count(";") > raw.count(",") else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=sep)
    headers = reader.fieldnames or []
    bank_format = _detect_bank_format(headers)

    # Charger les hashes existants pour déduplication
    existing_hashes: set[str] = set()
    if not preview:
        hashes_res = await db.execute(
            text("SELECT notes FROM finance_entries WHERE user_id = :uid AND notes LIKE 'hash:%'"),
            {"uid": user.id},
        )
        existing_hashes = {r[0].replace("hash:", "") for r in hashes_res.fetchall()}

    preview_rows = []
    entries_to_add = []
    duplicates_skipped = 0
    parse_errors = 0

    for row in reader:
        try:
            label, date_str, amount, explicit_type = _map_row(row, bank_format)
            if not label or amount == 0:
                continue
            entry_type, category = _categorize(label, amount, explicit_type)
            entry_date = _parse_date_fr(date_str) or datetime.now(timezone.utc)
            row_hash = _row_hash(date_str, label, abs(amount))

            if row_hash in existing_hashes:
                duplicates_skipped += 1
                continue

            entry_info = {
                "hash": row_hash,
                "type": entry_type,
                "label": label[:100],
                "amount": round(abs(amount), 2),
                "category": category,
                "date": entry_date.isoformat(),
            }
            preview_rows.append(entry_info)
            entries_to_add.append(entry_info)
        except Exception:
            parse_errors += 1
            continue

    if preview:
        return {
            "preview": True,
            "bank_format": bank_format,
            "total_rows": len(preview_rows) + duplicates_skipped,
            "will_add": len(preview_rows),
            "duplicates_skipped": duplicates_skipped,
            "parse_errors": parse_errors,
            "preview_rows": preview_rows[:20],
        }

    # Écriture en base
    import uuid as _uuid
    for e in entries_to_add:
        db.add(FinanceEntryDB(
            id=str(_uuid.uuid4()),
            user_id=user.id,
            type=e["type"],
            label=e["label"],
            amount=e["amount"],
            category=e["category"],
            date=datetime.fromisoformat(e["date"]),
            recurring=False,
            notes=f"hash:{e['hash']}",
        ))
    await db.commit()

    return {
        "ok": True,
        "bank_format": bank_format,
        "entries_added": len(entries_to_add),
        "duplicates_skipped": duplicates_skipped,
        "parse_errors": parse_errors,
    }


# ── Roadmap freeze / approve ──────────────────────────────────────────────────

class RoadmapFreezeIn(BaseModel):
    frozen: bool = True

@finance_router.post("/roadmap-freeze")
async def roadmap_freeze(body: RoadmapFreezeIn, user=Depends(get_current_user), db=Depends(get_db)):
    """Gèle ou libère la roadmap 48h."""
    try:
        from routes.swot_cron import _get_prefs, _set_prefs
        if body.frozen:
            frozen_until = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
            await _set_prefs(db, user.id, {"roadmap_frozen": True, "roadmap_frozen_until": frozen_until})
        else:
            await _set_prefs(db, user.id, {"roadmap_frozen": False, "roadmap_frozen_until": None})
    except Exception:
        pass
    return {"ok": True, "frozen": body.frozen}

@finance_router.get("/roadmap-freeze")
async def roadmap_freeze_status(user=Depends(get_current_user), db=Depends(get_db)):
    """Retourne l'état courant du gel roadmap."""
    try:
        from routes.swot_cron import _get_prefs
        prefs = await _get_prefs(db, user.id)
        frozen = prefs.get("roadmap_frozen", False)
        frozen_until = prefs.get("roadmap_frozen_until")
        if frozen and frozen_until:
            until_dt = datetime.fromisoformat(frozen_until.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > until_dt:
                frozen = False
        return {"frozen": frozen, "frozen_until": frozen_until}
    except Exception:
        return {"frozen": False, "frozen_until": None}

@finance_router.post("/roadmap-approve")
async def roadmap_approve(user=Depends(get_current_user), db=Depends(get_db)):
    """Valide la roadmap."""
    try:
        from routes.swot_cron import _set_prefs
        await _set_prefs(db, user.id, {"roadmap_approved_at": datetime.now(timezone.utc).isoformat()})
    except Exception:
        pass
    return {"ok": True, "approved_at": datetime.now(timezone.utc).isoformat()}
