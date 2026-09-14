"""
Test suite for Integrations API endpoints (Brevo Email + Web Scraping)
Iteration 131 - Testing new 'Actions réelles agents' feature
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_USER_EMAIL = "test.productivite@zayado.net"
TEST_USER_PASSWORD = "TestProd2026!"
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    # Try admin if test user doesn't exist
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestHealthCheck:
    """Basic health check to ensure API is running"""
    
    def test_health_endpoint(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health endpoint working")


class TestIntegrationsGet:
    """GET /api/integrations - Returns status of all integrations"""
    
    def test_get_integrations_returns_brevo_and_scraping(self, authenticated_client):
        """Fresh user should see brevo (configured: false) and scraping (configured: true, actif)"""
        response = authenticated_client.get(f"{BASE_URL}/api/integrations")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify brevo structure
        assert "brevo" in data, "Response should contain 'brevo' key"
        brevo = data["brevo"]
        assert "configured" in brevo, "brevo should have 'configured' field"
        assert isinstance(brevo["configured"], bool), "brevo.configured should be boolean"
        
        # Verify scraping structure
        assert "scraping" in data, "Response should contain 'scraping' key"
        scraping = data["scraping"]
        assert scraping.get("configured") == True, "scraping should be configured: true"
        assert scraping.get("status") == "actif", "scraping status should be 'actif'"
        
        print(f"✓ GET /api/integrations returns correct structure")
        print(f"  - brevo.configured: {brevo['configured']}")
        print(f"  - scraping.configured: {scraping['configured']}, status: {scraping['status']}")
    
    def test_get_integrations_requires_auth(self, api_client):
        """Unauthenticated request should fail"""
        # Create a new session without auth
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/integrations")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/integrations requires authentication")


class TestBrevoIntegration:
    """PUT/DELETE /api/integrations/brevo - Brevo API key management"""
    
    def test_save_brevo_key_valid_format(self, authenticated_client):
        """Valid Brevo key (starts with xkeysib-) should be saved"""
        test_key = "xkeysib-test1234567890abcdef1234567890abcdef"
        response = authenticated_client.put(f"{BASE_URL}/api/integrations/brevo", json={
            "api_key": test_key,
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success", "Response should have status: success"
        print("✓ PUT /api/integrations/brevo saves valid key")
    
    def test_save_brevo_key_invalid_format(self, authenticated_client):
        """Invalid Brevo key (not starting with xkeysib-) should be rejected"""
        invalid_key = "sk-invalid-key-format"
        response = authenticated_client.put(f"{BASE_URL}/api/integrations/brevo", json={
            "api_key": invalid_key
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data, "Error response should have 'detail'"
        assert "xkeysib" in data["detail"].lower() or "format" in data["detail"].lower(), \
            f"Error should mention format issue: {data['detail']}"
        print("✓ PUT /api/integrations/brevo rejects invalid key format")
    
    def test_save_brevo_key_empty(self, authenticated_client):
        """Empty Brevo key should be rejected"""
        response = authenticated_client.put(f"{BASE_URL}/api/integrations/brevo", json={
            "api_key": ""
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ PUT /api/integrations/brevo rejects empty key")
    
    def test_get_integrations_after_save_shows_configured(self, authenticated_client):
        """After saving key, GET should show brevo configured: true with masked key"""
        # First save a valid key
        test_key = "xkeysib-test1234567890abcdef1234567890abcdef"
        save_response = authenticated_client.put(f"{BASE_URL}/api/integrations/brevo", json={
            "api_key": test_key,
            "sender_email": "test@example.com",
            "sender_name": "Test Sender"
        })
        assert save_response.status_code == 200
        
        # Then verify GET shows configured
        response = authenticated_client.get(f"{BASE_URL}/api/integrations")
        assert response.status_code == 200
        
        data = response.json()
        brevo = data.get("brevo", {})
        assert brevo.get("configured") == True, "brevo should be configured: true after saving key"
        assert brevo.get("key_preview") is not None, "brevo should have key_preview"
        assert "..." in brevo.get("key_preview", ""), "key_preview should be masked with ..."
        assert brevo.get("sender_email") == "test@example.com", "sender_email should be saved"
        assert brevo.get("sender_name") == "Test Sender", "sender_name should be saved"
        
        print(f"✓ GET /api/integrations shows brevo configured with masked key: {brevo['key_preview']}")
    
    def test_delete_brevo_key(self, authenticated_client):
        """DELETE should remove the Brevo key"""
        response = authenticated_client.delete(f"{BASE_URL}/api/integrations/brevo")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success", "Response should have status: success"
        print("✓ DELETE /api/integrations/brevo removes key")
    
    def test_get_integrations_after_delete_shows_not_configured(self, authenticated_client):
        """After deleting key, GET should show brevo configured: false"""
        # First delete the key
        authenticated_client.delete(f"{BASE_URL}/api/integrations/brevo")
        
        # Then verify GET shows not configured
        response = authenticated_client.get(f"{BASE_URL}/api/integrations")
        assert response.status_code == 200
        
        data = response.json()
        brevo = data.get("brevo", {})
        assert brevo.get("configured") == False, "brevo should be configured: false after deletion"
        print("✓ GET /api/integrations shows brevo not configured after deletion")


class TestWebScraping:
    """POST /api/integrations/scrape - Web scraping functionality"""
    
    def test_scrape_valid_url(self, authenticated_client):
        """Scraping https://example.com should return success with title and text"""
        response = authenticated_client.post(f"{BASE_URL}/api/integrations/scrape", json={
            "url": "https://example.com"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success", f"Expected status: success, got: {data.get('status')}"
        assert "title" in data, "Response should contain 'title'"
        assert "text" in data, "Response should contain 'text'"
        assert data.get("url") == "https://example.com", "Response should echo the URL"
        
        # example.com should have "Example Domain" as title
        assert "example" in data.get("title", "").lower() or "domain" in data.get("title", "").lower(), \
            f"Title should contain 'example' or 'domain': {data.get('title')}"
        
        print(f"✓ POST /api/integrations/scrape returns success")
        print(f"  - title: {data.get('title')}")
        print(f"  - text length: {len(data.get('text', ''))}")
        print(f"  - word_count: {data.get('word_count')}")
    
    def test_scrape_invalid_url(self, authenticated_client):
        """Invalid URL should return error"""
        response = authenticated_client.post(f"{BASE_URL}/api/integrations/scrape", json={
            "url": "not-a-valid-url"
        })
        # Could be 400 or 200 with error status depending on implementation
        data = response.json()
        
        if response.status_code == 400:
            assert "detail" in data, "Error response should have 'detail'"
            print("✓ POST /api/integrations/scrape returns 400 for invalid URL")
        else:
            assert data.get("status") == "error", f"Expected status: error, got: {data.get('status')}"
            print("✓ POST /api/integrations/scrape returns error status for invalid URL")
    
    def test_scrape_empty_url(self, authenticated_client):
        """Empty URL should return error"""
        response = authenticated_client.post(f"{BASE_URL}/api/integrations/scrape", json={
            "url": ""
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ POST /api/integrations/scrape rejects empty URL")
    
    def test_scrape_requires_auth(self, api_client):
        """Unauthenticated scrape request should fail"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/integrations/scrape", json={
            "url": "https://example.com"
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/integrations/scrape requires authentication")


class TestBrevoTestEndpoint:
    """POST /api/integrations/brevo/test - Test Brevo API key validity"""
    
    def test_brevo_test_without_key(self, authenticated_client):
        """Testing without a configured key should return error"""
        # First ensure no key is configured
        authenticated_client.delete(f"{BASE_URL}/api/integrations/brevo")
        
        response = authenticated_client.post(f"{BASE_URL}/api/integrations/brevo/test")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ POST /api/integrations/brevo/test returns 400 when no key configured")
    
    def test_brevo_test_with_invalid_key(self, authenticated_client):
        """Testing with an invalid key should return valid: false"""
        # Save a fake key
        authenticated_client.put(f"{BASE_URL}/api/integrations/brevo", json={
            "api_key": "xkeysib-fake-invalid-key-for-testing"
        })
        
        response = authenticated_client.post(f"{BASE_URL}/api/integrations/brevo/test")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("valid") == False, "Test with invalid key should return valid: false"
        print("✓ POST /api/integrations/brevo/test returns valid: false for invalid key")
        
        # Cleanup
        authenticated_client.delete(f"{BASE_URL}/api/integrations/brevo")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
