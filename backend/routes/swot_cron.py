"""Cron mensuel : analyse SWOT automatique via Claude Sonnet 4.5.

Loop background : tourne toutes les 6h, vérifie chaque user qui a opté-in,
génère son analyse SWOT s'il s'est écoulé >=28j depuis la dernière, et envoie
un email récap via Brevo.

Opt-in : table `user_prefs` (clé/valeur JSON). Clé = "swot_monthly".
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from database import async_session_factory
from routes.missing_apis import _claude_complete, _list_rows, _insert_row, _ensure_table

logger = logging.getLogger(__name__)


def _utc_now():
    return datetime.now(timezone.utc)


async def _get_prefs(db, user_id: str) -> dict:
    await _ensure_table(db, "user_prefs")
    r = await db.execute(
        text("SELECT data FROM user_prefs WHERE user_id = :uid LIMIT 1"),
        {"uid": user_id},
    )
    row = r.fetchone()
    if not row:
        return {}
    d = row[0]
    if isinstance(d, str):
        d = json.loads(d)
    return d or {}


async def _set_prefs(db, user_id: str, patch: dict):
    await _ensure_table(db, "user_prefs")
    cur = await _get_prefs(db, user_id)
    cur.update(patch)
    cur["updated_at"] = _utc_now().isoformat()
    r = await db.execute(
        text("SELECT id FROM user_prefs WHERE user_id = :uid LIMIT 1"),
        {"uid": user_id},
    )
    row = r.fetchone()
    if row:
        await db.execute(
            text("UPDATE user_prefs SET data = :d WHERE user_id = :uid"),
            {"uid": user_id, "d": json.dumps(cur)},
        )
    else:
        import uuid as _uuid
        await db.execute(
            text("INSERT INTO user_prefs (id, user_id, data) VALUES (:id, :uid, :d)"),
            {"id": str(_uuid.uuid4()), "uid": user_id, "d": json.dumps(cur)},
        )
    await db.commit()
    return cur


def _email_html(user_name: str, analyse: dict, branding: dict | None = None) -> str:
    """Construit l'HTML de l'email SWOT via le template branded centralisé."""
    from routes.branding import render_email
    verdict = (analyse.get("verdict") or "à déterminer").upper()
    score = analyse.get("score") or "—"
    summary = analyse.get("summary") or "Pas d'analyse disponible ce mois-ci."

    def _ul(items):
        if not items:
            return "<li><em>Aucun élément</em></li>"
        return "".join(f"<li style='margin:4px 0'>{x}</li>" for x in items)

    actions_html = ""
    for i, a in enumerate(analyse.get("next_actions") or [], 1):
        actions_html += f"<p style='margin:6px 0'><strong>{i}.</strong> {a}</p>"

    primary = (branding or {}).get("primary_color", "#1B2A4A")
    body = (
        f'<div style="margin:18px 0;padding:16px;background:#FAF7F2;border-radius:10px;'
        f'display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap">'
        f'<div><p style="margin:0;font-size:11px;text-transform:uppercase;color:#7A7066">Verdict</p>'
        f'<p style="margin:2px 0 0;font-size:22px;color:{primary};font-weight:600">{verdict}</p></div>'
        f'<div style="text-align:right"><p style="margin:0;font-size:11px;text-transform:uppercase;color:#7A7066">Score</p>'
        f'<p style="margin:2px 0 0;font-size:22px;color:{primary};font-weight:600">{score}/100</p></div></div>'
        f'<p style="font-style:italic;color:#4A4538;margin:0 0 18px">{summary}</p>'
        f'<h3 style="font-family:Georgia,serif;color:{primary};margin-top:18px">Forces</h3>'
        f'<ul>{_ul(analyse.get("strengths"))}</ul>'
        f'<h3 style="font-family:Georgia,serif;color:{primary}">Faiblesses</h3>'
        f'<ul>{_ul(analyse.get("weaknesses"))}</ul>'
        f'<h3 style="font-family:Georgia,serif;color:{primary}">Opportunités</h3>'
        f'<ul>{_ul(analyse.get("opportunities"))}</ul>'
        f'<h3 style="font-family:Georgia,serif;color:{primary}">Menaces</h3>'
        f'<ul>{_ul(analyse.get("threats"))}</ul>'
        f'<h3 style="font-family:Georgia,serif;color:{primary}">Vos 3 prochaines actions</h3>'
        f'<div>{actions_html or "<p><em>Aucune action prioritaire identifiée.</em></p>"}</div>'
    )
    return render_email(
        branding or {},
        title=f"Bonjour {user_name},",
        intro="Voici l'analyse stratégique automatique de votre business ce mois-ci.",
        body_html=body,
        cta_label="Ouvrir mon cockpit",
        cta_url="https://app.zayado.net/",
    )


async def _generate_and_send(db, user) -> bool:
    """Génère l'analyse SWOT du user via Claude + envoie l'email. True si succès."""
    # Build context
    vision_rows = await _list_rows(db, "user_vision", user.id)
    vision = vision_rows[0] if vision_rows else {}
    profile_brief = (
        f"Utilisateur : {user.name or user.email}.\n"
        f"Vision (why) : {vision.get('why', 'non renseigné')}.\n"
        f"Vision (what) : {vision.get('what', 'non renseigné')}.\n"
        f"Cible (who) : {vision.get('who', 'non renseigné')}.\n"
    )
    system = (
        "Tu es un consultant senior en stratégie business pour solo founders. "
        "Tu produis des analyses SWOT mensuelles actionnables, en français, en JSON strict. "
        "Court, factuel, orienté action."
    )
    prompt = (
        f"Contexte du solo founder :\n\n{profile_brief}\n\n"
        "Génère une analyse SWOT mensuelle en JSON strict :\n"
        '{"summary": "2 phrases", "verdict": "go"|"pivot"|"abandon", "score": 0-100, '
        '"strengths": ["...", "..."], "weaknesses": ["...", "..."], '
        '"opportunities": ["...", "..."], "threats": ["...", "..."], '
        '"next_actions": ["action1", "action2", "action3"]}\n'
        "Réponds UNIQUEMENT avec le JSON."
    )
    raw = await _claude_complete(system=system, user_prompt=prompt, max_tokens=1200)
    if not raw:
        logger.warning(f"[SWOT_CRON] Claude returned empty for user {user.id}")
        return False
    parsed = {}
    try:
        s = raw.strip()
        if s.startswith("```"):
            s = s.strip("`").split("\n", 1)[-1]
            if s.endswith("```"):
                s = s.rsplit("```", 1)[0]
        parsed = json.loads(s)
    except Exception as e:
        logger.warning(f"[SWOT_CRON] JSON parse failed for user {user.id}: {e}")
        parsed = {"summary": raw[:300], "verdict": None, "score": None}

    data = {
        "summary": parsed.get("summary", ""),
        "verdict": parsed.get("verdict"),
        "score": parsed.get("score"),
        "strengths": parsed.get("strengths") or [],
        "weaknesses": parsed.get("weaknesses") or [],
        "opportunities": parsed.get("opportunities") or [],
        "threats": parsed.get("threats") or [],
        "next_actions": parsed.get("next_actions") or [],
        "generated_at": _utc_now().isoformat(),
        "source": "claude-sonnet-4-5-monthly",
    }
    # Persist (replace previous)
    await _ensure_table(db, "user_analyse")
    await db.execute(text("DELETE FROM user_analyse WHERE user_id = :uid"), {"uid": user.id})
    await db.commit()
    await _insert_row(db, "user_analyse", user.id, data)

    # Send email via Brevo (branded template)
    try:
        from utils import send_brevo_email
        from routes.branding import get_branding
        branding = await get_branding(db)
        loop = asyncio.get_running_loop()
        ok = await loop.run_in_executor(
            None,
            lambda: send_brevo_email(
                to_email=user.email,
                to_name=user.name or "",
                subject="Votre analyse SWOT mensuelle — MyExtension AI",
                html_content=_email_html(user.name or "", data, branding),
                brand="zayado",
            ),
        )
        return bool(ok)
    except Exception as e:
        logger.exception(f"[SWOT_CRON] Email send failed for {user.email}: {e}")
        return False


async def monthly_swot_loop():
    """Background loop : toutes les 6h, génère + envoie SWOT mensuel aux opt-in users.
    Délai initial : 60s après démarrage."""
    await asyncio.sleep(60)
    logger.info("[SWOT_CRON] Monthly SWOT analysis loop started")
    INTERVAL_SECONDS = 6 * 3600  # 6h
    MIN_DAYS_BETWEEN = 28
    while True:
        try:
            async with async_session_factory() as db:
                from sqlalchemy import select
                from models import User
                result = await db.execute(select(User).where(User.is_active == True))  # noqa: E712
                users = result.scalars().all()
                sent = 0
                for u in users:
                    try:
                        prefs = await _get_prefs(db, u.id)
                        if not prefs.get("swot_monthly", True):
                            continue
                        last = prefs.get("swot_last_sent_at")
                        if last:
                            try:
                                last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                                if (_utc_now() - last_dt).days < MIN_DAYS_BETWEEN:
                                    continue
                            except Exception:
                                pass
                        ok = await _generate_and_send(db, u)
                        if ok:
                            await _set_prefs(db, u.id, {"swot_last_sent_at": _utc_now().isoformat()})
                            sent += 1
                            # Throttle : 1 user / 5s pour ménager le LLM
                            await asyncio.sleep(5)
                    except Exception as ue:
                        logger.warning(f"[SWOT_CRON] User {u.id} error: {ue}")
                if sent > 0:
                    logger.info(f"[SWOT_CRON] Sent {sent} monthly SWOT emails")
        except Exception as e:
            logger.exception(f"[SWOT_CRON] Loop error: {e}")
        await asyncio.sleep(INTERVAL_SECONDS)


# ── Endpoints user-facing pour gérer l'opt-in ────────────────────────────────
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database import get_db
from deps import get_current_user, User as UserModel

swot_router = APIRouter(tags=["swot-cron"])


class PrefsIn(BaseModel):
    swot_monthly: bool | None = None


@swot_router.get("/prefs/swot")
async def get_swot_prefs(user: UserModel = Depends(get_current_user), db=Depends(get_db)):
    prefs = await _get_prefs(db, user.id)
    return {
        "swot_monthly": prefs.get("swot_monthly", True),
        "swot_last_sent_at": prefs.get("swot_last_sent_at"),
    }


@swot_router.patch("/prefs/swot")
async def set_swot_prefs(body: PrefsIn, user: UserModel = Depends(get_current_user), db=Depends(get_db)):
    patch = {k: v for k, v in body.dict().items() if v is not None}
    if not patch:
        return {"updated": False}
    new_prefs = await _set_prefs(db, user.id, patch)
    return {
        "updated": True,
        "swot_monthly": new_prefs.get("swot_monthly", True),
    }


@swot_router.post("/prefs/swot/send-now")
async def send_swot_now(user: UserModel = Depends(get_current_user), db=Depends(get_db)):
    """Force l'envoi immédiat d'une analyse SWOT (admin/test ou utilisateur impatient)."""
    ok = await _generate_and_send(db, user)
    if ok:
        await _set_prefs(db, user.id, {"swot_last_sent_at": _utc_now().isoformat()})
    return {"sent": ok}
