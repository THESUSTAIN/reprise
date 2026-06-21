"""User integrations management — Brevo, Web Scraping, etc."""
import os
import logging
import re
import json
from typing import Dict, Any
from datetime import datetime, timezone

import httpx
import sib_api_v3_sdk
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from deps import get_current_user

logger = logging.getLogger(__name__)
integrations_router = APIRouter(prefix="/integrations", tags=["Integrations"])


def _get_user_integrations(user: User) -> dict:
    """Get integrations dict from user settings."""
    settings = user.settings or {}
    return settings.get("integrations", {})


def _mask_key(key: str) -> str:
    """Mask API key for display: show first 8 and last 4 chars."""
    if not key or len(key) < 16:
        return "***"
    return key[:8] + "..." + key[-4:]


# ─── GET all integrations status ───────────────────────────────────────
@integrations_router.get("")
async def get_integrations(user: User = Depends(get_current_user)):
    """Return status of all user integrations (keys masked)."""
    integrations = _get_user_integrations(user)
    brevo_key = integrations.get("brevo_api_key", "")
    brevo_sender = integrations.get("brevo_sender_email", "")
    brevo_sender_name = integrations.get("brevo_sender_name", "")

    return {
        "brevo": {
            "configured": bool(brevo_key),
            "key_preview": _mask_key(brevo_key) if brevo_key else None,
            "sender_email": brevo_sender or None,
            "sender_name": brevo_sender_name or None,
        },
        "scraping": {
            "configured": True,
            "status": "actif",
        },
    }


# ─── SAVE Brevo API key ───────────────────────────────────────────────
@integrations_router.put("/brevo")
async def save_brevo_key(
    data: Dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save user's Brevo API key and optional sender info."""
    api_key = (data.get("api_key") or "").strip()
    sender_email = (data.get("sender_email") or "").strip()
    sender_name = (data.get("sender_name") or "").strip()

    if not api_key:
        raise HTTPException(status_code=400, detail="Cle API Brevo requise")
    if not api_key.startswith("xkeysib-"):
        raise HTTPException(status_code=400, detail="Format de cle invalide. La cle Brevo commence par 'xkeysib-'")

    settings = dict(user.settings or {})
    integrations = dict(settings.get("integrations", {}))
    integrations["brevo_api_key"] = api_key
    if sender_email:
        integrations["brevo_sender_email"] = sender_email
    if sender_name:
        integrations["brevo_sender_name"] = sender_name
    settings["integrations"] = integrations

    await db.execute(update(User).where(User.id == user.id).values(settings=settings))
    await db.commit()

    logger.info(f"Brevo API key saved for user {user.email}")
    return {"status": "success", "message": "Cle Brevo sauvegardee"}


# ─── DELETE Brevo API key ──────────────────────────────────────────────
@integrations_router.delete("/brevo")
async def delete_brevo_key(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove user's Brevo API key."""
    settings = dict(user.settings or {})
    integrations = dict(settings.get("integrations", {}))
    integrations.pop("brevo_api_key", None)
    integrations.pop("brevo_sender_email", None)
    integrations.pop("brevo_sender_name", None)
    settings["integrations"] = integrations

    await db.execute(update(User).where(User.id == user.id).values(settings=settings))
    await db.commit()

    return {"status": "success", "message": "Cle Brevo supprimee"}


# ─── TEST Brevo key ───────────────────────────────────────────────────
@integrations_router.post("/brevo/test")
async def test_brevo_key(
    user: User = Depends(get_current_user),
):
    """Test if the user's Brevo API key is valid."""
    integrations = _get_user_integrations(user)
    api_key = integrations.get("brevo_api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="Aucune cle Brevo configuree")

    try:
        config = sib_api_v3_sdk.Configuration()
        config.api_key["api-key"] = api_key
        api_client = sib_api_v3_sdk.ApiClient(config)
        account_api = sib_api_v3_sdk.AccountApi(api_client)
        account = account_api.get_account()
        return {
            "status": "success",
            "valid": True,
            "account_email": account.email,
            "plan": getattr(account, "plan_type", None),
            "message": f"Connexion Brevo OK ({account.email})",
        }
    except Exception as e:
        logger.warning(f"Brevo test failed for {user.email}: {e}")
        return {
            "status": "error",
            "valid": False,
            "message": "Cle API invalide ou expiree. Verifiez votre cle sur app.brevo.com.",
        }


# ─── SEND EMAIL via user's Brevo ──────────────────────────────────────
@integrations_router.post("/brevo/send")
async def send_email_via_brevo(
    data: Dict[str, Any],
    user: User = Depends(get_current_user),
):
    """Send a transactional email using the user's own Brevo API key."""
    integrations = _get_user_integrations(user)
    api_key = integrations.get("brevo_api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="Cle Brevo non configuree. Ajoutez-la dans Parametres > Integrations.")

    to_email = (data.get("to_email") or "").strip()
    to_name = (data.get("to_name") or "").strip()
    subject = (data.get("subject") or "").strip()
    html_content = (data.get("html_content") or "").strip()
    text_content = (data.get("text_content") or "").strip()

    if not to_email or not subject:
        raise HTTPException(status_code=400, detail="Destinataire et sujet requis")

    sender_email = integrations.get("brevo_sender_email") or user.email
    sender_name = integrations.get("brevo_sender_name") or user.name or "ZAYADO Agent"

    try:
        config = sib_api_v3_sdk.Configuration()
        config.api_key["api-key"] = api_key
        api_client = sib_api_v3_sdk.ApiClient(config)
        email_api = sib_api_v3_sdk.TransactionalEmailsApi(api_client)

        email_obj = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email, "name": to_name or to_email}],
            sender={"email": sender_email, "name": sender_name},
            subject=subject,
            html_content=html_content or f"<p>{text_content}</p>",
        )
        response = email_api.send_transac_email(email_obj)

        logger.info(f"Email sent via user Brevo ({user.email}) to {to_email}: {response.message_id}")
        return {
            "status": "success",
            "message_id": str(response.message_id),
            "message": f"Email envoye a {to_email}",
        }
    except sib_api_v3_sdk.rest.ApiException as e:
        logger.error(f"Brevo send error for {user.email}: {e.status} {e.reason}")
        if e.status == 401:
            raise HTTPException(status_code=401, detail="Cle Brevo invalide. Verifiez votre cle API.")
        raise HTTPException(status_code=502, detail=f"Erreur Brevo: {e.reason}")
    except Exception as e:
        logger.error(f"Email send error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")


# ─── WEB SCRAPING ─────────────────────────────────────────────────────
@integrations_router.post("/scrape")
async def scrape_url(
    data: Dict[str, Any],
    user: User = Depends(get_current_user),
):
    """Scrape a URL and return cleaned text content."""
    url = (data.get("url") or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL requise")
    if not url.startswith("http"):
        url = "https://" + url

    # Basic URL validation
    if not re.match(r"https?://[^\s]+\.[^\s]+", url):
        raise HTTPException(status_code=400, detail="URL invalide")

    max_content_length = 500_000  # 500KB max
    timeout = 15.0

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=5) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code != 200:
            return {
                "status": "error",
                "message": f"La page a retourne le code {resp.status_code}",
                "url": url,
            }

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return {
                "status": "partial",
                "message": f"Type de contenu non HTML: {content_type}",
                "url": url,
                "text": resp.text[:2000] if len(resp.text) < max_content_length else resp.text[:2000],
            }

        html = resp.text[:max_content_length]
        soup = BeautifulSoup(html, "lxml")

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")

        # Extract main text
        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive newlines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Truncate if too long
        if len(clean_text) > 8000:
            clean_text = clean_text[:8000] + "\n\n[... contenu tronque]"

        # Extract links
        links = []
        for a in soup.find_all("a", href=True)[:20]:
            href = a["href"]
            link_text = a.get_text(strip=True)[:100]
            if href.startswith("http") and link_text:
                links.append({"text": link_text, "url": href})

        logger.info(f"Scrape OK for {user.email}: {url} ({len(clean_text)} chars)")
        return {
            "status": "success",
            "url": url,
            "title": title,
            "meta_description": meta_desc,
            "text": clean_text,
            "links": links,
            "word_count": len(clean_text.split()),
        }
    except httpx.TimeoutException:
        return {"status": "error", "message": "Timeout — la page n'a pas repondu dans les 15 secondes", "url": url}
    except httpx.ConnectError:
        return {"status": "error", "message": "Impossible de se connecter a cette URL", "url": url}
    except Exception as e:
        logger.error(f"Scrape error for {url}: {e}")
        return {"status": "error", "message": f"Erreur de scraping: {str(e)[:200]}", "url": url}
