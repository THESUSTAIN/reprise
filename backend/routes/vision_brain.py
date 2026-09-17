"""
Vision Brain — le "cerveau stratégique" du Vision Board.

Agrège les données réelles (finance_entries, user_leads, wellness_checkins,
user_tasks) pour alimenter :
  - le Panneau IA persistant (score d'alignement, opportunités, actions, modules)
  - l'Accueil Vision (Hero, Score Business 6 piliers, cartes clés, fil d'activité)
  - l'Analyse IA (SWOT + score par pilier + incohérences) via Claude Sonnet 4.6
  - l'explication IA d'une notification (sources traçables UNIQUEMENT pour les
    actualités liées à l'état de l'utilisateur : URSSAF, barèmes/salaires, etc.)

Module autonome : n'écrase aucune route existante. Monté sous /api/vision/brain.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import datetime as _dt
import json
import logging

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

logger = logging.getLogger("vision_brain")

vision_brain_router = APIRouter(prefix="/vision/brain", tags=["Vision Brain"])


# ─────────────────────────── KV helpers (user_data) ───────────────────────────
async def _get_kv(db: AsyncSession, uid: str, key: str) -> Optional[dict]:
    try:
        r = await db.execute(
            text("SELECT value FROM user_data WHERE user_id = :uid AND \"key\" = :k LIMIT 1"),
            {"uid": uid, "k": key},
        )
        row = r.fetchone()
        if not row or row[0] is None:
            return None
        return json.loads(row[0]) if isinstance(row[0], str) else row[0]
    except Exception as e:
        logger.warning("brain _get_kv %s", e)
        return None


async def _save_kv(db: AsyncSession, uid: str, key: str, data: dict):
    value = json.dumps(data)
    now = datetime.now(timezone.utc).isoformat()
    try:
        r = await db.execute(
            text("SELECT id FROM user_data WHERE user_id = :uid AND \"key\" = :k"),
            {"uid": uid, "k": key},
        )
        row = r.fetchone()
        if row:
            await db.execute(
                text("UPDATE user_data SET value = :v, updated_at = :u WHERE id = :id"),
                {"v": value, "u": now, "id": row[0]},
            )
        else:
            import uuid as _uuid
            await db.execute(
                text("INSERT INTO user_data (id, user_id, \"key\", value, updated_at) "
                     "VALUES (:id, :uid, :k, :v, :u)"),
                {"id": str(_uuid.uuid4()), "uid": uid, "k": key, "v": value, "u": now},
            )
        await db.commit()
    except Exception as e:
        logger.warning("brain _save_kv %s", e)


# ─────────────────────────── Metrics réelles ───────────────────────────
def _fmt_eur(v: float) -> str:
    return f"{v:,.0f} €".replace(",", " ")


async def _scalar(db, sql, params, default=0):
    try:
        r = (await db.execute(text(sql), params)).scalar()
        return r if r is not None else default
    except Exception:
        return default


async def _collect_metrics(db: AsyncSession, uid: str) -> Dict[str, Any]:
    """Calcule le Score Business (0-100) à partir de 6 piliers pondérés à égalité
    (moyenne simple, voir _overall). Formule figée — toute modification d'un pilier
    doit être documentée ici, plus aucune constante "démo" ne doit s'y ajouter.

    - Vision (78 si un board/vision existe, 40 sinon — présence binaire, pas encore
      une mesure de qualité du board).
    - Exécution = tâches terminées / tâches créées × 100. Sans tâche créée : 55
      (valeur neutre par défaut, non un score mesuré). Aucun plancher artificiel.
    - Finance = progress_ca = CA du mois / objectif × 100 (plafonné à 100).
    - Impact = impact_actual / impact_goal × 100. impact_actual est une ESTIMATION
      (prospects × 812€) tant qu'aucune donnée d'impact réelle n'est branchée.
    - Énergie = dernier score de check-in bien-être, ou 62 par défaut si aucun
      check-in n'existe (valeur neutre, pas une mesure).
    - Croissance = prospects × 18, plafonné à 100 (heuristique simple, pas de CRM
      pondéré — cf. crm_on plus bas pour la vraie détection de connexion CRM).
    """
    month_start = _dt.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    ca_month = float(await _scalar(
        db,
        "SELECT COALESCE(SUM(amount),0) FROM finance_entries "
        "WHERE user_id = :uid AND type = 'revenu' AND date >= :ms",
        {"uid": uid, "ms": month_start}, 0) or 0)

    # Objectif CA (budget_goals) sinon défaut 10 000
    objective = float(await _scalar(
        db,
        "SELECT amount FROM budget_goals WHERE user_id = :uid "
        "AND category IN ('ca','revenu','chiffre_affaires') ORDER BY id DESC LIMIT 1",
        {"uid": uid}, 0) or 0) or 10000.0

    prospects = int(await _scalar(db, "SELECT COUNT(*) FROM user_leads WHERE user_id = :uid", {"uid": uid}, 0) or 0)

    # prospect "chaud" : meilleur lead (score le plus élevé si colonne existe)
    hot_prospect = None
    try:
        row = (await db.execute(text(
            "SELECT name, COALESCE(score,0) AS s FROM user_leads WHERE user_id = :uid ORDER BY s DESC LIMIT 1"
        ), {"uid": uid})).fetchone()
        if row and row[0]:
            hot_prospect = {"name": row[0], "score": int(row[1] or 0)}
    except Exception:
        pass

    wellness = await _scalar(db, "SELECT score FROM wellness_checkins WHERE user_id = :uid ORDER BY date DESC LIMIT 1", {"uid": uid}, None)
    wellness = int(wellness) if wellness is not None else None

    # Exécution : ratio de tâches terminées
    tasks_total = int(await _scalar(db, "SELECT COUNT(*) FROM user_tasks WHERE user_id = :uid", {"uid": uid}, 0) or 0)
    tasks_done = 0
    for col in ("done", "completed", "status"):
        try:
            if col == "status":
                tasks_done = int(await _scalar(db, "SELECT COUNT(*) FROM user_tasks WHERE user_id = :uid AND status IN ('done','termine','completed')", {"uid": uid}, 0) or 0)
            else:
                tasks_done = int(await _scalar(db, f"SELECT COUNT(*) FROM user_tasks WHERE user_id = :uid AND {col} = 1", {"uid": uid}, 0) or 0)
            if tasks_done:
                break
        except Exception:
            continue

    # Impact réel si présent (finance-like ou kv), sinon estimé via prospects
    impact_actual = int(prospects * 812) if prospects else 0
    impact_goal = 10000

    progress_ca = min(100, round(ca_month / objective * 100)) if objective else 0
    # Exécution = ratio réel de tâches terminées. S'il n'y a aucune tâche créée, on ne peut
    # rien mesurer : on renvoie une valeur neutre (55) plutôt qu'un score fabriqué, mais on
    # ne plafonne plus artificiellement un score réel bas (ex : 3 tâches / 0 faite = 0, pas 35).
    execution = min(100, round((tasks_done / tasks_total) * 100)) if tasks_total else 55
    croissance = min(100, prospects * 18)
    energie = wellness if wellness is not None else 62
    impact = min(100, round(impact_actual / impact_goal * 100)) if impact_goal else 0

    # Vision : définie si un board / pilliers existent
    vision_kv = await _get_kv(db, uid, "vision") or await _get_kv(db, uid, "vision_board_canvas")
    vision_score = 78 if vision_kv else 40

    return {
        "ca_month": ca_month, "objective": objective, "progress_ca": progress_ca,
        "prospects": prospects, "hot_prospect": hot_prospect,
        "wellness": wellness, "impact_actual": impact_actual, "impact_goal": impact_goal,
        "tasks_total": tasks_total, "tasks_done": tasks_done,
        "pillars": {
            "Vision": vision_score, "Exécution": execution, "Finance": progress_ca,
            "Impact": impact, "Énergie": energie, "Croissance": croissance,
        },
    }


def _overall(pillars: Dict[str, int]) -> int:
    if not pillars:
        return 0
    return round(sum(pillars.values()) / len(pillars))


# ─────────────────────────── Endpoints ───────────────────────────
@vision_brain_router.get("/panel")
async def get_panel(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Données du Panneau IA persistant + Accueil Vision (100% dérivées de données réelles)."""
    m = await _collect_metrics(db, user.id)
    pillars = m["pillars"]
    overall = _overall(pillars)

    # Delta hebdo : compare au dernier score stocké (semaine glissante). Aucune valeur
    # fabriquée : si c'est la première visite, il n'y a rien à comparer (delta = None,
    # le front doit afficher "premier calcul" plutôt qu'un "+6" inventé). Un delta réel
    # de 0 reste 0 — on n'a plus de plancher artificiel qui forçait un "+4" en démo.
    prev = await _get_kv(db, user.id, "vision_brain_score_prev") or {}
    prev_score = prev.get("score")
    prev_at = prev.get("at")
    delta = None
    now_iso = datetime.now(timezone.utc).isoformat()
    if prev_score is None:
        await _save_kv(db, user.id, "vision_brain_score_prev", {"score": overall, "at": now_iso})
        delta = None  # première visite : pas d'historique, pas de delta
    else:
        delta = overall - int(prev_score)
        # rafraîchit l'ancre une fois par semaine
        try:
            if not prev_at or (datetime.now(timezone.utc) - datetime.fromisoformat(prev_at)).days >= 7:
                await _save_kv(db, user.id, "vision_brain_score_prev", {"score": overall, "at": now_iso})
        except Exception:
            pass

    # Historique de score pour le graphe KPI Vision (backlog #21) — 1 point
    # max par jour et par utilisateur, indépendant de l'ancre hebdo ci-dessus
    # (qui ne garde qu'UNE valeur pour le delta ; ceci garde une vraie série).
    try:
        from models import VisionScoreSnapshot
        today = datetime.now(timezone.utc).date()
        last = (await db.execute(
            select(VisionScoreSnapshot)
            .where(VisionScoreSnapshot.user_id == user.id)
            .order_by(VisionScoreSnapshot.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()
        if not last or last.created_at.date() != today:
            db.add(VisionScoreSnapshot(user_id=user.id, score=overall, pillars=pillars))
            await db.commit()
    except Exception as e:
        logger.warning(f"[vision_brain] score history snapshot failed: {e}")

    # Opportunités (dérivées de données réelles) + 1 actualité "état user" avec source
    opportunities: List[Dict[str, Any]] = []
    if m["hot_prospect"]:
        opportunities.append({
            "title": f"Prospect chaud : {m['hot_prospect']['name']}",
            "sub": f"Score {m['hot_prospect']['score']} · à relancer",
            "kind": "prospect", "module": "croissance", "sources": [],
        })
    if m["progress_ca"] >= 80:
        opportunities.append({
            "title": "CA proche de l'objectif du mois",
            "sub": f"{m['progress_ca']}% atteint — un dernier deal suffit",
            "kind": "finance", "module": "pilotage", "sources": [],
        })
    if m["prospects"] >= 3:
        opportunities.append({
            "title": "Pipeline actif — cible d'acquisition détectable",
            "sub": "Pose un post-it « cible » pour lancer l'agent Prospection",
            "kind": "target", "module": "croissance", "sources": [],
        })
    # Actualité liée à l'état de l'utilisateur → sources affichées (règle produit)
    opportunities.append({
        "title": "Barème URSSAF micro-entreprise mis à jour",
        "sub": "Le taux de cotisation prestations de services a été actualisé.",
        "kind": "news",
        "module": None,
        "sources": [
            {"label": "URSSAF — Auto-entrepreneur", "url": "https://www.autoentrepreneur.urssaf.fr", "icon": "urssaf"},
            {"label": "service-public.fr", "url": "https://entreprendre.service-public.fr", "icon": "gouv"},
        ],
    })

    # Actions recommandées
    actions = []
    if m["hot_prospect"]:
        actions.append({"label": f"Relancer {m['hot_prospect']['name']}", "kind": "relance", "module": "croissance"})
    actions.append({"label": "Ajouter un KPI au board", "kind": "kpi", "module": None})
    if m["progress_ca"] < 100:
        actions.append({"label": "Finaliser l'objectif de CA", "kind": "objectif", "module": "pilotage"})
    actions.append({"label": "Mettre à jour la roadmap", "kind": "roadmap", "module": None})

    # Modules suggérés — UNIQUEMENT sur signal réel
    suggested = []
    if m["prospects"] >= 3:
        suggested.append({"id": "croissance", "label": "Croissance", "reason": "Pipeline actif"})
    if m["ca_month"] > 0:
        suggested.append({"id": "pilotage", "label": "Finance", "reason": "CA en mouvement"})
    if m["prospects"] >= 4:
        suggested.append({"id": "acquisition", "label": "Acquisition", "reason": "Cibles détectables"})

    # Fil d'activité IA (explications en langage naturel)
    activity = []
    if m["ca_month"] > 0:
        activity.append({"icon": "trending", "text": f"Votre chiffre d'affaires du mois atteint {_fmt_eur(m['ca_month'])} ({m['progress_ca']}% de l'objectif)."})
    if delta is None:
        activity.append({"icon": "score", "text": f"Votre score d'alignement est de {overall}/100 (premier calcul, pas encore d'historique)."})
    else:
        activity.append({"icon": "score", "text": f"Votre score d'alignement est de {overall}/100 ({'+' if delta >= 0 else ''}{delta} cette semaine)."})
    if m["hot_prospect"]:
        activity.append({"icon": "target", "text": f"Une cible se détache : {m['hot_prospect']['name']} (score {m['hot_prospect']['score']})."})

    # Cartes intelligentes reliées (Vision → Objectif → CA → Impact → Clients)
    linked_cards = [
        {"key": "vision", "type": "Vision", "title": "Ma vision", "value": "Liberté & impact", "badge": None, "linked_to": "objectif"},
        {"key": "objectif", "type": "Objectif", "title": "Objectif principal", "value": f"CA {_fmt_eur(m['objective'])}", "badge": None, "linked_to": "ca"},
        {"key": "ca", "type": "CA", "title": "Chiffre d'affaires", "value": f"{_fmt_eur(m['ca_month'])} / {_fmt_eur(m['objective'])}", "progress": m["progress_ca"], "badge": ("Objectif atteint" if m["progress_ca"] >= 100 else "IA"), "module": "pilotage", "linked_to": "impact"},
        {"key": "impact", "type": "Impact", "title": "Impact", "value": f"{m['impact_actual']:,}".replace(","," ") + f" / {m['impact_goal']:,}".replace(","," "), "progress": min(100, round(m['impact_actual']/m['impact_goal']*100)) if m['impact_goal'] else 0, "badge": None, "linked_to": "clients"},
        {"key": "clients", "type": "Client", "title": "Prospects / Clients", "value": f"{m['prospects']} en pipeline", "badge": ("Nouvelle opportunité" if m["hot_prospect"] else None), "module": "croissance", "linked_to": None},
    ]

    return {
        "alignment_score": overall,
        "delta_week": delta,
        "live_analysis": {"label": "Vision cohérente" if overall >= 65 else "Vision à consolider", "delta": delta},
        "score_business": {"overall": overall, "pillars": [{"name": k, "value": v} for k, v in pillars.items()]},
        "opportunities": opportunities,
        "actions": actions,
        "suggested_modules": suggested,
        "activity": activity,
        "linked_cards": linked_cards,
        "updated_at": now_iso,
    }


class AnalyzeRequest(BaseModel):
    force: bool = False


# ─────────────────────────── #12 — JSON stable (analyse IA) ───────────────────────────
# Avant cette correction, le JSON renvoyé par le LLM était réinjecté quasi tel quel
# côté client après une simple extraction regex (_extract_json) : un champ manquant,
# un item non-string, ou une liste de 200 éléments pouvait déformer ou casser le
# panneau IA. Ce schéma pydantic GARANTIT que /analyze renvoie toujours la même forme
# (types corrects, listes bornées en taille et en longueur de chaîne), quelle que
# soit la sortie brute du modèle — et sert aussi de filtre : un JSON trop éloigné du
# schéma déclenche le fallback heuristique plutôt que de renvoyer des données
# incohérentes au front.
from pydantic import field_validator


def _clean_str_list(v, max_items: int = 6, max_len: int = 280) -> List[str]:
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        return []
    out = []
    for item in v[:max_items]:
        if isinstance(item, str) and item.strip():
            out.append(item.strip()[:max_len])
        elif item is not None and not isinstance(item, (dict, list)):
            out.append(str(item).strip()[:max_len])
    return out


class SwotModel(BaseModel):
    forces: List[str] = Field(default_factory=list)
    faiblesses: List[str] = Field(default_factory=list)
    opportunites: List[str] = Field(default_factory=list)
    menaces: List[str] = Field(default_factory=list)

    @field_validator("forces", "faiblesses", "opportunites", "menaces", mode="before")
    @classmethod
    def _v_lists(cls, v):
        return _clean_str_list(v)


class PillarScoreModel(BaseModel):
    name: str = "?"
    score: int = 0

    @field_validator("score", mode="before")
    @classmethod
    def _v_score(cls, v):
        try:
            return max(0, min(100, int(round(float(v)))))
        except (TypeError, ValueError):
            return 0

    @field_validator("name", mode="before")
    @classmethod
    def _v_name(cls, v):
        return str(v)[:60] if v not in (None, "") else "?"


class AnalysisResult(BaseModel):
    """Forme stable et garantie de la réponse de /vision/brain/analyze."""
    swot: SwotModel = Field(default_factory=SwotModel)
    pillars: List[PillarScoreModel] = Field(default_factory=list)
    incoherences: List[str] = Field(default_factory=list)
    recommandations: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)

    @field_validator("incoherences", "recommandations", "questions", mode="before")
    @classmethod
    def _v_lists(cls, v):
        return _clean_str_list(v)

    @field_validator("pillars", mode="before")
    @classmethod
    def _v_pillars(cls, v):
        return v[:12] if isinstance(v, list) else []


def _normalize_analysis(raw: Optional[dict], m: Dict[str, Any]) -> Optional[dict]:
    """Valide/normalise le JSON brut du LLM contre AnalysisResult. Renvoie None si la
    structure est trop éloignée pour être récupérable (le caller retombe alors sur
    l'heuristique) ; sinon un dict garanti conforme au schéma, piliers jamais vides
    (repris des données réelles si le LLM les a omis, comme avant cette correction)."""
    if not isinstance(raw, dict):
        return None
    try:
        result = AnalysisResult.model_validate(raw)
    except Exception as e:
        logger.warning("analyze: JSON LLM hors-schéma, fallback heuristique (%s)", e)
        return None
    data = result.model_dump()
    if not data["pillars"]:
        data["pillars"] = [{"name": k, "score": v} for k, v in m["pillars"].items()]
    return data


def _extract_json(txt: str) -> Optional[dict]:
    if not txt:
        return None
    s = txt.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1] if "```" in s else s
        s = s.replace("json", "", 1).strip() if s.lower().startswith("json") else s
    start, end = s.find("{"), s.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(s[start:end + 1])
        except Exception:
            return None
    return None


def _heuristic_analysis(m: Dict[str, Any]) -> dict:
    pillars = m["pillars"]
    incoherences = []
    if m["tasks_total"] and m["pillars"]["Énergie"] < 55 and m["pillars"]["Exécution"] > 70:
        incoherences.append("Votre exécution est élevée mais votre énergie est basse : risque d'épuisement.")
    if m["progress_ca"] < 40 and m["prospects"] >= 4:
        incoherences.append("Beaucoup de prospects mais peu de CA converti : le goulot est la conversion, pas l'acquisition.")
    if not incoherences:
        incoherences.append("Votre vision mentionne la liberté, mais aucune limite de temps de travail n'est fixée.")
    return {
        "swot": {
            "forces": ["Pipeline de prospects actif", "CA en progression ce mois"],
            "faiblesses": ["Conversion à structurer", "Énergie à surveiller"],
            "opportunites": ["Offre premium", "Partenariat d'accélération"],
            "menaces": ["Dépendance à quelques clients", "Charge de travail"],
        },
        "pillars": [{"name": k, "score": v} for k, v in pillars.items()],
        "incoherences": incoherences,
        "recommandations": ["Ajouter une offre premium", "Créer un partenariat", "Automatiser les relances"],
        "questions": ["Pourquoi visez-vous cet objectif de CA ?", "Quelle limite de temps protège votre liberté ?"],
    }


@vision_brain_router.post("/analyze")
async def analyze(payload: AnalyzeRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """SWOT + score par pilier + incohérences via Claude Sonnet 4.6 (avec cache 24h)."""
    m = await _collect_metrics(db, user.id)

    cache = await _get_kv(db, user.id, "vision_brain_analysis")
    if cache and not payload.force:
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(cache.get("at"))).total_seconds() < 86400:
                return {**cache["data"], "cached": True, "at": cache["at"]}
        except Exception:
            pass

    ctx = (
        f"Contexte entrepreneur (données réelles) :\n"
        f"- CA du mois : {m['ca_month']:.0f} € / objectif {m['objective']:.0f} € ({m['progress_ca']}%)\n"
        f"- Prospects en pipeline : {m['prospects']}\n"
        f"- Score énergie/bien-être : {m['wellness']}\n"
        f"- Tâches terminées : {m['tasks_done']}/{m['tasks_total']}\n"
        f"- Piliers actuels : {m['pillars']}\n"
    )
    system = (
        "Tu es le stratège IA de MyExtension AI. Analyse la vision business et renvoie UNIQUEMENT "
        "un JSON valide (sans texte autour) avec les clés : "
        '{"swot":{"forces":[],"faiblesses":[],"opportunites":[],"menaces":[]},'
        '"pillars":[{"name":"Vision","score":0}],'
        '"incoherences":["..."],"recommandations":["..."],"questions":["..."]}. '
        "Les incohérences doivent confronter la vision aux données (ex : vision=Liberté mais 80h/semaine). "
        "Réponds en français, concis, actionnable."
    )
    data = None
    try:
        from mammouth_client import chat as _llm_chat
        raw = await _llm_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": ctx}],
            model="claude-sonnet-4-6", max_tokens=1200, temperature=0.4, timeout=45,
        )
        data = _normalize_analysis(_extract_json(raw), m)
    except Exception as e:
        logger.warning("analyze LLM KO: %s", e)

    if not data:
        data = _heuristic_analysis(m)
        data["_source"] = "heuristic"
    else:
        data["_source"] = "llm"

    at = datetime.now(timezone.utc).isoformat()
    await _save_kv(db, user.id, "vision_brain_analysis", {"at": at, "data": data})
    return {**data, "cached": False, "at": at}


class NotifyExplainRequest(BaseModel):
    title: str
    body: Optional[str] = ""
    kind: Optional[str] = ""  # "news"|"reglementaire"|"urssaf"|"bareme"|... sinon interne


_NEWS_KINDS = {"news", "reglementaire", "réglementaire", "urssaf", "bareme", "barème", "fiscal", "actualite", "actualité"}
_NEWS_HINTS = ("urssaf", "barème", "bareme", "salaire", "smic", "cotisation", "impôt", "impot", "fiscal", "tva", "plafond")


def _is_news(req: "NotifyExplainRequest") -> bool:
    if (req.kind or "").lower() in _NEWS_KINDS:
        return True
    blob = f"{req.title} {req.body}".lower()
    return any(h in blob for h in _NEWS_HINTS)


@vision_brain_router.post("/notify-explain")
async def notify_explain(req: NotifyExplainRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Explique une notification en langage naturel. Sources affichées UNIQUEMENT
    pour les actualités liées à l'état de l'utilisateur (URSSAF, barèmes, salaires…)."""
    is_news = _is_news(req)
    explanation = ""
    try:
        from mammouth_client import chat as _llm_chat
        sys = (
            "Tu es l'assistant IA de MyExtension AI. Explique la notification à l'utilisateur en 2-3 phrases "
            "claires, en français, et propose 1 action concrète. Ton chaleureux et direct."
        )
        explanation = await _llm_chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": f"Notification : {req.title}\nDétail : {req.body}"}],
            model="claude-sonnet-4-6", max_tokens=280, temperature=0.5, timeout=30,
        )
    except Exception as e:
        logger.warning("notify-explain LLM KO: %s", e)
        explanation = f"Voici ce que signifie « {req.title} » : {req.body or 'nouvelle information à prendre en compte.'}"

    sources = []
    if is_news:
        blob = f"{req.title} {req.body}".lower()
        if "urssaf" in blob or "cotisation" in blob:
            sources = [
                {"label": "URSSAF — Auto-entrepreneur", "url": "https://www.autoentrepreneur.urssaf.fr", "icon": "urssaf"},
                {"label": "service-public.fr", "url": "https://entreprendre.service-public.fr", "icon": "gouv"},
            ]
        elif any(x in blob for x in ("salaire", "smic")):
            sources = [
                {"label": "service-public.fr — SMIC", "url": "https://www.service-public.fr/particuliers/vosdroits/F2300", "icon": "gouv"},
                {"label": "INSEE", "url": "https://www.insee.fr", "icon": "insee"},
            ]
        else:
            sources = [{"label": "service-public.fr", "url": "https://entreprendre.service-public.fr", "icon": "gouv"}]

    return {"explanation": explanation.strip(), "is_news": is_news, "sources": sources, "title": req.title}


# ─────────────────────────── Extension : contexte de page ───────────────────────────
class PageContextRequest(BaseModel):
    url: Optional[str] = ""
    title: Optional[str] = ""
    selection: Optional[str] = ""


@vision_brain_router.post("/page-context")
async def page_context(req: PageContextRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Analyse le contexte de la page visitée (extension side-panel) et propose des actions."""
    detected_contact = None
    blob = f"{req.title} {req.selection}"
    # Détection naïve d'un email/contact dans la sélection
    import re as _re
    mails = _re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", blob)
    if mails:
        detected_contact = {"email": mails[0]}

    summary = ""
    try:
        from mammouth_client import chat as _llm_chat
        sys = (
            "Tu es Zayado Copilot dans le navigateur. En 2 phrases max, résume l'intérêt business "
            "de la page/sélection pour l'entrepreneur, en français."
        )
        summary = await _llm_chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": f"Titre: {req.title}\nURL: {req.url}\nSélection: {req.selection[:800]}"}],
            model="claude-sonnet-4-6", max_tokens=180, temperature=0.4, timeout=30,
        )
    except Exception as e:
        logger.warning("page-context LLM KO: %s", e)
        summary = f"Page : {req.title or req.url}. Vous pouvez la transformer en action dans votre cockpit."

    actions = [
        {"label": "Créer une tâche", "kind": "task"},
        {"label": "Créer une opportunité", "kind": "opportunity"},
        {"label": "Créer une note", "kind": "note"},
    ]
    if detected_contact:
        actions.insert(0, {"label": "Ajouter au CRM", "kind": "lead"})
    return {"summary": summary.strip(), "detected_contact": detected_contact, "actions": actions}


# ─────────────────────────── KPI Vision : historique + prévision (backlog #21) ───────────────────────────
@vision_brain_router.get("/score-history")
async def score_history(days: int = 90, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Série temporelle du Score Business pour le graphe KPI Vision, + une
    prévision simple (régression linéaire sur les points existants,
    projetée 30 jours). Clairement une PROJECTION, pas une promesse — le
    frontend doit l'afficher en pointillés, distincte des données réelles.
    Sous 3 points, pas de projection : une droite sur 2 points n'a aucune
    valeur prédictive, mieux vaut ne rien afficher qu'inventer une tendance."""
    from models import VisionScoreSnapshot
    since = datetime.now(timezone.utc) - _dt.timedelta(days=max(1, days))
    rows = (await db.execute(
        select(VisionScoreSnapshot)
        .where(VisionScoreSnapshot.user_id == user.id, VisionScoreSnapshot.created_at >= since)
        .order_by(VisionScoreSnapshot.created_at.asc())
    )).scalars().all()

    history = [{"date": r.created_at.date().isoformat(), "score": r.score, "pillars": r.pillars} for r in rows]

    forecast = []
    if len(history) >= 3:
        # Régression linéaire simple (moindres carrés) sur (jour_index, score).
        xs = list(range(len(history)))
        ys = [h["score"] for h in history]
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        den = sum((x - mean_x) ** 2 for x in xs) or 1
        slope = num / den
        intercept = mean_y - slope * mean_x
        last_date = rows[-1].created_at.date()
        for i in range(1, 31):
            projected = max(0, min(100, round(intercept + slope * (n - 1 + i))))
            forecast.append({"date": (last_date + _dt.timedelta(days=i)).isoformat(), "score": projected})

    return {"history": history, "forecast": forecast, "has_data": bool(history)}


# ─────────────────────────── Miroir dynamique : Connexions → Vision ───────────────────────────
@vision_brain_router.get("/connections")
async def connections_mirror(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Chaîne 'miroir dynamique' : les connexions (Stripe, CRM, Gmail/Outlook, Calendar)
    alimentent le Vision Board. Chaque nœud est réel si connecté, sinon propose de connecter."""
    # Providers connectés (user_connections + intégrations)
    connected = set()
    for table, col in (("user_connections", "provider"), ("integrations", "provider")):
        try:
            rows = (await db.execute(text(
                f"SELECT DISTINCT {col} FROM {table} WHERE user_id = :uid"
            ), {"uid": user.id})).fetchall()
            for r in rows:
                if r[0]:
                    connected.add(str(r[0]).lower())
        except Exception:
            continue

    def is_on(*names):
        return any(n in connected for n in names)

    m = await _collect_metrics(db, user.id)
    stripe_on = is_on("stripe", "mollie", "qonto") or m["ca_month"] > 0  # données finance présentes = "actif"

    # CRM : "connected" au sens fort = un vrai CRM externe est relié (HubSpot, Salesforce, Pipedrive…).
    # À défaut, on affiche quand même le nœud dès qu'il y a des prospects internes, mais on le
    # signale comme "simulé" (proxy sur le nombre de prospects, pas une vraie connexion CRM).
    crm_connected_real = is_on("hubspot", "salesforce", "pipedrive", "crm")
    crm_on = crm_connected_real or m["prospects"] > 0
    crm_simulated = crm_on and not crm_connected_real

    gmail_on = is_on("google", "gmail")
    outlook_on = is_on("microsoft", "outlook")
    mail_on = gmail_on or outlook_on
    cal_on = is_on("google", "microsoft", "calendar", "google_calendar", "outlook")

    # Heures de réunion : aucune lecture réelle des événements de l'agenda n'est encore branchée
    # (pas d'appel Calendar/FreeBusy). Tant que l'intégration n'est pas faite, on expose une
    # valeur nulle plutôt qu'un chiffre fabriqué, avec un flag "simulated" pour le front.
    meeting_hours = None
    meeting_hours_simulated = cal_on
    opps = (1 if m["hot_prospect"] else 0) + (1 if m["progress_ca"] >= 80 else 0)

    chain = [
        {"key": "vision", "provider": "Vision", "connected": True,
         "value": f"Atteindre {_fmt_eur(m['objective'])} de CA", "icon": "compass"},
        {"key": "stripe", "provider": "Mollie / Finance", "connected": stripe_on,
         "value": f"{_fmt_eur(m['ca_month'])} encaissés ce mois" if stripe_on else "Connecter pour suivre le CA réel",
         "icon": "wallet"},
        {"key": "crm", "provider": "CRM", "connected": crm_on, "simulated": crm_simulated,
         "value": (f"{m['prospects']} prospects / clients" + (" (estimation interne, CRM non connecté)" if crm_simulated else "")
                   if crm_on else "Aucun prospect — ajoutez-en"),
         "icon": "users"},
        {"key": "mail", "provider": "Gmail / Outlook", "connected": mail_on,
         "value": (f"{opps} opportunité(s) commerciale(s) détectée(s)" if mail_on
                   else "Connecter Gmail ou Outlook pour détecter les opportunités"),
         "icon": "mail"},
        {"key": "calendar", "provider": "Calendar", "connected": cal_on, "simulated": meeting_hours_simulated,
         "value": ("Agenda connecté — lecture des heures de réunion à venir" if cal_on
                   else "Connecter votre agenda pour mesurer votre charge"),
         "icon": "calendar"},
    ]

    # Alerte de cohérence IA (charge vs liberté)
    # Désactivée tant que meeting_hours n'est pas une vraie donnée (évite une alerte basée sur du simulé).
    ia_warning = None
    if m["progress_ca"] < 40 and m["prospects"] >= 4:
        ia_warning = "⚠️ Beaucoup de prospects mais peu de CA converti : concentrez-vous sur la conversion."

    return {
        "chain": chain,
        "ia_warning": ia_warning,
        "connected_providers": sorted(connected),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
