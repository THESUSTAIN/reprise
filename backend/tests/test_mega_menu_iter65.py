"""
Iteration 65: Mega Menu API Tests
Tests for:
- GET /api/public/config (mega_menu field)
- GET /api/admin/mega-menu (admin only)
- PUT /api/admin/mega-menu (admin only)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-panel-416.preview.emergentagent.com')

class TestPublicConfig:
    """Test public config endpoint returns mega_menu"""
    
    def test_public_config_returns_mega_menu(self):
        """GET /api/public/config should return mega_menu object"""
        response = requests.get(f"{BASE_URL}/api/public/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "mega_menu" in data, "mega_menu field missing from public config"
        assert "items" in data["mega_menu"], "items array missing from mega_menu"
        
        items = data["mega_menu"]["items"]
        assert len(items) >= 5, f"Expected at least 5 items, got {len(items)}"
        
        # Verify item structure
        for item in items:
            assert "key" in item, "item missing 'key'"
            assert "label" in item, "item missing 'label'"
            assert "url" in item, "item missing 'url'"
            assert "enabled" in item, "item missing 'enabled'"
    
    def test_public_config_default_items(self):
        """Verify default menu items are present"""
        response = requests.get(f"{BASE_URL}/api/public/config")
        assert response.status_code == 200
        
        items = response.json()["mega_menu"]["items"]
        keys = [item["key"] for item in items]
        
        expected_keys = ["jeMeLance", "jePilote", "jeGrandis", "boutique", "contact"]
        for key in expected_keys:
            assert key in keys, f"Expected key '{key}' not found in items"


class TestAdminMegaMenu:
    """Test admin mega menu endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@zayado.net", "password": "admin123"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture
    def admin_headers(self, admin_token):
        """Headers with admin auth"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_mega_menu_config(self, admin_headers):
        """GET /api/admin/mega-menu returns menu config"""
        response = requests.get(f"{BASE_URL}/api/admin/mega-menu", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data, "items array missing"
        assert len(data["items"]) >= 5, "Expected at least 5 items"
    
    def test_get_mega_menu_unauthorized(self):
        """GET /api/admin/mega-menu without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/admin/mega-menu")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_update_mega_menu_config(self, admin_headers):
        """PUT /api/admin/mega-menu updates config"""
        # First get current config
        get_response = requests.get(f"{BASE_URL}/api/admin/mega-menu", headers=admin_headers)
        original_items = get_response.json()["items"]
        
        # Update with test value
        test_items = original_items.copy()
        test_items[0]["label"] = "TEST_LABEL_UPDATE"
        
        put_response = requests.put(
            f"{BASE_URL}/api/admin/mega-menu",
            headers=admin_headers,
            json={"items": test_items}
        )
        assert put_response.status_code == 200
        assert put_response.json().get("status") == "saved"
        
        # Verify update persisted
        verify_response = requests.get(f"{BASE_URL}/api/admin/mega-menu", headers=admin_headers)
        assert verify_response.json()["items"][0]["label"] == "TEST_LABEL_UPDATE"
        
        # Restore original
        requests.put(
            f"{BASE_URL}/api/admin/mega-menu",
            headers=admin_headers,
            json={"items": original_items}
        )
    
    def test_update_mega_menu_unauthorized(self):
        """PUT /api/admin/mega-menu without auth returns 401/403"""
        response = requests.put(
            f"{BASE_URL}/api/admin/mega-menu",
            json={"items": []}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_mega_menu_item_toggle(self, admin_headers):
        """Test toggling item enabled/disabled"""
        # Get current config
        get_response = requests.get(f"{BASE_URL}/api/admin/mega-menu", headers=admin_headers)
        items = get_response.json()["items"]
        
        # Toggle first item
        original_enabled = items[0]["enabled"]
        items[0]["enabled"] = not original_enabled
        
        put_response = requests.put(
            f"{BASE_URL}/api/admin/mega-menu",
            headers=admin_headers,
            json={"items": items}
        )
        assert put_response.status_code == 200
        
        # Verify toggle persisted
        verify_response = requests.get(f"{BASE_URL}/api/admin/mega-menu", headers=admin_headers)
        assert verify_response.json()["items"][0]["enabled"] == (not original_enabled)
        
        # Restore original
        items[0]["enabled"] = original_enabled
        requests.put(
            f"{BASE_URL}/api/admin/mega-menu",
            headers=admin_headers,
            json={"items": items}
        )
    
    def test_public_config_reflects_admin_changes(self, admin_headers):
        """Changes via admin API should reflect in public config"""
        # Get current config
        get_response = requests.get(f"{BASE_URL}/api/admin/mega-menu", headers=admin_headers)
        original_items = get_response.json()["items"]
        
        # Update with test value
        test_items = original_items.copy()
        test_items[0]["label"] = "PUBLIC_TEST_SYNC"
        
        requests.put(
            f"{BASE_URL}/api/admin/mega-menu",
            headers=admin_headers,
            json={"items": test_items}
        )
        
        # Verify public config reflects change
        public_response = requests.get(f"{BASE_URL}/api/public/config")
        assert public_response.json()["mega_menu"]["items"][0]["label"] == "PUBLIC_TEST_SYNC"
        
        # Restore original
        requests.put(
            f"{BASE_URL}/api/admin/mega-menu",
            headers=admin_headers,
            json={"items": original_items}
        )


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """API health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
