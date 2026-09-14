"""Backend tests for iter184: Starter Templates, Notif Settings, Guest Auth, Health."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-panel-416.preview.emergentagent.com').rstrip('/')


@pytest.fixture(scope="module")
def auth_token():
    r = requests.post(f"{BASE_URL}/api/auth/guest", timeout=30)
    assert r.status_code == 200, f"Guest login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    tok = data.get("token") or data.get("access_token")
    assert tok, f"No token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def client(auth_token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {auth_token}"})
    return s


def test_health():
    r = requests.get(f"{BASE_URL}/api/health", timeout=15)
    assert r.status_code == 200, r.text[:300]


def test_guest_login_returns_token():
    r = requests.post(f"{BASE_URL}/api/auth/guest", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert (data.get("token") or data.get("access_token"))


def test_starter_templates(client):
    r = client.get(f"{BASE_URL}/api/vision/starter-templates", timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "templates" in data
    templates = data["templates"]
    assert len(templates) == 4
    ids = {t["id"] for t in templates}
    assert ids == {"lancement", "croissance", "equilibre", "rayonnement"}
    for t in templates:
        assert t.get("emoji")
        assert t.get("label")
        assert t.get("description")
        assert len(t.get("cards", [])) == 5


def test_notif_settings_defaults(client):
    r = client.get(f"{BASE_URL}/api/vision/notif-settings", timeout=15)
    assert r.status_code == 200, r.text[:300]
    settings = r.json().get("settings", {})
    assert settings.get("weekly_reminder") is True
    assert settings.get("include_coach_actions") is True


def test_notif_settings_update_persist(client):
    # Set to false
    r = client.put(f"{BASE_URL}/api/vision/notif-settings",
                   json={"settings": {"weekly_reminder": False}}, timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("ok") is True
    assert data["settings"]["weekly_reminder"] is False
    assert data["settings"]["include_coach_actions"] is True

    # Verify persistence via GET
    r2 = client.get(f"{BASE_URL}/api/vision/notif-settings", timeout=15)
    assert r2.json()["settings"]["weekly_reminder"] is False

    # Restore default
    client.put(f"{BASE_URL}/api/vision/notif-settings",
               json={"settings": {"weekly_reminder": True}}, timeout=15)
