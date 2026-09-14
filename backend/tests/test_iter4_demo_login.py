"""Iter 4 — Thomas demo-login + magic-link tests."""
import os
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://smart-board-engine.preview.emergentagent.com").rstrip("/")


def test_demo_login_thomas_returns_token():
    r = requests.post(f"{BASE}/api/auth/demo-login", json={"email": "thomas@zayado.fr"}, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data and len(data["access_token"]) > 20
    assert data["user"]["email"] == "thomas@zayado.fr"
    assert data["user"]["name"] == "Thomas"


def test_demo_login_token_works_on_me():
    r = requests.post(f"{BASE}/api/auth/demo-login", json={"email": "thomas@zayado.fr"}, timeout=15)
    token = r.json()["access_token"]
    me = requests.get(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert me.status_code == 200, me.text
    assert me.json()["email"] == "thomas@zayado.fr"


def test_demo_login_membre_thesustain():
    r = requests.post(f"{BASE}/api/auth/demo-login", json={"email": "membre@thesustain.net"}, timeout=15)
    # Whitelisted but user might not exist; accept 200 or 404 (never 403)
    assert r.status_code in (200, 404), r.text


def test_demo_login_rejects_non_whitelisted():
    r = requests.post(f"{BASE}/api/auth/demo-login", json={"email": "hacker@evil.com"}, timeout=15)
    assert r.status_code == 403


def test_demo_login_case_insensitive():
    r = requests.post(f"{BASE}/api/auth/demo-login", json={"email": "THOMAS@ZAYADO.FR"}, timeout=15)
    assert r.status_code == 200


def test_magic_link_thomas_returns_dev_link():
    r = requests.post(f"{BASE}/api/auth/request-link", json={"email": "thomas@zayado.fr"}, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("delivered_via_email") is True
    assert "dev_link" in data and "token=" in data["dev_link"]


def test_magic_link_verify_then_me():
    r = requests.post(f"{BASE}/api/auth/request-link", json={"email": "thomas@zayado.fr"}, timeout=15)
    dev_link = r.json()["dev_link"]
    token = dev_link.split("token=")[1]
    v = requests.post(f"{BASE}/api/auth/verify-link", json={"token": token}, timeout=15)
    assert v.status_code == 200, v.text
    session_token = v.json()["access_token"]
    me = requests.get(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {session_token}"}, timeout=15)
    assert me.status_code == 200
    assert me.json()["email"] == "thomas@zayado.fr"


def test_demo_login_unknown_email_rejected():
    r = requests.post(f"{BASE}/api/auth/demo-login", json={"email": ""}, timeout=15)
    assert r.status_code == 403
