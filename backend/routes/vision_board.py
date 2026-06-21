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


async def _get_flipbook_data(db: AsyncSession, user_id: str) -> dict | None:
    r = await db.execute(
        text("SELECT value FROM user_data WHERE user_id = :uid AND `key` = 'vision_board_flipbook' LIMIT 1"),
        {"uid": user_id},
    )
    row = r.fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


async def _save_flipbook_data(db: AsyncSession, user_id: str, data: dict):
    value = json.dumps(data)
    existing = (await db.execute(
        text("SELECT id FROM user_data WHERE user_id = :uid AND `key` = 'vision_board_flipbook'"),
        {"uid": user_id},
    )).fetchone()
    if existing:
        await db.execute(
            text("UPDATE user_data SET value = :v WHERE user_id = :uid AND `key` = 'vision_board_flipbook'"),
            {"v": value, "uid": user_id},
        )
    else:
        await db.execute(
            text("INSERT INTO user_data (id, user_id, `key`, value) VALUES (:id, :uid, 'vision_board_flipbook', :v)"),
            {"id": str(uuid.uuid4()), "uid": user_id, "v": value},
        )
    await db.commit()


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
    """Retourne l'URL et le mot de passe du flipbook existant."""
    data = await _get_flipbook_data(db, user.id)
    if not data:
        return {"flipbook": None}
    return {"flipbook": data}


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

    # 1. Générer HTML
    try:
        html = renderer(payload.data)
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

    # 5. Sauvegarder en DB
    flipbook_data = {
        "url": flipbook_url,
        "password": password,
        "template": payload.template,
        "title": title,
        "created_at": _utc_now(),
        "user_name": name,
    }
    await _save_flipbook_data(db, user.id, flipbook_data)

    return {
        "ok": True,
        "flipbook": flipbook_data,
    }


@router.delete("/flipbook")
async def delete_flipbook(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprime le flipbook en DB (Heyzine ne propose pas de delete API)."""
    await db.execute(
        text("DELETE FROM user_data WHERE user_id = :uid AND `key` = 'vision_board_flipbook'"),
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
    """Ancien endpoint Gemini — conservé pour compatibilité."""
    api_key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(503, "Génération d'image indisponible.")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")
        contents = []
        if payload.base_images:
            for b64 in payload.base_images[:2]:
                contents.append({"inline_data": {"mime_type": "image/png", "data": b64}})
        contents.append(payload.prompt)
        response = model.generate_content(contents)
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                mime = part.inline_data.mime_type or "image/png"
                data = base64.b64encode(part.inline_data.data).decode()
                return {"ok": True, "image": f"data:{mime};base64,{data}", "label": payload.label}
        raise HTTPException(502, "Le modèle n'a pas retourné d'image.")
    except Exception as e:
        raise HTTPException(502, f"Échec: {e}")
