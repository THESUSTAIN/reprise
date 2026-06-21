"""Backend tests for the Zayado MyExtension-ai review request.
Covers: auth/login, vision board public endpoints, finance, wellness, projects.
"""
import os
import time
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://zayado-extension-ui.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
EMAIL = "test@zayado.net"
PASSWORD = "Test1234!"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

TOKEN = None


def _auth():
    global TOKEN
    if TOKEN:
        return {"Authorization": f"Bearer {TOKEN}"}
    r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed {r.status_code} {r.text[:300]}"
    data = r.json()
    TOKEN = data.get("access_token") or data.get("token")
    assert TOKEN, f"no token in {data}"
    return {"Authorization": f"Bearer {TOKEN}"}


# ── Auth ─────────────────────────────────────────────────────────────
def test_login_success():
    r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert (d.get("access_token") or d.get("token"))
    assert d.get("user", {}).get("email") == EMAIL


def test_login_invalid():
    r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": "wrong"}, timeout=30)
    assert r.status_code == 401


def test_auth_me():
    h = _auth()
    r = session.get(f"{API}/auth/me", headers=h, timeout=30)
    assert r.status_code == 200, r.text[:300]
    assert r.json().get("email") == EMAIL


# ── Vision Board (public, no auth, user_id=demo) ─────────────────────
VISION_GET_ENDPOINTS = [
    "/vision/board",
    "/vision/info",
    "/vision/copilot-data",
    "/canva/status",
    "/vision/visionbook",
]


def test_vision_get_endpoints():
    failures = []
    for ep in VISION_GET_ENDPOINTS:
        r = session.get(f"{API}{ep}", timeout=30)
        if r.status_code != 200:
            failures.append(f"{ep} -> {r.status_code} {r.text[:200]}")
    assert not failures, "Vision endpoints failed: " + " | ".join(failures)


def test_vision_analyse():
    r = session.post(f"{API}/vision/analyse", json={}, timeout=60)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    d = r.json()
    # Expect some scoring keys in response
    text = str(d).lower()
    assert any(k in text for k in ["clart", "score", "alignement", "ambition"])


# ── Finance ──────────────────────────────────────────────────────────
def test_finance_overview():
    h = _auth()
    r = session.get(f"{API}/finance/overview", headers=h, timeout=30)
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    for k in ("revenus", "depenses", "net", "taux_marge", "weekly"):
        assert k in d, f"missing {k} in {list(d.keys())}"


def test_finance_forecast():
    h = _auth()
    r = session.get(f"{API}/finance/forecast", headers=h, timeout=30)
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert "forecast" in d and isinstance(d["forecast"], list) and len(d["forecast"]) == 3


def test_finance_serenity():
    h = _auth()
    r = session.get(f"{API}/finance/serenity", headers=h, timeout=30)
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert "score" in d and "pillars" in d


def test_finance_entry_creates_and_reflects():
    h = _auth()
    # baseline
    r0 = session.get(f"{API}/finance/overview", headers=h, timeout=30).json()
    base_rev = r0.get("revenus", 0)
    payload = {"type": "revenu", "label": "TEST_review_entry", "amount": 123.45, "category": "test"}
    r = session.post(f"{API}/finance/entry", json=payload, headers=h, timeout=30)
    assert r.status_code == 200, r.text[:300]
    entry = r.json().get("entry", {})
    assert entry.get("label") == "TEST_review_entry"
    assert entry.get("amount") == 123.45
    # verify reflected
    r2 = session.get(f"{API}/finance/overview", headers=h, timeout=30).json()
    assert r2.get("revenus", 0) >= base_rev + 123.44


# ── Wellness ─────────────────────────────────────────────────────────
def test_wellness_checkin_and_history():
    h = _auth()
    payload = {"energy": 4, "mood": 4, "stress": 2, "sleep": 3, "notes": "TEST_review"}
    r = session.post(f"{API}/wellness/checkin", json=payload, headers=h, timeout=30)
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert "score" in d and isinstance(d["score"], int)
    assert "micro_actions" in d
    # history
    rh = session.get(f"{API}/wellness/history", headers=h, timeout=30)
    assert rh.status_code == 200, rh.text[:300]
    hd = rh.json()
    assert "checkins" in hd and len(hd["checkins"]) >= 1


# ── Projects (Espace de travail) ─────────────────────────────────────
def test_projects_crud_and_timer():
    h = _auth()
    # list
    r0 = session.get(f"{API}/projects", headers=h, timeout=30)
    assert r0.status_code == 200, r0.text[:300]
    # create
    rc = session.post(f"{API}/projects", json={"name": "TEST_mission_review", "hourly_rate": 50.0, "color": "#1E3A8A"}, headers=h, timeout=30)
    assert rc.status_code == 200, rc.text[:300]
    pid = rc.json().get("id")
    assert pid
    # start
    rs = session.post(f"{API}/projects/{pid}/start", headers=h, timeout=30)
    assert rs.status_code == 200, rs.text[:300]
    time.sleep(1.2)
    # stop
    rst = session.post(f"{API}/projects/{pid}/stop", headers=h, timeout=30)
    assert rst.status_code == 200, rst.text[:300]
    assert rst.json().get("total_seconds", 0) >= 1
    # delete
    rd = session.delete(f"{API}/projects/{pid}", headers=h, timeout=30)
    assert rd.status_code == 200, rd.text[:300]
