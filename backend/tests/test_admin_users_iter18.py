"""Iteration 18 — Admin user tracking enhancement.

Tests:
- GET /api/admin/legacy/users : ARRAY with required fields (user_id, email, name, plan, role, provider, is_admin, credits, created_at, last_login_at)
- GET /api/admin/legacy/users?search=admin : filters by email/name (ilike)
- GET /api/admin/legacy/users/stats : {total, active_30d, new_30d, paying, by_plan, users:{...}}
- GET /api/admin/legacy/stats : enriched with users.new_30d
Regression :
- /api/admin/legacy/transactions (must still 200)
- /api/branding (public 200)
- /api/quote/today (public 200)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://myextension-ai.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed status={r.status_code} body={r.text[:200]}")
    data = r.json()
    token = data.get("token") or data.get("access_token") or (data.get("user") or {}).get("token")
    if not token:
        # Inspect common shapes
        token = data.get("data", {}).get("token") if isinstance(data.get("data"), dict) else None
    if not token:
        pytest.skip(f"Could not extract token from login response: {list(data.keys())}")
    return token


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ─────────────────────────────────────────────────────────────────────
# Admin legacy users
# ─────────────────────────────────────────────────────────────────────
class TestAdminLegacyUsers:
    def test_users_list_is_array_with_required_fields(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/users", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list), f"Expected list got {type(data)}"
        assert len(data) > 0, "Expected at least 1 user"
        required = {"user_id", "id", "email", "name", "plan", "role", "provider", "is_admin", "credits", "created_at", "last_login_at"}
        u0 = data[0]
        missing = required - set(u0.keys())
        assert not missing, f"Missing fields: {missing}. Got keys={list(u0.keys())}"
        # Validate types
        assert isinstance(u0["is_admin"], bool)
        assert isinstance(u0["credits"], int)

    def test_users_list_contains_admin(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/users", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        emails = [u["email"] for u in data]
        assert ADMIN_EMAIL in emails, f"admin@zayado.net not found in users list (n={len(emails)})"
        admin = next(u for u in data if u["email"] == ADMIN_EMAIL)
        assert admin["is_admin"] is True
        assert admin["last_login_at"] is not None, "admin should have last_login_at (just logged in)"
        assert admin["created_at"] is not None

    def test_users_search_filter(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/users?search=admin", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        # All results must include 'admin' in email or name (case-insensitive)
        for u in data:
            blob = f"{(u.get('email') or '').lower()} {(u.get('name') or '').lower()}"
            assert "admin" in blob, f"Result {u['email']} doesn't match 'admin' filter"

    def test_users_requires_admin(self):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/users", timeout=15)
        assert r.status_code in (401, 403), f"Unauthed should be 401/403 got {r.status_code}"


# ─────────────────────────────────────────────────────────────────────
# Admin legacy users stats
# ─────────────────────────────────────────────────────────────────────
class TestAdminLegacyUsersStats:
    def test_users_stats_shape(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/users/stats", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        required = {"total", "active_30d", "new_30d", "paying", "by_plan", "users"}
        missing = required - set(data.keys())
        assert not missing, f"Missing fields {missing}, got {list(data.keys())}"
        assert isinstance(data["by_plan"], dict)
        assert isinstance(data["users"], dict)
        for k in ("total", "active_30d", "new_30d", "paying", "by_plan"):
            assert k in data["users"], f"users.{k} missing"
        assert data["total"] == data["users"]["total"]
        assert data["new_30d"] == data["users"]["new_30d"]

    def test_users_stats_values_make_sense(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/users/stats", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= data["active_30d"]
        assert data["total"] >= data["new_30d"]
        assert data["total"] >= data["paying"]


# ─────────────────────────────────────────────────────────────────────
# Admin legacy stats (dashboard)
# ─────────────────────────────────────────────────────────────────────
class TestAdminLegacyStats:
    def test_legacy_stats_enriched_with_users_new30d(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/stats", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "users" in data
        users = data["users"]
        for k in ("total", "active_30d", "new_30d", "paying", "by_plan"):
            assert k in users, f"users.{k} missing in legacy/stats"
        assert "revenue" in data
        assert "newsletters" in data
        # users_total (legacy flat) and signups_30d (legacy flat) should also exist
        assert "users_total" in data
        assert "signups_30d" in data
        assert data["signups_30d"] == users["new_30d"]


# ─────────────────────────────────────────────────────────────────────
# Regression iteration_17
# ─────────────────────────────────────────────────────────────────────
class TestRegressionIter17:
    def test_branding_public(self):
        r = requests.get(f"{BASE_URL}/api/branding", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("app_name") and d.get("platform_name")

    def test_quote_today(self):
        r = requests.get(f"{BASE_URL}/api/quote/today", timeout=15)
        assert r.status_code == 200
        assert "text" in r.json()

    def test_legacy_transactions(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/transactions", headers=auth_headers, timeout=15)
        assert r.status_code == 200
