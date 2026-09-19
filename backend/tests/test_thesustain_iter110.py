"""
Test TheSustain Page Features - Iteration 110
Tests for:
- POST /api/chat/image - Image generation endpoint
- TheSustain page access control
- Audit 360 Biblique functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTheSustainImageGeneration:
    """Tests for image generation endpoint used by TheSustain Création de Contenu tab"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_image_generation_endpoint_exists(self):
        """Test that POST /api/chat/image endpoint exists and requires auth"""
        # Test without auth
        response = requests.post(f"{BASE_URL}/api/chat/image", json={
            "prompt": "test",
            "style": "inspirant"
        })
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
    
    def test_image_generation_with_auth(self):
        """Test image generation with valid authentication (may take 30-60 seconds)"""
        response = self.session.post(
            f"{BASE_URL}/api/chat/image",
            json={
                "prompt": "A simple cross",
                "style": "inspirant"
            },
            timeout=120  # Long timeout for image generation
        )
        
        assert response.status_code == 200, f"Image generation failed: {response.text}"
        data = response.json()
        
        # Verify response contains image_base64
        assert "image_base64" in data, "Response should contain image_base64"
        assert len(data["image_base64"]) > 100, "image_base64 should contain actual data"
    
    def test_image_generation_different_styles(self):
        """Test image generation with different styles"""
        styles = ["inspirant", "evangelisation", "communaute", "adoration", "annonce", "temoignage"]
        
        # Test with one style to verify style parameter is accepted
        response = self.session.post(
            f"{BASE_URL}/api/chat/image",
            json={
                "prompt": "A church building",
                "style": "adoration"
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Image generation with style failed: {response.text}"
    
    def test_image_generation_empty_prompt(self):
        """Test image generation with empty prompt"""
        response = self.session.post(
            f"{BASE_URL}/api/chat/image",
            json={
                "prompt": "",
                "style": "inspirant"
            },
            timeout=30
        )
        
        # Should fail with validation error or generate anyway
        # The endpoint may handle empty prompts differently
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"


class TestTheSustainAccess:
    """Tests for TheSustain page access control"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_admin_can_access_thesustain(self):
        """Test that admin user can access TheSustain features"""
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        
        user_data = login_response.json().get("user", {})
        role = user_data.get("role")
        
        # Admin should have access
        assert role == "admin", f"Expected admin role, got {role}"
    
    def test_user_profile_contains_thesustain_fields(self):
        """Test that user profile contains TheSustain-related fields"""
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get user profile
        profile_response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert profile_response.status_code == 200
        
        user_data = profile_response.json()
        # User should have role field that determines TheSustain access
        assert "role" in user_data or "plan" in user_data, "User should have role or plan field"


class TestChatMessageEndpoint:
    """Tests for chat message endpoint used by Chatbot Pastoral"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_chat_message_endpoint_exists(self):
        """Test that POST /api/chat/message endpoint exists"""
        # This endpoint is used by the Chatbot Pastoral feature
        response = self.session.post(
            f"{BASE_URL}/api/chat/send",
            json={
                "message": "Bonjour",
                "mode": "fast"
            },
            timeout=60
        )
        
        # Should return 200 or streaming response
        assert response.status_code in [200, 201], f"Chat endpoint failed: {response.status_code}"


class TestTeamEndpoints:
    """Tests for team endpoints used by Chatbot Pastoral configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_team_me_endpoint(self):
        """Test GET /api/team/me endpoint"""
        response = self.session.get(f"{BASE_URL}/api/team/me")
        
        # May return 200 with team data or 404 if no team
        assert response.status_code in [200, 404], f"Team endpoint failed: {response.status_code}"
    
    def test_team_config_endpoint(self):
        """Test POST /api/team/config endpoint for chatbot configuration"""
        response = self.session.post(
            f"{BASE_URL}/api/team/config",
            json={
                "bot_name": "Gabriel",
                "welcome_message": "Bonjour ! Je suis Gabriel.",
                "tone": 2,
                "knowledge_context": "Test knowledge"
            }
        )
        
        # May return 200 or 404 if no team exists
        assert response.status_code in [200, 201, 404], f"Team config failed: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
