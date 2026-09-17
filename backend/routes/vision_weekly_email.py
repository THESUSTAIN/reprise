"""Rappels Doux — Rappel hebdomadaire du Vision Board.

Envoyé chaque lundi à 7h (heure de Paris). Contenu de l'email :
  1. Le "why" / objectif de l'utilisateur
  2. Sa progression CA réelle (métriques live)
  3. Les 3 PROCHAINES ACTIONS du Coach Vision (nouveauté "Rappels Doux")

Chaque utilisateur peut désactiver le rappel via le toggle exposé par
`GET/PUT /api/vision/notif-settings` (clé `weekly_reminder`).

Pattern calqué sur churn_cron.py (background asyncio loop + Brevo).
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from database import async_session_factory
from models import User

logger = logging.getLogger(__name__)


def _is_monday_7am_paris(now_utc: datetime) -> bool:
    """Vrai si l'heure locale de Paris est lundi entre 7h00 et 7h35.
    Utilise zoneinfo pour gérer correctement l'heure d'hiver (UTC+1) ET
    l'heure d'été (UTC+2). La fenêtre de 35 min couvre le check toutes les 30 min."""
    try:
        from zoneinfo import ZoneInfo
        paris = now_utc.astimezone(ZoneInfo("Europe/Paris"))
    except Exception:
        # Repli : approxime en couvrant CET (6h UTC) et CEST (5h UTC)
        return now_utc.weekday() == 0 and now_utc.hour in (5, 6) and now_utc.minute < 35
    return paris.weekday() == 0 and paris.hour == 7 and paris.minute < 35


def _fmt_eur(v: float) -> str:
    return f"{v:,.0f} €".replace(",", " ")


def _txt(v):
    """Extrait le texte FR d'une valeur (string ou dict {fr, en})."""
    if isinstance(v, dict):
        return v.get("fr") or v.get("en") or ""
    return v or ""


def _render_weekly_email(name: str, why: str, live: dict, actions: list) -> str:
    ca = _fmt_eur(live.get("ca_month_eur", 0))
    objectif = _fmt_eur(live.get("objective_eur", 10000))
    progress = live.get("progress_percent", 0)
    leads = live.get("leads_count", 0)

    # Rendu des 3 prochaines actions du Coach — cœur de "Rappels Doux".
    actions_html = ""
    if actions:
        rows = []
        for i, a in enumerate(actions[:3], 1):
            title = (a.get("title") or "").strip()
            why_line = (a.get("why") or "").strip()
            if not title:
                continue
            rows.append(
                f"""
                <li style="display:flex;gap:12px;margin:0 0 12px;padding:12px 14px;background:#FAF8F3;border:1px solid #EFE8D7;border-radius:14px;list-style:none;">
                  <span style="flex:0 0 26px;height:26px;line-height:26px;text-align:center;border-radius:99px;background:#1A3A6E;color:#F6F2EA;font-weight:700;font-size:13px;">{i}</span>
                  <div style="flex:1;min-width:0;">
                    <p style="margin:0;font-size:14px;font-weight:600;color:#1a1814;">{title}</p>
                    {f'<p style="margin:2px 0 0;font-size:12.5px;color:#6a655a;line-height:1.45;">{why_line}</p>' if why_line else ""}
                  </div>
                </li>
                """
            )
        if rows:
            actions_html = f"""
              <p style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:#8a8578;margin:24px 0 10px;">Tes 3 prochaines actions</p>
              <ul style="padding:0;margin:0;">
                {''.join(rows)}
              </ul>
            """

    return f"""
    <div style="font-family:'Inter',Arial,sans-serif;max-width:560px;margin:0 auto;color:#1a1814;">
      <p style="font-size:15px;">Bonjour {name},</p>
      <p style="font-size:15px;">Cette semaine&nbsp;: <strong>« {why} »</strong></p>
      <div style="background:#FAF8F3;border:1px solid #EFE8D7;border-radius:16px;padding:20px 24px;margin:20px 0;">
        <p style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:#8a8578;margin:0 0 8px;">Votre progression</p>
        <p style="font-size:22px;margin:0;color:#1A3A6E;font-weight:600;">{ca} / {objectif} <span style="font-size:14px;color:#8a8578;font-weight:400;">({progress}%)</span></p>
        <div style="height:8px;background:#EFE8D7;border-radius:99px;margin-top:10px;overflow:hidden;">
          <div style="height:100%;width:{min(100, progress)}%;background:#1A3A6E;border-radius:99px;"></div>
        </div>
        <p style="font-size:13px;color:#8a8578;margin-top:10px;">Leads&nbsp;: {leads}</p>
      </div>
      {actions_html}
      <p style="font-size:14px;color:#4a463d;margin-top:24px;">Ouvre ton Vision Board pour transformer une action en carte objectif d'un simple tap.</p>
      <a href="https://app.zayado.net/vision-board" style="display:inline-block;margin-top:12px;background:#1A3A6E;color:#faf5e8;padding:12px 24px;border-radius:99px;text-decoration:none;font-weight:600;font-size:14px;">
        Voir mon Vision Board
      </a>
      <p style="margin-top:28px;font-size:11px;color:#a09b8f;line-height:1.6;">
        Tu reçois ce rappel doux car il est activé dans ton Vision Board. Pour le suspendre, ouvre le menu «&nbsp;⋯&nbsp;» → «&nbsp;Rappels doux&nbsp;».
      </p>
    </div>
    """


async def _get_next_coach_actions(db, user_id: str) -> list:
    """Récupère (ou génère) les 3 prochaines actions du Coach Vision pour ce user.

    Utilise directement la logique de `routes.vision_ext.coach_vision` sans
    passer par HTTP : on lit les cartes du canvas, on appelle Claude, on renvoie
    la liste `actions`. Retourne [] silencieusement en cas de canvas vide ou d'erreur.
    """
    try:
        from routes.vision_ext import BOARD_KEY, PILLARS_KEY
        from routes.vision_board import _get_kv
        # ── Chargement cartes + piliers ──
        board = await _get_kv(db, user_id, BOARD_KEY)
        cards = (board or {}).get("cards") or []
        pillars_data = await _get_kv(db, user_id, PILLARS_KEY)
        pillars = (pillars_data or {}).get("pillars") if pillars_data else None

        lines = []
        for c in cards[:40]:
            t = _txt(c.get("title"))
            b = _txt(c.get("body"))
            label = (t + (" — " + b if b else "")).strip()
            if label:
                lines.append(f"- [{c.get('type', 'note')}] {label[:160]}")
        pillar_lines = []
        for p in (pillars or []):
            pillar_lines.append(f"- {_txt(p.get('title'))} ({p.get('progress', 0)}%)")

        if not lines and not pillar_lines:
            return []

        from routes.vision_ext import _claude_complete_json
        system = (
            "Tu es un coach stratégique pour solo-entrepreneurs. À partir des cartes d'un vision board "
            "et des piliers, tu proposes les 3 PROCHAINES actions concrètes et priorisées. "
            "Réponds UNIQUEMENT en JSON strict, en français, sans markdown ni texte autour."
        )
        prompt = (
            "Cartes du canvas :\n" + ("\n".join(lines) or "(aucune)") +
            "\n\nPiliers :\n" + ("\n".join(pillar_lines) or "(aucun)") +
            "\n\nRenvoie ce JSON exact :\n"
            '{"summary": "1 phrase de synthèse bienveillante", '
            '"actions": [{"title": "action concrète (max 8 mots)", "why": "pourquoi maintenant (1 phrase)"}, '
            '{"title": "...", "why": "..."}, {"title": "...", "why": "..."}]}'
        )
        result = await _claude_complete_json(system, prompt, max_tokens=600)
        return (result.get("actions") or [])[:3]
    except Exception as e:
        logger.warning(f"[VISION_WEEKLY] Coach fetch failed for user {user_id}: {e}")
        return []


async def _send_weekly_reminder(db, user: User) -> bool:
    try:
        from utils import send_brevo_email
        from routes.vision_board import _get_live_metrics, _get_kv

        first_name = (user.name or "").split(" ")[0] if user.name else user.email.split("@")[0]
        settings = user.settings if isinstance(user.settings, dict) else {}
        why = settings.get("why") or settings.get("objective") or "Clarifier ma vision cette semaine"

        # ── Notif settings : respect de l'opt-out ──
        try:
            from routes.vision_ext import NOTIF_SETTINGS_KEY, DEFAULT_NOTIF_SETTINGS
            notif_kv = await _get_kv(db, user.id, NOTIF_SETTINGS_KEY)
            notif = {**DEFAULT_NOTIF_SETTINGS, **((notif_kv or {}).get("settings") or {})}
        except Exception:
            notif = {"weekly_reminder": True, "include_coach_actions": True}

        if not notif.get("weekly_reminder", True):
            logger.info(f"[VISION_WEEKLY] Skipped {user.email} (weekly_reminder=False)")
            return False

        # ── Métriques live + 3 prochaines actions du Coach ──
        live = await _get_live_metrics(db, user.id)
        actions = []
        if notif.get("include_coach_actions", True):
            actions = await _get_next_coach_actions(db, user.id)

        html = _render_weekly_email(first_name, why, live, actions)

        loop = asyncio.get_running_loop()
        ok = await loop.run_in_executor(
            None,
            lambda: send_brevo_email(
                to_email=user.email,
                to_name=user.name or "",
                subject=f"{first_name}, tes 3 prochaines actions cette semaine",
                html_content=html,
                brand="zayado",
            ),
        )
        return bool(ok)
    except Exception as e:
        logger.exception(f"[VISION_WEEKLY] Send failed for {user.email}: {e}")
        return False


async def vision_weekly_email_loop():
    """Background loop : vérifie toutes les 30 min si on est lundi ~7h,
    et envoie le rappel hebdomadaire à tous les users actifs (une seule fois
    par semaine ISO, tracké via user_data)."""
    await asyncio.sleep(180)
    logger.info("[VISION_WEEKLY] Loop started (Rappels Doux)")
    CHECK_INTERVAL = 30 * 60
    while True:
        try:
            now = datetime.now(timezone.utc)
            if _is_monday_7am_paris(now):
                iso_week = now.strftime("%G-W%V")
                async with async_session_factory() as db:
                    from routes.vision_board import _get_kv, _save_kv

                    rows = (await db.execute(
                        select(User).where(User.is_active == True)  # noqa: E712
                    )).scalars().all()
                    sent = 0
                    for u in rows:
                        try:
                            marker = await _get_kv(db, u.id, "vision_weekly_email_last_week")
                            if marker and marker.get("week") == iso_week:
                                continue  # déjà envoyé cette semaine
                            success = await _send_weekly_reminder(db, u)
                            if success:
                                await _save_kv(db, u.id, "vision_weekly_email_last_week", {"week": iso_week})
                                sent += 1
                        except Exception:
                            logger.exception(f"[VISION_WEEKLY] Failed for user {u.id}")
                    logger.info(f"[VISION_WEEKLY] Sent {sent} weekly reminders for week {iso_week}")
        except Exception:
            logger.exception("[VISION_WEEKLY] Loop iteration failed")
        await asyncio.sleep(CHECK_INTERVAL)
