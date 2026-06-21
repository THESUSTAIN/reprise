"""
Test License APIs - Iteration 98
Tests for ZAYADO Chatbot B2B License System:
- Admin: Create, List, Revoke licenses
- User: Activate, Validate, My licenses
- Download package for lifetime licenses
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


class TestLicenseAPIs:
    """License API tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    # ── Admin: Create License ──────────────────────────────────────
    
    def test_admin_create_license_chatbot_lifetime(self, headers):
        """POST /api/license/admin/create with plan_type=chatbot_lifetime"""
        response = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_lifetime", "quantity": 1}
        )
        assert response.status_code == 200, f"Create license failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("count") == 1
        assert len(data.get("licenses", [])) == 1
        
        license = data["licenses"][0]
        assert license["plan_type"] == "chatbot_lifetime"
        assert license["code"].startswith("ZAYA-CHA-")
        print(f"Created license: {license['code']}")
    
    def test_admin_create_license_chatbot_starter(self, headers):
        """POST /api/license/admin/create with plan_type=chatbot_starter"""
        response = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_starter", "quantity": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data["licenses"][0]["plan_type"] == "chatbot_starter"
    
    def test_admin_create_license_chatbot_pro(self, headers):
        """POST /api/license/admin/create with plan_type=chatbot_pro"""
        response = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_pro", "quantity": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data["licenses"][0]["plan_type"] == "chatbot_pro"
    
    def test_admin_create_license_pilote_lifetime(self, headers):
        """POST /api/license/admin/create with plan_type=pilote_chatbot_lifetime"""
        response = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "pilote_chatbot_lifetime", "quantity": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data["licenses"][0]["plan_type"] == "pilote_chatbot_lifetime"
    
    def test_admin_create_license_invalid_plan(self, headers):
        """POST /api/license/admin/create with invalid plan_type returns 400"""
        response = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "invalid_plan", "quantity": 1}
        )
        assert response.status_code == 400
    
    def test_admin_create_multiple_licenses(self, headers):
        """POST /api/license/admin/create with quantity > 1"""
        response = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_lifetime", "quantity": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("count") == 3
        assert len(data.get("licenses", [])) == 3
    
    # ── Admin: List Licenses ───────────────────────────────────────
    
    def test_admin_list_licenses(self, headers):
        """GET /api/license/admin/list returns all licenses"""
        response = requests.get(f"{BASE_URL}/api/license/admin/list", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "licenses" in data
        assert isinstance(data["licenses"], list)
        
        if len(data["licenses"]) > 0:
            lic = data["licenses"][0]
            # Verify license structure
            assert "id" in lic
            assert "code" in lic
            assert "plan_type" in lic
            assert "plan_label" in lic
            assert "status" in lic
            assert "max_chatbots" in lic
            assert "monthly_credits" in lic
            assert "is_lifetime" in lic
            assert "is_downloadable" in lic
            print(f"Found {len(data['licenses'])} licenses")
    
    def test_admin_list_licenses_unauthorized(self):
        """GET /api/license/admin/list without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/license/admin/list")
        assert response.status_code == 401
    
    # ── Validate License Code ──────────────────────────────────────
    
    def test_validate_license_active(self, headers):
        """GET /api/license/validate/{code} returns valid=true for active codes"""
        # First create a license
        create_resp = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_lifetime", "quantity": 1}
        )
        assert create_resp.status_code == 200
        code = create_resp.json()["licenses"][0]["code"]
        
        # Validate it (no auth required)
        response = requests.get(f"{BASE_URL}/api/license/validate/{code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == True
        assert data.get("plan_type") == "chatbot_lifetime"
        assert "plan_label" in data
        assert data.get("is_lifetime") == True
        print(f"Validated license: {code}")
    
    def test_validate_license_invalid_code(self):
        """GET /api/license/validate/{code} returns valid=false for invalid codes"""
        response = requests.get(f"{BASE_URL}/api/license/validate/INVALID-CODE-123")
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == False
        assert "reason" in data
    
    # ── Activate License ───────────────────────────────────────────
    
    def test_activate_license_success(self, headers):
        """POST /api/license/activate with valid code activates it and creates team"""
        # Create a new license
        create_resp = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_lifetime", "quantity": 1}
        )
        assert create_resp.status_code == 200
        code = create_resp.json()["licenses"][0]["code"]
        
        # Activate it
        response = requests.post(f"{BASE_URL}/api/license/activate", 
            headers=headers,
            json={"code": code, "team_name": "TEST_Chatbot_Team"}
        )
        assert response.status_code == 200, f"Activate failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "team_id" in data
        assert data.get("team_name") == "TEST_Chatbot_Team"
        assert data.get("plan_type") == "chatbot_lifetime"
        assert data.get("is_lifetime") == True
        assert data.get("is_downloadable") == True
        assert data.get("credits_added") > 0
        print(f"Activated license {code}, team_id: {data['team_id']}")
        return data["team_id"]
    
    def test_activate_license_already_used(self, headers):
        """POST /api/license/activate with used code returns 400"""
        # Create and activate a license
        create_resp = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_starter", "quantity": 1}
        )
        code = create_resp.json()["licenses"][0]["code"]
        
        # First activation
        requests.post(f"{BASE_URL}/api/license/activate", 
            headers=headers,
            json={"code": code}
        )
        
        # Second activation should fail
        response = requests.post(f"{BASE_URL}/api/license/activate", 
            headers=headers,
            json={"code": code}
        )
        assert response.status_code == 400
        assert "deja ete activee" in response.json().get("detail", "").lower() or "already" in response.json().get("detail", "").lower()
    
    def test_activate_license_invalid_code(self, headers):
        """POST /api/license/activate with invalid code returns 404"""
        response = requests.post(f"{BASE_URL}/api/license/activate", 
            headers=headers,
            json={"code": "INVALID-CODE-XYZ"}
        )
        assert response.status_code == 404
    
    def test_activate_license_unauthorized(self):
        """POST /api/license/activate without auth returns 401"""
        response = requests.post(f"{BASE_URL}/api/license/activate", 
            json={"code": "ZAYA-CHA-12345678"}
        )
        assert response.status_code == 401
    
    # ── Admin: Revoke License ──────────────────────────────────────
    
    def test_admin_revoke_license(self, headers):
        """POST /api/license/admin/revoke marks license as revoked"""
        # Create a license
        create_resp = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_starter", "quantity": 1}
        )
        license_id = None
        code = create_resp.json()["licenses"][0]["code"]
        
        # Get license ID from list
        list_resp = requests.get(f"{BASE_URL}/api/license/admin/list", headers=headers)
        for lic in list_resp.json()["licenses"]:
            if lic["code"] == code:
                license_id = lic["id"]
                break
        
        assert license_id is not None
        
        # Revoke it
        response = requests.post(f"{BASE_URL}/api/license/admin/revoke", 
            headers=headers,
            json={"license_id": license_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("status") == "revoked"
        
        # Verify it's revoked
        validate_resp = requests.get(f"{BASE_URL}/api/license/validate/{code}")
        assert validate_resp.json().get("valid") == False
        print(f"Revoked license: {code}")
    
    def test_admin_revoke_license_not_found(self, headers):
        """POST /api/license/admin/revoke with invalid ID returns 404"""
        response = requests.post(f"{BASE_URL}/api/license/admin/revoke", 
            headers=headers,
            json={"license_id": "invalid-uuid-12345"}
        )
        assert response.status_code == 404
    
    # ── User: My Licenses ──────────────────────────────────────────
    
    def test_my_licenses(self, headers):
        """GET /api/license/my returns licenses activated by user"""
        response = requests.get(f"{BASE_URL}/api/license/my", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "licenses" in data
        assert isinstance(data["licenses"], list)
        
        if len(data["licenses"]) > 0:
            lic = data["licenses"][0]
            assert "id" in lic
            assert "code" in lic
            assert "plan_type" in lic
            assert "team_id" in lic
            print(f"User has {len(data['licenses'])} activated licenses")
    
    def test_my_licenses_unauthorized(self):
        """GET /api/license/my without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/license/my")
        assert response.status_code == 401
    
    # ── Download Package (Lifetime only) ───────────────────────────
    
    def test_download_package_lifetime(self, headers):
        """GET /api/license/download/{team_id} returns ZIP for lifetime license"""
        # Create and activate a lifetime license
        create_resp = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=headers,
            json={"plan_type": "chatbot_lifetime", "quantity": 1}
        )
        code = create_resp.json()["licenses"][0]["code"]
        
        activate_resp = requests.post(f"{BASE_URL}/api/license/activate", 
            headers=headers,
            json={"code": code, "team_name": "TEST_Download_Team"}
        )
        team_id = activate_resp.json()["team_id"]
        
        # Download package
        response = requests.get(f"{BASE_URL}/api/license/download/{team_id}", 
            headers={"Authorization": headers["Authorization"]}
        )
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/zip"
        assert "attachment" in response.headers.get("content-disposition", "")
        assert len(response.content) > 100  # ZIP should have content
        print(f"Downloaded package for team {team_id}, size: {len(response.content)} bytes")
    
    def test_download_package_unauthorized(self, headers):
        """GET /api/license/download/{team_id} without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/license/download/some-team-id")
        assert response.status_code == 401


class TestTeamConfigForChatbot:
    """Test team config endpoints used by chatbot admin"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_team_list(self, headers):
        """GET /api/team/list returns user's teams"""
        response = requests.get(f"{BASE_URL}/api/team/list", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        print(f"User has {len(data['teams'])} teams")
    
    def test_team_config_update(self, headers):
        """PUT /api/team/config updates chatbot configuration"""
        # Get first team
        list_resp = requests.get(f"{BASE_URL}/api/team/list", headers=headers)
        teams = list_resp.json().get("teams", [])
        
        if len(teams) == 0:
            pytest.skip("No teams available for testing")
        
        team_id = teams[0]["id"]
        
        # Update config
        response = requests.put(f"{BASE_URL}/api/team/config?team_id={team_id}", 
            headers=headers,
            json={
                "bot_name": "TEST_Bot",
                "bot_tone": "friendly",
                "welcome_message": "Hello! How can I help?",
                "primary_color": "#FF5733",
                "accent_color": "#33FF57",
                "logo_url": "https://example.com/logo.png",
                "footer_text": "Powered by TEST"
            }
        )
        assert response.status_code == 200
        
        # Verify update
        me_resp = requests.get(f"{BASE_URL}/api/team/me?team_id={team_id}", headers=headers)
        assert me_resp.status_code == 200
        team_data = me_resp.json().get("team", me_resp.json())
        assert team_data.get("bot_name") == "TEST_Bot"
        print(f"Updated team config for {team_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
