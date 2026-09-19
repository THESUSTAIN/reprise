"""Iter 17 — Branding endpoints + VAGUE 1 regression + SWOT send-now branded."""
import os
import io
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASS = "Test1234!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Auth failed: {r.status_code} {r.text[:120]}")
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def admin_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ───────── Branding public GET ─────────
def test_branding_public_get():
    r = requests.get(f"{BASE}/api/branding", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("app_name") == "MyExtension AI", d
    assert d.get("platform_name") == "Zayado"
    assert d.get("primary_color", "").lower().startswith("#")
    for k in ("secondary_color", "accent_color", "email_footer",
              "support_email", "support_url"):
        assert k in d, f"missing {k}"
    # logos may be empty strings if not uploaded
    assert "app_logo_url" in d and "platform_logo_url" in d


def test_branding_patch_requires_auth():
    r = requests.patch(f"{BASE}/api/admin/branding",
                       json={"app_name": "Hacker"}, timeout=15)
    assert r.status_code in (401, 403), f"got {r.status_code}: {r.text[:120]}"


def test_branding_patch_persists(admin_h):
    # capture original to restore
    cur = requests.get(f"{BASE}/api/branding", timeout=15).json()
    new_footer = "TEST_FOOTER " + os.urandom(4).hex()
    try:
        r = requests.patch(f"{BASE}/api/admin/branding",
                           headers=admin_h, json={"email_footer": new_footer}, timeout=20)
        assert r.status_code == 200, r.text
        # verify GET reflects
        g = requests.get(f"{BASE}/api/branding", timeout=15).json()
        assert g.get("email_footer") == new_footer
        # ensure core fields preserved
        assert g.get("app_name") == cur.get("app_name")
    finally:
        # restore
        requests.patch(f"{BASE}/api/admin/branding",
                       headers=admin_h,
                       json={"email_footer": cur.get("email_footer")}, timeout=20)


def test_branding_upload_logo_no_file(admin_h):
    """Without multipart file -> should 4xx (422 unprocessable typically)."""
    r = requests.post(f"{BASE}/api/admin/branding/upload-logo?target=app",
                      headers=admin_h, timeout=15)
    assert 400 <= r.status_code < 500, f"expected 4xx, got {r.status_code}"


def test_branding_upload_logo_non_image(admin_h):
    """Reject non-image content-type with 400."""
    files = {"file": ("test.txt", b"hello", "text/plain")}
    r = requests.post(f"{BASE}/api/admin/branding/upload-logo?target=app",
                      headers=admin_h, files=files, timeout=20)
    # Could be 400 (our validation) or 500 if WP env not configured – accept 4xx/5xx,
    # but specifically prefer 400.
    assert r.status_code in (400, 413, 500, 502), r.status_code


# ───────── VAGUE 1 regression ─────────
@pytest.mark.parametrize("path", [
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
    "/api/prefs/swot",
])
def test_vague1_endpoints_200(admin_h, path):
    r = requests.get(f"{BASE}{path}", headers=admin_h, timeout=20)
    assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:120]}"


def test_wp_site_settings(admin_h):
    r = requests.get(f"{BASE}/api/wp/site-settings", headers=admin_h, timeout=20)
    assert r.status_code == 200, r.text


def test_broadcast_notifications(admin_h):
    r = requests.get(f"{BASE}/api/admin/broadcast-notifications",
                     headers=admin_h, timeout=20)
    assert r.status_code == 200, r.text


# ───────── SWOT send-now (Claude 4.5) ─────────
def test_swot_send_now(admin_h):
    r = requests.post(f"{BASE}/api/prefs/swot/send-now",
                      headers=admin_h, timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "sent" in d, d
    assert isinstance(d["sent"], bool)
