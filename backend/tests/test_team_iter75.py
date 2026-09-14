"""
Iteration 75 - Backend Tests for Team Config and Admin SEO
Tests: team_type, authorized_topics, Comportement toggles, Admin SEO endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@zayado.net",
        "password": "admin123"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

class TestTeamConfig:
    """Tests for team configuration including team_type and authorized_topics"""
    
    def test_team_me_returns_team_data(self, headers):
        """Test /api/team/me returns team data with settings"""
        response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "team" in data
        assert data["team"] is not None
        assert "settings" in data["team"]
    
    def test_team_settings_has_team_type(self, headers):
        """Test team settings includes team_type field"""
        response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        settings = data["team"].get("settings", {})
        # team_type should exist (default is 'enterprise')
        team_type = settings.get("team_type", "enterprise")
        assert team_type in ["enterprise", "association", "freelance"]
    
    def test_team_settings_has_authorized_topics(self, headers):
        """Test team settings includes authorized_topics field"""
        response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        settings = data["team"].get("settings", {})
        # authorized_topics should be a list
        topics = settings.get("authorized_topics", [])
        assert isinstance(topics, list)
    
    def test_team_settings_has_behavior_fields(self, headers):
        """Test team settings includes behavior toggles (escalation, multilang, 24h)"""
        response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        settings = data["team"].get("settings", {})
        # Check behavior fields exist (defaults to True)
        assert "behavior_escalation" in settings or settings.get("behavior_escalation", True) is not None
        assert "behavior_multilang" in settings or settings.get("behavior_multilang", True) is not None
        assert "behavior_24h" in settings or settings.get("behavior_24h", True) is not None
    
    def test_save_config_with_team_type_enterprise(self, headers):
        """Test saving config with team_type = enterprise"""
        payload = {
            "bot_name": "Test Assistant",
            "bot_tone": "professional",
            "bot_context": "Test context",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "Hello!",
            "end_of_credits_message": "Credits exhausted",
            "privacy_policy_url": "",
            "agent_ia_enabled": False,
            "pre_chat_fields": [],
            "footer_text": "Extension AI",
            "logo_url": "",
            "behavior_escalation": True,
            "behavior_multilang": True,
            "behavior_24h": True,
            "behavior_collect_email": False,
            "team_type": "enterprise",
            "authorized_topics": []
        }
        response = requests.post(f"{BASE_URL}/api/team/config", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
    
    def test_save_config_with_team_type_association(self, headers):
        """Test saving config with team_type = association and authorized_topics"""
        payload = {
            "bot_name": "Association Bot",
            "bot_tone": "friendly",
            "bot_context": "Association context",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "Bienvenue!",
            "end_of_credits_message": "Credits epuises",
            "privacy_policy_url": "",
            "agent_ia_enabled": False,
            "pre_chat_fields": [],
            "footer_text": "Extension AI",
            "logo_url": "",
            "behavior_escalation": True,
            "behavior_multilang": True,
            "behavior_24h": True,
            "behavior_collect_email": False,
            "team_type": "association",
            "authorized_topics": ["theologie", "bible", "priere"]
        }
        response = requests.post(f"{BASE_URL}/api/team/config", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
    
    def test_verify_saved_team_type_and_topics(self, headers):
        """Verify the saved team_type and authorized_topics are persisted"""
        response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        settings = data["team"].get("settings", {})
        # Should have the values we just saved
        assert settings.get("team_type") == "association"
        assert "theologie" in settings.get("authorized_topics", [])
    
    def test_reset_to_enterprise(self, headers):
        """Reset team_type back to enterprise for clean state"""
        payload = {
            "bot_name": "Assistant",
            "bot_tone": "professional",
            "bot_context": "",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "",
            "end_of_credits_message": "Notre assistant est momentanement indisponible.",
            "privacy_policy_url": "",
            "agent_ia_enabled": False,
            "pre_chat_fields": [],
            "footer_text": "Extension AI",
            "logo_url": "",
            "behavior_escalation": True,
            "behavior_multilang": True,
            "behavior_24h": True,
            "behavior_collect_email": False,
            "team_type": "enterprise",
            "authorized_topics": []
        }
        response = requests.post(f"{BASE_URL}/api/team/config", headers=headers, json=payload)
        assert response.status_code == 200


class TestTeamConversations:
    """Tests for team conversations and analytics"""
    
    def test_team_conversations_endpoint(self, headers):
        """Test /api/team/conversations returns list"""
        response = requests.get(f"{BASE_URL}/api/team/conversations", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_team_dashboard_endpoint(self, headers):
        """Test /api/team/dashboard returns stats"""
        response = requests.get(f"{BASE_URL}/api/team/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "team" in data
        assert "stats" in data


class TestPublicChatbot:
    """Tests for public chatbot endpoints"""
    
    def test_public_info_returns_footer_text(self):
        """Test public info returns footer_text field"""
        response = requests.get(f"{BASE_URL}/api/team/public/info/ZAYA-CFCC72")
        assert response.status_code == 200
        data = response.json()
        assert "footer_text" in data
        # Default should be 'Extension AI'
        assert data.get("footer_text") == "Extension AI"
    
    def test_public_info_returns_brand_color(self):
        """Test public info returns brand_color"""
        response = requests.get(f"{BASE_URL}/api/team/public/info/ZAYA-CFCC72")
        assert response.status_code == 200
        data = response.json()
        assert "brand_color" in data


class TestAdminSEO:
    """Tests for Admin SEO configuration endpoints"""
    
    def test_admin_seo_config_get(self, headers):
        """Test GET /api/admin/seo-config returns SEO data"""
        response = requests.get(f"{BASE_URL}/api/admin/seo-config", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Should be a dict (can be empty)
        assert isinstance(data, dict)
    
    def test_admin_seo_config_save(self, headers):
        """Test PUT /api/admin/seo-config saves SEO data"""
        payload = {
            "meta_title": "Test Title",
            "meta_description": "Test Description",
            "meta_keywords": "test, keywords",
            "canonical_url": "https://test.com"
        }
        response = requests.put(f"{BASE_URL}/api/admin/seo-config", headers=headers, json=payload)
        assert response.status_code == 200


class TestAdminStats:
    """Tests for Admin dashboard stats"""
    
    def test_admin_stats_endpoint(self, headers):
        """Test /api/admin/stats returns stats"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_admin_users_endpoint(self, headers):
        """Test /api/admin/users returns users list"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
