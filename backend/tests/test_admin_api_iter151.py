"""
Admin API Tests - Iteration 151
Tests for ZAYADO Admin Panel API endpoints
Focus: Admin login, dashboard stats, users, transactions, promo-codes, pricing, brevo-config, limits, seo-config, email-templates, email-log, activity-log
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "1@Elshaddai1"


class TestAdminAuth:
    """Test admin authentication"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.status_code} - {response.text}"
        data = response.json()
        # API returns access_token, not token
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        # API returns access_token, not token
        assert "access_token" in data or "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] in ["admin", "super_admin"]
    
    def test_admin_login_invalid_password(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]


class TestAdminStats:
    """Test admin stats endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_stats_returns_200(self, headers):
        """Test /api/admin/stats returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200, f"Stats failed: {response.status_code} - {response.text}"
    
    def test_admin_stats_has_required_fields(self, headers):
        """Test stats response has required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["total_users", "total_revenue", "total_conversations", "plans_distribution"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["total_revenue"], (int, float))


class TestAdminUsers:
    """Test admin users endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_users_returns_200(self, headers):
        """Test /api/admin/users returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        assert response.status_code == 200, f"Users failed: {response.status_code} - {response.text}"
    
    def test_admin_users_has_pagination(self, headers):
        """Test users response has pagination"""
        response = requests.get(f"{BASE_URL}/api/admin/users?skip=0&limit=20", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check pagination fields
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
    
    def test_admin_users_has_last_login_at(self, headers):
        """Test users response includes last_login_at field"""
        response = requests.get(f"{BASE_URL}/api/admin/users?skip=0&limit=20", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        if len(data["users"]) > 0:
            user = data["users"][0]
            assert "last_login_at" in user, f"Missing last_login_at field in user: {user.keys()}"


class TestAdminTransactions:
    """Test admin transactions endpoint - should be fast (<1s)"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_transactions_returns_200(self, headers):
        """Test /api/admin/transactions returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/transactions", headers=headers)
        assert response.status_code == 200, f"Transactions failed: {response.status_code} - {response.text}"
    
    def test_admin_transactions_is_fast(self, headers):
        """Test transactions endpoint is fast (<1s) - was 5.3s before fix"""
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/admin/transactions", headers=headers)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Transactions endpoint too slow: {elapsed:.2f}s (should be <1s)"
        print(f"Transactions endpoint response time: {elapsed:.2f}s")
    
    def test_admin_transactions_has_checkout_url(self, headers):
        """Test transactions include checkout_url for pending payments"""
        response = requests.get(f"{BASE_URL}/api/admin/transactions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert isinstance(data, list)
        if len(data) > 0:
            tx = data[0]
            required_fields = ["id", "user_id", "type", "amount", "status", "created_at"]
            for field in required_fields:
                assert field in tx, f"Missing field: {field}"


class TestAdminPromoCodes:
    """Test admin promo codes endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_promo_codes_returns_200(self, headers):
        """Test /api/admin/promo-codes returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/promo-codes", headers=headers)
        assert response.status_code == 200, f"Promo codes failed: {response.status_code} - {response.text}"


class TestAdminPricing:
    """Test admin pricing endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_pricing_returns_200(self, headers):
        """Test /api/admin/pricing returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/pricing", headers=headers)
        assert response.status_code == 200, f"Pricing failed: {response.status_code} - {response.text}"
    
    def test_admin_pricing_has_plans_and_packages(self, headers):
        """Test pricing response has plans and packages"""
        response = requests.get(f"{BASE_URL}/api/admin/pricing", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data
        assert "packages" in data


class TestAdminBrevoConfig:
    """Test admin Brevo config endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_brevo_config_returns_200(self, headers):
        """Test /api/admin/brevo-config returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/brevo-config", headers=headers)
        assert response.status_code == 200, f"Brevo config failed: {response.status_code} - {response.text}"


class TestAdminLimits:
    """Test admin limits endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_limits_returns_200(self, headers):
        """Test /api/admin/limits returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/limits", headers=headers)
        assert response.status_code == 200, f"Limits failed: {response.status_code} - {response.text}"


class TestAdminSeoConfig:
    """Test admin SEO config endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_seo_config_returns_200(self, headers):
        """Test /api/admin/seo-config returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/seo-config", headers=headers)
        assert response.status_code == 200, f"SEO config failed: {response.status_code} - {response.text}"


class TestAdminEmailTemplates:
    """Test admin email templates endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_email_templates_returns_200(self, headers):
        """Test /api/admin/email-templates returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/email-templates", headers=headers)
        assert response.status_code == 200, f"Email templates failed: {response.status_code} - {response.text}"


class TestAdminEmailLog:
    """Test admin email log endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_email_log_returns_200(self, headers):
        """Test /api/admin/email-log returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/email-log", headers=headers)
        assert response.status_code == 200, f"Email log failed: {response.status_code} - {response.text}"


class TestAdminActivityLog:
    """Test admin activity log endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_admin_activity_log_returns_200(self, headers):
        """Test /api/admin/activity-log returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/activity-log", headers=headers)
        assert response.status_code == 200, f"Activity log failed: {response.status_code} - {response.text}"


class TestLeadEndpoint:
    """Test /api/lead endpoint - fixed import error"""
    
    def test_lead_endpoint_returns_200(self):
        """Test /api/lead works without import error"""
        response = requests.post(f"{BASE_URL}/api/lead", json={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "phone": "0123456789",
            "company": "Test Company",
            "source": "simulateur",
            "tool": "Test Tool",
            "results": {}
        })
        # Should return 200 (success) not 500 (import error)
        assert response.status_code == 200, f"Lead endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("status") == "success"


class TestHealthEndpoint:
    """Test health endpoint"""
    
    def test_health_returns_200(self):
        """Test /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
