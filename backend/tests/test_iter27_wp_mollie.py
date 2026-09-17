"""Iteration 27 backend test — Mollie + WP-sync wired correctly.

Items:
- /api/payments/plans returns start/grow/serenity (non legacy)
- /api/payments/subscribe returns checkout_url (Mollie URL) or success for admin
- /api/payments/webhook exists (POST → not 404/500)
- /api/wp/pages: 8+ pages with slug/title/modified
- /api/wp/page/a-propos: exists True + content_html non vide
- /api/wp/webhook/invalidate: wrong secret 403, right secret 200
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PWD = "Test1234!"

# Read WP_WEBHOOK_SECRET from backend/.env
WP_SECRET = ""
try:
    for line in open("/app/backend/.env"):
        if line.startswith("WP_WEBHOOK_SECRET"):
            WP_SECRET = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
except Exception:
    pass


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PWD}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── Mollie / Payments ─────────────────────────────────────────────────────
class TestPayments:
    def test_plans_includes_new_tiers(self):
        r = requests.get(f"{BASE_URL}/api/payments/plans", timeout=15)
        assert r.status_code == 200, r.text[:300]
        plans = r.json()
        assert isinstance(plans, list) and len(plans) > 0
        ids = {p.get("id") for p in plans}
        assert "start" in ids, f"Missing 'start' plan. Got: {ids}"
        assert "grow" in ids, f"Missing 'grow' plan. Got: {ids}"
        assert "serenity" in ids, f"Missing 'serenity' plan. Got: {ids}"
        # Non-legacy
        non_legacy = [p for p in plans if not p.get("legacy") and p.get("id") in ("start", "grow", "serenity")]
        assert len(non_legacy) >= 3

    def test_subscribe_returns_checkout_or_success(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/payments/subscribe",
                          json={"plan_id": "start", "billing": "monthly"},
                          headers=auth_headers, timeout=30)
        # Should NOT be 404/500 — endpoint must be wired correctly
        assert r.status_code not in (404, 500), f"Endpoint broken: {r.status_code} {r.text[:300]}"
        # Accept 200 with redirect/checkout/success OR 400/409 if admin already on business
        if r.status_code == 200:
            data = r.json()
            status = data.get("status")
            checkout_url = data.get("checkout_url") or data.get("url") or ""
            if checkout_url:
                assert re.match(r"^https://(www\.|checkout\.)?mollie\.com/", checkout_url), \
                    f"checkout_url not a Mollie URL: {checkout_url}"
            else:
                # Plan already active or success short-circuit
                assert status in ("success", "active", "already_subscribed", "redirect", "ok"), \
                    f"Unexpected status: {data}"
        else:
            # 400/409 acceptable if admin can't downgrade/resubscribe
            assert r.status_code in (400, 401, 403, 409, 422), f"Unexpected: {r.status_code} {r.text[:200]}"

    def test_webhook_endpoint_wired(self):
        # Webhook should accept POST and not return 404/500 even without payload
        r = requests.post(f"{BASE_URL}/api/payments/webhook", data={}, timeout=15)
        assert r.status_code != 404, "Webhook endpoint MISSING (404)"
        assert r.status_code != 405, "Webhook does not accept POST"
        # Mollie webhook typically returns 200 or 400/422 for invalid payload
        assert r.status_code < 500, f"Webhook crashed: {r.status_code} {r.text[:200]}"


# ── WordPress Sync ────────────────────────────────────────────────────────
class TestWPSync:
    def test_list_pages_returns_8_plus(self):
        r = requests.get(f"{BASE_URL}/api/wp/pages", timeout=20)
        assert r.status_code == 200, f"WP pages: {r.status_code} {r.text[:300]}"
        data = r.json()
        items = data.get("items", [])
        assert len(items) >= 8, f"Expected 8+ pages, got {len(items)}"
        # Validate shape
        first = items[0]
        assert "slug" in first and "title" in first and "modified" in first

    def test_get_page_a_propos(self):
        r = requests.get(f"{BASE_URL}/api/wp/page/a-propos", timeout=20)
        assert r.status_code == 200, f"page a-propos: {r.status_code} {r.text[:300]}"
        data = r.json()
        assert data.get("exists") is True, f"a-propos page does not exist: {data}"
        assert data.get("content_html"), "content_html is empty"
        assert len(data["content_html"]) > 50

    def test_webhook_invalidate_wrong_secret(self):
        r = requests.post(f"{BASE_URL}/api/wp/webhook/invalidate?secret=wrong", timeout=10)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_webhook_invalidate_right_secret(self):
        if not WP_SECRET:
            pytest.skip("WP_WEBHOOK_SECRET not found in backend/.env")
        r = requests.post(f"{BASE_URL}/api/wp/webhook/invalidate?secret={WP_SECRET}", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert data.get("status") == "ok"


# ── Pilotage / Croissance smoke (just GET endpoints render) ───────────────
class TestModulesSmoke:
    def test_pilotage_endpoints(self, auth_headers):
        # Common pilotage endpoints
        for path in ["/api/finance/summary", "/api/finance/kpis", "/api/pilotage/summary"]:
            r = requests.get(f"{BASE_URL}{path}", headers=auth_headers, timeout=15)
            # Just check not 500
            if r.status_code == 500:
                pytest.fail(f"{path} returns 500: {r.text[:200]}")

    def test_croissance_endpoints(self, auth_headers):
        for path in ["/api/croissance/kpis", "/api/croissance/sources", "/api/croissance/outils"]:
            r = requests.get(f"{BASE_URL}{path}", headers=auth_headers, timeout=15)
            if r.status_code == 500:
                pytest.fail(f"{path} returns 500: {r.text[:200]}")
