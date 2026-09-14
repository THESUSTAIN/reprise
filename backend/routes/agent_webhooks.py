"""Agent Webhook Router — Public endpoints for Telegram/WhatsApp/Web to talk to deployed agents."""
import os
import json
import hmac
import hashlib
import asyncio
import logging
import httpx
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from fastapi import Depends
from models import CustomAgent, User, AgentMessage

logger = logging.getLogger(__name__)

agent_webhook_router = APIRouter(prefix="/agent-webhook", tags=["Agent Webhooks"])


def _verify_wa_signature(raw_body: bytes, signature_header: str, app_secret: str) -> bool:
    """Valide la signature Meta X-Hub-Signature-256 (HMAC-SHA256, app secret).
    Retourne True si pas d'app_secret configure (mode dev — l'appelant doit logger un warning)."""
    if not app_secret:
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.split("=", 1)[1])


async def _get_agent_by_token(token: str, db: AsyncSession) -> CustomAgent:
    result = await db.execute(select(CustomAgent).where(CustomAgent.webhook_token == token))
    agent = result.scalar_one_or_none()
    if not agent or not agent.is_active:
        raise HTTPException(404, "Agent not found or inactive")
    return agent


async def _agent_respond(
    agent: CustomAgent,
    user: User,
    message: str,
    db: AsyncSession,
    contact: str | None = None,
    channel: str = "test",
) -> str:
    """Generate agent response using Mammoth IA API (unified Claude/GPT/Gemini).

    `contact` identifie le client externe (numéro WhatsApp, chat_id Telegram,
    session_id du widget web) — chaque contact a son propre fil de conversation.
    `contact=None` = conversation de test du propriétaire dans l'app (comportement historique).
    """
    # Utilise MAMMOTH_API_KEY (la clé unifiée du projet Zayado)
    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        # Fallback sur ANTHROPIC_API_KEY si configurée
        mammoth_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not mammoth_key:
        logger.error("[agent_respond] MAMMOTH_API_KEY absente des variables Railway !")
        return "Service IA non configuré. Vérifiez les variables MAMMOTH_API_KEY dans Railway."
    else:
        logger.info(f"[agent_respond] Clé Mammoth présente ({len(mammoth_key)} chars), modèle: {agent.model or 'claude-haiku-4-5-20251001'}")

    MAMMOTH_BASE_URL = os.environ.get("MAMMOTH_BASE_URL", "https://api.mammouth.ai/v1")

    system = agent.system_prompt or "Tu es un assistant IA utile et professionnel."
    system += "\n\nTu reponds de maniere concise et utile. Reponds sans markdown excessif (pas de **bold**, pas de #headers)."

    # Load last 10 messages for context — isolé par contact (chaque client externe a son propre fil)
    history_q = select(AgentMessage).where(AgentMessage.agent_id == agent.id)
    if contact:
        history_q = history_q.where(AgentMessage.contact == contact)
    else:
        history_q = history_q.where(AgentMessage.contact.is_(None))
    history = await db.execute(history_q.order_by(AgentMessage.created_at.desc()).limit(10))
    msgs = list(reversed(list(history.scalars().all())))

    messages = []
    for m in msgs:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": message})

    # Mammoth utilise le format OpenAI (/v1/chat/completions)
    # Le system prompt est mis en premier message avec role="system"
    openai_messages = [{"role": "system", "content": system}] + messages
    model = agent.model or "claude-haiku-4-5-20251001"

    reply = None
    last_error_reply = "Erreur temporaire. Réessayez dans quelques instants."
    max_attempts = 2  # 1 essai + 1 retry sur erreur transitoire (timeout / réseau / 5xx)

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.mammouth.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {mammoth_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": openai_messages,
                        "max_tokens": agent.max_tokens or 1024,
                        "stream": False
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if not reply:
                        reply = "Je n'ai pas pu générer de réponse. Réessayez."
                    break  # succès — on sort de la boucle de retry

                error_body = resp.text[:500]
                logger.error(f"[agent_respond] Mammoth HTTP {resp.status_code} (essai {attempt}/{max_attempts}): {error_body}")
                if resp.status_code == 401:
                    reply = "Clé API invalide. Contactez le support Zayado."
                    break  # non transitoire — inutile de retenter
                elif resp.status_code == 429:
                    last_error_reply = "Trop de requêtes. Attendez quelques secondes et réessayez."
                elif resp.status_code >= 500:
                    last_error_reply = "Le service IA est momentanément surchargé. Réessayez dans 30 secondes."
                else:
                    reply = f"Erreur API ({resp.status_code}). Réessayez dans quelques instants."
                    break  # 4xx non transitoire — inutile de retenter

        except httpx.TimeoutException:
            logger.error(f"[agent_respond] Timeout après 60s sur Mammoth API (essai {attempt}/{max_attempts})")
            last_error_reply = "Je mets trop de temps à répondre. Réessayez dans un instant."
        except httpx.ConnectError as e:
            logger.error(f"[agent_respond] Connexion Mammoth impossible (essai {attempt}/{max_attempts}): {e}")
            last_error_reply = "Service IA momentanément indisponible. Réessayez dans 30 secondes."
        except Exception as e:
            logger.error(f"[agent_respond] Erreur inattendue (essai {attempt}/{max_attempts}): {type(e).__name__}: {e}")
            last_error_reply = "Erreur temporaire. Réessayez dans quelques instants."

        if attempt < max_attempts:
            await asyncio.sleep(1.5 * attempt)  # backoff court avant retry

    if reply is None:
        reply = last_error_reply

    # Save messages — tagués par contact/canal pour l'écran de gestion des conversations
    db.add(AgentMessage(agent_id=agent.id, user_id=user.id, role="user", content=message, contact=contact, channel=channel))
    db.add(AgentMessage(agent_id=agent.id, user_id=user.id, role="assistant", content=reply, contact=contact, channel=channel))
    agent.usage_count = (agent.usage_count or 0) + 1
    await db.commit()

    return reply


@agent_webhook_router.post("/{token}/telegram")
async def telegram_webhook(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Receive Telegram messages and respond via the deployed agent."""
    agent = await _get_agent_by_token(token, db)

    body = await request.json()
    msg = body.get("message", {})
    text = msg.get("text", "")
    chat_id = msg.get("chat", {}).get("id")
    from_user = msg.get("from", {})

    if not text or not chat_id:
        return {"ok": True}

    # Skip /start command
    if text.strip() == "/start":
        text = "Bonjour, comment puis-je vous aider ?"

    # Find or get the agent owner
    owner = await db.execute(select(User).where(User.id == agent.user_id))
    user = owner.scalar_one_or_none()
    if not user:
        return {"ok": True}

    reply = await _agent_respond(agent, user, text, db, contact=str(chat_id), channel="telegram")

    # Send reply via Telegram
    from routes.connections import _decrypt
    from models import UserConnection
    conn_result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == agent.user_id, UserConnection.provider == "telegram")
    )
    tg_conn = conn_result.scalar_one_or_none()
    if tg_conn:
        creds = json.loads(_decrypt(tg_conn.credentials)) if tg_conn.credentials else {}
        bot_token = creds.get("bot_token", "")
        if bot_token:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": chat_id, "text": reply, "parse_mode": "Markdown"}
                    )
            except Exception as e:
                logger.error(f"Telegram send error: {e}")

    return {"ok": True}


@agent_webhook_router.get("/{token}/telegram")
async def telegram_webhook_verify(token: str, db: AsyncSession = Depends(get_db)):
    """Telegram webhook verification."""
    await _get_agent_by_token(token, db)
    return {"ok": True}


@agent_webhook_router.post("/{token}/whatsapp")
async def whatsapp_webhook(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Receive WhatsApp messages via Meta Cloud API and respond."""
    agent = await _get_agent_by_token(token, db)

    raw_body = await request.body()

    # Récupérer l'App Secret Meta configuré pour cet agent (connexion WhatsApp),
    # ou à défaut la variable d'environnement globale WA_APP_SECRET.
    from models import UserConnection
    from routes.connections import _decrypt
    conn_result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == agent.user_id, UserConnection.provider == "whatsapp")
    )
    wa_conn = conn_result.scalar_one_or_none()
    app_secret = ""
    if wa_conn and wa_conn.credentials:
        try:
            app_secret = json.loads(_decrypt(wa_conn.credentials)).get("app_secret", "")
        except Exception:
            pass
    if not app_secret:
        app_secret = os.environ.get("WA_APP_SECRET", "")

    signature = request.headers.get("x-hub-signature-256", "")
    if app_secret:
        if not _verify_wa_signature(raw_body, signature, app_secret):
            logger.warning(f"[WA] Signature invalide pour agent {agent.id} — requete rejetee")
            raise HTTPException(403, "Signature invalide")
    else:
        logger.warning(f"[WA] Aucun app_secret configure pour agent {agent.id} — signature webhook NON verifiee (mode dev)")

    try:
        body = json.loads(raw_body)
    except Exception:
        raise HTTPException(400, "JSON invalide")

    entries = body.get("entry", [])

    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                text = ""
                if msg.get("type") == "text":
                    text = msg.get("text", {}).get("body", "")
                from_number = msg.get("from", "")

                if not text:
                    continue

                owner = await db.execute(select(User).where(User.id == agent.user_id))
                user = owner.scalar_one_or_none()
                if not user:
                    continue

                reply = await _agent_respond(agent, user, text, db, contact=from_number, channel="whatsapp")

                # Send reply via WhatsApp
                from models import UserConnection
                from routes.connections import _decrypt
                conn_result = await db.execute(
                    select(UserConnection).where(UserConnection.user_id == agent.user_id, UserConnection.provider == "whatsapp")
                )
                wa_conn = conn_result.scalar_one_or_none()
                if wa_conn:
                    creds = json.loads(_decrypt(wa_conn.credentials)) if wa_conn.credentials else {}
                    phone_id = creds.get("phone_number_id", "")
                    access_token = creds.get("access_token", "")
                    if phone_id and access_token:
                        try:
                            async with httpx.AsyncClient() as client:
                                await client.post(
                                    f"https://graph.facebook.com/v18.0/{phone_id}/messages",
                                    headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                                    json={"messaging_product": "whatsapp", "to": from_number, "type": "text", "text": {"body": reply}}
                                )
                        except Exception as e:
                            logger.error(f"WhatsApp send error: {e}")

    return {"ok": True}


@agent_webhook_router.get("/{token}/whatsapp")
async def whatsapp_webhook_verify(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """WhatsApp Cloud API webhook verification (hub.challenge response)."""
    mode = request.query_params.get("hub.mode")
    verify_token_param = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Récupérer le verify_token attendu depuis les credentials de l'agent
    try:
        agent = await _get_agent_by_token(token, db)
        from models import UserConnection
        from routes.connections import _decrypt
        conn_result = await db.execute(
            select(UserConnection).where(
                UserConnection.user_id == agent.user_id,
                UserConnection.provider == "whatsapp"
            )
        )
        wa_conn = conn_result.scalar_one_or_none()
        expected_verify = "zayado_wa_webhook_2026"  # Default fallback
        if wa_conn and wa_conn.credentials:
            creds = json.loads(_decrypt(wa_conn.credentials))
            expected_verify = creds.get("verify_token", expected_verify)
    except Exception:
        expected_verify = "zayado_wa_webhook_2026"

    if mode == "subscribe" and challenge:
        if verify_token_param == expected_verify:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(challenge)
        else:
            raise HTTPException(403, "Verify token invalide")
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════
# WhatsApp Web QR — Routes pour le microservice whatsapp-web.js
# ═══════════════════════════════════════════════════════════════

@agent_webhook_router.post("/{token}/whatsapp-web")
async def whatsapp_web_message(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Receive messages from the WhatsApp Web microservice and respond via the agent."""
    # Vérifier le secret de service
    service_secret = os.environ.get("WA_SERVICE_SECRET", "")
    if service_secret:
        req_secret = request.headers.get("x-service-secret", "")
        if req_secret != service_secret:
            raise HTTPException(401, "Non autorisé")

    agent = await _get_agent_by_token(token, db)
    body = await request.json()
    
    from_number = body.get("from", "")
    message = body.get("message", "")
    
    if not message or not from_number:
        return {"ok": True}

    # Récupérer le propriétaire de l'agent
    owner = await db.execute(select(User).where(User.id == agent.user_id))
    user = owner.scalar_one_or_none()
    if not user:
        return {"reply": "Agent non disponible."}

    # Générer la réponse via l'agent IA
    reply = await _agent_respond(agent, user, message, db, contact=from_number, channel="whatsapp_web")
    
    return {"reply": reply}


@agent_webhook_router.post("/{token}/whatsapp-web-ready")
async def whatsapp_web_session_ready(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Called by the WhatsApp Web service when a session becomes active."""
    service_secret = os.environ.get("WA_SERVICE_SECRET", "")
    if service_secret:
        req_secret = request.headers.get("x-service-secret", "")
        if req_secret != service_secret:
            raise HTTPException(401, "Non autorisé")

    body = await request.json()
    agent_id = body.get("agent_id")
    phone_number = body.get("phone_number")
    
    if agent_id:
        # Mettre à jour les canaux déployés de l'agent
        result = await db.execute(select(CustomAgent).where(CustomAgent.id == agent_id))
        agent = result.scalar_one_or_none()
        if agent:
            channels = list(agent.deployed_channels or [])
            if "whatsapp_web" not in channels:
                channels.append("whatsapp_web")
            agent.deployed_channels = channels
            await db.commit()
    
    logger.info(f"WhatsApp Web session ready — agent {agent_id}, phone {phone_number}")
    return {"ok": True}


# ── Public Chat Page (QR code target) ──
from fastapi.responses import HTMLResponse

@agent_webhook_router.get("/{token}/chat", response_class=HTMLResponse)
async def agent_chat_page(token: str, db: AsyncSession = Depends(get_db)):
    """Serve a mobile-friendly chat page for the agent (QR code landing)."""
    agent = await _get_agent_by_token(token, db)
    base_url = os.environ.get('APP_BASE_URL', 'https://app.zayado.net')
    api_url = f"{base_url}/api/agent-webhook/{token}/message"
    color = agent.color or '#1D4E8A'
    name = agent.name or 'Agent IA'
    avatar = agent.avatar or ''
    desc = agent.description or 'Posez-moi vos questions'

    return f"""<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{name} — Zayado</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'DM Sans',system-ui,sans-serif;background:#f8f9fa;height:100dvh;display:flex;flex-direction:column}}
.ch-header{{background:{color};color:white;padding:1rem 1.25rem;display:flex;align-items:center;gap:.75rem;flex-shrink:0}}
.ch-avatar{{width:2.5rem;height:2.5rem;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:700}}
.ch-name{{font-weight:700;font-size:1rem}}
.ch-desc{{font-size:.7rem;opacity:.7}}
.ch-messages{{flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:.625rem}}
.ch-msg{{max-width:82%;padding:.7rem 1rem;border-radius:1rem;font-size:.875rem;line-height:1.5;word-wrap:break-word}}
.ch-msg.bot{{background:white;border:1px solid #e5e7eb;border-bottom-left-radius:.25rem;align-self:flex-start}}
.ch-msg.user{{background:{color};color:white;border-bottom-right-radius:.25rem;align-self:flex-end}}
.ch-msg.typing{{color:#9ca3af;font-style:italic}}
.ch-input-bar{{display:flex;gap:.5rem;padding:.75rem 1rem;background:white;border-top:1px solid #e5e7eb;flex-shrink:0}}
.ch-input{{flex:1;border:1.5px solid #e5e7eb;border-radius:1.5rem;padding:.65rem 1rem;font-size:.875rem;outline:none;font-family:inherit}}
.ch-input:focus{{border-color:{color}}}
.ch-send{{width:2.5rem;height:2.5rem;border-radius:50%;background:{color};color:white;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.ch-send:disabled{{opacity:.4}}
.ch-badge{{text-align:center;padding:.5rem;font-size:.6rem;color:#9ca3af}}
.ch-badge a{{color:#9ca3af;text-decoration:none}}
</style></head><body>
<div class="ch-header">
  <div class="ch-avatar">{avatar if avatar and len(avatar)<3 else name[0].upper()}</div>
  <div><div class="ch-name">{name}</div><div class="ch-desc">{desc}</div></div>
</div>
<div class="ch-messages" id="msgs">
  <div class="ch-msg bot">Bonjour ! Je suis <strong>{name}</strong>. Comment puis-je vous aider ?</div>
</div>
<div class="ch-input-bar">
  <input class="ch-input" id="inp" placeholder="Ecrivez votre message..." autocomplete="off" enterkeyhint="send">
  <button class="ch-send" id="sendBtn" onclick="send()">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2 11 13"/><path d="M22 2 15 22 11 13 2 9z"/></svg>
  </button>
</div>
<div class="ch-badge">Propulse par <a href="https://zayado.net" target="_blank">Extension IA by Zayado</a></div>
<script>
var API='{api_url}',msgs=document.getElementById('msgs'),inp=document.getElementById('inp'),btn=document.getElementById('sendBtn'),sid='s_'+Math.random().toString(36).slice(2);
function addMsg(text,role){{var d=document.createElement('div');d.className='ch-msg '+role;d.innerHTML=text;msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight;return d;}}
async function send(){{
  var t=inp.value.trim();if(!t)return;
  inp.value='';btn.disabled=true;
  addMsg(t,'user');
  var typing=addMsg('...','bot typing');
  try{{
    var r=await fetch(API,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{message:t,session_id:sid}})}});
    var d=await r.json();
    typing.remove();
    addMsg(d.reply||d.message||'Erreur','bot');
  }}catch(e){{typing.remove();addMsg('Erreur de connexion','bot');}}
  btn.disabled=false;inp.focus();
}}
inp.addEventListener('keydown',function(e){{if(e.key==='Enter')send();}});
</script></body></html>"""


@agent_webhook_router.post("/{token}/message")
async def agent_public_message(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Handle a public chat message from the web chat page."""
    agent = await _get_agent_by_token(token, db)
    body = await request.json()
    message = body.get("message", "").strip()
    session_id = (body.get("session_id") or "").strip() or "web_anonyme"
    if not message:
        return {"reply": "Message vide."}

    # Use agent owner for credit deduction
    owner_result = await db.execute(select(User).where(User.id == agent.user_id))
    user = owner_result.scalar_one_or_none()
    if not user:
        return {"reply": "Agent non configure."}

    reply = await _agent_respond(agent, user, message, db, contact=session_id, channel="web")
    return {"reply": reply}
