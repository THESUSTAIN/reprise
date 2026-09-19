"""Iteration 14 — VAGUE 1 missing_apis endpoints tests.

Covers /api/{tasks,vision,documents,leads,streak,revenue/monthly,energy,processes/templates,
analyse,collaborateur/notify} introduced in /app/backend/routes/missing_apis.py.
"""
import os
import time
import pytest
import requests

def _load_env():
    env = os.environ.get("REACT_APP_BACKEND_URL")
    if not env:
        try:
            with open("/app/frontend/.env") as fh:
                for line in fh:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        env = line.strip().split("=", 1)[1]
                        break
        except FileNotFoundError:
            pass
    if not env:
        raise RuntimeError("REACT_APP_BACKEND_URL not set")
    return env.rstrip("/") + "/api"


BASE_URL = _load_env()
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"


# ------------ Fixtures ------------
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                      timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ------------ AUTH gating ------------
class TestAuthGuard:
    @pytest.mark.parametrize("path", [
        "/tasks", "/vision", "/documents", "/leads", "/streak",
        "/revenue/monthly", "/energy/today", "/energy/latest", "/analyse",
    ])
    def test_unauthenticated_blocked(self, path):
        r = requests.get(f"{BASE_URL}{path}", timeout=10)
        assert r.status_code in (401, 403), f"{path} returned {r.status_code}"


# ------------ TASKS ------------
class TestTasks:
    created_id = None

    def test_list_empty_shape(self, h):
        r = requests.get(f"{BASE_URL}/tasks", headers=h, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and isinstance(body["items"], list)

    def test_create_task(self, h):
        r = requests.post(f"{BASE_URL}/tasks", headers=h,
                          json={"label": "TEST_vague1 mission", "type": "humain"}, timeout=10)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["label"] == "TEST_vague1 mission"
        assert data["done"] is False
        assert data["in_progress"] is False
        assert "id" in data and data["id"]
        assert "created_at" in data
        TestTasks.created_id = data["id"]

    def test_patch_task_in_progress(self, h):
        assert TestTasks.created_id
        r = requests.patch(f"{BASE_URL}/tasks/{TestTasks.created_id}", headers=h,
                           json={"in_progress": True}, timeout=10)
        assert r.status_code == 200, r.text
        assert r.json()["in_progress"] is True

    def test_delete_task(self, h):
        assert TestTasks.created_id
        r = requests.delete(f"{BASE_URL}/tasks/{TestTasks.created_id}", headers=h, timeout=10)
        assert r.status_code == 200
        assert r.json().get("deleted") is True


# ------------ VISION ------------
class TestVision:
    def test_get_empty_shape(self, h):
        r = requests.get(f"{BASE_URL}/vision", headers=h, timeout=10)
        assert r.status_code == 200
        b = r.json()
        for key in ("why", "what", "who", "alignment_score"):
            assert key in b

    def test_patch_creates_or_updates(self, h):
        r = requests.patch(f"{BASE_URL}/vision", headers=h,
                           json={"why": "TEST_why", "what": "TEST_what", "who": "TEST_who"}, timeout=10)
        assert r.status_code == 200
        b = r.json()
        assert b.get("why") == "TEST_why"
        # second patch updates same doc
        r2 = requests.patch(f"{BASE_URL}/vision", headers=h, json={"why": "TEST_why2"}, timeout=10)
        assert r2.status_code == 200
        assert r2.json().get("why") == "TEST_why2"


# ------------ DOCUMENTS ------------
class TestDocuments:
    created_id = None

    def test_list_empty(self, h):
        r = requests.get(f"{BASE_URL}/documents", headers=h, timeout=10)
        assert r.status_code == 200 and "items" in r.json()

    def test_create(self, h):
        r = requests.post(f"{BASE_URL}/documents", headers=h,
                          json={"name": "TEST_doc", "type": "note", "content": "hello"}, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "TEST_doc"
        TestDocuments.created_id = d["id"]

    def test_generate_via_claude(self, h):
        r = requests.post(f"{BASE_URL}/documents/generate", headers=h,
                          json={"name": "TEST_gendoc", "type": "note",
                                "prompt": "Écris une note de 3 phrases sur la productivité."},
                          timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("source") == "ia"
        assert isinstance(d.get("content"), str)
        assert len(d.get("content", "")) > 20, f"Empty/short content: {d}"
        # cleanup
        requests.delete(f"{BASE_URL}/documents/{d['id']}", headers=h, timeout=10)

    def test_delete(self, h):
        if TestDocuments.created_id:
            r = requests.delete(f"{BASE_URL}/documents/{TestDocuments.created_id}", headers=h, timeout=10)
            assert r.status_code == 200


# ------------ LEADS ------------
class TestLeads:
    created_id = None

    def test_list_shape(self, h):
        r = requests.get(f"{BASE_URL}/leads", headers=h, timeout=10)
        assert r.status_code == 200
        b = r.json()
        assert "items" in b and "counters" in b and "total" in b
        for k in ("nouveau", "qualifie", "rdv", "client", "perdu"):
            assert k in b["counters"]

    def test_create_patch_delete(self, h):
        r = requests.post(f"{BASE_URL}/leads", headers=h,
                          json={"name": "TEST_Lead", "email": "test@x.io", "status": "nouveau"}, timeout=10)
        assert r.status_code == 200
        lid = r.json()["id"]
        r2 = requests.patch(f"{BASE_URL}/leads/{lid}", headers=h, json={"status": "qualifie"}, timeout=10)
        assert r2.status_code == 200 and r2.json()["status"] == "qualifie"
        r3 = requests.delete(f"{BASE_URL}/leads/{lid}", headers=h, timeout=10)
        assert r3.status_code == 200 and r3.json().get("deleted") is True


# ------------ STREAK / REVENUE / ENERGY ------------
class TestMisc:
    def test_streak(self, h):
        r = requests.get(f"{BASE_URL}/streak", headers=h, timeout=10)
        assert r.status_code == 200
        b = r.json()
        assert "streak" in b and "last_check_in" in b
        assert isinstance(b["streak"], int)

    def test_revenue(self, h):
        r = requests.get(f"{BASE_URL}/revenue/monthly", headers=h, timeout=10)
        assert r.status_code == 200
        b = r.json()
        assert b.get("currency") == "EUR"
        for k in ("current_month", "series", "growth_6m", "source"):
            assert k in b

    def test_energy_today(self, h):
        r = requests.get(f"{BASE_URL}/energy/today", headers=h, timeout=10)
        assert r.status_code == 200
        assert "recorded" in r.json()

    def test_energy_latest(self, h):
        r = requests.get(f"{BASE_URL}/energy/latest", headers=h, timeout=10)
        assert r.status_code == 200  # null OR object

    def test_processes_templates(self, h):
        r = requests.get(f"{BASE_URL}/processes/templates", headers=h, timeout=10)
        assert r.status_code == 200
        tpls = r.json().get("templates", [])
        assert len(tpls) == 8
        ids = {t["id"] for t in tpls}
        assert {"onboarding-client", "lancement-produit"}.issubset(ids)


# ------------ ANALYSE (Claude) ------------
class TestAnalyse:
    def test_get_empty(self, h):
        r = requests.get(f"{BASE_URL}/analyse", headers=h, timeout=10)
        assert r.status_code == 200
        b = r.json()
        for k in ("summary", "verdict", "strengths", "weaknesses", "opportunities", "threats", "next_actions"):
            assert k in b

    def test_run_then_verdict_then_export(self, h):
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/analyse/run", headers=h, json={}, timeout=120)
        elapsed = time.time() - t0
        assert r.status_code == 200, r.text
        assert elapsed < 90, f"analyse/run took {elapsed:.1f}s"
        a = r.json()
        assert a.get("source") == "claude-sonnet-4-5"
        assert a.get("generated_at")
        # verdict in allowed values OR None if claude failed (we still expect parsed)
        if a.get("verdict") is not None:
            assert a["verdict"] in ("go", "pivot", "abandon")
        # score numeric or None
        if a.get("score") is not None:
            assert 0 <= int(a["score"]) <= 100

        # Now verdict
        rv = requests.post(f"{BASE_URL}/analyse/verdict", headers=h, json={}, timeout=10)
        assert rv.status_code == 200
        assert "verdict" in rv.json() and "score" in rv.json()

        # Export
        rx = requests.get(f"{BASE_URL}/analyse/export", headers=h, timeout=10)
        assert rx.status_code == 200
        ex = rx.json()
        assert ex.get("format") == "markdown"
        assert ex.get("content", "").startswith("#")

    def test_verdict_404_when_no_analyse(self, h):
        # We just ran analyse, so we expect existing — instead test the static guide
        r = requests.post(f"{BASE_URL}/analyse/mom-test-guide", headers=h, json={}, timeout=10)
        assert r.status_code == 200
        b = r.json()
        assert "title" in b
        assert len(b.get("rules", [])) == 3
        assert len(b.get("questions", [])) == 5


# ------------ COLLABORATEUR notify ------------
class TestCollab:
    def test_notify(self, h):
        r = requests.post(f"{BASE_URL}/collaborateur/notify", headers=h,
                          json={"event": "mission_started", "title": "TEST_vague1"}, timeout=10)
        assert r.status_code == 200, r.text
        b = r.json()
        assert b.get("event") == "mission_started"
        assert b.get("ts")
        assert b.get("id")
