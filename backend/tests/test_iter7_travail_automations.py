"""Iteration 7 — Travail hub + Automatisations (custom NL + wellbeing consent).

Tests axés sur les endpoints demandés dans la review request:
- /api/travail/overview, /crm, /events, /recommendations
- /api/automations/stats, /custom, /wellbeing-consent
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"
EMAIL = "thomas@zayado.fr"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/request-link", json={"email": EMAIL}, timeout=15)
    assert r.status_code == 200, r.text
    dev_link = r.json().get("dev_link") or ""
    assert "token=" in dev_link
    tok = dev_link.split("token=")[1].split("&")[0]
    r2 = requests.post(f"{API}/auth/verify-link", json={"token": tok}, timeout=15)
    assert r2.status_code == 200, r2.text
    body = r2.json()
    return body["access_token"]


@pytest.fixture(scope="module")
def h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============================================================
# Travail — Overview
# ============================================================
class TestTravailOverview:
    def test_overview_shape(self, h):
        r = requests.get(f"{API}/travail/overview", headers=h, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("projects", "tasks", "appointments", "crm", "finance"):
            assert k in d, f"missing key {k}"
        assert "active" in d["projects"]
        assert "pending" in d["tasks"]
        assert "today" in d["appointments"]
        assert "pipeline" in d["crm"]
        for fk in ("ca", "depenses", "net", "marge"):
            assert fk in d["finance"]

    def test_overview_finance_realdata(self, h):
        # Thomas has real finance data; CA should be > 0 for current month if seeded
        r = requests.get(f"{API}/travail/overview", headers=h, timeout=15)
        d = r.json()
        # not asserting exact figure — just typed number
        assert isinstance(d["finance"]["ca"], (int, float))
        assert isinstance(d["finance"]["marge"], (int, float))


# ============================================================
# Travail — CRM CRUD
# ============================================================
class TestTravailCRM:
    lead_id = None

    def test_list_initial(self, h):
        r = requests.get(f"{API}/travail/crm", headers=h, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and "pipeline" in d and "total" in d and "won_value" in d
        for s in ("nouveau", "contacte", "proposition", "negociation", "gagne", "perdu"):
            assert s in d["pipeline"]

    def test_create_lead(self, h):
        payload = {"name": f"TEST_Lead_{uuid.uuid4().hex[:6]}", "stage": "nouveau", "value": 1200}
        r = requests.post(f"{API}/travail/crm", headers=h, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["name"] == payload["name"]
        assert d["stage"] == "nouveau"
        assert "id" in d
        TestTravailCRM.lead_id = d["id"]

        # Verify persistence
        r2 = requests.get(f"{API}/travail/crm", headers=h, timeout=15)
        ids = [it["id"] for it in r2.json()["items"]]
        assert TestTravailCRM.lead_id in ids

    def test_patch_stage(self, h):
        assert TestTravailCRM.lead_id, "requires create test to run first"
        r = requests.patch(f"{API}/travail/crm/{TestTravailCRM.lead_id}",
                           headers=h, json={"stage": "negociation"}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("stage") == "negociation"

        # Verify pipeline reflects
        d = requests.get(f"{API}/travail/crm", headers=h, timeout=15).json()
        lead = next((x for x in d["items"] if x["id"] == TestTravailCRM.lead_id), None)
        assert lead and lead["stage"] == "negociation"

    def test_delete(self, h):
        assert TestTravailCRM.lead_id
        r = requests.delete(f"{API}/travail/crm/{TestTravailCRM.lead_id}", headers=h, timeout=15)
        assert r.status_code == 200
        assert r.json().get("deleted") is True

        d = requests.get(f"{API}/travail/crm", headers=h, timeout=15).json()
        ids = [it["id"] for it in d["items"]]
        assert TestTravailCRM.lead_id not in ids


# ============================================================
# Travail — Agenda CRUD
# ============================================================
class TestTravailEvents:
    ev_id = None

    def test_list_events(self, h):
        r = requests.get(f"{API}/travail/events", headers=h, timeout=15)
        assert r.status_code == 200
        assert "items" in r.json()

    def test_list_today(self, h):
        r = requests.get(f"{API}/travail/events?day=today", headers=h, timeout=15)
        assert r.status_code == 200

    def test_create_event(self, h):
        payload = {"title": f"TEST_Event_{uuid.uuid4().hex[:6]}", "time": "10:00", "kind": "visio"}
        r = requests.post(f"{API}/travail/events", headers=h, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["title"] == payload["title"]
        assert d["kind"] == "visio"
        assert "date" in d  # should default to today
        TestTravailEvents.ev_id = d["id"]

    def test_delete_event(self, h):
        assert TestTravailEvents.ev_id
        r = requests.delete(f"{API}/travail/events/{TestTravailEvents.ev_id}", headers=h, timeout=15)
        assert r.status_code == 200
        assert r.json().get("deleted") is True


# ============================================================
# Travail — Recommendations
# ============================================================
class TestTravailRecos:
    def test_recos(self, h):
        r = requests.get(f"{API}/travail/recommendations", headers=h, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d
        # Structure: id/icon/tone/title/desc/route
        for reco in d["items"]:
            for k in ("id", "title", "desc"):
                assert k in reco


# ============================================================
# Automations
# ============================================================
class TestAutomations:
    custom_id = None

    def test_stats(self, h):
        r = requests.get(f"{API}/automations/stats", headers=h, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("active_count", "total_runs", "minutes_saved", "hours_saved", "wellbeing_adaptive"):
            assert k in d, f"missing {k}"
        assert isinstance(d["wellbeing_adaptive"], bool)

    def test_create_custom(self, h):
        desc = "TEST_Quand un client paie, envoie-lui un mail de remerciement personnalisé"
        r = requests.post(f"{API}/automations/custom", headers=h,
                          json={"description": desc}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "ok"
        auto = d["automation"]
        assert auto["custom"] is True
        assert auto["enabled"] is False
        assert auto["status"] == "à configurer"
        assert desc in auto["then"]
        TestAutomations.custom_id = auto["id"]

        # Verify it's returned in GET /automations
        r2 = requests.get(f"{API}/automations", headers=h, timeout=15)
        ids = [a["id"] for a in r2.json()["automations"]]
        assert TestAutomations.custom_id in ids

    def test_create_custom_empty_desc_rejected(self, h):
        r = requests.post(f"{API}/automations/custom", headers=h,
                          json={"description": ""}, timeout=15)
        assert r.status_code == 400

    def test_delete_custom(self, h):
        assert TestAutomations.custom_id
        r = requests.delete(f"{API}/automations/custom/{TestAutomations.custom_id}",
                            headers=h, timeout=15)
        assert r.status_code == 200
        assert r.json().get("deleted") is True

        # Verify removed
        r2 = requests.get(f"{API}/automations", headers=h, timeout=15)
        ids = [a["id"] for a in r2.json()["automations"]]
        assert TestAutomations.custom_id not in ids

    def test_wellbeing_consent_toggle(self, h):
        # enable
        r = requests.put(f"{API}/automations/wellbeing-consent", headers=h,
                        json={"enabled": True}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("wellbeing_adaptive") is True

        s = requests.get(f"{API}/automations/stats", headers=h, timeout=15).json()
        assert s["wellbeing_adaptive"] is True

        # disable
        r2 = requests.put(f"{API}/automations/wellbeing-consent", headers=h,
                        json={"enabled": False}, timeout=15)
        assert r2.status_code == 200
        assert r2.json().get("wellbeing_adaptive") is False

        s2 = requests.get(f"{API}/automations/stats", headers=h, timeout=15).json()
        assert s2["wellbeing_adaptive"] is False
