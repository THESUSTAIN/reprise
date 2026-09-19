"""Iteration 15 — VAGUE 2/3/SWOT cron tests."""
import os
import time
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0]).rstrip("/")
EMAIL = "admin@zayado.net"
PASSWORD = "Test1234!"


@pytest.fixture(scope="module")
def auth_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token in {r.json()}"
    s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


# --- SWOT prefs ---
class TestSwotPrefs:
    def test_get_prefs_shape(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/prefs/swot", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "swot_monthly" in d
        assert isinstance(d["swot_monthly"], bool)
        assert "swot_last_sent_at" in d  # nullable

    def test_patch_toggle_off_then_on(self, auth_client):
        r = auth_client.patch(f"{BASE_URL}/api/prefs/swot", json={"swot_monthly": False}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["updated"] is True
        assert d["swot_monthly"] is False
        # Verify persisted via GET
        r2 = auth_client.get(f"{BASE_URL}/api/prefs/swot", timeout=15)
        assert r2.json()["swot_monthly"] is False
        # Restore
        r3 = auth_client.patch(f"{BASE_URL}/api/prefs/swot", json={"swot_monthly": True}, timeout=15)
        assert r3.status_code == 200
        assert r3.json()["swot_monthly"] is True

    def test_unauthorized_no_token(self):
        r = requests.get(f"{BASE_URL}/api/prefs/swot", timeout=10)
        assert r.status_code in (401, 403)


# --- SWOT send-now (Claude Sonnet 4.5) ---
class TestSwotSendNow:
    def test_send_now_returns_sent_flag(self, auth_client):
        before = auth_client.get(f"{BASE_URL}/api/prefs/swot", timeout=15).json()
        last_before = before.get("swot_last_sent_at")
        r = auth_client.post(f"{BASE_URL}/api/prefs/swot/send-now", json={}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "sent" in d
        assert isinstance(d["sent"], bool)
        if d["sent"]:
            after = auth_client.get(f"{BASE_URL}/api/prefs/swot", timeout=15).json()
            assert after.get("swot_last_sent_at"), "swot_last_sent_at should be set after sent=True"
            assert after["swot_last_sent_at"] != last_before


# --- VAGUE 1 regression smoke (200 only) ---
class TestVague1Regression:
    @pytest.mark.parametrize("endpoint", [
        "/api/tasks",
        "/api/vision",
        "/api/documents",
        "/api/leads",
        "/api/streak",
        "/api/revenue/monthly",
        "/api/energy/today",
        "/api/energy/latest",
        "/api/processes/templates",
        "/api/analyse",
        "/api/quote/today",
    ])
    def test_smoke_endpoint_200(self, auth_client, endpoint):
        r = auth_client.get(f"{BASE_URL}{endpoint}", timeout=20)
        assert r.status_code == 200, f"{endpoint} -> {r.status_code} {r.text[:200]}"
