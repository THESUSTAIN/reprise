"""
ZAYADO — Backend DÉMO léger (étape preview)
=============================================
Ce backend NE REMPLACE PAS le vrai backend ZAYADO (FastAPI + SQLAlchemy,
~80 routes, IA Mammouth, OAuth, paiements...). Il sert uniquement à faire
tourner le FRONTEND ZAYADO en LIVE dans cet environnement de prévisualisation :

  • /api/auth/*        → login démo fonctionnel (compte test « Thomas »,
                          lien magique preview, OAuth stub) qui renvoie un
                          utilisateur + un jeton, pour traverser l'écran de
                          connexion et entrer dans l'app.
  • /api/health        → sonde de santé.
  • catch-all /api/*   → réponses vides douces (200 {}) pour éviter les
                          erreurs bruyantes ; les pages affichent alors leurs
                          états « vides » (données réelles = brancher le vrai
                          backend + clé Mammouth plus tard).

⚠️  L'IA du chat est en MODE DÉMO (aucune vraie génération). La clé Mammouth
    sera branchée ultérieurement.
"""
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os, uuid, logging
import httpx
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zayado-demo")

app = FastAPI(title="ZAYADO Demo Backend")
api = APIRouter(prefix="/api")

DEMO_TOKEN = "demo-preview-token"

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def demo_user(email: str = "thomas@zayado.net", name: str = "Thomas") -> Dict[str, Any]:
    """Utilisateur de démonstration renvoyé par les routes d'auth."""
    return {
        "id": "demo-user-thomas",
        "email": email,
        "name": name,
        "first_name": name,
        "role": "user",
        "credits": 500,
        "bonus_credits": 0,
        "purchased_credits": 0,
        "plan": "pro",
        "created_at": "2025-01-01T09:00:00+00:00",
        "discount_type": None,
        "discount_percent": 0,
        "discount_verified": False,
        "partner_code": None,
        "partner_url": None,
        "memory": None,
        "referral_code": "ZAYADO-DEMO",
        "settings": {"onboarding_completed": True, "language": "fr"},
        "cancel_at_period_end": False,
        "thesustain_member": False,
        "thesustain_type": None,
        "two_factor_enabled": False,
        "is_active": True,
        "credits_last_reset": None,
        "credits_per_month": 500,
        "onboarding_done": True,
        "trial_ends_at": None,
        "trial_days_left": None,
        "trial_active": False,
    }

def token_response(email: str = "thomas@zayado.net", name: str = "Thomas") -> Dict[str, Any]:
    return {"access_token": DEMO_TOKEN, "token_type": "bearer", "user": demo_user(email, name)}


# ── Santé ───────────────────────────────────────────────────────────────
@api.get("/health")
async def health():
    return {"status": "ok", "mode": "demo", "time": _now_iso()}

@api.get("/")
async def root():
    return {"message": "ZAYADO demo backend", "mode": "demo"}


# ── Auth (démo) ──────────────────────────────────────────────────────────
class Credentials(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None

@api.post("/auth/demo-login")
async def demo_login(data: Dict[str, Any] = None):
    email = (data or {}).get("email") or "thomas@zayado.net"
    return token_response(email, "Thomas")

@api.post("/auth/login")
async def login(creds: Credentials):
    return token_response(creds.email or "thomas@zayado.net", "Thomas")

@api.post("/auth/register")
async def register(creds: Credentials):
    return token_response(creds.email or "thomas@zayado.net", creds.first_name or "Thomas")

@api.post("/auth/request-link")
async def request_link(data: Dict[str, Any] = None):
    """Lien magique — en preview on renvoie directement le dev_link."""
    email = (data or {}).get("email") or "thomas@zayado.net"
    return {
        "ok": True,
        "preview": True,
        "message": "Mode preview : utilisez le lien ci-dessous.",
        "dev_link": f"/login?token={DEMO_TOKEN}",
        "email": email,
    }

@api.post("/auth/verify-link")
async def verify_link(data: Dict[str, Any] = None):
    return token_response()

@api.get("/auth/me")
async def me(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return JSONResponse(status_code=401, content={"detail": "Non authentifié"})
    return demo_user()

@api.post("/auth/oauth/{provider}/start")
async def oauth_start(provider: str, data: Dict[str, Any] = None):
    return {"authorization_url": f"/login?code=demo&state={provider}_demo", "preview": True}

@api.post("/auth/oauth/{provider}/exchange")
async def oauth_exchange(provider: str, data: Dict[str, Any] = None):
    return token_response()


# ── Chat / Copilote (démo statique) ─────────────────────────────────────
@api.get("/chat/messages")
async def chat_messages():
    # Doit être un TABLEAU (ChatPanel fait messages.map). Vide en démo.
    return []

@api.post("/chat/messages")
async def chat_messages_send(data: Dict[str, Any] = None):
    return {"reply": "Chat en mode démo — la vraie IA (Mammouth) sera branchée bientôt.", "sources": []}

@api.post("/growth/copilote")
async def growth_copilote(data: Dict[str, Any] = None):
    """Chat Copilote branché sur Mammouth (API compatible OpenAI).
    Repli propre en message démo si la clé manque ou si Mammouth échoue."""
    data = data or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []
    api_key = os.environ.get("MAMMOUTH_API_KEY") or os.environ.get("MAMMOTH_API_KEY", "")
    base_url = os.environ.get("MAMMOUTH_BASE_URL", "https://api.mammouth.ai/v1").rstrip("/")
    model = os.environ.get("MAMMOUTH_MODEL", "claude-haiku-4-5-20251001")

    if not user_message:
        return {"reply": "Comment puis-je vous aider aujourd'hui ?", "sources": []}
    if not api_key:
        return {"reply": "Chat en mode démo — la clé Mammouth n'est pas configurée.", "sources": []}

    system_prompt = (
        "Tu es MyExtension Business, le copilote IA de l'application ZAYADO pour solopreneurs "
        "et PME. Réponds en français, de façon claire, concise et actionnable. Tu aides sur la "
        "vision stratégique, la croissance, le pilotage (trésorerie, prospection) et le bien-être. "
        "Ne fais pas de promesses d'exécution automatique : propose, l'utilisateur valide."
    )
    messages = [{"role": "system", "content": system_prompt}]
    for m in history[-8:]:
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    payload = {"model": model, "messages": messages, "max_tokens": 700, "temperature": 0.6, "stream": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        if resp.status_code != 200:
            logger.error(f"[Mammouth] HTTP {resp.status_code}: {resp.text[:300]}")
            return {"reply": "Le service IA est momentanément indisponible. Réessayez dans un instant.", "sources": []}
        j = resp.json()
        reply = (j.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        return {"reply": reply or "Je n'ai pas de réponse pour le moment.", "sources": []}
    except Exception as e:
        logger.error(f"[Mammouth] exception: {e}")
        return {"reply": "Le service IA a rencontré une erreur réseau. Réessayez.", "sources": []}


app.include_router(api)


# ── Catch-all doux ───────────────────────────────────────────────────────
# GET      → []  (évite les crash « .map is not a function » ; les états
#                 « vides » s'affichent proprement)
# mutations → {} (POST/PUT/PATCH/DELETE)
# À remplacer par le vrai backend ZAYADO + clé Mammouth plus tard.
@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def catch_all(full_path: str, request: Request):
    logger.info(f"[demo catch-all] {request.method} /api/{full_path}")
    if request.method == "GET":
        return JSONResponse(status_code=200, content=[])
    return JSONResponse(status_code=200, content={})


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
