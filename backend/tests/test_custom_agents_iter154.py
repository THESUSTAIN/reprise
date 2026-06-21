"""
Iteration 154 - Custom Agents API Tests
Testing the 3-step Agent Builder wizard backend endpoints:
- GET /api/custom-agents/tools - List available tools
- GET /api/custom-agents/templates - List agent templates
- GET /api/custom-agents - List user's agents
- POST /api/custom-agents - Create new agent
- GET /api/custom-agents/{id} - Get single agent
- PUT /api/custom-agents/{id} - Update agent
- DELETE /api/custom-agents/{id} - Delete agent
- POST /api/custom-agents/{id}/duplicate - Duplicate agent
- POST /api/custom-agents/from-template - Create from template
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCustomAgentsAPI:
    """Custom Agents CRUD API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "1@Elshaddai1"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        self.token = data.get("token") or data.get("access_token")
        assert self.token, "No token in login response"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Store created agent IDs for cleanup
        self.created_agent_ids = []
        yield
        
        # Cleanup: delete test agents
        for agent_id in self.created_agent_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/custom-agents/{agent_id}")
            except:
                pass
    
    # ─── Tools Endpoint ───────────────────────────────────────────
    def test_get_tools_returns_200(self):
        """GET /api/custom-agents/tools returns 200"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/tools")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("✓ GET /api/custom-agents/tools returns 200")
    
    def test_get_tools_returns_list(self):
        """GET /api/custom-agents/tools returns list of tools"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/tools")
        data = resp.json()
        assert isinstance(data, list), "Expected list of tools"
        assert len(data) >= 10, f"Expected at least 10 tools, got {len(data)}"
        print(f"✓ GET /api/custom-agents/tools returns {len(data)} tools")
    
    def test_tools_have_required_fields(self):
        """Each tool has id, name, description, icon"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/tools")
        tools = resp.json()
        for tool in tools:
            assert "id" in tool, f"Tool missing 'id': {tool}"
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool missing 'description': {tool}"
            assert "icon" in tool, f"Tool missing 'icon': {tool}"
        print(f"✓ All {len(tools)} tools have required fields (id, name, description, icon)")
    
    def test_specific_tools_exist(self):
        """Verify specific tools exist: web_search, email_draft, calculator"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/tools")
        tools = resp.json()
        tool_ids = [t["id"] for t in tools]
        assert "web_search" in tool_ids, "web_search tool not found"
        assert "email_draft" in tool_ids, "email_draft tool not found"
        assert "calculator" in tool_ids, "calculator tool not found"
        print("✓ Specific tools exist: web_search, email_draft, calculator")
    
    # ─── Templates Endpoint ───────────────────────────────────────
    def test_get_templates_returns_200(self):
        """GET /api/custom-agents/templates returns 200"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/templates")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("✓ GET /api/custom-agents/templates returns 200")
    
    def test_get_templates_returns_list(self):
        """GET /api/custom-agents/templates returns list of templates"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/templates")
        data = resp.json()
        assert isinstance(data, list), "Expected list of templates"
        assert len(data) >= 4, f"Expected at least 4 templates, got {len(data)}"
        print(f"✓ GET /api/custom-agents/templates returns {len(data)} templates")
    
    def test_templates_have_required_fields(self):
        """Each template has id, name, description, avatar, color, system_prompt, tools"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/templates")
        templates = resp.json()
        for t in templates:
            assert "id" in t, f"Template missing 'id': {t}"
            assert "name" in t, f"Template missing 'name': {t}"
            assert "description" in t, f"Template missing 'description': {t}"
            assert "avatar" in t, f"Template missing 'avatar': {t}"
            assert "color" in t, f"Template missing 'color': {t}"
            assert "system_prompt" in t, f"Template missing 'system_prompt': {t}"
            assert "tools" in t, f"Template missing 'tools': {t}"
        print(f"✓ All {len(templates)} templates have required fields")
    
    # ─── List Agents Endpoint ─────────────────────────────────────
    def test_list_agents_returns_200(self):
        """GET /api/custom-agents returns 200"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("✓ GET /api/custom-agents returns 200")
    
    def test_list_agents_returns_list(self):
        """GET /api/custom-agents returns list"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents")
        data = resp.json()
        assert isinstance(data, list), "Expected list of agents"
        print(f"✓ GET /api/custom-agents returns list with {len(data)} agents")
    
    # ─── Create Agent Endpoint ────────────────────────────────────
    def test_create_agent_returns_200(self):
        """POST /api/custom-agents creates agent"""
        resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "name": "TEST_Agent_Iter154",
            "description": "Test agent for iteration 154",
            "avatar": "bot",
            "color": "#1D4E8A",
            "system_prompt": "Tu es un assistant de test.",
            "tools": ["web_search", "email_draft"],
            "model_preference": "auto",
            "temperature": 0.7,
            "is_active": True,
            "is_public": False
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "id" in data, "Response missing 'id'"
        self.created_agent_ids.append(data["id"])
        print(f"✓ POST /api/custom-agents creates agent with id={data['id']}")
    
    def test_create_agent_has_required_fields(self):
        """Created agent has all required fields"""
        resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "name": "TEST_Agent_Fields",
            "description": "Test agent fields",
            "avatar": "briefcase",
            "color": "#C7372F",
            "system_prompt": "Tu es un assistant commercial.",
            "tools": ["calculator"],
            "model_preference": "fast",
            "temperature": 0.5,
            "is_active": True,
            "is_public": True
        })
        data = resp.json()
        self.created_agent_ids.append(data["id"])
        
        assert data["name"] == "TEST_Agent_Fields"
        assert data["description"] == "Test agent fields"
        assert data["avatar"] == "briefcase"
        assert data["color"] == "#C7372F"
        assert "calculator" in data["tools"]
        assert data["model_preference"] == "fast"
        assert data["temperature"] == 0.5
        assert data["is_active"] == True
        assert data["is_public"] == True
        print("✓ Created agent has all required fields with correct values")
    
    def test_create_agent_without_name_fails(self):
        """POST /api/custom-agents without name returns 422"""
        resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "description": "No name agent",
            "system_prompt": "Test"
        })
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
        print("✓ POST /api/custom-agents without name returns 422")
    
    # ─── Get Single Agent Endpoint ────────────────────────────────
    def test_get_agent_returns_200(self):
        """GET /api/custom-agents/{id} returns 200"""
        # First create an agent
        create_resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "name": "TEST_Get_Agent",
            "system_prompt": "Test"
        })
        agent_id = create_resp.json()["id"]
        self.created_agent_ids.append(agent_id)
        
        # Then get it
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/{agent_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["id"] == agent_id
        assert data["name"] == "TEST_Get_Agent"
        print(f"✓ GET /api/custom-agents/{agent_id} returns 200 with correct data")
    
    def test_get_nonexistent_agent_returns_404(self):
        """GET /api/custom-agents/{invalid_id} returns 404"""
        resp = self.session.get(f"{BASE_URL}/api/custom-agents/nonexistent-id-12345")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("✓ GET /api/custom-agents/nonexistent returns 404")
    
    # ─── Update Agent Endpoint ────────────────────────────────────
    def test_update_agent_returns_200(self):
        """PUT /api/custom-agents/{id} updates agent"""
        # Create agent
        create_resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "name": "TEST_Update_Agent",
            "system_prompt": "Original prompt"
        })
        agent_id = create_resp.json()["id"]
        self.created_agent_ids.append(agent_id)
        
        # Update it
        resp = self.session.put(f"{BASE_URL}/api/custom-agents/{agent_id}", json={
            "name": "TEST_Updated_Agent",
            "description": "Updated description",
            "temperature": 0.9
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["name"] == "TEST_Updated_Agent"
        assert data["description"] == "Updated description"
        assert data["temperature"] == 0.9
        print(f"✓ PUT /api/custom-agents/{agent_id} updates agent correctly")
    
    def test_update_agent_tools(self):
        """PUT /api/custom-agents/{id} can update tools list"""
        # Create agent with no tools
        create_resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "name": "TEST_Tools_Agent",
            "system_prompt": "Test",
            "tools": []
        })
        agent_id = create_resp.json()["id"]
        self.created_agent_ids.append(agent_id)
        
        # Update tools
        resp = self.session.put(f"{BASE_URL}/api/custom-agents/{agent_id}", json={
            "tools": ["web_search", "email_draft", "calculator"]
        })
        data = resp.json()
        assert "web_search" in data["tools"]
        assert "email_draft" in data["tools"]
        assert "calculator" in data["tools"]
        print("✓ PUT /api/custom-agents/{id} can update tools list")
    
    def test_update_agent_active_status(self):
        """PUT /api/custom-agents/{id} can toggle is_active"""
        # Create active agent
        create_resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "name": "TEST_Active_Agent",
            "system_prompt": "Test",
            "is_active": True
        })
        agent_id = create_resp.json()["id"]
        self.created_agent_ids.append(agent_id)
        
        # Deactivate
        resp = self.session.put(f"{BASE_URL}/api/custom-agents/{agent_id}", json={
            "is_active": False
        })
        assert resp.json()["is_active"] == False
        
        # Reactivate
        resp = self.session.put(f"{BASE_URL}/api/custom-agents/{agent_id}", json={
            "is_active": True
        })
        assert resp.json()["is_active"] == True
        print("✓ PUT /api/custom-agents/{id} can toggle is_active")
    
    # ─── Delete Agent Endpoint ────────────────────────────────────
    def test_delete_agent_returns_200(self):
        """DELETE /api/custom-agents/{id} deletes agent"""
        # Create agent
        create_resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "name": "TEST_Delete_Agent",
            "system_prompt": "Test"
        })
        agent_id = create_resp.json()["id"]
        
        # Delete it
        resp = self.session.delete(f"{BASE_URL}/api/custom-agents/{agent_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify it's gone
        get_resp = self.session.get(f"{BASE_URL}/api/custom-agents/{agent_id}")
        assert get_resp.status_code == 404
        print(f"✓ DELETE /api/custom-agents/{agent_id} deletes agent")
    
    # ─── Duplicate Agent Endpoint ─────────────────────────────────
    def test_duplicate_agent_returns_200(self):
        """POST /api/custom-agents/{id}/duplicate creates copy"""
        # Create agent
        create_resp = self.session.post(f"{BASE_URL}/api/custom-agents", json={
            "name": "TEST_Original_Agent",
            "description": "Original",
            "system_prompt": "Original prompt",
            "tools": ["web_search"]
        })
        agent_id = create_resp.json()["id"]
        self.created_agent_ids.append(agent_id)
        
        # Duplicate it
        resp = self.session.post(f"{BASE_URL}/api/custom-agents/{agent_id}/duplicate")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.created_agent_ids.append(data["id"])
        
        assert data["id"] != agent_id, "Duplicate should have different ID"
        assert "copie" in data["name"].lower() or "copy" in data["name"].lower(), "Duplicate name should contain 'copie'"
        assert data["system_prompt"] == "Original prompt"
        assert "web_search" in data["tools"]
        print(f"✓ POST /api/custom-agents/{agent_id}/duplicate creates copy")
    
    # ─── Create From Template Endpoint ────────────────────────────
    def test_create_from_template_returns_200(self):
        """POST /api/custom-agents/from-template creates agent from template"""
        resp = self.session.post(f"{BASE_URL}/api/custom-agents/from-template", json={
            "template_id": "assistant_commercial"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.created_agent_ids.append(data["id"])
        
        assert data["name"] == "Assistant Commercial"
        assert len(data["tools"]) > 0
        print(f"✓ POST /api/custom-agents/from-template creates agent from template")
    
    def test_create_from_invalid_template_returns_404(self):
        """POST /api/custom-agents/from-template with invalid template returns 404"""
        resp = self.session.post(f"{BASE_URL}/api/custom-agents/from-template", json={
            "template_id": "nonexistent_template"
        })
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("✓ POST /api/custom-agents/from-template with invalid template returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
