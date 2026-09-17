"""Iter168 — Test custom-agents endpoints P0 fixes (use_user_memory, deploy, CRUD)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "1@Elshaddai1"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    tok = data.get("token") or data.get("access_token")
    assert tok, f"No token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── GET list ──
def test_list_custom_agents_200(headers):
    r = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers, timeout=30)
    assert r.status_code == 200, f"GET failed: {r.status_code} {r.text[:300]}"
    assert isinstance(r.json(), list)


# ── POST minimal create ──
def test_create_agent_minimal(headers):
    payload = {"name": "TEST_iter168_min", "system_prompt": "Tu es utile.", "use_user_memory": False}
    r = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers, json=payload, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    data = r.json()
    assert data["name"] == "TEST_iter168_min"
    assert data["use_user_memory"] is False, f"use_user_memory not persisted on create: {data}"
    # Cleanup
    requests.delete(f"{BASE_URL}/api/custom-agents/{data['id']}", headers=headers, timeout=30)


# ── POST from-template ──
def test_create_from_template_200(headers):
    r = requests.post(f"{BASE_URL}/api/custom-agents/from-template",
                      headers=headers, json={"template_id": "assistant_commercial"}, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    data = r.json()
    assert "use_user_memory" in data
    assert data.get("id")
    # Cleanup
    requests.delete(f"{BASE_URL}/api/custom-agents/{data['id']}", headers=headers, timeout=30)


# ── PUT update use_user_memory + deployed_channels ──
def test_update_agent_fields(headers):
    # Create agent
    c = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers,
                      json={"name": "TEST_iter168_upd", "system_prompt": "Test"}, timeout=30)
    assert c.status_code == 200
    aid = c.json()["id"]
    # Update
    r = requests.put(f"{BASE_URL}/api/custom-agents/{aid}", headers=headers,
                     json={"use_user_memory": False, "deployed_channels": ["web", "telegram"]}, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    d = r.json()
    assert d["use_user_memory"] is False
    assert set(d["deployed_channels"]) == {"web", "telegram"}
    # Verify persisted via GET
    g = requests.get(f"{BASE_URL}/api/custom-agents/{aid}", headers=headers, timeout=30)
    assert g.status_code == 200
    gd = g.json()
    assert gd["use_user_memory"] is False
    # Cleanup
    requests.delete(f"{BASE_URL}/api/custom-agents/{aid}", headers=headers, timeout=30)


# ── POST deploy with 4 channels ──
def test_deploy_agent_all_channels(headers):
    c = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers,
                      json={"name": "TEST_iter168_deploy", "system_prompt": "Test"}, timeout=30)
    aid = c.json()["id"]
    r = requests.post(f"{BASE_URL}/api/custom-agents/{aid}/deploy", headers=headers,
                      json={"channels": ["web", "whatsapp", "telegram", "discord"]}, timeout=60)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    d = r.json()
    assert "webhook_url" in d and d["webhook_url"].startswith("http")
    assert set(d["deployed_channels"]) >= {"web", "whatsapp", "telegram", "discord"}
    assert "deploy_instructions" in d
    # Cleanup
    requests.delete(f"{BASE_URL}/api/custom-agents/{aid}", headers=headers, timeout=30)


# ── DELETE ──
def test_delete_agent(headers):
    c = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers,
                      json={"name": "TEST_iter168_del", "system_prompt": "Test"}, timeout=30)
    aid = c.json()["id"]
    r = requests.delete(f"{BASE_URL}/api/custom-agents/{aid}", headers=headers, timeout=30)
    assert r.status_code == 200
    # Verify 404 on GET
    g = requests.get(f"{BASE_URL}/api/custom-agents/{aid}", headers=headers, timeout=30)
    assert g.status_code == 404
