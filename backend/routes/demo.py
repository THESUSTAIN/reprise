"""
demo.py — Mode "Démo Investisseur" (compte Thomas / admin).

Un bouton du cockpit appelle POST /api/demo/investor-fill : on peuple en <1s les
VRAIES tables (énergie, bien-être, finances, vision) de l'utilisateur courant pour
que le cockpit s'anime immédiatement (Énergie / Score Business / Équilibre + CA).
Idempotent (marqueur DEMO_INVESTOR). POST /api/demo/investor-reset remet à zéro.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

logger = logging.getLogger("demo")
demo_router = APIRouter(prefix="/demo", tags=["Demo"])

_TAG = "DEMO_INVESTOR"


def _require_investor_demo_access(user: User):
    """Reservé à Thomas (compte démo) et aux admins — jusqu'ici cette
    restriction n'existait QUE côté frontend (le bouton était masque pour
    les autres, mais rien n'empêchait un appel direct à l'API). N'importe
    quel utilisateur connecté pouvait donc peupler son propre compte de
    fausses données financières/bien-être via ces endpoints."""
    allowed = user and (user.email == "thomas@zayado.fr" or user.role in ("admin", "super_admin"))
    if not allowed:
        raise HTTPException(status_code=403, detail="Reserve au compte de demo / aux admins.")


@demo_router.get("/investor-status")
async def investor_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_investor_demo_access(user)
    try:
        row = (await db.execute(text(
            "SELECT COUNT(*) FROM finance_entries WHERE user_id = :uid AND notes = :tag"
        ), {"uid": user.id, "tag": _TAG})).scalar() or 0
        return {"active": row > 0}
    except Exception as e:
        # Rapporté en QA : ce endpoint renvoyait un 500 brut en prod ("le
        # bouton ne fait strictement rien"). Cause exacte non reproductible
        # sans les logs serveur réels (probable dérive de schéma sur
        # finance_entries en prod) — en attendant, on dégrade proprement
        # (le bouton reste utilisable) au lieu de casser la page, et on
        # logge l'erreur réelle côté serveur pour investigation.
        logger.error(f"investor_status failed for user {user.id}: {e}", exc_info=True)
        return {"active": False}


@demo_router.post("/investor-fill")
async def investor_fill(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_investor_demo_access(user)
    uid = user.id
    try:
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()

        # 1) Énergie du jour (upsert)
        e = (await db.execute(text("SELECT id FROM user_energy WHERE user_id=:uid AND date=:d"),
                              {"uid": uid, "d": today})).fetchone()
        if e:
            await db.execute(text("UPDATE user_energy SET level=5, note='Démo investisseur' WHERE id=:id"), {"id": e[0]})
        else:
            await db.execute(text(
                "INSERT INTO user_energy (id, user_id, level, note, date, created_at) "
                "VALUES (:id,:uid,5,'Démo investisseur',:d,:ca)"
            ), {"id": str(uuid.uuid4()), "uid": uid, "d": today, "ca": now.isoformat()})

        # 2) Check-in bien-être du jour (score élevé) — on nettoie celui du jour d'abord
        await db.execute(text("DELETE FROM wellness_checkins WHERE user_id=:uid AND date >= :d0"),
                         {"uid": uid, "d0": now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()})
        await db.execute(text(
            "INSERT INTO wellness_checkins (id, user_id, energy, mood, stress, sleep, notes, score, date, created_at) "
            "VALUES (:id,:uid,4,4,2,4,:tag,86,:d,:ca)"
        ), {"id": str(uuid.uuid4()), "uid": uid, "tag": _TAG, "d": now.isoformat(), "ca": now.isoformat()})

        # 3) Finances : CA du mois crédible + delta hebdo réaliste (~ +12%)
        await db.execute(text("DELETE FROM finance_entries WHERE user_id=:uid AND notes=:tag"), {"uid": uid, "tag": _TAG})
        entries = [
            ("Abonnements Pro (récurrent)", 3000.0, 9),   # semaine précédente
            ("Prestation conseil",         2600.0, 8),   # semaine précédente
            ("Marketplace — commissions",  1800.0, 5),   # cette semaine
            ("Nouveau client PME",         2100.0, 3),   # cette semaine
            ("Client Entreprise (acompte)",2400.0, 1),   # cette semaine
            # Mois précédent (pour un delta mensuel crédible ~ +20%, pas +1000%)
            ("CA mois précédent — récurrent", 15000.0, 36),
            ("CA mois précédent — prestations", 10000.0, 41),
        ]
        for label, amount, days_ago in entries:
            d = (now - timedelta(days=days_ago)).isoformat()
            await db.execute(text(
                "INSERT INTO finance_entries (id, user_id, type, label, amount, category, date, recurring, notes, created_at) "
                "VALUES (:id,:uid,'revenu',:label,:amt,'ventes',:d,0,:tag,:ca)"
            ), {"id": str(uuid.uuid4()), "uid": uid, "label": label, "amt": amount, "d": d, "tag": _TAG, "ca": now.isoformat()})

        # 4) Vision : alignement + résumé (dans settings)
        settings = dict(user.settings or {})
        settings.update({
            "vision_alignment": 78,
            "vision_summary": "Devenir la marketplace de mutualisation de référence pour les TPE/PME d'ici 3 ans.",
            "why": "Lancer la campagne d'acquisition et signer 3 partenaires stratégiques.",
            "ca_objective": 20000,
            "_demo_investor": True,
        })
        await db.execute(text("UPDATE users SET settings = :s WHERE id = :id"),
                         {"s": __import__("json").dumps(settings), "id": uid})
        await db.commit()
        return {"ok": True, "message": "Cockpit peuplé pour la démo investisseur."}
    except Exception as e:
        await db.rollback()
        logger.error(f"investor_fill failed for user {uid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur lors du remplissage de la démo. Voir logs serveur.")


@demo_router.post("/investor-reset")
async def investor_reset(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_investor_demo_access(user)
    uid = user.id
    try:
        await db.execute(text("DELETE FROM finance_entries WHERE user_id=:uid AND notes=:tag"), {"uid": uid, "tag": _TAG})
        await db.execute(text("DELETE FROM wellness_checkins WHERE user_id=:uid AND notes=:tag"), {"uid": uid, "tag": _TAG})
        await db.execute(text("UPDATE user_energy SET level=0 WHERE user_id=:uid AND note='Démo investisseur'"), {"uid": uid})
        settings = dict(user.settings or {})
        for k in ("vision_alignment", "vision_summary", "why", "_demo_investor"):
            settings.pop(k, None)
        await db.execute(text("UPDATE users SET settings = :s WHERE id = :id"),
                         {"s": __import__("json").dumps(settings), "id": uid})
        await db.commit()
        return {"ok": True, "message": "Données de démo retirées."}
    except Exception as e:
        await db.rollback()
        logger.error(f"investor_reset failed for user {uid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur lors de la réinitialisation. Voir logs serveur.")
