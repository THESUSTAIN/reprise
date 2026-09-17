"""
Tests iteration : News-Reprise, HeyGen connecteur (auth machine), Vision SSE, regressions auth.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://smart-board-engine.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASS = "ZayadoAdmin2026!"
WP_SECRET = "80Reg9AWFTf1evDlQtSZYbpXVb6S2KZy_DLM8IwdWx8"


@pytest.fixture(scope="module")
def admin_token():
    # Try password login endpoint (most common)
    for path in ["/auth/login", "/auth/password-login", "/auth/signin"]:
        try:
            r = requests.post(f"{API}{path}", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=15)
            if r.status_code == 200:
                data = r.json()
                tok = data.get("access_token") or data.get("token") or (data.get("data") or {}).get("access_token")
                if tok:
                    return tok
        except Exception:
            pass
    pytest.skip("Cannot authenticate admin")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ─────────── News-Reprise ───────────
class TestNewsReprise:
    draft_id = None

    def test_submit_requires_auth(self):
        r = requests.post(f"{API}/news-reprise/submit", json={"from_email": "x@y.z", "subject": "S", "body": "hello"}, timeout=15)
        assert r.status_code in (401, 403), f"got {r.status_code}"

    def test_submit_manual(self, auth_headers):
        payload = {"from_email": "concurrent@example.com", "subject": "Notre nouvelle offre", "body": "Bonjour, découvrez notre plateforme concurrente ..."}
        r = requests.post(f"{API}/news-reprise/submit", json=payload, headers=auth_headers, timeout=90)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert data.get("status") == "draft"
        assert data.get("id")
        assert data.get("rewritten_subject", "").strip() != ""
        assert data.get("scheduled_at")
        # scheduled_at ~ +72h
        from datetime import datetime, timezone, timedelta
        sched = datetime.fromisoformat(data["scheduled_at"].replace("Z", "+00:00"))
        delta = sched - datetime.now(timezone.utc)
        assert timedelta(hours=70) < delta < timedelta(hours=74), f"delta={delta}"
        TestNewsReprise.draft_id = data["id"]

    def test_list(self, auth_headers):
        r = requests.get(f"{API}/news-reprise/list", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "mailbox" in data
        assert data.get("delay_hours") == 72
        assert "drafts" in data and isinstance(data["drafts"], list)
        assert "total" in data
        ids = [d["id"] for d in data["drafts"]]
        assert TestNewsReprise.draft_id in ids

    def test_approve(self, auth_headers):
        assert TestNewsReprise.draft_id
        r = requests.put(f"{API}/news-reprise/{TestNewsReprise.draft_id}/approve", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "approved"

    def test_reject(self, auth_headers):
        # create new one to reject
        payload = {"from_email": "b@example.com", "subject": "Test reject", "body": "content"}
        r = requests.post(f"{API}/news-reprise/submit", json=payload, headers=auth_headers, timeout=90)
        assert r.status_code == 200
        did = r.json()["id"]
        r2 = requests.put(f"{API}/news-reprise/{did}/reject", headers=auth_headers, timeout=15)
        assert r2.status_code == 200
        assert r2.json().get("status") == "rejected"

    def test_inbound_with_secret(self):
        payload = {"from": "spam@rival.com", "subject": "Nouveauté inbound", "body": "Un mail entrant"}
        r = requests.post(f"{API}/news-reprise/inbound", json=payload, headers={"X-Zayado-Secret": WP_SECRET}, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True
        assert d.get("id")
        assert d.get("status") == "draft"

    def test_inbound_no_secret(self):
        r = requests.post(f"{API}/news-reprise/inbound", json={"from": "a", "subject": "b", "body": "c"}, timeout=15)
        assert r.status_code == 401

    def test_inbound_bad_secret(self):
        r = requests.post(f"{API}/news-reprise/inbound", json={"from": "a", "subject": "b", "body": "c"}, headers={"X-Zayado-Secret": "wrong"}, timeout=15)
        assert r.status_code == 401


# ─────────── HeyGen connector ───────────
class TestHeygen:
    def test_avatars_with_secret_returns_500_missing_key(self):
        r = requests.get(f"{API}/heygen/avatars", headers={"X-Zayado-Secret": WP_SECRET}, timeout=15)
        assert r.status_code == 500, f"expected 500 got {r.status_code} body={r.text[:200]}"
        assert "HEYGEN_API_KEY" in r.text

    def test_avatars_no_secret_401(self):
        r = requests.get(f"{API}/heygen/avatars", timeout=15)
        assert r.status_code == 401

    def test_avatars_bad_secret_401(self):
        r = requests.get(f"{API}/heygen/avatars", headers={"X-Zayado-Secret": "nope"}, timeout=15)
        assert r.status_code == 401


# ─────────── Vision SSE ───────────
class TestVisionSSE:
    def test_stream_invalid_token(self):
        r = requests.get(f"{API}/vision/events/stream", params={"token": "invalid.jwt.token"}, timeout=10)
        assert r.status_code == 401

    def test_stream_valid_token(self, admin_token):
        with requests.get(f"{API}/vision/events/stream", params={"token": admin_token}, stream=True, timeout=10) as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")
            first = next(r.iter_lines(decode_unicode=True))
            # Skip empty lines
            while first is not None and first == "":
                first = next(r.iter_lines(decode_unicode=True))
            assert first.startswith("retry:"), f"first line: {first!r}"


# ─────────── Regressions ───────────
class TestRegressions:
    def test_magic_link_idempotent(self):
        # Request magic link
        r = requests.post(f"{API}/auth/request-link", json={"email": ADMIN_EMAIL}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # #28 : delivered_via_email true (Brevo)
        assert data.get("delivered_via_email") is True, f"delivered_via_email missing: {data}"
        # In dev/staging the token may be returned; otherwise skip idempotency test
        token = data.get("token") or data.get("magic_token") or data.get("dev_token")
        if not token and data.get("dev_link"):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(data["dev_link"]).query)
            token = (q.get("token") or [None])[0]
        if not token:
            pytest.skip("magic token not returned (production mode) — idempotency requires DB access")
        r1 = requests.post(f"{API}/auth/verify-link", json={"token": token}, timeout=15)
        assert r1.status_code == 200, r1.text
        r2 = requests.post(f"{API}/auth/verify-link", json={"token": token}, timeout=15)
        assert r2.status_code == 200, f"second call not idempotent: {r2.status_code} {r2.text}"
