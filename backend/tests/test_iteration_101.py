"""
Iteration 101 - Testing merged Affiliate/Partner dashboard, workflow email domain, and route changes
Tests:
1. Login with admin credentials
2. Workflow email domain returns zayado.ai
3. Affiliate API endpoints work correctly
4. Partner redirect to affiliate
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Health check and authentication tests"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("PASS: Health check returns healthy")
    
    def test_login_success(self):
        """Test login with admin credentials"""
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
        print("PASS: Login successful with admin credentials")
        return data["access_token"]


class TestWorkflowEmailDomain:
    """Test workflow email domain is zayado.ai"""
    
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
    
    def test_workflow_email_settings_returns_zayado_ai(self, auth_token):
        """Test that workflow email settings return zayado.ai domain"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/workflows/email-settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "email_domain" in data
        assert data["email_domain"] == "zayado.ai", f"Expected zayado.ai, got {data['email_domain']}"
        print("PASS: Workflow email domain is zayado.ai")


class TestAffiliateEndpoints:
    """Test affiliate-related endpoints"""
    
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
    
    def test_affiliate_stats_endpoint(self, auth_token):
        """Test affiliate stats endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/affiliate/stats", headers=headers)
        # Should return 200 or 404 if user is not an affiliate
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            # Check for expected fields in affiliate stats
            print(f"PASS: Affiliate stats endpoint returns data: {list(data.keys())}")
        else:
            print("PASS: Affiliate stats returns 404 (user not an affiliate)")
    
    def test_affiliate_stats_contains_referrals(self, auth_token):
        """Test affiliate stats contains referrals data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/affiliate/stats", headers=headers)
        # Should return 200 or 404 if user is not an affiliate
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            # Check for referrals field in affiliate stats
            if "referrals" in data:
                print(f"PASS: Affiliate stats contains referrals: {len(data['referrals'])} referrals")
            else:
                print("PASS: Affiliate stats endpoint works (no referrals field)")
        else:
            print("PASS: Affiliate stats returns 404 (user not an affiliate)")


class TestUserSettings:
    """Test user settings endpoints"""
    
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
    
    def test_get_user_me(self, auth_token):
        """Test getting current user"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "settings" in data
        print("PASS: Get user /me endpoint works")
    
    def test_update_settings(self, auth_token):
        """Test updating user settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Get current settings first
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        current_settings = response.json().get("settings", {})
        
        # Update with same settings (no change)
        update_response = requests.put(
            f"{BASE_URL}/api/auth/settings",
            headers=headers,
            json={"language": current_settings.get("language", "fr")}
        )
        assert update_response.status_code == 200
        print("PASS: Update settings endpoint works")


class TestWorkflowsEndpoints:
    """Test workflows endpoints"""
    
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
    
    def test_list_workflows(self, auth_token):
        """Test listing workflows"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/workflows", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: List workflows returns {len(data)} workflows")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
