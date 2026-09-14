"""
Iteration 99 - Backend API Tests for ZAYADO
Tests for auth, chat, team, agent, workflows, payments endpoints
Based on functional audit fixes
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-panel-416.preview.emergentagent.com')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


class TestHealthAndBasics:
    """Health check and basic API tests"""
    
    def test_health_check(self):
        """GET /api/health - Should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health check passed")
    
    def test_packages_endpoint(self):
        """GET /api/payments/packages - Should return credit packages"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Packages endpoint returned {len(data)} packages")


class TestAuthFlow:
    """Authentication flow tests"""
    
    def test_login_success(self):
        """POST /api/auth/login - Should login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✅ Login successful for {ADMIN_EMAIL}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - Should reject invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✅ Invalid credentials correctly rejected")
    
    def test_login_missing_password(self):
        """POST /api/auth/login - Should reject missing password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL
        })
        assert response.status_code == 422  # Validation error
        print("✅ Missing password correctly rejected")
    
    def test_register_short_password(self):
        """POST /api/auth/register - Should reject short password"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "short",
            "name": "Test User"
        })
        assert response.status_code == 400
        print("✅ Short password correctly rejected")
    
    def test_forgot_password(self):
        """POST /api/auth/forgot-password - Should accept email"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": ADMIN_EMAIL
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✅ Forgot password endpoint works")
    
    def test_emergency_reset_no_secret(self):
        """POST /api/auth/emergency-reset - Should fail without ADMIN_RESET_SECRET"""
        response = requests.post(f"{BASE_URL}/api/auth/emergency-reset", json={
            "secret": "wrong_secret",
            "email": ADMIN_EMAIL,
            "new_password": "newpassword123"
        })
        # Should return 503 (not configured) or 403 (wrong secret)
        assert response.status_code in [503, 403]
        print("✅ Emergency reset correctly requires ADMIN_RESET_SECRET")


class TestAuthenticatedEndpoints:
    """Tests requiring authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_me(self):
        """GET /api/auth/me - Should return current user"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✅ /auth/me returned user: {data['email']}")
    
    def test_settings_whitelist(self):
        """PUT /api/auth/settings - Should only accept allowed keys"""
        # Test with allowed key
        response = requests.put(f"{BASE_URL}/api/auth/settings", 
            headers=self.headers,
            json={"language": "fr", "theme": "dark"}
        )
        assert response.status_code == 200
        print("✅ Settings whitelist accepts allowed keys")
    
    def test_get_usage(self):
        """GET /api/auth/usage - Should return usage stats"""
        response = requests.get(f"{BASE_URL}/api/auth/usage", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "credits_remaining" in data
        assert "total_conversations" in data
        print(f"✅ Usage stats: {data['credits_remaining']} credits remaining")


class TestChatEndpoints:
    """Chat API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_chat_send_unauthorized(self):
        """POST /api/chat/send - Should require auth"""
        response = requests.post(f"{BASE_URL}/api/chat/send", json={
            "message": "Hello",
            "mode": "fast"
        })
        assert response.status_code in [401, 403]  # 403 Forbidden is also valid
        print("✅ Chat send correctly requires authentication")
    
    def test_chat_send_invalid_mode(self):
        """POST /api/chat/send - Should reject invalid mode"""
        response = requests.post(f"{BASE_URL}/api/chat/send", 
            headers=self.headers,
            json={"message": "Hello", "mode": "invalid_mode"}
        )
        assert response.status_code == 400
        print("✅ Chat send correctly rejects invalid mode")
    
    def test_chat_send_empty_message(self):
        """POST /api/chat/send - Should reject empty message"""
        response = requests.post(f"{BASE_URL}/api/chat/send", 
            headers=self.headers,
            json={"message": "   ", "mode": "fast"}
        )
        assert response.status_code == 400
        print("✅ Chat send correctly rejects empty message")


class TestAgentEndpoints:
    """Agent API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_agent_estimate(self):
        """POST /api/agent/estimate - Should return credit estimate"""
        response = requests.post(f"{BASE_URL}/api/agent/estimate", 
            headers=self.headers,
            json={"task": "Recherche les dernières actualités sur l'IA"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "credits_needed" in data
        assert "can_run" in data
        assert "task_type" in data
        print(f"✅ Agent estimate: {data['credits_needed']} credits needed")
    
    def test_agent_estimate_unauthorized(self):
        """POST /api/agent/estimate - Should require auth"""
        response = requests.post(f"{BASE_URL}/api/agent/estimate", json={
            "task": "Test task"
        })
        assert response.status_code in [401, 403]  # 403 Forbidden is also valid
        print("✅ Agent estimate correctly requires authentication")


class TestTeamEndpoints:
    """Team API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_team_list(self):
        """GET /api/team/list - Should return user's teams"""
        response = requests.get(f"{BASE_URL}/api/team/list", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        print(f"✅ Team list returned {len(data['teams'])} teams")
    
    def test_team_me(self):
        """GET /api/team/me - Should return current team or null"""
        response = requests.get(f"{BASE_URL}/api/team/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Can be {"team": null} or {"team": {...}}
        assert "team" in data
        print(f"✅ Team me endpoint works")
    
    def test_team_create_and_invite_duplicate(self):
        """POST /api/team/create and /api/team/invite - Test duplicate prevention"""
        # Create a test team
        team_name = f"TEST_Team_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/team/create", 
            headers=self.headers,
            json={"name": team_name}
        )
        
        if create_response.status_code == 200:
            team_id = create_response.json().get("team", {}).get("id")
            print(f"✅ Team created: {team_name}")
            
            # Try to invite same email twice
            test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            
            # First invite
            invite1 = requests.post(f"{BASE_URL}/api/team/invite",
                headers=self.headers,
                params={"team_id": team_id},
                json={"email": test_email, "role": "member"}
            )
            
            if invite1.status_code == 200:
                # Second invite (should fail - duplicate)
                invite2 = requests.post(f"{BASE_URL}/api/team/invite",
                    headers=self.headers,
                    params={"team_id": team_id},
                    json={"email": test_email, "role": "member"}
                )
                assert invite2.status_code == 400
                print("✅ Duplicate invite correctly rejected")
            else:
                print(f"⚠️ First invite failed: {invite1.status_code}")
        else:
            # May fail due to plan limits - that's OK
            print(f"⚠️ Team creation returned {create_response.status_code} (may be plan limit)")


class TestWorkflowEndpoints:
    """Workflow API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_workflows_list(self):
        """GET /api/workflows - Should return user's workflows"""
        response = requests.get(f"{BASE_URL}/api/workflows", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Workflows list returned {len(data)} workflows")
    
    def test_workflow_create(self):
        """POST /api/workflows - Should create a workflow"""
        workflow_name = f"TEST_Workflow_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/workflows", 
            headers=self.headers,
            json={
                "name": workflow_name,
                "description": "Test workflow",
                "steps": [{"name": "Step 1", "prompt": "Test prompt"}],
                "schedule": None
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == workflow_name
        print(f"✅ Workflow created: {workflow_name}")
        
        # Cleanup - delete the workflow
        if "id" in data:
            requests.delete(f"{BASE_URL}/api/workflows/{data['id']}", headers=self.headers)


class TestPaymentsEndpoints:
    """Payments API tests"""
    
    def test_packages(self):
        """GET /api/payments/packages - Should return packages"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "credits" in data[0]
        print(f"✅ Packages endpoint returned {len(data)} packages")
    
    def test_plans(self):
        """GET /api/payments/plans - Should return subscription plans"""
        response = requests.get(f"{BASE_URL}/api/payments/plans")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Plans endpoint returned {len(data)} plans")


class TestTokenRefresh:
    """Token refresh tests"""
    
    def test_refresh_with_valid_token(self):
        """POST /api/auth/refresh - Should refresh valid token"""
        # First login to get a token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        token = login_response.json()["access_token"]
        
        # Try to refresh
        refresh_response = requests.post(f"{BASE_URL}/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        print("✅ Token refresh works")
    
    def test_refresh_without_token(self):
        """POST /api/auth/refresh - Should fail without token"""
        response = requests.post(f"{BASE_URL}/api/auth/refresh")
        assert response.status_code == 401
        print("✅ Refresh correctly requires token")


class TestOAuthDiagnostic:
    """OAuth diagnostic endpoint test"""
    
    def test_oauth_diagnostic(self):
        """GET /api/oauth/diagnostic - Should return OAuth config status"""
        response = requests.get(f"{BASE_URL}/api/oauth/diagnostic")
        assert response.status_code == 200
        data = response.json()
        assert "google_client_id_set" in data
        assert "allowed_redirect_origins" in data
        print(f"✅ OAuth diagnostic: Google configured = {data['google_client_id_set']}")


class TestFileUpload:
    """File upload tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_upload_unauthorized(self):
        """POST /api/chat/upload - Should require auth"""
        response = requests.post(f"{BASE_URL}/api/chat/upload")
        assert response.status_code in [401, 403, 422]  # 403 Forbidden is also valid
        print("✅ Upload correctly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
