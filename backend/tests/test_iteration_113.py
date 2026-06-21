"""
Iteration 113 - Delete Account Modal & Admin Affiliation Tests
Tests for:
1. DELETE MODAL: GET /api/auth/pre-delete-info - returns conversations, projects, workflows counts
2. DELETE MODAL: DELETE /api/auth/delete-account - accepts reason in body
3. ADMIN AFFILIATION: POST /api/affiliate/admin/create - promotes existing user or creates new
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("PASS: Health endpoint accessible")
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"PASS: Admin login successful, role: {data['user'].get('role')}")
        return data["access_token"]


class TestPreDeleteInfo:
    """Tests for GET /api/auth/pre-delete-info endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_pre_delete_info_returns_counts(self, admin_token):
        """Test pre-delete-info returns conversation, project, workflow counts"""
        response = requests.get(
            f"{BASE_URL}/api/auth/pre-delete-info",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields exist
        assert "conversations" in data, "Missing conversations count"
        assert "projects" in data, "Missing projects count"
        assert "workflows" in data, "Missing workflows count"
        assert "plan" in data, "Missing plan field"
        assert "credits" in data, "Missing credits field"
        
        # Verify retention offer fields
        assert "retention_code" in data, "Missing retention_code"
        assert "retention_discount" in data, "Missing retention_discount"
        assert data["retention_code"] == "RESTE30", f"Expected RESTE30, got {data['retention_code']}"
        assert data["retention_discount"] == 30, f"Expected 30, got {data['retention_discount']}"
        
        print(f"PASS: pre-delete-info returns: conversations={data['conversations']}, projects={data['projects']}, workflows={data['workflows']}")
        print(f"PASS: Retention offer: code={data['retention_code']}, discount={data['retention_discount']}%")
    
    def test_pre_delete_info_requires_auth(self):
        """Test pre-delete-info requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/pre-delete-info")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: pre-delete-info requires authentication")
    
    def test_pre_delete_info_cloud_status(self, admin_token):
        """Test pre-delete-info returns cloud connection status"""
        response = requests.get(
            f"{BASE_URL}/api/auth/pre-delete-info",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Cloud connection fields should exist (may be false)
        assert "gdrive_connected" in data, "Missing gdrive_connected field"
        assert "onedrive_connected" in data, "Missing onedrive_connected field"
        print(f"PASS: Cloud status: gdrive={data['gdrive_connected']}, onedrive={data['onedrive_connected']}")


class TestDeleteAccountEndpoint:
    """Tests for DELETE /api/auth/delete-account endpoint"""
    
    @pytest.fixture
    def test_user_token(self):
        """Create a test user and return token"""
        test_email = f"test_delete_{uuid.uuid4().hex[:8]}@test.com"
        # Register test user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "name": "Test Delete User",
            "password": "testpass123"
        })
        if response.status_code == 200:
            return response.json().get("access_token"), test_email
        pytest.skip("Could not create test user")
    
    def test_delete_account_accepts_reason(self, test_user_token):
        """Test delete-account accepts reason in body"""
        token, email = test_user_token
        
        # Delete with reason
        response = requests.delete(
            f"{BASE_URL}/api/auth/delete-account",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"reason": "trop_cher"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"PASS: Account deleted with reason, email: {email}")
    
    def test_delete_account_requires_auth(self):
        """Test delete-account requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/auth/delete-account")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: delete-account requires authentication")


class TestAdminAffiliateCreate:
    """Tests for POST /api/affiliate/admin/create endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_admin_create_affiliate_requires_admin(self):
        """Test admin/create requires admin role"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate/admin/create",
            json={"email": "test@test.com"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: admin/create requires admin authentication")
    
    def test_admin_create_affiliate_requires_email(self, admin_token):
        """Test admin/create requires email"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate/admin/create",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={}
        )
        assert response.status_code == 400
        print("PASS: admin/create requires email")
    
    def test_admin_create_new_affiliate(self, admin_token):
        """Test admin/create creates new user with temp password"""
        test_email = f"test_affiliate_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/affiliate/admin/create",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "email": test_email,
                "name": "Test Affiliate",
                "role": "partenaire",
                "tier_override": "silver"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return created status with temp password
        assert data.get("status") == "created", f"Expected 'created', got {data.get('status')}"
        assert "temp_password" in data, "Missing temp_password for new user"
        assert "referral_code" in data, "Missing referral_code"
        assert "promo_code" in data, "Missing promo_code"
        assert data.get("role") == "partenaire"
        
        print(f"PASS: New affiliate created: {test_email}")
        print(f"  - temp_password: {data.get('temp_password')}")
        print(f"  - referral_code: {data.get('referral_code')}")
        print(f"  - promo_code: {data.get('promo_code')}")
        print(f"  - tier_override: {data.get('tier_override')}")
    
    def test_admin_promote_existing_user(self, admin_token):
        """Test admin/create promotes existing user"""
        # First create a regular user
        test_email = f"test_promote_{uuid.uuid4().hex[:8]}@test.com"
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "name": "Test Promote User",
            "password": "testpass123"
        })
        if reg_response.status_code != 200:
            pytest.skip("Could not create test user for promotion")
        
        # Now promote to affiliate
        response = requests.post(
            f"{BASE_URL}/api/affiliate/admin/create",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "email": test_email,
                "role": "partenaire",
                "tier_override": "gold"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return promoted status (no temp password)
        assert data.get("status") == "promoted", f"Expected 'promoted', got {data.get('status')}"
        assert "temp_password" not in data or data.get("temp_password") is None, "Should not have temp_password for existing user"
        assert data.get("role") == "partenaire"
        
        print(f"PASS: Existing user promoted: {test_email}")
        print(f"  - status: {data.get('status')}")
        print(f"  - role: {data.get('role')}")
        print(f"  - tier_override: {data.get('tier_override')}")


class TestAdminAffiliateList:
    """Tests for GET /api/affiliate/admin/affiliates endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_admin_list_affiliates(self, admin_token):
        """Test admin can list affiliates"""
        response = requests.get(
            f"{BASE_URL}/api/affiliate/admin/affiliates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Admin can list affiliates, count: {len(data)}")
        
        # If there are affiliates, verify structure
        if len(data) > 0:
            affiliate = data[0]
            assert "id" in affiliate
            assert "email" in affiliate
            assert "tier" in affiliate
            print(f"  - First affiliate: {affiliate.get('email')}, tier: {affiliate.get('tier', {}).get('id', 'unknown')}")


class TestAdminUserSearch:
    """Tests for admin user search (used in affiliation flow)"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_admin_search_users(self, admin_token):
        """Test admin can search users by email"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users?search=admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Response could be list or dict with users key
        users = data.get("users", data) if isinstance(data, dict) else data
        assert isinstance(users, list)
        print(f"PASS: Admin can search users, found: {len(users)} matching 'admin'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
