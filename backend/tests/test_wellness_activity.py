"""
Test Wellness Activity Endpoints - Iteration 115
Tests for:
- GET /api/wellness/activity - new activity correlation endpoint
- GET /api/wellness/today - existing today check-in
- GET /api/wellness/history - existing history endpoint
- GET /api/wellness/weekly-report - existing weekly report
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_endpoint(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Health endpoint working")
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"✓ Admin login successful, token received")
        return data["access_token"]


class TestWellnessToday:
    """Test GET /api/wellness/today endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_today_endpoint_returns_200(self, auth_token):
        """Test today endpoint is accessible"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/today", headers=headers)
        assert response.status_code == 200, f"Today endpoint failed: {response.text}"
        data = response.json()
        assert "has_checkin" in data, "Missing has_checkin field"
        print(f"✓ Today endpoint working, has_checkin={data['has_checkin']}")
    
    def test_today_requires_auth(self):
        """Test today endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wellness/today")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Today endpoint requires auth")


class TestWellnessHistory:
    """Test GET /api/wellness/history endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_history_endpoint_returns_200(self, auth_token):
        """Test history endpoint is accessible"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/history?days=14", headers=headers)
        assert response.status_code == 200, f"History endpoint failed: {response.text}"
        data = response.json()
        assert "checkins" in data, "Missing checkins field"
        assert "stats" in data, "Missing stats field"
        assert "burnout_risk" in data, "Missing burnout_risk field"
        print(f"✓ History endpoint working, {len(data['checkins'])} checkins found")
    
    def test_history_requires_auth(self):
        """Test history endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wellness/history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ History endpoint requires auth")


class TestWellnessWeeklyReport:
    """Test GET /api/wellness/weekly-report endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_weekly_report_endpoint_returns_200(self, auth_token):
        """Test weekly-report endpoint is accessible"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/weekly-report", headers=headers)
        assert response.status_code == 200, f"Weekly report endpoint failed: {response.text}"
        data = response.json()
        # Either has_data=True with full report or has_data=False with message
        if data.get("has_data"):
            assert "nb_checkins" in data, "Missing nb_checkins field"
            assert "avg_score" in data, "Missing avg_score field"
            print(f"✓ Weekly report working, {data['nb_checkins']} checkins, avg_score={data['avg_score']}")
        else:
            assert "message" in data, "Missing message field when no data"
            print(f"✓ Weekly report working, no data: {data['message']}")
    
    def test_weekly_report_requires_auth(self):
        """Test weekly-report endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wellness/weekly-report")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Weekly report endpoint requires auth")


class TestWellnessActivity:
    """Test GET /api/wellness/activity endpoint - NEW endpoint for Mon activite tab"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_activity_endpoint_returns_200(self, auth_token):
        """Test activity endpoint is accessible and returns expected structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/activity?days=30", headers=headers)
        assert response.status_code == 200, f"Activity endpoint failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "daily" in data, "Missing daily field"
        assert "summary" in data, "Missing summary field"
        assert "alerts" in data, "Missing alerts field"
        assert "projects" in data, "Missing projects field"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_work_hours" in summary, "Missing total_work_hours in summary"
        assert "total_sessions" in summary, "Missing total_sessions in summary"
        assert "avg_wellness_score" in summary, "Missing avg_wellness_score in summary"
        assert "total_checkins" in summary, "Missing total_checkins in summary"
        
        print(f"✓ Activity endpoint working")
        print(f"  - daily entries: {len(data['daily'])}")
        print(f"  - total_work_hours: {summary['total_work_hours']}")
        print(f"  - total_sessions: {summary['total_sessions']}")
        print(f"  - avg_wellness_score: {summary['avg_wellness_score']}")
        print(f"  - total_checkins: {summary['total_checkins']}")
        print(f"  - alerts: {len(data['alerts'])}")
        print(f"  - projects: {len(data['projects'])}")
    
    def test_activity_daily_structure(self, auth_token):
        """Test daily data structure in activity response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/activity?days=30", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["daily"]) > 0:
            day = data["daily"][0]
            assert "date" in day, "Missing date in daily entry"
            assert "score" in day, "Missing score in daily entry"
            assert "work_minutes" in day, "Missing work_minutes in daily entry"
            assert "work_sessions" in day, "Missing work_sessions in daily entry"
            print(f"✓ Daily structure verified: date={day['date']}, score={day['score']}, work_minutes={day['work_minutes']}")
        else:
            print("✓ Daily structure test skipped (no data)")
    
    def test_activity_projects_structure(self, auth_token):
        """Test projects data structure in activity response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/activity?days=30", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["projects"]) > 0:
            project = data["projects"][0]
            assert "name" in project, "Missing name in project"
            assert "hours" in project, "Missing hours in project"
            assert "color" in project, "Missing color in project"
            print(f"✓ Projects structure verified: name={project['name']}, hours={project['hours']}")
        else:
            print("✓ Projects structure test skipped (no projects)")
    
    def test_activity_requires_auth(self):
        """Test activity endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wellness/activity")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Activity endpoint requires auth")
    
    def test_activity_days_parameter(self, auth_token):
        """Test activity endpoint respects days parameter"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test with 7 days
        response7 = requests.get(f"{BASE_URL}/api/wellness/activity?days=7", headers=headers)
        assert response7.status_code == 200
        
        # Test with 30 days
        response30 = requests.get(f"{BASE_URL}/api/wellness/activity?days=30", headers=headers)
        assert response30.status_code == 200
        
        print("✓ Activity endpoint accepts days parameter (7 and 30)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
