"""Croissance (Growth) — endpoints backing the Croissance page.

100% SQL (SQLAlchemy async / SQLite|MySQL). Aucune dépendance MongoDB.

Persistance :
  - Réglages / config canaux : table `user_data` (KV JSON) via vision_board._get_kv/_save_kv
  - Leads / pipeline         : table JSON `user_leads` (créée à la volée)

Les blocs analytiques (market insights, Reddit SEO, alertes, concurrents…)
renvoient des états vides bien formés tant qu'aucun moteur de détection de leads
n'est branché — le frontend affiche alors des empty-states propres.

Auth : user_id dérivé du JWT (Depends(get_current_user)) — jamais fait confiance à un
paramètre de requête, y compris pour les comptes invités (qui ont eux aussi un JWT réel,
voir /api/auth/guest). Évite qu'un utilisateur puisse lire/modifier les leads d'un autre
simplement en changeant ?user_id=... dans l'URL (IDOR).
"""
import io
import csv
import json
import uuid
import re
import os
import logging
from typing import Optional
from datetime import datetime, timezone

import httpx
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User, UserConnection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/growth", tags=["growth"])

PIPELINE_STAGES = [
    {"id": "detected",   "label": "Détecté",       "color": "#4a6a9e", "bg": "#4a6a9e22"},
    {"id": "contacted",  "label": "Contacté",      "color": "#C9A449", "bg": "#C9A44922"},
    {"id": "discussing", "label": "En discussion", "color": "#8b6fbf", "bg": "#8b6fbf22"},
    {"id": "signed",     "label": "Signé ✓",       "color": "#5e8a5a", "bg": "#5e8a5a22"},
]

DEFAULT_SETTINGS = {
    "profile": {"name": "", "email": "", "niche": ""},
    "project_type": "NET",
    "agent_paused": False,
    "slack_connected": False,
    "reddit_connected": False,
    "linkedin_connected": False,
    "youtube_connected": False,
    "email_notifications": True,
    "daily_digest": {"enabled": False, "hour": "08:00", "content": []},
    "vision": "",
    "keywords": [],
    "subreddits": [],
    "sirene_naf": "",          # code NAF/APE ciblé, ex "62.01Z" (dev informatique) — vide = pas de filtre
    "sirene_departement": "",  # ex "75" — vide = France entière
}

DEFAULT_CHANNELS = {
    "whatsapp": {"webhook_url": "", "phone": ""},
    "telegram": {"bot_token": ""},
}


# ─────────────────────────────────────────────────────────────────
# Helpers KV (table user_data — colonnes: id, user_id, key, value, updated_at)
# ─────────────────────────────────────────────────────────────────
async def _get_kv(db: AsyncSession, user_id: str, key: str) -> dict | None:
    try:
        r = await db.execute(
            text("SELECT value FROM user_data WHERE user_id = :uid AND \"key\" = :k LIMIT 1"),
            {"uid": user_id, "k": key},
        )
        row = r.fetchone()
        if not row or row[0] is None:
            return None
        return json.loads(row[0]) if isinstance(row[0], str) else row[0]
    except Exception as e:
        logger.warning("growth _get_kv failed: %s", e)
        return None


async def _save_kv(db: AsyncSession, user_id: str, key: str, data: dict):
    from datetime import datetime, timezone
    value = json.dumps(data)
    now = datetime.now(timezone.utc).isoformat()
    r = await db.execute(
        text("SELECT id FROM user_data WHERE user_id = :uid AND \"key\" = :k"),
        {"uid": user_id, "k": key},
    )
    row = r.fetchone()
    if row:
        await db.execute(
            text("UPDATE user_data SET value = :v, updated_at = :u WHERE user_id = :uid AND \"key\" = :k"),
            {"v": value, "u": now, "uid": user_id, "k": key},
        )
    else:
        await db.execute(
            text("INSERT INTO user_data (id, user_id, \"key\", value, updated_at) VALUES (:id, :uid, :k, :v, :u)"),
            {"id": str(uuid.uuid4()), "uid": user_id, "k": key, "v": value, "u": now},
        )
    await db.commit()


# ─────────────────────────────────────────────────────────────────
# Helpers leads (table JSON user_leads)
# ─────────────────────────────────────────────────────────────────
async def _ensure_leads_table(db: AsyncSession):
    await db.execute(text(
        "CREATE TABLE IF NOT EXISTS user_leads ("
        "id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, "
        "data JSON NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    ))


async def _list_leads(db: AsyncSession, user_id: str) -> list:
    await _ensure_leads_table(db)
    try:
        r = await db.execute(
            text("SELECT id, data FROM user_leads WHERE user_id = :uid ORDER BY created_at DESC"),
            {"uid": user_id},
        )
        out = []
        for row in r.fetchall():
            data = row[1]
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = {}
            data = data or {}
            data.setdefault("id", row[0])
            out.append(data)
        return out
    except Exception as e:
        logger.warning("growth _list_leads failed: %s", e)
        return []


async def _save_lead(db: AsyncSession, user_id: str, lead: dict):
    await _ensure_leads_table(db)
    await db.execute(
        text("INSERT INTO user_leads (id, user_id, data) VALUES (:id, :uid, :d)"),
        {"id": lead["id"], "uid": user_id, "d": json.dumps(lead)},
    )
    await db.commit()
    from routes.analytics import track_event
    await track_event(db, user_id, "first_lead_detected", {"source": lead.get("source")})


class LeadCreateIn(BaseModel):
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    sub: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None
    stage: Optional[str] = "detected"


@router.post("/leads")
async def create_lead(body: LeadCreateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Créer un lead manuellement (ex: capture depuis l'extension navigateur)."""
    lead = {
        "id": uuid.uuid4().hex,
        "name": body.name or "Lead",
        "email": body.email,
        "company": body.company,
        "sub": body.sub or body.source or "Ajouté manuellement",
        "snippet": body.snippet or "",
        "score": 50,
        "stage": body.stage or "detected",
        "source": body.source or "manual",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await _save_lead(db, user.id, lead)
    return {"ok": True, "lead": lead}


# ─────────── Qualification structurée d'un lead (fiche assistée par IA) ───────────
# Reprend le modèle décrit dans le brief prospection : un score sur 100 basé sur
# 6 critères pondérés, une fiche justifiée (jamais une qualification inventée
# sans donnée réelle), et un statut d'aide à la décision plutôt qu'un envoi
# automatique. Rien n'est envoyé au prospect depuis cet endpoint — il ne fait
# que qualifier, l'utilisateur reste maître de la suite.
# NOTE : backend prêt, mais pas encore branché côté interface — la page
# Croissance actuelle (refonte "Radar") n'a plus de liste de prospects/cartes
# à ce jour. Direction à choisir avant de construire l'UI (voir échange précédent).
_QUALIF_WEIGHTS = {
    "cible": 25,       # le prospect correspond à la cible définie
    "probleme": 25,    # le problème correspond réellement à l'offre
    "urgence": 15,     # le besoin est actuel ou urgent
    "decision": 15,    # le prospect a le pouvoir de décision
    "budget": 10,       # le budget est compatible
    "ouverture": 10,    # ouvert à un échange / une démonstration
}


class QualifyLeadIn(BaseModel):
    notes: str = ""  # ce que l'utilisateur sait déjà du prospect — seule source d'information autorisée


@router.post("/leads/{lead_id}/qualify")
async def qualify_lead(lead_id: str, body: QualifyLeadIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    leads = await _list_leads(db, user.id)
    lead = next((l for l in leads if l.get("id") == lead_id), None)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead introuvable")

    notes = (body.notes or lead.get("snippet") or "").strip()
    if not notes:
        raise HTTPException(status_code=400, detail="Ajoutez au moins une note sur ce prospect avant de le qualifier — l'IA ne peut pas inventer d'informations.")

    system = (
        "Tu qualifies un prospect commercial UNIQUEMENT à partir des notes fournies par l'utilisateur. "
        "Tu n'inventes jamais d'information absente des notes. Pour chaque critère, tu attribues une note "
        "de 0 au poids maximum indiqué, en te basant sur ce qui est explicitement écrit — si l'information "
        "manque, mets 0 et liste le critère dans 'inconnu'. Réponds UNIQUEMENT en JSON valide, structure exacte : "
        '{"scores": {"cible": 0-25, "probleme": 0-25, "urgence": 0-15, "decision": 0-15, "budget": 0-10, "ouverture": 0-10}, '
        '"justification": "phrase courte par critère noté", "inconnu": ["critères sans information"], '
        '"prochaine_action": "action concrète recommandée"}'
    )
    user_msg = f"Notes sur le prospect « {lead.get('name', 'Lead')} » ({lead.get('company') or 'entreprise non précisée'}) :\n\n{notes}"

    try:
        from mammouth_client import chat as ai_chat
        raw = await ai_chat([{"role": "system", "content": system}, {"role": "user", "content": user_msg}], max_tokens=500, temperature=0.2)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(json)?\s*|\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
        parsed = json.loads(cleaned)
    except Exception as e:
        logger.error(f"qualify_lead AI failed for lead {lead_id}: {e}")
        raise HTTPException(status_code=502, detail="La qualification IA est indisponible pour le moment — réessayez dans un instant.")

    scores = {k: max(0, min(_QUALIF_WEIGHTS[k], int(parsed.get("scores", {}).get(k, 0)))) for k in _QUALIF_WEIGHTS}
    total = sum(scores.values())
    band = "A transmettre" if total >= 70 else "A nourrir" if total >= 40 else "Non prioritaire"

    qualification = {
        "scores": scores,
        "total": total,
        "band": band,
        "justification": parsed.get("justification", ""),
        "inconnu": parsed.get("inconnu", []),
        "prochaine_action": parsed.get("prochaine_action", ""),
        "notes_source": notes,
        "qualified_at": datetime.now(timezone.utc).isoformat(),
    }
    lead["qualification"] = qualification
    lead["score"] = total
    await db.execute(text("UPDATE user_leads SET data = :d WHERE id = :id AND user_id = :uid"),
                     {"d": json.dumps(lead), "id": lead_id, "uid": user.id})
    await db.commit()
    return {"ok": True, "qualification": qualification}


# ─────────── Détection de leads (Reddit public JSON) ───────────
_INTENT_PATTERNS = [
    r"looking for", r"recommend", r"suggestion", r"any(one)? (know|use|tried)",
    r"alternative to", r"need help", r"how do (i|you)", r"best (tool|way|app)",
    r"cherche", r"besoin", r"recommand", r"quel(le)? (outil|logiciel|appli)",
    r"conseil", r"comment (faire|puis-je)", r"aidez", r"quelqu'un",
]
_INTENT_RE = re.compile("|".join(_INTENT_PATTERNS), re.IGNORECASE)


def _score_post(title: str, body: str, keywords: list) -> tuple:
    text_all = f"{title}\n{body}".lower()
    score = 40
    if _INTENT_RE.search(text_all):
        score += 25
    if "?" in title:
        score += 15
    kw_hits = sum(1 for k in keywords if k and k.lower() in text_all)
    if kw_hits:
        score += min(18, 9 * kw_hits)
    if any(k and k.lower() in title.lower() for k in keywords):
        score += 8
    score = max(35, min(98, score))
    if score >= 75:
        intent = "Chaud — bon moment pour engager"
    elif score >= 60:
        intent = "À qualifier"
    else:
        intent = "À surveiller"
    return score, intent


async def _fetch_reddit(query: str, subreddits: list, limit: int) -> list:
    """Interroge l'API JSON publique de Reddit. Renvoie une liste de posts bruts."""
    headers = {"User-Agent": "ZayadoGrowthBot/1.0 (lead detection)"}
    posts = []
    targets = []
    if subreddits:
        for s in subreddits[:5]:
            s = s.strip().lstrip("r/").strip("/")
            if s:
                targets.append(f"https://www.reddit.com/r/{s}/search.json?q={query}&restrict_sr=1&sort=new&limit={limit}&t=month")
    else:
        targets.append(f"https://www.reddit.com/search.json?q={query}&sort=new&limit={limit}&t=month")

    async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
        for url in targets:
            try:
                r = await client.get(url)
                if r.status_code != 200:
                    logger.warning("Reddit %s -> %s", url, r.status_code)
                    continue
                for child in r.json().get("data", {}).get("children", []):
                    d = child.get("data", {})
                    if d.get("stickied") or d.get("over_18"):
                        continue
                    posts.append({
                        "id": d.get("id"),
                        "author": d.get("author") or "reddit_user",
                        "subreddit": d.get("subreddit"),
                        "title": d.get("title") or "",
                        "selftext": (d.get("selftext") or "")[:400],
                        "permalink": "https://www.reddit.com" + (d.get("permalink") or ""),
                        "created": d.get("created_utc"),
                    })
            except Exception as e:
                logger.warning("Reddit fetch failed (%s): %s", url, e)
    return posts


async def _fetch_hackernews(query: str, limit: int) -> list:
    """Interroge l'API Algolia de HackerNews (publique, sans clé, fiable depuis le cloud)."""
    posts = []
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={query}&tags=(story,comment)&hitsPerPage={limit}"
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code != 200:
                logger.warning("HN %s -> %s", url, r.status_code)
                return posts
            for h in r.json().get("hits", []):
                title = h.get("title") or h.get("story_title") or ""
                body = h.get("story_text") or h.get("comment_text") or ""
                # nettoie le HTML basique des commentaires HN
                body = re.sub(r"<[^>]+>", " ", body)[:400]
                if not (title or body):
                    continue
                posts.append({
                    "id": h.get("objectID"),
                    "author": h.get("author") or "hn_user",
                    "subreddit": "HackerNews",
                    "title": title or (body[:80] + "…"),
                    "selftext": body,
                    "permalink": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "created": h.get("created_at_i"),
                })
    except Exception as e:
        logger.warning("HN fetch failed: %s", e)
    return posts


class DetectIn(BaseModel):
    keywords: list[str] | None = None
    subreddits: list[str] | None = None
    limit: int = 15


# ─────────────────────────────────────────────────────────────────
# Modèles
# ─────────────────────────────────────────────────────────────────
class StageIn(BaseModel):
    stage: str


class EngageGenerateIn(BaseModel):
    lead_id: str | None = None
    channel: str = "reddit"


class EngageSendIn(BaseModel):
    lead_id: str | None = None
    message: str = ""
    channel: str = "reddit"


# ─────────────────────────────────────────────────────────────────
# GET /api/growth — vue d'ensemble (dashboard + campagnes + analytics)
# ─────────────────────────────────────────────────────────────────
@router.get("")
async def growth_all(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    leads = await _list_leads(db, user_id)
    hot = sum(1 for l in leads if (l.get("score") or 0) >= 85)

    # Campagnes : regroupe les leads par 'campaign' (défaut "Tous les leads")
    by_campaign: dict[str, list] = {}
    for l in leads:
        cid = l.get("campaign") or "all"
        by_campaign.setdefault(cid, []).append({
            "id": l.get("id"),
            "name": l.get("name", "Lead"),
            "sub": l.get("sub") or l.get("source") or "",
            "date": l.get("date") or "",
            "intent": l.get("intent") or "À qualifier",
            "score": l.get("score") or 0,
        })
    campaigns = [{"id": cid, "name": "Tous les leads" if cid == "all" else cid, "leads": len(v)}
                 for cid, v in by_campaign.items()]
    if not campaigns:
        campaigns = [{"id": "all", "name": "Tous les leads", "leads": 0}]
        by_campaign = {"all": []}

    # Groupes par intention (backlog: la page Croissance avait 4 cartes qui
    # renvoyaient des tableaux vides EN PERMANENCE, pas juste pour un compte
    # neuf — repérée pendant une correction de responsive. Calculées ici à
    # partir des vrais leads (déjà en base), pas de valeur inventée.
    INTENT_COLORS = ["#C9A449", "#8b6fbf", "#4a6a9e", "#5e8a5a", "#d97a4e", "#4fa3c7"]
    intent_buckets: dict[str, list] = {}
    for l in leads:
        intent = l.get("intent") or "À qualifier"
        intent_buckets.setdefault(intent, []).append(l)

    intent_groups = []
    for i, (intent, items) in enumerate(sorted(intent_buckets.items(), key=lambda kv: -len(kv[1]))[:6]):
        color = INTENT_COLORS[i % len(INTENT_COLORS)]
        intent_groups.append({
            "key": intent, "label": intent, "color": color, "count": len(items),
            "leads": [
                {"name": it.get("name", "Lead"), "score": it.get("score") or 0,
                 "sub": it.get("sub") or it.get("source") or "", "snippet": it.get("snippet", "")}
                for it in sorted(items, key=lambda x: -(x.get("score") or 0))[:3]
            ],
        })
    lead_clusters = [{"label": g["label"], "count": g["count"], "color": g["color"]} for g in intent_groups]

    market_insights = [
        {"title": "Leads actifs", "value": str(len(leads)), "desc": "Total dans le pipeline", "tone": "navy"},
        {"title": "Prospects chauds", "value": str(hot), "desc": "Score ≥ 85", "tone": "terra" if hot > 0 else "gold"},
        {"title": "Sources actives", "value": str(len(campaigns)), "desc": "Canaux de détection connectés", "tone": "sage"},
    ]

    return {
        "dashboard": {
            "totals": {"leads": len(leads), "hot": hot},
            "market_insights": market_insights,
            "intent_groups": intent_groups,
            "recommended_actions": [],
            "lead_clusters": lead_clusters,
            "pain_requests": [],
            "competitor_signals": [],
        },
        "campaigns": campaigns,
        "leads_by_campaign": by_campaign,
        "reddit_seo": [],
        "conversations": {
            "kpis": {"dms_sent": 0, "replies": 0, "reply_rate": 0, "awaiting": 0, "queued": 0},
            "trend": [],
            "items": [],
        },
        "alerts": [],
        "competitors": {"timeline": [], "active": [], "products": [], "viral": []},
        "insights": {
            "over_time": [], "weekly": [], "top_subreddits": [],
            "top_keywords": [], "campaign_perf": [],
        },
    }


# ─────────────────────────────────────────────────────────────────
# Détection automatique de leads
# ─────────────────────────────────────────────────────────────────
@router.post("/detect")
async def detect_leads(body: DetectIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    settings = {**DEFAULT_SETTINGS, **(await _get_kv(db, user_id, "growth_settings") or {})}
    keywords = body.keywords if body.keywords is not None else (settings.get("keywords") or [])
    subreddits = body.subreddits if body.subreddits is not None else (settings.get("subreddits") or [])
    # Fallback : dérive un mot-clé de la niche si rien n'est fourni
    if not keywords:
        niche = (settings.get("profile") or {}).get("niche") or settings.get("vision") or ""
        keywords = [w for w in re.split(r"[,\s]+", niche) if len(w) > 3][:3]
    if not keywords:
        return {"new": 0, "scanned": 0, "error": "Ajoutez au moins un mot-clé (ou une niche) dans les Réglages."}

    query = " OR ".join(f'"{k}"' if " " in k else k for k in keywords[:5])
    hn_query = " ".join(keywords[:3])
    reddit_posts = await _fetch_reddit(query, subreddits, min(body.limit, 25))
    hn_posts = await _fetch_hackernews(hn_query, min(body.limit, 25))
    posts = reddit_posts + hn_posts
    if not posts:
        return {"new": 0, "scanned": 0, "error": "Aucun résultat pour le moment. Affinez vos mots-clés dans les Réglages."}

    existing = await _list_leads(db, user_id)
    existing_urls = {l.get("url") for l in existing}
    new_count = 0
    for p in posts:
        if p["permalink"] in existing_urls:
            continue
        score, intent = _score_post(p["title"], p["selftext"], keywords)
        is_hn = p.get("subreddit") == "HackerNews"
        try:
            date_str = datetime.fromtimestamp(p["created"], tz=timezone.utc).strftime("%Y-%m-%d") if p.get("created") else ""
        except Exception:
            date_str = ""
        lead = {
            "id": str(uuid.uuid4()),
            "name": p["author"],
            "sub": "HackerNews" if is_hn else (f"r/{p['subreddit']}" if p.get("subreddit") else "Reddit"),
            "source": "hackernews" if is_hn else "reddit",
            "url": p["permalink"],
            "snippet": (p["title"] + ("\n" + p["selftext"] if p["selftext"] else ""))[:500],
            "score": score,
            "intent": intent,
            "date": date_str,
            "stage": "detected",
            "campaign": "hackernews" if is_hn else "reddit",
        }
        await _save_lead(db, user_id, lead)
        existing_urls.add(p["permalink"])
        new_count += 1
    return {"new": new_count, "scanned": len(posts), "keywords": keywords, "subreddits": subreddits}


# ─────────────────────────────────────────────────────────────────
# Agent Prospection — entreprises réelles via l'API Sirene (INSEE)
# (backlog #9). RGPD : aucune donnée personnelle ingérée. L'API Sirene
# expose le répertoire LÉGAL des entreprises françaises (SIREN/SIRET,
# dénomination, code NAF, adresse, date de création) — une entité morale,
# pas une personne physique, n'entre pas dans le champ du RGPD. On ne
# récupère ici QUE ces données publiques officielles ; aucun email, aucun
# téléphone, aucun contact nominatif — ce qui écarte d'office le risque de
# conformité que poserait un scraping de réseau social ou d'annuaire de
# contacts. Source : https://api.insee.fr (portail officiel, clé API
# gratuite sur inscription — voir INSEE_SIRENE_API_KEY plus bas).
#
# Signal de prospection utilisé : entreprises nouvellement créées dans le
# secteur (NAF) et le département ciblés par l'utilisateur — une entreprise
# qui vient de se créer est un signal classique et légitime d'opportunité
# commerciale (besoin d'outils, de services, de prestataires).
INSEE_SIRENE_API_KEY = os.environ.get("INSEE_SIRENE_API_KEY", "")
INSEE_SIRENE_BASE = "https://api.insee.fr/api-sirene/3.11"


async def _fetch_sirene_companies(naf: str, departement: str, limit: int = 20) -> list:
    """Interroge l'API Sirene : établissements actifs, triés par date de
    création décroissante (les plus récents en premier). Best-effort :
    renvoie une liste vide en cas d'erreur réseau/quota plutôt que de
    remonter une exception (cohérent avec le reste du module : un flux
    externe indisponible ne doit jamais casser la page)."""
    if not INSEE_SIRENE_API_KEY:
        return []
    clauses = ["etatAdministratifEtablissement:A"]  # A = actif
    if naf:
        clauses.append(f'activitePrincipaleEtablissement:{naf}')
    if departement:
        clauses.append(f'codePostalEtablissement:{departement}*')
    query = " AND ".join(clauses)
    params = {"q": query, "nombre": str(limit), "tri": "dateCreationEtablissement desc"}
    headers = {"X-INSEE-Api-Key-Integration": INSEE_SIRENE_API_KEY, "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{INSEE_SIRENE_BASE}/siret", params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("Sirene API indisponible: %s", e)
        return []

    out = []
    for etab in (data.get("etablissements") or []):
        try:
            unite = etab.get("uniteLegale", {}) or {}
            adresse = etab.get("adresseEtablissement", {}) or {}
            denomination = (
                unite.get("denominationUniteLegale")
                or " ".join(filter(None, [unite.get("prenom1UniteLegale"), unite.get("nomUniteLegale")]))
                or "Entreprise sans dénomination connue"
            )
            ville = adresse.get("libelleCommuneEtablissement", "")
            naf_lib = etab.get("activitePrincipaleEtablissement", "")
            date_creation = etab.get("dateCreationEtablissement", "")
            out.append({
                "siret": etab.get("siret", ""),
                "name": denomination,
                "ville": ville,
                "naf": naf_lib,
                "date_creation": date_creation,
            })
        except Exception:
            continue
    return out


@router.post("/detect-companies")
async def detect_companies(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Détecte des entreprises réelles (API Sirene) selon le NAF et le
    département ciblés dans les Réglages, et les ajoute au pipeline comme
    leads (source="sirene")."""
    if not INSEE_SIRENE_API_KEY:
        return {
            "new": 0, "scanned": 0,
            "error": "Agent Prospection non configuré : clé API Sirene manquante. "
                     "Inscription gratuite sur https://api.insee.fr, variable d'environnement INSEE_SIRENE_API_KEY.",
        }

    settings = {**DEFAULT_SETTINGS, **(await _get_kv(db, user.id, "growth_settings") or {})}
    naf = (settings.get("sirene_naf") or "").strip()
    departement = (settings.get("sirene_departement") or "").strip()

    companies = await _fetch_sirene_companies(naf, departement, limit=20)
    if not companies:
        return {
            "new": 0, "scanned": 0,
            "error": "Aucun résultat. Vérifiez le code NAF et le département dans les Réglages, "
                     "ou l'API Sirene est temporairement indisponible.",
        }

    existing = await _list_leads(db, user.id)
    existing_sirets = {l.get("siret") for l in existing if l.get("siret")}
    new_count = 0
    for c in companies:
        if not c["siret"] or c["siret"] in existing_sirets:
            continue
        lead = {
            "id": str(uuid.uuid4()),
            "name": c["name"],
            "company": c["name"],
            "siret": c["siret"],
            "sub": f"Nouvelle entreprise · {c['ville']}" if c["ville"] else "Nouvelle entreprise",
            "source": "sirene",
            "snippet": f"SIRET {c['siret']} · Code NAF {c['naf']} · Créée le {c['date_creation']}",
            "date": c["date_creation"],
            "stage": "detected",
            "campaign": "sirene",
        }
        await _save_lead(db, user.id, lead)
        existing_sirets.add(c["siret"])
        new_count += 1
    return {"new": new_count, "scanned": len(companies), "naf": naf, "departement": departement}


# ─────────────────────────────────────────────────────────────────
# Réglages
# ─────────────────────────────────────────────────────────────────
@router.get("/settings")
async def get_settings(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    saved = await _get_kv(db, user.id, "growth_settings") or {}
    merged = {**DEFAULT_SETTINGS, **saved}
    return merged


@router.put("/settings")
async def save_settings(patch: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    saved = await _get_kv(db, user.id, "growth_settings") or {}
    merged = {**DEFAULT_SETTINGS, **saved, **(patch or {})}
    await _save_kv(db, user.id, "growth_settings", merged)
    return merged


# ─────────────────────────────────────────────────────────────────
# Config canaux (WhatsApp / Telegram)
# ─────────────────────────────────────────────────────────────────
@router.get("/channels/{channel}")
async def get_channel(channel: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    saved = await _get_kv(db, user_id, f"growth_channel_{channel}") or {}
    return {**DEFAULT_CHANNELS.get(channel, {}), **saved}


@router.put("/channels/{channel}")
async def save_channel(channel: str, config: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    merged = {**DEFAULT_CHANNELS.get(channel, {}), **(config or {})}
    await _save_kv(db, user_id, f"growth_channel_{channel}", merged)
    return {"ok": True, **merged}


# ─────────────────────────────────────────────────────────────────
# Pipeline Kanban
# ─────────────────────────────────────────────────────────────────
@router.get("/pipeline")
async def get_pipeline(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    leads = await _list_leads(db, user_id)
    stages = [{**s, "leads": []} for s in PIPELINE_STAGES]
    index = {s["id"]: s for s in stages}
    for l in leads:
        stage_id = l.get("stage") or "detected"
        target = index.get(stage_id, index["detected"])
        target["leads"].append({
            "id": l.get("id"),
            "name": l.get("name", "Lead"),
            "sub": l.get("sub") or l.get("source") or "",
            "score": l.get("score") or 0,
            "snippet": l.get("snippet") or l.get("notes") or "",
        })
    return {"stages": stages}


@router.patch("/pipeline/{lead_id}")
async def move_lead(lead_id: str, body: StageIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    await _ensure_leads_table(db)
    r = await db.execute(
        text("SELECT data FROM user_leads WHERE id = :id AND user_id = :uid"),
        {"id": lead_id, "uid": user_id},
    )
    row = r.fetchone()
    if not row:
        return {"ok": False, "error": "Lead introuvable"}
    data = row[0]
    if isinstance(data, str):
        data = json.loads(data)
    data = data or {}
    data["stage"] = body.stage
    await db.execute(
        text("UPDATE user_leads SET data = :d WHERE id = :id AND user_id = :uid"),
        {"d": json.dumps(data), "id": lead_id, "uid": user_id},
    )
    await db.commit()
    return {"ok": True, "stage": body.stage}


# ─────────────────────────────────────────────────────────────────
# Sync CRM externe — on NE remplace PAS ton CRM, on y POUSSE le lead.
# (Brevo / HubSpot connectés dans Intégrations.)
# ─────────────────────────────────────────────────────────────────
_FK = os.environ.get("FERNET_KEY", "")
_FERNET_CRM = Fernet(_FK.encode()) if _FK else None


def _crm_decrypt(v: str) -> str:
    if not _FERNET_CRM or not v:
        return v or ""
    try:
        return _FERNET_CRM.decrypt(v.encode()).decode()
    except Exception:
        return v


async def _get_connection(db: AsyncSession, user_id: str, provider: str):
    res = await db.execute(
        select(UserConnection).where(
            UserConnection.user_id == user_id,
            UserConnection.provider == provider,
        )
    )
    return res.scalar_one_or_none()


async def _push_brevo(creds: dict, lead: dict) -> dict:
    email = lead.get("email") or lead.get("contact_email")
    if not email:
        return {"ok": False, "error": "Ce lead n'a pas d'email — impossible de l'envoyer à Brevo."}
    api_key = creds.get("api_key", "")
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.post(
            "https://api.brevo.com/v3/contacts",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json={"email": email, "attributes": {"FIRSTNAME": lead.get("name") or ""}, "updateEnabled": True},
        )
    if r.status_code in (200, 201, 204):
        return {"ok": True, "provider": "brevo"}
    return {"ok": False, "error": f"Brevo a refusé la requête ({r.status_code})"}


async def _push_hubspot(creds: dict, lead: dict) -> dict:
    token = creds.get("api_key") or creds.get("access_token") or ""
    props = {"firstname": lead.get("name") or "", "company": lead.get("company") or lead.get("sub") or ""}
    if lead.get("email"):
        props["email"] = lead["email"]
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"properties": props},
        )
    if r.status_code in (200, 201):
        return {"ok": True, "provider": "hubspot"}
    return {"ok": False, "error": f"HubSpot a refusé la requête ({r.status_code})"}


class CrmPushIn(BaseModel):
    provider: Optional[str] = None  # brevo | hubspot | None (auto)


@router.post("/leads/{lead_id}/push-crm")
async def push_lead_to_crm(
    lead_id: str,
    body: CrmPushIn = CrmPushIn(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.id
    await _ensure_leads_table(db)
    r = await db.execute(
        text("SELECT data FROM user_leads WHERE id = :id AND user_id = :uid"),
        {"id": lead_id, "uid": user_id},
    )
    row = r.fetchone()
    if not row:
        return {"ok": False, "error": "Lead introuvable"}
    data = row[0]
    if isinstance(data, str):
        data = json.loads(data)
    data = data or {}

    providers = [body.provider] if body.provider else ["brevo", "hubspot"]
    conn = None
    provider = None
    for p in providers:
        conn = await _get_connection(db, user_id, p)
        if conn:
            provider = p
            break
    if not conn:
        return {"ok": False, "error": "Aucun CRM connecté. Connecte Brevo ou HubSpot dans Intégrations."}

    try:
        creds = json.loads(_crm_decrypt(conn.credentials)) if conn.credentials else {}
    except Exception:
        creds = {}

    result = await (_push_brevo(creds, data) if provider == "brevo" else _push_hubspot(creds, data))
    if result.get("ok"):
        data["crm_synced"] = provider
        data["crm_synced_at"] = datetime.now(timezone.utc).isoformat()
        await db.execute(
            text("UPDATE user_leads SET data = :d WHERE id = :id AND user_id = :uid"),
            {"d": json.dumps(data), "id": lead_id, "uid": user_id},
        )
        await db.commit()
    return result


# ─────────────────────────────────────────────────────────────────
# Canaux de détection (empty-state tant qu'aucun moteur branché)
# ─────────────────────────────────────────────────────────────────
@router.get("/youtube")
async def get_youtube(user: User = Depends(get_current_user)):
    return {"items": []}


@router.get("/linkedin")
async def get_linkedin(user: User = Depends(get_current_user)):
    return {"items": []}


@router.get("/forums")
async def get_forums(user: User = Depends(get_current_user)):
    return {"items": []}


@router.get("/terrain")
async def get_terrain(user: User = Depends(get_current_user)):
    return {"items": []}


# ─────────────────────────────────────────────────────────────────
# Engage — génération de message IA + envoi (log)
# ─────────────────────────────────────────────────────────────────
@router.post("/engage/generate")
async def engage_generate(body: EngageGenerateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    lead = None
    if body.lead_id:
        for l in await _list_leads(db, user_id):
            if l.get("id") == body.lead_id:
                lead = l
                break
    lead = lead or {}
    system = (
        "Tu es un assistant d'outreach B2B francophone. Rédige un premier message "
        "de contact court (3-5 phrases), chaleureux, personnalisé et non commercial, "
        f"adapté au canal '{body.channel}'. Pas de formule marketing agressive."
    )
    ctx = []
    if lead.get("name"):
        ctx.append(f"Prénom du lead : {lead['name']}.")
    if lead.get("sub") or lead.get("source"):
        ctx.append(f"Source : {lead.get('sub') or lead.get('source')}.")
    if lead.get("snippet") or lead.get("notes"):
        ctx.append(f"Contexte / ce qu'il a dit : « {lead.get('snippet') or lead.get('notes')} ».")
    prompt = ("Rédige le message. Contexte :\n" + "\n".join(ctx)) if ctx else \
        f"Rédige un premier message de contact générique et chaleureux pour le canal {body.channel}."

    message = ""
    try:
        from routes.growth_copilote import _llm_reply
        message = await _llm_reply(system, prompt)
    except Exception as e:
        logger.warning("engage_generate LLM failed: %s", e)
    if not message:
        name = lead.get("name") or "bonjour"
        message = (
            f"Bonjour {name}, j'ai vu votre message et votre situation me parle. "
            "J'accompagne des personnes dans votre cas et j'ai quelques idées qui "
            "pourraient vous être utiles. Seriez-vous ouvert(e) à en échanger 15 minutes ?"
        )
    return {"message": message, "channel": body.channel}


@router.post("/engage/send")
async def engage_send(body: EngageSendIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    """Enregistre l'envoi. L'envoi réel dépend des connexions canal configurées
    (WhatsApp webhook / Telegram bot / Reddit…), branchées dans Réglages."""
    log = await _get_kv(db, user_id, "growth_engage_log") or {"sent": []}
    log["sent"].append({
        "lead_id": body.lead_id,
        "channel": body.channel,
        "message": body.message[:2000],
        "at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    })
    log["sent"] = log["sent"][-200:]
    await _save_kv(db, user_id, "growth_engage_log", log)
    return {"ok": True, "channel": body.channel, "logged": True}


# ─────────────────────────────────────────────────────────────────
# Export CSV des leads
# ─────────────────────────────────────────────────────────────────
@router.get("/leads/export")
async def export_leads(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = user.id
    leads = await _list_leads(db, user_id)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Nom", "Source", "Score", "Intention", "Étape", "Date"])
    for l in leads:
        writer.writerow([
            l.get("name", ""),
            l.get("sub") or l.get("source") or "",
            l.get("score") or 0,
            l.get("intent") or "",
            l.get("stage") or "detected",
            l.get("date") or "",
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads-zayado.csv"},
    )
