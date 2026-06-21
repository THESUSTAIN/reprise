"""
Test Suite for Iteration 36 - Workflows CRUD and Auth Refresh Endpoint
Tests:
- GET /api/workflows - list workflows
- POST /api/workflows - create workflow
- PUT /api/workflows/{id} - update workflow
- DELETE /api/workflows/{id} - delete workflow
- POST /api/workflows/{id}/run - run workflow
- POST /api/auth/refresh - refresh expired/valid token
"""
import pytest
import requests
import os
import time
from datetime import datetime, timedelta
from jose import jwt

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"

# JWT settings (must match backend)
JWT_SECRET = os.environ.get('JWT_SECRET', '7Qx9-OhRcpWn0XRKvzWpFMFiZSQreyI1OkiS5epznvN7kdem-gxqqew_W_HTAP8t')
JWT_ALGORITHM = "HS256"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestAuthRefresh:
    """Tests for POST /api/auth/refresh endpoint"""
    
    def test_refresh_valid_token(self, auth_token):
        """Test refreshing a valid (non-expired) token"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/auth/refresh", headers=headers)
        assert response.status_code == 200, f"Refresh failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["email"] == TEST_EMAIL
        print(f"PASS: Refresh valid token - got new token and user data")
    
    def test_refresh_missing_token(self):
        """Test refresh without token returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/refresh")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"PASS: Refresh without token returns 401")
    
    def test_refresh_garbage_token(self):
        """Test refresh with garbage token returns 401"""
        headers = {"Authorization": "Bearer garbage_token_12345"}
        response = requests.post(f"{BASE_URL}/api/auth/refresh", headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"PASS: Refresh with garbage token returns 401")
    
    def test_refresh_malformed_header(self):
        """Test refresh with malformed auth header returns 401"""
        headers = {"Authorization": "NotBearer sometoken"}
        response = requests.post(f"{BASE_URL}/api/auth/refresh", headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"PASS: Refresh with malformed header returns 401")


class TestWorkflowsCRUD:
    """Tests for Workflows CRUD endpoints"""
    
    created_workflow_id = None
    
    def test_01_get_workflows_empty_or_list(self, auth_headers):
        """Test GET /api/workflows returns list"""
        response = requests.get(f"{BASE_URL}/api/workflows", headers=auth_headers)
        assert response.status_code == 200, f"GET workflows failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: GET /api/workflows returns list with {len(data)} workflows")
    
    def test_02_create_workflow(self, auth_headers):
        """Test POST /api/workflows creates a new workflow"""
        workflow_data = {
            "name": "TEST_Workflow_Iter36",
            "description": "Test workflow created by iteration 36 tests",
            "steps": [
                {"type": "prompt", "content": "Test step 1", "label": "Step 1"},
                {"type": "prompt", "content": "Test step 2", "label": "Step 2"}
            ],
            "schedule": {"frequency": "daily", "time": "09:00"},
            "status": "active"
        }
        response = requests.post(
            f"{BASE_URL}/api/workflows",
            headers=auth_headers,
            json=workflow_data
        )
        assert response.status_code == 200, f"Create workflow failed: {response.text}"
        data = response.json()
        assert "id" in data, "Response should contain id"
        assert data["name"] == workflow_data["name"], "Name should match"
        assert data["description"] == workflow_data["description"], "Description should match"
        assert data["status"] in ["active", "idle"], f"Status should be active or idle, got {data['status']}"
        TestWorkflowsCRUD.created_workflow_id = data["id"]
        print(f"PASS: POST /api/workflows created workflow with id={data['id']}")
    
    def test_03_get_workflow_by_id(self, auth_headers):
        """Test GET /api/workflows/{id} returns the created workflow"""
        assert TestWorkflowsCRUD.created_workflow_id, "No workflow created yet"
        wf_id = TestWorkflowsCRUD.created_workflow_id
        response = requests.get(f"{BASE_URL}/api/workflows/{wf_id}", headers=auth_headers)
        assert response.status_code == 200, f"GET workflow by id failed: {response.text}"
        data = response.json()
        assert data["id"] == wf_id, "ID should match"
        assert data["name"] == "TEST_Workflow_Iter36", "Name should match"
        print(f"PASS: GET /api/workflows/{wf_id} returns correct workflow")
    
    def test_04_update_workflow(self, auth_headers):
        """Test PUT /api/workflows/{id} updates the workflow"""
        assert TestWorkflowsCRUD.created_workflow_id, "No workflow created yet"
        wf_id = TestWorkflowsCRUD.created_workflow_id
        update_data = {
            "name": "TEST_Workflow_Iter36_Updated",
            "description": "Updated description",
            "steps": [{"type": "prompt", "content": "Updated step", "label": "Updated"}],
            "schedule": {"frequency": "weekly", "time": "10:00"},
            "status": "paused"
        }
        response = requests.put(
            f"{BASE_URL}/api/workflows/{wf_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update workflow failed: {response.text}"
        data = response.json()
        assert data["name"] == update_data["name"], "Name should be updated"
        assert data["description"] == update_data["description"], "Description should be updated"
        print(f"PASS: PUT /api/workflows/{wf_id} updated workflow successfully")
        
        # Verify update persisted with GET
        get_response = requests.get(f"{BASE_URL}/api/workflows/{wf_id}", headers=auth_headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["name"] == update_data["name"], "Update should persist"
        print(f"PASS: Update verified via GET - name is '{get_data['name']}'")
    
    def test_05_run_workflow(self, auth_headers):
        """Test POST /api/workflows/{id}/run executes the workflow"""
        assert TestWorkflowsCRUD.created_workflow_id, "No workflow created yet"
        wf_id = TestWorkflowsCRUD.created_workflow_id
        response = requests.post(
            f"{BASE_URL}/api/workflows/{wf_id}/run",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Run workflow failed: {response.text}"
        data = response.json()
        assert "status" in data, "Response should contain status"
        assert "results" in data or "step_results" in data, "Response should contain results"
        print(f"PASS: POST /api/workflows/{wf_id}/run executed - status={data.get('status')}")
    
    def test_06_get_workflow_not_found(self, auth_headers):
        """Test GET /api/workflows/{id} returns 404 for non-existent workflow"""
        fake_id = "non_existent_workflow_id_12345"
        response = requests.get(f"{BASE_URL}/api/workflows/{fake_id}", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"PASS: GET /api/workflows/{fake_id} returns 404")
    
    def test_07_delete_workflow(self, auth_headers):
        """Test DELETE /api/workflows/{id} deletes the workflow"""
        assert TestWorkflowsCRUD.created_workflow_id, "No workflow created yet"
        wf_id = TestWorkflowsCRUD.created_workflow_id
        response = requests.delete(f"{BASE_URL}/api/workflows/{wf_id}", headers=auth_headers)
        assert response.status_code == 200, f"Delete workflow failed: {response.text}"
        data = response.json()
        assert data.get("status") == "deleted", "Status should be deleted"
        print(f"PASS: DELETE /api/workflows/{wf_id} deleted workflow")
        
        # Verify deletion with GET
        get_response = requests.get(f"{BASE_URL}/api/workflows/{wf_id}", headers=auth_headers)
        assert get_response.status_code == 404, "Deleted workflow should return 404"
        print(f"PASS: Deletion verified - GET returns 404")
    
    def test_08_delete_workflow_not_found(self, auth_headers):
        """Test DELETE /api/workflows/{id} returns 404 for non-existent workflow"""
        fake_id = "non_existent_workflow_id_12345"
        response = requests.delete(f"{BASE_URL}/api/workflows/{fake_id}", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"PASS: DELETE /api/workflows/{fake_id} returns 404")


class TestWorkflowsValidation:
    """Tests for workflow validation and edge cases"""
    
    def test_create_workflow_minimal(self, auth_headers):
        """Test creating workflow with minimal required fields"""
        workflow_data = {
            "name": "TEST_Minimal_Workflow",
            "description": "",
            "steps": []
        }
        response = requests.post(
            f"{BASE_URL}/api/workflows",
            headers=auth_headers,
            json=workflow_data
        )
        assert response.status_code == 200, f"Create minimal workflow failed: {response.text}"
        data = response.json()
        wf_id = data["id"]
        print(f"PASS: Created minimal workflow with id={wf_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/workflows/{wf_id}", headers=auth_headers)
    
    def test_workflows_require_auth(self):
        """Test that workflows endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/workflows")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"PASS: GET /api/workflows requires auth (returns {response.status_code})")
        
        response = requests.post(f"{BASE_URL}/api/workflows", json={"name": "test"})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"PASS: POST /api/workflows requires auth (returns {response.status_code})")


class TestHealthAndLogin:
    """Basic health and login tests"""
    
    def test_health_check(self):
        """Test /api/health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print(f"PASS: /api/health returns 200")
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user"
        print(f"PASS: Login successful for {TEST_EMAIL}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
