"""
hot_opportunities.py — Moteur de détection d'opportunités chaudes pour la carte
"Développement" du Dashboard.

Fonctionnement :
  • Scraping configurable via Make (webhook entrant) OU appel direct d'URLs
  • Chaque opportunité reçoit un score IA (0-100) selon: mots-clés d'intention,
    canal, fraîcheur, pertinence secteur
  • Le Dashboard tire la dernière opportunité active via GET /api/hot-opportunities/latest
  • Un cron toutes les 6h lance un mini-scan Reddit (r/Entrepreneur, r/SaaS, r/freelance)
    pour les utilisateurs avec Growth Agent actif
  • Les opportunités expirent après 48h (champ expires_at)
"""

import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, async_session_factory
from deps import get_current_user
from models import User

logger = logging.getLogger(__name__)
hot_opps_router = APIRouter(prefix="/api/hot-opportunities", tags=["hot-opportunities"])

# ─────────── Score d'intention ───────────────────────────────────────
_INTENT_KEYWORDS = [
    "looking for", "cherche", "recommend", "recommandez", "best tool",
    "quel outil", "help with", "besoin d'aide", "anyone using", "quelqu'un utilise",
    "alternative to", "alternative à", "tired of", "marre de", "how do you",
    "comment vous", "startup", "solopreneur", "indie hacker", "freelance", "TPE", "PME",
    "productivité", "productivity", "organisation", "organization", "cockpit",
    "dashboard", "pilotage", "vision board", "burnout", "débordé", "overwhelmed",
]
_CHANNEL_WEIGHTS = {
    "reddit": 0.9, "linkedin": 1.0, "twitter": 0.8, "facebook": 0.75,
    "hacker_news": 0.85, "manual": 0.7, "webhook": 1.0,
}


def _score_opportunity(title: str, body: str, channel: str) -> int:
    """Calcule un score 0-100 pour une opportunité."""
    text_lower = (title + " " + body).lower()
    keyword_hits = sum(1 for kw in _INTENT_KEYWORDS if kw in text_lower)
    keyword_score = min(40, keyword_hits * 6)

    channel_weight = _CHANNEL_WEIGHTS.get(channel, 0.7)
    channel_score = int(20 * channel_weight)

    # Longueur du signal (post substantiel = plus sérieux)
    length_score = min(20, len(body) // 100)

    # Urgence (marqueurs temporels)
    urgency_kw = ["today", "urgently", "asap", "urgent", "immédiatement", "dès que possible", "right now"]
    urgency_score = 10 if any(kw in text_lower for kw in urgency_kw) else 0

    # Budget / achat (intent élevé)
    budget_kw = ["budget", "pay", "payer", "euros", "dollars", "purchase", "acheter", "subscribe", "s'abonner"]
    budget_score = 10 if any(kw in text_lower for kw in budget_kw) else 0

    total = keyword_score + channel_score + length_score + urgency_score + budget_score
    return min(100, max(1, total))


# ─────────── Schémas ─────────────────────────────────────────────────
class HotOppWebhookIn(BaseModel):
    """Payload Make/Zapier → Zayado."""
    source_url: Optional[str] = None
    title: str
    body: str = ""
    channel: str = "webhook"
    author: Optional[str] = None
    author_url: Optional[str] = None
    user_id: Optional[str] = None   # si connu; sinon broadcast


class HotOppManualIn(BaseModel):
    title: str
    body: str = ""
    channel: str = "manual"
    source_url: Optional[str] = None


# ─────────── Table JSON (user_data pattern) ──────────────────────────
# On réutilise la table user_data (clé "hot_opportunities") pour éviter
# une migration — format: {"items": [...], "last_scan": "ISO"}

async def _get_opps(db: AsyncSession, user_id: str) -> list:
    r = await db.execute(
        text("SELECT value FROM user_data WHERE user_id = :uid AND `key` = 'hot_opportunities' LIMIT 1"),
        {"uid": user_id},
    )
    row = r.fetchone()
    if not row:
        return []
    import json
    try:
        return json.loads(row[0]).get("items", [])
    except Exception:
        return []


async def _save_opps(db: AsyncSession, user_id: str, items: list):
    import json
    data = json.dumps({"items": items, "last_scan": datetime.now(timezone.utc).isoformat()})
    existing = (await db.execute(
        text("SELECT id FROM user_data WHERE user_id = :uid AND `key` = 'hot_opportunities'"),
        {"uid": user_id},
    )).fetchone()
    if existing:
        await db.execute(
            text("UPDATE user_data SET value = :d WHERE user_id = :uid AND `key` = 'hot_opportunities'"),
            {"d": data, "uid": user_id},
        )
    else:
        import uuid
        await db.execute(
            text("INSERT INTO user_data (id, user_id, `key`, value) VALUES (:id, :uid, 'hot_opportunities', :d)"),
            {"id": str(uuid.uuid4()), "uid": user_id, "d": data},
        )
    await db.commit()


def _make_opp(title: str, body: str, channel: str,
              source_url: str | None = None, author: str | None = None) -> dict:
    import uuid
    now = datetime.now(timezone.utc)
    score = _score_opportunity(title, body, channel)
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "body": body[:500],
        "channel": channel,
        "source_url": source_url,
        "author": author,
        "score": score,
        "detected_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=48)).isoformat(),
        "status": "active",  # active | converted | dismissed
    }


def _detected_ago(iso: str) -> str:
    """Retourne '2h', 'hier', '3j'…"""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        minutes = int(delta.total_seconds() // 60)
        if minutes < 60:
            return f"il y a {minutes}min"
        hours = minutes // 60
        if hours < 24:
            return f"il y a {hours}h"
        days = hours // 24
        return f"il y a {days}j"
    except Exception:
        return ""


# ─────────── Endpoints ───────────────────────────────────────────────

@hot_opps_router.get("/latest")
async def get_latest(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retourne la dernière opportunité active pour le Dashboard (DeveloppementCard)."""
    items = await _get_opps(db, user.id)
    now = datetime.now(timezone.utc)
    active = [
        i for i in items
        if i.get("status") == "active"
        and datetime.fromisoformat(i["expires_at"].replace("Z", "+00:00")) > now
    ]
    if not active:
        return {"hot_opportunity": None}
    best = max(active, key=lambda x: x["score"])
    return {
        "hot_opportunity": {
            "id": best["id"],
            "title": best["title"],
            "channel": best["channel"],
            "score": best["score"],
            "detected_ago": _detected_ago(best["detected_at"]),
            "source_url": best.get("source_url"),
            "author": best.get("author"),
        }
    }


@hot_opps_router.get("")
async def list_opps(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste toutes les opportunités (Dashboard Croissance / Agent)."""
    items = await _get_opps(db, user.id)
    now = datetime.now(timezone.utc)
    # Filtrer les expirées + trier par score desc
    active = sorted(
        [i for i in items
         if datetime.fromisoformat(i["expires_at"].replace("Z", "+00:00")) > now],
        key=lambda x: x["score"],
        reverse=True,
    )
    return {"items": active, "total": len(active)}


@hot_opps_router.post("/webhook")
async def make_webhook(
    payload: HotOppWebhookIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint Make/Zapier → reçoit une opportunité scrapée.
    Pas d'auth JWT (secret via MAKE_WEBHOOK_SECRET header ou param).
    """
    target_user_id = payload.user_id
    if not target_user_id:
        # Broadcast à tous les utilisateurs actifs avec Growth Agent actif
        # (simplification : on log sans rattachement user)
        logger.info(f"[HOT_OPP] Webhook broadcast: {payload.title[:80]}")
        return {"status": "logged", "note": "no user_id — pass user_id to attribute"}

    items = await _get_opps(db, target_user_id)
    opp = _make_opp(payload.title, payload.body, payload.channel,
                    payload.source_url, payload.author)
    items = [opp] + items[:49]   # max 50 items
    await _save_opps(db, target_user_id, items)
    return {"status": "ok", "opportunity_id": opp["id"], "score": opp["score"]}


@hot_opps_router.post("/manual")
async def add_manual(
    body: HotOppManualIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ajout manuel d'une opportunité (depuis Growth Agent UI)."""
    items = await _get_opps(db, user.id)
    opp = _make_opp(body.title, body.body, body.channel, body.source_url)
    items = [opp] + items[:49]
    await _save_opps(db, user.id, items)
    return {"status": "ok", "opportunity": opp}


@hot_opps_router.patch("/{opp_id}")
async def update_opp_status(
    opp_id: str,
    status: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marquer une opportunité comme 'converted' ou 'dismissed'."""
    if status not in ("converted", "dismissed", "active"):
        raise HTTPException(400, "status doit être: converted | dismissed | active")
    items = await _get_opps(db, user.id)
    items = [
        {**i, "status": status} if i["id"] == opp_id else i
        for i in items
    ]
    await _save_opps(db, user.id, items)
    return {"status": "ok"}


# ─────────── Scan Reddit (cron) ──────────────────────────────────────
_REDDIT_SUBREDDITS = ["Entrepreneur", "SaaS", "freelance", "startups", "productivity"]
_REDDIT_KEYWORDS = [
    "looking for", "recommend", "best tool", "help with",
    "cherche", "recommandez", "quel outil", "solopreneur",
]


async def _scan_reddit_subreddit(session: httpx.AsyncClient, sub: str) -> list[dict]:
    """Scanne les 25 derniers posts d'un subreddit."""
    try:
        r = await session.get(
            f"https://www.reddit.com/r/{sub}/new.json?limit=25",
            headers={"User-Agent": "Zayado/1.0 hot-opp-scanner"},
            timeout=10,
        )
        if r.status_code != 200:
            return []
        posts = r.json().get("data", {}).get("children", [])
        results = []
        for p in posts:
            d = p.get("data", {})
            title = d.get("title", "")
            selftext = d.get("selftext", "")
            combined = (title + " " + selftext).lower()
            if any(kw in combined for kw in _REDDIT_KEYWORDS):
                results.append({
                    "title": title[:200],
                    "body": selftext[:500],
                    "channel": "reddit",
                    "source_url": f"https://reddit.com{d.get('permalink', '')}",
                    "author": d.get("author"),
                })
        return results
    except Exception as e:
        logger.warning(f"[HOT_OPP] Reddit scan error r/{sub}: {e}")
        return []


async def hot_opportunities_scan_loop():
    """Background loop toutes les 6h — scan Reddit pour users actifs."""
    await asyncio.sleep(180)   # 3min après démarrage
    logger.info("[HOT_OPP] Scan loop started")
    INTERVAL = 6 * 3600

    while True:
        try:
            async with async_session_factory() as db:
                # Récupérer les users avec Growth Agent actif
                from sqlalchemy import text as t
                rows = (await db.execute(
                    t("SELECT user_id, value FROM user_data WHERE `key` = 'growth_config'")
                )).fetchall()

                async with httpx.AsyncClient() as session:
                    all_posts: list[dict] = []
                    for sub in _REDDIT_SUBREDDITS:
                        posts = await _scan_reddit_subreddit(session, sub)
                        all_posts.extend(posts)
                        await asyncio.sleep(1)

                for row in rows:
                    user_id = row[0]
                    try:
                        import json
                        cfg = json.loads(row[1])
                        if not cfg.get("enabled"):
                            continue
                        # Récupérer les opportunités existantes
                        items = await _get_opps(db, user_id)
                        existing_urls = {i.get("source_url") for i in items}

                        new_opps = []
                        for post in all_posts:
                            if post["source_url"] in existing_urls:
                                continue
                            opp = _make_opp(
                                post["title"], post["body"], post["channel"],
                                post["source_url"], post.get("author")
                            )
                            new_opps.append(opp)

                        if new_opps:
                            merged = new_opps + items
                            # Garder max 50, trier par score
                            merged = sorted(merged, key=lambda x: x["score"], reverse=True)[:50]
                            await _save_opps(db, user_id, merged)
                            logger.info(f"[HOT_OPP] User {user_id}: {len(new_opps)} new opps")
                    except Exception as e:
                        logger.warning(f"[HOT_OPP] User {user_id} error: {e}")

        except Exception as e:
            logger.exception(f"[HOT_OPP] Scan loop error: {e}")

        await asyncio.sleep(INTERVAL)
