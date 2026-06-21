"""Custom Prompts CRUD — user + admin routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from deps import get_current_user, get_db
from models import User, CustomPrompt

prompts_router = APIRouter(tags=["prompts"])


class PromptCreate(BaseModel):
    title: str
    prompt: str
    category: str = "general"
    icon: str = "sparkles"
    color: str = "bg-blue-50 text-blue-600"
    action: str = "insert"  # insert or auto_send


class PromptUpdate(BaseModel):
    title: Optional[str] = None
    prompt: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    action: Optional[str] = None


class AdminPromptCreate(PromptCreate):
    plan_required: str = "free"
    sort_order: int = 0


def serialize_prompt(p):
    return {
        "id": p.id, "title": p.title, "prompt": p.prompt,
        "category": p.category, "icon": p.icon, "color": p.color,
        "action": p.action, "plan_required": p.plan_required,
        "is_system": p.is_system, "sort_order": p.sort_order,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


# ────── User Endpoints ──────

@prompts_router.get("")
async def get_prompts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get all prompts: system prompts matching user plan + user's own prompts"""
    plan_order = {"free": 0, "starter": 1, "pro": 2, "business": 3, "team": 4, "enterprise": 5}
    user_plan_level = plan_order.get(user.plan, 0)

    # System prompts where plan_required <= user plan
    result = await db.execute(
        select(CustomPrompt).where(
            CustomPrompt.is_system == True,
        ).order_by(CustomPrompt.sort_order, CustomPrompt.created_at)
    )
    system_prompts = [p for p in result.scalars().all()
                      if plan_order.get(p.plan_required, 0) <= user_plan_level]

    # User's own custom prompts
    result2 = await db.execute(
        select(CustomPrompt).where(
            CustomPrompt.user_id == user.id, CustomPrompt.is_system == False
        ).order_by(CustomPrompt.sort_order, CustomPrompt.created_at)
    )
    user_prompts = result2.scalars().all()

    return {
        "system_prompts": [serialize_prompt(p) for p in system_prompts],
        "user_prompts": [serialize_prompt(p) for p in user_prompts],
    }


@prompts_router.post("")
async def create_prompt(data: PromptCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    p = CustomPrompt(
        title=data.title, prompt=data.prompt, category=data.category,
        icon=data.icon, color=data.color, action=data.action,
        user_id=user.id, is_system=False, plan_required="free",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return serialize_prompt(p)


@prompts_router.put("/{prompt_id}")
async def update_prompt(prompt_id: str, data: PromptUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomPrompt).where(CustomPrompt.id == prompt_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Prompt introuvable")
    # Allow user to edit own prompts, admin to edit any
    if p.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "Non autorise")
    updates = {k: v for k, v in data.dict().items() if v is not None}
    if updates:
        await db.execute(update(CustomPrompt).where(CustomPrompt.id == prompt_id).values(**updates))
        await db.commit()
    result2 = await db.execute(select(CustomPrompt).where(CustomPrompt.id == prompt_id))
    return serialize_prompt(result2.scalar_one())


@prompts_router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomPrompt).where(CustomPrompt.id == prompt_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Prompt introuvable")
    if p.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "Non autorise")
    await db.execute(delete(CustomPrompt).where(CustomPrompt.id == prompt_id))
    await db.commit()
    return {"status": "deleted"}


# ────── Admin Endpoints ──────

@prompts_router.get("/admin/all")
async def admin_get_all_prompts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    result = await db.execute(select(CustomPrompt).where(CustomPrompt.is_system == True).order_by(CustomPrompt.sort_order))
    return [serialize_prompt(p) for p in result.scalars().all()]


@prompts_router.post("/admin")
async def admin_create_prompt(data: AdminPromptCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    p = CustomPrompt(
        title=data.title, prompt=data.prompt, category=data.category,
        icon=data.icon, color=data.color, action=data.action,
        plan_required=data.plan_required, sort_order=data.sort_order,
        is_system=True, user_id=None,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return serialize_prompt(p)


@prompts_router.put("/admin/{prompt_id}")
async def admin_update_prompt(prompt_id: str, data: AdminPromptCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    result = await db.execute(select(CustomPrompt).where(CustomPrompt.id == prompt_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Prompt introuvable")
    updates = {k: v for k, v in data.dict().items() if v is not None}
    if updates:
        await db.execute(update(CustomPrompt).where(CustomPrompt.id == prompt_id).values(**updates))
        await db.commit()
    result2 = await db.execute(select(CustomPrompt).where(CustomPrompt.id == prompt_id))
    return serialize_prompt(result2.scalar_one())


@prompts_router.delete("/admin/{prompt_id}")
async def admin_delete_prompt(prompt_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    await db.execute(delete(CustomPrompt).where(CustomPrompt.id == prompt_id))
    await db.commit()
    return {"status": "deleted"}
