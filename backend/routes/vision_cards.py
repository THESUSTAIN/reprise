"""
vision_cards.py — Modèle de données unifié du Vision Board (backlog #1, tranche 1).

Remplace le double système existant :
  - CanvasElement (blob JSON libre, routes/vision_board.py::/canvas)
  - Live cards codées en dur (routes/vision_board.py::/live-data)

par UNE table `vision_cards` où chaque carte du canvas est un enregistrement
en base, et où une carte "intelligente" référence une entité réelle via
(entity_type, entity_id). Le RESOLVER ci-dessous va chercher la valeur live
dans la table source à CHAQUE lecture : la carte ne peut pas mentir, elle
n'a pas de valeur "cachée" par défaut (le cache n'est qu'un fallback si la
résolution échoue).

Monté sous /api/vision/cards. N'écrase aucune route existante — /canvas et
/live-data restent fonctionnelles pendant la transition (voir /migrate-legacy
pour basculer les données existantes vers ce modèle).
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from events_bus import publish as _publish_event
from models import User, VisionCard

log = logging.getLogger("vision_cards")
router = APIRouter(prefix="/api/vision/cards", tags=["vision-cards"])


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ───────────────────────── Resolver : entity_type -> valeur live ─────────────────────────
# Chaque resolver reçoit (db, user_id, entity_id) et renvoie soit un dict
# {label, value, sub, progress, exists}, soit None si l'entité n'existe plus
# (carte "orpheline" : le front doit le signaler, pas fabriquer une valeur).

async def _resolve_aggregate(db: AsyncSession, uid: str, key: str) -> Optional[Dict[str, Any]]:
    from datetime import datetime as _dt
    month_start = _dt.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if key == "ca_month":
        ca = (await db.execute(
            text("SELECT COALESCE(SUM(amount),0) FROM finance_entries "
                 "WHERE user_id=:uid AND type='revenu' AND date >= :ms"),
            {"uid": uid, "ms": month_start},
        )).scalar() or 0
        objective = (await db.execute(
            text("SELECT amount FROM budget_goals WHERE user_id=:uid "
                 "AND category IN ('ca','revenu','chiffre_affaires') ORDER BY id DESC LIMIT 1"),
            {"uid": uid},
        )).scalar() or 10000
        progress = min(100, round(float(ca) / float(objective) * 100)) if objective else 0
        return {"label": "CA du mois", "value": f"{float(ca):,.0f} €".replace(",", " "),
                "sub": f"Objectif {float(objective):,.0f} €".replace(",", " "), "progress": progress, "exists": True}

    if key == "wellness_latest":
        row = (await db.execute(
            text("SELECT score FROM wellness_checkins WHERE user_id=:uid ORDER BY date DESC LIMIT 1"),
            {"uid": uid},
        )).fetchone()
        score = int(row[0]) if row and row[0] is not None else None
        return {"label": "Bien-être", "value": f"{score}/100" if score is not None else "—",
                "sub": "Dernier check-in", "progress": score or 0, "exists": True}

    if key == "prospects_count":
        n = (await db.execute(text("SELECT COUNT(*) FROM user_leads WHERE user_id=:uid"), {"uid": uid})).scalar() or 0
        return {"label": "Prospects", "value": str(int(n)), "sub": "Pipeline Croissance", "progress": None, "exists": True}

    if key == "impact_estimate":
        n = (await db.execute(text("SELECT COUNT(*) FROM user_leads WHERE user_id=:uid"), {"uid": uid})).scalar() or 0
        actual = int(n) * 812
        goal = 10000
        return {"label": "Impact", "value": f"{actual:,.0f} €".replace(",", " "),
                "sub": f"Objectif {goal:,.0f} €".replace(",", " "), "progress": min(100, round(actual / goal * 100)), "exists": True}

    return None


async def _resolve_finance_entry(db: AsyncSession, uid: str, entity_id: str) -> Optional[Dict[str, Any]]:
    row = (await db.execute(
        text("SELECT label, amount, type, date FROM finance_entries WHERE id=:id AND user_id=:uid"),
        {"id": entity_id, "uid": uid},
    )).fetchone()
    if not row:
        return None
    label, amount, typ, date = row
    return {"label": label, "value": f"{float(amount):,.0f} €".replace(",", " "),
            "sub": "Revenu" if typ == "revenu" else "Dépense", "progress": None, "exists": True}


async def _resolve_budget_goal(db: AsyncSession, uid: str, entity_id: str) -> Optional[Dict[str, Any]]:
    row = (await db.execute(
        text("SELECT category, amount, period FROM budget_goals WHERE id=:id AND user_id=:uid"),
        {"id": entity_id, "uid": uid},
    )).fetchone()
    if not row:
        return None
    category, amount, period = row
    return {"label": f"Objectif {category}", "value": f"{float(amount):,.0f} €".replace(",", " "),
            "sub": f"par {period}", "progress": None, "exists": True}


async def _resolve_lead(db: AsyncSession, uid: str, entity_id: str) -> Optional[Dict[str, Any]]:
    import json as _json
    row = (await db.execute(
        text("SELECT data FROM user_leads WHERE id=:id AND user_id=:uid"),
        {"id": entity_id, "uid": uid},
    )).fetchone()
    if not row or not row[0]:
        return None
    data = row[0] if isinstance(row[0], dict) else _json.loads(row[0])
    name = data.get("name") or data.get("company") or "Prospect"
    score = data.get("score")
    return {"label": name, "value": (f"Score {score}" if score is not None else data.get("status", "—")),
            "sub": data.get("status") or "Pipeline", "progress": score, "exists": True}


async def _resolve_project(db: AsyncSession, uid: str, entity_id: str) -> Optional[Dict[str, Any]]:
    row = (await db.execute(
        text("SELECT name, total_time_seconds, hourly_rate FROM projects WHERE id=:id AND user_id=:uid"),
        {"id": entity_id, "uid": uid},
    )).fetchone()
    if not row:
        return None
    name, seconds, rate = row
    hours = (seconds or 0) / 3600
    return {"label": name, "value": f"{hours:.1f} h", "sub": f"{hours * (rate or 0):,.0f} €".replace(",", " "),
            "progress": None, "exists": True}


_RESOLVERS = {
    "finance_entry": _resolve_finance_entry,
    "budget_goal": _resolve_budget_goal,
    "lead": _resolve_lead,
    "project": _resolve_project,
}


async def resolve_card(db: AsyncSession, uid: str, card: VisionCard) -> Dict[str, Any]:
    """Résout la valeur live d'une carte. Ne renvoie JAMAIS une valeur fabriquée :
    si l'entité n'existe plus, `live=False` et le front doit afficher un état
    "orphelin" (avec le dernier cache connu en fallback informatif seulement)."""
    base = {
        "id": card.id, "card_type": card.card_type, "title": card.title,
        "entity_type": card.entity_type, "entity_id": card.entity_id,
        "x": card.x, "y": card.y, "width": card.width, "height": card.height,
        "rotation": card.rotation, "z": card.z, "style": card.style or {},
        "connections": card.connections or [],
    }

    if not card.entity_type:
        base.update({"live": False, "label": card.title, "value": card.manual_content, "sub": None, "progress": None})
        return base

    resolved = None
    if card.entity_type == "aggregate":
        resolved = await _resolve_aggregate(db, uid, card.entity_id)
    else:
        fn = _RESOLVERS.get(card.entity_type)
        if fn:
            resolved = await fn(db, uid, card.entity_id)

    if resolved is None:
        # Entité supprimée / introuvable : on le dit clairement plutôt que de garder
        # une valeur périmée silencieusement.
        base.update({
            "live": False, "orphan": True,
            "label": card.cache_label or card.title or "Carte liée à une entité supprimée",
            "value": card.cache_value, "sub": "⚠️ entité source introuvable", "progress": card.cache_progress,
        })
        return base

    base.update({"live": True, "label": resolved["label"], "value": resolved["value"],
                 "sub": resolved.get("sub"), "progress": resolved.get("progress")})
    return base


async def _refresh_cache(db: AsyncSession, card: VisionCard, resolved: Dict[str, Any]):
    """Met à jour le cache de fallback (best-effort, ne bloque jamais la lecture)."""
    if not resolved.get("live"):
        return
    card.cache_label = resolved.get("label")
    card.cache_value = resolved.get("value")
    card.cache_progress = resolved.get("progress")
    card.cache_updated_at = datetime.now(timezone.utc)


# ───────────────────────── Schémas ─────────────────────────
class VisionCardIn(BaseModel):
    board_id: str = "main"
    card_type: str = "postit"
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    title: Optional[str] = None
    manual_content: Optional[str] = None
    x: float = 40
    y: float = 40
    width: float = 220
    height: float = 140
    rotation: float = 0
    z: int = 0
    style: dict = Field(default_factory=dict)
    connections: list = Field(default_factory=list)


class VisionCardPatch(BaseModel):
    title: Optional[str] = None
    manual_content: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None
    z: Optional[int] = None
    style: Optional[dict] = None
    connections: Optional[list] = None


# ───────────────────────── Endpoints ─────────────────────────
@router.get("")
async def list_cards(board_id: str = "main", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Liste les cartes du board avec leur valeur live résolue à l'instant T."""
    rows = (await db.execute(
        select(VisionCard).where(VisionCard.user_id == user.id, VisionCard.board_id == board_id)
    )).scalars().all()

    cards = []
    for c in rows:
        resolved = await resolve_card(db, user.id, c)
        await _refresh_cache(db, c, resolved)
        cards.append(resolved)
    await db.commit()
    return {"cards": cards, "updated_at": _utc_now()}


@router.post("")
async def create_card(payload: VisionCardIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if payload.entity_type and payload.entity_type != "aggregate" and payload.entity_type not in _RESOLVERS:
        raise HTTPException(400, f"entity_type inconnu : {payload.entity_type}")
    card = VisionCard(
        user_id=user.id, board_id=payload.board_id, card_type=payload.card_type,
        entity_type=payload.entity_type, entity_id=payload.entity_id,
        title=payload.title, manual_content=payload.manual_content,
        x=payload.x, y=payload.y, width=payload.width, height=payload.height,
        rotation=payload.rotation, z=payload.z, style=payload.style, connections=payload.connections,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    resolved = await resolve_card(db, user.id, card)
    await _publish_event(user.id, "card_update", {"action": "create", "card_id": resolved["id"]})
    return resolved


@router.post("/migrate-legacy")
async def migrate_legacy(board_id: str = "main", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Bascule les données de l'ancien système (canvas libre + live-data codées en dur)
    vers le modèle unifié, sans rien perdre. Idempotent : ne recrée pas de doublons si
    des vision_cards existent déjà pour ce board."""
    existing = (await db.execute(
        text("SELECT COUNT(*) FROM vision_cards WHERE user_id=:uid AND board_id=:b"),
        {"uid": user.id, "b": board_id},
    )).scalar() or 0
    if existing:
        return {"ok": True, "skipped": True, "reason": "vision_cards déjà peuplée pour ce board"}

    created = 0

    # 1) Les 3 cartes live codées en dur -> cartes "aggregate"
    for i, (etype_key, ctype, x) in enumerate([
        ("ca_month", "ca", 40), ("wellness_latest", "impact", 300), ("prospects_count", "client", 560),
    ]):
        db.add(VisionCard(
            user_id=user.id, board_id=board_id, card_type=ctype,
            entity_type="aggregate", entity_id=etype_key,
            x=x, y=40, width=220, height=140, z=i,
        ))
        created += 1

    # 2) L'ancien canvas libre (blob JSON en user_data) -> cartes libres (entity_type=None)
    row = (await db.execute(
        text("SELECT value FROM user_data WHERE user_id=:uid AND \"key\"='vision_board_canvas' LIMIT 1"),
        {"uid": user.id},
    )).fetchone()
    if row and row[0]:
        import json as _json
        data = row[0] if isinstance(row[0], dict) else _json.loads(row[0])
        for el in (data.get("elements") or []):
            db.add(VisionCard(
                user_id=user.id, board_id=board_id, card_type=el.get("type", "postit"),
                entity_type=None, entity_id=None,
                title=None, manual_content=el.get("content"),
                x=el.get("x", 40), y=el.get("y", 40), width=el.get("width", 200), height=el.get("height", 200),
                rotation=el.get("rotation", 0), z=el.get("z", 0),
                style={"color": el.get("color"), "font_size": el.get("font_size"), "src": el.get("src"),
                       "shape": el.get("shape"), "fill": el.get("fill"), "stroke": el.get("stroke")},
            ))
            created += 1

    await db.commit()
    if created:
        await _publish_event(user.id, "card_update", {"action": "migrate", "created": created})
    return {"ok": True, "created": created}


# ───────────────────────── Historique / versioning (backlog #22) ─────────
# Un snapshot capture les champs persistables de chaque VisionCard du board
# à l'instant T. Manuel (bouton "Sauvegarder une version" côté canvas) —
# pas d'auto-snapshot périodique pour ce premier jet, pour éviter
# d'accumuler des versions entre deux sauvegardes explicites sans valeur
# pour l'utilisateur.

_SNAPSHOT_FIELDS = ["card_type", "entity_type", "entity_id", "title", "manual_content",
                     "x", "y", "width", "height", "rotation", "z", "style", "connections"]


def _card_to_snapshot_dict(card: VisionCard) -> dict:
    return {f: getattr(card, f) for f in _SNAPSHOT_FIELDS}


@router.post("/snapshots")
async def create_snapshot(board_id: str = "main", label: Optional[str] = None,
                           user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from models import VisionBoardSnapshot
    cards = (await db.execute(
        select(VisionCard).where(VisionCard.user_id == user.id, VisionCard.board_id == board_id)
    )).scalars().all()
    snap = VisionBoardSnapshot(
        user_id=user.id, board_id=board_id,
        label=label or datetime.now(timezone.utc).strftime("Version du %d/%m/%Y %H:%M"),
        cards_json=[_card_to_snapshot_dict(c) for c in cards],
    )
    db.add(snap)
    await db.commit()
    await db.refresh(snap)
    return {"id": snap.id, "label": snap.label, "created_at": snap.created_at.isoformat(), "card_count": len(snap.cards_json)}


@router.get("/snapshots")
async def list_snapshots(board_id: str = "main", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from models import VisionBoardSnapshot
    rows = (await db.execute(
        select(VisionBoardSnapshot)
        .where(VisionBoardSnapshot.user_id == user.id, VisionBoardSnapshot.board_id == board_id)
        .order_by(VisionBoardSnapshot.created_at.desc())
        .limit(30)
    )).scalars().all()
    return {"snapshots": [
        {"id": s.id, "label": s.label, "created_at": s.created_at.isoformat(), "card_count": len(s.cards_json or [])}
        for s in rows
    ]}


@router.post("/snapshots/{snapshot_id}/restore")
async def restore_snapshot(snapshot_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Remplace l'état actuel du board par celui du snapshot. Les cartes
    actuelles sont supprimées et recréées depuis le snapshot (nouveaux id) —
    plus simple et plus sûr qu'un merge champ par champ, au prix de perdre
    les id existants (sans conséquence : rien côté frontend ne dépend d'un
    id de carte stable entre deux sessions)."""
    from models import VisionBoardSnapshot
    snap = (await db.execute(
        select(VisionBoardSnapshot).where(VisionBoardSnapshot.id == snapshot_id, VisionBoardSnapshot.user_id == user.id)
    )).scalar_one_or_none()
    if not snap:
        raise HTTPException(404, "Version introuvable")

    current = (await db.execute(
        select(VisionCard).where(VisionCard.user_id == user.id, VisionCard.board_id == snap.board_id)
    )).scalars().all()
    for c in current:
        await db.delete(c)

    for card_data in (snap.cards_json or []):
        db.add(VisionCard(user_id=user.id, board_id=snap.board_id, **{k: v for k, v in card_data.items() if k in _SNAPSHOT_FIELDS}))

    await db.commit()
    await _publish_event(user.id, "card_update", {"action": "restore", "snapshot_id": snapshot_id})
    return {"ok": True, "restored": len(snap.cards_json or [])}


@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(snapshot_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from models import VisionBoardSnapshot
    snap = (await db.execute(
        select(VisionBoardSnapshot).where(VisionBoardSnapshot.id == snapshot_id, VisionBoardSnapshot.user_id == user.id)
    )).scalar_one_or_none()
    if not snap:
        raise HTTPException(404, "Version introuvable")
    await db.delete(snap)
    await db.commit()
    return {"ok": True}


# ───────────────────────── Partage public (backlog #23) ──────────────────
# Lien public en lecture seule. Volontairement minimal pour ce premier jet :
# active/désactive + slug, rendu HTML simple côté frontend (pas d'édition,
# pas de commentaires, pas d'export PDF/image — cf. limites documentées
# dans le suivi de tâches). Le slug est aléatoire (pas prévisible), mais ce
# n'est PAS un contrôle d'accès fort : toute personne avec le lien voit les
# vraies données du board (CA, objectifs...) — l'utilisateur doit être
# prévenu avant d'activer, ce que fait le frontend.
import secrets as _secrets


@router.get("/public-status")
async def get_public_status(board_id: str = "main", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        text("SELECT value FROM user_data WHERE user_id=:uid AND \"key\"='vision_board_public'"),
        {"uid": user.id},
    )).fetchone()
    cfg = {}
    if row and row[0]:
        cfg = row[0] if isinstance(row[0], dict) else _json_loads_safe(row[0])
    return {"enabled": bool(cfg.get("enabled")), "slug": cfg.get("slug") if cfg.get("enabled") else None}


def _json_loads_safe(v):
    import json as _json
    try:
        return _json.loads(v)
    except Exception:
        return {}


class PublicToggleIn(BaseModel):
    enabled: bool
    board_id: str = "main"


@router.put("/public-status")
async def set_public_status(body: PublicToggleIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        text("SELECT value FROM user_data WHERE user_id=:uid AND \"key\"='vision_board_public'"),
        {"uid": user.id},
    )).fetchone()
    cfg = {}
    if row and row[0]:
        cfg = row[0] if isinstance(row[0], dict) else _json_loads_safe(row[0])
    slug = cfg.get("slug") or _secrets.token_urlsafe(12)
    new_cfg = {"enabled": body.enabled, "slug": slug, "board_id": body.board_id}
    import json as _json
    new_cfg_json = _json.dumps(new_cfg)
    ts = datetime.now(timezone.utc)
    if row:
        await db.execute(
            text("UPDATE user_data SET value=:v, updated_at=:ts WHERE user_id=:uid AND \"key\"='vision_board_public'"),
            {"v": new_cfg_json, "ts": ts, "uid": user.id},
        )
    else:
        await db.execute(
            text("INSERT INTO user_data (id, user_id, \"key\", value, updated_at) VALUES (:id, :uid, 'vision_board_public', :v, :ts)"),
            {"id": new_uuid_str(), "uid": user.id, "v": new_cfg_json, "ts": ts},
        )
    await db.commit()
    return {"enabled": body.enabled, "slug": slug if body.enabled else None}


def new_uuid_str() -> str:
    import uuid as _uuid
    return str(_uuid.uuid4())


@router.get("/public/{slug}")
async def get_public_board(slug: str, db: AsyncSession = Depends(get_db)):
    """Endpoint PUBLIC (pas d'auth) — lecture seule d'un board partagé."""
    row = (await db.execute(
        text("SELECT user_id, value FROM user_data WHERE \"key\"='vision_board_public'"),
    )).fetchall()
    match = None
    owner_id = None
    for r in row:
        cfg = r[1] if isinstance(r[1], dict) else _json_loads_safe(r[1])
        if cfg.get("enabled") and cfg.get("slug") == slug:
            match = cfg
            owner_id = r[0]
            break
    if not match:
        raise HTTPException(404, "Ce board n'est pas partagé ou le lien n'est plus valide.")

    cards = (await db.execute(
        select(VisionCard).where(VisionCard.user_id == owner_id, VisionCard.board_id == match.get("board_id", "main"))
    )).scalars().all()
    resolved = [await resolve_card(db, owner_id, c) for c in cards]
    # On ne renvoie jamais entity_id/entity_type au public : seulement le rendu visuel.
    safe = [{k: v for k, v in r.items() if k not in ("entity_id", "entity_type")} for r in resolved]
    return {"cards": safe}


# ── Routes paramétrées /{card_id} en dernier (sinon elles masquent les routes littérales) ──
@router.put("/{card_id}")
async def update_card(card_id: str, payload: VisionCardPatch, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = (await db.execute(
        select(VisionCard).where(VisionCard.id == card_id, VisionCard.user_id == user.id)
    )).scalar_one_or_none()
    if not card:
        raise HTTPException(404, "Carte introuvable")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(card, field, value)
    card.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(card)
    resolved = await resolve_card(db, user.id, card)
    await _publish_event(user.id, "card_update", {"action": "update", "card_id": card_id})
    return resolved


@router.delete("/{card_id}")
async def delete_card(card_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = (await db.execute(
        select(VisionCard).where(VisionCard.id == card_id, VisionCard.user_id == user.id)
    )).scalar_one_or_none()
    if not card:
        raise HTTPException(404, "Carte introuvable")
    await db.delete(card)
    await db.commit()
    await _publish_event(user.id, "card_update", {"action": "delete", "card_id": card_id})
    return {"ok": True}
