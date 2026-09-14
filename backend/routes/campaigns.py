"""Reminders + Welcome Blast — endpoints admin pour campagnes / relances.
Branche sur la table admin_reminders et email_campaigns (cf models.py).
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, async_session_factory
from deps import get_admin_user
from models import User, AdminReminder, EmailCampaign

logger = logging.getLogger(__name__)
campaigns_router = APIRouter(tags=["admin-campaigns"])


# ─────────────── Reminders ───────────────
class ReminderCreate(BaseModel):
    type: str = "email"  # email | sms | whatsapp
    target_email: Optional[str] = None
    target_user_id: Optional[str] = None
    target_cohort: Optional[str] = None
    subject: str
    body_html: str
    brand: str = "myextension"
    scheduled_at: Optional[datetime] = None
    send_now: bool = False


@campaigns_router.get("/admin/reminders")
async def list_reminders(admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(AdminReminder).order_by(AdminReminder.created_at.desc()).limit(100))).scalars().all()
    return {"reminders": [{
        "id": r.id, "type": r.type, "target_email": r.target_email, "target_user_id": r.target_user_id,
        "target_cohort": r.target_cohort, "subject": r.subject, "brand": r.brand,
        "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
        "status": r.status, "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]}


@campaigns_router.post("/admin/reminders")
async def create_reminder(body: ReminderCreate, bg: BackgroundTasks,
                          admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    if not body.target_email and not body.target_user_id and not body.target_cohort:
        raise HTTPException(status_code=400, detail="Spécifiez target_email, target_user_id ou target_cohort.")
    r = AdminReminder(
        type=body.type, target_email=body.target_email, target_user_id=body.target_user_id,
        target_cohort=body.target_cohort, subject=body.subject[:200], body_html=body.body_html,
        brand=body.brand, scheduled_at=body.scheduled_at,
        status="sent" if body.send_now else "pending",
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    if body.send_now:
        bg.add_task(_run_reminder, r.id)
    return {"id": r.id, "status": r.status}


@campaigns_router.post("/admin/reminders/{rid}/send")
async def send_reminder_now(rid: str, bg: BackgroundTasks, admin=Depends(get_admin_user)):
    bg.add_task(_run_reminder, rid)
    return {"status": "queued"}


@campaigns_router.delete("/admin/reminders/{rid}")
async def delete_reminder(rid: str, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(AdminReminder).where(AdminReminder.id == rid))).scalar_one_or_none()
    if not r: raise HTTPException(status_code=404, detail="Reminder introuvable")
    await db.delete(r)
    await db.commit()
    return {"status": "deleted"}


async def _run_reminder(reminder_id: str):
    """Background task — envoie la relance."""
    from utils import send_brevo_email
    async with async_session_factory() as db:
        r = (await db.execute(select(AdminReminder).where(AdminReminder.id == reminder_id))).scalar_one_or_none()
        if not r: return
        targets = []
        if r.target_email:
            targets.append(r.target_email)
        elif r.target_user_id:
            u = (await db.execute(select(User).where(User.id == r.target_user_id))).scalar_one_or_none()
            if u: targets.append(u.email)
        elif r.target_cohort == "free_users":
            users = (await db.execute(select(User).where(User.plan == "free"))).scalars().all()
            targets = [u.email for u in users]
        elif r.target_cohort == "all":
            users = (await db.execute(select(User))).scalars().all()
            targets = [u.email for u in users]

        ok = 0
        for email in targets:
            try:
                msg_id = send_brevo_email(to_email=email, subject=r.subject, html_content=r.body_html, brand=r.brand or "myextension")
                if msg_id: ok += 1
            except Exception as e:
                logger.warning(f"[reminder {reminder_id}] send fail to {email}: {e}")
        r.sent_at = datetime.now(timezone.utc)
        r.status = "sent" if ok else "failed"
        await db.commit()
        logger.info(f"[reminder {reminder_id}] sent to {ok}/{len(targets)} targets")


# ─────────────── Welcome Blast (campagne mass-mail) ───────────────
class CampaignCreate(BaseModel):
    name: str
    kind: str = "welcome_blast"
    subject: str
    body_html: str
    brand: str = "zayado"
    cohort: str = "all"           # all | free | pro | signups_7d | signups_30d
    send_now: bool = False


@campaigns_router.get("/admin/campaigns")
async def list_campaigns(admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(50))).scalars().all()
    return {"campaigns": [{
        "id": c.id, "name": c.name, "kind": c.kind, "subject": c.subject, "brand": c.brand,
        "status": c.status, "total_targets": c.total_targets, "total_sent": c.total_sent, "total_failed": c.total_failed,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
    } for c in rows]}


@campaigns_router.post("/admin/welcome-blast")
async def welcome_blast(body: CampaignCreate, bg: BackgroundTasks,
                        admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    c = EmailCampaign(
        name=body.name[:120], kind=body.kind, subject=body.subject[:200], body_html=body.body_html,
        brand=body.brand, filter_json=json.dumps({"cohort": body.cohort}),
        status="running" if body.send_now else "draft",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    if body.send_now:
        bg.add_task(_run_campaign, c.id)
    return {"id": c.id, "status": c.status}


@campaigns_router.post("/admin/campaigns/{cid}/send")
async def send_campaign_now(cid: str, bg: BackgroundTasks, admin=Depends(get_admin_user)):
    bg.add_task(_run_campaign, cid)
    return {"status": "queued"}


@campaigns_router.get("/admin/campaigns/{cid}")
async def get_campaign(cid: str, admin=Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    c = (await db.execute(select(EmailCampaign).where(EmailCampaign.id == cid))).scalar_one_or_none()
    if not c: raise HTTPException(status_code=404, detail="Campagne introuvable")
    return {"id": c.id, "name": c.name, "kind": c.kind, "subject": c.subject, "body_html": c.body_html,
            "brand": c.brand, "status": c.status, "total_targets": c.total_targets, "total_sent": c.total_sent,
            "total_failed": c.total_failed,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None}


async def _run_campaign(cid: str):
    """Background : envoie la campagne en lot avec rate limit léger."""
    import asyncio
    from utils import send_brevo_email
    async with async_session_factory() as db:
        c = (await db.execute(select(EmailCampaign).where(EmailCampaign.id == cid))).scalar_one_or_none()
        if not c: return
        try:
            cohort = (json.loads(c.filter_json or "{}")).get("cohort", "all")
        except Exception:
            cohort = "all"

        q = select(User)
        if cohort == "free": q = q.where(User.plan == "free")
        if cohort == "pro":  q = q.where(User.plan != "free")
        users = (await db.execute(q)).scalars().all()

        c.total_targets = len(users)
        c.status = "running"
        await db.commit()

        sent = 0; failed = 0
        for u in users:
            try:
                ok = send_brevo_email(to_email=u.email, to_name=u.name or "", subject=c.subject,
                                       html_content=c.body_html, brand=c.brand or "zayado")
                if ok: sent += 1
                else: failed += 1
            except Exception as e:
                failed += 1
                logger.warning(f"[campaign {cid}] fail to {u.email}: {e}")
            await asyncio.sleep(0.15)  # rate limit léger

        c.total_sent = sent; c.total_failed = failed
        c.status = "done" if failed == 0 else "done"  # done even with some failures
        c.completed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"[campaign {cid}] complete: {sent} sent / {failed} failed")
