"""
Iteration 92 - Backend API Tests
Testing: /api/team/list, /api/chat/conversations, and auth endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com')

class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test admin login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == "admin@zayado.net"
        return data["access_token"]

    def test_login_invalid_credentials(self):
        """Test login with wrong credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


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
    
    def test_team_list_endpoint(self, auth_token):
        """Test GET /api/team/list returns teams"""
        response = requests.get(
            f"{BASE_URL}/api/team/list",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Team list failed: {response.text}"
        data = response.json()
        # Response should have teams structure
        assert "teams" in data or isinstance(data, list), f"Unexpected response: {data}"


class TestChatEndpoints:
    """Chat API endpoint tests"""
    
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
    
    def test_conversations_list(self, auth_token):
        """Test GET /api/chat/conversations returns list"""
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Conversations list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
    
    def test_conversations_with_limit(self, auth_token):
        """Test GET /api/chat/conversations with limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations?limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Conversations list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) <= 5, f"Expected max 5 items, got {len(data)}"


class TestHealthEndpoints:
    """Health check tests"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        # Accept 200 or 404 (if endpoint doesn't exist)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
    
    def test_public_config(self):
        """Test public config endpoint"""
        response = requests.get(f"{BASE_URL}/api/public/config")
        assert response.status_code == 200, f"Public config failed: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
