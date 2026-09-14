"""Studio — génération d'images IA (Nano Banana) + vidéos IA (Sora 2)
via la clé Emergent Universal LLM.

Endpoints :
- POST /api/studio/image  → génère une image PNG à partir d'un prompt (+ template preset)
- POST /api/studio/video  → génère une vidéo MP4 à partir d'un prompt (+ template preset)
- GET  /api/studio/quota  → retourne les quotas restants pour l'utilisateur

Metering : plafond mensuel par plan (voir STUDIO_LIMITS), persisté en DB.

──────────────────────────────────────────────────────────────────────────
CORRECTION vs version précédente (ticket #5 + #6 du backlog) :
- Les compteurs vivaient dans `_usage_cache: dict` en RAM → perdus à chaque
  restart backend. Remplacé par une table `studio_usage` (MySQL prod /
  SQLite dev), suivant exactement le même pattern que `routes/ai_quota.py`
  (déjà en prod dans ce repo) : CREATE TABLE IF NOT EXISTS + UPDATE puis
  INSERT si 0 ligne (upsert portable, sans dépendre de ON CONFLICT
  Postgres ni d'une migration Alembic — il n'y en a pas dans ce repo).
- Le plafond gratuit unique (1 image / 1 vidéo pour tout le monde) est
  remplacé par un plafond par plan (STUDIO_LIMITS), sur le modèle de
  PLAN_LIMITS dans ai_quota.py — mêmes clés de plan réelles
  (free / start / trajectoire / grow / serenite / business / admin).
  ⚠️ Les chiffres ci-dessous sont des valeurs de départ à valider côté
  business — seule la mécanique est garantie correcte.
──────────────────────────────────────────────────────────────────────────
"""

import os
import base64
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Literal
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/studio", tags=["studio"])

UPLOADS_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "uploads" / "studio"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────── Quotas persistés par plan (ticket #6) ─────────────────
# None = illimité. Clés alignées sur PLAN_LIMITS de ai_quota.py.
STUDIO_LIMITS = {
    "free":        {"image": 1,  "video": 1},
    "start":       {"image": 5,  "video": 2},
    "trajectoire": {"image": 5,  "video": 2},
    "grow":        {"image": 20, "video": 8},
    "serenite":    {"image": None, "video": None},
    "serenity":    {"image": None, "video": None},
    "business":    {"image": None, "video": None},
    "admin":       {"image": None, "video": None},
}


def _cap_for_user(user: User, kind: str) -> Optional[int]:
    """Plafond mensuel pour ce user/kind. None = illimité."""
    if getattr(user, "role", None) in ("admin", "super_admin"):
        return None
    plan = str(getattr(user, "plan", None) or "free").lower()
    return STUDIO_LIMITS.get(plan, STUDIO_LIMITS["free"]).get(kind)


# ─────────── Persistance quotas (ticket #5) ─────────────────────────
async def _ensure_table(db: AsyncSession):
    await db.execute(text(
        "CREATE TABLE IF NOT EXISTS studio_usage ("
        "user_id VARCHAR(36) NOT NULL, "
        "kind VARCHAR(16) NOT NULL, "
        "year INT NOT NULL, "
        "month INT NOT NULL, "
        "count INT NOT NULL DEFAULT 0, "
        "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "PRIMARY KEY (user_id, kind, year, month))"
    ))


async def _get_used(db: AsyncSession, user_id: str, kind: str) -> int:
    await _ensure_table(db)
    now = datetime.now(timezone.utc)
    try:
        r = await db.execute(
            text(
                "SELECT count FROM studio_usage "
                "WHERE user_id = :uid AND kind = :kind AND year = :y AND month = :m"
            ),
            {"uid": user_id, "kind": kind, "y": now.year, "m": now.month},
        )
        row = r.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        log.warning("studio_usage get_used failed: %s", e)
        return 0


async def _remaining(db: AsyncSession, user: User, kind: str) -> dict:
    cap = _cap_for_user(user, kind)
    used = await _get_used(db, str(user.id), kind)
    remaining = None if cap is None else max(0, cap - used)
    return {"cap": cap, "used": used, "remaining": remaining}


async def _increment(db: AsyncSession, user_id: str, kind: str):
    """Update-puis-insert : upsert portable MySQL/SQLite, sans ON CONFLICT dialecte-spécifique."""
    await _ensure_table(db)
    now = datetime.now(timezone.utc)
    try:
        r = await db.execute(
            text(
                "UPDATE studio_usage SET count = count + 1, updated_at = :ts "
                "WHERE user_id = :uid AND kind = :kind AND year = :y AND month = :m"
            ),
            {"uid": user_id, "kind": kind, "y": now.year, "m": now.month, "ts": now.isoformat()},
        )
        if r.rowcount == 0:
            await db.execute(
                text(
                    "INSERT INTO studio_usage (user_id, kind, year, month, count, updated_at) "
                    "VALUES (:uid, :kind, :y, :m, 1, :ts)"
                ),
                {"uid": user_id, "kind": kind, "y": now.year, "m": now.month, "ts": now.isoformat()},
            )
        await db.commit()
    except Exception as e:
        log.warning("studio_usage increment failed: %s", e)


# ─────────── Templates presets ─────────────────────────────────────
IMAGE_TEMPLATES = {
    "portrait": {
        "label": "Portrait entrepreneur",
        "hint": "Dirigeant confiant, bureau lumineux, casual chic",
        "style": "professional portrait photography, cinematic lighting, shallow depth of field, editorial quality, natural pose",
    },
    "moodboard": {
        "label": "Moodboard aspirationnel",
        "hint": "Vision de succès, ambiance, univers visuel",
        "style": "moodboard collage, elegant magazine editorial, warm and inspiring palette, soft light, high-end lifestyle",
    },
    "avatar-client": {
        "label": "Univers client cible",
        "hint": "Le contexte visuel de votre client idéal",
        "style": "documentary photography, everyday realism, natural light, authentic setting, aspirational lifestyle",
    },
    "brand-universe": {
        "label": "Univers de marque",
        "hint": "Identité visuelle, textures, ambiances",
        "style": "brand mood photography, elegant textures, refined color palette, editorial composition, high-end product photography",
    },
    "aspirational": {
        "label": "Vision aspirationnelle",
        "hint": "Symbolique de succès et de sérénité",
        "style": "aspirational cinematic photography, golden hour light, dreamy atmosphere, symbolic composition, magazine cover quality",
    },
}

VIDEO_TEMPLATES = {
    "manifesto": {
        "label": "Manifesto 4s",
        "hint": "Voici ce que je construis en 2026",
        "prefix": "A cinematic 4-second shot of ",
        "suffix": ", warm color grading, subtle camera motion, editorial style, motivational atmosphere",
        "duration": 4,
        "size": "1280x720",
    },
    "reveal": {
        "label": "Reveal / Coming Soon 4s",
        "hint": "Teaser d'un lancement à venir",
        "prefix": "A cinematic teaser shot of ",
        "suffix": ", dramatic reveal, slow motion, luxurious mood, coming soon feeling",
        "duration": 4,
        "size": "1280x720",
    },
    "vision": {
        "label": "Vision annuelle",
        "hint": "Timeline visuelle de votre parcours",
        "prefix": "A serene cinematic sequence showing ",
        "suffix": ", inspirational tone, golden hour, subtle time-lapse feel",
        "duration": 8,
        "size": "1280x720",
    },
    "citation": {
        "label": "Citation motion",
        "hint": "Ambiance apaisante pour une phrase forte",
        "prefix": "An abstract calming background suitable for a quote: ",
        "suffix": ", gentle motion, soft light, natural elements",
        "duration": 4,
        "size": "1280x720",
    },
}


# ─────────── Schemas ─────────────────────────────────────
class GenerateImageRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=800)
    template: Literal["portrait", "moodboard", "avatar-client", "brand-universe", "aspirational", "custom"] = "custom"


class GenerateVideoRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=800)
    template: Literal["manifesto", "reveal", "vision", "citation", "custom"] = "custom"
    duration: Optional[Literal[4, 8, 12]] = None


class StudioAsset(BaseModel):
    kind: Literal["image", "video"]
    url: str
    prompt: str
    template: str


# ─────────── Endpoints ─────────────────────────────────────
@router.get("/quota")
async def get_quota(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    images = await _remaining(db, user, "image")
    videos = await _remaining(db, user, "video")
    return {
        "images": {"remaining": images["remaining"], "cap": images["cap"]},
        "videos": {"remaining": videos["remaining"], "cap": videos["cap"]},
        "plan": getattr(user, "plan", "free"),
    }


@router.get("/templates")
async def list_templates():
    return {
        "images": [{"id": k, **v} for k, v in IMAGE_TEMPLATES.items()],
        "videos": [{"id": k, **v} for k, v in VIDEO_TEMPLATES.items()],
    }


@router.post("/image", response_model=StudioAsset)
async def generate_image(payload: GenerateImageRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère une image via Mammouth (modèle image, ex. Nano Banana) à partir d'un prompt + preset optionnel."""
    from mammouth_client import generate_image as mammouth_image, MammouthError, MAMMOUTH_API_KEY
    if not MAMMOUTH_API_KEY:
        raise HTTPException(503, "Studio indisponible : MAMMOUTH_API_KEY non configurée.")
    uid = str(user.id)
    quota = await _remaining(db, user, "image")
    if quota["remaining"] is not None and quota["remaining"] <= 0:
        raise HTTPException(429, "Quota mensuel d'images atteint pour votre offre. Passez à l'offre supérieure pour continuer.")

    # Compose final prompt with template style hints
    tpl = IMAGE_TEMPLATES.get(payload.template)
    style_suffix = f", {tpl['style']}" if tpl else ""
    final_prompt = f"{payload.prompt.strip()}{style_suffix}"

    try:
        image_bytes = await mammouth_image(final_prompt, size="1024x1024")
    except MammouthError as e:
        raise HTTPException(502, f"Génération image échouée : {e}")
    except Exception as e:
        log.exception("Mammouth image generation failed")
        raise HTTPException(502, f"Génération image échouée : {e}")

    if not image_bytes:
        raise HTTPException(502, "Aucune image générée.")

    filename = f"img_{uuid.uuid4().hex[:12]}.png"
    filepath = UPLOADS_DIR / filename
    filepath.write_bytes(image_bytes)

    await _increment(db, uid, "image")
    return StudioAsset(kind="image", url=f"/api/uploads/studio/{filename}", prompt=payload.prompt, template=payload.template)


@router.post("/video", response_model=StudioAsset)
async def generate_video(payload: GenerateVideoRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génération vidéo — non disponible via Mammouth (pas d'endpoint text-to-video).

    Conservé pour compatibilité frontend : renvoie 503 explicite tant qu'aucun
    fournisseur vidéo n'est branché.
    """
    raise HTTPException(503, "La génération vidéo IA n'est pas disponible pour le moment.")
