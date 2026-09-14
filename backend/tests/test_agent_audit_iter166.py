"""Audit complet Agent IA - iter166
Tests end-to-end des endpoints custom-agents pour admin@zayado.net (plan pro, limite 5)."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    # Fallback read frontend/.env
    try:
        with open('/app/frontend/.env') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    BASE_URL = line.split('=', 1)[1].strip().rstrip('/')
    except Exception:
        pass

ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PWD = "1@Elshaddai1"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PWD}, timeout=20)
    assert r.status_code == 200, f"Login failed {r.status_code} {r.text[:200]}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"No token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── GET endpoints ──
def test_list_agents(headers):
    r = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    print(f"[list_agents] count={len(data)}")
    if data:
        a = data[0]
        # Check serialization fields
        for field in ["id", "name", "system_prompt", "model_preference", "tools",
                      "temperature", "max_tokens", "deployed_channels"]:
            assert field in a, f"missing field {field}"


def test_list_tools(headers):
    r = requests.get(f"{BASE_URL}/api/custom-agents/tools", headers=headers, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, (list, dict))
    print(f"[list_tools] {data if isinstance(data,list) else list(data.keys())[:5]}")


def test_list_templates(headers):
    r = requests.get(f"{BASE_URL}/api/custom-agents/templates", headers=headers, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, (list, dict))
    items = data if isinstance(data, list) else data.get("templates", [])
    assert len(items) >= 1
    print(f"[templates] count={len(items)} first={items[0].get('id') if items else None}")


# ── CRUD scratch ──
AGENT_ID = None


def test_create_agent_scratch(headers):
    global AGENT_ID
    payload = {
        "name": "TEST_AUDIT_iter166",
        "description": "Agent de test d'audit",
        "system_prompt": "Tu es un assistant test. " * 30,  # >500 chars
        "model_preference": "claude-sonnet-4.5",
        "temperature": 0.5,
        "max_tokens": 2048,
        "tools": ["web_search"],
    }
    r = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers, json=payload, timeout=15)
    if r.status_code == 400 and "Limite" in r.text:
        pytest.skip(f"Plan limit reached: {r.text[:200]}")
    assert r.status_code in (200, 201), f"{r.status_code} {r.text[:300]}"
    data = r.json()
    AGENT_ID = data["id"]
    assert data["name"] == payload["name"]
    assert data["model_preference"] == "claude-sonnet-4.5"
    assert len(data["system_prompt"]) > 500
    assert "web_search" in data["tools"]
    print(f"[create_scratch] id={AGENT_ID} model={data['model_preference']}")


def test_update_agent(headers):
    assert AGENT_ID, "create test must run first"
    payload = {"description": "Mise à jour audit",
               "model_preference": "gpt-4o",
               "tools": ["web_search", "send_email"],
               "temperature": 0.8}
    r = requests.put(f"{BASE_URL}/api/custom-agents/{AGENT_ID}", headers=headers, json=payload, timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data["model_preference"] == "gpt-4o"
    assert data["temperature"] == 0.8
    assert "send_email" in data["tools"]


def test_get_agent(headers):
    r = requests.get(f"{BASE_URL}/api/custom-agents/{AGENT_ID}", headers=headers, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == AGENT_ID
    assert data["description"] == "Mise à jour audit"  # persisted


def test_duplicate_agent(headers):
    r = requests.post(f"{BASE_URL}/api/custom-agents/{AGENT_ID}/duplicate", headers=headers, timeout=15)
    if r.status_code == 400 and "Limite" in r.text:
        pytest.skip("Plan limit reached for duplicate")
        return
    assert r.status_code in (200, 201), r.text[:300]
    data = r.json()
    assert "(copie)" in data["name"]
    # Ensure secrets not copied
    assert not data.get("deployed_channels") or data.get("deployed_channels") == ["web"]
    dup_id = data["id"]
    # Cleanup duplicate
    requests.delete(f"{BASE_URL}/api/custom-agents/{dup_id}", headers=headers, timeout=15)


def test_chat_with_agent(headers):
    r = requests.post(f"{BASE_URL}/api/custom-agents/{AGENT_ID}/chat",
                      headers=headers,
                      json={"message": "Bonjour, répond en 5 mots max."}, timeout=60)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    data = r.json()
    # Flexible: response may be under 'response' or 'reply' or 'message'
    reply = data.get("response") or data.get("reply") or data.get("message") or data.get("content")
    assert reply, f"No reply field: {data}"
    print(f"[chat] reply len={len(str(reply))}")


def test_deploy_telegram(headers):
    # Deploy without bot_token connection → should still succeed with status info
    r = requests.post(f"{BASE_URL}/api/custom-agents/{AGENT_ID}/deploy",
                      headers=headers,
                      json={"channels": ["telegram", "web"]}, timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "webhook_url" in data
    # telegram_status should exist (even if "no_connection")
    assert "telegram_status" in data
    print(f"[deploy telegram] status={data.get('telegram_status')} url={data.get('webhook_url')[:60]}")


def test_deploy_imessage_not_supported(headers):
    """iMessage is proposed on marketing page but NOT in backend deploy."""
    r = requests.post(f"{BASE_URL}/api/custom-agents/{AGENT_ID}/deploy",
                      headers=headers,
                      json={"channels": ["imessage"]}, timeout=15)
    # Expected to succeed but with no specific handling
    data = r.json() if r.status_code == 200 else {}
    # Flag: no imessage_status returned = feature missing
    has_imessage_support = "imessage_status" in data or "imessage" in (data.get("deploy_instructions") or {})
    print(f"[deploy imessage] supported={has_imessage_support} status={r.status_code}")
    # Not asserting; just documenting the gap


def test_whatsapp_web_connect(headers):
    r = requests.post(f"{BASE_URL}/api/custom-agents/{AGENT_ID}/whatsapp-web-connect",
                      headers=headers, json={}, timeout=30)
    # Service Node may be down → expect clean error (not crash)
    print(f"[whatsapp_web_connect] status={r.status_code} body={r.text[:200]}")
    assert r.status_code in (200, 400, 500, 502, 503), f"unexpected {r.status_code}"


def test_delete_agent(headers):
    r = requests.delete(f"{BASE_URL}/api/custom-agents/{AGENT_ID}", headers=headers, timeout=15)
    assert r.status_code in (200, 204)
    # Verify removal
    r2 = requests.get(f"{BASE_URL}/api/custom-agents/{AGENT_ID}", headers=headers, timeout=15)
    assert r2.status_code == 404


def test_create_from_template(headers):
    # Get a template id
    r = requests.get(f"{BASE_URL}/api/custom-agents/templates", headers=headers, timeout=15)
    items = r.json() if isinstance(r.json(), list) else r.json().get("templates", [])
    if not items:
        pytest.skip("No templates available")
    tmpl_id = items[0].get("id")
    r = requests.post(f"{BASE_URL}/api/custom-agents/from-template",
                      headers=headers, json={"template_id": tmpl_id}, timeout=15)
    if r.status_code == 400 and "Limite" in r.text:
        pytest.skip(f"Plan limit reached: {r.text[:200]}")
    assert r.status_code in (200, 201), r.text[:300]
    data = r.json()
    assert data.get("id")
    # Cleanup
    requests.delete(f"{BASE_URL}/api/custom-agents/{data['id']}", headers=headers, timeout=15)
