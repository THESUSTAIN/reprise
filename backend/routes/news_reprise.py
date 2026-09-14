"""
News-Reprise — boîte de reprise éditoriale assistée par IA.

Flux métier :
  1. On transfère un email "concurrent"/inspirant vers news-reprise@zayado.net
     (webhook inbound Brevo) OU on le colle manuellement depuis le plugin admin.
  2. L'IA (Mammouth/Claude) reformule le contenu AU NOM DE ZAYADO, conforme à la
     niche (marketplace de mutualisation, entrepreneuriat responsable…), retire
     toute marque tierce, et propose un objet + corps HTML propres.
  3. Le résultat est stocké en BROUILLON avec une date d'envoi pré-remplie
     (par défaut +72h) et, si une liste Brevo est configurée, poussé en
     brouillon de campagne Brevo (best-effort).
  4. Une notification email est envoyée à l'équipe ("un mail a été réajusté").
  5. L'humain relit et valide (approve) ou rejette depuis le plugin admin.

Sécurité :
  - Endpoints de gestion (list/submit/approve/reject) : JWT admin (get_admin_user).
  - Webhook inbound : header `X-Zayado-Secret` == WP_CONNECTOR_SECRET (machine).
"""
import os
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, async_session_factory
from deps import get_admin_user
from models import User

logger = logging.getLogger("news_reprise")

news_reprise_router = APIRouter(prefix="/news-reprise", tags=["News Reprise"])

WP_CONNECTOR_SECRET = os.environ.get("WP_CONNECTOR_SECRET")
MAILBOX = os.environ.get("NEWS_REPRISE_MAILBOX", "news-reprise@zayado.net")
NOTIFY_TO = os.environ.get("NEWS_REPRISE_NOTIFY", os.environ.get("BREVO_SENDER_EMAIL", "admin@zayado.net"))
DEFAULT_DELAY_HOURS = int(os.environ.get("NEWS_REPRISE_DELAY_HOURS", "72"))
BREVO_LIST_ID = os.environ.get("NEWS_REPRISE_BREVO_LIST_ID")  # optionnel


# ─────────────────────────── DB (table dédiée, auto-créée) ───────────────────────────
async def _ensure_table(db: AsyncSession):
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS news_reprise_drafts (
            id VARCHAR(36) PRIMARY KEY,
            source_from TEXT,
            source_subject TEXT,
            original_body TEXT,
            rewritten_subject TEXT,
            rewritten_body TEXT,
            status VARCHAR(20) DEFAULT 'draft',
            scheduled_at VARCHAR(40),
            brevo_campaign_id VARCHAR(64),
            created_at VARCHAR(40),
            updated_at VARCHAR(40)
        )
    """))
    await db.commit()


def _uid():
    return str(uuid.uuid4())


# ─────────────────────────── IA de reformulation ───────────────────────────
async def _rewrite_email(subject: str, body: str) -> dict:
    """Reformule un email au nom de Zayado. Renvoie {subject, body_html}."""
    system = (
        "Tu es le responsable éditorial de Zayado, une marketplace de mutualisation "
        "pour entrepreneurs et TPE/PME (partage de ressources, entraide, entrepreneuriat "
        "responsable). On te transmet un email concurrent ou une actualité inspirante. "
        "Réécris-le INTÉGRALEMENT au nom de Zayado : supprime toute marque, logo, lien ou "
        "signature tiers ; adapte le ton (chaleureux, professionnel, orienté valeur) ; "
        "aligne le propos sur notre niche (mutualisation, marketplace, entraide entre pros). "
        "Réponds UNIQUEMENT en JSON valide : "
        '{"subject":"...","body_html":"<p>...</p>"}. '
        "Le body_html doit être du HTML email propre (paragraphes, éventuellement un titre h2 "
        "et un bouton CTA vers https://app.zayado.net). En français."
    )
    user = f"Objet reçu : {subject or '(sans objet)'}\n\nContenu reçu :\n{(body or '')[:6000]}"
    try:
        from mammouth_client import chat as _llm_chat
        raw = await _llm_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model="claude-sonnet-4-6", max_tokens=1500, temperature=0.5, timeout=45,
        )
        s = raw.strip()
        if s.startswith("```"):
            s = s.split("```", 2)[1].replace("json", "", 1).strip() if "```" in s else s
        start, end = s.find("{"), s.rfind("}")
        data = json.loads(s[start:end + 1]) if start >= 0 and end > start else {}
        subj = (data.get("subject") or "").strip() or f"[Zayado] {subject}"
        html = (data.get("body_html") or "").strip()
        if not html:
            raise ValueError("empty body_html")
        return {"subject": subj[:200], "body_html": html}
    except Exception as e:
        logger.warning("news-reprise rewrite fallback (%s)", e)
        # Repli : encadre le contenu original dans une coquille Zayado
        safe_body = (body or "").replace("<", "&lt;").replace(">", "&gt;")
        return {
            "subject": f"[Zayado] {subject or 'Actualité à relayer'}",
            "body_html": (
                f"<h2>Une actualité pour la communauté Zayado</h2>"
                f"<p>{safe_body[:4000]}</p>"
                f'<p><a href="https://app.zayado.net" style="background:#F2B93B;color:#0F1B3D;'
                f'padding:10px 18px;border-radius:24px;text-decoration:none;font-weight:600">Découvrir Zayado</a></p>'
            ),
        }


async def _create_brevo_draft(subject: str, html: str, scheduled_at: str) -> str | None:
    """Crée une campagne Brevo en brouillon (best-effort). Renvoie l'id ou None."""
    if not BREVO_LIST_ID:
        return None
    api_key = os.environ.get("BREVO_API_KEY")
    sender = os.environ.get("BREVO_SENDER_EMAIL")
    if not api_key or not sender:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.brevo.com/v3/emailCampaigns",
                headers={"api-key": api_key, "Content-Type": "application/json", "accept": "application/json"},
                json={
                    "name": f"News-Reprise {subject[:40]}",
                    "subject": subject,
                    "sender": {"email": sender, "name": os.environ.get("BREVO_SENDER_NAME", "Zayado")},
                    "htmlContent": html,
                    "scheduledAt": scheduled_at,
                    "recipients": {"listIds": [int(BREVO_LIST_ID)]},
                },
            )
        if r.status_code in (200, 201):
            return str(r.json().get("id"))
        logger.warning("Brevo draft campaign KO %s %s", r.status_code, r.text[:200])
    except Exception as e:
        logger.warning("Brevo draft campaign error: %s", e)
    return None


def _notify_team(subject: str, from_addr: str):
    try:
        from utils import send_brevo_email
        send_brevo_email(
            to_email=NOTIFY_TO,
            subject="✍️ Un mail a été réajusté (News-Reprise)",
            html_content=(
                f"<p>Bonjour,</p><p>L'IA vient de réajuster un email au nom de Zayado.</p>"
                f"<ul><li><strong>Source :</strong> {from_addr or 'inconnue'}</li>"
                f"<li><strong>Nouvel objet :</strong> {subject}</li></ul>"
                f"<p>Il est en <strong>brouillon</strong>, planifié à +{DEFAULT_DELAY_HOURS}h. "
                f'Relisez et validez depuis WordPress → MyExtension AI → News-Reprise.</p>'
            ),
            brand="zayado",
        )
    except Exception as e:
        logger.warning("news-reprise notify KO: %s", e)


async def _process_and_store(from_addr: str, subject: str, body: str) -> dict:
    rewritten = await _rewrite_email(subject, body)
    now = datetime.now(timezone.utc)
    scheduled_at = (now + timedelta(hours=DEFAULT_DELAY_HOURS)).replace(microsecond=0).isoformat()
    draft_id = _uid()
    campaign_id = await _create_brevo_draft(rewritten["subject"], rewritten["body_html"], scheduled_at)
    async with async_session_factory() as db:
        await _ensure_table(db)
        await db.execute(text("""
            INSERT INTO news_reprise_drafts
            (id, source_from, source_subject, original_body, rewritten_subject, rewritten_body,
             status, scheduled_at, brevo_campaign_id, created_at, updated_at)
            VALUES (:id, :sf, :ss, :ob, :rs, :rb, 'draft', :sa, :cid, :ca, :ua)
        """), {
            "id": draft_id, "sf": from_addr, "ss": subject, "ob": (body or "")[:8000],
            "rs": rewritten["subject"], "rb": rewritten["body_html"],
            "sa": scheduled_at, "cid": campaign_id,
            "ca": now.isoformat(), "ua": now.isoformat(),
        })
        await db.commit()
    _notify_team(rewritten["subject"], from_addr)
    return {"id": draft_id, "status": "draft", "scheduled_at": scheduled_at,
            "rewritten_subject": rewritten["subject"], "brevo_campaign_id": campaign_id}


# ─────────────────────────── Webhook inbound (machine) ───────────────────────────
@news_reprise_router.post("/inbound")
async def inbound(request: Request, x_zayado_secret: str = Header(default=None)):
    """Webhook inbound. Accepte le format Brevo Inbound (items[]) ou un JSON simple
    {from, subject, body}. Sécurisé par X-Zayado-Secret."""
    import hmac
    if not WP_CONNECTOR_SECRET or not x_zayado_secret or not hmac.compare_digest(x_zayado_secret, WP_CONNECTOR_SECRET):
        raise HTTPException(401, "Secret invalide")
    payload = await request.json()
    # Format Brevo inbound
    if isinstance(payload, dict) and payload.get("items"):
        item = payload["items"][0]
        frm = ((item.get("From") or {}).get("Address")) or item.get("from") or ""
        subject = item.get("Subject") or item.get("subject") or ""
        body = item.get("RawHtmlBody") or item.get("RawTextBody") or item.get("body") or ""
    else:
        frm = payload.get("from") or payload.get("from_email") or ""
        subject = payload.get("subject") or ""
        body = payload.get("body") or payload.get("text") or payload.get("html") or ""
    result = await _process_and_store(frm, subject, body)
    return {"ok": True, **result}


# ─────────────────────────── Gestion (admin JWT) ───────────────────────────
class SubmitPayload(BaseModel):
    from_email: str = ""
    subject: str = ""
    body: str


@news_reprise_router.post("/submit")
async def submit_manual(payload: SubmitPayload, admin: User = Depends(get_admin_user)):
    """Collage manuel d'un email depuis le plugin admin."""
    if not payload.body.strip():
        raise HTTPException(400, "Corps de l'email requis")
    result = await _process_and_store(payload.from_email, payload.subject, payload.body)
    return {"ok": True, **result}


@news_reprise_router.get("/list")
async def list_drafts(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _ensure_table(db)
    rows = (await db.execute(text(
        "SELECT id, source_from, source_subject, rewritten_subject, rewritten_body, status, "
        "scheduled_at, brevo_campaign_id, created_at FROM news_reprise_drafts "
        "ORDER BY created_at DESC LIMIT 100"
    ))).fetchall()
    items = [{
        "id": r[0], "source_from": r[1], "source_subject": r[2], "rewritten_subject": r[3],
        "rewritten_body": r[4], "status": r[5], "scheduled_at": r[6],
        "brevo_campaign_id": r[7], "created_at": r[8],
    } for r in rows]
    return {"mailbox": MAILBOX, "delay_hours": DEFAULT_DELAY_HOURS, "drafts": items, "total": len(items)}


@news_reprise_router.put("/{draft_id}/approve")
async def approve(draft_id: str, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _ensure_table(db)
    row = (await db.execute(text(
        "SELECT rewritten_subject, rewritten_body FROM news_reprise_drafts WHERE id = :id"
    ), {"id": draft_id})).fetchone()
    if not row:
        raise HTTPException(404, "Brouillon introuvable")
    await db.execute(text(
        "UPDATE news_reprise_drafts SET status='approved', updated_at=:u WHERE id=:id"
    ), {"u": datetime.now(timezone.utc).isoformat(), "id": draft_id})
    await db.commit()
    return {"ok": True, "status": "approved",
            "note": "Le brouillon Brevo reste planifié ; validez/envoyez la campagne côté Brevo."}


@news_reprise_router.put("/{draft_id}/reject")
async def reject(draft_id: str, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await _ensure_table(db)
    await db.execute(text(
        "UPDATE news_reprise_drafts SET status='rejected', updated_at=:u WHERE id=:id"
    ), {"u": datetime.now(timezone.utc).isoformat(), "id": draft_id})
    await db.commit()
    return {"ok": True, "status": "rejected"}
