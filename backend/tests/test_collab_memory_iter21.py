"""
Iter21 — Backend tests for collab_memory persistent conversation memory
Endpoints: /api/collaborateur/history GET/POST/DELETE
+ regression: chat, branding, vision, tasks, energy, revenue, swot, churn, users, wp_sync
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text}")
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── /api/collaborateur/history endpoints ───────────────────────────────────
class TestCollabMemory:
    def test_post_history_saves_messages(self, auth_headers):
        payload = {
            "messages": [
                {"role": "user", "content": "TEST_MSG_USER_1"},
                {"role": "assistant", "content": "TEST_MSG_ASSIST_1"},
                {"role": "user", "content": "TEST_MSG_USER_2"},
                {"role": "assistant", "content": "TEST_MSG_ASSIST_2"},
            ]
        }
        r = requests.post(
            f"{BASE_URL}/api/collaborateur/history",
            json=payload,
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, f"POST failed: {r.status_code} {r.text}"
        data = r.json()
        assert data.get("ok") is True
        assert data.get("saved") == 4, f"Expected saved=4, got {data}"

    def test_get_history_returns_saved(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/collaborateur/history",
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, f"GET failed: {r.status_code} {r.text}"
        data = r.json()
        assert "messages" in data
        msgs = data["messages"]
        assert isinstance(msgs, list)
        assert len(msgs) >= 4, f"Expected at least 4 saved msgs, got {len(msgs)}: {msgs}"
        # validate structure
        last = msgs[-1]
        assert last.get("role") == "assistant"
        assert last.get("content") == "TEST_MSG_ASSIST_2"

    def test_delete_history_clears(self, auth_headers):
        r = requests.delete(
            f"{BASE_URL}/api/collaborateur/history",
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, f"DELETE failed: {r.status_code} {r.text}"
        assert r.json().get("ok") is True

        # GET after DELETE should return empty
        r2 = requests.get(
            f"{BASE_URL}/api/collaborateur/history",
            headers=auth_headers,
            timeout=30,
        )
        assert r2.status_code == 200
        assert r2.json().get("messages") == []

    def test_post_history_no_auth_rejected(self):
        r = requests.post(
            f"{BASE_URL}/api/collaborateur/history",
            json={"messages": [{"role": "user", "content": "x"}]},
            timeout=15,
        )
        assert r.status_code in (401, 403), f"Expected 401/403 got {r.status_code}"

    def test_get_history_no_auth_rejected(self):
        r = requests.get(f"{BASE_URL}/api/collaborateur/history", timeout=15)
        assert r.status_code in (401, 403), f"Expected 401/403 got {r.status_code}"

    def test_delete_history_no_auth_rejected(self):
        r = requests.delete(f"{BASE_URL}/api/collaborateur/history", timeout=15)
        assert r.status_code in (401, 403), f"Expected 401/403 got {r.status_code}"

    def test_post_history_max_turns_truncation(self, auth_headers):
        # 25 messages → should keep last MAX_TURNS*2 = 20
        big = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"M{i}"}
            for i in range(25)
        ]
        r = requests.post(
            f"{BASE_URL}/api/collaborateur/history",
            json={"messages": big},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200
        assert r.json().get("saved") == 20

        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/collaborateur/history",
            headers=auth_headers,
            timeout=15,
        )


# ── Regression: chat collaborateur ─────────────────────────────────────────
class TestChatRegression:
    def test_chat_basic_smoke(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/collaborateur/chat",
            json={"messages": [], "ui_language": "fr"},
            headers=auth_headers,
            timeout=90,
        )
        assert r.status_code == 200, f"Chat failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        assert "reply" in data
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 0


# ── Regression VAGUE 1: tasks, vision, documents, leads, streak, revenue,
#    energy, processes, analyse, branding, swot, churn, users, wp_sync ─────
class TestRegressionVague1:
    @pytest.mark.parametrize("endpoint", [
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
        "/api/admin/inactivity/preview",
        "/api/admin/legacy/users",
        "/api/admin/legacy/stats",
        "/api/wp/site-settings",
    ])
    def test_endpoint_returns_200(self, auth_headers, endpoint):
        r = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"{endpoint} returned {r.status_code}: {r.text[:200]}"
