"""
Iteration 71: Test POST /api/team/config with new alert fields
- alert_on_conversation
- alert_low_credits  
- low_credit_threshold
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTeamConfigAlertFields:
    """Test POST /api/team/config accepts new alert fields"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Auth failed: {response.status_code} - {response.text}")
    
    def test_team_config_with_alert_fields(self, auth_token):
        """Test POST /api/team/config accepts alert_on_conversation, alert_low_credits, low_credit_threshold"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # First check if user has a team
        team_response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        assert team_response.status_code == 200, f"Failed to get team: {team_response.text}"
        team_data = team_response.json()
        
        if not team_data.get("team"):
            pytest.skip("No team found for admin user")
        
        # Test POST /api/team/config with new alert fields
        config_payload = {
            "bot_name": "Test Assistant",
            "bot_tone": "professional",
            "bot_context": "Test context",
            "credit_limit_per_member": 100,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "Bonjour! Comment puis-je vous aider?",
            "end_of_credits_message": "Credits epuises",
            # NEW ALERT FIELDS
            "alert_on_conversation": True,
            "alert_low_credits": True,
            "low_credit_threshold": 75
        }
        
        response = requests.post(f"{BASE_URL}/api/team/config", headers=headers, json=config_payload)
        
        # Verify response
        assert response.status_code == 200, f"Config update failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got: {data}"
        print(f"PASS: POST /api/team/config accepted all alert fields")
        
        # Verify the settings were saved by fetching team again
        verify_response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        team_settings = verify_data.get("team", {}).get("settings", {})
        
        # Check alert settings were persisted
        assert team_settings.get("alert_on_conversation") == True, f"alert_on_conversation not saved: {team_settings}"
        assert team_settings.get("alert_low_credits") == True, f"alert_low_credits not saved: {team_settings}"
        assert team_settings.get("low_credit_threshold") == 75, f"low_credit_threshold not saved: {team_settings}"
        print(f"PASS: Alert settings persisted correctly in team.settings")
    
    def test_team_config_alert_fields_toggle_off(self, auth_token):
        """Test toggling alert fields off"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        config_payload = {
            "bot_name": "Test Assistant",
            "bot_tone": "professional",
            "bot_context": "",
            "credit_limit_per_member": 50,
            "auto_recharge": False,
            "chrome_link": False,
            "brand_color": "#1E3A8A",
            "welcome_message": "",
            "end_of_credits_message": "",
            # Toggle alerts OFF
            "alert_on_conversation": False,
            "alert_low_credits": False,
            "low_credit_threshold": 25
        }
        
        response = requests.post(f"{BASE_URL}/api/team/config", headers=headers, json=config_payload)
        assert response.status_code == 200, f"Config update failed: {response.status_code}"
        
        # Verify
        verify_response = requests.get(f"{BASE_URL}/api/team/me", headers=headers)
        team_settings = verify_response.json().get("team", {}).get("settings", {})
        
        assert team_settings.get("alert_on_conversation") == False, "alert_on_conversation should be False"
        assert team_settings.get("alert_low_credits") == False, "alert_low_credits should be False"
        assert team_settings.get("low_credit_threshold") == 25, "low_credit_threshold should be 25"
        print(f"PASS: Alert settings toggled off correctly")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
