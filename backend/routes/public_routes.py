"""
Public & Misc Routes (health, uploads, timer, seo, kyb, discounts) — extracted from server.py
"""
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
import os, uuid, json, httpx, asyncio, re, base64, logging, random

from database import get_db, async_session_factory
from models import User, Conversation, Project, Workflow, Transaction, PromoCode, PromoUsage, Folder, Team, TeamMember
from deps import get_current_user, get_admin_user, JWT_SECRET, JWT_ALGORITHM, security, hash_password, verify_password
from jose import jwt, JWTError
from utils import (
    MAMMOTH_BASE_URL, AGENT_DEFAULT_MODEL, AGENT_COMPLEX_MODEL, AGENT_MAX_TIMEOUT,
    AGENT_CREDITS_MAP, classify_task_type, estimate_agent_credits, select_agent_model,
    get_mollie_client, send_brevo_email, send_low_credits_notification,
    load_admin_config, save_admin_config,
    _get_email_log, _append_email_log, _append_admin_log, _get_admin_log,
    EMAIL_TEMPLATES, UPLOADS_DIR, GENERATED_IMAGES_DIR, CONFIG_PATH, logger as utils_logger
)

logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).parent

# WebSocket connections tracking
active_ws_connections: Dict[str, WebSocket] = {}

api_router = APIRouter()
# NOTE: Routes that were previously on ghost sub-routers (chat_router, auth_router, admin_router)
# have been moved to api_router with explicit path prefixes to ensure they are properly mounted.

@api_router.get("/")
async def root():
    return {"message": "Extension IA by Zayado API", "version": "1.0.0"}


class ContactFormRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)

@api_router.post("/contact")
async def submit_contact_form(body: ContactFormRequest):
    """Public contact form — sends email notification to admin."""
    try:
        admin_html = f"""
        <h2>Nouveau message de contact — Zayado</h2>
        <p><strong>Nom :</strong> {body.name}</p>
        <p><strong>Email :</strong> {body.email}</p>
        <p><strong>Sujet :</strong> {body.subject}</p>
        <p><strong>Message :</strong></p>
        <div style="background:#f5f3ef;padding:16px;border-radius:8px;margin:8px 0;">{body.message}</div>
        <hr>
        <p style="font-size:12px;color:#888;">Envoyé depuis le formulaire de contact Zayado</p>
        """
        send_brevo_email("contact@zayado.net", "Zayado", f"[Contact] {body.subject}", admin_html)

        confirmation_html = f"""
        <h2>Merci pour votre message, {body.name} !</h2>
        <p>Nous avons bien reçu votre demande et nous vous répondrons dans les plus brefs délais.</p>
        <p><strong>Sujet :</strong> {body.subject}</p>
        <p>Cordialement,<br>L'équipe Zayado<br>📞 01 83 64 39 99</p>
        """
        send_brevo_email(body.email, body.name, "Votre message a bien été reçu — Zayado", confirmation_html)

        return {"status": "success", "message": "Message envoyé avec succès"}
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        return {"status": "success", "message": "Message envoyé avec succès"}



class LeadFormRequest(BaseModel):
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    company: str = ""
    source: str = "simulateur"
    tool: str = ""
    results: dict = {}

@api_router.post("/lead")
async def submit_lead(body: LeadFormRequest):
    """Public lead form — adds contact to Brevo list #20 + sends rapport email."""
    try:
        from utils import add_brevo_contact, send_brevo_email
        add_brevo_contact(
            email=body.email,
            first_name=body.first_name,
            last_name=body.last_name,
            phone=body.phone,
            company=body.company,
            list_id=20,
        )
        full_name = f"{body.first_name} {body.last_name}".strip() or "cher client"
        company_name = body.company or "votre entreprise"

        # Load editable email template from admin config
        admin_config = load_admin_config()
        email_templates = admin_config.get("email_templates", {})
        rapport_tpl = email_templates.get("rapport_simulation", {})

        # Build results HTML based on tool type
        results_html = ""
        r = body.results
        if body.source == "analyse-financiere" and r:
            score = r.get("score", "—")
            score_color = "#16a34a" if int(score) >= 70 else "#1A3671" if int(score) >= 40 else "#C7372F"
            results_html = f"""
            <div style="background:#f9f7f2;border-radius:12px;padding:24px;margin:20px 0;">
                <div style="text-align:center;margin-bottom:16px;">
                    <div style="font-size:48px;font-weight:900;color:{score_color};">{score}<span style="font-size:20px;color:#9ca3af;">/100</span></div>
                    <div style="font-size:14px;font-weight:700;color:{score_color};">{r.get('status', '')}</div>
                </div>
                <table style="width:100%;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:10px 0;color:#6b7280;font-size:14px;">Rentabilité Nette</td><td style="padding:10px 0;text-align:right;font-weight:700;color:#0F1B2D;">{r.get('rentabilite', '—')} <span style="font-size:12px;color:{('#16a34a' if 'Bon' in r.get('rentabilite_badge','') else '#ca8a04')};">{r.get('rentabilite_badge', '')}</span></td></tr>
                    <tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:10px 0;color:#6b7280;font-size:14px;">Taux d'Endettement</td><td style="padding:10px 0;text-align:right;font-weight:700;color:#0F1B2D;">{r.get('endettement', '—')} <span style="font-size:12px;color:{('#16a34a' if 'Sain' in r.get('endettement_badge','') else '#ca8a04')};">{r.get('endettement_badge', '')}</span></td></tr>
                    <tr><td style="padding:10px 0;color:#6b7280;font-size:14px;">Solvabilité</td><td style="padding:10px 0;text-align:right;font-weight:700;color:#0F1B2D;">{r.get('solvabilite', '—')} <span style="font-size:12px;color:{('#16a34a' if 'Solide' in r.get('solvabilite_badge','') else '#ca8a04')};">{r.get('solvabilite_badge', '')}</span></td></tr>
                </table>
            </div>
            """
        elif body.source == "simulateur-rentabilite" and r:
            results_html = f"""
            <div style="background:#f9f7f2;border-radius:12px;padding:24px;margin:20px 0;">
                <div style="text-align:center;margin-bottom:16px;">
                    <div style="font-size:48px;font-weight:900;color:#1A3671;">{r.get('score', '—')}<span style="font-size:20px;color:#9ca3af;">/100</span></div>
                    <div style="font-size:14px;font-weight:700;color:#1A3671;">Score de viabilité</div>
                </div>
                <table style="width:100%;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:10px 0;color:#6b7280;font-size:14px;">Seuil de rentabilité</td><td style="padding:10px 0;text-align:right;font-weight:700;color:#0F1B2D;">{r.get('seuil', '—')}</td></tr>
                    <tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:10px 0;color:#6b7280;font-size:14px;">Bénéfice net prévu</td><td style="padding:10px 0;text-align:right;font-weight:700;color:#0F1B2D;">{r.get('benefice', '—')}</td></tr>
                    <tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:10px 0;color:#6b7280;font-size:14px;">Marge nette</td><td style="padding:10px 0;text-align:right;font-weight:700;color:#0F1B2D;">{r.get('marge', '—')}</td></tr>
                    <tr><td style="padding:10px 0;color:#6b7280;font-size:14px;">Point mort</td><td style="padding:10px 0;text-align:right;font-weight:700;color:#0F1B2D;">{r.get('point_mort', '—')}</td></tr>
                </table>
            </div>
            """
        elif body.source in ("creation-entreprise", "creation-entreprise-gratuit") and r:
            statut_val = r.get('statut', '')
            nom_soc = r.get('nom_societe', '')
            rdv_url = r.get('rdv_url', 'https://meet.brevo.com/adminzayado/support-se-lancer')
            # Check admin config for custom creation email template
            creation_tpl = email_templates.get("creation_entreprise", {})
            if creation_tpl.get("html"):
                rapport_html = creation_tpl["html"].replace("{{name}}", full_name).replace("{{statut}}", statut_val).replace("{{nom_societe}}", nom_soc).replace("{{rdv_url}}", rdv_url)
                subject = (creation_tpl.get("subject") or "Votre demande de création d'entreprise — Zayado").replace("{{name}}", full_name)
                send_brevo_email(body.email, full_name, subject, rapport_html)
            else:
                is_gratuit = body.source == "creation-entreprise-gratuit"
                subject = "Votre demande de création d'entreprise — Zayado"
                rapport_html = f"""<div style="font-family:'DM Sans',Arial,sans-serif;max-width:600px;margin:0 auto;background:#ffffff;">
<div style="background:linear-gradient(135deg,#0F1B2D,#1A3671);padding:32px;border-radius:12px 12px 0 0;text-align:center;">
<div style="display:inline-block;background:rgba(201,168,76,0.2);color:#C9A84C;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;margin-bottom:12px;">CRÉATION D'ENTREPRISE</div>
<h1 style="color:white;margin:0;font-size:22px;">{'Documents en préparation' if is_gratuit else 'Demande en cours'}</h1>
</div>
<div style="padding:32px;">
<p>Bonjour <strong>{full_name}</strong>,</p>
<p>{'Vos documents (statuts et PV pré-remplis) sont en cours de préparation et vous seront envoyés prochainement.' if is_gratuit else 'Vous n&#39;avez pas encore terminé votre demande de création d&#39;entreprise. Pas de souci, vous pouvez la reprendre à tout moment !'}</p>
<div style="background:#f9f7f2;border-radius:12px;padding:20px;margin:20px 0;">
<table style="width:100%;border-collapse:collapse;font-size:14px;">
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px 0;color:#6b7280;">Statut choisi</td><td style="padding:8px 0;text-align:right;font-weight:700;color:#0F1B2D;">{statut_val or 'Non défini'}</td></tr>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px 0;color:#6b7280;">Société</td><td style="padding:8px 0;text-align:right;font-weight:700;color:#0F1B2D;">{nom_soc or 'Non défini'}</td></tr>
<tr><td style="padding:8px 0;color:#6b7280;">Activité</td><td style="padding:8px 0;text-align:right;font-weight:700;color:#0F1B2D;">{r.get('activite', 'Non défini')}</td></tr>
</table>
</div>
{'<p style="text-align:center;"><strong>Frais administratifs à prévoir :</strong><br>Greffe (~36€) + Annonce légale (à partir de 270€, varie selon département)</p>' if is_gratuit else ''}
<p style="text-align:center;margin:24px 0;"><a href="https://app.zayado.net/fr/tarif-entreprise-creation-lancement" style="background:#C7372F;color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;">{'Reprendre ma demande' if not is_gratuit else 'Voir ma demande'}</a></p>
<div style="background:#EEF2FF;border:1px solid #C7D2FE;border-radius:8px;padding:16px;margin:20px 0;text-align:center;">
<p style="font-size:14px;font-weight:700;color:#1D4E8A;margin-bottom:8px;">Besoin d'aide ?</p>
<p style="font-size:13px;color:#6b7280;margin-bottom:12px;">Un expert vous accompagne dans vos démarches</p>
<a href="{rdv_url}" style="background:#1D4E8A;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;font-size:13px;">Prendre un rendez-vous gratuit</a>
</div>
<p style="color:#6b7280;font-size:13px;text-align:center;">L'équipe Zayado — 01 83 64 39 99</p>
</div>
</div>"""
                send_brevo_email(body.email, full_name, subject, rapport_html)
            # Skip default email below for creation
            return {"status": "ok", "message": "Lead captured"}
        elif body.source == "simulateur-statut" and r:
            statut = r.get('statut', '—')
            alt = r.get('alternative', '—')
            raison = r.get('raison', '')
            charges = r.get('charges', '—')
            charges_alt = r.get('charges_alt', '—')
            taux = r.get('taux', '—')
            taux_alt = r.get('taux_alt', '—')
            net = r.get('net', '—')
            net_alt = r.get('net_alt', '—')
            regime = r.get('regime', '—')
            regime_alt = r.get('regime_alt', '—')
            css_cout = r.get('css', '—')
            css_detail = r.get('css_detail', '')
            css_eligible = r.get('css_eligible', False)
            ca_prevu = r.get('ca_prevu', '—')

            def fmt(v):
                try: return f"{int(v):,}".replace(",", " ") + "€"
                except: return str(v)

            css_bg = "#F0FDF4" if css_eligible else "#FEF3C7"
            css_border = "#BBF7D0" if css_eligible else "#FDE68A"
            css_color = "#166534" if css_eligible else "#92400E"

            results_html = f"""
            <div style="text-align:center;margin-bottom:16px;">
                <div style="font-size:14px;color:#6b7280;margin-bottom:4px;">Statut juridique recommandé</div>
                <div style="font-size:32px;font-weight:900;color:#C7372F;">{statut}</div>
                <div style="font-size:13px;color:#6b7280;">{raison}</div>
                <div style="font-size:12px;color:#9ca3af;margin-top:4px;">CA prévu : {ca_prevu}/an</div>
            </div>
            <div style="background:#f9f7f2;border-radius:12px;padding:16px;margin:16px 0;">
                <table style="width:100%;border-collapse:collapse;font-size:14px;">
                    <tr>
                        <th style="text-align:left;padding:8px 0;color:#9ca3af;font-size:12px;"></th>
                        <th style="text-align:center;padding:8px;background:#1A3671;color:white;border-radius:6px 0 0 0;font-size:13px;">{statut}</th>
                        <th style="text-align:center;padding:8px;color:#6b7280;font-size:13px;">{alt}</th>
                    </tr>
                    <tr style="border-bottom:1px solid #e5e7eb;">
                        <td style="padding:8px 0;color:#374151;font-weight:600;">Charges estimées/an</td>
                        <td style="text-align:center;padding:8px;font-weight:700;color:#C7372F;">{fmt(charges)}</td>
                        <td style="text-align:center;padding:8px;color:#6b7280;">{fmt(charges_alt)}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #e5e7eb;">
                        <td style="padding:8px 0;color:#374151;font-weight:600;">Taux charges</td>
                        <td style="text-align:center;padding:8px;font-weight:600;color:#0F1B2D;">{taux}</td>
                        <td style="text-align:center;padding:8px;color:#6b7280;">{taux_alt}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #e5e7eb;">
                        <td style="padding:8px 0;color:#374151;font-weight:600;">Revenu net estimé</td>
                        <td style="text-align:center;padding:8px;font-weight:700;color:#16a34a;">{fmt(net)}</td>
                        <td style="text-align:center;padding:8px;color:#6b7280;">{fmt(net_alt)}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:#374151;font-weight:600;">Régime social</td>
                        <td style="text-align:center;padding:8px;font-size:12px;color:#0F1B2D;">{regime}</td>
                        <td style="text-align:center;padding:8px;font-size:12px;color:#6b7280;">{regime_alt}</td>
                    </tr>
                </table>
            </div>
            <div style="background:{css_bg};border:1px solid {css_border};border-radius:12px;padding:16px;margin:16px 0;">
                <div style="font-size:14px;font-weight:700;color:{css_color};margin-bottom:4px;">Mutuelle Santé : {css_cout}</div>
                <div style="font-size:13px;color:#6b7280;">{css_detail}</div>
                <div style="font-size:11px;color:#9ca3af;margin-top:8px;">Source : ameli.fr — CSS 2025/2026. Plafonds pour 1 personne en métropole.</div>
            </div>
            """

        # Use editable template if available (per-source first, then global fallback)
        source_tpl_key = f"rapport_{body.source.replace('-', '_')}"
        source_tpl = email_templates.get(source_tpl_key, {})
        tpl = source_tpl if source_tpl.get("html") else rapport_tpl

        if tpl.get("html"):
            rapport_html = tpl["html"].replace("{{name}}", full_name).replace("{{company}}", company_name).replace("{{tool}}", body.tool or body.source).replace("{{results_html}}", results_html)
            subject = (tpl.get("subject") or f"Votre Rapport {body.tool} Personnalisé — Zayado").replace("{{tool}}", body.tool or body.source).replace("{{name}}", full_name)
        else:
            subject = f"Votre Rapport {body.tool} Personnalisé — Zayado"
            rapport_html = f"""<div style="font-family:'DM Sans',Arial,sans-serif;max-width:600px;margin:0 auto;background:#ffffff;">
<div style="background:linear-gradient(135deg,#0F1B2D,#1A3671);padding:32px;border-radius:12px 12px 0 0;text-align:center;">
<div style="display:inline-block;background:rgba(201,168,76,0.2);color:#C9A84C;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;margin-bottom:12px;">RAPPORT PERSONNALISÉ</div>
<h1 style="color:white;margin:0;font-size:22px;">{body.tool}</h1>
</div>
<div style="padding:32px;">
<p>Cher <strong>{full_name}</strong>,</p>
<p>Merci pour votre simulation. Voici vos résultats :</p>
{results_html}
<p><a href="https://app.zayado.net/fr/tarif-entreprise-creation-lancement" style="background:#C7372F;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;">Reprendre ma demande</a></p>
<p style="color:#6b7280;">L'équipe Zayado — 01 83 64 39 99</p>
</div>
</div>"""

        send_brevo_email(body.email, full_name, subject, rapport_html)
        # Notification admin
        admin_html = f"""
        <h2>Nouveau lead — {body.source}</h2>
        <p><strong>Outil :</strong> {body.tool}</p>
        <p><strong>Nom :</strong> {body.first_name} {body.last_name}</p>
        <p><strong>Email :</strong> {body.email}</p>
        <p><strong>Téléphone :</strong> {body.phone or 'Non renseigné'}</p>
        <p><strong>Entreprise :</strong> {body.company or 'Non renseigné'}</p>
        <p><strong>Résultats :</strong> {json.dumps(body.results, ensure_ascii=False) if body.results else 'Aucun'}</p>
        """
        send_brevo_email("contact@zayado.net", "Zayado", f"[Lead] {body.tool} — {body.email}", admin_html)
        return {"status": "success", "message": "Rapport envoyé avec succès"}
    except Exception as e:
        logger.error(f"Lead form error: {e}")
        return {"status": "success", "message": "Rapport envoyé avec succès"}



@api_router.get("/join-team")
async def join_team_page(token: str, db: AsyncSession = Depends(get_db)):

    """Vérifier un token d'invitation d'équipe (public)."""
    from sqlalchemy import select
    from models import TeamMember, Team
    result = await db.execute(
        select(TeamMember).where(TeamMember.invite_token == token, TeamMember.status == "pending")
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Invitation invalide ou expirée")
    team_res = await db.execute(select(Team).where(Team.id == member.team_id))
    team = team_res.scalar_one_or_none()
    return {
        "valid": True,
        "email": member.email,
        "team_name": team.name if team else "Équipe Zayado",
        "token": token
    }

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

@api_router.get("/extension/download")
async def download_extension():
    """Télécharger l'extension Chrome Zayado (ZIP)."""
    import zipfile, io
    from fastapi.responses import StreamingResponse
    
    ext_dir = os.path.join(os.path.dirname(__file__), "..", "chrome-extension")
    ext_dir = os.path.normpath(ext_dir)
    
    if not os.path.isdir(ext_dir):
        raise HTTPException(status_code=404, detail="Extension non disponible")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ext_dir):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__']]
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, ext_dir)
                zf.write(file_path, arcname)
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=zayado-extension.zip"}
    )

# ==================== PUBLIC CONFIG ENDPOINT ====================
@api_router.get("/public/config")
async def get_public_admin_config():
    """Public endpoint to get admin config (for landing page YouTube URL, social links, etc.)"""
    config = load_admin_config()
    if config:
        # Only expose safe keys
        safe_keys = ["demo_url", "social_instagram", "social_x", "social_tiktok", "social_linkedin", "social_youtube", "social_facebook", "whatsapp_url", "extension_url", "website_url", "footer_text", "footer_links", "footer_conditions_url", "footer_privacy_url", "footer_doc_url", "footer_copyright", "doc_url", "promo_banner", "logo_url", "extension_logo_url", "logo_white_url", "chat_logo_url"]
        result = {k: config.get(k, "") for k in safe_keys}
        # Add maintenance mode
        result["maintenance_mode"] = config.get("maintenance_mode", False)
        result["maintenance_newsletter"] = config.get("maintenance_newsletter", True)
        # Add sidebar redirects
        result["sidebar_redirects"] = config.get("sidebar_redirects", {})
        # Add mega menu config
        result["mega_menu"] = config.get("mega_menu", {
            "items": [
                {"key": "jeMeLance", "label": "Je me lance", "url": "https://zayado.net/je-me-lance", "enabled": True},
                {"key": "jePilote", "label": "Je pilote", "url": "https://zayado.net/je-pilote", "enabled": True},
                {"key": "jeGrandis", "label": "Je grandis", "url": "https://zayado.net/je-grandis", "enabled": True},
                {"key": "boutique", "label": "Boutique", "url": "https://zayado.net/boutique", "enabled": True},
                {"key": "contact", "label": "Contact", "url": "https://zayado.net/contact", "enabled": True},
            ]
        })
        # Add SEO config
        seo = config.get("seo", {})
        result["logo_url"] = seo.get("logo_url", "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='12' fill='%231E3A8A'/%3E%3Cpath d='M12 14h24l-14 20h14' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E")
        # Expose page-level SEO config for public pages
        page_seo = {}
        for k, v in seo.items():
            if k.startswith("page_seo_") and isinstance(v, dict):
                page_seo[k] = v
        if page_seo:
            result["page_seo"] = page_seo
        # Referral settings from platform_settings
        result["referral_bonus_referrer"] = config.get("referral_bonus_referrer", 50)
        result["referral_bonus_new_user"] = config.get("referral_bonus_new_user", 25)
        # Help videos for info buttons
        result["help_videos"] = config.get("help_videos", {})
        # Creation fees (editable from admin)
        result["creation_fees"] = config.get("creation_fees", {
            "Micro-Entreprise": {"total": 0, "label": "Micro-entreprise : 0€"},
            "SASU": {"total": 306, "label": "SASU : Greffe 35,59€ + Annonce légale à partir de 270€ = ~306€"},
            "EURL": {"total": 306, "label": "EURL : Greffe 35,59€ + Annonce légale à partir de 270€ = ~306€"},
            "SAS": {"total": 306, "label": "SAS : Greffe 35,59€ + Annonce légale à partir de 270€ = ~306€"},
            "SARL": {"total": 306, "label": "SARL : Greffe 35,59€ + Annonce légale à partir de 270€ = ~306€"},
            "SCI": {"total": 334, "label": "SCI : Greffe 63,54€ + Annonce légale à partir de 270€ = ~334€"},
        })
        return result
    return {}

@api_router.get("/public/pricing")
async def get_public_pricing():
    """Public endpoint to get dynamic pricing from admin config."""
    config = load_admin_config()
    if config:
        # Check both nested "pricing" key and root level
        pricing = config.get("pricing", {})
        plans_raw = pricing.get("plans", config.get("plans", []))
        packages_raw = pricing.get("packages", config.get("packages", []))
        # Transform plans for frontend
        plans = []
        features_map = {
            'free': [
                {'text': 'ChatGPT BYOK illimite', 'ok': True},
                {'text': '400 credits offerts', 'ok': True},
                {'text': 'Escalade vers Manus', 'ok': True},
                {'text': 'Sauvegarde cloud', 'ok': False},
                {'text': 'Projets & Timer', 'ok': False},
                {'text': 'Workflows', 'ok': False},
            ],
            'starter': [
                {'text': 'ChatGPT BYOK illimite', 'ok': True},
                {'text': 'Claude Fast illimite', 'ok': True},
                {'text': 'Taches Manus/mois', 'ok': True},
                {'text': 'Sauvegarde cloud', 'ok': True},
                {'text': 'Projets & Timer', 'ok': True},
                {'text': 'Workflows', 'ok': False},
            ],
            'pro': [
                {'text': 'ChatGPT BYOK illimite', 'ok': True},
                {'text': 'Claude Fast + Pro illimite', 'ok': True},
                {'text': 'Taches Manus/mois', 'ok': True},
                {'text': 'Sauvegarde cloud', 'ok': True},
                {'text': 'Projets & Timer', 'ok': True},
                {'text': 'Workflows', 'ok': True},
                {'text': 'Support prioritaire', 'ok': True},
            ],
            'team': [
                {'text': 'Tout du plan Pro', 'ok': True},
                {'text': 'Taches Manus/mois', 'ok': True},
                {'text': "Gestion d'equipe", 'ok': True},
                {'text': 'Support dedie', 'ok': True},
            ],
        }
        for p in plans_raw:
            pid = p.get('id', '')
            plans.append({
                'id': pid,
                'name': p.get('name', pid),
                'price': float(p.get('price', 0)),
                'period': '/mois' if float(p.get('price', 0)) > 0 else '',
                'credits': f"{p.get('credits_per_month', 0)}/mois" if float(p.get('price', 0)) > 0 else '400 (une fois)',
                'manus': f"{p.get('max_manus_tasks', 0)} taches Manus/mois",
                'badge': 'POPULAIRE' if pid == 'pro' else None,
                'features': features_map.get(pid, []),
            })
        packages = []
        for pkg in packages_raw:
            packages.append({
                'id': pkg.get('id', ''),
                'name': pkg.get('name', ''),
                'credits': str(pkg.get('credits', 0)),
                'price': str(pkg.get('price', 0)),
                'unit': f"{(float(pkg.get('price', 1)) / max(int(pkg.get('credits', 1)), 1)):.4f}",
            })
        return {"plans": plans, "packages": packages}
    return {"plans": [], "packages": []}

# ==================== FILE UPLOAD ENDPOINT ====================
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
WORKSPACES_DIR = os.path.join(os.path.dirname(__file__), "workspaces")
os.makedirs(WORKSPACES_DIR, exist_ok=True)

# Upload endpoint removed — the canonical version is in chat_routes.py with chunked validation
# (Fix #3: removed duplicate POST /api/chat/upload)


@api_router.post("/timer/session")
async def save_timer_session(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Save a completed timer session from extension or web."""
    from sqlalchemy import text as sa_text
    duration = data.get("duration_minutes", 0)
    mode = data.get("mode", "focus")
    source = data.get("source", "web")
    try:
        await db.execute(sa_text(
            "INSERT INTO timer_sessions (id, user_id, duration_minutes, mode, source, created_at) "
            "VALUES (:id, :uid, :dur, :mode, :src, NOW()) "
            "ON DUPLICATE KEY UPDATE duration_minutes=:dur"
        ), {"id": str(uuid.uuid4()), "uid": user.id, "dur": duration, "mode": mode, "src": source})
        await db.commit()
    except Exception:
        await db.rollback()
        # Table may not exist yet — create it silently
        try:
            await db.execute(sa_text(
                "CREATE TABLE IF NOT EXISTS timer_sessions ("
                "id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, "
                "duration_minutes INT DEFAULT 0, mode VARCHAR(20) DEFAULT 'focus', "
                "source VARCHAR(20) DEFAULT 'web', created_at DATETIME DEFAULT NOW())"
            ))
            await db.commit()
        except Exception:
            await db.rollback()
    return {"ok": True, "duration_minutes": duration}

@api_router.get("/timer/sessions")
async def get_timer_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get timer sessions for current user."""
    from sqlalchemy import text as sa_text
    try:
        result = await db.execute(sa_text(
            "SELECT id, duration_minutes, mode, source, created_at FROM timer_sessions "
            "WHERE user_id = :uid ORDER BY created_at DESC LIMIT 50"
        ), {"uid": user.id})
        rows = result.fetchall()
        return [{"id": r[0], "duration_minutes": r[1], "mode": r[2], "source": r[3],
                 "task_name": "", "created_at": r[4].isoformat() if r[4] else None} for r in rows]
    except Exception:
        return []

@api_router.get("/uploads/list")
async def list_user_uploads(user: User = Depends(get_current_user)):
    """List all files uploaded by the current user (from uploads directory)."""
    import glob, time
    files = []
    pattern = os.path.join(UPLOADS_DIR, f"{user.id}_*")
    # Also match files without user prefix (older format)
    all_files = sorted(glob.glob(os.path.join(UPLOADS_DIR, "*")), key=os.path.getmtime, reverse=True)
    for fpath in all_files[:50]:
        try:
            fname = os.path.basename(fpath)
            stat = os.stat(fpath)
            import datetime
            created_at = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat()
            ext = os.path.splitext(fname)[1].lower()
            files.append({
                "id": fname.split(".")[0],
                "filename": fname,
                "name": fname,
                "ext": ext,
                "size": stat.st_size,
                "url": f"/api/uploads/{fname}",
                "download_url": f"/api/uploads/download/{fname}",
                "created_at": created_at,
            })
        except Exception:
            pass
    return files

@api_router.get("/uploads/{filename}")
async def serve_upload(filename: str, token: str = "", user: User = Depends(get_current_user)):
    """Serve uploaded files (authenticated) — supports token in query string"""
    # Path traversal protection
    safe_name = os.path.basename(filename)
    if not safe_name or safe_name != filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    filepath = os.path.join(UPLOADS_DIR, safe_name)
    if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOADS_DIR)):
        raise HTTPException(status_code=400, detail="Acces refuse")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    import mimetypes
    mime, _ = mimetypes.guess_type(filepath)
    # Forcer le téléchargement pour ZIP/Word/Excel
    original_name = filename.split("_", 1)[-1] if "_" in filename else filename
    headers = {}
    if mime in ("application/zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        headers["Content-Disposition"] = f'attachment; filename="{original_name}"'
    return FileResponse(filepath, media_type=mime or "application/octet-stream", headers=headers)

@api_router.get("/uploads/download/{filename}")
async def download_upload(filename: str, token: str = None, db: AsyncSession = Depends(get_db)):
    """Téléchargement direct de fichier généré par l'IA.
    Accepte auth via header OU query param ?token= (pour chrome.downloads.download).
    """
    import mimetypes, os as _os, re as _re_dl
    from deps import JWT_SECRET, JWT_ALGORITHM
    from jose import jwt as _jwt, JWTError

    user = None
    # Try query param token
    if token:
        try:
            payload = _jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            uid = payload.get("sub")
            if uid:
                result = await db.execute(select(User).where(User.id == uid))
                user = result.scalar_one_or_none()
        except (JWTError, Exception):
            pass

    # Try Authorization header
    if user is None:
        from starlette.requests import Request
        # Will be injected by FastAPI
        pass

    # Allow: authenticated user OR generated file pattern
    is_generated = bool(_re_dl.match(r'^projet_corrige_[a-f0-9]+\.zip$', filename) or _re_dl.match(r'^[a-f0-9]+_', filename))
    if user is None and not is_generated:
        raise HTTPException(status_code=403, detail="Authentification requise")

    safe_name = _os.path.basename(filename)
    if not safe_name or safe_name != filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")

    filepath = _os.path.join(UPLOADS_DIR, safe_name)
    if not _os.path.abspath(filepath).startswith(_os.path.abspath(UPLOADS_DIR)):
        raise HTTPException(status_code=400, detail="Accès refusé")
    if not _os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    mime, _ = mimetypes.guess_type(filepath)
    display_name = safe_name.split("_", 1)[-1] if "_" in safe_name else safe_name
    return FileResponse(
        filepath,
        media_type=mime or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{display_name}"'}
    )



@api_router.post("/chat/generate-file")
async def generate_file_for_download(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Génère un fichier (Word/TXT) depuis du contenu texte et retourne un lien download"""
    body = await request.json()
    file_content = body.get("content", "")
    filename = body.get("filename", "document")
    file_format = body.get("format", "txt")  # txt, docx

    if not file_content:
        raise HTTPException(400, "Contenu requis")

    file_id = str(uuid.uuid4())[:8]
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    if file_format == "docx":
        try:
            import docx as _docx
            doc = _docx.Document()
            # Titre
            doc.add_heading(filename, 0)
            # Contenu ligne par ligne
            for line in file_content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("# "):
                    doc.add_heading(line[2:], level=1)
                elif line.startswith("## "):
                    doc.add_heading(line[3:], level=2)
                elif line.startswith("### "):
                    doc.add_heading(line[4:], level=3)
                elif line.startswith("- ") or line.startswith("* "):
                    doc.add_paragraph(line[2:], style="List Bullet")
                else:
                    doc.add_paragraph(line)
            out_filename = f"{file_id}_{filename}.docx"
            out_path = os.path.join(UPLOADS_DIR, out_filename)
            doc.save(out_path)
            return {
                "url": f"/api/uploads/{out_filename}",
                "download_url": f"/api/uploads/download/{out_filename}",
                "filename": f"{filename}.docx",
                "format": "docx"
            }
        except ImportError:
            file_format = "txt"  # fallback

    # TXT fallback
    out_filename = f"{file_id}_{filename}.txt"
    out_path = os.path.join(UPLOADS_DIR, out_filename)
    with open(out_path, "w", encoding="utf-8") as fw:
        fw.write(file_content)
    return {
        "url": f"/api/uploads/{out_filename}",
        "download_url": f"/api/uploads/download/{out_filename}",
        "filename": f"{filename}.txt",
        "format": "txt"
    }


# ==================== EXPORT DOCX / PPTX ====================
@api_router.get("/chat/conversations/{conv_id}/export/docx")
async def export_conversation_docx(conv_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Export conversation as Word document.
    Fix #169 — ImportError géré proprement.
    Fix #87  — messages limités à 500 pour éviter un export de plusieurs Go.
    """
    from fastapi.responses import StreamingResponse
    import io, re as _re
    try:
        import docx as _docx
    except ImportError:
        raise HTTPException(status_code=500, detail="La génération Word n'est pas disponible sur ce serveur (python-docx manquant).")

    result = await db.execute(select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")

    doc = _docx.Document()
    doc.add_heading(conv.title or "Conversation", 0)
    # fix #87 — limit to 200 messages max for export to avoid huge responses
    messages_export = (conv.messages or [])[:200]
    for msg in messages_export:
        role = "Vous" if msg.get("role") == "user" else "Assistant IA"
        p = doc.add_paragraph()
        p.add_run(f"{role} : ").bold = True
        content_text = msg.get("content", "")
        clean = _re.sub(r'<[^>]+>', '', content_text)
        p.add_run(clean[:5000])
        doc.add_paragraph()
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    safe_title = _re.sub(r'[^\w\-]', '_', (conv.title or "conversation"))[:40]
    filename = f"{safe_title}-{conv_id[:8]}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@api_router.get("/chat/conversations/{conv_id}/export/pptx")
async def export_conversation_pptx(conv_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Export conversation as PowerPoint.
    Fix #169 — ImportError géré proprement.
    Fix #87  — messages limités à 20 slides.
    """
    from fastapi.responses import StreamingResponse
    import io, re as _re
    try:
        from pptx import Presentation
        from pptx.util import Pt
    except ImportError:
        raise HTTPException(status_code=500, detail="La génération PowerPoint n'est pas disponible sur ce serveur (python-pptx manquant).")

    result = await db.execute(select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = conv.title or "Conversation IA"
    slide.placeholders[1].text = f"Exporté le {__import__('datetime').datetime.now().strftime('%d/%m/%Y')}"
    # fix #87 — limit to 20 slides
    for msg in (conv.messages or [])[:20]:
        sl = prs.slides.add_slide(prs.slide_layouts[1])
        sl.shapes.title.text = "Vous" if msg.get("role") == "user" else "Assistant IA"
        clean = _re.sub(r'<[^>]+>', '', msg.get("content", ""))
        sl.placeholders[1].text = clean[:500]
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    safe_title = _re.sub(r'[^\w\-]', '_', (conv.title or "conversation"))[:40]
    filename = f"{safe_title}-{conv_id[:8]}.pptx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# ==================== PROMO & ANNULATION ====================
@api_router.post("/auth/apply-promo")
async def apply_promo_code(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Appliquer un code promo (rétention anti-churn)"""
    body = await request.json()
    code = body.get("code", "").strip().upper()
    VALID_PROMOS = {
        "RESTE30": {"discount_percent": 30, "months": 3, "description": "-30% pendant 3 mois"},
    }
    promo = VALID_PROMOS.get(code)
    if not promo:
        raise HTTPException(status_code=400, detail="Code promo invalide")
    try:
        await db.execute(update(User).where(User.id == user.id).values(
            discount_percent=promo["discount_percent"],
            discount_expires_at=datetime.now(timezone.utc) + timedelta(days=30 * promo["months"])
        ))
        await db.commit()
        logger.info(f"Promo {code} appliqué pour {user.email}")
        return {"success": True, "message": f"Code {code} appliqué : {promo['description']}", "discount": promo}
    except Exception:
        return {"success": True, "message": f"Code {code} enregistré", "discount": promo}

@api_router.post("/auth/cancel-subscription")
async def cancel_subscription(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Annuler l'abonnement (passe en free à la fin de la période)"""
    body = await request.json()
    reason = body.get("reason", "")
    feedback = body.get("feedback", "")
    try:
        # Annulation souple : log + email, sans nécessiter les colonnes DB
        try:
            await db.execute(update(User).where(User.id == user.id).values(
                cancel_at_period_end=True,
                cancellation_reason=reason[:500] if reason else None
            ))
            await db.commit()
        except Exception:
            await db.rollback()  # Colonnes potentiellement absentes — continuer quand même
        logger.info(f"Annulation abonnement {user.email} - raison: {reason}")
        if os.environ.get('BREVO_API_KEY') and user.email:
            # Fix #24 — use run_in_executor for sync send_brevo_email (non-blocking)
            _email = user.email
            _name = user.name or "Utilisateur"
            _reason = reason
            asyncio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(
                to_email=_email, to_name=_name,
                subject="Votre abonnement ZAYADO a été annulé",
                html_content=f"<p>Votre abonnement sera annulé à la fin de la période en cours. Merci d'avoir utilisé ZAYADO.</p><p>Raison : {_reason}</p>"
            ))
        return {"success": True, "message": "Annulation enregistrée. Votre abonnement restera actif jusqu'à la fin de la période."}
    except Exception as e:
        logger.error(f"Cancel subscription error: {e}")
        return {"success": True, "message": "Annulation enregistrée."}



# ==================== API SEO / RÉFÉRENCEMENT ====================

@api_router.post("/seo/analyze")
async def seo_analyze(request: Request, user: User = Depends(get_current_user)):
    """Analyse SEO complète d'une URL via l'Agent IA"""
    body = await request.json()
    url    = body.get("url", "").strip()
    focus  = body.get("focus_keyword", "").strip()
    if not url:
        raise HTTPException(400, detail="URL requise")

    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(500, detail="Clé API Agent non configurée")

    # Prompt d'audit SEO professionnel
    seo_system = """Tu es un expert SEO professionnel. Analyse le contenu d'une page web et fournis un audit SEO complet au format JSON.
Réponds UNIQUEMENT avec un objet JSON valide, sans backticks ni texte autour."""

    user_msg = f"""Analyse SEO de : {url}
Mot-clé cible : {focus if focus else "Non spécifié"}

Fournis un audit JSON avec exactement cette structure :
{{
  "url": "{url}",
  "focus_keyword": "{focus}",
  "score_global": 75,
  "scores": {{
    "technique": 80,
    "contenu": 70,
    "mots_cles": 65,
    "structure": 85,
    "performance": 70
  }},
  "titre": {{
    "valeur": "Titre de la page (à extraire)",
    "longueur": 55,
    "optimise": true,
    "recommandation": "..."
  }},
  "meta_description": {{
    "valeur": "Meta description",
    "longueur": 150,
    "optimise": false,
    "recommandation": "..."
  }},
  "mots_cles": {{
    "principal": "{focus}",
    "densite": 2.3,
    "position_titre": true,
    "position_h1": true,
    "variations_suggérees": ["variation1", "variation2"]
  }},
  "structure": {{
    "h1_count": 1,
    "h2_count": 4,
    "h3_count": 6,
    "images_sans_alt": 2,
    "liens_internes": 8,
    "liens_externes": 3
  }},
  "problemes_critiques": [
    "Problème critique 1",
    "Problème critique 2"
  ],
  "recommandations": [
    {{"priorite": "haute", "action": "Action 1", "impact": "Impact attendu"}},
    {{"priorite": "moyenne", "action": "Action 2", "impact": "Impact attendu"}},
    {{"priorite": "basse", "action": "Action 3", "impact": "Impact attendu"}}
  ],
  "concurrents_suggeres": ["concurrent1.com", "concurrent2.fr"],
  "backlinks_strategie": "Stratégie de liens recommandée en 2-3 phrases."
}}"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{MAMMOTH_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={
                    "model": AGENT_COMPLEX_MODEL,
                    "messages": [
                        {"role": "system", "content": seo_system},
                        {"role": "user", "content": user_msg}
                    ],
                    "max_tokens": 2048,
                    "temperature": 0.2
                }
            )
        if resp.status_code != 200:
            raise HTTPException(502, detail=f"Erreur API: {resp.status_code}")

        raw = resp.json()["choices"][0]["message"]["content"]
        # Nettoyer les backticks eventuels
        import re as _re2
        raw = _re2.sub(r"^```(?:json)?\n?", "", raw.strip())
        raw = _re2.sub(r"```$", "", raw.strip())
        result = json.loads(raw)
        return {"success": True, "analysis": result}
    except json.JSONDecodeError:
        return {"success": False, "raw": raw, "error": "Réponse non parseable"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@api_router.post("/seo/keywords")
async def seo_keywords(request: Request, user: User = Depends(get_current_user)):
    """Génère des suggestions de mots-clés pour une thématique"""
    body = await request.json()
    topic   = body.get("topic", "").strip()
    country = body.get("country", "FR")
    lang    = body.get("lang", "fr")
    if not topic:
        raise HTTPException(400, detail="Thématique requise")

    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(500, detail="Clé API non configurée")

    prompt = f"""Génère 20 mots-clés SEO pour la thématique "{topic}" (pays: {country}, langue: {lang}).
Réponds UNIQUEMENT avec un JSON:
{{
  "keywords": [
    {{"mot_cle": "...", "volume_estimé": "élevé/moyen/faible", "difficulte": "élevé/moyen/faible", "intention": "informationnelle/transactionnelle/navigationnelle", "type": "principal/longue-traine"}},
    ...
  ],
  "clusters": [
    {{"theme": "Cluster 1", "mots_cles": ["kw1", "kw2", "kw3"]}},
    ...
  ]
}}"""

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{MAMMOTH_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={"model": AGENT_DEFAULT_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500, "temperature": 0.3}
            )
        raw = resp.json()["choices"][0]["message"]["content"]
        import re as _re3
        raw = _re3.sub(r"^```(?:json)?\n?", "", raw.strip()); raw = _re3.sub(r"```$", "", raw.strip())
        return {"success": True, "data": json.loads(raw)}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@api_router.get("/seo/settings")
async def get_seo_settings(user: User = Depends(get_current_user)):
    """Récupère les paramètres SEO de l'utilisateur"""
    try:
        raw_settings = getattr(user, 'settings', None)
        if isinstance(raw_settings, dict):
            seo_cfg = raw_settings.get("seo_config", {})
        elif isinstance(raw_settings, str):
            import json as _j
            seo_cfg = _j.loads(raw_settings).get("seo_config", {})
        else:
            seo_cfg = {}
        return {
            "enabled": seo_cfg.get("enabled", True),
            "auto_analyze": seo_cfg.get("auto_analyze", False),
            "default_country": seo_cfg.get("default_country", "FR"),
            "default_lang": seo_cfg.get("default_lang", "fr"),
            "tracked_urls": seo_cfg.get("tracked_urls", []),
            "notifications_enabled": seo_cfg.get("notifications_enabled", True)
        }
    except Exception:
        return {"enabled": True, "auto_analyze": False, "default_country": "FR", "default_lang": "fr", "tracked_urls": [], "notifications_enabled": True}


@api_router.post("/seo/settings")
async def save_seo_settings(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Sauvegarde les paramètres SEO"""
    body = await request.json()
    try:
        current_settings = user.settings or {} if hasattr(user, 'settings') and isinstance(user.settings, dict) else {}
        current_settings["seo_config"] = {
            "enabled":                body.get("enabled", True),
            "auto_analyze":           body.get("auto_analyze", False),
            "default_country":        body.get("default_country", "FR"),
            "default_lang":           body.get("default_lang", "fr"),
            "tracked_urls":           body.get("tracked_urls", []),
            "notifications_enabled":  body.get("notifications_enabled", True)
        }
        await db.execute(update(User).where(User.id == user.id).values(settings=current_settings))
        await db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@api_router.post("/seo/content-optimize")
async def seo_content_optimize(request: Request, user: User = Depends(get_current_user)):
    """Optimise un contenu pour le SEO selon un mot-clé cible"""
    body = await request.json()
    content = body.get("content", "").strip()
    keyword = body.get("keyword", "").strip()
    page_type = body.get("page_type", "article")
    if not content or not keyword:
        raise HTTPException(400, detail="Contenu et mot-clé requis")

    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(500, detail="Clé API non configurée")

    prompt = f"""Tu es expert SEO. Optimise ce contenu pour le mot-clé "{keyword}" (type: {page_type}).
Réponds en JSON:
{{
  "titre_optimise": "...",
  "meta_description": "...(155 caractères max)",
  "contenu_optimise": "...(version améliorée)",
  "changements": ["Changement 1", "Changement 2"],
  "score_avant": 45,
  "score_apres": 78
}}

Contenu original:
{content[:3000]}"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{MAMMOTH_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={"model": AGENT_COMPLEX_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.3}
            )
        raw = resp.json()["choices"][0]["message"]["content"]
        import re as _re4
        raw = _re4.sub(r"^```(?:json)?\n?", "", raw.strip()); raw = _re4.sub(r"```$", "", raw.strip())
        return {"success": True, "data": json.loads(raw)}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==================== VOICE TRANSCRIPTION ENDPOINT ====================
@api_router.post("/chat/transcribe")
async def transcribe_audio(audio: UploadFile = File(...), user: User = Depends(get_current_user)):
    """Transcribe audio to text using OpenAI Whisper or browser fallback"""
    content = await audio.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fichier audio trop volumineux (max 25MB)")

    # Try OpenAI Whisper if key available
    openai_key = os.environ.get("OPENAI_API_KEY") or user.openai_key
    if openai_key:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            async with httpx.AsyncClient(timeout=60) as client:
                with open(tmp_path, "rb") as f:
                    resp = await client.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {openai_key}"},
                        files={"file": ("voice.webm", f, "audio/webm")},
                        data={"model": "whisper-1", "language": "fr"}
                    )
                os.unlink(tmp_path)
                if resp.status_code == 200:
                    return {"text": resp.json().get("text", "")}
                else:
                    logger.warning(f"Whisper API error: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")

    # Fallback: essayer Mammoth IA Whisper
    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if mammoth_key:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            async with httpx.AsyncClient(timeout=60) as client:
                with open(tmp_path, "rb") as f:
                    resp = await client.post(
                        "https://api.mammouth.ai/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {mammoth_key}"},
                        files={"file": ("voice.webm", f, "audio/webm")},
                        data={"model": "whisper-1", "language": "fr"}
                    )
                os.unlink(tmp_path)
                if resp.status_code == 200:
                    return {"text": resp.json().get("text", "")}
        except Exception as me:
            logger.warning(f"Mammoth transcription error: {me}")
    # Dernier fallback: browser SpeechRecognition
    return {"text": "", "fallback": True, "message": "Utilisation de la reconnaissance vocale du navigateur."}



# ==================== KYB — VÉRIFICATION ORGANISATION ====================
# Requis pour plans Business, Team, et certaines promos

@api_router.post("/kyb/submit")
async def kyb_submit(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Soumettre une demande de vérification KYB (Know Your Business)."""
    body = await request.json()
    org_name = body.get("org_name", "").strip()
    org_type = body.get("org_type", "").strip()  # entreprise | association | eglise | autre
    doc_type = body.get("doc_type", "").strip()  # siret | kbis | rna | statuts | autre
    doc_description = body.get("doc_description", "").strip()

    allowed_types = ["entreprise", "association", "eglise", "ong", "autre"]
    allowed_docs = ["siret", "kbis", "rna", "statuts", "justificatif_etudiant", "carte_pro", "autre"]

    if not org_name:
        raise HTTPException(400, "Nom de l'organisation requis")
    if org_type not in allowed_types:
        raise HTTPException(400, f"Type d'organisation invalide. Valeurs acceptees: {', '.join(allowed_types)}")
    if doc_type not in allowed_docs:
        raise HTTPException(400, f"Type de document invalide. Valeurs acceptees: {', '.join(allowed_docs)}")

    # Stocker la demande dans les settings user
    kyb_data = {
        "status": "pending",
        "org_name": org_name,
        "org_type": org_type,
        "doc_type": doc_type,
        "doc_description": doc_description[:500],
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

    # Mettre à jour les settings utilisateur
    current_settings = {}
    if hasattr(user, 'settings') and user.settings:
        try:
            current_settings = dict(user.settings) if isinstance(user.settings, dict) else json.loads(user.settings)
        except Exception:
            pass
    current_settings["kyb"] = kyb_data

    await db.execute(
        update(User).where(User.id == user.id).values(settings=current_settings)
    )
    await db.commit()

    logger.info(f"KYB submitted by {user.email}: {org_type} - {doc_type}")
    return {"status": "pending", "message": "Demande enregistree. Verification sous 24-48h ouvrées."}

@api_router.get("/kyb/status")
async def kyb_status(user: User = Depends(get_current_user)):
    """Retourne le statut KYB de l'utilisateur."""
    settings = {}
    if hasattr(user, 'settings') and user.settings:
        try:
            settings = dict(user.settings) if isinstance(user.settings, dict) else json.loads(user.settings)
        except Exception:
            pass
    kyb = settings.get("kyb", {})
    return {
        "status": kyb.get("status", "not_submitted"),
        "org_name": kyb.get("org_name", ""),
        "org_type": kyb.get("org_type", ""),
        "submitted_at": kyb.get("submitted_at"),
        "required_for": ["business", "team"]
    }

@api_router.put("/admin/kyb/{user_id}/validate")
async def admin_kyb_validate(user_id: str, data: Dict[str, Any], admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Admin: valider ou rejeter un KYB."""
    status = data.get("status", "")  # approved | rejected
    if status not in ("approved", "rejected"):
        raise HTTPException(400, "Status doit etre 'approved' ou 'rejected'")
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "Utilisateur non trouve")
    settings = {}
    if target.settings:
        try:
            settings = dict(target.settings) if isinstance(target.settings, dict) else json.loads(target.settings)
        except Exception:
            pass
    if "kyb" in settings:
        settings["kyb"]["status"] = status
        settings["kyb"]["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        settings["kyb"]["reviewed_by"] = admin.email
    await db.execute(update(User).where(User.id == user_id).values(settings=settings))
    await db.commit()
    return {"status": status, "user": target.email}

# ==================== CREDIT SHARING ====================
@api_router.post("/credits/share")
async def share_credits(data: Dict[str, Any], user: User = Depends(get_current_user)):
    """Share bonus/purchased credits with another user by email. Business/Equipe only."""
    allowed_plans = ["business", "team", "admin", "super_admin"]
    if user.plan not in allowed_plans and user.role not in ("admin", "super_admin"):
        raise HTTPException(403, "Le partage de credits est disponible pour les plans Business et Equipe")
    target_email = data.get("recipient_email", data.get("email", data.get("target_email", ""))).strip()
    amount = int(data.get("amount", 0))

    if amount <= 0:
        raise HTTPException(400, "Le montant doit etre positif")
    if amount > 500:
        raise HTTPException(400, "Maximum 500 credits par partage")

    # Only bonus and purchased credits can be shared (not plan credits)
    shareable = (user.bonus_credits or 0) + (user.purchased_credits or 0)
    if amount > shareable:
        raise HTTPException(400, f"Credits partageables insuffisants ({shareable} disponibles)")

    async with async_session_factory() as db:
        # Find target user
        if target_email:
            result = await db.execute(select(User).where(User.email == target_email))
        else:
            raise HTTPException(400, "Email du destinataire requis")

        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(404, "Utilisateur destinataire introuvable")
        if target.id == user.id:
            raise HTTPException(400, "Vous ne pouvez pas partager avec vous-meme")

        # Deduct from sender (bonus first, then purchased)
        remaining = amount
        bonus_deduct = min(remaining, user.bonus_credits or 0)
        remaining -= bonus_deduct
        purchased_deduct = min(remaining, user.purchased_credits or 0)

        await db.execute(
            update(User).where(User.id == user.id).values(
                bonus_credits=User.bonus_credits - bonus_deduct,
                purchased_credits=User.purchased_credits - purchased_deduct
            )
        )
        # Add to target bonus credits
        await db.execute(
            update(User).where(User.id == target.id).values(
                bonus_credits=User.bonus_credits + amount
            )
        )
        await db.commit()

        # Send Brevo emails to both users
        brevo_key = os.environ.get("BREVO_API_KEY", "")
        if brevo_key:
            try:
                for email, subject, body in [
                    (user.email, "Credits partages avec succes",
                     f"Vous avez partage {amount} credits avec {target.email}. Votre solde bonus: {(user.bonus_credits or 0) - bonus_deduct} credits."),
                    (target.email, "Vous avez recu des credits !",
                     f"{user.name} vous a partage {amount} credits bonus. Profitez-en !"),
                ]:
                    async with httpx.AsyncClient() as client:
                        await client.post("https://api.brevo.com/v3/smtp/email", headers={
                            "api-key": brevo_key, "Content-Type": "application/json"
                        }, json={
                            "sender": {"email": "noreply@zayado.net", "name": "Extension IA by Zayado"},
                            "to": [{"email": email}],
                            "subject": subject,
                            "htmlContent": f"<p>{body}</p>"
                        })
            except Exception as e:
                logger.error(f"Brevo email error on credit share: {e}")

        # In-app notifications logged (no MongoDB in this app)
        try:
            logger.info(f"Credit share notification: {user.email} -> {target.email}: {amount} credits")
        except Exception as e:
            logger.error(f"Notification creation error: {e}")

        return {"message": f"{amount} credits partages avec {target.email}", "new_bonus": (user.bonus_credits or 0) - bonus_deduct, "new_purchased": (user.purchased_credits or 0) - purchased_deduct}

# ==================== PARTNER & DISCOUNT SYSTEM ====================
PARTNER_DISCOUNTS = {
    "thesustain": {
        "name": "TheSustain",
        "code": "SUSTAIN2026",
        "discount_percent": 30,
        "domains": ["thesustain.com", "thesustain.fr"],
        "logo": "https://thesustain.net/logo.png",
        "url": "https://thesustain.net",
        "active": True
    }
}

@api_router.post("/discounts/verify-code")
async def verify_discount_code(data: dict, db: AsyncSession = Depends(get_db)):
    """Verify a partner/promo discount code"""
    code = (data.get("code") or "").upper()
    for pid, partner in PARTNER_DISCOUNTS.items():
        if partner["code"] == code and partner["active"]:
            return {"valid": True, "partner": pid, "name": partner["name"], "discount": partner["discount_percent"], "url": partner.get("url")}
    return {"valid": False}

@api_router.post("/discounts/request")
async def request_discount(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request a preferential discount (supports FormData with file upload or JSON)"""
    content_type = request.headers.get("content-type", "")
    
    if "multipart/form-data" in content_type:
        form = await request.form()
        dtype = form.get("type")
        partner_code = form.get("partner_code")
        doc_file = form.get("document")
        doc_url = None
        if doc_file and hasattr(doc_file, 'read'):
            ext = os.path.splitext(doc_file.filename)[1].lower() if doc_file.filename else ".pdf"
            filename = f"discount_{user.id}_{uuid.uuid4().hex[:8]}{ext}"
            filepath = os.path.join(UPLOADS_DIR, filename)
            content = await doc_file.read()
            with open(filepath, "wb") as f:
                f.write(content)
            doc_url = f"/api/uploads/{filename}"
    else:
        data = await request.json()
        dtype = data.get("type")
        partner_code = data.get("partner_code")
        doc_url = data.get("document_url")

    if dtype == "partner" and partner_code:
        code = partner_code.upper()
        for pid, partner in PARTNER_DISCOUNTS.items():
            if partner["code"] == code and partner["active"]:
                await db.execute(update(User).where(User.id == user.id).values(
                    discount_type=f"partner_{pid}",
                    discount_percent=partner["discount_percent"],
                    discount_verified=True,
                    partner_code=code
                ))
                await db.commit()
                return {"success": True, "discount": partner["discount_percent"], "partner": partner["name"]}
        raise HTTPException(400, "Code partenaire invalide")

    if dtype == "student":
        if not doc_url:
            raise HTTPException(400, "Pièce requise : carte étudiant en cours de validité (PDF, JPG ou PNG uniquement)")
        # Vérifier le format du fichier
        ext_ok = any(doc_url.lower().endswith(e) for e in [".pdf", ".jpg", ".jpeg", ".png"])
        if not ext_ok:
            raise HTTPException(400, "Format invalide. Seuls PDF, JPG et PNG sont acceptés pour la carte étudiant")
        # Bloquer si déjà vérifié
        if user.discount_type == "student" and user.discount_verified:
            raise HTTPException(400, "Vous bénéficiez déjà d'une réduction étudiant vérifiée")
        await db.execute(update(User).where(User.id == user.id).values(
            discount_type="student", discount_percent=20,
            discount_verified=False, discount_doc_url=doc_url
        ))
        await db.commit()
        logger.info(f"Discount student request: {user.email} - {doc_url}")
        return {"success": True, "message": "Demande soumise. Notre équipe vérifie votre carte étudiant sous 24-48h ouvrées."}

    if dtype == "association":
        if not doc_url:
            raise HTTPException(400, "Pièce requise : RNA, statuts ou attestation préfectorale (PDF, JPG ou PNG uniquement)")
        ext_ok = any(doc_url.lower().endswith(e) for e in [".pdf", ".jpg", ".jpeg", ".png"])
        if not ext_ok:
            raise HTTPException(400, "Format invalide. Seuls PDF, JPG et PNG sont acceptés pour le justificatif association")
        if user.discount_type == "association" and user.discount_verified:
            raise HTTPException(400, "Vous bénéficiez déjà d'une réduction association vérifiée")
        await db.execute(update(User).where(User.id == user.id).values(
            discount_type="association", discount_percent=30,
            discount_verified=False, discount_doc_url=doc_url
        ))
        await db.commit()
        logger.info(f"Discount association request: {user.email} - {doc_url}")
        return {"success": True, "message": "Demande soumise. Notre équipe vérifie votre justificatif (RNA/statuts) sous 24-48h ouvrées."}

    raise HTTPException(400, "Type de reduction invalide")

@api_router.post("/admin/discounts/{user_id}/approve")
async def approve_discount(user_id: str, admin: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if admin.role not in ("admin", "super_admin"):
        raise HTTPException(403)
    await db.execute(update(User).where(User.id == user_id).values(discount_verified=True))
    await db.commit()
    return {"success": True}

@api_router.post("/admin/discounts/{user_id}/reject")
async def reject_discount(user_id: str, admin: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if admin.role not in ("admin", "super_admin"):
        raise HTTPException(403)
    await db.execute(update(User).where(User.id == user_id).values(
        discount_type=None, discount_percent=0, discount_verified=False, discount_doc_url=None
    ))
    await db.commit()
    return {"success": True}

@api_router.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket):
    """
    Agent IA interactif — boucle Action-Résultat.
    
    Le serveur peut envoyer :
    - {type:"step", message:"..."} → info progression
    - {type:"action", action:"navigate", url:"..."} → naviguer
    - {type:"action", action:"fill", selector:"...", value:"..."} → remplir input
    - {type:"action", action:"click", selector:"...", text:"..."} → cliquer
    - {type:"action", action:"extract"} → lire la page
    - {type:"chunk", content:"..."} → streaming réponse
    - {type:"result", content:"..."} → réponse finale
    - {type:"error", message:"..."} → erreur
    
    L'extension renvoie :
    - {type:"action_result", success:bool, content:"...", ...}
    - {type:"ping"} → heartbeat ignoré
    """
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        task              = data.get("task", "")
        token             = data.get("token", "")
        conversation_id   = data.get("conversation_id")
        extracted_content = data.get("extracted_content", "")
        navigated_url     = data.get("navigated_url", "")
        _ping = data.get("type") == "ping"

        if _ping:
            return

        if not task or not token:
            await websocket.send_json({"type": "error", "message": "Tache et token requis"})
            return

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
        except JWTError:
            await websocket.send_json({"type": "error", "message": "Token invalide"})
            return

        async with async_session_factory() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                await websocket.send_json({"type": "error", "message": "Utilisateur introuvable"})
                return

            total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
            credits_needed = 50
            if total_credits < credits_needed:
                await websocket.send_json({"type": "error",
                    "message": f"Crédits insuffisants — {total_credits} disponibles, {credits_needed} requis."})
                return

            mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
            if not mammoth_key:
                await websocket.send_json({"type": "error", "message": "Clé API agent non configurée"})
                return

            # ── Helper step ──────────────────────────────────────────
            async def step(msg: str, action_type: str = "step"):
                await websocket.send_json({"type": "step", "action": action_type, "message": msg})

            # ── Envoyer action à l'extension et attendre résultat ────
            async def send_action_and_wait(action_data: dict, timeout: float = 20.0) -> dict:
                """Envoie une action à l'extension Chrome et attend le résultat."""
                await websocket.send_json({"type": "action", **action_data})
                try:
                    # Attendre la réponse de l'extension
                    deadline = asyncio.get_running_loop().time() + timeout
                    while True:
                        remaining = deadline - asyncio.get_running_loop().time()
                        if remaining <= 0:
                            return {"success": False, "error": "Timeout"}
                        try:
                            raw = await asyncio.wait_for(websocket.receive_json(), timeout=remaining)
                            if raw.get("type") == "action_result":
                                return raw
                            elif raw.get("type") == "ping":
                                continue  # ignorer heartbeat
                            elif raw.get("type") == "error":
                                return {"success": False, "error": raw.get("message", "")}
                        except asyncio.TimeoutError:
                            return {"success": False, "error": "Timeout"}
                except Exception as e:
                    return {"success": False, "error": str(e)[:100]}

            # ── Outils web httpx (sans extension) ────────────────────
            async def real_web_fetch(url: str) -> str:
                try:
                    if not url.startswith("http"):
                        url = "https://" + url

                    # ── GitHub : API officielle ──────────────────────
                    import re as _rgh
                    gh_match = _rgh.match(
                        r"https?://github\.com/([^/]+)/([^/]+)(?:/(?:tree|blob)/([^/]+)/?(.*))?"
                        , url
                    )
                    if gh_match:
                        owner  = gh_match.group(1)
                        repo   = gh_match.group(2).rstrip(".git")
                        branch = gh_match.group(3) or "main"
                        path   = (gh_match.group(4) or "").strip("/")
                        api_base   = "https://api.github.com/repos/" + owner + "/" + repo
                        gh_headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "ZayadoAgent/1.0"}
                        async with httpx.AsyncClient(timeout=15.0) as gh:
                            if path:
                                r2 = await gh.get(api_base + "/contents/" + path + "?ref=" + branch, headers=gh_headers)
                                if r2.status_code == 200:
                                    data2 = r2.json()
                                    if isinstance(data2, list):
                                        items = ["- " + item["name"] + " (" + item["type"] + ")" for item in data2]
                                        return "[GitHub: " + owner + "/" + repo + "/" + path + "]\n" + "\n".join(items)
                                    elif isinstance(data2, dict) and data2.get("encoding") == "base64":
                                        import base64 as _b64
                                        raw = _b64.b64decode(data2["content"]).decode("utf-8", errors="replace")
                                        return "[GitHub: " + owner + "/" + repo + "/" + path + "]\n```\n" + raw[:8000] + "\n```"
                            else:
                                r2 = await gh.get(api_base, headers=gh_headers)
                                r3 = await gh.get(api_base + "/contents?ref=" + branch, headers=gh_headers)
                                info  = r2.json() if r2.status_code == 200 else {}
                                files = r3.json() if r3.status_code == 200 else []
                                desc  = str(info.get("description", ""))
                                items = ["- " + item["name"] + " (" + item["type"] + ")" for item in (files if isinstance(files, list) else [])]
                                return "[GitHub: " + owner + "/" + repo + "]\nDescription: " + desc + "\n\nFichiers:\n" + "\n".join(items)
                        return "Erreur accès GitHub " + owner + "/" + repo

                    # ── Page web normale ────────────────────────────
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,*/*",
                        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                    }
                    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                        r = await client.get(url, headers=headers)
                    if r.status_code != 200:
                        return f"Erreur HTTP {r.status_code}"
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(r.text, "lxml")
                    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                        tag.decompose()
                    title = soup.title.string if soup.title else ""
                    text  = soup.get_text(separator="\n", strip=True)
                    import re as _re2
                    text = _re2.sub(r"\n{3,}", "\n\n", text)
                    return f"[{title}]\n{text[:8000]}"
                except Exception as e:
                    return f"Erreur lecture: {str(e)[:100]}"

            async def real_web_search(query: str) -> str:
                try:
                    import urllib.parse
                    enc = urllib.parse.quote(query)
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "text/html"}
                    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                        r = await client.get(f"https://html.duckduckgo.com/html/?q={enc}", headers=headers)
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(r.text, "html.parser")
                    results = []
                    for res in soup.select(".result")[:6]:
                        t = res.select_one(".result__title")
                        s = res.select_one(".result__snippet")
                        u = res.select_one(".result__url")
                        if t:
                            results.append(
                                "**" + t.get_text(strip=True) + "**\n" +
                                (u.get_text(strip=True) if u else "") + "\n" +
                                (s.get_text(strip=True) if s else "")
                            )
                    return "\n\n".join(results) if results else "Aucun résultat"
                except Exception as e:
                    return f"Erreur recherche: {str(e)[:100]}"

            # ── Détecter l'intention et l'URL ─────────────────────────
            import re as _re_a, urllib.parse as _urlparse

            target_url = None
            search_query = None

            url_m = _re_a.search(r"https?://[^\s]+", task)
            if url_m:
                target_url = url_m.group(0).rstrip(".,;)")

            KNOWN = {
                "github": "https://github.com", "github.com": "https://github.com",
                "google": "https://www.google.fr", "youtube": "https://youtube.com",
                "linkedin": "https://linkedin.com", "twitter": "https://x.com",
                "x.com": "https://x.com", "wikipedia": "https://fr.wikipedia.org",
                "amazon": "https://www.amazon.fr", "leboncoin": "https://www.leboncoin.fr",
                "notion": "https://notion.so", "figma": "https://figma.com",
                "gmail": "https://mail.google.com",
            }
            tl = task.lower()
            if not target_url:
                for key, url in KNOWN.items():
                    if key in tl:
                        target_url = url
                        break

            if not target_url:
                dom = _re_a.search(
                    r"(?:www\.)?([a-zA-Z0-9-]+\.(?:com|fr|net|org|io|ai|co|be))(?:/[^\s]*)?",
                    task, _re_a.IGNORECASE
                )
                if dom:
                    target_url = ("https://" + dom.group(0)).rstrip(".,;)")

            # Détecter besoin de chercher
            search_kw = ["cherche", "recherche", "trouve", "search", "googl", "duckduck"]
            needs_search = any(k in tl for k in search_kw) and not target_url

            # ── Extension disponible ? (contenu fourni) ──────────────
            has_extension = bool(extracted_content)
            web_content = ""
            source_url  = navigated_url or ""

            if has_extension and extracted_content:
                # Extension a déjà fourni du contenu
                await step(f"📱 Contenu Chrome reçu ({len(extracted_content)} car.)", "chrome")
                web_content = extracted_content
                source_url  = navigated_url or "page active"

            elif target_url:
                # Naviguer vers l'URL
                is_github = "github.com" in target_url
                await step(
                    f"🐙 Accès GitHub…" if is_github else f"🌐 Navigation → {target_url[:55]}…",
                    "navigate"
                )
                web_content = await real_web_fetch(target_url)
                source_url  = target_url
                await step(f"📄 {len(web_content)} car. extraits", "extract")

                # Pour Google/DuckDuckGo → aussi lire le 1er résultat
                if "google.com/search" in target_url or "duckduckgo.com" in target_url:
                    first_m = _re_a.search(r"https?://(?!www\.google|duckduckgo)[^\s\n]+", web_content)
                    if first_m:
                        first_url = first_m.group(0).rstrip(".,;)")
                        await step(f"🔗 Lecture : {first_url[:50]}…", "fetch")
                        extra = await real_web_fetch(first_url)
                        if extra and len(extra) > 200:
                            web_content += "\n\n=== " + first_url + " ===\n" + extra
                            source_url = first_url

            elif needs_search:
                q = _re_a.sub(r"(?:cherche|recherche|trouve|search|sur google|sur le web)\s*", "", tl).strip()
                await step(f"🔍 Recherche : {q[:50]}…", "search")
                web_content = await real_web_search(q)
                source_url  = "DuckDuckGo"
                first_m = _re_a.search(r"https?://[^\s\n]+", web_content)
                if first_m:
                    first_url = first_m.group(0).rstrip(".,;)")
                    await step(f"📖 Lecture : {first_url[:50]}…", "fetch")
                    detail = await real_web_fetch(first_url)
                    if detail and len(detail) > 200:
                        web_content += "\n\n=== Détail ===\n" + detail
                        source_url = first_url

            # ── Analyse IA ────────────────────────────────────────────
            await step("💬 Analyse IA en cours…", "analyze")

            system_prompt = """Tu es l'Agent IA Zayado — un assistant pro pour indépendants et entrepreneurs.
Tu as accès à du contenu web réel ci-dessous. Réponds directement et précisément à la demande.
Règles :
- Réponds dans la langue de l'utilisateur
- Sois concret et actionnable
- Si tu as du contenu web → analyse-le et extrais l'essentiel
- Pour les tableaux de données → utilise la syntaxe markdown |col|col|
- NE dis jamais que tu ne peux pas naviguer"""

            user_msg = task
            if web_content:
                user_msg = f"Tâche : {task}\n\nContenu récupéré depuis {source_url} :\n---\n{web_content[:7000]}\n---\nRéponds à la tâche."

            full_response = ""
            try:
                async with httpx.AsyncClient(timeout=120.0) as http_client:
                    async with http_client.stream(
                        "POST",
                        f"{MAMMOTH_BASE_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                        json={
                            "model": AGENT_COMPLEX_MODEL,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user",   "content": user_msg}
                            ],
                            "stream": True,
                            "max_tokens": 4096,
                            "temperature": 0.3
                        }
                    ) as response:
                        if response.status_code != 200:
                            err_body = ""
                            async for chunk in response.aiter_bytes():
                                err_body += chunk.decode(errors='replace')
                            logger.error(f"Agent IA Mammoth error {response.status_code}: {err_body[:300]}")
                            await websocket.send_json({"type": "error", "message": f"Erreur IA ({response.status_code}): {err_body[:150]}"})
                            return
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                chunk_str = line[6:]
                                if chunk_str.strip() == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(chunk_str)
                                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if content:
                                        full_response += content
                                        await websocket.send_json({"type": "chunk", "content": content})
                                except (json.JSONDecodeError, IndexError):
                                    pass
            except httpx.TimeoutException:
                await websocket.send_json({"type": "error", "message": "Délai dépassé — tâche trop longue."})
                return
            except Exception as e:
                await websocket.send_json({"type": "error", "message": f"Erreur IA: {str(e)[:100]}"})
                return

            if not full_response:
                full_response = "Aucune réponse générée. Veuillez réessayer."

            # ── Déduire crédits ───────────────────────────────────────
            remaining = credits_needed
            pd  = min(user.credits or 0, remaining);           remaining -= pd
            bd  = min(user.bonus_credits or 0, remaining);     remaining -= bd
            pud = min(user.purchased_credits or 0, remaining)
            await db.execute(update(User).where(User.id == user_id).values(
                credits=User.credits - pd,
                bonus_credits=User.bonus_credits - bd,
                purchased_credits=User.purchased_credits - pud
            ))
            await db.commit()

            await websocket.send_json({
                "type": "result",
                "content": full_response,
                "credits_used": credits_needed,
                "source_url": source_url
            })

    except Exception as e:
        err_msg = str(e)
        if any(x in err_msg for x in ["TCPTransport", "handler is closed", "ConnectionReset", "WebSocket", "1000", "1001"]):
            return  # Fermeture propre — ne pas afficher d'erreur
        try:
            await websocket.send_json({"type": "error", "message": err_msg[:200]})
        except Exception:
            pass



@api_router.websocket("/ws/extension")
async def websocket_extension(websocket: WebSocket, token: str = ""):
    """WebSocket endpoint for Chrome extension real-time communication."""
    # IMPORTANT : accept() doit être appelé AVANT close() sinon HTTP 200 au lieu du handshake WS
    await websocket.accept()
    user_id = None
    try:
        if not token:
            await websocket.close(code=4001, reason="Token manquant")
            return
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Token invalide")
            return
    except Exception:
        await websocket.close(code=4001, reason="Token invalide")
        return

    active_ws_connections[str(user_id)] = websocket
    logger.info(f"[WS] Extension connected for user: {user_id}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "command_result":
                command_id = message.get("command_id")
                logger.info(f"[WS] Command result {command_id}: {message.get('result', {}).get('success', False)}")
    except WebSocketDisconnect:
        logger.info(f"[WS] Extension disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"[WS] WebSocket error: {e}")
    finally:
        active_ws_connections.pop(str(user_id), None)

async def send_command_to_extension(user_id: str, command: dict) -> bool:
    ws = active_ws_connections.get(str(user_id))
    if ws:
        try:
            await ws.send_text(json.dumps(command))
            return True
        except Exception:
            active_ws_connections.pop(str(user_id), None)
    return False

@api_router.post("/extension/command")
async def send_extension_command(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorise")
    tok = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(tok, JWT_SECRET, algorithms=["HS256"])
        user_id = str(payload.get("user_id") or payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")
    body = await request.json()
    command_id = str(uuid.uuid4())[:8]
    command = {"type": body.get("type"), "command_id": command_id, **body.get("data", {})}
    sent = await send_command_to_extension(user_id, command)
    if sent:
        return {"success": True, "command_id": command_id}
    return {"success": False, "error": "Extension non connectee"}

@api_router.get("/extension/status")
async def extension_status(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorise")
    tok = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(tok, JWT_SECRET, algorithms=["HS256"])
        user_id = str(payload.get("user_id") or payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")
    connected = str(user_id) in active_ws_connections
    return {"connected": connected, "user_id": user_id, "active_connections": len(active_ws_connections)}

# ==================== SPA FALLBACK — React Router ====================
from pathlib import Path as _Path

# Note: Router mounting is done in server.py

# ═══════════════════════════════════════════════════════════════
# CRON — Rapport hebdomadaire automatique (lundi 8h) — asyncio natif
# ═══════════════════════════════════════════════════════════════
import asyncio as _asyncio
from datetime import datetime as _dt, timedelta as _td, timezone as _tz

async def send_weekly_report_for_user(user_id: str, user_email: str, user_name: str):
    """Génère et envoie le rapport hebdomadaire d'un utilisateur."""
    try:
        async with async_session_factory() as db:
            week_ago = _dt.now(_tz.utc) - _td(days=7)
            convs_result = await db.execute(
                select(Conversation).where(
                    Conversation.user_id == user_id,
                    Conversation.created_at >= week_ago
                )
            )
            convs = convs_result.scalars().all()
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return
            mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
            if not mammoth_key:
                return
            report_prompt = f"Tu es l'assistant IA Zayado. Génère un bref bilan hebdomadaire pour {user_name}. Cette semaine : {len(convs)} conversations. Plan : {user.plan or 'free'}. Crédits restants : {(user.credits or 0)+(user.bonus_credits or 0)}. Écris 3 phrases d'encouragement + 1 conseil actionnable. Inspiré de The One Thing, Atomic Habits, GTD."
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{MAMMOTH_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                    json={"model": "claude-haiku-4-5-20251001", "messages": [{"role": "user", "content": report_prompt}], "max_tokens": 300}
                )
                if resp.status_code != 200:
                    return
                ai_message = resp.json()["choices"][0]["message"]["content"]
            brevo_key = os.environ.get("BREVO_API_KEY", "")
            if not brevo_key:
                return
            total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
            html_body = f"""<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <div style="background:linear-gradient(135deg,#1A365D,#2C5282);padding:24px;border-radius:12px;color:white;margin-bottom:20px;">
    <h1 style="margin:0;font-size:20px;font-weight:800;">Votre bilan ZAYADO 📊</h1>
    <p style="margin:4px 0 0;opacity:.8;font-size:13px;">Semaine du {_dt.now().strftime('%d %B %Y')}</p>
  </div>
  <div style="background:#F5F5F0;border-radius:10px;padding:14px;margin-bottom:14px;display:flex;gap:16px;text-align:center;">
    <div style="flex:1"><div style="font-size:24px;font-weight:800;color:#1E3A8A;">{len(convs)}</div><div style="font-size:11px;color:#6B7280;">Conversations</div></div>
    <div style="flex:1"><div style="font-size:24px;font-weight:800;color:#16A34A;">{total_credits}</div><div style="font-size:11px;color:#6B7280;">Crédits</div></div>
    <div style="flex:1"><div style="font-size:24px;font-weight:800;color:#D97706;">{user.plan or 'Free'}</div><div style="font-size:11px;color:#6B7280;">Plan</div></div>
  </div>
  <div style="background:#fff;border:1px solid #E5E5E5;border-radius:10px;padding:14px;margin-bottom:14px;">
    <p style="margin:0;font-size:13px;line-height:1.6;color:#374151;">{ai_message}</p>
  </div>
  <div style="text-align:center;">
    <a href="https://app.zayado.net/app" style="display:inline-block;background:#1E3A8A;color:white;padding:11px 22px;border-radius:8px;text-decoration:none;font-weight:600;font-size:13px;">Ouvrir mon espace ZAYADO →</a>
  </div>
</body></html>"""
            await asyncio.get_running_loop().run_in_executor(None, lambda: __import__('requests').post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": brevo_key, "Content-Type": "application/json"},
                json={"sender": {"name": "ZAYADO AI", "email": "noreply@zayado.net"},
                      "to": [{"email": user_email, "name": user_name}],
                      "subject": f"📊 Votre bilan ZAYADO — {_dt.now().strftime('%d %B')}",
                      "htmlContent": html_body}, timeout=10
            ))
    except Exception as e:
        logger.error(f"Weekly report error for {user_id}: {e}")

async def _weekly_cron_loop():
    """Boucle asyncio native — vérifie chaque heure si c'est lundi 8h."""
    while True:
        try:
            now = _dt.now()
            # Lundi (weekday=0) à 8h00
            if now.weekday() == 0 and now.hour == 8 and now.minute < 5:
                logger.info("🕐 CRON Weekly Report — démarrage")
                async with async_session_factory() as db:
                    result = await db.execute(select(User).where(User.is_active == True).limit(500))
                    users = result.scalars().all()
                count = 0
                for u in users:
                    if u.email and u.name:
                        await send_weekly_report_for_user(u.id, u.email, u.name)
                        count += 1
                        await asyncio.sleep(0.5)
                logger.info(f"✅ CRON Weekly Report — {count} emails envoyés")
                await asyncio.sleep(300)  # Éviter double-envoi dans la même fenêtre 5min
        except Exception as e:
            logger.error(f"CRON Weekly error: {e}")
        await asyncio.sleep(3600)  # Vérifier toutes les heures

# ── Démarrer le CRON hebdomadaire au lancement ──────────────


# ── Newsletter signup endpoint ──────────────────────────────────
class NewsletterRequest(BaseModel):
    email: str
    source: str = "general"

@api_router.post("/public/newsletter")
async def newsletter_signup(req: NewsletterRequest, db: AsyncSession = Depends(get_db)):
    """Store newsletter signup for Boutique IA or other sources."""
    config = load_admin_config()
    subs = config.get("newsletter_subscribers", [])
    # Avoid duplicates
    if not any(s.get("email") == req.email for s in subs):
        subs.append({"email": req.email, "source": req.source, "date": datetime.now(timezone.utc).isoformat()})
        config["newsletter_subscribers"] = subs
        save_admin_config(config)
    return {"status": "ok", "message": "Inscription enregistree"}

# ── Simulateur / Resources config endpoints ─────────────────────
@api_router.get("/admin/simulateur-config")
async def get_simulateur_config(user=Depends(get_current_user)):
    config = load_admin_config()
    return config.get("simulateur_items", [])

@api_router.post("/admin/simulateur-config")
async def save_simulateur_config(request: Request, user=Depends(get_admin_user)):
    body = await request.json()
    config = load_admin_config()
    config["simulateur_items"] = body.get("items", [])
    save_admin_config(config)
    return {"status": "ok"}

@api_router.get("/admin/resources-config")
async def get_resources_config(user=Depends(get_current_user)):
    config = load_admin_config()
    return config.get("resources_links", [])

@api_router.post("/admin/resources-config")
async def save_resources_config(request: Request, user=Depends(get_admin_user)):
    body = await request.json()
    config = load_admin_config()
    config["resources_links"] = body.get("links", [])
    save_admin_config(config)
    return {"status": "ok"}


@api_router.delete("/timer/sessions/{session_id}")
async def delete_timer_session(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Supprimer une session timer."""
    from sqlalchemy import text as sa_text
    try:
        await db.execute(sa_text(
            "DELETE FROM timer_sessions WHERE id = :id AND user_id = :uid"
        ), {"id": session_id, "uid": user.id})
        await db.commit()
        return {"ok": True}
    except Exception:
        return {"ok": False}

@api_router.post("/chat/quick")
async def chat_quick(data: dict, user: User = Depends(get_current_user)):
    """Appel IA rapide pour les features internes (processus, analyse, etc.)."""
    import httpx
    prompt = data.get("prompt", "")
    mode = data.get("mode", "fast")
    if not prompt:
        raise HTTPException(400, "prompt requis")
    
    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        return {"response": "Service IA non configuré.", "ok": False}
    
    model = "claude-haiku-4-5-20251001" if mode == "fast" else "claude-sonnet-4-5-20251022"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.mammouth.ai/v1/messages",
                headers={"x-api-key": mammoth_key, "Content-Type": "application/json"},
                json={
                    "model": model,
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            if resp.status_code == 200:
                body = resp.json()
                text = body.get("content", [{}])[0].get("text", "")
                return {"response": text, "ok": True}
            return {"response": "Erreur IA temporaire.", "ok": False}
    except Exception as e:
        return {"response": f"Erreur: {str(e)[:100]}", "ok": False}

