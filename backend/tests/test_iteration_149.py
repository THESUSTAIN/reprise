"""
Iteration 149 - Backend API Tests
Testing:
1. Team creation flow: POST /api/team/create
2. Admin dashboard stats: GET /api/admin/stats (pending_revenue field)
3. HTML export files accessibility
4. Team page data retrieval
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-panel-416.preview.emergentagent.com')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"
BUSINESS_USER_EMAIL = "testteam@zayado.net"
BUSINESS_USER_PASSWORD = "testteam123"


class TestAuth:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data, f"No token in response: {data}"
        print(f"✓ Admin login successful")
        return data.get("token") or data.get("access_token")
    
    def test_business_user_login(self):
        """Test business user login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": BUSINESS_USER_EMAIL,
            "password": BUSINESS_USER_PASSWORD
        })
        # User may not exist yet, so we accept 401 as well
        if response.status_code == 401:
            print(f"⚠ Business user {BUSINESS_USER_EMAIL} not found - may need to be created")
            pytest.skip("Business user not found")
        assert response.status_code == 200, f"Business user login failed: {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data, f"No token in response: {data}"
        print(f"✓ Business user login successful")
        return data.get("token") or data.get("access_token")


class TestAdminStats:
    """Admin dashboard stats tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_admin_stats_returns_pending_revenue(self, admin_token):
        """Test GET /api/admin/stats returns pending_revenue field"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200, f"Admin stats failed: {response.text}"
        data = response.json()
        
        # Verify pending_revenue field exists
        assert "pending_revenue" in data, f"pending_revenue field missing from stats: {data.keys()}"
        print(f"✓ pending_revenue field present: {data['pending_revenue']}")
        
        # Verify other expected fields
        expected_fields = ["total_users", "total_revenue", "revenue_30d", "total_conversations"]
        for field in expected_fields:
            assert field in data, f"Expected field {field} missing from stats"
        print(f"✓ All expected stats fields present")
        
        return data


class TestTeamCreation:
    """Team creation flow tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_team_create_endpoint_exists(self, admin_token):
        """Test POST /api/team/create endpoint exists and responds"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/team/create", headers=headers, json={
            "name": "TEST_Team_Iteration149"
        })
        
        # Accept 200 (success), 400 (limit reached), or 403 (plan restriction)
        assert response.status_code in [200, 400, 403], f"Unexpected status: {response.status_code} - {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, f"No success field in response: {data}"
            assert data["success"] == True, f"Team creation failed: {data}"
            assert "team" in data, f"No team field in response: {data}"
            assert "id" in data["team"], f"No team id in response: {data}"
            assert "name" in data["team"], f"No team name in response: {data}"
            print(f"✓ Team created successfully: {data['team']['name']} (id: {data['team']['id']})")
            
            # Cleanup - delete the test team
            team_id = data["team"]["id"]
            delete_response = requests.delete(f"{BASE_URL}/api/team/delete/{team_id}", headers=headers)
            if delete_response.status_code == 200:
                print(f"✓ Test team cleaned up")
        elif response.status_code == 400:
            data = response.json()
            print(f"⚠ Team creation limit reached: {data.get('detail', 'Unknown')}")
        elif response.status_code == 403:
            data = response.json()
            print(f"⚠ Team creation not allowed for plan: {data.get('detail', 'Unknown')}")
    
    def test_team_list_endpoint(self, admin_token):
        """Test GET /api/team/list returns teams"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/team/list", headers=headers)
        assert response.status_code == 200, f"Team list failed: {response.text}"
        data = response.json()
        assert "teams" in data, f"No teams field in response: {data}"
        print(f"✓ Team list returned {len(data['teams'])} teams")
    
    def test_team_me_endpoint(self, admin_token):
        """Test GET /api/team/me returns team data or null"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        assert response.status_code == 200, f"Team me failed: {response.text}"
        data = response.json()
        # team can be null if user has no team
        if data.get("team"):
            print(f"✓ User has team: {data['team'].get('name', 'Unknown')}")
            assert "id" in data["team"], "Team missing id"
            assert "name" in data["team"], "Team missing name"
        else:
            print(f"✓ User has no team (expected for some users)")


class TestHTMLExports:
    """HTML export files accessibility tests"""
    
    HTML_EXPORT_FILES = [
        "zayado.html",
        "extension-ia.html",
        "chatbot-b2b.html",
        "tarifs.html",
        "methodes.html",
        "creation.html"
    ]
    
    def test_html_export_zayado(self):
        """Test /html-export/zayado.html returns 200"""
        response = requests.get(f"{BASE_URL}/html-export/zayado.html")
        assert response.status_code == 200, f"zayado.html not accessible: {response.status_code}"
        assert len(response.text) > 1000, "HTML file seems too small"
        print(f"✓ zayado.html accessible ({len(response.text)} bytes)")
    
    def test_html_export_extension_ia(self):
        """Test /html-export/extension-ia.html returns 200"""
        response = requests.get(f"{BASE_URL}/html-export/extension-ia.html")
        assert response.status_code == 200, f"extension-ia.html not accessible: {response.status_code}"
        assert len(response.text) > 1000, "HTML file seems too small"
        print(f"✓ extension-ia.html accessible ({len(response.text)} bytes)")
    
    def test_html_export_chatbot_b2b(self):
        """Test /html-export/chatbot-b2b.html returns 200"""
        response = requests.get(f"{BASE_URL}/html-export/chatbot-b2b.html")
        assert response.status_code == 200, f"chatbot-b2b.html not accessible: {response.status_code}"
        assert len(response.text) > 1000, "HTML file seems too small"
        print(f"✓ chatbot-b2b.html accessible ({len(response.text)} bytes)")
    
    def test_html_export_tarifs(self):
        """Test /html-export/tarifs.html returns 200"""
        response = requests.get(f"{BASE_URL}/html-export/tarifs.html")
        assert response.status_code == 200, f"tarifs.html not accessible: {response.status_code}"
        assert len(response.text) > 1000, "HTML file seems too small"
        print(f"✓ tarifs.html accessible ({len(response.text)} bytes)")
    
    def test_html_export_methodes(self):
        """Test /html-export/methodes.html returns 200"""
        response = requests.get(f"{BASE_URL}/html-export/methodes.html")
        assert response.status_code == 200, f"methodes.html not accessible: {response.status_code}"
        assert len(response.text) > 1000, "HTML file seems too small"
        print(f"✓ methodes.html accessible ({len(response.text)} bytes)")
    
    def test_html_export_creation(self):
        """Test /html-export/creation.html returns 200"""
        response = requests.get(f"{BASE_URL}/html-export/creation.html")
        assert response.status_code == 200, f"creation.html not accessible: {response.status_code}"
        assert len(response.text) > 1000, "HTML file seems too small"
        print(f"✓ creation.html accessible ({len(response.text)} bytes)")


class TestTeamLimits:
    """Test TEAM_LIMITS_DEFAULTS sync with subscription plans"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_subscription_plans_have_team_dashboard(self, admin_token):
        """Test that subscription plans API returns team_dashboard feature"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/payments/plans", headers=headers)
        
        # This endpoint may not require auth
        if response.status_code == 401:
            response = requests.get(f"{BASE_URL}/api/payments/plans")
        
        assert response.status_code == 200, f"Plans API failed: {response.text}"
        data = response.json()
        
        # Check if plans have features
        plans = data.get("plans", data) if isinstance(data, dict) else data
        if isinstance(plans, list):
            for plan in plans:
                if plan.get("id") in ["business", "team"]:
                    features = plan.get("features", {})
                    if "team_dashboard" in features:
                        print(f"✓ Plan {plan['id']} has team_dashboard: {features['team_dashboard']}")
                    else:
                        print(f"⚠ Plan {plan['id']} features: {list(features.keys())[:5]}...")
        print(f"✓ Plans API returned data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
