"""
Test Admin New Tabs - Iteration 85
Tests for: Referrals, Notifications, AI Feedback, Email Logs tabs
Also tests: Security fixes (masked API keys), Profitability with API costs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


class TestAdminLogin:
    """Test admin authentication"""
    
    def test_admin_login_success(self):
        """Test admin login returns access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["role"] in ["admin", "super_admin"], f"User role is {data['user']['role']}, expected admin"
        
    def test_login_response_no_secrets(self):
        """Security: Login response should NOT contain API keys or secrets"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        response_text = response.text.lower()
        # Check that no API keys are exposed
        assert "openai_key" not in response_text, "openai_key exposed in login response!"
        assert "anthropic_api_key" not in response_text, "anthropic_api_key exposed!"
        assert "sk-ant-" not in response_text, "Anthropic key pattern found!"
        assert "sk-" not in response_text or "sk-emergent" in response_text, "Potential API key exposed!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin auth"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestAdminStats:
    """Test admin dashboard stats endpoint"""
    
    def test_admin_stats_returns_api_cost_metrics(self, admin_headers):
        """Dashboard should show API cost and margin metrics"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        # Check new API cost fields
        assert "total_api_cost" in data, "Missing total_api_cost"
        assert "api_cost_30d" in data, "Missing api_cost_30d"
        assert "margin_30d" in data, "Missing margin_30d"
        # Verify types
        assert isinstance(data["total_api_cost"], (int, float)), "total_api_cost should be numeric"
        assert isinstance(data["api_cost_30d"], (int, float)), "api_cost_30d should be numeric"


class TestAdminUsersSecurityFix:
    """Test that admin users endpoint doesn't expose secrets"""
    
    def test_admin_users_no_secrets(self, admin_headers):
        """Security: /api/admin/users should NOT contain API keys"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        response_text = response.text.lower()
        assert "openai_key" not in response_text, "openai_key exposed in users response!"
        assert "sk-" not in response_text or "sk-emergent" in response_text, "Potential API key in users!"


class TestOAuthDiagnosticMasked:
    """Test OAuth diagnostic endpoint masks client ID"""
    
    def test_oauth_diagnostic_masked_client_id(self):
        """Security: OAuth diagnostic should show only first 8 chars of client ID"""
        response = requests.get(f"{BASE_URL}/api/oauth/diagnostic")
        assert response.status_code == 200, f"Diagnostic failed: {response.text}"
        data = response.json()
        # Check that client ID is masked
        assert "google_client_id_preview" in data, "Missing google_client_id_preview"
        preview = data["google_client_id_preview"]
        # Should be like "42698665****" (8 chars + ****)
        assert "****" in preview, f"Client ID not masked: {preview}"
        # Should not show full client ID
        assert len(preview) <= 15, f"Client ID preview too long: {preview}"


# ==================== NEW ADMIN TABS ====================

class TestReferralsTab:
    """Test /api/admin/referrals endpoint"""
    
    def test_referrals_endpoint_returns_paginated_data(self, admin_headers):
        """Referrals endpoint should return paginated list"""
        response = requests.get(f"{BASE_URL}/api/admin/referrals", headers=admin_headers)
        assert response.status_code == 200, f"Referrals failed: {response.text}"
        data = response.json()
        # Check pagination structure
        assert "referrals" in data, "Missing referrals array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        assert "total_pages" in data, "Missing total_pages"
        assert isinstance(data["referrals"], list), "referrals should be a list"
        
    def test_referrals_with_status_filter(self, admin_headers):
        """Referrals endpoint should support status filter"""
        for status in ["pending", "completed", "expired"]:
            response = requests.get(f"{BASE_URL}/api/admin/referrals?status={status}", headers=admin_headers)
            assert response.status_code == 200, f"Referrals filter {status} failed: {response.text}"


class TestNotificationsTab:
    """Test /api/admin/notifications-list endpoint"""
    
    def test_notifications_list_returns_paginated_data(self, admin_headers):
        """Notifications list should return paginated data"""
        response = requests.get(f"{BASE_URL}/api/admin/notifications-list", headers=admin_headers)
        assert response.status_code == 200, f"Notifications list failed: {response.text}"
        data = response.json()
        assert "notifications" in data, "Missing notifications array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        
    def test_notifications_create(self, admin_headers):
        """Should be able to create a notification"""
        response = requests.post(f"{BASE_URL}/api/admin/notifications-list", 
            headers=admin_headers,
            json={
                "title": "TEST_Notification",
                "message": "Test message from iteration 85",
                "type": "info",
                "is_global": True
            }
        )
        assert response.status_code == 200, f"Create notification failed: {response.text}"
        data = response.json()
        assert data.get("status") == "created", f"Unexpected status: {data}"
        
    def test_notifications_type_filter(self, admin_headers):
        """Notifications should support type filter"""
        for notif_type in ["info", "warning", "success", "promo"]:
            response = requests.get(f"{BASE_URL}/api/admin/notifications-list?type_filter={notif_type}", headers=admin_headers)
            assert response.status_code == 200, f"Notifications filter {notif_type} failed"


class TestAiFeedbackTab:
    """Test /api/admin/ai-feedback endpoint"""
    
    def test_ai_feedback_returns_paginated_data(self, admin_headers):
        """AI Feedback endpoint should return paginated list"""
        response = requests.get(f"{BASE_URL}/api/admin/ai-feedback", headers=admin_headers)
        assert response.status_code == 200, f"AI Feedback failed: {response.text}"
        data = response.json()
        assert "feedback" in data, "Missing feedback array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        assert isinstance(data["feedback"], list), "feedback should be a list"
        
    def test_ai_feedback_rating_filter(self, admin_headers):
        """AI Feedback should support rating filter"""
        for rating in ["up", "down"]:
            response = requests.get(f"{BASE_URL}/api/admin/ai-feedback?rating={rating}", headers=admin_headers)
            assert response.status_code == 200, f"AI Feedback filter {rating} failed"


class TestEmailLogsTab:
    """Test /api/admin/email-logs endpoint"""
    
    def test_email_logs_returns_paginated_data(self, admin_headers):
        """Email logs endpoint should return paginated list"""
        response = requests.get(f"{BASE_URL}/api/admin/email-logs", headers=admin_headers)
        assert response.status_code == 200, f"Email logs failed: {response.text}"
        data = response.json()
        assert "logs" in data, "Missing logs array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        assert isinstance(data["logs"], list), "logs should be a list"
        
    def test_email_logs_status_filter(self, admin_headers):
        """Email logs should support status filter"""
        for status in ["sent", "failed", "bounced"]:
            response = requests.get(f"{BASE_URL}/api/admin/email-logs?status_filter={status}", headers=admin_headers)
            assert response.status_code == 200, f"Email logs filter {status} failed"


class TestAdminLogsTab:
    """Test /api/admin/admin-logs endpoint"""
    
    def test_admin_logs_returns_paginated_data(self, admin_headers):
        """Admin logs endpoint should return paginated list"""
        response = requests.get(f"{BASE_URL}/api/admin/admin-logs", headers=admin_headers)
        assert response.status_code == 200, f"Admin logs failed: {response.text}"
        data = response.json()
        assert "logs" in data, "Missing logs array"
        assert "total" in data, "Missing total count"
        assert isinstance(data["logs"], list), "logs should be a list"


class TestProfitabilityWithApiCosts:
    """Test profitability endpoint with API costs"""
    
    def test_profitability_returns_periods_with_api_cost(self, admin_headers):
        """Profitability should return periods with api_cost_eur"""
        response = requests.get(f"{BASE_URL}/api/admin/profitability", headers=admin_headers)
        assert response.status_code == 200, f"Profitability failed: {response.text}"
        data = response.json()
        
        # Check structure
        assert "periods" in data, "Missing periods"
        assert "credits_by_mode" in data, "Missing credits_by_mode"
        assert "costs_by_provider" in data, "Missing costs_by_provider"
        assert "daily_credits" in data, "Missing daily_credits"
        
        # Check 'all' period has api_cost_eur
        periods = data["periods"]
        assert "all" in periods, "Missing 'all' period"
        all_period = periods["all"]
        assert "api_cost_eur" in all_period, "Missing api_cost_eur in 'all' period"
        assert "revenue_eur" in all_period, "Missing revenue_eur"
        assert "margin_eur" in all_period, "Missing margin_eur"
        assert "total_credits_consumed" in all_period, "Missing total_credits_consumed"
        
        # Verify the backfilled API cost (should be ~0.0385 EUR from 26 conversations)
        api_cost = all_period["api_cost_eur"]
        print(f"API Cost (all period): {api_cost} EUR")
        # The backfill should have populated some cost
        assert isinstance(api_cost, (int, float)), "api_cost_eur should be numeric"


class TestCreditLogsTab:
    """Test credit logs endpoint"""
    
    def test_credit_logs_returns_paginated_data(self, admin_headers):
        """Credit logs should return paginated data"""
        response = requests.get(f"{BASE_URL}/api/admin/credit-logs", headers=admin_headers)
        assert response.status_code == 200, f"Credit logs failed: {response.text}"
        data = response.json()
        assert "logs" in data, "Missing logs array"
        assert "total" in data, "Missing total count"
        
    def test_credit_logs_mode_filter(self, admin_headers):
        """Credit logs should support mode filter"""
        for mode in ["fast", "pro", "agent"]:
            response = requests.get(f"{BASE_URL}/api/admin/credit-logs?mode={mode}", headers=admin_headers)
            assert response.status_code == 200, f"Credit logs filter {mode} failed"


class TestApiCostsEndpoint:
    """Test API costs endpoint"""
    
    def test_api_costs_returns_paginated_data(self, admin_headers):
        """API costs should return paginated data"""
        response = requests.get(f"{BASE_URL}/api/admin/api-costs", headers=admin_headers)
        assert response.status_code == 200, f"API costs failed: {response.text}"
        data = response.json()
        assert "costs" in data, "Missing costs array"
        assert "total" in data, "Missing total count"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
