"""Iteration 2 review tests — guest auth, vision board (file-based), fm pages backends."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://zayado-extension-ui.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def guest_token():
    r = requests.post(f"{BASE_URL}/api/auth/guest", json={}, timeout=15)
    assert r.status_code == 200, f"guest login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"no token in guest response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(guest_token):
    return {"Authorization": f"Bearer {guest_token}", "Content-Type": "application/json"}


# ---- auth ----
class TestAuth:
    def test_guest_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/guest", json={}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("access_token") or data.get("token")

    def test_me(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        # guest user should have some id/email field
        assert isinstance(body, dict)


# ---- vision board (no Mongo) ----
class TestVisionBoard:
    def test_board(self):
        r = requests.get(f"{BASE_URL}/api/vision/board", timeout=15)
        assert r.status_code == 200, r.text

    def test_info(self):
        r = requests.get(f"{BASE_URL}/api/vision/info", timeout=15)
        assert r.status_code == 200, r.text

    def test_copilot_data(self):
        r = requests.get(f"{BASE_URL}/api/vision/copilot-data", timeout=15)
        assert r.status_code == 200, r.text

    def test_canva_status(self):
        r = requests.get(f"{BASE_URL}/api/canva/status", timeout=15)
        assert r.status_code == 200, r.text

    def test_visionbook(self):
        r = requests.get(f"{BASE_URL}/api/vision/visionbook", timeout=15)
        assert r.status_code == 200, r.text

    def test_analyse(self):
        r = requests.post(f"{BASE_URL}/api/vision/analyse", json={}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # Expect scores + swot
        assert "scores" in data or "score_global" in data or "global_score" in data, data
        assert "swot" in data or "SWOT" in data or "analysis" in data, data


# ---- fm pages backend (best-effort: should not 500) ----
class TestFmPages:
    def test_finance_overview(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/finance/overview", headers=auth_headers, timeout=15)
        assert r.status_code in (200, 404), r.text  # 404 acceptable if empty for new guest

    def test_wellness_history(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/wellness/history", headers=auth_headers, timeout=15)
        assert r.status_code in (200, 404), r.text

    def test_projects_list(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/projects", headers=auth_headers, timeout=15)
        assert r.status_code in (200, 404), r.text
