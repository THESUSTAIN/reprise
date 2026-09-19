"""
Iteration 170 — Non-regression backend tests after Railway deploy-config fix
(added /app/_legacy/app-main/WhatsApp-service, /app/public-site, restored root
deploy files). No backend code was supposed to change.

Covers:
 - Health endpoint
 - Guest login (POST /api/auth/guest) + JWT validity
 - Authenticated lightweight endpoints (GET /api/auth/me, /api/profile/org, /api/custom-agents)
 - WhatsApp Web endpoints WITHOUT WA_SERVICE_URL configured -> handled error, not a 500
"""
import os
import base64
import json

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL is missing")
BASE_URL = base_url.rstrip("/")


@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def guest_token(api_client):
    r = api_client.post(f"{BASE_URL}/api/auth/guest", json={}, timeout=60)
    if r.status_code != 200:
        pytest.fail(f"Guest login failed {r.status_code}: {r.text[:400]}")
    data = r.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        pytest.fail(f"No token in guest response: {json.dumps(data)[:400]}")
    return token


@pytest.fixture(scope="session")
def auth_client(guest_token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {guest_token}"})
    return s


# Guest/free plan cannot own agents (403 by design), so we provision a
# throwaway "pro" user to exercise the WhatsApp Web endpoints.
TEST_PRO_EMAIL = "test_iter170_wa@example.com"
TEST_PRO_PASSWORD = "TestIter170!pwd"
DB_PATH = "/app/backend/zayado.db"


@pytest.fixture(scope="session")
def pro_client(api_client):
    import sqlite3
    r = api_client.post(f"{BASE_URL}/api/auth/register", timeout=60, json={
        "email": TEST_PRO_EMAIL, "password": TEST_PRO_PASSWORD, "name": "TEST Iter170"})
    if r.status_code not in (200, 201, 400):
        pytest.fail(f"register failed {r.status_code}: {r.text[:300]}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET plan='pro' WHERE email=?", (TEST_PRO_EMAIL,))
    conn.commit()
    conn.close()
    lr = api_client.post(f"{BASE_URL}/api/auth/login", timeout=60,
                         json={"email": TEST_PRO_EMAIL, "password": TEST_PRO_PASSWORD})
    if lr.status_code != 200:
        pytest.fail(f"login failed {lr.status_code}: {lr.text[:300]}")
    token = lr.json().get("token") or lr.json().get("access_token")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {token}"})
    yield s
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM custom_agents WHERE user_id IN (SELECT id FROM users WHERE email=?)",
                 (TEST_PRO_EMAIL,))
    conn.execute("DELETE FROM users WHERE email=?", (TEST_PRO_EMAIL,))
    conn.commit()
    conn.close()


# ── Module: health / server boot ──
class TestHealth:
    def test_health(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/health", timeout=30)
        assert r.status_code == 200, r.text[:300]
        assert r.json().get("status") == "healthy"

    def test_spa_served(self, api_client):
        r = api_client.get(f"{BASE_URL}/", timeout=30)
        assert r.status_code == 200
        assert "<div id=\"root\"" in r.text or "<html" in r.text.lower()


# ── Module: auth (guest login) ──
class TestGuestAuth:
    def test_guest_login_returns_jwt(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/guest", json={}, timeout=60)
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        token = data.get("token") or data.get("access_token")
        assert isinstance(token, str) and len(token) > 20
        # JWT structure with a sub claim
        parts = token.split(".")
        assert len(parts) == 3, "token is not a JWT"
        pad = lambda s: s + "=" * (-len(s) % 4)
        payload = json.loads(base64.urlsafe_b64decode(pad(parts[1])))
        assert payload.get("sub"), f"JWT missing sub: {payload}"

    def test_me_with_guest_token(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/auth/me", timeout=30)
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        assert data.get("id")
        assert "email" in data

    def test_me_without_token_is_401(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/auth/me", timeout=30)
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_me_with_bad_token_is_401(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/auth/me", timeout=30,
                           headers={"Authorization": "Bearer not.a.jwt"})
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"


# ── Module: lightweight authenticated endpoints (regression) ──
class TestAuthenticatedEndpoints:
    @pytest.mark.parametrize("path", [
        "/api/profile/org",
        "/api/custom-agents",
        "/api/auth/usage",
        "/api/config",
        "/api/features",
    ])
    def test_endpoint_no_server_error(self, auth_client, path):
        r = auth_client.get(f"{BASE_URL}{path}", timeout=60)
        assert r.status_code < 500, f"{path} -> {r.status_code}: {r.text[:300]}"
        assert r.status_code in (200, 401, 403, 404), f"{path} -> {r.status_code}: {r.text[:200]}"

    def test_custom_agents_list_shape(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/custom-agents", timeout=60)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert isinstance(data, (list, dict))


# ── Module: WhatsApp Web endpoints without WA_SERVICE_URL ──
AGENT_ID_FAKE = "TEST_nonexistent_agent_iter170"


class TestWhatsAppWebUnconfigured:
    @pytest.fixture(scope="class")
    def wa_agent(self, pro_client):
        """Create a throwaway agent to exercise WA endpoints."""
        r = pro_client.post(f"{BASE_URL}/api/custom-agents", timeout=60, json={
            "name": "TEST_iter170_wa_agent",
            "description": "regression test agent",
            "system_prompt": "You are a test agent.",
        })
        if r.status_code not in (200, 201):
            pytest.fail(f"agent creation failed {r.status_code}: {r.text[:300]}")
        body = r.json()
        aid = body.get("id") or (body.get("agent") or {}).get("id")
        assert aid, f"no agent id in response: {json.dumps(body)[:300]}"
        yield aid
        pro_client.delete(f"{BASE_URL}/api/custom-agents/{aid}", timeout=60)

    def test_wa_connect_handled_error(self, pro_client, wa_agent):
        r = pro_client.post(f"{BASE_URL}/api/custom-agents/{wa_agent}/whatsapp-web-connect",
                            json={}, timeout=60)
        assert r.status_code != 500, f"crash: {r.text[:400]}"
        assert r.status_code == 503, f"expected 503 service non configuré, got {r.status_code}: {r.text[:300]}"
        detail = str(r.json().get("detail", "")).lower()
        assert "whatsapp" in detail and ("configur" in detail or "support" in detail), detail

    def test_wa_status_handled(self, pro_client, wa_agent):
        r = pro_client.get(f"{BASE_URL}/api/custom-agents/{wa_agent}/whatsapp-web-status",
                           timeout=60)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        assert r.json().get("status") == "service_unavailable", r.text[:200]

    def test_wa_reset_handled(self, pro_client, wa_agent):
        r = pro_client.post(f"{BASE_URL}/api/custom-agents/{wa_agent}/whatsapp-web-reset",
                            json={}, timeout=60)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        assert r.json().get("ok") is True

    def test_wa_disconnect_handled(self, pro_client, wa_agent):
        r = pro_client.delete(f"{BASE_URL}/api/custom-agents/{wa_agent}/whatsapp-web-disconnect",
                              timeout=60)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"

    def test_wa_connect_unknown_agent_is_404(self, pro_client):
        r = pro_client.post(f"{BASE_URL}/api/custom-agents/{AGENT_ID_FAKE}/whatsapp-web-connect",
                            json={}, timeout=60)
        assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text[:300]}"

    def test_wa_status_requires_auth(self, api_client, wa_agent):
        r = api_client.get(f"{BASE_URL}/api/custom-agents/{wa_agent}/whatsapp-web-status",
                           timeout=30)
        assert r.status_code in (401, 403), f"unauthenticated access allowed: {r.status_code}"

    def test_guest_plan_cannot_create_agent(self, auth_client):
        r = auth_client.post(f"{BASE_URL}/api/custom-agents", timeout=60,
                             json={"name": "TEST_iter170_guest", "system_prompt": "x"})
        assert r.status_code == 403, f"{r.status_code}: {r.text[:200]}"


# ── Module: agent webhook whatsapp-web endpoints ──
class TestAgentWebhookWA:
    def test_webhook_wa_invalid_token(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/agent-webhook/TEST_bad_token_iter170/whatsapp-web",
                            json={"from": "33600000000", "text": "hello"}, timeout=60)
        assert r.status_code != 500, f"crash: {r.text[:400]}"
        assert r.status_code in (401, 403, 404), f"{r.status_code}: {r.text[:200]}"

    def test_webhook_wa_ready_no_crash(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/agent-webhook/TEST_bad_token_iter170/whatsapp-web-ready",
                            json={"phone": "33600000000"}, timeout=60)
        assert r.status_code != 500, f"crash: {r.text[:400]}"

    @pytest.mark.xfail(reason="KNOWN ISSUE: whatsapp-web-ready never validates the "
                              "webhook token and WA_SERVICE_SECRET defaults to empty "
                              "(no auth) -> returns 200 for any token", strict=False)
    def test_webhook_wa_ready_rejects_invalid_token(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/agent-webhook/TEST_bad_token_iter170/whatsapp-web-ready",
                            json={"phone": "33600000000"}, timeout=60)
        assert r.status_code in (401, 403, 404), f"{r.status_code}: {r.text[:200]}"
