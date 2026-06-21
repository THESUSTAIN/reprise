"""OneDrive/SharePoint integration routes via Microsoft Graph API."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import os
import json
import httpx
import logging

from database import get_db
from deps import get_current_user, User

logger = logging.getLogger(__name__)

onedrive_router = APIRouter(prefix="/onedrive", tags=["OneDrive"])

MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("MICROSOFT_REDIRECT_URI", 
    os.environ.get("FRONTEND_URL", "") + "/api/onedrive/callback")
GRAPH_API = "https://graph.microsoft.com/v1.0"
SCOPES = "Files.ReadWrite.All Sites.ReadWrite.All offline_access User.Read"

@onedrive_router.get("/connect")
async def connect_onedrive(user: User = Depends(get_current_user)):
    """Initiate Microsoft OAuth flow for OneDrive."""
    if not MICROSOFT_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Microsoft OneDrive non configure")
    
    auth_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        f"?client_id={MICROSOFT_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&state={user.id}"
        f"&response_mode=query"
    )
    return {"authorization_url": auth_url}

@onedrive_router.get("/callback")
async def onedrive_callback(code: str = Query(...), state: str = Query(""), db: AsyncSession = Depends(get_db)):
    """Handle Microsoft OAuth callback."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
                "scope": SCOPES,
            }
        )
    
    if resp.status_code != 200:
        logger.error(f"Microsoft token error: {resp.text}")
        frontend_url = os.environ.get("FRONTEND_URL", "")
        return RedirectResponse(url=f"{frontend_url}/integrations?provider=microsoft&status=error&msg=token_exchange")
    
    tokens = resp.json()
    
    import uuid as _uuid
    cred_id = str(_uuid.uuid4()).replace("-", "")

    await db.execute(text("""
        INSERT INTO onedrive_credentials (id, user_id, access_token, refresh_token, scopes, expiry, updated_at)
        VALUES (:cred_id, :user_id, :access_token, :refresh_token, :scopes, :expiry, :updated_at)
        ON DUPLICATE KEY UPDATE
            access_token=VALUES(access_token), 
            refresh_token=COALESCE(VALUES(refresh_token), refresh_token),
            scopes=VALUES(scopes), expiry=VALUES(expiry), updated_at=VALUES(updated_at)
    """), {
        "cred_id": cred_id,
        "user_id": state,
        "access_token": tokens.get("access_token", ""),
        "refresh_token": tokens.get("refresh_token", ""),
        "scopes": SCOPES,
        "expiry": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    })
    await db.commit()
    
    # Create Zayado Extension IA folder structure
    try:
        await _ensure_folder_structure(tokens.get("access_token", ""))
    except Exception as e:
        logger.warning(f"OneDrive folder creation error: {e}")
    
    frontend_url = os.environ.get("FRONTEND_URL", "")
    return RedirectResponse(url=f"{frontend_url}/integrations?provider=microsoft&status=ok")

async def _refresh_token(user_id: str, db: AsyncSession):
    """Refresh Microsoft access token."""
    result = await db.execute(text("SELECT * FROM onedrive_credentials WHERE user_id = :uid"), {"uid": user_id})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=400, detail="OneDrive non connecte")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "refresh_token": row["refresh_token"],
                "grant_type": "refresh_token",
                "scope": SCOPES,
            }
        )
    
    if resp.status_code != 200:
        # Token revoked or expired — cleanup from DB
        logger.warning(f"OneDrive token refresh failed for user {user_id}: {resp.status_code} {resp.text[:200]}. Cleaning up.")
        await db.execute(text("DELETE FROM onedrive_credentials WHERE user_id = :uid"), {"uid": user_id})
        await db.commit()
        raise HTTPException(status_code=401, detail="Acces OneDrive revoque. Veuillez reconnecter votre OneDrive.")
    
    tokens = resp.json()
    await db.execute(text("""
        UPDATE onedrive_credentials SET access_token=:token, refresh_token=COALESCE(:refresh, onedrive_credentials.refresh_token), updated_at=:updated WHERE user_id=:uid
    """), {
        "token": tokens["access_token"],
        "refresh": tokens.get("refresh_token"),
        "updated": datetime.now(timezone.utc).isoformat(),
        "uid": user_id
    })
    await db.commit()
    return tokens["access_token"]

async def _get_access_token(user: User, db: AsyncSession) -> str:
    """Get a valid access token, refreshing if needed."""
    result = await db.execute(text("SELECT * FROM onedrive_credentials WHERE user_id = :uid"), {"uid": user.id})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=400, detail="OneDrive non connecte")
    
    try:
        return await _refresh_token(user.id, db)
    except Exception:
        return row["access_token"]

async def _ensure_folder_structure(access_token: str):
    """Create Zayado Extension IA folder structure on OneDrive."""
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        # Create root "Zayado Extension IA" folder
        resp = await client.post(
            f"{GRAPH_API}/me/drive/root/children",
            headers=headers,
            json={"name": "Zayado Extension IA", "folder": {}, "@microsoft.graph.conflictBehavior": "rename"}
        )
        if resp.status_code in [200, 201]:
            root_id = resp.json().get("id")
            for subfolder in ["Images generees", "Documents & PDF", "Workflows"]:
                await client.post(
                    f"{GRAPH_API}/me/drive/items/{root_id}/children",
                    headers=headers,
                    json={"name": subfolder, "folder": {}, "@microsoft.graph.conflictBehavior": "rename"}
                )

@onedrive_router.get("/status")
async def onedrive_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Check if OneDrive is connected."""
    try:
        result = await db.execute(text("SELECT user_id FROM onedrive_credentials WHERE user_id = :uid"), {"uid": user.id})
        row = result.first()
        return {"connected": row is not None}
    except Exception:
        return {"connected": False}

@onedrive_router.get("/files")
async def list_onedrive_files(folder_path: str = "/", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List files in OneDrive."""
    token = await _get_access_token(user, db)
    headers = {"Authorization": f"Bearer {token}"}
    
    if folder_path == "/" or folder_path == "root":
        url = f"{GRAPH_API}/me/drive/root/children"
    else:
        url = f"{GRAPH_API}/me/drive/root:/{folder_path}:/children"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params={"$top": 30, "$orderby": "name"})
    
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erreur OneDrive")
    
    data = resp.json()
    files = [{
        "id": f["id"],
        "name": f["name"],
        "size": f.get("size", 0),
        "modifiedTime": f.get("lastModifiedDateTime", ""),
        "isFolder": "folder" in f,
        "webUrl": f.get("webUrl", ""),
        "mimeType": f.get("file", {}).get("mimeType", "folder" if "folder" in f else "")
    } for f in data.get("value", [])]
    
    return {"files": files, "folder_path": folder_path}

@onedrive_router.post("/upload")
async def upload_to_onedrive(file: UploadFile = File(...), folder_path: str = "Zayado Extension IA", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Upload a file to OneDrive."""
    token = await _get_access_token(user, db)
    headers = {"Authorization": f"Bearer {token}"}
    content = await file.read()
    filename = file.filename or "upload"
    
    upload_url = f"{GRAPH_API}/me/drive/root:/{folder_path}/{filename}:/content"
    async with httpx.AsyncClient() as client:
        resp = await client.put(upload_url, headers={**headers, "Content-Type": file.content_type or "application/octet-stream"}, content=content)
    
    if resp.status_code not in [200, 201]:
        raise HTTPException(status_code=resp.status_code, detail="Upload error")
    
    result = resp.json()
    return {"id": result["id"], "name": result["name"], "webUrl": result.get("webUrl", "")}


@onedrive_router.post("/ensure-folders")
async def ensure_onedrive_folders(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create the Zayado Extension IA folder structure on OneDrive."""
    token = await _get_access_token(user, db)
    await _ensure_folder_structure(token)
    return {"status": "ok", "message": "Dossiers crees avec succes"}

@onedrive_router.delete("/disconnect")
async def disconnect_onedrive(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Disconnect OneDrive."""
    await db.execute(text("DELETE FROM onedrive_credentials WHERE user_id = :uid"), {"uid": user.id})
    await db.commit()
    return {"status": "disconnected"}


# ============================================================
# SharePoint via Microsoft Graph
# ============================================================

SHAREPOINT_SCOPES = "Sites.ReadWrite.All offline_access User.Read Files.ReadWrite.All"

@onedrive_router.get("/sharepoint/sites")
async def list_sharepoint_sites(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List SharePoint sites the user has access to."""
    token = await _get_access_token(user, db)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{GRAPH_API}/sites?search=*", headers=headers)
    if resp.status_code == 403:
        raise HTTPException(status_code=403, detail="Permission Sites.ReadWrite.All requise. Reconnectez OneDrive avec les nouveaux scopes.")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erreur récupération sites SharePoint")
    data = resp.json()
    sites = [{"id": s["id"], "name": s.get("displayName", s.get("name", "")), "webUrl": s.get("webUrl", ""), "description": s.get("description", "")} for s in data.get("value", [])]
    return {"sites": sites}

@onedrive_router.get("/sharepoint/sites/{site_id}/files")
async def list_sharepoint_files(site_id: str, folder_path: str = "/", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List files in a SharePoint site's document library."""
    token = await _get_access_token(user, db)
    headers = {"Authorization": f"Bearer {token}"}
    # Utilise la drive racine du site
    if folder_path == "/" or folder_path == "root":
        url = f"{GRAPH_API}/sites/{site_id}/drive/root/children"
    else:
        url = f"{GRAPH_API}/sites/{site_id}/drive/root:/{folder_path.strip('/')}:/children"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=headers, params={"$top": 50, "$orderby": "name"})
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erreur récupération fichiers SharePoint")
    data = resp.json()
    files = [{"id": f["id"], "name": f["name"], "size": f.get("size", 0), "modifiedTime": f.get("lastModifiedDateTime", ""), "isFolder": "folder" in f, "webUrl": f.get("webUrl", ""), "mimeType": f.get("file", {}).get("mimeType", "folder" if "folder" in f else "")} for f in data.get("value", [])]
    return {"files": files, "site_id": site_id, "folder_path": folder_path}

@onedrive_router.post("/sharepoint/sites/{site_id}/upload")
async def upload_to_sharepoint(site_id: str, file: UploadFile = File(...), folder_path: str = "Zayado Extension IA", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Upload a file to a SharePoint site."""
    token = await _get_access_token(user, db)
    headers = {"Authorization": f"Bearer {token}"}
    content = await file.read()
    filename = file.filename or "upload"
    upload_url = f"{GRAPH_API}/sites/{site_id}/drive/root:/{folder_path}/{filename}:/content"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.put(upload_url, headers={**headers, "Content-Type": file.content_type or "application/octet-stream"}, content=content)
    if resp.status_code not in [200, 201]:
        raise HTTPException(status_code=resp.status_code, detail="Erreur upload SharePoint")
    result = resp.json()
    return {"id": result["id"], "name": result["name"], "webUrl": result.get("webUrl", "")}

@onedrive_router.post("/sharepoint/autosave")
async def sharepoint_autosave(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save content to a SharePoint site (body JSON)."""
    body = await request.json()
    site_id = body.get("site_id", "")
    content = body.get("content", "")
    content_type = body.get("content_type", "text")
    filename = body.get("filename", "")
    if not site_id:
        raise HTTPException(status_code=400, detail="site_id requis")
    token = await _get_access_token(user, db)
    headers = {"Authorization": f"Bearer {token}"}
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    folder = "Zayado Extension IA/Documents & PDF"
    if content_type == "image":
        folder = "Zayado Extension IA/Images generees"
    ext = ".md" if "# " in content or "**" in content else ".txt"
    fname = filename or f"document_{timestamp}{ext}"
    upload_url = f"{GRAPH_API}/sites/{site_id}/drive/root:/{folder}/{fname}:/content"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.put(upload_url, headers={**headers, "Content-Type": "text/plain"}, content=content.encode("utf-8"))
    if resp.status_code not in [200, 201]:
        raise HTTPException(status_code=resp.status_code, detail="Erreur sauvegarde SharePoint")
    result = resp.json()
    return {"id": result["id"], "name": result["name"], "webUrl": result.get("webUrl", ""), "autosaved": True}

@onedrive_router.post("/sharepoint/ensure-folders/{site_id}")
async def ensure_sharepoint_folders(site_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create Zayado folder structure on SharePoint site."""
    token = await _get_access_token(user, db)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{GRAPH_API}/sites/{site_id}/drive/root/children", headers=headers, json={"name": "Zayado Extension IA", "folder": {}, "@microsoft.graph.conflictBehavior": "rename"})
        if resp.status_code in [200, 201]:
            root_id = resp.json().get("id")
            for subfolder in ["Images generees", "Documents & PDF", "Workflows", "Conversations"]:
                await client.post(f"{GRAPH_API}/sites/{site_id}/drive/items/{root_id}/children", headers=headers, json={"name": subfolder, "folder": {}, "@microsoft.graph.conflictBehavior": "rename"})
    return {"status": "ok", "message": "Dossiers SharePoint créés"}
