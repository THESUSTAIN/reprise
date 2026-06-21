"""
Iteration 132 Backend Tests
Tests for:
1. POST /api/chat/send with mode=fast returns valid streamed response
2. GET /api/integrations returns brevo and scraping status
3. POST /api/integrations/scrape with url 'https://example.com' returns success
4. GET /api/folders returns a valid response
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "test.productivite@zayado.net"
TEST_USER_PASSWORD = "TestProd2026!"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Login response uses 'access_token' field
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data


class TestIntegrations:
    """Integration endpoints tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    def test_get_integrations_returns_brevo_and_scraping(self, auth_token):
        """GET /api/integrations returns brevo and scraping status"""
        response = requests.get(
            f"{BASE_URL}/api/integrations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify brevo key exists
        assert "brevo" in data, f"Missing 'brevo' in response: {data}"
        assert "configured" in data["brevo"], f"Missing 'configured' in brevo: {data}"
        
        # Verify scraping key exists
        assert "scraping" in data, f"Missing 'scraping' in response: {data}"
        assert "configured" in data["scraping"], f"Missing 'configured' in scraping: {data}"
        assert data["scraping"]["configured"] == True, f"Scraping should be configured: {data}"
        assert data["scraping"]["status"] == "actif", f"Scraping status should be 'actif': {data}"
        
        print(f"✓ GET /api/integrations returns brevo and scraping: {data}")
    
    def test_scrape_valid_url(self, auth_token):
        """POST /api/integrations/scrape with url 'https://example.com' returns success"""
        response = requests.post(
            f"{BASE_URL}/api/integrations/scrape",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"url": "https://example.com"}
        )
        assert response.status_code == 200, f"Scrape failed: {response.text}"
        data = response.json()
        
        # Verify success response
        assert data.get("status") == "success", f"Scrape status not success: {data}"
        assert "title" in data, f"Missing 'title' in scrape response: {data}"
        assert "text" in data, f"Missing 'text' in scrape response: {data}"
        assert data.get("url") == "https://example.com", f"URL mismatch: {data}"
        
        print(f"✓ POST /api/integrations/scrape success: title='{data.get('title')}', text_length={len(data.get('text', ''))}")


class TestFolders:
    """Folders endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    def test_get_folders_returns_valid_response(self, auth_token):
        """GET /api/folders returns a valid response (not slow)"""
        import time
        start = time.time()
        
        response = requests.get(
            f"{BASE_URL}/api/folders",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10  # Should respond within 10 seconds
        )
        
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Folders failed: {response.text}"
        data = response.json()
        
        # Should return a list (even if empty)
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        
        # Should be reasonably fast (under 5 seconds)
        assert elapsed < 5, f"Folders endpoint too slow: {elapsed:.2f}s"
        
        print(f"✓ GET /api/folders returned {len(data)} folders in {elapsed:.2f}s")


class TestChatSend:
    """Chat send endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    def test_chat_send_fast_mode_returns_streamed_response(self, auth_token):
        """POST /api/chat/send with mode=fast returns a valid streamed response (no 500 error)"""
        import uuid
        
        conversation_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "message": "Bonjour, dis-moi juste 'OK' en une seule ligne.",
                "mode": "fast",
                "conversation_id": conversation_id
            },
            stream=True,
            timeout=60
        )
        
        # Should not return 500 error
        assert response.status_code != 500, f"Chat send returned 500 error: {response.text}"
        assert response.status_code == 200, f"Chat send failed with status {response.status_code}: {response.text}"
        
        # Read streamed response
        full_response = ""
        has_content = False
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        if "content" in chunk:
                            full_response += chunk["content"]
                            has_content = True
                        if "error" in chunk:
                            # Check if it's a credit error (expected for free plan)
                            if "credits" in chunk["error"].lower() or "insuffisants" in chunk["error"].lower():
                                print(f"✓ Chat send returned credit error (expected for free plan): {chunk['error']}")
                                return
                            pytest.fail(f"Chat send returned error: {chunk['error']}")
                    except json.JSONDecodeError:
                        continue
        
        # Should have received some content
        assert has_content or full_response, f"No content received in streamed response"
        
        print(f"✓ POST /api/chat/send mode=fast returned streamed response: {full_response[:100]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
