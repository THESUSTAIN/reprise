"""Broadcast notification system — full backend test (admin CRUD + public /active)."""
import os
from datetime import datetime, timedelta, timezone

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"


# ───────────── fixtures ─────────────
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    assert data["user"]["role"] == "super_admin"
    return data["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture
def created_ids():
    ids = []
    yield ids
    # teardown — delete all notifs created during this test
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    if r.status_code == 200:
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        for nid in ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/admin/broadcast-notifications/{nid}",
                    headers=headers,
                    timeout=10,
                )
            except Exception:
                pass


# ───────────── auth tests ─────────────
def test_login_super_admin():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role"] == "super_admin"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 20


def test_list_notifs_requires_auth():
    r = requests.get(f"{BASE_URL}/api/admin/broadcast-notifications", timeout=15)
    assert r.status_code in (401, 403), f"unexpected {r.status_code}"


def test_list_notifs_with_admin(admin_headers):
    r = requests.get(
        f"{BASE_URL}/api/admin/broadcast-notifications", headers=admin_headers, timeout=15
    )
    assert r.status_code == 200
    data = r.json()
    assert "notifications" in data
    assert isinstance(data["notifications"], list)


# ───────────── CRUD ─────────────
def test_create_notif(admin_headers, created_ids):
    payload = {
        "title": "TEST_broadcast_create",
        "body_html": "<p>hello</p>",
        "embed_url": None,
        "surface": "app_modal",
        "audience": "all",
        "cta_label": "Open",
        "cta_url": "https://example.com",
        "active": True,
    }
    r = requests.post(
        f"{BASE_URL}/api/admin/broadcast-notifications",
        json=payload,
        headers=admin_headers,
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["title"] == payload["title"]
    assert body["surface"] == "app_modal"
    assert body["audience"] == "all"
    assert body["active"] is True
    assert "id" in body
    created_ids.append(body["id"])

    # verify via list
    r2 = requests.get(
        f"{BASE_URL}/api/admin/broadcast-notifications", headers=admin_headers, timeout=15
    )
    ids = [n["id"] for n in r2.json()["notifications"]]
    assert body["id"] in ids


def test_patch_notif(admin_headers, created_ids):
    payload = {
        "title": "TEST_to_update",
        "surface": "app_modal",
        "audience": "all",
        "active": True,
    }
    r = requests.post(
        f"{BASE_URL}/api/admin/broadcast-notifications",
        json=payload,
        headers=admin_headers,
        timeout=15,
    )
    nid = r.json()["id"]
    created_ids.append(nid)

    upd = {
        "title": "TEST_updated_title",
        "surface": "app_modal",
        "audience": "all",
        "active": False,
    }
    r2 = requests.patch(
        f"{BASE_URL}/api/admin/broadcast-notifications/{nid}",
        json=upd,
        headers=admin_headers,
        timeout=15,
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["title"] == "TEST_updated_title"
    assert body["active"] is False


def test_delete_notif(admin_headers):
    payload = {"title": "TEST_to_delete", "surface": "app_modal", "audience": "all", "active": True}
    r = requests.post(
        f"{BASE_URL}/api/admin/broadcast-notifications",
        json=payload,
        headers=admin_headers,
        timeout=15,
    )
    nid = r.json()["id"]
    r2 = requests.delete(
        f"{BASE_URL}/api/admin/broadcast-notifications/{nid}",
        headers=admin_headers,
        timeout=15,
    )
    assert r2.status_code == 200
    assert r2.json().get("status") == "deleted"


# ───────────── /active public endpoint ─────────────
def _deactivate_all_for_surface(admin_headers, surface):
    """Disable any pre-existing notifs on this surface so tests are deterministic."""
    r = requests.get(
        f"{BASE_URL}/api/admin/broadcast-notifications", headers=admin_headers, timeout=15
    )
    saved = []
    for n in r.json().get("notifications", []):
        if n["surface"] == surface and n["active"]:
            requests.patch(
                f"{BASE_URL}/api/admin/broadcast-notifications/{n['id']}",
                json={"title": n["title"], "surface": n["surface"], "audience": n["audience"], "active": False},
                headers=admin_headers,
                timeout=10,
            )
            saved.append(n)
    return saved


def _restore(admin_headers, saved):
    for n in saved:
        requests.patch(
            f"{BASE_URL}/api/admin/broadcast-notifications/{n['id']}",
            json={"title": n["title"], "surface": n["surface"], "audience": n["audience"], "active": True},
            headers=admin_headers,
            timeout=10,
        )


def test_active_app_modal_audience_logged_requires_token(admin_headers, admin_token, created_ids):
    saved = _deactivate_all_for_surface(admin_headers, "app_modal")
    try:
        payload = {
            "title": "TEST_active_logged",
            "body_html": "<p>logged only</p>",
            "surface": "app_modal",
            "audience": "logged",
            "active": True,
        }
        r = requests.post(
            f"{BASE_URL}/api/admin/broadcast-notifications",
            json=payload,
            headers=admin_headers,
            timeout=15,
        )
        nid = r.json()["id"]
        created_ids.append(nid)

        # guest call → None (logged-only filter)
        r_guest = requests.get(
            f"{BASE_URL}/api/broadcast-notifications/active?surface=app_modal", timeout=15
        )
        assert r_guest.status_code == 200
        assert r_guest.json() is None, f"expected None for guest, got {r_guest.json()}"

        # authed call → notif returned
        r_auth = requests.get(
            f"{BASE_URL}/api/broadcast-notifications/active?surface=app_modal",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert r_auth.status_code == 200
        body = r_auth.json()
        assert body is not None and body["id"] == nid
    finally:
        _restore(admin_headers, saved)


def test_active_shop_banner_audience_guests(admin_headers, admin_token, created_ids):
    saved = _deactivate_all_for_surface(admin_headers, "shop_banner")
    try:
        payload = {
            "title": "TEST_active_guest_banner",
            "body_html": "<p>guests only</p>",
            "surface": "shop_banner",
            "audience": "guests",
            "active": True,
        }
        r = requests.post(
            f"{BASE_URL}/api/admin/broadcast-notifications",
            json=payload,
            headers=admin_headers,
            timeout=15,
        )
        nid = r.json()["id"]
        created_ids.append(nid)

        # guest -> returned
        r_guest = requests.get(
            f"{BASE_URL}/api/broadcast-notifications/active?surface=shop_banner", timeout=15
        )
        assert r_guest.status_code == 200
        body = r_guest.json()
        assert body is not None and body["id"] == nid

        # authed -> filtered out
        r_auth = requests.get(
            f"{BASE_URL}/api/broadcast-notifications/active?surface=shop_banner",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert r_auth.status_code == 200
        assert r_auth.json() is None
    finally:
        _restore(admin_headers, saved)


def test_active_time_window_future_starts_at(admin_headers, created_ids):
    saved = _deactivate_all_for_surface(admin_headers, "app_modal")
    try:
        future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        payload = {
            "title": "TEST_future_starts_at",
            "surface": "app_modal",
            "audience": "all",
            "active": True,
            "starts_at": future,
        }
        r = requests.post(
            f"{BASE_URL}/api/admin/broadcast-notifications",
            json=payload,
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        nid = r.json()["id"]
        created_ids.append(nid)

        r2 = requests.get(
            f"{BASE_URL}/api/broadcast-notifications/active?surface=app_modal", timeout=15
        )
        assert r2.status_code == 200
        # this specific notif must not be returned
        body = r2.json()
        if body is not None:
            assert body["id"] != nid
    finally:
        _restore(admin_headers, saved)


def test_active_time_window_past_ends_at(admin_headers, created_ids):
    saved = _deactivate_all_for_surface(admin_headers, "app_modal")
    try:
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        payload = {
            "title": "TEST_past_ends_at",
            "surface": "app_modal",
            "audience": "all",
            "active": True,
            "ends_at": past,
        }
        r = requests.post(
            f"{BASE_URL}/api/admin/broadcast-notifications",
            json=payload,
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        nid = r.json()["id"]
        created_ids.append(nid)

        r2 = requests.get(
            f"{BASE_URL}/api/broadcast-notifications/active?surface=app_modal", timeout=15
        )
        body = r2.json()
        if body is not None:
            assert body["id"] != nid
    finally:
        _restore(admin_headers, saved)


# ───────────── PWA assets (served by frontend) ─────────────
def test_manifest_json_pwa():
    # PWA manifest is served by frontend at /manifest.json — use REACT_APP_BACKEND_URL host
    r = requests.get(f"{BASE_URL}/manifest.json", timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("display") == "standalone"
    assert data.get("theme_color", "").lower() == "#0b1b3a"
    icon_srcs = [i.get("src", "") for i in data.get("icons", [])]
    assert any("/icon-192.png" in s for s in icon_srcs), f"missing icon-192 in {icon_srcs}"
    assert any("/icon-512.png" in s for s in icon_srcs), f"missing icon-512 in {icon_srcs}"


def test_service_worker_js():
    r = requests.get(f"{BASE_URL}/service-worker.js", timeout=15)
    assert r.status_code == 200
    assert "self" in r.text or "addEventListener" in r.text
