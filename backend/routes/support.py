"""
Support Ticket Routes
User ticket submission and admin management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from database import get_db
from deps import get_current_user
from models import User, SupportTicket

support_router = APIRouter(prefix="/support", tags=["Support"])


class TicketCreate(BaseModel):
    subject: str
    message: str
    category: str = "general"
    priority: str = "normal"


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    admin_notes: Optional[str] = None
    admin_response: Optional[str] = None


class TicketResponse(BaseModel):
    id: str
    user_id: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    subject: str
    message: str
    category: str
    status: str
    priority: str
    admin_notes: Optional[str] = None
    admin_response: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    created_at: str
    updated_at: str


# ========== USER ENDPOINTS ==========

@support_router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    data: TicketCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new support ticket."""
    try:
        ticket = SupportTicket(
            user_id=user.id,
            subject=data.subject,
            message=data.message,
            category=data.category,
            priority=data.priority
        )
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur DB: {str(e)}. Verifiez que la table support_tickets existe (voir migration_zayado.sql).")
    
    return TicketResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        user_email=user.email,
        user_name=user.name,
        subject=ticket.subject,
        message=ticket.message,
        category=ticket.category,
        status=ticket.status,
        priority=ticket.priority,
        admin_notes=ticket.admin_notes,
        admin_response=ticket.admin_response,
        resolved_by=ticket.resolved_by,
        resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        created_at=ticket.created_at.isoformat(),
        updated_at=ticket.updated_at.isoformat()
    )


@support_router.get("/tickets/my", response_model=List[TicketResponse])
async def get_my_tickets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's tickets."""
    try:
        result = await db.execute(
            select(SupportTicket)
            .where(SupportTicket.user_id == user.id)
            .order_by(SupportTicket.created_at.desc())
        )
        tickets = result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur DB: {str(e)}. Verifiez que la table support_tickets existe (voir migration_zayado.sql).")
    
    return [
        TicketResponse(
            id=t.id,
            user_id=t.user_id,
            subject=t.subject,
            message=t.message,
            category=t.category,
            status=t.status,
            priority=t.priority,
            admin_response=t.admin_response,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat(),
            resolved_at=t.resolved_at.isoformat() if t.resolved_at else None,
            resolved_by=t.resolved_by
        )
        for t in tickets
    ]


# ========== ADMIN ENDPOINTS ==========

@support_router.get("/admin/tickets", response_model=List[TicketResponse])
async def get_all_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all support tickets (admin only)."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = select(SupportTicket, User).join(User, SupportTicket.user_id == User.id)
    
    if status:
        query = query.where(SupportTicket.status == status)
    if category:
        query = query.where(SupportTicket.category == category)
    if priority:
        query = query.where(SupportTicket.priority == priority)
    
    # Use CASE WHEN for SQLite-compatible priority ordering
    # Priority order: urgent=1 > high=2 > normal=3 > low=4
    from sqlalchemy import case
    priority_order = case(
        (SupportTicket.priority == 'urgent', 1),
        (SupportTicket.priority == 'high', 2),
        (SupportTicket.priority == 'normal', 3),
        (SupportTicket.priority == 'low', 4),
        else_=5
    )
    query = query.order_by(priority_order, SupportTicket.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        TicketResponse(
            id=ticket.id,
            user_id=ticket.user_id,
            user_email=u.email,
            user_name=u.name,
            subject=ticket.subject,
            message=ticket.message,
            category=ticket.category,
            status=ticket.status,
            priority=ticket.priority,
            admin_notes=ticket.admin_notes,
            admin_response=ticket.admin_response,
            resolved_by=ticket.resolved_by,
            resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            created_at=ticket.created_at.isoformat(),
            updated_at=ticket.updated_at.isoformat()
        )
        for ticket, u in rows
    ]


@support_router.get("/admin/tickets/stats")
async def get_ticket_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get ticket statistics (admin only)."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Count by status
    result = await db.execute(
        select(SupportTicket.status, func.count(SupportTicket.id))
        .group_by(SupportTicket.status)
    )
    status_counts = {row[0]: row[1] for row in result.all()}
    
    # Count by category
    result = await db.execute(
        select(SupportTicket.category, func.count(SupportTicket.id))
        .group_by(SupportTicket.category)
    )
    category_counts = {row[0]: row[1] for row in result.all()}
    
    # Count by priority
    result = await db.execute(
        select(SupportTicket.priority, func.count(SupportTicket.id))
        .group_by(SupportTicket.priority)
    )
    priority_counts = {row[0]: row[1] for row in result.all()}
    
    # Total count
    result = await db.execute(select(func.count(SupportTicket.id)))
    total = result.scalar() or 0
    
    return {
        "total": total,
        "by_status": status_counts,
        "by_category": category_counts,
        "by_priority": priority_counts
    }


@support_router.put("/admin/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    data: TicketUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a support ticket (admin only)."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(
        select(SupportTicket, User)
        .join(User, SupportTicket.user_id == User.id)
        .where(SupportTicket.id == ticket_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket, ticket_user = row
    
    if data.status:
        ticket.status = data.status
        if data.status in ["resolved", "closed"]:
            ticket.resolved_by = user.id
            ticket.resolved_at = datetime.now(timezone.utc)
    if data.priority:
        ticket.priority = data.priority
    if data.admin_notes is not None:
        ticket.admin_notes = data.admin_notes
    if data.admin_response is not None:
        ticket.admin_response = data.admin_response
    
    await db.commit()
    await db.refresh(ticket)
    
    return TicketResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        user_email=ticket_user.email,
        user_name=ticket_user.name,
        subject=ticket.subject,
        message=ticket.message,
        category=ticket.category,
        status=ticket.status,
        priority=ticket.priority,
        admin_notes=ticket.admin_notes,
        admin_response=ticket.admin_response,
        resolved_by=ticket.resolved_by,
        resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        created_at=ticket.created_at.isoformat(),
        updated_at=ticket.updated_at.isoformat()
    )


@support_router.delete("/admin/tickets/{ticket_id}")
async def delete_ticket(
    ticket_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a support ticket (admin only)."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    await db.delete(ticket)
    await db.commit()
    
    return {"status": "deleted", "id": ticket_id}
