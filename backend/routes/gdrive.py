"""Google Drive integration routes."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy import select, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime, timezone
import os
import io
import json
import tempfile
import logging

from database import get_db
from deps import get_current_user, User
from utils import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

logger = logging.getLogger(__name__)

drive_router = APIRouter(prefix="/drive", tags=["Google Drive"])

REDIRECT_URI = os.environ.get("GOOGLE_DRIVE_REDIRECT_URI", "")
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive']

def _get_flow():
    from google_auth_oauthlib.flow import Flow
    return Flow.from_client_config(
        {"web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }},
        scopes=DRIVE_SCOPES,
        redirect_uri=REDIRECT_URI
    )

@drive_router.get("/connect")
async def connect_drive(user: User = Depends(get_current_user)):
    """Initiate Google Drive OAuth flow."""
    if not GOOGLE_CLIENT_ID or not REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google Drive non configure")
    flow = _get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=user.id
    )
    return {"authorization_url": authorization_url}

@drive_router.get("/callback")
async def drive_callback(
    code: str = Query(...),
    state: str = Query(""),
    scope: str = Query(""),
    authuser: str = Query(""),
    prompt: str = Query(""),
    iss: str = Query(""),
    db: AsyncSession = Depends(get_db)
):
    """Handle Google Drive OAuth callback."""
    import os as _os
    # OAUTHLIB_INSECURE_TRANSPORT activé uniquement en dev local, jamais en prod (bug #5)
    if _os.environ.get("DEV_MODE", "").lower() in ("1", "true", "yes"):
        _os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    _os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"   # Google renvoie plus de scopes que demandés
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {"web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }},
        scopes=DRIVE_SCOPES,
        redirect_uri=REDIRECT_URI
    )
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error(f"Drive token fetch error: {e}")
        frontend_url = os.environ.get("FRONTEND_URL", "https://app.zayado.net")
        return RedirectResponse(url=f"{frontend_url}/integrations?provider=google&status=error&msg=token_exchange")
    credentials = flow.credentials

    import uuid as _uuid
    cred_id = str(_uuid.uuid4()).replace("-", "")

    await db.execute(text("""
        INSERT INTO drive_credentials (id, user_id, access_token, refresh_token, token_uri, client_id, client_secret, scopes, expiry, updated_at)
        VALUES (:cred_id, :user_id, :access_token, :refresh_token, :token_uri, :client_id, :client_secret, :scopes, :expiry, :updated_at)
        ON DUPLICATE KEY UPDATE
            access_token=VALUES(access_token), refresh_token=COALESCE(VALUES(refresh_token), refresh_token),
            token_uri=VALUES(token_uri), client_id=VALUES(client_id), client_secret=VALUES(client_secret),
            scopes=VALUES(scopes), expiry=VALUES(expiry), updated_at=VALUES(updated_at)
    """), {
        "cred_id": cred_id,
        "user_id": state,
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": json.dumps(list(credentials.scopes or [])),
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        "updated_at": datetime.now(timezone.utc).isoformat()
    })
    await db.commit()

    frontend_url = os.environ.get("FRONTEND_URL", os.environ.get("REACT_APP_BACKEND_URL", ""))
    return RedirectResponse(url=f"{frontend_url}/integrations?provider=google&status=ok")

async def _get_drive_service(user: User, db: AsyncSession):
    """Get a Google Drive service with auto-refresh."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest
    from googleapiclient.discovery import build

    result = await db.execute(text("SELECT * FROM drive_credentials WHERE user_id = :uid"), {"uid": user.id})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=400, detail="Google Drive non connecte. Connectez votre Drive d'abord.")

    scopes = json.loads(row["scopes"]) if row["scopes"] else DRIVE_SCOPES
    creds = Credentials(
        token=row["access_token"],
        refresh_token=row.get("refresh_token"),
        token_uri=row["token_uri"],
        client_id=row["client_id"],
        client_secret=row["client_secret"],
        scopes=scopes
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            await db.execute(text("""
                UPDATE drive_credentials SET access_token=:token, expiry=:expiry, updated_at=:updated_at WHERE user_id=:uid
            """), {
                "token": creds.token,
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "uid": user.id
            })
            await db.commit()
        except Exception as refresh_err:
            # Token revoked or invalid — cleanup from DB
            logger.warning(f"Drive token refresh failed for user {user.id}: {refresh_err}. Cleaning up.")
            await db.execute(text("DELETE FROM drive_credentials WHERE user_id = :uid"), {"uid": user.id})
            await db.commit()
            raise HTTPException(status_code=401, detail="Acces Google Drive revoque. Veuillez reconnecter votre Drive.")

    return build('drive', 'v3', credentials=creds)

@drive_router.get("/status")
async def drive_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Check if Google Drive is connected."""
    try:
        result = await db.execute(text("SELECT user_id FROM drive_credentials WHERE user_id = :uid"), {"uid": user.id})
        row = result.first()
        return {"connected": row is not None}
    except Exception:
        return {"connected": False}

@drive_router.get("/files")
async def list_drive_files(folder_id: str = "root", page_token: str = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List files in Google Drive."""
    service = await _get_drive_service(user, db)
    query = f"'{folder_id}' in parents and trashed = false"
    params = {
        "q": query,
        "pageSize": 30,
        "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime, iconLink, thumbnailLink, webViewLink)",
        "orderBy": "folder,name"
    }
    if page_token:
        params["pageToken"] = page_token
    results = service.files().list(**params).execute()
    files = results.get("files", [])
    return {
        "files": [{
            "id": f["id"],
            "name": f["name"],
            "mimeType": f.get("mimeType", ""),
            "size": int(f.get("size", 0)),
            "modifiedTime": f.get("modifiedTime", ""),
            "isFolder": f.get("mimeType") == "application/vnd.google-apps.folder",
            "webViewLink": f.get("webViewLink", ""),
            "iconLink": f.get("iconLink", ""),
        } for f in files],
        "nextPageToken": results.get("nextPageToken"),
        "folder_id": folder_id
    }

@drive_router.get("/download/{file_id}")
async def download_drive_file(file_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Download a file from Google Drive."""
    from googleapiclient.http import MediaIoBaseDownload
    service = await _get_drive_service(user, db)
    file_meta = service.files().get(fileId=file_id, fields="name,mimeType,size").execute()
    name = file_meta.get("name", "file")
    mime = file_meta.get("mimeType", "application/octet-stream")

    if mime.startswith("application/vnd.google-apps."):
        export_mimes = {
            "application/vnd.google-apps.document": "application/pdf",
            "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
        export_mime = export_mimes.get(mime, "application/pdf")
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        ext = {
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        }.get(export_mime, ".pdf")
        name = name + ext
        mime = export_mime
    else:
        request = service.files().get_media(fileId=file_id)

    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return StreamingResponse(buf, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{name}"'})

@drive_router.post("/upload")
async def upload_to_drive(file: UploadFile = File(...), folder_id: str = "root", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Upload a file to Google Drive."""
    from googleapiclient.http import MediaFileUpload
    service = await _get_drive_service(user, db)
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "file")[1]) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    file_metadata = {"name": file.filename or "upload", "parents": [folder_id]}
    media = MediaFileUpload(tmp_path, mimetype=file.content_type or "application/octet-stream", resumable=True)
    result = service.files().create(body=file_metadata, media_body=media, fields="id,name,webViewLink").execute()
    os.unlink(tmp_path)
    return {"id": result["id"], "name": result["name"], "webViewLink": result.get("webViewLink", "")}

@drive_router.delete("/disconnect")
async def disconnect_drive(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Disconnect Google Drive."""
    await db.execute(text("DELETE FROM drive_credentials WHERE user_id = :uid"), {"uid": user.id})
    await db.commit()
    return {"status": "disconnected"}

@drive_router.post("/ensure-folders")
async def ensure_drive_folders(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create the Zayado Extension IA folder structure on Google Drive."""
    service = await _get_drive_service(user, db)
    
    def _find_or_create_folder(name, parent_id="root"):
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id,name)").execute()
        existing = results.get("files", [])
        if existing:
            return existing[0]["id"]
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
        folder = service.files().create(body=meta, fields="id").execute()
        return folder["id"]
    
    root_id = _find_or_create_folder("Zayado Extension IA")
    subfolders = {}
    for name in ["Images generees", "Documents & PDF", "Workflows"]:
        subfolders[name] = _find_or_create_folder(name, root_id)
    
    return {"root_id": root_id, "subfolders": subfolders}

@drive_router.post("/save-image")
async def save_image_to_drive(image_url: str = "", image_name: str = "", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Save a generated image to the user's Google Drive Zayado Extension IA/Images folder."""
    import httpx as hx
    service = await _get_drive_service(user, db)
    
    # Download the image
    full_url = image_url
    if image_url.startswith("/"):
        frontend_url = os.environ.get("FRONTEND_URL", "")
        full_url = frontend_url + image_url
    
    async with hx.AsyncClient() as client:
        resp = await client.get(full_url)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Impossible de telecharger l'image")
        image_data = resp.content
    
    # Ensure Zayado Extension IA/Images generees folder exists
    def _find_or_create_folder(name, parent_id="root"):
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id,name)").execute()
        existing = results.get("files", [])
        if existing:
            return existing[0]["id"]
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
        folder = service.files().create(body=meta, fields="id").execute()
        return folder["id"]
    
    root_id = _find_or_create_folder("Zayado Extension IA")
    images_id = _find_or_create_folder("Images generees", root_id)
    
    # Upload image
    from googleapiclient.http import MediaInMemoryUpload
    filename = image_name or f"image_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')}.png"
    media = MediaInMemoryUpload(image_data, mimetype="image/png", resumable=False)
    file_meta = {"name": filename, "parents": [images_id]}
    result = service.files().create(body=file_meta, media_body=media, fields="id,name,webViewLink").execute()
    
    return {"id": result["id"], "name": result["name"], "webViewLink": result.get("webViewLink", "")}



@drive_router.post("/autosave")
async def autosave_to_drive(
    content: str = "",
    content_type: str = "text",  # "text" | "image" | "conversation"
    filename: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-save generated content to Google Drive.
    - text: Save as .txt or .md file in Documents & PDF folder
    - image: Download and save to Images generees folder
    - conversation: Save full conversation as JSON
    """
    import httpx as hx
    service = await _get_drive_service(user, db)
    
    def _find_or_create_folder(name, parent_id="root"):
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id,name)").execute()
        existing = results.get("files", [])
        if existing:
            return existing[0]["id"]
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
        folder = service.files().create(body=meta, fields="id").execute()
        return folder["id"]
    
    root_id = _find_or_create_folder("Zayado Extension IA")
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    
    if content_type == "image":
        # Save image
        images_id = _find_or_create_folder("Images generees", root_id)
        full_url = content
        if content.startswith("/"):
            frontend_url = os.environ.get("FRONTEND_URL", "")
            full_url = frontend_url + content
        async with hx.AsyncClient() as client:
            resp = await client.get(full_url)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Impossible de telecharger l'image")
            image_data = resp.content
        from googleapiclient.http import MediaInMemoryUpload
        fname = filename or f"image_{timestamp}.png"
        media = MediaInMemoryUpload(image_data, mimetype="image/png", resumable=False)
        file_meta = {"name": fname, "parents": [images_id]}
        result = service.files().create(body=file_meta, media_body=media, fields="id,name,webViewLink").execute()
    
    elif content_type == "conversation":
        # Save conversation as JSON
        docs_id = _find_or_create_folder("Documents & PDF", root_id)
        from googleapiclient.http import MediaInMemoryUpload
        fname = filename or f"conversation_{timestamp}.json"
        media = MediaInMemoryUpload(content.encode('utf-8'), mimetype="application/json", resumable=False)
        file_meta = {"name": fname, "parents": [docs_id]}
        result = service.files().create(body=file_meta, media_body=media, fields="id,name,webViewLink").execute()
    
    else:
        # Save text content
        docs_id = _find_or_create_folder("Documents & PDF", root_id)
        from googleapiclient.http import MediaInMemoryUpload
        ext = ".md" if "# " in content or "**" in content else ".txt"
        fname = filename or f"document_{timestamp}{ext}"
        media = MediaInMemoryUpload(content.encode('utf-8'), mimetype="text/plain", resumable=False)
        file_meta = {"name": fname, "parents": [docs_id]}
        result = service.files().create(body=file_meta, media_body=media, fields="id,name,webViewLink").execute()
    
    return {"id": result["id"], "name": result["name"], "webViewLink": result.get("webViewLink", ""), "autosaved": True}


@drive_router.get("/autosave-status")
async def get_autosave_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Check if user has Drive connected and autosave enabled."""
    try:
        # Check if user has drive credentials
        result = await db.execute(text("SELECT access_token FROM drive_credentials WHERE user_id = :uid"), {"uid": user.id})
        row = result.fetchone()
        has_drive = row is not None and row[0] is not None
        
        # Check user settings for autosave preference
        autosave_enabled = getattr(user, 'autosave_drive', False) if hasattr(user, 'autosave_drive') else False
        
        return {
            "drive_connected": has_drive,
            "autosave_enabled": autosave_enabled,
            "can_autosave": has_drive
        }
    except Exception as e:
        logger.error(f"Error checking autosave status: {e}")
        return {"drive_connected": False, "autosave_enabled": False, "can_autosave": False}


@drive_router.post("/sync-conversation")
async def sync_conversation_to_drive(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync une conversation complète sur Drive — 1 fichier par conversation.
    Si le fichier existe déjà (même conversation_id), il est MIS À JOUR.
    Si non, il est créé. Jamais de doublon.
    Format : Zayado Extension IA / Conversations / {conv_title}_{conv_id_short}.md
    """
    from googleapiclient.http import MediaInMemoryUpload
    
    body = await request.json()
    conversation_id  = body.get("conversation_id", "")
    conversation_title = body.get("title", "Conversation")
    messages         = body.get("messages", [])
    
    if not messages:
        raise HTTPException(400, "Aucun message à synchroniser")
    
    service = await _get_drive_service(user, db)
    
    def _find_or_create_folder(name, parent_id="root"):
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id,name)").execute()
        existing = results.get("files", [])
        if existing:
            return existing[0]["id"]
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
        folder = service.files().create(body=meta, fields="id").execute()
        return folder["id"]
    
    root_id   = _find_or_create_folder("Zayado Extension IA")
    conv_folder_id = _find_or_create_folder("Conversations", root_id)
    
    # Nom de fichier basé sur conversation_id (stable, pas de timestamp)
    conv_id_short = conversation_id[:8] if conversation_id else "unknown"
    safe_title = "".join(c for c in conversation_title if c.isalnum() or c in " -_")[:40].strip()
    filename = f"{safe_title}_{conv_id_short}.md"
    
    # Construire le contenu Markdown de la conversation
    lines = [f"# {conversation_title}", f"", f"*Conversation Zayado — ID: {conversation_id}*", f"*Dernière mise à jour: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC*", ""]
    for msg in messages:
        role = msg.get("role", "user")
        content_msg = msg.get("content", "")
        if isinstance(content_msg, list):
            content_msg = " ".join(part.get("text", "") for part in content_msg if isinstance(part, dict))
        if role == "user":
            lines.append(f"**Vous :** {content_msg}")
        elif role == "assistant":
            lines.append(f"**Extension IA :** {content_msg}")
        lines.append("")
    
    md_content = "\n".join(lines)
    
    # Chercher si un fichier avec cet ID de conversation existe déjà
    search_query = f"name='{filename}' and '{conv_folder_id}' in parents and trashed=false"
    existing_files = service.files().list(q=search_query, fields="files(id,name)").execute().get("files", [])
    
    media = MediaInMemoryUpload(md_content.encode("utf-8"), mimetype="text/markdown", resumable=False)
    
    if existing_files:
        # Mettre à jour le fichier existant (pas de doublon !)
        file_id = existing_files[0]["id"]
        result = service.files().update(fileId=file_id, media_body=media, fields="id,name,webViewLink").execute()
        action = "mis à jour"
    else:
        # Créer le fichier
        file_meta = {"name": filename, "parents": [conv_folder_id]}
        result = service.files().create(body=file_meta, media_body=media, fields="id,name,webViewLink").execute()
        action = "créé"
    
    return {
        "id": result["id"],
        "name": result["name"],
        "webViewLink": result.get("webViewLink", ""),
        "action": action,
        "synced": True
    }
