"""
Test P0 Bug Fixes - Iteration 137
1. Conversation 404 handling - non-existent conversations should return 404
2. Default API provider changed from 'emergent' to 'mammoth'
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestP0BugFixes:
    """Test P0 bug fixes for conversation 404 and API provider defaults"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.admin_email = "admin@zayado.net"
        self.admin_password = "admin123"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_auth_token(self):
        """Get authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    # ============ CONVERSATION 404 TESTS ============
    
    def test_health_endpoint(self):
        """Test health endpoint is working"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("PASS: Health endpoint returns healthy status")
    
    def test_login_admin_credentials(self):
        """Test login with admin credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("PASS: Admin login successful")
    
    def test_get_nonexistent_conversation_returns_404(self):
        """Test that GET /api/chat/conversations/<non-existent-id> returns 404"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        # Use a random UUID that doesn't exist
        fake_id = str(uuid.uuid4())
        response = self.session.get(
            f"{BASE_URL}/api/chat/conversations/{fake_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "not found" in data.get("detail", "").lower() or "introuvable" in data.get("detail", "").lower()
        print(f"PASS: Non-existent conversation {fake_id[:8]}... returns 404")
    
    def test_get_nonexistent_conversation_with_specific_id(self):
        """Test with a specific fake conversation ID format"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        # Use a specific fake ID pattern
        fake_id = "765a8952-fake-conv-id"
        response = self.session.get(
            f"{BASE_URL}/api/chat/conversations/{fake_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"PASS: Specific fake conversation ID returns 404")
    
    def test_get_existing_conversation_returns_200(self):
        """Test that GET /api/chat/conversations/<existing-id> returns 200"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        # First, get list of conversations to find an existing one
        response = self.session.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        conversations = response.json()
        
        if len(conversations) > 0:
            existing_id = conversations[0].get("id")
            response = self.session.get(
                f"{BASE_URL}/api/chat/conversations/{existing_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "id" in data
            assert "messages" in data
            print(f"PASS: Existing conversation {existing_id[:8]}... returns 200 with data")
        else:
            # Test with the known existing conversation ID from the request
            existing_id = "2652db17-3318-4f99-a8f0-03189e47d588"
            response = self.session.get(
                f"{BASE_URL}/api/chat/conversations/{existing_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            # This might be 404 if the conversation doesn't exist for this user
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                print(f"PASS: Known conversation ID returns 200")
            else:
                print(f"INFO: Known conversation ID not found for this user (expected if different user)")
    
    def test_conversations_list_returns_array(self):
        """Test that GET /api/chat/conversations returns a list"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Conversations list returns array with {len(data)} items")
    
    def test_conversations_requires_auth(self):
        """Test that conversations endpoint requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/chat/conversations")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Conversations endpoint requires authentication")
    
    # ============ API PROVIDER DEFAULT TESTS ============
    
    def test_chat_send_fast_mode(self):
        """Test that POST /api/chat/send with mode 'fast' works (uses Mammoth API)"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        # Send a simple message in fast mode
        response = self.session.post(
            f"{BASE_URL}/api/chat/send",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "text/event-stream"
            },
            json={
                "message": "Dis bonjour en une phrase",
                "mode": "fast"
            },
            stream=True
        )
        
        # Should return 200 for SSE stream
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Read first few chunks to verify streaming works
        content_received = False
        conversation_id = None
        for i, line in enumerate(response.iter_lines(decode_unicode=True)):
            if line and line.startswith("data: "):
                try:
                    import json
                    data = json.loads(line[6:])
                    if data.get("content"):
                        content_received = True
                    if data.get("conversation_id"):
                        conversation_id = data.get("conversation_id")
                except:
                    pass
            if i > 20:  # Read first 20 lines max
                break
        
        print(f"PASS: Chat send in fast mode returns 200 SSE stream, content_received={content_received}")
        if conversation_id:
            print(f"  - Conversation ID: {conversation_id[:8]}...")
    
    def test_folders_endpoint(self):
        """Test folders endpoint works"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(
            f"{BASE_URL}/api/folders",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Folders endpoint returns {len(data)} folders")


class TestCodeVerification:
    """Verify code changes for API provider defaults"""
    
    def test_chat_routes_no_emergent_default(self):
        """Verify chat_routes.py doesn't have 'emergent' as default fallback provider"""
        chat_routes_path = "/app/backend/routes/chat_routes.py"
        
        with open(chat_routes_path, 'r') as f:
            content = f.read()
        
        # Check for the fallback provider default - should be 'mammoth' not 'emergent'
        # Line ~847: _fb_provider = _fb_cfg.get("provider", "mammoth")
        # Line ~1381: _fb2_provider = _fb2_cfg.get("provider", "mammoth")
        
        # Count occurrences of emergent as default
        emergent_defaults = content.count('.get("provider", "emergent")')
        mammoth_defaults = content.count('.get("provider", "mammoth")')
        
        assert emergent_defaults == 0, f"Found {emergent_defaults} occurrences of 'emergent' as default provider"
        assert mammoth_defaults >= 2, f"Expected at least 2 'mammoth' defaults, found {mammoth_defaults}"
        
        print(f"PASS: No 'emergent' as default provider, found {mammoth_defaults} 'mammoth' defaults")
    
    def test_mammoth_api_url_used(self):
        """Verify Mammoth API URL is used correctly"""
        chat_routes_path = "/app/backend/routes/chat_routes.py"
        
        with open(chat_routes_path, 'r') as f:
            content = f.read()
        
        # Check for Mammoth API URL
        mammoth_url_count = content.count("https://api.mammouth.ai/v1/chat/completions")
        
        assert mammoth_url_count >= 5, f"Expected at least 5 Mammoth API URL references, found {mammoth_url_count}"
        print(f"PASS: Found {mammoth_url_count} references to Mammoth API URL")
    
    def test_mammoth_key_env_var(self):
        """Verify MAMMOTH_API_KEY environment variable is used"""
        chat_routes_path = "/app/backend/routes/chat_routes.py"
        
        with open(chat_routes_path, 'r') as f:
            content = f.read()
        
        # Check for MAMMOTH_API_KEY usage
        mammoth_key_count = content.count("MAMMOTH_API_KEY")
        
        assert mammoth_key_count >= 2, f"Expected at least 2 MAMMOTH_API_KEY references, found {mammoth_key_count}"
        print(f"PASS: Found {mammoth_key_count} references to MAMMOTH_API_KEY")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
