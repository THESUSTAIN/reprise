"""Iteration 178 — Vision Board honest data + mobile Storyflow backend sanity."""
import os
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")


@pytest.fixture(scope="module")
def guest_token():
    r = requests.post(f"{BASE_URL}/api/auth/guest", timeout=60)
    if r.status_code != 200:
        pytest.fail(f"guest login failed {r.status_code}: {r.text[:300]}")
    tok = r.json().get("token")
    assert tok, f"no token in {r.json()}"
    return tok


@pytest.fixture(scope="module")
def client(guest_token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {guest_token}"})
    return s


# ── Vision pillars (honest 0% data) ──────────────────────────────────────
class TestVisionPillars:
    def test_pillars_all_undone(self, client):
        r = client.get(f"{BASE_URL}/api/vision/pillars", timeout=30)
        assert r.status_code == 200, r.text[:300]
        pillars = r.json()
        assert isinstance(pillars, list) and len(pillars) >= 3
        for p in pillars:
            assert p["progress"] == 0, f"pillar {p['title']} progress={p['progress']}"
            assert p.get("objectives"), "pillar has no objectives"
            for o in p["objectives"]:
                assert o["done"] is False, f"objective pre-checked: {o}"

    def test_score_zero(self, client):
        r = client.get(f"{BASE_URL}/api/vision/score", timeout=30)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d["global"] == 0, d
        assert d["pillars_count"] >= 3

    def test_memories_empty(self, client):
        r = client.get(f"{BASE_URL}/api/vision/memories", timeout=30)
        assert r.status_code == 200
        assert r.json() == {"memories": []}

    def test_board_empty(self, client):
        r = client.get(f"{BASE_URL}/api/vision/board", timeout=30)
        assert r.status_code == 200
        assert r.json().get("cards") == []

    def test_toggle_objective_persists(self, client):
        pillars = client.get(f"{BASE_URL}/api/vision/pillars", timeout=30).json()
        pillars[0]["objectives"][0]["done"] = True
        expected = round(1 / len(pillars[0]["objectives"]) * 100)
        put = client.put(f"{BASE_URL}/api/vision/pillars", json={"pillars": pillars}, timeout=30)
        assert put.status_code == 200, put.text[:300]
        body = put.json()
        assert body["ok"] is True
        assert body["pillars"][0]["progress"] == expected, body["pillars"][0]
        # GET verifies persistence
        again = client.get(f"{BASE_URL}/api/vision/pillars", timeout=30).json()
        assert again[0]["objectives"][0]["done"] is True
        assert again[0]["progress"] == expected
        # reset
        again[0]["objectives"][0]["done"] = False
        client.put(f"{BASE_URL}/api/vision/pillars", json={"pillars": again}, timeout=30)
        reset = client.get(f"{BASE_URL}/api/vision/pillars", timeout=30).json()
        assert reset[0]["progress"] == 0

    def test_pillars_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/vision/pillars", timeout=30)
        assert r.status_code in (401, 403), r.status_code


# ── AI generation from prompt (real Mammouth) ────────────────────────────
class TestGenerateFromPrompt:
    def test_generate_board(self, client):
        r = client.post(f"{BASE_URL}/api/vision/generate-from-prompt",
                        json={"prompt": "Cabinet de conseil pour dirigeants, lancement Q2"},
                        timeout=120)
        if r.status_code == 502:
            pytest.fail(f"AI generation returned 502: {r.text[:300]}")
        assert r.status_code == 200, r.text[:300]
        cards = r.json().get("cards")
        assert isinstance(cards, list) and len(cards) >= 2, r.json()
        assert cards[0]["title"]["fr"] == "Vision"
        assert isinstance(cards[0]["body"]["fr"], str) and len(cards[0]["body"]["fr"]) > 5

    def test_generate_validation(self, client):
        r = client.post(f"{BASE_URL}/api/vision/generate-from-prompt",
                        json={"prompt": "a"}, timeout=30)
        assert r.status_code == 422, r.status_code


# ── Vision Book export ───────────────────────────────────────────────────
class TestVisionBook:
    def test_book_generate(self, client):
        r = client.post(f"{BASE_URL}/api/vision/book/generate", timeout=180)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        if not d.get("ok"):
            pytest.fail(f"book generation not ok: {d}")
        assert d.get("flipbook_url", "").startswith("http"), d


# ── Task generation ──────────────────────────────────────────────────────
class TestTasksGenerate:
    def test_generate_tasks(self, client):
        r = client.post(f"{BASE_URL}/api/tasks/generate", json={}, timeout=120)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert "items" in d, d
        assert isinstance(d["items"], list) and len(d["items"]) > 0, d
