"""
Vision Board — version SANS MongoDB (persistance fichier JSON local).
Fournit exactement les endpoints consommés par VisionBoardPage.jsx :
  /vision/board, /vision/info, /vision/copilot-data, /vision/analyse,
  /vision/visionbook (+ /generate), /canva/status, /canva/auth/start
L'app utilise SQL (SQLAlchemy) ; le Vision Board (mono-user "demo") n'a pas
besoin d'une table dédiée — un simple store JSON suffit et évite toute dépendance Mongo.
"""
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from vision_seed import FEUILLE_DE_ROUTE_DEFAULT, TEMPLATE_SEEDS

_STORE_PATH = os.path.join(os.path.dirname(__file__), "vision_store.json")


# ── Persistance fichier JSON ────────────────────────────────────────────────
def _read_all() -> Dict[str, Any]:
    try:
        with open(_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_all(data: Dict[str, Any]) -> None:
    tmp = _STORE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, _STORE_PATH)


def DEFAULT_VISION_INFO() -> Dict[str, Any]:
    return {
        "mission": "Aider les entrepreneurs francophones à clarifier leur vision et passer à l'action grâce à un compagnon IA bienveillant.",
        "pourquoi": "Parce que personne ne devrait être seul à construire son avenir. Une vision claire change une vie. Un entrepreneur aligné peut changer le monde.",
        "vision_1an": "MyExtension AI accompagne 5 000 entrepreneurs actifs, génère 1,2 M€ de CA récurrent et inspire une communauté engagée.",
        "vision_3ans": "Devenir LA référence francophone de l'accompagnement entrepreneurial augmenté par l'IA — 25 000 utilisateurs, 8 pays, marge nette 40%.",
        "vision_10ans": "Créer un écosystème mondial qui aura permis à 1 million d'entrepreneurs de vivre alignés avec leur vision, leur impact et leur bien-être.",
        "valeurs": ["Alignement", "Liberté", "Excellence", "Impact", "Intégrité"],
        "objectifs": {
            "ca_cible": 1200000, "nb_clients": 25000, "heures_libres": 20,
            "taille_equipe": 12, "sante": 9, "spiritualite": 8,
            "marge_op_pct": 24, "ikigai_score": 92,
            "phase": {"label": "Lancement", "mois": 4, "total": 12},
            "priorite_1": "Finaliser la landing /vision-board avant fin du trimestre",
            "date_cible": "2026-12-31",
        },
        "piliers": [
            {"id": "business", "label": "Business", "icon": "briefcase", "text": "Développer MyExtension AI", "progress": 68},
            {"id": "finances", "label": "Finances", "icon": "trending-up", "text": "1,2 M€ de CA récurrent", "progress": 42},
            {"id": "sante", "label": "Santé", "icon": "heart-pulse", "text": "Sport 3x / semaine, énergie 9/10", "progress": 75},
            {"id": "famille", "label": "Famille", "icon": "users", "text": "Plus de temps libre & présence", "progress": 60},
            {"id": "sens", "label": "Sens", "icon": "compass", "text": "Routine d'alignement quotidienne", "progress": 70},
            {"id": "impact", "label": "Impact", "icon": "globe", "text": "Aider 1 000 entrepreneurs", "progress": 38},
        ],
    }


def compute_analysis(info: Dict[str, Any]) -> Dict[str, Any]:
    obj = info.get("objectifs", {}) or {}
    sante = int(obj.get("sante", 7))
    spi = int(obj.get("spiritualite", 7))
    nb_valeurs = len(info.get("valeurs") or [])
    nb_visions = sum(1 for k in ("vision_1an", "vision_3ans", "vision_10ans") if info.get(k))
    score = min(95, 50 + (sante + spi) * 2 + nb_valeurs * 3 + nb_visions * 4)
    verdict = "Continue" if score >= 70 else ("À recentrer" if score >= 55 else "À clarifier")
    scores = {
        "clarte": min(98, 60 + nb_visions * 9 + nb_valeurs * 2),
        "alignement": min(96, score),
        "ambition": min(98, 70 + (1 if obj.get("ca_cible", 0) >= 1000000 else 0) * 20 + nb_visions * 3),
        "faisabilite": min(92, 55 + int(obj.get("ikigai_score", 80)) // 4),
        "equilibre": min(95, 50 + (sante + spi) * 2 + len(info.get("piliers") or []) * 3),
    }
    scores["global"] = round(sum(scores.values()) / len(scores))
    return {
        "score_alignement": score,
        "scores": scores,
        "verdict": verdict,
        "message": (
            "Votre vision est claire et cohérente. Continuez à travailler la délégation pour franchir le palier des 80%."
            if score >= 70 else
            "Votre vision gagnera en force en remplissant davantage vos objectifs et valeurs."
        ),
        "coherence": (
            f"Votre vision est ambitieuse et cohérente avec vos {nb_valeurs} valeurs principales. "
            f"Les objectifs sont réalistes au rythme actuel."
        ),
        "swot": {
            "forces": ["Vision claire et incarnée", "Expertise tech & IA",
                       "Communauté engagée", "Méthode 70/30 différenciante"],
            "faiblesses": ["Tendance à la dispersion", "Perfectionnisme bloquant", "Délégation perfectible"],
            "opportunites": ["Marché francophone en croissance",
                             "Avènement de l'IA grand public",
                             "Partenariats institutionnels"],
            "menaces": ["Concurrence US accélère", "Dépendance API tierces", "Saturation contenu IA"],
        },
        "opportunites_business": [
            "Lancer un parcours premium « Vision 90 jours » à 990€",
            "Partenariat distribution avec 2 réseaux d'incubateurs",
            "API publique Vision Board pour coachs partenaires",
        ],
        "risques": [
            "Si la délégation n'avance pas avant Q2, plafond de croissance personnel atteint.",
            "Surcharge cognitive — protéger les blocs de récupération.",
        ],
        "conseils": [
            "Bloquez 2 demi-journées focus par semaine pour finaliser la landing /vision-board.",
            "Identifiez 3 tâches à déléguer dès cette semaine pour libérer 6h de bande passante.",
            "Publiez la méthode 70/30 sous forme d'article de référence pour ancrer votre positionnement.",
        ],
        "mocked": True,
    }


def _get_or_create(user_id: str = "demo") -> dict:
    store = _read_all()
    doc = store.get(user_id)
    if doc:
        return doc
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": FEUILLE_DE_ROUTE_DEFAULT["title"],
        "template": FEUILLE_DE_ROUTE_DEFAULT["template"],
        "theme": FEUILLE_DE_ROUTE_DEFAULT["theme"],
        "cards": FEUILLE_DE_ROUTE_DEFAULT["cards"],
        "vision_info": DEFAULT_VISION_INFO(),
        "visionbook": {"flipbook_url": None, "pdf_url": None, "generated_at": None},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    store[user_id] = doc
    _write_all(store)
    return doc


def _save(user_id: str, doc: dict) -> None:
    store = _read_all()
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    store[user_id] = doc
    _write_all(store)


class VisionBoardUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: Optional[str] = None
    template: Optional[str] = None
    theme: Optional[Dict[str, Any]] = None
    cards: Optional[List[Dict[str, Any]]] = None


# ── Routers ─────────────────────────────────────────────────────────────────
vision_router = APIRouter(prefix="/vision", tags=["vision-board"])
canva_router = APIRouter(prefix="/canva", tags=["canva"])


@vision_router.get("/board")
async def get_board(user_id: str = "demo"):
    return _get_or_create(user_id)


@vision_router.put("/board")
async def update_board(payload: VisionBoardUpdate, user_id: str = "demo"):
    doc = _get_or_create(user_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        if v is not None:
            doc[k] = v
    _save(user_id, doc)
    return doc


@vision_router.post("/board/reset")
async def reset_board(user_id: str = "demo"):
    store = _read_all()
    store.pop(user_id, None)
    _write_all(store)
    return _get_or_create(user_id)


@vision_router.post("/board/switch-template")
async def switch_template(payload: Dict[str, Any], user_id: str = "demo"):
    tpl_id = payload.get("template")
    if tpl_id not in TEMPLATE_SEEDS:
        raise HTTPException(400, f"Template '{tpl_id}' non disponible")
    seed = TEMPLATE_SEEDS[tpl_id]
    doc = _get_or_create(user_id)
    doc.update({"template": seed["template"], "title": seed["title"],
                "theme": seed["theme"], "cards": seed["cards"]})
    _save(user_id, doc)
    return doc


@vision_router.get("/info")
async def get_vision_info(user_id: str = "demo"):
    doc = _get_or_create(user_id)
    return doc.get("vision_info") or DEFAULT_VISION_INFO()


@vision_router.put("/info")
async def update_vision_info(payload: Dict[str, Any], user_id: str = "demo"):
    doc = _get_or_create(user_id)
    doc["vision_info"] = payload
    _save(user_id, doc)
    return payload


@vision_router.post("/analyse")
async def analyse_vision(user_id: str = "demo"):
    doc = _get_or_create(user_id)
    info = doc.get("vision_info") or DEFAULT_VISION_INFO()
    return compute_analysis(info)


@vision_router.get("/copilot-data")
async def copilot_data(user_id: str = "demo"):
    doc = _get_or_create(user_id)
    info = doc.get("vision_info") or DEFAULT_VISION_INFO()
    obj = info.get("objectifs", {}) or {}
    phase = obj.get("phase", {}) or {}
    valeurs = info.get("valeurs") or []
    piliers = info.get("piliers") or []
    filled = sum([
        bool(obj.get("ca_cible")), bool(obj.get("marge_op_pct")),
        bool(obj.get("ikigai_score")), bool(phase.get("label")),
        len(valeurs) >= 3, len(piliers) >= 4,
        bool(info.get("vision_1an")), bool(info.get("vision_3ans")),
    ])
    return {
        "objectif_ca": {"cible": obj.get("ca_cible"), "devise": "EUR"},
        "marge_op_pct": obj.get("marge_op_pct"),
        "ikigai": {"score": obj.get("ikigai_score"), "citation": info.get("pourquoi", "")[:120]},
        "phase_actuelle": {"label": phase.get("label"), "mois": phase.get("mois"), "total": phase.get("total")},
        "valeurs": valeurs,
        "piliers": [{"label": p.get("label"), "progress": p.get("progress")} for p in piliers],
        "swot_disponible": True,
        "completion_score": round(filled / 8 * 100),
    }


@vision_router.get("/board/history")
async def board_history(user_id: str = "demo", limit: int = 20):
    now = datetime.now(timezone.utc)
    items = [
        {"id": f"v{i}", "label": label, "at": (now - timedelta(hours=h)).isoformat(),
         "by": "Vous", "summary": summary}
        for i, (h, label, summary) in enumerate([
            (0, "Sauvegarde auto", "Modification du titre et 2 photos"),
            (2, "Édition", "Mission mise à jour"),
            (24, "Switch template", "Passage à Arbre de Vie puis retour"),
            (48, "Création", "Vision Board créé depuis le modèle Feuille de Route"),
        ])
    ]
    return items[:limit]


@vision_router.get("/visionbook")
async def get_visionbook(user_id: str = "demo"):
    doc = _get_or_create(user_id)
    return doc.get("visionbook") or {"flipbook_url": None, "pdf_url": None, "generated_at": None}


@vision_router.post("/visionbook/generate")
async def generate_visionbook(user_id: str = "demo"):
    # Génération PDF/Heyzine non activée dans cet environnement — renvoie un état "à configurer".
    doc = _get_or_create(user_id)
    vb = {
        "flipbook_url": None,
        "pdf_url": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "message": "Génération du Vision Book (PDF + flipbook Heyzine) à activer avec la clé HEYZINE_API_KEY.",
    }
    doc["visionbook"] = vb
    _save(user_id, doc)
    return vb


@canva_router.get("/status")
async def canva_status():
    return {"connected": False, "configured": bool(os.environ.get("CANVA_CLIENT_ID"))}


@canva_router.get("/auth/start")
async def canva_auth_start():
    # Canva OAuth non branché ici — renvoie un état explicite (le front gère le cas).
    return {"authorization_url": None, "configured": bool(os.environ.get("CANVA_CLIENT_ID"))}
