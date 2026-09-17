"""Iter169 — Test agent deploy flow (Telegram + WhatsApp Cloud + idempotence)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "1@Elshaddai1"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    token = r.json().get("access_token") or r.json().get("token")
    assert token, f"no token in login response: {r.json()}"
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def created_agent(session):
    payload = {
        "name": "TEST_iter169_deploy",
        "description": "Test deploy flow",
        "system_prompt": "Tu es un agent de test.",
        "tools": ["calculator"],
        "model_preference": "fast",
    }
    r = session.post(f"{BASE_URL}/api/custom-agents", json=payload)
    assert r.status_code == 200, f"create failed: {r.status_code} {r.text[:300]}"
    agent = r.json()
    assert agent["name"] == "TEST_iter169_deploy"
    assert agent["deployed_channels"] == [] or agent["deployed_channels"] is None
    yield agent
    # cleanup
    session.delete(f"{BASE_URL}/api/custom-agents/{agent['id']}")


def test_list_agents(session):
    r = session.get(f"{BASE_URL}/api/custom-agents")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        # all agents must expose deployed_channels (list)
        assert "deployed_channels" in data[0]
        assert isinstance(data[0]["deployed_channels"], list)


def test_deploy_telegram_no_connection(session, created_agent):
    """Deploy to telegram WITHOUT a Telegram connection -> should still 200 and persist channel."""
    aid = created_agent["id"]
    r = session.post(f"{BASE_URL}/api/custom-agents/{aid}/deploy", json={"channels": ["telegram"]})
    assert r.status_code == 200, f"deploy failed: {r.status_code} {r.text[:300]}"
    body = r.json()
    assert "deployed_channels" in body
    assert "telegram" in body["deployed_channels"]
    # webhook_url should be present
    assert "webhook_url" in body and body["webhook_url"]
    # telegram_status should report no_connection / no_bot_token / error (not None)
    assert body.get("telegram_status") in ("no_connection", "no_bot_token") or "error" in str(body.get("telegram_status", "")).lower() or body.get("telegram_status") == "active"

    # GET to verify persistence
    g = session.get(f"{BASE_URL}/api/custom-agents/{aid}")
    assert g.status_code == 200
    assert "telegram" in g.json()["deployed_channels"]


def test_deploy_idempotent(session, created_agent):
    """Re-deploying same channel must not duplicate it."""
    aid = created_agent["id"]
    r = session.post(f"{BASE_URL}/api/custom-agents/{aid}/deploy", json={"channels": ["telegram"]})
    assert r.status_code == 200
    chans = r.json()["deployed_channels"]
    # exactly one 'telegram' entry
    assert chans.count("telegram") == 1


def test_deploy_multiple_channels(session, created_agent):
    """Deploy to telegram + whatsapp + web -> all persisted."""
    aid = created_agent["id"]
    r = session.post(
        f"{BASE_URL}/api/custom-agents/{aid}/deploy",
        json={"channels": ["telegram", "whatsapp", "web"]},
    )
    assert r.status_code == 200
    chans = r.json()["deployed_channels"]
    assert set(chans) == {"telegram", "whatsapp", "web"}

    g = session.get(f"{BASE_URL}/api/custom-agents/{aid}")
    assert set(g.json()["deployed_channels"]) == {"telegram", "whatsapp", "web"}


def test_deploy_undeploy(session, created_agent):
    """Empty channels -> undeploy (deployed_channels=[])."""
    aid = created_agent["id"]
    r = session.post(f"{BASE_URL}/api/custom-agents/{aid}/deploy", json={"channels": []})
    assert r.status_code == 200
    assert r.json()["deployed_channels"] == []


def test_whatsapp_web_connect_service_response(session, created_agent):
    """WA Web microservice may be up or down — must NOT 500. Acceptable: 200, 503."""
    aid = created_agent["id"]
    r = session.post(f"{BASE_URL}/api/custom-agents/{aid}/whatsapp-web-connect")
    assert r.status_code in (200, 503), f"unexpected: {r.status_code} {r.text[:200]}"


def test_deploy_unknown_agent_404(session):
    r = session.post(f"{BASE_URL}/api/custom-agents/nope-fake-id/deploy", json={"channels": ["telegram"]})
    assert r.status_code == 404
