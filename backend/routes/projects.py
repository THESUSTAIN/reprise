"""Project routes for Extension IA API."""
import logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime, timezone

from database import get_db
from models import User, Project
from deps import get_current_user
from schemas import ProjectCreateSchema, ProjectResponse
from utils import send_brevo_email

projects_router = APIRouter(prefix="/projects", tags=["Projects"])

@projects_router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreateSchema, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_project = Project(user_id=user.id, name=project.name, hourly_rate=project.hourly_rate, color=project.color)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return ProjectResponse(id=new_project.id, name=new_project.name, hourly_rate=new_project.hourly_rate, color=new_project.color, total_time_seconds=0, total_cost=0, is_running=False, timer_started_at=None, created_at=new_project.created_at)

@projects_router.get("")
async def get_projects(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Project).where(Project.user_id == user.id))
        projects = result.scalars().all()
        response = []
        for p in projects:
            total_seconds = getattr(p, 'total_time_seconds', 0) or 0
            if getattr(p, 'is_running', False) and getattr(p, 'timer_started_at', None):
                ts = p.timer_started_at
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                elapsed = (datetime.now(timezone.utc) - ts).total_seconds()
                total_seconds += int(elapsed)
            hourly = getattr(p, 'hourly_rate', 0) or 0
            total_cost = (total_seconds / 3600) * hourly
            response.append(ProjectResponse(id=p.id, name=p.name, hourly_rate=hourly, color=getattr(p, 'color', '#1E3A8A') or '#1E3A8A', total_time_seconds=total_seconds, total_cost=round(total_cost, 2), is_running=getattr(p, 'is_running', False) or False, timer_started_at=getattr(p, 'timer_started_at', None), created_at=p.created_at))
        return response
    except Exception as e:
        from utils import logger
        logger.error(f"Error fetching projects: {e}")
        return []

@projects_router.post("/{project_id}/start")
async def start_timer(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.is_running:
        raise HTTPException(status_code=400, detail="Timer already running")
    await db.execute(update(Project).where(Project.id == project_id).values(is_running=True, timer_started_at=datetime.now(timezone.utc)))
    await db.commit()
    return {"status": "started"}

@projects_router.post("/{project_id}/stop")
async def stop_timer(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.is_running:
        raise HTTPException(status_code=400, detail="Timer not running")
    timer_started = project.timer_started_at
    if timer_started.tzinfo is None:
        timer_started = timer_started.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - timer_started).total_seconds()
    new_total = project.total_time_seconds + int(elapsed)
    await db.execute(update(Project).where(Project.id == project_id).values(is_running=False, timer_started_at=None, total_time_seconds=new_total))
    await db.commit()
    return {"status": "stopped", "elapsed_seconds": int(elapsed), "total_seconds": new_total}


@projects_router.put("/{project_id}")
async def update_project(project_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Modifier un projet (nom, taux horaire, couleur)."""
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Projet introuvable")
    if "name" in data and data["name"].strip():
        project.name = data["name"].strip()
    if "hourly_rate" in data:
        project.hourly_rate = float(data["hourly_rate"] or 0)
    if "color" in data:
        project.color = data["color"]
    await db.commit()
    await db.refresh(project)
    return {"id": project.id, "name": project.name, "hourly_rate": project.hourly_rate, "color": project.color, "ok": True}

@projects_router.delete("/{project_id}")
async def delete_project(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(delete(Project).where(Project.id == project_id, Project.user_id == user.id))
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}

@projects_router.get("/{project_id}/export")
async def export_project(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    total_seconds = project.total_time_seconds
    if project.is_running and project.timer_started_at:
        timer_started = project.timer_started_at
        if timer_started.tzinfo is None:
            timer_started = timer_started.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - timer_started).total_seconds()
        total_seconds += int(elapsed)
    hours = total_seconds / 3600
    total_cost = round(hours * project.hourly_rate, 2)
    return {"project_name": project.name, "hourly_rate": project.hourly_rate, "total_hours": round(hours, 2), "total_cost": total_cost, "currency": "EUR", "generated_at": datetime.now(timezone.utc).isoformat(), "user_name": user.name, "user_email": user.email}

@projects_router.post("/{project_id}/send-invoice")
async def send_project_invoice(project_id: str, data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    total_seconds = project.total_time_seconds
    hours = total_seconds / 3600
    total_cost = round(hours * project.hourly_rate, 2)
    recipient = data.get("email", user.email)
    html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="text-align:center;margin-bottom:20px;"><h1 style="color:#1E3A8A;margin:0;">Decompte Projet</h1><p style="color:#666;">Genere par Extension IA</p></div>
        <div style="background:#F5F5F0;padding:20px;border-radius:12px;margin-bottom:20px;">
            <h2 style="color:#1E3A8A;margin-top:0;">{project.name}</h2>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:8px 0;color:#666;">Taux horaire</td><td style="text-align:right;font-weight:bold;">{project.hourly_rate:.2f} EUR/h</td></tr>
                <tr><td style="padding:8px 0;color:#666;">Heures totales</td><td style="text-align:right;font-weight:bold;">{hours:.2f}h</td></tr>
                <tr style="border-top:2px solid #ddd;"><td style="padding:12px 0;color:#1E3A8A;font-weight:bold;font-size:18px;">Total</td><td style="text-align:right;font-weight:bold;font-size:18px;color:#DC2626;">{total_cost:.2f} EUR</td></tr>
            </table>
        </div>
        <p style="color:#999;font-size:12px;text-align:center;">Date: {datetime.now(timezone.utc).strftime('%d/%m/%Y')} | {user.name} | {user.email}</p>
    </div>"""
    import asyncio as _aio
    _r = recipient
    _n = user.name
    _s = f"Decompte Projet - {project.name}"
    _h = html
    _aio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(_r, _n, _s, _h))
    return {"status": "sent", "email": recipient}
