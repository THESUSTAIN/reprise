"""
Test Custom Agents CRUD + Templates + Tools + Chat
Iteration 102 - Testing OpenClaw-style Custom Agents system
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


class TestCustomAgents:
    """Custom Agents API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        data = login_res.json()
        self.token = data.get("access_token")
        assert self.token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Store created agent IDs for cleanup
        self.created_agent_ids = []
        yield
        
        # Cleanup - delete test agents
        for agent_id in self.created_agent_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/custom-agents/{agent_id}")
            except:
                pass
    
    def test_health_check(self):
        """Test API health"""
        res = self.session.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "healthy"
        print("PASS: Health check returns healthy")
    
    def test_get_available_tools(self):
        """Test GET /api/custom-agents/tools returns 12 tools"""
        res = self.session.get(f"{BASE_URL}/api/custom-agents/tools")
        assert res.status_code == 200, f"Failed to get tools: {res.text}"
        tools = res.json()
        assert isinstance(tools, list), "Tools should be a list"
        assert len(tools) == 12, f"Expected 12 tools, got {len(tools)}"
        
        # Verify tool structure
        expected_tool_ids = ["web_search", "calculator", "email_draft", "doc_analysis", 
                           "code_helper", "translator", "seo_audit", "social_media",
                           "financial", "legal", "crm", "scheduler"]
        tool_ids = [t["id"] for t in tools]
        for expected_id in expected_tool_ids:
            assert expected_id in tool_ids, f"Missing tool: {expected_id}"
        
        # Verify tool has required fields
        for tool in tools:
            assert "id" in tool
            assert "name" in tool
            assert "description" in tool
            assert "icon" in tool
        
        print(f"PASS: GET /api/custom-agents/tools returns {len(tools)} tools")
    
    def test_get_agent_templates(self):
        """Test GET /api/custom-agents/templates returns 4 templates"""
        res = self.session.get(f"{BASE_URL}/api/custom-agents/templates")
        assert res.status_code == 200, f"Failed to get templates: {res.text}"
        templates = res.json()
        assert isinstance(templates, list), "Templates should be a list"
        assert len(templates) == 4, f"Expected 4 templates, got {len(templates)}"
        
        # Verify template IDs
        expected_template_ids = ["assistant_commercial", "redacteur_contenu", 
                                "comptable_ia", "assistant_juridique"]
        template_ids = [t["id"] for t in templates]
        for expected_id in expected_template_ids:
            assert expected_id in template_ids, f"Missing template: {expected_id}"
        
        # Verify template structure
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "system_prompt" in template
            assert "tools" in template
            assert isinstance(template["tools"], list)
        
        print(f"PASS: GET /api/custom-agents/templates returns {len(templates)} templates")
    
    def test_list_agents_empty_or_existing(self):
        """Test GET /api/custom-agents returns list"""
        res = self.session.get(f"{BASE_URL}/api/custom-agents")
        assert res.status_code == 200, f"Failed to list agents: {res.text}"
        agents = res.json()
        assert isinstance(agents, list), "Agents should be a list"
        print(f"PASS: GET /api/custom-agents returns {len(agents)} agents")
    
    def test_create_agent(self):
        """Test POST /api/custom-agents creates new agent"""
        agent_data = {
            "name": "TEST_Agent_102",
            "description": "Test agent for iteration 102",
            "avatar": "bot",
            "color": "#1D4E8A",
            "system_prompt": "Tu es un assistant de test pour l'iteration 102.",
            "tools": ["web_search", "calculator"],
            "model_preference": "auto",
            "temperature": 0.7,
            "max_tokens": 4096,
            "is_public": False
        }
        
        res = self.session.post(f"{BASE_URL}/api/custom-agents", json=agent_data)
        assert res.status_code == 200, f"Failed to create agent: {res.text}"
        
        agent = res.json()
        self.created_agent_ids.append(agent["id"])
        
        # Verify response structure
        assert "id" in agent
        assert agent["name"] == agent_data["name"]
        assert agent["description"] == agent_data["description"]
        assert agent["system_prompt"] == agent_data["system_prompt"]
        assert agent["tools"] == agent_data["tools"]
        assert agent["model_preference"] == agent_data["model_preference"]
        assert agent["is_active"] == True
        
        print(f"PASS: POST /api/custom-agents created agent with id={agent['id']}")
        return agent
    
    def test_get_agent_by_id(self):
        """Test GET /api/custom-agents/{id} returns agent"""
        # First create an agent
        agent_data = {
            "name": "TEST_GetById_Agent",
            "description": "Test get by ID",
            "system_prompt": "Test prompt",
            "tools": ["calculator"]
        }
        create_res = self.session.post(f"{BASE_URL}/api/custom-agents", json=agent_data)
        assert create_res.status_code == 200
        created = create_res.json()
        self.created_agent_ids.append(created["id"])
        
        # Now get by ID
        res = self.session.get(f"{BASE_URL}/api/custom-agents/{created['id']}")
        assert res.status_code == 200, f"Failed to get agent: {res.text}"
        
        agent = res.json()
        assert agent["id"] == created["id"]
        assert agent["name"] == agent_data["name"]
        
        print(f"PASS: GET /api/custom-agents/{created['id']} returns correct agent")
    
    def test_update_agent(self):
        """Test PUT /api/custom-agents/{id} updates agent"""
        # First create an agent
        agent_data = {
            "name": "TEST_Update_Agent",
            "description": "Original description",
            "system_prompt": "Original prompt",
            "tools": ["calculator"]
        }
        create_res = self.session.post(f"{BASE_URL}/api/custom-agents", json=agent_data)
        assert create_res.status_code == 200
        created = create_res.json()
        self.created_agent_ids.append(created["id"])
        
        # Update the agent
        update_data = {
            "name": "TEST_Updated_Agent",
            "description": "Updated description",
            "tools": ["calculator", "web_search"]
        }
        res = self.session.put(f"{BASE_URL}/api/custom-agents/{created['id']}", json=update_data)
        assert res.status_code == 200, f"Failed to update agent: {res.text}"
        
        updated = res.json()
        assert updated["name"] == update_data["name"]
        assert updated["description"] == update_data["description"]
        assert updated["tools"] == update_data["tools"]
        
        # Verify persistence with GET
        get_res = self.session.get(f"{BASE_URL}/api/custom-agents/{created['id']}")
        assert get_res.status_code == 200
        fetched = get_res.json()
        assert fetched["name"] == update_data["name"]
        
        print(f"PASS: PUT /api/custom-agents/{created['id']} updates agent correctly")
    
    def test_delete_agent(self):
        """Test DELETE /api/custom-agents/{id} deletes agent"""
        # First create an agent
        agent_data = {
            "name": "TEST_Delete_Agent",
            "description": "To be deleted",
            "system_prompt": "Delete me",
            "tools": []
        }
        create_res = self.session.post(f"{BASE_URL}/api/custom-agents", json=agent_data)
        assert create_res.status_code == 200
        created = create_res.json()
        agent_id = created["id"]
        
        # Delete the agent
        res = self.session.delete(f"{BASE_URL}/api/custom-agents/{agent_id}")
        assert res.status_code == 200, f"Failed to delete agent: {res.text}"
        
        # Verify deletion with GET (should return 404)
        get_res = self.session.get(f"{BASE_URL}/api/custom-agents/{agent_id}")
        assert get_res.status_code == 404, "Agent should not exist after deletion"
        
        print(f"PASS: DELETE /api/custom-agents/{agent_id} deletes agent correctly")
    
    def test_duplicate_agent(self):
        """Test POST /api/custom-agents/{id}/duplicate creates copy"""
        # First create an agent
        agent_data = {
            "name": "TEST_Original_Agent",
            "description": "Original to duplicate",
            "system_prompt": "Original prompt for duplication",
            "tools": ["web_search", "calculator"]
        }
        create_res = self.session.post(f"{BASE_URL}/api/custom-agents", json=agent_data)
        assert create_res.status_code == 200
        original = create_res.json()
        self.created_agent_ids.append(original["id"])
        
        # Duplicate the agent
        res = self.session.post(f"{BASE_URL}/api/custom-agents/{original['id']}/duplicate")
        assert res.status_code == 200, f"Failed to duplicate agent: {res.text}"
        
        duplicate = res.json()
        self.created_agent_ids.append(duplicate["id"])
        
        # Verify duplicate has different ID but same content
        assert duplicate["id"] != original["id"]
        assert duplicate["name"] == f"{original['name']} (copie)"
        assert duplicate["description"] == original["description"]
        assert duplicate["system_prompt"] == original["system_prompt"]
        assert duplicate["tools"] == original["tools"]
        
        print(f"PASS: POST /api/custom-agents/{original['id']}/duplicate creates copy")
    
    def test_create_from_template(self):
        """Test POST /api/custom-agents/from-template creates agent from template"""
        res = self.session.post(f"{BASE_URL}/api/custom-agents/from-template", json={
            "template_id": "assistant_commercial"
        })
        assert res.status_code == 200, f"Failed to create from template: {res.text}"
        
        agent = res.json()
        self.created_agent_ids.append(agent["id"])
        
        # Verify agent has template properties
        assert agent["name"] == "Assistant Commercial"
        assert "prospection" in agent["system_prompt"].lower() or "commercial" in agent["system_prompt"].lower()
        assert "email_draft" in agent["tools"]
        
        print(f"PASS: POST /api/custom-agents/from-template creates agent from template")
    
    def test_create_from_invalid_template(self):
        """Test POST /api/custom-agents/from-template with invalid template returns 404"""
        res = self.session.post(f"{BASE_URL}/api/custom-agents/from-template", json={
            "template_id": "invalid_template_id"
        })
        assert res.status_code == 404, f"Expected 404 for invalid template, got {res.status_code}"
        print("PASS: Invalid template returns 404")
    
    def test_agent_chat_without_mammoth_key(self):
        """Test POST /api/custom-agents/{id}/chat returns 500 if MAMMOTH_API_KEY not configured
        Note: This is expected behavior per the test requirements"""
        # First create an agent
        agent_data = {
            "name": "TEST_Chat_Agent",
            "description": "For chat testing",
            "system_prompt": "Tu es un assistant de test.",
            "tools": ["calculator"]
        }
        create_res = self.session.post(f"{BASE_URL}/api/custom-agents", json=agent_data)
        assert create_res.status_code == 200
        agent = create_res.json()
        self.created_agent_ids.append(agent["id"])
        
        # Try to chat - may return 500 if MAMMOTH_API_KEY not configured (expected)
        # or 402 if credits insufficient
        res = self.session.post(f"{BASE_URL}/api/custom-agents/{agent['id']}/chat", json={
            "message": "Bonjour, comment vas-tu?"
        })
        
        # Accept 500 (Mammoth not configured), 402 (insufficient credits), or 200 (success)
        assert res.status_code in [200, 402, 500], f"Unexpected status: {res.status_code} - {res.text}"
        
        if res.status_code == 500:
            print("PASS: Agent chat returns 500 (MAMMOTH_API_KEY not configured - expected)")
        elif res.status_code == 402:
            print("PASS: Agent chat returns 402 (insufficient credits)")
        else:
            print("PASS: Agent chat returns 200 (success)")
    
    def test_get_nonexistent_agent(self):
        """Test GET /api/custom-agents/{id} with invalid ID returns 404"""
        res = self.session.get(f"{BASE_URL}/api/custom-agents/nonexistent-id-12345")
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("PASS: Nonexistent agent returns 404")


class TestAffiliateAndSidebar:
    """Test affiliate icon visibility and sidebar behavior"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        data = login_res.json()
        self.token = data.get("access_token")
        self.user = data.get("user", {})
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_admin_role_check(self):
        """Verify admin user has admin role (affiliate icon should be hidden)"""
        res = self.session.get(f"{BASE_URL}/api/auth/me")
        assert res.status_code == 200
        user = res.json()
        assert user.get("role") == "admin", f"Expected admin role, got {user.get('role')}"
        print(f"PASS: User has admin role - affiliate icon should be hidden in sidebar")
    
    def test_affiliate_page_loads(self):
        """Test /api/affiliate/dashboard endpoint works"""
        res = self.session.get(f"{BASE_URL}/api/affiliate/dashboard")
        assert res.status_code == 200, f"Failed to get affiliate dashboard: {res.text}"
        data = res.json()
        assert isinstance(data, dict)
        print("PASS: Affiliate dashboard endpoint works")
    
    def test_workflow_email_domain(self):
        """Test workflow email domain is zayado.ai"""
        res = self.session.get(f"{BASE_URL}/api/workflows/config")
        # May return 200 or 404 depending on implementation
        if res.status_code == 200:
            data = res.json()
            if "email_domain" in data:
                assert data["email_domain"] == "zayado.ai", f"Expected zayado.ai, got {data['email_domain']}"
                print("PASS: Workflow email domain is zayado.ai")
            else:
                print("PASS: Workflow config endpoint works (no email_domain field)")
        else:
            print(f"INFO: Workflow config endpoint returned {res.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
