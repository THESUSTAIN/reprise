"""Agent IA routes — Mammoth IA powered

Fixes applied:
  #108/#109/#110/#111/#112 — Suppression des duplications de fonctions.
      classify_task_type, estimate_agent_credits, select_agent_model,
      AGENT_COMPLEX_MODEL, AGENT_MAX_TIMEOUT sont désormais uniquement dans utils.py.
  #127 — Crédits NE sont PAS déduits si la réponse échoue (TimeoutException ou erreur).
  #129 — Validation de la longueur du task en entrée (max 10 000 caractères).
  #67  — Timeout httpx explicite aligné sur AGENT_MAX_TIMEOUT (pas de blocage indéfini).
  #131 — Actions réelles: Brevo email + Web scraping intégrés dans l'agent.
"""
import os
import logging
import re
import urllib.parse
import httpx
import json
import sib_api_v3_sdk
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from database import get_db
from models import User, Conversation
from deps import get_current_user
from schemas import AgentEstimateRequest, AgentRunRequest

# fix #108–#112 — import shared helpers from utils, no more local duplicates
from utils import (
    MAMMOTH_BASE_URL,
    AGENT_DEFAULT_MODEL,
    AGENT_COMPLEX_MODEL,
    AGENT_MAX_TIMEOUT,
    classify_task_type,
    estimate_agent_credits,
    select_agent_model,
    classify_agent_specialization,
    get_agent_system_prompt,
)

logger = logging.getLogger(__name__)
agent_router = APIRouter(prefix="/agent", tags=["agent"])

_TASK_MAX_LEN = 10_000  # fix #129


# ─── Real Action Helpers ──────────────────────────────────────────────

def _detect_email_intent(task: str) -> dict | None:
    """Detect if user wants to send an email. Returns parsed email data or None."""
    tl = task.lower()
    email_kw = ["envoie un email", "envoie un mail", "envoyer un email", "envoyer un mail",
                "send an email", "send email", "send a mail", "mail a ", "email a ",
                "ecris un email", "ecris un mail", "ecrire un email",
                "envoie-lui un email", "envoie-lui un mail",
                "envoie un message a", "envoie un e-mail"]
    if not any(k in tl for k in email_kw):
        return None

    # Extract email address
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", task)
    if not email_match:
        return None

    to_email = email_match.group(0)

    # Extract subject (after "objet:", "sujet:", "subject:")
    subject_match = re.search(r"(?:objet|sujet|subject)\s*[:=]\s*(.+?)(?:\n|$|\.(?:\s|$))", task, re.IGNORECASE)
    subject = subject_match.group(1).strip() if subject_match else ""

    return {"to_email": to_email, "subject": subject, "task_text": task}


def _detect_scrape_intent(task: str) -> str | None:
    """Detect if user wants to scrape/analyze a URL. Returns URL or None."""
    tl = task.lower()
    scrape_kw = ["analyse le site", "analyse le contenu", "scrape", "extrais le contenu",
                 "regarde le site", "va sur le site", "recupere les informations",
                 "lis le contenu", "analyse la page", "extraire", "scraper",
                 "analyse cette page", "qu'est-ce qu'il y a sur", "contenu de",
                 "analyze the site", "scrape the", "extract from", "read the page"]
    if not any(k in tl for k in scrape_kw):
        # Check if there's a URL in the task anyway
        url_match = re.search(r"https?://[^\s]+", task)
        if url_match:
            # Only scrape if there's analysis-related context
            analysis_kw = ["analyse", "contenu", "resume", "info", "donnees", "data", "quoi", "extract", "lire", "read"]
            if any(k in tl for k in analysis_kw):
                return url_match.group(0).rstrip(".,;)")
        return None

    url_match = re.search(r"https?://[^\s]+", task)
    if url_match:
        return url_match.group(0).rstrip(".,;)")

    # Try to find a domain
    domain_match = re.search(r"(?:www\.)?([a-zA-Z0-9-]+\.(?:com|fr|net|org|io|co|be|ch|ca|ai|so|dev))(?:/[^\s]*)?", task, re.IGNORECASE)
    if domain_match:
        return "https://" + domain_match.group(0)

    return None


async def _execute_scrape(url: str) -> dict:
    """Scrape a URL and return cleaned content."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, max_redirects=5) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code != 200:
            return {"success": False, "error": f"Code HTTP {resp.status_code}"}

        html = resp.text[:500_000]
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_tag.get("content", "") if meta_tag else ""

        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)
        if len(clean_text) > 6000:
            clean_text = clean_text[:6000] + "\n[... tronque]"

        return {"success": True, "title": title, "meta_description": meta_desc, "text": clean_text, "url": url}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


def _execute_brevo_send(api_key: str, sender_email: str, sender_name: str,
                        to_email: str, subject: str, html_content: str) -> dict:
    """Send email via Brevo using user's API key."""
    try:
        config = sib_api_v3_sdk.Configuration()
        config.api_key["api-key"] = api_key
        api_client = sib_api_v3_sdk.ApiClient(config)
        email_api = sib_api_v3_sdk.TransactionalEmailsApi(api_client)

        email_obj = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email, "name": to_email}],
            sender={"email": sender_email, "name": sender_name},
            subject=subject,
            html_content=html_content,
        )
        response = email_api.send_transac_email(email_obj)
        return {"success": True, "message_id": str(response.message_id)}
    except sib_api_v3_sdk.rest.ApiException as e:
        return {"success": False, "error": f"Brevo error {e.status}: {e.reason}"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


@agent_router.post("/estimate")
async def agent_estimate(request: AgentEstimateRequest, user: User = Depends(get_current_user)):
    task_type = request.task_type or classify_task_type(request.task)
    specialization = classify_agent_specialization(request.task)
    credits_needed = estimate_agent_credits(task_type)
    total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)
    spec_label = {"research": "Recherche", "writing": "Redaction", "code": "Code", "analysis": "Analyse", "general": "General"}.get(specialization, "General")
    return {
        "credits_needed": credits_needed,
        "credits_available": total_credits,
        "can_run": total_credits >= credits_needed,
        "task_type": task_type,
        "specialization": specialization,
        "specialization_label": spec_label,
        "model": select_agent_model(task_type),
        "message": f"Agent {spec_label} — {credits_needed} credits ({task_type})",
    }


@agent_router.post("/run")
async def agent_run(request: AgentRunRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mammoth_key = os.environ.get("MAMMOTH_API_KEY", "")
    if not mammoth_key:
        raise HTTPException(status_code=500, detail="Mammoth IA non configure")

    task_text = (request.task or "").strip()
    if not task_text:
        raise HTTPException(status_code=400, detail="Tâche requise")
    if len(task_text) > _TASK_MAX_LEN:  # fix #129
        raise HTTPException(status_code=400, detail=f"Tâche trop longue ({len(task_text)} car.). Maximum : {_TASK_MAX_LEN}.")

    task_type = request.task_type or classify_task_type(task_text)
    credits_needed = estimate_agent_credits(task_type)
    total_credits = (user.credits or 0) + (user.bonus_credits or 0) + (user.purchased_credits or 0)

    if total_credits < credits_needed:
        raise HTTPException(status_code=402, detail=f"Credits insuffisants. Necessaire: {credits_needed}, Disponible: {total_credits}")

    model = select_agent_model(task_type)
    specialization = classify_agent_specialization(task_text)
    agent_system = get_agent_system_prompt(specialization)

    # ─── #131 Real Actions: detect and execute tools ───────────────────
    actions_performed = []
    extra_context = ""
    user_integrations = (user.settings or {}).get("integrations", {})

    # 1) Web Scraping detection
    scrape_url = _detect_scrape_intent(task_text)
    if scrape_url:
        logger.info(f"Agent scraping {scrape_url} for user {user.email}")
        scrape_result = await _execute_scrape(scrape_url)
        if scrape_result["success"]:
            extra_context += f"\n\n--- CONTENU SCRAPE DE {scrape_url} ---\nTitre: {scrape_result['title']}\n{scrape_result.get('meta_description','')}\n\n{scrape_result['text']}\n--- FIN DU CONTENU SCRAPE ---\n"
            actions_performed.append({"tool": "web_scraping", "url": scrape_url, "success": True})
        else:
            extra_context += f"\n\n[Erreur de scraping pour {scrape_url}: {scrape_result.get('error','')}]\n"
            actions_performed.append({"tool": "web_scraping", "url": scrape_url, "success": False, "error": scrape_result.get("error","")})

    # 2) Email sending detection
    email_data = _detect_email_intent(task_text)
    brevo_key = user_integrations.get("brevo_api_key", "")
    if email_data and brevo_key:
        # We'll let the LLM draft the email first, then send it
        agent_system += "\n\nACTION REELLE — EMAIL BREVO:\nL'utilisateur veut envoyer un email. Tu dois rediger l'email complet avec un sujet et un corps HTML professionnel. Inclus le sujet sur la premiere ligne sous la forme 'SUJET: ...' puis le contenu HTML. Le destinataire est " + email_data["to_email"] + "."
    elif email_data and not brevo_key:
        extra_context += "\n\n[ATTENTION: L'utilisateur veut envoyer un email mais n'a pas configure sa cle Brevo dans Parametres > Integrations. Indique-lui d'ajouter sa cle API Brevo pour activer l'envoi d'emails.]\n"

    agent_system += "\n\nCAPACITES REELLES DE L'AGENT IA ZAYADO:\n- Scraping web en temps reel (deja execute si une URL est detectee)\n- Envoi d'emails via Brevo (si l'utilisateur a configure sa cle)\n- Ne dis JAMAIS que tu ne peux pas acceder a internet\n- Presente les resultats comme des actions REELLES effectuees"

    # Combine task + scraped context
    user_message = task_text
    if extra_context:
        user_message += extra_context

    result_text = None
    try:
        async with httpx.AsyncClient(timeout=float(AGENT_MAX_TIMEOUT)) as client:
            response = await client.post(
                f"{MAMMOTH_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "system", "content": agent_system}, {"role": "user", "content": user_message}], "max_tokens": 4096, "temperature": 0.3},
            )
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Mammoth IA error: {response.status_code}")
            result_text = response.json()["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        logger.warning(f"Agent timeout task_type={task_type}")
        return {"success": False, "result": "", "credits_used": 0, "error": "Timeout — tâche trop longue. Aucun crédit débité."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent run error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # 3) After LLM response: if email intent detected, parse and send via Brevo
    if email_data and brevo_key and result_text:
        sender_email = user_integrations.get("brevo_sender_email") or user.email
        sender_name = user_integrations.get("brevo_sender_name") or user.name or "ZAYADO Agent"

        # Parse subject from LLM response
        subject_match = re.search(r"SUJET\s*:\s*(.+?)(?:\n|$)", result_text)
        email_subject = subject_match.group(1).strip() if subject_match else (email_data.get("subject") or "Message de votre Agent IA")

        # Use the LLM text as email body
        email_body = result_text
        if subject_match:
            email_body = result_text[subject_match.end():].strip()
        # Wrap in basic HTML if not already
        if not email_body.strip().startswith("<"):
            email_body = "<div style='font-family:Arial,sans-serif;line-height:1.6;'>" + email_body.replace("\n", "<br>") + "</div>"

        send_result = _execute_brevo_send(
            api_key=brevo_key,
            sender_email=sender_email,
            sender_name=sender_name,
            to_email=email_data["to_email"],
            subject=email_subject,
            html_content=email_body,
        )
        if send_result["success"]:
            result_text += f"\n\n---\nEmail envoye avec succes a {email_data['to_email']} (ID: {send_result['message_id']})"
            actions_performed.append({"tool": "brevo_email", "to": email_data["to_email"], "subject": email_subject, "success": True})
            email_sent = True
            logger.info(f"Agent sent email via Brevo for {user.email} to {email_data['to_email']}")
        else:
            result_text += f"\n\n---\nErreur lors de l'envoi de l'email: {send_result.get('error','')}"
            actions_performed.append({"tool": "brevo_email", "to": email_data["to_email"], "success": False, "error": send_result.get("error","")})

    # Credits deducted ONLY after successful response (#127)
    remaining = credits_needed
    plan_d  = min(user.credits or 0, remaining);        remaining -= plan_d
    bonus_d = min(user.bonus_credits or 0, remaining);  remaining -= bonus_d
    purch_d = min(user.purchased_credits or 0, remaining)
    await db.execute(update(User).where(User.id == user.id).values(
        credits=User.credits - plan_d,
        bonus_credits=User.bonus_credits - bonus_d,
        purchased_credits=User.purchased_credits - purch_d,
    ))
    await db.commit()

    return {
        "success": True,
        "result": result_text,
        "credits_used": credits_needed,
        "task_type": task_type,
        "model": model,
        "actions_performed": actions_performed,
    }


@agent_router.post("/plan")
async def agent_plan(request: Request, user: User = Depends(get_current_user)):
    """Décompose une tâche en étapes navigateur pour l'extension Chrome."""
    body = await request.json()
    task = body.get("task", "").strip()
    if not task:
        raise HTTPException(400, detail="Tache requise")
    if len(task) > _TASK_MAX_LEN:  # fix #129
        raise HTTPException(status_code=400, detail=f"Tâche trop longue. Maximum : {_TASK_MAX_LEN} caractères.")

    tl = task.lower()

    KNOWN_SERVICES = {
        "claude": "https://claude.ai", "claude ai": "https://claude.ai", "claude.ai": "https://claude.ai",
        "chatgpt": "https://chatgpt.com", "chat gpt": "https://chatgpt.com",
        "openai": "https://platform.openai.com", "gemini": "https://gemini.google.com",
        "google gemini": "https://gemini.google.com", "perplexity": "https://perplexity.ai",
        "github": "https://github.com", "gitlab": "https://gitlab.com",
        "youtube": "https://youtube.com", "twitter": "https://x.com", "x.com": "https://x.com",
        "linkedin": "https://linkedin.com", "facebook": "https://facebook.com",
        "instagram": "https://instagram.com", "gmail": "https://mail.google.com",
        "google drive": "https://drive.google.com", "google docs": "https://docs.google.com",
        "google sheets": "https://sheets.google.com", "notion": "https://notion.so",
        "figma": "https://figma.com", "canva": "https://canva.com",
        "stripe": "https://dashboard.stripe.com", "vercel": "https://vercel.com",
        "railway": "https://railway.com", "amazon": "https://amazon.fr",
        "wikipedia": "https://wikipedia.org", "reddit": "https://reddit.com",
        "stack overflow": "https://stackoverflow.com", "stackoverflow": "https://stackoverflow.com",
    }

    url_m = re.search(r"https?://[^\s]+", task)
    dom_m = re.search(r"(?:www\.)?([a-zA-Z0-9-]+\.(?:com|fr|net|org|io|co|be|ch|ca|ai|so|dev))(?:/[^\s]*)?", task, re.IGNORECASE)

    nav_kw    = ["va sur","ouvre","visite","browse","go to","open","cherche sur","search on","naviguer","navigate","accede","acceder"]
    search_kw = ["cherche","recherche","trouve","find","search","regarde","analyse","audite"]
    google_kw = ["google","bing","duckduckgo"]

    is_nav    = any(k in tl for k in nav_kw)
    is_search = any(k in tl for k in search_kw)
    is_google = any(k in tl for k in google_kw)

    target_url = None; steps = []; task_type = "text"

    if url_m:
        target_url = url_m.group(0).rstrip(".,;)"); task_type = "browser"
        steps = [{"action": "navigate", "url": target_url, "description": f"Ouverture de {target_url}"}, {"action": "extract", "description": "Extraction du contenu"}]
    elif is_nav:
        matched = None
        for sname, surl in sorted(KNOWN_SERVICES.items(), key=lambda x: -len(x[0])):
            if sname in tl: matched = (sname, surl); break
        if matched:
            target_url = matched[1]; task_type = "browser"
            steps = [{"action": "navigate", "url": target_url, "description": f"Ouverture de {matched[0]}"}, {"action": "extract", "description": "Extraction du contenu"}]
        elif dom_m:
            domain = dom_m.group(0); target_url = ("https://" + domain) if not domain.startswith("http") else domain; task_type = "browser"
            steps = [{"action": "navigate", "url": target_url, "description": f"Navigation vers {domain}"}, {"action": "extract", "description": "Lecture de la page"}]
        else:
            cleaned = re.sub(r"(?:va sur|ouvre|visite|browse|go to|open|naviguer|navigate|un onglet|sur|le|la|les|l'|de|du|des|pour|a|l )\s*", "", tl).strip()
            if cleaned:
                target_url = "https://www.google.com/search?q=" + urllib.parse.quote(cleaned); task_type = "browser"
                steps = [{"action": "navigate", "url": target_url, "description": f"Recherche : {cleaned}"}, {"action": "extract", "description": "Lecture des resultats"}]
    elif is_google or (is_search and not dom_m):
        q_m = re.search(r"(?:cherche|recherche|trouve|find|search|regarde)(?:\s+sur\s+\w+)?\s+(.+?)(?:\s+sur\s+\w+)?$", tl)
        query = q_m.group(1).strip() if q_m else re.sub(r"(?:va sur|go to|ouvre|open|cherche|recherche|trouve|search|sur|google|bing)\s*", "", tl).strip()
        if query:
            target_url = "https://www.google.com/search?q=" + urllib.parse.quote(query); task_type = "browser"
            steps = [{"action": "navigate", "url": target_url, "description": f"Recherche : {query}"}, {"action": "extract", "description": "Lecture des resultats"}]
    elif dom_m and is_search:
        domain = dom_m.group(0); target_url = ("https://" + domain) if not domain.startswith("http") else domain; task_type = "browser"
        steps = [{"action": "navigate", "url": target_url, "description": f"Navigation vers {domain}"}, {"action": "extract", "description": "Lecture de la page"}]

    return {"task_type": task_type, "target_url": target_url, "steps": steps, "type": task_type, "message": f"{len(steps)} etape(s) planifiee(s)" if steps else "Reponse IA directe"}
