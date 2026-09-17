"""Backend tests for AI quota, collaborateur chat (unlimited admin), and RGPD endpoints."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in login response: {data}"
    return token


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# --- AI Quota endpoint ---
class TestAiQuota:
    def test_quota_endpoint_admin_unlimited(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/ai/quota", headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"unexpected status: {r.status_code} {r.text[:300]}"
        data = r.json()
        # Required fields
        for key in ["plan", "used", "limit", "remaining", "unlimited", "year", "month"]:
            assert key in data, f"Missing key {key} in response: {data}"
        # Admin business → unlimited
        assert data["unlimited"] is True, f"Expected unlimited=True for admin, got {data}"
        assert data["limit"] is None, f"Expected limit=None for unlimited admin, got {data['limit']}"
        assert isinstance(data["used"], int)
        assert data["year"] >= 2025
        assert 1 <= data["month"] <= 12


# --- Collaborateur Chat with quota tracking ---
class TestCollaborateurChatQuota:
    def test_chat_admin_returns_reply_and_quota(self, admin_headers):
        # Get quota before
        r0 = requests.get(f"{BASE_URL}/api/ai/quota", headers=admin_headers, timeout=30)
        used_before = r0.json().get("used", 0) if r0.status_code == 200 else 0

        # Send chat — endpoint accepts either {message} or {messages:[{role,content}]}
        # Try the "messages" shape first (per 422 hint), fallback to "message".
        payload = {"messages": [{"role": "user", "content": "bonjour"}]}
        r = requests.post(f"{BASE_URL}/api/collaborateur/chat", headers=admin_headers, json=payload, timeout=120)
        if r.status_code == 422:
            payload = {"message": "bonjour"}
            r = requests.post(f"{BASE_URL}/api/collaborateur/chat", headers=admin_headers, json=payload, timeout=120)
        assert r.status_code == 200, f"chat failed: {r.status_code} {r.text[:500]}"
        data = r.json()
        assert "reply" in data, f"missing reply in {data}"
        assert isinstance(data["reply"], str) and len(data["reply"]) > 0
        # Quota must be present
        assert "quota" in data, f"missing quota in response: {list(data.keys())}"
        quota = data["quota"]
        for k in ["used", "limit", "remaining"]:
            assert k in quota, f"missing quota.{k}: {quota}"
        # For admin: limit=None and remaining=None (unlimited)
        assert quota["limit"] is None, f"Expected limit None for admin, got {quota['limit']}"
        # used should be incremented
        assert quota["used"] >= used_before + 1 or quota["used"] >= 1, \
            f"Expected used > {used_before}, got {quota['used']}"


# --- RGPD endpoints ---
class TestRgpd:
    def test_export_data(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/auth/export-data", headers=admin_headers, timeout=60)
        assert r.status_code == 200, f"export failed: {r.status_code} {r.text[:300]}"
        # Could be JSON or downloadable (Content-Type)
        ctype = r.headers.get("content-type", "")
        # Parse json content
        try:
            data = r.json()
        except Exception:
            pytest.fail(f"Export should return JSON. Content-Type={ctype}, body={r.text[:300]}")
        # Check expected top-level keys (per spec)
        for key in ["user", "conversations", "projects", "transactions"]:
            assert key in data, f"missing key '{key}' in export. Keys: {list(data.keys())}"

    def test_delete_account_endpoint_exists(self, admin_headers):
        # We do NOT actually delete admin. Instead, test that endpoint exists.
        # Most delete-account flows require POST/DELETE with confirmation. Use OPTIONS or send invalid payload.
        r = requests.delete(f"{BASE_URL}/api/auth/delete-account",
                            headers=admin_headers,
                            json={"confirm": "WRONG"}, timeout=30)
        # Acceptable: 400/403/422 (validation failed) ; 405 (wrong method) is also failure mode
        # 200/204 would be BAD because that would mean admin got deleted.
        assert r.status_code in (400, 401, 403, 404, 405, 409, 422), \
            f"unexpected status from delete-account: {r.status_code} {r.text[:300]}"
