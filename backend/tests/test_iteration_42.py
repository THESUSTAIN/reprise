"""
Iteration 42 - Backend API Tests for ZAYADO French AI SaaS
Tests: Login, Prompts CRUD, Diagnostic endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert len(data["access_token"]) > 0, "Empty access_token"
        print(f"Login successful, token length: {len(data['access_token'])}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"


class TestPromptsCRUD:
    """Prompts CRUD API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_prompts(self, auth_token):
        """Test GET /api/prompts - list all prompts"""
        response = requests.get(
            f"{BASE_URL}/api/prompts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get prompts failed: {response.text}"
        
        data = response.json()
        assert "system_prompts" in data, "No system_prompts in response"
        assert "user_prompts" in data, "No user_prompts in response"
        print(f"Found {len(data['system_prompts'])} system prompts, {len(data['user_prompts'])} user prompts")
    
    def test_create_prompt(self, auth_token):
        """Test POST /api/prompts - create new prompt"""
        prompt_data = {
            "title": "TEST_Prompt_42",
            "prompt": "This is a test prompt for iteration 42",
            "category": "general",
            "icon": "sparkles",
            "color": "bg-blue-50 text-blue-600",
            "action": "insert"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/prompts",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json=prompt_data
        )
        assert response.status_code in [200, 201], f"Create prompt failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "No id in created prompt"
        assert data["title"] == prompt_data["title"], "Title mismatch"
        print(f"Created prompt with id: {data['id']}")
        
        # Store for cleanup
        return data["id"]
    
    def test_update_prompt(self, auth_token):
        """Test PUT /api/prompts/{id} - update prompt"""
        # First create a prompt
        create_response = requests.post(
            f"{BASE_URL}/api/prompts",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "title": "TEST_Update_42",
                "prompt": "Original content",
                "category": "general",
                "action": "insert"
            }
        )
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        prompt_id = create_response.json()["id"]
        
        # Update the prompt
        update_response = requests.put(
            f"{BASE_URL}/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"title": "TEST_Updated_42", "prompt": "Updated content"}
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated_data = update_response.json()
        assert updated_data["title"] == "TEST_Updated_42", "Title not updated"
        print(f"Updated prompt {prompt_id}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_delete_prompt(self, auth_token):
        """Test DELETE /api/prompts/{id} - delete prompt"""
        # First create a prompt
        create_response = requests.post(
            f"{BASE_URL}/api/prompts",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "title": "TEST_Delete_42",
                "prompt": "To be deleted",
                "category": "general",
                "action": "insert"
            }
        )
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        prompt_id = create_response.json()["id"]
        
        # Delete the prompt
        delete_response = requests.delete(
            f"{BASE_URL}/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"Deleted prompt {prompt_id}")


class TestDiagnostic:
    """Diagnostic feature tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_diagnostic_score(self, auth_token):
        """Test GET /api/features/diagnostic/score"""
        response = requests.get(
            f"{BASE_URL}/api/features/diagnostic/score",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get diagnostic score failed: {response.text}"
        
        data = response.json()
        assert "score" in data, "No score in response"
        assert "pillars" in data, "No pillars in response"
        print(f"Diagnostic score: {data['score']}")
    
    def test_submit_diagnostic(self, auth_token):
        """Test POST /api/features/diagnostic/submit"""
        answers = {
            "activity_type": "freelance",
            "revenue_level": "2k-5k",
            "main_challenge": "clients",
            "clarity": "3",
            "energy": "4",
            "tools_usage": "some"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/features/diagnostic/submit",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"answers": answers}
        )
        assert response.status_code == 200, f"Submit diagnostic failed: {response.text}"
        
        data = response.json()
        assert "score" in data, "No score in response"
        assert "pillars" in data, "No pillars in response"
        print(f"Submitted diagnostic, new score: {data['score']}")


class TestConversations:
    """Conversation/Chat API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_conversations(self, auth_token):
        """Test GET /api/chat/conversations - list conversations"""
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} conversations")
        
        # Check conversation structure if any exist
        if len(data) > 0:
            conv = data[0]
            assert "id" in conv or "_id" in conv, "No id in conversation"
            print(f"First conversation: {conv.get('title', conv.get('id', 'N/A'))}")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_cleanup_test_prompts(self, auth_token):
        """Clean up TEST_ prefixed prompts"""
        # Get all prompts
        response = requests.get(
            f"{BASE_URL}/api/prompts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code != 200:
            return
        
        data = response.json()
        user_prompts = data.get("user_prompts", [])
        
        deleted = 0
        for prompt in user_prompts:
            if prompt.get("title", "").startswith("TEST_"):
                del_response = requests.delete(
                    f"{BASE_URL}/api/prompts/{prompt['id']}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                if del_response.status_code == 200:
                    deleted += 1
        
        print(f"Cleaned up {deleted} test prompts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
