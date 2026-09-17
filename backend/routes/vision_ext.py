"""Vision Board — extensions réelles (Piliers, Score, Vision Book).

Le frontend réel (frontend/src/pages/VisionBoardModule) appelle depuis longtemps
`visionExtApi.getPillars/savePillars/getScore/generateBook`, mais AUCUNE de ces
routes n'existait côté backend — les appels échouaient silencieusement
(`.catch(() => {})`) et l'onglet "Piliers stratégiques" retombait sur des
données 100% statiques (mock.js), sans aucune persistance réelle.

Ce module comble ce trou :
  GET/PUT /api/vision/pillars   → persistance réelle (table user_data, clé vision_pillars)
  GET     /api/vision/score     → score de complétion réel (remplace le mock)
  POST    /api/vision/book/generate → Vision Book multi-pages (PDF, réutilise Heyzine)

Fix #1 (score visible), #2 (piliers avec progression persistée),
#7 (notif de palier franchi), #8 (vue business/personnel séparée),
#10 (export Vision Book complet).
"""
import logging
import os
import base64
import secrets
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User
from routes.vision_board import (
    _get_kv, _save_kv, _utc_now, _html_to_pdf, _upload_to_heyzine, _gen_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vision", tags=["vision-ext"])


@router.get("/memories")
async def get_vision_memories(user: User = Depends(get_current_user)):
    """Souvenirs Vision (photos épinglables). Aucun encore → liste vide (évite le 404)."""
    return {"memories": []}


# ─── Rappels Doux (Notif Settings) ────────────────────────────────
# Toggle pour l'email hebdomadaire du Vision Board avec les 3 prochaines
# actions du Coach Vision. Persisté dans user_data (clé vision_notif_settings).

NOTIF_SETTINGS_KEY = "vision_notif_settings"
DEFAULT_NOTIF_SETTINGS = {
    "weekly_reminder": True,       # Envoi hebdo activé par défaut
    "include_coach_actions": True, # Inclure les 3 prochaines actions du Coach
}


@router.get("/notif-settings")
async def get_notif_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _get_kv(db, user.id, NOTIF_SETTINGS_KEY)
    settings = {**DEFAULT_NOTIF_SETTINGS, **((data or {}).get("settings") or {})}
    return {"settings": settings}


@router.put("/notif-settings")
async def save_notif_settings(
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = payload.get("settings") or {}
    if not isinstance(settings, dict):
        raise HTTPException(400, "settings doit être un objet")
    # Merge avec les defaults pour ne garder que les clés connues
    merged = {**DEFAULT_NOTIF_SETTINGS, **{k: v for k, v in settings.items() if k in DEFAULT_NOTIF_SETTINGS}}
    await _save_kv(db, user.id, NOTIF_SETTINGS_KEY, {"settings": merged, "updated_at": _utc_now()})
    return {"ok": True, "settings": merged}


# ─── Modèles de Départ (Starter Templates) ────────────────────────
# 3-4 canevas prêts à l'emploi que l'on remplit en un tap.
# Contrairement aux templates éditoriaux (STUDIO_TEMPLATES) axés photos,
# ces templates initialisent un canvas structurant complet avec des cartes
# note/objectif/palette pré-remplies. Zéro appel IA → instantané.

STARTER_TEMPLATES = [
    {
        "id": "lancement",
        "label": "Lancement",
        "emoji": "🚀",
        "description": "Poser les fondations d'un nouveau projet.",
        "cards": [
            {"type": "note", "w": 240, "x": 60, "y": 60, "color": "#0a1f4e",
             "title": {"fr": "Mon Pourquoi", "en": "My Why"},
             "body": {"fr": "En une phrase, la raison profonde qui me pousse à lancer.", "en": "In one sentence, the deep reason behind this launch."}},
            {"type": "objective", "w": 260, "x": 340, "y": 60, "color": "#C9A449",
             "title": {"fr": "Offre signature", "en": "Signature offer"},
             "checklist": [
                {"text": {"fr": "Cible précise (1 persona)", "en": "Precise target (1 persona)"}, "done": False},
                {"text": {"fr": "Promesse en 1 phrase", "en": "One-sentence promise"}, "done": False},
                {"text": {"fr": "Prix + livrables", "en": "Price + deliverables"}, "done": False},
             ], "progress": 0},
            {"type": "objective", "w": 260, "x": 60, "y": 320, "color": "#3f7d63",
             "title": {"fr": "3 premiers clients", "en": "First 3 clients"},
             "checklist": [
                {"text": {"fr": "Lister 10 prospects tièdes", "en": "List 10 warm leads"}, "done": False},
                {"text": {"fr": "Message d'approche personnalisé", "en": "Personalized outreach"}, "done": False},
                {"text": {"fr": "Signer 3 clients pilotes", "en": "Sign 3 pilot clients"}, "done": False},
             ], "progress": 0},
            {"type": "note", "w": 240, "x": 340, "y": 340, "color": "",
             "title": {"fr": "Deadline lancement", "en": "Launch deadline"},
             "body": {"fr": "J-30 : offre validée · J-15 : page prête · J-0 : ouverture.", "en": "D-30: offer OK · D-15: page ready · D-0: launch."}},
            {"type": "color", "w": 240, "x": 60, "y": 560, "colors": ["#0a1f4e", "#C9A449", "#3f7d63", "#F6F2EA"],
             "title": {"fr": "Palette de marque", "en": "Brand palette"}},
        ],
    },
    {
        "id": "croissance",
        "label": "Croissance",
        "emoji": "📈",
        "description": "Passer au niveau supérieur : scaler ce qui marche.",
        "cards": [
            {"type": "note", "w": 240, "x": 60, "y": 60, "color": "#0a1f4e",
             "title": {"fr": "Ambition 12 mois", "en": "12-month ambition"},
             "body": {"fr": "CA cible + nombre de clients + qualité de vie.", "en": "Target revenue + client count + quality of life."}},
            {"type": "objective", "w": 260, "x": 340, "y": 60, "color": "#4a6a9e",
             "title": {"fr": "Doubler les revenus", "en": "Double revenue"},
             "checklist": [
                {"text": {"fr": "Augmenter les prix de 20%", "en": "Raise prices 20%"}, "done": False},
                {"text": {"fr": "Ajouter 1 offre premium", "en": "Add premium offer"}, "done": False},
                {"text": {"fr": "Automatiser 1 canal d'acquisition", "en": "Automate 1 acquisition channel"}, "done": False},
             ], "progress": 0},
            {"type": "objective", "w": 260, "x": 60, "y": 320, "color": "#C9A449",
             "title": {"fr": "Système de contenu", "en": "Content system"},
             "checklist": [
                {"text": {"fr": "2 publications / semaine", "en": "2 posts / week"}, "done": False},
                {"text": {"fr": "1 newsletter mensuelle", "en": "1 monthly newsletter"}, "done": False},
                {"text": {"fr": "Atteindre 5K abonnés", "en": "Reach 5K followers"}, "done": False},
             ], "progress": 0},
            {"type": "note", "w": 240, "x": 340, "y": 340, "color": "",
             "title": {"fr": "Ce que je délègue", "en": "What I delegate"},
             "body": {"fr": "3 tâches à sortir de ma to-do d'ici 90 jours.", "en": "3 tasks to remove from my to-do within 90 days."}},
            {"type": "note", "w": 240, "x": 60, "y": 560, "color": "#3f7d63",
             "title": {"fr": "KPI à surveiller", "en": "Key KPIs"},
             "body": {"fr": "CA mensuel · taux de conversion · NPS clients.", "en": "Monthly revenue · conversion rate · client NPS."}},
        ],
    },
    {
        "id": "equilibre",
        "label": "Équilibre",
        "emoji": "🌿",
        "description": "Retrouver de l'énergie sans casser la dynamique.",
        "cards": [
            {"type": "note", "w": 240, "x": 60, "y": 60, "color": "#3f7d63",
             "title": {"fr": "Non-négociables", "en": "Non-negotiables"},
             "body": {"fr": "Les 3 choses que je protège même en semaine chargée.", "en": "The 3 things I protect even on busy weeks."}},
            {"type": "objective", "w": 260, "x": 340, "y": 60, "color": "#3f7d63",
             "title": {"fr": "Rituel matin", "en": "Morning ritual"},
             "checklist": [
                {"text": {"fr": "10 min sans écran", "en": "10 min no-screen"}, "done": False},
                {"text": {"fr": "Bouger 20 min", "en": "Move 20 min"}, "done": False},
                {"text": {"fr": "Écrire 1 intention", "en": "Write 1 intention"}, "done": False},
             ], "progress": 0},
            {"type": "objective", "w": 260, "x": 60, "y": 320, "color": "#8a5a83",
             "title": {"fr": "Coupures nettes", "en": "Clean cutoffs"},
             "checklist": [
                {"text": {"fr": "Fin de journée à 18h", "en": "Stop work at 6pm"}, "done": False},
                {"text": {"fr": "Pas d'écran après 21h", "en": "No screens after 9pm"}, "done": False},
                {"text": {"fr": "1 vraie journée off / semaine", "en": "1 full day off / week"}, "done": False},
             ], "progress": 0},
            {"type": "note", "w": 240, "x": 340, "y": 340, "color": "",
             "title": {"fr": "Ce qui me nourrit", "en": "What fuels me"},
             "body": {"fr": "3 activités qui me rechargent (hors travail).", "en": "3 activities that recharge me (outside work)."}},
            {"type": "color", "w": 240, "x": 60, "y": 560, "colors": ["#3f7d63", "#d8c9a3", "#8a5a83", "#F6F2EA"],
             "title": {"fr": "Ambiance douce", "en": "Soft mood"}},
        ],
    },
    {
        "id": "rayonnement",
        "label": "Rayonnement",
        "emoji": "✨",
        "description": "Devenir visible et reconnu·e dans son domaine.",
        "cards": [
            {"type": "note", "w": 240, "x": 60, "y": 60, "color": "#C9A449",
             "title": {"fr": "Ma promesse", "en": "My promise"},
             "body": {"fr": "Ce que je veux qu'on retienne quand on parle de moi.", "en": "What I want people to remember about me."}},
            {"type": "objective", "w": 260, "x": 340, "y": 60, "color": "#C9A449",
             "title": {"fr": "Autorité éditoriale", "en": "Editorial authority"},
             "checklist": [
                {"text": {"fr": "Choisir 1 sujet phare", "en": "Pick 1 flagship topic"}, "done": False},
                {"text": {"fr": "12 publications piliers", "en": "12 pillar posts"}, "done": False},
                {"text": {"fr": "1 prise de parole publique", "en": "1 public talk"}, "done": False},
             ], "progress": 0},
            {"type": "objective", "w": 260, "x": 60, "y": 320, "color": "#c26b4a",
             "title": {"fr": "Communauté", "en": "Community"},
             "checklist": [
                {"text": {"fr": "5K abonnés qualifiés", "en": "5K qualified followers"}, "done": False},
                {"text": {"fr": "1 rencontre / mois", "en": "1 meetup / month"}, "done": False},
                {"text": {"fr": "10 recommandations", "en": "10 testimonials"}, "done": False},
             ], "progress": 0},
            {"type": "note", "w": 240, "x": 340, "y": 340, "color": "",
             "title": {"fr": "Mes 3 signatures", "en": "My 3 signatures"},
             "body": {"fr": "Ce qui rend mon style reconnaissable en 1 coup d'œil.", "en": "What makes my style recognizable at a glance."}},
            {"type": "color", "w": 240, "x": 60, "y": 560, "colors": ["#C9A449", "#0a1f4e", "#c26b4a", "#F6F2EA"],
             "title": {"fr": "Signature couleurs", "en": "Signature colors"}},
        ],
    },
]


@router.get("/starter-templates")
async def get_starter_templates(user: User = Depends(get_current_user)):
    """Renvoie la liste des modèles de départ (canvas prêts à l'emploi)."""
    return {"templates": STARTER_TEMPLATES}






DEFAULT_PILLARS = [
    {"id": "p1", "icon": "TrendingUp", "color": "#4a6a9e", "category": "business",
     "title": "Croissance", "description": "Développer un business rentable et durable.",
     "pinned_dashboard": True,
     "objectives": [
        {"text": "Signer 3 clients récurrents", "done": False},
        {"text": "Lancer une offre signature", "done": False},
        {"text": "Atteindre 10K€/mois", "done": False},
     ]},
    {"id": "p2", "icon": "HeartPulse", "color": "#5e8a5a", "category": "personnel",
     "title": "Bien-être", "description": "Préserver mon énergie et mon équilibre.",
     "pinned_dashboard": False,
     "objectives": [
        {"text": "Rituel matinal quotidien", "done": False},
        {"text": "Coupure écran à 21h", "done": False},
     ]},
    {"id": "p3", "icon": "Globe", "color": "#C9A449", "category": "business",
     "title": "Rayonnement", "description": "Devenir une référence dans mon domaine.",
     "pinned_dashboard": False,
     "objectives": [
        {"text": "Publier 2 contenus/semaine", "done": False},
        {"text": "Atteindre 5K abonnés", "done": False},
        {"text": "Prise de parole publique", "done": False},
     ]},
    {"id": "p4", "icon": "Wallet", "color": "#8b6fbf", "category": "personnel",
     "title": "Liberté financière", "description": "Sécuriser mes revenus et investir.",
     "pinned_dashboard": False,
     "objectives": [
        {"text": "3 mois de trésorerie d'avance", "done": False},
        {"text": "Automatiser 1 revenu passif", "done": False},
     ]},
]

PILLARS_KEY = "vision_pillars"
SCORE_SNAPSHOT_KEY = "vision_score_snapshot"


def _compute_progress(pillar: dict) -> int:
    objs = pillar.get("objectives") or []
    if not objs:
        return 0
    done = sum(1 for o in objs if o.get("done"))
    return round(done / len(objs) * 100)


def _compute_global_score(pillars: list) -> int:
    """Score de complétion réel — fix #1 : plus de pourcentage statique.
    Moyenne pondérée de la progression de chaque pilier."""
    if not pillars:
        return 0
    return round(sum(_compute_progress(p) for p in pillars) / len(pillars))


class ObjectiveIn(BaseModel):
    text: str
    done: bool = False


class PillarIn(BaseModel):
    id: str
    icon: str = "TrendingUp"
    color: str = "#4a6a9e"
    category: Literal["business", "personnel"] = "business"
    title: str
    description: str = ""
    pinned_dashboard: bool = False
    objectives: list[ObjectiveIn] = Field(default_factory=list)


class PillarsIn(BaseModel):
    pillars: list[PillarIn]


@router.get("/pillars")
async def get_pillars(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    import copy
    data = await _get_kv(db, user.id, PILLARS_KEY)
    pillars = data.get("pillars") if data else None
    if not pillars:
        pillars = copy.deepcopy(DEFAULT_PILLARS)
    # recalcule toujours la progression à partir des objectifs réels
    for p in pillars:
        p["progress"] = _compute_progress(p)
    return pillars


@router.put("/pillars")
async def save_pillars(
    payload: PillarsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pillars = [p.dict() for p in payload.pillars]
    for p in pillars:
        p["progress"] = _compute_progress(p)
    await _save_kv(db, user.id, PILLARS_KEY, {"pillars": pillars, "updated_at": _utc_now()})

    # Fix #7 — notification de palier franchi (50/70/90%) sur le score global
    new_score = _compute_global_score(pillars)
    snapshot = await _get_kv(db, user.id, SCORE_SNAPSHOT_KEY) or {}
    old_score = snapshot.get("score", 0)
    milestone = None
    for threshold in (50, 70, 90, 100):
        if old_score < threshold <= new_score:
            milestone = threshold
    await _save_kv(db, user.id, SCORE_SNAPSHOT_KEY, {"score": new_score, "updated_at": _utc_now()})

    return {"ok": True, "pillars": pillars, "score": new_score, "milestone_reached": milestone}


@router.get("/score")
async def get_vision_score(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Score de complétion réel affiché en permanence (fix #1) — plus un mock statique."""
    data = await _get_kv(db, user.id, PILLARS_KEY)
    pillars = (data or {}).get("pillars") or DEFAULT_PILLARS
    score = _compute_global_score(pillars)
    business = [p for p in pillars if p.get("category") == "business"]
    personnel = [p for p in pillars if p.get("category") == "personnel"]
    return {
        "global": score,
        "business_score": _compute_global_score(business) if business else None,
        "personnel_score": _compute_global_score(personnel) if personnel else None,
        "pillars_count": len(pillars),
    }


@router.post("/book/generate")
async def generate_vision_book(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Vision Book complet (fix #10) — plusieurs pages : mission, piliers, roadmap.
    Réutilise le moteur PDF/Heyzine déjà en place pour le flipbook simple."""
    pillars_data = await _get_kv(db, user.id, PILLARS_KEY)
    pillars = (pillars_data or {}).get("pillars") or DEFAULT_PILLARS
    score = _compute_global_score(pillars)
    name = user.name or "Vision"

    def pillar_page(p):
        objs = "".join(
            f"<li style='margin-bottom:8px;{'text-decoration:line-through;opacity:.5;' if o.get('done') else ''}'>{o.get('text','')}</li>"
            for o in (p.get("objectives") or [])
        )
        return f"""
        <section style="page-break-after:always;padding:80px 70px;min-height:900px;background:#FAF8F3;">
          <div style="width:56px;height:6px;background:{p.get('color','#1A3A6E')};border-radius:99px;margin-bottom:26px;"></div>
          <h2 style="font-family:'Playfair Display',serif;font-size:34px;color:#1A1408;margin:0 0 6px;">{p.get('title','')}</h2>
          <p style="font-family:sans-serif;font-size:15px;color:#6b6558;max-width:480px;">{p.get('description','')}</p>
          <div style="margin-top:10px;font-size:13px;color:{p.get('color','#1A3A6E')};font-weight:700;">{_compute_progress(p)}% complété</div>
          <ul style="font-family:sans-serif;font-size:16px;color:#1a1814;margin-top:30px;padding-left:20px;">{objs}</ul>
        </section>"""

    html = f"""
    <html><body style="margin:0;font-family:sans-serif;">
      <section style="page-break-after:always;height:900px;background:#0B1F3A;color:#fff;
        display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:60px;">
        <span style="text-transform:uppercase;letter-spacing:0.2em;font-size:12px;color:#D6A85F;">Vision Book</span>
        <h1 style="font-family:'Playfair Display',serif;font-size:48px;margin:18px 0 8px;">{name}</h1>
        <p style="color:rgba(255,255,255,0.7);font-size:15px;">La feuille de route de ma vision</p>
        <div style="margin-top:40px;font-size:14px;color:#D6A85F;">Score global : {score}%</div>
      </section>
      {''.join(pillar_page(p) for p in pillars)}
    </body></html>
    """
    pdf_bytes = await _html_to_pdf(html)
    password = _gen_password(8)
    title = f"Vision Book · {name}"
    try:
        url = await _upload_to_heyzine(pdf_bytes, title, password)
    except Exception as e:
        logger.exception(f"[VISION_BOOK] Heyzine upload failed: {e}")
        return {"ok": False, "error": "Échec de la génération du Vision Book. Réessayez."}

    book_data = {"flipbook_url": url, "password": password, "created_at": _utc_now(), "score": score}
    await _save_kv(db, user.id, "vision_book_last", book_data)
    return {"ok": True, "flipbook_url": url, "pdf_url": url, **book_data}


# ─────────── Vision Canvas — persistance réelle des cartes (fix #1, #2) ───
# Corrige : GET/PUT /api/vision/board et POST /api/vision/card n'existaient
# nulle part côté backend — le Vision Canvas (1er onglet, ouvert par défaut)
# ne sauvegardait jamais rien, malgré un indicateur "Enregistré (SQL)" qui
# affichait un succès permanent.

BOARD_KEY = "vision_canvas_board"


@router.get("/board")
async def get_board(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await _get_kv(db, user.id, BOARD_KEY)
    return {"cards": (data or {}).get("cards", [])}


@router.put("/board")
async def save_board(
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cards = payload.get("cards", [])
    if not isinstance(cards, list):
        raise HTTPException(400, "cards doit être une liste")
    await _save_kv(db, user.id, BOARD_KEY, {"cards": cards, "updated_at": _utc_now()})
    return {"ok": True, "count": len(cards)}


@router.post("/card")
async def add_card(
    card: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _get_kv(db, user.id, BOARD_KEY) or {"cards": []}
    cards = data.get("cards", [])
    cards.append(card)
    await _save_kv(db, user.id, BOARD_KEY, {"cards": cards, "updated_at": _utc_now()})
    return {"ok": True, "card": card}


# ─────────── Photo de fond — upload réel vers WordPress media (fix #4) ────
# Même pattern que branding.py::branding_upload_logo — réutilise WP media
# comme stockage, pas de nouveau système de fichiers à maintenir.

@router.post("/photo")
async def upload_background_photo(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Le fichier doit être une image")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Image trop volumineuse (>5 Mo)")

    wp_base = os.environ.get("WP_BASE_URL", "").rstrip("/")
    wp_user = os.environ.get("WP_USERNAME", "")
    wp_pass = os.environ.get("WP_APP_PASSWORD", "")
    if not (wp_base and wp_user and wp_pass):
        raise HTTPException(500, "Hébergement média non configuré (WordPress).")

    auth = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{wp_base}/wp-json/wp/v2/media",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Disposition": f'attachment; filename="{file.filename or "vision-bg.jpg"}"',
                    "Content-Type": file.content_type,
                },
                content=content,
                timeout=30.0,
            )
            r.raise_for_status()
            url = r.json().get("source_url")
        except httpx.HTTPError as e:
            logger.error("Vision photo upload failed: %s", e)
            raise HTTPException(502, "Échec de l'upload de l'image.")

    return {"url": url}


# ─────────── Import depuis un lien public Canva (fix #3) ──────────────────
# Remplace l'import "simulé" côté frontend (un setTimeout qui prétendait
# réussir sans jamais vérifier le lien) par une vraie récupération de
# l'image via les balises Open Graph du lien de partage public Canva.

class CanvaImportRequest(BaseModel):
    url: str


@router.post("/canva-import")
async def import_canva_link(
    payload: CanvaImportRequest,
    user: User = Depends(get_current_user),
):
    url = (payload.url or "").strip()
    if "canva.com" not in url:
        raise HTTPException(400, "Ce n'est pas un lien Canva valide.")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            raise HTTPException(502, "Impossible d'accéder à ce lien Canva.")
        html = resp.text
        import re as _re
        m = _re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)
        if not m:
            m = _re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html)
        if not m:
            raise HTTPException(422, "Aucune image trouvée sur ce lien — vérifiez qu'il est bien public.")
        return {"url": m.group(1)}
    except httpx.HTTPError:
        raise HTTPException(502, "Échec de connexion à Canva.")


# ─────────── Génération d'un board complet depuis 1 prompt IA (quick-win #1) ──
# storyflow.so génère un board structuré à partir d'une simple description.
# Jusqu'ici l'IA du canvas n'ajoutait qu'1 seule note brute — ceci génère
# plusieurs cartes reliées (vision + piliers + actions) en un seul appel.

class GenerateBoardRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=800)


async def _claude_complete_json(system: str, user_prompt: str, max_tokens: int = 1200) -> dict:
    from mammouth_client import chat as mammouth_chat, MammouthError
    try:
        raw = await mammouth_chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        if raw.startswith("```"):
            raw = raw.strip("`").split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        import json as _json
        start, end = raw.find("{"), raw.rfind("}")
        return _json.loads(raw[start:end + 1]) if start != -1 else {}
    except (MammouthError, Exception) as e:
        logger.exception("Génération board IA (Mammouth) échouée: %s", e)
        return {}


@router.post("/generate-from-prompt")
async def generate_board_from_prompt(
    payload: GenerateBoardRequest,
    user: User = Depends(get_current_user),
):
    """
    Décrit ton projet en une phrase -> reçoit un board structuré (5-8 cartes :
    1 vision centrale, 2-3 piliers/objectifs, 2-3 prochaines actions).
    """
    system = (
        "Tu es un assistant qui structure la vision d'un solo-entrepreneur en cartes "
        "courtes pour un vision board. Réponds UNIQUEMENT en JSON strict, en français, "
        "sans aucun texte autour, sans markdown."
    )
    prompt = (
        f"Description du projet : {payload.prompt}\n\n"
        "Génère un board avec cette structure JSON exacte :\n"
        '{"vision": "1 phrase qui résume la vision, percutante", '
        '"pillars": ["pilier 1 (3-5 mots)", "pilier 2", "pilier 3"], '
        '"actions": ["prochaine action concrète 1", "action 2", "action 3"]}\n'
        "Chaque pilier et action doit être court (max 8 mots), concret, actionnable."
    )
    data = await _claude_complete_json(system, prompt, max_tokens=700)

    if not data or not data.get("vision"):
        raise HTTPException(502, "Génération impossible pour l'instant — réessayez dans un instant.")

    # Positionnement en éventail autour du centre du board (BOARD_CENTER = 660,420)
    cx, cy = 660, 420
    cards = [{
        "type": "note", "x": cx - 260, "y": cy - 160, "w": 260, "h": 130,
        "color": "#C9A449", "title": {"fr": "Vision", "en": "Vision"},
        "body": {"fr": data["vision"], "en": data["vision"]},
    }]
    pillars = (data.get("pillars") or [])[:3]
    for i, p in enumerate(pillars):
        cards.append({
            "type": "note", "x": cx + 60 + i * 230, "y": cy - 220, "w": 210, "h": 110,
            "color": "#4a6a9e", "title": {"fr": "Pilier", "en": "Pillar"},
            "body": {"fr": p, "en": p},
        })
    actions = (data.get("actions") or [])[:3]
    for i, a in enumerate(actions):
        cards.append({
            "type": "checklist", "x": cx - 260 + i * 230, "y": cy + 60, "w": 210, "h": 110,
            "color": "#5e8a5a", "title": {"fr": "Action", "en": "Action"},
            "body": {"fr": a, "en": a},
        })

    return {"cards": cards, "source": "claude-sonnet-4-5"}


class CoachRequest(BaseModel):
    cards: Optional[list] = None


@router.post("/coach")
async def coach_vision(
    payload: CoachRequest = CoachRequest(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Coach Vision : analyse le canvas + les piliers et renvoie 3 prochaines actions concrètes."""
    def _txt(v):
        if isinstance(v, dict):
            return v.get("fr") or v.get("en") or ""
        return v or ""

    cards = payload.cards
    if cards is None:
        data = await _get_kv(db, user.id, BOARD_KEY)
        cards = (data or {}).get("cards", [])

    lines = []
    for c in (cards or [])[:40]:
        t, b = _txt(c.get("title")), _txt(c.get("body"))
        label = (t + (" — " + b if b else "")).strip()
        if label:
            lines.append(f"- [{c.get('type', 'note')}] {label[:160]}")

    pdata = await _get_kv(db, user.id, PILLARS_KEY)
    pillars = (pdata or {}).get("pillars") if pdata else None
    pillar_lines = []
    for p in (pillars or []):
        pillar_lines.append(f"- {_txt(p.get('title'))} ({p.get('progress', 0)}%)")

    if not lines and not pillar_lines:
        return {
            "empty": True,
            "summary": "Ton canvas est encore vide.",
            "actions": [
                {"title": "Décris ta vision", "why": "Utilise Ask AI pour poser ta vision en une phrase."},
                {"title": "Ajoute 3 piliers", "why": "Structure ta vision en 3 axes clairs."},
                {"title": "Fixe une première action", "why": "Choisis un objectif réalisable cette semaine."},
            ],
        }

    system = (
        "Tu es un coach stratégique pour solo-entrepreneurs. À partir des cartes d'un vision board "
        "et des piliers, tu proposes les 3 PROCHAINES actions concrètes et priorisées. "
        "Réponds UNIQUEMENT en JSON strict, en français, sans markdown ni texte autour."
    )
    prompt = (
        "Cartes du canvas :\n" + ("\n".join(lines) or "(aucune)") +
        "\n\nPiliers :\n" + ("\n".join(pillar_lines) or "(aucun)") +
        "\n\nRenvoie ce JSON exact :\n"
        '{"summary": "1 phrase de synthèse bienveillante et lucide sur l\'état de la vision", '
        '"actions": [{"title": "action concrète (max 8 mots)", "why": "pourquoi maintenant (1 phrase)"}, '
        '{"title": "...", "why": "..."}, {"title": "...", "why": "..."}]}\n'
        "Les 3 actions doivent être concrètes, réalisables et tirées directement du contenu ci-dessus."
    )
    result = await _claude_complete_json(system, prompt, max_tokens=600)
    actions = (result.get("actions") or [])[:3]
    if not actions:
        raise HTTPException(502, "Le coach est indisponible pour l'instant — réessayez dans un instant.")
    return {
        "empty": False,
        "summary": result.get("summary") or "Voici tes prochaines actions.",
        "actions": actions,
    }


SWOT_KEY = "vision_swot_analysis"


@router.get("/swot")
async def get_swot(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Dernière analyse SWOT générée (persistée), ou {} si aucune n'existe encore —
    le frontend traite l'absence de 'strengths'/'summary' comme 'pas d'analyse'."""
    data = await _get_kv(db, user.id, SWOT_KEY)
    return (data or {}).get("swot") or {}


@router.post("/swot/generate")
async def generate_swot(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère une vraie analyse SWOT par IA à partir des données réelles de
    l'utilisateur (piliers stratégiques + canvas vision), pas un modèle
    générique codé en dur. Même mécanisme que /coach (Mammouth/Claude,
    JSON strict) — endpoint manquant côté serveur jusqu'ici alors que le
    frontend l'appelait déjà (getSwot/generateSwot -> 404)."""
    def _txt(v):
        if isinstance(v, dict):
            return v.get("fr") or v.get("en") or ""
        return v or ""

    pdata = await _get_kv(db, user.id, PILLARS_KEY)
    pillars = (pdata or {}).get("pillars") or []
    pillar_lines = [f"- {_txt(p.get('title'))} ({p.get('progress', 0)}% avancé) : {_txt(p.get('description'))}" for p in pillars]

    bdata = await _get_kv(db, user.id, BOARD_KEY)
    cards = (bdata or {}).get("cards", [])
    card_lines = []
    for c in (cards or [])[:40]:
        t, b = _txt(c.get("title")), _txt(c.get("body"))
        label = (t + (" — " + b if b else "")).strip()
        if label:
            card_lines.append(f"- [{c.get('type', 'note')}] {label[:160]}")

    if not pillar_lines and not card_lines:
        raise HTTPException(400, "Ajoutez au moins un pilier ou une carte à votre vision avant de générer une analyse — l'IA ne peut pas inventer votre contexte.")

    score = _compute_global_score(pillars) if pillars else None

    system = (
        "Tu es un consultant en stratégie qui réalise une analyse SWOT lucide et bienveillante "
        "pour un solo-entrepreneur, UNIQUEMENT à partir des piliers et cartes de vision fournis — "
        "tu n'inventes jamais d'élément absent de ces données. Réponds UNIQUEMENT en JSON strict, "
        "en français, sans markdown ni texte autour."
    )
    prompt = (
        "Piliers stratégiques :\n" + ("\n".join(pillar_lines) or "(aucun)") +
        "\n\nCartes du vision board :\n" + ("\n".join(card_lines) or "(aucune)") +
        (f"\n\nScore de complétion actuel des piliers : {score}/100" if score is not None else "") +
        "\n\nRenvoie ce JSON exact :\n"
        '{"strengths": ["force 1 tirée des données ci-dessus", "..."], '
        '"weaknesses": ["faiblesse 1", "..."], '
        '"opportunities": ["opportunité 1", "..."], '
        '"threats": ["menace ou risque 1", "..."], '
        '"verdict": "go|pivot|abandon", '
        '"summary": "1-2 phrases de synthèse lucide sur l\'état actuel de la vision", '
        '"next_actions": ["action concrète 1 (max 10 mots)", "action 2", "action 3"]}\n'
        "2 à 4 éléments par catégorie (forces/faiblesses/opportunités/menaces), toujours ancrés dans "
        "les données fournies. 'verdict' : 'go' si la vision est solide et actionnable, 'pivot' si des "
        "ajustements sont nécessaires, 'abandon' seulement si les signaux sont vraiment préoccupants."
    )
    result = await _claude_complete_json(system, prompt, max_tokens=900)
    if not result or not result.get("strengths"):
        raise HTTPException(502, "L'analyse IA est indisponible pour le moment — réessayez dans un instant.")

    swot = {
        "strengths": result.get("strengths") or [],
        "weaknesses": result.get("weaknesses") or [],
        "opportunities": result.get("opportunities") or [],
        "threats": result.get("threats") or [],
        "verdict": result.get("verdict") if result.get("verdict") in ("go", "pivot", "abandon") else None,
        "summary": result.get("summary") or "",
        "next_actions": (result.get("next_actions") or [])[:5],
        "score": score,
        "generated_at": _utc_now(),
    }
    await _save_kv(db, user.id, SWOT_KEY, {"swot": swot})
    return {"ok": True, "swot": swot}


# ─────────── Partage du board (fix #5) ─────────────────────────────────────

@router.post("/share")
async def share_board(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    existing = await _get_kv(db, user.id, "vision_share_token")
    token = (existing or {}).get("token") or secrets.token_urlsafe(12)
    await _save_kv(db, user.id, "vision_share_token", {"token": token, "created_at": _utc_now()})
    base = os.environ.get("PUBLIC_APP_URL", "https://app.zayado.net").rstrip("/")
    return {"share_url": f"{base}/vision-board/public/{token}"}
