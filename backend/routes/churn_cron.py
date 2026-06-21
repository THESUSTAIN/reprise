"""Cron de re-engagement utilisateurs inactifs.

3 paliers de relance basés sur last_login_at :
- 14j  : soft FOMO ("3 missions vous attendent")
- 60j  : empathique ("on s'inquiète, tout va bien ?")
- 335j : avertissement RGPD ("suppression dans 30j")

A/B Test sujets emails :
  - Chaque tier a 3 variantes de sujet (A, B, C)
  - La variante est assignée par hash(user_id) % 3 → déterministe & reproductible
  - L'ouverture est trackée via pixel Brevo (open tracking natif) + webhook Brevo → /api/churn/brevo-event
  - Les stats A/B sont stockées en user_prefs global (table platform_settings key 'churn_ab_stats')
  - Endpoint admin GET /admin/inactivity/ab-stats pour consulter les résultats
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import text, select
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from database import async_session_factory, get_db
from models import User, PlatformSetting
from deps import get_admin_user, get_current_user, User as UserModel
from routes.swot_cron import _get_prefs, _set_prefs

logger = logging.getLogger(__name__)
churn_router = APIRouter(tags=["churn-cron"])


def _utc_now():
    return datetime.now(timezone.utc)


# ───────────── A/B variants par tier ─────────────
# Format : liste de 3 sujets (A, B, C)
TIER_AB_SUBJECTS = {
    "tier_14": [
        # A — FOMO missions
        "{name}, votre cockpit vous attend (3 missions prêtes)",
        # B — curiosité chiffre
        "📊 {name} — votre IA a bossé 14j sans vous",
        # C — urgence douce
        "⏳ 2 semaines déjà, {name} — reprenez en 5 min",
    ],
    "tier_60": [
        # A — empathique
        "On s'inquiète pour vous, {name} — tout va bien ?",
        # B — feedback invite
        "👋 {name}, un mot suffit — qu'est-ce qu'on a raté ?",
        # C — retour facile
        "Votre cockpit vous manque, {name} ? Revenez en 1 clic",
    ],
    "tier_335": [
        # A — RGPD warning
        "⚠ {name}, suppression de votre compte dans 30 jours",
        # B — dernière chance narrative
        "🔒 {name}, votre compte Zayado sera supprimé le {date_purge}",
        # C — neutre / informatif
        "{name} — avis important concernant votre compte Zayado",
    ],
}


def _get_ab_variant(user_id: str, tier_key: str) -> int:
    """Retourne 0, 1 ou 2 — déterministe par hash(user_id + tier_key)."""
    digest = hashlib.md5(f"{user_id}{tier_key}".encode()).hexdigest()
    return int(digest[:8], 16) % 3


def _get_subject(user_id: str, tier_key: str, name: str, tier: dict) -> tuple[str, int]:
    """Retourne (subject, variant_index) pour cet utilisateur."""
    variants = TIER_AB_SUBJECTS.get(tier_key)
    if not variants:
        # Fallback sur subject_tpl du tier
        return tier["subject_tpl"].format(name=name), 0

    variant_idx = _get_ab_variant(user_id, tier_key)
    subject_tpl = variants[variant_idx]

    # Remplacement variables
    try:
        date_purge = (_utc_now() + timedelta(days=30)).strftime("%d/%m/%Y")
        subject = subject_tpl.format(name=name, date_purge=date_purge)
    except Exception:
        subject = subject_tpl.replace("{name}", name)

    return subject, variant_idx


# ───────────── Stats A/B (stockées en PlatformSetting) ──────────────
_AB_STATS_KEY = "churn_ab_stats"


async def _get_ab_stats(db) -> dict:
    r = await db.execute(
        select(PlatformSetting).where(PlatformSetting.key == _AB_STATS_KEY)
    )
    row = r.scalar_one_or_none()
    if not row:
        return {}
    try:
        return json.loads(row.value)
    except Exception:
        return {}


async def _save_ab_stats(db, stats: dict):
    r = await db.execute(
        select(PlatformSetting).where(PlatformSetting.key == _AB_STATS_KEY)
    )
    row = r.scalar_one_or_none()
    value = json.dumps(stats)
    if row:
        await db.execute(
            text("UPDATE platform_settings SET value = :v WHERE key = :k"),
            {"v": value, "k": _AB_STATS_KEY},
        )
    else:
        import uuid
        await db.execute(
            text("INSERT INTO platform_settings (id, key, value) VALUES (:id, :k, :v)"),
            {"id": str(uuid.uuid4()), "k": _AB_STATS_KEY, "v": value},
        )
    await db.commit()


async def _record_ab_send(db, tier_key: str, variant_idx: int):
    """Incrément sent_count pour ce tier/variant."""
    stats = await _get_ab_stats(db)
    tier_stats = stats.setdefault(tier_key, {})
    v_key = f"v{variant_idx}"
    v = tier_stats.setdefault(v_key, {"sent": 0, "opens": 0, "clicks": 0})
    v["sent"] += 1
    v["subject"] = TIER_AB_SUBJECTS.get(tier_key, ["", "", ""])[variant_idx]
    await _save_ab_stats(db, stats)


async def _record_ab_open(db, tier_key: str, variant_idx: int):
    """Incrément opens pour ce tier/variant."""
    stats = await _get_ab_stats(db)
    tier_stats = stats.setdefault(tier_key, {})
    v_key = f"v{variant_idx}"
    v = tier_stats.setdefault(v_key, {"sent": 0, "opens": 0, "clicks": 0})
    v["opens"] += 1
    await _save_ab_stats(db, stats)


# ───────────── Tier definitions ─────────────
TIERS = [
    {
        "key": "tier_14",
        "days": 14,
        "subject_tpl": "{name}, votre cockpit vous attend (3 missions prêtes)",
        "title_tpl": "{name}, ça fait 2 semaines.",
        "intro": (
            "Votre IA a continué de bosser pour vous en arrière-plan. "
            "Elle a préparé <strong>3 missions prioritaires</strong> et identifié "
            "<strong>2 opportunités</strong> que vous pourriez activer dès aujourd'hui."
        ),
        "body_html": (
            "<p style='margin:14px 0'>Ce n'est pas long, mais 14 jours sans pilotage, ça se sent vite :</p>"
            "<ul style='font-size:14.5px;line-height:1.6'>"
            "<li>Votre vision risque de dériver sans suivi quotidien</li>"
            "<li>Vos missions accumulent du retard silencieux</li>"
            "<li>Votre IA n'apprend plus rien de votre business</li>"
            "</ul>"
            "<p style='margin:16px 0'>5 minutes suffisent pour reprendre le contrôle.</p>"
        ),
        "cta_label": "Reprendre 5 minutes",
        "cta_url": "https://app.zayado.net/",
    },
    {
        "key": "tier_60",
        "days": 60,
        "subject_tpl": "On s'inquiète pour vous, {name} — tout va bien ?",
        "title_tpl": "Bonjour {name},",
        "intro": (
            "Ça fait 2 mois qu'on ne vous a pas vu sur votre cockpit. "
            "On voulait juste prendre des nouvelles, sans pression."
        ),
        "body_html": (
            "<p style='margin:14px 0'>Plusieurs raisons possibles :</p>"
            "<ul style='font-size:14.5px;line-height:1.6'>"
            "<li>Vous avez trouvé un autre outil → <em>on aimerait comprendre lequel et pourquoi.</em></li>"
            "<li>Votre business a pivoté → <em>on peut adapter votre cockpit en 1 clic.</em></li>"
            "<li>Vous êtes débordé → <em>l'IA peut justement vous décharger.</em></li>"
            "<li>Le produit ne vous a pas convaincu → <em>dites-nous ce qui n'allait pas.</em></li>"
            "</ul>"
            "<p style='margin:18px 0'>Que ce soit pour revenir ou pour partir, on aimerait avoir un mot de vous. "
            "Répondez à cet email — un humain (pas un bot) le lira.</p>"
        ),
        "cta_label": "Revenir sur mon cockpit",
        "cta_url": "https://app.zayado.net/",
    },
    {
        "key": "tier_335",
        "days": 335,
        "subject_tpl": "⚠ {name}, suppression de votre compte dans 30 jours",
        "title_tpl": "Information importante, {name}",
        "intro": (
            "Conformément au RGPD et à nos CGU, les comptes inactifs depuis plus de 12 mois "
            "sont automatiquement supprimés. Votre compte sera supprimé dans 30 jours "
            "si vous ne vous reconnectez pas."
        ),
        "body_html": (
            "<p style='margin:14px 0'>Ce que la suppression implique :</p>"
            "<ul style='font-size:14.5px;line-height:1.6'>"
            "<li>Toutes vos données seront effacées définitivement</li>"
            "<li>Votre vision, vos missions, vos analyses — supprimées</li>"
            "<li>Cette action est irréversible</li>"
            "</ul>"
            "<p style='margin:16px 0'>"
            "Si vous souhaitez conserver votre compte, <strong>reconnectez-vous simplement</strong>. "
            "Si vous ne souhaitez plus utiliser Zayado, vous pouvez aussi nous le confirmer en répondant à cet email — "
            "on supprimera votre compte immédiatement et sans délai.</p>"
        ),
        "cta_label": "Me reconnecter et garder mon compte",
        "cta_url": "https://app.zayado.net/",
    },
]


def _render_email_inactive(branding: dict, user_name: str, tier: dict) -> str:
    from routes.branding import render_email
    return render_email(
        branding=branding,
        title=tier["title_tpl"].format(name=user_name.split()[0] if user_name else ""),
        intro=tier["intro"],
        body_html=tier["body_html"],
        cta_label=tier["cta_label"],
        cta_url=tier["cta_url"],
    )


async def _send_inactivity_alert(db, user: User, tier: dict, branding: dict) -> tuple[bool, int]:
    """
    Envoie un email de relance pour un tier donné.
    Retourne (success, variant_index).
    """
    try:
        from utils import send_brevo_email
        name = (user.name or "").split()[0] if user.name else (user.email.split("@")[0])
        subject, variant_idx = _get_subject(user.id, tier["key"], name, tier)
        html = _render_email_inactive(branding, user.name or "", tier)

        # Injecter le variant dans les headers X- pour tracking Brevo webhook
        extra_headers = {
            "X-Zayado-AB-Tier": tier["key"],
            "X-Zayado-AB-Variant": str(variant_idx),
        }

        loop = asyncio.get_running_loop()
        ok = await loop.run_in_executor(
            None,
            lambda: send_brevo_email(
                to_email=user.email,
                to_name=user.name or "",
                subject=subject,
                html_content=html,
                brand="zayado",
                extra_headers=extra_headers,
            ),
        )
        return bool(ok), variant_idx
    except Exception as e:
        logger.exception(f"[CHURN_CRON] Send failed for {user.email} tier {tier['key']}: {e}")
        return False, 0


async def _gdpr_purge_loop():
    """Background loop : toutes les 24h, supprime les comptes inactifs >365j ayant reçu
    l'avertissement tier_335 il y a plus de 30j."""
    await asyncio.sleep(300)
    logger.info("[GDPR_PURGE] Loop started")
    INTERVAL = 24 * 3600
    JSON_TABLES = [
        "user_tasks", "user_vision", "user_documents", "user_leads",
        "user_analyse", "user_collab_events", "user_prefs",
        "broadcast_notifications",
    ]
    while True:
        try:
            async with async_session_factory() as db:
                now = _utc_now()
                cutoff_365 = now - timedelta(days=365)
                rows = (await db.execute(
                    select(User).where(
                        User.is_active == True,  # noqa: E712
                        User.last_login_at.isnot(None),
                        User.last_login_at <= cutoff_365,
                    )
                )).scalars().all()
                purged = 0
                for u in rows:
                    try:
                        prefs = await _get_prefs(db, u.id)
                        inactivity = prefs.get("inactivity_alerts", {}) or {}
                        warn_sent = inactivity.get("tier_335_sent_at")
                        if not warn_sent:
                            continue
                        try:
                            warn_dt = datetime.fromisoformat(warn_sent.replace("Z", "+00:00"))
                        except Exception:
                            continue
                        if (now - warn_dt).days < 30:
                            continue
                        for tbl in JSON_TABLES:
                            if tbl == "broadcast_notifications":
                                continue
                            try:
                                await db.execute(text(f"DELETE FROM {tbl} WHERE user_id = :uid"), {"uid": u.id})
                            except Exception:
                                pass
                        await db.execute(text(
                            "UPDATE users SET is_active = FALSE, "
                            "email = CONCAT('deleted-', id, '@gdpr.local'), "
                            "name = 'Supprimé (RGPD)', password_hash = NULL "
                            "WHERE id = :uid"
                        ), {"uid": u.id})
                        await db.commit()
                        purged += 1
                        logger.info(f"[GDPR_PURGE] Purged user {u.id} (last login {u.last_login_at})")
                    except Exception as e:
                        await db.rollback()
                        logger.warning(f"[GDPR_PURGE] User {u.id} error: {e}")
                if purged > 0:
                    logger.info(f"[GDPR_PURGE] Total purged this run: {purged}")
        except Exception as e:
            logger.exception(f"[GDPR_PURGE] Loop error: {e}")
        await asyncio.sleep(INTERVAL)


async def inactivity_alerts_loop():
    """Background loop : toutes les 12h, scanne les users inactifs et envoie les relances."""
    await asyncio.sleep(120)
    logger.info("[CHURN_CRON] Inactivity alerts loop started")
    INTERVAL_SECONDS = 12 * 3600
    while True:
        try:
            async with async_session_factory() as db:
                from routes.branding import get_branding
                branding = await get_branding(db)
                now = _utc_now()
                for tier in TIERS:
                    cutoff = now - timedelta(days=tier["days"])
                    rows = (await db.execute(
                        select(User).where(
                            User.is_active == True,  # noqa: E712
                            User.last_login_at.isnot(None),
                            User.last_login_at <= cutoff,
                        )
                    )).scalars().all()
                    sent_count = 0
                    for u in rows:
                        try:
                            prefs = await _get_prefs(db, u.id)
                            inactivity = prefs.get("inactivity_alerts", {}) or {}
                            sent_at = inactivity.get(f"{tier['key']}_sent_at")
                            if sent_at:
                                try:
                                    sent_dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
                                    last_login = u.last_login_at if u.last_login_at.tzinfo else u.last_login_at.replace(tzinfo=timezone.utc)
                                    if sent_dt > last_login:
                                        continue
                                except Exception:
                                    continue
                            if prefs.get("inactivity_alerts_enabled") is False:
                                continue

                            ok, variant_idx = await _send_inactivity_alert(db, u, tier, branding)
                            if ok:
                                inactivity[f"{tier['key']}_sent_at"] = now.isoformat()
                                inactivity[f"{tier['key']}_variant"] = variant_idx
                                await _set_prefs(db, u.id, {"inactivity_alerts": inactivity})
                                # Enregistrer dans les stats A/B globales
                                await _record_ab_send(db, tier["key"], variant_idx)
                                sent_count += 1
                                await asyncio.sleep(2)
                        except Exception as ue:
                            logger.warning(f"[CHURN_CRON] User {u.id} tier {tier['key']} error: {ue}")
                    if sent_count > 0:
                        logger.info(f"[CHURN_CRON] Tier {tier['key']} ({tier['days']}j) — sent {sent_count} alerts")
        except Exception as e:
            logger.exception(f"[CHURN_CRON] Loop error: {e}")
        await asyncio.sleep(INTERVAL_SECONDS)


# ───────────── User-facing endpoints ─────────────
class InactivityPrefsIn(BaseModel):
    inactivity_alerts_enabled: bool | None = None


@churn_router.get("/prefs/inactivity")
async def get_inactivity_prefs(user: UserModel = Depends(get_current_user), db=Depends(get_db)):
    prefs = await _get_prefs(db, user.id)
    return {
        "enabled": prefs.get("inactivity_alerts_enabled", True),
        "last_alerts": prefs.get("inactivity_alerts", {}),
    }


@churn_router.patch("/prefs/inactivity")
async def set_inactivity_prefs(body: InactivityPrefsIn, user: UserModel = Depends(get_current_user), db=Depends(get_db)):
    patch = {k: v for k, v in body.dict().items() if v is not None}
    if not patch:
        return {"updated": False}
    new = await _set_prefs(db, user.id, patch)
    return {"updated": True, "enabled": new.get("inactivity_alerts_enabled", True)}


# ───────────── Brevo webhook (tracking opens/clicks) ─────────────
@churn_router.post("/brevo-event")
async def brevo_event_webhook(request: Request, db=Depends(get_db)):
    """
    Endpoint Brevo Inbound Events → reçoit les événements open/click.
    À configurer dans Brevo : Transactional → Webhooks → URL = /api/churn/brevo-event
    Événements à cocher : opened, clicked
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "invalid_json"}

    event_type = payload.get("event", "")   # "opened" | "clicked"
    # Brevo injecte les headers X- dans les métadonnées de l'email
    # On les retrouve dans payload["X-Mailin-custom"] ou headers
    custom = payload.get("X-Mailin-custom", "") or payload.get("tags", "")
    tier_key = None
    variant_idx = None

    # Chercher dans les tags Brevo ou custom
    if isinstance(custom, str):
        import re as re_mod
        t = re_mod.search(r"tier=([^,&\s]+)", custom)
        v = re_mod.search(r"variant=(\d)", custom)
        if t:
            tier_key = t.group(1)
        if v:
            variant_idx = int(v.group(1))

    if not tier_key or variant_idx is None:
        # Fallback: chercher dans les paramètres d'URL du lien cliqué
        url = payload.get("link", "")
        if "ab_tier=" in url:
            import urllib.parse
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            tier_key = (qs.get("ab_tier", [""])[0]) or tier_key
            vi = qs.get("ab_variant", [None])[0]
            if vi is not None:
                variant_idx = int(vi)

    if not tier_key or variant_idx is None:
        return {"status": "no_ab_metadata"}

    async with async_session_factory() as db2:
        if event_type in ("opened", "open"):
            await _record_ab_open(db2, tier_key, variant_idx)
        # clicks non différenciés ici — extension possible

    return {"status": "ok", "event": event_type, "tier": tier_key, "variant": variant_idx}


# ───────────── Admin endpoints ─────────────
@churn_router.get("/admin/inactivity/preview")
async def admin_inactivity_preview(admin=Depends(get_admin_user), db=Depends(get_db)):
    """Liste les users qui recevront chaque tier au prochain run."""
    now = _utc_now()
    preview = {}
    for tier in TIERS:
        cutoff = now - timedelta(days=tier["days"])
        rows = (await db.execute(
            select(User).where(
                User.is_active == True,  # noqa: E712
                User.last_login_at.isnot(None),
                User.last_login_at <= cutoff,
            )
        )).scalars().all()
        eligible = []
        for u in rows:
            prefs = await _get_prefs(db, u.id)
            inactivity = prefs.get("inactivity_alerts", {}) or {}
            sent_at = inactivity.get(f"{tier['key']}_sent_at")
            already = False
            if sent_at:
                try:
                    sent_dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
                    last_login = u.last_login_at if u.last_login_at.tzinfo else u.last_login_at.replace(tzinfo=timezone.utc)
                    if sent_dt > last_login:
                        already = True
                except Exception:
                    pass
            variant_idx = _get_ab_variant(u.id, tier["key"])
            eligible.append({
                "user_id": u.id,
                "email": u.email,
                "name": u.name,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "days_inactive": (now - (u.last_login_at if u.last_login_at.tzinfo else u.last_login_at.replace(tzinfo=timezone.utc))).days,
                "alert_already_sent": already,
                "alert_sent_at": sent_at,
                "will_send_next_run": not already and prefs.get("inactivity_alerts_enabled") is not False,
                "ab_variant": variant_idx,
                "ab_subject": TIER_AB_SUBJECTS.get(tier["key"], [""])[variant_idx],
            })
        preview[tier["key"]] = {
            "tier": tier["key"],
            "days": tier["days"],
            "subjects_ab": TIER_AB_SUBJECTS.get(tier["key"], []),
            "eligible_count": len(eligible),
            "will_send_next_run": sum(1 for e in eligible if e["will_send_next_run"]),
            "users": eligible[:50],
        }
    return preview


@churn_router.get("/admin/inactivity/ab-stats")
async def admin_ab_stats(admin=Depends(get_admin_user), db=Depends(get_db)):
    """Résultats A/B test : sent, opens, open_rate par tier et variante."""
    stats = await _get_ab_stats(db)
    result = {}
    for tier_key, variants in stats.items():
        tier_result = {}
        for v_key, v_data in variants.items():
            sent = v_data.get("sent", 0)
            opens = v_data.get("opens", 0)
            tier_result[v_key] = {
                "subject": v_data.get("subject", ""),
                "sent": sent,
                "opens": opens,
                "open_rate": round(opens / sent * 100, 1) if sent > 0 else 0,
                "clicks": v_data.get("clicks", 0),
            }
        result[tier_key] = tier_result
    return result


class TriggerIn(BaseModel):
    user_id: str
    tier: str   # tier_14 | tier_60 | tier_335


@churn_router.post("/admin/inactivity/trigger")
async def admin_inactivity_trigger(body: TriggerIn, admin=Depends(get_admin_user), db=Depends(get_db)):
    """Envoie manuellement une relance à un user (debug / test)."""
    tier = next((t for t in TIERS if t["key"] == body.tier), None)
    if not tier:
        return {"error": "Tier inconnu", "available_tiers": [t["key"] for t in TIERS]}
    r = await db.execute(select(User).where(User.id == body.user_id))
    u = r.scalar_one_or_none()
    if not u:
        return {"error": "User introuvable"}
    from routes.branding import get_branding
    branding = await get_branding(db)
    ok, variant_idx = await _send_inactivity_alert(db, u, tier, branding)
    if ok:
        prefs = await _get_prefs(db, u.id)
        inactivity = prefs.get("inactivity_alerts", {}) or {}
        inactivity[f"{tier['key']}_sent_at"] = _utc_now().isoformat()
        inactivity[f"{tier['key']}_variant"] = variant_idx
        await _set_prefs(db, u.id, {"inactivity_alerts": inactivity})
        await _record_ab_send(db, tier["key"], variant_idx)
    return {
        "sent": ok,
        "user_id": u.id,
        "tier": tier["key"],
        "ab_variant": variant_idx,
        "subject_used": TIER_AB_SUBJECTS.get(tier["key"], [""])[variant_idx] if ok else None,
    }
