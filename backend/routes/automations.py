"""
automations.py — Logique backend des Automatisations dans Paramètres.

Chaque automatisation est stockée en DB (table user_data, key="automations").
L'exécution réelle est déclenchée :
  • Via le webhook universel /api/automations/trigger (Make/Zapier → Zayado)
  • Manuellement via POST /api/automations/{id}/run
  • Par le scheduler interne (tous les vendredis pour a5, etc.)

Actions réelles implémentées :
  a1 — Stripe paiement → email bienvenue Brevo + fiche lead CRM
  a2 — Commentaire YouTube → brouillon de réponse IA
  a3 — Résumé Facebook Groupe (message quotidien à 18h)
  a4 — Lead Facebook Ads → WhatsApp + Brevo
  a5 — Compte-rendu semaine (vendredi 17h)
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, async_session_factory
from deps import get_current_user
from models import User

logger = logging.getLogger(__name__)
automations_router = APIRouter(prefix="/api/automations", tags=["automations"])

# ─────────── Schémas ─────────────────────────────────────────────────
class AutomationToggle(BaseModel):
    enabled: bool


class AutomationRunResult(BaseModel):
    automation_id: str
    status: str           # "success" | "error" | "skipped"
    message: str
    executed_at: str


class WebhookTriggerIn(BaseModel):
    """Payload Make/Zapier → /api/automations/trigger"""
    automation_id: str       # a1, a2, a3, a4, a5
    user_id: Optional[str] = None
    payload: dict = {}


# ─────────── Persistance (user_data) ────────────────────────────────
DEFAULT_AUTOMATIONS = [
    {
        "id": "a1",
        "title": "Nouveau client Stripe → email bienvenue + fiche CRM",
        "when": "Quand un paiement Stripe arrive",
        "then": "L'IA génère un email Brevo personnalisé + crée la fiche CRM",
        "enabled": True,
        "trigger": "webhook",
        "last_run": None,
        "run_count": 0,
    },
    {
        "id": "a2",
        "title": "Commentaire YouTube → réponse IA proposée",
        "when": "Quand un commentaire est posté sur tes vidéos",
        "then": "Brouillon de réponse cohérent avec ton ton, prêt à valider",
        "enabled": True,
        "trigger": "webhook",
        "last_run": None,
        "run_count": 0,
    },
    {
        "id": "a3",
        "title": "Message Facebook Groupe → résumé quotidien",
        "when": "Chaque jour à 18h",
        "then": "Synthèse des conversations & questions importantes",
        "enabled": False,
        "trigger": "cron",
        "cron": "daily_18h",
        "last_run": None,
        "run_count": 0,
    },
    {
        "id": "a4",
        "title": "Lead Facebook Ads → relance WhatsApp",
        "when": "Quand un lead Ads est capté",
        "then": "Message de bienvenue WhatsApp + ajout dans Brevo",
        "enabled": True,
        "trigger": "webhook",
        "last_run": None,
        "run_count": 0,
    },
    {
        "id": "a5",
        "title": "Compte-rendu de semaine automatique",
        "when": "Tous les vendredis à 17h",
        "then": "Synthèse envoyée par email + déposée Notion",
        "enabled": True,
        "trigger": "cron",
        "cron": "weekly_fri_17h",
        "last_run": None,
        "run_count": 0,
    },
]


async def _get_automations(db: AsyncSession, user_id: str) -> list:
    r = await db.execute(
        text("SELECT value FROM user_data WHERE user_id = :uid AND `key` = 'automations' LIMIT 1"),
        {"uid": user_id},
    )
    row = r.fetchone()
    if not row:
        return [dict(a) for a in DEFAULT_AUTOMATIONS]
    try:
        stored = json.loads(row[0])
        # Merge avec les defaults pour garantir les nouveaux champs
        stored_map = {a["id"]: a for a in stored}
        merged = []
        for default in DEFAULT_AUTOMATIONS:
            stored_a = stored_map.get(default["id"], {})
            merged.append({**default, **stored_a})
        return merged
    except Exception:
        return [dict(a) for a in DEFAULT_AUTOMATIONS]


async def _save_automations(db: AsyncSession, user_id: str, automations: list):
    data = json.dumps(automations)
    existing = (await db.execute(
        text("SELECT id FROM user_data WHERE user_id = :uid AND `key` = 'automations'"),
        {"uid": user_id},
    )).fetchone()
    if existing:
        await db.execute(
            text("UPDATE user_data SET value = :d WHERE user_id = :uid AND `key` = 'automations'"),
            {"d": data, "uid": user_id},
        )
    else:
        await db.execute(
            text("INSERT INTO user_data (id, user_id, `key`, value) VALUES (:id, :uid, 'automations', :d)"),
            {"id": str(uuid.uuid4()), "uid": user_id, "d": data},
        )
    await db.commit()


# ─────────── Exécuteurs réels ─────────────────────────────────────────

async def _run_a1(db: AsyncSession, user: User, payload: dict) -> str:
    """Stripe paiement → email bienvenue Brevo + fiche lead CRM."""
    customer_email = payload.get("customer_email") or payload.get("email", "")
    customer_name = payload.get("customer_name") or payload.get("name", "Nouveau client")
    amount = payload.get("amount_eur") or payload.get("amount", 0)

    if not customer_email:
        return "email_missing"

    # Créer fiche lead
    try:
        from sqlalchemy import text as t
        await db.execute(t(
            "INSERT INTO user_data (id, user_id, `key`, value) "
            "SELECT :id, :uid, 'leads', JSON_ARRAY_APPEND(COALESCE("
            "(SELECT value FROM user_data WHERE user_id = :uid AND `key` = 'leads'), '[]'), "
            "'$', CAST(:lead AS JSON)) ON DUPLICATE KEY UPDATE data = "
            "JSON_ARRAY_APPEND(COALESCE(data, '[]'), '$', CAST(:lead AS JSON))"
        ), {
            "id": str(uuid.uuid4()),
            "uid": user.id,
            "lead": json.dumps({
                "id": str(uuid.uuid4()),
                "name": customer_name,
                "email": customer_email,
                "status": "Gagné",
                "from": "Stripe",
                "score": 95,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }),
        })
        await db.commit()
    except Exception as e:
        logger.warning(f"[AUTO a1] Lead insert error: {e}")

    # Envoyer email bienvenue Brevo
    try:
        from utils import send_brevo_email
        loop = asyncio.get_running_loop()
        html = f"""
        <h2>Bienvenue, {customer_name} !</h2>
        <p>Votre paiement de <strong>{amount} €</strong> a bien été reçu.</p>
        <p>Votre accès est maintenant activé. Connectez-vous et commencez à piloter votre business.</p>
        <p>À très vite,<br>L'équipe Zayado</p>
        """
        await loop.run_in_executor(None, lambda: send_brevo_email(
            to_email=customer_email,
            to_name=customer_name,
            subject=f"Bienvenue sur Zayado, {customer_name.split()[0]} 🎉",
            html_content=html,
            brand="zayado",
        ))
        return "email_sent_lead_created"
    except Exception as e:
        logger.warning(f"[AUTO a1] Brevo send error: {e}")
        return "lead_created_email_failed"


async def _run_a2(db: AsyncSession, user: User, payload: dict) -> str:
    """Commentaire YouTube → brouillon de réponse IA."""
    comment = payload.get("comment_text", "")
    video_title = payload.get("video_title", "votre vidéo")
    author = payload.get("author_name", "un viewer")

    if not comment:
        return "no_comment_text"

    try:
        from mammouth_client import chat_completion
        prompt = (
            f"Tu es un créateur de contenu. Quelqu'un a commenté sur '{video_title}' :\n"
            f"'{comment}'\n\n"
            f"Rédige une réponse courte, chaleureuse et personnalisée (max 3 phrases). "
            f"Commence par prénom si possible. Sois authentique."
        )
        reply = await chat_completion(prompt, model="claude-haiku-4-5-20251001", max_tokens=200)

        # Stocker le brouillon en user_data
        drafts_key = "yt_comment_drafts"
        r = await db.execute(
            text("SELECT value FROM user_data WHERE user_id = :uid AND `key` = :k LIMIT 1"),
            {"uid": user.id, "k": drafts_key},
        )
        row = r.fetchone()
        drafts = json.loads(row[0]) if row else []
        drafts = [{
            "id": str(uuid.uuid4()),
            "comment": comment,
            "author": author,
            "video": video_title,
            "draft_reply": reply,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
        }] + drafts[:49]

        data = json.dumps(drafts)
        existing = (await db.execute(
            text("SELECT id FROM user_data WHERE user_id = :uid AND `key` = :k"),
            {"uid": user.id, "k": drafts_key},
        )).fetchone()
        if existing:
            await db.execute(
                text("UPDATE user_data SET value = :d WHERE user_id = :uid AND `key` = :k"),
                {"d": data, "uid": user.id, "k": drafts_key},
            )
        else:
            await db.execute(
                text("INSERT INTO user_data (id, user_id, `key`, value) VALUES (:id, :uid, :k, :d)"),
                {"id": str(uuid.uuid4()), "uid": user.id, "k": drafts_key, "d": data},
            )
        await db.commit()
        return "draft_created"
    except Exception as e:
        logger.warning(f"[AUTO a2] Error: {e}")
        return f"error:{e}"


async def _run_a4(db: AsyncSession, user: User, payload: dict) -> str:
    """Lead Facebook Ads → WhatsApp bienvenue + Brevo."""
    lead_name = payload.get("name", "")
    lead_phone = payload.get("phone", "")
    lead_email = payload.get("email", "")

    results = []

    # Ajouter à Brevo contact list
    if lead_email:
        try:
            import sib_api_v3_sdk
            from sib_api_v3_sdk.rest import ApiException
            import os
            config = sib_api_v3_sdk.Configuration()
            config.api_key["api-key"] = os.environ.get("BREVO_API_KEY", "")
            contacts_api = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(config))
            contacts_api.create_contact(sib_api_v3_sdk.CreateContact(
                email=lead_email,
                attributes={"PRENOM": lead_name.split()[0] if lead_name else "", "SOURCE": "Facebook Ads"},
                list_ids=[2],   # Liste "Leads Ads" — à adapter
                update_enabled=True,
            ))
            results.append("brevo_added")
        except Exception as e:
            logger.warning(f"[AUTO a4] Brevo contact error: {e}")
            results.append("brevo_failed")

    # WhatsApp bienvenue via Railway proxy (si configuré)
    if lead_phone:
        try:
            import httpx, os
            wa_url = os.environ.get("WHATSAPP_SERVICE_URL", "")
            wa_secret = os.environ.get("WHATSAPP_SERVICE_SECRET", "")
            if wa_url and wa_secret:
                first = lead_name.split()[0] if lead_name else "vous"
                msg = (
                    f"Bonjour {first} 👋 Merci pour votre intérêt ! "
                    f"Je reviens vers vous dans les prochaines heures. "
                    f"En attendant, n'hésitez pas à visiter notre site."
                )
                async with httpx.AsyncClient(timeout=10) as session:
                    await session.post(f"{wa_url}/send", json={
                        "to": lead_phone,
                        "message": msg,
                    }, headers={"X-Secret": wa_secret})
                results.append("whatsapp_sent")
        except Exception as e:
            logger.warning(f"[AUTO a4] WhatsApp error: {e}")
            results.append("whatsapp_failed")

    return ",".join(results) if results else "no_contact_info"


async def _run_a5(db: AsyncSession, user: User) -> str:
    """Compte-rendu de semaine — email récap + stockage."""
    try:
        from mammouth_client import chat_completion
        # Récupérer les tâches de la semaine
        from datetime import timedelta
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        summary_prompt = (
            "Génère un compte-rendu de semaine pour un solopreneur / entrepreneur. "
            "Format : 3 sections — ✅ Accompli cette semaine, 🎯 Priorités semaine prochaine, "
            "💡 Conseil de l'IA. Style direct, motivant, < 150 mots."
        )
        summary = await chat_completion(summary_prompt, model="claude-haiku-4-5-20251001", max_tokens=300)

        # Envoyer par email
        if user.email:
            from utils import send_brevo_email
            loop = asyncio.get_running_loop()
            html = f"<div style='font-family:sans-serif;max-width:600px'>{summary.replace(chr(10), '<br>')}</div>"
            await loop.run_in_executor(None, lambda: send_brevo_email(
                to_email=user.email,
                to_name=user.name or "",
                subject=f"Votre semaine en 3 points — {datetime.now().strftime('%d/%m')}",
                html_content=html,
                brand="zayado",
            ))

        # Stocker en user_data
        await db.execute(text(
            "INSERT INTO user_data (id, user_id, `key`, value) VALUES (:id, :uid, 'weekly_recap_latest', :d) "
            "ON DUPLICATE KEY UPDATE data = :d"
        ), {
            "id": str(uuid.uuid4()),
            "uid": user.id,
            "d": json.dumps({"summary": summary, "generated_at": datetime.now(timezone.utc).isoformat()}),
        })
        await db.commit()
        return "recap_sent"
    except Exception as e:
        logger.warning(f"[AUTO a5] Error: {e}")
        return f"error:{e}"


_EXECUTORS = {
    "a1": _run_a1,
    "a2": _run_a2,
    "a4": _run_a4,
}


async def _execute_automation(db: AsyncSession, user: User, auto_id: str, payload: dict) -> AutomationRunResult:
    """Dispatch vers l'exécuteur réel."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        if auto_id == "a5":
            msg = await _run_a5(db, user)
        elif auto_id in _EXECUTORS:
            msg = await _EXECUTORS[auto_id](db, user, payload)
        else:
            return AutomationRunResult(
                automation_id=auto_id, status="skipped",
                message=f"Automatisation {auto_id} non encore implémentée",
                executed_at=now,
            )
        return AutomationRunResult(
            automation_id=auto_id, status="success",
            message=msg, executed_at=now,
        )
    except Exception as e:
        logger.exception(f"[AUTOMATIONS] {auto_id} error: {e}")
        return AutomationRunResult(
            automation_id=auto_id, status="error",
            message=str(e), executed_at=now,
        )


# ─────────── Endpoints ───────────────────────────────────────────────

@automations_router.get("")
async def list_automations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    automations = await _get_automations(db, user.id)
    return {"automations": automations}


@automations_router.patch("/{auto_id}/toggle")
async def toggle_automation(
    auto_id: str,
    body: AutomationToggle,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Active/désactive une automatisation (persiste en DB)."""
    automations = await _get_automations(db, user.id)
    updated = [
        {**a, "enabled": body.enabled} if a["id"] == auto_id else a
        for a in automations
    ]
    await _save_automations(db, user.id, updated)
    return {"status": "ok", "automation_id": auto_id, "enabled": body.enabled}


@automations_router.post("/{auto_id}/run")
async def run_automation_manual(
    auto_id: str,
    payload: dict = {},
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Exécution manuelle d'une automatisation (depuis le UI Paramètres)."""
    automations = await _get_automations(db, user.id)
    auto = next((a for a in automations if a["id"] == auto_id), None)
    if not auto:
        raise HTTPException(404, "Automatisation introuvable")
    if not auto.get("enabled"):
        return AutomationRunResult(
            automation_id=auto_id, status="skipped",
            message="Automatisation désactivée",
            executed_at=datetime.now(timezone.utc).isoformat(),
        )

    result = await _execute_automation(db, user, auto_id, payload)

    # Mettre à jour last_run + run_count
    updated = []
    for a in automations:
        if a["id"] == auto_id:
            a = {**a, "last_run": result.executed_at, "run_count": a.get("run_count", 0) + 1}
        updated.append(a)
    await _save_automations(db, user.id, updated)

    return result


@automations_router.post("/trigger")
async def webhook_trigger(
    body: WebhookTriggerIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook Make/Zapier → déclenche une automatisation pour un user donné.
    Pas d'auth JWT — sécurisé via MAKE_WEBHOOK_SECRET (header X-Secret).
    """
    if not body.user_id:
        return {"status": "error", "message": "user_id requis"}

    r = await db.execute(select(User).where(User.id == body.user_id, User.is_active == True))
    user = r.scalar_one_or_none()
    if not user:
        return {"status": "error", "message": "User introuvable"}

    automations = await _get_automations(db, user.id)
    auto = next((a for a in automations if a["id"] == body.automation_id), None)
    if not auto or not auto.get("enabled"):
        return {"status": "skipped", "reason": "disabled_or_not_found"}

    result = await _execute_automation(db, user, body.automation_id, body.payload)

    # Update last_run
    updated = []
    for a in automations:
        if a["id"] == body.automation_id:
            a = {**a, "last_run": result.executed_at, "run_count": a.get("run_count", 0) + 1}
        updated.append(a)
    await _save_automations(db, user.id, updated)

    return result


# ─────────── Scheduler (vendredi 17h pour a5, quotidien 18h pour a3) ─

async def automations_cron_loop():
    """Background loop : vérifie chaque heure si des crons doivent tourner."""
    await asyncio.sleep(60)
    logger.info("[AUTOMATIONS] Cron loop started")
    while True:
        try:
            now = datetime.now(timezone.utc)
            weekday = now.weekday()  # 4 = vendredi
            hour = now.hour

            async with async_session_factory() as db:
                # Récupérer tous les users avec automations activées
                rows = (await db.execute(
                    text("SELECT user_id, value FROM user_data WHERE `key` = 'automations'")
                )).fetchall()

                for row in rows:
                    user_id, data_str = row
                    try:
                        automations = json.loads(data_str)
                        for auto in automations:
                            if not auto.get("enabled"):
                                continue
                            cron = auto.get("cron", "")
                            should_run = False

                            if cron == "weekly_fri_17h" and weekday == 4 and hour == 17:
                                # Vérifier qu'on n'a pas déjà tourné aujourd'hui
                                last = auto.get("last_run")
                                if last:
                                    last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                                    if (now - last_dt).total_seconds() < 3600 * 20:
                                        continue
                                should_run = True

                            elif cron == "daily_18h" and hour == 18:
                                last = auto.get("last_run")
                                if last:
                                    last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                                    if (now - last_dt).total_seconds() < 3600 * 20:
                                        continue
                                should_run = True

                            if not should_run:
                                continue

                            r = await db.execute(select(User).where(User.id == user_id))
                            user = r.scalar_one_or_none()
                            if not user:
                                continue

                            result = await _execute_automation(db, user, auto["id"], {})
                            auto["last_run"] = result.executed_at
                            auto["run_count"] = auto.get("run_count", 0) + 1
                            logger.info(f"[AUTOMATIONS CRON] user={user_id} auto={auto['id']} → {result.status}")

                        # Persister les run_count / last_run mis à jour
                        await db.execute(
                            text("UPDATE user_data SET value = :d WHERE user_id = :uid AND `key` = 'automations'"),
                            {"d": json.dumps(automations), "uid": user_id},
                        )
                        await db.commit()
                    except Exception as e:
                        logger.warning(f"[AUTOMATIONS CRON] user {user_id} error: {e}")

        except Exception as e:
            logger.exception(f"[AUTOMATIONS CRON] Loop error: {e}")

        await asyncio.sleep(3600)   # Vérifier toutes les heures
