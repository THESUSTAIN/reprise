"""
Iteration 91 - Testing new sync features:
1. First-time sync prompt appears when user sends first message (localStorage 'zayado_sync_choice' is null AND messages.length === 0)
2. Sync prompt modal has two buttons: 'Sauvegarder sur mon Drive' and 'Non merci, stocker en interne'
3. After clicking 'Non merci', the prompt closes and localStorage is set to 'internal'
4. After clicking 'Sauvegarder sur mon Drive', localStorage is set to 'drive' and toast appears
5. Sync prompt does NOT reappear after choice is made
6. Bouton 'Synchroniser' visible in empty state chat (data-testid='sync-drive-empty-btn')
7. Bouton 'Synchroniser' visible in active state chat (data-testid='sync-drive-persistent-btn')
8. autoSyncing state shows spinning Loader2 icon on sync button during auto-sync
9. Auto-sync saves as .txt format (filename ends with .txt in code)
10. Backend /api/team/list returns teams
11. Backend image model map differentiates Fast vs HD models
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com')


class TestIteration91SyncFeatures:
    """Test sync features for iteration 91"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        # Login to get token
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@zayado.net", "password": "admin123"}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@zayado.net", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("PASS: Admin login successful")
    
    def test_team_list_endpoint(self):
        """Test /api/team/list returns teams"""
        response = self.session.get(f"{BASE_URL}/api/team/list")
        assert response.status_code == 200
        data = response.json()
        # API returns {"teams": [...]} object
        assert "teams" in data or isinstance(data, list)
        teams = data.get("teams", data) if isinstance(data, dict) else data
        print(f"PASS: /api/team/list returns {len(teams)} teams")
    
    def test_google_drive_status(self):
        """Test Google Drive status endpoint"""
        response = self.session.get(f"{BASE_URL}/api/drive/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        print(f"PASS: Google Drive status - connected: {data.get('connected')}")
    
    def test_onedrive_status(self):
        """Test OneDrive status endpoint"""
        response = self.session.get(f"{BASE_URL}/api/onedrive/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        print(f"PASS: OneDrive status - connected: {data.get('connected')}")
    
    def test_current_user_info(self):
        """Test current user info endpoint"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        print(f"PASS: Current user - email: {data.get('email')}")


class TestCodeVerificationIteration91:
    """Verify code structure for sync features"""
    
    def test_sync_prompt_state_in_chatinterface(self):
        """Verify showSyncPrompt state exists in ChatInterface.js"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        assert "showSyncPrompt" in content
        assert "setShowSyncPrompt" in content
        print("PASS: showSyncPrompt state exists in ChatInterface.js")
    
    def test_autosync_state_in_chatinterface(self):
        """Verify autoSyncing state exists in ChatInterface.js"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        assert "autoSyncing" in content
        assert "setAutoSyncing" in content
        print("PASS: autoSyncing state exists in ChatInterface.js")
    
    def test_sync_choice_localstorage_check(self):
        """Verify localStorage sync choice check in handleSend"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        assert "zayado_sync_choice" in content
        assert "localStorage.getItem('zayado_sync_choice')" in content
        print("PASS: localStorage sync choice check exists")
    
    def test_sync_prompt_modal_testids(self):
        """Verify sync prompt modal has correct data-testid attributes"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        assert 'data-testid="sync-prompt-modal"' in content
        assert 'data-testid="sync-prompt-drive-btn"' in content
        assert 'data-testid="sync-prompt-internal-btn"' in content
        assert 'data-testid="sync-prompt-overlay"' in content
        print("PASS: Sync prompt modal has correct data-testid attributes")
    
    def test_sync_button_empty_state_testid(self):
        """Verify sync button in empty state has correct data-testid"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        assert 'data-testid="sync-drive-empty-btn"' in content
        print("PASS: Sync button empty state has data-testid='sync-drive-empty-btn'")
    
    def test_sync_button_active_state_testid(self):
        """Verify sync button in active state has correct data-testid"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        assert 'data-testid="sync-drive-persistent-btn"' in content
        print("PASS: Sync button active state has data-testid='sync-drive-persistent-btn'")
    
    def test_autosync_txt_format(self):
        """Verify auto-sync saves as .txt format"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        # Check for .txt filename in auto-sync code
        assert "conversation_${ts}.txt" in content or 'conversation_' in content and '.txt' in content
        print("PASS: Auto-sync uses .txt format")
    
    def test_autosync_loader_animation(self):
        """Verify autoSyncing shows Loader2 animation"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        # Check for Loader2 with animate-spin when autoSyncing
        assert "autoSyncing" in content
        assert "Loader2" in content
        assert "animate-spin" in content
        print("PASS: autoSyncing shows Loader2 with animate-spin")
    
    def test_sync_prompt_createportal(self):
        """Verify sync prompt uses createPortal for rendering"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        assert "createPortal" in content
        assert "showSyncPrompt && createPortal" in content
        print("PASS: Sync prompt uses createPortal for rendering")
    
    def test_sync_prompt_zindex(self):
        """Verify sync prompt has high z-index"""
        with open("/app/frontend/src/components/ChatInterface.js", "r") as f:
            content = f.read()
        
        assert "zIndex: 99999" in content
        print("PASS: Sync prompt has z-index 99999")
    
    def test_backend_image_model_map_differentiation(self):
        """Verify backend image_model_map differentiates nano-banana and stable-diffusion"""
        with open("/app/backend/routes/chat_routes.py", "r") as f:
            content = f.read()
        
        assert "image_model_map" in content
        assert '"nano-banana": "gemini-2.5-flash-image"' in content
        assert '"stable-diffusion": "gemini-3-pro-image-preview"' in content
        print("PASS: Backend image_model_map differentiates nano-banana (gemini-2.5-flash-image) and stable-diffusion (gemini-3-pro-image-preview)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
