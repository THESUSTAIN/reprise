"""Backend tests iter 193 — Extension (page-context, captures) + Miroir dynamique (connections)."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
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
    dev_link = r.json().get("dev_link") or r.json().get("link") or ""
    m = re.search(r"token=([^&\s]+)", dev_link)
    assert m, f"no token in dev_link: {dev_link}"
    r2 = s.post(f"{BASE_URL}/api/auth/verify-link", json={"token": m.group(1)}, timeout=30)
    assert r2.status_code == 200, r2.text
    return r2.json()["access_token"]


@pytest.fixture()
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ─── /vision/brain/connections ───────────────────────────────────
class TestConnectionsMirror:
    def test_connections_structure_and_thomas_state(self, client):
        r = client.get(f"{BASE_URL}/api/vision/brain/connections", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "ia_warning" in d  # can be None but key must exist
        chain = d.get("chain") or []
        assert isinstance(chain, list) and len(chain) == 5, f"expected 5 nodes, got {len(chain)}"
        by_key = {n["key"]: n for n in chain}
        assert set(by_key.keys()) == {"vision", "stripe", "crm", "mail", "calendar"}, by_key.keys()

        # Vision : always connected
        assert by_key["vision"]["connected"] is True

        # Stripe : Thomas has finance data → connected + value contains "21 600 €"
        stripe = by_key["stripe"]
        assert stripe["connected"] is True, f"stripe not connected: {stripe}"
        assert "21 600" in stripe["value"], f"stripe value missing 21 600: {stripe['value']}"

        # CRM : Thomas has 4 prospects
        crm = by_key["crm"]
        assert crm["connected"] is True, crm
        assert "4" in crm["value"], f"crm value missing 4: {crm['value']}"

        # Mail : not connected → message about Gmail/Outlook
        mail = by_key["mail"]
        assert mail["connected"] is False, mail
        assert "Gmail" in mail["value"] or "Outlook" in mail["value"], mail["value"]

        # Calendar : not connected
        cal = by_key["calendar"]
        assert cal["connected"] is False, cal


# ─── /vision/brain/page-context ──────────────────────────────────
class TestPageContext:
    def test_page_context_with_email_detects_contact(self, client):
        payload = {
            "title": "Contact commercial ABC",
            "url": "https://example.com/contact",
            "selection": "Bonjour, contactez Jean Dupont à jean.dupont@abc.com pour un devis.",
        }
        r = client.post(f"{BASE_URL}/api/vision/brain/page-context", json=payload, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        # detected_contact.email must be set
        assert d.get("detected_contact"), f"no detected_contact: {d}"
        assert d["detected_contact"].get("email") == "jean.dupont@abc.com", d["detected_contact"]
        # summary non vide (fallback accepté)
        assert isinstance(d.get("summary"), str) and len(d["summary"]) > 0
        # actions: first must be "Ajouter au CRM"
        actions = d.get("actions") or []
        assert len(actions) >= 2, actions
        assert actions[0]["label"] == "Ajouter au CRM", actions[0]
        # Followed by task/opportunity/note
        second_labels = [a["label"] for a in actions[1:]]
        assert any(x in second_labels[0] for x in ("tâche", "opportunité", "note", "Créer")), second_labels

    def test_page_context_without_email(self, client):
        payload = {"title": "Article business", "url": "https://x.com", "selection": "Un texte sans email"}
        r = client.post(f"{BASE_URL}/api/vision/brain/page-context", json=payload, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("detected_contact") is None
        actions = d.get("actions") or []
        # 3 actions par défaut, pas de "Ajouter au CRM"
        assert not any(a["label"] == "Ajouter au CRM" for a in actions)


# ─── /features/captures (extension) ──────────────────────────────
class TestCapturesExtension:
    def test_create_capture_from_extension(self, client):
        payload = {
            "content": "TEST_iter193 opportunité captée depuis l'extension",
            "category": "opportunite",
            "source": "extension",
        }
        r = client.post(f"{BASE_URL}/api/features/captures", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("id"), d
        assert d.get("category") == "opportunite", d
        assert d.get("source") == "extension", d
        # persistance : GET liste
        r2 = client.get(f"{BASE_URL}/api/features/captures", timeout=30)
        assert r2.status_code == 200
        items = r2.json()
        assert any(x.get("id") == d["id"] for x in items), "capture not persisted"
        # cleanup
        client.delete(f"{BASE_URL}/api/features/captures/{d['id']}", timeout=15)


# ─── REGRESSION panel (iter 192) ─────────────────────────────────
class TestRegressionPanel:
    def test_panel_still_ok(self, client):
        r = client.get(f"{BASE_URL}/api/vision/brain/panel", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("alignment_score"), int)
        assert len(d.get("score_business", {}).get("pillars", [])) == 6
        # Cartes reliées contiennent bien la carte CA avec 21 600 €
        ca = next((c for c in d.get("linked_cards", []) if c["key"] == "ca"), None)
        assert ca is not None
        assert "21 600" in ca["value"], ca["value"]
