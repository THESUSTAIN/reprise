"""
Zayado — WhatsApp Cloud API Global Webhook
==========================================
Un seul numéro WhatsApp Business partagé.
Les agents sont liés aux utilisateurs via un code d'accès unique.
"""
import os
import re
import json
import hmac
import hashlib
import random
import string
import httpx
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from database import get_db
from models import CustomAgent, AgentMessage, User

logger = logging.getLogger(__name__)

wa_router = APIRouter(prefix="/webhooks", tags=["whatsapp-global"])

# ── Config Meta WhatsApp Cloud API ──────────────────────────────────────────
WA_PHONE_NUMBER_ID = os.environ.get("WA_PHONE_NUMBER_ID", "890062737519503")
WA_ACCESS_TOKEN    = os.environ.get("WA_ACCESS_TOKEN", "")
WA_VERIFY_TOKEN    = os.environ.get("WA_VERIFY_TOKEN", "zayado_wa_webhook_2026")
MAMMOTH_BASE_URL   = os.environ.get("MAMMOTH_BASE_URL", "https://api.mammouth.ai/v1")
MAMMOTH_API_KEY    = os.environ.get("MAMMOTH_API_KEY", "")
# App Secret Meta — pour valider la signature X-Hub-Signature-256 des webhooks.
WA_APP_SECRET      = os.environ.get("WA_APP_SECRET", "")

# ── Mapping en mémoire : phone_number → agent_id ────────────────────────────
# Persisté aussi dans la DB via les settings de l'agent
_phone_sessions: dict = {}  # { "33612345678": "agent_uuid" }

# Déduplication des webhooks (Meta renvoie en cas d'échec) — cache borné.
_processed_msg_ids: dict = {}   # message_id -> timestamp
_DEDUP_MAX = 500


def _dedup_seen(msg_id: str) -> bool:
    """True si le message a déjà été traité (évite le double traitement)."""
    if not msg_id:
        return False
    if msg_id in _processed_msg_ids:
        return True
    _processed_msg_ids[msg_id] = datetime.now(timezone.utc).timestamp()
    if len(_processed_msg_ids) > _DEDUP_MAX:
        # purge des plus anciens
        for k in sorted(_processed_msg_ids, key=_processed_msg_ids.get)[:100]:
            _processed_msg_ids.pop(k, None)
    return False


def _verify_signature(raw_body: bytes, header: str) -> bool:
    """Valide la signature Meta X-Hub-Signature-256 (HMAC-SHA256, app secret)."""
    if not WA_APP_SECRET:
        # Pas d'app secret configuré → on ne peut pas vérifier (mode dev).
        logger.warning("[WA] WA_APP_SECRET absent — signature webhook NON vérifiée")
        return True
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(WA_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.split("=", 1)[1])


def _gen_access_code() -> str:
    """Génère un code style TKXG-2416."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    digits  = ''.join(random.choices(string.digits, k=4))
    return f"{letters}-{digits}"


async def _send_wa_message(to: str, text: str):
    """Envoyer un message WhatsApp via Cloud API."""
    if not WA_ACCESS_TOKEN:
        logger.warning("[WA] WA_ACCESS_TOKEN non configuré — impossible d'envoyer")
        return
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"https://graph.facebook.com/v18.0/{WA_PHONE_NUMBER_ID}/messages",
                headers={"Authorization": f"Bearer {WA_ACCESS_TOKEN}", "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"body": text, "preview_url": False}
                }
            )
            if r.status_code != 200:
                logger.error(f"[WA] Erreur envoi {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.error(f"[WA] Exception envoi: {e}")


async def _agent_respond_wa(agent: "CustomAgent", user: "User", message: str, db: AsyncSession) -> str:
    """Générer une réponse via Mammoth IA."""
    if not MAMMOTH_API_KEY:
        return "Service IA non configuré. Contactez le support."

    system = agent.system_prompt or "Tu es un assistant IA utile et professionnel."
    system += "\n\nRéponds de façon concise. Tu es sur WhatsApp — pas de markdown excessif."

    history = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.agent_id == agent.id, AgentMessage.user_id == user.id)
        .order_by(AgentMessage.created_at.desc())
        .limit(8)
    )
    msgs = list(reversed(list(history.scalars().all())))
    messages = [{"role": "system", "content": system}]
    for m in msgs:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                "https://api.mammouth.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {MAMMOTH_API_KEY}", "Content-Type": "application/json"},
                json={"model": agent.model or "claude-haiku-4-5-20251001", "messages": messages, "max_tokens": 800, "stream": False}
            )
            if resp.status_code == 200:
                reply = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                if not reply: reply = "Je n'ai pas pu générer de réponse."
            else:
                logger.error(f"[WA] Mammoth error {resp.status_code}: {resp.text[:200]}")
                reply = "Erreur temporaire. Réessayez dans un instant."
    except Exception as e:
        logger.error(f"[WA] IA error: {e}")
        reply = "Erreur temporaire du service IA."

    db.add(AgentMessage(agent_id=agent.id, user_id=user.id, role="user", content=message))
    db.add(AgentMessage(agent_id=agent.id, user_id=user.id, role="assistant", content=reply))
    agent.usage_count = (agent.usage_count or 0) + 1
    await db.commit()
    return reply


# ── Vérification webhook Meta ────────────────────────────────────────────────
@wa_router.get("/whatsapp")
async def verify_webhook(request: Request):
    mode      = request.query_params.get("hub.mode")
    token     = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == WA_VERIFY_TOKEN and challenge:
        logger.info("[WA] Webhook vérifié par Meta ✓")
        return PlainTextResponse(challenge)
    raise HTTPException(403, "Verify token invalide")


# ── Réception des messages ────────────────────────────────────────────────────
@wa_router.post("/whatsapp")
async def receive_message(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Webhook global WhatsApp — reçoit tous les messages du numéro central.
    Route les messages vers l'agent selon le code d'accès ou la session active.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "JSON invalide")

    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                from_number = msg.get("from", "")   # ex: "33612345678"
                text = msg.get("text", {}).get("body", "").strip()
                if not text or not from_number:
                    continue

                await _process_message(from_number, text, db)

    return {"ok": True}


async def _process_message(from_number: str, text: str, db: AsyncSession):
    """Traiter un message entrant : pairing ou conversation."""
    
    # 1. Détecter si c'est un code d'accès
    code_match = re.search(
        r'(?:extension IA code is|extension ia code is|access code is|code[:\s]+)\s*([A-Z]{4}-\d{4})',
        text,
        re.IGNORECASE
    )
    
    if code_match:
        access_code = code_match.group(1).upper()
        await _handle_access_code(from_number, access_code, db)
        return

    # 2. Chercher la session active pour ce numéro
    agent_id = _phone_sessions.get(from_number)
    
    if not agent_id:
        # Chercher en DB (sessions persistées dans les settings de l'agent)
        agents_result = await db.execute(
            select(CustomAgent).where(
                CustomAgent.is_active == True
            )
        )
        for a in agents_result.scalars().all():
            settings = getattr(a, 'settings', {}) or {}
            linked = settings.get('wa_linked_phones', [])
            if from_number in linked:
                agent_id = a.id
                _phone_sessions[from_number] = agent_id
                break

    if not agent_id:
        # Numéro inconnu → demander le code
        await _send_wa_message(
            from_number,
            "👋 Bonjour ! Pour parler à un agent IA, veuillez entrer votre code d'accès.\n\n"
            "Exemple : *Hey, my extension IA code is XXXX-0000*\n\n"
            "Vous trouverez votre code dans l'application Zayado → vos agents → Déployer."
        )
        return

    # 3. Récupérer l'agent et son propriétaire
    agent_result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == agent_id, CustomAgent.is_active == True)
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        _phone_sessions.pop(from_number, None)
        return

    owner_result = await db.execute(select(User).where(User.id == agent.user_id))
    user = owner_result.scalar_one_or_none()
    if not user:
        return

    # 4. Générer la réponse
    reply = await _agent_respond_wa(agent, user, text, db)
    await _send_wa_message(from_number, reply)


async def _handle_access_code(from_number: str, access_code: str, db: AsyncSession):
    """Lier un numéro WhatsApp à un agent via son code d'accès."""
    # Chercher l'agent avec ce code
    agents_result = await db.execute(select(CustomAgent).where(CustomAgent.is_active == True))
    agent = None
    for a in agents_result.scalars().all():
        if a.webhook_token:
            # Le code est stocké dans les settings ou dans webhook_token
            settings = {}
            try:
                # Chercher dans deployed_channels settings
                if hasattr(a, 'settings') and isinstance(a.settings, dict):
                    settings = a.settings
            except Exception:
                pass
            
            # Le code d'accès est généré à partir des 8 premiers chars du webhook_token
            token_code = a.webhook_token[:8].upper() if a.webhook_token else ""
            # Format XXXX-XXXX depuis les 8 premiers chars
            if len(token_code) >= 8:
                formatted = f"{token_code[:4]}-{token_code[4:8]}"
                if formatted == access_code:
                    agent = a
                    break
            
            # Aussi vérifier wa_access_code dans settings
            wa_code = settings.get("wa_access_code", "")
            if wa_code and wa_code == access_code:
                agent = a
                break

    if not agent:
        await _send_wa_message(
            from_number,
            "❌ Code d'accès invalide ou expiré.\n\nVérifiez votre code dans l'application Zayado."
        )
        return

    # Lier le numéro à l'agent
    _phone_sessions[from_number] = agent.id
    
    # Persister dans les settings de l'agent
    try:
        linked = []
        if hasattr(agent, 'settings') and isinstance(agent.settings, dict):
            linked = agent.settings.get('wa_linked_phones', [])
        if from_number not in linked:
            linked.append(from_number)
        settings = agent.settings or {}
        settings['wa_linked_phones'] = linked
        await db.execute(
            update(CustomAgent)
            .where(CustomAgent.id == agent.id)
            .values(settings=settings)
        )
        await db.commit()
    except Exception as e:
        logger.warning(f"[WA] Erreur persistance session: {e}")

    # Récupérer le propriétaire pour le message de bienvenue
    owner_result = await db.execute(select(User).where(User.id == agent.user_id))
    user = owner_result.scalar_one_or_none()

    greeting = agent.system_prompt.split('\n')[0][:100] if agent.system_prompt else ""
    await _send_wa_message(
        from_number,
        f"✅ Connecté à **{agent.name}** !\n\n"
        f"{greeting}\n\n"
        f"Posez-moi votre première question 👇"
    )
