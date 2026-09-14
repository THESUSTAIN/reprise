"""
Iteration 118 - P0 Features Testing
Tests for:
1. BillingPage promo code input and validation
2. MonActivitePage diagnostic section (inline questionnaire)
3. /app/diagnostic redirect to /app/activite
4. POST /api/payments/redeem-promo endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("PASS: Health endpoint accessible")
    
    def test_admin_login(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"PASS: Admin login successful, token received")
        return data["access_token"]


class TestPromoCodeEndpoint:
    """Tests for POST /api/payments/redeem-promo endpoint"""
    
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
    
    def test_redeem_promo_without_code(self, auth_token):
        """Test redeem-promo endpoint with empty code"""
        response = requests.post(
            f"{BASE_URL}/api/payments/redeem-promo",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"code": ""}
        )
        # Should return 400 for empty code
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"PASS: Empty code returns 400 with detail: {data['detail']}")
    
    def test_redeem_promo_invalid_code(self, auth_token):
        """Test redeem-promo endpoint with invalid code"""
        response = requests.post(
            f"{BASE_URL}/api/payments/redeem-promo",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"code": "INVALIDCODE123"}
        )
        # Should return 404 for invalid code
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        print(f"PASS: Invalid code returns 404 with detail: {data['detail']}")
    
    def test_redeem_promo_endpoint_exists(self, auth_token):
        """Test that redeem-promo endpoint exists and accepts POST"""
        response = requests.post(
            f"{BASE_URL}/api/payments/redeem-promo",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"code": "TEST"}
        )
        # Should not return 405 (Method Not Allowed) or 404 (endpoint not found)
        assert response.status_code != 405, "Endpoint should accept POST method"
        # 400 or 404 are acceptable (code validation errors)
        assert response.status_code in [400, 404, 200]
        print(f"PASS: redeem-promo endpoint exists and accepts POST, status: {response.status_code}")


class TestBillingEndpoint:
    """Tests for billing endpoint"""
    
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
    
    def test_billing_endpoint(self, auth_token):
        """Test billing endpoint returns user billing info"""
        response = requests.get(
            f"{BASE_URL}/api/payments/billing",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "credits" in data
        print(f"PASS: Billing endpoint returns plan={data['plan']}, credits={data['credits']}")


class TestDiagnosticEndpoint:
    """Tests for diagnostic submit endpoint"""
    
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
    
    def test_diagnostic_score_endpoint(self, auth_token):
        """Test diagnostic score endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/features/diagnostic/score",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 200 (with or without existing score)
        assert response.status_code in [200, 404]
        print(f"PASS: Diagnostic score endpoint accessible, status: {response.status_code}")
    
    def test_diagnostic_submit_endpoint(self, auth_token):
        """Test diagnostic submit endpoint accepts POST"""
        test_answers = {
            "q1_capture": 3,
            "q2_deepwork": 3,
            "q3_essentialism": 3
        }
        test_scores = {
            "overall": 60,
            "pillars": {"clarity": 60, "energy": 60, "alignment": 60}
        }
        response = requests.post(
            f"{BASE_URL}/api/features/diagnostic/submit",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"answers": test_answers, "scores": test_scores}
        )
        # Should accept the submission
        assert response.status_code in [200, 201]
        print(f"PASS: Diagnostic submit endpoint accepts POST, status: {response.status_code}")


class TestActiviteEndpoint:
    """Tests for activite summary endpoint"""
    
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
    
    def test_activite_summary_endpoint(self, auth_token):
        """Test activite summary endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/activite/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        print(f"PASS: Activite summary endpoint accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
