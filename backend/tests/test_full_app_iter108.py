"""
Iteration 108 - Full Application Test Suite
Tests all major API endpoints for ZAYADO platform
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-panel-416.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "testuser@test.com"
TEST_USER_PASSWORD = "test1234"

# Known team ID from previous tests
KNOWN_TEAM_ID = "afe0e66c-ea92-4828-882a-7535f822449d"


class TestHealth:
    """Health check tests"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data}")


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_admin_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful, role: {data['user'].get('role')}")
        return data["access_token"]
    
    def test_login_testuser_success(self):
        """Test regular user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        # User may or may not exist
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            print(f"✓ Test user login successful")
            return data["access_token"]
        else:
            print(f"⚠ Test user login failed (user may not exist): {response.status_code}")
            return None
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_get_me_authenticated(self):
        """Test /auth/me with valid token"""
        token = self.test_login_admin_success()
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ GET /auth/me returned user: {data['email']}")
    
    def test_get_me_unauthenticated(self):
        """Test /auth/me without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
        print("✓ Unauthenticated /auth/me correctly rejected")
    
    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": "testpassword123",
            "name": "Test User"
        })
        assert response.status_code == 400
        print("✓ Duplicate email registration correctly rejected")


class TestConversations:
    """Chat/Conversation endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_list_conversations(self, auth_token):
        """Test listing conversations - correct path is /api/chat/conversations"""
        response = requests.get(f"{BASE_URL}/api/chat/conversations", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} conversations")
    
    def test_create_conversation(self, auth_token):
        """Test creating a new conversation"""
        response = requests.post(f"{BASE_URL}/api/chat/conversations", headers={
            "Authorization": f"Bearer {auth_token}"
        }, json={
            "title": f"Test Conversation {uuid.uuid4().hex[:8]}",
            "mode": "fast"
        })
        # May return 200 or 201
        assert response.status_code in [200, 201], f"Create conversation failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"✓ Created conversation: {data.get('id')}")
        return data["id"]


class TestCustomAgents:
    """Custom Agents endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_list_agents(self, auth_token):
        """Test listing custom agents"""
        response = requests.get(f"{BASE_URL}/api/custom-agents", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} custom agents")
    
    def test_list_agent_tools(self, auth_token):
        """Test listing available tools"""
        response = requests.get(f"{BASE_URL}/api/custom-agents/tools", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Listed {len(data)} available tools")
    
    def test_list_agent_templates(self, auth_token):
        """Test listing agent templates"""
        response = requests.get(f"{BASE_URL}/api/custom-agents/templates", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} agent templates")
    
    def test_create_agent(self, auth_token):
        """Test creating a custom agent"""
        response = requests.post(f"{BASE_URL}/api/custom-agents", headers={
            "Authorization": f"Bearer {auth_token}"
        }, json={
            "name": f"TEST_Agent_{uuid.uuid4().hex[:6]}",
            "description": "Test agent for iteration 108",
            "system_prompt": "Tu es un assistant de test.",
            "tools": ["email_draft", "calculator"],
            "temperature": 0.7
        })
        assert response.status_code == 200, f"Create agent failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"].startswith("TEST_Agent_")
        print(f"✓ Created agent: {data['name']}")
        return data["id"]
    
    def test_get_agent_history(self, auth_token):
        """Test getting agent history"""
        # First create an agent
        agent_id = self.test_create_agent(auth_token)
        response = requests.get(f"{BASE_URL}/api/custom-agents/{agent_id}/history", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got agent history: {len(data)} messages")


class TestTeam:
    """Team endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_list_teams(self, auth_token):
        """Test listing user's teams"""
        response = requests.get(f"{BASE_URL}/api/team/list", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        print(f"✓ Listed {len(data['teams'])} teams")
    
    def test_get_team_me(self, auth_token):
        """Test getting current team info"""
        response = requests.get(f"{BASE_URL}/api/team/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        # May have team or not
        if data.get("team"):
            print(f"✓ Got team info: {data['team']['name']}")
        else:
            print("✓ No team found (expected for some users)")
    
    def test_get_team_agents(self, auth_token):
        """Test listing team agents"""
        response = requests.get(f"{BASE_URL}/api/team/agents?team_id={KNOWN_TEAM_ID}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} team agents")
    
    def test_team_dashboard(self, auth_token):
        """Test team dashboard"""
        response = requests.get(f"{BASE_URL}/api/team/dashboard?team_id={KNOWN_TEAM_ID}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "team" in data
        print(f"✓ Got team dashboard: {data['team']['name']}")
    
    def test_team_conversations(self, auth_token):
        """Test listing team conversations"""
        response = requests.get(f"{BASE_URL}/api/team/conversations?team_id={KNOWN_TEAM_ID}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} team conversations")
    
    def test_team_credits_history(self, auth_token):
        """Test team credits history"""
        response = requests.get(f"{BASE_URL}/api/team/credits/history?team_id={KNOWN_TEAM_ID}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} credit history entries")


class TestLicense:
    """License endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_admin_list_licenses(self, auth_token):
        """Test admin listing all licenses"""
        response = requests.get(f"{BASE_URL}/api/license/admin/list", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "licenses" in data
        print(f"✓ Listed {len(data['licenses'])} licenses")
    
    def test_admin_create_license(self, auth_token):
        """Test admin creating a license"""
        response = requests.post(f"{BASE_URL}/api/license/admin/create", headers={
            "Authorization": f"Bearer {auth_token}"
        }, json={
            "plan_type": "chatbot_starter",
            "quantity": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["licenses"]) == 1
        print(f"✓ Created license: {data['licenses'][0]['code']}")
    
    def test_validate_invalid_license(self):
        """Test validating an invalid license code"""
        response = requests.get(f"{BASE_URL}/api/license/validate/INVALID-CODE-123")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        print("✓ Invalid license correctly rejected")
    
    def test_my_licenses(self, auth_token):
        """Test getting user's licenses"""
        response = requests.get(f"{BASE_URL}/api/license/my", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "licenses" in data
        print(f"✓ User has {len(data['licenses'])} licenses")


class TestFinance:
    """Finance endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_finance_overview(self, auth_token):
        """Test finance overview"""
        response = requests.get(f"{BASE_URL}/api/finance/overview", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "revenus" in data
        assert "depenses" in data
        assert "net" in data
        print(f"✓ Finance overview: revenus={data['revenus']}, depenses={data['depenses']}, net={data['net']}")
    
    def test_create_finance_entry(self, auth_token):
        """Test creating a finance entry"""
        response = requests.post(f"{BASE_URL}/api/finance/entry", headers={
            "Authorization": f"Bearer {auth_token}"
        }, json={
            "type": "revenu",
            "label": f"TEST_Entry_{uuid.uuid4().hex[:6]}",
            "amount": 100.0,
            "category": "services"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "entry" in data
        print(f"✓ Created finance entry: {data['entry']['label']}")
    
    def test_finance_forecast(self, auth_token):
        """Test finance forecast"""
        response = requests.get(f"{BASE_URL}/api/finance/forecast", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data
        assert "health" in data
        print(f"✓ Finance forecast: health={data['health']}")


class TestWellness:
    """Wellness endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_wellness_history(self, auth_token):
        """Test wellness history"""
        response = requests.get(f"{BASE_URL}/api/wellness/history", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "checkins" in data
        assert "stats" in data
        print(f"✓ Wellness history: {data['stats']['total_checkins']} checkins")
    
    def test_wellness_checkin(self, auth_token):
        """Test creating a wellness checkin"""
        response = requests.post(f"{BASE_URL}/api/wellness/checkin", headers={
            "Authorization": f"Bearer {auth_token}"
        }, json={
            "energy": 4,
            "mood": 4,
            "stress": 2,
            "sleep": 4,
            "notes": "Test checkin from iteration 108"
        })
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "ai_insight" in data
        print(f"✓ Wellness checkin: score={data['score']}")
    
    def test_wellness_today(self, auth_token):
        """Test getting today's checkin"""
        response = requests.get(f"{BASE_URL}/api/wellness/today", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        # May or may not have checkin
        print(f"✓ Today's checkin: has_checkin={data.get('has_checkin', False)}")
    
    def test_wellness_weekly_report(self, auth_token):
        """Test weekly wellness report"""
        response = requests.get(f"{BASE_URL}/api/wellness/weekly-report", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Weekly report: has_data={data.get('has_data', False)}")


class TestProjects:
    """Projects endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_list_projects(self, auth_token):
        """Test listing projects"""
        response = requests.get(f"{BASE_URL}/api/projects", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} projects")
    
    def test_create_project(self, auth_token):
        """Test creating a project"""
        response = requests.post(f"{BASE_URL}/api/projects", headers={
            "Authorization": f"Bearer {auth_token}"
        }, json={
            "name": f"TEST_Project_{uuid.uuid4().hex[:6]}",
            "hourly_rate": 75.0,
            "color": "#1E3A8A"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"].startswith("TEST_Project_")
        print(f"✓ Created project: {data['name']}")
        return data["id"]


class TestWorkflows:
    """Workflows endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_list_workflows(self, auth_token):
        """Test listing workflows"""
        response = requests.get(f"{BASE_URL}/api/workflows", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} workflows")
    
    def test_create_workflow(self, auth_token):
        """Test creating a workflow"""
        response = requests.post(f"{BASE_URL}/api/workflows", headers={
            "Authorization": f"Bearer {auth_token}"
        }, json={
            "name": f"TEST_Workflow_{uuid.uuid4().hex[:6]}",
            "description": "Test workflow from iteration 108",
            "steps": [
                {"type": "prompt", "prompt": "Dis bonjour", "label": "Etape 1"}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Created workflow: {data['name']}")
        return data["id"]


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_404_nonexistent_endpoint(self):
        """Test 404 for non-existent endpoint"""
        response = requests.get(f"{BASE_URL}/api/nonexistent-endpoint-xyz")
        assert response.status_code == 404
        print("✓ 404 returned for non-existent endpoint")
    
    def test_401_protected_endpoint_no_auth(self):
        """Test 401 for protected endpoint without auth"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
        print("✓ 401/403 returned for protected endpoint without auth")
    
    def test_invalid_json_body(self):
        """Test handling of invalid JSON"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
        print("✓ Invalid JSON correctly rejected")


class TestPublicEndpoints:
    """Test public endpoints that don't require auth"""
    
    def test_public_team_info_invalid_code(self):
        """Test public team info with invalid code"""
        response = requests.get(f"{BASE_URL}/api/team/public/info/INVALID-CODE")
        assert response.status_code == 404
        print("✓ Invalid team code correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
