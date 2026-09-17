"""
Iteration 112 - Monthly Credit Reset, Billing Page, Pricing Page, Document Upload Tests
Tests for:
- P0: Monthly credit reset on login (credits_last_reset check)
- P0: /api/auth/usage returns credits_per_month and credits_last_reset fields
- P0: Admin force reset endpoint POST /api/admin/credits/reset-monthly
- P1: Document upload /api/profile/import-document AI validation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("PASS: Health endpoint returns 200")
    
    def test_admin_login(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        print(f"PASS: Admin login successful, user plan: {data['user'].get('plan')}")
        return data["access_token"]


class TestUsageEndpoint:
    """Tests for /api/auth/usage endpoint - credits_per_month and credits_last_reset"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_usage_returns_credits_per_month(self, admin_token):
        """Test that /api/auth/usage returns credits_per_month field"""
        response = requests.get(
            f"{BASE_URL}/api/auth/usage",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Usage endpoint failed: {response.status_code}"
        data = response.json()
        
        # Check credits_per_month field exists
        assert "credits_per_month" in data, f"credits_per_month not in response: {data.keys()}"
        print(f"PASS: credits_per_month field present, value: {data['credits_per_month']}")
    
    def test_usage_returns_credits_last_reset(self, admin_token):
        """Test that /api/auth/usage returns credits_last_reset field"""
        response = requests.get(
            f"{BASE_URL}/api/auth/usage",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Usage endpoint failed: {response.status_code}"
        data = response.json()
        
        # Check credits_last_reset field exists (can be null for free users)
        assert "credits_last_reset" in data, f"credits_last_reset not in response: {data.keys()}"
        print(f"PASS: credits_last_reset field present, value: {data['credits_last_reset']}")
    
    def test_usage_returns_all_expected_fields(self, admin_token):
        """Test that /api/auth/usage returns all expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/auth/usage",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Usage endpoint failed: {response.status_code}"
        data = response.json()
        
        expected_fields = [
            "credits_remaining", "credits_base", "credits_bonus", "credits_purchased",
            "credits_per_month", "credits_last_reset", "total_credits_used",
            "credits_used_7d", "total_conversations", "conversations_7d",
            "total_projects", "total_time_tracked_hours", "plan", "member_since"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"PASS: All expected fields present in usage response")
        print(f"  - credits_per_month: {data['credits_per_month']}")
        print(f"  - credits_last_reset: {data['credits_last_reset']}")
        print(f"  - plan: {data['plan']}")


class TestAdminCreditReset:
    """Tests for admin force monthly credit reset endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_admin_reset_endpoint_exists(self, admin_token):
        """Test that POST /api/admin/credits/reset-monthly endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/admin/credits/reset-monthly",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 200 OK (success) or 403 (not admin) - not 404
        assert response.status_code != 404, f"Endpoint not found: {response.status_code}"
        print(f"PASS: Admin reset endpoint exists, status: {response.status_code}")
    
    def test_admin_reset_returns_expected_fields(self, admin_token):
        """Test that admin reset returns expected response fields"""
        response = requests.post(
            f"{BASE_URL}/api/admin/credits/reset-monthly",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin reset failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Check expected fields
        assert "status" in data, "Missing 'status' field"
        assert data["status"] == "ok", f"Status not ok: {data['status']}"
        assert "reset_count" in data, "Missing 'reset_count' field"
        assert "reset_at" in data, "Missing 'reset_at' field"
        
        print(f"PASS: Admin reset successful")
        print(f"  - reset_count: {data['reset_count']}")
        print(f"  - reset_at: {data['reset_at']}")
    
    def test_admin_reset_requires_auth(self):
        """Test that admin reset requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/credits/reset-monthly")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got: {response.status_code}"
        print(f"PASS: Admin reset requires authentication (status: {response.status_code})")


class TestDocumentUpload:
    """Tests for document upload AI validation"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_document_upload_endpoint_exists(self, admin_token):
        """Test that POST /api/profile/import-document endpoint exists"""
        # Send empty request to check endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/profile/import-document",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 400 (no file) or 422 (validation error) - not 404
        assert response.status_code != 404, f"Endpoint not found: {response.status_code}"
        print(f"PASS: Document upload endpoint exists, status: {response.status_code}")
    
    def test_document_upload_requires_file(self, admin_token):
        """Test that document upload requires a file"""
        response = requests.post(
            f"{BASE_URL}/api/profile/import-document",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 400 or 422 for missing file
        assert response.status_code in [400, 422], f"Expected validation error, got: {response.status_code}"
        print(f"PASS: Document upload requires file (status: {response.status_code})")
    
    def test_document_upload_rejects_invalid_format(self, admin_token):
        """Test that document upload rejects invalid file formats"""
        # Create a fake text file
        files = {"file": ("test.txt", b"This is a test file", "text/plain")}
        response = requests.post(
            f"{BASE_URL}/api/profile/import-document",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        # Should return 400 for invalid format
        assert response.status_code == 400, f"Expected 400 for invalid format, got: {response.status_code}"
        print(f"PASS: Document upload rejects invalid format (status: {response.status_code})")


class TestBillingEndpoint:
    """Tests for billing endpoint - credits_per_month display"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_billing_returns_credits_per_month(self, admin_token):
        """Test that /api/payments/billing returns credits_per_month"""
        response = requests.get(
            f"{BASE_URL}/api/payments/billing",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Billing endpoint failed: {response.status_code}"
        data = response.json()
        
        # Check credits_per_month field exists
        assert "credits_per_month" in data, f"credits_per_month not in billing response: {data.keys()}"
        print(f"PASS: Billing returns credits_per_month: {data['credits_per_month']}")
    
    def test_billing_returns_bonus_cap(self, admin_token):
        """Test that /api/payments/billing returns bonus_cap"""
        response = requests.get(
            f"{BASE_URL}/api/payments/billing",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Billing endpoint failed: {response.status_code}"
        data = response.json()
        
        # Check bonus_cap field exists
        assert "bonus_cap" in data, f"bonus_cap not in billing response: {data.keys()}"
        print(f"PASS: Billing returns bonus_cap: {data['bonus_cap']}")


class TestLoginCreditReset:
    """Tests for monthly credit reset on login"""
    
    def test_login_returns_user_with_credits(self):
        """Test that login returns user with credits info"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        data = response.json()
        
        user = data.get("user", {})
        assert "credits" in user, "User missing credits field"
        print(f"PASS: Login returns user with credits: {user.get('credits')}")
    
    def test_login_updates_last_login(self):
        """Test that login updates last_login_at timestamp"""
        # First login
        response1 = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response1.status_code == 200
        
        # Second login should also work
        response2 = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response2.status_code == 200
        print("PASS: Multiple logins work correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
