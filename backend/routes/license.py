"""
Routes Licences — Système de licence chatbot B2B ZAYADO
Fonctionnalités : créer licence (admin), activer par code, valider, télécharger package
"""
import uuid, secrets, json, io, zipfile
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import User, License, Team, TeamMember

license_router = APIRouter(prefix="/license", tags=["License"])
bearer = HTTPBearer(auto_error=False)


def utcnow():
    return datetime.now(timezone.utc)


async def get_user(creds, db):
    if not creds:
        raise HTTPException(status_code=401, detail="Non authentifie")
    import jwt, os
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


PLAN_CONFIG = {
    "chatbot_starter": {"max_chatbots": 1, "monthly_credits": 1000, "is_lifetime": False, "is_downloadable": False},
    "chatbot_pro": {"max_chatbots": 3, "monthly_credits": 5000, "is_lifetime": False, "is_downloadable": False},
    "chatbot_lifetime": {"max_chatbots": 3, "monthly_credits": 2000, "is_lifetime": True, "is_downloadable": True},
    "pilote_chatbot_lifetime": {"max_chatbots": -1, "monthly_credits": 5000, "is_lifetime": True, "is_downloadable": True},
}

PLAN_LABELS = {
    "chatbot_starter": "Chatbot Starter",
    "chatbot_pro": "Chatbot Pro",
    "chatbot_lifetime": "Chatbot B2B — Licence a Vie",
    "pilote_chatbot_lifetime": "Pilote + Chatbot — Licence a Vie Premium",
}


# ── Pydantic models ────────────────────────────

class CreateLicenseRequest(BaseModel):
    plan_type: str
    quantity: int = 1

class ActivateLicenseRequest(BaseModel):
    code: str
    team_name: Optional[str] = None

class RevokeLicenseRequest(BaseModel):
    license_id: str


# ── Admin: Create licenses ────────────────────

@license_router.post("/admin/create")
async def create_licenses(body: CreateLicenseRequest, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin requis")
    if body.plan_type not in PLAN_CONFIG:
        raise HTTPException(status_code=400, detail=f"Plan invalide. Choix: {list(PLAN_CONFIG.keys())}")

    config = PLAN_CONFIG[body.plan_type]
    created = []
    for _ in range(min(body.quantity, 50)):
        code = f"ZAYA-{body.plan_type.split('_')[0].upper()[:3]}-{secrets.token_hex(4).upper()}"
        lic = License(
            id=str(uuid.uuid4()),
            code=code,
            plan_type=body.plan_type,
            status="active",
            max_chatbots=config["max_chatbots"],
            monthly_credits=config["monthly_credits"],
            is_lifetime=config["is_lifetime"],
            is_downloadable=config["is_downloadable"],
        )
        db.add(lic)
        created.append({"code": code, "plan_type": body.plan_type, "plan_label": PLAN_LABELS.get(body.plan_type, body.plan_type)})
    await db.commit()
    return {"success": True, "licenses": created, "count": len(created)}


# ── Admin: List all licenses ──────────────────

@license_router.get("/admin/list")
async def list_licenses(db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin requis")

    result = await db.execute(select(License).order_by(License.created_at.desc()))
    licenses = result.scalars().all()
    items = []
    for lic in licenses:
        activated_email = None
        if lic.activated_by:
            u_result = await db.execute(select(User.email).where(User.id == lic.activated_by))
            activated_email = u_result.scalar_one_or_none()
        items.append({
            "id": lic.id,
            "code": lic.code,
            "plan_type": lic.plan_type,
            "plan_label": PLAN_LABELS.get(lic.plan_type, lic.plan_type),
            "status": lic.status,
            "activated_by_email": activated_email,
            "activated_at": lic.activated_at.isoformat() if lic.activated_at else None,
            "team_id": lic.team_id,
            "max_chatbots": lic.max_chatbots,
            "monthly_credits": lic.monthly_credits,
            "is_lifetime": lic.is_lifetime,
            "is_downloadable": lic.is_downloadable,
            "created_at": lic.created_at.isoformat() if lic.created_at else None,
        })
    return {"licenses": items}


# ── Admin: Revoke license ─────────────────────

@license_router.post("/admin/revoke")
async def revoke_license(body: RevokeLicenseRequest, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin requis")
    result = await db.execute(select(License).where(License.id == body.license_id))
    lic = result.scalar_one_or_none()
    if not lic:
        raise HTTPException(status_code=404, detail="Licence introuvable")
    lic.status = "revoked"
    await db.commit()
    return {"success": True, "status": "revoked"}


# ── Public: Activate license ──────────────────

@license_router.post("/activate")
async def activate_license(body: ActivateLicenseRequest, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    result = await db.execute(select(License).where(License.code == body.code.strip().upper()))
    lic = result.scalar_one_or_none()
    if not lic:
        raise HTTPException(status_code=404, detail="Code licence invalide")
    if lic.status == "used":
        raise HTTPException(status_code=400, detail="Cette licence a deja ete activee")
    if lic.status == "revoked":
        raise HTTPException(status_code=400, detail="Cette licence a ete revoquee")
    if lic.status == "expired":
        raise HTTPException(status_code=400, detail="Cette licence a expire")

    # Create a team for the chatbot
    team_name = body.team_name or f"Chatbot {user.name}"
    team_code = "ZAYA-" + secrets.token_hex(3).upper()
    team = Team(
        id=str(uuid.uuid4()),
        name=team_name,
        owner_id=user.id,
        shared_credits=lic.monthly_credits,
        max_seats=10,
        team_code=team_code,
        bot_name="Assistant",
        bot_tone="professional",
        chatbot_enabled=True,
    )
    db.add(team)

    # Add user as owner member
    member = TeamMember(
        id=str(uuid.uuid4()),
        team_id=team.id,
        user_id=user.id,
        email=user.email,
        role="owner",
        status="active",
        joined_at=utcnow(),
    )
    db.add(member)

    # Upgrade user plan if lifetime
    config = PLAN_CONFIG.get(lic.plan_type, {})
    if config.get("is_lifetime"):
        user.plan = "team"
    elif lic.plan_type == "chatbot_pro":
        user.plan = "pro"
    elif lic.plan_type == "chatbot_starter":
        user.plan = "pro"

    # Add credits
    user.credits = (user.credits or 0) + lic.monthly_credits

    # Mark license as used
    lic.status = "used"
    lic.activated_by = user.id
    lic.activated_at = utcnow()
    lic.team_id = team.id

    await db.commit()
    return {
        "success": True,
        "team_id": team.id,
        "team_name": team_name,
        "plan_type": lic.plan_type,
        "plan_label": PLAN_LABELS.get(lic.plan_type, lic.plan_type),
        "credits_added": lic.monthly_credits,
        "is_lifetime": lic.is_lifetime,
        "is_downloadable": lic.is_downloadable,
        "max_chatbots": lic.max_chatbots,
    }


# ── User: Get my licenses ─────────────────────

@license_router.get("/my")
async def my_licenses(db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    result = await db.execute(select(License).where(License.activated_by == user.id).order_by(License.activated_at.desc()))
    licenses = result.scalars().all()
    items = []
    for lic in licenses:
        items.append({
            "id": lic.id,
            "code": lic.code,
            "plan_type": lic.plan_type,
            "plan_label": PLAN_LABELS.get(lic.plan_type, lic.plan_type),
            "status": lic.status,
            "team_id": lic.team_id,
            "max_chatbots": lic.max_chatbots,
            "monthly_credits": lic.monthly_credits,
            "is_lifetime": lic.is_lifetime,
            "is_downloadable": lic.is_downloadable,
            "activated_at": lic.activated_at.isoformat() if lic.activated_at else None,
        })
    return {"licenses": items}


# ── User: Validate a code (pre-check) ─────────

@license_router.get("/validate/{code}")
async def validate_license(code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(License).where(License.code == code.strip().upper()))
    lic = result.scalar_one_or_none()
    if not lic:
        return {"valid": False, "reason": "Code invalide"}
    if lic.status != "active":
        return {"valid": False, "reason": f"Licence {lic.status}"}
    return {
        "valid": True,
        "plan_type": lic.plan_type,
        "plan_label": PLAN_LABELS.get(lic.plan_type, lic.plan_type),
        "is_lifetime": lic.is_lifetime,
        "max_chatbots": lic.max_chatbots,
        "monthly_credits": lic.monthly_credits,
    }


# ── Download chatbot package (lifetime only) ──

@license_router.get("/download/{team_id}")
async def download_chatbot_package(team_id: str, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)

    # Verify license is downloadable
    result = await db.execute(select(License).where(License.activated_by == user.id, License.team_id == team_id, License.is_downloadable == True))
    lic = result.scalar_one_or_none()
    if not lic:
        raise HTTPException(status_code=403, detail="Licence non telechargeable ou introuvable")

    # Get team config
    t_result = await db.execute(select(Team).where(Team.id == team_id))
    team = t_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Equipe introuvable")

    # Build config JSON
    config = {
        "team_code": team.team_code,
        "bot_name": team.bot_name or "Assistant",
        "bot_tone": team.bot_tone or "professional",
        "primary_color": getattr(team, 'primary_color', None) or "#1D4E8A",
        "accent_color": getattr(team, 'accent_color', None) or "#C9A84C",
        "logo_url": getattr(team, 'logo_url', None) or "",
        "footer_text": getattr(team, 'footer_text', None) or "",
        "welcome_message": getattr(team, 'welcome_message', None) or f"Bonjour ! Je suis {team.bot_name or 'votre assistant'}. Comment puis-je vous aider ?",
        "api_endpoint": "https://www.extension-ia.com/api/team/chatbot/public",
    }

    widget_js = f"""/**
 * ZAYADO Chatbot Widget v1.0
 * Licence: {lic.code}
 * Equipe: {team.name}
 * 
 * Integration: Ajoutez ce script dans votre page HTML
 * <script src="widget.js"></script>
 */
(function() {{
  var CONFIG = {json.dumps(config, indent=2, ensure_ascii=False)};
  
  var container = document.createElement('div');
  container.id = 'zayado-chatbot-widget';
  container.innerHTML = '<div id="zayado-chat-bubble" style="position:fixed;bottom:20px;right:20px;width:60px;height:60px;border-radius:50%;background:' + CONFIG.primary_color + ';display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.15);z-index:9999;transition:transform 0.2s"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg></div>';
  document.body.appendChild(container);
  
  var bubble = document.getElementById('zayado-chat-bubble');
  var chatOpen = false;
  var chatFrame = null;
  
  bubble.addEventListener('click', function() {{
    if (!chatOpen) {{
      chatFrame = document.createElement('iframe');
      chatFrame.src = CONFIG.api_endpoint.replace('/api/team/chatbot/public', '') + '/chatbot/' + CONFIG.team_code;
      chatFrame.style.cssText = 'position:fixed;bottom:90px;right:20px;width:380px;height:550px;border:none;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,0.2);z-index:9998;';
      document.body.appendChild(chatFrame);
      chatOpen = true;
    }} else {{
      if (chatFrame) chatFrame.remove();
      chatOpen = false;
    }}
  }});
}})();"""

    style_css = f"""/* ZAYADO Chatbot Widget Styles */
#zayado-chatbot-widget {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}
#zayado-chat-bubble:hover {{
  transform: scale(1.1);
}}
"""

    readme = f"""# ZAYADO Chatbot Widget — {team.name}

## Installation

### Option 1 : Script simple
Ajoutez avant la fermeture de `</body>` :
```html
<script src="widget.js"></script>
```

### Option 2 : Integration avancee
Modifiez `config.json` selon vos besoins puis :
```html
<link rel="stylesheet" href="style.css">
<script src="widget.js"></script>
```

## Configuration (config.json)
- `bot_name` : Nom affiche du chatbot
- `bot_tone` : Ton (professional, friendly, casual)
- `primary_color` : Couleur principale (hex)
- `accent_color` : Couleur d'accent (hex)
- `logo_url` : URL de votre logo
- `footer_text` : Texte "Propulse par [votre texte]"
- `welcome_message` : Message d'accueil
- `api_endpoint` : Endpoint API ZAYADO (ne pas modifier sauf BYOK)

## Support
Email: support@zayado.net
Licence: {lic.code}
"""

    # Create ZIP
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('widget.js', widget_js)
        zf.writestr('style.css', style_css)
        zf.writestr('config.json', json.dumps(config, indent=2, ensure_ascii=False))
        zf.writestr('README.md', readme)
    buffer.seek(0)

    filename = f"zayado-chatbot-{team.team_code}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
