from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="Vision Board Gallery API")
api_router = APIRouter(prefix="/api")


# ---------- Static template catalog (metadata) ----------
TEMPLATES = [
    {
        "id": "pillars",
        "category": "holistic",
        "accent": "#E05A47",
        "name_fr": "Les Piliers de Vie",
        "name_en": "Life Pillars",
        "subtitle_fr": "La Roue de l'Équilibre",
        "subtitle_en": "The Wheel of Balance",
    },
    {
        "id": "roadmap",
        "category": "planning",
        "accent": "#D97706",
        "name_fr": "La Feuille de Route",
        "name_en": "Chronological Roadmap",
        "subtitle_fr": "Roadmap Temporelle Q1–Q4",
        "subtitle_en": "Temporal Roadmap Q1–Q4",
    },
    {
        "id": "identity",
        "category": "mindset",
        "accent": "#8B5CF6",
        "name_fr": "Le Modèle Identitaire",
        "name_en": "The Identity Model",
        "subtitle_fr": "Vision · Mission · Identité",
        "subtitle_en": "Vision · Mission · Identity",
    },
    {
        "id": "sensory",
        "category": "artistic",
        "accent": "#EC4899",
        "name_fr": "Le Moodboard Sensoriel",
        "name_en": "The Sensory Moodboard",
        "subtitle_fr": "Ambiance & Énergie",
        "subtitle_en": "Atmosphere & Energy",
    },
    {
        "id": "strategic",
        "category": "strategic",
        "accent": "#10B981",
        "name_fr": "Le Cockpit Stratégique",
        "name_en": "The Strategic Cockpit",
        "subtitle_fr": "Tableau de Bord Visuel",
        "subtitle_en": "Visual Dashboard",
    },
]


# ---------- Models ----------
class FavoriteToggle(BaseModel):
    session_id: str
    template_id: str


class FavoritesResponse(BaseModel):
    session_id: str
    template_ids: List[str] = Field(default_factory=list)


# ---------- Routes ----------
@api_router.get("/")
async def root():
    return {"message": "Vision Board Gallery API"}


@api_router.get("/templates")
async def get_templates():
    return TEMPLATES


@api_router.get("/favorites/{session_id}", response_model=FavoritesResponse)
async def get_favorites(session_id: str):
    doc = await db.favorites.find_one({"session_id": session_id})
    ids = doc["template_ids"] if doc else []
    return FavoritesResponse(session_id=session_id, template_ids=ids)


@api_router.post("/favorites/toggle", response_model=FavoritesResponse)
async def toggle_favorite(payload: FavoriteToggle):
    doc = await db.favorites.find_one({"session_id": payload.session_id})
    ids = doc["template_ids"] if doc else []
    if payload.template_id in ids:
        ids = [t for t in ids if t != payload.template_id]
    else:
        ids = ids + [payload.template_id]
    await db.favorites.update_one(
        {"session_id": payload.session_id},
        {"$set": {
            "session_id": payload.session_id,
            "template_ids": ids,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    return FavoritesResponse(session_id=payload.session_id, template_ids=ids)


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
