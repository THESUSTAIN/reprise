"""
Iteration 195 — Validation end-to-end de l'export 'zayado-corrige-final'.
Focus: auth magic-link, cartes Vision unifiées, live-data, SSE, news digest,
gamification, analytics admin, dashboard, vision brain panel.
"""
import os
import re
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://strategy-brain-2.preview.emergentagent.com").rstrip("/")
EMAIL = "thomas@zayado.fr"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def auth(session):
    """Get auth token via passwordless magic link flow."""
    r = session.post(f"{BASE_URL}/api/auth/request-link", json={"email": EMAIL}, timeout=15)
    assert r.status_code == 200, f"request-link -> {r.status_code} {r.text[:200]}"
    body = r.json()
    dev_link = body.get("dev_link") or body.get("link") or ""
    token = None
    if dev_link:
        m = re.search(r"token=([A-Za-z0-9_\-\.]+)", dev_link)
        if m:
            token = m.group(1)
    if not token:
        token = body.get("token")
    assert token, f"No token found in response: {body}"

    r2 = session.post(f"{BASE_URL}/api/auth/verify-link", json={"token": token}, timeout=15)
    assert r2.status_code == 200, f"verify-link -> {r2.status_code} {r2.text[:200]}"
    data = r2.json()
    access_token = data.get("access_token") or data.get("token")
    assert access_token, f"No access_token in {data}"
    user = data.get("user") or {}
    user_id = user.get("id") or user.get("_id") or data.get("user_id")
    return {"token": access_token, "user_id": user_id, "user": user}


@pytest.fixture(scope="session")
def headers(auth):
    return {"Authorization": f"Bearer {auth['token']}", "Content-Type": "application/json"}


# ---------- AUTH ----------
def test_auth_me(session, headers):
    r = session.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    email = (data.get("email") or data.get("user", {}).get("email") or "").lower()
    assert EMAIL in email, f"me returned {data}"


# ---------- Vision cards unified ----------
def test_vision_cards_list(session, headers):
    r = session.get(f"{BASE_URL}/api/vision/cards", headers=headers, timeout=20)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    cards = data if isinstance(data, list) else (data.get("cards") or data.get("items") or [])
    assert isinstance(cards, list)
    print(f"[cards] count={len(cards)} sample_keys={list(cards[0].keys()) if cards else []}")


# ---------- Live data (CA du mois) ----------
def test_vision_board_live_data(session, headers):
    r = session.get(f"{BASE_URL}/api/vision/board/live-data", headers=headers, timeout=20)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    print(f"[live-data] keys={list(data.keys())}")
    # CA du mois — attendu ~21600 via finance_entries
    ca = data.get("ca_mois") or data.get("revenue_month") or data.get("ca") or None
    if isinstance(ca, dict):
        ca = ca.get("value") or ca.get("amount")
    print(f"[live-data] ca_mois={ca}")


# ---------- SSE ----------
def test_vision_events_stream(auth):
    url = f"{BASE_URL}/api/vision/events/stream?token={auth['token']}"
    got_any = False
    ctype = ""
    status = 0
    try:
        with requests.get(url, stream=True, timeout=(5, 4)) as r:
            status = r.status_code
            ctype = r.headers.get("Content-Type", "")
            assert status == 200, f"status={status}"
            assert "text/event-stream" in ctype, f"content-type={ctype}"
            start = time.time()
            for raw in r.iter_lines(decode_unicode=True):
                if raw:
                    got_any = True
                    print(f"[sse] {raw[:120]}")
                if time.time() - start > 3:
                    break
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
        # SSE is long-lived; timeout after receiving initial event(s) is OK
        print(f"[sse] closed after receiving events (expected): {type(e).__name__}")
    assert status == 200
    assert "text/event-stream" in ctype
    assert got_any, "no SSE event received before timeout"


# ---------- News digest ----------
def test_news_digest(session, headers):
    r = session.get(f"{BASE_URL}/api/news/digest", headers=headers, timeout=30)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    items = data if isinstance(data, list) else (data.get("items") or data.get("news") or [])
    assert isinstance(items, list)
    print(f"[news] count={len(items)}")


# ---------- Gamification ----------
def test_gamification_passport(session, headers):
    r = session.get(f"{BASE_URL}/api/gamification/passport", headers=headers, timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    print(f"[passport] keys={list(data.keys())}")


# ---------- Analytics admin ----------
def test_admin_analytics_funnel(session, headers):
    r = session.get(f"{BASE_URL}/api/admin/analytics/funnel", headers=headers, timeout=15)
    assert r.status_code in (200, 403), f"unexpected {r.status_code} {r.text[:200]}"
    print(f"[funnel] status={r.status_code}")


def test_admin_analytics_retention(session, headers):
    r = session.get(f"{BASE_URL}/api/admin/analytics/retention", headers=headers, timeout=15)
    assert r.status_code in (200, 403), f"unexpected {r.status_code} {r.text[:200]}"
    print(f"[retention] status={r.status_code}")


# ---------- Dashboard non-régression ----------
def test_dashboard(session, headers, auth):
    uid = auth.get("user_id") or ""
    r = session.get(f"{BASE_URL}/api/dashboard", params={"user_id": uid}, headers=headers, timeout=20)
    assert r.status_code == 200, r.text[:300]
    print(f"[dashboard] keys={list(r.json().keys())[:10]}")


# ---------- Vision brain panel + analyze ----------
def test_vision_brain_panel(session, headers):
    r = session.get(f"{BASE_URL}/api/vision/brain/panel", headers=headers, timeout=25)
    assert r.status_code == 200, r.text[:300]
    print(f"[brain/panel] keys={list(r.json().keys())}")


def test_analyze_swot(session, headers):
    payload = {"content": "Zayado est un cockpit stratégique pour PME. Nous avons un bon produit.", "type": "swot"}
    r = session.post(f"{BASE_URL}/api/vision/brain/analyze", json=payload, headers=headers, timeout=60)
    assert r.status_code == 200, r.text[:300]
    print(f"[analyze] keys={list(r.json().keys())[:10]}")
