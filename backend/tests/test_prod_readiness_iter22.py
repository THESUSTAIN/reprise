"""Production readiness smoke test (iter22) — audit critical endpoints."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed {r.status_code} {r.text[:200]}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def h(token):
    return {"Authorization": f"Bearer {token}"}


# Critical user-facing endpoints
ENDPOINTS = [
    "/api/me/profile",
    "/api/tasks",
    "/api/vision",
    "/api/documents",
    "/api/leads",
    "/api/streak",
    "/api/revenue/monthly",
    "/api/energy/today",
    "/api/processes/templates",
    "/api/analyse",
    "/api/branding",
    "/api/prefs/swot",
    "/api/quote/today",
    "/api/collaborateur/history",
    "/api/memory/list",
    "/api/memory/stats",
    "/api/wellness/today",
    "/api/missions/today",
]


@pytest.mark.parametrize("ep", ENDPOINTS)
def test_endpoint_200(ep, h):
    r = requests.get(f"{BASE_URL}{ep}", headers=h, timeout=15)
    assert r.status_code in (200, 201), f"{ep} -> {r.status_code} {r.text[:200]}"


def test_guest_endpoint_status():
    """Guest login should be allowed in preview, forbidden in prod."""
    r = requests.post(f"{BASE_URL}/api/auth/guest", timeout=15)
    # In preview env it's 200, in prod it should be 403
    assert r.status_code in (200, 403)


def test_collab_chat(h):
    r = requests.post(f"{BASE_URL}/api/collaborateur/chat",
                      headers=h,
                      json={"message": "Bonjour, quelle est ma priorité ?"},
                      timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data or "message" in data or "content" in data
    reply = data.get("reply") or data.get("message") or data.get("content")
    assert reply and len(str(reply)) > 5


# Integration /start endpoints
@pytest.mark.parametrize("ep", ["/api/drive/start", "/api/onedrive/start", "/api/wa/start"])
def test_integration_start(ep, h):
    r = requests.get(f"{BASE_URL}{ep}", headers=h, timeout=15, allow_redirects=False)
    # should return JSON with auth_url OR 200/302 redirect
    assert r.status_code in (200, 302), f"{ep} -> {r.status_code} {r.text[:200]}"


# Admin endpoints
ADMIN_ENDPOINTS = [
    "/api/admin/stats",
    "/api/admin/revenue/monthly",
    "/api/admin/logs/recent",
    "/api/admin/services-status",
    "/api/admin/legacy/users",
    "/api/admin/legacy/stats",
    "/api/admin/ai/config",
    "/api/admin/ai/stats",
    "/api/admin/tickets",
    "/api/admin/email-templates",
    "/api/admin/articles",
    "/api/admin/onboarding/results",
    "/api/admin/legacy/newsletters",
    "/api/admin/security/summary",
    "/api/admin/modules",
    "/api/admin/quotes",
    "/api/admin/roles/admins",
    "/api/admin/backups",
]


@pytest.mark.parametrize("ep", ADMIN_ENDPOINTS)
def test_admin_endpoint(ep, h):
    r = requests.get(f"{BASE_URL}{ep}", headers=h, timeout=15)
    assert r.status_code == 200, f"{ep} -> {r.status_code} {r.text[:200]}"
