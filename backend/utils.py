"""Shared utilities, constants, and clients for the ZAYADO backend."""
import os
import json
import logging
import re
import time
import threading
from pathlib import Path
from datetime import datetime, timezone

import sib_api_v3_sdk
from mollie.api.client import Client as MollieClient

ROOT_DIR = Path(__file__).parent
CONFIG_PATH = os.path.join(ROOT_DIR, "admin_config.json")
UPLOADS_DIR = os.path.join(ROOT_DIR, "uploads")
GENERATED_IMAGES_DIR = os.path.join(ROOT_DIR, "generated_images")

logger = logging.getLogger("extension_ia")

# ==================== MAMMOTH IA CONFIG ====================
MAMMOTH_BASE_URL = "https://api.mammouth.ai/v1"
AGENT_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
AGENT_COMPLEX_MODEL = "claude-sonnet-4-5"
AGENT_MAX_TIMEOUT = 300

# Crédits Agent IA — recalibrés sur les vrais coûts API (août 2025)
# Coût API réel : haiku ~0.0015-0.004€/tâche, sonnet ~0.03-0.09€/tâche
# Valeur 1 crédit = 0.01€ — marge cible 75-85%
# Crédits Agent IA — 4 niveaux selon la complexité réelle de la tâche
AGENT_CREDITS_MAP = {
    "simple":  60,   # tache simple (~0.50€ par tache) — question, reformulation, traduction
    "medium":  150,  # tache moyenne (~1.50€ par tache) — email, document, analyse simple
    "complex": 300,  # tache complexe (~3.00€ par tache) — rapport, audit, strategie
    "expert":  600,  # tache expert (~6.00€ par tache) — projet complet, business plan, benchmark exhaustif
}

# Sub-agent specializations
AGENT_SPECIALIZATIONS = {
    "research": {
        "keywords": ["recherche", "search", "find", "compare", "benchmark", "analyse marche", "tendance", "concurrent", "competitor"],
        "system": """Tu es l'Agent Recherche ZAYADO — specialise en recherche et analyse approfondie.

MISSION : Mener des recherches structurees, comparer des sources, et livrer des syntheses exploitables.

METHODE DE TRAVAIL :
1. CADRAGE — Reformule l'objectif de recherche et les axes d'investigation
2. COLLECTE — Recherche les donnees pertinentes (web, bases, documents fournis)
3. ANALYSE — Compare, croise les sources, identifie les tendances
4. SYNTHESE — Livre un rapport structure avec sources et recommandations

FORMAT : Rapport structure avec sections, donnees chiffrees, sources citees.
Langue : Detecte et reponds toujours dans la langue de l'utilisateur."""
    },
    "writing": {
        "keywords": ["redige", "ecris", "write", "draft", "email", "article", "contenu", "content", "post", "lettre", "courrier", "redaction"],
        "system": """Tu es l'Agent Redaction ZAYADO — specialise en redaction professionnelle.

MISSION : Produire des contenus de qualite professionnelle, adaptes au contexte et a l'audience.

METHODE DE TRAVAIL :
1. BRIEF — Identifie le type de contenu, l'audience cible et le ton souhaite
2. STRUCTURE — Propose un plan/structure avant la redaction
3. REDACTION — Produit le contenu avec le ton et style adaptes
4. RELECTURE — Verifie la coherence, l'orthographe et la pertinence

FORMAT : Contenu pret a l'emploi, bien structure, professionnel.
Langue : Detecte et reponds toujours dans la langue de l'utilisateur."""
    },
    "code": {
        "keywords": ["code", "develop", "script", "api", "debug", "function", "programme", "algorith", "html", "css", "javascript", "python", "sql"],
        "system": """Tu es l'Agent Code ZAYADO — specialise en developpement et assistance technique.

MISSION : Ecrire du code propre, deboguer, et proposer des solutions techniques optimales.

METHODE DE TRAVAIL :
1. ANALYSE — Comprends le besoin technique et les contraintes
2. CONCEPTION — Propose l'architecture/approche avant de coder
3. IMPLEMENTATION — Ecris le code avec commentaires et bonnes pratiques
4. VALIDATION — Explique le fonctionnement et les points d'attention

FORMAT : Code commente, structure, avec explications claires.
Langue : Detecte et reponds toujours dans la langue de l'utilisateur."""
    },
    "analysis": {
        "keywords": ["analyse", "analyze", "rapport", "report", "diagnostic", "audit", "evaluer", "evaluate", "metriques", "kpi", "performance", "financ"],
        "system": """Tu es l'Agent Analyse ZAYADO — specialise en analyse de donnees et diagnostic.

MISSION : Analyser des donnees, produire des diagnostics et des recommandations actionnables.

METHODE DE TRAVAIL :
1. DONNEES — Collecte et structure les donnees disponibles
2. ANALYSE — Applique des methodes analytiques adaptees
3. DIAGNOSTIC — Identifie les points forts, faiblesses et opportunites
4. RECOMMANDATIONS — Livre des actions concretes et prioritisees

FORMAT : Rapport avec graphiques/tableaux, indicateurs cles, plan d'action.
Langue : Detecte et reponds toujours dans la langue de l'utilisateur."""
    },
    "general": {
        "keywords": [],
        "system": """Tu es l'Agent IA Zayado — agent autonome polyvalent.

MISSION : Executer des taches complexes avec methode et precision.

METHODE DE TRAVAIL :
1. COMPREHENSION — Reformule la demande pour confirmer ta comprehension
2. PLANIFICATION — Decris les etapes que tu vas suivre
3. EXECUTION — Realise chaque etape avec rigueur
4. LIVRAISON — Presente les resultats de maniere structuree

FORMAT : Professionnel, structure, avec faits et chiffres concrets.
Langue : Detecte et reponds toujours dans la langue de l'utilisateur."""
    },
}

def classify_task_type(task: str) -> str:
    task_lower = task.lower()
    # Niveau expert : projet complet, business plan, benchmark exhaustif, etude de marche complete
    expert_kw = [
        "audit complet", "rapport complet", "etude complete", "projet complet",
        "strategie complete", "plan complet", "analyse exhaustive", "benchmark complet",
        "dossier complet", "business plan", "plan d'affaires", "market research",
        "veille concurrentielle complete", "analyse de marche complete",
        "plan de lancement", "etude de faisabilite"
    ]
    # Niveau complex : rapport, audit, synthese multi-sources, strategie
    complex_kw = [
        "rapport", "report", "analyse complete", "multi-sources", "recherche approfondie",
        "comprehensive", "audit", "synthese", "etude", "bilan", "diagnostic",
        "plan strategique", "strategie", "roadmap", "analyse de marche"
    ]
    # Niveau medium : redaction, analyse simple, document, comparaison
    medium_kw = [
        "redaction", "email", "analyse", "document", "resume", "write", "draft",
        "summarize", "recherche", "compare", "comparaison", "liste", "tableau",
        "proposition", "devis", "contrat", "lettre", "article"
    ]
    if any(k in task_lower for k in expert_kw): return "expert"
    if any(k in task_lower for k in complex_kw): return "complex"
    if any(k in task_lower for k in medium_kw): return "medium"
    return "simple"

def classify_agent_specialization(task: str) -> str:
    """Route task to the best sub-agent based on keywords."""
    task_lower = task.lower()
    scores = {}
    for spec, config in AGENT_SPECIALIZATIONS.items():
        if spec == "general":
            continue
        score = sum(1 for kw in config["keywords"] if kw in task_lower)
        if score > 0:
            scores[spec] = score
    if scores:
        return max(scores, key=scores.get)
    return "general"

def get_agent_system_prompt(specialization: str) -> str:
    """Get system prompt for a specific sub-agent."""
    return AGENT_SPECIALIZATIONS.get(specialization, AGENT_SPECIALIZATIONS["general"])["system"]

def estimate_agent_credits(task_type: str) -> int:
    return AGENT_CREDITS_MAP.get(task_type, 50)

def select_agent_model(task_type: str) -> str:
    # Utiliser le modèle complexe pour les tâches complex ET expert
    return AGENT_COMPLEX_MODEL if task_type in ("complex", "expert") else AGENT_DEFAULT_MODEL

def anonymize_for_manus(text: str):
    placeholders = {}
    counter = {"n": 0}
    def replace_match(m, label):
        key = f"[{label}_{counter['n']}]"
        placeholders[key] = m.group()
        counter["n"] += 1
        return key
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', lambda m: replace_match(m, "EMAIL"), text)
    text = re.sub(r'(?:\+33|0033|0)[1-9](?:[\s.-]?\d{2}){4}', lambda m: replace_match(m, "TEL"), text)
    text = re.sub(r'[A-Z]{2}\d{2}[\s]?(?:\d{4}[\s]?){4,7}\d{1,4}', lambda m: replace_match(m, "IBAN"), text)
    text = re.sub(r'\b(?:\d{4}[\s-]?){3}\d{4}\b', lambda m: replace_match(m, "CARTE"), text)
    return text, placeholders

# ==================== MOLLIE CLIENT ====================
_mollie_key = os.environ.get('MOLLIE_API_KEY', '')
if not (_mollie_key and (_mollie_key.startswith('test_') or _mollie_key.startswith('live_'))):
    logger.warning("Mollie API key not configured - payment features disabled")

def get_mollie_client():
    """Create a fresh Mollie client per request to avoid stale TCP connections."""
    client = MollieClient()
    if _mollie_key:
        client.set_api_key(_mollie_key)
    return client

# Backward compat alias
mollie_client = None  # Deprecated: use get_mollie_client() instead

# ==================== OAUTH CONFIG ====================
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')

# ==================== BREVO (EMAIL) ====================
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
brevo_config = sib_api_v3_sdk.Configuration()
brevo_config.api_key['api-key'] = BREVO_API_KEY
brevo_email_api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(brevo_config))
MAIL_FROM_EMAIL = "noreply@zayado.net"
MAIL_FROM_NAME = "Zayado"
# Brand identities — selon le contexte d'envoi
MAIL_BRANDS = {
    "zayado": {
        "email": "noreply@zayado.net",
        "name": "zayado.net",
        "footer_logo": "https://zayado.net/logo.svg",
        "footer_text": "zayado.net — Entreprendre avec sens, clarté et bien-être.",
        "site_url": "https://zayado.net",
    },
    "myextension": {
        "email": "noreply@zayado.net",  # même domaine vérifié Brevo, juste le sender_name change
        "name": "MyExtension-ai by Zayado",
        "footer_logo": "https://zayado.net/logo.svg",
        "footer_text": "MyExtension-ai by Zayado — Votre extension IA. Elle prépare, vous décidez. 70% IA · 30% humain.",
        "site_url": "https://app.zayado.net",
    },
}

def _wrap_brand(html_content: str, brand: str = "zayado") -> str:
    """Ajoute le footer brandé sur les emails (logo + signature)."""
    b = MAIL_BRANDS.get(brand, MAIL_BRANDS["zayado"])
    footer = (
        '<table width="100%" style="margin-top:32px;border-top:1px solid #E8E2D8;padding-top:18px;'
        'font-family:Arial,sans-serif;font-size:12px;color:#777"><tr><td align="left">'
        f'<a href="{b["site_url"]}" style="text-decoration:none;color:#0F1B3D;font-weight:600">{b["footer_text"]}</a>'
        '<br><span style="color:#999">Cet email vous a été envoyé automatiquement, ne répondez pas directement.</span>'
        '</td></tr></table>'
    )
    return f'<div style="font-family:Arial,sans-serif;color:#1a1a1a">{html_content}{footer}</div>'

def send_brevo_email(to_email: str, to_name: str = "", subject: str = "", html_content: str = "", brand: str = "zayado", html: str = None):
    """Send transactional email via Brevo, branded selon le contexte.

    Args:
        brand: 'zayado' (défaut, site public + boutique) ou 'myextension' (app SaaS)
        html: alias pour html_content (rétrocompatibilité)
    """
    if html is not None and not html_content:
        html_content = html
    b = MAIL_BRANDS.get(brand, MAIL_BRANDS["zayado"])
    full_html = _wrap_brand(html_content, brand)
    try:
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email, "name": to_name or to_email.split("@")[0]}],
            sender={"email": b["email"], "name": b["name"]},
            subject=subject,
            html_content=full_html
        )
        response = brevo_email_api.send_transac_email(send_smtp_email)
        logger.info(f"Email[{brand}] sent to {to_email}: {response.message_id}")
        try:
            _append_email_log({"to": to_email, "to_name": to_name, "subject": subject, "brand": brand, "status": "sent", "message_id": str(response.message_id), "sent_at": datetime.now(timezone.utc).isoformat()})
        except Exception:
            pass
        return response.message_id
    except Exception as e:
        logger.error(f"Brevo email error[{brand}]: {str(e)}")
        try:
            _append_email_log({"to": to_email, "to_name": to_name, "subject": subject, "brand": brand, "status": "error", "error": str(e), "sent_at": datetime.now(timezone.utc).isoformat()})
        except Exception:
            pass
        return None

def add_brevo_contact(email: str, first_name: str = "", last_name: str = "", phone: str = "", company: str = "", list_id: int = 20, attributes: dict = None):
    """Add a contact to a Brevo list"""
    try:
        contacts_api = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(brevo_config))
        attrs = {}
        if first_name:
            attrs["FIRSTNAME"] = first_name
            attrs["PRENOM"] = first_name
        if last_name:
            attrs["LASTNAME"] = last_name
            attrs["NOM"] = last_name
        if company:
            attrs["COMPANY"] = company
        if attributes:
            for k, v in attributes.items():
                attrs[k] = v
        contact = sib_api_v3_sdk.CreateContact(
            email=email,
            list_ids=[list_id],
            update_enabled=True
        )
        if attrs:
            contact.attributes = attrs
        contacts_api.create_contact(contact)
        logger.info(f"Brevo contact added: {email} to list {list_id}")
        return True
    except Exception as e:
        error_str = str(e)
        if "duplicate" in error_str.lower() or "already exist" in error_str.lower():
            logger.info(f"Brevo contact already exists: {email}, updating list")
            try:
                contacts_api.update_contact(email, sib_api_v3_sdk.UpdateContact(list_ids=[list_id]))
                return True
            except Exception:
                pass
        logger.error(f"Brevo contact error: {error_str}")
        return False

async def send_low_credits_notification(user):
    """Send Brevo email when user credits are low"""
    try:
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
            <h2 style="color:#1E3A8A;">Credits bientot epuises</h2>
            <p>Bonjour {user.name or 'cher utilisateur'},</p>
            <p>Il vous reste <strong>{(user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)} credits</strong> sur votre compte ZAYADO.</p>
            <p>Pour continuer a utiliser l'assistant IA sans interruption, pensez a recharger vos credits ou passer a un plan superieur.</p>
            <a href="https://app.zayado.net/pricing" style="display:inline-block;padding:12px 24px;background:#1E3A8A;color:white;border-radius:8px;text-decoration:none;font-weight:bold;">Recharger mes credits</a>
        </div>
        """
        send_brevo_email(user.email, user.name or "", "Vos credits sont bientot epuises", html)
    except Exception as e:
        logger.error(f"Low credits notification error: {e}")

# ==================== ADMIN CONFIG HELPERS ====================
_admin_config_cache = None
_admin_config_mtime = 0

def load_admin_config() -> dict:
    """Load admin config with in-memory cache — reloads only if file changed."""
    global _admin_config_cache, _admin_config_mtime
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        mtime = os.path.getmtime(CONFIG_PATH)
        if _admin_config_cache is not None and mtime == _admin_config_mtime:
            return _admin_config_cache
        with open(CONFIG_PATH, "r") as f:
            _admin_config_cache = json.load(f)
        _admin_config_mtime = mtime
        return _admin_config_cache
    except Exception:
        return _admin_config_cache or {}

def save_admin_config(config: dict):
    """Atomic write to prevent corruption (#190). Invalidates cache."""
    global _admin_config_cache, _admin_config_mtime
    import tempfile
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(CONFIG_PATH), suffix='.tmp')
    try:
        with os.fdopen(tmp_fd, 'w') as f:
            json.dump(config, f, indent=2)
        os.replace(tmp_path, CONFIG_PATH)
        _admin_config_cache = config
        _admin_config_mtime = os.path.getmtime(CONFIG_PATH)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

def _get_email_log():
    return load_admin_config().get("email_log", [])

def _append_email_log(entry):
    config = load_admin_config()
    log = config.get("email_log", [])
    log.insert(0, entry)
    config["email_log"] = log[:200]
    save_admin_config(config)

def _append_admin_log(entry):
    config = load_admin_config()
    log = config.get("admin_log", [])
    log.insert(0, entry)
    config["admin_log"] = log[:500]
    save_admin_config(config)

def log_system_event(action: str, detail: str = "", level: str = "info"):
    """Log a system event to the admin monitoring dashboard."""
    from datetime import datetime, timezone
    _append_admin_log({
        "action": action,
        "detail": detail,
        "level": level,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "by": "system"
    })

def _get_admin_log():
    return load_admin_config().get("admin_log", [])

# ==================== EMAIL TEMPLATES ====================
EMAIL_TEMPLATES = {
    "welcome": {
        "subject": "Bienvenue sur ZAYADO !",
        "html": """<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<h1 style="color:#1E3A8A;">Bienvenue {{name}} !</h1>
<p>Merci de rejoindre ZAYADO. Vous disposez de <strong>200 credits gratuits</strong>.</p>
<p><a href="https://app.zayado.net/chat" style="background:#DC2626;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;display:inline-block;">Commencer</a></p>
</div>"""
    },
    "password_reset": {
        "subject": "Reinitialisation de mot de passe - ZAYADO",
        "html": """<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
<h2 style="color:#1E3A8A;">Reinitialisation de mot de passe</h2>
<p>Bonjour {{name}},</p>
<p>Vous avez demande la reinitialisation de votre mot de passe ZAYADO.</p>
<a href="{{reset_link}}" style="display:inline-block;padding:12px 24px;background:#1E3A8A;color:white;border-radius:8px;text-decoration:none;font-weight:bold;">Reinitialiser mon mot de passe</a>
<p style="color:#666;font-size:12px;margin-top:20px;">Ce lien expire dans 30 minutes.</p>
</div>"""
    },
    "invoice": {
        "subject": "Decompte Projet - {{project_name}}",
        "html": """<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<h1 style="color:#1E3A8A;">Decompte Projet</h1>
<h2>{{project_name}}</h2>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:8px 0;color:#666;">Taux horaire</td><td style="text-align:right;font-weight:bold;">{{hourly_rate}} EUR/h</td></tr>
<tr><td style="padding:8px 0;color:#666;">Heures totales</td><td style="text-align:right;font-weight:bold;">{{total_hours}}h</td></tr>
<tr style="border-top:2px solid #ddd;"><td style="padding:12px 0;font-weight:bold;font-size:18px;">Total</td><td style="text-align:right;font-weight:bold;font-size:18px;color:#DC2626;">{{total_cost}} EUR</td></tr>
</table>
</div>"""
    }
}

# ==================== PRICING CONSTANTS ====================
CREDIT_PACKAGES = [
    {"id": "mini_pack",     "name": "Mini",     "credits": 300,   "price": 1.99},
    {"id": "starter_pack",  "name": "Starter",  "credits": 1000,  "price": 4.99},
    {"id": "standard_pack", "name": "Standard", "credits": 2500,  "price": 9.99},
    {"id": "pro_pack",      "name": "Pro",      "credits": 6000,  "price": 19.99},
    {"id": "ultra_pack",    "name": "Ultra",    "credits": 12000, "price": 34.99},
    {"id": "business_pack", "name": "Business", "credits": 25000, "price": 64.99}
]

SUBSCRIPTION_PLANS = [
    # ─── New 2026 strategy: 3 tiers + Creation door ────────────────────────
    {
        "id": "start", "name": "START", "price": 29.00,
        "credits_per_month": 3000, "credits_onetime": False, "bonus_cap": 2000, "seats": 1,
        "first_month_price": 1.00,
        "annual_discount_pct": 20,
        "tagline": "Pour lancer son activité l'esprit serein.",
        "features": {
            "ia_fast": True, "ia_pro": True, "ia_gemini": False, "ia_grok": False,
            "ia_perplexity": False, "ia_image": True, "ia_agent": False,
            "agent_tasks_month": 0,
            "timer_projects": True, "workflows": True, "workflows_advanced": False,
            "cloud_backup": False, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": False,
            "team_dashboard": False, "shared_credits": False, "chatbot_support": False,
            "sharepoint": False, "onedrive": False, "gdrive": True,
            "kyb_required": False, "promo_allowed": True,
            "support_level": "email", "sla_hours": 48,
            # New strategy features
            "creation_eligible": True,            # accès création 1 €
            "mutualisation_basic": True,          # adresse Paris, devis partenaires
            "mutualisation_premium": False,       # mutuelle / RC Pro inclus
            "humain_quota_min": 0,                # 30 % Humain quota mensuel (minutes coach)
            "bilan_creation_offert": True,
        },
        "features_list": [
            "Bilan création OFFERT",
            "Création d'entreprise à 1 € éligible",
            "Co-pilote IA (Claude rapide + pro)",
            "Image IA incluse",
            "Workflows simples",
            "Timer & Projets",
            "Google Drive intégré",
            "Support email 48h",
            "1er mois à 1 €",
        ]
    },
    {
        "id": "grow", "name": "GROW", "price": 79.00,
        "credits_per_month": 10000, "credits_onetime": False, "bonus_cap": 6000, "seats": 1,
        "first_month_price": 9.00,
        "annual_discount_pct": 20,
        "tagline": "Pour accélérer croissance et leads.",
        "highlight": True,
        "features": {
            "ia_fast": True, "ia_pro": True, "ia_gemini": True, "ia_grok": True,
            "ia_perplexity": True, "ia_image": True, "ia_agent": True,
            "agent_tasks_month": 10,
            "timer_projects": True, "workflows": True, "workflows_advanced": True,
            "cloud_backup": True, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": True,
            "team_dashboard": False, "shared_credits": False, "chatbot_support": True,
            "sharepoint": False, "onedrive": True, "gdrive": True,
            "kyb_required": False, "promo_allowed": True,
            "support_level": "standard", "sla_hours": 24,
            "creation_eligible": True,
            "mutualisation_basic": True,
            "mutualisation_premium": False,
            "humain_quota_min": 30,
            "bilan_creation_offert": True,
            "expansion_agent": True,
        },
        "features_list": [
            "Tout START +",
            "Expansion Agent (croissance & leads)",
            "8 modèles IA (Claude, GPT, Gemini, Grok)",
            "Agent IA 10 tâches/mois",
            "Workflows avancés",
            "Chatbot Support inclus",
            "30 min de coach humain / mois",
            "Cloud backup & partage crédits",
            "Support chat 24h",
            "1er mois à 9 €",
        ]
    },
    {
        "id": "serenity", "name": "SERENITY", "price": 149.00,
        "credits_per_month": 25000, "credits_onetime": False, "bonus_cap": 15000, "seats": 2,
        "first_month_price": 149.00,
        "annual_discount_pct": 20,
        "tagline": "Pour entreprendre sans rester seul. Le 30 % Humain inclus.",
        "features": {
            "ia_fast": True, "ia_pro": True, "ia_gemini": True, "ia_grok": True,
            "ia_perplexity": True, "ia_image": True, "ia_agent": True,
            "agent_tasks_month": 30, "agents_unlimited": True,
            "timer_projects": True, "workflows": True, "workflows_advanced": True,
            "cloud_backup": True, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": True,
            "team_dashboard": True, "shared_credits": True, "chatbot_support": True,
            "sharepoint": True, "onedrive": True, "gdrive": True,
            "kyb_required": False, "promo_allowed": True,
            "support_level": "premium", "sla_hours": 6,
            "creation_eligible": True,
            "mutualisation_basic": True,
            "mutualisation_premium": True,        # mutuelle + RC Pro inclus
            "humain_quota_min": 120,              # 2h de coach humain / mois
            "bilan_creation_offert": True,
            "expansion_agent": True,
            "daf_supervision": True,              # supervision DAF/compta
            "domiciliation_paris": True,
        },
        "features_list": [
            "Tout GROW +",
            "Mutuelle + RC Pro mutualisées",
            "Adresse de Prestige Paris incluse (10 Rue de la Paix)",
            "Supervision DAF/compta",
            "2 h de coach humain / mois",
            "Agent IA illimité",
            "SharePoint + OneDrive + Drive",
            "Support premium 6h",
            "Tableau de bord équipe (2 sièges)",
            "Pas de remise — l'humain ne se brade pas",
        ]
    },
    # ─── Legacy plans (kept for backward compat with existing customers) ───
    {
        "id": "free", "name": "BYOK", "price": 1.00,
        "credits_per_month": 200, "credits_per_day": 200, "credits_onetime": False, "bonus_cap": 0, "seats": 1,
        "first_month_price": 0,
        "legacy": True,
        "features": {
            "ia_fast": True, "ia_pro": False, "ia_gemini": False, "ia_grok": False,
            "ia_perplexity": False, "ia_image": False, "ia_agent": False,
            "agent_tasks_month": 0,
            "timer_projects": True, "workflows": False, "workflows_advanced": False,
            "cloud_backup": False, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": False,
            "team_dashboard": False, "shared_credits": False, "chatbot_support": False,
            "sharepoint": False, "onedrive": False, "gdrive": False,
            "kyb_required": False, "promo_allowed": True,
            "support_level": "community", "sla_hours": 0
        },
        "features_list": ["200 credits/mois", "ChatGPT BYOK illimite (cle perso)", "IA Rapide (Claude)", "Timer & Projets", "Memoire illimitee", "Historique illimite", "1er mois offert"]
    },
    {
        "id": "starter", "name": "Productivite", "price": 7.90,
        "credits_per_month": 1250, "credits_onetime": False, "bonus_cap": 1000, "seats": 1,
        "first_month_price": 3.00,
        "legacy": True,
        "features": {
            "ia_fast": True, "ia_pro": False, "ia_gemini": False, "ia_grok": False,
            "ia_perplexity": False, "ia_image": False, "ia_agent": False,
            "agent_tasks_month": 0,
            "timer_projects": True, "workflows": True, "workflows_advanced": False,
            "cloud_backup": False, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": False,
            "team_dashboard": False, "shared_credits": False, "chatbot_support": False,
            "sharepoint": False, "onedrive": False, "gdrive": False,
            "kyb_required": False, "promo_allowed": True,
            "support_level": "email", "sla_hours": 72
        },
        "features_list": ["1 250 credits/mois", "Plafond bonus 1 000", "IA Rapide (Claude)", "Timer & Projets", "Workflows (5/mois)", "Memoire illimitee", "Support email 72h"]
    },
    {
        "id": "pro", "name": "Pro", "price": 19.90,
        "credits_per_month": 5000, "credits_onetime": False, "bonus_cap": 2500, "seats": 1,
        "first_month_price": 3.00,
        "legacy": True,
        "features": {
            "ia_fast": True, "ia_pro": True, "ia_gemini": True, "ia_grok": True,
            "ia_perplexity": True, "ia_image": True, "ia_agent": True,
            "agent_tasks_month": 3,
            "timer_projects": True, "workflows": True, "workflows_advanced": True,
            "cloud_backup": True, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": True,
            "team_dashboard": False, "shared_credits": False, "chatbot_support": False,
            "sharepoint": False, "onedrive": True, "gdrive": True,
            "kyb_required": False, "promo_allowed": True,
            "support_level": "standard", "sla_hours": 24
        },
        "features_list": ["5 000 credits/mois", "Plafond bonus 5 000", "8 modeles IA", "Image IA", "Agent IA 3 taches/mois", "Timer & Projets", "Workflows avances", "OneDrive + Google Drive", "Partage credits", "Chat 24h"]
    },
    {
        "id": "business", "name": "Business", "price": 39.90,
        "credits_per_month": 20000, "credits_onetime": False, "bonus_cap": 12000, "seats": 1,
        "legacy": True,
        "features": {
            "ia_fast": True, "ia_pro": True, "ia_gemini": True, "ia_grok": True,
            "ia_perplexity": True, "ia_image": True, "ia_agent": True,
            "agent_tasks_month": 17, "agents_unlimited": True,
            "timer_projects": True, "workflows": True, "workflows_advanced": True,
            "cloud_backup": True, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": True,
            "team_dashboard": True, "shared_credits": True, "chatbot_support": False,
            "sharepoint": False, "onedrive": True, "gdrive": True,
            "kyb_required": True, "promo_allowed": True,
            "support_level": "dedicated", "sla_hours": 12
        },
        "features_list": ["20 000 credits/mois", "Plafond bonus 12 000", "1 equipe, 2 membres max", "Agents IA illimites", "8 modeles IA", "Image IA", "Agent IA 17 taches/mois", "Timer & Projets", "Workflows avances", "OneDrive + Google Drive", "Partage credits", "Justificatif entreprise requis", "Chat + WhatsApp 12h"]
    },
    {
        "id": "student", "name": "Etudiant", "price": 12.90,
        "credits_per_month": 2500, "credits_onetime": False, "bonus_cap": 2000, "seats": 1,
        "legacy": True,
        "features": {
            "ia_fast": True, "ia_pro": True, "ia_gemini": False, "ia_grok": False,
            "ia_perplexity": False, "ia_image": True, "ia_agent": False,
            "agent_tasks_month": 0,
            "timer_projects": True, "workflows": True, "workflows_advanced": False,
            "cloud_backup": False, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": False,
            "team_dashboard": False, "shared_credits": False, "chatbot_support": False,
            "sharepoint": False, "onedrive": False, "gdrive": False,
            "kyb_required": True, "promo_allowed": False,
            "support_level": "email", "sla_hours": 72
        },
        "features_list": ["2 500 credits/mois", "Plafond bonus 2 000", "IA Rapide + Pro (Claude)", "Image IA", "Timer & Projets", "Workflows (10/mois)", "Memoire illimitee", "Verification carte etudiante requise"]
    },
    {
        "id": "team", "name": "Equipe", "price": 149.90,
        "credits_per_month": 60000, "credits_onetime": False, "bonus_cap": 30000, "seats": 10,
        "legacy": True,
        "features": {
            "ia_fast": True, "ia_pro": True, "ia_gemini": True, "ia_grok": True,
            "ia_perplexity": True, "ia_image": True, "ia_agent": True,
            "agent_tasks_month": 30, "agents_unlimited": True,
            "timer_projects": True, "workflows": True, "workflows_advanced": True,
            "cloud_backup": True, "history_unlimited": True, "memory_unlimited": True,
            "credit_sharing": True,
            "team_dashboard": True, "shared_credits": True, "chatbot_support": True,
            "sharepoint": True, "onedrive": True, "gdrive": True,
            "kyb_required": True, "promo_allowed": True,
            "support_level": "premium", "sla_hours": 12
        },
        "features_list": ["60 000 credits/mois partages", "Plafond bonus 30 000", "Jusqu'a 10 membres", "Tableau de bord equipe", "Chatbot Support Client IA", "8 modeles IA + Image IA", "Agent IA 30 taches/mois", "OneDrive + SharePoint + Google Drive", "Partage credits equipe", "Justificatif organisation requis", "Chat + WhatsApp 12h"]
    }
]

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)

# ==================== RATE LIMITER ====================
# NOTE: In-memory rate limiter — effective for single-worker deployments.
# For multi-worker (Gunicorn) production, replace with Redis-based limiter.
class RateLimiter:
    """In-memory sliding window rate limiter. Thread-safe."""
    def __init__(self):
        self._store: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def is_rate_limited(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            attempts = self._store.get(key, [])
            attempts = [t for t in attempts if t > cutoff]
            if len(attempts) >= max_attempts:
                self._store[key] = attempts
                return True
            attempts.append(now)
            self._store[key] = attempts
            return False

    def cleanup(self, max_age: int = 3600):
        """Remove expired entries. Call periodically."""
        now = time.time()
        cutoff = now - max_age
        with self._lock:
            to_delete = [k for k, v in self._store.items() if not v or v[-1] < cutoff]
            for k in to_delete:
                del self._store[k]

rate_limiter = RateLimiter()
