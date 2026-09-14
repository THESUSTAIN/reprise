"""Sprint 1 tests: Studio quota persistence (#5) + metering per plan (#6)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def guest_token():
    r = requests.post(f"{BASE_URL}/api/auth/guest", timeout=30)
    assert r.status_code == 200, f"guest login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"no token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(guest_token):
    return {"Authorization": f"Bearer {guest_token}"}


# ---------- Auth / boot ----------
def test_guest_login_returns_access_token():
    r = requests.post(f"{BASE_URL}/api/auth/guest", timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and isinstance(body["access_token"], str) and len(body["access_token"]) > 20


# ---------- Templates (public) ----------
def test_studio_templates_public():
    r = requests.get(f"{BASE_URL}/api/studio/templates", timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "images" in body and "videos" in body
    assert isinstance(body["images"], list) and len(body["images"]) >= 1
    assert isinstance(body["videos"], list) and len(body["videos"]) >= 1
    # sanity - fields present
    img0 = body["images"][0]
    assert "id" in img0 and "label" in img0


# ---------- Quota (auth) - fresh guest ----------
def test_studio_quota_free_guest(auth_headers):
    r = requests.get(f"{BASE_URL}/api/studio/quota", headers=auth_headers, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("plan", "free") in ("free", None, "")
    assert body["images"]["cap"] == 1
    assert body["videos"]["cap"] == 1
    assert body["images"]["remaining"] in (0, 1)
    assert body["videos"]["remaining"] in (0, 1)


def test_studio_quota_requires_auth():
    r = requests.get(f"{BASE_URL}/api/studio/quota", timeout=30)
    assert r.status_code in (401, 403)


# ---------- Persistence (#5): quota unchanged after failed generation ----------
def test_studio_image_failure_does_not_increment(auth_headers):
    # capture quota before
    r0 = requests.get(f"{BASE_URL}/api/studio/quota", headers=auth_headers, timeout=30)
    assert r0.status_code == 200
    before = r0.json()["images"]["remaining"]

    # attempt generation (Emergent key may return 429 concurrent_request_limit -> expected)
    r = requests.post(
        f"{BASE_URL}/api/studio/image",
        headers={**auth_headers, "Content-Type": "application/json"},
        json={"prompt": "test prompt sprint1", "template": "portrait"},
        timeout=120,
    )
    # We accept success (200) or failure (429/502/500). Only assert quota invariant on failure.
    if r.status_code == 200:
        pytest.skip("Image generation succeeded — cannot assert 'no increment on failure' here.")
    assert r.status_code in (429, 500, 502, 503), f"Unexpected status: {r.status_code} {r.text[:200]}"

    r1 = requests.get(f"{BASE_URL}/api/studio/quota", headers=auth_headers, timeout=30)
    assert r1.status_code == 200
    after = r1.json()["images"]["remaining"]
    assert after == before, f"Quota changed after failed generation: {before} -> {after}"


# ---------- Metering config (#6) - inspected via templates+quota, sanity of caps ----------
def test_studio_limits_module_constants():
    # Import the module directly to assert STUDIO_LIMITS logic without hitting DB per plan.
    import importlib, sys
    sys.path.insert(0, "/app/backend")
    mod = importlib.import_module("routes.studio")
    lim = mod.STUDIO_LIMITS
    assert lim["free"] == {"image": 1, "video": 1}
    for finite in ("free", "start", "trajectoire", "grow"):
        assert lim[finite]["image"] is not None and lim[finite]["video"] is not None
    for unlimited in ("serenite", "business", "admin"):
        assert lim[unlimited]["image"] is None and lim[unlimited]["video"] is None
