"""
Iteration 116 - Testing P0/P1 fixes:
1. Agent deactivated should NOT be usable (is_active check in backend)
2. ChatGPT BYOK moved to first position in mode selector
3. Diagnostic inline in MonActivitePage (no redirect to /app/diagnostic)
4. 'Demander à l'IA' button passes context to chat
5. Structuration inline (no redirect to /app/structuration)
6. GettingStarted modal auto-shows for incomplete users
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
        print("PASS: Health endpoint returns 200")
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"PASS: Admin login successful, token received")
        return data["access_token"]


class TestCustomAgentIsActiveCheck:
    """Test that deactivated agents cannot be used for chat"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_list_agents(self, auth_headers):
        """Test listing custom agents"""
        response = requests.get(f"{BASE_URL}/api/custom-agents", headers=auth_headers)
        assert response.status_code == 200
        agents = response.json()
        print(f"PASS: Listed {len(agents)} custom agents")
        return agents
    
    def test_create_agent_for_testing(self, auth_headers):
        """Create a test agent for is_active testing"""
        response = requests.post(f"{BASE_URL}/api/custom-agents", headers=auth_headers, json={
            "name": "TEST_Agent_IsActive_Check",
            "description": "Test agent for is_active verification",
            "system_prompt": "Tu es un assistant de test.",
            "tools": [],
            "model_preference": "auto",
            "temperature": 0.7,
            "max_tokens": 1024
        })
        # May fail if agent limit reached, that's ok
        if response.status_code == 201:
            agent = response.json()
            print(f"PASS: Created test agent with id={agent['id']}")
            return agent
        elif response.status_code == 400:
            print(f"INFO: Agent limit reached, will use existing agent")
            return None
        else:
            print(f"INFO: Create agent returned {response.status_code}: {response.text}")
            return None
    
    def test_deactivate_agent_and_try_chat(self, auth_headers):
        """
        CRITICAL TEST: Deactivate an agent and verify chat returns 403
        This tests the is_active check at line 287 of custom_agents.py
        """
        # First, list agents to find one to test
        list_response = requests.get(f"{BASE_URL}/api/custom-agents", headers=auth_headers)
        assert list_response.status_code == 200
        agents = list_response.json()
        
        if not agents:
            # Create a test agent
            create_response = requests.post(f"{BASE_URL}/api/custom-agents", headers=auth_headers, json={
                "name": "TEST_Deactivation_Check",
                "description": "Test agent for deactivation check",
                "system_prompt": "Tu es un assistant de test.",
                "tools": [],
                "model_preference": "auto"
            })
            if create_response.status_code == 201:
                agents = [create_response.json()]
            else:
                pytest.skip("No agents available and cannot create one")
        
        test_agent = agents[0]
        agent_id = test_agent["id"]
        print(f"Testing with agent: {test_agent['name']} (id={agent_id})")
        
        # Step 1: Deactivate the agent
        deactivate_response = requests.put(
            f"{BASE_URL}/api/custom-agents/{agent_id}",
            headers=auth_headers,
            json={"is_active": False}
        )
        assert deactivate_response.status_code == 200
        updated_agent = deactivate_response.json()
        assert updated_agent["is_active"] == False
        print(f"PASS: Agent deactivated successfully (is_active=False)")
        
        # Step 2: Try to chat with deactivated agent - should return 403
        chat_response = requests.post(
            f"{BASE_URL}/api/custom-agents/{agent_id}/chat",
            headers=auth_headers,
            json={"message": "Hello, this should fail"}
        )
        
        # Verify 403 is returned for deactivated agent
        assert chat_response.status_code == 403, f"Expected 403 for deactivated agent, got {chat_response.status_code}"
        error_data = chat_response.json()
        assert "desactive" in error_data.get("detail", "").lower() or "inactive" in error_data.get("detail", "").lower()
        print(f"PASS: Chat with deactivated agent correctly returns 403: {error_data.get('detail')}")
        
        # Step 3: Reactivate the agent for cleanup
        reactivate_response = requests.put(
            f"{BASE_URL}/api/custom-agents/{agent_id}",
            headers=auth_headers,
            json={"is_active": True}
        )
        assert reactivate_response.status_code == 200
        print(f"PASS: Agent reactivated for cleanup")
    
    def test_active_agent_can_chat(self, auth_headers):
        """Verify that an active agent CAN be used for chat (control test)"""
        # List agents
        list_response = requests.get(f"{BASE_URL}/api/custom-agents", headers=auth_headers)
        assert list_response.status_code == 200
        agents = list_response.json()
        
        if not agents:
            pytest.skip("No agents available for testing")
        
        # Find an active agent
        active_agent = next((a for a in agents if a.get("is_active", True)), None)
        if not active_agent:
            # Activate the first agent
            agent_id = agents[0]["id"]
            requests.put(f"{BASE_URL}/api/custom-agents/{agent_id}", headers=auth_headers, json={"is_active": True})
            active_agent = agents[0]
        
        agent_id = active_agent["id"]
        
        # Try to chat - should NOT return 403 (may return other errors like 402 for credits, but not 403)
        chat_response = requests.post(
            f"{BASE_URL}/api/custom-agents/{agent_id}/chat",
            headers=auth_headers,
            json={"message": "Test message"}
        )
        
        # Should not be 403 (deactivated error)
        assert chat_response.status_code != 403 or "desactive" not in chat_response.text.lower(), \
            f"Active agent should not return 403 deactivated error"
        print(f"PASS: Active agent chat returns {chat_response.status_code} (not 403 deactivated)")


class TestChatConfigBYOKFirst:
    """Test that chatConfig.js has BYOK as first mode"""
    
    def test_byok_is_first_in_mainmodes(self):
        """
        Verify BYOK is the first item in mainModes array
        This is a code review test - we check the file content
        """
        # Read the chatConfig.js file
        config_path = "/app/frontend/src/components/chat/chatConfig.js"
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Find the mainModes array
        import re
        # Look for the first mode in the array
        match = re.search(r"export const mainModes.*?\[\s*\{[^}]*id:\s*['\"](\w+)['\"]", content, re.DOTALL)
        
        assert match, "Could not find mainModes array in chatConfig.js"
        first_mode_id = match.group(1)
        
        assert first_mode_id == "byok", f"Expected first mode to be 'byok', got '{first_mode_id}'"
        print(f"PASS: BYOK is the first mode in mainModes array")


class TestMonActivitePageInlineDiagnostic:
    """Test that MonActivitePage has inline diagnostic (no redirect)"""
    
    def test_diagnostic_inline_in_monactivite(self):
        """
        Verify MonActivitePage has inline diagnostic grid
        Check for Organisation, Finances, Energie, Clients buttons
        """
        page_path = "/app/frontend/src/components/MonActivitePage.js"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check for inline diagnostic elements
        diagnostic_items = ['Organisation', 'Finances', 'Energie', 'Clients']
        for item in diagnostic_items:
            assert item in content, f"Missing diagnostic item: {item}"
        
        # Check for data-testid for diagnostic buttons
        assert 'data-testid={`diag-' in content, "Missing data-testid for diagnostic buttons"
        
        # Verify NO redirect to /app/diagnostic
        assert "navigate('/app/diagnostic')" not in content, "Found redirect to /app/diagnostic - should be inline"
        
        print(f"PASS: MonActivitePage has inline diagnostic with all 4 items")
    
    def test_ask_ia_button_exists(self):
        """
        Verify 'Demander a l'IA' button exists with data-testid='ask-ia-btn'
        """
        page_path = "/app/frontend/src/components/MonActivitePage.js"
        with open(page_path, 'r') as f:
            content = f.read()
        
        assert "data-testid=\"ask-ia-btn\"" in content, "Missing data-testid='ask-ia-btn' for IA button"
        assert "Demander a l'IA" in content, "Missing 'Demander a l'IA' button text"
        
        print(f"PASS: 'Demander a l'IA' button exists with correct data-testid")
    
    def test_ask_ia_passes_context(self):
        """
        Verify 'Demander a l'IA' button passes context to chat
        Should use navigate('/app', { state: { prefillMessage: ... } })
        """
        page_path = "/app/frontend/src/components/MonActivitePage.js"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check for context passing via state
        assert "prefillMessage" in content, "Missing prefillMessage in navigate state"
        assert "navigate('/app'" in content, "Missing navigate to /app"
        
        print(f"PASS: 'Demander a l'IA' button passes context via prefillMessage")


class TestStructurationInline:
    """Test that Structuration is inline in MonActivitePage (no redirect)"""
    
    def test_structuration_inline_pillars(self):
        """
        Verify MonActivitePage has inline structuration pillars
        Should have clickable pillars instead of 'Ouvrir le plan complet' redirect
        """
        page_path = "/app/frontend/src/components/MonActivitePage.js"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check for structuration section
        assert "Plan de Structuration" in content or "section-structuration" in content, \
            "Missing Structuration section"
        
        # Check for inline pillars
        pillar_items = ['Clarte', 'Energie', 'Alignement', 'Rentabilite']
        found_pillars = sum(1 for item in pillar_items if item in content)
        assert found_pillars >= 3, f"Expected at least 3 pillar items, found {found_pillars}"
        
        # Verify NO redirect to /app/structuration
        assert "navigate('/app/structuration')" not in content, \
            "Found redirect to /app/structuration - should be inline"
        
        # Check for pillar data-testids
        assert "structuration-pillar-" in content, "Missing data-testid for structuration pillars"
        
        print(f"PASS: Structuration is inline with clickable pillars")


class TestGettingStartedAutoShow:
    """Test that GettingStarted modal auto-shows for incomplete users"""
    
    def test_getting_started_auto_show_logic(self):
        """
        Verify DashboardLayout has auto-show logic for GettingStarted modal
        Should check localStorage for incomplete steps
        """
        layout_path = "/app/frontend/src/components/DashboardLayout.js"
        with open(layout_path, 'r') as f:
            content = f.read()
        
        # Check for auto-show logic (lines 103-115 mentioned in review request)
        assert "zayado_gs_" in content, "Missing localStorage key for GettingStarted"
        assert "setShowGettingStartedModal" in content, "Missing setShowGettingStartedModal"
        
        # Check for incomplete steps check
        assert "completed.length" in content or "totalSteps" in content, \
            "Missing check for incomplete steps"
        
        print(f"PASS: GettingStarted auto-show logic exists in DashboardLayout")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
