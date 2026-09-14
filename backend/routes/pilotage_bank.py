"""Pilotage Bank Sync — endpoint Make/Zapier pour synchroniser les transactions bancaires.

Flow attendu :
  1. L'utilisateur configure dans Make un scénario : Qonto / Bridge / Stripe → Webhook Zayado
  2. À chaque nouvelle transaction, Make envoie POST /api/pilotage/bank/sync avec le payload
  3. On stocke dans la table `bank_transactions` (créée automatiquement)
  4. Le dashboard Pilotage agrège ces transactions par mois pour calculer CA, charges, marge

Sécurité : header X-Make-Secret (env MAKE_WEBHOOK_SECRET) requis.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database import DB_TYPE
from models import User
from deps import get_current_user

logger = logging.getLogger(__name__)
pilotage_bank_router = APIRouter()

MAKE_WEBHOOK_SECRET = os.environ.get("MAKE_WEBHOOK_SECRET", "")
_IS_SQLITE = (DB_TYPE == "sqlite")


# ─── Schémas ───────────────────────────────────────────────────────
class BankTxIn(BaseModel):
    user_id: str = Field(..., description="ID de l'utilisateur Zayado")
    external_id: str = Field(..., description="ID unique de la transaction côté Qonto/Stripe/etc.")
    source: str = Field("qonto", description="qonto | bridge | stripe | manual")
    type: str = Field("income", description="income | expense | transfer")
    amount_cents: int = Field(..., description="Montant en centimes (positif=encaissé, négatif=dépense)")
    currency: str = Field("EUR")
    label: str = Field("", description="Libellé / mémo")
    category: Optional[str] = Field(None, description="Catégorie (vente, abonnement, charges, salaire, etc.)")
    counterparty: Optional[str] = Field(None, description="Nom du client/fournisseur")
    booked_at: Optional[str] = Field(None, description="ISO datetime de la transaction")


# ─── Helpers ────────────────────────────────────────────────────────
async def _ensure_table(db: AsyncSession):
    if _IS_SQLITE:
        await db.execute(text(
            "CREATE TABLE IF NOT EXISTS bank_transactions ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id VARCHAR(36) NOT NULL, "
            "external_id VARCHAR(128) NOT NULL, "
            "source VARCHAR(32) NOT NULL DEFAULT 'qonto', "
            "type VARCHAR(16) NOT NULL DEFAULT 'income', "
            "amount_cents INT NOT NULL DEFAULT 0, "
            "currency VARCHAR(8) NOT NULL DEFAULT 'EUR', "
            "label VARCHAR(255) DEFAULT NULL, "
            "category VARCHAR(64) DEFAULT NULL, "
            "counterparty VARCHAR(128) DEFAULT NULL, "
            "booked_at TIMESTAMP DEFAULT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "UNIQUE (user_id, source, external_id))"
        ))
        await db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_bank_user_booked ON bank_transactions (user_id, booked_at)"
        ))
    else:
        await db.execute(text(
            "CREATE TABLE IF NOT EXISTS bank_transactions ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "user_id VARCHAR(36) NOT NULL, "
            "external_id VARCHAR(128) NOT NULL, "
            "source VARCHAR(32) NOT NULL DEFAULT 'qonto', "
            "type VARCHAR(16) NOT NULL DEFAULT 'income', "
            "amount_cents INT NOT NULL DEFAULT 0, "
            "currency VARCHAR(8) NOT NULL DEFAULT 'EUR', "
            "label VARCHAR(255) DEFAULT NULL, "
            "category VARCHAR(64) DEFAULT NULL, "
            "counterparty VARCHAR(128) DEFAULT NULL, "
            "booked_at TIMESTAMP DEFAULT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "INDEX idx_user_booked (user_id, booked_at), "
            "UNIQUE KEY unique_external (user_id, source, external_id))"
        ))


# ─── Endpoints ───────────────────────────────────────────────────────
@pilotage_bank_router.post("/pilotage/bank/sync")
async def sync_bank_transaction(
    body: BankTxIn,
    db: AsyncSession = Depends(get_db),
    x_make_secret: Optional[str] = Header(None),
):
    """Webhook Make — enregistre une transaction bancaire.

    Authentification : header X-Make-Secret (vérifié contre MAKE_WEBHOOK_SECRET env).
    Si MAKE_WEBHOOK_SECRET non configuré côté serveur, l'endpoint refuse tout.

    Idempotent : (user_id, source, external_id) est UNIQUE → un même Make-run
    peut être rejoué sans dupliquer.
    """
    if not MAKE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="MAKE_WEBHOOK_SECRET non configuré côté serveur")
    if x_make_secret != MAKE_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Secret Make invalide")

    await _ensure_table(db)

    booked = None
    if body.booked_at:
        try:
            booked = datetime.fromisoformat(body.booked_at.replace("Z", "+00:00"))
        except Exception:
            booked = datetime.now(timezone.utc)
    else:
        booked = datetime.now(timezone.utc)

    try:
        params = {
            "uid": body.user_id, "eid": body.external_id, "src": body.source, "typ": body.type,
            "amt": body.amount_cents, "cur": body.currency, "lbl": body.label[:255] if body.label else None,
            "cat": body.category, "cp": body.counterparty, "bk": booked.isoformat(),
        }
        # Upsert portable : UPDATE puis INSERT si aucune ligne (clé logique user_id+source+external_id)
        res = await db.execute(
            text(
                "UPDATE bank_transactions SET "
                "amount_cents=:amt, label=:lbl, category=:cat, counterparty=:cp, booked_at=:bk "
                "WHERE user_id=:uid AND source=:src AND external_id=:eid"
            ),
            params,
        )
        if res.rowcount == 0:
            await db.execute(
                text(
                    "INSERT INTO bank_transactions "
                    "(user_id, external_id, source, type, amount_cents, currency, label, category, counterparty, booked_at) "
                    "VALUES (:uid, :eid, :src, :typ, :amt, :cur, :lbl, :cat, :cp, :bk)"
                ),
                params,
            )
        await db.commit()
    except Exception as e:
        logger.warning("bank_transactions insert failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Insert failed: {e}")

    return {"status": "ok", "external_id": body.external_id, "stored_at": datetime.now(timezone.utc).isoformat()}


@pilotage_bank_router.get("/pilotage/bank/summary")
async def get_bank_summary(
    months: int = 6,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retourne l'agrégat CA/charges/marge des N derniers mois pour le user authentifié."""
    await _ensure_table(db)

    if _IS_SQLITE:
        summary_sql = (
            "SELECT strftime('%Y-%m', booked_at) AS month, "
            "SUM(CASE WHEN amount_cents > 0 THEN amount_cents ELSE 0 END) AS income_cents, "
            "SUM(CASE WHEN amount_cents < 0 THEN amount_cents ELSE 0 END) AS expense_cents, "
            "COUNT(*) AS tx_count "
            "FROM bank_transactions "
            "WHERE user_id = :uid AND booked_at >= datetime('now', :interval) "
            "GROUP BY strftime('%Y-%m', booked_at) "
            "ORDER BY month ASC"
        )
        params = {"uid": user.id, "interval": f"-{int(months)} months"}
    else:
        summary_sql = (
            "SELECT DATE_FORMAT(booked_at, '%Y-%m') AS month, "
            "SUM(CASE WHEN amount_cents > 0 THEN amount_cents ELSE 0 END) AS income_cents, "
            "SUM(CASE WHEN amount_cents < 0 THEN amount_cents ELSE 0 END) AS expense_cents, "
            "COUNT(*) AS tx_count "
            "FROM bank_transactions "
            "WHERE user_id = :uid AND booked_at >= DATE_SUB(NOW(), INTERVAL :m MONTH) "
            "GROUP BY DATE_FORMAT(booked_at, '%Y-%m') "
            "ORDER BY month ASC"
        )
        params = {"uid": user.id, "m": int(months)}

    rows = (await db.execute(text(summary_sql), params)).fetchall()

    series = []
    for r in rows:
        month, income, expense, count = r
        series.append({
            "month": month,
            "income_cents": int(income or 0),
            "expense_cents": int(expense or 0),
            "margin_cents": int(income or 0) + int(expense or 0),
            "tx_count": int(count or 0),
        })

    total_income = sum(s["income_cents"] for s in series)
    total_expense = sum(s["expense_cents"] for s in series)

    return {
        "months": months,
        "series": series,
        "total_income_cents": total_income,
        "total_expense_cents": total_expense,
        "total_margin_cents": total_income + total_expense,
        "configured": bool(MAKE_WEBHOOK_SECRET),
    }


@pilotage_bank_router.get("/pilotage/bank/config")
async def get_bank_config(user: User = Depends(get_current_user)):
    """Retourne les infos de config Make côté frontend (URL webhook + statut)."""
    backend_url = os.environ.get("APP_BASE_URL", "https://app.zayado.net")
    return {
        "webhook_url": f"{backend_url}/api/pilotage/bank/sync",
        "secret_configured": bool(MAKE_WEBHOOK_SECRET),
        "secret_header": "X-Make-Secret",
        "instructions": [
            "1. Crée un scénario Make.com qui récupère tes transactions Qonto/Bridge/Stripe",
            "2. Module HTTP → POST vers le webhook_url ci-dessus",
            "3. Ajoute le header X-Make-Secret avec ta valeur de MAKE_WEBHOOK_SECRET",
            "4. Body JSON : { user_id, external_id, source, type, amount_cents, label, booked_at }",
            "5. Active le scénario — les transactions remontent dans Pilotage en temps réel",
        ],
    }
