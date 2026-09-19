"""Backend tests for Zayado admin panel + auth flows used by WP plugin.
Only the flows listed in the review request are tested.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://smart-board-engine.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "ZayadoAdmin2026!"
DEMO_EMAIL = "thomas@zayado.fr"
DEMO_PASSWORD = "Thomas2026!"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    token = data.get("access_token")
    assert token, f"no access_token: {data}"
    return token


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# --- Health ---
def test_health(session):
    r = session.get(f"{API}/health", timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("db") is True


# --- Auth ---
def test_admin_login_returns_jwt(admin_token):
    assert isinstance(admin_token, str) and len(admin_token) > 20


def test_demo_login(session):
    r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"demo login failed: {r.status_code} {r.text[:400]}"
    assert r.json().get("access_token")


# --- Admin security ---
def test_admin_stats_requires_auth(session):
    r = session.get(f"{API}/admin/stats", timeout=15)
    assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"


# --- Admin stats ---
def test_admin_stats(session, admin_headers):
    r = session.get(f"{API}/admin/stats", headers=admin_headers, timeout=30)
    assert r.status_code == 200, r.text[:400]
    data = r.json()
    assert data.get("total_users", 0) > 0, f"total_users must be >0: {data}"
    assert "plans_distribution" in data
    assert "daily_signups" in data


# --- Admin users listing ---
def test_admin_users_list(session, admin_headers):
    r = session.get(f"{API}/admin/users?skip=0&limit=20", headers=admin_headers, timeout=30)
    assert r.status_code == 200, r.text[:400]
    data = r.json()
    assert "users" in data and isinstance(data["users"], list)
    assert "total" in data and "total_pages" in data
    assert len(data["users"]) > 0, "expected at least 1 user"


def test_admin_users_filter_by_plan_free(session, admin_headers):
    r = session.get(f"{API}/admin/users?skip=0&limit=50&plan=free", headers=admin_headers, timeout=30)
    assert r.status_code == 200, r.text[:400]
    data = r.json()
    for u in data.get("users", []):
        assert u.get("plan") == "free", f"user with non-free plan returned: {u.get('plan')}"


# --- Admin config (plugin connection test) ---
def test_admin_config(session, admin_headers):
    r = session.get(f"{API}/admin/config", headers=admin_headers, timeout=30)
    assert r.status_code == 200, r.text[:400]


# --- Gift credits (the fix) ---
@pytest.fixture(scope="session")
def target_user_id(session, admin_headers):
    r = session.get(f"{API}/admin/users?skip=0&limit=50", headers=admin_headers, timeout=30)
    assert r.status_code == 200
    users = r.json().get("users", [])
    # Pick a non-admin user if possible
    for u in users:
        if u.get("email") not in (ADMIN_EMAIL, DEMO_EMAIL):
            return u.get("id")
    return users[0].get("id") if users else pytest.skip("no users")


def test_gift_credits_amount_field(session, admin_headers, target_user_id):
    """Main fix: plugin sends {'amount': n}"""
    r = session.post(
        f"{API}/admin/users/{target_user_id}/credits",
        headers=admin_headers,
        json={"amount": 100, "reason": "WP gift"},
        timeout=30,
    )
    assert r.status_code == 200, f"amount payload failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    assert data.get("status") == "credits_added", f"unexpected status: {data}"
    assert data.get("credits") == 100, f"expected credits=100, got {data.get('credits')}"


def test_gift_credits_credits_field_backcompat(session, admin_headers, target_user_id):
    """Retrocompat: {'credits': n}"""
    r = session.post(
        f"{API}/admin/users/{target_user_id}/credits",
        headers=admin_headers,
        json={"credits": 50},
        timeout=30,
    )
    assert r.status_code == 200, f"credits payload failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    assert data.get("status") == "credits_added"


# --- Change plan ---
def test_change_plan(session, admin_headers, target_user_id):
    r = session.put(
        f"{API}/admin/users/{target_user_id}/plan",
        headers=admin_headers,
        json={"plan": "start"},
        timeout=30,
    )
    assert r.status_code == 200, f"change plan failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    assert data.get("status") == "success", f"unexpected: {data}"
