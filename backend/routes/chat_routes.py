"""
Chat Routes (conversations, upload, streaming, transcribe) — extracted from server.py
"""
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse, Response
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
import os, uuid, json, httpx, asyncio, re, base64, logging, random

from database import get_db, async_session_factory
from models import User, Conversation, Project, Workflow, Transaction, PromoCode, PromoUsage, Folder, Team, TeamMember
from schemas import (
    ChatRequest, ConversationResponse, ProjectCreateSchema, ProjectResponse,
    WorkflowCreateSchema, WorkflowResponse, AgentEstimateRequest, AgentRunRequest
)
from deps import get_current_user, get_admin_user, JWT_SECRET, JWT_ALGORITHM, security, hash_password, verify_password
from utils import (
    UPLOADS_DIR, MAMMOTH_BASE_URL, AGENT_DEFAULT_MODEL, AGENT_COMPLEX_MODEL, AGENT_MAX_TIMEOUT,
    AGENT_CREDITS_MAP, classify_task_type, estimate_agent_credits, select_agent_model,
    classify_agent_specialization, get_agent_system_prompt,
    get_mollie_client, send_brevo_email, send_low_credits_notification,
    load_admin_config, save_admin_config,
    _get_email_log, _append_email_log, _append_admin_log, _get_admin_log,
    EMAIL_TEMPLATES, GENERATED_IMAGES_DIR, CONFIG_PATH, logger as utils_logger,
    CREDIT_PACKAGES, SUBSCRIPTION_PLANS, BREVO_API_KEY,
)
from mollie.api.client import Client as MollieClient
from mollie.api.error import Error as MollieError
from routes.app_logs import log_event

logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).parent

chat_router = APIRouter(tags=["Chat"])

# ── Directories ────────────────────────────────────────────────
WORKSPACES_DIR = os.path.join(os.path.dirname(__file__), "workspaces")
os.makedirs(WORKSPACES_DIR, exist_ok=True)

# ── File Upload ────────────────────────────────────────────────
@chat_router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Upload a file (image, PDF, Word, ZIP, etc.) and return URL + extracted text for AI"""
    ALLOWED_EXTENSIONS = {
        ".pdf", ".doc", ".docx", ".txt", ".csv", ".xls", ".xlsx",
        ".zip", ".png", ".jpg", ".jpeg", ".gif", ".webp",
        ".md", ".json", ".xml"
    }
    ext = os.path.splitext(file.filename or "file")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Format non supporté: {ext}. Formats acceptés: PDF, Word, Excel, ZIP, images, texte.")

    max_size = 25 * 1024 * 1024  # 25MB
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    # Lecture en mémoire (pas d'écriture du fichier uploadé sur le disque du pod)
    import io as _io_up
    _bio = _io_up.BytesIO()
    total_read = 0
    chunk_size = 256 * 1024  # 256KB chunks
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > max_size:
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 25 Mo)")
        _bio.write(chunk)
    file_content = _bio.getvalue()

    extracted_text = ""
    file_info = {"pages": 0, "words": 0, "extractable": False}
    try:
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(_io_up.BytesIO(file_content))
                texts = [p.extract_text() or "" for p in reader.pages]
                extracted_text = "\n".join(texts)[:15000]
                file_info = {"pages": len(reader.pages), "words": len(extracted_text.split()), "extractable": True}
            except Exception:
                extracted_text = "[PDF - extraction impossible, fichier peut être scanné]"
        elif ext == ".docx":
            try:
                import docx as _docx
                doc = _docx.Document(_io_up.BytesIO(file_content))
                extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])[:15000]
                file_info = {"pages": 1, "words": len(extracted_text.split()), "extractable": True}
            except Exception:
                extracted_text = "[Word - extraction impossible]"
        elif ext in (".txt", ".md", ".csv", ".json", ".xml"):
            extracted_text = file_content.decode("utf-8", errors="replace")[:15000]
            file_info = {"pages": 1, "words": len(extracted_text.split()), "extractable": True}
        elif ext == ".zip":
            import zipfile as _zf_upload
            if _zf_upload.is_zipfile(_io_up.BytesIO(file_content)):
                workspace_dir = os.path.join(WORKSPACES_DIR, file_id)
                os.makedirs(workspace_dir, exist_ok=True)
                code_exts = {'.py','.js','.jsx','.ts','.tsx','.vue','.rb','.php','.java','.go','.rs','.cs','.html','.css'}
                config_exts = {'.json','.yaml','.yml','.toml','.cfg','.ini','.env','.sh','.sql','.scss'}
                doc_exts = {'.md','.txt','.csv','.rst'}
                all_text_exts = code_exts | config_exts | doc_exts
                skip_dirs = {'node_modules','.git','__pycache__','.next','dist','build','.venv','.cache','vendor'}
                with _zf_upload.ZipFile(_io_up.BytesIO(file_content), "r") as zf:
                    zf.extractall(workspace_dir)
                    names = zf.namelist()
                    def file_priority(n):
                        e = os.path.splitext(n)[1].lower()
                        if e in code_exts: return 0
                        if e in config_exts: return 1
                        if e in doc_exts: return 2
                        return 3
                    text_files = sorted([
                        n for n in names if not n.endswith('/')
                        and not any(sd in n.replace('\\','/').split('/') for sd in skip_dirs)
                        and os.path.splitext(n)[1].lower() in all_text_exts
                    ], key=file_priority)
                    file_contents_str = ""
                    total_chars = 0
                    extracted_files = []
                    skipped_binary = 0
                    for name in text_files:
                        try:
                            # Read from disk (already extracted above — avoids double ZIP read #98)
                            disk_path = os.path.join(workspace_dir, name)
                            if not os.path.isfile(disk_path):
                                continue
                            with open(disk_path, "rb") as _df:
                                raw = _df.read()
                            try:
                                text_content = raw.decode('utf-8')
                            except UnicodeDecodeError:
                                skipped_binary += 1
                                continue
                            if text_content[:20].startswith('%PDF') or '\x00' in text_content[:200]:
                                skipped_binary += 1
                                continue
                            truncated = text_content[:15000]
                            file_contents_str += f"\n--- FICHIER: {name} ---\n{truncated}\n"
                            total_chars += len(truncated)
                            extracted_files.append(name)
                            if total_chars >= 200000:
                                file_contents_str += f"\n[... {len(text_files)-len(extracted_files)} fichiers restants tronqués ...]\n"
                                break
                        except Exception:
                            pass
                    summary = f"Archive ZIP: {file.filename} ({len(names)} fichier(s))\nFichiers lus: {len(extracted_files)}/{len(text_files)}\n"
                    extracted_text = summary + "\n--- CONTENU DES FICHIERS ---\n" + file_contents_str
                    file_info = {"pages": len(extracted_files), "words": len(extracted_text.split()), "extractable": True, "workspace_id": file_id}
        elif ext in (".xls", ".xlsx"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(_io_up.BytesIO(file_content), read_only=True, data_only=True)
                rows = []
                for ws in wb.worksheets[:3]:
                    for row in ws.iter_rows(max_row=100, values_only=True):
                        if any(c is not None for c in row):
                            rows.append("\t".join([str(c) if c is not None else "" for c in row]))
                extracted_text = "\n".join(rows)[:15000]
                file_info = {"pages": len(wb.worksheets), "words": len(extracted_text.split()), "extractable": True}
            except Exception:
                extracted_text = "[Excel - extraction impossible]"
    except Exception as extract_err:
        logger.warning(f"File extraction error: {extract_err}")

    # Persistance dans le stockage objet Emergent (survit aux redéploiements Railway) + réf DB
    from storage import put_object, guess_content_type
    from models import UploadedFile
    _ct = file.content_type or guess_content_type(ext)
    _storage_path = f"zayado/uploads/{filename}"
    await put_object(_storage_path, file_content, _ct)
    db.add(UploadedFile(id=file_id, user_id=user.id, filename=filename,
                        original_name=file.filename or filename, storage_path=_storage_path,
                        content_type=_ct, size=len(file_content)))
    await db.commit()

    file_url = f"/api/chat/uploads-store/{filename}"
    return {
        "id": file_id,
        "url": file_url,
        "download_url": file_url,
        "name": file.filename,
        "type": _ct,
        "size": len(file_content),
        "ext": ext,
        "extracted_text": extracted_text,
        "file_info": file_info
    }


@chat_router.get("/uploads-store/{filename}")
@chat_router.head("/uploads-store/{filename}")
async def serve_upload_store(filename: str, db: AsyncSession = Depends(get_db)):
    """Sert un fichier uploadé depuis le stockage objet (public, pour <img src>)."""
    safe = os.path.basename(filename)
    if not safe or safe != filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    from models import UploadedFile
    from storage import get_object
    res = await db.execute(select(UploadedFile).where(UploadedFile.filename == safe))
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    try:
        data, ct = await get_object(rec.storage_path)
    except Exception as e:
        logger.warning(f"serve_upload_store get failed: {e}")
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return Response(content=data, media_type=rec.content_type or ct)

@chat_router.get("/public-config")
async def chat_public_config(user: User = Depends(get_current_user)):
    """Authenticated public config — partner links, etc. Uses cached config loader."""
    try:
        _cfg = load_admin_config()
        return {
            "partner_links": _cfg.get("partner_links", []),
            "promo_banner": _cfg.get("promo_banner", ""),
        }
    except Exception:
        return {"partner_links": [], "promo_banner": ""}


# Streaming abort store (conversation_id -> should_abort flag)
# Fix #audit — bounded dict with TTL cleanup to prevent memory leak
_streaming_abort = {}
_ABORT_MAX_SIZE = 500

def _cleanup_abort_store():
    """Remove oldest entries if store grows too large."""
    if len(_streaming_abort) > _ABORT_MAX_SIZE:
        # Keep only the newest half
        to_keep = _ABORT_MAX_SIZE // 2
        keys = list(_streaming_abort.keys())
        for k in keys[:-to_keep]:
            _streaming_abort.pop(k, None)

@chat_router.post("/abort")
async def abort_streaming(request: Request, user: User = Depends(get_current_user)):
    body = await request.json()
    cid = body.get("conversation_id")
    if cid:
        _cleanup_abort_store()
        _streaming_abort[cid] = True
    return {"ok": True}


async def _deduct_credits(db: AsyncSession, user: User, amount: int, conversation_id: str = None, mode: str = None):
    """Atomically deduct credits: plan bucket first, then bonus, then purchased.
    Uses SELECT FOR UPDATE to prevent race conditions on concurrent requests (#18).
    Always logs to credit_logs so data persists even if conversation is deleted.
    """
    from sqlalchemy import select as sa_select
    from models import CreditLog
    # Re-fetch user with fresh data to avoid stale reads
    result = await db.execute(sa_select(User).where(User.id == user.id).with_for_update())
    fresh_user = result.scalar_one_or_none()
    if not fresh_user:
        return
    remaining = amount
    plan_d    = min(fresh_user.credits or 0, remaining);         remaining -= plan_d
    bonus_d   = min(fresh_user.bonus_credits or 0, remaining);   remaining -= bonus_d
    purch_d   = min(fresh_user.purchased_credits or 0, remaining)
    await db.execute(
        update(User).where(User.id == user.id).values(
            credits=User.credits - plan_d,
            bonus_credits=User.bonus_credits - bonus_d,
            purchased_credits=User.purchased_credits - purch_d,
        )
    )
    if conversation_id:
        await db.execute(
            update(Conversation).where(Conversation.id == conversation_id).values(
                total_credits_used=Conversation.total_credits_used + amount
            )
        )
    # Always log credit deduction for permanent tracking
    db.add(CreditLog(
        user_id=user.id,
        conversation_id=conversation_id,
        amount=-amount,
        mode=mode,
        log_type="chat_deduction",
        description=f"{amount} credits ({mode or 'unknown'})"
    ))
    await db.commit()



# ═══════════════════════════════════════════════════════════════
# CONTEXT COMPRESSION — Comme Claude.ai et Manus
# Quand une conversation devient longue, résume les anciens messages
# via l'IA au lieu de les couper. L'utilisateur garde tout son historique.
# ═══════════════════════════════════════════════════════════════

MAX_TOKENS_ESTIMATE = 80000   # ~80k tokens = limite sûre avant compression
TOKEN_PER_CHAR = 3             # estimation : 1 token ≈ 3 caractères français

def _estimate_tokens(messages: list) -> int:
    """Estimation rapide du nombre de tokens dans une liste de messages."""
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    return total_chars // TOKEN_PER_CHAR

async def _compress_context(messages: list, mammoth_key: str, mammoth_model: str) -> list:
    """
    Technique Claude.ai / Manus :
    1. Garder les 6 derniers échanges intacts (contexte récent)
    2. Résumer tout le reste en un seul bloc compact via l'IA
    3. Retourner [résumé_system] + [6 derniers messages]
    
    Si la compression échoue → retourner les messages tels quels (fail safe)
    """
    if len(messages) <= 20:
        return messages  # Pas besoin de compresser

    # Séparer : anciens messages à résumer + récents à garder intacts
    KEEP_RECENT = 12  # Garder les 12 derniers messages intacts
    old_messages = messages[:-KEEP_RECENT]
    recent_messages = messages[-KEEP_RECENT:]

    # Construire le texte à résumer
    conversation_text = ""
    for m in old_messages:
        role = "Utilisateur" if m.get("role") == "user" else "Assistant"
        content = str(m.get("content", ""))[:2000]  # Tronquer les très longs messages
        conversation_text += f"{role}: {content}\n\n"

    summary_prompt = f"""Tu es un assistant qui résume des conversations de manière concise et précise.

Résume cette conversation en gardant :
- Les décisions prises et les sujets discutés
- Les informations importantes partagées par l'utilisateur (nom, contexte, projet)
- Les réponses clés de l'assistant
- Le ton et le style de la conversation

Conversation à résumer :
{conversation_text[:8000]}

Résumé compact (max 500 mots) :"""

    try:
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.mammouth.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={
                    "model": mammoth_model,
                    "messages": [{"role": "user", "content": summary_prompt}],
                    "max_tokens": 800,
                    "stream": False
                }
            )
            if resp.status_code == 200:
                summary = resp.json()["choices"][0]["message"]["content"]
                # Construire le contexte compressé
                compressed = [
                    {
                        "role": "system",
                        "content": f"[RÉSUMÉ DE LA CONVERSATION PRÉCÉDENTE]\n{summary}\n[FIN DU RÉSUMÉ]"
                    }
                ] + recent_messages
                logger.info(f"Context compressed: {len(messages)} msgs → {len(compressed)} msgs (résumé + {KEEP_RECENT} récents)")
                return compressed
    except Exception as e:
        logger.warning(f"Context compression failed (using original): {e}")

    # Fail safe : retourner les messages originaux sans compression
    return messages


async def _smart_context(messages: list, mammoth_key: str = None, mammoth_model: str = None) -> list:
    """
    Point d'entrée principal — gestion intelligente du contexte comme Claude.ai :
    - Estime la taille du contexte
    - Si < 80k tokens → envoie tout (pas de compression)
    - Si >= 80k tokens → compresse via résumé IA
    """
    estimated = _estimate_tokens(messages)

    if estimated < MAX_TOKENS_ESTIMATE:
        return messages  # Contexte normal, rien à faire

    # Contexte trop long → compression
    logger.info(f"Context too long ({estimated} tokens est.), compressing...")

    if mammoth_key and mammoth_model:
        return await _compress_context(messages, mammoth_key, mammoth_model)

    # Sans clé Mammoth → garder les 10 premiers + 90 derniers (fallback)
    logger.warning("No Mammoth key for compression, using fallback truncation")
    if len(messages) > 100:
        return list(messages[:10]) + list(messages[-90:])
    return messages

async def _log_api_cost(db: AsyncSession, user_id: str, conversation_id: str, provider: str, model: str, mode: str, input_tokens: int, output_tokens: int, credits_charged: int):
    """FIX: Log API cost — utilise une session indépendante robuste pour la production."""
    # Tarifs API réels ($/1M tokens) — mis à jour avril 2025
    # Source : pages pricing officielles de chaque provider
    COST_PER_1M = {
        # ── Anthropic (via Mammoth ou direct) ──
        "claude-haiku-4-5-20251001":  {"input": 0.80,  "output": 4.00},   # Claude Haiku 4.5
        "claude-haiku":               {"input": 0.80,  "output": 4.00},   # alias
        "claude-sonnet-4-5":          {"input": 3.00,  "output": 15.00},  # Claude Sonnet 4.5
        "claude-sonnet-4-5-20250929": {"input": 3.00,  "output": 15.00},  # alias
        "claude-sonnet":              {"input": 3.00,  "output": 15.00},  # alias
        "claude-opus-4-5":            {"input": 15.00, "output": 75.00},  # Claude Opus 4.5
        "claude-opus":                {"input": 15.00, "output": 75.00},  # alias
        # ── OpenAI (via Mammoth ou direct) ──
        "gpt-4o-mini":                {"input": 0.15,  "output": 0.60},   # GPT-4o mini
        "gpt-4o":                     {"input": 2.50,  "output": 10.00},  # GPT-4o
        "o1-mini":                    {"input": 3.00,  "output": 12.00},  # o1-mini
        "o1":                         {"input": 15.00, "output": 60.00},  # o1
        # ── Google (via Mammoth ou direct) ──
        "gemini-2.5-flash-image":     {"input": 0.075, "output": 0.30},   # Gemini 2.5 Flash
        "gemini-2.0-flash":           {"input": 0.075, "output": 0.30},   # Gemini 2.0 Flash
        "gemini-flash":               {"input": 0.075, "output": 0.30},   # alias
        "gemini-3.1-pro-preview":     {"input": 1.25,  "output": 5.00},   # Gemini 3.1 Pro
        "gemini-3-pro-image-preview": {"input": 1.25,  "output": 5.00},   # Gemini 3 Pro Image
        "gemini-pro":                 {"input": 1.25,  "output": 5.00},   # alias
        # ── xAI Grok (via Mammoth) ──
        "grok-4-1-fast":              {"input": 3.00,  "output": 15.00},  # Grok 4 Fast
        "grok":                       {"input": 3.00,  "output": 15.00},  # alias
        # ── Perplexity (via Mammoth) ──
        "sonar-pro":                  {"input": 3.00,  "output": 15.00},  # Sonar Pro
        "perplexity":                 {"input": 3.00,  "output": 15.00},  # alias
        # ── Groq (fallback direct) ──
        "llama-3.3-70b-versatile":    {"input": 0.59,  "output": 0.79},   # Llama 3.3 70B
        "llama-3.1-8b-instant":       {"input": 0.05,  "output": 0.08},   # Llama 3.1 8B
        # ── Mistral (fallback direct) ──
        "mistral-large-latest":       {"input": 2.00,  "output": 6.00},   # Mistral Large
        "mistral-small":              {"input": 0.10,  "output": 0.30},   # Mistral Small
        # ── Mammoth IA tarif générique (quand modèle non reconnu) ──
        "mammouth":                   {"input": 1.00,  "output": 4.00},   # moyen pondéré Mammoth
        "mammoth":                    {"input": 1.00,  "output": 4.00},   # alias
    }
    try:
        from models import ApiCost
        rates = COST_PER_1M.get(model, COST_PER_1M.get(provider, {"input": 1.0, "output": 3.0}))
        estimated = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000

        # FIX: Utiliser engine directement pour éviter les problèmes de session en prod
        from database import engine
        from sqlalchemy.ext.asyncio import AsyncSession as _AS
        from sqlalchemy.orm import sessionmaker as _sm
        _factory = _sm(engine, class_=_AS, expire_on_commit=False)
        async with _factory() as session:
            async with session.begin():
                session.add(ApiCost(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    provider=provider,
                    model=model,
                    mode=mode,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost_eur=round(estimated, 6),
                    credits_charged=credits_charged,
                ))
    except Exception as e:
        logger.warning(f"_log_api_cost failed: {e}")
        try:
            from utils import log_system_event
            log_system_event("api_cost_error", str(e)[:200], "error")
        except Exception:
            pass


@chat_router.post("/send")
async def send_message(request: ChatRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Input validation — max 500KB message to prevent abuse
    if len(request.message) > 500_000:
        raise HTTPException(status_code=400, detail="Message trop long (max 500 000 caracteres)")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Le message ne peut pas etre vide")
    # Validate mode
    valid_modes = {"fast", "pro", "quick", "advanced", "gemini", "grok", "perplexity", "image", "agent", "byok"}
    if request.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Mode invalide: {request.mode}")

    mode = request.mode
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Smart Routing: get credit costs from admin config (or use defaults)
    config = load_admin_config()
    credit_costs = config.get("credit_costs", {"fast": 2, "quick": 1, "pro": 4, "advanced": 4, "gemini": 3, "grok": 3, "perplexity": 4, "image": 8, "agent": 60})
    credits_required = credit_costs.get(mode, 0)

    total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
    if mode != "agent" and total_credits < credits_required:
        raise HTTPException(status_code=402, detail="Crédits insuffisants")
    if mode == "agent":
        # Calculer le vrai coût AVANT l'envoi pour éviter l'erreur en plein streaming
        _task_type_pre = classify_task_type(request.message)
        _credits_needed_pre = estimate_agent_credits(_task_type_pre)
        if total_credits < _credits_needed_pre:
            raise HTTPException(
                status_code=402,
                detail=f"Crédits insuffisants pour cette tâche Agent ({total_credits}/{_credits_needed_pre} crédits requis — niveau {_task_type_pre})"
            )

    # Get or create conversation — créer immédiatement pour que l'onglet apparaisse
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if not conversation:
        # Créer la conversation MAINTENANT pour que l'onglet sidebar apparaisse immédiatement
        init_title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        conversation = Conversation(
            id=conversation_id,
            user_id=user.id,
            title=init_title,
            mode=mode,
            messages=[]
        )
        db.add(conversation)
        try:
            await db.commit()
            await db.refresh(conversation)
        except Exception:
            await db.rollback()
    # Charger TOUS les messages depuis la DB — rien n'est supprimé
    # La compression intelligente (comme Claude.ai) sera appliquée
    # dans _smart_context() au moment de l'envoi à l'API IA
    _all_msgs = conversation.messages if conversation and conversation.messages else []
    messages = list(_all_msgs)

    # Save a clean display version of the user message (without extracted file contents)
    import re as _re_msg
    display_msg = request.message
    # Remove extracted text from [Fichier: xxx]\n...content...
    display_msg = _re_msg.sub(
        r'\[Fichier:\s*([^\]]+)\]\n[\s\S]*?(?=\[Fichier:|\[Image jointe:|\[Fichier joint:|\[Avertissement:|Message utilisateur:|$)',
        lambda m: f'📎 {m.group(1)}\n', display_msg
    )
    display_msg = _re_msg.sub(r'\[Image jointe:\s*([^\]]+)\]', r'📎 \1', display_msg)
    display_msg = _re_msg.sub(r'\[Fichier joint:\s*([^\]]+)\]', r'📎 \1', display_msg)
    display_msg = _re_msg.sub(r'\[Avertissement:[^\]]*\]', '', display_msg)
    display_msg = _re_msg.sub(r'^Message utilisateur:\s*', '', display_msg, flags=_re_msg.MULTILINE)
    display_msg = _re_msg.sub(r'^Analyse et traite ce fichier\.?\s*$', '', display_msg, flags=_re_msg.MULTILINE)
    display_msg = display_msg.strip() or request.message[:200]

    messages.append({"role": "user", "content": display_msg, "credit_cost": credits_required, "mode": mode})

    # Process file attachments - build content for multimodal messages
    file_contents = []
    # Vision depuis extension Chrome : image/screenshot en base64
    if getattr(request, 'image_b64', None):
        mime = getattr(request, 'image_mime', 'image/png') or 'image/png'
        file_contents.append({"type": "image", "data": request.image_b64, "mime": mime})
    if getattr(request, 'screenshot_b64', None):
        file_contents.append({"type": "image", "data": request.screenshot_b64, "mime": "image/png"})
    if request.file_ids:
        logger.info(f"Processing file_ids: {request.file_ids}")
        import io as _io_send, base64 as _b64_send
        from models import UploadedFile as _UF
        from storage import get_object as _get_object
        for fid in request.file_ids:
            _uf_res = await db.execute(select(_UF).where(_UF.id == fid))
            rec = _uf_res.scalar_one_or_none()
            if not rec:
                logger.warning(f"File not found for id: {fid}")
                continue
            fname = rec.filename
            ext = os.path.splitext(fname)[1].lower()
            try:
                raw_bytes, _ = await _get_object(rec.storage_path)
            except Exception as ge:
                logger.warning(f"storage get failed {fid}: {ge}")
                file_contents.append({"type": "text", "data": f"[Fichier joint indisponible: {fid}]"})
                continue
            if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                b64 = _b64_send.b64encode(raw_bytes).decode()
                mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}[ext.lstrip(".")]
                file_contents.append({"type": "image", "data": b64, "mime": mime})
            elif ext == ".pdf":
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(_io_send.BytesIO(raw_bytes))
                    text = ""
                    for page in reader.pages:
                        text += (page.extract_text() or "") + "\n"
                    if text.strip():
                        file_contents.append({"type": "text", "data": f"[Contenu du PDF {fname}]:\n{text[:15000]}"})
                    else:
                        b64_data = _b64_send.b64encode(raw_bytes).decode()
                        file_contents.append({"type": "image", "data": b64_data, "mime": "application/pdf"})
                except Exception as pdf_err:
                    logger.warning(f"PDF extraction error: {pdf_err}")
                    file_contents.append({"type": "text", "data": f"[Fichier PDF joint: {fid}]"})
            elif ext == ".docx":
                try:
                    from docx import Document as DocxDocument
                    doc = DocxDocument(_io_send.BytesIO(raw_bytes))
                    text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                    file_contents.append({"type": "text", "data": f"[Contenu du fichier {fname}]:\n{text[:15000]}"})
                except Exception as docx_err:
                    logger.warning(f"DOCX extraction error: {docx_err}")
                    file_contents.append({"type": "text", "data": f"[Fichier Word joint: {fid}]"})
            elif ext in [".xlsx", ".xls"]:
                try:
                    from openpyxl import load_workbook
                    wb = load_workbook(_io_send.BytesIO(raw_bytes))
                    text = ""
                    for sheet_name in wb.sheetnames:
                        ws = wb[sheet_name]
                        text += f"\n[Feuille: {sheet_name}]\n"
                        for row in ws.iter_rows(values_only=True):
                            text += " | ".join([str(c) if c is not None else "" for c in row]) + "\n"
                    file_contents.append({"type": "text", "data": f"[Contenu du fichier {fname}]:\n{text[:15000]}"})
                except Exception as xlsx_err:
                    logger.warning(f"Excel extraction error: {xlsx_err}")
                    file_contents.append({"type": "text", "data": f"[Fichier Excel joint: {fid}]"})
            elif ext == ".zip":
                try:
                    import zipfile as _zf
                    _zbio = _io_send.BytesIO(raw_bytes)
                    if _zf.is_zipfile(_zbio):
                        with _zf.ZipFile(_zbio, "r") as zfr:
                            znames = zfr.namelist()
                            code_exts = {'.py', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.rb', '.php', '.java', '.go', '.rs', '.swift', '.kt', '.cs'}
                            config_exts = {'.json', '.yaml', '.yml', '.toml', '.cfg', '.ini', '.env', '.sh', '.xml', '.sql', '.html', '.css', '.scss'}
                            doc_exts = {'.md', '.txt', '.csv', '.rst'}
                            all_exts = code_exts | config_exts | doc_exts
                            skip_parts = {'node_modules', '.git', '__pycache__', '.next', 'dist', 'build', '.venv', '.cache', 'vendor'}
                            def zprio(n):
                                e = os.path.splitext(n)[1].lower()
                                return 0 if e in code_exts else (1 if e in config_exts else 2)
                            candidates = []
                            for zn in znames:
                                if zn.endswith('/'): continue
                                parts = zn.replace('\\', '/').split('/')
                                if any(sd in parts for sd in skip_parts): continue
                                if os.path.splitext(zn)[1].lower() in all_exts:
                                    candidates.append(zn)
                            candidates.sort(key=zprio)
                            zip_text = f"Archive ZIP: {fname} ({len(znames)} fichiers)\n"
                            total_chars = 0
                            read_count = 0
                            for zn in candidates:
                                try:
                                    raw = zfr.read(zn)
                                    try:
                                        fc = raw.decode('utf-8')
                                    except UnicodeDecodeError:
                                        continue
                                    if fc[:20].startswith('%PDF') or '\x00' in fc[:200]:
                                        continue
                                    fc = fc[:15000]
                                    zip_text += f"\n--- FICHIER: {zn} ---\n{fc}\n"
                                    total_chars += len(fc)
                                    read_count += 1
                                    if total_chars >= 200000:
                                        zip_text += f"\n[... {len(candidates) - read_count} fichiers restants tronques ...]\n"
                                        break
                                except Exception:
                                    pass
                            file_contents.append({"type": "text", "data": zip_text})
                    else:
                        file_contents.append({"type": "text", "data": f"[Fichier ZIP invalide: {fid}]"})
                except Exception as zip_err:
                    logger.warning(f"ZIP extraction error: {zip_err}")
                    file_contents.append({"type": "text", "data": f"[Fichier ZIP joint: {fid}]"})
            else:
                try:
                    text = raw_bytes.decode("utf-8", errors="replace")[:15000]
                    file_contents.append({"type": "text", "data": f"[Contenu du fichier {fname}]:\n{text}"})
                except Exception:
                    file_contents.append({"type": "text", "data": f"[Fichier joint: {fid}]"})
        logger.info(f"Total file_contents prepared: {len(file_contents)}")

    async def generate_response():
        try:
            if mode == "byok":
                yield f"data: {json.dumps({'error': 'Mode BYOK desactive. Utilisez Mammoth IA Fast ou Pro.'})}\n\n"
                return

            elif mode in ["fast", "pro", "quick", "advanced"]:
                # Fast/Pro via Mammoth IA (Claude models)
                mammoth_key = os.environ.get('MAMMOTH_API_KEY', '')
                if not mammoth_key:
                    asyncio.ensure_future(log_event(
                        'ERROR', 'chat', 'MAMMOTH_API_KEY manquante — service IA indisponible',
                        action='chat_request', user_id=user.id, user_email=user.email,
                        details={'mode': mode, 'fix': 'Ajouter MAMMOTH_API_KEY dans les variables Railway'}
                    ))
                    yield f"data: {json.dumps({'error': 'Service IA indisponible. Contactez le support ou vérifiez la configuration dans Admin → API de secours.'})}\n\n"
                    return

                mammoth_model = "claude-haiku-4-5-20251001" if mode in ["fast", "quick"] else "claude-sonnet-4-5"
                # Use credit costs from admin config (consistent with initial check)
                actual_credits = credits_required or credit_costs.get(mode, 2)

                # Build messages for Mammoth IA (OpenAI format)
                # Construire le system prompt avec les notes du dossier si présentes
                base_system = """Tu es Zayado IA — assistant IA specialise pour les professionnels independants : freelances, auto-entrepreneurs, consultants, coaches, artisans, TPE/PME.

Tu n'es PAS un assistant generaliste. Tu parles a des pros qui ont des enjeux concrets : rentabilite, clients, tresorerie, organisation, temps, visibilite.

═══════════════════════════════════════════════════
TON POSITIONNEMENT
═══════════════════════════════════════════════════

TU AIDES CONCRETEMENT sur :
- Finances : calcul revenu net, seuil de rentabilite, tarif horaire, devis
- Clients : propositions commerciales, relances, contrats, negociation
- Organisation : gestion du temps, priorisation, outils, process
- Communication : LinkedIn, contenu, mails pros, personal branding
- Juridique/fiscal : statuts, charges, TVA, auto-entrepreneur (sans conseil officiel)
- Digital : site web, SEO, reseaux, automatisation

TU N'ES PAS fait pour :
- Les conversations de loisirs ou topics generaux sans lien pro
- Les demandes scolaires basiques (exercices de maths, etc.)
Si hors sujet : oriente gentiment vers le contexte professionnel.

TON STYLE — CRITIQUE :
- JAMAIS de préambule : ne dis jamais "Je vais...", "Voici...", "Bien sûr...", "Voici une version..."
- Commence DIRECTEMENT par la réponse ou le contenu demandé
- Direct, concret, sans jargon inutile
- Donne des chiffres, des exemples, des templates
- Parle comme un associé expérimenté, pas comme un chatbot
- Détecte la langue et réponds TOUJOURS dans cette langue
- Quand tu génères un fichier : ne le précède pas d'un long texte explicatif
- Si tu corriges un texte : commence directement par la version corrigée
- RÉPONSES COURTES : max 3-5 paragraphes sauf si le sujet nécessite plus
- Ne détaille PAS le code source fichier par fichier — résume en bullet points

═══════════════════════════════════════════════════
QUALITE DU CODE GENERE — REGLES ABSOLUES
═══════════════════════════════════════════════════

Quand tu génères du code (Python, JavaScript, HTML, SQL, etc.) :

✅ TOUJOURS :
- Écrire du code COMPLET et FONCTIONNEL — jamais de "# TODO" ou "# à compléter"
- Inclure les imports/dépendances nécessaires en haut du fichier
- Ajouter des commentaires clairs sur les parties complexes
- Gérer les cas d'erreur avec try/except ou équivalent
- Respecter les conventions du langage (PEP8 pour Python, camelCase pour JS, etc.)
- Tester mentalement le code avant de le donner — vérifier la logique
- Pour les fonctions : inclure les types de paramètres et valeurs de retour
- Pour les APIs : inclure les headers, codes d'erreur et exemples de réponse

❌ JAMAIS :
- Laisser des placeholders comme "YOUR_API_KEY", "VOTRE_TOKEN", "REMPLACEZ_ICI" sans explication
- Donner du pseudo-code quand du vrai code est demandé
- Tronquer le code avec "... (suite similaire)"
- Mélanger plusieurs langages dans un même bloc sans l'indiquer
- Oublier les guillemets, parenthèses ou accolades fermantes

FORMAT DU CODE :
- Toujours utiliser des blocs ```langage pour afficher le code
- Pour les fichiers longs : diviser en sections logiques avec des commentaires de séparation
- Indiquer le nom du fichier en commentaire en haut : # fichier: nom.py

═══════════════════════════════════════════════════
CAPACITES TECHNIQUES DISPONIBLES
═══════════════════════════════════════════════════

📁 FICHIERS : ZIP, Word, PDF, Excel lus automatiquement — ne jamais demander de copier-coller
📸 IMAGES : analyses visuelles (screenshots, schemas, captures)
🔍 MODE PERPLEXITY : recherche web temps reel
🤖 MODE AGENT : navigation Chrome reelle (via extension Zayado) — tu PEUX voir l'ecran de l'utilisateur via l'extension Chrome
🧠 MEMOIRE SESSION : preferences et contexte retenus durant la conversation
🌐 EXTENSION CHROME : l'extension Zayado permet de capturer le contenu de la page active de l'utilisateur. Si du contenu de page est fourni, c'est que tu VOIS ce que l'utilisateur voit.

IMPORTANT : Si l'utilisateur demande "tu vois mon ecran ?" ou "prends la main" → OUI, grace a l'extension Chrome tu peux voir le contenu de sa page. Confirme et aide.

IMPORTANT NAVIGATION WEB : Si l'utilisateur demande de chercher sur internet, d'acceder a un site web, ou de faire une recherche en ligne :
- NE JAMAIS dire "utilise l'extension Chrome" ou "installe l'extension" ou "telecharge l'extension"
- DIRE : "Pour effectuer une recherche web en temps reel, utilisez le mode Perplexity (bouton Perplexity dans la barre de modes en haut) ou cliquez sur le bouton Web dans la barre de chat."
- En mode Perplexity, tu PEUX effectuer des recherches web reelles — utilise cette capacite directement sans rediriger vers l'extension.

═══════════════════════════════════════════════════
CORRECTION DE FICHIERS ZIP
═══════════════════════════════════════════════════

Quand l'utilisateur envoie un ZIP et demande des corrections :

ETAPE 1 — ANALYSE RAPIDE (max 10 lignes) :
"J'ai analysé [nom du projet]. Problèmes trouvés :"
- Bug 1 : [fichier] — description courte
- Bug 2 : [fichier] — description courte
(pas de code source ici, juste les résumés)

ETAPE 2 — CORRECTIONS SILENCIEUSES (le système crée le ZIP) :
[CORRECTED_FILE:chemin/exact/fichier.ext]
contenu COMPLET corrigé du fichier
[/CORRECTED_FILE]
Répète pour chaque fichier. NE MONTRE PAS le code à l'utilisateur.

ETAPE 3 — CONFIRMATION COURTE :
"✅ [N] fichiers corrigés. Téléchargez le ZIP ci-dessous."

IMPORTANT : Le contenu entre [CORRECTED_FILE] est traité par le système et NE s'affiche PAS dans le chat. L'utilisateur ne voit que le résumé de l'étape 1 et la confirmation de l'étape 3.

═══════════════════════════════════════════════════
GENERATION DE FICHIERS — REGLES ABSOLUES
═══════════════════════════════════════════════════

⚠️ INTERDIT ABSOLU — Ne jamais dire :
- "Je ne peux pas générer de fichier .zip"
- "Je ne peux pas envoyer de fichier binaire"
- "Je ne suis pas capable d'envoyer des fichiers"
- "Les corrections sont prêtes à être appliquées manuellement"
- Toute formulation suggérant une limite sur les fichiers

TU PEUX et DOIS générer des fichiers. Le système les traite et les envoie automatiquement.

[GENERATE_FILE:format=docx,filename=nom]
contenu
[/GENERATE_FILE]
Formats : docx, txt, zip, xlsx

Après génération : "✅ Fichier prêt — téléchargez-le ci-dessous."

═══════════════════════════════════════════════════
MESSAGES D'ERREUR
═══════════════════════════════════════════════════

Toujours : cause precise + solution actionnable.
Jamais : "une erreur est survenue" sans contexte."""

                # Injecter la mémoire persistante de l'utilisateur
                user_memory_ctx = ""
                try:
                    mem_raw = user.memory or "{}"
                    mem = json.loads(mem_raw) if isinstance(mem_raw, str) else (mem_raw or {})
                    mem_parts = []
                    if mem.get("about_me"):       mem_parts.append(f"A PROPOS DE L'UTILISATEUR: {mem['about_me']}")
                    if mem.get("professional_context"): mem_parts.append(f"CONTEXTE PRO: {mem['professional_context']}")
                    if mem.get("writing_style"):  mem_parts.append(f"STYLE DE REPONSE ATTENDU: {mem['writing_style']}")
                    if mem.get("preferences"):    mem_parts.append(f"PREFERENCES: {mem['preferences']}")
                    if mem_parts:
                        user_memory_ctx = "\n\nMEMOIRE UTILISATEUR (respecter en toutes circonstances):\n" + "\n".join(mem_parts)
                except Exception as mem_err:
                    logger.warning(f"Memory parsing error: {mem_err}")

                base_system = base_system + user_memory_ctx

                # Injecter la mémoire vectorielle (souvenirs sémantiques)
                vector_memory_ctx = ""
                try:
                    from routes.memory import retrieve_relevant_memories
                    _user_msg = request.message or ""
                    if _user_msg and len(_user_msg) > 10:
                        vector_memory_ctx = await retrieve_relevant_memories(user.id, _user_msg, db, limit=3, threshold=0.35)
                        if vector_memory_ctx:
                            vector_memory_ctx = "\n\n" + vector_memory_ctx
                except Exception as vec_err:
                    logger.warning(f"Vector memory retrieval error: {vec_err}")

                base_system = base_system + vector_memory_ctx

                # Enrichir avec les notes du dossier actif
                folder_context = ""
                conversation = await db.get(Conversation, request.conversation_id) if request.conversation_id else None
                if conversation and conversation.folder_id:
                    folder = await db.get(Folder, conversation.folder_id)
                    if folder:
                        parts = []
                        if folder.ai_intro:
                            parts.append(f"INTRODUCTION DOSSIER: {folder.ai_intro}")
                        if folder.knowledge_notes:
                            parts.append(f"NOTES DE CONNAISSANCE: {folder.knowledge_notes}")
                        if parts:
                            folder_context = "\n\n" + "\n\n".join(parts)

                # Appliquer la compression de contexte intelligente (comme Claude.ai)
                _raw_msgs = [m for m in messages if m["role"] in ["user", "assistant"]]
                _smart_msgs = await _smart_context(
                    _raw_msgs,
                    mammoth_key=os.environ.get('MAMMOTH_API_KEY', ''),
                    mammoth_model=mammoth_model
                )
                mammoth_msgs = [{"role": "system", "content": base_system + folder_context}]
                for m in _smart_msgs:
                    mammoth_msgs.append({"role": m["role"], "content": m["content"]})

                # Add file content to the last user message (multimodal support)
                if file_contents and mammoth_msgs:
                    has_images = any(fc["type"] == "image" for fc in file_contents)
                    if has_images:
                        user_content = []
                        for fc in file_contents:
                            if fc["type"] == "image":
                                mime = fc.get("mime", "image/png")
                                user_content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{fc['data']}"}})
                            else:
                                user_content.append({"type": "text", "text": fc["data"]})
                        user_content.append({"type": "text", "text": mammoth_msgs[-1]["content"]})
                        mammoth_msgs[-1]["content"] = user_content
                    else:
                        extra_text = "\n".join(fc["data"] for fc in file_contents if fc["type"] == "text")
                        if extra_text:
                            mammoth_msgs[-1]["content"] = extra_text + "\n" + mammoth_msgs[-1]["content"]

                async with httpx.AsyncClient(timeout=120.0) as http_client:
                    full_response = ""
                    _mammoth_ok = False
                    _streaming_abort.pop(conversation_id, None)

                    # Retry loop: 2 attempts for transient Mammoth errors (502/503/504)
                    for _attempt in range(2):
                        if _mammoth_ok:
                            break
                        try:
                            logger.info(f"Sending to Mammoth (attempt {_attempt+1}/2): model={mammoth_model}, msgs={len(mammoth_msgs)}")
                            async with http_client.stream(
                                "POST",
                                "https://api.mammouth.ai/v1/chat/completions",
                                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                                json={"model": mammoth_model, "messages": mammoth_msgs, "stream": True, "max_tokens": 16384}
                            ) as response:
                                logger.info(f"Mammoth response status: {response.status_code}")
                                if response.status_code == 200:
                                    async for line in response.aiter_lines():
                                        if _streaming_abort.get(conversation_id):
                                            _streaming_abort.pop(conversation_id, None)
                                            full_response += "\n\n[Generation arretee par l'utilisateur]"
                                            yield f"data: {json.dumps({'content': chr(10)+chr(10)+'*[Generation arretee]*'})}\n\n"
                                            break
                                        if line.startswith("data: "):
                                            data_str = line[6:]
                                            if data_str == "[DONE]":
                                                break
                                            try:
                                                chunk_data = json.loads(data_str)
                                                content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                                if content:
                                                    full_response += content
                                                    yield f"data: {json.dumps({'content': content})}\n\n"
                                            except json.JSONDecodeError:
                                                continue
                                    _mammoth_ok = True
                                elif response.status_code in (502, 503, 504):
                                    _err = b""
                                    async for c in response.aiter_bytes():
                                        _err += c
                                    logger.warning(f"Mammoth {response.status_code} (attempt {_attempt+1}/2): {_err[:200]}")
                                    if _attempt == 0:
                                        await asyncio.sleep(2)
                                else:
                                    error_text = ""
                                    async for c in response.aiter_bytes():
                                        error_text += c.decode(errors='replace')
                                    logger.error(f"Mammoth API error: {error_text[:500]}")
                                    yield f"data: {json.dumps({'content': f'Erreur API ({response.status_code})'})}\n\n"
                                    return
                        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as conn_err:
                            logger.warning(f"Mammoth connection error (attempt {_attempt+1}/2): {conn_err}")
                            asyncio.ensure_future(log_event(
                                'WARNING', 'chat', f'Mammoth connexion échouée (tentative {_attempt+1}/2)',
                                action='mammoth_connect_error', user_id=user.id, user_email=user.email,
                                details={'error': str(conn_err), 'mode': mode, 'attempt': _attempt+1}
                            ))
                            if _attempt == 0:
                                await asyncio.sleep(2)

                    # Fallback to configured backup API if Mammoth failed completely
                    if not _mammoth_ok and not full_response:
                        try:
                            _fb_cfg = load_admin_config().get("fallback_api", {})
                            _fb_enabled = _fb_cfg.get("enabled", True)
                            # Nouvelle structure : clés par provider
                            _fb_providers_cfg = _fb_cfg.get("providers", {})
                            
                            # Sélection intelligente du provider selon le mode demandé
                            # Mode fast/quick/pro/advanced → Claude → fallback Anthropic
                            # Mode gemini → Google
                            # Mode grok → Groq
                            _mode_provider_map = {
                                "fast": ["anthropic", "openai", "groq", "mistral"],
                                "quick": ["anthropic", "openai", "groq", "mistral"],
                                "pro": ["anthropic", "openai", "groq", "mistral"],
                                "advanced": ["anthropic", "openai", "groq", "mistral"],
                                "gemini": ["google", "anthropic", "openai"],
                                "grok": ["groq", "anthropic", "openai"],
                                "perplexity": ["groq", "anthropic", "openai"],
                            }
                            _preferred_providers = _mode_provider_map.get(mode, ["anthropic", "openai", "google", "groq"])
                            
                            # Trouver le premier provider avec une clé configurée
                            _fb_provider = None
                            _fb_key = None
                            for _prov in _preferred_providers:
                                _prov_key = _fb_providers_cfg.get(_prov, {}).get("api_key", "")
                                if _prov_key:
                                    _fb_provider = _prov
                                    _fb_key = _prov_key
                                    break
                            
                            # Fallback legacy : ancienne config provider unique
                            if not _fb_key:
                                _fb_provider = _fb_cfg.get("provider", "emergent")
                                _fb_key = _fb_cfg.get("api_key", "") or os.environ.get('EMERGENT_LLM_KEY', '')
                            
                            _fb_model_cfg = _fb_providers_cfg.get(_fb_provider, {}).get("model", "") if _fb_provider else _fb_cfg.get("model", "")

                            if not _fb_enabled or not _fb_key:
                                asyncio.ensure_future(log_event(
                                    'ERROR', 'chat', 'Mammoth échoué + fallback désactivé — service indisponible',
                                    action='service_unavailable', user_id=user.id, user_email=user.email,
                                    details={'mode': mode, 'fallback_enabled': _fb_enabled, 'has_key': bool(_fb_key),
                                             'configured_providers': list(_fb_providers_cfg.keys()),
                                             'fix': 'Activer le fallback API dans Admin → API de secours et configurer les clés'}
                                ))
                                yield f"data: {json.dumps({'error': 'Service IA temporairement indisponible. Notre équipe a été notifiée. Veuillez réessayer dans quelques minutes.'})}\n\n"
                                return

                            logger.info(f"Mammoth down — fallback to {_fb_provider}")
                            
                            # ── EMAIL ALERTE MODE SURVIE ──
                            try:
                                _alert_email = load_admin_config().get("fallback_alert_email", "admin@zayado.net")
                                if _alert_email:
                                    _now = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')
                                    _html = f"""
                                    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
                                      <div style="background:#C7372F;color:white;padding:1rem 1.5rem;border-radius:8px 8px 0 0">
                                        <h2 style="margin:0">⚠️ Extension IA — Mode Survie Activé</h2>
                                      </div>
                                      <div style="background:#FEF2F2;border:1px solid #FECACA;padding:1.5rem;border-radius:0 0 8px 8px">
                                        <p><strong>Date :</strong> {_now}</p>
                                        <p><strong>Mammoth IA</strong> est inaccessible (erreur 502/503/504).</p>
                                        <p><strong>Basculement automatique vers :</strong> {_fb_provider.upper()}</p>
                                        <p><strong>Mode chat :</strong> {mode}</p>
                                        <p><strong>Utilisateur :</strong> {user.email}</p>
                                        <hr style="border:1px solid #FECACA;margin:1rem 0">
                                        <p style="color:#6b7280;font-size:0.875rem">
                                          Action requise : Vérifiez le solde de votre compte Mammoth IA sur <a href="https://mammouth.ai/app/account/api">mammouth.ai/app/account/api</a> 
                                          et rechargez si nécessaire.<br>
                                          <a href="https://app.zayado.net/admin#fallback-api">Voir config Admin → API Secours</a>
                                        </p>
                                      </div>
                                    </div>"""
                                    asyncio.ensure_future(
                                        asyncio.get_event_loop().run_in_executor(
                                            None, send_brevo_email,
                                            _alert_email, "Admin Zayado",
                                            f"⚠️ Mode Survie Activé — Mammoth indisponible ({_now})", _html
                                        )
                                    )
                            except Exception as _mail_err:
                                logger.warning(f"Fallback alert email failed: {_mail_err}")
                            
                            yield f"data: {json.dumps({'content': '*[Service principal indisponible — basculement automatique...]*' + chr(10) + chr(10)})}\n\n"

                            _last = mammoth_msgs[-1]["content"] if mammoth_msgs else request.message
                            if isinstance(_last, list):
                                _last = " ".join(i.get("text", "") for i in _last if isinstance(i, dict) and i.get("type") == "text")
                            _last = str(_last)[:12000]

                            if _fb_provider == "openai":
                                async with httpx.AsyncClient(timeout=60.0) as _fb_http:
                                    _fb_m = _fb_model_cfg or ("gpt-4o" if mode in ["pro", "advanced"] else "gpt-4o-mini")
                                    _fb_r = await _fb_http.post(
                                        "https://api.openai.com/v1/chat/completions",
                                        headers={"Authorization": f"Bearer {_fb_key}", "Content-Type": "application/json"},
                                        json={"model": _fb_m, "messages": [{"role": "system", "content": (base_system + folder_context)[:8000]}, {"role": "user", "content": _last}], "max_tokens": 4096}
                                    )
                                    if _fb_r.status_code == 200:
                                        full_response = _fb_r.json()["choices"][0]["message"]["content"]
                                    else:
                                        raise Exception(f"OpenAI {_fb_r.status_code}: {_fb_r.text[:200]}")
                            elif _fb_provider == "anthropic":
                                async with httpx.AsyncClient(timeout=60.0) as _fb_http:
                                    _fb_m = _fb_model_cfg or ("claude-sonnet-4-5-20250929" if mode in ["pro", "advanced"] else "claude-haiku-4-5-20251001")
                                    _fb_r = await _fb_http.post(
                                        "https://api.anthropic.com/v1/messages",
                                        headers={"x-api-key": _fb_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                                        json={"model": _fb_m, "system": (base_system + folder_context)[:8000], "messages": [{"role": "user", "content": _last}], "max_tokens": 4096}
                                    )
                                    if _fb_r.status_code == 200:
                                        full_response = _fb_r.json()["content"][0]["text"]
                                    else:
                                        raise Exception(f"Anthropic {_fb_r.status_code}: {_fb_r.text[:200]}")
                            elif _fb_provider == "google":
                                async with httpx.AsyncClient(timeout=60.0) as _fb_http:
                                    _fb_m = _fb_model_cfg or "gemini-2.0-flash"
                                    _fb_r = await _fb_http.post(
                                        f"https://generativelanguage.googleapis.com/v1beta/models/{_fb_m}:generateContent?key={_fb_key}",
                                        headers={"Content-Type": "application/json"},
                                        json={"contents": [{"parts": [{"text": (base_system + folder_context)[:4000] + "\n\nUser: " + _last}]}], "generationConfig": {"maxOutputTokens": 4096}}
                                    )
                                    if _fb_r.status_code == 200:
                                        full_response = _fb_r.json()["candidates"][0]["content"]["parts"][0]["text"]
                                    else:
                                        raise Exception(f"Google {_fb_r.status_code}: {_fb_r.text[:200]}")
                            elif _fb_provider in ("mistral", "groq"):
                                _api_urls = {"mistral": "https://api.mistral.ai/v1/chat/completions", "groq": "https://api.groq.com/openai/v1/chat/completions"}
                                _defaults = {"mistral": "mistral-large-latest", "groq": "llama-3.3-70b-versatile"}
                                async with httpx.AsyncClient(timeout=60.0) as _fb_http:
                                    _fb_m = _fb_model_cfg or _defaults[_fb_provider]
                                    _fb_r = await _fb_http.post(
                                        _api_urls[_fb_provider],
                                        headers={"Authorization": f"Bearer {_fb_key}", "Content-Type": "application/json"},
                                        json={"model": _fb_m, "messages": [{"role": "system", "content": (base_system + folder_context)[:8000]}, {"role": "user", "content": _last}], "max_tokens": 4096}
                                    )
                                    if _fb_r.status_code == 200:
                                        full_response = _fb_r.json()["choices"][0]["message"]["content"]
                                    else:
                                        raise Exception(f"{_fb_provider} {_fb_r.status_code}: {_fb_r.text[:200]}")
                            else:
                                # Fallback natif via API Anthropic directe
                                _fb_m = _fb_model_cfg or ("claude-sonnet-4-5-20250929" if mode in ["pro", "advanced"] else "claude-haiku-4-5-20251001")
                                import httpx as _httpx
                                _fb_headers = {"x-api-key": _fb_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
                                _fb_payload = {"model": _fb_m, "system": (base_system + folder_context)[:8000], "messages": [{"role": "user", "content": _last}], "max_tokens": 4096}
                                async with _httpx.AsyncClient(timeout=60) as _fb_client:
                                    _fb_resp = await _fb_client.post("https://api.anthropic.com/v1/messages", headers=_fb_headers, json=_fb_payload)
                                if _fb_resp.status_code == 200:
                                    full_response = _fb_resp.json()["content"][0]["text"]
                                else:
                                    raise Exception(f"Anthropic fallback {_fb_resp.status_code}: {_fb_resp.text[:200]}")

                            yield f"data: {json.dumps({'content': full_response})}\n\n"
                        except Exception as fb_err:
                            logger.error(f"Fallback API error: {fb_err}")
                            yield f"data: {json.dumps({'error': 'Service de secours indisponible. Verifiez la configuration dans Admin.'})}\n\n"
                            return

                    messages.append({"role": "assistant", "content": full_response})

                    # Post-process: handle [CORRECTED_FILE] and [GENERATE_FILE] markers
                    import re as _re
                    import shutil

                    # 1. Handle [CORRECTED_FILE] markers — apply corrections to workspace and re-zip
                    # Regex robuste : accepte les backticks et espaces en début de bloc
                    corrected_blocks = _re.findall(
                        r'\[CORRECTED_FILE:([^\]]+)\]\s*(?:```[^\n]*\n)?(.*?)(?:```\s*)?\[/CORRECTED_FILE\]',
                        full_response, _re.DOTALL
                    )
                    if corrected_blocks:
                        import zipfile as _zipfile
                        import uuid as _uuid

                        # Trouver le workspace ZIP d'origine (si disponible)
                        workspace_id = None
                        if request.file_ids:
                            for fid in request.file_ids:
                                ws_path = os.path.join(WORKSPACES_DIR, fid)
                                if os.path.isdir(ws_path):
                                    workspace_id = fid
                                    break

                        # Créer un dossier de travail temporaire pour le ZIP corrigé
                        out_id = _uuid.uuid4().hex[:12]
                        out_fn = f"projet_corrige_{out_id}.zip"
                        zip_path = os.path.join(UPLOADS_DIR, out_fn)
                        os.makedirs(UPLOADS_DIR, exist_ok=True)

                        corrected_count = 0
                        with _zipfile.ZipFile(zip_path, 'w', _zipfile.ZIP_DEFLATED) as zfw:
                            # Si workspace d'origine disponible : partir de tous ses fichiers
                            if workspace_id:
                                ws_path = os.path.join(WORKSPACES_DIR, workspace_id)
                                # Ajouter tous les fichiers du workspace original
                                for root, dirs, files in os.walk(ws_path):
                                    dirs[:] = [d for d in dirs if d not in {'node_modules', '.git', '__pycache__', '.next', 'dist', 'build', '.venv', '.cache', '.idea'}]
                                    for fname_ws in files:
                                        full_path = os.path.join(root, fname_ws)
                                        arcname = os.path.relpath(full_path, ws_path)
                                        zfw.write(full_path, arcname)

                            # Appliquer les corrections (écrase les fichiers originaux)
                            for fpath_raw, fcontent_raw in corrected_blocks:
                                fpath_clean = fpath_raw.strip().lstrip('/')
                                fcontent_clean = fcontent_raw.strip()

                                # Nettoyer les backticks markdown résiduels
                                if fcontent_clean.startswith("```"):
                                    lines = fcontent_clean.split("\n")
                                    if lines[0].startswith("```"):
                                        lines = lines[1:]
                                    while lines and lines[-1].strip() in ("```", ""):
                                        lines.pop()
                                    fcontent_clean = "\n".join(lines)

                                if fpath_clean and fcontent_clean:
                                    zfw.writestr(fpath_clean, fcontent_clean.encode('utf-8'))
                                    corrected_count += 1
                                    logger.info(f"ZIP correction: {fpath_clean} ({len(fcontent_clean)} chars)")

                        if corrected_count > 0:
                            dl_url = f"/api/uploads/download/{out_fn}"
                            yield f"data: {json.dumps({'file_download': {'url': dl_url, 'filename': out_fn, 'format': 'zip', 'corrected_files': corrected_count}})}\n\n"
                            logger.info(f"Generated corrected ZIP: {out_fn} with {corrected_count} files")
                        else:
                            # Aucun bloc valide — nettoyer
                            try:
                                os.remove(zip_path)
                            except Exception:
                                pass
                            logger.warning("corrected_blocks found but no valid content extracted")

                    # 2. Handle [GENERATE_FILE] markers — create new files from scratch
                    file_blocks = _re.findall(r'\[GENERATE_FILE:format=(\w+),filename=([^\]]+)\](.*?)\[/GENERATE_FILE\]', full_response, _re.DOTALL)
                    for fmt, fname, fcontent in file_blocks:
                        out_path_gen = None
                        try:
                            os.makedirs(UPLOADS_DIR, exist_ok=True)
                            gen_id = str(uuid.uuid4())[:8]
                            fmt_clean = fmt.strip().lower()
                            # Sanitize filename — strip path separators and dangerous chars
                            fname_clean = re.sub(r'[^\w\-. ]', '_', fname.strip())[:80]
                            if not fname_clean:
                                fname_clean = "document"

                            if fmt_clean == "zip":
                                import zipfile as _zipfile
                                out_fn = f"{gen_id}_{fname_clean}.zip"
                                out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                with _zipfile.ZipFile(out_path_gen, 'w', _zipfile.ZIP_DEFLATED) as zfw:
                                    file_parts = _re.split(r'--- FICHIER:\s*(.+?)\s*---\n', fcontent.strip())
                                    if len(file_parts) > 1:
                                        for idx in range(1, len(file_parts), 2):
                                            fp = file_parts[idx].strip()
                                            fd = file_parts[idx + 1] if idx + 1 < len(file_parts) else ""
                                            if fp:
                                                zfw.writestr(fp, fd.strip())
                                    else:
                                        zfw.writestr(f"{fname_clean}.txt", fcontent.strip())

                            elif fmt_clean == "docx":
                                try:
                                    import docx as _docx
                                except ImportError:
                                    logger.warning("[GENERATE_FILE] python-docx non disponible — fallback txt")
                                    fmt_clean = "txt"
                                    out_fn = f"{gen_id}_{fname_clean}.txt"
                                    out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                    with open(out_path_gen, "w", encoding="utf-8") as fw:
                                        fw.write(fcontent.strip())
                                else:
                                    doc = _docx.Document()
                                    doc.add_heading(fname_clean, 0)
                                    for fline in fcontent.strip().split("\n"):
                                        fline = fline.strip()
                                        if not fline: continue
                                        if fline.startswith("# "): doc.add_heading(fline[2:], level=1)
                                        elif fline.startswith("## "): doc.add_heading(fline[3:], level=2)
                                        elif fline.startswith("- ") or fline.startswith("* "): doc.add_paragraph(fline[2:], style="List Bullet")
                                        else: doc.add_paragraph(fline)
                                    out_fn = f"{gen_id}_{fname_clean}.docx"
                                    out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                    doc.save(out_path_gen)

                            elif fmt_clean == "xlsx":
                                # Support xlsx — nouveau format manquant dans l'original
                                try:
                                    import openpyxl as _opxl
                                    wb = _opxl.Workbook()
                                    ws = wb.active
                                    ws.title = fname_clean[:31]
                                    for row_line in fcontent.strip().split("\n"):
                                        if row_line.strip():
                                            cells = [c.strip() for c in row_line.split("|") if c.strip()]
                                            if cells:
                                                ws.append(cells)
                                    out_fn = f"{gen_id}_{fname_clean}.xlsx"
                                    out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                    wb.save(out_path_gen)
                                except ImportError:
                                    logger.warning("[GENERATE_FILE] openpyxl non disponible — fallback csv")
                                    fmt_clean = "txt"
                                    out_fn = f"{gen_id}_{fname_clean}.csv"
                                    out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                    with open(out_path_gen, "w", encoding="utf-8") as fw:
                                        fw.write(fcontent.strip())

                            elif fmt_clean in ("html", "htm"):
                                # FIX HTML — Générer un fichier HTML téléchargeable avec styles
                                out_fn = f"{gen_id}_{fname_clean}.html"
                                out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                html_content = fcontent.strip()
                                # Si le contenu n'a pas de balise <html>, ajouter un wrapper complet
                                if "<html" not in html_content.lower():
                                    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{fname_clean}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; color: #1a1a1a; line-height: 1.6; }}
  h1,h2,h3 {{ color: #0F1B2D; }} table {{ width: 100%; border-collapse: collapse; }} th,td {{ padding: .5rem 1rem; border: 1px solid #e5e7eb; }} th {{ background: #f9fafb; }}
  .zayado-footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; font-size: .75rem; color: #9ca3af; text-align: center; }}
</style>
</head>
<body>
{html_content}
<div class="zayado-footer">Généré par Extension IA by Zayado · {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC</div>
</body>
</html>"""
                                with open(out_path_gen, "w", encoding="utf-8") as fw:
                                    fw.write(html_content)
                            elif fmt_clean in ("md", "markdown"):
                                out_fn = f"{gen_id}_{fname_clean}.md"
                                out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                with open(out_path_gen, "w", encoding="utf-8") as fw:
                                    fw.write(fcontent.strip())
                            elif fmt_clean in ("json",):
                                out_fn = f"{gen_id}_{fname_clean}.json"
                                out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                with open(out_path_gen, "w", encoding="utf-8") as fw:
                                    fw.write(fcontent.strip())
                            elif fmt_clean in ("pptx", "ppt"):
                                out_fn = f"{gen_id}_{fname_clean}.pptx"
                                out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                try:
                                    from pptx import Presentation as _PPT
                                    prs = _PPT()
                                    slides_raw = [s.strip() for s in fcontent.split("---") if s.strip()]
                                    for slide_text in slides_raw[:20]:
                                        slide_layout = prs.slide_layouts[1]
                                        slide = prs.slides.add_slide(slide_layout)
                                        lines = slide_text.strip().split("\n", 1)
                                        slide.shapes.title.text = lines[0].lstrip("#").strip() if lines else ""
                                        if len(lines) > 1:
                                            slide.placeholders[1].text = lines[1].strip()
                                    prs.save(out_path_gen)
                                except Exception:
                                    fmt_clean = "txt"
                                    out_fn = f"{gen_id}_{fname_clean}.txt"
                                    out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                    with open(out_path_gen, "w", encoding="utf-8") as fw:
                                        fw.write(fcontent.strip())
                            else:
                                out_fn = f"{gen_id}_{fname_clean}.txt"
                                out_path_gen = os.path.join(UPLOADS_DIR, out_fn)
                                with open(out_path_gen, "w", encoding="utf-8") as fw:
                                    fw.write(fcontent.strip())

                            if out_path_gen and os.path.isfile(out_path_gen):
                                dl_url = f"/api/uploads/download/{out_fn}"
                                file_size = os.path.getsize(out_path_gen)
                                yield f"data: {json.dumps({'file_download': {'url': dl_url, 'filename': out_fn, 'format': fmt_clean, 'size': file_size}})}\n\n"
                                # FIX CRÉDITS fichiers — déduire les crédits pour HTML/DOCX/XLSX comme pour les images
                                file_credits = {'html': 2, 'htm': 2, 'md': 1, 'json': 1, 'docx': 3, 'xlsx': 3, 'pptx': 4, 'csv': 1, 'txt': 1, 'zip': 0}
                                file_cr = file_credits.get(fmt_clean, 2)
                                if file_cr > 0:
                                    try:
                                        await _deduct_credits(db, user, file_cr, conversation_id, mode=f"file_{fmt_clean}")
                                    except Exception: pass
                                logger.info(f"[GENERATE_FILE] generated: {out_fn} ({file_size} bytes)")

                        except Exception as gen_err:
                            logger.error(f"[GENERATE_FILE] error: {gen_err}")
                            # Cleanup partial file on error
                            if out_path_gen:
                                try: os.remove(out_path_gen)
                                except Exception: pass
                # ── NETTOYER les balises techniques du texte affiche ──────
                import re as _re2
                display_text = full_response
                _pat_gen = r'\[GENERATE_FILE:[^\]]+\].*?\[/GENERATE_FILE\]'
                _pat_cor = r'\[CORRECTED_FILE:[^\]]+\].*?\[/CORRECTED_FILE\]'
                _pat_sep = r'\n---+\n'
                _pat_nl  = r'\n{3,}'
                display_text = _re2.sub(_pat_gen, '', display_text, flags=_re2.DOTALL)
                display_text = _re2.sub(_pat_cor, '', display_text, flags=_re2.DOTALL)
                display_text = _re2.sub(_pat_sep, '\n', display_text)
                display_text = _re2.sub(_pat_nl,  '\n\n', display_text).strip()
                if display_text != full_response:
                    yield 'data: ' + json.dumps({'display_update': display_text}) + '\n\n'
                    # Update saved message with clean text (without [CORRECTED_FILE] blocks)
                    if messages and messages[-1].get("role") == "assistant":
                        messages[-1]["content"] = display_text

                # #37 — Don't deduct if AI returned empty response (API failure mid-stream)
                if not full_response.strip():
                    yield f"data: {json.dumps({'error': 'Erreur: reponse IA vide. Credits non debites.'})}\n\n"
                    return

                # Deduct credits via shared helper (#18 — single deduction path, no duplication)
                await _deduct_credits(db, user, actual_credits, conversation.id if conversation else None, mode=mode)
                # FIX CREDITS: Envoyer le vrai décompte au frontend après la réponse
                yield f"data: {json.dumps({'credit_update': actual_credits, 'mode': mode})}\n\n"

                # Log API cost for profitability tracking
                try:
                    est_input = len(str(mammoth_msgs)) // 3  # ~3 chars/token FR
                    est_output = len(full_response) // 3
                    provider = "mammouth"
                    # Noms exacts pour matcher COST_PER_1M et avoir les vrais tarifs
                    model_name = "claude-haiku-4-5-20251001" if mode in ["fast", "quick"] else "claude-sonnet-4-5"
                    await _log_api_cost(db, user.id, conversation.id if conversation else None, provider, model_name, mode, est_input, est_output, actual_credits)
                except Exception as cost_err:
                    logger.warning(f"Cost logging error: {cost_err}")

            elif mode in ["gemini", "grok", "perplexity", "image"]:
                # Mammoth IA integration - OpenAI-compatible API
                mammoth_key = os.environ.get('MAMMOTH_API_KEY', '')
                if not mammoth_key and mode != "image":
                    yield f"data: {json.dumps({'error': 'Mammoth IA not configured'})}\n\n"
                    return

                # Resolve conversation for credit logging
                conversation = await db.get(Conversation, request.conversation_id) if request.conversation_id else None

                image_model_map = {
                    "nano-banana": "gemini-2.5-flash-image",
                    "stable-diffusion": "gemini-3-pro-image-preview",
                    "gemini-flash": "gemini-2.5-flash-image",
                    "gemini-pro": "gemini-3-pro-image-preview",
                }
                model_map = {
                    "gemini": "gemini-3.1-pro-preview",
                    "grok": "grok-4-1-fast",
                    "perplexity": "sonar-pro",
                    "image": image_model_map.get(request.image_model, "gemini-2.5-flash-image")
                }
                mammoth_model = model_map[mode]
                # Load credit costs from admin config (use cached load_admin_config to avoid blocking I/O per request)
                try:
                    _admin_cfg = load_admin_config()
                    credit_costs = _admin_cfg.get("credit_costs", {"fast": 2, "gemini": 3, "grok": 3, "pro": 4, "perplexity": 4, "image": 8, "agent": 60})
                except Exception as cfg_err:
                    logger.warning(f"Config load error: {cfg_err}")
                    credit_costs = {"fast": 2, "gemini": 3, "grok": 3, "pro": 4, "perplexity": 4, "image": 8, "agent": 60}
                actual_credits = credit_costs.get(mode, 2)

                # Build messages for Mammoth (OpenAI format)
                if mode == "image":
                    mammoth_messages = [{"role": "system", "content": "You are an image generation AI. Generate the requested image. Always produce a visual image in your response."}]
                else:
                    mammoth_messages = [{"role": "system", "content": "Tu es Zayado IA — assistant pro integre dans Chrome. REGLE STYLE : Ne commence JAMAIS par Je vais / Voici / Bien sur / Parfait. Commence DIRECTEMENT par la reponse. Direct, concis, oriente resultat. Detecte la langue et reponds dans cette langue. Style : expert concret, pas chatbot verbeux."}]
                # Compression intelligente du contexte (comme Claude.ai)
                _raw_msgs2 = [m for m in messages if m["role"] in ["user", "assistant"]]
                _smart_msgs2 = await _smart_context(
                    _raw_msgs2,
                    mammoth_key=os.environ.get('MAMMOTH_API_KEY', ''),
                    mammoth_model=mammoth_model
                )
                for m in _smart_msgs2:
                    mammoth_messages.append({"role": m["role"], "content": m["content"]})

                # Add file content to the last user message (multimodal support)
                if file_contents and mammoth_messages:
                    has_images = any(fc["type"] == "image" for fc in file_contents)
                    if has_images:
                        # Build multimodal content array (OpenAI Vision format)
                        user_content = []
                        for fc in file_contents:
                            if fc["type"] == "image":
                                mime = fc.get("mime", "image/png")
                                user_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime};base64,{fc['data']}"}
                                })
                            else:
                                user_content.append({"type": "text", "text": fc["data"]})
                        user_content.append({"type": "text", "text": mammoth_messages[-1]["content"]})
                        mammoth_messages[-1]["content"] = user_content
                    else:
                        extra_text = "\n".join(fc["data"] for fc in file_contents if fc["type"] == "text")
                        if extra_text:
                            mammoth_messages[-1]["content"] = extra_text + "\n" + mammoth_messages[-1]["content"]

                if mode == "image":
                    # Image generation via Mammouth AI
                    import base64 as b64_mod
                    import re as re_mod
                    text_content = ""
                    image_urls = []
                    image_generated = False

                    # Choose model based on user selection
                    img_model_name = mammoth_model  # Uses image_model_map from above
                    logger.info(f"[IMG] Using model: {img_model_name} (user selected: {request.image_model})")

                    try:
                        async with httpx.AsyncClient(timeout=120.0) as http_client:
                            response = await http_client.post(
                                "https://api.mammouth.ai/v1/chat/completions",
                                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                                json={
                                    "model": img_model_name,
                                    "messages": [{"role": "user", "content": request.message}],
                                    "max_tokens": 4096
                                }
                            )
                            print(f"[IMG] Mammouth {img_model_name} status: {response.status_code}")
                            if response.status_code == 200:
                                mdata = response.json()
                                msg_data = mdata.get("choices", [{}])[0].get("message", {})
                                text_content = msg_data.get("content", "") or ""
                                for img in msg_data.get("images", []):
                                    url = img.get("image_url", {}).get("url", "")
                                    if url:
                                        image_urls.append(url)
                                        image_generated = True
                                print(f"[IMG] Images found: {len(image_urls)}")
                            elif response.status_code == 500:
                                # Bug Mammouth: images parfois dans le body d'erreur 500
                                try:
                                    err_text = response.text
                                    data_uris = re_mod.findall(r'data:image/[a-zA-Z]+;base64,[A-Za-z0-9+/=]+', err_text)
                                    if data_uris:
                                        image_urls = data_uris
                                        image_generated = True
                                        print(f"[IMG] Found {len(data_uris)} image(s) in 500 body")
                                        content_match = re_mod.search(r"'content':\s*'((?:[^'\\\\]|\\\\.)*?)'", err_text)
                                        if content_match:
                                            text_content = content_match.group(1)
                                except Exception:
                                    pass
                            else:
                                print(f"[IMG] Error body: {response.text[:500]}")
                                # Fallback : try alternate image model
                                fallback_model = "gemini-3-pro-image-preview" if img_model_name != "gemini-3-pro-image-preview" else "gemini-2.5-flash-image"
                                print(f"[IMG] Trying fallback model: {fallback_model}")
                                response2 = await http_client.post(
                                    "https://api.mammouth.ai/v1/chat/completions",
                                    headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                                    json={
                                        "model": fallback_model,
                                        "messages": [{"role": "user", "content": request.message}],
                                        "max_tokens": 4096
                                    }
                                )
                                if response2.status_code == 200:
                                    mdata = response2.json()
                                    msg_data = mdata.get("choices", [{}])[0].get("message", {})
                                    text_content = msg_data.get("content", "") or ""
                                    for img in msg_data.get("images", []):
                                        url = img.get("image_url", {}).get("url", "")
                                        if url:
                                            image_urls.append(url)
                                            image_generated = True
                    except Exception as me:
                        logger.warning(f"Mammouth image generation failed: {me}")

                    if not image_generated:
                        yield f"data: {json.dumps({'error': 'Impossible de générer l image. Veuillez réessayer.'})}\n\n"
                        return

                    # Build full response with saved images
                    full_response = text_content
                    import re as re_mod2
                    for img_url in image_urls:
                        # Stocker directement la data URL dans la conversation (persistant)
                        if img_url.startswith("data:image/"):
                            try:
                                # Toujours stocker en data URL pour persistance (Railway redémarre)
                                # Si > 1.5MB : recompresser en JPEG 75%
                                MAX_IMG_SIZE = 1_500_000
                                if len(img_url) > MAX_IMG_SIZE:
                                    try:
                                        b64_match = re_mod2.match(r"data:image/(\w+);base64,(.*)", img_url, re_mod2.DOTALL)
                                        if b64_match:
                                            from PIL import Image as _PIL_Image
                                            import io as _io
                                            img_bytes = b64_mod.b64decode(b64_match.group(2))
                                            pil_img = _PIL_Image.open(_io.BytesIO(img_bytes))
                                            out = _io.BytesIO()
                                            pil_img.convert("RGB").save(out, format="JPEG", quality=75, optimize=True)
                                            compressed = "data:image/jpeg;base64," + b64_mod.b64encode(out.getvalue()).decode()
                                            full_response += f"\n\n![Image generee]({compressed})"
                                            logger.info(f"Image compressed: {len(img_url)} → {len(compressed)} bytes")
                                        else:
                                            full_response += f"\n\n![Image generee]({img_url[:MAX_IMG_SIZE]})"
                                    except Exception:
                                        # Fallback: stocker tronquée
                                        full_response += f"\n\n![Image generee]({img_url})"
                                else:
                                    full_response += f"\n\n![Image generee]({img_url})"
                            except Exception as img_save_err:
                                logger.error(f"Error saving image: {img_save_err}")
                                full_response += f"\n\n![Image generee]({img_url})"
                        else:
                            full_response += f"\n\n![Image generee]({img_url})"

                    if not full_response:
                        full_response = "Aucune image generee. Veuillez reessayer."

                    yield f"data: {json.dumps({'content': full_response})}\n\n"
                    messages.append({"role": "assistant", "content": full_response})
                else:
                    # Text generation - streaming with retry + fallback
                    async with httpx.AsyncClient(timeout=60.0) as http_client:
                        full_response = ""
                        _m2_ok = False
                        for _att2 in range(2):
                            if _m2_ok:
                                break
                            try:
                                async with http_client.stream(
                                    "POST",
                                    "https://api.mammouth.ai/v1/chat/completions",
                                    headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                                    json={"model": mammoth_model, "messages": mammoth_messages, "stream": True, "max_tokens": 4096}
                                ) as response:
                                    if response.status_code == 200:
                                        async for line in response.aiter_lines():
                                            if line.startswith("data: "):
                                                data_str = line[6:]
                                                if data_str == "[DONE]":
                                                    break
                                                try:
                                                    chunk_data = json.loads(data_str)
                                                    content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                                    if content:
                                                        full_response += content
                                                        yield f"data: {json.dumps({'content': content})}\n\n"
                                                except json.JSONDecodeError:
                                                    continue
                                        _m2_ok = True
                                    elif response.status_code in (502, 503, 504):
                                        logger.warning(f"Mammoth text {response.status_code} (attempt {_att2+1}/2)")
                                        if _att2 == 0:
                                            await asyncio.sleep(2)
                                    else:
                                        error_text = ""
                                        async for c in response.aiter_bytes():
                                            error_text += c.decode(errors='replace')
                                        logger.error(f"Mammoth text API error: {error_text[:500]}")
                                        yield f"data: {json.dumps({'content': f'Erreur API ({response.status_code})'})}\n\n"
                                        return
                            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as ce:
                                logger.warning(f"Mammoth text conn error (attempt {_att2+1}/2): {ce}")
                                if _att2 == 0:
                                    await asyncio.sleep(2)

                        if not _m2_ok and not full_response:
                            try:
                                _fb2_cfg = load_admin_config().get("fallback_api", {})
                                _fb2_provider = _fb2_cfg.get("provider", "emergent")
                                _fb2_key = _fb2_cfg.get("api_key", "") or os.environ.get('EMERGENT_LLM_KEY', '')
                                _fb2_model_cfg = _fb2_cfg.get("model", "")
                                if not _fb2_key or not _fb2_cfg.get("enabled", True):
                                    yield f"data: {json.dumps({'error': 'Service temporairement indisponible.'})}\n\n"
                                    return
                                logger.info(f"Mammoth text failed — fallback {_fb2_provider}")
                                yield f"data: {json.dumps({'content': '*[Basculement automatique...]*' + chr(10) + chr(10)})}\n\n"
                                _last2 = mammoth_messages[-1]["content"] if mammoth_messages else request.message
                                if isinstance(_last2, list):
                                    _last2 = " ".join(i.get("text", "") for i in _last2 if isinstance(i, dict) and i.get("type") == "text")
                                _last2 = str(_last2)[:12000]

                                if _fb2_provider == "openai":
                                    async with httpx.AsyncClient(timeout=60.0) as _fb2_http:
                                        _fb2_m = _fb2_model_cfg or "gpt-4o"
                                        _fb2_r = await _fb2_http.post("https://api.openai.com/v1/chat/completions",
                                            headers={"Authorization": f"Bearer {_fb2_key}", "Content-Type": "application/json"},
                                            json={"model": _fb2_m, "messages": [{"role": "system", "content": "Tu es Zayado IA. Direct, concis."}, {"role": "user", "content": _last2}], "max_tokens": 4096})
                                        if _fb2_r.status_code == 200:
                                            full_response = _fb2_r.json()["choices"][0]["message"]["content"]
                                        else:
                                            raise Exception(f"OpenAI {_fb2_r.status_code}")
                                elif _fb2_provider == "anthropic":
                                    async with httpx.AsyncClient(timeout=60.0) as _fb2_http:
                                        _fb2_m = _fb2_model_cfg or "claude-sonnet-4-5-20250929"
                                        _fb2_r = await _fb2_http.post("https://api.anthropic.com/v1/messages",
                                            headers={"x-api-key": _fb2_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                                            json={"model": _fb2_m, "system": "Tu es Zayado IA. Direct, concis.", "messages": [{"role": "user", "content": _last2}], "max_tokens": 4096})
                                        if _fb2_r.status_code == 200:
                                            full_response = _fb2_r.json()["content"][0]["text"]
                                        else:
                                            raise Exception(f"Anthropic {_fb2_r.status_code}")
                                else:
                                    # Fallback natif via API Anthropic directe
                                    import httpx as _httpx2
                                    _fb2_headers2 = {"x-api-key": _fb2_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
                                    _fb2_payload2 = {"model": _fb2_model_cfg or "claude-sonnet-4-5-20250929", "system": "Tu es Zayado IA. Direct, concis.", "messages": [{"role": "user", "content": _last2}], "max_tokens": 4096}
                                    async with _httpx2.AsyncClient(timeout=60) as _fb2_client:
                                        _fb2_resp = await _fb2_client.post("https://api.anthropic.com/v1/messages", headers=_fb2_headers2, json=_fb2_payload2)
                                    if _fb2_resp.status_code == 200:
                                        full_response = _fb2_resp.json()["content"][0]["text"]
                                    else:
                                        raise Exception(f"Anthropic fallback2 {_fb2_resp.status_code}")
                                yield f"data: {json.dumps({'content': full_response})}\n\n"
                            except Exception as fb2_err:
                                logger.error(f"Fallback text error: {fb2_err}")
                                yield f"data: {json.dumps({'error': 'Service de secours indisponible.'})}\n\n"
                                return

                        messages.append({"role": "assistant", "content": full_response})

                # #37 — Don't deduct if response empty (API failure)
                if mode != "image" and (not full_response or not full_response.strip()):
                    yield f"data: {json.dumps({'error': 'Erreur: reponse IA vide. Credits non debites.'})}\n\n"
                    return

                # Deduct credits via shared helper (#18 — single deduction path)
                await _deduct_credits(db, user, actual_credits, conversation.id if conversation else None, mode=mode)
                # FIX CREDITS: Envoyer le vrai décompte au frontend après la réponse
                yield f"data: {json.dumps({'credit_update': actual_credits, 'mode': mode})}\n\n"

                # Log API cost for profitability tracking
                try:
                    est_input = len(str(mammoth_messages)) // 3
                    est_output = len(full_response) // 3 if full_response else 0
                    provider_map = {"gemini": "mammouth", "grok": "mammouth", "perplexity": "mammouth", "image": "mammouth"}
                    model_map_cost = {
                        "gemini": "gemini-3.1-pro-preview",
                        "grok": "grok-4-1-fast",
                        "perplexity": "sonar-pro",
                        "image": "gemini-2.5-flash-image",
                    }
                    await _log_api_cost(db, user.id, conversation.id if conversation else None, provider_map.get(mode, "mammouth"), model_map_cost.get(mode, mode), mode, est_input, est_output, actual_credits)
                except Exception as cost_err:
                    logger.warning(f"Cost logging error: {cost_err}")

            elif mode == "agent":
                # Agent IA via Mammoth IA (replaces Manus)
                mammoth_key = os.environ.get('MAMMOTH_API_KEY', '')
                if not mammoth_key:
                    yield f"data: {json.dumps({'error': 'Agent IA non configure'})}\n\n"
                    return

                task_type = classify_task_type(request.message)
                credits_needed = estimate_agent_credits(task_type)
                total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)

                if total_credits < credits_needed:
                    yield f"data: {json.dumps({'error': f'Credits insuffisants ({total_credits}/{credits_needed})'})}\n\n"
                    return

                # Save user credit values before streaming (session may detach)
                user_credits_val = user.credits or 0
                user_bonus_val = user.bonus_credits or 0
                user_purchased_val = user.purchased_credits or 0
                user_id_val = user.id

                model = select_agent_model(task_type)
                specialization = classify_agent_specialization(request.message)
                agent_system = get_agent_system_prompt(specialization)
                spec_label = {"research": "Recherche", "writing": "Redaction", "code": "Code", "analysis": "Analyse", "general": "General"}.get(specialization, "General")
                nl = "\n\n"
                yield f"data: {json.dumps({'content': f'Agent IA ({spec_label}) en cours...' + nl})}\n\n"

                try:
                    # Build context from conversation history
                    context_parts = []
                    for m in messages[:-1]:
                        role_label = "Utilisateur" if m["role"] == "user" else "Assistant"
                        context_parts.append(f"{role_label}: {m['content'][:500]}")

                    agent_prompt = request.message
                    if context_parts:
                        history_ctx = "\n".join(context_parts[-6:])
                        agent_prompt = f"Contexte:\n{history_ctx}\n\nNouvelle demande: {request.message}"

                    # ── Inject file contents into agent prompt (same as fast/pro) ──
                    if file_contents:
                        file_section = "\n\n## FICHIERS JOINTS PAR L'UTILISATEUR\n"
                        has_images = any(fc["type"] == "image" for fc in file_contents)
                        if has_images:
                            file_section += "(Images jointes — analysées en vision)\n"
                        text_parts = [fc["data"] for fc in file_contents if fc["type"] == "text"]
                        if text_parts:
                            file_section += "\n".join(text_parts[:5])  # max 5 files
                        agent_prompt = file_section + "\n\n## DEMANDE\n" + agent_prompt

                    # Enhance specialized prompt with navigation capabilities
                    agent_system = agent_system + """

CAPACITES SUPPLEMENTAIRES (Extension Chrome Zayado) :
- Acces au contenu des pages web en temps reel via l'extension
- Pour toute recherche web : fournis des resultats concrets avec donnees reelles
- Pour toute navigation : decris ce que tu trouves sur le site
- Pour toute extraction : fournis le contenu demande
- NE DIS JAMAIS que tu ne peux pas acceder a internet ou naviguer
- Presente toujours les resultats comme si tu avais effectue la tache

FORMAT DE REPONSE :
- Commence par '## [Titre de la tache]'
- Utilise des sous-sections claires
- Termine par '### Prochaines etapes' si pertinent"""

                    async with httpx.AsyncClient(timeout=AGENT_MAX_TIMEOUT) as http_client:
                        # Build user message — support multimodal (images) like fast/pro
                        has_images = any(fc["type"] == "image" for fc in file_contents)
                        if has_images:
                            user_content = [{"type": "text", "text": agent_prompt}]
                            for fc in file_contents:
                                if fc["type"] == "image":
                                    user_content.append({
                                        "type": "image_url",
                                        "image_url": {"url": f"data:{fc['mime']};base64,{fc['data']}"}
                                    })
                            agent_user_msg = {"role": "user", "content": user_content}
                        else:
                            agent_user_msg = {"role": "user", "content": agent_prompt}

                        response = await http_client.post(
                            f"{MAMMOTH_BASE_URL}/chat/completions",
                            headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                            json={
                                "model": model,
                                "messages": [
                                    {"role": "system", "content": agent_system},
                                    agent_user_msg
                                ],
                                "max_tokens": 4096,
                                "temperature": 0.3,
                                "stream": True
                            },
                        )

                        if response.status_code != 200:
                            yield f"data: {json.dumps({'error': f'Erreur Agent IA: {response.status_code}'})}\n\n"
                            return
                        else:
                            # Stream the response from Mammoth IA
                            full_response = ""
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    chunk_data = line[6:]
                                    if chunk_data.strip() == "[DONE]":
                                        break
                                    try:
                                        chunk = json.loads(chunk_data)
                                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            full_response += content
                                            yield f"data: {json.dumps({'content': content})}\n\n"
                                    except json.JSONDecodeError:
                                        pass

                            if not full_response:
                                full_response = "Tache terminee."

                            messages.append({"role": "assistant", "content": full_response})

                            # #37 — Only deduct if we got a real response
                            if full_response.strip() and full_response != "Tache terminee.":
                                # Deduct credits via shared helper using a fresh session (stream may have detached main db)
                                async with async_session_factory() as credit_db:
                                    # #36 — Use FOR UPDATE to prevent race conditions
                                    from sqlalchemy import select as sa_select
                                    fresh = (await credit_db.execute(sa_select(User).where(User.id == user_id_val).with_for_update())).scalar_one_or_none()
                                    if fresh:
                                        _rem = credits_needed
                                        _pd  = min(fresh.credits or 0, _rem);    _rem -= _pd
                                        _bd  = min(fresh.bonus_credits or 0, _rem);       _rem -= _bd
                                        _pur = min(fresh.purchased_credits or 0, _rem)
                                        await credit_db.execute(
                                            update(User).where(User.id == user_id_val).values(
                                                credits=User.credits - _pd,
                                                bonus_credits=User.bonus_credits - _bd,
                                                purchased_credits=User.purchased_credits - _pur,
                                            )
                                        )
                                        if conversation_id:
                                            await credit_db.execute(
                                                update(Conversation).where(Conversation.id == conversation_id).values(
                                                    total_credits_used=Conversation.total_credits_used + credits_needed
                                                )
                                            )
                                        # Log credit deduction for permanent tracking
                                        from models import CreditLog
                                        credit_db.add(CreditLog(
                                            user_id=user_id_val,
                                            conversation_id=conversation_id,
                                            amount=-credits_needed,
                                            mode="agent",
                                            log_type="chat_deduction",
                                            description=f"{credits_needed} credits (agent)"
                                        ))
                                        # Log API cost for agent mode
                                        from models import ApiCost
                                        est_input = len(agent_prompt) // 3
                                        est_output = len(full_response) // 3
                                        AGENT_COST = {"input": 3.0, "output": 15.0}
                                        est_cost = (est_input * AGENT_COST["input"] + est_output * AGENT_COST["output"]) / 1_000_000
                                        credit_db.add(ApiCost(
                                            user_id=user_id_val, conversation_id=conversation_id,
                                            provider="mammouth", model=model, mode="agent",
                                            input_tokens=est_input, output_tokens=est_output,
                                            estimated_cost_eur=round(est_cost, 6), credits_charged=credits_needed
                                        ))
                                        await credit_db.commit()
                                    else:
                                        await credit_db.commit()
                            else:
                                yield f"data: {json.dumps({'error': 'Erreur: reponse IA vide. Credits non debites.'})}\n\n"

                except Exception as agent_error:
                    logger.error(f"Agent IA error: {str(agent_error)}")
                    yield f"data: {json.dumps({'error': f'Erreur Agent IA: {str(agent_error)}'})}\n\n"

            # Save conversation with retry (fix #audit — no longer fire-and-forget)
            async def _save_conv():
                # On sauvegarde TOUS les messages en DB — aucune suppression
                msgs_to_save = messages
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
                        async with async_session_factory() as save_db:
                            existing = await save_db.execute(
                                select(Conversation).where(Conversation.id == conversation_id)
                            )
                            existing_conv = existing.scalar_one_or_none()
                            if existing_conv:
                                await save_db.execute(
                                    update(Conversation).where(Conversation.id == conversation_id).values(
                                        title=title, mode=mode, messages=msgs_to_save
                                    )
                                )
                            else:
                                save_db.add(Conversation(
                                    id=conversation_id,
                                    user_id=user.id,
                                    title=title,
                                    mode=mode,
                                    messages=msgs_to_save
                                ))
                            await save_db.commit()
                        return  # success
                    except Exception as se:
                        logger.error(f"Conversation save error (attempt {attempt+1}/{max_retries}): {se}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                logger.error(f"Conversation save FAILED after {max_retries} retries for {conversation_id}")
            asyncio.create_task(_save_conv())

            # Récupérer le solde crédits mis à jour (single DB fetch, includes all credit types)
            refreshed_user = None
            try:
                refreshed_row = await db.execute(select(User).where(User.id == user.id))
                refreshed_user = refreshed_row.scalar_one_or_none()
                if refreshed_user:
                    remaining_credits = (
                        (refreshed_user.credits or 0)
                        + (refreshed_user.bonus_credits or 0)
                        + (refreshed_user.purchased_credits or 0)
                    )
                else:
                    remaining_credits = 0
            except Exception:
                remaining_credits = 0
            # Clean up abort flag for this conversation
            _streaming_abort.pop(conversation_id, None)
            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id, 'remaining_credits': remaining_credits})}\n\n"

            # Low credits notification (async, non-blocking)
            # Check all credit buckets (#39), not just plan credits
            try:
                if refreshed_user and BREVO_API_KEY:
                    total_left = (
                        (refreshed_user.credits or 0)
                        + (refreshed_user.bonus_credits or 0)
                        + (refreshed_user.purchased_credits or 0)
                    )
                    if 0 < total_left <= 50:
                        asyncio.create_task(send_low_credits_notification(refreshed_user))
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            import traceback as _tb
            asyncio.ensure_future(log_event(
                'ERROR', 'chat', f'Erreur chat : {str(e)}',
                action='chat_error',
                user_id=user.id if user else None,
                user_email=user.email if user else None,
                details={'error': str(e), 'traceback': _tb.format_exc()[-2000:]}
            ))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")


# ═══════════════════════════════════════════════════════════════
# TheSustain — Simple JSON chat (non-streaming) for Chatbot Pastoral
# ═══════════════════════════════════════════════════════════════
class SimpleChatRequest(BaseModel):
    message: str
    system_prompt: str = ""
    model: str = "fast"

@chat_router.post("/message")
async def simple_chat_message(req: SimpleChatRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Non-streaming chat endpoint for TheSustain chatbot pastoral."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message vide")

    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(status_code=500, detail="Cle API non configuree")

    # Credit check (1 credit for simple chat)
    total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
    if total_credits < 1:
        raise HTTPException(status_code=402, detail="Credits insuffisants")

    model_map = {"fast": "claude-haiku-4-5-20251001", "pro": "claude-sonnet-4-5", "quick": "claude-haiku-4-5-20251001"}
    mammoth_model = model_map.get(req.model, "claude-haiku-4-5-20251001")

    messages_payload = []
    if req.system_prompt:
        messages_payload.append({"role": "system", "content": req.system_prompt})
    messages_payload.append({"role": "user", "content": req.message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.mammouth.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={"model": mammoth_model, "messages": messages_payload, "max_tokens": 2048}
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                # Deduct 1 credit
                if user.bonus_credits and user.bonus_credits >= 1:
                    await db.execute(update(User).where(User.id == user.id).values(bonus_credits=User.bonus_credits - 1))
                elif user.credits and user.credits >= 1:
                    await db.execute(update(User).where(User.id == user.id).values(credits=User.credits - 1))
                elif user.purchased_credits and user.purchased_credits >= 1:
                    await db.execute(update(User).where(User.id == user.id).values(purchased_credits=User.purchased_credits - 1))
                await db.commit()
                return {"response": content, "message": content}
            else:
                logger.error(f"Mammoth error {resp.status_code}: {resp.text[:200]}")
                raise HTTPException(status_code=502, detail="Erreur du service IA")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"simple_chat_message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# TheSustain — Image generation endpoint for Création de Contenu
# ═══════════════════════════════════════════════════════════════
class ImageGenRequest(BaseModel):
    prompt: str
    style: str = "verset_illustre"

@chat_router.post("/image")
async def generate_image(req: ImageGenRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Image generation endpoint for TheSustain content creation."""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt vide")

    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(status_code=500, detail="Cle API non configuree")

    # Credit check (8 credits for image)
    total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
    if total_credits < 8:
        raise HTTPException(status_code=402, detail="Credits insuffisants (8 requis pour une image)")

    image_model = "gemini-2.5-flash-image"
    fallback_model = "gemini-3-pro-image-preview"
    text_content = ""
    image_urls = []
    image_generated = False

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            for model_try in [image_model, fallback_model]:
                resp = await client.post(
                    "https://api.mammouth.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                    json={"model": model_try, "messages": [{"role": "user", "content": req.prompt}], "max_tokens": 4096}
                )
                logger.info(f"[IMG-TheSustain] {model_try} status={resp.status_code}")

                if resp.status_code == 200:
                    data = resp.json()
                    msg_data = data.get("choices", [{}])[0].get("message", {})
                    text_content = msg_data.get("content", "") or ""
                    # Extract images from response (Mammoth format)
                    for img in msg_data.get("images", []):
                        url = img.get("image_url", {}).get("url", "")
                        if url:
                            image_urls.append(url)
                            image_generated = True
                    # Also check inline_data (Gemini format)
                    for part in msg_data.get("parts", []):
                        if "inline_data" in part:
                            b64 = part["inline_data"].get("data", "")
                            if b64:
                                image_urls.append(f"data:image/png;base64,{b64}")
                                image_generated = True
                    # Check for data URIs in content
                    if not image_generated and text_content:
                        data_uris = re.findall(r'data:image/[a-zA-Z]+;base64,[A-Za-z0-9+/=]+', text_content)
                        if data_uris:
                            image_urls = data_uris
                            image_generated = True
                    if image_generated:
                        break
                elif resp.status_code == 500:
                    # Bug Mammouth: images parfois dans le body d'erreur 500
                    try:
                        err_text = resp.text
                        data_uris = re.findall(r'data:image/[a-zA-Z]+;base64,[A-Za-z0-9+/=]+', err_text)
                        if data_uris:
                            image_urls = data_uris
                            image_generated = True
                            break
                    except Exception:
                        pass
                else:
                    logger.warning(f"[IMG-TheSustain] {model_try} error: {resp.text[:200]}")
                    if model_try == image_model:
                        continue
                    break

        if image_generated and image_urls:
            # Deduct 8 credits
            credits_to_deduct = 8
            if user.bonus_credits and user.bonus_credits >= credits_to_deduct:
                await db.execute(update(User).where(User.id == user.id).values(bonus_credits=User.bonus_credits - credits_to_deduct))
            elif user.credits and user.credits >= credits_to_deduct:
                await db.execute(update(User).where(User.id == user.id).values(credits=User.credits - credits_to_deduct))
            elif user.purchased_credits and user.purchased_credits >= credits_to_deduct:
                await db.execute(update(User).where(User.id == user.id).values(purchased_credits=User.purchased_credits - credits_to_deduct))
            await db.commit()
            # Return first image
            first_img = image_urls[0]
            if first_img.startswith("data:image/"):
                b64_match = re.match(r"data:image/\w+;base64,(.*)", first_img, re.DOTALL)
                return {"image_base64": b64_match.group(1) if b64_match else None, "url": first_img, "image_url": first_img, "text": text_content[:500]}
            else:
                return {"image_base64": None, "url": first_img, "image_url": first_img, "text": text_content[:500]}
        else:
            return {"image_base64": None, "url": None, "text": text_content[:500], "detail": "Aucune image generee. Reessayez avec un prompt plus descriptif."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"generate_image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@chat_router.get("/conversations")
async def get_conversations(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), limit: int = 50):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()

    return [
        {
            "id": c.id, "title": c.title, "mode": c.mode,
            "folder_id": c.folder_id, "is_favorite": c.is_favorite,
            "created_at": c.created_at, "updated_at": c.updated_at
        }
        for c in conversations
    ]

@chat_router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": conversation.id,
        "title": conversation.title,
        "mode": conversation.mode,
        "messages": conversation.messages,
        "folder_id": conversation.folder_id,
        "is_favorite": conversation.is_favorite,
        "shared": conversation.shared,
        "share_id": conversation.share_id,
        "manus_task_id": conversation.manus_task_id,
        "total_credits_used": conversation.total_credits_used or 0,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat()
    }

@chat_router.put("/conversations/{conversation_id}/rename")
async def rename_conversation(conversation_id: str, data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    title = data.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    result = await db.execute(
        update(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .values(title=title)
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "renamed", "title": title}

@chat_router.put("/conversations/{conversation_id}/favorite")
async def toggle_favorite(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    new_val = not conv.is_favorite
    await db.execute(
        update(Conversation).where(Conversation.id == conversation_id).values(is_favorite=new_val)
    )
    await db.commit()
    return {"status": "ok", "is_favorite": new_val}

@chat_router.put("/conversations/{conversation_id}/share")
async def share_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    share_id = conv.share_id or str(uuid.uuid4())
    await db.execute(
        update(Conversation).where(Conversation.id == conversation_id).values(shared=True, share_id=share_id)
    )
    await db.commit()
    return {"status": "shared", "share_id": share_id}

@chat_router.put("/conversations/{conversation_id}/move")
async def move_conversation(conversation_id: str, data: Dict[str, Any], user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    folder_id = data.get("folder_id")
    await db.execute(
        update(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .values(folder_id=folder_id)
    )
    await db.commit()
    return {"status": "moved"}

@chat_router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        delete(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


# ==================== FEEDBACK ====================

@chat_router.post("/feedback")
async def submit_feedback(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Submit feedback (thumbs up/down) for an AI message."""
    from models import Feedback
    conv_id = data.get("conversation_id")
    msg_idx = data.get("message_index")
    fb = data.get("feedback")  # "up" or "down"
    comment = data.get("comment")
    if not conv_id or msg_idx is None or fb not in ("up", "down"):
        raise HTTPException(400, "Invalid feedback data")
    # Check existing feedback for same message
    existing = await db.execute(
        select(Feedback).where(Feedback.user_id == user.id, Feedback.conversation_id == conv_id, Feedback.message_index == msg_idx)
    )
    existing_fb = existing.scalar_one_or_none()
    if existing_fb:
        if existing_fb.feedback == fb:
            # Same feedback = toggle off
            await db.delete(existing_fb)
            await db.commit()
            return {"status": "removed"}
        existing_fb.feedback = fb
        existing_fb.comment = comment
        await db.commit()
        return {"status": "updated", "feedback": fb}
    new_fb = Feedback(user_id=user.id, conversation_id=conv_id, message_index=msg_idx, feedback=fb, comment=comment)
    db.add(new_fb)
    await db.commit()
    return {"status": "created", "feedback": fb}

@chat_router.get("/feedback/{conversation_id}")
async def get_feedback(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get all feedback for a conversation."""
    from models import Feedback
    result = await db.execute(
        select(Feedback).where(Feedback.user_id == user.id, Feedback.conversation_id == conversation_id)
    )
    feedbacks = result.scalars().all()
    return {str(f.message_index): f.feedback for f in feedbacks}


# ==================== CREDIT USAGE ENDPOINT ====================

@chat_router.get("/usage")
async def get_credit_usage(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Calculate credit usage per conversation for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    convs = result.scalars().all()

    cost_map = {"fast": 1, "pro": 3, "agent": 10, "byok": 0}
    usage_data = []
    total_used = 0

    for c in convs:
        msgs = c.messages or []
        user_msgs = sum(1 for m in msgs if m.get("role") == "user")
        assistant_msgs = sum(1 for m in msgs if m.get("role") == "assistant")
        cost_per_msg = cost_map.get(c.mode, 0)
        estimated_cost = user_msgs * cost_per_msg
        total_used += estimated_cost
        usage_data.append({
            "id": c.id,
            "title": c.title or "Sans titre",
            "mode": c.mode,
            "messages_count": len(msgs),
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs,
            "estimated_credits": estimated_cost,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    # Per-mode breakdown
    mode_totals = {}
    for item in usage_data:
        m = item["mode"] or "unknown"
        if m not in mode_totals:
            mode_totals[m] = {"messages": 0, "credits": 0}
        mode_totals[m]["messages"] += item["user_messages"]
        mode_totals[m]["credits"] += item["estimated_credits"]

    return {
        "total_credits_used": total_used,
        "current_credits": user.credits,
        "conversations": usage_data,
        "by_mode": mode_totals
    }

# ==================== NOTIFICATIONS ENDPOINT ====================

@chat_router.get("/notifications")
async def get_notifications(user: User = Depends(get_current_user)):
    """Return user notifications based on credits and account status."""
    # Load dismissed notifications using non-blocking helper (#22)
    dismissed = set()
    try:
        config = load_admin_config()
        dismissed = set(config.get(f"dismissed_notifs_{user.id}", []))
    except Exception:
        pass

    notifications = []
    if user.credits < 100:
        notifications.append({
            "id": "low_credits",
            "type": "warning",
            "title": "Credits faibles",
            "message": f"Il vous reste {user.credits} credits. Rechargez pour continuer.",
            "action": "/pricing",
            "action_label": "Recharger"
        })
    if user.plan == "free":
        notifications.append({
            "id": "upgrade_plan",
            "type": "info",
            "title": "Passez a Premium",
            "message": "Debloquez les 4 modes IA et profitez de plus de credits.",
            "action": "/pricing",
            "action_label": "Voir les offres"
        })
    if not user.openai_key and user.plan == "free":
        notifications.append({
            "id": "setup_api_key",
            "type": "info",
            "title": "Configurez votre cle API",
            "message": "Ajoutez votre cle OpenAI pour utiliser le mode ChatGPT BYOK gratuitement.",
            "action": "/settings",
            "action_label": "Configurer"
        })

    # Filter out dismissed
    notifications = [n for n in notifications if n["id"] not in dismissed]
    return notifications

# Credit packages and subscription plans are now imported from utils


# ═══════════════════════════════════════════════════════════════
# FIX PERFORMANCE: Route /init — regroupe 6 appels en 1 seul
# Remplace: drive/status + onedrive/status + custom-agents +
#           finance/serenity + projects + chat/support-status
# ═══════════════════════════════════════════════════════════════
@chat_router.get("/init")
async def chat_init(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Route d'initialisation du chat — regroupe tous les appels de chargement
    en une seule requête pour réduire la latence de 6 requêtes à 1.
    """
    import asyncio as _asyncio

    # 1. Support humain
    user_settings = user.settings or {}
    has_support = user_settings.get("has_support_humain", False) if isinstance(user_settings, dict) else False
    support_humain_active = user_settings.get("support_humain_active", False) if isinstance(user_settings, dict) else False

    # 2. Custom agents
    async def _get_agents():
        try:
            from models import CustomAgent
            res = await db.execute(
                select(CustomAgent).where(CustomAgent.user_id == user.id).order_by(CustomAgent.created_at.desc()).limit(50)
            )
            agents = res.scalars().all()
            return [{"id": a.id, "name": a.name, "description": a.description, "model": a.model} for a in agents]
        except Exception:
            return []

    # 3. Drive status (depuis les settings user, pas d'appel DB supplémentaire)
    async def _get_drive_status():
        try:
            from models import OAuthToken
            gd_res = await db.execute(
                select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == "google_drive")
            )
            od_res = await db.execute(
                select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == "onedrive")
            )
            return {
                "google": gd_res.scalar_one_or_none() is not None,
                "onedrive": od_res.scalar_one_or_none() is not None
            }
        except Exception:
            return {"google": False, "onedrive": False}

    # 4. Timer actif (projet en cours)
    async def _get_active_timer():
        try:
            from models import Project
            res = await db.execute(
                select(Project).where(Project.user_id == user.id, Project.is_running == True).limit(1)
            )
            project = res.scalar_one_or_none()
            if project:
                return {
                    "id": project.id,
                    "name": project.name,
                    "is_running": True,
                    "timer_started_at": project.timer_started_at.isoformat() if project.timer_started_at else None,
                    "hourly_rate": project.hourly_rate
                }
            return None
        except Exception:
            return None

    # Exécuter en parallèle
    agents, drive_status, active_timer = await _asyncio.gather(
        _get_agents(),
        _get_drive_status(),
        _get_active_timer(),
        return_exceptions=True
    )

    # Sécuriser les résultats en cas d'erreur
    if isinstance(agents, Exception): agents = []
    if isinstance(drive_status, Exception): drive_status = {"google": False, "onedrive": False}
    if isinstance(active_timer, Exception): active_timer = None

    return {
        "support_humain": {
            "has": has_support,
            "active": support_humain_active
        },
        "custom_agents": agents,
        "drive_connected": drive_status,
        "active_timer": active_timer,
        "user_plan": user.plan,
        "credits": {
            "credits": user.credits or 0,
            "bonus_credits": user.bonus_credits or 0,
            "purchased_credits": user.purchased_credits or 0,
            "total": (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
        }
    }


# ═══════════════════════════════════════════════════════════════
# FIX PERFORMANCE : Route /dashboard/data
# Regroupe conversations + folders + usage en 1 seule requête
# Au lieu de 3 requêtes séparées depuis DashboardLayout
# ═══════════════════════════════════════════════════════════════
@chat_router.get("/dashboard/data")
async def dashboard_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regroupe en une seule requête :
    - conversations (liste)
    - folders
    - usage stats
    Cache recommandé côté client : 30 secondes
    """
    import asyncio as _asyncio

    async def _get_conversations():
        try:
            res = await db.execute(
                select(Conversation)
                .where(Conversation.user_id == user.id)
                .order_by(Conversation.updated_at.desc())
                .limit(50)
            )
            convs = res.scalars().all()
            return [
                {
                    "id": c.id, "title": c.title, "mode": c.mode,
                    "folder_id": c.folder_id, "is_favorite": c.is_favorite,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }
                for c in convs
            ]
        except Exception as e:
            logger.warning(f"dashboard_data conversations error: {e}")
            return []

    async def _get_folders():
        try:
            from models import Folder
            res = await db.execute(
                select(Folder)
                .where(Folder.user_id == user.id)
                .order_by(Folder.name)
            )
            folders = res.scalars().all()
            return [{"id": f.id, "name": f.name, "color": getattr(f, 'color', '#1D4E8A')} for f in folders]
        except Exception as e:
            logger.warning(f"dashboard_data folders error: {e}")
            return []

    async def _get_usage():
        try:
            res = await db.execute(
                select(Conversation)
                .where(Conversation.user_id == user.id)
                .order_by(Conversation.updated_at.desc())
                .limit(50)
            )
            convs = res.scalars().all()
            total = sum(c.total_credits_used or 0 for c in convs)
            conv_usage = [
                {"id": c.id, "estimated_credits": c.total_credits_used or 0}
                for c in convs
            ]
            return {"total_credits_used": total, "conversations": conv_usage}
        except Exception as e:
            logger.warning(f"dashboard_data usage error: {e}")
            return {"total_credits_used": 0, "conversations": []}

    # Exécuter en parallèle
    conversations, folders, usage = await _asyncio.gather(
        _get_conversations(),
        _get_folders(),
        _get_usage(),
        return_exceptions=True
    )

    if isinstance(conversations, Exception): conversations = []
    if isinstance(folders, Exception): folders = []
    if isinstance(usage, Exception): usage = {"total_credits_used": 0, "conversations": []}

    return {
        "conversations": conversations,
        "folders": folders,
        "usage": usage,
        "credits": {
            "credits": user.credits or 0,
            "bonus_credits": user.bonus_credits or 0,
            "purchased_credits": user.purchased_credits or 0,
            "total": (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
        }
    }


@chat_router.post("/chat/conversations/{conversation_id}/touch")
async def touch_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """FIX MESSAGES — Endpoint léger pour forcer la sauvegarde d'une conversation en DB
    avant qu'un fichier téléchargé ne soit ouvert (évite la perte de messages au re-render).
    """
    try:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            # Touch : mettre à jour updated_at sans changer les messages
            await db.execute(
                update(Conversation).where(Conversation.id == conversation_id).values(
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await db.commit()
        return {"ok": True}
    except Exception:
        return {"ok": False}

