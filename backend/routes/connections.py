"""User Connections — Secure service integrations for agents & workflows."""
import os
import json
import secrets
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from cryptography.fernet import Fernet

from database import get_db
from deps import get_current_user, User
from models import UserConnection

logger = logging.getLogger(__name__)

connections_router = APIRouter(prefix="/connections", tags=["Connections"])

# Fernet encryption for credentials at rest
_FERNET_KEY = os.environ.get("FERNET_KEY", "")
_fernet = Fernet(_FERNET_KEY.encode()) if _FERNET_KEY else None


def _encrypt(data: str) -> str:
    """Encrypt a string with Fernet. Falls back to plain if no key."""
    if _fernet:
        return _fernet.encrypt(data.encode()).decode()
    return data


def _decrypt(data: str) -> str:
    """Decrypt a Fernet-encrypted string. Falls back to plain."""
    if not _fernet or not data:
        return data
    try:
        return _fernet.decrypt(data.encode()).decode()
    except Exception:
        return data  # Already plain text (legacy)

# Available providers
PROVIDERS = [
    {
        "id": "brevo",
        "name": "Brevo (Email)",
        "description": "Envoi d'emails transactionnels et marketing",
        "icon": "mail",
        "color": "#0B996E",
        "fields": [
            {"key": "api_key", "label": "Cle API Brevo", "type": "password", "required": True},
            {"key": "sender_email", "label": "Email expediteur", "type": "email", "required": True},
            {"key": "sender_name", "label": "Nom expediteur", "type": "text", "required": False},
        ],
        "category": "email",
    },
    {
        "id": "smtp",
        "name": "SMTP Personnalise",
        "description": "Serveur SMTP personnalise (OVH, Ionos, etc.)",
        "icon": "server",
        "color": "#6366F1",
        "fields": [
            {"key": "host", "label": "Serveur SMTP", "type": "text", "required": True},
            {"key": "port", "label": "Port", "type": "number", "required": True},
            {"key": "username", "label": "Identifiant", "type": "text", "required": True},
            {"key": "password", "label": "Mot de passe", "type": "password", "required": True},
            {"key": "sender_email", "label": "Email expediteur", "type": "email", "required": True},
            {"key": "use_tls", "label": "Utiliser TLS", "type": "boolean", "required": False},
        ],
        "category": "email",
    },
    {
        "id": "whatsapp",
        "name": "WhatsApp Business",
        "description": "Envoi de messages WhatsApp via l'API Cloud",
        "icon": "message-circle",
        "color": "#25D366",
        "fields": [
            {"key": "phone_number_id", "label": "Phone Number ID", "type": "text", "required": True},
            {"key": "access_token", "label": "Access Token (permanent)", "type": "password", "required": True},
            {"key": "verify_token", "label": "Verify Token (webhook)", "type": "text", "required": False},
            {"key": "business_account_id", "label": "Business Account ID", "type": "text", "required": False},
            {"key": "app_secret", "label": "App Secret (Meta - pour signature HMAC)", "type": "password", "required": False},
        ],
        "category": "messaging",
    },
    {
        "id": "telegram",
        "name": "Telegram Bot",
        "description": "Bot Telegram pour notifications et conversations",
        "icon": "send",
        "color": "#0088CC",
        "fields": [
            {"key": "bot_token", "label": "Bot Token (@BotFather)", "type": "password", "required": True},
            {"key": "chat_id", "label": "Chat ID par defaut", "type": "text", "required": False},
            {"key": "webhook_url", "label": "URL Webhook (optionnel)", "type": "text", "required": False},
        ],
        "category": "messaging",
    },
    {
        "id": "ovh_phone",
        "name": "OVH Telephonie / SMS",
        "description": "Appels et SMS via OVH Telecom",
        "icon": "phone",
        "color": "#000E9C",
        "fields": [
            {"key": "application_key", "label": "Application Key", "type": "text", "required": True},
            {"key": "application_secret", "label": "Application Secret", "type": "password", "required": True},
            {"key": "consumer_key", "label": "Consumer Key", "type": "password", "required": True},
            {"key": "service_name", "label": "Nom du service (billing account)", "type": "text", "required": True},
            {"key": "sender", "label": "Expediteur SMS", "type": "text", "required": False},
        ],
        "category": "phone",
    },
    # ─── Productivité / outils bureautiques (API Key simples) ───
    {"id": "notion",     "name": "Notion",          "description": "Centralisez notes, docs, wikis et taches dans un espace de travail unifie.", "icon": "notebook", "color": "#000000",
        "fields": [{"key": "integration_token", "label": "Token d'integration (secret_...)", "type": "password", "required": True, "hint": "Obtenir sur notion.so/my-integrations"}],
        "help_url": "https://www.notion.so/my-integrations", "category": "productivity"},
    {"id": "slack",      "name": "Slack",           "description": "Messagerie par canaux pour vos equipes, integrations et recherche rapide.",   "icon": "slack",    "color": "#4A154B",
        "fields": [{"key": "webhook_url", "label": "Webhook URL (Incoming Webhook)", "type": "password", "required": True, "hint": "Creez un webhook sur api.slack.com/apps"}],
        "help_url": "https://api.slack.com/messaging/webhooks", "category": "productivity"},
    {"id": "discord",    "name": "Discord",         "description": "Bot Discord pour conversations et notifications communautaires.",              "icon": "hash",     "color": "#5865F2",
        "fields": [{"key": "webhook_url", "label": "Webhook URL Discord", "type": "password", "required": True, "hint": "Parametres salon > Integrations > Webhooks"}],
        "help_url": "https://support.discord.com/hc/en-us/articles/228383668", "category": "messaging"},
    {"id": "airtable",   "name": "Airtable",        "description": "Bases tableurs hybrides pour organiser projets, taches et workflows.",         "icon": "database", "color": "#FF6B35",
        "fields": [
            {"key": "api_key", "label": "Personal Access Token", "type": "password", "required": True, "hint": "airtable.com/create/tokens"},
            {"key": "base_id", "label": "Base ID par defaut (optionnel)", "type": "text", "required": False},
        ],
        "help_url": "https://airtable.com/create/tokens", "category": "productivity"},
    {"id": "asana",      "name": "Asana",           "description": "Suivi de taches, projets et collaboration pour equipes.",                      "icon": "target",   "color": "#F06A6A",
        "fields": [{"key": "access_token", "label": "Personal Access Token", "type": "password", "required": True, "hint": "app.asana.com > Mes parametres > Apps > Developer"}],
        "help_url": "https://developers.asana.com/docs/personal-access-token", "category": "productivity"},
    {"id": "trello",     "name": "Trello",          "description": "Tableaux kanban pour organiser projets et taches en equipe.",                  "icon": "columns",  "color": "#0052CC",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "password", "required": True},
            {"key": "token",   "label": "Token",   "type": "password", "required": True},
        ],
        "help_url": "https://trello.com/power-ups/admin", "category": "productivity"},
    {"id": "linear",     "name": "Linear",          "description": "Suivi d'incidents et planification produit rapide pour equipes modernes.",    "icon": "zap",      "color": "#5E6AD2",
        "fields": [{"key": "api_key", "label": "API Key (lin_api_...)", "type": "password", "required": True, "hint": "linear.app/settings/api"}],
        "help_url": "https://linear.app/settings/api", "category": "productivity"},
    {"id": "github",     "name": "GitHub",          "description": "Hebergement de code, revues et pipelines CI/CD.",                              "icon": "github",   "color": "#181717",
        "fields": [{"key": "personal_access_token", "label": "Personal Access Token (classic)", "type": "password", "required": True, "hint": "github.com/settings/tokens"}],
        "help_url": "https://github.com/settings/tokens", "category": "productivity"},
    {"id": "calendly",   "name": "Calendly",        "description": "Planification automatique de rendez-vous avec rappels.",                      "icon": "calendar", "color": "#006BFF",
        "fields": [{"key": "personal_access_token", "label": "Personal Access Token", "type": "password", "required": True, "hint": "calendly.com/integrations/api_webhooks"}],
        "help_url": "https://calendly.com/integrations/api_webhooks", "category": "productivity"},
    {"id": "hubspot",    "name": "HubSpot",         "description": "CRM, marketing automation et analyses de leads.",                             "icon": "heart",    "color": "#FF7A59",
        "fields": [{"key": "access_token", "label": "Private App Access Token", "type": "password", "required": True, "hint": "Settings > Integrations > Private Apps"}],
        "help_url": "https://developers.hubspot.com/docs/api/private-apps", "category": "productivity"},
    # ─── OAuth social (1 clic → plusieurs services) ───
    {"id": "google_workspace", "name": "Google Workspace", "description": "Connectez-vous avec Google et debloquez Gmail, Drive, Docs, Sheets, Calendar et Meet en un clic.",
        "icon": "google", "color": "#4285F4", "fields": [], "category": "productivity", "oauth_provider": "google",
        "includes": ["Gmail", "Drive", "Docs", "Sheets", "Calendar", "Meet"]},
    {"id": "microsoft_365",   "name": "Microsoft 365",    "description": "Connectez-vous avec Microsoft et debloquez Outlook, OneDrive, Teams et Office 365.",
        "icon": "microsoft", "color": "#0078D4", "fields": [], "category": "productivity", "oauth_provider": "microsoft",
        "includes": ["Outlook", "OneDrive", "Teams", "Office 365"]},
    # ─── Réseaux sociaux (OAuth a venir) ───
    {"id": "linkedin",   "name": "LinkedIn",        "description": "Reseau professionnel pour publications et prospection.",                      "icon": "linkedin", "color": "#0077B5", "fields": [], "category": "productivity", "coming_soon": True},
]


class ConnectionCreate(BaseModel):
    provider: str
    label: Optional[str] = None
    credentials: dict


class ConnectionUpdate(BaseModel):
    label: Optional[str] = None
    credentials: Optional[dict] = None
    is_active: Optional[bool] = None


@connections_router.get("/providers")
async def list_providers(user: User = Depends(get_current_user)):
    """List all available connection providers."""
    return PROVIDERS


@connections_router.get("")
async def list_connections(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List user's active connections."""
    result = await db.execute(
        select(UserConnection)
        .where(UserConnection.user_id == user.id, UserConnection.revoked_at.is_(None))
        .order_by(UserConnection.created_at.desc())
    )
    conns = result.scalars().all()
    return [_serialize(c) for c in conns]


@connections_router.post("")
async def create_connection(data: ConnectionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create a new service connection."""
    provider_info = next((p for p in PROVIDERS if p["id"] == data.provider), None)
    if not provider_info:
        raise HTTPException(400, f"Fournisseur inconnu: {data.provider}")
    if provider_info.get("coming_soon"):
        raise HTTPException(400, f"{provider_info['name']} sera disponible prochainement.")

    # Check required fields
    for field in provider_info.get("fields", []):
        if field["required"] and not data.credentials.get(field["key"]):
            raise HTTPException(400, f"Champ requis: {field['label']}")

    # Check if user already has this provider
    existing = (await db.execute(
        select(UserConnection).where(
            UserConnection.user_id == user.id,
            UserConnection.provider == data.provider,
            UserConnection.revoked_at.is_(None),
        )
    )).scalar_one_or_none()

    if existing:
        # Update existing connection
        existing.credentials = _encrypt(json.dumps(data.credentials))
        existing.label = data.label or provider_info["name"]
        existing.is_active = True
        existing.is_verified = False
        existing.verification_token = secrets.token_urlsafe(32)
        await db.commit()
        await db.refresh(existing)
        return _serialize(existing)

    # Create new
    verification_token = secrets.token_urlsafe(32)
    conn = UserConnection(
        user_id=user.id,
        provider=data.provider,
        label=data.label or provider_info["name"],
        credentials=_encrypt(json.dumps(data.credentials)),
        is_active=True,
        is_verified=False,
        verification_token=verification_token,
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)

    # Auto-test the connection
    test_result = await _test_connection(conn)
    if test_result["success"]:
        conn.is_verified = True
        await db.commit()
        await db.refresh(conn)

    return {**_serialize(conn), "test_result": test_result}


@connections_router.post("/{conn_id}/test")
async def test_connection(conn_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Test a connection."""
    conn = await _get_user_connection(conn_id, user.id, db)
    result = await _test_connection(conn)
    if result["success"]:
        conn.is_verified = True
        await db.commit()
    return result


@connections_router.put("/{conn_id}")
async def update_connection(conn_id: str, data: ConnectionUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Update a connection."""
    conn = await _get_user_connection(conn_id, user.id, db)
    if data.label is not None:
        conn.label = data.label
    if data.credentials is not None:
        conn.credentials = _encrypt(json.dumps(data.credentials))
        conn.is_verified = False  # Re-verify on credential change
    if data.is_active is not None:
        conn.is_active = data.is_active
    await db.commit()
    await db.refresh(conn)
    return _serialize(conn)


@connections_router.delete("/{conn_id}")
async def revoke_connection(conn_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Revoke (soft-delete) a connection."""
    conn = await _get_user_connection(conn_id, user.id, db)
    conn.revoked_at = datetime.now(timezone.utc)
    conn.is_active = False
    conn.verification_token = None
    await db.commit()
    return {"status": "revoked", "message": f"Connexion {conn.label} revoquee."}


async def _test_connection(conn: UserConnection) -> dict:
    """Test if a connection works."""
    try:
        raw = _decrypt(conn.credentials) if conn.credentials else "{}"
        creds = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"success": False, "error": "Credentials invalides"}

    if conn.provider == "brevo":
        return await _test_brevo(creds)
    elif conn.provider == "smtp":
        return await _test_smtp(creds)
    elif conn.provider == "whatsapp":
        return await _test_whatsapp(creds)
    elif conn.provider == "telegram":
        return await _test_telegram(creds)
    elif conn.provider == "ovh_phone":
        return await _test_ovh(creds)
    elif conn.provider == "notion":
        return await _test_notion(creds)
    elif conn.provider in ("slack", "discord"):
        return await _test_webhook(creds)
    elif conn.provider == "airtable":
        return await _test_airtable(creds)
    elif conn.provider == "asana":
        return await _test_asana(creds)
    elif conn.provider == "trello":
        return await _test_trello(creds)
    elif conn.provider == "linear":
        return await _test_linear(creds)
    elif conn.provider == "github":
        return await _test_github(creds)
    elif conn.provider == "calendly":
        return await _test_calendly(creds)
    elif conn.provider == "hubspot":
        return await _test_hubspot(creds)

    return {"success": False, "error": "Test non disponible pour ce fournisseur"}


# ─── Tests des nouveaux providers (ping API avec API key) ───
async def _test_notion(creds: dict) -> dict:
    import httpx
    token = creds.get("integration_token", "")
    if not token:
        return {"success": False, "error": "Token manquant"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get("https://api.notion.com/v1/users/me",
                headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
            if r.status_code == 200:
                return {"success": True, "message": f"Notion OK — {r.json().get('name','Bot connecte')}"}
            return {"success": False, "error": f"Notion rejette le token ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_webhook(creds: dict) -> dict:
    """Test Slack/Discord incoming webhook via une requete sans payload (verifie juste l'URL)."""
    import httpx
    url = creds.get("webhook_url", "")
    if not url or not url.startswith("https://"):
        return {"success": False, "error": "Webhook URL invalide"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            # POST vide => 400 attendu mais URL valide, 404/403 => URL invalide
            r = await c.post(url, json={})
            if r.status_code in (200, 204, 400):
                return {"success": True, "message": "Webhook accessible"}
            return {"success": False, "error": f"Webhook invalide ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_airtable(creds: dict) -> dict:
    import httpx
    token = creds.get("api_key", "")
    if not token:
        return {"success": False, "error": "API Key manquante"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get("https://api.airtable.com/v0/meta/whoami",
                headers={"Authorization": f"Bearer {token}"})
            if r.status_code == 200:
                return {"success": True, "message": f"Airtable OK — {r.json().get('email','connecte')}"}
            return {"success": False, "error": f"Airtable rejette le token ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_asana(creds: dict) -> dict:
    import httpx
    token = creds.get("access_token", "")
    if not token:
        return {"success": False, "error": "Token manquant"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get("https://app.asana.com/api/1.0/users/me",
                headers={"Authorization": f"Bearer {token}"})
            if r.status_code == 200:
                name = r.json().get("data", {}).get("name", "connecte")
                return {"success": True, "message": f"Asana OK — {name}"}
            return {"success": False, "error": f"Asana rejette le token ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_trello(creds: dict) -> dict:
    import httpx
    key = creds.get("api_key", "")
    token = creds.get("token", "")
    if not key or not token:
        return {"success": False, "error": "API Key ou Token manquant"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(f"https://api.trello.com/1/members/me?key={key}&token={token}")
            if r.status_code == 200:
                name = r.json().get("fullName", "connecte")
                return {"success": True, "message": f"Trello OK — {name}"}
            return {"success": False, "error": f"Trello rejette les credentials ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_linear(creds: dict) -> dict:
    import httpx
    key = creds.get("api_key", "")
    if not key:
        return {"success": False, "error": "API Key manquante"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post("https://api.linear.app/graphql",
                headers={"Authorization": key, "Content-Type": "application/json"},
                json={"query": "{ viewer { name email } }"})
            if r.status_code == 200 and "data" in r.json() and r.json()["data"].get("viewer"):
                name = r.json()["data"]["viewer"].get("name", "connecte")
                return {"success": True, "message": f"Linear OK — {name}"}
            return {"success": False, "error": f"Linear rejette le token ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_github(creds: dict) -> dict:
    import httpx
    token = creds.get("personal_access_token", "")
    if not token:
        return {"success": False, "error": "Personal Access Token manquant"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get("https://api.github.com/user",
                headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"})
            if r.status_code == 200:
                login = r.json().get("login", "connecte")
                return {"success": True, "message": f"GitHub OK — @{login}"}
            return {"success": False, "error": f"GitHub rejette le token ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_calendly(creds: dict) -> dict:
    import httpx
    token = creds.get("personal_access_token", "")
    if not token:
        return {"success": False, "error": "Personal Access Token manquant"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get("https://api.calendly.com/users/me",
                headers={"Authorization": f"Bearer {token}"})
            if r.status_code == 200:
                name = r.json().get("resource", {}).get("name", "connecte")
                return {"success": True, "message": f"Calendly OK — {name}"}
            return {"success": False, "error": f"Calendly rejette le token ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_hubspot(creds: dict) -> dict:
    import httpx
    token = creds.get("access_token", "")
    if not token:
        return {"success": False, "error": "Access Token manquant"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get("https://api.hubapi.com/account-info/v3/details",
                headers={"Authorization": f"Bearer {token}"})
            if r.status_code == 200:
                pid = r.json().get("portalId", "")
                return {"success": True, "message": f"HubSpot OK — Portal {pid}"}
            return {"success": False, "error": f"HubSpot rejette le token ({r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Erreur reseau: {str(e)[:120]}"}


async def _test_brevo(creds: dict) -> dict:
    """Test Brevo API key."""
    import httpx
    api_key = creds.get("api_key", "")
    if not api_key:
        return {"success": False, "error": "Cle API manquante"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.brevo.com/v3/account",
                headers={"api-key": api_key},
            )
            if resp.status_code == 200:
                data = resp.json()
                return {"success": True, "message": f"Connecte en tant que {data.get('email', 'OK')}"}
            elif resp.status_code == 401:
                return {"success": False, "error": "Cle API invalide ou expiree"}
            else:
                return {"success": False, "error": f"Erreur Brevo ({resp.status_code})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_smtp(creds: dict) -> dict:
    """Test SMTP connection."""
    import smtplib
    try:
        host = creds.get("host", "")
        port = int(creds.get("port", 587))
        username = creds.get("username", "")
        password = creds.get("password", "")
        use_tls = creds.get("use_tls", True)

        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        server.login(username, password)
        server.quit()
        return {"success": True, "message": f"Connecte a {host}:{port}"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "error": "Identifiants SMTP invalides"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_whatsapp(creds: dict) -> dict:
    """Test WhatsApp Business API connection."""
    import httpx
    access_token = creds.get("access_token", "")
    phone_number_id = creds.get("phone_number_id", "")
    if not access_token or not phone_number_id:
        return {"success": False, "error": "Access Token et Phone Number ID requis"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://graph.facebook.com/v18.0/{phone_number_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                display = data.get("display_phone_number", phone_number_id)
                return {"success": True, "message": f"WhatsApp connecte: {display}"}
            elif resp.status_code == 401:
                return {"success": False, "error": "Access Token invalide ou expire"}
            else:
                return {"success": False, "error": f"Erreur WhatsApp API ({resp.status_code})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_telegram(creds: dict) -> dict:
    """Test Telegram Bot Token."""
    import httpx
    bot_token = creds.get("bot_token", "")
    if not bot_token:
        return {"success": False, "error": "Bot Token requis"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    bot_name = data["result"].get("username", "Bot")
                    return {"success": True, "message": f"Bot Telegram connecte: @{bot_name}"}
                return {"success": False, "error": "Reponse invalide de Telegram"}
            elif resp.status_code == 401:
                return {"success": False, "error": "Bot Token invalide"}
            else:
                return {"success": False, "error": f"Erreur Telegram ({resp.status_code})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_ovh(creds: dict) -> dict:
    """Test OVH Telecom API credentials."""
    import httpx
    import hashlib
    import time
    app_key = creds.get("application_key", "")
    app_secret = creds.get("application_secret", "")
    consumer_key = creds.get("consumer_key", "")
    if not app_key or not app_secret or not consumer_key:
        return {"success": False, "error": "Application Key, Secret et Consumer Key requis"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get server time
            time_resp = await client.get("https://eu.api.ovh.com/1.0/auth/time")
            server_time = time_resp.text.strip()
            # Build OVH signature
            method = "GET"
            url = "https://eu.api.ovh.com/1.0/me"
            body = ""
            to_sign = f"{app_secret}+{consumer_key}+{method}+{url}+{body}+{server_time}"
            signature = "$1$" + hashlib.sha1(to_sign.encode()).hexdigest()
            resp = await client.get(url, headers={
                "X-Ovh-Application": app_key,
                "X-Ovh-Consumer": consumer_key,
                "X-Ovh-Timestamp": server_time,
                "X-Ovh-Signature": signature,
            })
            if resp.status_code == 200:
                data = resp.json()
                name = data.get("firstname", "") + " " + data.get("name", "")
                return {"success": True, "message": f"OVH connecte: {name.strip()}"}
            elif resp.status_code == 403:
                return {"success": False, "error": "Consumer Key invalide ou droits insuffisants"}
            else:
                return {"success": False, "error": f"Erreur OVH API ({resp.status_code})"}
    except Exception as e:
        return {"success": False, "error": str(e)}



def _serialize(conn: UserConnection) -> dict:
    """Serialize a connection (hide sensitive credentials)."""
    try:
        raw = _decrypt(conn.credentials) if conn.credentials else "{}"
        creds = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        creds = {}

    # Mask sensitive fields
    masked = {}
    SENSITIVE_KEYS = ("api_key", "password", "secret", "access_token", "bot_token",
                      "application_secret", "consumer_key")
    for k, v in creds.items():
        if k in SENSITIVE_KEYS and v:
            masked[k] = v[:4] + "****" + v[-4:] if len(str(v)) > 8 else "****"
        else:
            masked[k] = v

    return {
        "id": conn.id,
        "provider": conn.provider,
        "label": conn.label,
        "credentials_masked": masked,
        "is_active": conn.is_active,
        "is_verified": conn.is_verified,
        "last_used_at": conn.last_used_at.isoformat() if conn.last_used_at else None,
        "created_at": conn.created_at.isoformat() if conn.created_at else None,
    }


async def _get_user_connection(conn_id: str, user_id: str, db: AsyncSession) -> UserConnection:
    """Get a connection owned by user."""
    result = await db.execute(
        select(UserConnection).where(
            UserConnection.id == conn_id,
            UserConnection.user_id == user_id,
            UserConnection.revoked_at.is_(None),
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(404, "Connexion non trouvee")
    return conn


# ─── ADMIN : stats connexions utilisateurs ─────────────────────────────────
@connections_router.get("/admin/stats")
async def admin_connections_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Renvoie les stats de connexions aggregees par provider (admin only)."""
    if user.email != "admin@zayado.net" and not getattr(user, "is_admin", False):
        raise HTTPException(403, "Acces admin requis")

    from sqlalchemy import func, Integer, cast
    result = await db.execute(
        select(
            UserConnection.provider,
            func.count(UserConnection.id).label("total"),
            func.sum(cast(UserConnection.is_verified, Integer)).label("verified"),
        )
        .where(UserConnection.revoked_at.is_(None), UserConnection.is_active.is_(True))
        .group_by(UserConnection.provider)
    )
    per_provider = [
        {"provider": row[0], "total": int(row[1] or 0), "verified": int(row[2] or 0)}
        for row in result.all()
    ]
    per_provider.sort(key=lambda x: x["total"], reverse=True)

    total_connections = sum(p["total"] for p in per_provider)
    unique_users = await db.execute(
        select(func.count(func.distinct(UserConnection.user_id)))
        .where(UserConnection.revoked_at.is_(None), UserConnection.is_active.is_(True))
    )
    users_with_connections = int(unique_users.scalar() or 0)

    return {
        "total_connections": total_connections,
        "users_with_connections": users_with_connections,
        "per_provider": per_provider,
    }


@connections_router.get("/admin/list")
async def admin_connections_list(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), limit: int = 200):
    """Liste de toutes les connexions (admin only)."""
    if user.email != "admin@zayado.net" and not getattr(user, "is_admin", False):
        raise HTTPException(403, "Acces admin requis")

    result = await db.execute(
        select(UserConnection, User.email)
        .join(User, User.id == UserConnection.user_id)
        .where(UserConnection.revoked_at.is_(None))
        .order_by(UserConnection.created_at.desc())
        .limit(limit)
    )
    rows = []
    for conn, email in result.all():
        rows.append({
            "id": conn.id,
            "user_email": email,
            "provider": conn.provider,
            "label": conn.label,
            "is_active": conn.is_active,
            "is_verified": conn.is_verified,
            "last_used_at": conn.last_used_at.isoformat() if conn.last_used_at else None,
            "created_at": conn.created_at.isoformat() if conn.created_at else None,
        })
    return rows



# ─── OAuth 1-clic : Google Workspace & Microsoft 365 ───────────────────────

GOOGLE_WORKSPACE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "openid",
]

MS_365_SCOPES = [
    "openid", "profile", "email", "offline_access",
    "Mail.Read", "Mail.Send",
    "Files.ReadWrite.All",
    "Calendars.ReadWrite",
]


@connections_router.get("/oauth/{provider}/authorize")
async def oauth_authorize(provider: str, user: User = Depends(get_current_user)):
    """Renvoie l'URL OAuth à ouvrir en popup pour Google ou Microsoft."""
    import urllib.parse

    if provider == "google":
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        redirect_uri = os.environ.get("GOOGLE_CONNECTIONS_REDIRECT_URI") \
            or (os.environ.get("PUBLIC_APP_URL", "https://app.zayado.net") + "/api/connections/oauth/google/callback")
        if not client_id:
            raise HTTPException(500, "Google OAuth non configuré")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_WORKSPACE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": user.id,
        }
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
        return {"authorization_url": url}

    if provider == "microsoft":
        client_id = os.environ.get("MICROSOFT_CLIENT_ID", "")
        redirect_uri = os.environ.get("MICROSOFT_CONNECTIONS_REDIRECT_URI") \
            or (os.environ.get("PUBLIC_APP_URL", "https://app.zayado.net") + "/api/connections/oauth/microsoft/callback")
        if not client_id:
            raise HTTPException(500, "Microsoft OAuth non configuré")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "response_mode": "query",
            "scope": " ".join(MS_365_SCOPES),
            "state": user.id,
        }
        url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + urllib.parse.urlencode(params)
        return {"authorization_url": url}

    raise HTTPException(400, "Provider OAuth inconnu")


@connections_router.get("/oauth/google/callback")
async def oauth_google_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Callback Google : échange code → tokens → stocke connection google_workspace."""
    import httpx
    from fastapi.responses import HTMLResponse

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("GOOGLE_CONNECTIONS_REDIRECT_URI") \
        or (os.environ.get("PUBLIC_APP_URL", "https://app.zayado.net") + "/api/connections/oauth/google/callback")

    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            })
        if r.status_code != 200:
            return HTMLResponse(_oauth_popup_response(False, r.text[:200]), status_code=400)
        tokens = r.json()

        # Récupère l'email pour label
        async with httpx.AsyncClient(timeout=10.0) as c:
            prof = await c.get("https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"})
        email = prof.json().get("email", "") if prof.status_code == 200 else ""

        # Stocker / mettre à jour la connexion
        await _upsert_oauth_connection(
            db, user_id=state, provider="google_workspace",
            label=f"Google Workspace ({email})" if email else "Google Workspace",
            tokens=tokens,
        )
        return HTMLResponse(_oauth_popup_response(True))
    except Exception as e:
        logger.exception("Google OAuth callback failed")
        return HTMLResponse(_oauth_popup_response(False, str(e)[:200]), status_code=500)


@connections_router.get("/oauth/microsoft/callback")
async def oauth_microsoft_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Callback Microsoft : échange code → tokens → stocke connection microsoft_365."""
    import httpx
    from fastapi.responses import HTMLResponse

    client_id = os.environ.get("MICROSOFT_CLIENT_ID", "")
    client_secret = os.environ.get("MICROSOFT_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("MICROSOFT_CONNECTIONS_REDIRECT_URI") \
        or (os.environ.get("PUBLIC_APP_URL", "https://app.zayado.net") + "/api/connections/oauth/microsoft/callback")

    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "scope": " ".join(MS_365_SCOPES),
            })
        if r.status_code != 200:
            return HTMLResponse(_oauth_popup_response(False, r.text[:200]), status_code=400)
        tokens = r.json()

        # Récupère l'email via Graph
        async with httpx.AsyncClient(timeout=10.0) as c:
            prof = await c.get("https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"})
        email = ""
        if prof.status_code == 200:
            j = prof.json()
            email = j.get("mail") or j.get("userPrincipalName", "")

        await _upsert_oauth_connection(
            db, user_id=state, provider="microsoft_365",
            label=f"Microsoft 365 ({email})" if email else "Microsoft 365",
            tokens=tokens,
        )
        return HTMLResponse(_oauth_popup_response(True))
    except Exception as e:
        logger.exception("Microsoft OAuth callback failed")
        return HTMLResponse(_oauth_popup_response(False, str(e)[:200]), status_code=500)


async def _upsert_oauth_connection(db: AsyncSession, user_id: str, provider: str, label: str, tokens: dict):
    """Crée ou met à jour une UserConnection OAuth."""
    creds_json = json.dumps({
        "access_token":  tokens.get("access_token", ""),
        "refresh_token": tokens.get("refresh_token", ""),
        "token_type":    tokens.get("token_type", "Bearer"),
        "expires_in":    tokens.get("expires_in", 3600),
        "scope":         tokens.get("scope", ""),
        "id_token":      tokens.get("id_token", ""),
    })
    encrypted = _encrypt(creds_json)

    result = await db.execute(
        select(UserConnection).where(
            UserConnection.user_id == user_id,
            UserConnection.provider == provider,
            UserConnection.revoked_at.is_(None),
        )
    )
    conn = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if conn:
        conn.credentials = encrypted
        conn.label = label
        conn.is_active = True
        conn.is_verified = True
        conn.updated_at = now
    else:
        db.add(UserConnection(
            id=secrets.token_urlsafe(16),
            user_id=user_id,
            provider=provider,
            label=label,
            credentials=encrypted,
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
        ))
    await db.commit()


def _oauth_popup_response(success: bool, error: str = "") -> str:
    """Renvoie une page HTML qui poste un message à la fenêtre parente et se ferme."""
    safe_error = (error or "").replace("<", "&lt;").replace(">", "&gt;").replace("'", "\\'")
    status = "true" if success else "false"
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Connexion…</title>
<style>body{{font-family:-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#FAFAF8;color:#1D4E8A}}
.box{{text-align:center;padding:2rem}}h2{{margin:.5rem 0}}</style></head>
<body><div class="box"><h2>{'✅ Connexion réussie !' if success else '❌ Connexion échouée'}</h2>
<p>{('Cette fenêtre va se fermer automatiquement.' if success else safe_error)}</p></div>
<script>
try {{ window.opener && window.opener.postMessage({{source:'zayado-oauth', success:{status}, error:'{safe_error}'}}, '*'); }} catch(e){{}}
setTimeout(() => {{ try {{ window.close(); }} catch(e){{}} }}, 1200);
</script></body></html>"""
