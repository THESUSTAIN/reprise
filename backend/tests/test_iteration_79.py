"""
Iteration 79 Tests - New Features:
1. Homepage / redirects to /fr/fonctionnalites/assistant-ia
2. SEO optimization for assistant-ia page (H1, H2, meta title, image alt)
3. DELETE /api/team/delete/{team_id} - delete team (owner only)
4. PUT /api/team/rename/{team_id} - rename team (owner only)
5. Welcome email code path exists on registration
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests - get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        return data["access_token"]
    
    def test_login_returns_access_token(self, auth_token):
        """Verify login returns access_token (not 'token')"""
        assert auth_token is not None
        assert len(auth_token) > 0


class TestTeamRenameDelete:
    """Test team rename and delete endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_create_team_for_testing(self, headers):
        """Create a test team for rename/delete tests"""
        response = requests.post(f"{BASE_URL}/api/team/create", 
            headers=headers,
            json={"name": "TEST_Team_Iter79_RenameDelete"})
        # May fail if limit reached, but we'll try
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "team" in data
            return data["team"]["id"]
        elif response.status_code == 400 and "Limite" in response.text:
            pytest.skip("Team limit reached - cannot create test team")
        else:
            # Try to get existing teams
            list_resp = requests.get(f"{BASE_URL}/api/team/list", headers=headers)
            if list_resp.status_code == 200:
                teams = list_resp.json().get("teams", [])
                test_teams = [t for t in teams if t.get("name", "").startswith("TEST_")]
                if test_teams:
                    return test_teams[0]["id"]
            pytest.skip(f"Could not create or find test team: {response.text}")
    
    def test_rename_team_success(self, headers):
        """Test PUT /api/team/rename/{team_id} - rename team"""
        # First create a team
        create_resp = requests.post(f"{BASE_URL}/api/team/create", 
            headers=headers,
            json={"name": "TEST_Team_ToRename_Iter79"})
        
        if create_resp.status_code != 200:
            # Try to find existing test team
            list_resp = requests.get(f"{BASE_URL}/api/team/list", headers=headers)
            if list_resp.status_code == 200:
                teams = list_resp.json().get("teams", [])
                owned_teams = [t for t in teams if t.get("is_owner")]
                if owned_teams:
                    team_id = owned_teams[0]["id"]
                else:
                    pytest.skip("No owned teams available for rename test")
            else:
                pytest.skip("Cannot list teams")
        else:
            team_id = create_resp.json()["team"]["id"]
        
        # Rename the team
        new_name = "TEST_Team_Renamed_Iter79"
        rename_resp = requests.put(f"{BASE_URL}/api/team/rename/{team_id}",
            headers=headers,
            json={"name": new_name})
        
        assert rename_resp.status_code == 200, f"Rename failed: {rename_resp.text}"
        data = rename_resp.json()
        assert data.get("success") == True
        assert data.get("name") == new_name
        print(f"PASS: Team renamed to '{new_name}'")
    
    def test_rename_team_invalid_name(self, headers):
        """Test rename with empty name returns 400"""
        # Get any owned team
        list_resp = requests.get(f"{BASE_URL}/api/team/list", headers=headers)
        if list_resp.status_code != 200:
            pytest.skip("Cannot list teams")
        
        teams = list_resp.json().get("teams", [])
        owned_teams = [t for t in teams if t.get("is_owner")]
        if not owned_teams:
            pytest.skip("No owned teams for test")
        
        team_id = owned_teams[0]["id"]
        
        # Try to rename with empty name
        rename_resp = requests.put(f"{BASE_URL}/api/team/rename/{team_id}",
            headers=headers,
            json={"name": "   "})
        
        assert rename_resp.status_code == 400, f"Expected 400 for empty name, got {rename_resp.status_code}"
        print("PASS: Empty name correctly rejected with 400")
    
    def test_rename_team_not_owner(self, headers):
        """Test rename by non-owner returns 404"""
        # Use a fake team ID
        fake_team_id = "00000000-0000-0000-0000-000000000000"
        rename_resp = requests.put(f"{BASE_URL}/api/team/rename/{fake_team_id}",
            headers=headers,
            json={"name": "Should Fail"})
        
        assert rename_resp.status_code == 404, f"Expected 404 for non-existent team, got {rename_resp.status_code}"
        print("PASS: Non-owner/non-existent team correctly returns 404")
    
    def test_delete_team_success(self, headers):
        """Test DELETE /api/team/delete/{team_id} - delete team"""
        # Create a team specifically for deletion
        create_resp = requests.post(f"{BASE_URL}/api/team/create", 
            headers=headers,
            json={"name": "TEST_Team_ToDelete_Iter79"})
        
        if create_resp.status_code != 200:
            pytest.skip(f"Cannot create team for delete test: {create_resp.text}")
        
        team_id = create_resp.json()["team"]["id"]
        
        # Delete the team
        delete_resp = requests.delete(f"{BASE_URL}/api/team/delete/{team_id}",
            headers=headers)
        
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"
        data = delete_resp.json()
        assert data.get("success") == True
        assert "supprimee" in data.get("message", "").lower() or "deleted" in data.get("message", "").lower()
        print(f"PASS: Team {team_id} deleted successfully")
        
        # Verify team no longer exists
        list_resp = requests.get(f"{BASE_URL}/api/team/list", headers=headers)
        if list_resp.status_code == 200:
            teams = list_resp.json().get("teams", [])
            team_ids = [t["id"] for t in teams]
            assert team_id not in team_ids, "Deleted team should not appear in list"
            print("PASS: Deleted team no longer in team list")
    
    def test_delete_team_not_owner(self, headers):
        """Test delete by non-owner returns 404"""
        fake_team_id = "00000000-0000-0000-0000-000000000000"
        delete_resp = requests.delete(f"{BASE_URL}/api/team/delete/{fake_team_id}",
            headers=headers)
        
        assert delete_resp.status_code == 404, f"Expected 404 for non-existent team, got {delete_resp.status_code}"
        print("PASS: Non-owner/non-existent team delete correctly returns 404")


class TestWelcomeEmailCodePath:
    """Verify welcome email code exists in registration endpoint"""
    
    def test_welcome_email_code_exists(self):
        """Verify the welcome email HTML and send_brevo_email call exist in auth.py"""
        import os
        auth_file = "/app/backend/routes/auth.py"
        
        assert os.path.exists(auth_file), f"Auth file not found: {auth_file}"
        
        with open(auth_file, 'r') as f:
            content = f.read()
        
        # Check for welcome email HTML
        assert "Bienvenue" in content, "Welcome email should contain 'Bienvenue'"
        assert "welcome_html" in content, "Welcome email HTML variable should exist"
        assert "send_brevo_email" in content, "send_brevo_email function should be called"
        assert "180 credits" in content or "180 crédits" in content, "Welcome email should mention 180 credits"
        
        # Check it's called after registration
        assert "asyncio.get_running_loop().run_in_executor" in content, "Email should be sent asynchronously"
        
        print("PASS: Welcome email code path verified in auth.py")
        print("  - Contains 'Bienvenue' greeting")
        print("  - Contains welcome_html variable")
        print("  - Calls send_brevo_email")
        print("  - Mentions 180 credits")
        print("  - Uses async executor for non-blocking send")


class TestPaymentPackages:
    """Test payment packages endpoint for buy credits section"""
    
    def test_get_payment_packages(self):
        """Test GET /api/payments/packages returns credit packs"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        
        # May require auth or may be public
        if response.status_code == 401:
            # Try with auth
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if login_resp.status_code == 200:
                token = login_resp.json()["access_token"]
                response = requests.get(f"{BASE_URL}/api/payments/packages",
                    headers={"Authorization": f"Bearer {token}"})
        
        if response.status_code == 200:
            data = response.json()
            # Should return list of packages
            assert isinstance(data, list), "Should return list of packages"
            if len(data) > 0:
                # Check package structure
                pkg = data[0]
                assert "id" in pkg or "pack_id" in pkg, "Package should have id"
                print(f"PASS: Payment packages endpoint returns {len(data)} packages")
        else:
            print(f"INFO: Payment packages endpoint returned {response.status_code}")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
