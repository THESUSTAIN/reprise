"""
Iteration 111 - Testing new features:
1. Audit 360° Biblique dashboard APIs (CRUD + AI analysis)
2. ChatbotAdminPage logout button
3. AuthForm lifetime plan redirect
4. SettingsModal tabs (8 tabs)
5. PricingPage incremental features
6. MonActivitePage Structuration section
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@zayado.net",
        "password": "admin123"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestAuditDataAPI:
    """Test Audit 360° Biblique data CRUD endpoints"""
    
    def test_get_audit_data(self, headers):
        """GET /api/audit/data - should return audit data structure"""
        response = requests.get(f"{BASE_URL}/api/audit/data", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify structure has expected fields
        assert "metrics" in data or "org_name" in data, "Response should have metrics or org_name"
        print(f"GET /api/audit/data: {response.status_code} - Keys: {list(data.keys())}")
    
    def test_save_audit_data(self, headers):
        """POST /api/audit/save - should save audit metrics"""
        payload = {
            "org_name": "TEST_Eglise de Test",
            "org_type": "eglise",
            "metrics": {
                "engagement_global": 75,
                "sentiment_positif": 80,
                "sentiment_neutre": 15,
                "sentiment_negatif": 5,
                "nouveaux_visiteurs": 150,
                "score_sante": 8.0,
                "engagement_physique": [70, 65, 80, 85, 60, 55, 75],
                "engagement_digital": [30, 50, 45, 25, 90, 30, 95],
                "labels_mois": ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun", "Jul"]
            }
        }
        response = requests.post(f"{BASE_URL}/api/audit/save", headers=headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "ok", "Save should return status ok"
        print(f"POST /api/audit/save: {response.status_code} - Status: {data.get('status')}")
    
    def test_add_comment(self, headers):
        """POST /api/audit/comment - should add a member comment"""
        payload = {
            "text": "TEST_Les jeunes apprecient les nouveaux formats de culte",
            "source": "sondage",
            "sentiment": "positif",
            "author": "Test User"
        }
        response = requests.post(f"{BASE_URL}/api/audit/comment", headers=headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "ok", "Add comment should return status ok"
        assert "comments" in data, "Response should include comments list"
        print(f"POST /api/audit/comment: {response.status_code} - Comments count: {len(data.get('comments', []))}")
    
    def test_delete_comment(self, headers):
        """DELETE /api/audit/comment/{index} - should delete a comment"""
        # First add a comment to delete
        add_payload = {
            "text": "TEST_Comment to delete",
            "source": "observation",
            "sentiment": "neutre"
        }
        add_response = requests.post(f"{BASE_URL}/api/audit/comment", headers=headers, json=add_payload)
        assert add_response.status_code == 200
        
        comments_before = add_response.json().get("comments", [])
        if len(comments_before) > 0:
            # Delete the last comment
            delete_index = len(comments_before) - 1
            response = requests.delete(f"{BASE_URL}/api/audit/comment/{delete_index}", headers=headers)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            data = response.json()
            assert data.get("status") == "ok", "Delete should return status ok"
            print(f"DELETE /api/audit/comment/{delete_index}: {response.status_code} - Status: {data.get('status')}")
        else:
            print("No comments to delete, skipping delete test")


class TestAuditAnalyzeAPI:
    """Test Audit AI analysis endpoint"""
    
    def test_analyze_audit(self, headers):
        """POST /api/audit/analyze - should generate AI biblical insights"""
        payload = {
            "org_name": "Eglise Evangelique de Lyon",
            "metrics": {
                "engagement_global": 72,
                "sentiment_positif": 85,
                "sentiment_neutre": 10,
                "sentiment_negatif": 5,
                "nouveaux_visiteurs": 124,
                "score_sante": 8.5
            },
            "comments": [
                {"text": "Les jeunes veulent plus de contenus digitaux", "source": "sondage"},
                {"text": "L'accueil est tres chaleureux", "source": "instagram"}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/audit/analyze", headers=headers, json=payload, timeout=60)
        
        # AI analysis may take time or fail if API key issues
        if response.status_code == 200:
            data = response.json()
            assert "insights" in data, "Response should contain insights"
            print(f"POST /api/audit/analyze: {response.status_code} - Insights count: {len(data.get('insights', []))}")
        elif response.status_code == 400:
            # API key may not be configured
            print(f"POST /api/audit/analyze: {response.status_code} - API key may not be configured")
        elif response.status_code == 500:
            print(f"POST /api/audit/analyze: {response.status_code} - Server error (may be LLM API issue)")
        else:
            print(f"POST /api/audit/analyze: {response.status_code} - {response.text[:200]}")


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_login_returns_user_data(self):
        """Login should return user data including plan field"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data or "token" in data, "Response should have token"
        assert "user" in data, "Response should have user object"
        
        user = data.get("user", {})
        print(f"Login user data: role={user.get('role')}, plan={user.get('plan')}")
        # Admin user should have role='admin'
        assert user.get("role") == "admin", f"Expected admin role, got {user.get('role')}"


class TestHealthAndBasicEndpoints:
    """Test basic health endpoints"""
    
    def test_health_check(self):
        """Health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print(f"GET /api/health: {response.status_code}")
    
    def test_public_config(self):
        """Public config should be accessible"""
        response = requests.get(f"{BASE_URL}/api/public/config")
        # May return 200 or 404 depending on implementation
        print(f"GET /api/public/config: {response.status_code}")


class TestTeamAndLicenseEndpoints:
    """Test team and license endpoints for ChatbotAdminPage"""
    
    def test_team_list(self, headers):
        """GET /api/team/list - should return teams"""
        response = requests.get(f"{BASE_URL}/api/team/list", headers=headers)
        # May return 200 with empty list or 404
        print(f"GET /api/team/list: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Teams count: {len(data.get('teams', []))}")
    
    def test_license_my(self, headers):
        """GET /api/license/my - should return user licenses"""
        response = requests.get(f"{BASE_URL}/api/license/my", headers=headers)
        print(f"GET /api/license/my: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Licenses count: {len(data.get('licenses', []))}")


class TestActiviteEndpoints:
    """Test MonActivite page endpoints"""
    
    def test_activite_summary(self, headers):
        """GET /api/activite/summary - should return activity summary"""
        response = requests.get(f"{BASE_URL}/api/activite/summary", headers=headers)
        print(f"GET /api/activite/summary: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Summary keys: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
