"""
Backend Dependencies - Authentification & Autorisation
CORRECTIONS APPLIQUÉES :
- ✅ JWT avec jti pour révocation (déjà présent)
- ✅ Vérification is_active ajoutée
- ✅ Validation JWT_SECRET au démarrage
- ✅ Documentation bcrypt 72 chars
- ✅ Suppression openai_api_key de UserResponse (sécurité)
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
import bcrypt as _bcrypt
from datetime import datetime, timezone, timedelta
import os
import uuid
import logging

from database import get_db
from models import User
from schemas import UserResponse

logger = logging.getLogger(__name__)

# ✅ JWT_SECRET avec validation stricte
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError(
        "❌ FATAL: JWT_SECRET environment variable is not set!\n"
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
        "Then set it: export JWT_SECRET='your-secret-here'"
    )

if len(JWT_SECRET) < 32:
    logger.warning("⚠️  JWT_SECRET is too short (< 32 chars). Security risk!")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 jours

security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash un mot de passe avec bcrypt.
    
    ⚠️  IMPORTANT: bcrypt tronque à 72 caractères.
    Les caractères au-delà sont ignorés silencieusement.
    """
    if len(password) > 72:
        logger.warning("Password > 72 chars will be truncated (bcrypt limitation)")
    
    return _bcrypt.hashpw(password[:72].encode(), _bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash bcrypt"""
    try:
        return _bcrypt.checkpw(plain_password[:72].encode(), hashed_password.encode())
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_minutes: int = None) -> str:
    """
    Crée un JWT access token avec jti pour révocation.
    
    Args:
        data: Données à encoder (doit contenir 'sub' pour user_id)
        expires_minutes: Durée de vie en minutes (optionnel)
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    # Ajout jti si absent
    if "jti" not in to_encode:
        to_encode["jti"] = str(uuid.uuid4())
    
    # Expiration
    if expires_minutes:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Crée un refresh token (30 jours) pour renouveler l'access token.
    #177 — Refresh token must be longer-lived than access token (30d vs 7d)
    """
    data = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur authentifié depuis le JWT.
    
    ✅ CORRECTIONS :
    - Vérification is_active ajoutée
    - Gestion erreurs DB améliorée
    - Logging explicite
    """
    try:
        # Décodage JWT
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Récupération utilisateur
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
        except Exception as db_err:
            logger.error(f"DB error for user {user_id}: {db_err}")
            # With NullPool, retry with a fresh session
            try:
                from database import async_session_factory
                async with async_session_factory() as fresh_db:
                    result = await fresh_db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
            except Exception as retry_err:
                logger.critical(f"DB retry failed: {retry_err}")
                raise HTTPException(status_code=503, detail="Service temporairement indisponible. Réessayez.")
        
        if user is None:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        
        # ✅ CORRECTION : Vérification is_active
        if not getattr(user, 'is_active', True):
            raise HTTPException(status_code=403, detail="Compte désactivé. Contactez le support.")
        
        return user
        
    except HTTPException:
        raise
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur d'authentification")


from fastapi import Header

async def _get_user_optional_impl(
    authorization: str | None,
    db: AsyncSession,
) -> User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and getattr(user, "is_active", True):
            return user
    except Exception:
        return None
    return None


async def get_current_user_optional(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Retourne l'utilisateur si auth valide, sinon None (pas d'erreur 401)."""
    return await _get_user_optional_impl(authorization, db)


async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Vérifie que l'utilisateur a des privilèges admin.
    """
    if user.role not in ("admin", "super_admin"):
        logger.warning(f"Unauthorized admin access attempt by user {user.id}")
        raise HTTPException(status_code=403, detail="Accès admin requis")
    
    return user


def user_to_response(user: User) -> UserResponse:
    """
    Conversion User → UserResponse avec fallbacks sécurisés.
    
    ✅ CORRECTION : openai_api_key retiré (sensible)
    """
    def _get(attr, default=None):
        """Helper pour récupérer un attribut avec fallback"""
        try:
            v = getattr(user, attr, default)
            return v if v is not None else default
        except Exception:
            return default

    # #11 — Remove sensitive internal keys from settings before returning to client
    raw_settings = _get("settings", {})
    if isinstance(raw_settings, dict):
        safe_settings = {k: v for k, v in raw_settings.items() if k not in ("pending_2fa_code", "pending_2fa_time", "last_reset_jti", "brevo_api_key")}
    else:
        safe_settings = raw_settings or {}

    resp = UserResponse(
        id=_get("id", ""),
        email=_get("email", ""),
        name=_get("name", ""),
        role=_get("role", "user"),
        credits=_get("credits", 0) or 0,
        bonus_credits=_get("bonus_credits", 0) or 0,
        purchased_credits=_get("purchased_credits", 0) or 0,
        plan=_get("plan", "free"),
        created_at=_get("created_at"),
        discount_type=_get("discount_type"),
        discount_percent=_get("discount_percent", 0) or 0,
        discount_verified=_get("discount_verified", False) or False,
        partner_code=_get("partner_code"),
        partner_url=_get("partner_url"),
        memory=_get("memory"),
        referral_code=_get("referral_code"),
        settings=safe_settings,
        is_active=_get("is_active", True),
        two_factor_enabled=_get("two_factor_enabled", False),
        thesustain_member=_get("thesustain_member", False),
        credits_last_reset=_get("credits_last_reset"),
        onboarding_done=bool(isinstance(raw_settings, dict) and raw_settings.get("onboarding_completed", False)),
    )
    try:
        from utils import SUBSCRIPTION_PLANS
        plan_info = next((p for p in SUBSCRIPTION_PLANS if p["id"] == _get("plan", "free")), None)
        resp.credits_per_month = plan_info.get("credits_per_month", 0) if plan_info else 0
    except Exception:
        resp.credits_per_month = 0
    return resp
