"""
kairos.py — Kairos, dimension valeurs (backlog #19).

Ma recommandation, faute de spec fonctionnelle reçue : rester délibérément
simple et non-intrusif, cohérent avec "100% opt-in" posé dans le backlog
d'origine. Ce que je NE fais PAS, volontairement :
  - Pas de détection automatique de "désalignement" entre actions et valeurs
    (ex: analyser le contenu des tâches/messages pour juger si l'utilisateur
    "vit ses valeurs") — je n'ai aucune base fiable pour ce jugement, et le
    faire mal serait intrusif/moralisateur, à l'opposé de l'esprit "douce
    alerte" du backlog.
  - Pas de scoring ("Score Valeurs" façon Score Business) — les valeurs ne
    se réduisent pas à un chiffre, et en fabriquer un serait exactement le
    genre de "fausse mesure" que le reste du produit (score business,
    insights) s'est justement engagé à éviter.

Ce que je fais : l'utilisateur choisit ses valeurs (opt-in explicite,
désactivable à tout moment), et reçoit une notification de réflexion douce
et non jugeante une fois par semaine maximum — un rappel, pas une alerte.
Le contenu de la notification cite ses valeurs telles qu'il les a
formulées, sans interprétation.

Stocké dans User.settings.kairos (réutilise l'endpoint générique
PUT /api/settings déjà existant — pas de nouvel endpoint de sauvegarde).
"""
from datetime import datetime, timezone, timedelta

VALUE_TAGS = [
    "Famille", "Intégrité", "Impact", "Liberté", "Simplicité",
    "Excellence", "Foi", "Communauté", "Créativité", "Sérénité",
]


def get_kairos_settings(user) -> dict:
    k = (user.settings or {}).get("kairos") or {}
    return {
        "enabled": bool(k.get("enabled")),
        "values": k.get("values") or [],
        "values_freetext": k.get("values_freetext") or "",
        "last_nudge_at": k.get("last_nudge_at"),
    }


def should_send_nudge(kairos: dict) -> bool:
    """Au maximum 1 rappel par semaine, et seulement si l'utilisateur a
    vraiment choisi au moins une valeur (pas de rappel vide de sens)."""
    if not kairos.get("enabled"):
        return False
    if not kairos.get("values") and not kairos.get("values_freetext"):
        return False
    last = kairos.get("last_nudge_at")
    if not last:
        return True
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(last)).days >= 7
    except Exception:
        return True


def build_nudge_message(kairos: dict) -> tuple:
    """Renvoie (titre, corps) — cite les valeurs telles que formulées par
    l'utilisateur, sans interprétation ni jugement."""
    values = kairos.get("values") or []
    if values:
        values_str = ", ".join(values[:3])
        body = f"Vos valeurs : {values_str}. Un moment cette semaine pour vérifier que votre cap leur ressemble ?"
    else:
        body = f"« {kairos.get('values_freetext', '').strip()[:120]} » — un moment pour y revenir cette semaine ?"
    return ("Petit rappel Kairos", body)
