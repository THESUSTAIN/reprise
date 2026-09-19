"""
Iteration 105 - Testing NEW features:
1. Agent dropdown in chat bar (from Bot icon)
2. Persistent agent memory (AgentMessage model, chat history saved per agent)
3. Team agent sharing (is_public flag, shared agents visible to team members)
4. Workflow agent steps (multi-step chaining with agent steps)
5. Settings > Mes Agents (CRUD only, no chat)
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
        data = response.json()
        # API returns access_token, not token
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed - skipping tests")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestCustomAgentsPersistentMemory:
    """Test persistent agent memory (AgentMessage model)"""
    
    def test_get_agent_history_endpoint_exists(self, headers):
        """Test GET /api/custom-agents/{id}/history endpoint exists"""
        # First get list of agents
        agents_res = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        assert agents_res.status_code == 200
        agents = agents_res.json()
        
        if len(agents) == 0:
            pytest.skip("No agents available for testing")
        
        agent_id = agents[0]["id"]
        
        # Test history endpoint
        history_res = requests.get(f"{BASE_URL}/api/custom-agents/{agent_id}/history", headers=headers)
        assert history_res.status_code == 200
        history = history_res.json()
        assert isinstance(history, list)
        print(f"Agent {agents[0]['name']} has {len(history)} messages in history")
    
    def test_agent_history_returns_messages_with_role_and_content(self, headers):
        """Test that history returns messages with role and content fields"""
        agents_res = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        agents = agents_res.json()
        
        if len(agents) == 0:
            pytest.skip("No agents available for testing")
        
        agent_id = agents[0]["id"]
        history_res = requests.get(f"{BASE_URL}/api/custom-agents/{agent_id}/history", headers=headers)
        history = history_res.json()
        
        if len(history) > 0:
            msg = history[0]
            assert "role" in msg, "Message should have 'role' field"
            assert "content" in msg, "Message should have 'content' field"
            assert msg["role"] in ["user", "assistant"], f"Role should be 'user' or 'assistant', got {msg['role']}"
            print(f"First message: role={msg['role']}, content_length={len(msg['content'])}")
    
    def test_clear_agent_history_endpoint(self, headers):
        """Test DELETE /api/custom-agents/{id}/history clears history"""
        agents_res = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        agents = agents_res.json()
        
        if len(agents) == 0:
            pytest.skip("No agents available for testing")
        
        agent_id = agents[0]["id"]
        
        # Clear history
        clear_res = requests.delete(f"{BASE_URL}/api/custom-agents/{agent_id}/history", headers=headers)
        assert clear_res.status_code == 200
        data = clear_res.json()
        assert data.get("status") == "ok"
        
        # Verify history is empty
        history_res = requests.get(f"{BASE_URL}/api/custom-agents/{agent_id}/history", headers=headers)
        history = history_res.json()
        assert len(history) == 0, "History should be empty after clearing"
        print("History cleared successfully")


class TestCustomAgentsSharedField:
    """Test team agent sharing (is_public flag, shared field in response)"""
    
    def test_agents_list_includes_shared_field(self, headers):
        """Test GET /api/custom-agents includes 'shared' field in response"""
        response = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        assert response.status_code == 200
        agents = response.json()
        
        if len(agents) == 0:
            pytest.skip("No agents available for testing")
        
        agent = agents[0]
        assert "shared" in agent, "Agent response should include 'shared' field"
        assert isinstance(agent["shared"], bool), "'shared' field should be boolean"
        print(f"Agent '{agent['name']}' shared={agent['shared']}")
    
    def test_agent_has_is_public_field(self, headers):
        """Test that agents have is_public field"""
        response = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        agents = response.json()
        
        if len(agents) == 0:
            pytest.skip("No agents available for testing")
        
        agent = agents[0]
        assert "is_public" in agent, "Agent response should include 'is_public' field"
        assert isinstance(agent["is_public"], bool), "'is_public' field should be boolean"
        print(f"Agent '{agent['name']}' is_public={agent['is_public']}")
    
    def test_create_agent_with_is_public(self, headers):
        """Test creating agent with is_public flag"""
        agent_data = {
            "name": "TEST_Shared_Agent",
            "description": "Test agent for sharing",
            "system_prompt": "Tu es un assistant de test.",
            "is_public": True
        }
        
        response = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers, json=agent_data)
        assert response.status_code == 200
        agent = response.json()
        assert agent["is_public"] == True, "Agent should be created with is_public=True"
        assert agent["shared"] == False, "Own agent should have shared=False"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/custom-agents/{agent['id']}", headers=headers)
        print("Created and deleted test agent with is_public=True")


class TestCustomAgentsChatEndpoint:
    """Test POST /api/custom-agents/{id}/chat saves messages"""
    
    def test_chat_endpoint_exists(self, headers):
        """Test POST /api/custom-agents/{id}/chat endpoint exists"""
        agents_res = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        agents = agents_res.json()
        
        if len(agents) == 0:
            pytest.skip("No agents available for testing")
        
        agent_id = agents[0]["id"]
        
        # Test chat endpoint (may fail due to credits but should return proper error)
        chat_res = requests.post(
            f"{BASE_URL}/api/custom-agents/{agent_id}/chat",
            headers=headers,
            json={"message": "Bonjour, test de memoire persistante"}
        )
        
        # Accept 200 (success), 402 (insufficient credits), or 502 (API error)
        assert chat_res.status_code in [200, 402, 502], f"Unexpected status: {chat_res.status_code}"
        
        if chat_res.status_code == 200:
            data = chat_res.json()
            assert "success" in data
            assert "response" in data
            print(f"Chat response: success={data['success']}, response_length={len(data.get('response', ''))}")
        elif chat_res.status_code == 402:
            print("Chat endpoint works but insufficient credits")
        else:
            print(f"Chat endpoint returned {chat_res.status_code}")


class TestWorkflowAgentSteps:
    """Test workflow with agent step type"""
    
    def test_create_workflow_with_agent_step(self, headers):
        """Test creating workflow with agent step type"""
        # First get an agent ID
        agents_res = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        agents = agents_res.json()
        
        agent_id = agents[0]["id"] if len(agents) > 0 else None
        
        workflow_data = {
            "name": "TEST_Workflow_Agent_Step",
            "description": "Test workflow with agent step",
            "steps": [
                {"type": "prompt", "prompt": "Analyse cette demande", "label": "Etape 1"},
                {"type": "agent", "agent_id": agent_id, "prompt": "Utilise l'agent pour repondre", "label": "Etape Agent"} if agent_id else {"type": "prompt", "prompt": "Step 2", "label": "Etape 2"}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/workflows", headers=headers, json=workflow_data)
        assert response.status_code == 200
        workflow = response.json()
        assert workflow["name"] == "TEST_Workflow_Agent_Step"
        assert len(workflow["steps"]) == 2
        
        workflow_id = workflow["id"]
        
        # Verify workflow was created
        get_res = requests.get(f"{BASE_URL}/api/workflows/{workflow_id}", headers=headers)
        assert get_res.status_code == 200
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/workflows/{workflow_id}", headers=headers)
        print(f"Created and deleted workflow with agent step (agent_id={agent_id})")
    
    def test_workflow_run_with_agent_step(self, headers):
        """Test running workflow with agent step (may fail due to credits)"""
        agents_res = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        agents = agents_res.json()
        
        if len(agents) == 0:
            pytest.skip("No agents available for testing")
        
        agent_id = agents[0]["id"]
        
        workflow_data = {
            "name": "TEST_Run_Agent_Workflow",
            "description": "Test running workflow with agent step",
            "steps": [
                {"type": "agent", "agent_id": agent_id, "prompt": "Dis bonjour", "label": "Agent Step"}
            ]
        }
        
        create_res = requests.post(f"{BASE_URL}/api/workflows", headers=headers, json=workflow_data)
        assert create_res.status_code == 200
        workflow_id = create_res.json()["id"]
        
        # Run workflow
        run_res = requests.post(f"{BASE_URL}/api/workflows/{workflow_id}/run", headers=headers)
        # Accept various status codes (may fail due to credits or API)
        assert run_res.status_code in [200, 402, 500, 502]
        
        if run_res.status_code == 200:
            data = run_res.json()
            assert "status" in data
            assert "results" in data or "step_results" in data
            print(f"Workflow run status: {data['status']}")
        else:
            print(f"Workflow run returned {run_res.status_code} (may be due to credits/API)")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/workflows/{workflow_id}", headers=headers)


class TestCustomAgentsCRUD:
    """Test Settings > Mes Agents CRUD operations"""
    
    def test_list_agents(self, headers):
        """Test GET /api/custom-agents returns list"""
        response = requests.get(f"{BASE_URL}/api/custom-agents", headers=headers)
        assert response.status_code == 200
        agents = response.json()
        assert isinstance(agents, list)
        print(f"Found {len(agents)} agents")
    
    def test_create_agent(self, headers):
        """Test POST /api/custom-agents creates agent"""
        agent_data = {
            "name": "TEST_CRUD_Agent",
            "description": "Test agent for CRUD",
            "system_prompt": "Tu es un assistant de test.",
            "avatar": "bot",
            "color": "#1D4E8A"
        }
        
        response = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers, json=agent_data)
        assert response.status_code == 200
        agent = response.json()
        assert agent["name"] == "TEST_CRUD_Agent"
        assert "id" in agent
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/custom-agents/{agent['id']}", headers=headers)
        print("Created and deleted test agent")
    
    def test_update_agent(self, headers):
        """Test PUT /api/custom-agents/{id} updates agent"""
        # Create agent
        agent_data = {
            "name": "TEST_Update_Agent",
            "description": "Original description",
            "system_prompt": "Tu es un assistant."
        }
        create_res = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers, json=agent_data)
        agent_id = create_res.json()["id"]
        
        # Update agent
        update_data = {"description": "Updated description"}
        update_res = requests.put(f"{BASE_URL}/api/custom-agents/{agent_id}", headers=headers, json=update_data)
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["description"] == "Updated description"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/custom-agents/{agent_id}", headers=headers)
        print("Updated and deleted test agent")
    
    def test_delete_agent(self, headers):
        """Test DELETE /api/custom-agents/{id} deletes agent"""
        # Create agent
        agent_data = {
            "name": "TEST_Delete_Agent",
            "system_prompt": "Tu es un assistant."
        }
        create_res = requests.post(f"{BASE_URL}/api/custom-agents", headers=headers, json=agent_data)
        agent_id = create_res.json()["id"]
        
        # Delete agent
        delete_res = requests.delete(f"{BASE_URL}/api/custom-agents/{agent_id}", headers=headers)
        assert delete_res.status_code == 200
        
        # Verify deleted
        get_res = requests.get(f"{BASE_URL}/api/custom-agents/{agent_id}", headers=headers)
        assert get_res.status_code == 404
        print("Deleted test agent and verified removal")


class TestAgentTools:
    """Test agent tools endpoint"""
    
    def test_get_available_tools(self, headers):
        """Test GET /api/custom-agents/tools returns available tools"""
        response = requests.get(f"{BASE_URL}/api/custom-agents/tools", headers=headers)
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check tool structure
        tool = tools[0]
        assert "id" in tool
        assert "name" in tool
        assert "description" in tool
        print(f"Found {len(tools)} available tools")


class TestAgentTemplates:
    """Test agent templates endpoint"""
    
    def test_get_templates(self, headers):
        """Test GET /api/custom-agents/templates returns templates"""
        response = requests.get(f"{BASE_URL}/api/custom-agents/templates", headers=headers)
        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Check template structure
        template = templates[0]
        assert "id" in template
        assert "name" in template
        assert "system_prompt" in template
        print(f"Found {len(templates)} agent templates")
    
    def test_create_from_template(self, headers):
        """Test POST /api/custom-agents/from-template creates agent from template"""
        # Get templates
        templates_res = requests.get(f"{BASE_URL}/api/custom-agents/templates", headers=headers)
        templates = templates_res.json()
        
        if len(templates) == 0:
            pytest.skip("No templates available")
        
        template_id = templates[0]["id"]
        
        # Create from template
        response = requests.post(
            f"{BASE_URL}/api/custom-agents/from-template",
            headers=headers,
            json={"template_id": template_id}
        )
        assert response.status_code == 200
        agent = response.json()
        assert "id" in agent
        assert agent["name"] == templates[0]["name"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/custom-agents/{agent['id']}", headers=headers)
        print(f"Created agent from template '{template_id}' and deleted")


class TestHealthAndBasicAPIs:
    """Test basic API health"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
    
    def test_auth_login(self):
        """Test login endpoint"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        assert "user" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
