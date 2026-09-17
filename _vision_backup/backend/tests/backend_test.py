"""Backend tests for Vision Board Gallery API"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://vision-board-hub-7.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

EXPECTED_IDS = {"pillars", "roadmap", "identity", "sensory", "strategic"}
REQUIRED_FIELDS = {"id", "category", "accent", "name_fr", "name_en", "subtitle_fr", "subtitle_en"}


# ---- Templates ----
def test_get_templates_returns_five():
    r = requests.get(f"{API}/templates", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 5
    ids = {t["id"] for t in data}
    assert ids == EXPECTED_IDS
    for t in data:
        assert REQUIRED_FIELDS.issubset(t.keys()), f"Missing fields in {t}"


# ---- Favorites ----
def test_get_favorites_unknown_session_returns_empty():
    sid = f"TEST_unknown_{uuid.uuid4().hex[:8]}"
    r = requests.get(f"{API}/favorites/{sid}", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == sid
    assert data["template_ids"] == []


def test_toggle_favorite_add_remove_flow():
    sid = f"TEST_toggle_{uuid.uuid4().hex[:8]}"
    # add pillars
    r1 = requests.post(f"{API}/favorites/toggle", json={"session_id": sid, "template_id": "pillars"}, timeout=15)
    assert r1.status_code == 200
    assert r1.json()["template_ids"] == ["pillars"]

    # add roadmap
    r2 = requests.post(f"{API}/favorites/toggle", json={"session_id": sid, "template_id": "roadmap"}, timeout=15)
    assert r2.status_code == 200
    assert set(r2.json()["template_ids"]) == {"pillars", "roadmap"}

    # GET persists
    r3 = requests.get(f"{API}/favorites/{sid}", timeout=15)
    assert r3.status_code == 200
    assert set(r3.json()["template_ids"]) == {"pillars", "roadmap"}

    # toggle off pillars
    r4 = requests.post(f"{API}/favorites/toggle", json={"session_id": sid, "template_id": "pillars"}, timeout=15)
    assert r4.status_code == 200
    assert r4.json()["template_ids"] == ["roadmap"]

    # toggle off roadmap
    r5 = requests.post(f"{API}/favorites/toggle", json={"session_id": sid, "template_id": "roadmap"}, timeout=15)
    assert r5.status_code == 200
    assert r5.json()["template_ids"] == []
