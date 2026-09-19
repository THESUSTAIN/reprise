"""
notif_gate.py — "gel" global des notifications pendant une correction/maintenance.

Quand le gel est ACTIF :
  - Toute notification (push web + modales broadcast) est BLOQUÉE globalement.
  - On ne mémorise QUE la DERNIÈRE notification tentée (les précédentes sont
    écrasées) → à la réactivation, une seule notification part (la plus récente),
    pas une avalanche de rattrapage.

État persisté dans admin_config.json (clé `notifications_gate`) pour être lu par
tous les process/consommateurs (push.py, notifications.py).
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from utils import load_admin_config, save_admin_config

logger = logging.getLogger("notif_gate")

_KEY = "notifications_gate"


def _state() -> dict:
    cfg = load_admin_config() or {}
    g = cfg.get(_KEY) or {}
    return {
        "hold": bool(g.get("hold", False)),
        "since": g.get("since"),
        "held_last": g.get("held_last"),
        "blocked_count": int(g.get("blocked_count", 0)),
    }


def get_state() -> dict:
    return _state()


def is_held() -> bool:
    return _state()["hold"]


def set_hold(hold: bool) -> dict:
    cfg = load_admin_config() or {}
    g = cfg.get(_KEY) or {}
    g["hold"] = bool(hold)
    if hold:
        g.setdefault("since", datetime.now(timezone.utc).isoformat())
        g["blocked_count"] = int(g.get("blocked_count", 0))
    else:
        # réactivation : on garde held_last pour que l'appelant puisse le renvoyer,
        # mais on remet le compteur/since à zéro.
        g["since"] = None
        g["blocked_count"] = 0
    cfg[_KEY] = g
    save_admin_config(cfg)
    return _state()


def record_blocked(kind: str, payload: dict) -> None:
    """Mémorise la DERNIÈRE notification bloquée (écrase la précédente)."""
    cfg = load_admin_config() or {}
    g = cfg.get(_KEY) or {}
    g["held_last"] = {"kind": kind, "payload": payload, "at": datetime.now(timezone.utc).isoformat()}
    g["blocked_count"] = int(g.get("blocked_count", 0)) + 1
    cfg[_KEY] = g
    save_admin_config(cfg)


def pop_last() -> Optional[dict]:
    """Récupère et efface la dernière notification bloquée (à renvoyer)."""
    cfg = load_admin_config() or {}
    g = cfg.get(_KEY) or {}
    last = g.get("held_last")
    g["held_last"] = None
    cfg[_KEY] = g
    save_admin_config(cfg)
    return last
