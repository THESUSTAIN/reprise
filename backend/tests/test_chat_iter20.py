"""Iter20 — Tests collab_chat (Claude Sonnet 4.5) + regression VAGUE1/branding/swot/churn.

Endpoints under test:
- POST /api/collaborateur/chat (auth required, multi-turn, ui_language, empty fallback)
- Regression suite : branding / admin legacy / swot preview / churn preview
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://myextension-ai.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "Test1234!"
TIMEOUT_CHAT = 90  # Claude Sonnet 4.5 may take 20-40s


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ============================================================
# Chat — happy path + i18n
# ============================================================
class TestCollabChat:
    def test_chat_no_auth_returns_401_or_403(self):
        r = requests.post(f"{BASE_URL}/api/collaborateur/chat",
                          json={"messages": [{"role": "user", "content": "hi"}]},
                          timeout=20)
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_chat_empty_messages_returns_fallback_greeting(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/collaborateur/chat",
                          headers=auth_headers,
                          json={"messages": [], "ui_language": "fr"},
                          timeout=20)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert "reply" in data
        assert isinstance(data["reply"], str) and len(data["reply"]) > 0
        # Doit être le fallback statique
        assert "Bonjour" in data["reply"] or "aider" in data["reply"].lower()

    def test_chat_fr_basic_question(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/collaborateur/chat",
                          headers=auth_headers,
                          json={
                              "messages": [{"role": "user", "content": "En une phrase, dis-moi bonjour et présente-toi brièvement."}],
                              "context_page": "Dashboard",
                              "ui_language": "fr",
                          }, timeout=TIMEOUT_CHAT)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert "reply" in data
        reply = data["reply"]
        assert isinstance(reply, str) and len(reply) > 5
        # Check français : présence de mots français très courants
        low = reply.lower()
        french_markers = ["je", "vous", "tu", "bonjour", "salut", "votre", "ton", "suis", "aider", "ici"]
        assert any(m in low for m in french_markers), f"Reply doesn't look French: {reply[:200]}"

    def test_chat_multi_turn(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/collaborateur/chat",
                          headers=auth_headers,
                          json={
                              "messages": [
                                  {"role": "user", "content": "Mon prénom est Marc."},
                                  {"role": "assistant", "content": "Bonjour Marc, comment puis-je t'aider ?"},
                                  {"role": "user", "content": "Quel est mon prénom ?"},
                              ],
                              "ui_language": "fr",
                          }, timeout=TIMEOUT_CHAT)
        assert r.status_code == 200, r.text[:300]
        reply = r.json().get("reply", "")
        assert isinstance(reply, str) and len(reply) > 0
        # Claude doit reconnaître "Marc" dans le contexte multi-turn
        assert "marc" in reply.lower(), f"Multi-turn ctx lost: {reply[:200]}"

    def test_chat_english(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/collaborateur/chat",
                          headers=auth_headers,
                          json={
                              "messages": [{"role": "user", "content": "In one sentence, say hello and introduce yourself."}],
                              "ui_language": "en",
                          }, timeout=TIMEOUT_CHAT)
        assert r.status_code == 200, r.text[:300]
        reply = r.json().get("reply", "")
        assert len(reply) > 5
        low = reply.lower()
        english_markers = ["i", "you", "hello", "hi", "am", "the", "help"]
        # Au moins 2 marqueurs anglais pour réduire les faux positifs
        hits = sum(1 for m in english_markers if f" {m} " in f" {low} " or low.startswith(m + " "))
        assert hits >= 2, f"Reply doesn't look English: {reply[:200]}"

    def test_chat_spanish(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/collaborateur/chat",
                          headers=auth_headers,
                          json={
                              "messages": [{"role": "user", "content": "En una frase, salúdame y preséntate."}],
                              "ui_language": "es",
                          }, timeout=TIMEOUT_CHAT)
        assert r.status_code == 200, r.text[:300]
        reply = r.json().get("reply", "")
        assert len(reply) > 5
        low = reply.lower()
        spanish_markers = ["soy", "hola", "tu", "puedo", "ayudar", "estoy", "buenos", "días"]
        assert any(m in low for m in spanish_markers), f"Reply doesn't look Spanish: {reply[:200]}"


# ============================================================
# Regression — VAGUE 1 + branding + swot + churn
# ============================================================
class TestRegression:
    def test_branding(self):
        r = requests.get(f"{BASE_URL}/api/branding", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "app_name" in data or "logo_url" in data or "name" in data or "company_name" in data

    def test_vision_get(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/vision", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_tasks_list(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/tasks", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        assert "items" in r.json()

    def test_streak(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/streak", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        assert "streak" in r.json()

    def test_energy_today(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/energy/today", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_revenue_monthly(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/revenue/monthly", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_admin_legacy_users(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/users", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_admin_legacy_stats(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/legacy/stats", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_prefs_swot(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/prefs/swot", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_admin_inactivity_preview(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/inactivity/preview", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        # Should still contain tier_14/tier_60/tier_335 keys
        assert "tier_14" in data and "tier_60" in data and "tier_335" in data
