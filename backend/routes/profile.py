"""Profile, productivity, document, and slash command routes."""
import logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import os
import json
import uuid
import httpx

from database import get_db
from models import User, Conversation, Transaction, TeamMember
from deps import get_current_user
from utils import (
    MAMMOTH_BASE_URL, UPLOADS_DIR, CONFIG_PATH,
    load_admin_config, send_brevo_email, logger
)

profile_router = APIRouter(tags=["Profile"])

def _safe_load_memory(user) -> dict:
    """Safely parse user.memory JSON, returning {} on any error (#21 fix)."""
    try:
        return json.loads(user.memory) if user.memory else {}
    except (json.JSONDecodeError, TypeError):
        return {}

@profile_router.post("/profile/import-document")
async def import_profile_document(file: UploadFile = File(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Upload and process a document to populate user profile with AI validation."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Fichier requis")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Format non supporte. Utilisez PDF ou image.")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10MB)")
    extracted_text = ""
    if ext == ".pdf":
        try:
            from pypdf import PdfReader as _PdfReader
            import io as _io_m
            _reader = _PdfReader(_io_m.BytesIO(content))
            _pdf_text = []
            for _page in _reader.pages:
                _pdf_text.append(_page.extract_text() or "")
            extracted_text = "\n".join(_pdf_text)
        except Exception:
            extracted_text = "[Impossible d extraire le texte du PDF]"
    if not extracted_text or ext in [".png", ".jpg", ".jpeg", ".webp"]:
        import base64
        b64 = base64.b64encode(content).decode()
        mime = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext.lstrip("."), "application/octet-stream")
        mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
        if mammoth_key:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(f"{MAMMOTH_BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                        json={"model": "gemini-1.5-pro", "messages": [{"role": "system", "content": """Tu es un assistant specialise dans la verification de documents officiels francais.
ETAPE 1: Determine si ce document est un document officiel valide parmi: Kbis, extrait INSEE, attestation URSSAF, RNA, statuts d'association, carte d'etudiant, bulletin de salaire, contrat d'alternance. 
ETAPE 2: Si c'est un document valide, extrais: nom de l'organisation, type (association/entreprise/etudiant), SIRET, SIREN, RNA, adresse, representant legal, date de creation, objet social.
ETAPE 3: Reponds en JSON avec ce format exact:
{"is_valid_document": true/false, "document_type": "kbis/insee/urssaf/rna/statuts/carte_etudiant/bulletin_salaire/contrat_alternance/inconnu", "confidence": 0.0-1.0, "rejection_reason": "si invalide", "nom_organisation": "", "type_organisation": "", "siret": "", "siren": "", "rna": "", "adresse": "", "representant_legal": "", "date_creation": "", "objet_social": ""}
Si le document n'est PAS un document officiel (photo, facture, document personnel, etc), mets is_valid_document a false."""},
                            {"role": "user", "content": [{"type": "text", "text": f"Verifie et extrais les informations de ce document. Texte extrait: {extracted_text[:3000]}" if extracted_text else "Verifie et extrais les informations de ce document."}, {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}], "max_tokens": 2048})
                if response.status_code == 200:
                    data = response.json()
                    ai_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    try:
                        import re
                        json_match = re.search(r'\{[^{}]*\}', ai_text, re.DOTALL)
                        if json_match:
                            profile_data = json.loads(json_match.group())
                        else:
                            profile_data = {"raw_extraction": ai_text, "is_valid_document": False}
                    except Exception:
                        profile_data = {"raw_extraction": ai_text, "is_valid_document": False}

                    # AI Validation Gate
                    is_valid = profile_data.get("is_valid_document", False)
                    confidence = float(profile_data.get("confidence", 0))
                    if not is_valid or confidence < 0.5:
                        reason = profile_data.get("rejection_reason", "Ce document ne semble pas etre un document officiel valide (Kbis, INSEE, RNA, carte etudiante, etc).")
                        return {"status": "rejected", "message": reason, "document_type": profile_data.get("document_type", "inconnu")}

                    # Auto-verify SIRET/RNA via government APIs
                    siret = profile_data.get("siret", "")
                    rna = profile_data.get("rna", "")
                    api_verification = {"siret_verified": False, "rna_verified": False}
                    if siret and len(siret) >= 9:
                        try:
                            async with httpx.AsyncClient(timeout=10) as api_client:
                                resp = await api_client.get(f"https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}")
                            if resp.status_code == 200:
                                api_verification["siret_verified"] = True
                                api_data = resp.json()
                                etab = api_data.get("etablissement", {})
                                uc = etab.get("unite_legale", {})
                                api_verification["siret_name"] = uc.get("denomination", "")
                        except Exception:
                            pass
                    if rna and rna.startswith("W"):
                        try:
                            async with httpx.AsyncClient(timeout=10) as api_client:
                                resp = await api_client.get(f"https://entreprise.data.gouv.fr/api/rna/v1/id/{rna}")
                            if resp.status_code == 200:
                                api_verification["rna_verified"] = True
                                api_data = resp.json()
                                asso = api_data.get("association", {})
                                api_verification["rna_name"] = asso.get("titre", "")
                        except Exception:
                            pass

                    profile_data["api_verification"] = api_verification

                    memory = _safe_load_memory(user)
                    memory["imported_profile"] = profile_data
                    memory["import_date"] = datetime.now(timezone.utc).isoformat()
                    memory["import_filename"] = file.filename
                    await db.execute(update(User).where(User.id == user.id).values(memory=json.dumps(memory)))
                    await db.commit()
                    # Notify admin by email
                    try:
                        admin_result = await db.execute(select(User).where(User.role.in_(["admin", "super_admin"])))
                        admins = admin_result.scalars().all()
                        verified_str = "SIRET OK" if api_verification.get("siret_verified") else ("RNA OK" if api_verification.get("rna_verified") else "Non verifie API")
                        html = f"""
                        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
                            <h2 style="color:#1E3A8A;">Nouveau document importe</h2>
                            <p>L'utilisateur <strong>{user.email}</strong> (plan: {user.plan}) a importe un document.</p>
                            <p><strong>Fichier :</strong> {file.filename}</p>
                            <p><strong>Type document :</strong> {profile_data.get('document_type', 'inconnu')}</p>
                            <p><strong>Validation API :</strong> {verified_str}</p>
                            <p><strong>Donnees extraites :</strong></p>
                            <pre style="background:#f5f5f0;padding:12px;border-radius:8px;font-size:12px;overflow-x:auto;">{json.dumps(profile_data, indent=2, ensure_ascii=False)[:2000]}</pre>
                            <p style="color:#666;font-size:12px;">Date : {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC</p>
                        </div>"""
                        for admin in admins:
                            send_brevo_email(admin.email, admin.name or "Admin", f"Document importe par {user.email}", html)
                    except Exception as e:
                        logger.error(f"Admin notification error: {e}")
                    return {"status": "success", "extracted": profile_data, "api_verification": api_verification}
            except Exception as e:
                logger.error(f"Document import AI error: {e}")
    if extracted_text:
        memory = _safe_load_memory(user)
        memory["imported_text"] = extracted_text[:5000]
        memory["import_date"] = datetime.now(timezone.utc).isoformat()
        await db.execute(update(User).where(User.id == user.id).values(memory=json.dumps(memory)))
        await db.commit()
        return {"status": "partial", "message": "Texte extrait, analyse IA indisponible", "text_preview": extracted_text[:500]}
    raise HTTPException(status_code=500, detail="Impossible d'extraire les informations du document")

@profile_router.get("/profile/organization")
async def get_org_profile(user: User = Depends(get_current_user)):
    memory = _safe_load_memory(user)
    return memory.get("organization", {})

@profile_router.put("/profile/organization")
async def update_org_profile(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    memory = _safe_load_memory(user)
    memory["organization"] = data
    await db.execute(update(User).where(User.id == user.id).values(memory=json.dumps(memory)))
    await db.commit()
    return {"status": "saved"}

@profile_router.post("/profile/verify-rna/{rna}")
async def verify_rna(rna: str, user: User = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://entreprise.data.gouv.fr/api/rna/v1/id/{rna}")
        if resp.status_code == 200:
            data = resp.json()
            asso = data.get("association", {})
            return {"valid": True, "name": asso.get("titre", ""), "address": asso.get("adresse_siege", ""), "object": asso.get("objet", ""), "date_creation": asso.get("date_creation", "")}
        return {"valid": False, "message": "RNA non trouve"}
    except Exception:
        return {"valid": False, "message": "Service indisponible"}

# #47 — Simple cache for SIRET/RNA verification (avoid redundant API calls)
_siret_cache = {}
_SIRET_CACHE_TTL = 3600  # 1 hour

@profile_router.post("/profile/verify-siret/{siret}")
async def verify_siret(siret: str, user: User = Depends(get_current_user)):
    import time as _time_siret
    cache_key = f"siret:{siret}"
    cached = _siret_cache.get(cache_key)
    if cached and (_time_siret.time() - cached["ts"]) < _SIRET_CACHE_TTL:
        return cached["data"]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}")
        if resp.status_code == 200:
            data = resp.json()
            etab = data.get("etablissement", {})
            uc = etab.get("unite_legale", {})
            result = {"valid": True, "name": uc.get("denomination", ""), "siret": siret, "naf": etab.get("activite_principale", ""), "address": etab.get("geo_adresse", "")}
            _siret_cache[cache_key] = {"data": result, "ts": _time_siret.time()}
            return result
        return {"valid": False, "message": "SIRET non trouve"}
    except Exception:
        return {"valid": False, "message": "Service indisponible"}

@profile_router.get("/productivity/stats")
async def get_productivity_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get productivity statistics for the current user."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(select(func.count(Conversation.id)).where(Conversation.user_id == user.id, Conversation.created_at >= month_start))
    monthly_conversations = result.scalar() or 0
    result = await db.execute(select(func.count(Conversation.id)).where(Conversation.user_id == user.id))
    total_conversations = result.scalar() or 0
    result = await db.execute(select(func.coalesce(func.sum(Conversation.total_credits_used), 0)).where(Conversation.user_id == user.id, Conversation.created_at >= month_start))
    monthly_credits = result.scalar() or 0
    total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
    estimated_time_saved = monthly_conversations * 5
    # #40 — Label as estimate, EUR is the platform currency
    estimated_value = round(estimated_time_saved * 0.5, 2)
    # #39 — Get actual message count from conversations
    msg_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.user_id == user.id,
            Conversation.created_at >= month_start,
            Conversation.total_credits_used > 0
        )
    )
    actual_message_count = (msg_result.scalar() or 0) * 2  # approx user + AI per convo
    return {
        "period": month_start.strftime("%B %Y"),
        "conversations": monthly_conversations,
        "messages_sent": max(actual_message_count, monthly_conversations),
        "total_conversations": total_conversations,
        "credits_used": int(monthly_credits),
        "credits_remaining": total_credits,
        "time_saved_minutes": estimated_time_saved,
        "estimated_value_eur": estimated_value,
        "plan": user.plan,
        "member_since": user.created_at.isoformat() if user.created_at else None,
    }

@profile_router.post("/documents/upload")
async def upload_document_for_qa(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Fichier requis")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".pdf":
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptes")
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 20MB)")
    # #15 — Use full UUID for doc_id (12 hex chars too short for collision prevention)
    doc_id = str(uuid.uuid4())
    # #3/#7 — Isolate files by user_id to prevent unauthorized access
    filepath = os.path.join(UPLOADS_DIR, f"doc_{user.id}_{doc_id}.pdf")
    with open(filepath, "wb") as f:
        f.write(content)
    extracted_text = ""
    try:
        from pypdf import PdfReader as _PdfReader
        _reader = _PdfReader(filepath)
        extracted_text = "\n".join(p.extract_text() or "" for p in _reader.pages)
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur de lecture du document")
    return {
        "status": "uploaded",
        "doc_id": doc_id,
        "text_preview": extracted_text[:500] if extracted_text else "",
        "word_count": len(extracted_text.split()) if extracted_text else 0
    }

@profile_router.post("/documents/{doc_id}/ask")
async def ask_document_question(doc_id: str, data: Dict[str, Any], user: User = Depends(get_current_user)):
    """Ask a question about a previously uploaded document."""
    question = (data.get("question") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question requise")
    # #7/#98 — Use user_id prefix to ensure ownership check
    filepath = os.path.join(UPLOADS_DIR, f"doc_{user.id}_{doc_id}.pdf")
    if not os.path.exists(filepath):
        # Fallback: check old format (backwards compat) but verify no path traversal
        old_filepath = os.path.join(UPLOADS_DIR, f"doc_{doc_id}.pdf")
        if os.path.exists(old_filepath) and '..' not in doc_id:
            filepath = old_filepath
        else:
            raise HTTPException(status_code=404, detail="Document non trouve")
    extracted_text = ""
    try:
        from pypdf import PdfReader as _PdfReader
        _reader = _PdfReader(filepath)
        extracted_text = "\n".join(p.extract_text() or "" for p in _reader.pages)
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur de lecture du document")
    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(status_code=500, detail="IA non configuree")
    context = extracted_text[:12000]
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{MAMMOTH_BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "messages": [{"role": "system", "content": f"Tu es un assistant qui repond aux questions sur un document. Voici le contenu du document:\n\n{context}\n\nReponds uniquement en te basant sur le contenu du document. Detecte automatiquement la langue de la question et reponds dans cette meme langue."},
                    {"role": "user", "content": question}], "max_tokens": 2048, "temperature": 0.2})
        if response.status_code == 200:
            answer = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"answer": answer, "doc_id": doc_id}
        raise HTTPException(status_code=502, detail=f"Erreur IA: {response.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@profile_router.get("/conversations/{conv_id}/export/{fmt}")
async def export_conversation_multi(conv_id: str, fmt: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if fmt not in ("pdf", "docx", "pptx"):
        raise HTTPException(status_code=400, detail="Format non supporte. Utilisez pdf, docx ou pptx.")
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    messages = conv.messages or []
    title = conv.title or "Conversation"
    if fmt == "pdf":
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.utils import simpleSplit
        import io
        buf = io.BytesIO()
        c = pdf_canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        y = h - 50
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, title[:60])
        y -= 30
        c.setFont("Helvetica", 10)
        for msg in messages:
            role = "Vous" if msg.get("role") == "user" else "IA"
            text = f"[{role}] {msg.get('content', '')}"
            lines = simpleSplit(text, "Helvetica", 10, w - 100)
            for line in lines:
                if y < 50:
                    c.showPage()
                    y = h - 50
                    c.setFont("Helvetica", 10)
                c.drawString(50, y, line)
                y -= 14
            y -= 10
        c.save()
        buf.seek(0)
        from fastapi.responses import StreamingResponse
        return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{title[:30]}.pdf"'})
    elif fmt == "docx":
        from docx import Document as DocxDocument
        import io
        doc = DocxDocument()
        doc.add_heading(title, level=1)
        for msg in messages:
            role = "Vous" if msg.get("role") == "user" else "IA"
            doc.add_paragraph(f"[{role}]", style="Intense Quote" if role == "IA" else None)
            doc.add_paragraph(msg.get("content", ""))
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        from fastapi.responses import StreamingResponse
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="{title[:30]}.docx"'})
    elif fmt == "pptx":
        from pptx import Presentation
        from pptx.util import Inches, Pt
        import io
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = title
        slide.placeholders[1].text = f"Exporte le {datetime.now(timezone.utc).strftime('%d/%m/%Y')}"
        for msg in messages:
            role = "Vous" if msg.get("role") == "user" else "IA"
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = role
            content = msg.get("content", "")[:800]
            slide.placeholders[1].text = content
        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        from fastapi.responses import StreamingResponse
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers={"Content-Disposition": f'attachment; filename="{title[:30]}.pptx"'})

@profile_router.get("/notifications")
async def get_smart_notifications(user: User = Depends(get_current_user)):
    """Smart notifications for the user."""
    notifications = []
    if user.credits < 100:
        notifications.append({"id": "smart_low_credits", "type": "warning", "title": "Credits faibles", "message": f"Il vous reste {user.credits} credits.", "action_url": "/pricing"})
    if user.plan == "free" and (user.credits or 0) < 200:
        notifications.append({"id": "smart_upgrade", "type": "info", "title": "Passez a Premium", "message": "Debloquez plus de credits et les modes avances.", "action_url": "/pricing"})
    return {"notifications": notifications, "count": len(notifications)}

@profile_router.post("/slash/summarize")
async def slash_summarize(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv_id = data.get("conversation_id")
    if not conv_id:
        raise HTTPException(status_code=400, detail="conversation_id requis")
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    messages = conv.messages or []
    text = "\n".join(f"[{m.get('role','?')}]: {m.get('content','')}" for m in messages[-20:])
    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        return {"summary": "Resume indisponible (IA non configuree)"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{MAMMOTH_BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "messages": [{"role": "system", "content": "Resume cette conversation en 3-5 points cles. Sois concis."}, {"role": "user", "content": text}], "max_tokens": 512})
        if resp.status_code == 200:
            summary = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"summary": summary}
    except Exception:
        pass
    return {"summary": "Resume indisponible"}

@profile_router.post("/slash/reformat")
async def slash_reformat(data: Dict[str, Any], user: User = Depends(get_current_user)):
    text = data.get("text", "")
    format_type = data.get("format", "email")
    if not text:
        raise HTTPException(status_code=400, detail="Texte requis")
    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        return {"result": text}
    prompts = {
        "email": "Reformate ce texte en email professionnel bien structure.",
        "court": "Reformate ce texte en version courte et concise (max 3 phrases).",
        "formel": "Reformate ce texte en version formelle et professionnelle.",
    }
    prompt = prompts.get(format_type, prompts["email"])
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{MAMMOTH_BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}], "max_tokens": 1024})
        if resp.status_code == 200:
            result = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"result": result, "format": format_type}
    except Exception:
        pass
    return {"result": text}



# ==================== CUSTOM PROMPTS ====================

@profile_router.get("/profile/custom-prompts")
async def get_custom_prompts(user: User = Depends(get_current_user)):
    """Get user's custom prompts."""
    settings = user.settings or {}
    return {"prompts": settings.get("custom_prompts", [])}

@profile_router.post("/profile/custom-prompts")
async def create_custom_prompt(data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create a new custom prompt."""
    title = (data.get("title") or "").strip()
    prompt_text = (data.get("prompt") or "").strip()
    if not title or not prompt_text:
        raise HTTPException(status_code=400, detail="Titre et prompt requis")
    settings = dict(user.settings or {})
    prompts = list(settings.get("custom_prompts", []))
    if len(prompts) >= 50:
        raise HTTPException(status_code=400, detail="Maximum 50 prompts personnalises")
    new_prompt = {
        "id": str(uuid.uuid4())[:8],
        "title": title[:100],
        "prompt": prompt_text[:2000],
        "category": (data.get("category") or "personnel")[:50],
        "icon": (data.get("icon") or "")[:4],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    prompts.append(new_prompt)
    settings["custom_prompts"] = prompts
    await db.execute(update(User).where(User.id == user.id).values(settings=settings))
    await db.commit()
    return new_prompt

@profile_router.put("/profile/custom-prompts/{prompt_id}")
async def update_custom_prompt(prompt_id: str, data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Update a custom prompt."""
    settings = dict(user.settings or {})
    prompts = list(settings.get("custom_prompts", []))
    for i, p in enumerate(prompts):
        if p.get("id") == prompt_id:
            if data.get("title"):
                prompts[i]["title"] = data["title"][:100]
            if data.get("prompt"):
                prompts[i]["prompt"] = data["prompt"][:2000]
            if data.get("category"):
                prompts[i]["category"] = data["category"][:50]
            if data.get("icon"):
                prompts[i]["icon"] = data["icon"][:4]
            settings["custom_prompts"] = prompts
            await db.execute(update(User).where(User.id == user.id).values(settings=settings))
            await db.commit()
            return prompts[i]
    raise HTTPException(status_code=404, detail="Prompt non trouve")

@profile_router.delete("/profile/custom-prompts/{prompt_id}")
async def delete_custom_prompt(prompt_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Delete a custom prompt."""
    settings = dict(user.settings or {})
    prompts = list(settings.get("custom_prompts", []))
    settings["custom_prompts"] = [p for p in prompts if p.get("id") != prompt_id]
    await db.execute(update(User).where(User.id == user.id).values(settings=settings))
    await db.commit()
    return {"status": "deleted"}


@profile_router.post("/profile/custom-prompts/{prompt_id}/share")
async def share_custom_prompt(prompt_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Share a custom prompt with the user's team."""
    from routes.team import get_user_team
    settings = user.settings or {}
    prompts = settings.get("custom_prompts", [])
    prompt = next((p for p in prompts if p.get("id") == prompt_id), None)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt non trouve")
    team = await get_user_team(user, db)
    if not team:
        raise HTTPException(status_code=400, detail="Vous n'avez pas d'equipe. Creez ou rejoignez une equipe pour partager des prompts.")
    # Get team members
    result = await db.execute(select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.status == "active", TeamMember.user_id != user.id))
    members = result.scalars().all()
    shared_count = 0
    for member in members:
        if not member.user_id:
            continue
        m_result = await db.execute(select(User).where(User.id == member.user_id))
        m_user = m_result.scalar_one_or_none()
        if not m_user:
            continue
        m_settings = dict(m_user.settings or {})
        m_prompts = list(m_settings.get("custom_prompts", []))
        # Skip if they already have this prompt (by title)
        if any(p.get("title") == prompt["title"] for p in m_prompts):
            continue
        if len(m_prompts) >= 50:
            continue
        shared_prompt = {
            "id": str(uuid.uuid4())[:8],
            "title": prompt["title"],
            "prompt": prompt["prompt"],
            "category": prompt.get("category", "equipe"),
            "icon": prompt.get("icon", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "shared_by": user.name or user.email
        }
        m_prompts.append(shared_prompt)
        m_settings["custom_prompts"] = m_prompts
        await db.execute(update(User).where(User.id == m_user.id).values(settings=m_settings))
        shared_count += 1
    await db.commit()
    return {"status": "shared", "shared_count": shared_count, "message": f"Prompt partage avec {shared_count} membre(s) de l'equipe"}
