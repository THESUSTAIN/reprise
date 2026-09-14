"""
vision_events.py — Flux SSE temps réel du Vision Board (backlog #2, tranche 1).

Remplace le polling `setInterval` côté frontend (VisionBrainPanel, LiveCardsStrip)
par UNE connexion HTTP persistante (Server-Sent Events) par onglet ouvert.

Deux types d'événements poussés :
  - `card_update` : émis IMMÉDIATEMENT par routes/vision_cards.py à la création,
    mise à jour, suppression ou migration d'une VisionCard. Le front n'attend
    plus jusqu'à 60s pour voir une carte apparaître/changer.
  - `tick`         : émis toutes les TICK_SECONDS (même cadence que l'ancien
    polling). Sert de signal "recalcule-toi" pour les données qui ne sont pas
    encore branchées sur ce bus (finance_entries, user_leads, user_tasks…
    modifiées ailleurs dans l'app) — le panneau IA se rafraîchit à réception
    sans que le navigateur ait besoin d'ouvrir une requête toutes les minutes.

Ce que ce module NE fait PAS (honnête, volontaire) :
  - Il ne pousse pas d'event dès qu'une ligne finance_entries / user_leads /
    user_tasks change ailleurs dans l'app (Pilotage, Croissance, Bien-être…) —
    cela nécessiterait d'instrumenter tous les endpoints d'écriture concernés,
    hors scope de cette tranche. Le `tick` périodique couvre ce cas en attendant.
  - Il ne fonctionne correctement qu'en déploiement single-worker (voir
    events_bus.py pour la limitation multi-worker).

Monté sous /api/vision/events.
"""
import asyncio
import json
import logging
import time as _time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from sqlalchemy import select

from database import async_session_factory
from deps import JWT_ALGORITHM, JWT_SECRET, get_current_user
from events_bus import subscribe, unsubscribe
from models import User

logger = logging.getLogger("vision_events")

router = APIRouter(prefix="/api/vision/events", tags=["vision-events"])

HEARTBEAT_SECONDS = 25   # garde la connexion ouverte à travers les proxys/LB
TICK_SECONDS = 60        # même cadence que l'ancien setInterval qu'on remplace
_SSE_TICKET_TTL_SECONDS = 45  # doit juste survivre le temps d'ouvrir la connexion


@router.post("/ticket")
async def issue_sse_ticket(user: User = Depends(get_current_user)):
    """Emet un ticket JWT de tres courte duree (45s), a usage unique pour
    ouvrir la connexion SSE. Correctif signale en QA (mineur, securite) :
    EventSource ne peut pas envoyer de header Authorization, donc le token
    doit voyager dans l'URL — mais y mettre le VRAI token de session (long-
    vecu, meme portee que le compte entier) l'exposait aux logs
    serveur/proxy/historique navigateur. Ce ticket est scope a la seule
    portee "ouvrir le flux SSE" et expire en quelques secondes : meme s'il
    fuit dans un log, la fenetre d'exploitation est quasi nulle."""
    exp = datetime.now(timezone.utc) + timedelta(seconds=_SSE_TICKET_TTL_SECONDS)
    ticket = jwt.encode({"sub": user.id, "purpose": "sse", "exp": exp}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"ticket": ticket, "expires_in": _SSE_TICKET_TTL_SECONDS}


async def _user_from_token(token: str) -> "User | None":
    """Valide un ticket SSE (voir /ticket ci-dessus). N'accepte PAS un token
    de session classique : force le passage par /ticket, pour que seul un
    jeton court et a portee reduite transite dans l'URL du flux SSE."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("purpose") != "sse":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and getattr(user, "is_active", True):
            return user
    return None


@router.get("/stream")
async def stream(request: Request, token: str = Query(..., description="Ticket SSE court (via POST /ticket) — EventSource ne permet pas de header")):
    user = await _user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Ticket invalide ou expire — redemandez-en un via POST /api/vision/events/ticket")

    queue = await subscribe(user.id)
    logger.info("SSE: connexion ouverte pour user %s", user.id)

    async def event_gen():
        last_tick = _time.monotonic()
        try:
            yield "retry: 4000\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                    yield f"event: {item['event']}\ndata: {json.dumps(item['data'])}\n\n"
                except asyncio.TimeoutError:
                    now = _time.monotonic()
                    if now - last_tick >= TICK_SECONDS:
                        last_tick = now
                        yield "event: tick\ndata: {}\n\n"
                    else:
                        yield ": heartbeat\n\n"  # commentaire SSE : garde la connexion vivante
        except asyncio.CancelledError:
            pass
        finally:
            await unsubscribe(user.id, queue)
            logger.info("SSE: connexion fermée pour user %s", user.id)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # nginx : désactive le buffering du flux
        },
    )
