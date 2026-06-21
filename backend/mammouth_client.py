"""Mammouth AI client — OpenAI-compatible chat completions.

Mammouth wraps multiple LLMs (Claude, GPT, Gemini, Mistral…) behind one OpenAI-style API.
Default model: claude-haiku-4-5 (fast, French-friendly, business-oriented).
"""
import os
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

MAMMOUTH_API_KEY = os.environ.get("MAMMOUTH_API_KEY", "")
MAMMOUTH_BASE_URL = os.environ.get("MAMMOUTH_BASE_URL", "https://api.mammouth.ai/v1").rstrip("/")
MAMMOUTH_MODEL = os.environ.get("MAMMOUTH_MODEL", "claude-haiku-4-5-20251001")


class MammouthError(Exception):
    pass


async def chat(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: float = 60.0,
) -> str:
    """Send a chat completion to Mammouth and return the assistant text."""
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
    headers = {
        "Authorization": f"Bearer {MAMMOUTH_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        body = resp.text[:500]
        logger.error("Mammouth HTTP %s — %s", resp.status_code, body)
        if resp.status_code == 401:
            raise MammouthError("Clé Mammouth invalide")
        if resp.status_code in (402, 429):
            raise MammouthError("Quota Mammouth dépassé — vérifiez votre solde sur app.mammouth.ai")
        raise MammouthError(f"Mammouth indisponible ({resp.status_code})")
    data = resp.json()
    reply = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    if not reply:
        raise MammouthError("Réponse vide de Mammouth")
    return reply
