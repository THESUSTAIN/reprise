"""OAuth routes for Extension IA API.

Supports two flows:
  1. Implicit flow: frontend sends an access_token obtained directly from the provider.
  2. Authorization-code flow: frontend sends a code + redirect_uri for exchange.
"""
import logging
import asyncio
import os

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import uuid

from database import get_db
from models import User
from deps import hash_password, create_access_token, user_to_response
from schemas import OAuthLoginRequest, TokenResponse
from utils import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET,
    send_brevo_email, logger
)
from routes.app_logs import log_event

oauth_router = APIRouter(prefix="/oauth", tags=["OAuth"])

# Allowed redirect URIs for OAuth flows (anti-CSRF #26)
# ── Origines autorisées pour les redirections OAuth ──────────────────────
# On accepte toutes les origines https valides.
# La vraie sécurité CSRF est assurée par le paramètre state (vérifié côté frontend).
# La restriction d'origines est configurée dans Google Cloud Console (source de vérité).
# Utilisé uniquement à titre informatif par /oauth/diagnostic ci-dessous.
_ALLOWED_REDIRECT_ORIGINS = [o.strip() for o in os.environ.get(
    "CORS_ORIGINS",
    "https://app.zayado.net,https://www.zayado.net,https://zayado.net"
).split(",") if o.strip() and o.strip() != "*"]

def _validate_redirect_uri(redirect_uri: str | None):
    """Accepte toute URI de redirection HTTPS — la validation réelle est dans Google/Microsoft."""
    if not redirect_uri:
        return
    from urllib.parse import urlparse
    parsed = urlparse(redirect_uri)
    # Rejeter uniquement les URI manifestement dangereuses (javascript:, data:)
    if parsed.scheme not in ("https", "http"):
        raise HTTPException(status_code=400, detail=f"redirect_uri invalide: schéma non autorisé ({parsed.scheme}).")
    # En production, exiger HTTPS
    if os.environ.get("ENV", "development") == "production" and parsed.scheme != "https":
        raise HTTPException(status_code=400, detail="redirect_uri doit utiliser HTTPS en production.")


async def _http_post(url: str, data: dict, retries: int = 3) -> dict:
    """Make a POST request with retry logic to avoid TCPTransport closed issues."""
    last_err = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=0),
                http2=False,
            ) as client:
                resp = await client.post(url, data=data)
                return {"status": resp.status_code, "body": resp.json()}
        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.WriteError, httpx.ConnectError, httpx.PoolTimeout, httpx.StreamClosed) as e:
            last_err = e
            logger.warning(f"_http_post attempt {attempt+1}/{retries} failed: {e}")
            await asyncio.sleep(0.5 * (attempt + 1))
        except Exception as e:
            last_err = e
            logger.error(f"_http_post unexpected error: {e}")
            if "TCPTransport" in str(e) or "closed" in str(e).lower():
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            break
    raise Exception(f"HTTP POST failed after {retries} retries: {last_err}")


async def _http_get(url: str, headers: dict, retries: int = 3) -> dict:
    """Make a GET request with retry logic to avoid TCPTransport closed issues."""
    last_err = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=0),
                http2=False,
            ) as client:
                resp = await client.get(url, headers=headers)
                return {"status": resp.status_code, "body": resp.json()}
        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.WriteError, httpx.ConnectError, httpx.PoolTimeout, httpx.StreamClosed) as e:
            last_err = e
            logger.warning(f"_http_get attempt {attempt+1}/{retries} failed: {e}")
            await asyncio.sleep(0.5 * (attempt + 1))
        except Exception as e:
            last_err = e
            logger.error(f"_http_get unexpected error: {e}")
            if "TCPTransport" in str(e) or "closed" in str(e).lower():
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            break
    raise Exception(f"HTTP GET failed after {retries} retries: {last_err}")


async def _resolve_google_access_token(request: OAuthLoginRequest) -> str:
    """Return an access_token: use it directly (implicit) or exchange a code."""
    if request.code and request.redirect_uri:
        _validate_redirect_uri(request.redirect_uri)
        logger.info(f"Google OAuth code exchange: redirect_uri={request.redirect_uri}, client_id={GOOGLE_CLIENT_ID[:20]}...")
        result = await _http_post("https://oauth2.googleapis.com/token", {
            "code": request.code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": request.redirect_uri,
            "grant_type": "authorization_code"
        })
        if result["status"] != 200:
            logger.error(f"Google token exchange failed: status={result['status']}, body={result['body']}, redirect_uri={request.redirect_uri}")
            error_body = result["body"]
            error_desc = error_body.get("error_description", error_body.get("error", ""))
            if "redirect_uri_mismatch" in str(error_body):
                raise HTTPException(status_code=400, detail=f"redirect_uri_mismatch: L'URL '{request.redirect_uri}' n'est pas autorisee dans Google Cloud Console. Ajoutez-la dans Identifiants > URIs de redirection autorises.")
            if "invalid_client" in str(error_body):
                raise HTTPException(status_code=400, detail="Client Google invalide. Verifiez GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET dans les variables d'environnement.")
            if "invalid_grant" in str(error_body):
                raise HTTPException(status_code=400, detail="Code d'autorisation expire ou deja utilise. Veuillez reessayer.")
            raise HTTPException(status_code=400, detail=f"Erreur Google OAuth: {error_desc}" if error_desc else f"Erreur Google OAuth ({result['status']})")
        return result["body"].get("access_token")
    if request.token:
        return request.token
    raise HTTPException(status_code=400, detail="Token ou code manquant")


async def _resolve_microsoft_access_token(request: OAuthLoginRequest) -> str:
    """Return an access_token: use it directly (implicit) or exchange a code."""
    if request.code and request.redirect_uri:
        _validate_redirect_uri(request.redirect_uri)
        result = await _http_post("https://login.microsoftonline.com/common/oauth2/v2.0/token", {
            "code": request.code,
            "client_id": MICROSOFT_CLIENT_ID,
            "client_secret": MICROSOFT_CLIENT_SECRET,
            "redirect_uri": request.redirect_uri,
            "grant_type": "authorization_code",
            "scope": "openid profile email User.Read"
        })
        if result["status"] != 200:
            logger.error(f"Microsoft token exchange failed: {result['body']}")
            raise HTTPException(status_code=400, detail="Erreur d'authentification Microsoft")
        return result["body"].get("access_token")
    if request.token:
        return request.token
    raise HTTPException(status_code=400, detail="Token ou code manquant")


@oauth_router.get("/diagnostic")
async def oauth_diagnostic():
    """Diagnostic endpoint for OAuth configuration. Helps debug production issues."""
    try:
        gid = GOOGLE_CLIENT_ID or ""
        msid = MICROSOFT_CLIENT_ID or ""
        return {
            "google_client_id_set": bool(gid and len(gid) > 10),
            "google_client_id_preview": (gid[:8] + "****") if gid else "NOT SET",
            "google_secret_set": bool(GOOGLE_CLIENT_SECRET and len(GOOGLE_CLIENT_SECRET) > 5),
            "microsoft_client_id_set": bool(msid and len(msid) > 10),
            "allowed_redirect_origins": list(_ALLOWED_REDIRECT_ORIGINS or []),
            "expected_redirect_uris": [f"{o}/login" for o in (list(_ALLOWED_REDIRECT_ORIGINS or []))],
            "instructions": "Assurez-vous que les URIs de redirection ci-dessus sont EXACTEMENT configurees dans Google Cloud Console > APIs > Identifiants > Client OAuth 2.0 > URIs de redirection autorisees."
        }
    except Exception as e:
        return {"error": str(e), "google_client_id_set": bool(GOOGLE_CLIENT_ID), "google_secret_set": bool(GOOGLE_CLIENT_SECRET)}



@oauth_router.post("/google")
async def google_oauth(request: OAuthLoginRequest, db: AsyncSession = Depends(get_db)):
    max_retries = 2
    last_error = None
    for attempt in range(max_retries):
        try:
            access_token = await _resolve_google_access_token(request)
            result = await _http_get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                {"Authorization": f"Bearer {access_token}"}
            )
            if result["status"] != 200:
                raise HTTPException(status_code=400, detail="Impossible de recuperer les informations utilisateur Google")
            google_user = result["body"]
            email = google_user.get("email")
            name = google_user.get("name", email.split("@")[0])
            db_result = await db.execute(select(User).where(User.email == email))
            user = db_result.scalar_one_or_none()
            if not user:
                user = User(
                    email=email, name=name,
                    password_hash=hash_password(str(uuid.uuid4())),
                    oauth_provider="google", oauth_id=google_user.get("id"),
                    credits=180, plan="free"
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                try:
                    asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(email, name, "Bienvenue sur ZAYADO !",
                        f'<div style="font-family:Arial;max-width:600px;margin:0 auto;padding:20px;">'
                        f'<h1 style="color:#1E3A8A;">Bienvenue {name} !</h1>'
                        f'<p>Compte cree via Google. Vous disposez de <strong>180 credits gratuits</strong>.</p></div>'))
                except Exception:
                    pass
            # Fix #106 — Update last_login_at for OAuth logins
            from datetime import datetime, timezone
            from sqlalchemy import update
            try:
                await db.execute(update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc)))
                await db.commit()
                from routes.analytics import track_event
                await track_event(db, user.id, "login", {"via": "google"})
            except Exception:
                await db.rollback()
            token = create_access_token({"sub": user.id})
            asyncio.ensure_future(log_event(
                'INFO', 'oauth', f'Connexion Google réussie : {email}',
                action='google_login', user_id=user.id, user_email=email,
                details={'provider': 'google'}
            ))
            return {"access_token": token, "user": user_to_response(user).model_dump(), "provider": "google"}
        except HTTPException:
            raise
        except Exception as e:
            last_error = e
            error_str = str(e)
            if "TCPTransport" in error_str or "closed" in error_str.lower() or "handler" in error_str.lower():
                logger.warning(f"Google OAuth attempt {attempt+1}/{max_retries} transport error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0)
                    try:
                        await db.rollback()
                    except Exception:
                        pass
                    continue
            logger.error(f"Google OAuth error: {e}")
            import traceback
            asyncio.ensure_future(log_event(
                'ERROR', 'oauth', f'Erreur Google OAuth : {error_str}',
                action='google_oauth_error',
                details={'error': error_str, 'traceback': traceback.format_exc()[-1000:]}
            ))
            raise HTTPException(status_code=500, detail=f"Erreur Google OAuth: {error_str}")
    raise HTTPException(status_code=500, detail=f"Erreur Google OAuth apres {max_retries} tentatives: {str(last_error)}")


@oauth_router.post("/microsoft")
async def microsoft_oauth(request: OAuthLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        access_token = await _resolve_microsoft_access_token(request)
        result = await _http_get(
            "https://graph.microsoft.com/v1.0/me",
            {"Authorization": f"Bearer {access_token}"}
        )
        if result["status"] != 200:
            raise HTTPException(status_code=400, detail="Impossible de recuperer les informations utilisateur Microsoft")
        ms_user = result["body"]
        email = ms_user.get("mail") or ms_user.get("userPrincipalName")
        name = ms_user.get("displayName", email.split("@")[0] if email else "User")
        if not email:
            raise HTTPException(status_code=400, detail="Impossible de recuperer l'email Microsoft")
        db_result = await db.execute(select(User).where(User.email == email))
        user = db_result.scalar_one_or_none()
        if not user:
            user = User(
                email=email, name=name,
                password_hash=hash_password(str(uuid.uuid4())),
                oauth_provider="microsoft", oauth_id=ms_user.get("id"),
                credits=180, plan="free"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            try:
                asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(email, name, "Bienvenue sur ZAYADO !",
                    f'<div style="font-family:Arial;max-width:600px;margin:0 auto;padding:20px;">'
                    f'<h1 style="color:#1E3A8A;">Bienvenue {name} !</h1>'
                    f'<p>Compte cree via Microsoft. Vous disposez de <strong>180 credits gratuits</strong>.</p></div>'))
            except Exception:
                pass
        # Fix #106 — Update last_login_at for OAuth logins
        from datetime import datetime, timezone
        from sqlalchemy import update
        try:
            await db.execute(update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc)))
            await db.commit()
            from routes.analytics import track_event
            await track_event(db, user.id, "login", {"via": "microsoft"})
        except Exception:
            await db.rollback()
        token = create_access_token({"sub": user.id})
        asyncio.ensure_future(log_event(
            'INFO', 'oauth', f'Connexion Microsoft réussie : {email}',
            action='microsoft_login', user_id=user.id, user_email=email,
            details={'provider': 'microsoft'}
        ))
        return {"access_token": token, "user": user_to_response(user).model_dump(), "provider": "microsoft"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Microsoft OAuth error: {e}")
        import traceback
        asyncio.ensure_future(log_event(
            'ERROR', 'oauth', f'Erreur Microsoft OAuth : {str(e)}',
            action='microsoft_oauth_error',
            details={'error': str(e), 'traceback': traceback.format_exc()[-1000:]}
        ))
        raise HTTPException(status_code=500, detail=f"Erreur Microsoft OAuth: {str(e)}")


# ── Routes /start — le backend initie le flux OAuth ──────────────────────
# Évite le problème REACT_APP_GOOGLE_CLIENT_ID non exposé par CRA

@oauth_router.get("/google/start")
async def google_oauth_start(redirect_uri: str):
    """Retourne l'URL d'autorisation Google pour le frontend."""
    _validate_redirect_uri(redirect_uri)
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(503, "GOOGLE_CLIENT_ID non configuré dans Railway.")
    import secrets as _sec
    from urllib.parse import urlencode as _ue
    state = "google_" + _sec.token_urlsafe(16)
    params = _ue({
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  redirect_uri,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account",
        "state":         state,
    })
    return {"authorization_url": f"https://accounts.google.com/o/oauth2/v2/auth?{params}"}


@oauth_router.get("/microsoft/start")
async def microsoft_oauth_start(redirect_uri: str):
    """Retourne l'URL d'autorisation Microsoft pour le frontend."""
    _validate_redirect_uri(redirect_uri)
    from utils import MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET
    if not MICROSOFT_CLIENT_ID:
        raise HTTPException(503, "MICROSOFT_CLIENT_ID non configuré dans Railway.")
    import secrets as _sec
    from urllib.parse import urlencode as _ue
    state = "ms_" + _sec.token_urlsafe(16)
    params = _ue({
        "client_id":     MICROSOFT_CLIENT_ID,
        "redirect_uri":  redirect_uri,
        "response_type": "code",
        "scope":         "openid email profile User.Read offline_access",
        "response_mode": "query",
        "state":         state,
    })
    return {"authorization_url": f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{params}"}
