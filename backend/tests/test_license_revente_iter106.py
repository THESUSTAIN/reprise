"""
Test License/Revente Flow - Iteration 106
Tests the complete B2B Chatbot License flow:
- Admin login with role='admin'
- Admin creates licenses (chatbot_lifetime)
- Admin lists licenses
- License validation (public endpoint)
- License activation (creates team + credits)
- User lists their licenses
- Download widget package (ZIP) for lifetime licenses
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLicenseReventeFlow:
    """Complete License/Revente flow tests"""
    
    admin_token = None
    created_license_code = None
    activated_team_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get admin token"""
        if not TestLicenseReventeFlow.admin_token:
            # Login as admin
            res = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "admin@zayado.net",
                "password": "admin123"
            })
            assert res.status_code == 200, f"Admin login failed: {res.text}"
            data = res.json()
            # API returns 'access_token' not 'token'
            TestLicenseReventeFlow.admin_token = data.get('access_token') or data.get('token')
            assert TestLicenseReventeFlow.admin_token, f"No token in response: {data}"
    
    def get_headers(self):
        return {
            'Authorization': f'Bearer {TestLicenseReventeFlow.admin_token}',
            'Content-Type': 'application/json'
        }
    
    # ── Test 1: Admin Login returns role='admin' ──
    def test_01_admin_login_returns_admin_role(self):
        """Login with admin@zayado.net should return role='admin'"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert res.status_code == 200, f"Login failed: {res.text}"
        data = res.json()
        
        # Check token exists (API returns 'access_token')
        assert 'access_token' in data or 'token' in data, f"No token in response: {data}"
        
        # Check user role
        user = data.get('user', {})
        assert user.get('role') == 'admin', f"Expected role='admin', got: {user.get('role')}"
        print(f"✓ Admin login successful, role={user.get('role')}")
    
    # ── Test 2: Admin creates licenses ──
    def test_02_admin_create_licenses(self):
        """Admin can create chatbot_lifetime licenses"""
        res = requests.post(f"{BASE_URL}/api/license/admin/create", 
            headers=self.get_headers(),
            json={
                "plan_type": "chatbot_lifetime",
                "quantity": 1
            }
        )
        assert res.status_code == 200, f"Create license failed: {res.text}"
        data = res.json()
        
        assert data.get('success') == True, f"Expected success=True: {data}"
        assert 'licenses' in data, f"No licenses in response: {data}"
        assert len(data['licenses']) == 1, f"Expected 1 license: {data}"
        
        license = data['licenses'][0]
        assert 'code' in license, f"No code in license: {license}"
        assert license['plan_type'] == 'chatbot_lifetime', f"Wrong plan_type: {license}"
        
        # Save for later tests
        TestLicenseReventeFlow.created_license_code = license['code']
        print(f"✓ Created license: {license['code']}")
    
    # ── Test 3: Admin lists licenses ──
    def test_03_admin_list_licenses(self):
        """Admin can list all licenses"""
        res = requests.get(f"{BASE_URL}/api/license/admin/list", headers=self.get_headers())
        assert res.status_code == 200, f"List licenses failed: {res.text}"
        data = res.json()
        
        assert 'licenses' in data, f"No licenses in response: {data}"
        licenses = data['licenses']
        assert isinstance(licenses, list), f"licenses should be a list: {type(licenses)}"
        
        # Check structure of license items
        if len(licenses) > 0:
            lic = licenses[0]
            assert 'id' in lic, "License missing 'id'"
            assert 'code' in lic, "License missing 'code'"
            assert 'plan_type' in lic, "License missing 'plan_type'"
            assert 'status' in lic, "License missing 'status'"
            assert 'is_lifetime' in lic, "License missing 'is_lifetime'"
            assert 'is_downloadable' in lic, "License missing 'is_downloadable'"
        
        print(f"✓ Listed {len(licenses)} licenses")
    
    # ── Test 4: Validate license code (public endpoint) ──
    def test_04_validate_license_code(self):
        """Validate a license code before activation"""
        code = TestLicenseReventeFlow.created_license_code
        if not code:
            pytest.skip("No license code from previous test")
        
        res = requests.get(f"{BASE_URL}/api/license/validate/{code}")
        assert res.status_code == 200, f"Validate failed: {res.text}"
        data = res.json()
        
        assert data.get('valid') == True, f"Expected valid=True: {data}"
        assert data.get('plan_type') == 'chatbot_lifetime', f"Wrong plan_type: {data}"
        assert data.get('is_lifetime') == True, f"Expected is_lifetime=True: {data}"
        assert 'monthly_credits' in data, f"Missing monthly_credits: {data}"
        assert 'max_chatbots' in data, f"Missing max_chatbots: {data}"
        
        print(f"✓ License {code} is valid, plan={data.get('plan_label')}")
    
    # ── Test 5: Validate invalid code returns valid=False ──
    def test_05_validate_invalid_code(self):
        """Invalid code should return valid=False"""
        res = requests.get(f"{BASE_URL}/api/license/validate/INVALID-CODE-12345")
        assert res.status_code == 200, f"Validate failed: {res.text}"
        data = res.json()
        
        assert data.get('valid') == False, f"Expected valid=False: {data}"
        assert 'reason' in data, f"Missing reason: {data}"
        print(f"✓ Invalid code correctly rejected: {data.get('reason')}")
    
    # ── Test 6: Activate license ──
    def test_06_activate_license(self):
        """Activate a license - creates team + adds credits"""
        code = TestLicenseReventeFlow.created_license_code
        if not code:
            pytest.skip("No license code from previous test")
        
        res = requests.post(f"{BASE_URL}/api/license/activate",
            headers=self.get_headers(),
            json={
                "code": code,
                "team_name": "Test Revente Iter106"
            }
        )
        assert res.status_code == 200, f"Activate failed: {res.text}"
        data = res.json()
        
        assert data.get('success') == True, f"Expected success=True: {data}"
        assert 'team_id' in data, f"Missing team_id: {data}"
        assert 'team_name' in data, f"Missing team_name: {data}"
        assert 'credits_added' in data, f"Missing credits_added: {data}"
        assert data.get('is_lifetime') == True, f"Expected is_lifetime=True: {data}"
        assert data.get('is_downloadable') == True, f"Expected is_downloadable=True: {data}"
        
        TestLicenseReventeFlow.activated_team_id = data['team_id']
        print(f"✓ License activated, team_id={data['team_id']}, credits={data['credits_added']}")
    
    # ── Test 7: Cannot activate same license twice ──
    def test_07_cannot_activate_twice(self):
        """Already used license should fail activation"""
        code = TestLicenseReventeFlow.created_license_code
        if not code:
            pytest.skip("No license code from previous test")
        
        res = requests.post(f"{BASE_URL}/api/license/activate",
            headers=self.get_headers(),
            json={"code": code}
        )
        # Should fail with 400
        assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
        data = res.json()
        assert 'detail' in data, f"Missing error detail: {data}"
        print(f"✓ Double activation correctly rejected: {data.get('detail')}")
    
    # ── Test 8: User lists their licenses ──
    def test_08_user_my_licenses(self):
        """User can list their activated licenses"""
        res = requests.get(f"{BASE_URL}/api/license/my", headers=self.get_headers())
        assert res.status_code == 200, f"My licenses failed: {res.text}"
        data = res.json()
        
        assert 'licenses' in data, f"No licenses in response: {data}"
        licenses = data['licenses']
        assert isinstance(licenses, list), f"licenses should be a list"
        
        # Should have at least the one we just activated
        assert len(licenses) >= 1, f"Expected at least 1 license: {data}"
        
        # Find our activated license
        our_license = next((l for l in licenses if l.get('code') == TestLicenseReventeFlow.created_license_code), None)
        if our_license:
            assert our_license.get('status') == 'used', f"Expected status='used': {our_license}"
            assert our_license.get('is_downloadable') == True, f"Expected is_downloadable=True: {our_license}"
        
        print(f"✓ User has {len(licenses)} activated license(s)")
    
    # ── Test 9: Download widget package (ZIP) ──
    def test_09_download_widget_package(self):
        """Download chatbot widget package for lifetime license"""
        team_id = TestLicenseReventeFlow.activated_team_id
        if not team_id:
            pytest.skip("No team_id from previous test")
        
        res = requests.get(f"{BASE_URL}/api/license/download/{team_id}", 
            headers={'Authorization': f'Bearer {TestLicenseReventeFlow.admin_token}'}
        )
        assert res.status_code == 200, f"Download failed: {res.text}"
        
        # Check content type is ZIP
        content_type = res.headers.get('Content-Type', '')
        assert 'application/zip' in content_type or 'application/octet-stream' in content_type, \
            f"Expected ZIP content type, got: {content_type}"
        
        # Check content disposition header
        content_disp = res.headers.get('Content-Disposition', '')
        assert 'attachment' in content_disp, f"Expected attachment disposition: {content_disp}"
        assert '.zip' in content_disp, f"Expected .zip in filename: {content_disp}"
        
        # Check content is not empty
        assert len(res.content) > 100, f"ZIP content too small: {len(res.content)} bytes"
        
        # Verify it's a valid ZIP (starts with PK)
        assert res.content[:2] == b'PK', "Content is not a valid ZIP file"
        
        print(f"✓ Downloaded widget package: {len(res.content)} bytes")
    
    # ── Test 10: Download fails for non-downloadable license ──
    def test_10_download_fails_for_invalid_team(self):
        """Download should fail for invalid team_id"""
        res = requests.get(f"{BASE_URL}/api/license/download/invalid-team-id-12345", 
            headers={'Authorization': f'Bearer {TestLicenseReventeFlow.admin_token}'}
        )
        # Should fail with 403 or 404
        assert res.status_code in [403, 404], f"Expected 403/404, got {res.status_code}: {res.text}"
        print(f"✓ Download correctly rejected for invalid team")
    
    # ── Test 11: Non-admin cannot create licenses ──
    def test_11_non_admin_cannot_create_licenses(self):
        """Non-admin users should not be able to create licenses"""
        # Create a test user first
        import uuid
        test_email = f"test_user_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register
        res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Test User"
        })
        if res.status_code != 200:
            pytest.skip("Could not create test user")
        
        user_token = res.json().get('access_token') or res.json().get('token')
        if not user_token:
            pytest.skip("No token for test user")
        
        # Try to create license
        res = requests.post(f"{BASE_URL}/api/license/admin/create",
            headers={'Authorization': f'Bearer {user_token}', 'Content-Type': 'application/json'},
            json={"plan_type": "chatbot_lifetime", "quantity": 1}
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        print(f"✓ Non-admin correctly rejected from creating licenses")
    
    # ── Test 12: Admin can revoke license ──
    def test_12_admin_revoke_license(self):
        """Admin can revoke a license"""
        # First create a new license to revoke
        res = requests.post(f"{BASE_URL}/api/license/admin/create",
            headers=self.get_headers(),
            json={"plan_type": "chatbot_starter", "quantity": 1}
        )
        if res.status_code != 200:
            pytest.skip("Could not create license to revoke")
        
        license_code = res.json()['licenses'][0]['code']
        
        # Get license ID from list
        res = requests.get(f"{BASE_URL}/api/license/admin/list", headers=self.get_headers())
        licenses = res.json().get('licenses', [])
        license_to_revoke = next((l for l in licenses if l['code'] == license_code), None)
        
        if not license_to_revoke:
            pytest.skip("Could not find license to revoke")
        
        # Revoke it
        res = requests.post(f"{BASE_URL}/api/license/admin/revoke",
            headers=self.get_headers(),
            json={"license_id": license_to_revoke['id']}
        )
        assert res.status_code == 200, f"Revoke failed: {res.text}"
        data = res.json()
        assert data.get('success') == True, f"Expected success=True: {data}"
        assert data.get('status') == 'revoked', f"Expected status='revoked': {data}"
        
        # Verify it's revoked by trying to validate
        res = requests.get(f"{BASE_URL}/api/license/validate/{license_code}")
        data = res.json()
        assert data.get('valid') == False, f"Revoked license should be invalid: {data}"
        
        print(f"✓ License {license_code} successfully revoked")


class TestTeamListForChatbotAdmin:
    """Test team list endpoint used by ChatbotAdminPage"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if not TestLicenseReventeFlow.admin_token:
            res = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "admin@zayado.net",
                "password": "admin123"
            })
            TestLicenseReventeFlow.admin_token = res.json().get('access_token') or res.json().get('token')
    
    def test_team_list_endpoint(self):
        """GET /api/team/list returns user's teams"""
        res = requests.get(f"{BASE_URL}/api/team/list",
            headers={'Authorization': f'Bearer {TestLicenseReventeFlow.admin_token}'}
        )
        assert res.status_code == 200, f"Team list failed: {res.text}"
        data = res.json()
        
        assert 'teams' in data, f"No teams in response: {data}"
        teams = data['teams']
        assert isinstance(teams, list), f"teams should be a list"
        
        print(f"✓ User has {len(teams)} team(s)")
        
        # Check team structure if any exist
        if len(teams) > 0:
            team = teams[0]
            assert 'id' in team, "Team missing 'id'"
            assert 'name' in team, "Team missing 'name'"
            print(f"  First team: {team.get('name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
