"""Iteration 13 retest: WP sync regression + preview-site MIME + broadcast notifications regression."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"

ORIGINAL_DESCRIPTION = "Zayado — Le cockpit IA des solo founders. Vision, pilotage, croissance."
ORIGINAL_TITLE = "Cms Zayado.net"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"Admin login failed ({r.status_code}): {r.text[:200]}")
    return r.json().get("access_token")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- preview-site MIME / asset serving ----------
class TestPreviewSite:
    def test_preview_site_index_html_served(self):
        r = requests.get(f"{BASE_URL}/api/preview-site/", timeout=20)
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert "text/html" in ct, f"Expected text/html got {ct}"
        assert "/api/preview-site/assets/index-" in r.text, "Bundle path not properly rewritten"

    def test_preview_site_js_bundle_mime(self):
        r = requests.get(f"{BASE_URL}/api/preview-site/", timeout=20)
        # Extract bundle path
        import re
        m = re.search(r'src="(/api/preview-site/assets/index-[^"]+\.js)"', r.text)
        assert m, "Could not find JS bundle in index.html"
        bundle_path = m.group(1)
        rj = requests.get(f"{BASE_URL}{bundle_path}", timeout=20)
        assert rj.status_code == 200
        ct = rj.headers.get("content-type", "")
        assert ("javascript" in ct or "text/javascript" in ct), f"JS bundle returned wrong MIME: {ct}"

    def test_preview_site_css_bundle(self):
        r = requests.get(f"{BASE_URL}/api/preview-site/", timeout=20)
        import re
        m = re.search(r'href="(/api/preview-site/assets/index-[^"]+\.css)"', r.text)
        assert m, "Could not find CSS bundle"
        rc = requests.get(f"{BASE_URL}{m.group(1)}", timeout=20)
        assert rc.status_code == 200
        assert "css" in rc.headers.get("content-type", "")


# ---------- WP Sync ----------
class TestWPSync:
    def test_get_site_settings_public(self):
        r = requests.get(f"{BASE_URL}/api/wp/site-settings", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "title" in d
        assert "description" in d
        assert "url" in d

    def test_put_site_settings_no_auth_forbidden(self):
        r = requests.put(f"{BASE_URL}/api/wp/site-settings", json={"description": "x"})
        assert r.status_code in (401, 403)

    def test_put_site_settings_and_restore(self, admin_headers):
        new_desc = "TEST_iter13_retest_safe_to_revert"
        try:
            r = requests.put(f"{BASE_URL}/api/wp/site-settings",
                             json={"description": new_desc}, headers=admin_headers, timeout=30)
            assert r.status_code == 200, r.text
            g = requests.get(f"{BASE_URL}/api/wp/site-settings", timeout=15)
            assert g.json().get("description") == new_desc
        finally:
            requests.put(f"{BASE_URL}/api/wp/site-settings",
                         json={"description": ORIGINAL_DESCRIPTION},
                         headers=admin_headers, timeout=30)


# ---------- Admin legacy stats (DashboardSection robustness) ----------
class TestAdminLegacyStats:
    def test_legacy_stats_endpoint(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/stats", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        # Payload may or may not contain users/revenue/newsletters fields — DashboardSection must handle both.
        assert isinstance(r.json(), dict)


# ---------- Broadcast notifications regression ----------
class TestBroadcastNotifications:
    def test_list_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/admin/broadcast-notifications")
        assert r.status_code in (401, 403)

    def test_crud_cycle(self, admin_headers):
        payload = {
            "title": "TEST_iter13 broadcast",
            "body_html": "<p>hello</p>",
            "surface": "app_modal",
            "audience": "all",
            "active": False,
        }
        # Create
        r = requests.post(f"{BASE_URL}/api/admin/broadcast-notifications",
                          json=payload, headers=admin_headers, timeout=15)
        assert r.status_code in (200, 201), r.text
        item = r.json()
        nid = item.get("id") or item.get("notification", {}).get("id")
        assert nid

        # List contains
        l = requests.get(f"{BASE_URL}/api/admin/broadcast-notifications", headers=admin_headers)
        assert l.status_code == 200
        ids = [n.get("id") for n in (l.json().get("notifications") or [])]
        assert nid in ids

        # Patch (NotifIn requires full payload)
        p = requests.patch(f"{BASE_URL}/api/admin/broadcast-notifications/{nid}",
                           json={**payload, "active": True}, headers=admin_headers)
        assert p.status_code == 200, p.text

        # Delete
        d = requests.delete(f"{BASE_URL}/api/admin/broadcast-notifications/{nid}",
                            headers=admin_headers)
        assert d.status_code in (200, 204)
