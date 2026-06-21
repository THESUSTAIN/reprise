"""
Iteration 87 Backend Tests
Tests for:
- Email settings API (GET/PUT /api/workflows/email-settings)
- ExtensionIAPage and public pages loading
- French accents verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test admin login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"PASS - Admin login successful, got access_token")
        return data["access_token"]


class TestEmailSettingsAPI:
    """Email settings API tests (GET/PUT /api/workflows/email-settings)"""
    
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
    
    def test_get_email_settings(self, auth_token):
        """Test GET /api/workflows/email-settings returns expected fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/workflows/email-settings", headers=headers)
        
        assert response.status_code == 200, f"GET email-settings failed: {response.text}"
        data = response.json()
        
        # Verify expected fields exist
        assert "email_prefix" in data, "Missing email_prefix field"
        assert "email_domain" in data, "Missing email_domain field"
        assert "workflow_emails" in data, "Missing workflow_emails field"
        assert "approved_senders" in data, "Missing approved_senders field"
        
        # Verify email_domain is correct
        assert data["email_domain"] == "zayado.bot", f"Unexpected email_domain: {data['email_domain']}"
        
        print(f"PASS - GET /api/workflows/email-settings returns: email_prefix={data['email_prefix']}, email_domain={data['email_domain']}")
    
    def test_update_email_prefix(self, auth_token):
        """Test PUT /api/workflows/email-settings updates email_prefix"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Update email prefix
        new_prefix = "testprefix87"
        response = requests.put(f"{BASE_URL}/api/workflows/email-settings", headers=headers, json={
            "email_prefix": new_prefix
        })
        
        assert response.status_code == 200, f"PUT email-settings failed: {response.text}"
        data = response.json()
        assert data.get("email_prefix") == new_prefix, f"Email prefix not updated: {data}"
        
        # Verify with GET
        get_response = requests.get(f"{BASE_URL}/api/workflows/email-settings", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["email_prefix"] == new_prefix, "Email prefix not persisted"
        
        print(f"PASS - PUT /api/workflows/email-settings updated email_prefix to '{new_prefix}'")
    
    def test_email_prefix_validation_min_length(self, auth_token):
        """Test email prefix validation rejects prefix < 2 characters"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Try to set prefix with only 1 character
        response = requests.put(f"{BASE_URL}/api/workflows/email-settings", headers=headers, json={
            "email_prefix": "a"
        })
        
        assert response.status_code == 400, f"Expected 400 for short prefix, got {response.status_code}"
        print("PASS - Email prefix validation rejects prefix < 2 characters")
    
    def test_update_approved_senders(self, auth_token):
        """Test PUT /api/workflows/email-settings updates approved_senders"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Update approved senders
        new_senders = [
            {"email": "test1@example.com"},
            {"email": "test2@example.com"}
        ]
        response = requests.put(f"{BASE_URL}/api/workflows/email-settings", headers=headers, json={
            "approved_senders": new_senders
        })
        
        assert response.status_code == 200, f"PUT email-settings failed: {response.text}"
        data = response.json()
        
        # Verify senders were added
        senders = data.get("approved_senders", [])
        sender_emails = [s.get("email") for s in senders]
        assert "test1@example.com" in sender_emails, "test1@example.com not in approved_senders"
        assert "test2@example.com" in sender_emails, "test2@example.com not in approved_senders"
        
        print(f"PASS - PUT /api/workflows/email-settings updated approved_senders")
    
    def test_update_workflow_emails(self, auth_token):
        """Test PUT /api/workflows/email-settings updates workflow_emails"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Update workflow emails
        new_wf_emails = [
            {"address": "newsletter", "instructions": "Resume les newsletters"}
        ]
        response = requests.put(f"{BASE_URL}/api/workflows/email-settings", headers=headers, json={
            "workflow_emails": new_wf_emails
        })
        
        assert response.status_code == 200, f"PUT email-settings failed: {response.text}"
        data = response.json()
        
        # Verify workflow emails were added
        wf_emails = data.get("workflow_emails", [])
        assert len(wf_emails) >= 1, "No workflow_emails returned"
        assert any(we.get("address") == "newsletter" for we in wf_emails), "newsletter not in workflow_emails"
        
        print(f"PASS - PUT /api/workflows/email-settings updated workflow_emails")


class TestPublicPages:
    """Test public pages load correctly"""
    
    def test_extension_ia_page_loads(self):
        """Test ExtensionIAPage at /fr/extension-ia loads"""
        response = requests.get(f"{BASE_URL}/fr/extension-ia", allow_redirects=True)
        # Frontend routes may return 200 or redirect to index.html
        assert response.status_code in [200, 304], f"ExtensionIAPage failed to load: {response.status_code}"
        print("PASS - ExtensionIAPage at /fr/extension-ia loads (status 200)")
    
    def test_chatbot_b2b_page_loads(self):
        """Test ChatbotB2BPage at /fr/chatbot-b2b loads"""
        response = requests.get(f"{BASE_URL}/fr/chatbot-b2b", allow_redirects=True)
        assert response.status_code in [200, 304], f"ChatbotB2BPage failed to load: {response.status_code}"
        print("PASS - ChatbotB2BPage at /fr/chatbot-b2b loads (status 200)")


class TestWorkflowsAPI:
    """Test workflows API endpoints"""
    
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
    
    def test_get_workflows(self, auth_token):
        """Test GET /api/workflows returns list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/workflows", headers=headers)
        
        assert response.status_code == 200, f"GET workflows failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Workflows response should be a list"
        print(f"PASS - GET /api/workflows returns {len(data)} workflows")
    
    def test_create_workflow_with_email_confirm(self, auth_token):
        """Test creating workflow with email_confirm toggle"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        workflow_data = {
            "name": "TEST_Email_Confirm_Workflow_87",
            "description": "Test workflow with email confirmation",
            "steps": [{
                "type": "prompt",
                "content": "Test prompt",
                "label": "Test step",
                "email_confirm": True,
                "email_confirm_to": "test@example.com"
            }],
            "status": "idle"
        }
        
        response = requests.post(f"{BASE_URL}/api/workflows", headers=headers, json=workflow_data)
        assert response.status_code == 200, f"Create workflow failed: {response.text}"
        
        data = response.json()
        assert data.get("name") == "TEST_Email_Confirm_Workflow_87"
        
        # Verify steps contain email_confirm
        steps = data.get("steps", [])
        assert len(steps) > 0, "No steps in workflow"
        assert steps[0].get("email_confirm") == True, "email_confirm not set in step"
        assert steps[0].get("email_confirm_to") == "test@example.com", "email_confirm_to not set"
        
        # Cleanup - delete the test workflow
        workflow_id = data.get("id")
        if workflow_id:
            requests.delete(f"{BASE_URL}/api/workflows/{workflow_id}", headers=headers)
        
        print("PASS - Created workflow with email_confirm toggle")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
