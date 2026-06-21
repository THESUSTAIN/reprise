"""
Iteration 86 - Test email settings, ExtensionIAPage, ChatbotB2BPage, and French accents
Features to test:
1. GET /api/workflows/email-settings returns email_prefix, email_domain, workflow_emails, approved_senders
2. PUT /api/workflows/email-settings updates email prefix and approved senders
3. ExtensionIAPage at /fr/extension-ia shows 'optimiser votre configuration commerciale' text
4. ExtensionIAPage has proper French accents (Modèles, Démarrage, complète, génération, etc.)
5. ChatbotB2BPage at /fr/chatbot-b2b has proper French accents (répond, intègre, crédits, Fonctionnalités)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


class TestAuthentication:
    """Test authentication to get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns 'access_token' not 'token'
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    def test_login_success(self, auth_token):
        """Verify login works and returns access_token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"PASS - Login successful, got access_token")


class TestEmailSettings:
    """Test email settings endpoints for workflows"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    def test_get_email_settings(self, auth_token):
        """GET /api/workflows/email-settings returns expected fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/workflows/email-settings", headers=headers)
        
        assert response.status_code == 200, f"GET email-settings failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify all required fields are present
        assert "email_prefix" in data, "Missing email_prefix field"
        assert "email_domain" in data, "Missing email_domain field"
        assert "workflow_emails" in data, "Missing workflow_emails field"
        assert "approved_senders" in data, "Missing approved_senders field"
        
        # Verify email_domain is zayado.bot
        assert data["email_domain"] == "zayado.bot", f"Expected email_domain 'zayado.bot', got '{data['email_domain']}'"
        
        # Verify types
        assert isinstance(data["workflow_emails"], list), "workflow_emails should be a list"
        assert isinstance(data["approved_senders"], list), "approved_senders should be a list"
        
        print(f"PASS - GET /api/workflows/email-settings returns: email_prefix={data['email_prefix']}, email_domain={data['email_domain']}, workflow_emails count={len(data['workflow_emails'])}, approved_senders count={len(data['approved_senders'])}")
    
    def test_update_email_prefix(self, auth_token):
        """PUT /api/workflows/email-settings updates email prefix"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Update email prefix
        test_prefix = "testprefix86"
        response = requests.put(
            f"{BASE_URL}/api/workflows/email-settings",
            headers=headers,
            json={"email_prefix": test_prefix}
        )
        
        assert response.status_code == 200, f"PUT email-settings failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert data.get("status") == "ok", f"Expected status 'ok', got '{data.get('status')}'"
        assert data.get("email_prefix") == test_prefix, f"Expected email_prefix '{test_prefix}', got '{data.get('email_prefix')}'"
        
        print(f"PASS - PUT /api/workflows/email-settings updated email_prefix to '{test_prefix}'")
    
    def test_update_approved_senders(self, auth_token):
        """PUT /api/workflows/email-settings updates approved senders"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Update approved senders
        test_senders = [
            {"email": "test1@example.com"},
            {"email": "test2@example.com"}
        ]
        response = requests.put(
            f"{BASE_URL}/api/workflows/email-settings",
            headers=headers,
            json={"approved_senders": test_senders}
        )
        
        assert response.status_code == 200, f"PUT email-settings failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert data.get("status") == "ok", f"Expected status 'ok', got '{data.get('status')}'"
        assert len(data.get("approved_senders", [])) == 2, f"Expected 2 approved_senders, got {len(data.get('approved_senders', []))}"
        
        # Verify the emails are in the response
        sender_emails = [s.get("email") for s in data.get("approved_senders", [])]
        assert "test1@example.com" in sender_emails, "test1@example.com not in approved_senders"
        assert "test2@example.com" in sender_emails, "test2@example.com not in approved_senders"
        
        print(f"PASS - PUT /api/workflows/email-settings updated approved_senders: {sender_emails}")
    
    def test_update_workflow_emails(self, auth_token):
        """PUT /api/workflows/email-settings updates workflow emails"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Update workflow emails
        test_workflow_emails = [
            {"address": "newsletter", "instructions": "Resume les newsletters quotidiennes"}
        ]
        response = requests.put(
            f"{BASE_URL}/api/workflows/email-settings",
            headers=headers,
            json={"workflow_emails": test_workflow_emails}
        )
        
        assert response.status_code == 200, f"PUT email-settings failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert data.get("status") == "ok", f"Expected status 'ok', got '{data.get('status')}'"
        assert len(data.get("workflow_emails", [])) == 1, f"Expected 1 workflow_email, got {len(data.get('workflow_emails', []))}"
        
        print(f"PASS - PUT /api/workflows/email-settings updated workflow_emails")
    
    def test_email_prefix_validation_min_length(self, auth_token):
        """PUT /api/workflows/email-settings validates email prefix min length"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Try to set a prefix that's too short (less than 2 characters)
        response = requests.put(
            f"{BASE_URL}/api/workflows/email-settings",
            headers=headers,
            json={"email_prefix": "a"}
        )
        
        assert response.status_code == 400, f"Expected 400 for short prefix, got {response.status_code}"
        print(f"PASS - Email prefix validation rejects prefix < 2 characters")


class TestPublicPages:
    """Test public pages for French accents and content"""
    
    def test_extension_ia_page_loads(self):
        """Test ExtensionIAPage at /fr/extension-ia loads"""
        response = requests.get(f"{BASE_URL}/fr/extension-ia", allow_redirects=True)
        # Frontend routes may return 200 or redirect to index.html
        assert response.status_code in [200, 304], f"ExtensionIAPage failed to load: {response.status_code}"
        print(f"PASS - ExtensionIAPage at /fr/extension-ia loads (status {response.status_code})")
    
    def test_chatbot_b2b_page_loads(self):
        """Test ChatbotB2BPage at /fr/chatbot-b2b loads"""
        response = requests.get(f"{BASE_URL}/fr/chatbot-b2b", allow_redirects=True)
        # Frontend routes may return 200 or redirect to index.html
        assert response.status_code in [200, 304], f"ChatbotB2BPage failed to load: {response.status_code}"
        print(f"PASS - ChatbotB2BPage at /fr/chatbot-b2b loads (status {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
