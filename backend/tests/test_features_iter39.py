"""
Iteration 39 - Features Router Tests
Tests for: captures, priority, energy, focus sessions, structuration, diagnostic score
All endpoints under /api/features/*
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("PASS: API health check")


class TestCaptures:
    """Tests for /api/features/captures endpoints"""
    
    def test_get_captures_empty(self, auth_headers):
        """GET /api/features/captures - should return list (may be empty)"""
        response = requests.get(f"{BASE_URL}/api/features/captures", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Captures should be a list"
        print(f"PASS: GET captures returned {len(data)} items")
    
    def test_create_capture(self, auth_headers):
        """POST /api/features/captures - should create a capture"""
        payload = {
            "content": "TEST_capture_iteration_39",
            "category": "idee",
            "source": "text"
        }
        response = requests.post(f"{BASE_URL}/api/features/captures", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "id" in data, "Capture should have an id"
        assert data["content"] == payload["content"], "Content should match"
        assert data["category"] == payload["category"], "Category should match"
        print(f"PASS: Created capture with id {data['id']}")
        return data["id"]
    
    def test_create_and_verify_capture(self, auth_headers):
        """POST then GET to verify capture persistence"""
        # Create
        payload = {"content": "TEST_verify_capture", "category": "tache"}
        create_resp = requests.post(f"{BASE_URL}/api/features/captures", json=payload, headers=auth_headers)
        assert create_resp.status_code == 200
        capture_id = create_resp.json()["id"]
        
        # Verify via GET
        get_resp = requests.get(f"{BASE_URL}/api/features/captures", headers=auth_headers)
        assert get_resp.status_code == 200
        captures = get_resp.json()
        found = any(c["id"] == capture_id for c in captures)
        assert found, f"Created capture {capture_id} not found in list"
        print(f"PASS: Capture {capture_id} verified in list")
    
    def test_delete_capture(self, auth_headers):
        """DELETE /api/features/captures/{id} - should delete capture"""
        # First create one
        payload = {"content": "TEST_to_delete", "category": "probleme"}
        create_resp = requests.post(f"{BASE_URL}/api/features/captures", json=payload, headers=auth_headers)
        assert create_resp.status_code == 200
        capture_id = create_resp.json()["id"]
        
        # Delete it
        del_resp = requests.delete(f"{BASE_URL}/api/features/captures/{capture_id}", headers=auth_headers)
        assert del_resp.status_code == 200, f"Delete failed: {del_resp.status_code}"
        
        # Verify deleted
        get_resp = requests.get(f"{BASE_URL}/api/features/captures", headers=auth_headers)
        captures = get_resp.json()
        found = any(c["id"] == capture_id for c in captures)
        assert not found, f"Capture {capture_id} should be deleted"
        print(f"PASS: Capture {capture_id} deleted successfully")


class TestPriority:
    """Tests for /api/features/priority endpoints"""
    
    def test_get_priority_default(self, auth_headers):
        """GET /api/features/priority - should return default or user priority"""
        response = requests.get(f"{BASE_URL}/api/features/priority", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "title" in data, "Priority should have title"
        assert "date" in data, "Priority should have date"
        print(f"PASS: GET priority returned: {data.get('title', 'N/A')[:50]}")
    
    def test_set_priority(self, auth_headers):
        """POST /api/features/priority - should set a new priority"""
        payload = {
            "title": "TEST_priority_iteration_39",
            "why": "Testing the priority endpoint",
            "estimated_time": "3h"
        }
        response = requests.post(f"{BASE_URL}/api/features/priority", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data["title"] == payload["title"], "Title should match"
        assert data["set_by"] == "user", "set_by should be 'user'"
        print(f"PASS: Set priority: {data['title']}")
    
    def test_set_and_verify_priority(self, auth_headers):
        """POST then GET to verify priority persistence"""
        payload = {"title": "TEST_verify_priority", "why": "Verification test"}
        post_resp = requests.post(f"{BASE_URL}/api/features/priority", json=payload, headers=auth_headers)
        assert post_resp.status_code == 200
        
        get_resp = requests.get(f"{BASE_URL}/api/features/priority", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["title"] == payload["title"], "Priority should persist"
        print("PASS: Priority verified after set")


class TestEnergy:
    """Tests for /api/features/energy endpoints"""
    
    def test_get_energy_default(self, auth_headers):
        """GET /api/features/energy - should return today's energy or default"""
        response = requests.get(f"{BASE_URL}/api/features/energy", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "level" in data, "Energy should have level"
        assert "date" in data, "Energy should have date"
        print(f"PASS: GET energy returned level {data.get('level')}")
    
    def test_set_energy(self, auth_headers):
        """POST /api/features/energy - should set energy level (1-5)"""
        payload = {"level": 4, "note": "TEST_energy_iteration_39"}
        response = requests.post(f"{BASE_URL}/api/features/energy", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data["level"] == 4, "Level should be 4"
        assert data["set"] == True, "Energy should be marked as set"
        print(f"PASS: Set energy level to {data['level']}")
    
    def test_set_and_verify_energy(self, auth_headers):
        """POST then GET to verify energy persistence"""
        payload = {"level": 3, "note": "Verification test"}
        post_resp = requests.post(f"{BASE_URL}/api/features/energy", json=payload, headers=auth_headers)
        assert post_resp.status_code == 200
        
        get_resp = requests.get(f"{BASE_URL}/api/features/energy", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["level"] == 3, "Energy level should persist"
        assert data["set"] == True
        print("PASS: Energy verified after set")


class TestFocusSessions:
    """Tests for /api/features/focus/* endpoints"""
    
    def test_get_focus_sessions(self, auth_headers):
        """GET /api/features/focus/sessions - should return sessions list"""
        response = requests.get(f"{BASE_URL}/api/features/focus/sessions", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Sessions should be a list"
        print(f"PASS: GET focus sessions returned {len(data)} items")
    
    def test_create_focus_session(self, auth_headers):
        """POST /api/features/focus/sessions - should create a focus session"""
        payload = {
            "task": "TEST_focus_session_iter39",
            "duration": 1500,  # 25 minutes in seconds
            "completed": True
        }
        response = requests.post(f"{BASE_URL}/api/features/focus/sessions", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "id" in data, "Session should have id"
        assert data["task"] == payload["task"], "Task should match"
        assert data["duration"] == payload["duration"], "Duration should match"
        print(f"PASS: Created focus session with id {data['id']}")
    
    def test_get_focus_stats(self, auth_headers):
        """GET /api/features/focus/stats - should return focus stats"""
        response = requests.get(f"{BASE_URL}/api/features/focus/stats", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "today_sessions" in data, "Stats should have today_sessions"
        assert "today_minutes" in data, "Stats should have today_minutes"
        assert "total_sessions" in data, "Stats should have total_sessions"
        assert "total_minutes" in data, "Stats should have total_minutes"
        print(f"PASS: Focus stats - today: {data['today_sessions']} sessions, {data['today_minutes']} min")


class TestStructuration:
    """Tests for /api/features/structuration endpoints"""
    
    def test_get_structuration(self, auth_headers):
        """GET /api/features/structuration - should return progress map"""
        response = requests.get(f"{BASE_URL}/api/features/structuration", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Structuration should be a dict"
        print(f"PASS: GET structuration returned {len(data)} progress items")
    
    def test_toggle_structuration_action(self, auth_headers):
        """POST /api/features/structuration - should toggle an action"""
        payload = {
            "pillar": "clarity",
            "action_index": 0,
            "done": True
        }
        response = requests.post(f"{BASE_URL}/api/features/structuration", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "clarity_0" in data, "Progress should contain clarity_0"
        assert data["clarity_0"] == True, "clarity_0 should be True"
        print(f"PASS: Toggled structuration action clarity_0 to True")
    
    def test_toggle_and_verify_structuration(self, auth_headers):
        """POST then GET to verify structuration persistence"""
        payload = {"pillar": "energy", "action_index": 1, "done": True}
        post_resp = requests.post(f"{BASE_URL}/api/features/structuration", json=payload, headers=auth_headers)
        assert post_resp.status_code == 200
        
        get_resp = requests.get(f"{BASE_URL}/api/features/structuration", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data.get("energy_1") == True, "energy_1 should persist as True"
        print("PASS: Structuration action verified after toggle")


class TestDiagnosticScore:
    """Tests for /api/features/diagnostic/score endpoint"""
    
    def test_get_diagnostic_score(self, auth_headers):
        """GET /api/features/diagnostic/score - should return computed score"""
        response = requests.get(f"{BASE_URL}/api/features/diagnostic/score", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Validate structure
        assert "score" in data, "Should have global score"
        assert "pillars" in data, "Should have pillars"
        assert isinstance(data["score"], int), "Score should be int"
        
        # Validate pillars
        pillars = data["pillars"]
        assert "clarity" in pillars, "Should have clarity pillar"
        assert "energy" in pillars, "Should have energy pillar"
        assert "alignment" in pillars, "Should have alignment pillar"
        assert "revenue" in pillars, "Should have revenue pillar"
        
        # Validate additional fields
        assert "captures_count" in data, "Should have captures_count"
        assert "has_priority" in data, "Should have has_priority"
        assert "has_energy" in data, "Should have has_energy"
        assert "focus_sessions_today" in data, "Should have focus_sessions_today"
        
        print(f"PASS: Diagnostic score = {data['score']}, pillars = {pillars}")


class TestAuthRequired:
    """Tests that endpoints require authentication"""
    
    def test_captures_requires_auth(self):
        """Captures endpoint should require auth"""
        response = requests.get(f"{BASE_URL}/api/features/captures")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print("PASS: Captures requires auth")
    
    def test_priority_requires_auth(self):
        """Priority endpoint should require auth"""
        response = requests.get(f"{BASE_URL}/api/features/priority")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print("PASS: Priority requires auth")
    
    def test_energy_requires_auth(self):
        """Energy endpoint should require auth"""
        response = requests.get(f"{BASE_URL}/api/features/energy")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print("PASS: Energy requires auth")
    
    def test_focus_requires_auth(self):
        """Focus sessions endpoint should require auth"""
        response = requests.get(f"{BASE_URL}/api/features/focus/sessions")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print("PASS: Focus sessions requires auth")
    
    def test_structuration_requires_auth(self):
        """Structuration endpoint should require auth"""
        response = requests.get(f"{BASE_URL}/api/features/structuration")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print("PASS: Structuration requires auth")
    
    def test_diagnostic_requires_auth(self):
        """Diagnostic score endpoint should require auth"""
        response = requests.get(f"{BASE_URL}/api/features/diagnostic/score")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print("PASS: Diagnostic score requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
