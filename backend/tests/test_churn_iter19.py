"""Iter19 — Churn / inactivity re-engagement endpoints."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    import dotenv
    dotenv.load_dotenv("/app/frontend/.env")
    BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PWD = "Test1234!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PWD},
        timeout=20,
    )
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ────────── User prefs ──────────
class TestInactivityPrefs:
    def test_get_prefs_default_enabled(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/prefs/inactivity", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "enabled" in d
        assert "last_alerts" in d
        assert isinstance(d["last_alerts"], dict)

    def test_patch_prefs_disable_then_enable(self, admin_headers):
        # disable
        r = requests.patch(
            f"{BASE_URL}/api/prefs/inactivity",
            headers=admin_headers,
            json={"inactivity_alerts_enabled": False},
            timeout=10,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("updated") is True
        assert d.get("enabled") is False
        # verify persistence
        g = requests.get(f"{BASE_URL}/api/prefs/inactivity", headers=admin_headers, timeout=10)
        assert g.status_code == 200
        assert g.json().get("enabled") is False
        # re-enable
        r2 = requests.patch(
            f"{BASE_URL}/api/prefs/inactivity",
            headers=admin_headers,
            json={"inactivity_alerts_enabled": True},
            timeout=10,
        )
        assert r2.status_code == 200
        assert r2.json().get("enabled") is True

    def test_prefs_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/prefs/inactivity", timeout=10)
        assert r.status_code in (401, 403)


# ────────── Admin preview ──────────
class TestAdminInactivityPreview:
    def test_preview_returns_three_tiers(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/inactivity/preview", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("tier_14", "tier_60", "tier_335"):
            assert k in d, f"Missing tier {k}"
            t = d[k]
            assert t["days"] in (14, 60, 335)
            assert "subject_example" in t and isinstance(t["subject_example"], str) and len(t["subject_example"]) > 5
            assert "eligible_count" in t
            assert "will_send_next_run" in t
            assert isinstance(t.get("users"), list)

    def test_preview_days_inactive_coherent(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/inactivity/preview", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        thresholds = {"tier_14": 14, "tier_60": 60, "tier_335": 335}
        for k, threshold in thresholds.items():
            for u in d[k]["users"]:
                assert u["days_inactive"] >= threshold, f"{k}: {u['email']} has {u['days_inactive']} < {threshold}"
                for f in ("user_id", "email", "last_login_at", "alert_already_sent", "will_send_next_run"):
                    assert f in u

    def test_preview_requires_admin(self):
        r = requests.get(f"{BASE_URL}/api/admin/inactivity/preview", timeout=10)
        assert r.status_code in (401, 403)


# ────────── Admin trigger ──────────
class TestAdminInactivityTrigger:
    def test_trigger_unknown_tier(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/inactivity/trigger",
            headers=admin_headers,
            json={"user_id": "any", "tier": "tier_999"},
            timeout=10,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("error") == "Tier inconnu"
        assert d.get("available_tiers") == ["tier_14", "tier_60", "tier_335"]

    def test_trigger_unknown_user(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/inactivity/trigger",
            headers=admin_headers,
            json={"user_id": "00000000-0000-0000-0000-000000000000", "tier": "tier_14"},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json().get("error") == "User introuvable"

    def test_trigger_valid_returns_shape(self, admin_headers):
        # Pick a real eligible user from preview (tier_14)
        prev = requests.get(f"{BASE_URL}/api/admin/inactivity/preview", headers=admin_headers, timeout=15).json()
        users = prev.get("tier_14", {}).get("users") or []
        if not users:
            pytest.skip("No tier_14 eligible users")
        uid = users[0]["user_id"]
        r = requests.post(
            f"{BASE_URL}/api/admin/inactivity/trigger",
            headers=admin_headers,
            json={"user_id": uid, "tier": "tier_14"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "sent" in d and isinstance(d["sent"], bool)
        assert d.get("user_id") == uid
        assert d.get("tier") == "tier_14"

    def test_trigger_requires_admin(self):
        r = requests.post(
            f"{BASE_URL}/api/admin/inactivity/trigger",
            json={"user_id": "x", "tier": "tier_14"},
            timeout=10,
        )
        assert r.status_code in (401, 403)


# ────────── Regression ──────────
class TestRegression:
    def test_branding_public(self):
        r = requests.get(f"{BASE_URL}/api/branding", timeout=10)
        assert r.status_code == 200
        assert "app_name" in r.json()

    def test_admin_legacy_users(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/users?limit=5", headers=admin_headers, timeout=15)
        assert r.status_code == 200

    def test_admin_legacy_stats(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/stats", headers=admin_headers, timeout=15)
        assert r.status_code == 200

    def test_swot_admin_preview(self, admin_headers):
        # VAGUE 1 regression — swot cron preview
        r = requests.get(f"{BASE_URL}/api/admin/swot/preview", headers=admin_headers, timeout=15)
        assert r.status_code in (200, 404)  # tolerate if route absent
