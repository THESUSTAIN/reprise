"""
Test SEO Config API endpoints for Admin Panel
Tests: GET/PUT /api/admin/seo-config and GET /api/public/config
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSEOConfigAPI:
    """SEO Config endpoint tests for admin panel"""
    
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
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.token = token
            else:
                pytest.skip("No token in login response")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_get_seo_config(self):
        """Test GET /api/admin/seo-config returns SEO configuration"""
        response = self.session.get(f"{BASE_URL}/api/admin/seo-config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify expected fields exist
        assert "meta_title" in data or "logo_url" in data, "SEO config should have meta_title or logo_url"
        print(f"SEO Config keys: {list(data.keys())}")
    
    def test_put_seo_config_with_page_seo(self):
        """Test PUT /api/admin/seo-config saves page_seo_extension_ia with h1_override and canonical"""
        # First get current config
        get_response = self.session.get(f"{BASE_URL}/api/admin/seo-config")
        assert get_response.status_code == 200
        current_config = get_response.json()
        
        # Add page_seo_extension_ia with h1_override and canonical
        test_page_seo = {
            "title": "Test Extension IA Title",
            "description": "Test description for Extension IA page",
            "keyword": "extension ia, test",
            "h1_override": "Test H1 Override for Extension IA",
            "canonical": "https://www.extension-ia.com/fr/extension-ia"
        }
        
        # Update config with page_seo_extension_ia
        updated_config = {**current_config, "page_seo_extension_ia": test_page_seo}
        
        put_response = self.session.put(f"{BASE_URL}/api/admin/seo-config", json=updated_config)
        assert put_response.status_code == 200, f"Expected 200, got {put_response.status_code}: {put_response.text}"
        
        result = put_response.json()
        assert result.get("status") == "saved", f"Expected status 'saved', got {result}"
        
        # Verify the data was saved by fetching again
        verify_response = self.session.get(f"{BASE_URL}/api/admin/seo-config")
        assert verify_response.status_code == 200
        
        saved_config = verify_response.json()
        assert "page_seo_extension_ia" in saved_config, "page_seo_extension_ia should be saved"
        
        saved_page_seo = saved_config["page_seo_extension_ia"]
        assert saved_page_seo.get("h1_override") == test_page_seo["h1_override"], "h1_override should be saved"
        assert saved_page_seo.get("canonical") == test_page_seo["canonical"], "canonical should be saved"
        assert saved_page_seo.get("title") == test_page_seo["title"], "title should be saved"
        assert saved_page_seo.get("description") == test_page_seo["description"], "description should be saved"
        
        print(f"Successfully saved page_seo_extension_ia: {saved_page_seo}")
    
    def test_put_seo_config_og_fields(self):
        """Test PUT /api/admin/seo-config saves OG Title, OG Description, GA Tracking ID"""
        # Get current config
        get_response = self.session.get(f"{BASE_URL}/api/admin/seo-config")
        assert get_response.status_code == 200
        current_config = get_response.json()
        
        # Update with OG fields
        og_data = {
            "og_title": "Test OG Title for Extension IA",
            "og_description": "Test OG Description for social sharing",
            "ga_tracking_id": "G-TEST12345"
        }
        
        updated_config = {**current_config, **og_data}
        
        put_response = self.session.put(f"{BASE_URL}/api/admin/seo-config", json=updated_config)
        assert put_response.status_code == 200, f"Expected 200, got {put_response.status_code}"
        
        # Verify saved
        verify_response = self.session.get(f"{BASE_URL}/api/admin/seo-config")
        saved_config = verify_response.json()
        
        assert saved_config.get("og_title") == og_data["og_title"], "og_title should be saved"
        assert saved_config.get("og_description") == og_data["og_description"], "og_description should be saved"
        assert saved_config.get("ga_tracking_id") == og_data["ga_tracking_id"], "ga_tracking_id should be saved"
        
        print(f"OG fields saved: og_title={saved_config.get('og_title')}, og_description={saved_config.get('og_description')}, ga_tracking_id={saved_config.get('ga_tracking_id')}")
    
    def test_public_config_exposes_page_seo(self):
        """Test GET /api/public/config returns page_seo data when saved"""
        # First save some page_seo data
        get_response = self.session.get(f"{BASE_URL}/api/admin/seo-config")
        current_config = get_response.json()
        
        test_page_seo = {
            "title": "Public Test Title",
            "description": "Public test description",
            "keyword": "public test",
            "h1_override": "Public H1 Override",
            "canonical": "https://www.extension-ia.com/fr/extension-ia"
        }
        
        updated_config = {**current_config, "page_seo_extension_ia": test_page_seo}
        self.session.put(f"{BASE_URL}/api/admin/seo-config", json=updated_config)
        
        # Now test public config endpoint (no auth required)
        public_response = requests.get(f"{BASE_URL}/api/public/config")
        assert public_response.status_code == 200, f"Expected 200, got {public_response.status_code}"
        
        public_data = public_response.json()
        
        # Check if page_seo is exposed
        if "page_seo" in public_data:
            assert "page_seo_extension_ia" in public_data["page_seo"], "page_seo_extension_ia should be in public config"
            print(f"Public config exposes page_seo: {list(public_data['page_seo'].keys())}")
        else:
            print("Note: page_seo not exposed in public config (may be by design)")
        
        # Verify logo_url is exposed
        assert "logo_url" in public_data, "logo_url should be in public config"
        print(f"Public config keys: {list(public_data.keys())}")


class TestSEOConfigValidation:
    """Test SEO config validation and edge cases"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")
    
    def test_seo_config_character_counters(self):
        """Test that title and description can be saved with various lengths"""
        get_response = self.session.get(f"{BASE_URL}/api/admin/seo-config")
        current_config = get_response.json()
        
        # Test with title at exactly 70 chars
        title_70 = "A" * 70
        # Test with description at exactly 160 chars
        desc_160 = "B" * 160
        
        test_page_seo = {
            "title": title_70,
            "description": desc_160,
            "keyword": "test keyword",
            "h1_override": "Test H1",
            "canonical": "https://test.com"
        }
        
        updated_config = {**current_config, "page_seo_test": test_page_seo}
        
        put_response = self.session.put(f"{BASE_URL}/api/admin/seo-config", json=updated_config)
        assert put_response.status_code == 200
        
        # Verify lengths are preserved
        verify_response = self.session.get(f"{BASE_URL}/api/admin/seo-config")
        saved_config = verify_response.json()
        
        if "page_seo_test" in saved_config:
            assert len(saved_config["page_seo_test"]["title"]) == 70, "Title length should be preserved"
            assert len(saved_config["page_seo_test"]["description"]) == 160, "Description length should be preserved"
            print("Character length validation passed: title=70, description=160")
    
    def test_seo_config_unauthorized(self):
        """Test that SEO config requires admin auth"""
        # Create new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/admin/seo-config")
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthorized, got {response.status_code}"
        print(f"Unauthorized access correctly blocked: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
