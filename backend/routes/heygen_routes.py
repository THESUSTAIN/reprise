"""
HeyGen Routes — Génération de vidéos avatar IA, pilotée depuis WordPress
(ou n'importe quel client externe) via un secret partagé.

Sécurité :
- La clé API HeyGen (HEYGEN_API_KEY) reste UNIQUEMENT côté ce backend.
- Le client externe (plugin WP) s'authentifie avec un header
  `X-Zayado-Secret` comparé à WP_CONNECTOR_SECRET (env var), PAS avec un
  compte utilisateur Zayado — c'est un appel machine-to-machine.
- Seuls les avatars "stock" HeyGen ou un avatar vérifié pré-enregistré
  côté HeyGen sont utilisables. Aucun upload libre de visage tiers ici.
"""
import os
import logging
import hmac
import httpx
from fastapi import APIRouter, HTTPException, Header, Depends

logger = logging.getLogger(__name__)
heygen_router = APIRouter(prefix="/heygen", tags=["HeyGen"])

HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY")
WP_CONNECTOR_SECRET = os.environ.get("WP_CONNECTOR_SECRET")
HEYGEN_BASE_URL = "https://api.heygen.com"

if not WP_CONNECTOR_SECRET:
    logger.warning(
        "⚠️ WP_CONNECTOR_SECRET n'est pas défini — le connecteur WordPress "
        "sera inutilisable tant que cette variable d'env n'est pas configurée."
    )


def verify_wp_secret(x_zayado_secret: str = Header(default=None)):
    """Auth machine-to-machine pour le plugin WordPress."""
    if not WP_CONNECTOR_SECRET:
        raise HTTPException(500, "WP_CONNECTOR_SECRET non configuré côté serveur")
    if not x_zayado_secret or not hmac.compare_digest(x_zayado_secret, WP_CONNECTOR_SECRET):
        raise HTTPException(401, "Secret invalide")
    return True


def _heygen_headers():
    if not HEYGEN_API_KEY:
        raise HTTPException(500, "HEYGEN_API_KEY non configuré côté serveur")
    return {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}


# ─── Liste des avatars & voix autorisés (stock uniquement) ────────────
@heygen_router.get("/avatars")
async def list_avatars(_=Depends(verify_wp_secret)):
    """Retourne la liste des avatars stock disponibles sur le compte HeyGen."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{HEYGEN_BASE_URL}/v2/avatars", headers=_heygen_headers())
    if r.status_code != 200:
        raise HTTPException(r.status_code, f"Erreur HeyGen: {r.text}")
    data = r.json().get("data", {})
    return {"avatars": data.get("avatars", [])}


@heygen_router.get("/voices")
async def list_voices(_=Depends(verify_wp_secret)):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{HEYGEN_BASE_URL}/v2/voices", headers=_heygen_headers())
    if r.status_code != 200:
        raise HTTPException(r.status_code, f"Erreur HeyGen: {r.text}")
    return {"voices": r.json().get("data", {}).get("voices", [])}


# ─── Génération vidéo ───────────────────────────────────────────────────
class GenerateVideoPayload(dict):
    """avatar_id: str, voice_id: str, script: str, title: str (optionnel)"""


@heygen_router.post("/generate")
async def generate_video(payload: dict, _=Depends(verify_wp_secret)):
    avatar_id = payload.get("avatar_id")
    voice_id = payload.get("voice_id")
    script = (payload.get("script") or "").strip()
    title = payload.get("title") or "Zayado Video"

    if not avatar_id or not voice_id or not script:
        raise HTTPException(400, "avatar_id, voice_id et script sont requis")
    if len(script) > 1500:
        raise HTTPException(400, "Script trop long (max 1500 caractères)")

    body = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                },
            }
        ],
        "dimension": {"width": 1280, "height": 720},
        "title": title,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{HEYGEN_BASE_URL}/v2/video/generate",
            headers=_heygen_headers(),
            json=body,
        )
    if r.status_code not in (200, 201):
        logger.error(f"HeyGen generate error: {r.status_code} {r.text}")
        raise HTTPException(r.status_code, f"Erreur HeyGen: {r.text}")

    data = r.json().get("data", {})
    video_id = data.get("video_id")
    if not video_id:
        raise HTTPException(502, "Réponse HeyGen inattendue (pas de video_id)")

    return {"video_id": video_id, "status": "processing"}


# ─── Statut / polling ────────────────────────────────────────────────────
@heygen_router.get("/status/{video_id}")
async def video_status(video_id: str, _=Depends(verify_wp_secret)):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{HEYGEN_BASE_URL}/v1/video_status.get",
            headers=_heygen_headers(),
            params={"video_id": video_id},
        )
    if r.status_code != 200:
        raise HTTPException(r.status_code, f"Erreur HeyGen: {r.text}")

    data = r.json().get("data", {})
    status = data.get("status")  # pending | processing | completed | failed
    result = {"video_id": video_id, "status": status}
    if status == "completed":
        result["video_url"] = data.get("video_url")
        result["thumbnail_url"] = data.get("thumbnail_url")
        result["duration"] = data.get("duration")
    elif status == "failed":
        result["error"] = data.get("error")
    return result
