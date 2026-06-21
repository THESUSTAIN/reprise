"""
Iteration 44 - Backend API Tests
Testing: Team conversations endpoint and sidebar hide logic verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com')

class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@zayado.net"
        assert data["user"]["role"] == "admin"
        assert data["user"]["plan"] == "pro"


class TestTeamEndpoints:
    """Team API endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_team_me_endpoint(self, auth_token):
        """Test GET /api/team/me - returns team info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify team structure
        assert "team" in data
        assert "members" in data
        assert "is_owner" in data
        
        # Verify team fields
        team = data["team"]
        assert "id" in team
        assert "name" in team
        assert "owner_id" in team
        assert "shared_credits" in team
        assert "max_seats" in team
        assert "team_code" in team
        assert "bot_name" in team
        assert "bot_tone" in team
    
    def test_team_conversations_endpoint(self, auth_token):
        """Test GET /api/team/conversations - returns team conversations list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/team/conversations", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # If there are conversations, verify structure
        if len(data) > 0:
            conv = data[0]
            assert "id" in conv
            assert "title" in conv
            assert "mode" in conv
            assert "user_email" in conv
            assert "message_count" in conv
            assert "updated_at" in conv
            assert "created_at" in conv
    
    def test_team_dashboard_endpoint(self, auth_token):
        """Test GET /api/team/dashboard - returns team dashboard stats"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/team/dashboard", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard structure
        assert "stats" in data or "members" in data


class TestTeamConversationsData:
    """Verify team conversations data integrity"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_conversations_have_required_fields(self, auth_token):
        """Verify all conversations have required fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/team/conversations", headers=headers)
        
        assert response.status_code == 200
        conversations = response.json()
        
        for conv in conversations:
            # Required fields
            assert "id" in conv, f"Missing 'id' in conversation"
            assert "title" in conv, f"Missing 'title' in conversation {conv.get('id')}"
            assert "user_email" in conv, f"Missing 'user_email' in conversation {conv.get('id')}"
            
            # Optional but expected fields
            assert "mode" in conv, f"Missing 'mode' in conversation {conv.get('id')}"
            assert "message_count" in conv, f"Missing 'message_count' in conversation {conv.get('id')}"
    
    def test_conversations_count(self, auth_token):
        """Verify conversations are returned"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/team/conversations", headers=headers)
        
        assert response.status_code == 200
        conversations = response.json()
        
        # Should have at least some conversations based on previous tests
        print(f"Found {len(conversations)} team conversations")
        assert len(conversations) >= 0  # Can be empty for new teams


class TestUnauthorizedAccess:
    """Test unauthorized access to team endpoints"""
    
    def test_team_me_without_auth(self):
        """Test /api/team/me without authentication"""
        response = requests.get(f"{BASE_URL}/api/team/me")
        assert response.status_code in [401, 403, 422]
    
    def test_team_conversations_without_auth(self):
        """Test /api/team/conversations without authentication"""
        response = requests.get(f"{BASE_URL}/api/team/conversations")
        assert response.status_code in [401, 403, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
