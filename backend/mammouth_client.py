"""Client IA — Mammouth (OpenAI-compatible) avec repli automatique sur la clé Emergent.

Mammouth expose plusieurs LLM (Claude, GPT, Gemini, Mistral…) derrière une API
style OpenAI. Si Mammouth échoue (budget dépassé, 429, clé invalide, réseau…),
on bascule automatiquement sur la clé universelle Emergent (emergentintegrations).

Bascule pilotée par AI_PROVIDER :
- "auto" (défaut) : Mammouth d'abord, repli Emergent en cas d'échec.
- "mammouth"      : Mammouth uniquement.
- "emergent"      : Emergent uniquement.
"""
import os
import base64
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

# Support both env var spellings used across the codebase
MAMMOUTH_API_KEY = os.environ.get("MAMMOUTH_API_KEY") or os.environ.get("MAMMOTH_API_KEY", "")
MAMMOUTH_BASE_URL = os.environ.get("MAMMOUTH_BASE_URL", "https://api.mammouth.ai/v1").rstrip("/")
MAMMOUTH_MODEL = os.environ.get("MAMMOUTH_MODEL", "claude-haiku-4-5-20251001")
MAMMOUTH_IMAGE_MODEL = os.environ.get("MAMMOUTH_IMAGE_MODEL", "gemini-3.1-flash-image-preview")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
EMERGENT_TEXT_MODEL = os.environ.get("EMERGENT_TEXT_MODEL", "claude-haiku-4-5-20251001")
EMERGENT_IMAGE_MODEL = os.environ.get("EMERGENT_IMAGE_MODEL", "gemini-3.1-flash-image-preview")

# auto | mammouth | emergent (valeur par défaut via env, surchargée par la config admin)
# Défaut = "mammouth" : Emergent n'est JAMAIS appelé (donc jamais crédité) tant que
# l'admin ne bascule pas explicitement sur "auto" (repli) ou "emergent" dans l'admin.
AI_PROVIDER = os.environ.get("AI_PROVIDER", "mammouth").lower()

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "admin_config.json")

# Anti-spam : n'envoie l'alerte "crédit Mammouth épuisé" qu'une fois toutes les N secondes.
_LAST_ALERT_TS = 0.0
_ALERT_COOLDOWN = float(os.environ.get("LLM_ALERT_COOLDOWN_SECONDS", "3600"))


def _alert_llm_problem(kind: str, detail: str = "") -> None:
    """Prévient l'admin par email quand Mammouth est indisponible (crédit épuisé / clé invalide).
    Throttlé pour éviter le spam. Ne lève jamais d'exception (best-effort)."""
    global _LAST_ALERT_TS
    import time as _time
    now = _time.time()
    if now - _LAST_ALERT_TS < _ALERT_COOLDOWN:
        return
    _LAST_ALERT_TS = now
    try:
        recipient = os.environ.get("LLM_ALERT_EMAIL") or os.environ.get("BREVO_SENDER_EMAIL") or "contact@zayado.net"
        subject = "⚠️ IA Mammouth indisponible — action requise"
        body = f"""<p>Bonjour,</p>
<p>Le fournisseur IA <strong>Mammouth</strong> a renvoyé une erreur : <strong>{kind}</strong>.</p>
<p>Les fonctionnalités IA (copilote, génération, simulation) sont donc <strong>interrompues</strong> jusqu'à résolution.</p>
<ul>
  <li>Vérifiez le solde / la clé Mammouth (MAMMOUTH_API_KEY).</li>
  <li>Ou activez temporairement le repli dans <em>Admin → IA</em> (provider = "auto" ou "emergent").</li>
</ul>
<p style="color:#777;font-size:12px">Détail technique : {detail[:300]}</p>
<p style="color:#777;font-size:12px">— Alerte automatique MyExtension AI</p>"""
        from utils import send_brevo_email
        send_brevo_email(to_email=recipient, subject=subject, html_content=body, brand="myextension")
        logger.warning("[LLM ALERT] Email d'alerte envoyé à %s (%s)", recipient, kind)
    except Exception as e:
        logger.error("[LLM ALERT] Échec envoi email d'alerte: %s", e)


def get_ai_provider() -> str:
    """Provider IA courant : config admin (admin_config.json) prioritaire, sinon env AI_PROVIDER."""
    try:
        import json
        with open(_CONFIG_PATH, "r") as f:
            v = (json.load(f).get("ai_provider") or "").lower()
        if v in ("auto", "mammouth", "emergent"):
            return v
    except Exception:
        pass
    return AI_PROVIDER


class MammouthError(Exception):
    pass


# ─────────────────────── Emergent (repli) ───────────────────────
async def _emergent_chat(messages: List[Dict[str, str]], *, max_tokens: int, temperature: float) -> str:
    if not EMERGENT_LLM_KEY:
        raise MammouthError("EMERGENT_LLM_KEY non configurée (repli indisponible)")
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import uuid
    system_parts = [m.get("content", "") for m in messages if m.get("role") == "system"]
    user_parts = [m.get("content", "") for m in messages if m.get("role") != "system"]
    system_message = "\n\n".join(p for p in system_parts if p) or "Tu es un assistant utile."
    user_text = "\n\n".join(p for p in user_parts if p) or ""
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=uuid.uuid4().hex,
        system_message=system_message,
    ).with_model("anthropic", EMERGENT_TEXT_MODEL).with_params(max_tokens=max_tokens, temperature=temperature)
    reply = await chat.send_message(UserMessage(text=user_text))
    reply = (reply or "").strip()
    if not reply:
        raise MammouthError("Réponse vide (Emergent)")
    return reply


async def _emergent_image(prompt: str) -> bytes:
    if not EMERGENT_LLM_KEY:
        raise MammouthError("EMERGENT_LLM_KEY non configurée (repli indisponible)")
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import uuid
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=uuid.uuid4().hex,
        system_message="You are a helpful AI image generation assistant.",
    ).with_model("gemini", EMERGENT_IMAGE_MODEL).with_params(modalities=["image", "text"])
    _text, images = await chat.send_message_multimodal_response(UserMessage(text=prompt))
    if not images:
        raise MammouthError("Aucune image générée (Emergent)")
    return base64.b64decode(images[0]["data"])


# ─────────────────────── Mammouth ───────────────────────
async def _mammouth_image(prompt: str, *, model: Optional[str], size: str, timeout: float) -> bytes:
    if not MAMMOUTH_API_KEY:
        raise MammouthError("MAMMOUTH_API_KEY is not configured")
    url = f"{MAMMOUTH_BASE_URL}/images/generations"
    payload: Dict[str, Any] = {
        "model": model or MAMMOUTH_IMAGE_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": size,
    }
    headers = {"Authorization": f"Bearer {MAMMOUTH_API_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        body = resp.text[:500]
        logger.error("Mammouth image HTTP %s — %s", resp.status_code, body)
        if resp.status_code == 401:
            raise MammouthError("Clé Mammouth invalide")
        if resp.status_code in (402, 429):
            raise MammouthError("Quota Mammouth dépassé")
        raise MammouthError(f"Mammouth image indisponible ({resp.status_code})")
    data = resp.json()
    items = data.get("data") or []
    if not items:
        raise MammouthError("Aucune image générée par Mammouth")
    first = items[0]
    b64 = first.get("b64_json")
    if b64:
        return base64.b64decode(b64)
    img_url = first.get("url")
    if img_url:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r2 = await client.get(img_url)
        if r2.status_code == 200:
            return r2.content
    raise MammouthError("Format d'image Mammouth inattendu")


async def _mammouth_chat(messages, *, model, max_tokens, temperature, timeout) -> str:
    if not MAMMOUTH_API_KEY:
        raise MammouthError("MAMMOUTH_API_KEY is not configured")
    url = f"{MAMMOUTH_BASE_URL}/chat/completions"
    payload: Dict[str, Any] = {
        "model": model or MAMMOUTH_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {MAMMOUTH_API_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        body = resp.text[:500]
        logger.error("Mammouth HTTP %s — %s", resp.status_code, body)
        if resp.status_code == 401:
            _alert_llm_problem("Clé Mammouth invalide (401)", body)
            raise MammouthError("Clé Mammouth invalide")
        if resp.status_code in (402, 429):
            _alert_llm_problem("Quota / crédit Mammouth dépassé", body)
            raise MammouthError("Quota Mammouth dépassé")
        raise MammouthError(f"Mammouth indisponible ({resp.status_code})")
    data = resp.json()
    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not reply:
        raise MammouthError("Réponse vide de Mammouth")
    return reply


# ─────────────────────── API publique ───────────────────────
async def generate_image(
    prompt: str,
    *,
    model: Optional[str] = None,
    size: str = "1024x1024",
    timeout: float = 120.0,
) -> bytes:
    """Génère une image (bytes PNG/JPEG). Mammouth d'abord, repli Emergent si échec."""
    provider = get_ai_provider()
    if provider == "emergent":
        return await _emergent_image(prompt)
    try:
        return await _mammouth_image(prompt, model=model, size=size, timeout=timeout)
    except Exception as e:
        if provider == "mammouth":
            raise
        logger.warning("Mammouth image KO (%s) → repli Emergent", e)
        return await _emergent_image(prompt)


async def chat(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: float = 60.0,
) -> str:
    """Complétion de chat. Mammouth d'abord, repli Emergent si échec."""
    provider = get_ai_provider()
    if provider == "emergent":
        return await _emergent_chat(messages, max_tokens=max_tokens, temperature=temperature)
    try:
        return await _mammouth_chat(messages, model=model, max_tokens=max_tokens, temperature=temperature, timeout=timeout)
    except Exception as e:
        if provider == "mammouth":
            raise
        logger.warning("Mammouth chat KO (%s) → repli Emergent", e)
        return await _emergent_chat(messages, max_tokens=max_tokens, temperature=temperature)
