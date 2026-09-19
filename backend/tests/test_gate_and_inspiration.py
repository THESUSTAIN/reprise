"""Tests for iteration 3:
- Notifications gate (hold/resume) endpoints
- Inspiration quotes (current/overview/schedule/CRUD)
"""
import os
from datetime import datetime, timezone, timedelta

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "ZayadoAdmin2026!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ─────────── Notifications gate ───────────
class TestNotifGate:
    def test_gate_requires_auth(self):
        r = requests.get(f"{API}/admin/notifications/gate", timeout=10)
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_gate_post_requires_auth(self):
        r = requests.post(f"{API}/admin/notifications/gate", json={"hold": True}, timeout=10)
        assert r.status_code in (401, 403)

    def test_gate_get_shape(self, admin_headers):
        r = requests.get(f"{API}/admin/notifications/gate", headers=admin_headers, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("hold", "since", "held_last", "blocked_count"):
            assert k in d, f"missing key {k}"
        assert isinstance(d["hold"], bool)
        assert isinstance(d["blocked_count"], int)

    def test_gate_hold_true_blocks_active(self, admin_headers):
        r = requests.post(f"{API}/admin/notifications/gate",
                          headers=admin_headers, json={"hold": True}, timeout=10)
        assert r.status_code == 200, r.text
        assert r.json().get("hold") is True

        # Now /broadcast-notifications/active should return null
        r2 = requests.get(f"{API}/broadcast-notifications/active",
                          params={"surface": "app_modal"}, timeout=10)
        assert r2.status_code == 200
        assert r2.json() is None, f"expected null, got {r2.json()}"

    def test_gate_hold_false_returns_resent_field(self, admin_headers):
        r = requests.post(f"{API}/admin/notifications/gate",
                          headers=admin_headers, json={"hold": False}, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("hold") is False
        assert "resent" in d, f"missing 'resent' field: {d}"

    def test_gate_final_state_is_false(self, admin_headers):
        # Ensure we don't leave the system with notifications blocked
        requests.post(f"{API}/admin/notifications/gate",
                      headers=admin_headers, json={"hold": False}, timeout=10)
        r = requests.get(f"{API}/admin/notifications/gate", headers=admin_headers, timeout=10)
        assert r.json()["hold"] is False


# ─────────── Inspiration ───────────
class TestInspiration:
    def test_current_secular(self):
        r = requests.get(f"{API}/inspiration/current",
                         params={"set_type": "secular"}, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("set_type") == "secular"
        assert d.get("date")
        assert d.get("quote"), "expected non empty quote"
        assert d["quote"].get("text")

    def test_current_christian(self):
        r = requests.get(f"{API}/inspiration/current",
                         params={"set_type": "christian"}, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d.get("set_type") == "christian"
        assert d["quote"] and d["quote"].get("text")
        # Should be from christian seed pool
        assert d["quote"].get("set_type") == "christian"

    def test_admin_overview(self, admin_headers):
        r = requests.get(f"{API}/admin/inspiration/overview",
                         headers=admin_headers, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        for st in ("christian", "secular"):
            assert st in d
            assert "current" in d[st]
            assert "upcoming" in d[st]
            assert "all" in d[st]

    def test_create_scheduled_quote_and_verify(self, admin_headers):
        starts_at = (datetime.now(timezone.utc).date() + timedelta(days=10)).isoformat()
        payload = {
            "text": "TEST_ Quote scheduled",
            "author": "Tester",
            "set_type": "secular",
            "starts_at": starts_at,
        }
        r = requests.post(f"{API}/admin/inspiration/quotes",
                          headers=admin_headers, json=payload, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True
        qid = d.get("id")
        assert qid

        # GET schedule
        r2 = requests.get(f"{API}/admin/inspiration/schedule",
                          headers=admin_headers,
                          params={"set_type": "secular", "days": 30}, timeout=10)
        assert r2.status_code == 200
        sched = r2.json()
        assert sched.get("current") is not None, "current should not be empty"
        upcoming_ids = [u["id"] for u in sched.get("upcoming", [])]
        assert qid in upcoming_ids, f"quote {qid} not in upcoming: {upcoming_ids}"
        # verify starts_in_days == 10
        item = next(u for u in sched["upcoming"] if u["id"] == qid)
        assert item.get("starts_in_days") == 10, item

        # Cleanup: delete
        r3 = requests.delete(f"{API}/admin/inspiration/quotes/{qid}",
                             headers=admin_headers, timeout=10)
        assert r3.status_code == 200
        assert r3.json().get("ok") is True

        # Verify deletion
        r4 = requests.get(f"{API}/admin/inspiration/schedule",
                          headers=admin_headers,
                          params={"set_type": "secular", "days": 30}, timeout=10)
        upcoming_ids2 = [u["id"] for u in r4.json().get("upcoming", [])]
        assert qid not in upcoming_ids2

    def test_create_quote_invalid_set_type(self, admin_headers):
        r = requests.post(f"{API}/admin/inspiration/quotes",
                          headers=admin_headers,
                          json={"text": "hello", "set_type": "invalid_type"}, timeout=10)
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text}"

    def test_admin_endpoints_require_auth(self):
        r = requests.get(f"{API}/admin/inspiration/overview", timeout=10)
        assert r.status_code in (401, 403)
        r = requests.get(f"{API}/admin/inspiration/schedule",
                         params={"set_type": "secular"}, timeout=10)
        assert r.status_code in (401, 403)


# Final teardown-like — always ensure gate is off
def test_zzz_final_cleanup_gate(admin_headers):
    requests.post(f"{API}/admin/notifications/gate",
                  headers=admin_headers, json={"hold": False}, timeout=10)
    r = requests.get(f"{API}/admin/notifications/gate", headers=admin_headers, timeout=10)
    assert r.json()["hold"] is False
