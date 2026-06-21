"""Branding configuration — gestion centralisée des logos, noms, couleurs.

Stockage : table `app_branding` (1 ligne unique, id='global').
Utilisé par :
- Email templates (svc utils.send_brevo_email)
- Notifications in-app (futur)
- Logo top-nav (futur, dynamique)

Brand model :
  - app_name        : nom de l'application (défaut "MyExtension AI")
  - platform_name   : nom de la plateforme (défaut "Zayado")
  - app_logo_url    : URL logo MyExtension AI
  - platform_logo_url : URL logo Zayado
  - email_footer    : texte footer email
  - primary_color   : #1B2A4A (navy)
  - secondary_color : #F9F6F0 (cream)
"""
import os
import json
import logging
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_admin_user

logger = logging.getLogger(__name__)
branding_router = APIRouter(tags=["branding"])

DEFAULT_BRANDING = {
    "app_name": "MyExtension AI",
    "platform_name": "Zayado",
    "app_logo_url": "",
    "platform_logo_url": "",
    "email_footer": "MyExtension AI est une application de la plateforme Zayado",
    "primary_color": "#1B2A4A",
    "secondary_color": "#F9F6F0",
    "accent_color": "#E8C36B",
    "support_email": "contact@zayado.net",
    "support_url": "https://zayado.net/contact",
}


async def _ensure_branding_table(db: AsyncSession):
    await db.execute(text(
        "CREATE TABLE IF NOT EXISTS app_branding ("
        "id VARCHAR(36) PRIMARY KEY, data JSON NOT NULL, "
        "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)"
    ))


async def get_branding(db: AsyncSession) -> dict:
    """Helper : lit la config branding (fallback DEFAULT_BRANDING)."""
    try:
        await _ensure_branding_table(db)
        r = await db.execute(text("SELECT data FROM app_branding WHERE id = 'global' LIMIT 1"))
        row = r.fetchone()
        if row:
            d = row[0]
            if isinstance(d, str):
                d = json.loads(d)
            return {**DEFAULT_BRANDING, **(d or {})}
    except Exception as e:
        logger.warning("get_branding failed: %s", e)
    return DEFAULT_BRANDING.copy()


class BrandingIn(BaseModel):
    app_name: str | None = None
    platform_name: str | None = None
    app_logo_url: str | None = None
    platform_logo_url: str | None = None
    email_footer: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    accent_color: str | None = None
    support_email: str | None = None
    support_url: str | None = None


@branding_router.get("/branding")
async def branding_public(db: AsyncSession = Depends(get_db)):
    """Lecture publique (utilisé par l'app pour afficher logos/noms).
    On expose tout sauf colonnes sensibles (aucune ici)."""
    return await get_branding(db)


@branding_router.patch("/admin/branding")
async def branding_update(body: BrandingIn, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _ensure_branding_table(db)
    current = await get_branding(db)
    patch = {k: v for k, v in body.dict().items() if v is not None}
    new = {**current, **patch}
    # Upsert
    r = await db.execute(text("SELECT id FROM app_branding WHERE id = 'global' LIMIT 1"))
    if r.fetchone():
        await db.execute(
            text("UPDATE app_branding SET data = :d WHERE id = 'global'"),
            {"d": json.dumps(new)},
        )
    else:
        await db.execute(
            text("INSERT INTO app_branding (id, data) VALUES ('global', :d)"),
            {"d": json.dumps(new)},
        )
    await db.commit()
    return new


@branding_router.post("/admin/branding/upload-logo")
async def branding_upload_logo(
    file: UploadFile = File(...),
    target: str = "app",   # "app" | "platform"
    admin=Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload un logo vers WordPress média, puis l'enregistre dans la config branding.
    Réutilise WP_BASE_URL + APP_PASSWORD pour héberger les médias (pas de stockage local)."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Le fichier doit être une image")
    content = await file.read()
    if len(content) > 3 * 1024 * 1024:
        raise HTTPException(413, "Image trop volumineuse (>3 Mo)")

    WP_BASE = os.environ.get("WP_BASE_URL", "").rstrip("/")
    WP_USER = os.environ.get("WP_USERNAME", "")
    WP_PASS = os.environ.get("WP_APP_PASSWORD", "")
    if not (WP_BASE and WP_USER and WP_PASS):
        raise HTTPException(500, "WordPress non configuré pour les uploads")

    import base64
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{WP_BASE}/wp-json/wp/v2/media",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Disposition": f'attachment; filename="{file.filename or "logo.png"}"',
                    "Content-Type": file.content_type,
                },
                content=content,
                timeout=30.0,
            )
            r.raise_for_status()
            data = r.json()
            url = data.get("source_url")
        except httpx.HTTPError as e:
            logger.error("WP media upload failed: %s", e)
            raise HTTPException(502, "Échec upload média WP")

    # Save in branding config
    field = "app_logo_url" if target == "app" else "platform_logo_url"
    await branding_update(BrandingIn(**{field: url}), admin, db)
    return {"url": url, "target": target, "field": field}


# ────────────────────────── Email template ──────────────────────────
def render_email(branding: dict, *, title: str, intro: str = "", body_html: str = "",
                 cta_label: str | None = None, cta_url: str | None = None) -> str:
    """Wrap un contenu HTML dans le template branded email.
    Header logo MyExtension AI, footer 'MyExtension AI est une application de la plateforme Zayado'.
    """
    primary = branding.get("primary_color", "#1B2A4A")
    secondary = branding.get("secondary_color", "#F9F6F0")
    app_name = branding.get("app_name", "MyExtension AI")
    platform_name = branding.get("platform_name", "Zayado")
    app_logo = branding.get("app_logo_url", "")
    footer_txt = branding.get("email_footer", "MyExtension AI est une application de la plateforme Zayado")
    support_url = branding.get("support_url", "https://zayado.net/contact")

    logo_html = (
        f'<img src="{app_logo}" alt="{app_name}" '
        f'style="height:32px;display:block;margin:0 auto" />'
    ) if app_logo else (
        f'<div style="font-family:Georgia,serif;color:{secondary};font-size:22px;'
        f'font-weight:600;letter-spacing:.5px">{app_name}</div>'
    )

    cta_html = ""
    if cta_label and cta_url:
        cta_html = (
            f'<p style="text-align:center;margin:28px 0 8px">'
            f'<a href="{cta_url}" style="background:{primary};color:{secondary};'
            f'padding:13px 26px;border-radius:999px;text-decoration:none;'
            f'font-family:Arial,sans-serif;font-size:14px;font-weight:600;display:inline-block">'
            f'{cta_label}</a></p>'
        )

    return f"""<!doctype html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:{secondary};font-family:Arial,Helvetica,sans-serif;color:#2A2A2A">
  <div style="max-width:600px;margin:0 auto;background:#fff">
    <div style="background:{primary};padding:24px 20px;text-align:center">
      {logo_html}
    </div>
    <div style="padding:36px 30px">
      <h1 style="font-family:Georgia,serif;color:{primary};font-size:24px;margin:0 0 14px">{title}</h1>
      {('<p style="font-size:15px;line-height:1.55;color:#3A3A3A">' + intro + '</p>') if intro else ''}
      <div style="font-size:14.5px;line-height:1.6;color:#2A2A2A">{body_html}</div>
      {cta_html}
    </div>
    <div style="background:#FAF7F2;padding:18px 30px;text-align:center;border-top:1px solid #E8E2D8">
      <p style="margin:0;font-size:12px;color:#7A7066;font-family:Arial,sans-serif">
        © {datetime.now(timezone.utc).year} {platform_name} · {footer_txt}
      </p>
      <p style="margin:6px 0 0;font-size:11px;color:#9A9088">
        <a href="{support_url}" style="color:#9A9088;text-decoration:none">Besoin d'aide ?</a>
      </p>
    </div>
  </div>
</body></html>"""
