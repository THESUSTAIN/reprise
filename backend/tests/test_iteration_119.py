"""
Iteration 119 Backend Tests
Tests for:
1. /api/chat/quick endpoint (used by IA Contextuelle and Capture Transformer)
2. Health and auth endpoints
3. Activite summary endpoint
4. Diagnostic endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-panel-416.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        # Handle both 'token' and 'access_token' response formats
        token = data.get("access_token") or data.get("token")
        if token:
            return token
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print(f"Health check: {response.json()}")
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        # Accept both token formats
        assert "access_token" in data or "token" in data
        print(f"Login successful, token received")


class TestChatQuickEndpoint:
    """Tests for /api/chat/quick endpoint - used by IA Contextuelle and Capture Transformer"""
    
    def test_quick_endpoint_exists(self, auth_token):
        """Test that /api/chat/quick endpoint exists and accepts POST"""
        response = requests.post(
            f"{BASE_URL}/api/chat/quick",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Test message"}
        )
        # Should not return 404 or 405
        assert response.status_code not in [404, 405], f"Endpoint not found or method not allowed: {response.status_code}"
        print(f"Quick endpoint status: {response.status_code}")
    
    def test_quick_endpoint_returns_response(self, auth_token):
        """Test that /api/chat/quick returns AI response"""
        response = requests.post(
            f"{BASE_URL}/api/chat/quick",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "message": "Donne une recommandation courte pour un entrepreneur",
                "system": "Tu es un coach business. Reponds en 1-2 phrases."
            },
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data, f"Expected 'response' in data, got: {data}"
        assert len(data["response"]) > 10, f"Response too short: {data['response']}"
        print(f"Quick response: {data['response'][:100]}...")
    
    def test_quick_endpoint_without_auth(self):
        """Test that /api/chat/quick requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/chat/quick",
            headers={"Content-Type": "application/json"},
            json={"message": "Test"}
        )
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"Correctly requires auth: {response.status_code}")


class TestActiviteEndpoints:
    """Tests for Mon Activité related endpoints"""
    
    def test_activite_summary_endpoint(self, auth_token):
        """Test /api/activite/summary endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/activite/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"Activite summary: {data}")
    
    def test_activite_blocker_endpoint(self, auth_token):
        """Test /api/activite/blocker endpoint accepts POST"""
        response = requests.post(
            f"{BASE_URL}/api/activite/blocker",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"tension": "Test blocker from iteration 119"}
        )
        # Should accept POST (200 or 201)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        print(f"Blocker endpoint: {response.status_code}")


class TestDiagnosticEndpoints:
    """Tests for diagnostic endpoints"""
    
    def test_diagnostic_score_endpoint(self, auth_token):
        """Test /api/features/diagnostic/score endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/features/diagnostic/score",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 200 (with or without existing score)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"Diagnostic score: {response.json()}")
    
    def test_diagnostic_submit_endpoint(self, auth_token):
        """Test /api/features/diagnostic/submit endpoint accepts POST"""
        test_answers = {
            "q1_capture": 3,
            "q2_deepwork": 2,
            "q3_essentialism": 4
        }
        test_scores = {
            "overall": 60,
            "pillars": {"clarity": 60, "energy": 50, "alignment": 70}
        }
        response = requests.post(
            f"{BASE_URL}/api/features/diagnostic/submit",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"answers": test_answers, "scores": test_scores}
        )
        # Should accept POST
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        print(f"Diagnostic submit: {response.status_code}")


class TestCaptureEndpoints:
    """Tests for Capture page endpoints"""
    
    def test_captures_list_endpoint(self, auth_token):
        """Test /api/features/captures endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/features/captures",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"Captures list: {response.json()[:2] if response.json() else 'empty'}")
    
    def test_captures_create_endpoint(self, auth_token):
        """Test creating a capture"""
        response = requests.post(
            f"{BASE_URL}/api/features/captures",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "content": "TEST_iteration_119_capture",
                "category": "idee",
                "source": "text"
            }
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        data = response.json()
        assert "id" in data, f"Expected 'id' in response, got: {data}"
        print(f"Created capture: {data.get('id')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
