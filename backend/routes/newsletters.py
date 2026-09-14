"""
Newsletter Pipeline : Brevo Inbound Parse → IA reformulation (ton Zayado) → Brouillons Brevo.

Flux :
  1. Email externe arrive sur newsletter@inbox.zayado.net (via Brevo Inbound Parse)
  2. Brevo POST JSON sur /api/inbound/brevo → IncomingNewsletter stocké
  3. IA (Claude Sonnet via Emergent LLM key) reformule au ton Zayado + niche TPE/freelance
  4. PreparedNewsletter créé (status=draft)
  5. Admin review → validate/edit → push vers Brevo en tant que brouillon (Templates)
"""
import os
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from deps import get_current_user, User
from models import IncomingNewsletter, PreparedNewsletter

logger = logging.getLogger(__name__)

newsletters_router = APIRouter(tags=["Newsletters"])
INBOUND_SECRET = os.environ.get("BREVO_INBOUND_SECRET", "")  # optionnel, pour signer le webhook


# ─── Webhook Brevo Inbound Parse ───────────────────────────────────────────
@newsletters_router.post("/inbound/brevo")
async def brevo_inbound_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Reçoit les emails entrants depuis Brevo Inbound Parse.
    Format: https://developers.brevo.com/docs/inbound-parse-webhooks
    """
    # Auth optionnelle via token dans l'URL query string
    if INBOUND_SECRET:
        if request.query_params.get("token") != INBOUND_SECRET:
            raise HTTPException(401, "Token inbound invalide")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Payload JSON invalide")

    items = payload.get("items") if isinstance(payload, dict) else None
    if not items and isinstance(payload, dict):
        items = [payload]  # Brevo peut envoyer un objet unique
    if not items:
        return {"ok": True, "stored": 0}

    stored_ids = []
    for item in items:
        try:
            sender = (item.get("From") or {})
            sender_email = sender.get("Address") or item.get("Sender") or ""
            sender_name  = sender.get("Name") or ""
            to_list = item.get("To") or []
            received_to = to_list[0].get("Address") if to_list and isinstance(to_list[0], dict) else ""

            nl = IncomingNewsletter(
                id=secrets.token_urlsafe(16),
                sender_email=sender_email[:255],
                sender_name=sender_name[:255] if sender_name else None,
                subject=(item.get("Subject") or "")[:500],
                received_to=received_to[:255],
                html_body=item.get("RawHtmlBody") or item.get("HtmlBody") or "",
                text_body=item.get("RawTextBody") or item.get("TextBody") or "",
                raw_headers=json.dumps(item.get("Headers") or {}),
                received_at=datetime.now(timezone.utc),
                status="received",
            )
            db.add(nl)
            stored_ids.append(nl.id)
        except Exception as e:
            logger.exception("Failed to store inbound newsletter: %s", e)
            continue

    await db.commit()

    # Déclenche la reformulation async (non-bloquant)
    import asyncio
    for nid in stored_ids:
        asyncio.create_task(_process_newsletter(nid))

    return {"ok": True, "stored": len(stored_ids)}


# ─── IA Reformulation (ton Zayado) ─────────────────────────────────────────
ZAYADO_SYSTEM_PROMPT = """Tu es l'éditeur en chef de la newsletter Zayado — une IA SaaS B2B pour TPE, indépendants et freelances francophones.

Ton rôle : transformer une newsletter externe (reçue dans notre boîte) en une version Zayado originale, ciblée pour notre audience.

TON ÉDITORIAL ZAYADO :
- Français clair, chaleureux, tutoiement
- Concret et actionnable (exemples TPE, freelance, KBIS, Urssaf)
- Bref, pas de blabla marketing
- Zéro jargon anglais sauf si nécessaire
- Met toujours en avant un conseil pratique ou une implication pour un indépendant

RÈGLES ABSOLUES :
- Ne copie jamais mot pour mot la source (on reformule tout)
- Pas de mention de la source ni de l'émetteur original
- Sujet : 60 caractères max, accrocheur, sans clickbait
- Corps : 150-250 mots, HTML simple (<p>, <strong>, <ul>, <li>, <a>), pas de CSS inline

SORTIE JSON STRICTE (aucun markdown autour) :
{
  "subject": "…",
  "summary": "… (2 lignes max, pour la liste admin)",
  "html": "<p>…</p>...",
  "text": "version texte brut"
}"""


async def _process_newsletter(incoming_id: str):
    """Appelle l'IA pour reformuler une newsletter entrante. Tâche async non-bloquante.

    Utilise Mammoth IA en primaire, fallback_api (admin_config.json) en secours.
    """
    from database import async_session
    from utils import load_admin_config
    import httpx

    async with async_session() as db:
        try:
            result = await db.execute(select(IncomingNewsletter).where(IncomingNewsletter.id == incoming_id))
            inc = result.scalar_one_or_none()
            if not inc:
                return
            inc.status = "processing"
            await db.commit()

            # Tronque les corps trop longs (limite LLM)
            src_text = (inc.text_body or "")[:6000]
            src_html = (inc.html_body or "")[:4000] if not src_text else ""
            user_msg = f"""Voici une newsletter externe reçue dans notre boîte. Reformule-la pour Zayado en suivant les règles du système.

SUJET SOURCE : {inc.subject or '(sans sujet)'}

CONTENU SOURCE :
{src_text or src_html or '(vide)'}

Réponds UNIQUEMENT avec le JSON demandé, sans texte autour."""

            messages = [
                {"role": "system", "content": ZAYADO_SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ]

            # Essai 1 : Mammouth IA (Claude Sonnet 4.5)
            mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
            mammoth_url = os.environ.get("MAMMOTH_BASE_URL", "https://api.mammouth.ai/v1")
            reply = ""
            error_primary = ""
            if mammoth_key:
                try:
                    async with httpx.AsyncClient(timeout=60) as c:
                        r = await c.post(
                            f"{mammoth_url}/chat/completions",
                            headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                            json={"model": "claude-sonnet-4-5", "messages": messages, "max_tokens": 1800, "temperature": 0.7},
                        )
                    if r.status_code == 200:
                        reply = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    else:
                        error_primary = f"Mammouth {r.status_code}: {r.text[:150]}"
                except Exception as e:
                    error_primary = f"Mammouth exception: {str(e)[:150]}"
            else:
                error_primary = "MAMMOTH_API_KEY manquante"

            # Essai 2 : fallback_api (admin_config.json)
            if not reply:
                fb = load_admin_config().get("fallback_api") or {}
                if fb.get("enabled") and fb.get("api_key"):
                    provider = (fb.get("provider") or "openai").lower()
                    model    = fb.get("model") or "gpt-4o-mini"
                    # URL par provider
                    fb_url_map = {
                        "openai": "https://api.openai.com/v1/chat/completions",
                        "groq":   "https://api.groq.com/openai/v1/chat/completions",
                        "mistral":"https://api.mistral.ai/v1/chat/completions",
                    }
                    fb_url = fb_url_map.get(provider, fb_url_map["openai"])
                    try:
                        async with httpx.AsyncClient(timeout=60) as c:
                            r = await c.post(
                                fb_url,
                                headers={"Authorization": f"Bearer {fb['api_key']}", "Content-Type": "application/json"},
                                json={"model": model, "messages": messages, "max_tokens": 1800, "temperature": 0.7},
                            )
                        if r.status_code == 200:
                            reply = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                        else:
                            logger.error("Fallback API %s error %s: %s", provider, r.status_code, r.text[:200])
                    except Exception as e:
                        logger.error("Fallback API exception: %s", e)

            if not reply:
                inc.status = "failed"
                inc.error = f"Aucun LLM disponible. Primaire: {error_primary}"
                await db.commit()
                return

            # Parser le JSON (tolérant)
            raw = reply.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rsplit("```", 1)[0].strip()
            try:
                data = json.loads(raw)
            except Exception:
                start = raw.find("{")
                end = raw.rfind("}")
                data = json.loads(raw[start:end + 1]) if (start >= 0 and end > start) else {}

            prepared = PreparedNewsletter(
                id=secrets.token_urlsafe(16),
                incoming_id=inc.id,
                source_subject=inc.subject,
                source_sender=inc.sender_email,
                rewritten_subject=(data.get("subject") or "")[:500],
                rewritten_html=data.get("html") or "",
                rewritten_text=data.get("text") or "",
                summary=(data.get("summary") or "")[:500],
                status="draft",
            )
            db.add(prepared)
            inc.status = "prepared"
            await db.commit()
            logger.info("Newsletter %s reformulée avec succès (via Mammouth ou fallback)", incoming_id)
        except Exception as e:
            logger.exception("Erreur reformulation newsletter %s", incoming_id)
            try:
                await db.execute(update(IncomingNewsletter)
                    .where(IncomingNewsletter.id == incoming_id)
                    .values(status="failed", error=str(e)[:500]))
                await db.commit()
            except Exception:
                pass


# ─── ADMIN : liste, détail, modification, push Brevo ───────────────────────

def _is_admin(user: User) -> bool:
    return user.email == "admin@zayado.net" or getattr(user, "is_admin", False)


@newsletters_router.get("/admin/newsletters")
async def list_prepared(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                        status_filter: Optional[str] = None, limit: int = 100):
    """Liste les newsletters préparées (pour la page Admin)."""
    if not _is_admin(user):
        raise HTTPException(403, "Admin requis")
    stmt = select(PreparedNewsletter).order_by(PreparedNewsletter.created_at.desc()).limit(limit)
    if status_filter:
        stmt = stmt.where(PreparedNewsletter.status == status_filter)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [{
        "id": r.id,
        "incoming_id": r.incoming_id,
        "source_subject": r.source_subject,
        "source_sender": r.source_sender,
        "rewritten_subject": r.rewritten_subject,
        "summary": r.summary,
        "status": r.status,
        "brevo_draft_id": r.brevo_draft_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]


@newsletters_router.get("/admin/newsletters/{nid}")
async def get_prepared(nid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not _is_admin(user):
        raise HTTPException(403, "Admin requis")
    r = (await db.execute(select(PreparedNewsletter).where(PreparedNewsletter.id == nid))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Newsletter non trouvée")
    return {
        "id": r.id, "incoming_id": r.incoming_id, "source_subject": r.source_subject,
        "source_sender": r.source_sender, "rewritten_subject": r.rewritten_subject,
        "rewritten_html": r.rewritten_html, "rewritten_text": r.rewritten_text,
        "summary": r.summary, "status": r.status, "brevo_draft_id": r.brevo_draft_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


class PreparedUpdate(BaseModel):
    rewritten_subject: Optional[str] = None
    rewritten_html: Optional[str] = None
    rewritten_text: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None


@newsletters_router.put("/admin/newsletters/{nid}")
async def update_prepared(nid: str, payload: PreparedUpdate,
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not _is_admin(user):
        raise HTTPException(403, "Admin requis")
    r = (await db.execute(select(PreparedNewsletter).where(PreparedNewsletter.id == nid))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Newsletter non trouvée")
    for field, val in payload.dict(exclude_unset=True).items():
        setattr(r, field, val)
    r.reviewed_by = user.id
    r.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True, "id": r.id, "status": r.status}


@newsletters_router.post("/admin/newsletters/{nid}/push-to-brevo")
async def push_to_brevo_draft(nid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Pousse la newsletter comme brouillon de campagne email dans Brevo."""
    if not _is_admin(user):
        raise HTTPException(403, "Admin requis")
    r = (await db.execute(select(PreparedNewsletter).where(PreparedNewsletter.id == nid))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Newsletter non trouvée")
    if not r.rewritten_subject or not r.rewritten_html:
        raise HTTPException(400, "Sujet ou HTML manquant")

    brevo_key = os.environ.get("BREVO_API_KEY", "")
    if not brevo_key:
        raise HTTPException(500, "BREVO_API_KEY non configurée")

    import httpx
    sender_email = os.environ.get("BREVO_SENDER_EMAIL", "newsletter@zayado.net")
    sender_name  = os.environ.get("BREVO_SENDER_NAME", "Zayado")

    try:
        async with httpx.AsyncClient(timeout=20.0) as c:
            resp = await c.post(
                "https://api.brevo.com/v3/emailCampaigns",
                headers={"api-key": brevo_key, "Content-Type": "application/json", "accept": "application/json"},
                json={
                    "name": f"[Zayado] {r.rewritten_subject[:80]}",
                    "subject": r.rewritten_subject,
                    "sender": {"email": sender_email, "name": sender_name},
                    "htmlContent": r.rewritten_html,
                    "type": "classic",
                    # Ne pas planifier : Brevo crée en brouillon par défaut sans scheduledAt
                },
            )
        if resp.status_code not in (200, 201):
            logger.error("Brevo campaign create failed: %s %s", resp.status_code, resp.text[:500])
            raise HTTPException(502, f"Brevo: {resp.status_code} {resp.text[:200]}")
        data = resp.json()
        r.brevo_draft_id = str(data.get("id", ""))
        r.status = "pushed_to_brevo"
        await db.commit()
        return {"ok": True, "brevo_campaign_id": r.brevo_draft_id,
                "brevo_url": f"https://app.brevo.com/camp/template/{r.brevo_draft_id}/message-setup"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Brevo push failed")
        raise HTTPException(500, f"Erreur Brevo: {str(e)[:200]}")


@newsletters_router.delete("/admin/newsletters/{nid}")
async def delete_prepared(nid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not _is_admin(user):
        raise HTTPException(403, "Admin requis")
    r = (await db.execute(select(PreparedNewsletter).where(PreparedNewsletter.id == nid))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Newsletter non trouvée")
    r.status = "rejected"
    await db.commit()
    return {"ok": True}


@newsletters_router.post("/admin/newsletters/{nid}/retry")
async def retry_prepared(nid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Relance la reformulation IA (utile si l'IA a échoué ou ton insuffisant)."""
    if not _is_admin(user):
        raise HTTPException(403, "Admin requis")
    r = (await db.execute(select(PreparedNewsletter).where(PreparedNewsletter.id == nid))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Newsletter non trouvée")
    import asyncio
    asyncio.create_task(_process_newsletter(r.incoming_id))
    return {"ok": True, "incoming_id": r.incoming_id, "message": "Reformulation relancée"}
