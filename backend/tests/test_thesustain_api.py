"""
Test TheSustain API endpoints - Iteration 141
Tests POST /api/payments/thesustain/link and GET /api/payments/thesustain/status
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTheSustainAPI:
    """TheSustain link and status endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            # Use access_token field (not token)
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.token = token
            else:
                pytest.skip("No token in login response")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_thesustain_link_member(self):
        """Test POST /api/payments/thesustain/link with type=member"""
        response = self.session.post(f"{BASE_URL}/api/payments/thesustain/link", json={
            "type": "member"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("type") == "member"
        assert data.get("discount") == 30
        print(f"✓ TheSustain link (member) - 30% discount applied")
    
    def test_thesustain_link_association(self):
        """Test POST /api/payments/thesustain/link with type=association"""
        response = self.session.post(f"{BASE_URL}/api/payments/thesustain/link", json={
            "type": "association"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("type") == "association"
        assert data.get("discount") == 100
        print(f"✓ TheSustain link (association) - 100% discount (free Pro)")
    
    def test_thesustain_status(self):
        """Test GET /api/payments/thesustain/status"""
        response = self.session.get(f"{BASE_URL}/api/payments/thesustain/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have is_member, type, discount_percent, plan fields
        assert "is_member" in data
        assert "type" in data
        assert "discount_percent" in data
        assert "plan" in data
        print(f"✓ TheSustain status - is_member: {data.get('is_member')}, type: {data.get('type')}, discount: {data.get('discount_percent')}%")


class TestAuthEndpoint:
    """Basic auth endpoint test"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        data = response.json()
        
        # Check for access_token (not token)
        assert "access_token" in data or "token" in data, "No token in response"
        print(f"✓ Login successful - token received")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
