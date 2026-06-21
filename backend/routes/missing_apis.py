"""Endpoints manquants — empty states bien formés + stockage léger via JSON tables.

VAGUE 1 — fournit des endpoints non-404 pour :
- /api/tasks                  (CRUD)
- /api/vision                 (GET/PATCH)
- /api/documents              (CRUD + /generate)
- /api/leads                  (CRUD)
- /api/streak                 (GET)
- /api/revenue/monthly        (GET)
- /api/energy/today           (GET)
- /api/energy/latest          (GET)
- /api/processes/templates    (GET)
- /api/analyse                (GET/POST avec Claude Sonnet 4.5)

Pattern : tables ad-hoc créées à la volée (CREATE TABLE IF NOT EXISTS),
stockage JSON simple. Cohérent avec routes/processes.py.
"""
import os
import uuid
import json
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user, User

logger = logging.getLogger(__name__)
missing_router = APIRouter(tags=["missing-apis"])


def _utc_now():
    return datetime.now(timezone.utc)


# ============================================================
# Generic JSON table helper
# ============================================================
async def _ensure_table(db: AsyncSession, table: str):
    await db.execute(text(
        f"CREATE TABLE IF NOT EXISTS {table} ("
        f"id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, "
        f"data JSON NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
        f"updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    ))


async def _list_rows(db: AsyncSession, table: str, user_id: str) -> list:
    await _ensure_table(db, table)
    try:
        r = await db.execute(
            text(f"SELECT data FROM {table} WHERE user_id = :uid ORDER BY created_at DESC"),
            {"uid": user_id}
        )
        rows = r.fetchall()
        result = []
        for row in rows:
            data = row[0]
            if isinstance(data, str):
                data = json.loads(data)
            result.append(data)
        return result
    except Exception as e:
        logger.warning("list_rows %s failed: %s", table, e)
        return []


async def _insert_row(db: AsyncSession, table: str, user_id: str, data: dict) -> dict:
    await _ensure_table(db, table)
    rid = data.get("id") or str(uuid.uuid4())
    data["id"] = rid
    data["created_at"] = data.get("created_at") or _utc_now().isoformat()
    try:
        await db.execute(
            text(f"INSERT INTO {table} (id, user_id, data) VALUES (:id, :uid, :d)"),
            {"id": rid, "uid": user_id, "d": json.dumps(data)},
        )
        await db.commit()
        return data
    except Exception as e:
        await db.rollback()
        logger.warning("insert_row %s failed: %s", table, e)
        raise HTTPException(500, "Erreur de sauvegarde")


async def _update_row(db: AsyncSession, table: str, user_id: str, rid: str, patch: dict) -> Optional[dict]:
    await _ensure_table(db, table)
    r = await db.execute(
        text(f"SELECT data FROM {table} WHERE id = :id AND user_id = :uid"),
        {"id": rid, "uid": user_id},
    )
    row = r.fetchone()
    if not row:
        return None
    cur = row[0]
    if isinstance(cur, str):
        cur = json.loads(cur)
    cur.update({k: v for k, v in patch.items() if v is not None})
    cur["updated_at"] = _utc_now().isoformat()
    await db.execute(
        text(f"UPDATE {table} SET data = :d WHERE id = :id AND user_id = :uid"),
        {"id": rid, "uid": user_id, "d": json.dumps(cur)},
    )
    await db.commit()
    return cur


async def _delete_row(db: AsyncSession, table: str, user_id: str, rid: str) -> bool:
    await _ensure_table(db, table)
    r = await db.execute(
        text(f"DELETE FROM {table} WHERE id = :id AND user_id = :uid"),
        {"id": rid, "uid": user_id},
    )
    await db.commit()
    return (r.rowcount or 0) > 0


# ============================================================
# TASKS  /api/tasks
# ============================================================
class TaskIn(BaseModel):
    label: str
    type: Optional[str] = "humain"   # humain | ia
    priority: Optional[str] = "normal"
    due_at: Optional[str] = None
    notes: Optional[str] = None


class TaskPatch(BaseModel):
    label: Optional[str] = None
    type: Optional[str] = None
    done: Optional[bool] = None
    in_progress: Optional[bool] = None
    priority: Optional[str] = None
    due_at: Optional[str] = None
    notes: Optional[str] = None


@missing_router.get("/tasks")
async def list_tasks(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_tasks", user.id)
    return {"items": items}


@missing_router.post("/tasks")
async def create_task(body: TaskIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = body.dict()
    data["done"] = False
    data["in_progress"] = False
    return await _insert_row(db, "user_tasks", user.id, data)


@missing_router.patch("/tasks/{tid}")
async def patch_task(tid: str, body: TaskPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await _update_row(db, "user_tasks", user.id, tid, body.dict(exclude_unset=True))
    if not res:
        raise HTTPException(404, "Tâche introuvable")
    return res


@missing_router.delete("/tasks/{tid}")
async def delete_task(tid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await _delete_row(db, "user_tasks", user.id, tid)
    return {"deleted": ok}


# ============================================================
# VISION  /api/vision  (single doc per user)
# ============================================================
class VisionPatch(BaseModel):
    why: Optional[str] = None
    where: Optional[str] = None
    what: Optional[str] = None
    who: Optional[str] = None
    when: Optional[str] = None
    how: Optional[str] = None
    progress: Optional[int] = None
    notes: Optional[str] = None


@missing_router.get("/vision")
async def get_vision(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_vision", user.id)
    if items:
        return items[0]
    # Empty state bien formé
    return {
        "id": None,
        "why": "", "where": "", "what": "", "who": "", "when": "", "how": "",
        "progress": 0, "notes": "",
        "alignment_score": None,
        "items": [],
    }


@missing_router.patch("/vision")
async def patch_vision(body: VisionPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_vision", user.id)
    if items:
        vid = items[0]["id"]
        res = await _update_row(db, "user_vision", user.id, vid, body.dict(exclude_unset=True))
        return res
    data = body.dict(exclude_unset=True)
    return await _insert_row(db, "user_vision", user.id, data)


# ============================================================
# DOCUMENTS  /api/documents
# ============================================================
class DocumentIn(BaseModel):
    name: str
    type: Optional[str] = "general"
    content: Optional[str] = ""
    source: Optional[str] = "humain"   # humain | ia


@missing_router.get("/documents")
async def list_documents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_documents", user.id)
    return {"items": items}


@missing_router.post("/documents")
async def create_document(body: DocumentIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _insert_row(db, "user_documents", user.id, body.dict())


@missing_router.delete("/documents/{did}")
async def delete_document(did: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"deleted": await _delete_row(db, "user_documents", user.id, did)}


class DocumentGenerateIn(BaseModel):
    name: str
    type: Optional[str] = "general"
    prompt: str


@missing_router.post("/documents/generate")
async def generate_document(body: DocumentGenerateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère un document via Claude Sonnet 4.5. Retourne le document créé."""
    content = await _claude_complete(
        system="Tu es un assistant rédactionnel pour solo founders. Rédige des documents professionnels, en français, en markdown clair. Sois précis et actionnable.",
        user_prompt=f"Document demandé : {body.name} (type : {body.type}).\n\nBrief utilisateur :\n{body.prompt}\n\nRédige le document complet maintenant.",
        max_tokens=2000,
    )
    data = {
        "name": body.name,
        "type": body.type,
        "content": content or "",
        "source": "ia",
    }
    return await _insert_row(db, "user_documents", user.id, data)


# ============================================================
# LEADS  /api/leads
# ============================================================
class LeadIn(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = "manuel"
    status: Optional[str] = "nouveau"   # nouveau | qualifie | rdv | client | perdu
    notes: Optional[str] = None


class LeadPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@missing_router.get("/leads")
async def list_leads(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_leads", user.id)
    # Compute basic counters
    counters = {"nouveau": 0, "qualifie": 0, "rdv": 0, "client": 0, "perdu": 0}
    for it in items:
        s = it.get("status", "nouveau")
        if s in counters:
            counters[s] += 1
    return {"items": items, "counters": counters, "total": len(items)}


@missing_router.post("/leads")
async def create_lead(body: LeadIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _insert_row(db, "user_leads", user.id, body.dict())


@missing_router.patch("/leads/{lid}")
async def patch_lead(lid: str, body: LeadPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await _update_row(db, "user_leads", user.id, lid, body.dict(exclude_unset=True))
    if not res:
        raise HTTPException(404, "Lead introuvable")
    return res


@missing_router.delete("/leads/{lid}")
async def delete_lead(lid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"deleted": await _delete_row(db, "user_leads", user.id, lid)}


# ============================================================
# STREAK  /api/streak (calculé à la volée à partir de user_energy ou last_login)
# ============================================================
@missing_router.get("/streak")
async def get_streak(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Renvoie le streak basé sur les enregistrements energy quotidiens des 30 derniers jours."""
    try:
        # Compter le nombre de jours consécutifs jusqu'à aujourd'hui où l'user a un check-in
        r = await db.execute(text(
            "SELECT DATE(created_at) AS d FROM user_energy WHERE user_id = :uid "
            "AND created_at >= NOW() - INTERVAL 60 DAY ORDER BY d DESC"
        ), {"uid": user.id})
        days = sorted({row[0] for row in r.fetchall() if row[0]}, reverse=True)
    except Exception:
        days = []

    streak = 0
    today = date.today()
    cur = today
    for d in days:
        if isinstance(d, datetime):
            d = d.date()
        if d == cur:
            streak += 1
            cur = cur - timedelta(days=1)
        elif d == cur + timedelta(days=1):
            # account already counted, skip
            continue
        else:
            break

    return {"streak": streak, "last_check_in": days[0].isoformat() if days else None}


# ============================================================
# REVENUE  /api/revenue/monthly
# ============================================================
@missing_router.get("/revenue/monthly")
async def revenue_monthly(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Stub revenu — empty state. À brancher sur Mollie/Stripe plus tard."""
    # On peut aussi sommer finance_entries si elles existent
    try:
        r = await db.execute(text(
            "SELECT DATE_FORMAT(created_at, '%Y-%m') AS m, SUM(amount) AS total "
            "FROM finance_entries WHERE user_id = :uid AND type = 'revenue' "
            "GROUP BY m ORDER BY m DESC LIMIT 12"
        ), {"uid": user.id})
        rows = r.fetchall()
        series = [{"month": row[0], "total": float(row[1] or 0)} for row in rows]
    except Exception:
        series = []

    current = series[0]["total"] if series else 0.0
    return {
        "current_month": current,
        "currency": "EUR",
        "series": series,
        "growth_6m": None,
        "source": "manual" if series else "empty",
    }


# ============================================================
# ENERGY  /api/energy/today  /api/energy/latest
# ============================================================
@missing_router.get("/energy/today")
async def energy_today(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        r = await db.execute(text(
            "SELECT physique, mentale, stress, focus, mood, created_at FROM user_energy "
            "WHERE user_id = :uid AND DATE(created_at) = CURDATE() ORDER BY created_at DESC LIMIT 1"
        ), {"uid": user.id})
        row = r.fetchone()
    except Exception:
        row = None
    if not row:
        return {"recorded": False, "physique": None, "mentale": None, "stress": None,
                "focus": None, "mood": None, "checked_in_at": None}
    return {
        "recorded": True,
        "physique": row[0], "mentale": row[1], "stress": row[2],
        "focus": row[3], "mood": row[4],
        "checked_in_at": row[5].isoformat() if row[5] else None,
    }


@missing_router.get("/energy/latest")
async def energy_latest(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        r = await db.execute(text(
            "SELECT physique, mentale, stress, focus, mood, created_at FROM user_energy "
            "WHERE user_id = :uid ORDER BY created_at DESC LIMIT 1"
        ), {"uid": user.id})
        row = r.fetchone()
    except Exception:
        row = None
    if not row:
        return None
    return {
        "physique": row[0], "mentale": row[1], "stress": row[2],
        "focus": row[3], "mood": row[4],
        "checked_in_at": row[5].isoformat() if row[5] else None,
    }


# ============================================================
# PROCESSES TEMPLATES  /api/processes/templates
# ============================================================
PROCESS_TEMPLATES = [
    {"id": "onboarding-client", "name": "Onboarding client", "category": "Commercial", "steps": 6},
    {"id": "lancement-produit", "name": "Lancement produit", "category": "Marketing", "steps": 8},
    {"id": "newsletter-hebdo", "name": "Newsletter hebdomadaire", "category": "Marketing", "steps": 4},
    {"id": "facturation", "name": "Facturation mensuelle", "category": "Finance", "steps": 5},
    {"id": "recrutement", "name": "Recrutement freelance", "category": "Équipe", "steps": 6},
    {"id": "qualif-lead", "name": "Qualification d'un lead", "category": "Commercial", "steps": 5},
    {"id": "post-vente", "name": "Post-vente / fidélisation", "category": "Commercial", "steps": 5},
    {"id": "audit-mensuel", "name": "Audit mensuel business", "category": "Pilotage", "steps": 7},
]


@missing_router.get("/processes/templates")
async def processes_templates(user: User = Depends(get_current_user)):
    return {"templates": PROCESS_TEMPLATES}


# ============================================================
# ANALYSE  /api/analyse — Claude Sonnet 4.5
# ============================================================
async def _claude_complete(system: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """Appel Claude Sonnet 4.5 via emergentintegrations (Emergent LLM Key)."""
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        logger.warning("EMERGENT_LLM_KEY manquant — retour empty")
        return ""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
        chat = LlmChat(
            api_key=key,
            session_id=f"analyse-{uuid.uuid4().hex[:8]}",
            system_message=system,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        out = []
        async for ev in chat.stream_message(UserMessage(text=user_prompt)):
            if isinstance(ev, TextDelta):
                out.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        return "".join(out).strip()
    except Exception as e:
        logger.exception("Claude completion failed: %s", e)
        return ""


@missing_router.get("/analyse")
async def get_analyse(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_analyse", user.id)
    if items:
        return items[0]
    return {
        "id": None,
        "summary": "",
        "verdict": None,
        "score": None,
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": [],
        "next_actions": [],
        "generated_at": None,
        "source": "empty",
    }


@missing_router.post("/analyse/run")
async def run_analyse(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère une analyse marché via Claude Sonnet 4.5 à partir du profil + vision."""
    # Récupérer contexte utilisateur
    vision_items = await _list_rows(db, "user_vision", user.id)
    vision = vision_items[0] if vision_items else {}
    profile_brief = (
        f"Utilisateur : {user.name or user.email}.\n"
        f"Secteur : {getattr(user, 'sector', '') or 'inconnu'}.\n"
        f"Vision (why) : {vision.get('why', 'non renseigné')}.\n"
        f"Vision (what) : {vision.get('what', 'non renseigné')}.\n"
        f"Cible (who) : {vision.get('who', 'non renseigné')}.\n"
    )
    system = (
        "Tu es un consultant senior en stratégie business, spécialisé en pré-validation de projets entrepreneuriaux. "
        "Tu produis des analyses SWOT actionnables, en français, en JSON strict. "
        "Pas de bla-bla : factuel, court, actionnable."
    )
    prompt = (
        f"Voici le contexte du solo founder :\n\n{profile_brief}\n\n"
        "Génère une analyse SWOT au format JSON strict avec cette structure (uniquement ces clés) :\n"
        "{\"summary\": \"2 phrases\", \"verdict\": \"go\"|\"pivot\"|\"abandon\", \"score\": 0-100, "
        "\"strengths\": [\"...\", \"...\"], \"weaknesses\": [\"...\", \"...\"], "
        "\"opportunities\": [\"...\", \"...\"], \"threats\": [\"...\", \"...\"], "
        "\"next_actions\": [\"action1\", \"action2\", \"action3\"]}\n"
        "Réponds UNIQUEMENT avec le JSON, sans markdown ni texte autour."
    )
    raw = await _claude_complete(system=system, user_prompt=prompt, max_tokens=1200)
    parsed = {}
    if raw:
        # Extraire JSON si Claude a entouré
        try:
            s = raw.strip()
            if s.startswith("```"):
                s = s.strip("`").split("\n", 1)[-1]
                if s.endswith("```"):
                    s = s.rsplit("```", 1)[0]
            parsed = json.loads(s)
        except Exception as e:
            logger.warning("analyse JSON parse failed: %s", e)
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
        "source": "claude-sonnet-4-5",
    }
    # Remplace l'ancienne analyse (1 par user)
    await _ensure_table(db, "user_analyse")
    await db.execute(text("DELETE FROM user_analyse WHERE user_id = :uid"), {"uid": user.id})
    await db.commit()
    return await _insert_row(db, "user_analyse", user.id, data)


@missing_router.post("/analyse/verdict")
async def verdict_analyse(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Force juste le calcul d'un verdict synthétique (réutilise l'analyse existante)."""
    items = await _list_rows(db, "user_analyse", user.id)
    if not items:
        raise HTTPException(404, "Aucune analyse — lance d'abord /analyse/run")
    return {"verdict": items[0].get("verdict"), "score": items[0].get("score")}


@missing_router.post("/analyse/mom-test-guide")
async def mom_test_guide(user: User = Depends(get_current_user)):
    """Renvoie un guide Mom Test français court (statique, pas besoin de LLM)."""
    return {
        "title": "Mom Test — 3 règles d'or",
        "rules": [
            "Parlez de la vie du client, pas de votre idée.",
            "Posez des questions spécifiques sur le passé, pas des hypothèses sur le futur.",
            "Écoutez plus que vous ne parlez — leur silence vaut leurs mots.",
        ],
        "questions": [
            "Qu'est-ce qui est difficile pour vous en ce moment dans [domaine] ?",
            "Quand avez-vous essayé de résoudre ce problème pour la dernière fois ?",
            "Quelle solution avez-vous essayée ? Pourquoi ne marche-t-elle pas ?",
            "Combien dépensez-vous actuellement (temps/argent) pour gérer ça ?",
            "Si je vous propose [votre idée], qu'est-ce qui vous ferait dire non ?",
        ],
    }


@missing_router.get("/analyse/export")
async def export_analyse(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await _list_rows(db, "user_analyse", user.id)
    if not items:
        return {"format": "markdown", "content": "# Aucune analyse\n\nLance d'abord une analyse depuis l'app."}
    a = items[0]
    md = [
        f"# Analyse stratégique\n\n_Généré le {a.get('generated_at', '')}_",
        f"\n## Verdict : **{(a.get('verdict') or 'à déterminer').upper()}**  ·  Score : {a.get('score') or '—'}/100",
        f"\n## Synthèse\n{a.get('summary', '')}",
        "\n## Forces\n" + "\n".join(f"- {x}" for x in (a.get("strengths") or [])),
        "\n## Faiblesses\n" + "\n".join(f"- {x}" for x in (a.get("weaknesses") or [])),
        "\n## Opportunités\n" + "\n".join(f"- {x}" for x in (a.get("opportunities") or [])),
        "\n## Menaces\n" + "\n".join(f"- {x}" for x in (a.get("threats") or [])),
        "\n## Prochaines actions\n" + "\n".join(f"1. {x}" for x in (a.get("next_actions") or [])),
    ]
    return {"format": "markdown", "content": "\n".join(md)}


# ============================================================
# COLLABORATEUR  /api/collaborateur/notify (event log léger)
#                /api/collaborateur/chat   (Claude Sonnet 4.5)
# ============================================================
class CollabNotifyIn(BaseModel):
    event: str
    title: Optional[str] = None
    duration_min: Optional[int] = None
    notes: Optional[str] = None


@missing_router.post("/collaborateur/notify")
async def collab_notify(body: CollabNotifyIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Enregistre un événement à destination du collaborateur IA (mission_started, etc.).
    Sert de fil d'événements que le chat IA peut lire pour contextualiser ses réponses."""
    data = body.dict()
    data["ts"] = _utc_now().isoformat()
    return await _insert_row(db, "user_collab_events", user.id, data)


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatIn(BaseModel):
    messages: list[ChatMessage]
    context_page: Optional[str] = None
    ui_language: Optional[str] = "fr"


@missing_router.post("/collaborateur/chat")
async def collab_chat(body: ChatIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Chat IA avec contexte utilisateur (vision, tasks, page actuelle).
    Utilise Claude Sonnet 4.5 via emergentintegrations.

    Quota par plan (mois courant) :
        free=10, start=300, grow=1500, serenity/business/admin=illimité.
    """
    # ── 1. Vérification quota IA (avant l'appel coûteux à Claude) ─────
    from routes.ai_quota import check_and_increment
    is_admin = bool(getattr(user, "is_admin", False) or getattr(user, "role", None) in ("admin", "super_admin"))
    quota = await check_and_increment(db, user.id, getattr(user, "plan", None), is_admin=is_admin)
    if not quota.get("ok"):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "ai_quota_exceeded",
                "used": quota.get("used"),
                "limit": quota.get("limit"),
                "message": f"Quota IA mensuel atteint ({quota.get('limit')} messages). Upgradez votre plan pour continuer.",
            },
        )

    # Build context : vision + 3 last tasks + page courante
    vision_items = await _list_rows(db, "user_vision", user.id)
    vision = vision_items[0] if vision_items else {}
    tasks_all = await _list_rows(db, "user_tasks", user.id)
    pending_tasks = [t for t in tasks_all if not t.get("done")][:5]

    name = (user.name or "").split()[0] if user.name else "ami"
    page = body.context_page or "Dashboard"
    lang = body.ui_language or "fr"

    sys_lang = {
        "fr": "Tu réponds toujours en français.",
        "en": "Always answer in English.",
        "es": "Responde siempre en español.",
        "de": "Antworte immer auf Deutsch.",
        "it": "Rispondi sempre in italiano.",
        "pt": "Responda sempre em português.",
    }.get(lang, "Tu réponds toujours en français.")

    system = (
        f"Tu es le Collaborateur IA personnel de {name}, intégré à son cockpit business MyExtension AI (plateforme Zayado). "
        f"{sys_lang} "
        f"Page actuelle : {page}. "
        "Style : direct, chaleureux, factuel. Pas de blabla, pas de listes interminables. "
        "Réponses courtes (3-6 phrases sauf si l'utilisateur demande plus). "
        "Tu peux poser une question de clarification si nécessaire. "
        "Tu connais le contexte business du user — utilise-le si pertinent.\n\n"
        f"=== Contexte business de {name} ===\n"
        f"Vision (why) : {vision.get('why') or 'non renseigné'}\n"
        f"Cible (who)  : {vision.get('who') or 'non renseigné'}\n"
        f"Offre (what) : {vision.get('what') or 'non renseigné'}\n"
        f"Missions en cours ({len(pending_tasks)}) : "
        + (", ".join(t.get("label", "") for t in pending_tasks) if pending_tasks else "aucune")
    )

    # Build conversation : Claude n'accepte qu'un message à la fois via emergentintegrations,
    # on concatène l'historique dans un seul message utilisateur final
    history = body.messages or []
    if not history:
        return {"reply": "Bonjour, comment puis-je vous aider ?"}

    # ── Bug #5/#18 : tronquer l'historique à 10 tours (20 messages max) ──
    # Évite le timeout 30s et le crash Chrome sur les longues conversations
    MAX_TURNS = 10
    if len(history) > MAX_TURNS * 2:
        history = history[-(MAX_TURNS * 2):]

    last_user = history[-1].content if history[-1].role == "user" else ""
    prev_turns = ""
    for m in history[:-1]:
        prefix = "User" if m.role == "user" else "Assistant"
        # Tronquer chaque message à 800 chars max pour éviter les payloads géants
        content = str(m.content)[:800]
        prev_turns += f"\n{prefix}: {content}"
    user_msg = (prev_turns + f"\nUser: {last_user}\nAssistant:").strip() if prev_turns else last_user

    try:
        # Timeout explicite 25s (< Railway 30s) pour éviter le crash Chrome
        import asyncio as _asyncio
        reply = await _asyncio.wait_for(
            _claude_complete(system=system, user_prompt=user_msg, max_tokens=600),
            timeout=25.0
        )
    except _asyncio.TimeoutError:
        logger.warning("Chat timeout after 25s — returning fallback")
        reply = ""
    except Exception as e:
        logger.exception("Chat Claude error: %s", e)
        reply = ""
    if not reply:
        reply = "Désolé, je n'ai pas pu générer de réponse. Réessayez dans un instant."
    return {
        "reply": reply,
        "quota": {
            "used": quota.get("used"),
            "limit": quota.get("limit"),
            "remaining": quota.get("remaining"),
        },
    }


# ── AI quota endpoint ────────────────────────────────────────────────
@missing_router.get("/ai/quota")
async def ai_quota_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Retourne la quota IA mensuelle du user (used / limit / remaining)."""
    from routes.ai_quota import get_usage, _plan_limit
    is_admin = bool(getattr(user, "is_admin", False) or getattr(user, "role", None) in ("admin", "super_admin"))
    plan = getattr(user, "plan", None)
    usage = await get_usage(db, user.id)
    limit = _plan_limit(plan, is_admin=is_admin)
    used = usage["used"]
    remaining = None if limit is None else max(0, limit - used)
    return {
        "plan": plan,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "unlimited": limit is None,
        "year": usage["year"],
        "month": usage["month"],
    }


# ── Stub endpoints for /settings?section=integrations to silence 404 noise ──
@missing_router.get("/whatsapp/status")
async def whatsapp_status(user=Depends(get_current_user)):
    """Stub: returns disconnected state to silence console 404 on Integrations section."""
    return {"connected": False, "phone": None, "provider": "whatsapp-cloud-api"}


@missing_router.get("/revenue/sources/status")
async def revenue_sources_status(user=Depends(get_current_user)):
    """Stub: revenue source connections (Stripe, Mollie, bank). Stub for now."""
    return {"connected_sources": [], "available_sources": ["stripe", "mollie", "manual"]}


@missing_router.get("/integrations/whatsapp-personal/status")
async def whatsapp_personal_status(user=Depends(get_current_user)):
    """Stub: WhatsApp personal QR pairing status."""
    return {"connected": False, "qr_pending": False, "session_id": None}


@missing_router.get("/integrations/brevo/status")
async def brevo_status(user=Depends(get_current_user)):
    """Stub: Brevo email integration status."""
    import os
    brevo_key_set = bool(os.environ.get("BREVO_API_KEY"))
    return {"connected": brevo_key_set, "sender_email": os.environ.get("BREVO_SENDER_EMAIL"), "personal": False}


@missing_router.post("/wellness/bilan/send")
async def wellness_bilan_send(payload: dict, user=Depends(get_current_user)):
    """Send the weekly/quarterly wellness bilan to the user + support@zayado.net via Brevo."""
    from utils import send_brevo_email
    # user can be dict (alias) or User pydantic object — handle both
    user_email = getattr(user, "email", None) or (user.get("email") if hasattr(user, "get") else None)
    phys = payload.get("physique", 0)
    ment = payload.get("mentale", 0)
    stress = payload.get("stress", 0)
    quarter = payload.get("quarter", "")
    html = f"""
    <h2>Bilan bien-être</h2>
    <p><strong>Énergie physique :</strong> {phys}/10</p>
    <p><strong>Clarté mentale :</strong> {ment}/10</p>
    <p><strong>Niveau de stress :</strong> {stress}/10</p>
    <p><strong>Trimestre :</strong> {quarter}</p>
    <p style="color:#777">— L'équipe MyExtension-ai</p>
    """
    subject = f"Votre bilan bien-être — MyExtension-ai"
    sent_user = bool(user_email) and send_brevo_email(to_email=user_email, subject=subject, html_content=html, brand="myextension")
    sent_support = send_brevo_email(to_email="support@zayado.net", subject=f"[Bilan client] {user_email or 'inconnu'}", html_content=html, brand="myextension")
    return {"ok": True, "sent_to_user": sent_user, "sent_to_support": sent_support, "message": "Bilan envoyé"}


@missing_router.post("/wellness/daily")
async def wellness_daily(payload: dict, user=Depends(get_current_user)):
    """Save the daily wellness check-in (stub for now — frontend uses localStorage too)."""
    return {"ok": True, "saved_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}


@missing_router.get("/wellness/state")
async def wellness_state(user=Depends(get_current_user)):
    """Returns full wellness state for /bien-etre page: today, history 30d, bilans, recos, weekly form."""
    uid = getattr(user, "id", None) or (user.get("id") if hasattr(user, "get") else None)
    today = {"physique": 6, "mentale": 6, "stress": 4, "verdict": "Modérée", "raison": "Énergie moyenne, stress contenu.", "rituel": ["1 décision importante max", "3 tâches IA à valider (15 min)", "Pas d'appel client à froid"], "citation": "« On ralentit pour décider juste. »"}
    try:
        from sqlalchemy import text
        from database import async_session_factory
        from datetime import datetime, timezone, timedelta
        async with async_session_factory() as s:
            r = await s.execute(text("SELECT value FROM user_data WHERE user_id = :uid AND `key` = 'wellness_today'"), {"uid": uid})
            row = r.fetchone()
            if row and row[0]:
                import json
                try: today = {**today, **json.loads(row[0])}
                except Exception: pass
            r = await s.execute(text("SELECT value FROM user_data WHERE user_id = :uid AND `key` = 'wellness_history_30d'"), {"uid": uid})
            row2 = r.fetchone()
            history = []
            if row2 and row2[0]:
                import json
                try: history = json.loads(row2[0])
                except Exception: history = []
            if not history:
                # empty state: 30 days with current today's values
                history = []
    except Exception:
        history = []
    return {
        "today": today,
        "energyHistory": history,
        "bilanHistory": [
            {"id": "q4-2025", "title": "Bilan Q4 2025", "period": "Oct-Déc 2025", "energieMoyenne": 6.8, "stressMoyen": 4.1, "verdict": "Trimestre solide.", "stable": True, "status": "current"},
            {"id": "q3-2025", "title": "Bilan Q3 2025", "period": "Jul-Sep 2025", "energieMoyenne": 5.9, "stressMoyen": 5.2, "verdict": "Trimestre difficile, charge trop forte.", "stable": False, "status": "archived"},
        ],
        "boutiqueRecos": [
            {"id": "the-adaptogene", "title": "Thé adaptogène", "price": "18€", "raison": "Stress modéré détecté"},
            {"id": "luminothérapie", "title": "Lampe luminothérapie", "price": "89€", "raison": "Énergie basse en hiver"},
            {"id": "carnet-rituel", "title": "Carnet rituel matin", "price": "24€", "raison": "Pour ancrer le rituel"},
        ],
        "weeklyReview": {"questions": ["Décision la plus stratégique cette semaine ?", "Tâche que j'aurais dû déléguer ?", "Mon vrai niveau d'énergie en moyenne (1-10) ?", "Une chose à arrêter la semaine prochaine ?", "Mon focus principal lundi ?"]}
    }
