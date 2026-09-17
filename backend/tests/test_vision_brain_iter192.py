"""Backend tests for Vision Brain module (iter 192)."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # try frontend env file
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass

TEST_EMAIL = "thomas@zayado.fr"


@pytest.fixture(scope="module")
def token():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/request-link", json={"email": TEST_EMAIL}, timeout=30)
    assert r.status_code == 200, f"request-link failed: {r.status_code} {r.text}"
    body = r.json()
    dev_link = body.get("dev_link") or body.get("link") or ""
    assert dev_link, f"no dev_link in {body}"
    m = re.search(r"token=([^&\s]+)", dev_link)
    assert m, f"no token in dev_link: {dev_link}"
    tok = m.group(1)
    r2 = s.post(f"{BASE_URL}/api/auth/verify-link", json={"token": tok}, timeout=30)
    assert r2.status_code == 200, f"verify-link failed: {r2.status_code} {r2.text}"
    access = r2.json().get("access_token")
    assert access, f"no access_token in {r2.json()}"
    return access


@pytest.fixture()
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ─── /vision/brain/panel ─────────────────────────────────────────────
class TestBrainPanel:
    def test_panel_structure(self, client):
        r = client.get(f"{BASE_URL}/api/vision/brain/panel", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d.get("alignment_score"), int)
        assert "delta_week" in d
        sb = d.get("score_business", {})
        pillars = sb.get("pillars", [])
        names = {p["name"] for p in pillars}
        assert {"Vision", "Exécution", "Finance", "Impact", "Énergie", "Croissance"}.issubset(names), names
        assert len(pillars) == 6
        for k in ("opportunities", "actions", "suggested_modules", "activity", "linked_cards"):
            assert isinstance(d.get(k), list), f"{k} missing"

    def test_panel_ca_card(self, client):
        r = client.get(f"{BASE_URL}/api/vision/brain/panel", timeout=30)
        assert r.status_code == 200
        cards = r.json().get("linked_cards", [])
        ca = next((c for c in cards if c.get("key") == "ca"), None)
        assert ca is not None, "linked_card 'ca' missing"
        assert "21 600" in ca.get("value", ""), f"CA value expected to contain '21 600 €', got {ca.get('value')!r}"
        assert ca.get("badge"), "CA card should carry a badge"

    def test_panel_news_has_sources_others_do_not(self, client):
        r = client.get(f"{BASE_URL}/api/vision/brain/panel", timeout=30)
        opps = r.json()["opportunities"]
        news = [o for o in opps if o.get("kind") == "news"]
        others = [o for o in opps if o.get("kind") != "news"]
        assert news, "no news opportunity found"
        for o in news:
            assert len(o.get("sources") or []) > 0, f"news opp without sources: {o}"
        for o in others:
            assert len(o.get("sources") or []) == 0, f"non-news opp with sources: {o}"


# ─── /vision/brain/analyze ───────────────────────────────────────────
class TestBrainAnalyze:
    def test_analyze_force(self, client):
        r = client.post(f"{BASE_URL}/api/vision/brain/analyze", json={"force": True}, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        swot = d.get("swot") or {}
        for k in ("forces", "faiblesses", "opportunites", "menaces"):
            assert isinstance(swot.get(k), list), f"swot.{k} missing"
        assert isinstance(d.get("pillars"), list) and d["pillars"]
        assert isinstance(d.get("incoherences"), list) and d["incoherences"]
        assert isinstance(d.get("recommandations"), list) and d["recommandations"]
        assert isinstance(d.get("questions"), list) and d["questions"]


# ─── /vision/brain/notify-explain ────────────────────────────────────
class TestNotifyExplain:
    def test_news_urssaf_has_sources(self, client):
        r = client.post(
            f"{BASE_URL}/api/vision/brain/notify-explain",
            json={"title": "Barème URSSAF mis à jour", "kind": "news"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("is_news") is True
        assert len(d.get("sources") or []) > 0

    def test_internal_has_no_sources(self, client):
        r = client.post(
            f"{BASE_URL}/api/vision/brain/notify-explain",
            json={"title": "Nouvelle carte ajoutée", "kind": "internal"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("is_news") is False
        assert (d.get("sources") or []) == []
