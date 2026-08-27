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
    return {"reply": "Chat en mode démo — la vraie IA (Mammouth) sera branchée bientôt.", "sources": []}


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
