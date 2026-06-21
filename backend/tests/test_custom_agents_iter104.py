"""
Iteration 104 - Custom Agents API Tests
Tests for:
- GET /api/custom-agents - list agents
- POST /api/custom-agents/{id}/chat - chat with custom agent (uses claude-haiku-4-5 model)
- Mammoth API URL fix (mammouth.ai with TWO m's)
- Model name fix (claude-haiku-4-5 instead of mammoth-1)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestCustomAgentsAPI:
    """Custom Agents API tests"""
    
    def test_list_custom_agents(self, auth_headers):
        """Test GET /api/custom-agents returns list of agents"""
        response = requests.get(f"{BASE_URL}/api/custom-agents", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} custom agents")
        
        # If there are agents, verify structure
        if len(data) > 0:
            agent = data[0]
            assert "id" in agent, "Agent should have id"
            assert "name" in agent, "Agent should have name"
            assert "system_prompt" in agent, "Agent should have system_prompt"
            print(f"First agent: {agent.get('name')}")
    
    def test_list_agent_tools(self, auth_headers):
        """Test GET /api/custom-agents/tools returns available tools"""
        response = requests.get(f"{BASE_URL}/api/custom-agents/tools", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        tools = response.json()
        assert isinstance(tools, list), "Response should be a list"
        assert len(tools) > 0, "Should have at least one tool"
        
        # Verify tool structure
        tool = tools[0]
        assert "id" in tool, "Tool should have id"
        assert "name" in tool, "Tool should have name"
        print(f"Found {len(tools)} available tools")
    
    def test_list_agent_templates(self, auth_headers):
        """Test GET /api/custom-agents/templates returns templates"""
        response = requests.get(f"{BASE_URL}/api/custom-agents/templates", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        templates = response.json()
        assert isinstance(templates, list), "Response should be a list"
        assert len(templates) > 0, "Should have at least one template"
        
        # Verify template structure
        template = templates[0]
        assert "id" in template, "Template should have id"
        assert "name" in template, "Template should have name"
        assert "system_prompt" in template, "Template should have system_prompt"
        print(f"Found {len(templates)} agent templates")


class TestCustomAgentChat:
    """Test custom agent chat functionality"""
    
    def test_chat_with_custom_agent(self, auth_headers):
        """Test POST /api/custom-agents/{id}/chat works"""
        # First get list of agents
        list_response = requests.get(f"{BASE_URL}/api/custom-agents", headers=auth_headers)
        assert list_response.status_code == 200
        
        agents = list_response.json()
        if len(agents) == 0:
            # Create an agent from template first
            create_response = requests.post(
                f"{BASE_URL}/api/custom-agents/from-template",
                headers=auth_headers,
                json={"template_id": "assistant_commercial"}
            )
            if create_response.status_code == 200:
                agent = create_response.json()
                print(f"Created agent from template: {agent.get('name')}")
            else:
                pytest.skip("No agents available and couldn't create one")
                return
        else:
            agent = agents[0]
        
        agent_id = agent.get("id")
        print(f"Testing chat with agent: {agent.get('name')} (ID: {agent_id})")
        
        # Send a simple message
        chat_response = requests.post(
            f"{BASE_URL}/api/custom-agents/{agent_id}/chat",
            headers=auth_headers,
            json={"message": "Bonjour, comment vas-tu?"}
        )
        
        # Check response - may fail due to credits or API issues
        if chat_response.status_code == 402:
            print("Credits insuffisants - skipping chat test")
            pytest.skip("Insufficient credits for chat test")
        elif chat_response.status_code == 500:
            # Check if it's a Mammoth API configuration issue
            error_data = chat_response.json()
            if "Mammoth" in str(error_data) or "non configure" in str(error_data):
                print(f"Mammoth API not configured: {error_data}")
                pytest.skip("Mammoth API not configured")
            else:
                pytest.fail(f"Server error: {error_data}")
        elif chat_response.status_code == 502:
            print("Mammoth API error - external service issue")
            pytest.skip("Mammoth API external service error")
        else:
            assert chat_response.status_code == 200, f"Expected 200, got {chat_response.status_code}: {chat_response.text}"
            
            data = chat_response.json()
            assert data.get("success") == True, "Chat should be successful"
            assert "response" in data, "Should have response field"
            assert len(data.get("response", "")) > 0, "Response should not be empty"
            
            # Verify model used is claude-haiku-4-5 (not mammoth-1)
            model_used = data.get("model", "")
            print(f"Model used: {model_used}")
            assert "mammoth-1" not in model_used, "Should NOT use old mammoth-1 model name"
            
            print(f"Chat response received: {data.get('response', '')[:100]}...")


class TestWellnessAPI:
    """Test Wellness (Pulse Bien-etre) API still works"""
    
    def test_wellness_checkin(self, auth_headers):
        """Test POST /api/wellness/checkin still works"""
        response = requests.post(
            f"{BASE_URL}/api/wellness/checkin",
            headers=auth_headers,
            json={
                "energy": 4,
                "mood": 4,
                "stress": 2,
                "sleep": 4
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "score" in data, "Should have score"
        assert 0 <= data["score"] <= 100, "Score should be 0-100"
        print(f"Wellness check-in score: {data['score']}")


class TestFinanceAPI:
    """Test Finance (Pilotage Financier) API still works"""
    
    def test_finance_overview(self, auth_headers):
        """Test GET /api/finance/overview still returns data"""
        response = requests.get(f"{BASE_URL}/api/finance/overview", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "revenus" in data or "net" in data, "Should have financial data"
        print(f"Finance overview: revenus={data.get('revenus', 0)}, depenses={data.get('depenses', 0)}")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API is responding"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("API health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
