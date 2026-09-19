"""
Iteration 45 - Backend API Tests
Testing: Finance APIs, Activite APIs, Onboarding APIs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data, "No token in response"
        print(f"Login successful, token received")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    data = response.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        pytest.skip("No token in login response")
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestFinanceOverview:
    """Tests for GET /api/finance/overview"""
    
    def test_finance_overview_default_period(self, auth_headers):
        """Test finance overview with default period (mois)"""
        response = requests.get(f"{BASE_URL}/api/finance/overview", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "period" in data
        assert "revenus" in data
        assert "depenses" in data
        assert "net" in data
        assert "seuil_equilibre" in data
        assert "taux_marge" in data
        assert "nb_transactions" in data
        assert "weekly" in data
        assert "monthly" in data
        assert "recent_entries" in data
        
        print(f"Finance overview: revenus={data['revenus']}, depenses={data['depenses']}, net={data['net']}")
    
    def test_finance_overview_semaine(self, auth_headers):
        """Test finance overview with semaine period"""
        response = requests.get(f"{BASE_URL}/api/finance/overview?period=semaine", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "semaine"
        print(f"Finance overview (semaine): {data['nb_transactions']} transactions")
    
    def test_finance_overview_trimestre(self, auth_headers):
        """Test finance overview with trimestre period"""
        response = requests.get(f"{BASE_URL}/api/finance/overview?period=trimestre", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "trimestre"
        print(f"Finance overview (trimestre): {data['nb_transactions']} transactions")
    
    def test_finance_overview_annee(self, auth_headers):
        """Test finance overview with annee period"""
        response = requests.get(f"{BASE_URL}/api/finance/overview?period=annee", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "annee"
        print(f"Finance overview (annee): {data['nb_transactions']} transactions")


class TestFinanceEntry:
    """Tests for POST/DELETE /api/finance/entry"""
    
    def test_create_finance_entry_revenu(self, auth_headers):
        """Test creating a revenue entry"""
        payload = {
            "type": "revenu",
            "label": "TEST_Facture client",
            "amount": 1500.00,
            "category": "service",
            "recurring": False
        }
        response = requests.post(f"{BASE_URL}/api/finance/entry", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["status"] == "ok"
        assert "entry" in data
        entry = data["entry"]
        assert entry["type"] == "revenu"
        assert entry["label"] == "TEST_Facture client"
        assert entry["amount"] == 1500.00
        assert entry["category"] == "service"
        assert "id" in entry
        
        print(f"Created revenue entry: {entry['id']}")
        return entry["id"]
    
    def test_create_finance_entry_depense(self, auth_headers):
        """Test creating an expense entry"""
        payload = {
            "type": "depense",
            "label": "TEST_Achat materiel",
            "amount": 250.00,
            "category": "outils",
            "recurring": True
        }
        response = requests.post(f"{BASE_URL}/api/finance/entry", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["status"] == "ok"
        entry = data["entry"]
        assert entry["type"] == "depense"
        assert entry["recurring"] == True
        
        print(f"Created expense entry: {entry['id']}")
        return entry["id"]
    
    def test_delete_finance_entry(self, auth_headers):
        """Test deleting a finance entry"""
        # First create an entry
        payload = {
            "type": "revenu",
            "label": "TEST_To be deleted",
            "amount": 100.00,
            "category": "autre"
        }
        create_response = requests.post(f"{BASE_URL}/api/finance/entry", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        entry_id = create_response.json()["entry"]["id"]
        
        # Delete the entry
        delete_response = requests.delete(f"{BASE_URL}/api/finance/entry/{entry_id}", headers=auth_headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        data = delete_response.json()
        assert data["status"] == "ok"
        
        print(f"Deleted entry: {entry_id}")


class TestFinanceForecast:
    """Tests for GET /api/finance/forecast"""
    
    def test_finance_forecast(self, auth_headers):
        """Test finance forecast endpoint"""
        response = requests.get(f"{BASE_URL}/api/finance/forecast", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "avg_monthly_revenue" in data
        assert "avg_monthly_expense" in data
        assert "forecast" in data
        assert "health" in data
        
        # Verify forecast array
        assert isinstance(data["forecast"], list)
        if len(data["forecast"]) > 0:
            forecast_item = data["forecast"][0]
            assert "month" in forecast_item
            assert "revenus_prevu" in forecast_item
            assert "depenses_prevu" in forecast_item
            assert "net_prevu" in forecast_item
        
        # Verify health is one of expected values
        assert data["health"] in ["bon", "attention", "critique"]
        
        print(f"Forecast health: {data['health']}, avg_revenue: {data['avg_monthly_revenue']}")


class TestActiviteSummary:
    """Tests for GET /api/activite/summary"""
    
    def test_activite_summary(self, auth_headers):
        """Test activite summary endpoint returns 6 sections"""
        response = requests.get(f"{BASE_URL}/api/activite/summary", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify all 6 sections exist
        assert "ou_tu_en_es" in data, "Missing section: ou_tu_en_es"
        assert "ce_qui_te_bloque" in data, "Missing section: ce_qui_te_bloque"
        assert "ton_action_prioritaire" in data, "Missing section: ton_action_prioritaire"
        assert "fais_le_maintenant" in data, "Missing section: fais_le_maintenant"
        assert "suivi" in data, "Missing section: suivi"
        assert "ia_contextuelle" in data, "Missing section: ia_contextuelle"
        
        # Verify ou_tu_en_es structure
        ou_tu_en_es = data["ou_tu_en_es"]
        assert "phase" in ou_tu_en_es
        assert "resume" in ou_tu_en_es
        
        # Verify fais_le_maintenant structure
        fais_le = data["fais_le_maintenant"]
        assert "checklist" in fais_le
        assert "progress" in fais_le
        assert "total" in fais_le
        assert "done" in fais_le
        
        # Verify suivi structure
        suivi = data["suivi"]
        assert "entries" in suivi
        assert "current_day" in suivi
        
        print(f"Activite summary: phase={ou_tu_en_es['phase']}, progress={fais_le['progress']}%")


class TestActiviteBlocker:
    """Tests for POST /api/activite/blocker"""
    
    def test_save_blocker(self, auth_headers):
        """Test saving a blocker"""
        payload = {
            "tension": "TEST_Manque de temps pour prospecter",
            "detail": "Trop de taches administratives"
        }
        response = requests.post(f"{BASE_URL}/api/activite/blocker", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        
        # Verify blocker was saved by checking summary
        summary_response = requests.get(f"{BASE_URL}/api/activite/summary", headers=auth_headers)
        summary = summary_response.json()
        assert summary["ce_qui_te_bloque"] is not None
        assert summary["ce_qui_te_bloque"]["tension"] == "TEST_Manque de temps pour prospecter"
        
        print(f"Blocker saved successfully")


class TestActivitePriority:
    """Tests for POST /api/activite/priority"""
    
    def test_save_priority(self, auth_headers):
        """Test saving a priority"""
        payload = {
            "title": "TEST_Contacter 5 prospects",
            "why": "Augmenter le pipeline commercial"
        }
        response = requests.post(f"{BASE_URL}/api/activite/priority", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        
        # Verify priority was saved
        summary_response = requests.get(f"{BASE_URL}/api/activite/summary", headers=auth_headers)
        summary = summary_response.json()
        assert summary["ton_action_prioritaire"] is not None
        assert summary["ton_action_prioritaire"]["title"] == "TEST_Contacter 5 prospects"
        
        print(f"Priority saved successfully")


class TestActiviteChecklist:
    """Tests for POST /api/activite/checklist and toggle"""
    
    def test_save_checklist(self, auth_headers):
        """Test saving checklist items"""
        items = [
            {"text": "TEST_Etape 1: Preparer le pitch", "done": False},
            {"text": "TEST_Etape 2: Envoyer les emails", "done": False},
            {"text": "TEST_Etape 3: Faire le suivi", "done": True}
        ]
        response = requests.post(f"{BASE_URL}/api/activite/checklist", json=items, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        assert "checklist" in data
        assert len(data["checklist"]) == 3
        
        print(f"Checklist saved: {len(data['checklist'])} items")
        return data["checklist"]
    
    def test_toggle_checklist_item(self, auth_headers):
        """Test toggling a checklist item"""
        # First save a checklist
        items = [{"text": "TEST_Toggle item", "done": False}]
        save_response = requests.post(f"{BASE_URL}/api/activite/checklist", json=items, headers=auth_headers)
        assert save_response.status_code == 200
        checklist = save_response.json()["checklist"]
        item_id = checklist[0]["id"]
        
        # Toggle the item
        toggle_response = requests.post(f"{BASE_URL}/api/activite/checklist/toggle/{item_id}", headers=auth_headers)
        assert toggle_response.status_code == 200, f"Toggle failed: {toggle_response.text}"
        data = toggle_response.json()
        assert data["status"] == "ok"
        
        # Verify item was toggled
        toggled_item = next((i for i in data["checklist"] if i["id"] == item_id), None)
        assert toggled_item is not None
        assert toggled_item["done"] == True
        
        print(f"Checklist item toggled: {item_id}")


class TestActiviteSuivi:
    """Tests for POST /api/activite/suivi"""
    
    def test_add_suivi_entry(self, auth_headers):
        """Test adding a suivi timeline entry"""
        payload = {
            "day": 1,
            "note": "TEST_Premier jour: objectifs definis",
            "status": "en_cours"
        }
        response = requests.post(f"{BASE_URL}/api/activite/suivi", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        
        # Verify suivi was saved
        summary_response = requests.get(f"{BASE_URL}/api/activite/summary", headers=auth_headers)
        summary = summary_response.json()
        suivi_entries = summary["suivi"]["entries"]
        assert len(suivi_entries) > 0
        
        # Find our entry
        test_entry = next((e for e in suivi_entries if "TEST_Premier jour" in e.get("note", "")), None)
        assert test_entry is not None
        assert test_entry["day"] == 1
        
        print(f"Suivi entry added for day {payload['day']}")
    
    def test_add_suivi_day_7(self, auth_headers):
        """Test adding a J+7 suivi entry"""
        payload = {
            "day": 7,
            "note": "TEST_Semaine 1: progression notable",
            "status": "fait"
        }
        response = requests.post(f"{BASE_URL}/api/activite/suivi", json=payload, headers=auth_headers)
        assert response.status_code == 200
        print(f"Suivi J+7 entry added")
    
    def test_add_suivi_day_30(self, auth_headers):
        """Test adding a J+30 suivi entry"""
        payload = {
            "day": 30,
            "note": "TEST_Mois 1: bilan positif",
            "status": "fait"
        }
        response = requests.post(f"{BASE_URL}/api/activite/suivi", json=payload, headers=auth_headers)
        assert response.status_code == 200
        print(f"Suivi J+30 entry added")


class TestOnboarding:
    """Tests for onboarding endpoints"""
    
    def test_onboarding_status(self, auth_headers):
        """Test getting onboarding status"""
        response = requests.get(f"{BASE_URL}/api/features/onboarding/status", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "completed" in data
        print(f"Onboarding status: completed={data['completed']}")
    
    def test_complete_onboarding(self, auth_headers):
        """Test completing onboarding with answers"""
        payload = {
            "status": "freelance",
            "sector": "tech",
            "objective": "revenus",
            "challenge": "temps",
            "budget": "500",
            "experience": "intermediaire"
        }
        response = requests.post(f"{BASE_URL}/api/features/onboarding/complete", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["status"] == "ok"
        assert "message" in data
        
        # Verify onboarding is now complete
        status_response = requests.get(f"{BASE_URL}/api/features/onboarding/status", headers=auth_headers)
        status = status_response.json()
        assert status["completed"] == True
        assert "data" in status
        assert status["data"]["status"] == "freelance"
        
        print(f"Onboarding completed successfully")


class TestUnauthorizedAccess:
    """Tests for unauthorized access"""
    
    def test_finance_overview_no_auth(self):
        """Test finance overview without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/finance/overview")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print(f"Finance overview without auth: {response.status_code}")
    
    def test_activite_summary_no_auth(self):
        """Test activite summary without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/activite/summary")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print(f"Activite summary without auth: {response.status_code}")
    
    def test_onboarding_status_no_auth(self):
        """Test onboarding status without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/features/onboarding/status")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print(f"Onboarding status without auth: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
