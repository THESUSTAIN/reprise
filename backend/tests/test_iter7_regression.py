"""Iteration 7 regression sanity — API base defaulting to '' code change."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
EMAIL = "thomas@zayado.fr"
PASSWORD = "Thomas2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health():
    r = requests.get(f"{BASE_URL}/api/health", timeout=15)
    assert r.status_code == 200


def test_auth_me(auth_headers):
    r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=15)
    assert r.status_code == 200
    assert r.json().get("email") == EMAIL


def test_growth(auth_headers):
    r = requests.get(f"{BASE_URL}/api/growth", headers=auth_headers, timeout=20)
    assert r.status_code == 200


def test_vision_live_data(auth_headers):
    r = requests.get(f"{BASE_URL}/api/vision/board/live-data", headers=auth_headers, timeout=20)
    assert r.status_code == 200
    data = r.json()
    # Should contain some sort of card data
    assert isinstance(data, dict)


def test_simulation_state(auth_headers):
    r = requests.get(f"{BASE_URL}/api/simulation/state", headers=auth_headers, timeout=20)
    assert r.status_code == 200


def test_request_link_returns_dev_link():
    r = requests.post(f"{BASE_URL}/api/auth/request-link", json={"email": EMAIL}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    # In preview, dev_link should be returned
    assert "dev_link" in body or "link" in body or body.get("ok") is True
