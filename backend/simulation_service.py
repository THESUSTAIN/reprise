"""Service IA du module Simulation (clients virtuels).

Adaptatif à n'importe quel programme (licence, licence pro, bachelor,
master, MBA...) : le programme est un champ texte libre saisi par
l'utilisateur (`programme_label`), l'IA en déduit elle-même le domaine
et calibre clients + tâches en conséquence — pas de logique hardcodée
par diplôme.

Suit exactement le pattern LLM déjà utilisé dans ce repo
(routes/growth_copilote.py) : Emergent LLM Key (Claude) en priorité,
repli Mammouth AI si configuré.
"""

import os
import re
import json
import uuid
import logging

log = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
MAMMOUTH_API_KEY = os.environ.get("MAMMOUTH_API_KEY")


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


async def _llm_json(system: str, user_prompt: str, session_prefix: str) -> dict:
    """Appelle le LLM et parse un JSON. Respecte le réglage admin (auto/mammouth/emergent)."""
    from mammouth_client import get_ai_provider
    provider = get_ai_provider()
    raw = None

    async def _try_emergent():
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"{session_prefix}-{uuid.uuid4().hex[:8]}",
            system_message=system,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        return await chat.send_message(UserMessage(text=user_prompt))

    async def _try_mammouth():
        from mammouth_client import chat as mammouth_chat
        return await mammouth_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}]
        )

    # Ordre selon le provider : mammouth d'abord si "mammouth"/"auto"-avec-Mammouth, sinon Emergent d'abord.
    if provider == "mammouth" and MAMMOUTH_API_KEY:
        try:
            raw = await _try_mammouth()
        except Exception as e:
            log.error("Simulation LLM (Mammouth) échoué : %s", e)
            raw = None
    else:
        # "auto" et "emergent" : Emergent (Claude) en priorité
        if EMERGENT_LLM_KEY:
            try:
                raw = await _try_emergent()
            except Exception as e:
                log.warning("Simulation LLM (Emergent) échoué : %s", e)
                raw = None
        if raw is None and provider != "emergent" and MAMMOUTH_API_KEY:
            try:
                raw = await _try_mammouth()
            except Exception as e:
                log.error("Simulation LLM (Mammouth) échoué aussi : %s", e)
                raw = None

    if not raw:
        raise RuntimeError("Aucun fournisseur LLM disponible (EMERGENT_LLM_KEY / MAMMOUTH_API_KEY manquants ou en échec).")

    try:
        return json.loads(_strip_json_fences(raw))
    except json.JSONDecodeError:
        # Dernier recours : extraire le premier bloc { ... } du texte
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Réponse IA non-JSON : {raw[:300]}")


async def generate_initial_clients(programme_label: str, n: int = 3) -> list[dict]:
    """Génère N clients virtuels calibrés sur le programme déclaré par l'utilisateur.

    Fonctionne pour n'importe quel intitulé (licence, licence pro, bachelor,
    master, MBA, formation courte...) — l'IA infère elle-même le domaine
    (finance, marketing, RH, tech, droit...) à partir du texte libre.
    """
    system = (
        "Tu conçois des simulations pédagogiques réalistes pour de l'apprentissage "
        "par la pratique (experiential learning). Tu réponds UNIQUEMENT en JSON valide, "
        "sans texte avant/après, sans balises markdown."
    )
    prompt = f"""
Programme de l'utilisateur : "{programme_label}"

1. Déduis le domaine principal de ce programme (1-2 mots, ex: "finance", "marketing digital", "ressources humaines").
2. Génère {n} clients virtuels réalistes et variés (secteurs différents, tailles différentes, personnalités différentes)
   dont les problématiques initiales correspondent au domaine déduit — assez concrets pour que quelqu'un qui suit
   ce programme puisse réellement y répondre, sans être triviaux.

Format JSON strict :
{{
  "domain": "...",
  "clients": [
    {{
      "name": "Prénom Nom",
      "industry": "secteur",
      "company_size": "small|mid|large",
      "personality": "demanding|collaborative|difficult|urgent",
      "budget": 12000,
      "initial_problem": "Description concrète du problème initial (2-3 phrases, à la 1ère personne du client)."
    }}
  ]
}}
"""
    data = await _llm_json(system, prompt, "simu-clients")
    data.setdefault("clients", [])
    return data


async def generate_task_for_client(client: dict, domain: str, day: int, previous_task_titles: list[str]) -> dict:
    """Génère la prochaine tâche pour un client, avec escalade de difficulté (jour 1-3 facile → 8+ difficile)."""
    difficulty = min(5, (day // 3) + 1)
    system = (
        "Tu es un client d'entreprise exigeant mais juste, dans un scénario pédagogique. "
        "Tu réponds UNIQUEMENT en JSON valide, sans texte avant/après."
    )
    prompt = f"""
DOMAINE : {domain}
CLIENT : {client['name']} — {client['industry']} ({client['company_size']}), personnalité "{client['personality']}", budget {client['budget']}€
JOUR DE SIMULATION : {day}
DIFFICULTÉ CIBLE : {difficulty}/5
TÂCHES PRÉCÉDENTES (ne pas répéter) : {previous_task_titles[-3:] if previous_task_titles else "aucune"}

Génère UNE demande réaliste de ce client, cohérente avec sa situation et le domaine,
qui force une vraie réflexion (pas de question à réponse évidente).

Format JSON strict :
{{
  "title": "titre court",
  "description": "ce que le client demande, 3-5 phrases, à la 1ère personne",
  "difficulty": {difficulty},
  "key_points": ["point attendu 1", "point attendu 2", "point attendu 3"],
  "rubric": {{"completeness": "...", "accuracy": "...", "business_sense": "..."}}
}}
"""
    return await _llm_json(system, prompt, "simu-task")


async def evaluate_response(task: dict, client: dict, domain: str, user_response: str) -> dict:
    """Évalue la réponse de l'utilisateur : score, feedback pédagogique, réaction du client."""
    system = (
        "Tu es un évaluateur pédagogique exigeant mais bienveillant, et tu incarnes aussi "
        "le client virtuel pour sa réaction. Tu réponds UNIQUEMENT en JSON valide."
    )
    prompt = f"""
DOMAINE : {domain}
CLIENT : {client['name']} ({client['industry']}), personnalité "{client['personality']}"
TÂCHE : {task['title']}
POINTS ATTENDUS : {task.get('key_points', [])}
RUBRIQUE : {json.dumps(task.get('rubric', {}), ensure_ascii=False)}

RÉPONSE DE L'UTILISATEUR :
\"\"\"{user_response.strip()[:4000]}\"\"\"

Évalue sur 10, identifie ce qui est bien et ce qui manque, donne 2-3 axes d'amélioration concrets,
une leçon clé à retenir, et écris la réaction du client (2-3 phrases, cohérente avec sa personnalité :
"demanding"=critique mais juste, "collaborative"=encourageant, "difficult"=challengeant, "urgent"=pressé).

Format JSON strict :
{{
  "score": 7,
  "comments": "...",
  "what_went_well": ["...", "..."],
  "improvements_needed": ["...", "..."],
  "learning_point": "...",
  "client_reaction": "..."
}}
"""
    return await _llm_json(system, prompt, "simu-eval")
