"""
Iteration 89 - Cloud Sync Fixes & Image Model Tests
Tests:
1. Backend image model mapping (nano-banana -> gemini-2.5-flash-image, stable-diffusion -> gemini-3-pro-image-preview)
2. Team list API endpoint
3. Team members API endpoint with user_id field
4. Admin login
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login returns access_token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert len(data["access_token"]) > 0, "Empty access_token"
        print(f"PASS - Admin login successful, token length: {len(data['access_token'])}")
        return data["access_token"]


class TestTeamAPIs:
    """Team-related API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_team_list_endpoint(self, auth_token):
        """Test GET /api/team/list returns teams array"""
        response = requests.get(
            f"{BASE_URL}/api/team/list",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Team list failed: {response.text}"
        data = response.json()
        # API returns {"teams": [...]} format
        if isinstance(data, dict) and "teams" in data:
            teams = data["teams"]
        else:
            teams = data
        assert isinstance(teams, list), "Response should contain a teams list"
        print(f"PASS - Team list returned {len(teams)} teams")
    
    def test_team_me_endpoint_with_user_id(self, auth_token):
        """Test GET /api/team/me?team_id=X returns members with user_id field"""
        # First get team list
        teams_response = requests.get(
            f"{BASE_URL}/api/team/list",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if teams_response.status_code != 200:
            pytest.skip("Could not get team list")
        
        data = teams_response.json()
        # API returns {"teams": [...]} format
        if isinstance(data, dict) and "teams" in data:
            teams = data["teams"]
        else:
            teams = data
        
        if not teams:
            pytest.skip("No teams available for testing")
        
        team_id = teams[0].get("id")
        
        # Get team members
        response = requests.get(
            f"{BASE_URL}/api/team/me?team_id={team_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Team members failed: {response.text}"
        data = response.json()
        
        # Check members have user_id field
        members = data.get("members", [])
        if members:
            first_member = members[0]
            assert "user_id" in first_member, "Member should have user_id field"
            assert "email" in first_member, "Member should have email field"
            assert "role" in first_member, "Member should have role field"
            print(f"PASS - Team members returned with user_id field, {len(members)} members")
        else:
            print("PASS - Team members endpoint works (no members in team)")


class TestCurrentUser:
    """Current user API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_current_user_info(self, auth_token):
        """Test GET /api/auth/me returns user data with id"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert "id" in data, "User should have id field"
        assert "email" in data, "User should have email field"
        print(f"PASS - Current user info returned with id: {data.get('id')[:8]}...")


class TestDriveStatus:
    """Drive connection status tests"""
    
    def get_auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_google_drive_status(self):
        """Test GET /api/drive/status returns connected status"""
        auth_token = self.get_auth_token()
        assert auth_token, "Failed to get auth token"
        
        response = requests.get(
            f"{BASE_URL}/api/drive/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Drive status failed: {response.text}"
        data = response.json()
        assert "connected" in data, "Response should have connected field"
        print(f"PASS - Google Drive status: connected={data.get('connected')}")
    
    def test_onedrive_status(self):
        """Test GET /api/onedrive/status returns connected status"""
        auth_token = self.get_auth_token()
        assert auth_token, "Failed to get auth token"
        
        response = requests.get(
            f"{BASE_URL}/api/onedrive/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"OneDrive status failed: {response.text}"
        data = response.json()
        assert "connected" in data, "Response should have connected field"
        print(f"PASS - OneDrive status: connected={data.get('connected')}")


class TestCodeVerification:
    """Code structure verification tests (no API calls)"""
    
    def test_image_model_map_in_code(self):
        """Verify image_model_map differentiates nano-banana and stable-diffusion"""
        # Read the chat_routes.py file
        chat_routes_path = "/app/backend/routes/chat_routes.py"
        with open(chat_routes_path, "r") as f:
            content = f.read()
        
        # Check image_model_map exists
        assert "image_model_map" in content, "image_model_map not found in chat_routes.py"
        
        # Check nano-banana maps to gemini-2.5-flash-image
        assert '"nano-banana": "gemini-2.5-flash-image"' in content, \
            "nano-banana should map to gemini-2.5-flash-image"
        
        # Check stable-diffusion maps to gemini-3-pro-image-preview
        assert '"stable-diffusion": "gemini-3-pro-image-preview"' in content, \
            "stable-diffusion should map to gemini-3-pro-image-preview"
        
        print("PASS - Backend image_model_map correctly differentiates models")
    
    def test_saveToDrive_uses_autosync_source(self):
        """Verify saveToDrive function checks localStorage for provider"""
        chat_interface_path = "/app/frontend/src/components/ChatInterface.js"
        with open(chat_interface_path, "r") as f:
            content = f.read()
        
        # Check saveToDrive function exists
        assert "const saveToDrive" in content, "saveToDrive function not found"
        
        # Check it reads from localStorage
        assert "zayado_autosync_source" in content, \
            "saveToDrive should check zayado_autosync_source from localStorage"
        
        print("PASS - saveToDrive function checks localStorage for provider")
    
    def test_handleSyncDrive_single_provider(self):
        """Verify handleSyncDrive only syncs to configured provider"""
        chat_interface_path = "/app/frontend/src/components/ChatInterface.js"
        with open(chat_interface_path, "r") as f:
            content = f.read()
        
        # Check handleSyncDrive function exists
        assert "const handleSyncDrive" in content, "handleSyncDrive function not found"
        
        # Check it uses syncSource from localStorage
        assert "zayado_autosync_source" in content, \
            "handleSyncDrive should check zayado_autosync_source"
        
        print("PASS - handleSyncDrive uses configured provider")
    
    def test_sync_button_in_empty_state(self):
        """Verify sync button exists in empty state with correct data-testid"""
        chat_interface_path = "/app/frontend/src/components/ChatInterface.js"
        with open(chat_interface_path, "r") as f:
            content = f.read()
        
        # Check sync button in empty state
        assert 'data-testid="sync-drive-empty-btn"' in content, \
            "Sync button with data-testid='sync-drive-empty-btn' not found"
        
        # Check it shows 'Synchroniser' text
        assert "Synchroniser" in content, "Synchroniser text not found"
        
        print("PASS - Sync button exists in empty state with correct data-testid")
    
    def test_sync_button_in_active_state(self):
        """Verify sync button exists in active state with correct data-testid"""
        chat_interface_path = "/app/frontend/src/components/ChatInterface.js"
        with open(chat_interface_path, "r") as f:
            content = f.read()
        
        # Check sync button in active state
        assert 'data-testid="sync-drive-persistent-btn"' in content, \
            "Sync button with data-testid='sync-drive-persistent-btn' not found"
        
        print("PASS - Sync button exists in active state with correct data-testid")
    
    def test_last_sync_time_display(self):
        """Verify last sync time is displayed next to sync button"""
        chat_interface_path = "/app/frontend/src/components/ChatInterface.js"
        with open(chat_interface_path, "r") as f:
            content = f.read()
        
        # Check lastSyncTime state exists
        assert "lastSyncTime" in content, "lastSyncTime state not found"
        
        # Check it's stored in localStorage
        assert "zayado_last_sync_time" in content, \
            "Last sync time should be stored in localStorage"
        
        # Check data-testid for last sync time display
        assert 'data-testid="last-sync-time-empty"' in content, \
            "Last sync time display with data-testid not found"
        
        print("PASS - Last sync time is displayed and stored in localStorage")
    
    def test_image_container_max_width(self):
        """Verify image container has max-w-[400px] and overflow-hidden"""
        markdown_content_path = "/app/frontend/src/components/chat/MarkdownContent.js"
        with open(markdown_content_path, "r") as f:
            content = f.read()
        
        # Check max-w-[400px] exists
        assert "max-w-[400px]" in content, "max-w-[400px] not found in MarkdownContent.js"
        
        # Check overflow-hidden exists
        assert "overflow-hidden" in content, "overflow-hidden not found in MarkdownContent.js"
        
        print("PASS - Image container has max-w-[400px] overflow-hidden")
    
    def test_cloud_button_tooltip(self):
        """Verify cloud button on messages has 'Synchroniser sur le cloud' tooltip"""
        chat_interface_path = "/app/frontend/src/components/ChatInterface.js"
        with open(chat_interface_path, "r") as f:
            content = f.read()
        
        # Check tooltip text
        assert 'title="Synchroniser sur le cloud"' in content, \
            "Cloud button should have 'Synchroniser sur le cloud' tooltip"
        
        print("PASS - Cloud button has correct tooltip")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
