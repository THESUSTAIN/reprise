"""
news_digest.py — Flux d'actualité réel, personnalisé par marché (backlog #13).

Demande initiale : « ce serait bien si c'était l'utilisateur qui choisit
[son marché] ... user choisit marché Français, alors tout son cockpit
s'actualise en conséquence avec les bons RSS, même les actualités de son
secteur (via 2 ou 3 flux) ».

Choix technique — IMPORTANT : la première version testée ici utilisait
`news.google.com/rss/search` (paramétrable par pays/mot-clé, séduisant sur
le papier). Le `robots.txt` de Google interdit explicitement l'accès
automatisé à ce endpoint : le construire dans un produit qui l'interroge
en continu depuis un serveur, c'est prendre un risque de conformité et de
blocage d'IP pour rien. Écarté.

À la place : flux RSS officiels de lemonde.fr, publiés et documentés par
Le Monde lui-même pour la syndication, vérifiés actifs (dernière
publication récente, source : catalogue de flux surveillé) au moment où ce
module a été écrit (août 2026). Chaque marché a jusqu'à 2 flux : l'actualité
du pays + l'actualité économique générale.

## Limite assumée
Le Monde ne publie pas de flux RSS par secteur d'activité (Tech, Retail,
Artisanat...) — seulement par pays/région/thème général. La demande initiale
voulait aussi une déclinaison par secteur ; ce n'est PAS fait ici faute de
source vérifiée. `market` seul pilote le digest pour l'instant. Si une
source RSS sectorielle fiable est identifiée plus tard, l'ajouter à
`MARKETS[...]["economy_feed"]` ou comme 3e flux ne demande aucun changement
de schéma.
"""
import asyncio
import logging
from datetime import datetime, timezone

import feedparser
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

logger = logging.getLogger("news_digest")
router = APIRouter(prefix="/api/news", tags=["news"])

# ── Marchés supportés ───────────────────────────────────────────────────
# Flux vérifiés actifs (lemonde.fr, syndication officielle) : France en
# premier (marché principal), + marchés africains francophones prioritaires
# pour le go-to-market (mémoire produit : Afrique en 1er pour la pub
# payante). "economy_feed" est partagé (flux Afrique-économie) quand aucun
# flux économie dédié au pays n'existe dans le catalogue lemonde.fr — c'est
# le cas pour tous les marchés hors France ci-dessous, limite assumée.
_ECONOMIE_FR = "https://www.lemonde.fr/economie/rss_full.xml"
_ECONOMIE_AFRIQUE = "https://www.lemonde.fr/afrique-economie/rss_full.xml"

MARKETS = {
    "france":      {"label": "France",                  "country_feed": "https://www.lemonde.fr/economie-francaise/rss_full.xml", "economy_feed": _ECONOMIE_FR},
    "senegal":     {"label": "Sénégal",                  "country_feed": "https://www.lemonde.fr/senegal/rss_full.xml",           "economy_feed": _ECONOMIE_AFRIQUE},
    "cote_ivoire": {"label": "Côte d'Ivoire",            "country_feed": "https://www.lemonde.fr/cote-d-ivoire/rss_full.xml",     "economy_feed": _ECONOMIE_AFRIQUE},
    "cameroun":    {"label": "Cameroun",                 "country_feed": "https://www.lemonde.fr/cameroun/rss_full.xml",          "economy_feed": _ECONOMIE_AFRIQUE},
    "maroc":       {"label": "Maroc",                    "country_feed": "https://www.lemonde.fr/maroc/rss_full.xml",             "economy_feed": _ECONOMIE_AFRIQUE},
    "afrique_dev": {"label": "Afrique (développement)",  "country_feed": "https://www.lemonde.fr/developpement/rss_full.xml",     "economy_feed": _ECONOMIE_AFRIQUE},
    "belgique":    {"label": "Belgique",                 "country_feed": "https://www.lemonde.fr/belgique/rss_full.xml",          "economy_feed": _ECONOMIE_FR},
}
DEFAULT_MARKET = "france"


def _build_feed_urls(market_key: str) -> list:
    m = MARKETS.get(market_key, MARKETS[DEFAULT_MARKET])
    urls = [m["country_feed"]]
    if m["economy_feed"] not in urls:
        urls.append(m["economy_feed"])
    return urls


async def _fetch_feed(client: httpx.AsyncClient, url: str) -> list:
    """Récupère et parse un flux. Best-effort : un flux en échec est ignoré
    silencieusement (logué) plutôt que de faire échouer tout le digest."""
    try:
        r = await client.get(url, timeout=6.0, headers={"User-Agent": "Mozilla/5.0 (compatible; ZayadoBot/1.0; +https://zayado.net)"})
        r.raise_for_status()
        parsed = await asyncio.to_thread(feedparser.parse, r.content)  # parsing XML synchrone, hors event loop
        items = []
        for e in parsed.entries[:10]:
            published = None
            if getattr(e, "published_parsed", None):
                try:
                    published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                except Exception:
                    published = None
            items.append({
                "title": getattr(e, "title", "").strip(),
                "link": getattr(e, "link", ""),
                "source": "Le Monde",
                "published_at": published,
            })
        return items
    except Exception as exc:
        logger.warning(f"[news_digest] Échec récupération flux {url}: {exc}")
        return []


@router.get("/markets")
async def list_markets():
    """Liste des marchés disponibles pour le sélecteur frontend."""
    return {"markets": [{"id": k, "label": v["label"]} for k, v in MARKETS.items()], "default": DEFAULT_MARKET}


class MarketUpdate(BaseModel):
    market: str


@router.get("/market")
async def get_market(user: User = Depends(get_current_user)):
    return {"market": (user.settings or {}).get("market", DEFAULT_MARKET)}


@router.put("/market")
async def set_market(body: MarketUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if body.market not in MARKETS:
        return {"ok": False, "error": "Marché inconnu"}
    await db.execute(update(User).where(User.id == user.id).values(
        settings={**(user.settings or {}), "market": body.market}
    ))
    await db.commit()
    return {"ok": True, "market": body.market}


@router.get("/digest")
async def get_digest(user: User = Depends(get_current_user)):
    """Digest d'actualité personnalisé selon le marché choisi par
    l'utilisateur (settings.market, France par défaut). Flux fusionnés,
    dédupliqués par titre, triés par date."""
    market_key = (user.settings or {}).get("market", DEFAULT_MARKET)
    urls = _build_feed_urls(market_key)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        results = await asyncio.gather(*[_fetch_feed(client, u) for u in urls])

    seen_titles = set()
    merged = []
    for items in results:
        for it in items:
            key = (it["title"] or "").lower().strip()
            if not key or key in seen_titles:
                continue
            seen_titles.add(key)
            merged.append(it)

    merged.sort(key=lambda it: it["published_at"] or "", reverse=True)

    return {
        "market": market_key,
        "items": merged[:15],
        "has_data": bool(merged),
    }
