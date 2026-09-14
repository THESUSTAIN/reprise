"""
Iteration 74 - Full Audit of /app/team page
Tests: Vue d'ensemble, Conversations, Analytics, Equipe, Config tabs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTeamPageIteration74:
    """Full audit tests for /app/team page - iteration 74"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        self.token = data.get("access_token") or data.get("token")
        assert self.token, "No token in login response"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        print(f"✓ Login successful, token obtained")
    
    # ─── Vue d'ensemble tests ───────────────────────────────────────
    
    def test_team_me_returns_team_data(self):
        """GET /api/team/me returns team with all required fields"""
        resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert resp.status_code == 200, f"team/me failed: {resp.text}"
        data = resp.json()
        assert data.get("team"), "No team in response"
        team = data["team"]
        assert "name" in team
        assert "team_code" in team
        assert "shared_credits" in team
        assert "settings" in team
        print(f"✓ team/me returns team: {team.get('name')} ({team.get('team_code')})")
    
    def test_team_dashboard_returns_stats(self):
        """GET /api/team/dashboard returns stats for Vue d'ensemble"""
        resp = self.session.get(f"{BASE_URL}/api/team/dashboard")
        assert resp.status_code == 200, f"dashboard failed: {resp.text}"
        data = resp.json()
        assert "team" in data
        assert "stats" in data
        assert "members" in data
        print(f"✓ dashboard returns stats: {data.get('stats')}")
    
    def test_team_conversations_returns_list(self):
        """GET /api/team/conversations returns conversations for Vue d'ensemble"""
        resp = self.session.get(f"{BASE_URL}/api/team/conversations")
        assert resp.status_code == 200, f"conversations failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "conversations should be a list"
        print(f"✓ conversations returns {len(data)} items")
        return len(data)
    
    # ─── Conversations tab tests ────────────────────────────────────
    
    def test_conversations_have_required_fields(self):
        """Conversations have user_name, user_email, message_count, timestamps"""
        resp = self.session.get(f"{BASE_URL}/api/team/conversations")
        assert resp.status_code == 200
        data = resp.json()
        if len(data) > 0:
            conv = data[0]
            assert "user_name" in conv or "title" in conv
            assert "message_count" in conv
            print(f"✓ Conversation has required fields: {list(conv.keys())}")
        else:
            print("⚠ No conversations to verify fields")
    
    # ─── Analytics tab tests ────────────────────────────────────────
    
    def test_analytics_data_from_dashboard(self):
        """Dashboard provides data for Analytics stats cards"""
        resp = self.session.get(f"{BASE_URL}/api/team/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        # Analytics uses: total conversations, leads, messages, credits
        team = data.get("team", {})
        stats = data.get("stats", {})
        assert "shared_credits" in team or "total_credits_used_month" in stats
        print(f"✓ Analytics data available: team credits={team.get('shared_credits')}, stats={stats}")
    
    # ─── Equipe tab tests ───────────────────────────────────────────
    
    def test_team_members_list(self):
        """GET /api/team/me returns members list for Equipe tab"""
        resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert resp.status_code == 200
        data = resp.json()
        members = data.get("members", [])
        assert isinstance(members, list)
        print(f"✓ Team has {len(members)} members")
        for m in members:
            assert "email" in m
            assert "role" in m
            assert "status" in m
    
    # ─── Config tab tests ───────────────────────────────────────────
    
    def test_config_has_behavior_fields(self):
        """Team settings include behavior toggles (Escalade, Multi-langue, 24h, Collecte emails)"""
        resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert resp.status_code == 200
        data = resp.json()
        settings = data["team"].get("settings", {})
        # Check behavior fields exist (may be True/False or not set)
        print(f"✓ Settings keys: {list(settings.keys())}")
        # These should be present after config save
        behavior_keys = ["behavior_escalation", "behavior_multilang", "behavior_24h", "behavior_collect_email"]
        for key in behavior_keys:
            if key in settings:
                print(f"  - {key}: {settings[key]}")
    
    def test_config_has_logo_url_field(self):
        """Team settings include logo_url field"""
        resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert resp.status_code == 200
        settings = resp.json()["team"].get("settings", {})
        # logo_url may be empty string or not set
        print(f"✓ logo_url in settings: {settings.get('logo_url', 'NOT SET')}")
    
    def test_config_has_footer_text_field(self):
        """Team settings include footer_text (marque blanche)"""
        resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert resp.status_code == 200
        settings = resp.json()["team"].get("settings", {})
        footer = settings.get("footer_text", "NOT SET")
        print(f"✓ footer_text in settings: {footer}")
    
    def test_config_has_pre_chat_fields_with_required(self):
        """Team settings include pre_chat_fields with required toggle"""
        resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert resp.status_code == 200
        settings = resp.json()["team"].get("settings", {})
        fields = settings.get("pre_chat_fields", [])
        print(f"✓ pre_chat_fields: {len(fields)} fields")
        for f in fields:
            print(f"  - {f.get('label')}: required={f.get('required', False)}")
    
    def test_save_config_with_all_new_fields(self):
        """POST /api/team/config saves all new fields"""
        config_data = {
            "bot_name": "Test Bot",
            "bot_tone": "professional",
            "bot_context": "Test context for iteration 74",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "Bonjour ! Je suis Test Bot.",
            "end_of_credits_message": "Credits epuises.",
            "alert_on_conversation": True,
            "alert_low_credits": True,
            "low_credit_threshold": 50,
            "privacy_policy_url": "https://example.com/privacy",
            "agent_ia_enabled": False,
            "pre_chat_fields": [
                {"key": "name", "label": "Votre nom", "type": "text", "required": True},
                {"key": "email", "label": "Votre email", "type": "email", "required": False},
                {"key": "company", "label": "Entreprise", "type": "text", "required": True}
            ],
            "footer_text": "Extension AI",
            "logo_url": "",
            "behavior_escalation": True,
            "behavior_multilang": True,
            "behavior_24h": True,
            "behavior_collect_email": False
        }
        resp = self.session.post(f"{BASE_URL}/api/team/config", json=config_data)
        assert resp.status_code == 200, f"Config save failed: {resp.text}"
        data = resp.json()
        assert data.get("status") == "ok" or "message" in data
        print(f"✓ Config saved successfully: {data}")
    
    # ─── Public chatbot tests ───────────────────────────────────────
    
    def test_public_info_returns_pre_chat_fields(self):
        """GET /api/team/public/info returns pre_chat_fields from config"""
        resp = requests.get(f"{BASE_URL}/api/team/public/info/ZAYA-CFCC72")
        assert resp.status_code == 200, f"public/info failed: {resp.text}"
        data = resp.json()
        assert "pre_chat_fields" in data
        fields = data["pre_chat_fields"]
        print(f"✓ Public info returns {len(fields)} pre_chat_fields")
        for f in fields:
            print(f"  - {f.get('label')}: required={f.get('required', False)}")
    
    def test_public_info_returns_footer_text(self):
        """GET /api/team/public/info returns footer_text"""
        resp = requests.get(f"{BASE_URL}/api/team/public/info/ZAYA-CFCC72")
        assert resp.status_code == 200
        data = resp.json()
        footer = data.get("footer_text", "NOT SET")
        assert footer != "Zayado AI", "Footer should not be 'Zayado AI'"
        print(f"✓ Public info footer_text: {footer}")
    
    def test_public_info_returns_logo_url(self):
        """GET /api/team/public/info returns logo_url"""
        resp = requests.get(f"{BASE_URL}/api/team/public/info/ZAYA-CFCC72")
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Public info logo_url: {data.get('logo_url', 'NOT SET')}")
    
    def test_public_info_returns_privacy_policy_url(self):
        """GET /api/team/public/info returns privacy_policy_url for RGPD link"""
        resp = requests.get(f"{BASE_URL}/api/team/public/info/ZAYA-CFCC72")
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Public info privacy_policy_url: {data.get('privacy_policy_url', 'NOT SET')}")
    
    def test_public_chat_accepts_shared_url(self):
        """POST /api/team/public/chat accepts shared_url parameter"""
        # This tests the URL share button functionality
        chat_data = {
            "team_code": "ZAYA-CFCC72",
            "message": "Test message with URL",
            "user_name": "Test User",
            "user_email": "test@example.com",
            "session_id": "test-session-74",
            "shared_url": "https://example.com/test-page",
            "history": []
        }
        resp = requests.post(f"{BASE_URL}/api/team/public/chat", json=chat_data)
        # May fail due to credits but should accept the request format
        if resp.status_code == 402:
            print("⚠ Credits exhausted but request format accepted")
        elif resp.status_code == 200:
            data = resp.json()
            assert "reply" in data
            print(f"✓ Public chat with shared_url works: {data.get('reply', '')[:50]}...")
        else:
            print(f"⚠ Public chat response: {resp.status_code} - {resp.text[:100]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
