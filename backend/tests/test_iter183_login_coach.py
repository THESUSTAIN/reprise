"""Iteration 183 — Login refonte (magic link / test account Thomas) + Coach Vision + Vision board basics."""
import os

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
THOMAS = "thomas@zayado.fr"


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def thomas_token(client):
    """Login as Thomas via magic link (preview exposes dev_link)."""
    r = client.post(f"{BASE_URL}/api/auth/request-link", json={"email": THOMAS}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "dev_link" in data, f"dev_link not exposed in preview: {data}"
    token = data["dev_link"].split("token=")[-1]
    v = client.post(f"{BASE_URL}/api/auth/verify-link", json={"token": token}, timeout=30)
    assert v.status_code == 200, v.text
    vd = v.json()
    assert vd["user"]["email"] == THOMAS, vd["user"]
    assert isinstance(vd.get("token"), str) and len(vd["token"]) > 20
    return vd["token"]


# ── AUTH / magic link ────────────────────────────────────────────────
class TestMagicLink:
    def test_request_link_masked_email(self, client):
        r = client.post(f"{BASE_URL}/api/auth/request-link", json={"email": THOMAS}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("masked_email")
        assert d.get("expires_in_minutes") == 15

    def test_request_link_invalid_email(self, client):
        r = client.post(f"{BASE_URL}/api/auth/request-link", json={"email": "not-an-email"}, timeout=20)
        assert r.status_code in (400, 422), r.text

    def test_verify_bad_token(self, client):
        r = client.post(f"{BASE_URL}/api/auth/verify-link", json={"token": "garbage"}, timeout=20)
        assert r.status_code == 401, r.text

    def test_thomas_session_is_not_guest(self, client, thomas_token):
        r = client.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {thomas_token}"}, timeout=20)
        assert r.status_code == 200, r.text
        me = r.json()
        user = me.get("user", me)
        assert user.get("email") == THOMAS, user
        assert "guest" not in (user.get("email") or "")


# ── Coach Vision ─────────────────────────────────────────────────────
class TestCoachVision:
    def test_coach_requires_auth(self, client):
        r = client.post(f"{BASE_URL}/api/vision/coach", json={}, timeout=30)
        assert r.status_code in (401, 403), r.text

    def test_coach_with_cards(self, client, thomas_token):
        payload = {"cards": [
            {"type": "note", "title": {"fr": "Vision"}, "body": {"fr": "Devenir référence du coaching solo"}},
            {"type": "note", "title": {"fr": "Pilier"}, "body": {"fr": "Croissance récurrente"}},
        ]}
        r = client.post(f"{BASE_URL}/api/vision/coach", json=payload,
                        headers={"Authorization": f"Bearer {thomas_token}"}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d.get("summary"), str) and d["summary"].strip()
        actions = d.get("actions")
        assert isinstance(actions, list) and len(actions) == 3, actions
        for a in actions:
            assert a.get("title"), a
            assert a.get("why"), a

    def test_coach_empty_board(self, client, thomas_token):
        r = client.post(f"{BASE_URL}/api/vision/coach", json={"cards": []},
                        headers={"Authorization": f"Bearer {thomas_token}"}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert len(d.get("actions") or []) == 3


# ── Vision board regression (used by mobile canvas) ──────────────────
class TestVisionBoard:
    def test_get_board(self, client, thomas_token):
        r = client.get(f"{BASE_URL}/api/vision/board",
                       headers={"Authorization": f"Bearer {thomas_token}"}, timeout=30)
        assert r.status_code == 200, r.text
        assert isinstance(r.json().get("cards"), list)

    def test_save_board_and_persist(self, client, thomas_token):
        h = {"Authorization": f"Bearer {thomas_token}"}
        original = client.get(f"{BASE_URL}/api/vision/board", headers=h, timeout=30).json()["cards"]
        cards = original + [{"id": "TEST_iter183", "type": "note", "x": 100, "y": 120,
                             "w": 200, "h": 100, "title": {"fr": "TEST_note"}, "body": {"fr": "TEST"}}]
        r = client.put(f"{BASE_URL}/api/vision/board", json={"cards": cards}, headers=h, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json().get("count") == len(cards)
        got = client.get(f"{BASE_URL}/api/vision/board", headers=h, timeout=30).json()["cards"]
        assert any(c.get("id") == "TEST_iter183" for c in got)
        # cleanup — restore original board
        client.put(f"{BASE_URL}/api/vision/board", json={"cards": original}, headers=h, timeout=30)
        after = client.get(f"{BASE_URL}/api/vision/board", headers=h, timeout=30).json()["cards"]
        assert not any(c.get("id") == "TEST_iter183" for c in after)

    def test_save_board_invalid_payload(self, client, thomas_token):
        r = client.put(f"{BASE_URL}/api/vision/board", json={"cards": "nope"},
                       headers={"Authorization": f"Bearer {thomas_token}"}, timeout=30)
        assert r.status_code == 400, r.text

    def test_pillars_and_score(self, client, thomas_token):
        h = {"Authorization": f"Bearer {thomas_token}"}
        p = client.get(f"{BASE_URL}/api/vision/pillars", headers=h, timeout=30)
        assert p.status_code == 200, p.text
        assert isinstance(p.json(), list)
        s = client.get(f"{BASE_URL}/api/vision/score", headers=h, timeout=30)
        assert s.status_code == 200, s.text
        assert isinstance(s.json().get("global"), int)
