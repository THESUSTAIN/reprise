"""
Stockage objet Emergent (S3-compatible) — remplace l'écriture des fichiers
uploadés sur le disque du pod (éphémère sur Railway / redéploiements).

Utilise EMERGENT_LLM_KEY. Session-scoped storage_key, initialisé à la demande.
"""
import os
import logging
import httpx

logger = logging.getLogger("storage")

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
APP_NAME = "zayado"

_storage_key = None

MIME_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml",
    "ico": "image/x-icon", "pdf": "application/pdf", "json": "application/json",
    "csv": "text/csv", "txt": "text/plain", "md": "text/markdown",
    "xml": "application/xml", "zip": "application/zip",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def guess_content_type(ext: str) -> str:
    return MIME_TYPES.get((ext or "").lstrip(".").lower(), "application/octet-stream")


async def _init(force: bool = False) -> str:
    """Récupère (et met en cache) le storage_key de session."""
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    if not EMERGENT_KEY:
        raise RuntimeError("EMERGENT_LLM_KEY manquant — stockage objet indisponible")
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY})
        r.raise_for_status()
        _storage_key = r.json()["storage_key"]
    return _storage_key


async def put_object(path: str, data: bytes, content_type: str = "application/octet-stream") -> dict:
    """Envoie des octets vers le stockage objet. Retourne {path,size,etag}."""
    key = await _init()
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.put(f"{STORAGE_URL}/objects/{path}",
                        headers={"X-Storage-Key": key, "Content-Type": content_type},
                        content=data)
        if r.status_code == 403:
            key = await _init(force=True)
            r = await c.put(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key, "Content-Type": content_type},
                            content=data)
        r.raise_for_status()
        return r.json()


async def get_object(path: str):
    """Télécharge des octets. Retourne (bytes, content_type)."""
    key = await _init()
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key})
        if r.status_code == 403:
            key = await _init(force=True)
            r = await c.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key})
        r.raise_for_status()
        return r.content, r.headers.get("Content-Type", "application/octet-stream")


async def init_storage_startup():
    try:
        await _init()
        logger.info("Emergent object storage initialisé")
    except Exception as e:
        logger.warning(f"Init stockage objet différé (sera réessayé à la demande): {e}")
