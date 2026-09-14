"""
Routes Base de connaissances — Upload, extraction texte, liste, suppression
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import uuid
import io
import logging

from database import get_db
from models import User, Team, TeamMember, KnowledgeFile

logger = logging.getLogger("knowledge")
knowledge_router = APIRouter(prefix="/team/knowledge", tags=["Knowledge"])
bearer = HTTPBearer(auto_error=False)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def get_user(creds: HTTPAuthorizationCredentials, db: AsyncSession) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Non authentifie")
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


async def get_user_team(user: User, db: AsyncSession, team_id: str = None) -> Team:
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
        raise HTTPException(status_code=404, detail="Aucune equipe trouvee")
    result = await db.execute(select(Team).where(Team.owner_id == user.id).order_by(Team.created_at).limit(1))
    team = result.scalar_one_or_none()
    if team:
        return team
    result2 = await db.execute(
        select(Team).join(TeamMember).where(TeamMember.user_id == user.id, TeamMember.status == "active")
        .order_by(Team.created_at).limit(1)
    )
    team = result2.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Aucune equipe trouvee")
    return team


def extract_text_from_pdf(data: bytes) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(data))
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t.strip())
    return "\n\n".join(text_parts)


def extract_text_from_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def extract_text_from_txt(data: bytes) -> str:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def extract_text(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return extract_text_from_pdf(data)
    elif ext == "docx":
        return extract_text_from_docx(data)
    elif ext in ("txt", "csv", "md"):
        return extract_text_from_txt(data)
    else:
        raise ValueError(f"Format non supporte: .{ext}")


@knowledge_router.post("/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(creds, db)
    team = await get_user_team(user, db)

    # Validate file
    allowed_ext = {"pdf", "docx", "txt", "csv", "md"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"Format non supporte. Formats acceptes: {', '.join(allowed_ext)}")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10 Mo)")

    # Extract text
    try:
        text = extract_text(file.filename, data)
    except Exception as e:
        logger.error(f"Text extraction failed for {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Erreur d'extraction: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Aucun texte extractible dans ce fichier")

    # Truncate very large texts (keep first 50k chars for context)
    truncated_text = text[:50000]

    # Save to DB
    kf = KnowledgeFile(
        id=str(uuid.uuid4()),
        team_id=team.id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size=len(data),
        extracted_text=truncated_text,
        status="active",
    )
    db.add(kf)
    await db.commit()

    logger.info(f"Knowledge file uploaded: {file.filename} ({len(truncated_text)} chars) for team {team.id}")

    return {
        "id": kf.id,
        "filename": kf.filename,
        "size": kf.size,
        "status": kf.status,
        "text_length": len(truncated_text),
        "created_at": kf.created_at.isoformat() if kf.created_at else None,
    }


@knowledge_router.get("/files")
async def list_knowledge_files(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(creds, db)
    team = await get_user_team(user, db)

    result = await db.execute(
        select(KnowledgeFile)
        .where(KnowledgeFile.team_id == team.id)
        .order_by(KnowledgeFile.created_at.desc())
    )
    files = result.scalars().all()

    return [
        {
            "id": f.id,
            "filename": f.filename,
            "size": f.size,
            "status": f.status,
            "text_length": len(f.extracted_text) if f.extracted_text else 0,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


@knowledge_router.delete("/files/{file_id}")
async def delete_knowledge_file(
    file_id: str,
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(creds, db)
    team = await get_user_team(user, db)

    result = await db.execute(
        select(KnowledgeFile).where(KnowledgeFile.id == file_id, KnowledgeFile.team_id == team.id)
    )
    kf = result.scalar_one_or_none()
    if not kf:
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    await db.delete(kf)
    await db.commit()

    return {"success": True, "message": f"{kf.filename} supprime"}
