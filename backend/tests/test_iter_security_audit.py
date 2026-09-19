"""
Security audit tests:
- Magic-link single-use (usage unique)
- 2FA actually enforced on password /login
- Non-regression for password login without 2FA
"""
import os
import json
import sqlite3
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://myext-audit-preview.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
DB_PATH = "/app/backend/zayado.db"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- Magic link single use ----------
def test_magic_link_single_use(s):
    r = s.post(f"{API}/auth/request-link", json={"email": "thomas@zayado.fr"})
    assert r.status_code == 200, r.text
    body = r.json()
    dev_link = body.get("dev_link")
    assert dev_link and "token=" in dev_link, f"dev_link missing: {body}"
    token = dev_link.split("token=")[-1].split("&")[0]

    # First use OK
    r1 = s.post(f"{API}/auth/verify-link", json={"token": token})
    assert r1.status_code == 200, r1.text
    assert "access_token" in r1.json()

    # Second use must fail 401 with specific detail
    r2 = s.post(f"{API}/auth/verify-link", json={"token": token})
    assert r2.status_code == 401, f"expected 401, got {r2.status_code}: {r2.text}"
    detail = r2.json().get("detail", "")
    assert "déjà" in detail or "already" in detail.lower() or "utilis" in detail.lower(), f"unexpected detail: {detail}"


# ---------- 2FA enforced ----------
@pytest.fixture(scope="module")
def audit_user(s):
    email = "audit2fa@example.com"
    password = "MotDePasse123"
    # register (idempotent-ish: if exists, try login)
    r = s.post(f"{API}/auth/register", json={"email": email, "name": "Audit 2FA", "password": password})
    if r.status_code == 200:
        token = r.json()["access_token"]
    else:
        # already exists
        rlog = s.post(f"{API}/auth/login", json={"email": email, "password": password})
        assert rlog.status_code == 200, rlog.text
        body = rlog.json()
        # if 2FA already active from prior run, disable via toggle after login/verify path is complex;
        # attempt: fetch challenge and require reset — safer: skip
        if body.get("requires_2fa"):
            pytest.skip("Existing user already has 2FA; module-level test needs a clean user")
        token = body["access_token"]
    return {"email": email, "password": password, "token": token}


def test_enable_2fa_and_login_challenge(s, audit_user):
    # enable 2FA
    r = s.post(f"{API}/auth/2fa/toggle", headers={"Authorization": f"Bearer {audit_user['token']}"})
    assert r.status_code == 200, r.text
    body = r.json()
    # allow either shape
    tfa = body.get("two_factor_enabled", body.get("enabled"))
    if tfa is False:
        # was toggled off; toggle again
        r = s.post(f"{API}/auth/2fa/toggle", headers={"Authorization": f"Bearer {audit_user['token']}"})
        body = r.json()
        tfa = body.get("two_factor_enabled", body.get("enabled"))
    assert tfa is True, f"2FA not enabled: {body}"

    # login again -> should require 2FA
    r = s.post(f"{API}/auth/login", json={"email": audit_user["email"], "password": audit_user["password"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("requires_2fa") is True, f"expected requires_2fa: {body}"
    assert "access_token" not in body, f"access_token should be absent: {body}"
    challenge = body.get("challenge_token")
    assert challenge, f"missing challenge_token: {body}"

    # read code from DB
    time.sleep(0.5)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT settings FROM users WHERE email = ?", (audit_user["email"],))
    row = cur.fetchone()
    conn.close()
    assert row, "user row not found"
    settings = json.loads(row[0]) if row[0] else {}
    code = settings.get("pending_2fa_code")
    assert code and len(str(code)) == 6, f"pending_2fa_code missing/invalid: {settings}"

    # wrong code -> 400
    rbad = s.post(f"{API}/auth/login/verify-2fa", json={"challenge_token": challenge, "code": "000000" if code != "000000" else "111111"})
    assert rbad.status_code == 400, f"expected 400 for bad code, got {rbad.status_code}: {rbad.text}"
    assert "invalide" in rbad.json().get("detail", "").lower() or "invalid" in rbad.json().get("detail", "").lower()

    # good code -> 200 with access_token
    # NOTE: need fresh challenge if bad attempt invalidated code; re-login
    r = s.post(f"{API}/auth/login", json={"email": audit_user["email"], "password": audit_user["password"]})
    body = r.json()
    challenge = body.get("challenge_token")
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute("SELECT settings FROM users WHERE email = ?", ("audit2fa@example.com",))
    row = cur.fetchone(); conn.close()
    code = json.loads(row[0]).get("pending_2fa_code")

    rok = s.post(f"{API}/auth/login/verify-2fa", json={"challenge_token": challenge, "code": code})
    assert rok.status_code == 200, rok.text
    assert "access_token" in rok.json()


# ---------- Non-regression: password login without 2FA ----------
def test_password_login_no_2fa(s):
    email = f"noaudit2fa+{int(time.time())}@example.com"
    password = "MotDePasse123"
    r = s.post(f"{API}/auth/register", json={"email": email, "name": "No 2FA", "password": password})
    assert r.status_code == 200, r.text

    r = s.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body, f"expected access_token directly: {body}"
    assert not body.get("requires_2fa"), f"should NOT require 2FA: {body}"
