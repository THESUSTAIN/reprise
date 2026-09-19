"""
Routes Équipe — Plan Team Zayado
Fonctionnalités : créer équipe, inviter membres, tableau de bord, crédits partagés, chat support IA
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
import secrets
import os
from datetime import datetime, timezone, timedelta

from database import get_db
from models import User, Team, TeamMember, Transaction, CreditLog, PlatformSetting
import json as _json
import logging

logger = logging.getLogger(__name__)

team_router = APIRouter(prefix="/team", tags=["Team"])
bearer = HTTPBearer(auto_error=False)

TEAM_LIMITS_DEFAULTS = {
    "free": {"max_teams": 0, "max_members": 0},
    "starter": {"max_teams": 0, "max_members": 0},
    "pro": {"max_teams": 0, "max_members": 0},
    "business": {"max_teams": 1, "max_members": 2},
    "team": {"max_teams": -1, "max_members": -1},
}


def utcnow():
    return datetime.now(timezone.utc)


async def get_team_limits(db: AsyncSession) -> dict:
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == "team_limits"))
    row = result.scalar_one_or_none()
    if row:
        try:
            return _json.loads(row.value)
        except Exception:
            pass
    return dict(TEAM_LIMITS_DEFAULTS)


# ─── Helpers ────────────────────────────────────────────────────

async def get_user(creds: HTTPAuthorizationCredentials, db: AsyncSession) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Non authentifié")
    from jose import jwt, JWTError
    from deps import JWT_SECRET
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = str(payload.get("user_id") or payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


async def get_user_team(user: User, db: AsyncSession, team_id: str = None) -> Optional[Team]:
    if team_id:
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        if team:
            if team.owner_id == user.id:
                return team
            mem = await db.execute(
                select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == user.id, TeamMember.status == "active")
            )
            if mem.scalar_one_or_none():
                return team
        return None
    # Multi-teams: user may own multiple teams, return the first one (ordered by created_at)
    result = await db.execute(select(Team).where(Team.owner_id == user.id).order_by(Team.created_at).limit(1))
    team = result.scalar_one_or_none()
    if team:
        return team
    # Check if user is a member of any team
    result = await db.execute(
        select(Team).join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user.id, TeamMember.status == "active", Team.owner_id != user.id)
        .order_by(Team.created_at).limit(1)
    )
    return result.scalar_one_or_none()


# ─── Schémas ────────────────────────────────────────────────────

class CreateTeamRequest(BaseModel):
    name: str

class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "member"

class AllocateCreditsRequest(BaseModel):
    member_id: str
    credits: int

class TeamChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


# ─── Routes ─────────────────────────────────────────────────────

@team_router.post("/create")
async def create_team(body: CreateTeamRequest, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="Le nom de l'equipe est obligatoire")
    team_name = body.name.strip()[:100]
    limits = await get_team_limits(db)
    plan_limits = limits.get(user.plan, limits.get("free", {"max_teams": 0, "max_members": 0}))
    max_teams = plan_limits.get("max_teams", 0)
    # Admin/super_admin bypass limits
    if user.role not in ("admin", "super_admin"):
        if max_teams == 0:
            raise HTTPException(status_code=403, detail="Votre forfait ne permet pas de creer d'equipe. Passez a un plan superieur.")
        if max_teams > 0:
            existing = await db.execute(select(func.count()).select_from(Team).where(Team.owner_id == user.id))
            team_count = existing.scalar() or 0
            if team_count >= max_teams:
                raise HTTPException(status_code=400, detail=f"Limite de {max_teams} equipe(s) atteinte pour votre forfait")
    else:
        existing = await db.execute(select(func.count()).select_from(Team).where(Team.owner_id == user.id))
        team_count = existing.scalar() or 0
        if max_teams > 0 and team_count >= max_teams and max_teams != -1:
            pass  # Admin can still create
    import secrets as _sec
    import logging as _log
    _logger = _log.getLogger("team")
    # Generate unique team_code with retry (avoid unique constraint collision)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            team_code = "ZAYA-" + _sec.token_hex(4).upper()
            team = Team(id=str(uuid.uuid4()), name=team_name, owner_id=user.id, shared_credits=0, max_seats=plan_limits.get("max_members", 10), team_code=team_code, bot_name="Assistant", bot_tone="professional", chatbot_enabled=True)
            db.add(team)
            owner_member = TeamMember(id=str(uuid.uuid4()), team_id=team.id, user_id=user.id, email=user.email, role="owner", status="active", joined_at=utcnow())
            db.add(owner_member)
            await db.commit()
            await db.refresh(team)
            return {"success": True, "team": {"id": team.id, "name": team.name}}
        except Exception as e:
            await db.rollback()
            _logger.error(f"[Team Create] Attempt {attempt+1}/{max_retries} failed for user {user.id}: {e}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"Erreur creation equipe. Reessayez. ({str(e)[:100]})")
    raise HTTPException(status_code=500, detail="Erreur creation equipe apres plusieurs tentatives.")


class RenameTeamRequest(BaseModel):
    name: str

@team_router.put("/rename/{team_id}")
async def rename_team(team_id: str, body: RenameTeamRequest, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    result = await db.execute(select(Team).where(Team.id == team_id, Team.owner_id == user.id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Equipe introuvable ou vous n'etes pas proprietaire")
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Nom invalide")
    team.name = body.name.strip()
    await db.commit()
    return {"success": True, "name": team.name}


@team_router.delete("/delete/{team_id}")
async def delete_team(team_id: str, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    result = await db.execute(select(Team).where(Team.id == team_id, Team.owner_id == user.id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Equipe introuvable ou vous n'etes pas proprietaire")
    # Supprimer les membres, logs et fichiers knowledge associés
    await db.execute(delete(TeamMember).where(TeamMember.team_id == team_id))
    await db.execute(delete(CreditLog).where(CreditLog.team_id == team_id))
    try:
        from models import KnowledgeFile
        await db.execute(delete(KnowledgeFile).where(KnowledgeFile.team_id == team_id))
    except Exception:
        pass
    await db.delete(team)
    await db.commit()
    return {"success": True, "message": "Equipe supprimee"}



@team_router.get("/list")
async def list_my_teams(db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Liste toutes les équipes dont l'utilisateur est propriétaire ou membre actif."""
    user = await get_user(creds, db)
    # Owned teams
    owned_res = await db.execute(select(Team).where(Team.owner_id == user.id).order_by(Team.created_at))
    owned = owned_res.scalars().all()
    # Member teams (not owned)
    member_res = await db.execute(
        select(Team).join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user.id, TeamMember.status == "active", Team.owner_id != user.id)
    )
    member_teams = member_res.scalars().all()
    teams = []
    for t in list(owned) + list(member_teams):
        teams.append({
            "id": t.id, "name": t.name, "team_code": t.team_code,
            "shared_credits": t.shared_credits or 0,
            "is_owner": t.owner_id == user.id,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    return {"teams": teams}


@team_router.get("/me")
async def get_my_team(team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    # If team_id is provided, load that specific team
    if team_id:
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        if not team:
            return {"team": None}
        # Check user is owner or active member
        is_owner = team.owner_id == user.id
        if not is_owner:
            mem_check = await db.execute(
                select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == user.id, TeamMember.status == "active")
            )
            if not mem_check.scalar_one_or_none():
                return {"team": None}
    else:
        team = await get_user_team(user, db)
    if not team:
        return {"team": None}
    try:
        result = await db.execute(select(TeamMember).where(TeamMember.team_id == team.id))
        members_db = result.scalars().all()
        members = []
        for m in members_db:
            member_data = {"id": m.id, "user_id": m.user_id, "email": m.email, "role": m.role, "status": m.status, "credits_allocated": getattr(m, 'credits_allocated', 0) or 0, "joined_at": m.joined_at.isoformat() if m.joined_at else None}
            if m.user_id:
                u_res = await db.execute(select(User).where(User.id == m.user_id))
                u = u_res.scalar_one_or_none()
                if u:
                    member_data["name"] = u.name
                    member_data["credits"] = (u.credits or 0) + (u.bonus_credits or 0) + (getattr(u, "purchased_credits", 0) or 0)
                    member_data["plan"] = u.plan
            members.append(member_data)
        active_count = sum(1 for m in members_db if m.status == "active")
        return {
            "team": {
                "id": team.id,
                "name": team.name,
                "owner_id": team.owner_id,
                "shared_credits": team.shared_credits or 0,
                "max_seats": team.max_seats or 10,
                "seats_used": active_count,
                "seats_available": (team.max_seats or 10) - active_count,
                "chatbot_enabled": getattr(team, 'chatbot_enabled', True),
                "team_code": getattr(team, 'team_code', None),
                "bot_name": getattr(team, 'bot_name', None) or "Assistant",
                "bot_tone": getattr(team, 'bot_tone', None) or "professional",
                "bot_context": getattr(team, 'bot_context', None) or "",
                "credit_limit_per_member": getattr(team, 'credit_limit_per_member', 50) or 50,
                "auto_recharge": getattr(team, 'auto_recharge', False) or False,
                "chrome_link": getattr(team, 'chrome_link', False) or False,
                "settings": getattr(team, 'settings', {}) or {},
                "primary_color": getattr(team, 'primary_color', None) or "#1D4E8A",
                "accent_color": getattr(team, 'accent_color', None) or "#C9A84C",
                "welcome_message": getattr(team, 'welcome_message', None) or "",
                "footer_text": getattr(team, 'footer_text', None) or "",
                "logo_url": getattr(team, 'logo_url', None) or "",
                "created_at": team.created_at.isoformat() if team.created_at else None
            },
            "members": members,
            "is_owner": team.owner_id == user.id,
        }
    except Exception as e:
        import logging
        logging.getLogger("team").error(f"team/me error for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@team_router.post("/invite")
async def invite_member(body: InviteMemberRequest, team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    team = await get_user_team(user, db, team_id)
    if not team or team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Seul le propriétaire peut inviter")
    # Check member limits based on plan
    limits = await get_team_limits(db)
    plan_limits = limits.get(user.plan, limits.get("free", {"max_teams": 0, "max_members": 0}))
    max_members = plan_limits.get("max_members", 0)
    if user.role not in ("admin", "super_admin") and max_members != -1:
        member_count_result = await db.execute(select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team.id))
        current_members = member_count_result.scalar() or 0
        if max_members > 0 and current_members >= max_members:
            raise HTTPException(status_code=400, detail=f"Limite de {max_members} membre(s) atteinte pour votre forfait")
        if max_members == 0:
            raise HTTPException(status_code=403, detail="Votre forfait ne permet pas d'inviter des membres")
    existing = await db.execute(select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.email == str(body.email)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cet email est déjà dans l'équipe")
    invite_token = secrets.token_urlsafe(32)
    member = TeamMember(id=str(uuid.uuid4()), team_id=team.id, email=str(body.email), role=body.role, status="pending", invite_token=invite_token)
    db.add(member)
    await db.commit()
    invite_url = f"https://app.zayado.net/join-team?token={invite_token}"
    # Envoyer l'email d'invitation via Brevo
    try:
        from utils import send_brevo_email
        invite_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;">
          <h2 style="color:#1E3A8A;">Vous êtes invité(e) à rejoindre l'équipe !</h2>
          <p>Bonjour,</p>
          <p><strong>{user.name or user.email}</strong> vous invite à rejoindre l'équipe <strong>"{team.name}"</strong> sur Extension IA.</p>
          <p style="margin:24px 0;">
            <a href="{invite_url}" style="background:#1E3A8A;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:bold;display:inline-block;">
              Accepter l'invitation →
            </a>
          </p>
          <p style="color:#6b7280;font-size:12px;">Ce lien expire dans 7 jours. Si vous n'attendiez pas cette invitation, ignorez cet email.</p>
        </div>"""
        import asyncio as _aio
        _to = str(body.email)
        _subj = f"[ZAYADO] Invitation à rejoindre l'équipe « {team.name} »"
        _html = invite_html
        _aio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(
            to_email=_to, to_name=_to, subject=_subj, html_content=_html
        ))
        email_sent = True
    except Exception as e:
        import logging
        logging.getLogger("extension_ia").error(f"[Team] Erreur envoi invitation: {e}")
        email_sent = False

    msg = f"Invitation envoyée à {body.email}" if email_sent else "Membre ajouté (email non envoyé — configurer BREVO_API_KEY)"
    return {"success": True, "invite_url": invite_url, "message": msg, "email_sent": bool(email_sent)}


@team_router.post("/join")
async def join_team(invite_token: str, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    result = await db.execute(select(TeamMember).where(TeamMember.invite_token == invite_token))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Invitation invalide ou expirée")
    if member.status != "pending":
        raise HTTPException(status_code=400, detail="Invitation déjà utilisée")
    member.user_id = user.id
    member.status = "active"
    member.invite_token = None
    member.joined_at = utcnow()
    await db.execute(update(User).where(User.id == user.id).values(plan="team"))
    await db.commit()
    return {"success": True, "message": "Vous avez rejoint l'équipe !"}


@team_router.delete("/members/{member_id}")
async def remove_member(member_id: str, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    team = await get_user_team(user, db)
    if not team or team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Seul le propriétaire peut retirer des membres")
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team.id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    if member.role == "owner":
        raise HTTPException(status_code=400, detail="Impossible de retirer le propriétaire")
    if member.user_id:
        await db.execute(update(User).where(User.id == member.user_id).values(plan="free"))
    await db.delete(member)
    await db.commit()
    return {"success": True}


@team_router.post("/credits/allocate")
async def allocate_credits(body: AllocateCreditsRequest, team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user = await get_user(creds, db)
    team = await get_user_team(user, db, team_id)
    if not team or team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Seul le propriétaire peut allouer des crédits")
    if body.credits <= 0:
        raise HTTPException(status_code=400, detail="Montant invalide")
    if team.shared_credits < body.credits:
        raise HTTPException(status_code=400, detail=f"Crédits insuffisants ({team.shared_credits} disponibles)")
    result = await db.execute(select(TeamMember).where(TeamMember.id == body.member_id, TeamMember.team_id == team.id))
    member = result.scalar_one_or_none()
    if not member or not member.user_id:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    # UPDATE atomique pour éviter la race condition (bug #6)
    atomic = await db.execute(
        update(Team)
        .where(Team.id == team.id, Team.shared_credits >= body.credits)
        .values(shared_credits=Team.shared_credits - body.credits)
    )
    if atomic.rowcount == 0:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Crédits insuffisants (conflit concurrent)")
    await db.execute(
        update(TeamMember).where(TeamMember.id == body.member_id)
        .values(credits_allocated=TeamMember.credits_allocated + body.credits)
    )
    await db.execute(update(User).where(User.id == member.user_id).values(purchased_credits=User.purchased_credits + body.credits))
    # Log the credit allocation
    member_user = (await db.execute(select(User).where(User.id == member.user_id))).scalar_one_or_none()
    member_name = member_user.name if member_user else member.email
    db.add(CreditLog(
        id=str(uuid.uuid4()), team_id=team.id, user_id=user.id,
        amount=-body.credits, log_type="allocate_member",
        description=f"Allocation de {body.credits} credits a {member_name}"
    ))
    await db.commit()
    team_row = (await db.execute(select(Team).where(Team.id == team.id))).scalar_one_or_none()
    return {"success": True, "team_credits_remaining": team_row.shared_credits if team_row else 0}



class AddCreditsRequest(BaseModel):
    credits: int = 100

@team_router.post("/credits/add")
async def add_credits_to_pool(body: AddCreditsRequest, team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Ajoute des crédits au pool partagé de l'équipe depuis le solde du propriétaire."""
    user = await get_user(creds, db)
    team = await get_user_team(user, db, team_id)
    if not team or team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Seul le proprietaire peut ajouter des credits")
    if body.credits <= 0:
        raise HTTPException(status_code=400, detail="Montant invalide")
    # Vérifier que le propriétaire a assez de crédits (total = credits + bonus + purchased)
    owner = (await db.execute(select(User).where(User.id == user.id))).scalar_one_or_none()
    total_owner = (owner.credits or 0) + (owner.bonus_credits or 0) + (owner.purchased_credits or 0)
    if total_owner < body.credits:
        raise HTTPException(status_code=400, detail=f"Credits insuffisants. Vous avez {total_owner} credits disponibles.")
    # Transférer du propriétaire au pool — déduire dans l'ordre: purchased > bonus > credits
    remaining = body.credits
    new_purchased = owner.purchased_credits or 0
    new_bonus = owner.bonus_credits or 0
    new_credits = owner.credits or 0
    # D'abord purchased_credits
    if remaining > 0 and new_purchased > 0:
        deduct = min(remaining, new_purchased)
        new_purchased -= deduct
        remaining -= deduct
    # Puis bonus_credits
    if remaining > 0 and new_bonus > 0:
        deduct = min(remaining, new_bonus)
        new_bonus -= deduct
        remaining -= deduct
    # Enfin credits
    if remaining > 0 and new_credits > 0:
        deduct = min(remaining, new_credits)
        new_credits -= deduct
        remaining -= deduct
    await db.execute(update(User).where(User.id == user.id).values(
        purchased_credits=new_purchased, bonus_credits=new_bonus, credits=new_credits
    ))
    await db.execute(update(Team).where(Team.id == team.id).values(shared_credits=Team.shared_credits + body.credits))
    # Log credit transfer
    db.add(CreditLog(
        id=str(uuid.uuid4()), team_id=team.id, user_id=user.id,
        amount=body.credits, log_type="add_to_pool",
        description=f"Transfert de {body.credits} credits vers le pool equipe"
    ))
    await db.commit()
    team_row = (await db.execute(select(Team).where(Team.id == team.id))).scalar_one_or_none()
    return {"success": True, "team_credits": team_row.shared_credits if team_row else 0}


@team_router.get("/dashboard")
async def team_dashboard(team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        user = await get_user(creds, db)
        team = await get_user_team(user, db, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Aucune équipe trouvée")
        result = await db.execute(select(TeamMember).where(TeamMember.team_id == team.id))
        members_db = result.scalars().all()
        members_stats = []
        total_used = 0
        for m in members_db:
            if m.user_id and m.status == "active":
                u_res = await db.execute(select(User).where(User.id == m.user_id))
                u = u_res.scalar_one_or_none()
                if u:
                    month_ago = utcnow() - timedelta(days=30)
                    try:
                        from models import Conversation
                        conv_res = await db.execute(
                            select(func.sum(Conversation.total_credits_used))
                            .where(Conversation.user_id == u.id, Conversation.updated_at >= month_ago)
                        )
                        used = int(conv_res.scalar() or 0)
                    except Exception:
                        used = 0
                    total_used += used
                    members_stats.append({
                        "id": m.id, "name": u.name, "email": u.email,
                        "role": m.role, "status": m.status,
                        "credits_available": (u.credits or 0) + (u.bonus_credits or 0) + (getattr(u, "purchased_credits", 0) or 0),
                        "credits_used_month": used,
                        "credits_allocated": m.credits_allocated or 0,
                        "joined_at": m.joined_at.isoformat() if m.joined_at else None
                    })
        return {
            "team": {
                "id": team.id, "name": team.name,
                "shared_credits": team.shared_credits or 0,
                "max_seats": getattr(team, "max_seats", None),
                "active_members": sum(1 for m in members_db if m.status == "active"),
                "pending_invitations": sum(1 for m in members_db if m.status == "pending"),
            },
            "stats": {"total_credits_used_month": total_used, "members_count": len(members_stats)},
            "members": members_stats,
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger("team").error(f"team/dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur tableau de bord: {str(e)}")



@team_router.get("/chatbot/sessions")
async def get_chatbot_sessions(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials = Depends(bearer)
):
    """Get chatbot sessions for a team — used by ChatbotAdminPage."""
    try:
        from models import TeamMember
        user_result = await db.execute(
            select(User).join(TeamMember, TeamMember.user_id == User.id)
            .where(TeamMember.team_id == team_id)
        )
        members = user_result.scalars().all()
        # Return basic session stats (conversations from agent messages)
        return {"sessions": [], "total": 0, "team_id": team_id}
    except Exception as e:
        return {"sessions": [], "total": 0, "error": str(e)}


@team_router.post("/chatbot")
async def team_chatbot(body: TeamChatRequest, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    import httpx
    user = await get_user(creds, db)
    team = await get_user_team(user, db)
    if not team:
        raise HTTPException(status_code=403, detail="Fonctionnalité réservée au plan Équipe")
    MAMMOTH_KEY = os.environ.get("MAMMOTH_API_KEY", "")
    if not MAMMOTH_KEY:
        raise HTTPException(status_code=503, detail="Service IA non configuré")
    system_prompt = f"""Tu es l'assistant support de l'équipe "{team.name}" sur Zayado AI. Réponds aux questions sur la plateforme de façon concise et professionnelle en français."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.mammouth.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {MAMMOTH_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 500,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": body.message}
                    ]
                }
            )
        data = resp.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "Je n'ai pas pu répondre.")
        return {"response": text, "conversation_id": body.conversation_id or str(uuid.uuid4())}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur chatbot: {str(e)}")


# ============================================================
# CHATBOT PUBLIC — Route sans authentification
# Accès via QR code / lien partagé avec teamCode
# ============================================================

class PublicChatRequest(BaseModel):
    team_code: str
    message: str
    session_id: Optional[str] = None
    user_name: str = "Anonyme"
    user_email: Optional[str] = None
    client_id: Optional[str] = None
    shared_url: Optional[str] = None
    history: list = []   # historique de conversation [{"role": "user"|"assistant", "content": "..."}]

class TeamConfigRequest(BaseModel):
    bot_name: str = "Assistant"
    bot_tone: str = "professional"
    bot_context: str = ""
    credit_limit_per_member: int = 50
    auto_recharge: bool = False
    chrome_link: bool = False
    brand_color: str = "#1E3A8A"
    welcome_message: str = ""
    end_of_credits_message: str = "Notre assistant est momentanément indisponible. Contactez-nous directement."
    alert_on_conversation: bool = True
    alert_low_credits: bool = True
    low_credit_threshold: int = 50
    privacy_policy_url: str = ""
    agent_ia_enabled: bool = False
    pre_chat_fields: list = []
    footer_text: str = "Extension AI"
    logo_url: str = ""
    behavior_escalation: bool = True
    behavior_multilang: bool = True
    behavior_24h: bool = True
    behavior_collect_email: bool = False
    team_type: str = "enterprise"
    authorized_topics: list = []
    knowledge_urls: list = []

class UpdateMemberRoleRequest(BaseModel):
    role: str = "member"

@team_router.get("/public/info/{team_code}")
async def get_public_team_info(team_code: str, db: AsyncSession = Depends(get_db)):
    """Retourne les infos publiques d'une équipe pour l'interface chatbot."""
    result = await db.execute(select(Team).where(Team.team_code == team_code))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Code équipe invalide")
    if not team.chatbot_enabled:
        raise HTTPException(status_code=403, detail="Chatbot non activé pour cette équipe")
    return {
        "team_name": team.name,
        "bot_name": team.bot_name or "Assistant",
        "bot_tone": team.bot_tone or "professional",
        "chrome_link": team.chrome_link or False,
        "credit_limit": team.credit_limit_per_member or 50,
        "brand_color": (team.settings or {}).get("brand_color", "#1E3A8A"),
        "welcome_message": (team.settings or {}).get("welcome_message", ""),
        "end_of_credits_message": (team.settings or {}).get("end_of_credits_message", ""),
        "privacy_policy_url": (team.settings or {}).get("privacy_policy_url", ""),
        "pre_chat_fields": (team.settings or {}).get("pre_chat_fields", []),
        "footer_text": (team.settings or {}).get("footer_text", "Extension AI"),
        "logo_url": (team.settings or {}).get("logo_url", ""),
        "agent_ia_enabled": (team.settings or {}).get("agent_ia_enabled", False),
        "behavior_multilang": (team.settings or {}).get("behavior_multilang", True),
    }

@team_router.post("/public/chat")
async def public_chat(body: PublicChatRequest, db: AsyncSession = Depends(get_db)):
    """Chat public accessible sans authentification via teamCode."""
    import os as _os
    import httpx as _httpx
    import json as _json
    result = await db.execute(select(Team).where(Team.team_code == body.team_code))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Code équipe invalide")
    if not team.chatbot_enabled:
        raise HTTPException(status_code=403, detail="Chatbot non activé")

    # Vérifier le pool de crédits de l'équipe
    owner_result = await db.execute(select(User).where(User.id == team.owner_id))
    owner = owner_result.scalar_one_or_none()
    use_owner_credits = False
    if (team.shared_credits or 0) <= 0:
        # Fallback: utiliser les crédits personnels du propriétaire
        owner_total = (owner.credits or 0) + (owner.bonus_credits or 0) + (owner.purchased_credits or 0) if owner else 0
        if owner_total >= 2:
            use_owner_credits = True
        else:
            custom_msg = (team.settings or {}).get("end_of_credits_message", "Notre assistant est momentanement indisponible. Contactez votre administrateur.")
            raise HTTPException(status_code=402, detail=custom_msg)

    mammoth_key = _os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(status_code=500, detail="IA non configurée")

    # Construire le system prompt personnalisé
    tone_map = {
        "professional": "professionnel et concis",
        "friendly": "bienveillant et chaleureux",
        "formal": "formel et courtois",
        "teacher": "pédagogique et explicatif",
        "conversion": "commercial et orienté conversion, suggère subtilement les produits/services de l'entreprise",
    }
    tone_desc = tone_map.get(team.bot_tone or "professional", "professionnel")
    bot_context = team.bot_context or ""
    bot_name = team.bot_name or "Assistant"
    settings = team.settings or {}

    # Agent IA: web search if enabled
    web_search_context = ""
    agent_ia_enabled = settings.get("agent_ia_enabled", False)
    if agent_ia_enabled:
        # Check if user message contains a URL to read
        import re
        urls_in_msg = re.findall(r'https?://[^\s<>"\']+', body.message)
        if urls_in_msg:
            try:
                async with _httpx.AsyncClient(timeout=15.0) as web_client:
                    for url in urls_in_msg[:2]:
                        try:
                            resp_web = await web_client.get(url, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
                            if resp_web.status_code == 200:
                                text = resp_web.text[:3000]
                                import re as _re
                                text = _re.sub(r'<script[^>]*>.*?</script>', '', text, flags=_re.DOTALL)
                                text = _re.sub(r'<style[^>]*>.*?</style>', '', text, flags=_re.DOTALL)
                                text = _re.sub(r'<[^>]+>', ' ', text)
                                text = _re.sub(r'\s+', ' ', text).strip()[:2000]
                                web_search_context += f"\n\nCONTENU DU SITE {url}:\n{text}\n"
                        except Exception:
                            web_search_context += f"\n\nSite {url} : impossible de lire le contenu.\n"
            except Exception:
                pass

    # Check if user shared a URL via the URL button
    if body.shared_url:
        try:
            async with _httpx.AsyncClient(timeout=15.0) as web_client:
                resp_web = await web_client.get(body.shared_url, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
                if resp_web.status_code == 200:
                    import re as _re
                    text = resp_web.text[:3000]
                    text = _re.sub(r'<script[^>]*>.*?</script>', '', text, flags=_re.DOTALL)
                    text = _re.sub(r'<style[^>]*>.*?</style>', '', text, flags=_re.DOTALL)
                    text = _re.sub(r'<[^>]+>', ' ', text)
                    text = _re.sub(r'\s+', ' ', text).strip()[:2000]
                    web_search_context += f"\n\nCONTENU DU LIEN PARTAGÉ ({body.shared_url}):\n{text}\n"
        except Exception:
            web_search_context += f"\n\nLien partagé ({body.shared_url}) : impossible de lire le contenu.\n"

    # Behavior: multilang
    lang_instruction = ""
    if settings.get("behavior_multilang", True):
        lang_instruction = "Détecte la langue de l'utilisateur et réponds dans cette langue."
    else:
        lang_instruction = "Réponds toujours en français."

    # Construire le contexte client si fourni
    client_context = ""
    if body.user_email or body.client_id:
        client_context = f"\nCLIENT IDENTIFIÉ : Nom={body.user_name}"
        if body.user_email:
            client_context += f", Email={body.user_email}"
        if body.client_id:
            client_context += f", Référence/Dossier={body.client_id}"
        client_context += "\nIMPORTANT: Répondez UNIQUEMENT avec les informations concernant CE client. Ne divulguez jamais les données d'autres clients."

    # RAG : trouver le dossier du client par son code
    client_folders = (team.settings or {}).get("client_folders", [])
    knowledge_context = ""
    if body.client_id and client_folders:
        # Chercher le dossier correspondant au code client
        matched = next((f for f in client_folders if f.get("code","").upper() == str(body.client_id).upper()), None)
        if matched:
            knowledge_context = f"""
DOSSIER CLIENT IDENTIFIÉ :
Code : {matched.get('code')}
Client : {matched.get('label', matched.get('code'))}
Accès dossier : {matched.get('url')}

INSTRUCTION : Ce client a accès à son dossier via le lien ci-dessus. 
Si la question concerne ses documents, fournissez le lien et précisez qu'il peut y accéder directement.
Ne divulguez PAS les dossiers d'autres clients."""
        else:
            knowledge_context = f"\nCode client '{body.client_id}' non trouvé dans notre système. Demandez au client de vérifier son code."
    elif client_folders:
        # Client non identifié mais des dossiers existent
        knowledge_context = "\nPour accéder à votre dossier, veuillez renseigner votre code client lors de la prochaine session."

    # RAG : base de connaissances (fichiers uploadés)
    kb_context = ""
    try:
        from models import KnowledgeFile
        kb_result = await db.execute(
            select(KnowledgeFile).where(KnowledgeFile.team_id == team.id, KnowledgeFile.status == "active")
        )
        kb_files = kb_result.scalars().all()
        if kb_files:
            # Simple keyword relevance: search user message terms in extracted text
            user_terms = set(body.message.lower().split())
            relevant_chunks = []
            for kf in kb_files:
                if not kf.extracted_text:
                    continue
                text_lower = kf.extracted_text.lower()
                score = sum(1 for t in user_terms if len(t) > 3 and t in text_lower)
                if score > 0:
                    # Take first 3000 chars of relevant files
                    relevant_chunks.append((score, kf.filename, kf.extracted_text[:3000]))
            relevant_chunks.sort(key=lambda x: -x[0])
            if relevant_chunks:
                kb_parts = []
                total = 0
                for _, fname, chunk in relevant_chunks[:3]:  # Max 3 files
                    if total + len(chunk) > 6000:
                        break
                    kb_parts.append(f"[Document: {fname}]\n{chunk}")
                    total += len(chunk)
                kb_context = "\n\nBASE DE CONNAISSANCES (documents de reference):\n" + "\n---\n".join(kb_parts)
                kb_context += "\n\nINSTRUCTION: Utilise ces documents pour enrichir tes reponses. Cite les sources si pertinent."
    except Exception as e:
        logger.warning(f"Knowledge base lookup error: {e}")

    system_prompt = f"""Tu es {bot_name}, l'assistant IA de l'équipe '{team.name}'.
Ton style de communication est : {tone_desc}.
{f"Contexte et informations importantes : {bot_context}" if bot_context else ""}
{knowledge_context}
{kb_context}
{client_context}
{web_search_context}
{lang_instruction}
Réponds de manière utile et adaptée."""

    # Construire l'historique de conversation pour le contexte
    chat_messages = [{"role": "system", "content": system_prompt}]
    # Ajouter l'historique (max 10 derniers échanges pour éviter les tokens excessifs)
    for h in (body.history or [])[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            chat_messages.append({"role": h["role"], "content": str(h["content"])[:500]})
    chat_messages.append({"role": "user", "content": body.message})

    try:
        async with _httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.mammouth.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "messages": chat_messages,
                    "max_tokens": 1024,
                    "temperature": 0.7
                }
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Erreur IA")
        reply = resp.json()["choices"][0]["message"]["content"]
    except _httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout IA")

    # Déduire 2 crédits
    cost = 2
    if use_owner_credits:
        o = owner
        rem = cost
        new_p = o.purchased_credits or 0
        new_b = o.bonus_credits or 0
        new_c = o.credits or 0
        if rem > 0 and new_p > 0:
            d = min(rem, new_p); new_p -= d; rem -= d
        if rem > 0 and new_b > 0:
            d = min(rem, new_b); new_b -= d; rem -= d
        if rem > 0 and new_c > 0:
            d = min(rem, new_c); new_c -= d; rem -= d
        await db.execute(update(User).where(User.id == o.id).values(
            purchased_credits=new_p, bonus_credits=new_b, credits=new_c
        ))
        db.add(CreditLog(
            id=str(uuid.uuid4()), team_id=team.id, user_id=team.owner_id,
            amount=-cost, log_type="owner_deduction",
            description=f"Chat public: -{cost} credits (proprietaire)"
        ))
    else:
        await db.execute(
            update(Team).where(Team.id == team.id).values(
                shared_credits=Team.shared_credits - cost
            )
        )
        db.add(CreditLog(
            id=str(uuid.uuid4()), team_id=team.id, user_id=None,
            amount=-cost, log_type="chat_deduction",
            description=f"Chat public: -{cost} credits (pool equipe)"
        ))

    # Persist conversation in team settings for the dashboard
    try:
        current = await db.execute(select(Team).where(Team.id == team.id))
        current_team = current.scalar_one_or_none()
        settings = dict(current_team.settings or {})
        public_conversations = settings.get("public_conversations", [])

        # Find existing session or create new
        existing = next((c for c in public_conversations if c.get("session_id") == (body.session_id or "")), None)
        now_iso = utcnow().isoformat()
        if existing:
            existing["message_count"] = existing.get("message_count", 0) + 2
            existing["updated_at"] = now_iso
            existing["messages"] = existing.get("messages", [])
            existing["messages"].append({"role": "user", "content": body.message})
            existing["messages"].append({"role": "assistant", "content": reply})
            # Keep only last 50 messages per conversation
            existing["messages"] = existing["messages"][-50:]
        else:
            public_conversations.append({
                "session_id": body.session_id or str(uuid.uuid4())[:8],
                "user_name": body.user_name,
                "user_email": body.user_email or "",
                "title": body.message[:60] if body.message else "Conversation",
                "message_count": 2,
                "messages": [
                    {"role": "user", "content": body.message},
                    {"role": "assistant", "content": reply}
                ],
                "created_at": now_iso,
                "updated_at": now_iso,
                "shared_url": body.shared_url or "",
            })

        # Keep only last 100 conversations
        settings["public_conversations"] = public_conversations[-100:]
        await db.execute(update(Team).where(Team.id == team.id).values(settings=settings))
    except Exception:
        pass

    await db.commit()

    return {
        "reply": reply,
        "bot_name": bot_name,
        "credits_remaining": max(0, (team.shared_credits or 0) - cost),
        "session_id": body.session_id or str(uuid.uuid4())[:8]
    }


class ShareSupportRequest(BaseModel):
    team_code: str
    session_id: str
    visible: bool = True

@team_router.post("/public/share-support")
async def toggle_support_visibility(body: ShareSupportRequest, db: AsyncSession = Depends(get_db)):
    """Toggle conversation visibility for support/team members from public chat."""
    result = await db.execute(select(Team).where(Team.team_code == body.team_code))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Equipe non trouvee")
    
    # Store the visibility preference in the team settings under public_visible_sessions
    current = await db.execute(select(Team).where(Team.id == team.id))
    current_team = current.scalar_one_or_none()
    settings = dict(current_team.settings or {})
    visible_sessions = settings.get("public_visible_sessions", [])
    
    if body.visible and body.session_id not in visible_sessions:
        visible_sessions.append(body.session_id)
    elif not body.visible and body.session_id in visible_sessions:
        visible_sessions.remove(body.session_id)
    
    settings["public_visible_sessions"] = visible_sessions
    await db.execute(update(Team).where(Team.id == team.id).values(settings=settings))
    await db.commit()
    
    return {"status": "ok", "visible": body.visible}

@team_router.post("/config")
async def update_team_chatbot_config(body: TeamConfigRequest, team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Met à jour la configuration du chatbot de l'équipe."""
    user = await get_user(creds, db)
    team = await get_user_team(user, db, team_id)
    if not team or team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Mettre à jour les settings avec brand_color et messages
    current = await db.execute(select(Team).where(Team.id == team.id))
    current_team = current.scalar_one_or_none()
    new_settings = dict(current_team.settings or {})
    new_settings["brand_color"] = body.brand_color
    new_settings["welcome_message"] = body.welcome_message
    new_settings["end_of_credits_message"] = body.end_of_credits_message
    new_settings["privacy_policy_url"] = body.privacy_policy_url
    new_settings["agent_ia_enabled"] = body.agent_ia_enabled
    new_settings["pre_chat_fields"] = body.pre_chat_fields
    new_settings["footer_text"] = body.footer_text
    new_settings["logo_url"] = body.logo_url
    new_settings["behavior_escalation"] = body.behavior_escalation
    new_settings["behavior_multilang"] = body.behavior_multilang
    new_settings["behavior_24h"] = body.behavior_24h
    new_settings["behavior_collect_email"] = body.behavior_collect_email
    new_settings["team_type"] = body.team_type
    new_settings["authorized_topics"] = body.authorized_topics
    new_settings["knowledge_urls"] = body.knowledge_urls
    # Alert settings
    if hasattr(body, 'alert_on_conversation') and body.alert_on_conversation is not None:
        new_settings["alert_on_conversation"] = body.alert_on_conversation
    if hasattr(body, 'alert_low_credits') and body.alert_low_credits is not None:
        new_settings["alert_low_credits"] = body.alert_low_credits
    if hasattr(body, 'low_credit_threshold') and body.low_credit_threshold is not None:
        new_settings["low_credit_threshold"] = body.low_credit_threshold

    await db.execute(
        update(Team).where(Team.id == team.id).values(
            bot_name=body.bot_name,
            bot_tone=body.bot_tone,
            bot_context=body.bot_context,
            credit_limit_per_member=body.credit_limit_per_member,
            auto_recharge=body.auto_recharge,
            chrome_link=body.chrome_link,
            chatbot_enabled=True,
            settings=new_settings
        )
    )
    await db.commit()
    return {"status": "ok", "message": "Configuration sauvegardée"}


@team_router.put("/config")
async def update_team_config_simple(body: dict, team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Simplified config update for ChatbotAdminPage — accepts flat dict."""
    user = await get_user(creds, db)
    team = await get_user_team(user, db, team_id)
    if not team or team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Acces refuse")
    values = {}
    if "bot_name" in body: values["bot_name"] = body["bot_name"]
    if "bot_tone" in body: values["bot_tone"] = body["bot_tone"]
    if "welcome_message" in body: values["welcome_message"] = body["welcome_message"]
    if "primary_color" in body: values["primary_color"] = body["primary_color"]
    if "accent_color" in body: values["accent_color"] = body["accent_color"]
    if "logo_url" in body: values["logo_url"] = body["logo_url"]
    if "footer_text" in body: values["footer_text"] = body["footer_text"]
    if values:
        await db.execute(update(Team).where(Team.id == team.id).values(**values))
        await db.commit()
    return {"status": "ok"}


@team_router.patch("/members/{member_id}/role")
async def update_member_role(member_id: str, body: UpdateMemberRoleRequest, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Change le rôle d'un membre de l'équipe (admin/member)."""
    user = await get_user(creds, db)
    team = await get_user_team(user, db)
    if not team or team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Seul le propriétaire peut changer les rôles")
    if body.role not in ("admin", "member"):
        raise HTTPException(status_code=400, detail="Rôle invalide (admin ou member)")
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team.id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    if member.role == "owner":
        raise HTTPException(status_code=400, detail="Impossible de changer le rôle du propriétaire")
    member.role = body.role
    await db.commit()
    return {"success": True, "new_role": body.role}


@team_router.post("/invite/{member_id}/resend")
async def resend_invitation(member_id: str, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Renvoie l'email d'invitation à un membre en attente."""
    user = await get_user(creds, db)
    team = await get_user_team(user, db)
    if not team or team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Seul le propriétaire peut relancer les invitations")
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team.id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    if member.status != "pending":
        raise HTTPException(status_code=400, detail="Ce membre a déjà rejoint l'équipe")
    if not member.invite_token:
        member.invite_token = secrets.token_urlsafe(32)
        await db.commit()
    invite_url = f"https://app.zayado.net/join-team?token={member.invite_token}"
    try:
        from utils import send_brevo_email
        invite_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;">
          <h2 style="color:#1E3A8A;">Rappel : Vous êtes invité(e) à rejoindre l'équipe !</h2>
          <p>Bonjour,</p>
          <p><strong>{user.name or user.email}</strong> vous invite à rejoindre l'équipe <strong>"{team.name}"</strong> sur ZAYADO.</p>
          <p style="margin:24px 0;">
            <a href="{invite_url}" style="background:#1E3A8A;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:bold;display:inline-block;">
              Accepter l'invitation
            </a>
          </p>
          <p style="color:#6b7280;font-size:12px;">Ce lien expire dans 7 jours.</p>
        </div>"""
        import asyncio as _aio
        _aio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(
            to_email=member.email, to_name=member.email,
            subject=f"[ZAYADO] Rappel — Invitation à rejoindre « {team.name} »",
            html_content=invite_html
        ))
        return {"success": True, "message": f"Invitation renvoyée à {member.email}", "invite_url": invite_url}
    except Exception:
        return {"success": True, "message": "Relance effectuée (email non envoyé)", "invite_url": invite_url}


@team_router.get("/conversations")
async def get_team_conversations(team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Retourne uniquement les conversations publiques du chatbot (pas les conversations privées des membres)."""
    user = await get_user(creds, db)
    team = await get_user_team(user, db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Aucune équipe trouvée")

    try:
        # Only return sessions explicitly shared via the public chatbot
        settings = team.settings or {}
        visible_sessions = settings.get("public_visible_sessions", [])
        public_conversations = settings.get("public_conversations", [])

        conversations = []
        for conv in public_conversations:
            conversations.append({
                "id": conv.get("session_id", ""),
                "title": conv.get("title", "Conversation chatbot"),
                "mode": "chatbot",
                "user_email": conv.get("user_email", ""),
                "user_name": conv.get("user_name", "Anonyme"),
                "message_count": conv.get("message_count", 0),
                "messages": conv.get("messages", []),
                "updated_at": conv.get("updated_at"),
                "created_at": conv.get("created_at"),
                "visible": conv.get("session_id", "") in visible_sessions,
            })
        return conversations
    except Exception as e:
        import logging
        logging.getLogger("team").error(f"team/conversations error: {e}")
        return []


@team_router.get("/credits/history")
async def get_credit_history(team_id: str = None, db: AsyncSession = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Retourne l'historique des mouvements de crédits de l'équipe."""
    user = await get_user(creds, db)
    team = await get_user_team(user, db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Aucune equipe trouvee")
    result = await db.execute(
        select(CreditLog).where(CreditLog.team_id == team.id).order_by(CreditLog.created_at.desc()).limit(50)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "amount": l.amount,
            "type": l.log_type,
            "description": l.description,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
