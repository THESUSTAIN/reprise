"""
vision_board.py — Vision Board complet avec 3 templates + export Heyzine flipbook.

Templates disponibles :
  magazine   — Magazine du Futur (viral LinkedIn)
  trajectoire — Feuille de route 90j/1an/3ans avec KPIs
  arbre       — Arbre de Vie (signature Zayado)

Flow :
  1. POST /api/vision/board/generate-flipbook  → génère HTML, convertit en PDF, upload Heyzine
  2. Heyzine retourne une URL flipbook protégée par mot de passe
  3. L'URL + le mot de passe sont stockés en user_data (key="vision_board_flipbook")
  4. GET /api/vision/board/flipbook → retourne l'URL et le mot de passe du user
  5. DELETE /api/vision/board/flipbook → supprime le flipbook Heyzine + efface en DB

Variables d'environnement nécessaires :
  HEYZINE_API_KEY     — clé API Heyzine (plan avec protection par mot de passe)
  HEYZINE_PASSWORD    — mot de passe partagé pour tous les flipbooks (optionnel, sinon généré)
"""
import asyncio
import base64
import json
import logging
import os
import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vision/board", tags=["vision-board"])


# ─────────── Helpers ─────────────────────────────────────────────────

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gen_password(length: int = 8) -> str:
    """Génère un mot de passe alphanumérique lisible."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _get_kv(db: AsyncSession, user_id: str, key: str) -> dict | None:
    r = await db.execute(
        text("SELECT value FROM user_data WHERE user_id = :uid AND \"key\" = :k LIMIT 1"),
        {"uid": user_id, "k": key},
    )
    row = r.fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


async def _save_kv(db: AsyncSession, user_id: str, key: str, data: dict):
    value = json.dumps(data)
    now = _utc_now()
    existing = (await db.execute(
        text("SELECT id FROM user_data WHERE user_id = :uid AND \"key\" = :k"),
        {"uid": user_id, "k": key},
    )).fetchone()
    if existing:
        await db.execute(
            text("UPDATE user_data SET value = :v, updated_at = :ts WHERE user_id = :uid AND \"key\" = :k"),
            {"v": value, "ts": now, "uid": user_id, "k": key},
        )
    else:
        await db.execute(
            text("INSERT INTO user_data (id, user_id, \"key\", value, updated_at) VALUES (:id, :uid, :k, :v, :ts)"),
            {"id": str(uuid.uuid4()), "uid": user_id, "k": key, "v": value, "ts": now},
        )
    await db.commit()


async def _get_flipbook_data(db: AsyncSession, user_id: str) -> dict | None:
    return await _get_kv(db, user_id, "vision_board_flipbook")


async def _save_flipbook_data(db: AsyncSession, user_id: str, data: dict):
    await _save_kv(db, user_id, "vision_board_flipbook", data)


# ─────────── Métriques live (widgets dynamiques) ──────────────────────

async def _get_live_metrics(db: AsyncSession, user_id: str) -> dict:
    """Métriques temps réel du Cockpit, injectées dans le flipbook et affichées
    dans la bannière live du Vision Board (objectif CA, leads, progression)."""
    ca_month_eur = 0.0
    objective_eur = 10000.0
    leads_count = 0
    try:
        import datetime as _dt
        row = (await db.execute(
            text(
                "SELECT SUM(CASE WHEN amount_cents > 0 AND booked_at >= :month_start THEN amount_cents ELSE 0 END) "
                "FROM bank_transactions WHERE user_id = :uid"
            ),
            {"uid": user_id, "month_start": _dt.datetime.utcnow().replace(day=1).isoformat()},
        )).fetchone()
        if row and row[0] is not None:
            ca_month_eur = round((row[0] or 0) / 100, 2)
    except Exception:
        pass
    # Fallback (cohérent avec /api/dashboard) : si aucune transaction bancaire,
    # on alimente le CA du mois avec les entrées manuelles du Pilotage
    # (finance_entries, type=revenu) du mois courant. Sans cela la carte
    # "CA du mois" reste à 0 alors que des revenus existent → board non-vivant.
    if not ca_month_eur:
        try:
            import datetime as _dt2
            _mstart = _dt2.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            rev = (await db.execute(
                text(
                    "SELECT COALESCE(SUM(amount),0) FROM finance_entries "
                    "WHERE user_id = :uid AND type = 'revenu' AND date >= :ms"
                ),
                {"uid": user_id, "ms": _mstart},
            )).scalar() or 0
            ca_month_eur = round(float(rev), 2)
        except Exception:
            pass
    try:
        goal = (await db.execute(
            text("SELECT amount FROM budget_goals WHERE user_id = :uid AND category IN ('ca', 'revenu', 'chiffre_affaires') ORDER BY id DESC LIMIT 1"),
            {"uid": user_id},
        )).fetchone()
        if goal and goal[0]:
            objective_eur = float(goal[0])
    except Exception:
        pass
    try:
        row = (await db.execute(
            text("SELECT COUNT(*) FROM user_leads WHERE user_id = :uid"),
            {"uid": user_id},
        )).fetchone()
        if row and row[0] is not None:
            leads_count = int(row[0])
    except Exception:
        pass
    progress = min(100, round(ca_month_eur / objective_eur * 100)) if objective_eur else 0
    return {
        "ca_month_eur": ca_month_eur,
        "objective_eur": objective_eur,
        "leads_count": leads_count,
        "progress_percent": progress,
        "updated_at": _utc_now(),
    }


def _fmt_eur(v: float) -> str:
    return f"{v:,.0f} €".replace(",", " ")


def _live_metrics_band(live: dict) -> str:
    """Petite bande HTML injectée en bas du PDF flipbook avec les métriques réelles."""
    return f"""
<div style="position:absolute;bottom:0;left:0;right:0;background:#111;color:#fff;
  padding:14px 40px;display:flex;justify-content:space-between;align-items:center;
  font-family:'Inter',sans-serif;font-size:12px;letter-spacing:0.04em;">
  <span>Objectif CA&nbsp;: <strong>{_fmt_eur(live['ca_month_eur'])} / {_fmt_eur(live['objective_eur'])}</strong> ({live['progress_percent']}%)</span>
  <span>Leads&nbsp;: <strong>{live['leads_count']}</strong></span>
  <span style="opacity:0.6;">Mis à jour automatiquement</span>
</div>
"""


# ─────────── Générateurs de templates HTML ───────────────────────────

def _render_magazine(data: dict) -> str:
    """Template Magazine du Futur — style couverture de magazine premium."""
    name = data.get("name", "Votre Nom")
    year = data.get("year", "2029")
    headline = data.get("headline", f"Comment {name} a tout changé")
    subtitle = data.get("subtitle", "De la vision à l'impact : le parcours qui inspire une génération")
    achievement1 = data.get("achievement1", "10 000 entrepreneurs accompagnés")
    achievement2 = data.get("achievement2", "Chiffre d'affaires × 10 en 3 ans")
    achievement3 = data.get("achievement3", "Liberté totale · vie sur ses termes")
    quote = data.get("quote", "« J'ai arrêté de subir. J'ai commencé à construire. »")
    project = data.get("project", "Zayado")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;600&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 794px; height: 1123px; overflow: hidden;
    background: #0d0d0d; color: #f5f0e8;
    font-family: 'Inter', sans-serif;
    position: relative;
  }}
  .bg-pattern {{
    position: absolute; inset: 0;
    background: linear-gradient(135deg, #0d0d0d 0%, #1a1408 50%, #0d0d0d 100%);
  }}
  .gold-border {{
    position: absolute; inset: 12px;
    border: 1px solid #c9a84c;
    pointer-events: none;
    z-index: 10;
  }}
  .gold-border::before {{
    content: '';
    position: absolute; inset: 4px;
    border: 0.5px solid rgba(201,168,76,0.3);
  }}
  .logo-bar {{
    position: relative; z-index: 5;
    display: flex; align-items: center; justify-content: space-between;
    padding: 32px 48px 16px;
    border-bottom: 0.5px solid rgba(201,168,76,0.4);
  }}
  .mag-name {{
    font-family: 'Playfair Display', serif;
    font-size: 13px; letter-spacing: 0.5em;
    text-transform: uppercase; color: #c9a84c;
  }}
  .issue-info {{
    font-size: 10px; letter-spacing: 0.2em;
    color: rgba(245,240,232,0.5); text-transform: uppercase;
  }}
  .hero-zone {{
    position: relative; z-index: 5;
    padding: 48px 48px 0;
  }}
  .edition-tag {{
    display: inline-block;
    background: #c9a84c; color: #0d0d0d;
    font-size: 9px; font-weight: 600;
    letter-spacing: 0.3em; text-transform: uppercase;
    padding: 5px 14px; margin-bottom: 28px;
  }}
  .cover-headline {{
    font-family: 'Playfair Display', serif;
    font-size: 58px; line-height: 1.08;
    font-weight: 700; color: #f5f0e8;
    margin-bottom: 20px;
    max-width: 580px;
  }}
  .cover-headline em {{
    font-style: italic; color: #c9a84c;
  }}
  .cover-subtitle {{
    font-size: 15px; line-height: 1.65;
    color: rgba(245,240,232,0.7);
    max-width: 500px; margin-bottom: 40px;
    font-weight: 300;
  }}
  .divider {{
    width: 60px; height: 1px;
    background: #c9a84c; margin-bottom: 40px;
  }}
  .achievements {{
    display: flex; gap: 0;
    margin-bottom: 48px;
  }}
  .ach-item {{
    flex: 1; padding: 20px 24px;
    border-left: 0.5px solid rgba(201,168,76,0.3);
  }}
  .ach-item:first-child {{ border-left: none; padding-left: 0; }}
  .ach-number {{
    font-family: 'Playfair Display', serif;
    font-size: 28px; color: #c9a84c;
    font-weight: 700; line-height: 1;
    margin-bottom: 6px;
  }}
  .ach-label {{
    font-size: 11px; color: rgba(245,240,232,0.55);
    text-transform: uppercase; letter-spacing: 0.15em;
    line-height: 1.4;
  }}
  .quote-block {{
    position: relative; z-index: 5;
    margin: 0 48px;
    padding: 28px 32px;
    border-left: 2px solid #c9a84c;
    background: rgba(201,168,76,0.06);
  }}
  .quote-text {{
    font-family: 'Playfair Display', serif;
    font-size: 20px; font-style: italic;
    line-height: 1.6; color: #f5f0e8;
  }}
  .quote-author {{
    margin-top: 12px;
    font-size: 11px; letter-spacing: 0.2em;
    color: #c9a84c; text-transform: uppercase;
  }}
  .bottom-bar {{
    position: absolute; bottom: 0; left: 0; right: 0; z-index: 5;
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 48px;
    border-top: 0.5px solid rgba(201,168,76,0.3);
    background: rgba(13,13,13,0.8);
  }}
  .bottom-project {{
    font-size: 11px; letter-spacing: 0.3em;
    text-transform: uppercase; color: rgba(245,240,232,0.4);
  }}
  .bottom-year {{
    font-family: 'Playfair Display', serif;
    font-size: 32px; color: rgba(201,168,76,0.25);
    font-weight: 700;
  }}
</style>
</head>
<body>
<div class="bg-pattern"></div>
<div class="gold-border"></div>

<div class="logo-bar">
  <div class="mag-name">My Life · Vision</div>
  <div class="issue-info">Édition spéciale · Vision {year} · {name}</div>
</div>

<div class="hero-zone">
  <div class="edition-tag">Édition {year} · Couverture</div>
  <h1 class="cover-headline">{headline.replace(".", ".<br>")}</h1>
  <p class="cover-subtitle">{subtitle}</p>
  <div class="divider"></div>
  <div class="achievements">
    <div class="ach-item">
      <div class="ach-number">01</div>
      <div class="ach-label">{achievement1}</div>
    </div>
    <div class="ach-item">
      <div class="ach-number">02</div>
      <div class="ach-label">{achievement2}</div>
    </div>
    <div class="ach-item">
      <div class="ach-number">03</div>
      <div class="ach-label">{achievement3}</div>
    </div>
  </div>
</div>

<div class="quote-block">
  <div class="quote-text">{quote}</div>
  <div class="quote-author">— {name} · Fondateur {project}</div>
</div>

<div class="bottom-bar">
  <div class="bottom-project">Propulsé par {project}</div>
  <div class="bottom-year">{year}</div>
</div>
</body>
</html>"""


def _render_trajectoire(data: dict) -> str:
    """Template Trajectoire — feuille de route 90j/1an/3ans avec KPIs."""
    name = data.get("name", "Votre Nom")
    mission = data.get("mission", "Transformer la façon dont les entrepreneurs pilotent leur business")
    today_status = data.get("today_status", "Lancement produit · Premiers clients")
    j90_goal = data.get("j90_goal", "1 000 utilisateurs actifs")
    j90_kpi1 = data.get("j90_kpi1", "MRR : 5 000 €")
    j90_kpi2 = data.get("j90_kpi2", "NPS > 60")
    an1_goal = data.get("an1_goal", "10 000 utilisateurs · rentabilité")
    an1_kpi1 = data.get("an1_kpi1", "ARR : 120 000 €")
    an1_kpi2 = data.get("an1_kpi2", "Équipe : 3 personnes")
    an3_goal = data.get("an3_goal", "Leader européen · 100k entreprises")
    an3_kpi1 = data.get("an3_kpi1", "ARR : 2 M€")
    an3_kpi2 = data.get("an3_kpi2", "Impact : 100 000 solopreneurs")
    freedom_vision = data.get("freedom_vision", "Travailler 4h/jour depuis n'importe où dans le monde")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 794px; height: 1123px; overflow: hidden;
    background: #faf8f3; color: #1a1814;
    font-family: 'Inter', sans-serif;
  }}
  .header {{
    background: #1a2744; color: #f5f0e8;
    padding: 36px 48px;
    display: flex; justify-content: space-between; align-items: flex-end;
  }}
  .header-title {{
    font-family: 'Playfair Display', serif;
    font-size: 38px; font-weight: 700; line-height: 1.1;
  }}
  .header-title span {{
    font-style: italic; color: #c9a84c;
  }}
  .header-name {{
    font-size: 12px; letter-spacing: 0.25em;
    color: rgba(245,240,232,0.5); text-transform: uppercase;
    margin-top: 8px;
  }}
  .header-today {{
    text-align: right;
  }}
  .today-label {{
    font-size: 10px; letter-spacing: 0.25em;
    text-transform: uppercase; color: rgba(245,240,232,0.45);
    margin-bottom: 4px;
  }}
  .today-value {{
    font-size: 13px; color: rgba(245,240,232,0.75);
    max-width: 220px; text-align: right; line-height: 1.5;
  }}
  .mission-bar {{
    background: #c9a84c; padding: 14px 48px;
    font-size: 12px; letter-spacing: 0.08em;
    color: #1a1814; font-weight: 600;
    display: flex; align-items: center; gap: 12px;
  }}
  .mission-label {{
    font-size: 9px; letter-spacing: 0.3em;
    text-transform: uppercase; opacity: 0.6;
  }}
  .timeline {{
    display: flex; padding: 0 48px;
    gap: 0; margin-top: 32px;
    position: relative;
  }}
  .timeline::before {{
    content: '';
    position: absolute;
    top: 22px; left: 48px; right: 48px;
    height: 1px; background: #d4cfc6;
  }}
  .milestone {{
    flex: 1; position: relative; padding-top: 0;
  }}
  .milestone-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: #1a2744; border: 2px solid #faf8f3;
    box-shadow: 0 0 0 1.5px #1a2744;
    margin-bottom: 16px; position: relative; z-index: 2;
  }}
  .milestone-dot.gold {{ background: #c9a84c; box-shadow: 0 0 0 1.5px #c9a84c; }}
  .milestone-tag {{
    font-size: 9px; letter-spacing: 0.3em;
    text-transform: uppercase; color: #9a8f80;
    margin-bottom: 6px;
  }}
  .milestone-period {{
    font-family: 'Playfair Display', serif;
    font-size: 22px; font-weight: 700; color: #1a2744;
    margin-bottom: 4px;
  }}
  .milestone-period.accent {{ color: #c9a84c; }}
  .milestone-goal {{
    font-size: 12px; color: #4a4540; line-height: 1.5;
    margin-bottom: 14px; max-width: 170px;
  }}
  .kpi-list {{ display: flex; flex-direction: column; gap: 6px; }}
  .kpi-item {{
    display: flex; align-items: center; gap: 8px;
    font-size: 11px; color: #6a6058;
  }}
  .kpi-dot {{
    width: 4px; height: 4px; border-radius: 50%;
    background: #c9a84c; flex-shrink: 0;
  }}
  .freedom-section {{
    margin: 32px 48px 0;
    background: #1a2744;
    padding: 28px 32px;
    display: flex; align-items: center; gap: 24px;
  }}
  .freedom-icon {{
    font-size: 36px; flex-shrink: 0;
  }}
  .freedom-label {{
    font-size: 9px; letter-spacing: 0.3em;
    text-transform: uppercase; color: #c9a84c;
    margin-bottom: 6px;
  }}
  .freedom-text {{
    font-family: 'Playfair Display', serif;
    font-size: 18px; font-style: italic;
    color: #f5f0e8; line-height: 1.5;
  }}
  .bottom-section {{
    margin: 28px 48px 0;
    display: grid; grid-template-columns: 1fr 1fr 1fr;
    gap: 1px; background: #d4cfc6;
    border: 1px solid #d4cfc6;
  }}
  .bottom-cell {{
    background: #faf8f3; padding: 20px 22px;
  }}
  .cell-label {{
    font-size: 9px; letter-spacing: 0.25em;
    text-transform: uppercase; color: #9a8f80;
    margin-bottom: 6px;
  }}
  .cell-value {{
    font-family: 'Playfair Display', serif;
    font-size: 16px; color: #1a2744;
    line-height: 1.4;
  }}
  .footer {{
    position: absolute; bottom: 0; left: 0; right: 0;
    display: flex; justify-content: space-between; align-items: center;
    padding: 14px 48px;
    border-top: 0.5px solid #d4cfc6;
    background: #faf8f3;
  }}
  .footer-name {{
    font-size: 10px; letter-spacing: 0.25em;
    text-transform: uppercase; color: #9a8f80;
  }}
  .footer-brand {{
    font-family: 'Playfair Display', serif;
    font-size: 12px; color: #c9a84c;
  }}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="header-title">Ma <span>Trajectoire</span></div>
    <div class="header-name">{name}</div>
  </div>
  <div class="header-today">
    <div class="today-label">Aujourd'hui</div>
    <div class="today-value">{today_status}</div>
  </div>
</div>

<div class="mission-bar">
  <span class="mission-label">Mission ·</span>
  {mission}
</div>

<div class="timeline">
  <div class="milestone">
    <div class="milestone-dot"></div>
    <div class="milestone-tag">Point de départ</div>
    <div class="milestone-period">Maintenant</div>
    <div class="milestone-goal">{today_status}</div>
  </div>
  <div class="milestone">
    <div class="milestone-dot"></div>
    <div class="milestone-tag">Horizon court</div>
    <div class="milestone-period">90 jours</div>
    <div class="milestone-goal">{j90_goal}</div>
    <div class="kpi-list">
      <div class="kpi-item"><span class="kpi-dot"></span>{j90_kpi1}</div>
      <div class="kpi-item"><span class="kpi-dot"></span>{j90_kpi2}</div>
    </div>
  </div>
  <div class="milestone">
    <div class="milestone-dot"></div>
    <div class="milestone-tag">Horizon moyen</div>
    <div class="milestone-period">1 an</div>
    <div class="milestone-goal">{an1_goal}</div>
    <div class="kpi-list">
      <div class="kpi-item"><span class="kpi-dot"></span>{an1_kpi1}</div>
      <div class="kpi-item"><span class="kpi-dot"></span>{an1_kpi2}</div>
    </div>
  </div>
  <div class="milestone">
    <div class="milestone-dot gold"></div>
    <div class="milestone-tag">Vision long terme</div>
    <div class="milestone-period accent">3 ans</div>
    <div class="milestone-goal">{an3_goal}</div>
    <div class="kpi-list">
      <div class="kpi-item"><span class="kpi-dot"></span>{an3_kpi1}</div>
      <div class="kpi-item"><span class="kpi-dot"></span>{an3_kpi2}</div>
    </div>
  </div>
</div>

<div class="freedom-section">
  <div class="freedom-icon">🌍</div>
  <div>
    <div class="freedom-label">Ma vision de liberté</div>
    <div class="freedom-text">{freedom_vision}</div>
  </div>
</div>

<div class="bottom-section">
  <div class="bottom-cell">
    <div class="cell-label">Focus actuel</div>
    <div class="cell-value">Acquisition & product-market fit</div>
  </div>
  <div class="bottom-cell">
    <div class="cell-label">Ressource clé</div>
    <div class="cell-value">Temps · Énergie · Réseau</div>
  </div>
  <div class="bottom-cell">
    <div class="cell-label">Non-négociable</div>
    <div class="cell-value">Famille · Santé · Intégrité</div>
  </div>
</div>

<div class="footer">
  <div class="footer-name">{name} · Vision Board</div>
  <div class="footer-brand">Zayado</div>
</div>
</body>
</html>"""


def _render_arbre(data: dict) -> str:
    """Template Arbre de Vie — signature Zayado avec SVG intégré."""
    name = data.get("name", "Votre Nom")
    valeur1 = data.get("valeur1", "Liberté")
    valeur2 = data.get("valeur2", "Impact")
    valeur3 = data.get("valeur3", "Authenticité")
    mission = data.get("mission", "Accompagner 10 000 entrepreneurs vers leur vie idéale")
    branch_business = data.get("branch_business", "Zayado · SaaS · 1M ARR")
    branch_sante = data.get("branch_sante", "Sport quotidien · Énergie maximale")
    branch_famille = data.get("branch_famille", "Présent · Épanoui · Modèle")
    branch_impact = data.get("branch_impact", "Communauté · Livre · Conférences")
    fruit1 = data.get("fruit1", "Liberté financière")
    fruit2 = data.get("fruit2", "Famille heureuse")
    fruit3 = data.get("fruit3", "Héritage durable")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 794px; height: 1123px; overflow: hidden;
    background: #f7f4ed; color: #1a1814;
    font-family: 'Inter', sans-serif;
    position: relative;
  }}
  .header {{
    padding: 36px 48px 24px;
    border-bottom: 0.5px solid #d8d2c4;
    display: flex; justify-content: space-between; align-items: flex-end;
  }}
  .title-block .eyebrow {{
    font-size: 10px; letter-spacing: 0.35em;
    text-transform: uppercase; color: #8a7d68;
    margin-bottom: 6px;
  }}
  .title-block h1 {{
    font-family: 'Playfair Display', serif;
    font-size: 36px; font-weight: 700; color: #1a2744;
  }}
  .title-block h1 span {{ font-style: italic; color: #c9a84c; }}
  .name-badge {{
    background: #1a2744; color: #f5f0e8;
    padding: 8px 18px; font-size: 12px;
    letter-spacing: 0.2em; text-transform: uppercase;
  }}
  .roots-section {{
    padding: 20px 48px 16px;
    background: #1a2744;
    display: flex; align-items: center; gap: 16px;
  }}
  .roots-label {{
    font-size: 9px; letter-spacing: 0.3em;
    text-transform: uppercase; color: rgba(245,240,232,0.4);
    flex-shrink: 0;
  }}
  .roots-values {{
    display: flex; gap: 24px;
  }}
  .root-value {{
    font-family: 'Playfair Display', serif;
    font-size: 16px; font-style: italic;
    color: #c9a84c;
  }}
  .root-value::before {{ content: '· '; color: rgba(201,168,76,0.4); }}
  .root-value:first-child::before {{ content: ''; }}
  .trunk-section {{
    margin: 0 48px;
    padding: 18px 24px;
    background: #2d4a1e; color: #e8f4df;
    display: flex; align-items: center; gap: 16px;
  }}
  .trunk-label {{
    font-size: 9px; letter-spacing: 0.3em;
    text-transform: uppercase; color: rgba(232,244,223,0.5);
    flex-shrink: 0; margin-top: 2px;
  }}
  .trunk-mission {{
    font-family: 'Playfair Display', serif;
    font-size: 17px; font-style: italic;
    line-height: 1.5;
  }}
  .branches-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 12px; margin: 20px 48px 0;
  }}
  .branch {{
    border: 1px solid #d8d2c4;
    background: white;
    padding: 20px 22px;
  }}
  .branch-header {{
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 10px;
  }}
  .branch-icon {{
    font-size: 18px;
  }}
  .branch-name {{
    font-family: 'Playfair Display', serif;
    font-size: 16px; color: #1a2744;
  }}
  .branch-content {{
    font-size: 12px; color: #5a5248; line-height: 1.6;
  }}
  .branch-bar {{
    margin-top: 10px; height: 2px;
    background: #e8e4dc;
    position: relative;
  }}
  .branch-bar::after {{
    content: '';
    position: absolute; top: 0; left: 0;
    height: 100%; width: 65%;
    background: #c9a84c;
  }}
  .fruits-section {{
    margin: 20px 48px 0;
    display: flex; gap: 0;
    border: 1px solid #d8d2c4;
  }}
  .fruit-item {{
    flex: 1; padding: 16px 20px;
    border-left: 1px solid #d8d2c4;
    display: flex; align-items: center; gap: 10px;
  }}
  .fruit-item:first-child {{ border-left: none; }}
  .fruit-emoji {{ font-size: 20px; flex-shrink: 0; }}
  .fruit-text {{
    font-size: 12px; color: #3a3530;
    font-weight: 500;
  }}
  .footer {{
    position: absolute; bottom: 0; left: 0; right: 0;
    padding: 14px 48px;
    border-top: 0.5px solid #d8d2c4;
    display: flex; justify-content: space-between; align-items: center;
    background: #f7f4ed;
  }}
  .footer-name {{
    font-size: 10px; letter-spacing: 0.2em;
    text-transform: uppercase; color: #9a8f80;
  }}
  .footer-brand {{
    font-family: 'Playfair Display', serif;
    font-size: 13px; color: #c9a84c;
  }}
</style>
</head>
<body>
<div class="header">
  <div class="title-block">
    <div class="eyebrow">Vision Board · Arbre de Vie</div>
    <h1>Mon <span>Arbre de Vie</span></h1>
  </div>
  <div class="name-badge">{name}</div>
</div>

<div class="roots-section">
  <div class="roots-label">🌱 Racines · Valeurs</div>
  <div class="roots-values">
    <div class="root-value">{valeur1}</div>
    <div class="root-value">{valeur2}</div>
    <div class="root-value">{valeur3}</div>
  </div>
</div>

<div class="trunk-section">
  <div class="trunk-label">🌳 Tronc · Mission</div>
  <div class="trunk-mission">{mission}</div>
</div>

<div class="branches-grid">
  <div class="branch">
    <div class="branch-header">
      <span class="branch-icon">💼</span>
      <div class="branch-name">Business</div>
    </div>
    <div class="branch-content">{branch_business}</div>
    <div class="branch-bar"></div>
  </div>
  <div class="branch">
    <div class="branch-header">
      <span class="branch-icon">🏃</span>
      <div class="branch-name">Santé</div>
    </div>
    <div class="branch-content">{branch_sante}</div>
    <div class="branch-bar"></div>
  </div>
  <div class="branch">
    <div class="branch-header">
      <span class="branch-icon">👨‍👩‍👧</span>
      <div class="branch-name">Famille</div>
    </div>
    <div class="branch-content">{branch_famille}</div>
    <div class="branch-bar"></div>
  </div>
  <div class="branch">
    <div class="branch-header">
      <span class="branch-icon">🌍</span>
      <div class="branch-name">Impact</div>
    </div>
    <div class="branch-content">{branch_impact}</div>
    <div class="branch-bar"></div>
  </div>
</div>

<div class="fruits-section">
  <div class="fruit-item">
    <span class="fruit-emoji">🍎</span>
    <div class="fruit-text">{fruit1}</div>
  </div>
  <div class="fruit-item">
    <span class="fruit-emoji">🍊</span>
    <div class="fruit-text">{fruit2}</div>
  </div>
  <div class="fruit-item">
    <span class="fruit-emoji">✨</span>
    <div class="fruit-text">{fruit3}</div>
  </div>
</div>

<div class="footer">
  <div class="footer-name">{name} · Vision Board</div>
  <div class="footer-brand">Zayado</div>
</div>
</body>
</html>"""


TEMPLATE_RENDERERS = {
    "magazine": _render_magazine,
    "trajectoire": _render_trajectoire,
    "arbre": _render_arbre,
}

TEMPLATE_QUESTIONS = {
    "magazine": {
        "name": "Votre prénom / nom",
        "year": "Année cible (ex: 2029)",
        "headline": "Votre titre de une (ex: Comment Julien a bâti Zayado)",
        "subtitle": "Sous-titre inspirant",
        "achievement1": "Accomplissement #1",
        "achievement2": "Accomplissement #2",
        "achievement3": "Accomplissement #3",
        "quote": "Votre citation clé",
        "project": "Nom de votre projet/entreprise",
    },
    "trajectoire": {
        "name": "Votre prénom",
        "mission": "Votre mission en une phrase",
        "today_status": "Situation actuelle (1-2 mots)",
        "j90_goal": "Objectif 90 jours",
        "j90_kpi1": "KPI 90j #1 (ex: MRR 5k€)",
        "j90_kpi2": "KPI 90j #2",
        "an1_goal": "Objectif 1 an",
        "an1_kpi1": "KPI 1an #1",
        "an1_kpi2": "KPI 1an #2",
        "an3_goal": "Vision 3 ans",
        "an3_kpi1": "KPI 3ans #1",
        "an3_kpi2": "KPI 3ans #2",
        "freedom_vision": "Votre vision de liberté",
    },
    "arbre": {
        "name": "Votre prénom",
        "valeur1": "Valeur fondamentale #1",
        "valeur2": "Valeur fondamentale #2",
        "valeur3": "Valeur fondamentale #3",
        "mission": "Votre mission (tronc)",
        "branch_business": "Branche Business",
        "branch_sante": "Branche Santé",
        "branch_famille": "Branche Famille",
        "branch_impact": "Branche Impact",
        "fruit1": "Fruit / résultat #1",
        "fruit2": "Fruit / résultat #2",
        "fruit3": "Fruit / résultat #3",
    },
}


# ─────────── HTML → PDF (weasyprint ou playwright) ───────────────────

async def _html_to_pdf(html: str) -> bytes:
    """Convertit HTML en PDF. Essaie weasyprint d'abord, puis playwright."""
    loop = asyncio.get_running_loop()

    # Tentative weasyprint
    try:
        import weasyprint
        def _render():
            return weasyprint.HTML(string=html).write_pdf()
        return await loop.run_in_executor(None, _render)
    except ImportError:
        pass
    except Exception as e:
        log.warning(f"weasyprint failed: {e}")

    # Tentative playwright
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")
            pdf_bytes = await page.pdf(
                width="794px", height="1123px",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            await browser.close()
            return pdf_bytes
    except ImportError:
        pass
    except Exception as e:
        log.warning(f"playwright failed: {e}")

    raise HTTPException(503, "Conversion PDF indisponible. Installez weasyprint ou playwright.")


# ─────────── Heyzine API ─────────────────────────────────────────────

async def _upload_to_heyzine(pdf_bytes: bytes, title: str, password: str) -> str:
    """
    Upload un PDF vers Heyzine et retourne l'URL du flipbook.
    Doc API : https://heyzine.com/api
    """
    api_key = os.environ.get("HEYZINE_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "HEYZINE_API_KEY manquant dans les variables d'environnement")

    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    payload = {
        "pdf": pdf_b64,
        "title": title,
        "password": password,
        "language": "fr",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://heyzine.com/api1/retrive",
            json=payload,
            headers={
                "k": api_key,
                "Content-Type": "application/json",
            },
        )

    if r.status_code != 200:
        log.error(f"Heyzine error {r.status_code}: {r.text[:300]}")
        raise HTTPException(502, f"Erreur Heyzine {r.status_code}: {r.text[:100]}")

    data = r.json()
    url = data.get("url") or data.get("flipbook_url") or data.get("link")
    if not url:
        log.error(f"Heyzine response sans URL: {data}")
        raise HTTPException(502, "Heyzine n'a pas retourné d'URL")

    return url


# ─────────── Schémas ─────────────────────────────────────────────────

TemplateType = Literal["magazine", "trajectoire", "arbre"]


class GenerateFlipbookRequest(BaseModel):
    template: TemplateType
    data: dict = Field(default_factory=dict)
    password: Optional[str] = None  # si None → généré automatiquement


class GenerateImageRequest(BaseModel):
    """Rétrocompatibilité avec l'ancien endpoint Gemini."""
    prompt: str = Field(min_length=4, max_length=1000)
    label: Optional[str] = None
    base_images: Optional[list[str]] = None


# ─────────── Endpoints ───────────────────────────────────────────────

@router.get("/templates")
async def list_templates(user: User = Depends(get_current_user)):
    """Liste les 3 templates disponibles avec leurs champs."""
    return {
        "templates": [
            {
                "id": "magazine",
                "name": "Magazine du Futur",
                "emoji": "📖",
                "description": "Couverture de magazine premium · viral LinkedIn",
                "best_for": "Hook fort · partage social · vision aspirationnelle",
                "fields": TEMPLATE_QUESTIONS["magazine"],
            },
            {
                "id": "trajectoire",
                "name": "Trajectoire",
                "emoji": "🛣️",
                "description": "Feuille de route 90j / 1an / 3ans avec KPIs",
                "best_for": "Entrepreneurs · clarté opérationnelle · accountability",
                "fields": TEMPLATE_QUESTIONS["trajectoire"],
            },
            {
                "id": "arbre",
                "name": "Arbre de Vie",
                "emoji": "🌳",
                "description": "Valeurs → Mission → 4 branches → Fruits",
                "best_for": "Signature Zayado · profondeur · équilibre de vie",
                "fields": TEMPLATE_QUESTIONS["arbre"],
            },
        ]
    }


@router.get("/flipbook")
async def get_flipbook(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retourne l'URL et le mot de passe du flipbook existant, avec un flag
    `stale` si les métriques live (CA, objectif, leads) ont changé depuis la
    dernière génération — le frontend déclenche alors un /refresh automatique."""
    data = await _get_flipbook_data(db, user.id)
    if not data:
        return {"flipbook": None}
    live = await _get_live_metrics(db, user.id)
    snapshot = data.get("live_snapshot") or {}
    stale = (
        snapshot.get("objective_eur") != live["objective_eur"]
        or snapshot.get("leads_count") != live["leads_count"]
        or abs((snapshot.get("ca_month_eur") or 0) - live["ca_month_eur"]) >= max(50, live["objective_eur"] * 0.03)
    )
    return {"flipbook": {**data, "stale": stale}, "live_metrics": live}


@router.get("/live-metrics")
async def get_live_metrics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Métriques temps réel pour la bannière du Vision Board (widgets dynamiques)."""
    return await _get_live_metrics(db, user.id)


@router.post("/refresh")
async def refresh_flipbook(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Régénère le flipbook existant avec les métriques live à jour (objectif CA,
    leads…) sans repasser par le formulaire. Appelé automatiquement par le frontend
    quand la page détecte un flipbook `stale`, ou juste après un changement d'objectif."""
    existing = await _get_flipbook_data(db, user.id)
    if not existing:
        raise HTTPException(404, "Aucun Vision Board à régénérer.")
    template = existing.get("template")
    renderer = TEMPLATE_RENDERERS.get(template)
    if not renderer:
        raise HTTPException(400, f"Template inconnu: {template}")

    data = dict(existing.get("form_data") or {"name": existing.get("user_name")})
    live = await _get_live_metrics(db, user.id)

    try:
        html = renderer(data)
        html = html.replace("</body>", _live_metrics_band(live) + "</body>")
    except Exception as e:
        raise HTTPException(500, f"Erreur de rendu HTML: {e}")

    pdf_bytes = await _html_to_pdf(html)
    password = existing.get("password") or _gen_password(8)
    title = existing.get("title") or f"Vision Board · {existing.get('user_name')} · {str(template).capitalize()}"
    flipbook_url = await _upload_to_heyzine(pdf_bytes, title, password)

    flipbook_data = {
        **existing,
        "url": flipbook_url,
        "password": password,
        "updated_at": _utc_now(),
        "live_snapshot": live,
    }
    await _save_flipbook_data(db, user.id, flipbook_data)
    return {"ok": True, "flipbook": {**flipbook_data, "stale": False}, "live_metrics": live}


@router.post("/generate-flipbook")
async def generate_flipbook(
    payload: GenerateFlipbookRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pipeline complet :
    1. Injecter les données user dans le template HTML
    2. Convertir en PDF
    3. Uploader sur Heyzine avec mot de passe
    4. Sauvegarder URL + mot de passe en DB
    5. Retourner les données au frontend
    """
    renderer = TEMPLATE_RENDERERS.get(payload.template)
    if not renderer:
        raise HTTPException(400, f"Template inconnu: {payload.template}")

    # Injecter le prénom depuis le profil si absent
    if not payload.data.get("name") and user.name:
        payload.data["name"] = user.name.split()[0]

    # 0. Métriques live (widgets dynamiques) — injectées dans le PDF
    live = await _get_live_metrics(db, user.id)

    # 1. Générer HTML
    try:
        html = renderer(payload.data)
        html = html.replace("</body>", _live_metrics_band(live) + "</body>")
    except Exception as e:
        raise HTTPException(500, f"Erreur de rendu HTML: {e}")

    # 2. Convertir en PDF
    pdf_bytes = await _html_to_pdf(html)

    # 3. Mot de passe (fixe env ou généré)
    password = (
        payload.password
        or os.environ.get("HEYZINE_PASSWORD")
        or _gen_password(8)
    )

    # 4. Upload Heyzine
    name = payload.data.get("name", user.name or "Vision")
    title = f"Vision Board · {name} · {payload.template.capitalize()}"
    flipbook_url = await _upload_to_heyzine(pdf_bytes, title, password)

    # 5. Sauvegarder en DB (form_data + snapshot live pour la détection de staleness)
    flipbook_data = {
        "url": flipbook_url,
        "password": password,
        "template": payload.template,
        "title": title,
        "created_at": _utc_now(),
        "user_name": name,
        "form_data": payload.data,
        "live_snapshot": live,
    }
    await _save_flipbook_data(db, user.id, flipbook_data)

    return {
        "ok": True,
        "flipbook": flipbook_data,
        "live_metrics": live,
    }


@router.delete("/flipbook")
async def delete_flipbook(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprime le flipbook en DB (Heyzine ne propose pas de delete API)."""
    await db.execute(
        text("DELETE FROM user_data WHERE user_id = :uid AND \"key\" = 'vision_board_flipbook'"),
        {"uid": user.id},
    )
    await db.commit()
    return {"ok": True}


@router.get("/preview-html")
async def preview_html(
    template: TemplateType,
    user: User = Depends(get_current_user),
):
    """Retourne le HTML du template avec des données exemple (pour preview frontend)."""
    renderer = TEMPLATE_RENDERERS.get(template)
    if not renderer:
        raise HTTPException(400, "Template inconnu")
    name = (user.name or "").split()[0] or "Julien"
    sample_data = {"name": name}
    html = renderer(sample_data)
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


# Endpoint PUBLIC (pas d'auth) pour le showcase /vision-board sur public-site.
# Ne révèle aucune donnée user — utilise un sample fixe "Margaux".
@router.get("/preview-public")
async def preview_html_public(template: TemplateType):
    """Preview HTML public (no auth) pour iframe sur public-site /vision-board."""
    renderer = TEMPLATE_RENDERERS.get(template)
    if not renderer:
        raise HTTPException(400, "Template inconnu")
    sample_data = {
        "name": "Margaux",
        "summary": "Mon why : aider les entrepreneurs à entreprendre sans s'épuiser.",
        "values": ["Calme", "Lucidité", "Trajectoire", "Durabilité"],
        "keywords": ["IA", "30% humain", "Sérénité", "Cap clair"],
        "domains": ["Business", "Famille", "Santé", "Apprentissage", "Communauté"],
    }
    html = renderer(sample_data)
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


# ─────────── Rétrocompatibilité ancienne API Gemini ──────────────────

@router.post("/generate")
async def generate_board_image_legacy(
    payload: GenerateImageRequest,
    user: User = Depends(get_current_user),
):
    """Génère une image de board via Mammouth (image model)."""
    from mammouth_client import generate_image as mammouth_image, MammouthError, MAMMOUTH_API_KEY
    if not MAMMOUTH_API_KEY:
        raise HTTPException(503, "Génération d'image indisponible.")
    try:
        image_bytes = await mammouth_image(payload.prompt, size="1024x1024")
        data = base64.b64encode(image_bytes).decode()
        return {"ok": True, "image": f"data:image/png;base64,{data}", "label": payload.label}
    except MammouthError as e:
        raise HTTPException(502, f"Échec: {e}")
    except Exception as e:
        raise HTTPException(502, f"Échec: {e}")


# ─────────── Canvas WYSIWYG (drag & drop libre) ────────────────────────
# Persistance simple en user_data (key="vision_board_canvas") : liste
# d'éléments (image / texte / forme) avec position, taille, rotation, z-index.

class CanvasElement(BaseModel):
    id: str
    type: Literal["image", "text", "shape"]
    x: float = 40
    y: float = 40
    width: float = 200
    height: float = 200
    rotation: float = 0
    z: int = 0
    # image
    src: Optional[str] = None
    # text
    content: Optional[str] = None
    font_size: Optional[int] = 18
    color: Optional[str] = "#1A3A6E"
    font_family: Optional[str] = "Inter, sans-serif"
    # shape
    shape: Optional[Literal["rect", "circle", "line"]] = None
    fill: Optional[str] = "#EFE8D7"
    stroke: Optional[str] = "#1A3A6E"


class CanvasSaveRequest(BaseModel):
    elements: list[CanvasElement] = Field(default_factory=list)
    background: Optional[str] = "#FAF8F3"


@router.get("/canvas")
async def get_canvas(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retourne le canvas libre (images/texte/formes positionnés) de l'utilisateur."""
    data = await _get_kv(db, user.id, "vision_board_canvas")
    if not data:
        return {"elements": [], "background": "#FAF8F3"}
    return data


@router.put("/canvas")
async def save_canvas(
    payload: CanvasSaveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sauvegarde l'état complet du canvas (repositionnement libre, texte, formes)."""
    data = {
        "elements": [e.dict() for e in payload.elements],
        "background": payload.background,
        "updated_at": _utc_now(),
    }
    await _save_kv(db, user.id, "vision_board_canvas", data)
    return {"ok": True, **data}



# ─────────── Inspirer : génération de citation via Mammouth ───────────
class InspireRequest(BaseModel):
    universe: Optional[str] = None  # "entrepreneur" | "biblique" | "stoicien" | "croissance"


@router.post("/inspire")
async def inspire_quote(
    payload: InspireRequest,
    user: User = Depends(get_current_user),
):
    """Génère une citation inspirante (via Mammouth) selon l'univers choisi."""
    from mammouth_client import chat as mammouth_chat, MammouthError

    settings = (user.settings or {})
    universe = (payload.universe or settings.get("spirituality") or "entrepreneur").lower()
    tone = {
        "biblique": "une citation biblique (verset) porteuse d'espérance et de sens pour un entrepreneur",
        "stoicien": "une citation stoïcienne (Sénèque, Marc Aurèle, Épictète) sur la discipline et le contrôle de soi",
        "croissance": "une citation sur la croissance personnelle et la persévérance",
    }.get(universe, "une citation entrepreneuriale percutante et motivante")

    prompt = (
        f"Donne {tone}, en français. "
        "Réponds UNIQUEMENT en JSON strict, sans texte autour, au format "
        '{"quote": "...", "author": "..."}. '
        "La citation doit faire moins de 160 caractères."
    )
    try:
        raw = await mammouth_chat(
            messages=[
                {"role": "system", "content": "Tu es un coach qui inspire des entrepreneurs indépendants."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.9,
        )
    except MammouthError as e:
        raise HTTPException(503, f"Génération indisponible : {e}")

    quote, author = None, None
    try:
        start, end = raw.find("{"), raw.rfind("}")
        parsed = json.loads(raw[start:end + 1]) if start != -1 else {}
        quote = (parsed.get("quote") or "").strip()
        author = (parsed.get("author") or "").strip()
    except Exception:
        quote = raw.strip().strip('"')
    if not quote:
        raise HTTPException(502, "Réponse vide.")
    return {"quote": quote, "author": author or "Anonyme", "universe": universe}


# ─────────── AI Document : génération de contenu structuré via Mammouth ─────
# Inspiré de storyflow.so : générer un document complet (brief, plan, positioning,
# swot narratif…) directement dans le board, puis l'utilisateur peut l'éditer.

_DOC_TYPES = {
    "brief": {
        "label": "Brief stratégique",
        "prompt": (
            "Rédige un BRIEF STRATÉGIQUE court et actionnable (150-220 mots) pour "
            "un solopreneur, structuré en 4 sections courtes précédées d'un titre "
            "en gras MAJUSCULE suivi d'une ligne vide :\n"
            "OBJECTIF (1-2 lignes)\n"
            "PUBLIC CIBLE (1-2 lignes)\n"
            "MESSAGE CLÉ (1-2 lignes)\n"
            "PROCHAINES ÉTAPES (3 bullets '• …')"
        ),
        "title_hint": "Brief",
    },
    "plan": {
        "label": "Plan d'action 30 jours",
        "prompt": (
            "Rédige un PLAN D'ACTION 30 JOURS pour un solopreneur (180-260 mots), "
            "avec 3 phases claires en MAJUSCULES :\n"
            "SEMAINE 1 (fondations)\n"
            "SEMAINES 2-3 (exécution)\n"
            "SEMAINE 4 (mesure & itération)\n"
            "Sous chaque phase : 3-4 actions concrètes en bullets '• verbe + résultat mesurable'."
        ),
        "title_hint": "Plan 30 jours",
    },
    "positioning": {
        "label": "Positionnement",
        "prompt": (
            "Rédige un STATEMENT DE POSITIONNEMENT en 3 blocs courts (120-180 mots) :\n"
            "1) POUR QUI (1 phrase)\n"
            "2) QUI VEUT / A BESOIN DE (1-2 phrases sur la douleur)\n"
            "3) NOTRE OFFRE EST (1 phrase forte) — CE QUI NOUS DISTINGUE : 3 bullets."
        ),
        "title_hint": "Positionnement",
    },
    "swot": {
        "label": "SWOT narratif",
        "prompt": (
            "Rédige un mini-SWOT narratif (150-220 mots) en 4 sections MAJUSCULES :\n"
            "FORCES (2 bullets)\n"
            "FAIBLESSES (2 bullets)\n"
            "OPPORTUNITÉS (2 bullets)\n"
            "MENACES (2 bullets)\n"
            "Termine par UNE PHRASE de recommandation prioritaire."
        ),
        "title_hint": "SWOT",
    },
    "note": {
        "label": "Note libre",
        "prompt": (
            "Rédige une note claire et actionnable (100-180 mots) autour du sujet ci-dessous. "
            "Utilise 1 court paragraphe d'intro puis 3-5 bullets '• …' si pertinent. "
            "Pas de langue de bois."
        ),
        "title_hint": "Note",
    },
}


class GenerateDocRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1500)
    doc_type: Literal["brief", "plan", "positioning", "swot", "note"] = "note"


@router.post("/generate-doc")
async def generate_ai_document(
    payload: GenerateDocRequest,
    user: User = Depends(get_current_user),
):
    """
    Génère un AI Document structuré (brief, plan, positionnement, swot, note libre)
    via Mammouth IA. Renvoie {title, content, doc_type} — le frontend crée une card
    de type 'ai-doc' avec ces valeurs.
    """
    from mammouth_client import chat as mammouth_chat, MammouthError

    spec = _DOC_TYPES.get(payload.doc_type, _DOC_TYPES["note"])

    system = (
        "Tu es un rédacteur business pour solopreneurs. Tu écris en français, "
        "avec un ton direct, concret, sans langue de bois. Tu respectes STRICTEMENT "
        "la structure demandée. Tu commences DIRECTEMENT par le contenu, sans phrase "
        "d'introduction du style 'Voici votre document'."
    )
    user_prompt = (
        f"{spec['prompt']}\n\n"
        f"Sujet / contexte fourni par l'utilisateur :\n\"\"\"\n{payload.prompt.strip()}\n\"\"\"\n\n"
        "Réponds UNIQUEMENT en JSON strict, sans texte autour, au format :\n"
        '{"title": "titre court (3-6 mots)", "content": "le document complet, '
        "avec retours à la ligne '\\n' préservés et bullets '• '\"}"
    )

    try:
        raw = await mammouth_chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=900,
            temperature=0.7,
        )
    except MammouthError as e:
        log.warning("AI Doc gen failed (mammouth): %s", e)
        raise HTTPException(503, f"Génération indisponible : {e}")

    # Nettoyage éventuel ```json … ```
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]

    title, content = None, None
    try:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1:
            parsed = json.loads(cleaned[start:end + 1])
            title = (parsed.get("title") or "").strip()
            content = (parsed.get("content") or "").strip()
    except Exception:
        pass

    # Fallback : si le JSON est cassé, on prend la 1re ligne comme titre
    if not content:
        lines = [l for l in cleaned.splitlines() if l.strip()]
        if lines:
            title = title or lines[0][:80].strip("#* ")
            content = "\n".join(lines[1:] if len(lines) > 1 else lines).strip()
    if not content:
        raise HTTPException(502, "Réponse vide de l'IA.")

    return {
        "title": title or spec["title_hint"],
        "content": content,
        "doc_type": payload.doc_type,
    }


# ─────────── Photos : recherche Unsplash ──────────────────────────────
_CURATED_PHOTOS = [
    {"thumb": "https://images.unsplash.com/photo-1500534623283-312aade485b7?w=200&q=70", "full": "https://images.unsplash.com/photo-1500534623283-312aade485b7?w=800&q=80", "alt": "Sommet"},
    {"thumb": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=200&q=70", "full": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80", "alt": "Plage"},
    {"thumb": "https://images.unsplash.com/photo-1518495973542-4542c06a5843?w=200&q=70", "full": "https://images.unsplash.com/photo-1518495973542-4542c06a5843?w=800&q=80", "alt": "Lumière"},
    {"thumb": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=200&q=70", "full": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=80", "alt": "Forêt"},
]


@router.get("/photos")
async def search_photos(q: str = "inspiration", per_page: int = 12):
    """Recherche des photos libres via Unsplash (UNSPLASH_ACCESS_KEY). Fallback: sélection curée. Public."""
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        return {"source": "curated", "results": _CURATED_PHOTOS}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": q, "per_page": min(per_page, 30), "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {access_key}"},
            )
        if resp.status_code != 200:
            return {"source": "curated", "results": _CURATED_PHOTOS, "error": f"unsplash {resp.status_code}"}
        items = resp.json().get("results", [])
        results = [
            {
                "thumb": it["urls"]["small"],
                "full": it["urls"]["regular"],
                "alt": it.get("alt_description") or q,
                "credit": (it.get("user") or {}).get("name"),
            }
            for it in items
        ]
        return {"source": "unsplash", "results": results or _CURATED_PHOTOS}
    except Exception as e:
        log.warning("Unsplash search failed: %s", e)
        return {"source": "curated", "results": _CURATED_PHOTOS}


# ─────────── #4 Live Cards — agrégateur de données live ────────────────
@router.get("/live-data")
async def get_live_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Agrège les données live des autres modules pour alimenter les cartes
    dynamiques du Vision Board (CA Pilotage, streak/score Bien-être, prospects Croissance)."""
    live = await _get_live_metrics(db, user.id)

    # Bien-être : dernier score + streak de check-ins
    wellness_score = None
    wellness_streak = 0
    try:
        rows = (await db.execute(
            text("SELECT score, DATE(date) AS d FROM wellness_checkins WHERE user_id = :uid ORDER BY date DESC LIMIT 60"),
            {"uid": user.id},
        )).fetchall()
        if rows:
            wellness_score = rows[0][0]
            from datetime import date as _date, timedelta as _td
            days = []
            for r in rows:
                dv = r[1]
                if isinstance(dv, str):
                    dv = dv[:10]
                else:
                    dv = str(dv)[:10]
                days.append(dv)
            seen = sorted(set(days), reverse=True)
            cur = _date.today()
            for dstr in seen:
                try:
                    dd = _date.fromisoformat(dstr)
                except Exception:
                    break
                if dd == cur or dd == cur - _td(days=1):
                    wellness_streak += 1
                    cur = dd - _td(days=1)
                else:
                    break
    except Exception:
        pass

    # Croissance : nb de prospects/leads
    prospects = 0
    try:
        row = (await db.execute(
            text("SELECT COUNT(*) FROM user_leads WHERE user_id = :uid"),
            {"uid": user.id},
        )).fetchone()
        prospects = int(row[0]) if row and row[0] is not None else 0
    except Exception:
        pass

    return {
        "cards": [
            {"key": "ca", "label": "CA du mois", "value": _fmt_eur(live["ca_month_eur"]),
             "sub": f"Objectif {_fmt_eur(live['objective_eur'])}", "progress": live["progress_percent"], "module": "pilotage"},
            {"key": "wellness", "label": "Bien-être", "value": (f"{wellness_score}/100" if wellness_score is not None else "—"),
             "sub": f"{wellness_streak} jour(s) de suite", "progress": wellness_score or 0, "module": "bien-etre"},
            {"key": "prospects", "label": "Prospects", "value": str(prospects),
             "sub": "Pipeline Croissance", "progress": None, "module": "croissance"},
        ],
        "updated_at": _utc_now(),
    }
