"""
Vector Memory Routes — Mémoire vectorielle pour l'Agent IA
Provides semantic storage and retrieval using OpenAI text-embedding-3-small via Mammoth API.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import os, json, logging, math, httpx

from database import get_db
from models import User, VectorMemory
from deps import get_current_user

logger = logging.getLogger(__name__)
memory_router = APIRouter(tags=["Memory"])

MAMMOTH_EMBED_URL = "https://api.mammouth.ai/v1/embeddings"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536


# ── Schemas ─────────────────────────────────────────────────────
class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=3, max_length=5000)
    category: str = Field(default="general")
    source: str = Field(default="manual")
    source_id: Optional[str] = None


class MemoryResponse(BaseModel):
    id: str
    content: str
    category: str
    source: str
    source_id: Optional[str]
    score: Optional[float] = None
    created_at: str


class MemorySearchResponse(BaseModel):
    results: List[MemoryResponse]
    query: str
    total: int


# ── Embedding Helper ────────────────────────────────────────────
async def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector using Mammoth API (OpenAI-compatible)."""
    mammoth_key = os.environ.get('MAMMOTH_API_KEY', '')
    if not mammoth_key:
        raise HTTPException(status_code=500, detail="Mammoth API key not configured")

    truncated = text[:8000]  # Limit input to ~2000 tokens
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            MAMMOTH_EMBED_URL,
            headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
            json={"model": EMBED_MODEL, "input": truncated}
        )
        if resp.status_code != 200:
            logger.error(f"Embedding API error {resp.status_code}: {resp.text[:300]}")
            raise HTTPException(status_code=502, detail="Embedding service unavailable")
        data = resp.json()
        return data["data"][0]["embedding"]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Routes ──────────────────────────────────────────────────────

@memory_router.post("/store", response_model=MemoryResponse)
async def store_memory(
    body: MemoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Store a new memory with its vector embedding."""
    embedding = await generate_embedding(body.content)

    mem = VectorMemory(
        user_id=user.id,
        content=body.content,
        embedding=json.dumps(embedding),
        source=body.source,
        source_id=body.source_id,
        category=body.category,
    )
    db.add(mem)
    await db.commit()
    await db.refresh(mem)

    logger.info(f"Memory stored: user={user.id}, id={mem.id}, cat={body.category}")
    return MemoryResponse(
        id=mem.id, content=mem.content, category=mem.category,
        source=mem.source, source_id=mem.source_id,
        created_at=mem.created_at.isoformat()
    )


@memory_router.get("/search", response_model=MemorySearchResponse)
async def search_memory(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=5, ge=1, le=20),
    category: Optional[str] = Query(default=None),
    threshold: float = Query(default=0.3, ge=0.0, le=1.0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Semantic search across user's vector memories."""
    query_embedding = await generate_embedding(q)

    # Load all user memories
    stmt = select(VectorMemory).where(VectorMemory.user_id == user.id)
    if category:
        stmt = stmt.where(VectorMemory.category == category)
    result = await db.execute(stmt)
    memories = result.scalars().all()

    if not memories:
        return MemorySearchResponse(results=[], query=q, total=0)

    # Compute similarities
    scored = []
    for mem in memories:
        try:
            mem_emb = json.loads(mem.embedding)
            sim = cosine_similarity(query_embedding, mem_emb)
            if sim >= threshold:
                scored.append((mem, sim))
        except (json.JSONDecodeError, TypeError):
            continue

    # Sort by similarity descending
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]

    results = [
        MemoryResponse(
            id=m.id, content=m.content, category=m.category,
            source=m.source, source_id=m.source_id,
            score=round(s, 4), created_at=m.created_at.isoformat()
        )
        for m, s in top
    ]

    return MemorySearchResponse(results=results, query=q, total=len(scored))


@memory_router.get("/list")
async def list_memories(
    limit: int = Query(default=50, ge=1, le=200),
    category: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's memories (without embeddings for performance)."""
    stmt = (
        select(VectorMemory)
        .where(VectorMemory.user_id == user.id)
        .order_by(VectorMemory.created_at.desc())
        .limit(limit)
    )
    if category:
        stmt = stmt.where(VectorMemory.category == category)
    result = await db.execute(stmt)
    memories = result.scalars().all()

    return [
        {
            "id": m.id, "content": m.content[:200], "category": m.category,
            "source": m.source, "source_id": m.source_id,
            "created_at": m.created_at.isoformat()
        }
        for m in memories
    ]


@memory_router.get("/stats")
async def memory_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get memory usage stats for the current user."""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(VectorMemory.id)).where(VectorMemory.user_id == user.id)
    )
    total = result.scalar() or 0

    cat_result = await db.execute(
        select(VectorMemory.category, func.count(VectorMemory.id))
        .where(VectorMemory.user_id == user.id)
        .group_by(VectorMemory.category)
    )
    categories = {row[0]: row[1] for row in cat_result.all()}

    return {"total_memories": total, "categories": categories}


@memory_router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific memory."""
    result = await db.execute(
        select(VectorMemory).where(VectorMemory.id == memory_id, VectorMemory.user_id == user.id)
    )
    mem = result.scalar_one_or_none()
    if not mem:
        raise HTTPException(status_code=404, detail="Memoire non trouvee")

    await db.delete(mem)
    await db.commit()
    return {"ok": True, "deleted": memory_id}


@memory_router.delete("/clear/all")
async def clear_all_memories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear all memories for the current user."""
    await db.execute(
        delete(VectorMemory).where(VectorMemory.user_id == user.id)
    )
    await db.commit()
    return {"ok": True, "message": "Toutes les memoires ont ete supprimees"}


# ── Internal helper for chat integration ────────────────────────
async def retrieve_relevant_memories(user_id: str, query: str, db: AsyncSession, limit: int = 3, threshold: float = 0.35) -> str:
    """Retrieve relevant memories for a given query — used by chat routes to enrich context."""
    try:
        query_embedding = await generate_embedding(query)
    except Exception as e:
        logger.warning(f"Embedding generation failed for memory retrieval: {e}")
        return ""

    stmt = select(VectorMemory).where(VectorMemory.user_id == user_id)
    result = await db.execute(stmt)
    memories = result.scalars().all()

    if not memories:
        return ""

    scored = []
    for mem in memories:
        try:
            mem_emb = json.loads(mem.embedding)
            sim = cosine_similarity(query_embedding, mem_emb)
            if sim >= threshold:
                scored.append((mem, sim))
        except (json.JSONDecodeError, TypeError):
            continue

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]

    if not top:
        return ""

    lines = ["MEMOIRE VECTORIELLE (souvenirs pertinents de l'utilisateur):"]
    for mem, sim in top:
        lines.append(f"- [{mem.category}] {mem.content}")

    return "\n".join(lines)


async def auto_store_memory(user_id: str, content: str, db: AsyncSession, source: str = "conversation", source_id: str = None, category: str = "context"):
    """Automatically store a memory from a conversation — called after AI response."""
    if len(content.strip()) < 20:
        return

    try:
        embedding = await generate_embedding(content)
        mem = VectorMemory(
            user_id=user_id,
            content=content[:5000],
            embedding=json.dumps(embedding),
            source=source,
            source_id=source_id,
            category=category,
        )
        db.add(mem)
        await db.commit()
        logger.info(f"Auto-stored memory: user={user_id}, source={source}")
    except Exception as e:
        logger.warning(f"Auto-store memory error: {e}")
