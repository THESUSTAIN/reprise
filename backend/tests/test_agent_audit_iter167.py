"""Audit Agent IA iter167 — re-validation des 3 fixes (Discord, use_user_memory, chat retire)."""
import os
import re
import requests
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
EMAIL = "admin@zayado.net"
PASSWORD = "1@Elshaddai1"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def hdrs(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def temp_agent(hdrs):
    """Cree un agent temporaire pour tests deploy/update, supprime ensuite."""
    payload = {
        "name": "TEST_iter167_audit",
        "description": "Agent audit iter167",
        "avatar": "bot",
        "color": "#1D4E8A",
        "system_prompt": "Tu es un agent de test.",
        "tools": ["web_search"],
        "model_preference": "auto",
        "temperature": 0.7,
        "max_tokens": 2048,
        "use_user_memory": False,
    }
    r = requests.post(f"{BASE}/api/custom-agents", json=payload, headers=hdrs, timeout=30)
    if r.status_code == 400 and "Limite" in r.text:
        # Plan limit hit — clean up old TEST agents and retry
        lst = requests.get(f"{BASE}/api/custom-agents", headers=hdrs, timeout=30).json()
        for a in lst:
            if a["name"].startswith("TEST_"):
                requests.delete(f"{BASE}/api/custom-agents/{a['id']}", headers=hdrs, timeout=30)
        r = requests.post(f"{BASE}/api/custom-agents", json=payload, headers=hdrs, timeout=30)
    assert r.status_code in (200, 201), f"Create agent failed: {r.status_code} {r.text[:300]}"
    agent = r.json()
    yield agent
    requests.delete(f"{BASE}/api/custom-agents/{agent['id']}", headers=hdrs, timeout=30)


# ── 1. CRÉATION AGENT (use_user_memory dans payload + reponse) ────────────────
def test_create_returns_use_user_memory(temp_agent):
    assert "use_user_memory" in temp_agent, "use_user_memory absent de la reponse create"
    assert temp_agent["use_user_memory"] is False, f"Attendu False, recu {temp_agent['use_user_memory']}"


# ── 2. GET AGENT round-trip use_user_memory persiste ──────────────────────────
def test_get_persists_use_user_memory(hdrs, temp_agent):
    r = requests.get(f"{BASE}/api/custom-agents/{temp_agent['id']}", headers=hdrs, timeout=30)
    assert r.status_code == 200
    assert r.json().get("use_user_memory") is False


# ── 3. UPDATE use_user_memory=True persiste ───────────────────────────────────
def test_update_use_user_memory_persists(hdrs, temp_agent):
    upd = requests.put(
        f"{BASE}/api/custom-agents/{temp_agent['id']}",
        json={"use_user_memory": True},
        headers=hdrs, timeout=30,
    )
    assert upd.status_code == 200
    assert upd.json().get("use_user_memory") is True
    # Verify with GET
    g = requests.get(f"{BASE}/api/custom-agents/{temp_agent['id']}", headers=hdrs, timeout=30)
    assert g.json().get("use_user_memory") is True, "Pas persiste apres GET"


# ── 4. DEPLOY DISCORD ─────────────────────────────────────────────────────────
def test_deploy_discord(hdrs, temp_agent):
    r = requests.post(
        f"{BASE}/api/custom-agents/{temp_agent['id']}/deploy",
        json={"channels": ["discord"]},
        headers=hdrs, timeout=30,
    )
    assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
    body = r.json()
    assert "discord_status" in body, "discord_status absent"
    assert body["discord_status"] in ("no_connection", "no_bot_token", "active"), f"Status inattendu: {body['discord_status']}"
    assert "deploy_instructions" in body
    assert "discord" in body["deploy_instructions"], "deploy_instructions.discord absent"
    assert "/discord" in body["deploy_instructions"]["discord"]


# ── 5. DEPLOY TELEGRAM ────────────────────────────────────────────────────────
def test_deploy_telegram(hdrs, temp_agent):
    r = requests.post(
        f"{BASE}/api/custom-agents/{temp_agent['id']}/deploy",
        json={"channels": ["telegram"]},
        headers=hdrs, timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert "telegram_status" in body


# ── 6. DEPLOY WHATSAPP ────────────────────────────────────────────────────────
def test_deploy_whatsapp(hdrs, temp_agent):
    r = requests.post(
        f"{BASE}/api/custom-agents/{temp_agent['id']}/deploy",
        json={"channels": ["whatsapp"]},
        headers=hdrs, timeout=30,
    )
    assert r.status_code == 200
    assert "whatsapp" in r.json().get("deploy_instructions", {})


# ── 7. DEPLOY WEB ─────────────────────────────────────────────────────────────
def test_deploy_web(hdrs, temp_agent):
    r = requests.post(
        f"{BASE}/api/custom-agents/{temp_agent['id']}/deploy",
        json={"channels": ["web"]},
        headers=hdrs, timeout=30,
    )
    assert r.status_code == 200
    web = r.json().get("deploy_instructions", {}).get("web", "")
    assert "<script" in web and "/api/widget/" in web


# ── 8. DEPLOY combine 3 canaux ────────────────────────────────────────────────
def test_deploy_combined(hdrs, temp_agent):
    r = requests.post(
        f"{BASE}/api/custom-agents/{temp_agent['id']}/deploy",
        json={"channels": ["telegram", "discord", "web"]},
        headers=hdrs, timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("telegram_status") is not None
    assert body.get("discord_status") is not None
    di = body.get("deploy_instructions", {})
    assert "telegram" in di and "discord" in di and "web" in di


# ── 9. TEMPLATES ──────────────────────────────────────────────────────────────
def test_templates(hdrs):
    r = requests.get(f"{BASE}/api/custom-agents/templates", headers=hdrs, timeout=30)
    assert r.status_code == 200
    assert len(r.json()) >= 4


# ── 10. TOOLS ─────────────────────────────────────────────────────────────────
def test_tools(hdrs):
    r = requests.get(f"{BASE}/api/custom-agents/tools", headers=hdrs, timeout=30)
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ── 11. DUPLICATE clean (sans tokens) ─────────────────────────────────────────
def test_duplicate_clean(hdrs, temp_agent):
    r = requests.post(f"{BASE}/api/custom-agents/{temp_agent['id']}/duplicate", headers=hdrs, timeout=30)
    assert r.status_code in (200, 201)
    dup = r.json()
    assert dup["name"].endswith("(copie)")
    assert not dup.get("webhook_token"), "webhook_token NE DOIT PAS etre copie"
    # cleanup
    requests.delete(f"{BASE}/api/custom-agents/{dup['id']}", headers=hdrs, timeout=30)


# ── 12. DELETE OK ─────────────────────────────────────────────────────────────
def test_delete_works(hdrs):
    # cree puis supprime
    r = requests.post(f"{BASE}/api/custom-agents", json={
        "name": "TEST_to_delete", "system_prompt": "test"
    }, headers=hdrs, timeout=30)
    if r.status_code == 400:
        pytest.skip("Limite plan atteinte")
    aid = r.json()["id"]
    d = requests.delete(f"{BASE}/api/custom-agents/{aid}", headers=hdrs, timeout=30)
    assert d.status_code == 200
    g = requests.get(f"{BASE}/api/custom-agents/{aid}", headers=hdrs, timeout=30)
    assert g.status_code == 404


# ── 13. LIMITE PLAN ───────────────────────────────────────────────────────────
def test_plan_limit(hdrs):
    """Verifie que le backend renvoie une erreur claire quand >= max."""
    # On compte les agents actuels
    lst = requests.get(f"{BASE}/api/custom-agents", headers=hdrs, timeout=30).json()
    own = [a for a in lst if not a.get("shared")]
    # pro = 5
    if len(own) < 5:
        pytest.skip(f"Seulement {len(own)} agents — pas a la limite")
    r = requests.post(f"{BASE}/api/custom-agents", json={"name": "TEST_overflow", "system_prompt": "x"}, headers=hdrs, timeout=30)
    assert r.status_code in (400, 403), f"Attendu 400/403, recu {r.status_code}"
    assert "imite" in r.text or "max" in r.text.lower()


# ── 14. MARKETING PAGE: Discord present, iMessage absent ──────────────────────
def test_marketing_page_discord_imessage():
    """Verifie agent-ia.html: 0 occurrence iMessage, Discord present."""
    candidates = [
        "/app/frontend/public/preview/agent-ia.html",
        "/app/html-wordpress/zayado-plugin/includes/page-agent-ia.php",
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # Count iMessage (case-insensitive but excluding "message" alone)
        imessage_count = len(re.findall(r"iMessage", content, re.IGNORECASE))
        discord_count = len(re.findall(r"Discord", content))
        assert imessage_count == 0, f"{path}: {imessage_count} occurrences iMessage trouvees (attendu 0)"
        assert discord_count >= 1, f"{path}: Discord absent (attendu >=1)"
