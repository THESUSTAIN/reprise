"""WordPress site settings sync (favicon + meta).

Bidirectional pull/push avec WP REST API.
- GET  /api/wp/site-settings        : tous publics → renvoie favicon + meta (cache léger).
- PUT  /api/wp/site-settings        : admin seulement → push vers WP.
- POST /api/wp/site-icon            : admin seulement → upload une image et la définit comme site_icon.

WordPress side:
- Endpoint : /wp-json/wp/v2/settings (auth Basic via Application Password)
- Champs synchronisés : title, description, site_icon (ID), site_icon_url (lecture seule)
"""
import os
import base64
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from deps import get_admin_user

logger = logging.getLogger(__name__)
wp_router = APIRouter(tags=["wp-sync"])

WP_BASE_URL = os.environ.get("WP_BASE_URL", "").rstrip("/")
WP_USERNAME = os.environ.get("WP_USERNAME", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")


def _wp_auth_header() -> dict:
    if not (WP_USERNAME and WP_APP_PASSWORD):
        raise HTTPException(status_code=500, detail="WordPress credentials non configurées")
    token = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def _get_site_icon_url(client: httpx.AsyncClient, icon_id: int) -> Optional[str]:
    if not icon_id:
        return None
    try:
        r = await client.get(
            f"{WP_BASE_URL}/wp-json/wp/v2/media/{icon_id}",
            headers=_wp_auth_header(),
            timeout=10.0,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("source_url")
    except Exception as e:
        logger.warning("Failed to fetch site_icon media %s: %s", icon_id, e)
    return None


class SiteSettings(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    site_icon: Optional[int] = None    # WP media ID
    language: Optional[str] = None


@wp_router.get("/wp/site-settings")
async def get_wp_site_settings():
    """Renvoie un sous-ensemble des site settings WP (lecture publique).
    Utilisé par le public-site pour afficher favicon + meta dynamiques."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{WP_BASE_URL}/wp-json/wp/v2/settings",
                headers=_wp_auth_header(),
                timeout=10.0,
            )
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPError as e:
            logger.error("WP settings fetch error: %s", e)
            raise HTTPException(status_code=502, detail="Impossible de joindre WordPress")
        icon_id = data.get("site_icon") or 0
        icon_url = await _get_site_icon_url(client, icon_id) if icon_id else None
        return {
            "title": data.get("title"),
            "description": data.get("description"),
            "language": data.get("language"),
            "site_icon": icon_id,
            "site_icon_url": icon_url,
            "url": data.get("url"),
        }


@wp_router.put("/wp/site-settings")
async def update_wp_site_settings(body: SiteSettings, admin=Depends(get_admin_user)):
    """Met à jour les site settings sur WordPress (admin seulement)."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    payload = {k: v for k, v in body.dict().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{WP_BASE_URL}/wp-json/wp/v2/settings",
                headers={**_wp_auth_header(), "Content-Type": "application/json"},
                json=payload,
                timeout=15.0,
            )
            r.raise_for_status()
            return {"status": "ok", "wp": r.json()}
        except httpx.HTTPError as e:
            logger.error("WP settings update error: %s", e)
            raise HTTPException(status_code=502, detail=f"Échec mise à jour WP: {e}")


@wp_router.post("/wp/site-icon")
async def upload_site_icon(file: UploadFile = File(...), admin=Depends(get_admin_user)):
    """Upload une image vers la médiathèque WordPress puis la définit comme site_icon (favicon)."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image trop volumineuse (>5 Mo)")

    async with httpx.AsyncClient() as client:
        # 1. Upload to WP media library
        try:
            r = await client.post(
                f"{WP_BASE_URL}/wp-json/wp/v2/media",
                headers={
                    **_wp_auth_header(),
                    "Content-Disposition": f'attachment; filename="{file.filename or "site-icon.png"}"',
                    "Content-Type": file.content_type,
                },
                content=content,
                timeout=30.0,
            )
            r.raise_for_status()
            media = r.json()
            media_id = media.get("id")
        except httpx.HTTPError as e:
            logger.error("WP media upload error: %s — body=%s", e, getattr(e, "response", None) and e.response.text[:300])
            raise HTTPException(status_code=502, detail="Échec upload média WP")

        # 2. Set as site_icon
        try:
            r2 = await client.post(
                f"{WP_BASE_URL}/wp-json/wp/v2/settings",
                headers={**_wp_auth_header(), "Content-Type": "application/json"},
                json={"site_icon": media_id},
                timeout=15.0,
            )
            r2.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Could not set site_icon: %s", e)

        return {
            "status": "ok",
            "media_id": media_id,
            "url": media.get("source_url"),
        }


# ───────────────────────────────────────────────────────────────────────────
# Pages publiques (Gutenberg) — pull from WP /wp-json/wp/v2/pages?slug={slug}
# ───────────────────────────────────────────────────────────────────────────

# Simple in-memory cache (TTL 5 min) — to keep pull-WP→React snappy
import time as _t
_wp_cache: dict = {}  # key → (expires_ts, payload)
_WP_TTL_S = 30        # 30 s — propagation rapide sans surcharger WP


def _cache_get(key: str):
    v = _wp_cache.get(key)
    if v and v[0] > _t.time():
        return v[1]
    if v:
        _wp_cache.pop(key, None)
    return None


def _cache_set(key: str, payload):
    _wp_cache[key] = (_t.time() + _WP_TTL_S, payload)


@wp_router.get("/wp/page/{slug}")
async def get_wp_page(slug: str):
    """Public — Pull a WP page by slug (Gutenberg HTML + Yoast SEO meta if available)."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    cached = _cache_get(f"page:{slug}")
    if cached is not None:
        return cached
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{WP_BASE_URL}/wp-json/wp/v2/pages",
                params={"slug": slug, "_embed": "true"},
                headers=_wp_auth_header(),
                timeout=10.0,
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                payload = {"slug": slug, "exists": False}
                _cache_set(f"page:{slug}", payload)
                return payload
            page = data[0]
            payload = {
                "slug": slug, "exists": True,
                "id": page.get("id"),
                "title": (page.get("title") or {}).get("rendered", ""),
                "content_html": (page.get("content") or {}).get("rendered", ""),
                "excerpt_html": (page.get("excerpt") or {}).get("rendered", ""),
                "modified": page.get("modified"),
                "yoast": {
                    "title": page.get("yoast_head_json", {}).get("title"),
                    "description": page.get("yoast_head_json", {}).get("description"),
                    "canonical": page.get("yoast_head_json", {}).get("canonical"),
                    "og_image": (page.get("yoast_head_json", {}).get("og_image") or [{}])[0].get("url"),
                } if page.get("yoast_head_json") else None,
            }
            _cache_set(f"page:{slug}", payload)
            return payload
        except httpx.HTTPError as e:
            logger.error("WP page %s error: %s", slug, e)
            raise HTTPException(status_code=502, detail=f"WP page {slug} indisponible")


@wp_router.put("/wp/page/{slug}")
async def upsert_wp_page(slug: str, body: dict, admin=Depends(get_admin_user)):
    """Admin — Create or update a WP page (by slug) with title/content + Yoast meta."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    async with httpx.AsyncClient() as client:
        # Find existing page
        page_id = None
        try:
            r = await client.get(f"{WP_BASE_URL}/wp-json/wp/v2/pages",
                                 params={"slug": slug}, headers=_wp_auth_header(), timeout=10.0)
            r.raise_for_status()
            data = r.json()
            if data:
                page_id = data[0].get("id")
        except httpx.HTTPError as e:
            logger.warning("WP page lookup %s: %s", slug, e)

        payload = {
            "slug": slug,
            "status": "publish",
            "title": body.get("title", ""),
            "content": body.get("content_html", ""),
        }
        # Yoast SEO meta (works if Yoast SEO REST API is enabled)
        if body.get("yoast"):
            payload["meta"] = {
                "_yoast_wpseo_title": body["yoast"].get("title", ""),
                "_yoast_wpseo_metadesc": body["yoast"].get("description", ""),
                "_yoast_wpseo_canonical": body["yoast"].get("canonical", ""),
            }
        try:
            url = f"{WP_BASE_URL}/wp-json/wp/v2/pages" + (f"/{page_id}" if page_id else "")
            r = await client.request(
                "POST" if not page_id else "PUT",
                url,
                headers={**_wp_auth_header(), "Content-Type": "application/json"},
                json=payload, timeout=20.0,
            )
            r.raise_for_status()
            _wp_cache.pop(f"page:{slug}", None)  # invalidate cache
            return {"status": "ok", "id": r.json().get("id"), "slug": slug, "action": "updated" if page_id else "created"}
        except httpx.HTTPError as e:
            logger.error("WP page push %s error: %s", slug, e)
            raise HTTPException(status_code=502, detail=f"Push WP /{slug} échoué")


# ───────────────────────────────────────────────────────────────────────────
# WooCommerce — public products pull (via WooCommerce REST API or WP /products)
# ───────────────────────────────────────────────────────────────────────────

@wp_router.get("/wp/products")
async def get_woo_products(per_page: int = 24, page: int = 1, category: str = ""):
    """Public — Pull WooCommerce products (uses WP REST proxy if available).
    Returns simplified shape ready for the React Boutique."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    cache_key = f"products:{page}:{per_page}:{category}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    async with httpx.AsyncClient() as client:
        # Try WooCommerce REST API first (requires consumer key/secret)
        # Fallback: WP REST API for product post type
        try:
            params = {"per_page": min(per_page, 100), "page": page}
            if category:
                params["category"] = category
            r = await client.get(
                f"{WP_BASE_URL}/wp-json/wc/v3/products",
                params=params,
                headers=_wp_auth_header(),  # Basic auth fallback (also OK for WC if user has admin)
                timeout=15.0,
            )
            if r.status_code == 200:
                items = r.json()
                payload = {
                    "items": [
                        {
                            "id": p.get("id"),
                            "slug": p.get("slug"),
                            "name": p.get("name"),
                            "permalink": p.get("permalink"),
                            "price": p.get("price"),
                            "regular_price": p.get("regular_price"),
                            "sale_price": p.get("sale_price"),
                            "on_sale": p.get("on_sale"),
                            "short_description": p.get("short_description", ""),
                            "image": (p.get("images") or [{}])[0].get("src", ""),
                            "categories": [c.get("name") for c in (p.get("categories") or [])],
                            "stock_status": p.get("stock_status"),
                        }
                        for p in items
                    ],
                    "total": int(r.headers.get("X-WP-Total", len(items))),
                    "total_pages": int(r.headers.get("X-WP-TotalPages", 1)),
                    "source": "woocommerce",
                }
                _cache_set(cache_key, payload)
                return payload
        except httpx.HTTPError as e:
            logger.warning("WC products error: %s", e)

        # Fallback: empty list with explanatory message
        payload = {"items": [], "total": 0, "total_pages": 0, "source": "fallback",
                   "note": "WooCommerce REST API non disponible — vérifiez les clés WC consumer/secret"}
        _cache_set(cache_key, payload)
        return payload


@wp_router.get("/wp/product/{slug}")
async def get_woo_product(slug: str):
    """Public — Pull single WooCommerce product by slug."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    cached = _cache_get(f"product:{slug}")
    if cached is not None:
        return cached
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{WP_BASE_URL}/wp-json/wc/v3/products",
                params={"slug": slug},
                headers=_wp_auth_header(),
                timeout=10.0,
            )
            if r.status_code == 200 and r.json():
                p = r.json()[0]
                payload = {
                    "id": p.get("id"), "slug": p.get("slug"), "name": p.get("name"),
                    "permalink": p.get("permalink"),
                    "price": p.get("price"), "regular_price": p.get("regular_price"),
                    "sale_price": p.get("sale_price"), "on_sale": p.get("on_sale"),
                    "description": p.get("description", ""),
                    "short_description": p.get("short_description", ""),
                    "images": [{"src": i.get("src"), "alt": i.get("alt")} for i in (p.get("images") or [])],
                    "categories": [{"id": c.get("id"), "name": c.get("name"), "slug": c.get("slug")} for c in (p.get("categories") or [])],
                    "stock_status": p.get("stock_status"),
                    "attributes": p.get("attributes", []),
                }
                _cache_set(f"product:{slug}", payload)
                return payload
        except httpx.HTTPError as e:
            logger.warning("WC product %s error: %s", slug, e)
        raise HTTPException(status_code=404, detail="Produit introuvable")


@wp_router.post("/wp/cache/clear")
async def clear_wp_cache(admin=Depends(get_admin_user)):
    """Admin — Force cache flush (utile si WP webhook ou si modif côté admin WP).
    Idéalement appelé par un webhook WP `post_save` → trigger /wp/cache/clear."""
    n = len(_wp_cache)
    _wp_cache.clear()
    return {"status": "ok", "cleared": n}


# ───────────────────────────────────────────────────────────────────────────
# Sync React → WP : pousse le contenu seed (depuis seed_wp_pages.py)
# vers WordPress. À appeler depuis admin UI ou au démarrage du backend.
# ───────────────────────────────────────────────────────────────────────────
@wp_router.post("/wp/sync-react-to-wp")
async def sync_react_to_wp(force: bool = True, admin=Depends(get_admin_user)):
    """Admin — Pousse le contenu React (script seed_wp_pages.py) vers WP.

    Args:
        force: True = écrase le contenu existant (utile après refonte React)
               False = ne crée que les pages absentes (préserve les edits WP)
    """
    import sys
    sys.path.insert(0, "/app/scripts")
    try:
        from seed_wp_pages import sync_all_pages_to_wp
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"seed_wp_pages.py introuvable : {e}")
    stats = sync_all_pages_to_wp(force=bool(force))
    # Invalider le cache pour que les changements soient immédiats côté React
    _wp_cache.clear()
    return stats


# ───────────────────────────────────────────────────────────────────────────
# Webhook PUBLIC (avec secret token) — appelé par WP sur save_post/transition
# pour invalider le cache instantanément côté React. Pas d'auth admin requise
# car WordPress n'a pas de JWT — on protège via un secret partagé.
# ───────────────────────────────────────────────────────────────────────────

WP_WEBHOOK_SECRET = os.environ.get("WP_WEBHOOK_SECRET", "")


@wp_router.post("/wp/webhook/invalidate")
async def wp_webhook_invalidate(secret: str = "", slug: str = "", scope: str = "all"):
    """Webhook public appelé par WordPress quand une page/post est publié(e)
    ou modifié(e). Invalide le cache du backend pour que la prochaine requête
    React récupère la dernière version depuis WP.

    Usage côté WP (mu-plugin) — voir docs/wp-mu-plugin.php :
        wp_remote_post(
            'https://app.zayado.net/api/wp/webhook/invalidate?secret=XXX',
            ['body' => ['slug' => $slug, 'scope' => 'page']]
        );

    Args:
        secret: doit matcher WP_WEBHOOK_SECRET (env)
        slug:   slug spécifique à invalider (optionnel)
        scope:  'page' | 'product' | 'all' (defaut 'all')
    """
    if not WP_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="WP_WEBHOOK_SECRET non configuré côté serveur")
    if secret != WP_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Secret invalide")

    before = len(_wp_cache)
    if slug:
        # Cible un slug particulier (page ou produit)
        _wp_cache.pop(f"page:{slug}", None)
        _wp_cache.pop(f"product:{slug}", None)
        return {"status": "ok", "invalidated": [f"page:{slug}", f"product:{slug}"], "remaining": len(_wp_cache)}
    if scope == "page":
        keys = [k for k in _wp_cache.keys() if k.startswith("page:")]
    elif scope == "product":
        keys = [k for k in _wp_cache.keys() if k.startswith("product:")]
    else:
        keys = list(_wp_cache.keys())
    for k in keys:
        _wp_cache.pop(k, None)
    return {"status": "ok", "invalidated_count": len(keys), "scope": scope, "remaining": len(_wp_cache), "before": before}


# ───────────────────────────────────────────────────────────────────────────
# Liste toutes les pages WP publiées — utile pour debug + UI admin "Quel slug ?"
# ───────────────────────────────────────────────────────────────────────────

@wp_router.get("/wp/pages")
async def list_wp_pages(per_page: int = 50):
    """Public — Liste toutes les pages WP publiées (id, slug, titre, date modif)."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    cached = _cache_get("pages_list")
    if cached is not None:
        return cached
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{WP_BASE_URL}/wp-json/wp/v2/pages",
                params={"per_page": min(per_page, 100), "status": "publish", "_fields": "id,slug,title,modified,link"},
                headers=_wp_auth_header(),
                timeout=10.0,
            )
            r.raise_for_status()
            items = [
                {
                    "id": p.get("id"),
                    "slug": p.get("slug"),
                    "title": (p.get("title") or {}).get("rendered", ""),
                    "modified": p.get("modified"),
                    "link": p.get("link"),
                }
                for p in r.json()
            ]
            payload = {"items": items, "total": len(items)}
            _cache_set("pages_list", payload)
            return payload
        except httpx.HTTPError as e:
            logger.error("WP pages list error: %s", e)
            raise HTTPException(status_code=502, detail="Liste pages WP indisponible")


@wp_router.get("/wp/posts")
async def list_wp_posts(per_page: int = 20):
    """Public — Liste les articles WP publiés (blog)."""
    if not WP_BASE_URL:
        raise HTTPException(status_code=500, detail="WP_BASE_URL non configuré")
    cached = _cache_get(f"posts:{per_page}")
    if cached is not None:
        return cached
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{WP_BASE_URL}/wp-json/wp/v2/posts",
                params={"per_page": min(per_page, 100), "_embed": "wp:featuredmedia,author"},
                headers=_wp_auth_header(),
                timeout=10.0,
            )
            r.raise_for_status()
            items = []
            for p in r.json():
                emb = p.get("_embedded") or {}
                media = (emb.get("wp:featuredmedia") or [{}])[0]
                author = (emb.get("author") or [{}])[0]
                items.append({
                    "id": p.get("id"),
                    "slug": p.get("slug"),
                    "title": (p.get("title") or {}).get("rendered", ""),
                    "excerpt_html": (p.get("excerpt") or {}).get("rendered", ""),
                    "date": p.get("date"),
                    "modified": p.get("modified"),
                    "link": p.get("link"),
                    "image": media.get("source_url"),
                    "author": author.get("name"),
                })
            payload = {"items": items, "total": len(items)}
            _cache_set(f"posts:{per_page}", payload)
            return payload
        except httpx.HTTPError as e:
            logger.error("WP posts list error: %s", e)
            raise HTTPException(status_code=502, detail="Articles WP indisponibles")

