"""
events_bus.py — Pub/sub léger en mémoire pour le streaming SSE (Vision Board).

Portée volontairement limitée (correction #2, tranche 1) : un `asyncio.Queue`
par connexion SSE ouverte, regroupées par user_id dans un dict en mémoire du
process. Suffisant pour un déploiement single-worker (Uvicorn --workers 1).

Limitation connue et assumée : si l'app tourne en multi-worker (ou plusieurs
instances derrière un load balancer), un événement publié sur le worker A
n'atteint PAS un client SSE connecté au worker B. Lever cette limitation
nécessiterait un broker externe (Redis pub/sub, etc.) — hors scope de cette
tranche, à faire si/quand l'app scale horizontalement.
"""
import asyncio
import logging
from collections import defaultdict
from typing import Dict, Optional, Set

logger = logging.getLogger("vision_events_bus")

_subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
_lock = asyncio.Lock()


async def subscribe(user_id: str) -> asyncio.Queue:
    """Ouvre une nouvelle file d'événements pour ce user_id. maxsize borné :
    si un client ne consomme plus (onglet en arrière-plan, réseau lent), on
    ne veut pas accumuler indéfiniment en mémoire — les plus anciens events
    sont alors droppés au profit des plus récents (voir publish)."""
    q: asyncio.Queue = asyncio.Queue(maxsize=20)
    async with _lock:
        _subscribers[user_id].add(q)
    return q


async def unsubscribe(user_id: str, q: asyncio.Queue) -> None:
    async with _lock:
        _subscribers[user_id].discard(q)
        if not _subscribers[user_id]:
            _subscribers.pop(user_id, None)


async def publish(user_id: str, event: str, data: Optional[dict] = None) -> None:
    """Pousse un événement à toutes les connexions SSE ouvertes de cet
    utilisateur (plusieurs onglets = plusieurs queues, tous notifiés).
    Best-effort et non bloquant : un abonné lent ne doit jamais ralentir
    l'écriture qui déclenche l'event (ex: création d'une VisionCard)."""
    async with _lock:
        queues = list(_subscribers.get(user_id, ()))
    if not queues:
        return
    payload = {"event": event, "data": data or {}}
    for q in queues:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            try:
                q.get_nowait()  # drop le plus ancien
                q.put_nowait(payload)
            except Exception:
                logger.warning("SSE: queue pleine pour user %s, event %s perdu", user_id, event)


def subscriber_count(user_id: str) -> int:
    return len(_subscribers.get(user_id, ()))
