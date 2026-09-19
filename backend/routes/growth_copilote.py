"""Co-pilote IA du Cockpit — POST /api/growth/copilote

Chat assistant business (Mon Bureau → onglet Co-pilote). Répond à une question
de l'utilisateur en s'appuyant sur son contexte (vision / objectif, tâches
récentes) quand il est disponible.

LLM : Emergent LLM Key via emergentintegrations (Claude), avec repli sur
Mammouth AI si MAMMOUTH_API_KEY est configuré.
"""
import os
import uuid
import json
import logging
import calendar
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from routes.growth import _get_kv, _save_kv

from database import get_db
from deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/growth", tags=["growth-copilote"])

SYSTEM_PROMPT = (
    "Tu es le Co-pilote IA de Zayado, un assistant business francophone pour "
    "entrepreneurs et indépendants. Tu es concret, bienveillant et orienté action. "
    "Tu aides à rédiger, analyser, prioriser et générer du contenu. Réponds en "
    "français, de façon claire et concise (pas de blabla), avec des étapes ou des "
    "listes quand c'est utile."
)


class CopiloteIn(BaseModel):
    message: str
    history: list = []  # mémoire conversationnelle : [{role:"user"/"assistant", text/content}]


async def _build_context(db: AsyncSession, user_id: str) -> str:
    """Récupère un contexte léger (objectif + tâches récentes) pour ancrer la réponse."""
    parts = []
    try:
        row = (await db.execute(
            text("SELECT settings FROM users WHERE id = :uid LIMIT 1"),
            {"uid": user_id},
        )).fetchone()
        if row and row[0]:
            raw = row[0]
            settings = json.loads(raw) if isinstance(raw, str) else (raw or {})
            why = settings.get("why") or settings.get("objective")
            if why:
                parts.append(f"Objectif / vision de l'utilisateur : « {why} ».")
            sector = settings.get("sector")
            if sector:
                parts.append(f"Secteur : {sector}.")
    except Exception:
        pass
    try:
        rows = (await db.execute(
            text("SELECT data FROM user_tasks WHERE user_id = :uid ORDER BY created_at DESC LIMIT 5"),
            {"uid": user_id},
        )).fetchall()
        labels = []
        for r in rows:
            d = r[0]
            if isinstance(d, str):
                try:
                    d = json.loads(d)
                except Exception:
                    continue
            if isinstance(d, dict) and d.get("label"):
                labels.append(d["label"])
        if labels:
            parts.append("Tâches récentes : " + "; ".join(labels) + ".")
    except Exception:
        pass

    # Décisions du Copilote en attente (user_copilot_decisions, générées à partir
    # de vraies données — tâches en retard, piliers faibles — cf. copilot_persistence.py).
    # Avant cette correction, ce contexte n'était jamais lu : le Copilote pouvait
    # afficher une décision "à valider" dans l'onglet Décisions tout en l'ignorant
    # complètement dans ses réponses de chat — deux vues déconnectées de la même donnée.
    try:
        from routes.missing_apis import _list_rows
        decisions = await _list_rows(db, "user_copilot_decisions", user_id)
        pending = [d for d in decisions if d.get("status") == "pending"]
        if pending:
            lines = []
            for d in pending[:3]:
                title = d.get("title") or "Décision en attente"
                why = d.get("why_now")
                lines.append(f"{title}" + (f" ({why})" if why else ""))
            parts.append("Décisions en attente de validation : " + "; ".join(lines) + ".")
    except Exception:
        pass
    return "\n".join(parts)


async def _llm_reply(system: str, user_prompt: str, history=None) -> str:
    """Appelle le LLM via le client unifié du projet (Mammouth d'abord, piloté par
    AI_PROVIDER ; repli Emergent automatique en mode 'auto').

    `history` : mémoire conversationnelle optionnelle — liste de tours
    [{role, content}] insérés entre le system et la question courante."""
    try:
        from mammouth_client import chat as ai_chat
        msgs = [{"role": "system", "content": system}]
        for turn in (history or []):
            role = turn.get("role")
            content = (turn.get("content") or turn.get("text") or "").strip()
            if role in ("user", "assistant") and content:
                msgs.append({"role": role, "content": content[:1500]})
        msgs.append({"role": "user", "content": user_prompt})
        reply = await ai_chat(msgs, max_tokens=1024)
        return (reply or "").strip()
    except Exception as e:
        logger.warning("LLM (_llm_reply) échoué: %s", e)
        return ""


@router.post("/copilote")
async def copilote(
    body: CopiloteIn,
    user_id: str = Query("default"),
    db: AsyncSession = Depends(get_db),
):
    message = (body.message or "").strip()
    if not message:
        return {"reply": "Posez-moi une question et je vous aide tout de suite 🙂"}

    context = await _build_context(db, user_id)
    user_prompt = message if not context else f"[Contexte]\n{context}\n\n[Question]\n{message}"

    # Mémoire conversationnelle : on garde les 8 derniers tours (hors message courant).
    history = [h for h in (body.history or []) if isinstance(h, dict)][-8:]

    reply = await _llm_reply(SYSTEM_PROMPT, user_prompt, history=history)
    if not reply:
        reply = (
            "Je n'ai pas pu contacter mon moteur d'IA à l'instant. Réessayez dans "
            "quelques secondes — en attendant, précisez votre objectif pour que je "
            "vous propose un plan d'action concret."
        )
    return {"reply": reply}



# ═══════════════════════════════════════════════════════════════
# « LE POINT DU JOUR » — brief proactif du Cockpit
# Échéances = moteur de règles FIXE (aucune hallucination LLM).
# Le résumé/dialogue se fait ensuite dans le chat (endpoint /copilote).
# ═══════════════════════════════════════════════════════════════

# Jours FR : lundi=0 ... dimanche=6
_JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_MOIS_FR = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
            "août", "septembre", "octobre", "novembre", "décembre"]


def _fmt_fr(d: date) -> str:
    return f"{_JOURS_FR[d.weekday()]} {d.day} {_MOIS_FR[d.month]}"


def _clamp_day(year: int, month: int, day: int) -> date:
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last))


def _next_monthly(today: date, day: int) -> date:
    """Prochaine occurrence d'un jour du mois (ex: le 24 de chaque mois)."""
    cand = _clamp_day(today.year, today.month, day)
    if cand < today:
        y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
        cand = _clamp_day(y, m, day)
    return cand


def _next_from_list(today: date, occurrences) -> date:
    """Prochaine occurrence parmi une liste de (mois, jour) récurrents annuels."""
    cands = []
    for (mo, dy) in occurrences:
        c = _clamp_day(today.year, mo, dy)
        if c < today:
            c = _clamp_day(today.year + 1, mo, dy)
        cands.append(c)
    return min(cands)


def _compute_deadlines(today: date, horizon_days: int = 45):
    """Échéances fiscales/sociales FR récurrentes (INDICATIF — varient selon régime).
    On calcule la prochaine occurrence de chaque règle et on garde celles à venir
    dans l'horizon donné."""
    rules = [
        {
            "label": "Déclaration & paiement de la TVA (régime réel mensuel)",
            "category": "fiscal",
            "date": _next_monthly(today, 24),
            "note": "Date indicative — entre le 15 et le 24 selon votre département.",
        },
        {
            "label": "Cotisations URSSAF micro-entrepreneur (déclaration mensuelle)",
            "category": "social",
            "date": _next_monthly(today, 31),
            "note": "Si vous êtes en déclaration mensuelle.",
        },
        {
            "label": "Cotisations URSSAF micro-entrepreneur (déclaration trimestrielle)",
            "category": "social",
            "date": _next_from_list(today, [(4, 30), (7, 31), (10, 31), (1, 31)]),
            "note": "Si vous êtes en déclaration trimestrielle.",
        },
        {
            "label": "Acompte d'impôt sur les sociétés (IS)",
            "category": "fiscal",
            "date": _next_from_list(today, [(3, 15), (6, 15), (9, 15), (12, 15)]),
            "note": "Sociétés soumises à l'IS.",
        },
        {
            "label": "Cotisation Foncière des Entreprises (CFE)",
            "category": "fiscal",
            "date": _next_from_list(today, [(12, 15)]),
            "note": "Paiement en ligne avant le 15 décembre.",
        },
        {
            "label": "Déclaration de revenus (impôt sur le revenu)",
            "category": "fiscal",
            "date": _next_from_list(today, [(5, 31)]),
            "note": "Fin mai / début juin selon votre département.",
        },
    ]
    out = []
    for r in rules:
        days_left = (r["date"] - today).days
        if 0 <= days_left <= horizon_days:
            urgency = "urgent" if days_left <= 3 else ("soon" if days_left <= 10 else "info")
            out.append({
                "label": r["label"],
                "category": r["category"],
                "date": r["date"].isoformat(),
                "date_label": _fmt_fr(r["date"]),
                "days_left": days_left,
                "urgency": urgency,
                "note": r["note"],
            })
    out.sort(key=lambda x: x["days_left"])
    return out[:5]


async def _fetch_reminders(db: AsyncSession, user_id: str):
    """Rappels persos = tâches récentes de l'utilisateur (données réelles)."""
    reminders = []
    try:
        rows = (await db.execute(
            text("SELECT data FROM user_tasks WHERE user_id = :uid ORDER BY created_at DESC LIMIT 4"),
            {"uid": user_id},
        )).fetchall()
        for r in rows:
            d = r[0]
            if isinstance(d, str):
                try:
                    d = json.loads(d)
                except Exception:
                    continue
            if isinstance(d, dict) and d.get("label"):
                reminders.append(d["label"])
    except Exception:
        pass
    return reminders


def _greeting_word(now: datetime) -> str:
    h = now.hour
    if h < 5:
        return "Bonne nuit"
    if h < 18:
        return "Bonjour"
    return "Bonsoir"


# ─── Flux RSS d'actualités sectorielles (Google News, sans clé, tenu à jour) ───
_NEWS_CACHE = {}       # query -> (timestamp, items)
_NEWS_TTL = 1800       # 30 minutes


def _news_query(sector: str) -> str:
    s = (sector or "").strip()
    return s if s else "entrepreneur PME"


def _fetch_news_sync(query: str):
    import urllib.parse, urllib.request, feedparser
    q = urllib.parse.quote(f"{query} France")
    url = f"https://news.google.com/rss/search?q={q}&hl=fr&gl=FR&ceid=FR:fr"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=5) as r:
        data = r.read()
    feed = feedparser.parse(data)
    items = []
    for e in feed.entries[:5]:
        title = e.get("title", "") or ""
        source = ""
        if " - " in title:
            title, source = title.rsplit(" - ", 1)
        items.append({
            "title": title.strip(),
            "link": e.get("link", ""),
            "source": source.strip(),
            "published": e.get("published", ""),
        })
    return items


async def _fetch_news(query: str):
    import time, asyncio
    now = time.time()
    cached = _NEWS_CACHE.get(query)
    if cached and now - cached[0] < _NEWS_TTL:
        return cached[1]
    items = []
    try:
        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, _fetch_news_sync, query)
    except Exception as e:
        logger.warning("RSS fetch failed (%s): %s", query, e)
        if cached:
            return cached[1]
    if items:
        _NEWS_CACHE[query] = (now, items)
    return items


async def _fetch_sector(db: AsyncSession, user_id: str) -> str:
    try:
        row = (await db.execute(
            text("SELECT settings FROM users WHERE id = :uid LIMIT 1"),
            {"uid": user_id},
        )).fetchone()
        if row and row[0]:
            raw = row[0]
            settings = json.loads(raw) if isinstance(raw, str) else (raw or {})
            return (settings.get("sector") or settings.get("secteur") or "").strip()
    except Exception:
        pass
    return ""



def _build_chat_intro(greeting: str, first_name: str, deadlines, reminders, news=None) -> str:
    """Message d'accueil du chat « Le Point du jour » — factuel (échéances issues
    du moteur de règles, pas du LLM). Texte simple (le chat n'affiche pas le markdown)."""
    name = f" {first_name}" if first_name else ""
    lines = [f"Le Point du jour — {greeting.lower()}{name} 👋", ""]
    if deadlines:
        lines.append("📅 ÉCHÉANCES À NE PAS MANQUER")
        for d in deadlines:
            emoji = "🔴" if d["urgency"] == "urgent" else ("🟠" if d["urgency"] == "soon" else "🟢")
            jr = "aujourd'hui" if d["days_left"] == 0 else (
                "demain" if d["days_left"] == 1 else f"dans {d['days_left']} jours")
            lines.append(f"{emoji} {d['label']} — {d['date_label']} ({jr})")
        lines.append("")
        lines.append("ℹ️ Dates indicatives : elles dépendent de votre régime. Dites-moi votre statut et je précise.")
        lines.append("")
    if reminders:
        lines.append("✅ VOS RAPPELS EN COURS")
        for r in reminders[:4]:
            lines.append(f"• {r}")
        lines.append("")
    if news:
        lines.append("📰 ACTUALITÉS DU JOUR (votre secteur)")
        for n in news[:3]:
            src = f" — {n['source']}" if n.get("source") else ""
            lines.append(f"• {n['title']}{src}")
        lines.append("")
        lines.append("Dites « Résume-moi l'actualité » et je vous en fais une synthèse actionnable.")
        lines.append("")
    lines.append("Sur quoi voulez-vous avancer en priorité aujourd'hui ? Je peux résumer l'actualité de votre secteur, préparer une échéance, ou vous aider sur votre projet.")
    return "\n".join(lines)


@router.get("/daily-brief")
async def daily_brief(
    user_id: str = Query("default"),
    db: AsyncSession = Depends(get_db),
):
    """« Le Point du jour » — brief proactif : échéances (règles fixes) + rappels."""
    now = datetime.now(timezone.utc)
    today = now.date()
    greeting = _greeting_word(now)

    first_name = ""
    try:
        row = (await db.execute(
            text("SELECT name, settings FROM users WHERE id = :uid LIMIT 1"),
            {"uid": user_id},
        )).fetchone()
        if row and row[0]:
            first_name = (row[0] or "").strip().split(" ")[0]
    except Exception:
        pass

    deadlines = _compute_deadlines(today)
    reminders = await _fetch_reminders(db, user_id)
    sector = await _fetch_sector(db, user_id)
    news = await _fetch_news(_news_query(sector))
    chat_intro = _build_chat_intro(greeting, first_name, deadlines, reminders, news)

    top = deadlines[0] if deadlines else None
    if top:
        jr = "aujourd'hui" if top["days_left"] == 0 else (
            "demain" if top["days_left"] == 1 else f"dans {top['days_left']} j")
        headline = f"{top['label'].split('(')[0].strip()} — {jr}"
    else:
        headline = "Aucune échéance imminente. Belle journée pour avancer sur votre vision."

    return {
        "date": today.isoformat(),
        "date_label": _fmt_fr(today),
        "greeting": greeting,
        "first_name": first_name,
        "headline": headline,
        "deadlines": deadlines,
        "reminders": reminders,
        "news": news,
        "sector": sector,
        "chat_intro": chat_intro,
        "has_urgent": any(d["urgency"] == "urgent" for d in deadlines),
    }


NEWS_SYSTEM = (
    "Tu es un veilleur économique francophone pour entrepreneurs. À partir de titres "
    "d'actualité, tu produis une synthèse courte, factuelle et utile. N'invente jamais "
    "d'information au-delà des titres fournis."
)


NEWS_DIGEST_KEY = "news_digest_cache"
NEWS_DIGEST_CADENCE_DAYS = 7  # défaut Paramètres : 1x/semaine


@router.get("/news-digest")
async def news_digest(
    user_id: str = Query("default"),
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Résumé IA des actualités du secteur (le résumé se fait via le chat).
    Mis en cache selon la cadence réglée dans Paramètres (7 jours par
    défaut) — sans ce garde-fou, chaque appel (chaque ouverture du chat)
    régénérait un digest neuf via le LLM, sans aucune limite."""
    cached = await _get_kv(db, user_id, NEWS_DIGEST_KEY)
    if cached and not refresh:
        try:
            generated_at = datetime.fromisoformat(cached["generated_at"])
        except Exception:
            generated_at = None
        if generated_at and (datetime.now(timezone.utc) - generated_at).days < NEWS_DIGEST_CADENCE_DAYS:
            return {"ok": True, "digest": cached["digest"], "sources": cached.get("sources", []), "sector": cached.get("sector"), "cached": True}

    sector = await _fetch_sector(db, user_id)
    items = await _fetch_news(_news_query(sector))
    if not items:
        # ok=False -> le frontend NE DOIT PAS écraser une actualité déjà affichée
        if cached:
            return {"ok": True, "digest": cached["digest"], "sources": cached.get("sources", []), "sector": cached.get("sector"), "cached": True}
        return {"ok": False, "digest": "Je n'ai pas pu récupérer l'actualité à l'instant. Réessayez dans un moment.", "sources": []}

    headlines = "\n".join(f"- {it['title']}" + (f" ({it['source']})" if it.get("source") else "") for it in items)
    secteur_txt = sector or "entrepreneuriat / PME"
    prompt = (
        f"Secteur de l'utilisateur : {secteur_txt}.\n"
        f"Voici les titres d'actualité du jour :\n{headlines}\n\n"
        "Rédige une synthèse en 3 à 4 puces courtes (une ligne chacune), en français, "
        "pertinentes pour cet entrepreneur. Termine par une puce « 👉 À retenir : » avec "
        "un conseil actionnable. Pas de markdown gras, texte simple."
    )
    digest = await _llm_reply(NEWS_SYSTEM, prompt)
    if not digest:
        digest = "Actualités du jour :\n" + "\n".join(f"• {it['title']}" for it in items)
    await _save_kv(db, user_id, NEWS_DIGEST_KEY, {
        "digest": digest, "sources": items, "sector": sector,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "digest": digest, "sources": items, "sector": sector}


# ─── « Travailler avec l'équipe » — demande de collaboration ──────
class WorkRequestIn(BaseModel):
    message: str
    channel: str = "chat"      # chat | whatsapp | email
    contact: str = ""          # email/téléphone laissé par l'utilisateur


@router.post("/work-request")
async def work_request(
    body: WorkRequestIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enregistre une demande de collaboration pour son compte et notifie l'équipe."""
    msg = (body.message or "").strip()
    if not msg:
        return {"ok": False, "error": "Message vide"}

    email = body.contact
    name = ""
    try:
        row = (await db.execute(
            text("SELECT name, email FROM users WHERE id = :uid LIMIT 1"),
            {"uid": str(user.id)},
        )).fetchone()
        if row:
            name = row[0] or ""
            email = email or (row[1] or "")
    except Exception:
        pass

    logger.info("Work request from %s (%s) via %s: %s", name, email, body.channel, msg[:200])

    # Notifie l'équipe par email (best-effort, n'échoue jamais l'appel)
    try:
        from utils import send_brevo_email, load_admin_config
        team_email = load_admin_config().get("fallback_alert_email", "contact@zayado.net")
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
          <h2 style="color:#14213d">🤝 Nouvelle demande de collaboration</h2>
          <p><strong>Client :</strong> {name or 'Utilisateur'} ({email or 'email non fourni'})</p>
          <p><strong>Canal souhaité :</strong> {body.channel}</p>
          <p><strong>Message :</strong></p>
          <blockquote style="border-left:3px solid #C9A449;padding-left:12px;color:#333">{msg}</blockquote>
          <p style="color:#6b7280;font-size:.85rem">Envoyé depuis « Le Point du jour » — MyExtension AI.</p>
        </div>"""
        import asyncio as _asyncio
        _asyncio.get_event_loop().run_in_executor(
            None, send_brevo_email, team_email, "Équipe Zayado",
            f"🤝 Demande de collaboration — {name or 'Client'}", html
        )
    except Exception as e:
        logger.warning("work-request email failed: %s", e)

    return {"ok": True, "message": "Votre demande est bien partie 🙌 L'équipe vous répond très vite."}
