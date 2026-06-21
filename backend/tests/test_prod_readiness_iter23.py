"""
Iter23 PRODUCTION-READINESS RETEST
Validates iter22 fixes:
  1) memory_router collision fix (alias collab_memory_router)
  2) NEW hot-opportunities + automations endpoints
  3) Core page-supporting backend endpoints (regression).
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://myextension-ai.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASS = "Test1234!"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------------- ITER22 BUG FIX (a): memory_router collision ----------------
class TestIter22Fix_MemoryRouter:
    def test_memory_list_200(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/memory/list", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}"
        body = r.json()
        # collab_memory router may return list or dict
        assert isinstance(body, (list, dict))

    def test_memory_stats_200(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/memory/stats", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}"

    def test_collaborateur_history_200(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/collaborateur/history", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}"


# ---------------- NEW: hot-opportunities ----------------
class TestHotOpportunities:
    def test_list_root(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/hot-opportunities", headers=auth_headers, timeout=15)
        assert r.status_code in (200, 204), f"got {r.status_code}: {r.text[:200]}"

    def test_latest(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/hot-opportunities/latest", headers=auth_headers, timeout=15)
        assert r.status_code in (200, 204), f"got {r.status_code}: {r.text[:200]}"


# ---------------- NEW: automations ----------------
class TestAutomations:
    def test_list_root(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/automations", headers=auth_headers, timeout=15)
        assert r.status_code in (200, 204), f"got {r.status_code}: {r.text[:200]}"
        # data shape check
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (list, dict))


# ---------------- Core endpoints (regression) ----------------
CORE_GET = [
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
    "/api/wellness/today",
]

@pytest.mark.parametrize("path", CORE_GET)
def test_core_endpoints_alive(auth_headers, path):
    r = requests.get(f"{BASE_URL}{path}", headers=auth_headers, timeout=15)
    assert r.status_code in (200, 204), f"{path} -> {r.status_code}: {r.text[:200]}"


# ---------------- Collaborateur chat (real LLM) ----------------
def test_collaborateur_chat(auth_headers):
    # try with multiple possible payload shapes
    payloads = [
        {"messages": [{"role": "user", "content": "Dis 'OK' uniquement."}], "context": {"page": "/"}},
        {"messages": [{"role": "user", "content": "Dis 'OK' uniquement."}]},
    ]
    last = None
    for p in payloads:
        r = requests.post(f"{BASE_URL}/api/collaborateur/chat",
                          headers=auth_headers, json=p, timeout=60)
        last = r
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)
            # response should contain some text body
            assert any(k in data for k in ("response", "message", "content", "reply", "text", "answer")), \
                f"unexpected schema: {list(data.keys())}"
            return
    pytest.fail(f"chat all payloads failed; last={last.status_code} {last.text[:200]}")
