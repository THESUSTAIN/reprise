"""
Iteration 37 - UI Restructuring Tests
Tests for:
1. Newsletter endpoint (POST /api/public/newsletter)
2. Simulateur config endpoints (GET/POST /api/admin/simulateur-config)
3. Resources config endpoints (GET/POST /api/admin/resources-config)
4. Admin page accessibility
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("PASS: Health check returns 200")
    
    def test_login_admin(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data or "access_token" in data
        print("PASS: Admin login successful")
        return data.get("token") or data.get("access_token")


class TestNewsletterEndpoint:
    """Test POST /api/public/newsletter"""
    
    def test_newsletter_signup_success(self):
        """Test newsletter signup with valid email"""
        response = requests.post(f"{BASE_URL}/api/public/newsletter", json={
            "email": "test_newsletter@example.com",
            "source": "boutique_ia"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("PASS: Newsletter signup returns 200 with status ok")
    
    def test_newsletter_signup_general_source(self):
        """Test newsletter signup with general source"""
        response = requests.post(f"{BASE_URL}/api/public/newsletter", json={
            "email": "test_general@example.com",
            "source": "general"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("PASS: Newsletter signup with general source works")
    
    def test_newsletter_duplicate_email(self):
        """Test newsletter signup with duplicate email (should still return ok)"""
        # First signup
        requests.post(f"{BASE_URL}/api/public/newsletter", json={
            "email": "duplicate_test@example.com",
            "source": "boutique_ia"
        })
        # Second signup with same email
        response = requests.post(f"{BASE_URL}/api/public/newsletter", json={
            "email": "duplicate_test@example.com",
            "source": "boutique_ia"
        })
        assert response.status_code == 200
        print("PASS: Duplicate newsletter signup handled gracefully")


class TestSimulateurConfig:
    """Test simulateur config endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        self.token = response.json().get("token") or response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_simulateur_config(self):
        """Test GET /api/admin/simulateur-config"""
        response = requests.get(f"{BASE_URL}/api/admin/simulateur-config", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: GET simulateur-config returns list with {len(data)} items")
    
    def test_post_simulateur_config_admin(self):
        """Test POST /api/admin/simulateur-config (admin only)"""
        test_items = [
            {"id": "test_sim_1", "label": "Test Simulator", "type": "iframe", "url": "https://example.com", "icon": "calculator"},
            {"id": "test_sim_2", "label": "External Tool", "type": "redirect", "url": "https://tool.example.com", "icon": "globe"}
        ]
        response = requests.post(f"{BASE_URL}/api/admin/simulateur-config", 
            headers={**self.headers, "Content-Type": "application/json"},
            json={"items": test_items}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("PASS: POST simulateur-config saves items successfully")
        
        # Verify items were saved
        get_response = requests.get(f"{BASE_URL}/api/admin/simulateur-config", headers=self.headers)
        saved_items = get_response.json()
        assert len(saved_items) == 2
        assert saved_items[0]["id"] == "test_sim_1"
        print("PASS: Simulateur config items persisted correctly")
    
    def test_simulateur_config_requires_auth(self):
        """Test that simulateur-config GET requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/simulateur-config")
        assert response.status_code in [401, 403, 422]
        print("PASS: Simulateur config requires authentication")


class TestResourcesConfig:
    """Test resources config endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        self.token = response.json().get("token") or response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_resources_config(self):
        """Test GET /api/admin/resources-config"""
        response = requests.get(f"{BASE_URL}/api/admin/resources-config", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: GET resources-config returns list with {len(data)} items")
    
    def test_post_resources_config_admin(self):
        """Test POST /api/admin/resources-config (admin only)"""
        test_links = [
            {"id": "res_1", "label": "Documentation", "url": "https://docs.example.com", "icon": "file"},
            {"id": "res_2", "label": "Help Center", "url": "https://help.example.com", "icon": "globe"}
        ]
        response = requests.post(f"{BASE_URL}/api/admin/resources-config", 
            headers={**self.headers, "Content-Type": "application/json"},
            json={"links": test_links}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("PASS: POST resources-config saves links successfully")
        
        # Verify links were saved
        get_response = requests.get(f"{BASE_URL}/api/admin/resources-config", headers=self.headers)
        saved_links = get_response.json()
        assert len(saved_links) == 2
        assert saved_links[0]["id"] == "res_1"
        print("PASS: Resources config links persisted correctly")
    
    def test_resources_config_requires_auth(self):
        """Test that resources-config GET requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/resources-config")
        assert response.status_code in [401, 403, 422]
        print("PASS: Resources config requires authentication")


class TestAdminPageAccess:
    """Test admin page and stats endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        token = response.json().get("token") or response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_admin_stats_endpoint(self):
        """Test GET /api/admin/stats"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Should return stats object
        assert isinstance(data, dict)
        print("PASS: Admin stats endpoint returns data")
    
    def test_admin_users_endpoint(self):
        """Test GET /api/admin/users"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Admin users endpoint returns {len(data)} users")
    
    def test_admin_config_endpoint(self):
        """Test GET /api/admin/config"""
        response = requests.get(f"{BASE_URL}/api/admin/config", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print("PASS: Admin config endpoint returns data")


class TestPublicConfig:
    """Test public config endpoint"""
    
    def test_public_config(self):
        """Test GET /api/public/config"""
        response = requests.get(f"{BASE_URL}/api/public/config")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print("PASS: Public config endpoint returns data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
