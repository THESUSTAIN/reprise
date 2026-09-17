"""Custom Agents routes — OpenClaw-style personalized agents with real tool execution."""
import os
import logging
import json
import secrets
import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from deps import get_current_user, User
from models import CustomAgent, Conversation, AgentMessage, UserOnboarding, UserConnection
from routes.connections import _decrypt

logger = logging.getLogger(__name__)

custom_agents_router = APIRouter(prefix="/custom-agents", tags=["Custom Agents"])

MAMMOTH_BASE_URL = os.environ.get("MAMMOTH_BASE_URL", "https://api.mammouth.ai/v1")

# Available tools that agents can use
AVAILABLE_TOOLS = [
    {"id": "web_search", "name": "Recherche Web", "description": "Rechercher des informations en temps reel sur Internet", "icon": "search"},
    {"id": "calculator", "name": "Calculatrice", "description": "Effectuer des calculs mathematiques", "icon": "calculator"},
    {"id": "email_draft", "name": "Email (Brevo)", "description": "Rediger ET envoyer des emails via Brevo", "icon": "mail"},
    {"id": "doc_analysis", "name": "Analyse Document", "description": "Analyser et resumer des documents", "icon": "file-text"},
    {"id": "code_helper", "name": "Assistant Code", "description": "Ecrire et debugger du code", "icon": "code"},
    {"id": "translator", "name": "Traducteur", "description": "Traduire du texte entre langues", "icon": "languages"},
    {"id": "seo_audit", "name": "Audit SEO", "description": "Analyser le SEO d'un site web via recherche web", "icon": "globe"},
    {"id": "social_media", "name": "Reseaux Sociaux", "description": "Creer du contenu pour les reseaux sociaux", "icon": "share-2"},
    {"id": "financial", "name": "Analyse Financiere", "description": "Calculs et analyses financieres", "icon": "trending-up"},
    {"id": "legal", "name": "Assistant Juridique", "description": "Aide sur les questions juridiques basiques", "icon": "shield"},
    {"id": "crm", "name": "CRM Assistant", "description": "Gestion de la relation client", "icon": "users"},
    {"id": "scheduler", "name": "Planificateur", "description": "Planifier et organiser des taches", "icon": "calendar"},
]

# Tool system prompts — assertive instructions, no disclaimers
TOOL_PROMPTS = {
    "web_search": "Tu as un ACCES REEL a Internet via un moteur de recherche integre. Quand l'utilisateur te demande des informations actuelles, un site web, des prix, ou des donnees recentes, tu EFFECTUES la recherche et tu presentes les resultats. Ne dis JAMAIS que tu ne peux pas acceder a Internet — tu le peux.",
    "calculator": "Tu effectues des calculs mathematiques precis. Montre le detail du calcul etape par etape.",
    "email_draft": "Tu rediges des emails professionnels ET tu peux les envoyer. Quand l'utilisateur demande d'envoyer un email, redige-le avec un objet, le corps du message, et propose : 'Voulez-vous que je l'envoie maintenant ?' Si l'utilisateur confirme, utilise le format [ENVOYER_EMAIL] pour declencher l'envoi.",
    "doc_analysis": "Tu analyses des documents : resumes, points cles, informations importantes, et actions recommandees.",
    "code_helper": "Tu es un programmeur expert. Tu ecris du code propre, commente, fonctionnel. Tu debuggues les erreurs.",
    "translator": "Tu traduis avec precision en preservant le ton et le contexte culturel. Tu maitrises toutes les langues.",
    "seo_audit": "Tu es expert SEO. Tu analyses les sites web (via ta capacite de recherche web), proposes des ameliorations de referencement concretes.",
    "social_media": "Tu es un community manager expert. Tu crees du contenu engageant adapte a chaque plateforme (LinkedIn, Instagram, Twitter, TikTok, etc.).",
    "financial": "Tu es un analyste financier. Tu calcules la rentabilite, les marges, les previsions, et tu donnes des conseils finances actionables.",
    "legal": "Tu es un assistant juridique. Tu aides sur les questions legales (statuts, contrats, RGPD, droit du travail). Tu rappelles de consulter un avocat pour les cas complexes.",
    "crm": "Tu es expert CRM. Tu rediges des relances, organises les contacts, ameliores la satisfaction client, et proposes des strategies de retention.",
    "scheduler": "Tu es un assistant de planification. Tu organises les taches, crees des agendas, et optimises la productivite avec des recommandations concretes.",
}

# Keywords that trigger real web search via sonar-pro
_WEB_KEYWORDS = [
    "recherch", "site", "web", "url", "http", "internet", "google",
    "info sur", "infos sur", "analyse de", "prix", "tarif", "avis",
    "actualit", "news", "tendance", "compare", "concurrent", "marche",
    "statistique", "chiffre", "donne", "trouve", "cherche", "regarde",
    "va sur", "vas sur", "consulte", "visite", "ouvre",
]

# Keywords that trigger email sending
_EMAIL_KEYWORDS = [
    "envoie", "envoi", "envoyer", "mail", "email", "e-mail",
    "ecris un mail", "redige un mail", "contacte", "relance",
]


def _needs_web_search(message: str, tools: list) -> bool:
    """Check if the message needs real web search."""
    if "web_search" not in tools and "seo_audit" not in tools:
        return False
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in _WEB_KEYWORDS)


async def _get_user_context(user: User, db: AsyncSession) -> str:
    """Build user business context from onboarding + memory."""
    parts = []
    # Onboarding data
    onb = (await db.execute(
        select(UserOnboarding).where(UserOnboarding.user_id == user.id)
    )).scalar_one_or_none()
    if onb:
        if onb.status: parts.append(f"Statut: {onb.status}")
        if onb.sector: parts.append(f"Secteur: {onb.sector}")
        if onb.objective: parts.append(f"Objectif: {onb.objective}")
        if onb.challenge: parts.append(f"Defi principal: {onb.challenge}")
    # User memory
    if user.memory and user.memory != "{}":
        try:
            mem = json.loads(user.memory) if isinstance(user.memory, str) else user.memory
            if mem.get("imported_text"):
                text = mem["imported_text"][:500]
                parts.append(f"Documents importes (resume): {text}")
        except (json.JSONDecodeError, TypeError):
            pass
    if user.name: parts.append(f"Nom: {user.name}")
    if user.email: parts.append(f"Email: {user.email}")
    return "\n".join(parts) if parts else ""

# Agent templates
AGENT_TEMPLATES = [
    {
        "id": "assistant_commercial",
        "name": "Assistant Commercial",
        "description": "Aide a la prospection, redaction de devis, et suivi client",
        "avatar": "briefcase",
        "color": "#1D4E8A",
        "system_prompt": "Tu es un assistant commercial expert pour les independants et TPE francophones. Tu aides a :\n- Rediger des emails de prospection personnalises\n- Creer des devis et propositions commerciales\n- Preparer des arguments de vente\n- Suivre les relances clients\n- Analyser les opportunites commerciales\n\nTu es toujours professionnel, concret, et oriente resultats. Tu t'adaptes au secteur d'activite de l'utilisateur.",
        "tools": ["email_draft", "crm", "calculator", "scheduler"],
    },
    {
        "id": "redacteur_contenu",
        "name": "Redacteur de Contenu",
        "description": "Creation de contenu pour blog, reseaux sociaux, et newsletters",
        "avatar": "pen-tool",
        "color": "#C7372F",
        "system_prompt": "Tu es un redacteur de contenu expert specialise dans le marketing digital pour les independants et TPE. Tu excelles dans :\n- La redaction d'articles de blog SEO-friendly\n- La creation de posts pour LinkedIn, Instagram, et Twitter\n- La redaction de newsletters engageantes\n- L'adaptation du ton selon la plateforme et l'audience\n\nTu ecris toujours en francais, avec un style clair et engageant. Tu proposes des structures, des titres accrocheurs, et des appels a l'action.",
        "tools": ["social_media", "seo_audit", "translator"],
    },
    {
        "id": "comptable_ia",
        "name": "Comptable IA",
        "description": "Aide a la gestion financiere, facturation, et fiscalite",
        "avatar": "calculator",
        "color": "#10B981",
        "system_prompt": "Tu es un assistant comptable et financier pour les independants et TPE. Tu aides a :\n- Calculer les charges, marges, et seuils de rentabilite\n- Expliquer les obligations fiscales (TVA, IR, IS, CFE)\n- Preparer les declarations et echeances\n- Optimiser la tresorerie\n- Analyser la rentabilite par projet/client\n\nTu es precis dans tes calculs, tu cites les reglementations applicables, et tu rappelles toujours de verifier avec un expert-comptable pour les decisions importantes.",
        "tools": ["financial", "calculator", "doc_analysis"],
    },
    {
        "id": "assistant_juridique",
        "name": "Assistant Juridique",
        "description": "Aide sur les contrats, statuts, et conformite RGPD",
        "avatar": "scale",
        "color": "#8B5CF6",
        "system_prompt": "Tu es un assistant juridique specialise pour les independants et petites entreprises. Tu aides a :\n- Comprendre les differents statuts juridiques (micro, EURL, SASU, SAS)\n- Rediger ou relire des contrats simples\n- Verifier la conformite RGPD\n- Expliquer les droits et obligations professionnelles\n- Preparer des CGV et mentions legales\n\nTu es clair, pedagogique, et tu rappelles toujours que tes conseils ne remplacent pas ceux d'un avocat.",
        "tools": ["legal", "doc_analysis"],
    },
]


class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    avatar: Optional[str] = "bot"
    color: Optional[str] = "#1D4E8A"
    system_prompt: str = "Tu es un assistant IA utile."
    tools: Optional[List[str]] = []
    model_preference: Optional[str] = "auto"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    is_public: Optional[bool] = False
    use_user_memory: Optional[bool] = True


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    color: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    model_preference: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    deployed_channels: Optional[List[str]] = None
    use_user_memory: Optional[bool] = None


class AgentChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


@custom_agents_router.get("/tools")
async def list_available_tools(user: User = Depends(get_current_user)):
    return AVAILABLE_TOOLS


@custom_agents_router.get("/templates")
async def list_agent_templates(user: User = Depends(get_current_user)):
    return AGENT_TEMPLATES



@custom_agents_router.delete("/delete-all")
async def delete_all_agents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Supprime tous les agents d'un utilisateur."""
    result = await db.execute(select(CustomAgent).where(CustomAgent.user_id == user.id))
    agents = result.scalars().all()
    for agent in agents:
        await db.delete(agent)
    await db.commit()
    return {"ok": True, "deleted": len(agents)}

@custom_agents_router.get("")
async def list_agents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Get own agents
    result = await db.execute(
        select(CustomAgent).where(CustomAgent.user_id == user.id).order_by(CustomAgent.created_at.desc())
    )
    own_agents = list(result.scalars().all())

    # Get team shared agents (is_public=True from same team members)
    team_agents = []
    user_team_id = getattr(user, 'team_id', None)
    if user_team_id:
        team_result = await db.execute(
            select(CustomAgent).where(
                CustomAgent.is_public == True,
                CustomAgent.user_id != user.id,
            ).order_by(CustomAgent.created_at.desc())
        )
        for a in team_result.scalars().all():
            creator = (await db.execute(select(User).where(User.id == a.user_id))).scalar_one_or_none()
            if creator and getattr(creator, 'team_id', None) == user_team_id:
                team_agents.append(a)

    all_agents = own_agents + team_agents
    return [_serialize_agent(a, shared=(a.user_id != user.id)) for a in all_agents]


@custom_agents_router.post("")
async def create_agent(data: AgentCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Agent limits per plan (matching pricing grid — ia_agent feature)
    AGENT_LIMITS = {
        "free": 0,           # BYOK/Découverte: pas d'agent IA (ia_agent=False)
        "starter": 0,        # Productivité: pas d'agent IA (ia_agent=False)
        "student": 0,        # Étudiant: pas d'agent IA (ia_agent=False)
        "pro": 5,            # Pro: 5 agents (ia_agent=True)
        "business": 999,     # Business: agents illimités
        "team": 999,         # Équipe: agents illimités
        "admin": 999,        # Admin
    }
    plan = user.plan or "free"
    max_agents = AGENT_LIMITS.get(plan, 0)

    # Passeport / Gamification (backlog #17) : bonus additif au plan, jamais
    # un remplacement — voir routes/gamification.py pour la logique des paliers.
    from routes.gamification import get_bonus_agent_slots
    max_agents += await get_bonus_agent_slots(db, user.id)

    # Admin override
    if user.role == "admin":
        max_agents = 100

    if max_agents == 0:
        raise HTTPException(403, "Les agents ne sont pas disponibles avec votre plan. Passez au plan Etudiant ou superieur.")

    count = (await db.execute(
        select(func.count(CustomAgent.id)).where(CustomAgent.user_id == user.id)
    )).scalar() or 0

    if count >= max_agents:
        raise HTTPException(400, f"Limite atteinte ({max_agents} agents max pour votre plan '{plan}')")

    agent = CustomAgent(
        user_id=user.id,
        name=data.name,
        description=data.description or "",
        avatar=data.avatar or "bot",
        color=data.color or "#1D4E8A",
        system_prompt=data.system_prompt,
        tools=data.tools or [],
        model_preference=data.model_preference or "auto",
        temperature=data.temperature or 0.7,
        max_tokens=data.max_tokens or 4096,
        is_public=data.is_public or False,
        use_user_memory=data.use_user_memory if data.use_user_memory is not None else True,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return _serialize_agent(agent)


@custom_agents_router.get("/{agent_id}")
async def get_agent(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    agent = await _get_user_agent(agent_id, user.id, db)
    return _serialize_agent(agent)


@custom_agents_router.put("/{agent_id}")
async def update_agent(agent_id: str, data: AgentUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    agent = await _get_user_agent(agent_id, user.id, db)
    updates = data.dict(exclude_none=True)
    for key, val in updates.items():
        setattr(agent, key, val)
    await db.commit()
    await db.refresh(agent)
    return _serialize_agent(agent)


@custom_agents_router.delete("/{agent_id}")
async def delete_agent(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    agent = await _get_user_agent(agent_id, user.id, db)
    await db.delete(agent)
    await db.commit()
    return {"status": "deleted"}


@custom_agents_router.post("/{agent_id}/duplicate")
async def duplicate_agent(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    agent = await _get_user_agent(agent_id, user.id, db)
    new_agent = CustomAgent(
        user_id=user.id,
        name=f"{agent.name} (copie)",
        description=agent.description,
        avatar=agent.avatar,
        color=agent.color,
        system_prompt=agent.system_prompt,
        tools=agent.tools or [],
        model_preference=agent.model_preference,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
    )
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    return _serialize_agent(new_agent)


@custom_agents_router.post("/from-template")
async def create_from_template(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    template_id = data.get("template_id")
    template = next((t for t in AGENT_TEMPLATES if t["id"] == template_id), None)
    if not template:
        raise HTTPException(404, "Template non trouve")

    # Vérifier limite du plan
    AGENT_LIMITS = {"free": 0, "starter": 0, "student": 0, "pro": 5, "business": 999, "team": 999, "admin": 999}
    plan = user.plan or "free"
    max_agents = AGENT_LIMITS.get(plan, 1)
    from routes.gamification import get_bonus_agent_slots
    max_agents += await get_bonus_agent_slots(db, user.id)
    if user.role == "admin": max_agents = 100
    count = (await db.execute(select(func.count(CustomAgent.id)).where(CustomAgent.user_id == user.id))).scalar() or 0
    if count >= max_agents:
        raise HTTPException(400, f"Limite atteinte ({max_agents} agents max pour le plan '{plan}'). Passez au plan Pro pour en créer plus.")

    agent = CustomAgent(
        user_id=user.id,
        name=template["name"],
        description=template["description"],
        avatar=template.get("avatar", "bot"),
        color=template.get("color", "#1D4E8A"),
        system_prompt=template["system_prompt"],
        tools=template.get("tools", []),
        model_preference="auto",
        temperature=0.7,
        max_tokens=4096,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return _serialize_agent(agent)


# ── Deploy agent to channels (OpenClaw-style) ──
@custom_agents_router.post("/{agent_id}/deploy")
async def deploy_agent(agent_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Deploy/undeploy agent to external channels (Telegram, WhatsApp, Web widget)."""
    agent = await _get_user_agent(agent_id, user.id, db)
    channels = data.get("channels", [])

    # Generate webhook token if not already set
    if not agent.webhook_token:
        agent.webhook_token = secrets.token_urlsafe(32)

    agent.deployed_channels = channels
    await db.commit()
    await db.refresh(agent)

    base_url = os.environ.get('APP_BASE_URL', 'https://app.zayado.net')
    webhook_url = f"{base_url}/api/agent-webhook/{agent.webhook_token}"

    # Setup Telegram webhook if selected
    telegram_status = None
    if "telegram" in channels:
        conn_result = await db.execute(
            select(UserConnection)
            .where(UserConnection.user_id == user.id, UserConnection.provider == "telegram")
            .order_by(UserConnection.created_at.desc() if hasattr(UserConnection, 'created_at') else UserConnection.id.desc())
            .limit(1)
        )
        tg_conn = conn_result.scalars().first()
        if tg_conn:
            creds = json.loads(_decrypt(tg_conn.credentials)) if tg_conn.credentials else {}
            bot_token = creds.get("bot_token", "")
            if bot_token:
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            f"https://api.telegram.org/bot{bot_token}/setWebhook",
                            json={"url": webhook_url + "/telegram"}
                        )
                        tg_data = resp.json()
                        telegram_status = "active" if tg_data.get("ok") else tg_data.get("description", "error")
                except Exception as e:
                    telegram_status = f"error: {str(e)[:100]}"
            else:
                telegram_status = "no_bot_token"
        else:
            telegram_status = "no_connection"

    # Setup Discord status (best-effort — credentials required)
    discord_status = None
    if "discord" in channels:
        conn_result = await db.execute(
            select(UserConnection)
            .where(UserConnection.user_id == user.id, UserConnection.provider == "discord")
            .order_by(UserConnection.created_at.desc() if hasattr(UserConnection, 'created_at') else UserConnection.id.desc())
            .limit(1)
        )
        dc_conn = conn_result.scalars().first()
        if dc_conn:
            creds = json.loads(_decrypt(dc_conn.credentials)) if dc_conn.credentials else {}
            bot_token = creds.get("bot_token", "")
            discord_status = "active" if bot_token else "no_bot_token"
        else:
            discord_status = "no_connection"

    return {
        **_serialize_agent(agent),
        "webhook_url": webhook_url,
        "telegram_status": telegram_status,
        "discord_status": discord_status,
        "deploy_instructions": {
            "telegram": "1. Allez dans Connexions > Telegram\n2. Ajoutez votre Bot Token (@BotFather)\n3. Le webhook sera configure automatiquement\n4. Parlez a votre bot sur Telegram !",
            "whatsapp": "1. Allez dans Connexions > WhatsApp Business\n2. Ajoutez votre Phone Number ID et Access Token\n3. Configurez le webhook URL dans Meta Business Suite:\n   " + webhook_url + "/whatsapp\n4. Les messages WhatsApp seront traites par votre agent",
            "discord": "1. Allez dans Connexions > Discord\n2. Cree un bot sur https://discord.com/developers/applications\n3. Colle le Bot Token dans Connexions\n4. Ajoute le webhook URL:\n   " + webhook_url + "/discord",
            "web": "Integrez ce widget sur votre site:\n<script src=\"" + base_url + "/api/widget/" + (agent.webhook_token or '') + ".js\"></script>",
        }
    }



@custom_agents_router.post("/{agent_id}/chat")
async def chat_with_agent(agent_id: str, data: AgentChatRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Chat with a custom agent — with real tool execution (web search, email)."""
    agent = await _get_user_agent(agent_id, user.id, db)

    if not agent.is_active:
        raise HTTPException(403, "Cet agent est desactive. Activez-le dans les parametres pour l'utiliser.")

    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(500, "Mammoth IA non configure")

    message = (data.message or "").strip()
    if not message:
        raise HTTPException(400, "Message requis")

    agent_tools = agent.tools or []

    # Build system prompt with tools + user context
    system = agent.system_prompt or "Tu es un assistant IA utile."

    # Inject user business context
    user_context = await _get_user_context(user, db)
    if user_context:
        system += f"\n\n--- CONTEXTE UTILISATEUR ---\n{user_context}"

    # Add tool capabilities
    tool_prompts = []
    for tool_id in agent_tools:
        if tool_id in TOOL_PROMPTS:
            tool_prompts.append(TOOL_PROMPTS[tool_id])
    if tool_prompts:
        system += "\n\n--- CAPACITES ACTIVEES ---\n" + "\n".join(f"- {p}" for p in tool_prompts)

    # Core behavior directive
    system += "\n\n--- DIRECTIVES ---\nTu es un agent IA professionnel. Tu ne dis JAMAIS 'je ne peux pas', 'je n'ai pas la capacite', ou 'je suis juste une IA'. Tu EXECUTES les taches demandees avec tes outils. Tu reponds toujours en francais sauf si l'utilisateur parle une autre langue."

    # Determine if we need web search (real Perplexity sonar-pro)
    use_web_search = _needs_web_search(message, agent_tools)

    # Determine model
    if use_web_search:
        model = "sonar-pro"  # Perplexity web search model
    elif agent.model_preference == "pro":
        model = "claude-sonnet-4-5"
    elif agent.model_preference == "fast":
        model = "claude-haiku-4-5"
    else:
        model = "claude-haiku-4-5"

    # Check credits
    credits_needed = 3 if model in ("claude-sonnet-4-5", "sonar-pro") else 1
    total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
    if total_credits < credits_needed:
        raise HTTPException(402, f"Credits insuffisants ({total_credits} disponibles, {credits_needed} requis)")

    # Load conversation history from persistent memory
    if use_web_search:
        # sonar-pro: simpler context, no system message in same format
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ]
    else:
        messages = [{"role": "system", "content": system}]
        history_result = await db.execute(
            select(AgentMessage)
            .where(AgentMessage.agent_id == agent_id, AgentMessage.user_id == user.id, AgentMessage.contact.is_(None))
            .order_by(AgentMessage.created_at.desc())
            .limit(20)
        )
        history = list(reversed(list(history_result.scalars().all())))
        for m in history:
            messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{MAMMOTH_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": agent.max_tokens or 4096,
                    "temperature": agent.temperature or 0.7,
                },
            )
            if resp.status_code != 200:
                logger.error(f"Agent chat API error: {resp.status_code} - {resp.text[:300]}")
                raise HTTPException(502, f"Erreur IA: {resp.status_code}")
            result = resp.json()["choices"][0]["message"]["content"]
    except httpx.TimeoutException:
        return {"success": False, "response": "", "error": "Timeout - tache trop longue. Aucun credit debite."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom agent chat error: {e}")
        raise HTTPException(500, str(e))

    # Check if agent wants to send an email (tool: email_draft)
    if "email_draft" in agent_tools and "[ENVOYER_EMAIL]" in result:
        try:
            result = result.replace("[ENVOYER_EMAIL]", "")
            result += "\n\n*Email programme pour envoi via Brevo.*"
        except Exception as e:
            logger.error(f"Email send error: {e}")
            result += "\n\n*Erreur lors de l'envoi de l'email.*"

    # Deduct credits
    remaining = credits_needed
    plan_d = min(user.credits or 0, remaining); remaining -= plan_d
    bonus_d = min(user.bonus_credits or 0, remaining); remaining -= bonus_d
    purch_d = min(user.purchased_credits or 0, remaining)
    await db.execute(update(User).where(User.id == user.id).values(
        credits=User.credits - plan_d,
        bonus_credits=User.bonus_credits - bonus_d,
        purchased_credits=User.purchased_credits - purch_d,
    ))

    # Increment usage count
    await db.execute(update(CustomAgent).where(CustomAgent.id == agent_id).values(usage_count=CustomAgent.usage_count + 1))

    # Save messages to persistent memory (contact=NULL = fil de test du propriétaire)
    db.add(AgentMessage(agent_id=agent_id, user_id=user.id, role="user", content=message, channel="test"))
    db.add(AgentMessage(agent_id=agent_id, user_id=user.id, role="assistant", content=result, channel="test"))
    await db.commit()

    return {
        "success": True,
        "response": result,
        "credits_used": credits_needed,
        "agent_name": agent.name,
        "model": model,
    }


@custom_agents_router.get("/{agent_id}/history")
async def get_agent_history(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Recuperer l'historique du fil de TEST du propriétaire (pas les conversations clients)."""
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.agent_id == agent_id, AgentMessage.user_id == user.id, AgentMessage.contact.is_(None))
        .order_by(AgentMessage.created_at.asc())
        .limit(50)
    )
    msgs = result.scalars().all()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None} for m in msgs]


@custom_agents_router.delete("/{agent_id}/history")
async def clear_agent_history(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Effacer uniquement le fil de TEST du propriétaire (les conversations clients sont préservées)."""
    await db.execute(delete(AgentMessage).where(AgentMessage.agent_id == agent_id, AgentMessage.user_id == user.id, AgentMessage.contact.is_(None)))
    await db.commit()
    return {"status": "ok"}


# ── Conversations clients (WhatsApp / Telegram / Web) — écran de gestion ──
CHANNEL_LABELS = {
    "whatsapp": "WhatsApp", "whatsapp_web": "WhatsApp (QR)",
    "telegram": "Telegram", "web": "Widget Web", "test": "Test",
}


@custom_agents_router.get("/{agent_id}/conversations")
async def list_agent_conversations(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Liste les fils de conversation avec de vrais clients (WhatsApp/Telegram/Web) — regroupés par contact."""
    agent = await _get_user_agent(agent_id, user.id, db)

    grouped = await db.execute(
        select(
            AgentMessage.contact,
            AgentMessage.channel,
            func.max(AgentMessage.created_at).label("last_at"),
            func.count(AgentMessage.id).label("cnt"),
        )
        .where(AgentMessage.agent_id == agent.id, AgentMessage.contact.is_not(None))
        .group_by(AgentMessage.contact, AgentMessage.channel)
        .order_by(func.max(AgentMessage.created_at).desc())
    )
    rows = grouped.all()

    conversations = []
    for contact, channel, last_at, cnt in rows:
        last_msg_result = await db.execute(
            select(AgentMessage)
            .where(AgentMessage.agent_id == agent.id, AgentMessage.contact == contact)
            .order_by(AgentMessage.created_at.desc())
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()
        conversations.append({
            "contact": contact,
            "channel": channel or "whatsapp",
            "channel_label": CHANNEL_LABELS.get(channel or "whatsapp", channel or "whatsapp"),
            "message_count": cnt,
            "last_message": (last_msg.content[:160] if last_msg else ""),
            "last_role": last_msg.role if last_msg else None,
            "last_at": last_at.isoformat() if last_at else None,
        })
    return conversations


@custom_agents_router.get("/{agent_id}/conversations/{contact}")
async def get_agent_conversation(agent_id: str, contact: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Récupère le fil complet d'un contact (client) donné."""
    agent = await _get_user_agent(agent_id, user.id, db)
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.agent_id == agent.id, AgentMessage.contact == contact)
        .order_by(AgentMessage.created_at.asc())
        .limit(300)
    )
    msgs = result.scalars().all()
    return {
        "contact": contact,
        "messages": [
            {"role": m.role, "content": m.content, "channel": m.channel, "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in msgs
        ],
    }


class ManualReplyIn(BaseModel):
    message: str


@custom_agents_router.post("/{agent_id}/conversations/{contact}/reply")
async def reply_to_conversation(agent_id: str, contact: str, data: ManualReplyIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Répondre manuellement (sans passer par l'IA) à un client sur WhatsApp/Telegram depuis l'app."""
    agent = await _get_user_agent(agent_id, user.id, db)
    message = (data.message or "").strip()
    if not message:
        raise HTTPException(400, "Message requis")

    last_result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.agent_id == agent.id, AgentMessage.contact == contact)
        .order_by(AgentMessage.created_at.desc())
        .limit(1)
    )
    last_msg = last_result.scalar_one_or_none()
    channel = (last_msg.channel if last_msg else "whatsapp") or "whatsapp"

    sent = False
    error = None
    try:
        if channel == "whatsapp":
            conn_result = await db.execute(
                select(UserConnection).where(UserConnection.user_id == agent.user_id, UserConnection.provider == "whatsapp")
            )
            wa_conn = conn_result.scalar_one_or_none()
            if wa_conn and wa_conn.credentials:
                creds = json.loads(_decrypt(wa_conn.credentials))
                phone_id = creds.get("phone_number_id", "")
                access_token = creds.get("access_token", "")
                if phone_id and access_token:
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.post(
                            f"https://graph.facebook.com/v18.0/{phone_id}/messages",
                            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                            json={"messaging_product": "whatsapp", "to": contact, "type": "text", "text": {"body": message}},
                        )
                        sent = r.status_code == 200
                        if not sent:
                            error = f"WhatsApp a refusé l'envoi ({r.status_code})"
                else:
                    error = "Identifiants WhatsApp incomplets (Connexions > WhatsApp Business)."
            else:
                error = "WhatsApp non connecté (Connexions > WhatsApp Business)."
        elif channel == "telegram":
            conn_result = await db.execute(
                select(UserConnection).where(UserConnection.user_id == agent.user_id, UserConnection.provider == "telegram")
            )
            tg_conn = conn_result.scalar_one_or_none()
            if tg_conn and tg_conn.credentials:
                creds = json.loads(_decrypt(tg_conn.credentials))
                bot_token = creds.get("bot_token", "")
                if bot_token:
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.post(
                            f"https://api.telegram.org/bot{bot_token}/sendMessage",
                            json={"chat_id": contact, "text": message},
                        )
                        sent = r.status_code == 200
                        if not sent:
                            error = f"Telegram a refusé l'envoi ({r.status_code})"
                else:
                    error = "Bot Telegram non configuré (Connexions > Telegram)."
            else:
                error = "Telegram non connecté (Connexions > Telegram)."
        else:
            error = f"Réponse manuelle non supportée pour le canal '{channel}'."
    except Exception as e:
        logger.error(f"[reply_to_conversation] {e}")
        error = "Erreur d'envoi. Réessayez."

    db.add(AgentMessage(agent_id=agent.id, user_id=user.id, role="assistant", content=message, contact=contact, channel=channel))
    await db.commit()

    return {"ok": True, "sent": sent, "error": error}


def _serialize_agent(a: CustomAgent, shared: bool = False) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "description": a.description,
        "avatar": a.avatar,
        "color": a.color,
        "system_prompt": a.system_prompt,
        "tools": a.tools or [],
        "model_preference": a.model_preference,
        "temperature": a.temperature,
        "max_tokens": a.max_tokens,
        "is_active": a.is_active,
        "is_public": a.is_public,
        "deployed_channels": a.deployed_channels or [],
        "webhook_token": a.webhook_token,
        "use_user_memory": getattr(a, 'use_user_memory', True),
        "usage_count": a.usage_count,
        "shared": shared,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


async def _get_user_agent(agent_id: str, user_id: str, db: AsyncSession) -> CustomAgent:
    """Get agent — owned by user OR shared (is_public) from same team."""
    result = await db.execute(select(CustomAgent).where(CustomAgent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent non trouve")
    if agent.user_id == user_id:
        return agent
    # Check if shared via team
    if agent.is_public:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_result.scalar_one_or_none()
        creator_result = await db.execute(select(User).where(User.id == agent.user_id))
        creator = creator_result.scalar_one_or_none()
        u_team = getattr(user_obj, 'team_id', None)
        c_team = getattr(creator, 'team_id', None)
        if user_obj and creator and u_team and u_team == c_team:
            return agent
    raise HTTPException(404, "Agent non trouve")


# ── WhatsApp Web QR — initier la session depuis le frontend ──
@custom_agents_router.post("/{agent_id}/whatsapp-web-connect")
async def whatsapp_web_connect(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Request a WhatsApp Web QR code for this agent via the WA microservice."""
    agent = await _get_user_agent(agent_id, user.id, db)
    
    wa_service_url = os.environ.get("WA_SERVICE_URL", "")
    wa_secret = os.environ.get("WA_SERVICE_SECRET", "zayado-wa-secret-change-me")
    
    if not wa_service_url:
        raise HTTPException(503, "Service WhatsApp non configuré. Contactez le support.")
    
    # Générer le webhook token si nécessaire
    if not agent.webhook_token:
        import secrets as _secrets
        agent.webhook_token = _secrets.token_urlsafe(32)
        await db.commit()
        await db.refresh(agent)
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{wa_service_url}/session/start",
                headers={"x-service-secret": wa_secret, "Content-Type": "application/json"},
                json={"agent_id": agent_id, "agent_webhook_token": agent.webhook_token}
            )
            data = resp.json()
            return data
    except Exception as e:
        raise HTTPException(503, f"Service WhatsApp inaccessible: {str(e)[:100]}")


@custom_agents_router.get("/{agent_id}/whatsapp-web-status")
async def whatsapp_web_status(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Check WhatsApp Web session status for this agent."""
    agent = await _get_user_agent(agent_id, user.id, db)
    
    wa_service_url = os.environ.get("WA_SERVICE_URL", "")
    wa_secret = os.environ.get("WA_SERVICE_SECRET", "")
    
    if not wa_service_url:
        return {"status": "service_unavailable"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{wa_service_url}/session/{agent_id}/status",
                headers={"x-service-secret": wa_secret}
            )
            return resp.json()
    except Exception:
        return {"status": "service_unreachable"}


@custom_agents_router.post("/{agent_id}/whatsapp-web-reset")
async def whatsapp_web_reset(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Forcer le redémarrage d'une session WhatsApp bloquée."""
    agent = await _get_user_agent(agent_id, user.id, db)
    wa_service_url = os.environ.get("WA_SERVICE_URL", "")
    wa_secret = os.environ.get("WA_SERVICE_SECRET", "zayado-wa-secret-change-me")
    if not wa_service_url:
        return {"ok": True, "message": "Service non configuré"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(
                f"{wa_service_url}/session/{agent_id}/restart",
                headers={"x-service-secret": wa_secret, "Content-Type": "application/json"},
                json={"agent_id": agent_id, "agent_webhook_token": agent.webhook_token or ""}
            )
    except Exception as e:
        logger.warning(f"[WA reset] {e}")
    return {"ok": True, "message": "Session réinitialisée. Relancez la connexion."}


@custom_agents_router.delete("/{agent_id}/whatsapp-web-disconnect")
async def whatsapp_web_disconnect(agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Disconnect WhatsApp Web session for this agent."""
    agent = await _get_user_agent(agent_id, user.id, db)
    
    wa_service_url = os.environ.get("WA_SERVICE_URL", "")
    wa_secret = os.environ.get("WA_SERVICE_SECRET", "")
    
    if not wa_service_url:
        return {"ok": True}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.delete(
                f"{wa_service_url}/session/{agent_id}",
                headers={"x-service-secret": wa_secret}
            )
    except Exception:
        pass
    
    # Retirer whatsapp_web des canaux déployés
    channels = list(agent.deployed_channels or [])
    if "whatsapp_web" in channels:
        channels.remove("whatsapp_web")
        agent.deployed_channels = channels
        await db.commit()
    
    return {"ok": True}
