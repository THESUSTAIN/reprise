"""
Test suite for Serenity Finance features - Iteration 121
Tests:
- GET /api/finance/serenity - Score de Sérénité Financière (0-100)
- POST /api/finance/comfort-goal - Objectif CA confortable
- POST /api/finance/tresorerie - Trésorerie déclarée
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSerenityFinanceFeatures:
    """Tests for the new well-being focused financial features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth token"""
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
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    # ═══════════════════════════════════════════════════════════
    # Health & Auth Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Health endpoint OK")
    
    def test_admin_login(self):
        """Test admin login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        print("✓ Admin login OK")
    
    # ═══════════════════════════════════════════════════════════
    # GET /api/finance/serenity Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_serenity_endpoint_returns_200(self):
        """Test serenity endpoint returns 200"""
        response = self.session.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code == 200, f"Serenity endpoint failed: {response.status_code} - {response.text}"
        print("✓ Serenity endpoint returns 200")
    
    def test_serenity_response_has_score(self):
        """Test serenity response contains score (0-100)"""
        response = self.session.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code == 200
        data = response.json()
        assert "score" in data, "Missing 'score' in response"
        assert isinstance(data["score"], (int, float)), "Score should be numeric"
        assert 0 <= data["score"] <= 100, f"Score {data['score']} not in range 0-100"
        print(f"✓ Serenity score: {data['score']}/100")
    
    def test_serenity_response_has_level(self):
        """Test serenity response contains level (serenite/vigilance/tension/alerte)"""
        response = self.session.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code == 200
        data = response.json()
        assert "level" in data, "Missing 'level' in response"
        valid_levels = ["serenite", "vigilance", "tension", "alerte"]
        assert data["level"] in valid_levels, f"Invalid level: {data['level']}"
        print(f"✓ Serenity level: {data['level']}")
    
    def test_serenity_response_has_pillars(self):
        """Test serenity response contains 4 pillars"""
        response = self.session.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code == 200
        data = response.json()
        assert "pillars" in data, "Missing 'pillars' in response"
        pillars = data["pillars"]
        expected_pillars = ["resultat_net", "regularite", "couverture", "diversification"]
        for pillar in expected_pillars:
            assert pillar in pillars, f"Missing pillar: {pillar}"
            assert "score" in pillars[pillar], f"Missing score in pillar {pillar}"
            assert "max" in pillars[pillar], f"Missing max in pillar {pillar}"
            assert pillars[pillar]["max"] == 25, f"Pillar {pillar} max should be 25"
        print(f"✓ All 4 pillars present: {list(pillars.keys())}")
    
    def test_serenity_response_has_comfort(self):
        """Test serenity response contains comfort goal data"""
        response = self.session.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code == 200
        data = response.json()
        assert "comfort" in data, "Missing 'comfort' in response"
        comfort = data["comfort"]
        assert "target" in comfort, "Missing 'target' in comfort"
        assert "current" in comfort, "Missing 'current' in comfort"
        assert "pct" in comfort, "Missing 'pct' in comfort"
        print(f"✓ Comfort data: target={comfort['target']}, current={comfort['current']}, pct={comfort['pct']}%")
    
    def test_serenity_response_has_tresorerie(self):
        """Test serenity response contains tresorerie"""
        response = self.session.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code == 200
        data = response.json()
        assert "tresorerie" in data, "Missing 'tresorerie' in response"
        print(f"✓ Tresorerie: {data['tresorerie']} EUR")
    
    def test_serenity_without_auth_fails(self):
        """Test serenity endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Serenity endpoint requires auth")
    
    # ═══════════════════════════════════════════════════════════
    # POST /api/finance/comfort-goal Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_comfort_goal_endpoint_saves_target(self):
        """Test comfort-goal endpoint saves the comfort target"""
        test_amount = 5000.0
        response = self.session.post(f"{BASE_URL}/api/finance/comfort-goal", json={
            "category": "objectif_confort",
            "amount": test_amount
        })
        assert response.status_code == 200, f"Comfort-goal failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("status") == "ok", "Expected status 'ok'"
        assert data.get("target") == test_amount, f"Expected target {test_amount}, got {data.get('target')}"
        print(f"✓ Comfort goal saved: {test_amount} EUR")
    
    def test_comfort_goal_persists_in_serenity(self):
        """Test comfort goal is reflected in serenity endpoint"""
        # Set comfort goal
        test_amount = 6000.0
        self.session.post(f"{BASE_URL}/api/finance/comfort-goal", json={
            "category": "objectif_confort",
            "amount": test_amount
        })
        # Verify in serenity
        response = self.session.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code == 200
        data = response.json()
        assert data["comfort"]["target"] == test_amount, f"Comfort target not persisted: {data['comfort']['target']}"
        print(f"✓ Comfort goal persisted in serenity: {test_amount} EUR")
    
    def test_comfort_goal_without_auth_fails(self):
        """Test comfort-goal endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/finance/comfort-goal", json={
            "category": "objectif_confort",
            "amount": 5000
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Comfort-goal endpoint requires auth")
    
    # ═══════════════════════════════════════════════════════════
    # POST /api/finance/tresorerie Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_tresorerie_endpoint_saves_value(self):
        """Test tresorerie endpoint saves the declared treasury"""
        test_amount = 15000.0
        response = self.session.post(f"{BASE_URL}/api/finance/tresorerie", json={
            "category": "tresorerie",
            "amount": test_amount
        })
        assert response.status_code == 200, f"Tresorerie failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("status") == "ok", "Expected status 'ok'"
        assert data.get("tresorerie") == test_amount, f"Expected tresorerie {test_amount}, got {data.get('tresorerie')}"
        print(f"✓ Tresorerie saved: {test_amount} EUR")
    
    def test_tresorerie_persists_in_serenity(self):
        """Test tresorerie is reflected in serenity endpoint"""
        # Set tresorerie
        test_amount = 20000.0
        self.session.post(f"{BASE_URL}/api/finance/tresorerie", json={
            "category": "tresorerie",
            "amount": test_amount
        })
        # Verify in serenity
        response = self.session.get(f"{BASE_URL}/api/finance/serenity")
        assert response.status_code == 200
        data = response.json()
        assert data["tresorerie"] == test_amount, f"Tresorerie not persisted: {data['tresorerie']}"
        print(f"✓ Tresorerie persisted in serenity: {test_amount} EUR")
    
    def test_tresorerie_without_auth_fails(self):
        """Test tresorerie endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/finance/tresorerie", json={
            "category": "tresorerie",
            "amount": 10000
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Tresorerie endpoint requires auth")
    
    # ═══════════════════════════════════════════════════════════
    # Existing Finance Endpoints Still Work
    # ═══════════════════════════════════════════════════════════
    
    def test_finance_overview_still_works(self):
        """Test existing finance overview endpoint still works"""
        response = self.session.get(f"{BASE_URL}/api/finance/overview?period=mois")
        assert response.status_code == 200, f"Overview failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "revenus" in data, "Missing 'revenus' in overview"
        assert "depenses" in data, "Missing 'depenses' in overview"
        assert "net" in data, "Missing 'net' in overview"
        assert "seuil_equilibre" in data, "Missing 'seuil_equilibre' in overview"
        print(f"✓ Finance overview OK: CA={data['revenus']}, Dépenses={data['depenses']}, Net={data['net']}")
    
    def test_finance_entry_still_works(self):
        """Test adding a finance entry still works"""
        response = self.session.post(f"{BASE_URL}/api/finance/entry", json={
            "type": "revenu",
            "label": "TEST_iter121_revenu",
            "amount": 100.0,
            "category": "service"
        })
        assert response.status_code == 200, f"Entry creation failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("status") == "ok", "Expected status 'ok'"
        assert "entry" in data, "Missing 'entry' in response"
        print(f"✓ Finance entry creation OK: {data['entry']['label']}")
        
        # Cleanup - delete the test entry
        entry_id = data["entry"]["id"]
        delete_response = self.session.delete(f"{BASE_URL}/api/finance/entry/{entry_id}")
        assert delete_response.status_code == 200, f"Entry deletion failed: {delete_response.status_code}"
        print(f"✓ Test entry cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
