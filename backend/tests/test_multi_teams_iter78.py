"""
Iteration 78 - Multi-Teams and Credit Allocation Tests
Tests for:
1. GET /api/team/list - returns list of user teams
2. POST /api/team/create - allows creating multiple teams (max 5)
3. GET /api/team/me?team_id=<id> - returns specific team details
4. POST /api/team/credits/allocate - creates CreditLog entry
5. GET /api/team/credits/history - returns credit history
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMultiTeamsAndCredits:
    """Multi-teams and credit allocation tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with admin credentials
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        # Note: response uses 'access_token' not 'token'
        self.token = data.get("access_token")
        assert self.token, f"No access_token in response: {data}"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get initial team list
        list_resp = self.session.get(f"{BASE_URL}/api/team/list")
        if list_resp.status_code == 200:
            self.initial_teams = list_resp.json().get("teams", [])
        else:
            self.initial_teams = []
    
    def test_01_team_list_returns_teams(self):
        """GET /api/team/list returns list of user teams"""
        resp = self.session.get(f"{BASE_URL}/api/team/list")
        assert resp.status_code == 200, f"Team list failed: {resp.text}"
        data = resp.json()
        assert "teams" in data, f"No 'teams' key in response: {data}"
        teams = data["teams"]
        assert isinstance(teams, list), f"Teams should be a list: {teams}"
        print(f"PASS: GET /api/team/list returns {len(teams)} teams")
        
        # Verify team structure
        if teams:
            team = teams[0]
            assert "id" in team, "Team should have 'id'"
            assert "name" in team, "Team should have 'name'"
            assert "team_code" in team, "Team should have 'team_code'"
            assert "shared_credits" in team, "Team should have 'shared_credits'"
            print(f"PASS: Team structure verified: {team['name']} ({team['team_code']})")
    
    def test_02_team_me_returns_team_details(self):
        """GET /api/team/me returns team details"""
        resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert resp.status_code == 200, f"Team me failed: {resp.text}"
        data = resp.json()
        assert "team" in data, f"No 'team' key in response: {data}"
        team = data["team"]
        if team:
            assert "id" in team, "Team should have 'id'"
            assert "name" in team, "Team should have 'name'"
            assert "shared_credits" in team, "Team should have 'shared_credits'"
            self.team_id = team["id"]
            print(f"PASS: GET /api/team/me returns team: {team['name']}")
        else:
            print("INFO: No team found for user")
    
    def test_03_team_me_with_team_id_param(self):
        """GET /api/team/me?team_id=<id> returns specific team details"""
        # First get team list to get a team_id
        list_resp = self.session.get(f"{BASE_URL}/api/team/list")
        assert list_resp.status_code == 200
        teams = list_resp.json().get("teams", [])
        
        if not teams:
            pytest.skip("No teams available to test team_id param")
        
        team_id = teams[0]["id"]
        resp = self.session.get(f"{BASE_URL}/api/team/me?team_id={team_id}")
        assert resp.status_code == 200, f"Team me with team_id failed: {resp.text}"
        data = resp.json()
        assert "team" in data, f"No 'team' key in response: {data}"
        team = data["team"]
        assert team is not None, "Team should not be None"
        assert team["id"] == team_id, f"Team ID mismatch: expected {team_id}, got {team['id']}"
        print(f"PASS: GET /api/team/me?team_id={team_id} returns correct team: {team['name']}")
    
    def test_04_create_second_team(self):
        """POST /api/team/create allows creating a second team when one already exists"""
        import uuid
        test_team_name = f"TEST_Team_{uuid.uuid4().hex[:6]}"
        
        # Count existing teams
        list_resp = self.session.get(f"{BASE_URL}/api/team/list")
        initial_count = len(list_resp.json().get("teams", []))
        
        # Create new team
        resp = self.session.post(f"{BASE_URL}/api/team/create", json={
            "name": test_team_name
        })
        
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") == True, f"Create team should succeed: {data}"
            assert "team" in data, f"Response should contain 'team': {data}"
            new_team = data["team"]
            assert new_team["name"] == test_team_name
            print(f"PASS: Created new team: {test_team_name}")
            
            # Verify team count increased
            list_resp2 = self.session.get(f"{BASE_URL}/api/team/list")
            new_count = len(list_resp2.json().get("teams", []))
            assert new_count == initial_count + 1, f"Team count should increase: {initial_count} -> {new_count}"
            print(f"PASS: Team count increased from {initial_count} to {new_count}")
            
            # Store for cleanup
            self.created_team_id = new_team["id"]
        elif resp.status_code == 400 and "5 equipes" in resp.text:
            print("INFO: Max 5 teams limit reached - this is expected behavior")
            pytest.skip("Max 5 teams limit reached")
        else:
            pytest.fail(f"Unexpected response: {resp.status_code} - {resp.text}")
    
    def test_05_credit_history_endpoint(self):
        """GET /api/team/credits/history returns credit history"""
        resp = self.session.get(f"{BASE_URL}/api/team/credits/history")
        assert resp.status_code == 200, f"Credit history failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Credit history should be a list: {data}"
        print(f"PASS: GET /api/team/credits/history returns {len(data)} entries")
        
        # Verify structure if entries exist
        if data:
            entry = data[0]
            assert "id" in entry, "Entry should have 'id'"
            assert "amount" in entry, "Entry should have 'amount'"
            assert "type" in entry, "Entry should have 'type'"
            assert "description" in entry, "Entry should have 'description'"
            print(f"PASS: Credit log structure verified: {entry['description']}")
    
    def test_06_credit_allocation_creates_log(self):
        """POST /api/team/credits/allocate creates CreditLog entry"""
        # First get team and members
        team_resp = self.session.get(f"{BASE_URL}/api/team/me")
        assert team_resp.status_code == 200
        team_data = team_resp.json()
        team = team_data.get("team")
        members = team_data.get("members", [])
        
        if not team:
            pytest.skip("No team available")
        
        # Find a member to allocate credits to (not owner)
        target_member = None
        for m in members:
            if m.get("role") != "owner" and m.get("status") == "active":
                target_member = m
                break
        
        if not target_member:
            print("INFO: No non-owner active member found to test allocation")
            pytest.skip("No non-owner active member available")
        
        # Check if team has credits
        if (team.get("shared_credits") or 0) < 10:
            print(f"INFO: Team has insufficient credits ({team.get('shared_credits')})")
            pytest.skip("Insufficient team credits for allocation test")
        
        # Get initial credit history count
        history_resp = self.session.get(f"{BASE_URL}/api/team/credits/history")
        initial_history = history_resp.json() if history_resp.status_code == 200 else []
        initial_count = len(initial_history)
        
        # Allocate credits
        alloc_resp = self.session.post(f"{BASE_URL}/api/team/credits/allocate", json={
            "member_id": target_member["id"],
            "credits": 5
        })
        
        if alloc_resp.status_code == 200:
            data = alloc_resp.json()
            assert data.get("success") == True, f"Allocation should succeed: {data}"
            print(f"PASS: Allocated 5 credits to member {target_member.get('email')}")
            
            # Verify CreditLog was created
            history_resp2 = self.session.get(f"{BASE_URL}/api/team/credits/history")
            new_history = history_resp2.json() if history_resp2.status_code == 200 else []
            new_count = len(new_history)
            
            assert new_count > initial_count, f"Credit history should have new entry: {initial_count} -> {new_count}"
            
            # Check latest entry
            if new_history:
                latest = new_history[0]  # Most recent first
                assert latest["amount"] == -5, f"Amount should be -5: {latest['amount']}"
                assert "allocate" in latest.get("type", "").lower() or "allocation" in latest.get("description", "").lower(), \
                    f"Entry should be allocation type: {latest}"
                print(f"PASS: CreditLog entry created: {latest['description']}")
        elif alloc_resp.status_code == 400:
            print(f"INFO: Allocation failed (expected if insufficient credits): {alloc_resp.text}")
        else:
            pytest.fail(f"Unexpected allocation response: {alloc_resp.status_code} - {alloc_resp.text}")


class TestPaymentPacks:
    """Test payment/credit pack endpoints"""
    
    def test_get_credit_packs(self):
        """GET /api/payments/packages returns available credit packs"""
        # Note: endpoint is /packages not /packs
        resp = requests.get(f"{BASE_URL}/api/payments/packages")
        assert resp.status_code == 200, f"Get packages failed: {resp.text}"
        data = resp.json()
        # Response may be a dict with 'packages' key or a list
        packs = data.get("packages", data) if isinstance(data, dict) else data
        assert isinstance(packs, list), f"Packs should be a list: {packs}"
        
        # Verify pack structure
        if packs:
            for pack in packs:
                assert "id" in pack or "name" in pack, f"Pack should have 'id' or 'name': {pack}"
                assert "credits" in pack or "amount" in pack, f"Pack should have 'credits' or 'amount': {pack}"
            print(f"PASS: GET /api/payments/packages returns {len(packs)} packs")
            for p in packs:
                credits = p.get('credits', p.get('amount', 'N/A'))
                price = p.get('price', p.get('price_eur', 'N/A'))
                print(f"  - {p.get('id', p.get('name'))}: {credits} credits for {price}€")
        else:
            print("INFO: No credit packs returned (may be empty)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
