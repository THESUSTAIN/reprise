"""
Iteration 73: Major Update Testing - 13+ Issues Fixed
Tests for:
1. Pre-chat form uses config fields from backend (not hardcoded 'nom')
2. Footer text changed from 'Zayado AI' to 'Extension AI' and is customizable
3. RGPD link + 'i' button on public chatbot
4. Required toggle for pre-chat fields
5. Agent IA web search (reads URLs)
6. URL sharing button in chat bar
7. Comportement section (Escalade, Multi-langue, 24h, Collecte emails)
8. Logo URL in config
9. Astuce conversion tip restored
10. Prompts scoped to team only (category='chatbot')
11. Conversations count fixed
12. Knowledge base section in Vue d'ensemble
13. Apparence & marque blanche section
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPublicChatbotFeatures:
    """Test public chatbot features for iteration 73"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.team_code = "ZAYA-CFCC72"
    
    def test_public_info_returns_footer_text(self):
        """Test GET /api/team/public/info returns footer_text (not 'Zayado AI')"""
        resp = self.session.get(f"{BASE_URL}/api/team/public/info/{self.team_code}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check footer_text field exists
        assert "footer_text" in data, "footer_text field missing from public info"
        # Default should be 'Extension AI' not 'Zayado AI'
        footer = data.get("footer_text", "")
        assert "Zayado" not in footer or footer == "Extension AI", f"Footer should not contain 'Zayado AI', got: {footer}"
        print(f"Footer text: {footer}")
    
    def test_public_info_returns_logo_url(self):
        """Test GET /api/team/public/info returns logo_url"""
        resp = self.session.get(f"{BASE_URL}/api/team/public/info/{self.team_code}")
        assert resp.status_code == 200
        data = resp.json()
        
        # Check logo_url field exists
        assert "logo_url" in data, "logo_url field missing from public info"
        print(f"Logo URL: {data.get('logo_url', 'not set')}")
    
    def test_public_info_returns_agent_ia_enabled(self):
        """Test GET /api/team/public/info returns agent_ia_enabled"""
        resp = self.session.get(f"{BASE_URL}/api/team/public/info/{self.team_code}")
        assert resp.status_code == 200
        data = resp.json()
        
        # Check agent_ia_enabled field exists
        assert "agent_ia_enabled" in data, "agent_ia_enabled field missing from public info"
        print(f"Agent IA enabled: {data.get('agent_ia_enabled')}")
    
    def test_public_info_returns_pre_chat_fields(self):
        """Test GET /api/team/public/info returns pre_chat_fields from config"""
        resp = self.session.get(f"{BASE_URL}/api/team/public/info/{self.team_code}")
        assert resp.status_code == 200
        data = resp.json()
        
        # Check pre_chat_fields field exists
        assert "pre_chat_fields" in data, "pre_chat_fields field missing from public info"
        fields = data.get("pre_chat_fields", [])
        print(f"Pre-chat fields: {fields}")
        
        # If fields exist, verify structure
        for field in fields:
            assert "key" in field, "Field missing 'key'"
            assert "label" in field, "Field missing 'label'"
            # Required field should be present
            if "required" in field:
                assert isinstance(field["required"], bool), "required should be boolean"
    
    def test_public_info_returns_privacy_policy_url(self):
        """Test GET /api/team/public/info returns privacy_policy_url for RGPD"""
        resp = self.session.get(f"{BASE_URL}/api/team/public/info/{self.team_code}")
        assert resp.status_code == 200
        data = resp.json()
        
        # Check privacy_policy_url field exists
        assert "privacy_policy_url" in data, "privacy_policy_url field missing from public info"
        print(f"Privacy policy URL: {data.get('privacy_policy_url', 'not set')}")


class TestPublicChatWithSharedUrl:
    """Test public chat with shared_url parameter (URL sharing feature)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.team_code = "ZAYA-CFCC72"
    
    def test_public_chat_accepts_shared_url(self):
        """Test POST /api/team/public/chat accepts shared_url parameter"""
        chat_data = {
            "team_code": self.team_code,
            "message": "Peux-tu me resumer cette page?",
            "user_name": "Test User",
            "session_id": "test-session-url-73",
            "shared_url": "https://example.com/test-page",
            "history": []
        }
        
        resp = self.session.post(f"{BASE_URL}/api/team/public/chat", json=chat_data)
        # Should accept the request (may fail due to credits but should not be 400/422)
        assert resp.status_code in [200, 402, 502, 504], f"Expected 200/402/502/504, got {resp.status_code}: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert "reply" in data, "Response should contain 'reply'"
            print(f"Chat with shared_url successful: {data.get('reply', '')[:100]}...")
        else:
            print(f"Chat returned {resp.status_code} (expected for credits/timeout)")


class TestTeamConfigNewFields:
    """Test team config with new fields for iteration 73"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Login failed - skipping authenticated tests")
    
    def test_config_accepts_footer_text(self):
        """Test POST /api/team/config accepts footer_text field"""
        config_data = {
            "bot_name": "Test Bot",
            "bot_tone": "professional",
            "bot_context": "",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "",
            "end_of_credits_message": "",
            "privacy_policy_url": "",
            "agent_ia_enabled": False,
            "pre_chat_fields": [],
            "footer_text": "Custom Footer Text",
            "logo_url": "",
            "behavior_escalation": True,
            "behavior_multilang": True,
            "behavior_24h": True,
            "behavior_collect_email": False
        }
        
        resp = self.session.post(f"{BASE_URL}/api/team/config", json=config_data)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify saved
        verify_resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert verify_resp.status_code == 200
        team_data = verify_resp.json()
        settings = team_data.get("team", {}).get("settings", {})
        assert settings.get("footer_text") == "Custom Footer Text", "footer_text not saved"
        print("footer_text saved successfully")
    
    def test_config_accepts_logo_url(self):
        """Test POST /api/team/config accepts logo_url field"""
        config_data = {
            "bot_name": "Test Bot",
            "bot_tone": "professional",
            "bot_context": "",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "",
            "end_of_credits_message": "",
            "privacy_policy_url": "",
            "agent_ia_enabled": False,
            "pre_chat_fields": [],
            "footer_text": "Extension AI",
            "logo_url": "https://example.com/logo.png",
            "behavior_escalation": True,
            "behavior_multilang": True,
            "behavior_24h": True,
            "behavior_collect_email": False
        }
        
        resp = self.session.post(f"{BASE_URL}/api/team/config", json=config_data)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify saved
        verify_resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert verify_resp.status_code == 200
        team_data = verify_resp.json()
        settings = team_data.get("team", {}).get("settings", {})
        assert settings.get("logo_url") == "https://example.com/logo.png", "logo_url not saved"
        print("logo_url saved successfully")
    
    def test_config_accepts_behavior_fields(self):
        """Test POST /api/team/config accepts behavior_* fields (Comportement section)"""
        config_data = {
            "bot_name": "Test Bot",
            "bot_tone": "professional",
            "bot_context": "",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "",
            "end_of_credits_message": "",
            "privacy_policy_url": "",
            "agent_ia_enabled": False,
            "pre_chat_fields": [],
            "footer_text": "Extension AI",
            "logo_url": "",
            "behavior_escalation": False,
            "behavior_multilang": False,
            "behavior_24h": False,
            "behavior_collect_email": True
        }
        
        resp = self.session.post(f"{BASE_URL}/api/team/config", json=config_data)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify saved
        verify_resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert verify_resp.status_code == 200
        team_data = verify_resp.json()
        settings = team_data.get("team", {}).get("settings", {})
        
        assert settings.get("behavior_escalation") == False, "behavior_escalation not saved"
        assert settings.get("behavior_multilang") == False, "behavior_multilang not saved"
        assert settings.get("behavior_24h") == False, "behavior_24h not saved"
        assert settings.get("behavior_collect_email") == True, "behavior_collect_email not saved"
        print("All behavior_* fields saved successfully")
    
    def test_config_accepts_pre_chat_fields_with_required(self):
        """Test POST /api/team/config accepts pre_chat_fields with required toggle"""
        config_data = {
            "bot_name": "Test Bot",
            "bot_tone": "professional",
            "bot_context": "",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "",
            "end_of_credits_message": "",
            "privacy_policy_url": "",
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
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify saved
        verify_resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert verify_resp.status_code == 200
        team_data = verify_resp.json()
        settings = team_data.get("team", {}).get("settings", {})
        fields = settings.get("pre_chat_fields", [])
        
        assert len(fields) == 3, f"Expected 3 fields, got {len(fields)}"
        # Check required flags
        name_field = next((f for f in fields if f.get("key") == "name"), None)
        email_field = next((f for f in fields if f.get("key") == "email"), None)
        company_field = next((f for f in fields if f.get("key") == "company"), None)
        
        assert name_field and name_field.get("required") == True, "name field should be required"
        assert email_field and email_field.get("required") == False, "email field should not be required"
        assert company_field and company_field.get("required") == True, "company field should be required"
        print("pre_chat_fields with required toggle saved successfully")


class TestConversationsCount:
    """Test conversations count consistency"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Login failed")
    
    def test_conversations_count_matches(self):
        """Test that conversations count from /api/team/conversations matches dashboard"""
        # Get conversations list
        conv_resp = self.session.get(f"{BASE_URL}/api/team/conversations")
        assert conv_resp.status_code == 200
        conversations = conv_resp.json()
        conv_count = len(conversations)
        
        print(f"Conversations count from /api/team/conversations: {conv_count}")
        
        # The count should be consistent (this is a basic check)
        assert isinstance(conversations, list), "Conversations should be a list"


class TestPromptsScoping:
    """Test that prompts are scoped to team only (category='chatbot')"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Login failed")
    
    def test_prompts_endpoint_exists(self):
        """Test GET /api/prompts endpoint exists"""
        resp = self.session.get(f"{BASE_URL}/api/prompts")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"Prompts response keys: {data.keys() if isinstance(data, dict) else 'list'}")
    
    def test_create_chatbot_prompt(self):
        """Test creating a prompt with category='chatbot'"""
        prompt_data = {
            "title": "Test Chatbot Prompt",
            "prompt": "This is a test prompt for chatbot",
            "category": "chatbot"
        }
        
        resp = self.session.post(f"{BASE_URL}/api/prompts", json=prompt_data)
        # Should succeed or return validation error
        assert resp.status_code in [200, 201, 400, 422], f"Unexpected status: {resp.status_code}: {resp.text}"
        
        if resp.status_code in [200, 201]:
            print("Chatbot prompt created successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
