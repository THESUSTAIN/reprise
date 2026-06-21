"""Iteration 164 — audit endpoints listés par main agent."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://tarif-preview-v2.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "1@Elshaddai1"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


ENDPOINTS_GET = [
    "/api/custom-agents",
    "/api/custom-agents/tools",
    "/api/custom-agents/templates",
    "/api/features/captures",
    "/api/projects",
    "/api/timer/sessions",
    "/api/processes",
    "/api/workflows",
    "/api/chat/conversations?limit=10",
]


@pytest.mark.parametrize("path", ENDPOINTS_GET)
def test_get_endpoint_ok(path, auth_headers):
    r = requests.get(f"{BASE_URL}{path}", headers=auth_headers, timeout=20)
    assert r.status_code == 200, f"{path} → {r.status_code} {r.text[:300]}"
