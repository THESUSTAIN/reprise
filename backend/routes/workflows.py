"""Workflow routes for Extension IA API."""
import logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone
import os
import json
import httpx

from database import get_db
from models import User, Workflow
from deps import get_current_user
from schemas import WorkflowCreateSchema, WorkflowResponse
from utils import MAMMOTH_BASE_URL

workflows_router = APIRouter(prefix="/workflows", tags=["Workflows"])

def _normalize_result(result):
    """Convert result to string format. Handles legacy list format and new string format."""
    if result is None:
        return None
    if isinstance(result, list):
        if len(result) == 0:
            return None
        # Legacy format: list of step dicts [{step, name, result, status}]
        parts = []
        for r in result:
            if isinstance(r, dict):
                name = r.get("name", f"Etape {r.get('step', '?')}")
                content = r.get("result", "")
                parts.append(f"### {name}\n{content}")
        return "\n\n".join(parts) if parts else str(result)
    return str(result) if result else None


def _send_approval_email(user, workflow, combined_result: str):
    """Send an approval email to the user before sending workflow emails."""
    if not user.email:
        return
    try:
        from utils import send_brevo_email
        import asyncio as _aio
        approve_url = f"https://app.zayado.net/api/workflows/{workflow.id}/approve?token={_generate_approval_token(workflow.id, user.id)}"
        
        # Truncate result for email preview
        preview = combined_result[:2000] if combined_result else "Aucun contenu"
        preview_html = preview.replace("\n", "<br>").replace("### ", "<h3>").replace("**", "<strong>")
        
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
            <h2 style="color:#1E3A8A;margin-bottom:8px;">Validation requise — Workflow « {workflow.name} »</h2>
            <p style="color:#374151;">Bonjour {user.name or 'cher utilisateur'},</p>
            <p style="color:#374151;margin:12px 0;">
                Votre workflow a genere le contenu suivant. <strong>Verifiez-le avant l'envoi.</strong>
            </p>
            <div style="background:#F5F5F0;border:1px solid #E5E7EB;border-radius:8px;padding:16px;margin:16px 0;font-size:14px;color:#374151;max-height:400px;overflow-y:auto;">
                {preview_html}
            </div>
            <div style="text-align:center;margin:24px 0;">
                <a href="{approve_url}"
                   style="display:inline-block;padding:14px 32px;background:#059669;
                          color:white;border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">
                    Approuver et Envoyer
                </a>
            </div>
            <p style="color:#9CA3AF;font-size:12px;text-align:center;">
                Si vous ne souhaitez pas envoyer, ignorez cet email. Le workflow restera en attente.
            </p>
        </div>
        """
        _to = user.email
        _name = user.name or ""
        _subj = f"[ZAYADO] Validation requise — Workflow « {workflow.name} »"
        _html = html
        _aio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(
            to_email=_to, to_name=_name, subject=_subj, html_content=_html
        ))
        logger.info(f"[Workflow] Email de validation envoye a {user.email}")
    except Exception as e:
        logger.warning(f"[Workflow] Erreur envoi email validation: {e}")

def _generate_approval_token(workflow_id: str, user_id: str) -> str:
    """Generate a simple approval token (HMAC-based)."""
    import hashlib
    secret = os.environ.get('JWT_SECRET', 'zayado-secret')
    return hashlib.sha256(f"{workflow_id}:{user_id}:{secret}".encode()).hexdigest()[:32]


def _send_workflow_notification(user, workflow_name: str, status: str, step_count: int):
    """Send email + in-app notification when workflow completes.
    CORRECTION: utilise send_brevo_email() centralise depuis utils.py.
    """
    status_text = "termine avec succes" if status == "completed" else "termine avec des erreurs"
    status_emoji = "✅" if status == "completed" else "❌"

    # Email notification
    if user.email:
        try:
            from utils import send_brevo_email
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;">
                <h2 style="color:#1E3A8A;margin-bottom:8px;">{status_emoji} Workflow {status_text}</h2>
                <p style="color:#374151;">Bonjour {user.name or 'cher utilisateur'},</p>
                <p style="color:#374151;margin:12px 0;">
                    Votre workflow <strong>{workflow_name}</strong> vient de s executer.<br>
                    <strong>{step_count} etape(s)</strong> traitee(s).
                </p>
                <a href="https://app.zayado.net/workflows"
                   style="display:inline-block;padding:12px 24px;background:#1E3A8A;
                          color:white;border-radius:8px;text-decoration:none;font-weight:bold;">
                    Voir les resultats
                </a>
                <p style="color:#9CA3AF;font-size:12px;margin-top:24px;">
                    Equipe ZAYADO —
                    <a href="https://app.zayado.net/settings" style="color:#1E3A8A;">
                        Gerer les notifications
                    </a>
                </p>
            </div>
            """
            import asyncio as _aio
            _to = user.email
            _name = user.name or ""
            _subj = f"[ZAYADO] Workflow « {workflow_name} » {status_text}"
            _html = html
            _aio.get_running_loop().run_in_executor(None, lambda: send_brevo_email(
                to_email=_to, to_name=_name, subject=_subj, html_content=_html
            ))
            logger.info(f"[Workflow] Email envoye (async) a {user.email} pour '{workflow_name}'")
        except Exception as e:
            logger.warning(f"[Workflow] Erreur email: {e}")

    # In-app notification (stored via centralized config helpers)
    try:
        from utils import load_admin_config, save_admin_config
        cfg = load_admin_config()
        notif_key = f"workflow_notifs_{user.id}"
        notifs = cfg.get(notif_key, [])
        notifs.append({
            "id": f"wf_{workflow_name}_{datetime.now(timezone.utc).isoformat()}",
            "workflow_name": workflow_name,
            "status": status,
            "steps": step_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        cfg[notif_key] = notifs[-20:]
        save_admin_config(cfg)
    except Exception as e:
        logger.warning(f"[Workflow] Erreur notification in-app: {e}")

@workflows_router.post("", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreateSchema, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # #127 — Validate that steps is a non-empty list
    if not workflow.steps or not isinstance(workflow.steps, list) or len(workflow.steps) == 0:
        raise HTTPException(status_code=400, detail="Un workflow doit contenir au moins une etape")
    # CORRECTION : si status est fourni on l'utilise ; sinon "active" quand une
    # planification existe (le scheduler ne filtre que status=="active"),
    # "idle" pour les workflows sans planification (exécution manuelle uniquement).
    resolved_status = workflow.status or ("active" if workflow.schedule else "idle")
    new_wf = Workflow(
        user_id=user.id,
        name=workflow.name,
        description=workflow.description,
        steps=workflow.steps,
        schedule=workflow.schedule,
        status=resolved_status,
    )
    db.add(new_wf)
    await db.commit()
    await db.refresh(new_wf)
    return WorkflowResponse(id=new_wf.id, name=new_wf.name, description=new_wf.description, steps=new_wf.steps, schedule=new_wf.schedule, status=new_wf.status, result=_normalize_result(new_wf.result), last_run=new_wf.last_run, created_at=new_wf.created_at)

@workflows_router.get("", response_model=List[WorkflowResponse])
async def get_workflows(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), limit: int = 100, offset: int = 0):
    # #50 — Add pagination to prevent loading all workflows in memory
    result = await db.execute(
        select(Workflow).where(Workflow.user_id == user.id)
        .order_by(Workflow.created_at.desc())
        .limit(min(limit, 200)).offset(offset)
    )
    workflows = result.scalars().all()
    return [WorkflowResponse(id=w.id, name=w.name, description=w.description, steps=w.steps, schedule=w.schedule, status=w.status, result=_normalize_result(w.result), last_run=w.last_run, created_at=w.created_at) for w in workflows]


# ─── Email Settings (must be before /{workflow_id} routes) ──────
from pydantic import BaseModel as _BM
from typing import Optional as _Opt
import re as _re
import uuid as _uuid

class EmailSettingsUpdate(_BM):
    email_prefix: _Opt[str] = None
    workflow_emails: _Opt[list] = None
    approved_senders: _Opt[list] = None

@workflows_router.get("/email-settings")
async def get_email_settings(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    settings = user.settings or {}
    return {
        "email_prefix": settings.get("wf_email_prefix", user.name.split()[0].lower() if user.name else "mon"),
        "email_domain": "zayado.ai",
        "workflow_emails": settings.get("wf_workflow_emails", []),
        "approved_senders": settings.get("wf_approved_senders", []),
    }

@workflows_router.put("/email-settings")
async def update_email_settings(body: EmailSettingsUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    settings = dict(user.settings or {})
    if body.email_prefix is not None:
        prefix = _re.sub(r'[^a-zA-Z0-9._-]', '', body.email_prefix.strip().lower())
        if len(prefix) < 2:
            raise HTTPException(status_code=400, detail="Le prefixe doit contenir au moins 2 caracteres")
        if len(prefix) > 30:
            raise HTTPException(status_code=400, detail="Le prefixe ne peut pas depasser 30 caracteres")
        settings["wf_email_prefix"] = prefix
    if body.workflow_emails is not None:
        cleaned = []
        for we in body.workflow_emails:
            addr = _re.sub(r'[^a-zA-Z0-9._-]', '', str(we.get("address", "")).strip().lower())
            if addr:
                cleaned.append({"id": we.get("id") or str(_uuid.uuid4()), "address": addr, "instructions": str(we.get("instructions", ""))[:500]})
        settings["wf_workflow_emails"] = cleaned
    if body.approved_senders is not None:
        cleaned = []
        for s in body.approved_senders:
            email = str(s.get("email", "")).strip().lower()
            if "@" in email:
                cleaned.append({"id": s.get("id") or str(_uuid.uuid4()), "email": email})
        settings["wf_approved_senders"] = cleaned
    await db.execute(update(User).where(User.id == user.id).values(settings=settings))
    await db.commit()
    return {"status": "ok", "email_prefix": settings.get("wf_email_prefix", ""), "email_domain": "zayado.ai", "workflow_emails": settings.get("wf_workflow_emails", []), "approved_senders": settings.get("wf_approved_senders", [])}


@workflows_router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id, Workflow.user_id == user.id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowResponse(id=workflow.id, name=workflow.name, description=workflow.description, steps=workflow.steps, schedule=workflow.schedule, status=workflow.status, result=_normalize_result(workflow.result), last_run=workflow.last_run, created_at=workflow.created_at)

@workflows_router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, data: WorkflowCreateSchema, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id, Workflow.user_id == user.id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    update_values = dict(name=data.name, description=data.description, steps=data.steps, schedule=data.schedule)
    if data.status:
        update_values["status"] = data.status
    elif data.schedule and workflow.status == "idle":
        # Si on ajoute une planification à un workflow idle, l'activer automatiquement
        update_values["status"] = "active"
    elif not data.schedule and workflow.status == "active":
        # Si on supprime la planification, repasser en idle
        update_values["status"] = "idle"
    await db.execute(update(Workflow).where(Workflow.id == workflow_id).values(**update_values))
    await db.commit()
    await db.refresh(workflow)
    return WorkflowResponse(id=workflow.id, name=workflow.name, description=workflow.description, steps=workflow.steps, schedule=workflow.schedule, status=workflow.status, result=_normalize_result(workflow.result), last_run=workflow.last_run, created_at=workflow.created_at)

@workflows_router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id, Workflow.user_id == user.id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.execute(update(Workflow).where(Workflow.id == workflow_id).values(status="running"))
    await db.commit()
    step_results = []
    mammoth_key = os.environ.get('MAMMOTH_API_KEY', '')
    for i, step in enumerate(workflow.steps or []):
        step_type = step.get("type", "prompt")  # "prompt" | "agent"
        step_prompt = step.get("prompt") or step.get("content") or step.get("label") or step.get("name") or f"Step {i+1}"
        step_name = step.get("label") or step.get("name") or step.get("prompt") or f"Etape {i+1}"

        # Inject previous step results as context
        if i > 0 and step_results:
            prev_context = "\n".join([f"[Etape {r['step']}]: {r['result'][:500]}" for r in step_results if r.get('status') == 'completed'])
            step_prompt = f"Contexte des etapes precedentes:\n{prev_context}\n\nTache actuelle: {step_prompt}"

        # Agent step — use custom agent
        if step_type == "agent" and step.get("agent_id"):
            from models import CustomAgent as CA
            agent_result = await db.execute(select(CA).where(CA.id == step["agent_id"]))
            agent = agent_result.scalar_one_or_none()
            if agent and mammoth_key:
                system = agent.system_prompt or "Tu es un assistant professionnel."
                model = "claude-sonnet-4-5" if agent.model_preference == "pro" else "claude-haiku-4-5"
                try:
                    async with httpx.AsyncClient(timeout=60.0) as http_client:
                        response = await http_client.post(
                            f"{MAMMOTH_BASE_URL}/chat/completions",
                            headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                            json={"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": step_prompt}], "max_tokens": agent.max_tokens or 4096, "temperature": agent.temperature or 0.7}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            step_results.append({"step": i + 1, "name": f"{step_name} ({agent.name})", "result": content, "status": "completed"})
                        else:
                            step_results.append({"step": i + 1, "name": step_name, "result": f"Erreur agent: {response.status_code}", "status": "error"})
                except Exception as e:
                    step_results.append({"step": i + 1, "name": step_name, "result": str(e), "status": "error"})
            else:
                step_results.append({"step": i + 1, "name": step_name, "result": "Agent introuvable ou API non configuree", "status": "error"})
            continue

        # Standard prompt step
        # Use sonar-pro (web search) if step asks for web/search/site/url access
        _web_keywords = ["recherch", "site", "web", "url", "http", "internet", "google", "info sur", "infos sur", "analyse de"]
        needs_web = any(kw in step_prompt.lower() for kw in _web_keywords)
        prompt_model = "sonar-pro" if needs_web else "claude-haiku-4-5-20251001"
        system_msg = (
            "Tu es un assistant professionnel avec acces a Internet. Recherche et analyse les informations demandees."
            if needs_web else
            "Tu es un assistant professionnel. Execute cette etape de workflow."
        )
        if mammoth_key:
            try:
                async with httpx.AsyncClient(timeout=60.0) as http_client:
                    response = await http_client.post(
                        f"{MAMMOTH_BASE_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {mammoth_key}", "Content-Type": "application/json"},
                        json={"model": prompt_model, "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": step_prompt}], "max_tokens": 2048, "temperature": 0.3}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        step_results.append({"step": i + 1, "name": step_name, "result": content, "status": "completed"})
                    else:
                        step_results.append({"step": i + 1, "name": step_name, "result": f"Error: {response.status_code}", "status": "error"})
            except Exception as e:
                step_results.append({"step": i + 1, "name": step_name, "result": str(e), "status": "error"})
        else:
            step_results.append({"step": i + 1, "name": step_name, "result": "Mammoth IA non configure — vérifiez MAMMOTH_API_KEY dans les variables d'environnement.", "status": "error"})
    exec_status = "completed" if all(r.get("status") == "completed" for r in step_results) else "error"
    combined_result = "\n\n".join([f"### {r['name']}\n{r['result']}" for r in step_results])

    # Check if any step contains email content → require approval before sending
    has_email_step = any(
        s.get("type") == "email" or "email" in (s.get("prompt", "") + s.get("label", "")).lower()
        for s in (workflow.steps or [])
    )

    if has_email_step and exec_status == "completed":
        # Pause workflow → pending_approval, send approval email to user
        await db.execute(update(Workflow).where(Workflow.id == workflow_id).values(
            status="pending_approval",
            result=combined_result,
            last_run=datetime.now(timezone.utc)
        ))
        await db.commit()

        # Send approval email
        _send_approval_email(user, workflow, combined_result)

        return {"status": "pending_approval", "results": step_results, "step_results": step_results, "combined_result": combined_result, "message": "Un email de validation vous a ete envoye. Cliquez sur le lien pour approuver l'envoi."}

    # No email step or error → proceed normally

    # CORRECTION: apres execution, repasser "active" si planifie pour que
    # le scheduler puisse relancer a la prochaine occurrence.
    result_wf2 = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf_refreshed = result_wf2.scalar_one_or_none()
    post_status = "active" if (wf_refreshed and wf_refreshed.schedule) else exec_status

    await db.execute(update(Workflow).where(Workflow.id == workflow_id).values(
        status=post_status,
        result=combined_result,
        last_run=datetime.now(timezone.utc)
    ))
    await db.commit()

    # Send workflow completion notification (email + in-app)
    _send_workflow_notification(user, workflow.name, exec_status, len(step_results))

    return {"status": exec_status, "results": step_results, "step_results": step_results, "combined_result": combined_result}

@workflows_router.patch("/{workflow_id}/schedule")
async def update_schedule(workflow_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id, Workflow.user_id == user.id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.execute(update(Workflow).where(Workflow.id == workflow_id).values(schedule=data.get("schedule")))
    await db.commit()
    return {"status": "updated", "schedule": data.get("schedule")}

@workflows_router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(delete(Workflow).where(Workflow.id == workflow_id, Workflow.user_id == user.id))
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"status": "deleted"}


# ─── Approval endpoint (public — triggered by email link) ───
@workflows_router.get("/{workflow_id}/approve")
async def approve_workflow(workflow_id: str, token: str, db: AsyncSession = Depends(get_db)):
    """Approve a pending workflow email — triggered by clicking the link in the approval email."""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow introuvable")
    if workflow.status != "pending_approval":
        return {"status": "already_processed", "message": "Ce workflow a deja ete traite."}

    # Verify token
    expected = _generate_approval_token(workflow_id, workflow.user_id)
    if token != expected:
        raise HTTPException(status_code=403, detail="Lien d'approbation invalide")

    # Get user
    user_result = await db.execute(select(User).where(User.id == workflow.user_id))
    user = user_result.scalar_one_or_none()

    # Send the actual workflow emails to recipients
    email_settings = (user.settings or {}).get("wf_workflow_emails", []) if user else []
    if email_settings and workflow.result:
        from utils import send_brevo_email
        for we in email_settings:
            addr = we.get("address", "")
            if addr and "@" in addr:
                try:
                    send_brevo_email(
                        to_email=addr,
                        to_name=addr.split("@")[0],
                        subject=f"[ZAYADO] Workflow — {workflow.name}",
                        html_content=f"<div style='font-family:Arial;padding:20px;'>{workflow.result.replace(chr(10), '<br>')}</div>"
                    )
                    logger.info(f"[Workflow] Email envoye a {addr}")
                except Exception as e:
                    logger.warning(f"[Workflow] Erreur envoi a {addr}: {e}")

    # Mark as completed
    post_status = "active" if workflow.schedule else "completed"
    await db.execute(update(Workflow).where(Workflow.id == workflow_id).values(status=post_status))
    await db.commit()

    # Return a nice HTML page confirming the approval
    html = f"""
    <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Workflow approuve</title></head>
    <body style="font-family:Arial,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#F5F5F0;margin:0;">
        <div style="text-align:center;background:white;padding:40px;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,0.1);max-width:400px;">
            <div style="width:60px;height:60px;background:#059669;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <h2 style="color:#059669;margin-bottom:8px;">Emails envoyes !</h2>
            <p style="color:#374151;">Le workflow <strong>{workflow.name}</strong> a ete approuve. Les emails ont ete envoyes a vos destinataires.</p>
            <a href="https://app.zayado.net/app/workflows" style="display:inline-block;margin-top:16px;padding:10px 24px;background:#1E3A8A;color:white;border-radius:8px;text-decoration:none;">Retour aux workflows</a>
        </div>
    </body></html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)

