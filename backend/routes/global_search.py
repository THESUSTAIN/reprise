"""
Recherche globale (Cmd+K) — corrige un bug réel : la recherche du header
ne filtrait qu'une liste statique de pages de menu, jamais les vraies
données de l'utilisateur (chercher le nom exact d'un projet existant ne
renvoyait jamais rien). Interroge les vraies sources : la table Project
(SQLAlchemy), et les tâches/prospects (pattern JSON déjà éprouvé).
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User, Project
from routes.missing_apis import _list_rows

router = APIRouter(prefix="/api/search", tags=["Recherche globale"])


@router.get("")
async def global_search(q: str = "", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = (q or "").strip().lower()
    if not query:
        return {"results": []}

    results = []

    proj_rows = (await db.execute(select(Project).where(Project.user_id == user.id))).scalars().all()
    for p in proj_rows:
        if query in (p.name or "").lower():
            results.append({"label": p.name, "type": "Projet", "path": "/travail", "id": p.id})

    tasks = await _list_rows(db, "user_tasks", user.id)
    for t in tasks:
        label = t.get("label") or ""
        if query in label.lower():
            results.append({"label": label, "type": "Tâche", "path": "/travail", "id": t.get("id")})

    leads = await _list_rows(db, "user_leads", user.id)
    for lead in leads:
        name = lead.get("name") or ""
        company = lead.get("company") or ""
        if query in name.lower() or query in (company or "").lower():
            label = f"{name} — {company}" if company else name
            results.append({"label": label, "type": "Prospect", "path": "/croissance", "id": lead.get("id")})

    return {"results": results[:20]}
