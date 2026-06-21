"""
Canva Connect API — OAuth2 Authorization Code + PKCE.
Le canvas central du Vision Board est propulsé par Canva (éditeur externe).
Flux: /canva/auth/start -> Canva -> /canva/auth/callback -> tokens en Mongo.
"""
import os
import base64
import hashlib
import secrets
import time
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

AUTH_URL = "https://www.canva.com/api/oauth/authorize"
TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"
PROFILE_URL = "https://api.canva.com/rest/v1/users/me/profile"


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    return verifier, challenge


def build_router(db: AsyncIOMotorDatabase) -> APIRouter:
    router = APIRouter(prefix="/canva", tags=["canva"])
    STATES = db.canva_oauth_state
    TOKENS = db.canva_tokens

    client_id = os.environ.get("CANVA_CLIENT_ID", "")
    client_secret = os.environ.get("CANVA_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("CANVA_REDIRECT_URI", "")
    scopes = os.environ.get("CANVA_SCOPES", "design:content:read profile:read")
    app_base = os.environ.get("APP_BASE_URL", "").rstrip("/")
    # Compte Canva UNIQUE de l'équipe/marque — tous les utilisateurs finaux passent
    # par ce compte côté serveur (ils n'ont jamais à se connecter à Canva).
    ACCOUNT = os.environ.get("CANVA_ACCOUNT", "team")

    def _basic_auth_header():
        raw = f"{client_id}:{client_secret}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    @router.get("/auth/start")
    async def auth_start():
        if not client_id or not redirect_uri:
            raise HTTPException(500, "Canva non configuré (CANVA_CLIENT_ID/REDIRECT_URI).")
        verifier, challenge = _pkce_pair()
        state = secrets.token_urlsafe(24)
        await STATES.insert_one({
            "state": state, "code_verifier": verifier, "user_id": ACCOUNT,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        from urllib.parse import urlencode
        params = {
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "scope": scopes,
            "response_type": "code",
            "client_id": client_id,
            "state": state,
            "redirect_uri": redirect_uri,
        }
        return {"authorization_url": f"{AUTH_URL}?{urlencode(params)}"}

    @router.get("/auth/callback")
    async def auth_callback(request: Request):
        params = request.query_params
        code = params.get("code")
        state = params.get("state")
        error = params.get("error")
        front = f"{app_base}/vision-board"
        if error:
            return RedirectResponse(f"{front}?canva=error&reason={error}")
        if not code or not state:
            return RedirectResponse(f"{front}?canva=error&reason=missing_code")
        st = await STATES.find_one({"state": state})
        if not st:
            return RedirectResponse(f"{front}?canva=error&reason=bad_state")
        await STATES.delete_one({"state": state})

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    TOKEN_URL,
                    headers={"Authorization": _basic_auth_header(),
                             "Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "code_verifier": st["code_verifier"],
                        "redirect_uri": redirect_uri,
                    },
                )
            if resp.status_code != 200:
                import logging
                logging.getLogger("canva").error("TOKEN EXCHANGE %s -> %s", resp.status_code, resp.text[:500])
                return RedirectResponse(f"{front}?canva=error&reason=token_{resp.status_code}")
            tok = resp.json()
        except Exception as e:  # noqa
            import logging
            logging.getLogger("canva").exception("TOKEN EXCHANGE EXCEPTION: %s", e)
            return RedirectResponse(f"{front}?canva=error&reason=token_exception")

        await TOKENS.update_one(
            {"user_id": st["user_id"]},
            {"$set": {
                "user_id": st["user_id"],
                "access_token": tok.get("access_token"),
                "refresh_token": tok.get("refresh_token"),
                "scope": tok.get("scope"),
                "expires_at": time.time() + int(tok.get("expires_in", 3600)),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )
        return RedirectResponse(f"{front}?canva=connected")

    async def _valid_token():
        rec = await TOKENS.find_one({"user_id": ACCOUNT})
        if not rec:
            return None
        if rec.get("expires_at", 0) > time.time() + 60:
            return rec.get("access_token")
        # refresh
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    TOKEN_URL,
                    headers={"Authorization": _basic_auth_header(),
                             "Content-Type": "application/x-www-form-urlencoded"},
                    data={"grant_type": "refresh_token",
                          "refresh_token": rec.get("refresh_token")},
                )
            if resp.status_code != 200:
                return None
            tok = resp.json()
            await TOKENS.update_one(
                {"user_id": ACCOUNT},
                {"$set": {
                    "access_token": tok.get("access_token"),
                    "refresh_token": tok.get("refresh_token", rec.get("refresh_token")),
                    "expires_at": time.time() + int(tok.get("expires_in", 3600)),
                }},
            )
            return tok.get("access_token")
        except Exception:  # noqa
            return None

    @router.get("/status")
    async def status():
        token = await _valid_token()
        if not token:
            return {"connected": False, "account": ACCOUNT}
        profile = None
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(PROFILE_URL,
                                     headers={"Authorization": f"Bearer {token}"})
                if r.status_code == 200:
                    profile = r.json()
        except Exception:  # noqa
            pass
        return {"connected": True, "account": ACCOUNT, "profile": profile}

    @router.post("/disconnect")
    async def disconnect():
        await TOKENS.delete_one({"user_id": ACCOUNT})
        return {"connected": False}

    return router
