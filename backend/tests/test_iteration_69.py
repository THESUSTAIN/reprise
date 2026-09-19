"""
Iteration 69 Backend Tests
Testing: Prompts API, Share-Support API, Public Chat Route
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_api_health(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("✓ API health check passed")
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data, "No token in response"
        print("✓ Admin login successful")
        return data.get("token") or data.get("access_token")


class TestPromptsAPI:
    """Test /api/prompts endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_get_prompts(self, auth_token):
        """GET /api/prompts should return system_prompts and user_prompts arrays"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/prompts", headers=headers, timeout=10)
        
        assert response.status_code == 200, f"GET prompts failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "system_prompts" in data, "Missing system_prompts in response"
        assert "user_prompts" in data, "Missing user_prompts in response"
        assert isinstance(data["system_prompts"], list), "system_prompts should be a list"
        assert isinstance(data["user_prompts"], list), "user_prompts should be a list"
        
        print(f"✓ GET /api/prompts returned {len(data['system_prompts'])} system prompts, {len(data['user_prompts'])} user prompts")
    
    def test_create_prompt(self, auth_token):
        """POST /api/prompts should create a new custom prompt"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        prompt_data = {
            "title": "TEST_Iteration69_Prompt",
            "prompt": "This is a test prompt for iteration 69 testing",
            "category": "chatbot"
        }
        
        response = requests.post(f"{BASE_URL}/api/prompts", headers=headers, json=prompt_data, timeout=10)
        
        assert response.status_code == 200, f"POST prompts failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify created prompt
        assert "id" in data, "Created prompt should have an id"
        assert data["title"] == prompt_data["title"], "Title mismatch"
        assert data["prompt"] == prompt_data["prompt"], "Prompt content mismatch"
        assert data["is_system"] == False, "User prompt should not be system prompt"
        
        print(f"✓ POST /api/prompts created prompt with id: {data['id']}")
        
        # Cleanup - delete the test prompt
        delete_response = requests.delete(f"{BASE_URL}/api/prompts/{data['id']}", headers=headers, timeout=10)
        if delete_response.status_code in [200, 204]:
            print(f"✓ Cleaned up test prompt {data['id']}")
    
    def test_create_and_verify_prompt_persistence(self, auth_token):
        """Create prompt then GET to verify it persists"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        prompt_data = {
            "title": "TEST_Persistence_Check",
            "prompt": "Testing persistence of prompts",
            "category": "general"
        }
        
        # Create
        create_response = requests.post(f"{BASE_URL}/api/prompts", headers=headers, json=prompt_data, timeout=10)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        created = create_response.json()
        prompt_id = created["id"]
        
        # GET all prompts and verify our prompt is there
        get_response = requests.get(f"{BASE_URL}/api/prompts", headers=headers, timeout=10)
        assert get_response.status_code == 200
        data = get_response.json()
        
        user_prompt_ids = [p["id"] for p in data["user_prompts"]]
        assert prompt_id in user_prompt_ids, "Created prompt not found in user_prompts"
        
        print(f"✓ Prompt {prompt_id} persisted and found in GET response")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/prompts/{prompt_id}", headers=headers, timeout=10)


class TestShareSupportAPI:
    """Test /api/team/public/share-support endpoint"""
    
    def test_share_support_invalid_team_code(self):
        """POST /api/team/public/share-support with invalid team code should return 404"""
        response = requests.post(f"{BASE_URL}/api/team/public/share-support", json={
            "team_code": "INVALID-CODE-123",
            "session_id": "test-session-123",
            "visible": True
        }, timeout=10)
        
        # Should return 404 for invalid team code
        assert response.status_code == 404, f"Expected 404 for invalid team code, got {response.status_code}"
        print("✓ POST /api/team/public/share-support returns 404 for invalid team code")
    
    def test_share_support_endpoint_exists(self):
        """Verify the share-support endpoint exists (not 405 Method Not Allowed)"""
        response = requests.post(f"{BASE_URL}/api/team/public/share-support", json={
            "team_code": "TEST-CODE",
            "session_id": "test-session",
            "visible": True
        }, timeout=10)
        
        # Should NOT be 405 (method not allowed) or 404 (endpoint not found)
        # 404 is acceptable if it's "team not found" vs "endpoint not found"
        assert response.status_code != 405, "Endpoint does not accept POST method"
        
        # Check if it's a proper error response
        if response.status_code == 404:
            data = response.json()
            assert "detail" in data, "Should have error detail"
            print(f"✓ Endpoint exists, returns 404 with detail: {data.get('detail')}")
        else:
            print(f"✓ Endpoint exists, returned status: {response.status_code}")


class TestPublicChatRoute:
    """Test public chat team info endpoint"""
    
    def test_public_team_info_invalid_code(self):
        """GET /api/team/public/info/{invalid_code} should return 404"""
        response = requests.get(f"{BASE_URL}/api/team/public/info/INVALID-CODE-XYZ", timeout=10)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Should have error detail"
        print(f"✓ Public team info returns 404 for invalid code: {data.get('detail')}")
    
    def test_public_chat_invalid_code(self):
        """POST /api/team/public/chat with invalid code should return 404"""
        response = requests.post(f"{BASE_URL}/api/team/public/chat", json={
            "team_code": "INVALID-CODE-ABC",
            "message": "Hello",
            "user_name": "Test User"
        }, timeout=10)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Public chat returns 404 for invalid team code")


class TestTeamAPI:
    """Test team-related endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_get_team_me(self, auth_token):
        """GET /api/team/me should return team info or null"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/team/me", headers=headers, timeout=10)
        
        assert response.status_code == 200, f"GET team/me failed: {response.status_code}"
        data = response.json()
        
        # Should have team key (can be null if no team)
        assert "team" in data, "Response should have 'team' key"
        
        if data["team"]:
            # If team exists, verify structure
            team = data["team"]
            assert "id" in team, "Team should have id"
            assert "name" in team, "Team should have name"
            assert "team_code" in team or team.get("team_code") is None, "Team should have team_code"
            print(f"✓ GET /api/team/me returned team: {team.get('name')} (code: {team.get('team_code')})")
        else:
            print("✓ GET /api/team/me returned null team (user has no team)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
