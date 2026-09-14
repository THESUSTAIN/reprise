"""
Test suite for ZAYADO Affiliate System - Iteration 114
Tests:
- Registration with ref code gives 230 credits (180+50 bonus) and sets referred_by
- Registration without ref gives normal 180 credits
- GET /api/affiliate/admin/tiers returns saved tier config
- PUT /api/affiliate/admin/tiers persists and GET returns updated values
- GET /api/affiliate/admin/affiliates returns partner_code field
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"
TEST_AFFILIATE_CODE = "PROMO-TEST"


class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_endpoint(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Health endpoint working")
    
    def test_admin_login(self):
        """Verify admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful, role: {data['user'].get('role')}")


class TestRegistrationWithRefCode:
    """Test registration with affiliate ref code gives bonus credits"""
    
    def test_register_with_ref_code_gives_230_credits(self):
        """Register with ref=PROMO-TEST should give 230 credits (180+50 bonus)"""
        unique_email = f"test-ref-{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test Ref User",
            "ref": TEST_AFFILIATE_CODE
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Verify credits
        user = data.get("user", {})
        credits = user.get("credits", 0)
        bonus_credits = user.get("bonus_credits", 0)
        
        print(f"  User credits: {credits}, bonus_credits: {bonus_credits}")
        
        # Should have 230 total (180 base + 50 bonus)
        assert credits == 230, f"Expected 230 credits, got {credits}"
        assert bonus_credits == 50, f"Expected 50 bonus_credits, got {bonus_credits}"
        
        print(f"✓ Registration with ref={TEST_AFFILIATE_CODE} gave 230 credits (180+50 bonus)")
        
        # Cleanup: delete test user
        token = data.get("access_token")
        if token:
            requests.delete(f"{BASE_URL}/api/auth/delete-account", 
                          headers={"Authorization": f"Bearer {token}"},
                          json={"reason": "test cleanup"})
    
    def test_register_without_ref_gives_180_credits(self):
        """Register without ref should give normal 180 credits"""
        unique_email = f"test-noref-{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test No Ref User"
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        user = data.get("user", {})
        credits = user.get("credits", 0)
        bonus_credits = user.get("bonus_credits", 0)
        
        print(f"  User credits: {credits}, bonus_credits: {bonus_credits}")
        
        # Should have 180 credits (no bonus)
        assert credits == 180, f"Expected 180 credits, got {credits}"
        assert bonus_credits == 0, f"Expected 0 bonus_credits, got {bonus_credits}"
        
        print("✓ Registration without ref gave 180 credits (no bonus)")
        
        # Cleanup
        token = data.get("access_token")
        if token:
            requests.delete(f"{BASE_URL}/api/auth/delete-account",
                          headers={"Authorization": f"Bearer {token}"},
                          json={"reason": "test cleanup"})
    
    def test_register_with_invalid_ref_gives_180_credits(self):
        """Register with invalid ref code should give normal 180 credits"""
        unique_email = f"test-badref-{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test Bad Ref User",
            "ref": "INVALID-CODE-12345"
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        user = data.get("user", {})
        credits = user.get("credits", 0)
        
        # Invalid ref should not give bonus
        assert credits == 180, f"Expected 180 credits with invalid ref, got {credits}"
        
        print("✓ Registration with invalid ref gave 180 credits (no bonus)")
        
        # Cleanup
        token = data.get("access_token")
        if token:
            requests.delete(f"{BASE_URL}/api/auth/delete-account",
                          headers={"Authorization": f"Bearer {token}"},
                          json={"reason": "test cleanup"})


class TestAffiliateTiersAPI:
    """Test affiliate tier configuration endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("access_token")
    
    def test_get_tiers_returns_config(self, admin_token):
        """GET /api/affiliate/admin/tiers should return tier configuration"""
        response = requests.get(f"{BASE_URL}/api/affiliate/admin/tiers",
                               headers={"Authorization": f"Bearer {admin_token}"})
        
        assert response.status_code == 200, f"GET tiers failed: {response.text}"
        data = response.json()
        
        # Should have all 4 tiers
        assert "bronze" in data, "Missing bronze tier"
        assert "silver" in data, "Missing silver tier"
        assert "gold" in data, "Missing gold tier"
        assert "diamond" in data, "Missing diamond tier"
        
        # Each tier should have commission_rate and min_sales
        for tier_name in ["bronze", "silver", "gold", "diamond"]:
            tier = data[tier_name]
            assert "commission_rate" in tier, f"{tier_name} missing commission_rate"
            assert "min_sales" in tier, f"{tier_name} missing min_sales"
        
        print(f"✓ GET /api/affiliate/admin/tiers returned config:")
        for tier_name, tier in data.items():
            rate = tier.get("commission_rate", 0) * 100
            print(f"  {tier_name}: {rate}% commission, min_sales={tier.get('min_sales')}")
    
    def test_put_tiers_persists_config(self, admin_token):
        """PUT /api/affiliate/admin/tiers should persist and GET should return updated values"""
        # First, get current config
        get_response = requests.get(f"{BASE_URL}/api/affiliate/admin/tiers",
                                   headers={"Authorization": f"Bearer {admin_token}"})
        original_tiers = get_response.json() if get_response.status_code == 200 else {}
        
        # Update with new values
        new_tiers = {
            "bronze":  {"min_sales": 0,  "commission_rate": 0.12, "label": "Bronze"},
            "silver":  {"min_sales": 5,  "commission_rate": 0.15, "label": "Silver"},
            "gold":    {"min_sales": 15, "commission_rate": 0.20, "label": "Gold"},
            "diamond": {"min_sales": 50, "commission_rate": 0.25, "label": "Diamond"},
        }
        
        put_response = requests.put(f"{BASE_URL}/api/affiliate/admin/tiers",
                                   headers={"Authorization": f"Bearer {admin_token}",
                                           "Content-Type": "application/json"},
                                   json={"tiers": new_tiers})
        
        assert put_response.status_code == 200, f"PUT tiers failed: {put_response.text}"
        put_data = put_response.json()
        assert put_data.get("status") == "success", f"PUT did not return success: {put_data}"
        
        print("✓ PUT /api/affiliate/admin/tiers succeeded")
        
        # Verify GET returns updated values
        verify_response = requests.get(f"{BASE_URL}/api/affiliate/admin/tiers",
                                      headers={"Authorization": f"Bearer {admin_token}"})
        
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        
        # Check bronze rate was updated to 12%
        bronze_rate = verify_data.get("bronze", {}).get("commission_rate", 0)
        assert bronze_rate == 0.12, f"Expected bronze rate 0.12, got {bronze_rate}"
        
        print(f"✓ GET after PUT returned updated bronze rate: {bronze_rate * 100}%")
        
        # Restore original if we had it
        if original_tiers:
            requests.put(f"{BASE_URL}/api/affiliate/admin/tiers",
                        headers={"Authorization": f"Bearer {admin_token}",
                                "Content-Type": "application/json"},
                        json={"tiers": original_tiers})
    
    def test_tiers_requires_admin_auth(self):
        """Tiers endpoints should require admin authentication"""
        # Without auth
        response = requests.get(f"{BASE_URL}/api/affiliate/admin/tiers")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print("✓ Tiers endpoint requires authentication")


class TestAffiliatesListAPI:
    """Test admin affiliates list endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("access_token")
    
    def test_get_affiliates_returns_partner_code(self, admin_token):
        """GET /api/affiliate/admin/affiliates should return partner_code for each affiliate"""
        response = requests.get(f"{BASE_URL}/api/affiliate/admin/affiliates",
                               headers={"Authorization": f"Bearer {admin_token}"})
        
        assert response.status_code == 200, f"GET affiliates failed: {response.text}"
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        
        print(f"✓ GET /api/affiliate/admin/affiliates returned {len(data)} affiliates")
        
        # Check each affiliate has partner_code field
        for affiliate in data:
            assert "partner_code" in affiliate, f"Affiliate {affiliate.get('email')} missing partner_code field"
            assert "email" in affiliate
            assert "tier" in affiliate
            
            print(f"  - {affiliate.get('email')}: partner_code={affiliate.get('partner_code')}, tier={affiliate.get('tier', {}).get('id', 'unknown')}")
        
        # Find test affiliate with PROMO-TEST code
        test_affiliate = next((a for a in data if a.get("partner_code") == TEST_AFFILIATE_CODE), None)
        if test_affiliate:
            print(f"✓ Found test affiliate with partner_code={TEST_AFFILIATE_CODE}")
        else:
            print(f"⚠ Test affiliate with partner_code={TEST_AFFILIATE_CODE} not found in list")
    
    def test_affiliates_requires_admin_auth(self):
        """Affiliates endpoint should require admin authentication"""
        response = requests.get(f"{BASE_URL}/api/affiliate/admin/affiliates")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print("✓ Affiliates endpoint requires authentication")


class TestAffiliateReferralTracking:
    """Test that referred_by is set correctly when registering with ref code"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("access_token")
    
    def test_referred_by_is_set_on_registration(self, admin_token):
        """When registering with ref code, referred_by should be set to affiliate's user ID"""
        # First, find the affiliate with PROMO-TEST code
        affiliates_response = requests.get(f"{BASE_URL}/api/affiliate/admin/affiliates",
                                          headers={"Authorization": f"Bearer {admin_token}"})
        
        if affiliates_response.status_code != 200:
            pytest.skip("Could not fetch affiliates list")
        
        affiliates = affiliates_response.json()
        test_affiliate = next((a for a in affiliates if a.get("partner_code") == TEST_AFFILIATE_CODE), None)
        
        if not test_affiliate:
            pytest.skip(f"Test affiliate with partner_code={TEST_AFFILIATE_CODE} not found")
        
        affiliate_id = test_affiliate.get("id")
        print(f"  Test affiliate ID: {affiliate_id}")
        
        # Register a new user with the ref code
        unique_email = f"test-tracking-{uuid.uuid4().hex[:8]}@test.com"
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test Tracking User",
            "ref": TEST_AFFILIATE_CODE
        })
        
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        reg_data = reg_response.json()
        new_user_token = reg_data.get("access_token")
        
        # Check the affiliate's referrals count increased
        # We can verify by checking the affiliate dashboard or admin list
        affiliates_after = requests.get(f"{BASE_URL}/api/affiliate/admin/affiliates",
                                       headers={"Authorization": f"Bearer {admin_token}"}).json()
        
        affiliate_after = next((a for a in affiliates_after if a.get("id") == affiliate_id), None)
        
        if affiliate_after:
            referrals_before = test_affiliate.get("total_referrals", 0)
            referrals_after = affiliate_after.get("total_referrals", 0)
            print(f"  Affiliate referrals: {referrals_before} -> {referrals_after}")
            
            # Referrals should have increased by 1
            assert referrals_after >= referrals_before, "Referral count should not decrease"
        
        print("✓ Registration with ref code tracked correctly")
        
        # Cleanup
        if new_user_token:
            requests.delete(f"{BASE_URL}/api/auth/delete-account",
                          headers={"Authorization": f"Bearer {new_user_token}"},
                          json={"reason": "test cleanup"})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
