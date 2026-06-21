"""
Vision Board API
Routes pour persister + lister les Vision Boards de l'utilisateur.
Pour l'instant : un seul user "demo" (pas d'auth). À brancher quand auth en place.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid


# ============================================================
# MODELS
# ============================================================
class Card(BaseModel):
    """Carte/bloc déplaçable sur le canvas — coordonnées en %."""
    model_config = ConfigDict(extra="allow")

    id: str
    type: str  # title | quote | image | timeline | mission | quote-card | note | valeurs
    x: float
    y: float
    w: float
    h: float
    content: Dict[str, Any] = Field(default_factory=dict)
    style: Optional[Dict[str, Any]] = None


class Theme(BaseModel):
    palette: str = "navy-gold"
    font: str = "fraunces"


class VisionBoard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "demo"
    title: str = "Vision Board 2029"
    template: str = "feuille_de_route"
    theme: Theme = Field(default_factory=Theme)
    cards: List[Card] = Field(default_factory=list)
    vision_info: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_public: bool = False
    public_slug: Optional[str] = None


class VisionBoardUpdate(BaseModel):
    """Payload accepté pour PUT — tout est optionnel (autosave granulaire)."""
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    template: Optional[str] = None
    theme: Optional[Theme] = None
    cards: Optional[List[Card]] = None
    is_public: Optional[bool] = None


def DEFAULT_VISION_INFO() -> Dict[str, Any]:
    """Infos vision par défaut (board démo). Module-level pour réutilisation (PDF)."""
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
    """Analyse IA des infos utilisateur (heuristique, MOCKÉE tant que pas de LLM).
    Partagée entre l'endpoint /analyse et la génération du Vision Book PDF."""
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


# ============================================================
# ROUTER FACTORY (db injection)
# ============================================================
def build_router(db: AsyncIOMotorDatabase) -> APIRouter:
    router = APIRouter(prefix="/vision", tags=["vision-board"])

    COLLECTION = db.vision_boards

    def _default_vision_info():
        return DEFAULT_VISION_INFO()

    async def _get_or_create(user_id: str = "demo") -> dict:
        """Récupère le board du user; en crée un par défaut s'il n'existe pas."""
        doc = await COLLECTION.find_one({"user_id": user_id}, {"_id": 0})
        if doc:
            return doc

        # Seed avec la Feuille de Route par défaut
        from vision_seed import FEUILLE_DE_ROUTE_DEFAULT
        new_board = VisionBoard(
            user_id=user_id,
            title=FEUILLE_DE_ROUTE_DEFAULT["title"],
            template=FEUILLE_DE_ROUTE_DEFAULT["template"],
            theme=Theme(**FEUILLE_DE_ROUTE_DEFAULT["theme"]),
            cards=[Card(**c) for c in FEUILLE_DE_ROUTE_DEFAULT["cards"]],
        )
        doc = new_board.model_dump()
        await COLLECTION.insert_one(doc)
        return doc

    @router.get("/board")
    async def get_board(user_id: str = "demo"):
        """Récupère le Vision Board actif de l'utilisateur."""
        doc = await _get_or_create(user_id)
        doc.pop("_id", None)
        return doc

    @router.put("/board")
    async def update_board(payload: VisionBoardUpdate, user_id: str = "demo"):
        """Auto-save partiel du board (PATCH-style)."""
        await _get_or_create(user_id)
        # model_dump already produces plain JSON-serializable dicts/lists
        update = {k: v for k, v in payload.model_dump(exclude_unset=True).items()
                  if v is not None}
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await COLLECTION.update_one({"user_id": user_id}, {"$set": update})
        doc = await COLLECTION.find_one({"user_id": user_id}, {"_id": 0})
        return doc

    @router.post("/board/reset")
    async def reset_board(user_id: str = "demo"):
        """Réinitialise le Vision Board au template par défaut (feuille_de_route)."""
        await COLLECTION.delete_one({"user_id": user_id})
        doc = await _get_or_create(user_id)
        doc.pop("_id", None)
        return doc

    @router.post("/board/switch-template")
    async def switch_template(payload: Dict[str, Any], user_id: str = "demo"):
        """Change le template ET remplace les cards par celles du nouveau template."""
        from vision_seed import TEMPLATE_SEEDS
        tpl_id = payload.get("template")
        if tpl_id not in TEMPLATE_SEEDS:
            raise HTTPException(400, f"Template '{tpl_id}' non disponible")
        seed = TEMPLATE_SEEDS[tpl_id]
        await _get_or_create(user_id)
        await COLLECTION.update_one(
            {"user_id": user_id},
            {"$set": {
                "template": seed["template"],
                "title": seed["title"],
                "theme": seed["theme"],
                "cards": seed["cards"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        doc = await COLLECTION.find_one({"user_id": user_id}, {"_id": 0})
        return doc

    @router.get("/info")
    async def get_vision_info(user_id: str = "demo"):
        """Récupère les infos personnelles utilisées par Analyse IA + édition manuelle."""
        doc = await _get_or_create(user_id)
        info = doc.get("vision_info") or _default_vision_info()
        return info

    @router.put("/info")
    async def update_vision_info(payload: Dict[str, Any], user_id: str = "demo"):
        """Met à jour les infos personnelles (Mission, Pourquoi, Visions, Valeurs, Objectifs)."""
        await _get_or_create(user_id)
        await COLLECTION.update_one(
            {"user_id": user_id},
            {"$set": {"vision_info": payload,
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return payload

    @router.post("/analyse")
    async def analyse_vision(user_id: str = "demo"):
        """Analyse IA des infos utilisateur. MOCKÉE — branchera LLM dès que clés fournies."""
        doc = await _get_or_create(user_id)
        info = doc.get("vision_info") or _default_vision_info()
        return compute_analysis(info)

    @router.get("/board/history")
    async def get_board_history(user_id: str = "demo", limit: int = 20):
        """Liste mockée des versions du Vision Board.
        TODO : à remplacer par une vraie versioning quand le user voudra."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        items = [
            {"id": f"v{i}", "label": label, "at": (now - timedelta(hours=h)).isoformat(),
             "by": "Julien Martin", "summary": summary}
            for i, (h, label, summary) in enumerate([
                (0, "Sauvegarde auto", "Modification du titre et 2 photos"),
                (2, "Édition", "Mission mise à jour"),
                (24, "Switch template", "Passage à Arbre de Vie puis retour"),
                (48, "Création", "Vision Board 2029 créé depuis le modèle Feuille de Route"),
            ])
        ]
        return items[:limit]

    @router.post("/board/publish")
    async def publish_board(user_id: str = "demo"):
        """Bascule l'état public du board, génère un slug si besoin."""
        doc = await _get_or_create(user_id)
        new_public = not doc.get("is_public", False)
        slug = doc.get("public_slug") or f"{user_id}-{uuid.uuid4().hex[:8]}"
        await COLLECTION.update_one(
            {"user_id": user_id},
            {"$set": {"is_public": new_public, "public_slug": slug,
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return {"is_public": new_public, "public_slug": slug,
                "url": f"zayado.net/vision/{slug}"}

    @router.get("/templates")
    async def list_templates():
        """Liste des templates disponibles (avec leur état actif/bientôt)."""
        return [
            {"id": "feuille_de_route", "name": "Feuille de Route", "tag": "Trajectoire", "ready": True,
             "img": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=600&q=80"},
            {"id": "arbre",     "name": "Arbre de Vie",      "tag": "Équilibre",       "ready": True,
             "img": "https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?auto=format&fit=crop&w=600&q=80"},
            {"id": "moodboard", "name": "Moodboard Premium", "tag": "Inspiration",     "ready": False,
             "img": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?auto=format&fit=crop&w=600&q=80"},
            {"id": "ceo",       "name": "CEO Dashboard",     "tag": "Business",        "ready": False,
             "img": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=600&q=80"},
            {"id": "magazine",  "name": "Magazine du Futur", "tag": "Storytelling",    "ready": False,
             "img": "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?auto=format&fit=crop&w=600&q=80"},
            {"id": "compass",   "name": "Life Compass",      "tag": "Équilibre",       "ready": False,
             "img": "https://images.unsplash.com/photo-1531346878377-a5be20888e57?auto=format&fit=crop&w=600&q=80"},
        ]

    @router.get("/ai/suggestions")
    async def get_ai_suggestions(user_id: str = "demo"):
        """Suggestions du Collaborateur AI — MOCKÉES (sans clé IA).
        Seront remplacées par un appel LLM réel quand l'utilisateur fournira la clé."""
        return [
            {"id": "fin", "text": "Votre Vision Board manque d'objectifs financiers.", "action": "add_finance_block"},
            {"id": "3y", "text": "Souhaitez-vous ajouter une trajectoire à 3 ans ?", "action": "add_timeline_3y"},
            {"id": "swot", "text": "Je peux générer une SWOT adaptée à votre projet.", "action": "generate_swot"},
        ]

    @router.post("/ai/generate")
    async def generate_ai_content(payload: Dict[str, Any]):
        """Endpoint AI mocké — renvoie un contenu placeholder en attendant les clés."""
        kind = payload.get("kind", "swot")
        return {
            "kind": kind,
            "mocked": True,
            "message": "AI generation est désactivée — fournissez vos clés (OpenAI/Gemini) pour activer le Collaborateur AI.",
        }

    @router.get("/copilot-data")
    async def copilot_data(user_id: str = "demo"):
        """JSON structuré exact que le Co-pilote IA lit (jamais le fond Canva).
        Blocs métier: Objectif CA, Marge, Ikigai, Phase, Valeurs, Piliers, SWOT."""
        doc = await _get_or_create(user_id)
        info = doc.get("vision_info") or _default_vision_info()
        obj = info.get("objectifs", {}) or {}
        phase = obj.get("phase", {}) or {}
        valeurs = info.get("valeurs") or []
        piliers = info.get("piliers") or []
        # completion basé sur les blocs métier remplis (pas un comptage de cartes)
        filled = sum([
            bool(obj.get("ca_cible")), bool(obj.get("marge_op_pct")),
            bool(obj.get("ikigai_score")), bool(phase.get("label")),
            len(valeurs) >= 3, len(piliers) >= 4,
            bool(info.get("vision_1an")), bool(info.get("vision_3ans")),
        ])
        completion = round(filled / 8 * 100)
        return {
            "objectif_ca": {"cible": obj.get("ca_cible"), "devise": "EUR"},
            "marge_op_pct": obj.get("marge_op_pct"),
            "ikigai": {"score": obj.get("ikigai_score"),
                       "citation": info.get("pourquoi", "")[:120]},
            "phase_actuelle": {"label": phase.get("label"),
                               "mois": phase.get("mois"), "total": phase.get("total")},
            "valeurs": valeurs,
            "piliers": [{"label": p.get("label"), "progress": p.get("progress")} for p in piliers],
            "swot_disponible": True,
            "completion_score": completion,
            "note": "L'IA ne lit jamais le fond Canva — uniquement ces blocs métier structurés.",
        }

    return router
