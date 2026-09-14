"""
Test Admin Features - Iteration 84
Tests for:
- Admin login
- Admin Dashboard with new API cost/margin metrics
- Admin Users tab with pagination, filters, search
- Admin Credit Logs tab (new)
- Admin Rentabilite/Profitability tab (new)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


class TestAdminAuth:
    """Test admin authentication"""
    
    def test_admin_login_success(self):
        """Test admin can login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["role"] in ["admin", "super_admin"], f"User role is {data['user']['role']}, expected admin"
        print(f"✓ Admin login successful, role: {data['user']['role']}")
        return data["access_token"]


class TestAdminStats:
    """Test /api/admin/stats endpoint with new metrics"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_admin_stats_returns_200(self, auth_token):
        """Test stats endpoint returns 200"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"
        print("✓ Admin stats endpoint returns 200")
    
    def test_admin_stats_has_required_fields(self, auth_token):
        """Test stats has all required fields including new API cost metrics"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Original fields
        required_fields = [
            "total_users", "active_users_7d", "new_users_today", "new_users_7d",
            "total_conversations", "total_revenue", "revenue_30d", "revenue_7d",
            "plans_distribution", "credits_by_mode", "daily_signups",
            "total_credits_in_circulation", "total_credits_spent",
            "conversion_rate", "paid_users"
        ]
        
        # New fields for API costs and margin
        new_fields = ["total_api_cost", "api_cost_30d", "margin_30d"]
        
        for field in required_fields + new_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Stats has all required fields")
        print(f"  - total_users: {data['total_users']}")
        print(f"  - total_api_cost: {data['total_api_cost']} EUR")
        print(f"  - api_cost_30d: {data['api_cost_30d']} EUR")
        print(f"  - margin_30d: {data['margin_30d']} EUR")


class TestAdminUsers:
    """Test /api/admin/users endpoint with pagination, filters, search"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_users_returns_paginated_response(self, auth_token):
        """Test users endpoint returns paginated response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        assert response.status_code == 200, f"Users failed: {response.text}"
        data = response.json()
        
        # Check pagination fields
        assert "users" in data, "Missing users array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        assert "per_page" in data, "Missing per_page"
        assert "total_pages" in data, "Missing total_pages"
        
        print(f"✓ Users endpoint returns paginated response")
        print(f"  - Total users: {data['total']}")
        print(f"  - Page: {data['page']}/{data['total_pages']}")
        print(f"  - Users on page: {len(data['users'])}")
    
    def test_users_pagination_skip_limit(self, auth_token):
        """Test pagination with skip and limit parameters"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get first page
        response1 = requests.get(f"{BASE_URL}/api/admin/users?skip=0&limit=5", headers=headers)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = requests.get(f"{BASE_URL}/api/admin/users?skip=5&limit=5", headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify different pages
        if data1["total"] > 5:
            assert data1["page"] == 1
            assert data2["page"] == 2
            print(f"✓ Pagination works: page 1 has {len(data1['users'])} users, page 2 has {len(data2['users'])} users")
        else:
            print(f"✓ Pagination works (only {data1['total']} users total)")
    
    def test_users_filter_by_plan(self, auth_token):
        """Test filtering users by plan"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users?plan=pro", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # All returned users should have pro plan
        for user in data["users"]:
            assert user["plan"] == "pro", f"User {user['email']} has plan {user['plan']}, expected pro"
        
        print(f"✓ Plan filter works: {len(data['users'])} pro users found")
    
    def test_users_filter_by_role(self, auth_token):
        """Test filtering users by role"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users?role=admin", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # All returned users should have admin role
        for user in data["users"]:
            assert user["role"] in ["admin", "super_admin"], f"User {user['email']} has role {user['role']}"
        
        print(f"✓ Role filter works: {len(data['users'])} admin users found")
    
    def test_users_search(self, auth_token):
        """Test searching users by email/name"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users?search=admin", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Search should return results containing 'admin'
        for user in data["users"]:
            assert "admin" in user["email"].lower() or "admin" in (user["name"] or "").lower(), \
                f"User {user['email']} doesn't match search 'admin'"
        
        print(f"✓ Search works: {len(data['users'])} users matching 'admin'")
    
    def test_users_sort_options(self, auth_token):
        """Test sorting users"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test newest sort
        response = requests.get(f"{BASE_URL}/api/admin/users?sort=newest", headers=headers)
        assert response.status_code == 200
        print("✓ Sort by newest works")
        
        # Test credits_desc sort
        response = requests.get(f"{BASE_URL}/api/admin/users?sort=credits_desc", headers=headers)
        assert response.status_code == 200
        print("✓ Sort by credits_desc works")


class TestAdminCreditLogs:
    """Test /api/admin/credit-logs endpoint (NEW)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_credit_logs_returns_200(self, auth_token):
        """Test credit-logs endpoint returns 200"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/credit-logs", headers=headers)
        assert response.status_code == 200, f"Credit logs failed: {response.text}"
        print("✓ Credit logs endpoint returns 200")
    
    def test_credit_logs_has_pagination(self, auth_token):
        """Test credit-logs returns paginated response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/credit-logs", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check pagination fields
        assert "logs" in data, "Missing logs array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        assert "per_page" in data, "Missing per_page"
        assert "total_pages" in data, "Missing total_pages"
        
        print(f"✓ Credit logs has pagination")
        print(f"  - Total logs: {data['total']}")
        print(f"  - Page: {data['page']}/{data['total_pages']}")
    
    def test_credit_logs_filter_by_mode(self, auth_token):
        """Test filtering credit logs by mode"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/credit-logs?mode=fast", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # All returned logs should have fast mode (or be empty)
        for log in data["logs"]:
            assert log["mode"] == "fast", f"Log has mode {log['mode']}, expected fast"
        
        print(f"✓ Mode filter works: {len(data['logs'])} fast mode logs")
    
    def test_credit_logs_filter_by_type(self, auth_token):
        """Test filtering credit logs by log_type"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/credit-logs?log_type=gift", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # All returned logs should have gift type (or be empty)
        for log in data["logs"]:
            assert log["log_type"] == "gift", f"Log has type {log['log_type']}, expected gift"
        
        print(f"✓ Type filter works: {len(data['logs'])} gift logs")
    
    def test_credit_logs_structure(self, auth_token):
        """Test credit log entry structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/credit-logs?limit=1", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["logs"]:
            log = data["logs"][0]
            expected_fields = ["id", "user_id", "amount", "log_type", "created_at"]
            for field in expected_fields:
                assert field in log, f"Missing field: {field}"
            print(f"✓ Credit log structure is correct")
        else:
            print("✓ Credit logs endpoint works (no logs yet - tables are empty)")


class TestAdminProfitability:
    """Test /api/admin/profitability endpoint (NEW)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_profitability_returns_200(self, auth_token):
        """Test profitability endpoint returns 200"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/profitability", headers=headers)
        assert response.status_code == 200, f"Profitability failed: {response.text}"
        print("✓ Profitability endpoint returns 200")
    
    def test_profitability_has_periods(self, auth_token):
        """Test profitability returns data for all periods"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/profitability", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check periods
        assert "periods" in data, "Missing periods"
        expected_periods = ["7d", "30d", "90d", "all"]
        for period in expected_periods:
            assert period in data["periods"], f"Missing period: {period}"
            period_data = data["periods"][period]
            assert "revenue_eur" in period_data, f"Missing revenue_eur in {period}"
            assert "api_cost_eur" in period_data, f"Missing api_cost_eur in {period}"
            assert "margin_eur" in period_data, f"Missing margin_eur in {period}"
            assert "total_credits_consumed" in period_data, f"Missing total_credits_consumed in {period}"
        
        print(f"✓ Profitability has all periods: {expected_periods}")
        print(f"  - 30d revenue: {data['periods']['30d']['revenue_eur']} EUR")
        print(f"  - 30d API cost: {data['periods']['30d']['api_cost_eur']} EUR")
        print(f"  - 30d margin: {data['periods']['30d']['margin_eur']} EUR")
    
    def test_profitability_has_credits_by_mode(self, auth_token):
        """Test profitability returns credits_by_mode"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/profitability", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "credits_by_mode" in data, "Missing credits_by_mode"
        print(f"✓ Profitability has credits_by_mode: {data['credits_by_mode']}")
    
    def test_profitability_has_costs_by_provider(self, auth_token):
        """Test profitability returns costs_by_provider"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/profitability", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "costs_by_provider" in data, "Missing costs_by_provider"
        print(f"✓ Profitability has costs_by_provider: {data['costs_by_provider']}")
    
    def test_profitability_has_daily_credits(self, auth_token):
        """Test profitability returns daily_credits for chart"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/profitability", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "daily_credits" in data, "Missing daily_credits"
        assert isinstance(data["daily_credits"], list), "daily_credits should be a list"
        
        # Should have 30 days of data
        assert len(data["daily_credits"]) == 30, f"Expected 30 days, got {len(data['daily_credits'])}"
        
        # Each entry should have date and credits
        if data["daily_credits"]:
            entry = data["daily_credits"][0]
            assert "date" in entry, "Missing date in daily_credits entry"
            assert "credits" in entry, "Missing credits in daily_credits entry"
        
        print(f"✓ Profitability has daily_credits: {len(data['daily_credits'])} days")


class TestAdminApiCosts:
    """Test /api/admin/api-costs endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_api_costs_returns_200(self, auth_token):
        """Test api-costs endpoint returns 200"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/api-costs", headers=headers)
        assert response.status_code == 200, f"API costs failed: {response.text}"
        print("✓ API costs endpoint returns 200")
    
    def test_api_costs_has_pagination(self, auth_token):
        """Test api-costs returns paginated response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/api-costs", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check pagination fields
        assert "costs" in data, "Missing costs array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        
        print(f"✓ API costs has pagination")
        print(f"  - Total costs: {data['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
