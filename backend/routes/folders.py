"""Folder routes for Extension IA API."""
import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from database import get_db
from models import Folder, Conversation
from deps import get_current_user, User

folders_router = APIRouter(prefix="/folders", tags=["Folders"])

@folders_router.get("")
async def get_folders(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Folder).where(Folder.user_id == user.id).order_by(Folder.created_at.desc()))
    folders = result.scalars().all()
    # Count conversations per folder
    counts_result = await db.execute(
        select(Conversation.folder_id, func.count(Conversation.id))
        .where(Conversation.user_id == user.id, Conversation.folder_id.isnot(None))
        .group_by(Conversation.folder_id)
    )
    counts = {row[0]: row[1] for row in counts_result.all()}
    return [{
        "id": f.id, "name": f.name, "color": f.color, "emoji": f.emoji,
        "conversation_count": counts.get(f.id, 0),
        "created_at": f.created_at.isoformat()
    } for f in folders]

@folders_router.get("/{folder_id}")
async def get_folder_detail(folder_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id))
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    convs_result = await db.execute(
        select(Conversation).where(Conversation.folder_id == folder_id).order_by(Conversation.updated_at.desc())
    )
    conversations = convs_result.scalars().all()

    conv_list = []
    total_messages = 0
    total_credits = 0
    attachment_count = 0
    attachments = []

    for c in conversations:
        msgs = c.messages if isinstance(c.messages, list) else []
        msg_count = len(msgs)
        credits_used = c.total_credits_used or 0
        total_messages += msg_count
        total_credits += credits_used

        for i, msg in enumerate(msgs):
            if isinstance(msg, dict) and msg.get("attachments"):
                for att in msg["attachments"]:
                    attachment_count += 1
                    attachments.append({
                        "name": att.get("name", "Fichier"),
                        "type": att.get("type", "file"),
                        "conversation_id": c.id,
                        "conversation_title": c.title,
                    })

        conv_list.append({
            "id": c.id,
            "title": c.title,
            "mode": c.mode,
            "message_count": msg_count,
            "total_credits_used": credits_used,
            "is_favorite": getattr(c, 'is_favorite', False),
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    return {
        "id": folder.id,
        "name": folder.name,
        "color": folder.color,
        "emoji": folder.emoji,
        "description": folder.description,
        "knowledge_notes": folder.knowledge_notes,
        "ai_intro": folder.ai_intro,
        "team_id": folder.team_id,
        "created_at": folder.created_at.isoformat(),
        "stats": {
            "conversation_count": len(conversations),
            "total_messages": total_messages,
            "total_credits_used": total_credits,
            "attachment_count": attachment_count,
        },
        "conversations": conv_list,
        "attachments": attachments[:50],
    }

@folders_router.post("")
async def create_folder(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    # #155 — Validate hex color format
    import re as _re_color
    color = data.get("color", "#1E3A8A")
    if not _re_color.match(r'^#[0-9a-fA-F]{6}$', color):
        color = "#1E3A8A"
    folder = Folder(
        user_id=user.id,
        name=name,
        color=color,
        emoji=data.get("emoji"),
        team_id=data.get("team_id"),
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return {"id": folder.id, "name": folder.name, "color": folder.color, "emoji": folder.emoji, "team_id": folder.team_id, "created_at": folder.created_at.isoformat()}

@folders_router.put("/{folder_id}")
async def update_folder(folder_id: str, data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    values = {}
    old_team_id = None
    for key in ("name", "color", "emoji", "description", "knowledge_notes", "ai_intro", "team_id"):
        if key in data:
            val = data[key]
            if key == "name" and not str(val).strip():
                raise HTTPException(status_code=400, detail="Name is required")
            values[key] = val
    if not values:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Check if team_id is changing (for notifications)
    new_team_id = values.get("team_id")
    if "team_id" in values and new_team_id:
        result = await db.execute(select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id))
        folder = result.scalar_one_or_none()
        if folder:
            old_team_id = getattr(folder, 'team_id', None)

    await db.execute(update(Folder).where(Folder.id == folder_id, Folder.user_id == user.id).values(**values))
    await db.commit()

    # Send notifications when folder is assigned to a team
    if "team_id" in values and new_team_id and new_team_id != old_team_id:
        try:
            await _notify_folder_shared(db, user, folder_id, new_team_id, values.get("name") or (folder.name if folder else "Dossier"))
        except Exception as e:
            import logging
            logging.getLogger("folders").warning(f"Folder share notification error: {e}")

    return {"status": "updated"}


async def _notify_folder_shared(db: AsyncSession, owner: User, folder_id: str, team_id: str, folder_name: str):
    """Send in-app + email notifications to team members when a folder is shared."""
    from models import Team, TeamMember
    import json
    import os
    import logging
    logger = logging.getLogger("folders")

    # Get team info
    team_result = await db.execute(select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()
    if not team:
        return

    # Get team members (exclude the owner who shared)
    members_result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.status == "active")
    )
    members = members_result.scalars().all()

    # Store in-app notification via centralized config helpers
    from utils import load_admin_config, save_admin_config
    config = load_admin_config()

    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).isoformat()

    for member in members:
        if member.user_id and member.user_id != owner.id:
            notif_key = f"folder_notifs_{member.user_id}"
            if notif_key not in config:
                config[notif_key] = []
            config[notif_key].append({
                "id": f"folder_shared_{folder_id}_{now_str}",
                "type": "info",
                "title": "Dossier partage",
                "message": f"{owner.name or owner.email} a partage le dossier '{folder_name}' avec l'equipe {team.name}.",
                "created_at": now_str,
                "folder_id": folder_id
            })
            config[notif_key] = config[notif_key][-20:]

            # Send email notification via Brevo
            if member.email:
                try:
                    from utils import send_brevo_email
                    import asyncio
                    loop = asyncio.get_running_loop()
                    _email = member.email
                    _name = member.email.split("@")[0]
                    _subject = f"Dossier partage : {folder_name}"
                    _frontend = os.environ.get("FRONTEND_URL", "https://app.zayado.net")
                    _html = f"""
                        <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;padding:30px;background:#F5F5F0;border-radius:12px">
                            <div style="background:#1E3A8A;color:white;padding:16px 24px;border-radius:8px;text-align:center;margin-bottom:20px">
                                <h2 style="margin:0;font-size:18px">Dossier partage avec votre equipe</h2>
                            </div>
                            <p style="color:#333;font-size:14px"><strong>{owner.name or owner.email}</strong> a partage le dossier <strong>"{folder_name}"</strong> avec l'equipe <strong>{team.name}</strong>.</p>
                            <p style="color:#666;font-size:13px">Connectez-vous a Zayado pour y acceder.</p>
                            <div style="text-align:center;margin-top:20px">
                                <a href="{_frontend}/chat" style="background:#1E3A8A;color:white;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:14px">Ouvrir Zayado</a>
                            </div>
                        </div>
                        """
                    loop.run_in_executor(None, lambda: send_brevo_email(
                        to_email=_email, to_name=_name,
                        subject=_subject, html_content=_html
                    ))
                    # Note: fire-and-forget via run_in_executor is intentional (non-blocking)
                    logger.info(f"Folder share email sent to {member.email}")
                except Exception as email_err:
                    logger.warning(f"Failed to send folder share email to {member.email}: {email_err}")

    try:
        save_admin_config(config)
    except Exception as save_err:
        logger.warning(f"Failed to save folder notifications: {save_err}")

@folders_router.delete("/{folder_id}")
async def delete_folder(folder_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(update(Conversation).where(Conversation.folder_id == folder_id, Conversation.user_id == user.id).values(folder_id=None))
    await db.execute(delete(Folder).where(Folder.id == folder_id, Folder.user_id == user.id))
    await db.commit()
    return {"status": "deleted"}
