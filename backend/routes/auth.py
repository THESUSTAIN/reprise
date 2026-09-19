"""Authentication routes for Extension IA by Zayado API."""
import asyncio
import hmac
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import os
import random
import logging
import json
logger = logging.getLogger(__name__)

from database import get_db
from models import User, Conversation, Project, Workflow, Transaction, Folder
from deps import (
    JWT_SECRET, JWT_ALGORITHM, hash_password, verify_password, create_access_token,
    get_current_user, user_to_response
)
from schemas import (
    UserCreateSchema, UserLoginSchema, UserResponse, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from utils import send_brevo_email, logger as utils_logger, rate_limiter
from jose import jwt
from routes.app_logs import log_event

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreateSchema, request: Request = None, db: AsyncSession = Depends(get_db)):
    # Rate limit: 5 registrations per IP per 10 minutes
    client_ip = request.client.host if request else "unknown"
    if rate_limiter.is_rate_limited(f"register:{client_ip}", max_attempts=5, window_seconds=600):
        raise HTTPException(status_code=429, detail="Trop de tentatives. Reessayez dans quelques minutes.")
    # Input validation
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caracteres")
    if len(user_data.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Le nom doit contenir au moins 2 caracteres")
    if len(user_data.name) > 100:
        raise HTTPException(status_code=400, detail="Le nom ne doit pas depasser 100 caracteres")
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    # Traiter le code de parrainage (ref)
    referrer = None
    ref_code = (user_data.ref or "").strip().upper()
    if ref_code:
        # Chercher le parrain par partner_code ou referral_code
        ref_result = await db.execute(
            select(User).where(
                (User.partner_code == ref_code) | (User.referral_code == ref_code)
            )
        )
        referrer = ref_result.scalar_one_or_none()

    # Crédits de bienvenue + bonus filleul si parrainage valide
    welcome_credits = 200
    referral_bonus_new_user = 100  # Crédits offerts au filleul
    referral_bonus_referrer = 150  # Crédits offerts au parrain

    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hash_password(user_data.password),
        credits=welcome_credits + (referral_bonus_new_user if referrer else 0),
        plan="free",
        referred_by=referrer.id if referrer else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    from routes.analytics import track_event
    await track_event(db, user.id, "signup", {"has_referrer": bool(referrer)})

    # Créditer le parrain si parrainage valide
    if referrer:
        try:
            await db.execute(
                update(User).where(User.id == referrer.id)
                .values(bonus_credits=User.bonus_credits + referral_bonus_referrer)
            )
            await db.commit()
            logger.info(f"Referral bonus: {referral_bonus_referrer} credits added to referrer {referrer.id} for new user {user.id}")
        except Exception as e:
            logger.error(f"Failed to credit referrer {referrer.id}: {e}")
            asyncio.ensure_future(log_event(
                'ERROR', 'affiliate', f'Erreur crédit parrain lors de l\'inscription : {str(e)}',
                action='referral_credit_error',
                details={'referrer_id': referrer.id, 'new_user_email': user_data.email, 'error': str(e)}
            ))
            await db.rollback()

    token = create_access_token({"sub": user.id})
    # Envoyer email de bienvenue — optimise conversion
    welcome_html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;background:#ffffff;">
      <!-- Header -->
      <div style="background:linear-gradient(135deg,#152F5C 0%,#1D4E8A 100%);padding:32px 24px;text-align:center;border-radius:12px 12px 0 0;">
        <div style="display:inline-block;background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 16px;margin-bottom:16px;">
          <span style="color:#E5D5A2;font-weight:700;font-size:18px;letter-spacing:1px;">ZAYADO</span>
        </div>
        <h1 style="color:#ffffff;font-size:26px;font-weight:700;margin:0 0 8px;">Bienvenue {user.name} !</h1>
        <p style="color:rgba(255,255,255,0.85);font-size:15px;margin:0;">Votre assistant IA professionnel est pret.</p>
      </div>
      <!-- Body -->
      <div style="padding:32px 24px;background:#ffffff;">
        <p style="color:#334155;font-size:15px;line-height:1.7;margin:0 0 20px;">
          Felicitations pour votre inscription ! Vous disposez de <strong style="color:#1E3A8A;">200 credits gratuits</strong> pour decouvrir tout le potentiel de ZAYADO.
        </p>
        <!-- 3 features -->
        <div style="background:#F8FAFC;border-radius:12px;padding:20px;margin:0 0 24px;">
          <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px;">
            <div style="width:36px;height:36px;border-radius:8px;background:#EEF2FF;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <span style="font-size:16px;">&#x1f4ac;</span>
            </div>
            <div>
              <p style="color:#1E3A8A;font-weight:700;font-size:14px;margin:0 0 2px;">8 modeles IA en 1 seul outil</p>
              <p style="color:#64748B;font-size:13px;margin:0;line-height:1.5;">ChatGPT, Claude, Gemini, Grok, Perplexity — choisissez le meilleur modele pour chaque tache.</p>
            </div>
          </div>
          <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px;">
            <div style="width:36px;height:36px;border-radius:8px;background:#FEF3C7;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <span style="font-size:16px;">&#x1f4c8;</span>
            </div>
            <div>
              <p style="color:#1E3A8A;font-weight:700;font-size:14px;margin:0 0 2px;">Diagnostic & Pilotage financier</p>
              <p style="color:#64748B;font-size:13px;margin:0;line-height:1.5;">Analysez votre CA, charges, TJM et obtenez des recommandations IA personnalisees.</p>
            </div>
          </div>
          <div style="display:flex;align-items:flex-start;gap:12px;">
            <div style="width:36px;height:36px;border-radius:8px;background:#ECFDF5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <span style="font-size:16px;">&#x1f916;</span>
            </div>
            <div>
              <p style="color:#1E3A8A;font-weight:700;font-size:14px;margin:0 0 2px;">Chatbot B2B pour votre site</p>
              <p style="color:#64748B;font-size:13px;margin:0;line-height:1.5;">Deployez un assistant IA sur votre site web en 5 minutes. Generez des leads 24h/24.</p>
            </div>
          </div>
        </div>
        <!-- CTA -->
        <div style="text-align:center;margin:0 0 24px;">
          <a href="https://app.zayado.net/app" style="display:inline-block;background:#C7372F;color:#ffffff;font-weight:700;font-size:16px;padding:14px 40px;border-radius:10px;text-decoration:none;box-shadow:0 4px 12px rgba(199,55,47,0.3);">
            Lancer mon assistant IA
          </a>
          <p style="color:#94A3B8;font-size:12px;margin:12px 0 0;">200 credits offerts — aucune carte requise</p>
        </div>
        <!-- Tip -->
        <div style="border-left:3px solid #E5D5A2;padding:12px 16px;background:#FFFBEB;border-radius:0 8px 8px 0;margin:0 0 20px;">
          <p style="color:#92400E;font-size:13px;font-weight:600;margin:0 0 4px;">Astuce pour bien demarrer</p>
          <p style="color:#78716C;font-size:13px;margin:0;line-height:1.6;">Commencez par le <strong>Diagnostic IA</strong> pour obtenir un bilan complet de votre activite. C'est le meilleur moyen de decouvrir comment ZAYADO peut vous aider au quotidien.</p>
        </div>
      </div>
      <!-- Footer -->
      <div style="background:#F8FAFC;padding:20px 24px;text-align:center;border-radius:0 0 12px 12px;border-top:1px solid #E2E8F0;">
        <p style="color:#94A3B8;font-size:11px;margin:0 0 4px;">Une question ? Repondez directement a cet email.</p>
        <p style="color:#CBD5E1;font-size:10px;margin:0;">MyExtension IA — L'assistant IA des independants et TPE (by Zayado)</p>
      </div>
    </div>"""
    asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(user.email, user.name, "Bienvenue sur MyExtension IA — Votre assistant IA est pret !", welcome_html))
    asyncio.ensure_future(log_event('INFO', 'auth', f'Nouvel utilisateur inscrit : {user.email}',
        action='register', user_id=user.id, user_email=user.email,
        details={'plan': user.plan, 'credits': user.credits, 'ref_used': bool(user_data.ref)}))
    return TokenResponse(access_token=token, user=user_to_response(user))

@auth_router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLoginSchema, request: Request = None, db: AsyncSession = Depends(get_db)):
    # Rate limit: 10 login attempts per IP per 5 minutes
    client_ip = request.client.host if request else "unknown"
    if rate_limiter.is_rate_limited(f"login:{client_ip}", max_attempts=10, window_seconds=300):
        raise HTTPException(status_code=429, detail="Trop de tentatives de connexion. Reessayez dans quelques minutes.")
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.password_hash):
        asyncio.ensure_future(log_event('WARNING', 'auth', f'Tentative de connexion échouée : {credentials.email}',
            action='login_failed', ip_address=client_ip,
            details={'email': credentials.email, 'reason': 'invalid_credentials'}))
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    # Fix #16 — check is_active
    if hasattr(user, 'is_active') and user.is_active is False:
        raise HTTPException(status_code=403, detail="Ce compte a ete desactive")
    # Fix #15 — update last_login_at
    try:
        await db.execute(update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc)))
        await db.commit()
        from routes.analytics import track_event
        await track_event(db, user.id, "login")
    except Exception:
        await db.rollback()
    # ── 2FA réellement appliquée (correction audit) ──────────────────────────
    # Si l'utilisateur a activé la double authentification, on N'ÉMET PAS le JWT
    # de session ici : on envoie un code par email et on renvoie un challenge.
    # Le token final n'est délivré que par /auth/login/verify-2fa.
    if bool((user.settings or {}).get("two_factor_enabled", False)):
        code = str(random.randint(100000, 999999))
        new_settings = {**(user.settings or {}),
                        "pending_2fa_code": code,
                        "pending_2fa_time": datetime.now(timezone.utc).isoformat()}
        await db.execute(update(User).where(User.id == user.id).values(settings=new_settings))
        await db.commit()
        html = f"""<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
            <h2 style="color:#1E3A8A;">Code de connexion - MyExtension IA</h2>
            <div style="font-size:32px;font-weight:bold;color:#1E3A8A;padding:20px;background:#F5F5F0;border-radius:8px;text-align:center;letter-spacing:8px;">{code}</div>
            <p style="color:#666;font-size:12px;margin-top:20px;">Ce code expire dans 10 minutes.</p></div>"""
        try:
            asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(user.email, user.name or "", "Code de connexion - MyExtension IA", html))
        except Exception as e:
            logger.error(f"2FA login email error: {e}")
        challenge_token = create_access_token({"sub": user.id, "scope": "login_2fa"}, expires_minutes=10)
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=200, content={
            "requires_2fa": True,
            "challenge_token": challenge_token,
            "message": "Un code de vérification a été envoyé par email.",
        })
    token = create_access_token({"sub": user.id})
    asyncio.ensure_future(log_event('INFO', 'auth', f'Connexion réussie : {user.email}',
        action='login_success', user_id=user.id, user_email=user.email,
        ip_address=client_ip, details={'plan': user.plan}))
    return TokenResponse(access_token=token, user=user_to_response(user))

@auth_router.post("/demo-login", response_model=TokenResponse)
async def demo_login(data: Dict[str, str], request: Request = None, db: AsyncSession = Depends(get_db)):
    """Connexion directe (sans mot de passe) réservée aux comptes de DÉMO whitelistés.

    Sert au bouton « Ouvrir le compte test (Thomas) » : garantit l'accès à la
    démo en preview ET en prod, sans dépendre d'un email/dev_link. Restreint à
    la liste blanche `DEMO_LOGIN_EMAILS` (par défaut : thomas + membre thesustain)."""
    client_ip = request.client.host if request else "unknown"
    if rate_limiter.is_rate_limited(f"demologin:{client_ip}", max_attempts=20, window_seconds=300):
        raise HTTPException(status_code=429, detail="Trop de tentatives. Reessayez dans quelques minutes.")
    email = (data.get("email") or "").strip().lower()
    whitelist = [e.strip().lower() for e in os.environ.get(
        "DEMO_LOGIN_EMAILS", "thomas@zayado.fr,membre@thesustain.net"
    ).split(",") if e.strip()]
    if email not in whitelist:
        raise HTTPException(status_code=403, detail="Compte de démo non autorisé.")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Compte de démo introuvable.")
    try:
        await db.execute(update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc)))
        await db.commit()
    except Exception:
        await db.rollback()
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=user_to_response(user))


@auth_router.post("/login/verify-2fa", response_model=TokenResponse)
async def login_verify_2fa(data: Dict[str, str], request: Request = None, db: AsyncSession = Depends(get_db)):
    """Étape 2 du login quand la 2FA est activée : échange (challenge_token + code) → JWT de session."""
    """Étape 2 du login quand la 2FA est activée : échange (challenge_token + code) → JWT de session."""
    client_ip = request.client.host if request else "unknown"
    if rate_limiter.is_rate_limited(f"login2fa:{client_ip}", max_attempts=10, window_seconds=300):
        raise HTTPException(status_code=429, detail="Trop de tentatives. Reessayez dans quelques minutes.")
    challenge = data.get("challenge_token", "")
    code = (data.get("code") or "").strip()
    try:
        payload = jwt.decode(challenge, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Session de vérification expirée. Reconnectez-vous.")
    if payload.get("scope") != "login_2fa":
        raise HTTPException(status_code=401, detail="Jeton de vérification invalide")
    user_id = payload.get("sub")
    # Audit sécurité : ce code à 6 chiffres n'avait aucune limite de tentatives
    # (contrairement à login/reset/emergency-reset juste au-dessus) — brute-forçable
    # en quelques secondes sans throttle. Même fenêtre que les autres endpoints sensibles.
    if rate_limiter.is_rate_limited(f"2fa-verify:{user_id}", max_attempts=8, window_seconds=600):
        raise HTTPException(status_code=429, detail="Trop de tentatives. Reconnectez-vous.")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    settings = user.settings or {}
    stored_code = settings.get("pending_2fa_code", "")
    stored_time = settings.get("pending_2fa_time", "")
    if not stored_code or not hmac.compare_digest(code, stored_code):
        raise HTTPException(status_code=400, detail="Code invalide")
    if stored_time and (datetime.now(timezone.utc) - datetime.fromisoformat(stored_time)).total_seconds() > 600:
        raise HTTPException(status_code=400, detail="Code expiré")
    # Consomme le code (anti-rejeu)
    new_settings = {**settings}
    new_settings.pop("pending_2fa_code", None)
    new_settings.pop("pending_2fa_time", None)
    await db.execute(update(User).where(User.id == user.id).values(settings=new_settings))
    await db.commit()
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=user_to_response(user))

@auth_router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, req: Request = None, db: AsyncSession = Depends(get_db)):
    # Rate limit: 3 reset attempts per email per 15 minutes
    if rate_limiter.is_rate_limited(f"reset:{request.email}", max_attempts=3, window_seconds=900):
        return {"status": "ok", "message": "Si un compte existe, un email a ete envoye"}
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user:
        return {"status": "ok", "message": "Si un compte existe, un email a ete envoye"}
    reset_token = create_access_token({"sub": user.id, "type": "reset"}, expires_minutes=30)
    # Determine frontend URL: prefer Referer (public browser URL), then env FRONTEND_URL
    frontend_url = os.environ.get('FRONTEND_URL', 'https://app.zayado.net')
    if req:
        referer = req.headers.get("referer") or ""
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                frontend_url = f"{parsed.scheme}://{parsed.netloc}"
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    html = f"""<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
        <h2 style="color:#1E3A8A;">R&#233;initialisation de mot de passe</h2>
        <p>Bonjour {user.name or ''},</p>
        <a href="{reset_link}" style="display:inline-block;padding:12px 24px;background:#1E3A8A;color:white;border-radius:8px;text-decoration:none;font-weight:bold;">R&#233;initialiser mon mot de passe</a>
        <p style="color:#666;font-size:12px;margin-top:20px;">Ce lien expire dans 30 minutes.</p>
    </div>"""
    try:
        asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(user.email, user.name or "", "Réinitialisation de mot de passe - Extension IA by Zayado", html))
    except Exception as e:
        logger.error(f"Password reset email error: {e}")
    return {"status": "ok", "message": "Si un compte existe, un email a ete envoye"}

@auth_router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, req: Request = None, db: AsyncSession = Depends(get_db)):
    # Rate limit: 5 reset submissions per IP per 15 minutes
    client_ip = req.client.host if req else "unknown"
    if rate_limiter.is_rate_limited(f"reset-submit:{client_ip}", max_attempts=5, window_seconds=900):
        raise HTTPException(status_code=429, detail="Trop de tentatives. Reessayez dans quelques minutes.")
    # Validate new password length
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caracteres")
    try:
        payload = jwt.decode(request.token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Token invalide")
        user_id = payload.get("sub")
        token_jti = payload.get("jti", "")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Le lien a expire")
    except Exception:
        raise HTTPException(status_code=400, detail="Token invalide")
    # Check user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Token invalide")
    # Fix #45 — Prevent token reuse: check if jti was already used
    used_jti = (user.settings or {}).get("last_reset_jti", "")
    if token_jti and used_jti == token_jti:
        raise HTTPException(status_code=400, detail="Ce lien a deja ete utilise")
    hashed = hash_password(request.new_password)
    # Mark token as used by storing jti
    new_settings = {**(user.settings or {}), "last_reset_jti": token_jti}
    await db.execute(update(User).where(User.id == user_id).values(password_hash=hashed, settings=new_settings))
    await db.commit()
    return {"status": "ok", "message": "Mot de passe reinitialise avec succes"}

@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    """Refresh an expired token within a 7-day grace period.
    Accepts the old (expired) token in the Authorization header and returns a new one."""
    client_ip = request.client.host if request else "unknown"
    if rate_limiter.is_rate_limited(f"refresh:{client_ip}", max_attempts=10, window_seconds=600):
        raise HTTPException(status_code=429, detail="Trop de tentatives de rafraichissement")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")
    old_token = auth_header.split(" ", 1)[1]
    try:
        # Decode WITHOUT verifying expiration — accept expired tokens within grace period
        payload = jwt.decode(old_token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalide")
        # Check the token isn't too old (grace: 7 days past expiration)
        exp = payload.get("exp", 0)
        now_ts = datetime.now(timezone.utc).timestamp()
        grace_seconds = 7 * 24 * 3600  # 7 days
        if now_ts - exp > grace_seconds:
            raise HTTPException(status_code=401, detail="Token trop ancien, reconnexion requise")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh decode error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail="Token invalide")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    if hasattr(user, 'is_active') and user.is_active is False:
        raise HTTPException(status_code=403, detail="Compte desactive")
    new_token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=new_token, user=user_to_response(user))

@auth_router.post("/emergency-reset")
async def emergency_reset(data: Dict[str, str], request: Request = None, db: AsyncSession = Depends(get_db)):
    """Emergency password reset — requires ADMIN_RESET_SECRET env var (fix #3)."""
    # Rate limit: 3 attempts per IP per 30 minutes
    client_ip = request.client.host if request else "unknown"
    if rate_limiter.is_rate_limited(f"emergency:{client_ip}", max_attempts=3, window_seconds=1800):
        raise HTTPException(status_code=429, detail="Trop de tentatives")
    secret = data.get("secret", "")
    email = data.get("email", "")
    new_password = data.get("new_password", "")
    admin_secret = os.environ.get("ADMIN_RESET_SECRET")
    if not admin_secret:
        raise HTTPException(status_code=503, detail="Réinitialisation d'urgence non configurée")
    client_ip = request.client.host if request else "unknown"
    if not hmac.compare_digest(secret, admin_secret):
        logger.warning(f"Emergency reset FAILED attempt for {email} from {client_ip}")
        raise HTTPException(status_code=403, detail="Accès interdit")
    if not email or not new_password:
        raise HTTPException(status_code=400, detail="Email et nouveau mot de passe requis")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    hashed = hash_password(new_password)
    await db.execute(update(User).where(User.id == user.id).values(password_hash=hashed))
    await db.commit()
    logger.info(f"Emergency password reset for {email} from {client_ip}")
    return {"status": "ok", "message": f"Password reset for {email}"}

@auth_router.post("/2fa/send-code")
async def send_2fa_code(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    code = str(random.randint(100000, 999999))
    await db.execute(update(User).where(User.id == user.id).values(
        settings={**(user.settings or {}), "pending_2fa_code": code, "pending_2fa_time": datetime.now(timezone.utc).isoformat()}
    ))
    await db.commit()
    html = f"""<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
        <h2 style="color:#1E3A8A;">Code de vérification - Extension IA by Zayado</h2>
        <div style="font-size:32px;font-weight:bold;color:#1E3A8A;padding:20px;background:#F5F5F0;border-radius:8px;text-align:center;letter-spacing:8px;">{code}</div>
        <p style="color:#666;font-size:12px;margin-top:20px;">Ce code expire dans 10 minutes.</p>
    </div>"""
    try:
        asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(user.email, user.name or "", "Code de vérification - Extension IA by Zayado", html))
    except Exception as e:
        logger.error(f"2FA email error: {e}")
        raise HTTPException(status_code=500, detail="Erreur d'envoi email")
    return {"status": "ok", "message": "Code envoye par email"}

@auth_router.post("/2fa/verify")
async def verify_2fa_code(data: Dict[str, str], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    code = data.get("code", "")
    if rate_limiter.is_rate_limited(f"2fa-verify-settings:{user.id}", max_attempts=8, window_seconds=600):
        raise HTTPException(status_code=429, detail="Trop de tentatives. Réessayez plus tard.")
    settings = user.settings or {}
    stored_code = settings.get("pending_2fa_code", "")
    stored_time = settings.get("pending_2fa_time", "")
    if not stored_code or not hmac.compare_digest(code, stored_code):
        raise HTTPException(status_code=400, detail="Code invalide")
    if stored_time:
        code_time = datetime.fromisoformat(stored_time)
        if (datetime.now(timezone.utc) - code_time).total_seconds() > 600:
            raise HTTPException(status_code=400, detail="Code expire")
    # Fix #46 — Delete 2FA code after successful verification
    new_settings = {**settings}
    new_settings.pop("pending_2fa_code", None)
    new_settings.pop("pending_2fa_time", None)
    new_settings["two_factor_enabled"] = True
    await db.execute(update(User).where(User.id == user.id).values(settings=new_settings))
    await db.commit()
    return {"status": "ok", "verified": True}

@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user_to_response(user)

@auth_router.put("/settings")
async def update_settings(settings: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ALLOWED_KEYS = {
        "default_mode", "language", "theme", "notifications", "timer_alert_hours",
        "creditAlert", "mode_switch_behavior", "dismissed_notifications",
        "bubble_position", "font_size", "auto_execute_agent", "kairos", "market",
    }
    current = dict(user.settings or {})
    for k, v in settings.items():
        if k in ALLOWED_KEYS:
            current[k] = v
    await db.execute(update(User).where(User.id == user.id).values(settings=current))
    await db.commit()
    return {"status": "success"}

@auth_router.put("/openai-key")
async def update_openai_key(data: Dict[str, str], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(update(User).where(User.id == user.id).values(openai_key=data.get("key")))
    await db.commit()
    return {"status": "success"}

@auth_router.put("/partner-url")
async def update_partner_url(data: Dict[str, str], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role not in ("partenaire", "presta-partenaire", "admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Acces reserve aux partenaires")
    url = data.get("url", "").strip()
    await db.execute(update(User).where(User.id == user.id).values(partner_url=url))
    await db.commit()
    return {"status": "success", "partner_url": url}

@auth_router.put("/profile")
async def update_profile(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    values = {}
    if "name" in data:
        values["name"] = data["name"]
    if "memory" in data:
        values["memory"] = data["memory"]
    # extension_logo_url n'est pas une colonne User — ignoré
    if values:
        await db.execute(update(User).where(User.id == user.id).values(**values))
        await db.commit()
    return {"status": "success"}


@auth_router.get("/partner-url")
async def get_partner_url(user: User = Depends(get_current_user)):
    return {"partner_url": user.partner_url or ""}

@auth_router.post("/test-openai-key")
async def test_openai_key(data: Dict[str, str], user: User = Depends(get_current_user)):
    key = data.get("key") or user.openai_key
    if not key:
        raise HTTPException(status_code=400, detail="No OpenAI key provided")
    try:
        import openai
        client = openai.OpenAI(api_key=key)
        response = client.chat.completions.create(model="gpt-4o-mini", max_tokens=10, messages=[{"role": "user", "content": "Say OK"}])
        return {"status": "valid", "model": "gpt-4o-mini", "response": response.choices[0].message.content}
    except Exception as e:
        return {"status": "invalid", "error": str(e)}

@auth_router.post("/notifications/check-credits")
async def check_low_credits(user: User = Depends(get_current_user)):
    threshold = (user.settings or {}).get("creditAlert", 100) if isinstance(user.settings, dict) else 100
    if user.credits < threshold and user.credits > 0:
        asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(
            user.email, user.name, "Credits faibles - Zayado AI",
            f'<div style="font-family:Arial;padding:20px;"><h2 style="color:#1E3A8A;">Credits faibles</h2><p>Il vous reste <strong style="color:#DC2626;">{user.credits} credits</strong>.</p><a href="https://app.zayado.net/pricing" style="background:#C7372F;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;">Recharger</a></div>'
        ))
        return {"status": "notification_sent", "credits": user.credits}
    return {"status": "ok", "credits": user.credits}

@auth_router.get("/usage")
async def get_user_usage(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    total_conversations = (await db.execute(select(func.count(Conversation.id)).where(Conversation.user_id == user.id))).scalar() or 0
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    conversations_7d = (await db.execute(select(func.count(Conversation.id)).where(Conversation.user_id == user.id, Conversation.created_at >= week_ago))).scalar() or 0
    total_credits_used = (await db.execute(select(func.coalesce(func.sum(Conversation.total_credits_used), 0)).where(Conversation.user_id == user.id))).scalar() or 0
    credits_used_7d = (await db.execute(select(func.coalesce(func.sum(Conversation.total_credits_used), 0)).where(Conversation.user_id == user.id, Conversation.created_at >= week_ago))).scalar() or 0
    total_projects = (await db.execute(select(func.count(Project.id)).where(Project.user_id == user.id))).scalar() or 0
    total_time_seconds = (await db.execute(select(func.coalesce(func.sum(Project.total_time_seconds), 0)).where(Project.user_id == user.id))).scalar() or 0
    total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
    return {
        "credits_remaining": total_credits, "credits_base": user.credits or 0,
        "credits_bonus": user.bonus_credits or 0, "credits_purchased": user.purchased_credits or 0,
        "total_credits_used": int(total_credits_used), "credits_used_7d": int(credits_used_7d),
        "total_conversations": total_conversations, "conversations_7d": conversations_7d,
        "total_projects": total_projects, "total_time_tracked_hours": round(total_time_seconds / 3600, 1),
        "plan": user.plan, "member_since": user.created_at.isoformat() if user.created_at else None
    }

@auth_router.post("/notifications/dismiss")
async def dismiss_notification(data: Dict[str, str], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    notification_id = data.get("notification_id", "")
    if not notification_id:
        raise HTTPException(status_code=400, detail="notification_id required")
    settings = dict(user.settings or {})
    dismissed = settings.get("dismissed_notifications", [])
    if notification_id not in dismissed:
        dismissed.append(notification_id)
    settings["dismissed_notifications"] = dismissed
    await db.execute(update(User).where(User.id == user.id).values(settings=settings))
    await db.commit()
    return {"status": "ok", "dismissed": dismissed}

@auth_router.get("/notifications/dismissed")
async def get_dismissed_notifications(user: User = Depends(get_current_user)):
    return {"dismissed": (user.settings or {}).get("dismissed_notifications", [])}

@auth_router.get("/export-data")
async def export_user_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conversations = (await db.execute(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.created_at.desc()))).scalars().all()
    convs_data = [{"id": c.id, "title": c.title, "mode": c.mode, "messages": c.messages or [], "created_at": c.created_at.isoformat() if c.created_at else None, "total_credits_used": c.total_credits_used or 0} for c in conversations]
    projects = (await db.execute(select(Project).where(Project.user_id == user.id))).scalars().all()
    projects_data = [{"id": p.id, "name": p.name, "hourly_rate": p.hourly_rate, "total_time_seconds": p.total_time_seconds} for p in projects]
    transactions = (await db.execute(select(Transaction).where(Transaction.user_id == user.id))).scalars().all()
    tx_data = [{"id": t.id, "type": t.type, "amount": t.amount, "status": t.status} for t in transactions]
    return {"user": {"email": user.email, "name": user.name, "plan": user.plan, "credits": user.credits}, "conversations": convs_data, "projects": projects_data, "transactions": tx_data}

@auth_router.delete("/delete-account")
async def delete_user_account(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Suppression définitive du compte (RGPD). Confirmation côté serveur requise.

    Le client DOIT passer un body JSON `{"confirm": "SUPPRIMER"}` (en-tête
    Content-Type: application/json) pour éviter les suppressions accidentelles
    via un JWT volé ou un appel direct API.
    """
    # ── Confirmation serveur (anti-erreur / anti-replay) ─────────────────
    try:
        raw = await request.body()
        bdata = json.loads(raw) if raw else {}
    except Exception:
        bdata = {}
    confirm = str(bdata.get("confirm") or "").strip().upper()
    if confirm != "SUPPRIMER":
        raise HTTPException(
            status_code=400,
            detail="Confirmation requise — passer {\"confirm\": \"SUPPRIMER\"} dans le body."
        )

    user_id, user_email, user_name = user.id, user.email, user.name or ""
    await db.execute(delete(Conversation).where(Conversation.user_id == user_id))
    await db.execute(delete(Project).where(Project.user_id == user_id))
    await db.execute(delete(Workflow).where(Workflow.user_id == user_id))
    await db.execute(delete(Folder).where(Folder.user_id == user_id))
    # Transaction n'a pas de colonne `user_email` — on anonymise via user_id seul.
    await db.execute(update(Transaction).where(Transaction.user_id == user_id).values(user_id="DELETED"))
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    try:
        _e = user_email
        _n = user_name
        asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(_e, _n, "Confirmation de suppression - Extension IA by Zayado",
            "<div style='font-family:Arial;padding:20px;'><h2 style='color:#1E3A8A;'>Compte supprime</h2><p>Votre compte et toutes vos donnees ont ete supprimes conformement au RGPD.</p></div>"))
    except Exception:
        pass
    return {"status": "ok", "message": "Votre compte et vos donnees ont ete supprimes."}

@auth_router.post("/apply-promo")
async def apply_promo_retention(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Apply a retention promo code (e.g. RESTE30) — used by anti-churn modal.
    If the code exists in PromoCode table, apply it normally.
    If not, treat RESTE30 as a special retention discount stored in user settings."""
    from models import PromoCode, PromoUsage
    try:
        raw = await request.body()
        bdata = json.loads(raw) if raw else {}
    except Exception:
        bdata = {}
    code_str = (bdata.get("code") or "").strip().upper()
    source = bdata.get("source", "")
    if not code_str:
        raise HTTPException(status_code=400, detail="Code requis")

    # Try to find the code in the PromoCode table first
    result = await db.execute(select(PromoCode).where(PromoCode.code == code_str, PromoCode.active == True))
    promo = result.scalar_one_or_none()

    if promo:
        # Normal promo code flow
        if promo.expires_at and promo.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Code promo expiré")
        if promo.current_uses >= promo.max_uses:
            raise HTTPException(status_code=400, detail="Code promo épuisé")
        existing_use = await db.execute(select(PromoUsage).where(PromoUsage.user_id == user.id, PromoUsage.promo_code_id == promo.id))
        if existing_use.scalar_one_or_none():
            # Already used — still return success for retention UX
            return {"status": "success", "message": "Réduction de fidélité déjà appliquée sur votre compte.", "credits_added": 0}
        credits_added = 0
        if promo.type == "credits":
            credits_added = int(promo.value)
            await db.execute(update(User).where(User.id == user.id).values(credits=User.credits + credits_added))
        db.add(PromoUsage(user_id=user.id, promo_code_id=promo.id))
        await db.execute(update(PromoCode).where(PromoCode.id == promo.id).values(current_uses=PromoCode.current_uses + 1))
        await db.commit()
        return {"status": "success", "message": f"Code {code_str} appliqué avec succès !", "credits_added": credits_added}

    # Fallback: RESTE30 is a special retention code — store discount in user settings
    if code_str == "RESTE30":
        current_settings = user.settings or {}
        if current_settings.get("retention_discount_applied"):
            return {"status": "success", "message": "Réduction de fidélité déjà appliquée sur votre compte.", "credits_added": 0}
        new_settings = {
            **current_settings,
            "retention_discount_applied": True,
            "retention_discount_code": code_str,
            "retention_discount_rate": 30,
            "retention_discount_months": 3,
            "retention_discount_applied_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.execute(update(User).where(User.id == user.id).values(settings=new_settings))
        await db.commit()
        return {"status": "success", "message": "Réduction de 30% appliquée pour 3 mois !", "credits_added": 0}

    raise HTTPException(status_code=404, detail="Code promo invalide ou expiré")


# ─── Routes sécurité manquantes ───────────────────────────────────────────────

@auth_router.get("/login-history")
async def get_login_history(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Historique des connexions (stocké dans user.settings)."""
    settings = user.settings or {}
    history = settings.get("login_history", [])
    return history[-20:][::-1]  # 20 dernières, plus récente en premier

@auth_router.get("/sessions")
async def get_sessions(user: User = Depends(get_current_user)):
    """Sessions actives (simplifiée — session courante uniquement)."""
    return [{"id": "current", "device": "Session courante", "ip": None, "is_current": True, "last_active": datetime.now(timezone.utc).isoformat()}]

@auth_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: User = Depends(get_current_user)):
    """Révoquer une session (stub — JWT stateless)."""
    if session_id == "current":
        raise HTTPException(400, "Impossible de révoquer la session courante")
    return {"ok": True}

@auth_router.get("/oauth-providers")
async def get_oauth_providers(user: User = Depends(get_current_user)):
    """Fournisseurs OAuth connectés."""
    settings = user.settings or {}
    return {
        "google": bool(settings.get("google_connected") or settings.get("gdrive_connected")),
        "microsoft": bool(settings.get("microsoft_connected") or settings.get("onedrive_connected"))
    }

@auth_router.post("/2fa/toggle")
async def toggle_2fa(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Activer / désactiver la 2FA par email."""
    settings = user.settings or {}
    current = bool(settings.get("two_factor_enabled", False))
    new_settings = {**settings, "two_factor_enabled": not current}
    await db.execute(update(User).where(User.id == user.id).values(settings=new_settings))
    await db.commit()
    return {"two_factor_enabled": not current}

@auth_router.get("/pre-delete-info")
async def pre_delete_info(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Informations avant suppression du compte."""
    convs = await db.execute(select(func.count()).select_from(Conversation).where(Conversation.user_id == user.id))
    projs = await db.execute(select(func.count()).select_from(Project).where(Project.user_id == user.id))
    return {
        "conversations": convs.scalar() or 0,
        "projects": projs.scalar() or 0,
        "credits": user.credits or 0,
        "plan": user.plan or "free",
        "member_since": user.created_at.isoformat() if user.created_at else None
    }


# ── Compte invité ─────────────────────────────────────────────────────────
import os as _os
from fastapi import HTTPException as _HTTPException



# ──────────────────────────────────────────────────────────────────────
# Magic-link & Guest login (used by frontend pages/Login.js)
# ──────────────────────────────────────────────────────────────────────
import re as _re
from pydantic import BaseModel

_EMAIL_RE = _re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

class _MagicReq(BaseModel):
    email: str

class _VerifyReq(BaseModel):
    token: str


def _is_preview_env() -> bool:
    """Allow guest login only in preview / local envs."""
    if os.environ.get("ALLOW_GUEST_LOGIN", "").lower() in ("1", "true", "yes"):
        return True
    pub = (os.environ.get("PUBLIC_FRONTEND_URL") or os.environ.get("REACT_APP_BACKEND_URL") or "").lower()
    return any(s in pub for s in ("preview", "emergentagent", "localhost"))


def _mask_email(email: str) -> str:
    try:
        name, dom = email.split("@", 1)
        if len(name) <= 2:
            return f"{name[0]}*@{dom}"
        return f"{name[0]}{'*' * (len(name) - 2)}{name[-1]}@{dom}"
    except Exception:
        return email


@auth_router.post("/request-link")
async def request_magic_link(
    body: _MagicReq,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Génère un lien magique (JWT 15 min). Envoi Brevo si configuré,
    sinon retourne le `dev_link` directement (mode preview)."""
    email = body.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Adresse email invalide.")

    # Rate limit (anti-spam)
    client_ip = request.client.host if request else "unknown"
    if rate_limiter.is_rate_limited(f"magic:{client_ip}", max_attempts=10, window_seconds=600):
        raise HTTPException(status_code=429, detail="Trop de demandes, réessayez plus tard.")

    # Auto-create user if not exists (passwordless onboarding)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        _auto_name = email.split("@")[0][:80]
        # Compte de test unique : « Thomas » (préville / démo) — nom propre capitalisé.
        if email == "thomas@zayado.fr":
            _auto_name = "Thomas"
        user = User(
            email=email,
            name=_auto_name,
            password_hash=hash_password(os.urandom(16).hex()),  # random unusable pwd
            role="user",
            plan="free",
            credits=200,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Magic token : JWT 15 min avec scope = magic
    magic_token = create_access_token({"sub": user.id, "scope": "magic"}, expires_minutes=15)

    # Build link
    public_base = (
        os.environ.get("PUBLIC_FRONTEND_URL")
        or os.environ.get("REACT_APP_BACKEND_URL", "")
    ).rstrip("/")
    dev_link = f"{public_base}/login?token={magic_token}" if public_base else f"/login?token={magic_token}"

    # Try Brevo (silently fall back to dev_link if not available)
    delivered = False
    try:
        from utils import send_brevo_email
        sent = send_brevo_email(
            to_email=email,
            subject="Votre lien de connexion — MyExtension-ai by Zayado",
            html_content=f"""<p>Bonjour,</p>
<p>Cliquez sur le lien ci-dessous pour vous connecter à <strong>MyExtension-ai by Zayado</strong> :</p>
<p><a href="{dev_link}" style="background:#0F1B3D;color:#fff;padding:10px 18px;border-radius:24px;text-decoration:none">Se connecter</a></p>
<p style="color:#777;font-size:13px;margin-top:18px">Ce lien expire dans 15 minutes.</p>
<p style="color:#777;font-size:13px">— L'équipe MyExtension-ai<br/><span style="color:#999">Votre extension IA. Elle prépare, vous décidez.</span></p>""",
            brand="myextension",
        )
        delivered = bool(sent)
    except Exception as e:
        logger.warning(f"[magic-link] Brevo unavailable, returning dev_link: {e}")

    # Sécurité : le lien direct (dev_link) n'est JAMAIS exposé en production.
    # Il n'est renvoyé que si ALLOW_GUEST_LOGIN=true (preview / local).
    expose_link = os.environ.get("ALLOW_GUEST_LOGIN", "").lower() == "true"

    # Défense en profondeur : même si ALLOW_GUEST_LOGIN=true a fuité en prod,
    # on bloque strictement l'exposition du dev_link si le hostname public
    # correspond à un domaine de production connu. La liste est lue depuis
    # l'env `PROD_HOSTNAMES` (CSV) pour permettre aux ops d'ajouter un domaine
    # sans redéployer. Si l'env est vide, on retombe sur la liste par défaut.
    _default_prod = "zayado.net,app.zayado.net,www.zayado.net,myextension-ai.com,www.myextension-ai.com,app.myextension-ai.com"
    _prod_hosts = tuple(
        h.strip().lower()
        for h in (os.environ.get("PROD_HOSTNAMES") or _default_prod).split(",")
        if h.strip()
    )
    try:
        _host_hdr = ""
        if request is not None:
            _host_hdr = (request.headers.get("host") or "").split(":")[0].lower()
            if not _host_hdr:
                _host_hdr = (request.url.hostname or "").lower()
        _public_host = ""
        if public_base:
            from urllib.parse import urlparse as _urlparse
            _public_host = (_urlparse(public_base).hostname or "").lower()
        if _host_hdr in _prod_hosts or _public_host in _prod_hosts:
            expose_link = False
    except Exception:
        # Ne jamais autoriser expose_link en cas de doute
        expose_link = False

    if delivered and not expose_link:
        return {
            "delivered_via_email": True,
            "sent_to": _mask_email(email),
            "masked_email": _mask_email(email),
            "expires_in_minutes": 15,
        }
    if expose_link:
        # Preview / local : on expose toujours le lien direct (pas d'accès à la boîte mail).
        return {
            "delivered_via_email": bool(delivered),
            "dev_link": dev_link,
            "masked_email": _mask_email(email),
            "expires_in_minutes": 15,
        }
    # Production + échec d'envoi d'email : on NE divulgue PAS le lien. Erreur propre.
    return {
        "delivered_via_email": False,
        "delivery_failed": True,
        "masked_email": _mask_email(email),
        "expires_in_minutes": 15,
    }


@auth_router.post("/verify-link")
async def verify_magic_link(body: _VerifyReq, db: AsyncSession = Depends(get_db)):
    """Vérifie un token magique et renvoie un JWT de session + user."""
    try:
        payload = jwt.decode(body.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Lien invalide ou expiré.")

    if payload.get("scope") != "magic":
        raise HTTPException(status_code=401, detail="Lien invalide.")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    # Anti-rejeu idempotent (fix #5 — React.StrictMode).
    # Avant : le 2e appel (StrictMode monte/démonte le composant, ou refresh)
    # trouvait le jti déjà consommé et renvoyait 401 → le front affichait
    # ?error=link_failed alors que la 1re vérification avait réussi.
    # Maintenant : on mémorise l'instant de 1re consommation par jti ; toute
    # reprise dans une courte fenêtre de grâce ré-émet la session SANS erreur
    # (idempotent), au-delà on rejette réellement (anti-rejeu conservé).
    token_jti = payload.get("jti", "")
    settings = user.settings or {}
    used = settings.get("used_magic_jti", {})
    if isinstance(used, list):  # backcompat ancien format (liste de jti)
        used = {j: None for j in used}
    if not isinstance(used, dict):
        used = {}
    now = datetime.now(timezone.utc)
    GRACE_SECONDS = 120
    if token_jti and token_jti in used:
        first_iso = used.get(token_jti)
        within_grace = False
        if first_iso:
            try:
                within_grace = (now - datetime.fromisoformat(first_iso)).total_seconds() <= GRACE_SECONDS
            except Exception:
                within_grace = False
        if not within_grace:
            raise HTTPException(status_code=401, detail="Ce lien a déjà été utilisé.")
        # Fenêtre de grâce → idempotent : on continue et ré-émet une session.
    elif token_jti:
        used[token_jti] = now.isoformat()
        if len(used) > 20:  # garde les 20 derniers
            for k in list(used.keys())[:-20]:
                used.pop(k, None)
        await db.execute(update(User).where(User.id == user.id).values(
            settings={**settings, "used_magic_jti": used}
        ))
        await db.commit()

    # Full session JWT
    access_token = create_access_token({"sub": user.id})
    return {
        "token":        access_token,
        "access_token": access_token,
        "token_type":   "bearer",
        "user":         user_to_response(user),
    }


@auth_router.post("/guest")
async def guest_login(db: AsyncSession = Depends(get_db)):
    """Compte invité DÉSACTIVÉ.

    Le produit ne propose plus qu'un unique compte de test « Thomas »
    (thomas@zayado.fr, via lien magique en preview). L'ancien compte
    « Invité » (guest@zayado.preview) a été supprimé pour éviter la confusion.
    """
    raise HTTPException(status_code=410, detail="Le mode invité a été supprimé. Utilisez le compte test Thomas.")
