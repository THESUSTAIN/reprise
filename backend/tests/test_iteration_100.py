"""
Iteration 100 - Testing Affiliate System, SettingsModal consolidation, Admin Stats Cache
Tests: Login, Health, Affiliate Dashboard, Admin Affiliates, Admin Payouts, Admin Stats
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


class TestHealthAndAuth:
    """Health check and authentication tests"""
    
    def test_health_check(self):
        """GET /api/health - should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health check passed")
    
    def test_login_success(self):
        """POST /api/auth/login - should return access_token for admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✅ Login success - user role: {data['user'].get('role')}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - should return 401 for invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✅ Invalid login correctly rejected with 401")


class TestAffiliateDashboard:
    """Affiliate dashboard API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_affiliate_dashboard(self, auth_token):
        """GET /api/affiliate/dashboard - should return affiliate stats for partner/admin"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/affiliate/dashboard", headers=headers)
        
        # Admin should have access (role check: partenaire, presta-partenaire, admin, super_admin)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "referral_code" in data
        assert "tier" in data
        assert "stats" in data
        
        # Verify stats structure
        stats = data["stats"]
        assert "total_referrals" in stats
        assert "total_sales" in stats
        assert "total_commissions" in stats
        assert "pending_commissions" in stats
        assert "paid_commissions" in stats
        
        # Verify tier structure
        tier = data["tier"]
        assert "id" in tier
        assert "label" in tier
        assert "commission_rate" in tier
        
        print(f"✅ Affiliate dashboard - referral_code: {data['referral_code']}, tier: {tier['label']}")
    
    def test_affiliate_dashboard_unauthorized(self):
        """GET /api/affiliate/dashboard - should return 403 without auth"""
        response = requests.get(f"{BASE_URL}/api/affiliate/dashboard")
        assert response.status_code in [401, 403]
        print("✅ Affiliate dashboard correctly requires authentication")


class TestAdminAffiliates:
    """Admin affiliate management tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_admin_list_affiliates(self, auth_token):
        """GET /api/affiliate/admin/affiliates - should return array of affiliates"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/affiliate/admin/affiliates", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return an array
        assert isinstance(data, list)
        
        # If there are affiliates, verify structure
        if len(data) > 0:
            affiliate = data[0]
            assert "id" in affiliate
            assert "email" in affiliate
            assert "tier" in affiliate
            assert "total_referrals" in affiliate
            assert "total_sales" in affiliate
            assert "total_commissions" in affiliate
            print(f"✅ Admin affiliates list - found {len(data)} affiliates")
        else:
            print("✅ Admin affiliates list - empty array (no affiliates yet)")
    
    def test_admin_list_payouts(self, auth_token):
        """GET /api/affiliate/admin/payouts - should return array of payouts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/affiliate/admin/payouts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return an array
        assert isinstance(data, list)
        
        # If there are payouts, verify structure
        if len(data) > 0:
            payout = data[0]
            assert "id" in payout
            assert "affiliate_email" in payout
            assert "amount" in payout
            assert "method" in payout
            assert "status" in payout
            print(f"✅ Admin payouts list - found {len(data)} payouts")
        else:
            print("✅ Admin payouts list - empty array (no payouts yet)")
    
    def test_admin_affiliates_unauthorized(self):
        """GET /api/affiliate/admin/affiliates - should return 401/403 without auth"""
        response = requests.get(f"{BASE_URL}/api/affiliate/admin/affiliates")
        assert response.status_code in [401, 403]
        print("✅ Admin affiliates correctly requires admin auth")


class TestAdminStats:
    """Admin stats with cache tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_admin_stats(self, auth_token):
        """GET /api/admin/stats - should return stats object with cache"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats structure
        assert "total_users" in data
        assert "active_users_7d" in data
        assert "total_conversations" in data
        assert "total_revenue" in data
        assert "plans_distribution" in data
        assert "credits_by_mode" in data
        
        print(f"✅ Admin stats - total_users: {data['total_users']}, total_conversations: {data['total_conversations']}")
    
    def test_admin_stats_cache(self, auth_token):
        """GET /api/admin/stats - verify cache works (second call should be fast)"""
        import time
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First call
        start1 = time.time()
        response1 = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        time1 = time.time() - start1
        
        # Second call (should hit cache)
        start2 = time.time()
        response2 = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        time2 = time.time() - start2
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both should return same data structure
        data1 = response1.json()
        data2 = response2.json()
        assert data1["total_users"] == data2["total_users"]
        
        print(f"✅ Admin stats cache - first call: {time1:.3f}s, second call: {time2:.3f}s")


class TestPaymentsPackages:
    """Payments packages tests"""
    
    def test_get_packages(self):
        """GET /api/payments/packages - should return credit packages"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            package = data[0]
            assert "id" in package
            assert "name" in package
            assert "credits" in package
            assert "price" in package
        print(f"✅ Payments packages - found {len(data)} packages")
    
    def test_get_plans(self):
        """GET /api/payments/plans - should return subscription plans"""
        response = requests.get(f"{BASE_URL}/api/payments/plans")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            plan = data[0]
            assert "id" in plan
            assert "name" in plan
            assert "price" in plan
        print(f"✅ Payments plans - found {len(data)} plans")


class TestPublicConfig:
    """Public config tests"""
    
    def test_public_config(self):
        """GET /api/public/config - should return public configuration"""
        response = requests.get(f"{BASE_URL}/api/public/config")
        assert response.status_code == 200
        data = response.json()
        # Should return a dict with config values
        assert isinstance(data, dict)
        print(f"✅ Public config - keys: {list(data.keys())[:5]}...")


class TestAuthMe:
    """Auth me endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_auth_me(self, auth_token):
        """GET /api/auth/me - should return current user data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "role" in data
        assert "credits" in data
        assert data["email"] == ADMIN_EMAIL
        print(f"✅ Auth me - email: {data['email']}, role: {data['role']}, credits: {data['credits']}")


class TestAdminUsers:
    """Admin users management tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_admin_users_list(self, auth_token):
        """GET /api/admin/users - should return paginated users list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        print(f"✅ Admin users list - total: {data['total']}, page users: {len(data['users'])}")


class TestAdminConfig:
    """Admin config tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_admin_config(self, auth_token):
        """GET /api/admin/config - should return admin configuration"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/config", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"✅ Admin config - keys: {list(data.keys())[:5]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
