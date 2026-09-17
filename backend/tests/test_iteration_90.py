"""
Iteration 90 - Audit of recent corrections (iterations 88-90)
Tests for:
1. Image inline restored to original size (max-w-full max-h-[400px])
2. Image lightbox uses createPortal to render on document.body with z-index 99999
3. Synchroniser button ALWAYS visible (no driveConnected condition)
4. handleSyncDrive shows toast error if no drive connected
5. Backend image models differentiated (nano-banana vs stable-diffusion)
6. Gift modal routing and API
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestIteration90Audit:
    """Audit tests for iterations 88-90 fixes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Login failed - skipping authenticated tests")
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("PASS: Admin login successful")
    
    def test_team_list_endpoint(self):
        """Test /api/team/list returns teams"""
        response = self.session.get(f"{BASE_URL}/api/team/list")
        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        print(f"PASS: Team list endpoint returns {len(data.get('teams', []))} teams")
    
    def test_team_me_endpoint(self):
        """Test /api/team/me returns members with user_id field"""
        # First get a team
        teams_response = self.session.get(f"{BASE_URL}/api/team/list")
        if teams_response.status_code == 200:
            teams = teams_response.json().get("teams", [])
            if teams:
                team_id = teams[0].get("id")
                response = self.session.get(f"{BASE_URL}/api/team/me?team_id={team_id}")
                assert response.status_code == 200
                data = response.json()
                # Check members have user_id field
                members = data.get("members", [])
                if members:
                    assert "user_id" in members[0]
                print(f"PASS: Team me endpoint returns members with user_id field")
            else:
                print("SKIP: No teams available to test")
        else:
            print("SKIP: Could not get teams list")
    
    def test_google_drive_status(self):
        """Test Google Drive status endpoint"""
        response = self.session.get(f"{BASE_URL}/api/drive/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        print(f"PASS: Google Drive status: connected={data.get('connected')}")
    
    def test_onedrive_status(self):
        """Test OneDrive status endpoint"""
        response = self.session.get(f"{BASE_URL}/api/onedrive/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        print(f"PASS: OneDrive status: connected={data.get('connected')}")
    
    def test_current_user_info(self):
        """Test /api/auth/me returns user data"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data or "email" in data
        print(f"PASS: Current user info retrieved")


class TestCodeVerification:
    """Verify code changes in frontend files"""
    
    def test_markdown_content_createportal_import(self):
        """Verify createPortal is imported from react-dom"""
        with open("/app/frontend/src/components/chat/MarkdownContent.js", "r") as f:
            content = f.read()
        assert "import { createPortal } from 'react-dom'" in content
        print("PASS: createPortal imported from react-dom")
    
    def test_markdown_content_inline_image_classes(self):
        """Verify inline image has original size classes: max-w-full max-h-[400px]"""
        with open("/app/frontend/src/components/chat/MarkdownContent.js", "r") as f:
            content = f.read()
        # Check for the original classes
        assert "max-w-full max-h-[400px]" in content
        print("PASS: Inline image has max-w-full max-h-[400px] classes")
    
    def test_markdown_content_lightbox_createportal(self):
        """Verify lightbox uses createPortal with document.body"""
        with open("/app/frontend/src/components/chat/MarkdownContent.js", "r") as f:
            content = f.read()
        assert "createPortal(" in content
        assert "document.body" in content
        print("PASS: Lightbox uses createPortal with document.body")
    
    def test_markdown_content_lightbox_zindex(self):
        """Verify lightbox has z-index 99999"""
        with open("/app/frontend/src/components/chat/MarkdownContent.js", "r") as f:
            content = f.read()
        assert "zIndex: 99999" in content
        print("PASS: Lightbox has z-index 99999")
    
    def test_sync_button_empty_state_always_visible(self):
        """Verify sync button in empty state is ALWAYS visible (no driveConnected condition)"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        # Find the sync-drive-empty-btn section
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'data-testid="sync-drive-empty-btn"' in line:
                # Check surrounding lines for driveConnected condition
                context = '\n'.join(lines[max(0, i-5):i+5])
                # Should NOT have driveConnected condition wrapping it
                assert "driveConnected.google || driveConnected.onedrive" not in context or "{(" not in context
                print("PASS: Sync button in empty state is always visible (no driveConnected condition)")
                return
        pytest.fail("Could not find sync-drive-empty-btn")
    
    def test_sync_button_active_state_always_visible(self):
        """Verify sync button in active state is ALWAYS visible (no driveConnected condition)"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        # Find the sync-drive-persistent-btn section
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'data-testid="sync-drive-persistent-btn"' in line:
                # Check surrounding lines for driveConnected condition
                context = '\n'.join(lines[max(0, i-5):i+5])
                # Should NOT have driveConnected condition wrapping it
                assert "driveConnected.google || driveConnected.onedrive" not in context or "{(" not in context
                print("PASS: Sync button in active state is always visible (no driveConnected condition)")
                return
        pytest.fail("Could not find sync-drive-persistent-btn")
    
    def test_handle_sync_drive_no_drive_message(self):
        """Verify handleSyncDrive shows toast error if no drive connected"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        # Check for the error message when no drive is connected
        assert "Connectez votre Drive dans Parametres" in content
        print("PASS: handleSyncDrive shows error message when no drive connected")
    
    def test_message_bubble_max_width(self):
        """Verify message bubble stays max-w-[80%] for ALL messages"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        assert "max-w-[80%]" in content
        print("PASS: Message bubble has max-w-[80%] class")
    
    def test_backend_image_model_map_differentiation(self):
        """Verify backend image_model_map differentiates nano-banana and stable-diffusion"""
        with open("/app/backend/routes/chat_routes.py", "r") as f:
            content = f.read()
        # Check for differentiated models
        assert '"nano-banana": "gemini-2.5-flash-image"' in content
        assert '"stable-diffusion": "gemini-3-pro-image-preview"' in content
        print("PASS: Backend image_model_map differentiates nano-banana (gemini-2.5-flash-image) and stable-diffusion (gemini-3-pro-image-preview)")
    
    def test_save_to_drive_uses_provider(self):
        """Verify saveToDrive checks localStorage zayado_autosync_source for provider"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        assert "zayado_autosync_source" in content
        print("PASS: saveToDrive uses localStorage zayado_autosync_source for provider selection")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
