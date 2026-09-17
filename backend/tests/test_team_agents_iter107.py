"""
Test Team Agents CRUD API - Iteration 107
Tests for: POST/GET/PUT/DELETE /api/team/agents
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"
TEAM_ID = "afe0e66c-ea92-4828-882a-7535f822449d"  # Team 'test'


class TestTeamAgentsCRUD:
    """Team Agents CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token")
        assert self.token, "No access_token in login response"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.created_agent_id = None
    
    def test_01_list_team_agents(self):
        """GET /api/team/agents - List agents for a team"""
        response = requests.get(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers
        )
        assert response.status_code == 200, f"List agents failed: {response.text}"
        agents = response.json()
        assert isinstance(agents, list), "Response should be a list"
        print(f"✓ List agents: Found {len(agents)} agent(s)")
        
        # Check structure if agents exist
        if agents:
            agent = agents[0]
            assert "id" in agent, "Agent should have id"
            assert "name" in agent, "Agent should have name"
            assert "system_prompt" in agent, "Agent should have system_prompt"
            print(f"  First agent: {agent['name']}")
    
    def test_02_create_team_agent(self):
        """POST /api/team/agents - Create a new team agent"""
        agent_data = {
            "name": "TEST_Agent_Iter107",
            "description": "Agent de test pour iteration 107",
            "system_prompt": "Tu es un assistant de test. Reponds toujours en francais.",
            "tools": ["email_draft", "web_search"],
            "temperature": 0.5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers,
            json=agent_data
        )
        assert response.status_code == 200, f"Create agent failed: {response.text}"
        
        created = response.json()
        assert "id" in created, "Created agent should have id"
        assert created["name"] == agent_data["name"], "Name should match"
        assert created["description"] == agent_data["description"], "Description should match"
        assert created["temperature"] == agent_data["temperature"], "Temperature should match"
        assert "email_draft" in created.get("tools", []), "Tools should include email_draft"
        
        self.__class__.created_agent_id = created["id"]
        print(f"✓ Created agent: {created['name']} (ID: {created['id']})")
        
        # Verify by GET
        verify_response = requests.get(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        agents = verify_response.json()
        found = any(a["id"] == created["id"] for a in agents)
        assert found, "Created agent should appear in list"
        print("✓ Verified agent appears in list")
    
    def test_03_update_team_agent(self):
        """PUT /api/team/agents/{agent_id} - Update an existing agent"""
        # First create an agent to update
        create_data = {
            "name": "TEST_Agent_ToUpdate",
            "description": "Agent a modifier",
            "system_prompt": "Prompt initial",
            "tools": [],
            "temperature": 0.7
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers,
            json=create_data
        )
        assert create_response.status_code == 200, f"Create for update failed: {create_response.text}"
        agent_id = create_response.json()["id"]
        
        # Update the agent
        update_data = {
            "name": "TEST_Agent_Updated",
            "description": "Description mise a jour",
            "temperature": 0.3,
            "tools": ["code_helper"]
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/team/agents/{agent_id}?team_id={TEAM_ID}",
            headers=self.headers,
            json=update_data
        )
        assert update_response.status_code == 200, f"Update agent failed: {update_response.text}"
        
        result = update_response.json()
        assert result.get("success") == True, "Update should return success"
        print(f"✓ Updated agent: {result.get('name', agent_id)}")
        
        # Verify update by listing
        verify_response = requests.get(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers
        )
        agents = verify_response.json()
        updated_agent = next((a for a in agents if a["id"] == agent_id), None)
        assert updated_agent is not None, "Updated agent should exist"
        assert updated_agent["name"] == "TEST_Agent_Updated", "Name should be updated"
        assert updated_agent["temperature"] == 0.3, "Temperature should be updated"
        print("✓ Verified agent was updated correctly")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/team/agents/{agent_id}?team_id={TEAM_ID}",
            headers=self.headers
        )
    
    def test_04_delete_team_agent(self):
        """DELETE /api/team/agents/{agent_id} - Delete an agent"""
        # First create an agent to delete
        create_data = {
            "name": "TEST_Agent_ToDelete",
            "description": "Agent a supprimer",
            "system_prompt": "Prompt test",
            "tools": [],
            "temperature": 0.7
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers,
            json=create_data
        )
        assert create_response.status_code == 200, f"Create for delete failed: {create_response.text}"
        agent_id = create_response.json()["id"]
        
        # Delete the agent
        delete_response = requests.delete(
            f"{BASE_URL}/api/team/agents/{agent_id}?team_id={TEAM_ID}",
            headers=self.headers
        )
        assert delete_response.status_code == 200, f"Delete agent failed: {delete_response.text}"
        
        result = delete_response.json()
        assert result.get("success") == True, "Delete should return success"
        print(f"✓ Deleted agent: {agent_id}")
        
        # Verify deletion
        verify_response = requests.get(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers
        )
        agents = verify_response.json()
        found = any(a["id"] == agent_id for a in agents)
        assert not found, "Deleted agent should not appear in list"
        print("✓ Verified agent was deleted")
    
    def test_05_create_agent_without_name_fails(self):
        """POST /api/team/agents - Should fail without name"""
        agent_data = {
            "description": "Agent sans nom",
            "system_prompt": "Test prompt"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers,
            json=agent_data
        )
        # Should fail with 422 (validation error) or similar
        assert response.status_code in [400, 422], f"Should fail without name, got {response.status_code}"
        print("✓ Create without name correctly rejected")
    
    def test_06_non_member_cannot_access_agents(self):
        """Non-team member should not access team agents"""
        # Use invalid team_id
        response = requests.get(
            f"{BASE_URL}/api/team/agents?team_id=invalid-team-id-12345",
            headers=self.headers
        )
        # Should return empty list or 403/404
        if response.status_code == 200:
            agents = response.json()
            assert agents == [], "Should return empty list for invalid team"
        else:
            assert response.status_code in [403, 404], f"Should return 403/404 for invalid team"
        print("✓ Invalid team access handled correctly")
    
    def test_07_cleanup_test_agents(self):
        """Cleanup: Delete all TEST_ prefixed agents"""
        response = requests.get(
            f"{BASE_URL}/api/team/agents?team_id={TEAM_ID}",
            headers=self.headers
        )
        if response.status_code == 200:
            agents = response.json()
            test_agents = [a for a in agents if a.get("name", "").startswith("TEST_")]
            for agent in test_agents:
                requests.delete(
                    f"{BASE_URL}/api/team/agents/{agent['id']}?team_id={TEAM_ID}",
                    headers=self.headers
                )
                print(f"  Cleaned up: {agent['name']}")
        print(f"✓ Cleanup complete: removed {len(test_agents) if 'test_agents' in dir() else 0} test agent(s)")


class TestChatbotAdminPage:
    """Test ChatbotAdminPage endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_team_list(self):
        """GET /api/team/list - List user's teams"""
        response = requests.get(f"{BASE_URL}/api/team/list", headers=self.headers)
        assert response.status_code == 200, f"Team list failed: {response.text}"
        data = response.json()
        assert "teams" in data, "Response should have teams"
        print(f"✓ Team list: {len(data['teams'])} team(s)")
    
    def test_license_my(self):
        """GET /api/license/my - Get user's licenses"""
        response = requests.get(f"{BASE_URL}/api/license/my", headers=self.headers)
        assert response.status_code == 200, f"License my failed: {response.text}"
        data = response.json()
        assert "licenses" in data, "Response should have licenses"
        print(f"✓ My licenses: {len(data['licenses'])} license(s)")
    
    def test_team_me(self):
        """GET /api/team/me - Get team details"""
        response = requests.get(
            f"{BASE_URL}/api/team/me?team_id={TEAM_ID}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Team me failed: {response.text}"
        data = response.json()
        assert "team" in data, "Response should have team"
        if data["team"]:
            team = data["team"]
            assert "bot_name" in team, "Team should have bot_name"
            assert "bot_tone" in team, "Team should have bot_tone"
            print(f"✓ Team details: {team.get('name', 'N/A')}")


class TestSidebarLinks:
    """Test sidebar navigation links"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_user_has_team_plan_or_admin(self):
        """Verify user has team plan or admin role for sidebar visibility"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        user = response.json()
        
        # Admin should see CHATBOT B2B section
        is_admin = user.get("role") == "admin"
        is_team_plan = user.get("plan") == "team"
        
        assert is_admin or is_team_plan, "User should be admin or have team plan"
        print(f"✓ User role: {user.get('role')}, plan: {user.get('plan')}")
        print(f"  CHATBOT B2B section should be visible: {is_admin or is_team_plan}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
