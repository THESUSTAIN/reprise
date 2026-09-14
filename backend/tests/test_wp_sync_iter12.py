"""WP Sync + Broadcast Notifications regression — iter 12.

Tests the /api/wp/site-settings endpoints (GET public, PUT admin-only),
and regression-checks /api/admin/broadcast-notifications.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://app.zayado.net").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"No token in login response: {data}"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ── WP Sync: public GET ────────────────────────────────────────────────
class TestWPSiteSettingsGet:
    def test_get_public_no_auth(self):
        r = requests.get(f"{BASE_URL}/api/wp/site-settings", timeout=20)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Verify required keys present
        for k in ("title", "description", "language", "site_icon", "site_icon_url", "url"):
            assert k in data, f"Missing key '{k}' in response: {data}"
        # title + url should be strings if present
        assert isinstance(data.get("title"), (str, type(None)))
        assert isinstance(data.get("url"), (str, type(None)))


# ── WP Sync: PUT admin-only ────────────────────────────────────────────
class TestWPSiteSettingsPut:
    def test_put_without_token_unauthorized(self):
        r = requests.put(
            f"{BASE_URL}/api/wp/site-settings",
            json={"description": "hack-attempt"},
            timeout=20,
        )
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}: {r.text[:200]}"

    def test_put_empty_body_returns_400(self, admin_headers):
        r = requests.put(
            f"{BASE_URL}/api/wp/site-settings",
            headers=admin_headers,
            json={},
            timeout=20,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text[:200]}"

    def test_put_description_persists(self, admin_headers):
        # Save original description first
        original = requests.get(f"{BASE_URL}/api/wp/site-settings", timeout=20).json()
        orig_desc = original.get("description") or ""

        new_desc = f"TEST_iter12_zayado_sync_{int(time.time())}"
        try:
            r = requests.put(
                f"{BASE_URL}/api/wp/site-settings",
                headers=admin_headers,
                json={"description": new_desc},
                timeout=30,
            )
            assert r.status_code == 200, f"PUT failed: {r.status_code} {r.text[:400]}"
            body = r.json()
            assert body.get("status") == "ok", f"Expected status=ok: {body}"
            assert "wp" in body, f"Missing 'wp' key in response: {body}"

            # Verify GET returns new description
            time.sleep(1)
            r2 = requests.get(f"{BASE_URL}/api/wp/site-settings", timeout=20)
            assert r2.status_code == 200
            assert r2.json().get("description") == new_desc, (
                f"Description not persisted. Got: {r2.json().get('description')!r}, expected: {new_desc!r}"
            )
        finally:
            # Restore original description
            requests.put(
                f"{BASE_URL}/api/wp/site-settings",
                headers=admin_headers,
                json={"description": orig_desc},
                timeout=30,
            )


# ── Regression: broadcast notifications still work ─────────────────────
class TestBroadcastNotificationsRegression:
    def test_admin_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/broadcast-notifications", headers=admin_headers, timeout=20)
        assert r.status_code == 200, f"List failed: {r.status_code} {r.text[:200]}"
        data = r.json()
        assert "notifications" in data, f"Expected 'notifications' key: {data}"
        assert isinstance(data["notifications"], list)

    def test_admin_list_no_auth_forbidden(self):
        r = requests.get(f"{BASE_URL}/api/admin/broadcast-notifications", timeout=20)
        assert r.status_code in (401, 403)

    def test_admin_crud_cycle(self, admin_headers):
        # CREATE
        payload = {
            "title": "TEST_iter12_regression",
            "body": "regression body",
            "surface": "app_modal",
            "audience": "all",
            "active": False,
        }
        r = requests.post(
            f"{BASE_URL}/api/admin/broadcast-notifications",
            headers=admin_headers,
            json=payload,
            timeout=20,
        )
        assert r.status_code in (200, 201), f"Create failed: {r.status_code} {r.text[:300]}"
        created = r.json()
        notif_id = created.get("id")
        assert notif_id, f"No id in created: {created}"
        assert created.get("title") == "TEST_iter12_regression"

        try:
            # PATCH
            r2 = requests.patch(
                f"{BASE_URL}/api/admin/broadcast-notifications/{notif_id}",
                headers=admin_headers,
                json={**payload, "title": "TEST_iter12_updated"},
                timeout=20,
            )
            assert r2.status_code == 200, f"Patch failed: {r2.status_code} {r2.text[:300]}"
            assert r2.json().get("title") == "TEST_iter12_updated"
        finally:
            # DELETE
            r3 = requests.delete(
                f"{BASE_URL}/api/admin/broadcast-notifications/{notif_id}",
                headers=admin_headers,
                timeout=20,
            )
            assert r3.status_code in (200, 204), f"Delete failed: {r3.status_code}"
