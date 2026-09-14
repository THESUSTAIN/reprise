"""
Iteration 117 - P1 Features Testing
Tests for:
1. GET /api/wellness/history?days=14 - burnout_risk with prediction and trends
2. GET /api/wellness/activity?days=30 - daily, summary, alerts, projects
3. chatConfig.js - BYOK first in mainModes
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
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Health endpoint OK")
    
    def test_admin_login(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"✓ Admin login OK, token received")
        return data["access_token"]


class TestWellnessHistoryBurnoutPrediction:
    """Test GET /api/wellness/history?days=14 returns burnout_risk with prediction and trends"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_wellness_history_returns_burnout_risk(self, auth_token):
        """Test that wellness history returns burnout_risk object"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/history?days=14", headers=headers)
        
        assert response.status_code == 200, f"Wellness history failed: {response.text}"
        data = response.json()
        
        # Check burnout_risk exists
        assert "burnout_risk" in data, "burnout_risk not in response"
        burnout = data["burnout_risk"]
        
        # Check burnout_risk structure
        assert "risk" in burnout, "risk field missing in burnout_risk"
        assert "level" in burnout, "level field missing in burnout_risk"
        assert "message" in burnout, "message field missing in burnout_risk"
        
        print(f"✓ burnout_risk present: risk={burnout['risk']}, level={burnout['level']}")
        
        # If there's enough data, check for prediction and trends
        if burnout["risk"] != "insufficient_data":
            # Check prediction object
            if "prediction" in burnout and burnout["prediction"]:
                pred = burnout["prediction"]
                assert "days_until_risk" in pred, "days_until_risk missing in prediction"
                assert "projected_date" in pred, "projected_date missing in prediction"
                assert "confidence" in pred, "confidence missing in prediction"
                assert "message" in pred, "message missing in prediction"
                print(f"✓ prediction present: days_until_risk={pred['days_until_risk']}, date={pred['projected_date']}, confidence={pred['confidence']}")
            
            # Check trends object
            if "trends" in burnout and burnout["trends"]:
                trends = burnout["trends"]
                assert "energy" in trends, "energy missing in trends"
                assert "stress" in trends, "stress missing in trends"
                assert "mood" in trends, "mood missing in trends"
                assert "sleep" in trends, "sleep missing in trends"
                print(f"✓ trends present: energy={trends['energy']}, stress={trends['stress']}, mood={trends['mood']}, sleep={trends['sleep']}")
        else:
            print("⚠ Not enough check-ins for prediction/trends (insufficient_data)")
        
        return data
    
    def test_wellness_history_has_checkins_and_stats(self, auth_token):
        """Test that wellness history returns checkins and stats"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/history?days=14", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkins" in data, "checkins not in response"
        assert "stats" in data, "stats not in response"
        
        stats = data["stats"]
        assert "total_checkins" in stats, "total_checkins missing in stats"
        assert "avg_score" in stats, "avg_score missing in stats"
        assert "avg_energy" in stats, "avg_energy missing in stats"
        assert "avg_stress" in stats, "avg_stress missing in stats"
        
        print(f"✓ stats present: total_checkins={stats['total_checkins']}, avg_score={stats['avg_score']}")


class TestWellnessActivity:
    """Test GET /api/wellness/activity?days=30 returns daily, summary, alerts, projects"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_wellness_activity_returns_all_fields(self, auth_token):
        """Test that wellness activity returns daily, summary, alerts, projects"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/wellness/activity?days=30", headers=headers)
        
        assert response.status_code == 200, f"Wellness activity failed: {response.text}"
        data = response.json()
        
        # Check all required fields exist
        assert "daily" in data, "daily not in response"
        assert "summary" in data, "summary not in response"
        assert "alerts" in data, "alerts not in response"
        assert "projects" in data, "projects not in response"
        
        print(f"✓ All fields present: daily={len(data['daily'])} items, alerts={len(data['alerts'])}, projects={len(data['projects'])}")
        
        # Check summary structure
        summary = data["summary"]
        assert "total_work_hours" in summary, "total_work_hours missing in summary"
        assert "total_project_hours" in summary, "total_project_hours missing in summary"
        assert "avg_work_minutes_per_day" in summary, "avg_work_minutes_per_day missing in summary"
        assert "avg_wellness_score" in summary, "avg_wellness_score missing in summary"
        assert "total_sessions" in summary, "total_sessions missing in summary"
        assert "total_checkins" in summary, "total_checkins missing in summary"
        
        print(f"✓ summary structure OK: total_work_hours={summary['total_work_hours']}, total_checkins={summary['total_checkins']}")
        
        # Check daily structure if there are items
        if len(data["daily"]) > 0:
            day = data["daily"][0]
            assert "date" in day, "date missing in daily item"
            print(f"✓ daily item structure OK")
        
        return data


class TestChatConfigBYOKFirst:
    """Test that BYOK (ChatGPT) is first in mainModes array"""
    
    def test_byok_is_first_in_chatconfig(self):
        """Verify BYOK is first in chatConfig.js mainModes"""
        # Read the chatConfig.js file
        config_path = "/app/frontend/src/components/chat/chatConfig.js"
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Find mainModes array
        assert "export const mainModes" in content, "mainModes not found in chatConfig.js"
        
        # Check that byok is the first item in the array
        # The pattern should be: mainModes = (lang) => [ { id: 'byok', ...
        import re
        pattern = r"mainModes\s*=\s*\(lang\)\s*=>\s*\[\s*\{\s*id:\s*['\"](\w+)['\"]"
        match = re.search(pattern, content)
        
        assert match, "Could not parse mainModes array structure"
        first_mode_id = match.group(1)
        
        assert first_mode_id == "byok", f"First mode should be 'byok', but found '{first_mode_id}'"
        print(f"✓ BYOK is first in mainModes array (id='{first_mode_id}')")


class TestEnergiePage:
    """Test EnergiePage burnout risk display structure"""
    
    def test_energie_page_has_burnout_risk_testid(self):
        """Verify EnergiePage has data-testid for burnout-risk section"""
        page_path = "/app/frontend/src/components/EnergiePage.js"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check for burnout-risk data-testid
        assert 'data-testid="burnout-risk"' in content, "burnout-risk data-testid not found"
        print("✓ burnout-risk data-testid found in EnergiePage")
        
        # Check for prediction display
        assert "history.burnout_risk.prediction" in content, "prediction display not found"
        print("✓ prediction display found in EnergiePage")
        
        # Check for trends display
        assert "history.burnout_risk.trends" in content, "trends display not found"
        print("✓ trends display found in EnergiePage")
        
        # Check for trend badges (Energie, Stress, Humeur, Sommeil)
        assert "'Energie'" in content or '"Energie"' in content, "Energie trend badge not found"
        assert "'Stress'" in content or '"Stress"' in content, "Stress trend badge not found"
        assert "'Humeur'" in content or '"Humeur"' in content, "Humeur trend badge not found"
        assert "'Sommeil'" in content or '"Sommeil"' in content, "Sommeil trend badge not found"
        print("✓ All trend badges found (Energie, Stress, Humeur, Sommeil)")


class TestChatInterfaceCloudButton:
    """Test ChatInterface has Cloud/CloudOff sync button"""
    
    def test_chat_interface_has_cloud_button(self):
        """Verify ChatInterface has Cloud/CloudOff button"""
        page_path = "/app/frontend/src/components/ChatInterface.js"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check for Cloud and CloudOff imports
        assert "Cloud" in content, "Cloud icon not imported"
        assert "CloudOff" in content, "CloudOff icon not imported"
        print("✓ Cloud and CloudOff icons imported")
        
        # Check for sync button with data-testid
        assert 'data-testid="sync-drive' in content, "sync-drive data-testid not found"
        print("✓ sync-drive button data-testid found")
        
        # Check for driveConnected state
        assert "driveConnected" in content, "driveConnected state not found"
        print("✓ driveConnected state found")
        
        # Check for CloudOff display when not connected
        assert "<CloudOff" in content, "CloudOff component not used"
        print("✓ CloudOff component used for disconnected state")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
