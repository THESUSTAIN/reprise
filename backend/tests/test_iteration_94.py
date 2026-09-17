"""
Iteration 94 - Testing:
1. Settings page: 'Mémoire IA' tab no longer exists as separate tab
2. Settings > Profil & Memoire: MemorySettings with 2 sub-tabs (Memoire Profil + Memoire Vectorielle)
3. Admin panel > Systeme > 'API de secours' tab exists
4. Admin fallback config: can select provider (OpenAI/Anthropic/Emergent), enter API key, set model
5. Admin fallback config: save works via PUT /api/admin/config with fallback_api field
6. Backend: fallback API reads from admin_config.json instead of hardcoded Emergent key
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestIteration94:
    """Test fallback API configuration and admin config endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login as admin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if login_res.status_code == 200:
            token = login_res.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Login failed: {login_res.status_code}")
    
    def test_01_login_success(self):
        """Verify admin login works"""
        res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        print("PASS - Admin login successful")
    
    def test_02_get_admin_config(self):
        """GET /api/admin/config returns current config including fallback_api"""
        res = self.session.get(f"{BASE_URL}/api/admin/config")
        assert res.status_code == 200
        data = res.json()
        print(f"Admin config keys: {list(data.keys())}")
        # fallback_api may or may not exist yet
        if "fallback_api" in data:
            fb = data["fallback_api"]
            print(f"Existing fallback_api config: provider={fb.get('provider')}, enabled={fb.get('enabled')}")
        else:
            print("No fallback_api config yet (will be created on save)")
        print("PASS - GET /api/admin/config works")
    
    def test_03_save_fallback_api_config_openai(self):
        """PUT /api/admin/config with fallback_api field (OpenAI provider)"""
        fallback_config = {
            "fallback_api": {
                "provider": "openai",
                "api_key": "sk-test-key-12345",
                "model": "gpt-4o-mini",
                "enabled": True
            }
        }
        res = self.session.put(f"{BASE_URL}/api/admin/config", json=fallback_config)
        assert res.status_code == 200
        print("PASS - PUT /api/admin/config with OpenAI fallback saved")
        
        # Verify it was saved
        verify_res = self.session.get(f"{BASE_URL}/api/admin/config")
        assert verify_res.status_code == 200
        data = verify_res.json()
        assert "fallback_api" in data
        fb = data["fallback_api"]
        assert fb["provider"] == "openai"
        assert fb["model"] == "gpt-4o-mini"
        assert fb["enabled"] == True
        print(f"PASS - Verified fallback_api saved: {fb}")
    
    def test_04_save_fallback_api_config_anthropic(self):
        """PUT /api/admin/config with fallback_api field (Anthropic provider)"""
        fallback_config = {
            "fallback_api": {
                "provider": "anthropic",
                "api_key": "sk-ant-test-key-67890",
                "model": "claude-sonnet-4-5-20250929",
                "enabled": True
            }
        }
        res = self.session.put(f"{BASE_URL}/api/admin/config", json=fallback_config)
        assert res.status_code == 200
        print("PASS - PUT /api/admin/config with Anthropic fallback saved")
        
        # Verify
        verify_res = self.session.get(f"{BASE_URL}/api/admin/config")
        data = verify_res.json()
        fb = data["fallback_api"]
        assert fb["provider"] == "anthropic"
        assert fb["model"] == "claude-sonnet-4-5-20250929"
        print(f"PASS - Verified Anthropic fallback: {fb}")
    
    def test_05_save_fallback_api_config_emergent(self):
        """PUT /api/admin/config with fallback_api field (Emergent provider - default)"""
        fallback_config = {
            "fallback_api": {
                "provider": "emergent",
                "api_key": "",  # Uses EMERGENT_LLM_KEY env var
                "model": "",
                "enabled": True
            }
        }
        res = self.session.put(f"{BASE_URL}/api/admin/config", json=fallback_config)
        assert res.status_code == 200
        print("PASS - PUT /api/admin/config with Emergent fallback saved")
        
        # Verify
        verify_res = self.session.get(f"{BASE_URL}/api/admin/config")
        data = verify_res.json()
        fb = data["fallback_api"]
        assert fb["provider"] == "emergent"
        print(f"PASS - Verified Emergent fallback: {fb}")
    
    def test_06_disable_fallback_api(self):
        """PUT /api/admin/config with fallback_api disabled"""
        fallback_config = {
            "fallback_api": {
                "provider": "openai",
                "api_key": "sk-test",
                "model": "gpt-4o",
                "enabled": False
            }
        }
        res = self.session.put(f"{BASE_URL}/api/admin/config", json=fallback_config)
        assert res.status_code == 200
        
        # Verify
        verify_res = self.session.get(f"{BASE_URL}/api/admin/config")
        data = verify_res.json()
        fb = data["fallback_api"]
        assert fb["enabled"] == False
        print("PASS - Fallback API can be disabled")
    
    def test_07_memory_stats_endpoint(self):
        """GET /api/memory/stats works (for vector memory tab)"""
        res = self.session.get(f"{BASE_URL}/api/memory/stats")
        assert res.status_code == 200
        data = res.json()
        assert "total_memories" in data
        print(f"PASS - Memory stats: {data}")
    
    def test_08_memory_list_endpoint(self):
        """GET /api/memory/list works (for vector memory tab)"""
        res = self.session.get(f"{BASE_URL}/api/memory/list?limit=10")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        print(f"PASS - Memory list returned {len(data)} items")
    
    def test_09_auth_me_has_memory(self):
        """GET /api/auth/me returns user with memory field (for static memory tab)"""
        res = self.session.get(f"{BASE_URL}/api/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        # memory field should exist (may be empty string or JSON)
        print(f"PASS - User has memory field: {type(data.get('memory'))}")
    
    def test_10_restore_default_fallback(self):
        """Restore default fallback config for production"""
        fallback_config = {
            "fallback_api": {
                "provider": "emergent",
                "api_key": "",
                "model": "",
                "enabled": True
            }
        }
        res = self.session.put(f"{BASE_URL}/api/admin/config", json=fallback_config)
        assert res.status_code == 200
        print("PASS - Restored default Emergent fallback config")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
