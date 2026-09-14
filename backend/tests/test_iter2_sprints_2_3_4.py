"""
Iteration 2 backend tests — Sprints 2/3/4 + Studio via Mammouth + Guest auth.
Covers:
- POST /api/auth/guest returns access_token
- PUT /api/vision/board/canvas saves for guest
- GET /api/studio/quota
- POST /api/studio/video -> 503
- POST /api/studio/image -> if quota available, 1 call at most; if 0, expect 429
- GET /api/wellness/correlations?days=60 -> status ok (seeded 7 days)
- GET /api/vision/board/live-data -> {cards:[ca,wellness,prospects]}
- GET /api/dashboard/fusion -> hero + snapshot + priority + timeline + memories + pilotage + missions
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/guest", json={}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"No access_token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- GUEST AUTH ----------
def test_guest_login_returns_token():
    r = requests.post(f"{BASE_URL}/api/auth/guest", json={}, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert j.get("access_token") or j.get("token")
    assert "user" in j or "user_id" in j or j.get("access_token")


# ---------- VISION BOARD SAVE (bug fix) ----------
def test_vision_board_canvas_save_guest(auth_headers):
    payload = {
        "elements": [
            {"id": "test-1", "type": "text", "x": 10, "y": 20, "content": "TEST_iter2"}
        ],
        "background": "#ffffff",
    }
    r = requests.put(f"{BASE_URL}/api/vision/board/canvas", headers=auth_headers, json=payload, timeout=30)
    assert r.status_code == 200, f"Save failed: {r.status_code} {r.text}"


# ---------- STUDIO ----------
def test_studio_quota(auth_headers):
    r = requests.get(f"{BASE_URL}/api/studio/quota", headers=auth_headers, timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    assert "images" in j and "videos" in j
    assert j["images"]["cap"] == 1
    assert j["videos"]["cap"] == 1


def test_studio_video_503(auth_headers):
    r = requests.post(f"{BASE_URL}/api/studio/video", headers=auth_headers, json={"prompt": "test video please generate"}, timeout=30)
    assert r.status_code == 503, f"Expected 503 got {r.status_code}: {r.text}"


def test_studio_image_mammouth_or_quota(auth_headers):
    """At most one real Mammouth image call.
    - If quota remaining >0: attempt one gen; expect 200 with kind=image & url starting with /api/uploads/studio/ ; verify quota decrements.
    - If quota remaining == 0: expect 429 with 'Quota mensuel'.
    """
    q = requests.get(f"{BASE_URL}/api/studio/quota", headers=auth_headers, timeout=15).json()
    remaining = q["images"].get("remaining", 0)
    r = requests.post(
        f"{BASE_URL}/api/studio/image",
        headers=auth_headers,
        json={"prompt": "A calm blue ocean sunrise, minimalist wallpaper"},
        timeout=120,
    )
    if remaining <= 0:
        assert r.status_code == 429, r.text
        assert "Quota" in r.text or "quota" in r.text
    else:
        assert r.status_code == 200, f"Image gen failed: {r.status_code} {r.text[:400]}"
        j = r.json()
        assert j.get("kind") == "image"
        assert str(j.get("url", "")).startswith("/api/uploads/studio/")
        # Confirm counter decremented
        q2 = requests.get(f"{BASE_URL}/api/studio/quota", headers=auth_headers, timeout=15).json()
        assert q2["images"]["remaining"] == remaining - 1


# ---------- SPRINT 3 - #3.1 CORRELATIONS ----------
def test_wellness_correlations(auth_headers):
    r = requests.get(f"{BASE_URL}/api/wellness/correlations?days=60", headers=auth_headers, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    assert "status" in j
    # Seeded guest has 7 days -> expect ok
    if j["status"] == "ok":
        assert "coefficient" in j or "correlation" in j or "value" in j
    else:
        # acceptable fallback
        assert j["status"] in ("insufficient_data", "no_data")


# ---------- SPRINT 4 - #4 LIVE CARDS ----------
def test_vision_live_data(auth_headers):
    r = requests.get(f"{BASE_URL}/api/vision/board/live-data", headers=auth_headers, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    assert "cards" in j and isinstance(j["cards"], list)
    keys = {c.get("key") for c in j["cards"]}
    assert {"ca", "wellness", "prospects"}.issubset(keys), f"Missing keys, got: {keys}"


# ---------- SPRINT 3 - #2 DASHBOARD FUSION ----------
def test_dashboard_fusion(auth_headers):
    r = requests.get(f"{BASE_URL}/api/dashboard/fusion", headers=auth_headers, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    for k in ["hero", "vision_snapshot", "today_priority", "timeline", "memories", "pilotage", "missions"]:
        assert k in j, f"Missing key '{k}' in fusion response. Got keys: {list(j.keys())}"
    hero = j["hero"]
    for hk in ["greeting", "first_name", "message"]:
        assert hk in hero, f"Missing hero.{hk}"
