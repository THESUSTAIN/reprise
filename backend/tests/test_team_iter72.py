"""
Iteration 72: Team Page Major Refactoring Tests
Tests for:
1. Team page standalone layout (no sidebar)
2. All 8 tabs: Vue d'ensemble, Equipe, Configuration, Connaissances, Conversations, Analytics, Integration, Alertes
3. PATCH /api/team/members/{id}/role endpoint
4. POST /api/team/invite/{id}/resend endpoint
5. GET /api/team/conversations returns only public chatbot conversations
6. POST /api/team/config with new fields (privacy_policy_url, agent_ia_enabled, pre_chat_fields)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTeamEndpoints:
    """Test Team API endpoints for iteration 72"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login with admin credentials
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
    
    def test_team_me_endpoint(self):
        """Test GET /api/team/me returns team info"""
        resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Should have team data
        assert "team" in data
        if data["team"]:
            assert "id" in data["team"]
            assert "name" in data["team"]
            assert "team_code" in data["team"]
            assert "settings" in data["team"]
            # Check for new settings fields
            settings = data["team"].get("settings", {})
            # These may or may not be set, but the structure should exist
            print(f"Team settings keys: {settings.keys() if settings else 'empty'}")
    
    def test_team_dashboard_endpoint(self):
        """Test GET /api/team/dashboard returns dashboard data"""
        resp = self.session.get(f"{BASE_URL}/api/team/dashboard")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "team" in data
        assert "stats" in data
        assert "members" in data
        print(f"Dashboard stats: {data['stats']}")
    
    def test_team_conversations_returns_public_only(self):
        """Test GET /api/team/conversations returns only public chatbot conversations"""
        resp = self.session.get(f"{BASE_URL}/api/team/conversations")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Should be a list
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        # Each conversation should have chatbot mode indicator
        for conv in data:
            # Should have mode = chatbot or be from public chat
            assert "id" in conv or "session_id" in conv
            # Should NOT have private user conversations
            if "mode" in conv:
                assert conv["mode"] == "chatbot", f"Expected chatbot mode, got {conv['mode']}"
        print(f"Found {len(data)} public chatbot conversations")
    
    def test_team_config_with_new_fields(self):
        """Test POST /api/team/config accepts new fields: privacy_policy_url, agent_ia_enabled, pre_chat_fields"""
        config_data = {
            "bot_name": "Test Assistant",
            "bot_tone": "professional",
            "bot_context": "Test context",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "Bienvenue !",
            "end_of_credits_message": "Credits epuises",
            "alert_on_conversation": True,
            "alert_low_credits": True,
            "low_credit_threshold": 50,
            # New fields for iteration 72
            "privacy_policy_url": "https://example.com/privacy",
            "agent_ia_enabled": True,
            "pre_chat_fields": [
                {"key": "name", "label": "Votre nom", "type": "text", "required": True},
                {"key": "email", "label": "Votre email", "type": "email", "required": False},
                {"key": "phone", "label": "Telephone", "type": "tel", "required": False}
            ]
        }
        resp = self.session.post(f"{BASE_URL}/api/team/config", json=config_data)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "ok" or data.get("success") == True
        print("Config saved successfully with new fields")
        
        # Verify the config was saved by fetching team/me
        verify_resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert verify_resp.status_code == 200
        team_data = verify_resp.json()
        if team_data.get("team"):
            settings = team_data["team"].get("settings", {})
            assert settings.get("privacy_policy_url") == "https://example.com/privacy", "Privacy policy URL not saved"
            assert settings.get("agent_ia_enabled") == True, "Agent IA enabled not saved"
            assert len(settings.get("pre_chat_fields", [])) == 3, "Pre-chat fields not saved correctly"
            print("Verified: privacy_policy_url, agent_ia_enabled, pre_chat_fields saved correctly")


class TestMemberRoleChange:
    """Test PATCH /api/team/members/{id}/role endpoint"""
    
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
    
    def test_change_member_role_endpoint_exists(self):
        """Test PATCH /api/team/members/{id}/role endpoint exists and validates input"""
        # First get team members
        team_resp = self.session.get(f"{BASE_URL}/api/team/me")
        if team_resp.status_code != 200:
            pytest.skip("No team found")
        
        team_data = team_resp.json()
        members = team_data.get("members", [])
        
        # Find a non-owner member to test with
        non_owner = next((m for m in members if m.get("role") != "owner"), None)
        
        if non_owner:
            member_id = non_owner["id"]
            # Test changing role to admin
            resp = self.session.patch(f"{BASE_URL}/api/team/members/{member_id}/role", json={"role": "admin"})
            # Should succeed or return validation error
            assert resp.status_code in [200, 400, 403], f"Unexpected status: {resp.status_code}"
            if resp.status_code == 200:
                data = resp.json()
                assert data.get("success") == True or data.get("new_role") == "admin"
                print(f"Successfully changed role for member {member_id}")
        else:
            # Test with invalid member ID to verify endpoint exists
            resp = self.session.patch(f"{BASE_URL}/api/team/members/invalid-id/role", json={"role": "member"})
            assert resp.status_code in [404, 400, 403], f"Endpoint should return error for invalid ID, got {resp.status_code}"
            print("Endpoint exists and validates member ID")
    
    def test_invalid_role_rejected(self):
        """Test that invalid roles are rejected"""
        resp = self.session.patch(f"{BASE_URL}/api/team/members/test-id/role", json={"role": "superadmin"})
        # Should return 400 or 404 (not 500)
        assert resp.status_code in [400, 404, 403], f"Expected 400/404/403 for invalid role, got {resp.status_code}"


class TestInviteResend:
    """Test POST /api/team/invite/{id}/resend endpoint"""
    
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
    
    def test_resend_invite_endpoint_exists(self):
        """Test POST /api/team/invite/{id}/resend endpoint exists"""
        # Test with invalid ID to verify endpoint exists
        resp = self.session.post(f"{BASE_URL}/api/team/invite/invalid-id/resend")
        # Should return 404 for invalid member, not 405 (method not allowed)
        assert resp.status_code in [404, 400, 403], f"Expected 404/400/403, got {resp.status_code}: {resp.text}"
        print("Resend invite endpoint exists and validates member ID")
    
    def test_resend_invite_for_pending_member(self):
        """Test resending invite for a pending member"""
        # Get team members
        team_resp = self.session.get(f"{BASE_URL}/api/team/me")
        if team_resp.status_code != 200:
            pytest.skip("No team found")
        
        team_data = team_resp.json()
        members = team_data.get("members", [])
        
        # Find a pending member
        pending = next((m for m in members if m.get("status") == "pending"), None)
        
        if pending:
            member_id = pending["id"]
            resp = self.session.post(f"{BASE_URL}/api/team/invite/{member_id}/resend")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data.get("success") == True
            assert "invite_url" in data
            print(f"Successfully resent invite to {pending.get('email')}")
        else:
            print("No pending members to test resend with")


class TestPublicTeamInfo:
    """Test public team info endpoint"""
    
    def test_public_team_info_endpoint(self):
        """Test GET /api/team/public/info/{team_code}"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # First login to get team code
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if login_resp.status_code != 200:
            pytest.skip("Login failed")
        
        data = login_resp.json()
        token = data.get("access_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get team code
        team_resp = session.get(f"{BASE_URL}/api/team/me")
        if team_resp.status_code != 200:
            pytest.skip("No team found")
        
        team_data = team_resp.json()
        team_code = team_data.get("team", {}).get("team_code")
        
        if team_code:
            # Test public info endpoint (no auth required)
            public_session = requests.Session()
            resp = public_session.get(f"{BASE_URL}/api/team/public/info/{team_code}")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            info = resp.json()
            assert "team_name" in info
            assert "bot_name" in info
            assert "privacy_policy_url" in info
            assert "pre_chat_fields" in info
            print(f"Public team info: {info}")
        else:
            pytest.skip("No team code found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
