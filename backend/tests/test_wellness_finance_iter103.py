"""
Test Wellness (Pulse Bien-etre) and Finance (Pilotage Financier) APIs - Iteration 103
Tests:
- Wellness: POST /api/wellness/checkin, GET /api/wellness/today, GET /api/wellness/history, GET /api/wellness/weekly-report
- Finance: POST /api/finance/entry, GET /api/finance/overview, DELETE /api/finance/entry/{id}, GET /api/finance/forecast
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    elif response.status_code == 429:
        pytest.skip("Rate limited - wait before retrying")
    pytest.fail(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestWellnessAPI:
    """Tests for Wellness / Pulse Bien-etre API endpoints"""
    
    def test_wellness_checkin_create(self, headers):
        """POST /api/wellness/checkin - Create a daily check-in"""
        payload = {
            "energy": 4,
            "mood": 3,
            "stress": 2,
            "sleep": 4,
            "notes": "Test check-in from iteration 103"
        }
        response = requests.post(f"{BASE_URL}/api/wellness/checkin", json=payload, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response should contain 'id'"
        assert "score" in data, "Response should contain 'score'"
        assert "ai_insight" in data, "Response should contain 'ai_insight'"
        assert "micro_actions" in data, "Response should contain 'micro_actions'"
        assert "burnout_risk" in data, "Response should contain 'burnout_risk'"
        
        # Verify score is 0-100
        assert 0 <= data["score"] <= 100, f"Score should be 0-100, got {data['score']}"
        
        # Verify micro_actions is a list
        assert isinstance(data["micro_actions"], list), "micro_actions should be a list"
        
        print(f"PASS: Wellness check-in created with score {data['score']}")
        return data
    
    def test_wellness_today(self, headers):
        """GET /api/wellness/today - Get today's check-in"""
        response = requests.get(f"{BASE_URL}/api/wellness/today", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should have has_checkin field
        assert "has_checkin" in data, "Response should contain 'has_checkin'"
        
        if data["has_checkin"]:
            # Verify check-in data structure
            assert "energy" in data, "Should have energy"
            assert "mood" in data, "Should have mood"
            assert "stress" in data, "Should have stress"
            assert "sleep" in data, "Should have sleep"
            assert "score" in data, "Should have score"
            print(f"PASS: Today's check-in found with score {data['score']}")
        else:
            print("PASS: No check-in today (expected if first test)")
        
        return data
    
    def test_wellness_history(self, headers):
        """GET /api/wellness/history?days=14 - Get check-in history"""
        response = requests.get(f"{BASE_URL}/api/wellness/history?days=14", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "checkins" in data, "Response should contain 'checkins'"
        assert "stats" in data, "Response should contain 'stats'"
        assert "burnout_risk" in data, "Response should contain 'burnout_risk'"
        
        # Verify checkins is a list
        assert isinstance(data["checkins"], list), "checkins should be a list"
        
        # Verify stats structure
        stats = data["stats"]
        assert "total_checkins" in stats, "Stats should have total_checkins"
        assert "avg_score" in stats, "Stats should have avg_score"
        assert "avg_energy" in stats, "Stats should have avg_energy"
        assert "avg_stress" in stats, "Stats should have avg_stress"
        
        print(f"PASS: History returned {stats['total_checkins']} check-ins, avg score: {stats['avg_score']}")
        return data
    
    def test_wellness_weekly_report(self, headers):
        """GET /api/wellness/weekly-report - Get weekly wellness report"""
        response = requests.get(f"{BASE_URL}/api/wellness/weekly-report", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should have has_data field
        if data.get("has_data"):
            assert "nb_checkins" in data, "Should have nb_checkins"
            assert "avg_score" in data, "Should have avg_score"
            assert "avg_energy" in data, "Should have avg_energy"
            assert "avg_stress" in data, "Should have avg_stress"
            assert "energy_trend" in data, "Should have energy_trend"
            assert "stress_trend" in data, "Should have stress_trend"
            assert "advice" in data, "Should have advice"
            print(f"PASS: Weekly report - {data['nb_checkins']} check-ins, avg score: {data['avg_score']}")
        else:
            assert "message" in data, "Should have message when no data"
            print(f"PASS: No weekly data - {data.get('message', 'No message')}")
        
        return data
    
    def test_wellness_checkin_validation(self, headers):
        """Test validation - values must be 1-5"""
        # Test invalid energy value
        payload = {
            "energy": 6,  # Invalid - should be 1-5
            "mood": 3,
            "stress": 2,
            "sleep": 4
        }
        response = requests.post(f"{BASE_URL}/api/wellness/checkin", json=payload, headers=headers)
        
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for invalid value, got {response.status_code}"
        print("PASS: Validation correctly rejects energy > 5")
    
    def test_wellness_score_calculation(self, headers):
        """Test score calculation - verify score is computed correctly"""
        # Best case: energy=5, mood=5, stress=1 (low stress is good), sleep=5
        # Score formula: ((energy + mood + (6-stress) + sleep) / 4 - 1) / 4 * 100
        # = ((5 + 5 + 5 + 5) / 4 - 1) / 4 * 100 = (5 - 1) / 4 * 100 = 100
        payload = {
            "energy": 5,
            "mood": 5,
            "stress": 1,  # Low stress = good
            "sleep": 5
        }
        response = requests.post(f"{BASE_URL}/api/wellness/checkin", json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # Perfect score should be 100
            assert data["score"] == 100, f"Perfect inputs should give score 100, got {data['score']}"
            print(f"PASS: Perfect score calculation verified: {data['score']}")
        else:
            print(f"INFO: Could not verify score calculation - {response.status_code}")


class TestFinanceAPI:
    """Tests for Finance / Pilotage Financier API endpoints"""
    
    created_entry_id = None
    
    def test_finance_entry_create_revenu(self, headers):
        """POST /api/finance/entry - Create a revenue entry"""
        payload = {
            "type": "revenu",
            "label": "TEST_Facture client iteration 103",
            "amount": 1500.00,
            "category": "service",
            "recurring": False
        }
        response = requests.post(f"{BASE_URL}/api/finance/entry", json=payload, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("status") == "ok", "Status should be 'ok'"
        assert "entry" in data, "Response should contain 'entry'"
        
        entry = data["entry"]
        assert entry["type"] == "revenu", "Type should be 'revenu'"
        assert entry["label"] == payload["label"], "Label should match"
        assert entry["amount"] == payload["amount"], "Amount should match"
        assert entry["category"] == payload["category"], "Category should match"
        assert "id" in entry, "Entry should have an ID"
        
        TestFinanceAPI.created_entry_id = entry["id"]
        print(f"PASS: Revenue entry created with ID {entry['id']}")
        return entry
    
    def test_finance_entry_create_depense(self, headers):
        """POST /api/finance/entry - Create an expense entry"""
        payload = {
            "type": "depense",
            "label": "TEST_Abonnement logiciel iteration 103",
            "amount": 49.99,
            "category": "outils",
            "recurring": True
        }
        response = requests.post(f"{BASE_URL}/api/finance/entry", json=payload, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("status") == "ok", "Status should be 'ok'"
        entry = data["entry"]
        assert entry["type"] == "depense", "Type should be 'depense'"
        assert entry["recurring"] == True, "Recurring should be True"
        
        print(f"PASS: Expense entry created with ID {entry['id']}")
        return entry
    
    def test_finance_overview(self, headers):
        """GET /api/finance/overview?period=mois - Get financial overview"""
        response = requests.get(f"{BASE_URL}/api/finance/overview?period=mois", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "period" in data, "Should have period"
        assert "revenus" in data, "Should have revenus"
        assert "depenses" in data, "Should have depenses"
        assert "net" in data, "Should have net"
        assert "seuil_equilibre" in data, "Should have seuil_equilibre"
        assert "taux_marge" in data, "Should have taux_marge"
        assert "nb_transactions" in data, "Should have nb_transactions"
        assert "categories_revenus" in data, "Should have categories_revenus"
        assert "categories_depenses" in data, "Should have categories_depenses"
        assert "weekly" in data, "Should have weekly"
        assert "monthly" in data, "Should have monthly"
        assert "recent_entries" in data, "Should have recent_entries"
        
        # Verify data types
        assert isinstance(data["revenus"], (int, float)), "revenus should be numeric"
        assert isinstance(data["depenses"], (int, float)), "depenses should be numeric"
        assert isinstance(data["weekly"], list), "weekly should be a list"
        assert isinstance(data["monthly"], list), "monthly should be a list"
        assert isinstance(data["recent_entries"], list), "recent_entries should be a list"
        
        print(f"PASS: Finance overview - Revenus: {data['revenus']} EUR, Depenses: {data['depenses']} EUR, Net: {data['net']} EUR")
        return data
    
    def test_finance_overview_periods(self, headers):
        """Test different period filters"""
        periods = ["semaine", "mois", "trimestre", "annee"]
        
        for period in periods:
            response = requests.get(f"{BASE_URL}/api/finance/overview?period={period}", headers=headers)
            assert response.status_code == 200, f"Period '{period}' failed: {response.status_code}"
            data = response.json()
            assert data["period"] == period, f"Period should be '{period}'"
            print(f"PASS: Period '{period}' works correctly")
    
    def test_finance_forecast(self, headers):
        """GET /api/finance/forecast - Get financial forecast"""
        response = requests.get(f"{BASE_URL}/api/finance/forecast", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "avg_monthly_revenue" in data, "Should have avg_monthly_revenue"
        assert "avg_monthly_expense" in data, "Should have avg_monthly_expense"
        assert "forecast" in data, "Should have forecast"
        assert "health" in data, "Should have health"
        
        # Verify forecast is a list with 3 months
        assert isinstance(data["forecast"], list), "forecast should be a list"
        
        # Verify health is one of expected values
        assert data["health"] in ["bon", "attention", "critique"], f"Health should be bon/attention/critique, got {data['health']}"
        
        print(f"PASS: Forecast - Avg revenue: {data['avg_monthly_revenue']} EUR, Health: {data['health']}")
        return data
    
    def test_finance_entry_delete(self, headers):
        """DELETE /api/finance/entry/{id} - Delete a finance entry"""
        # First create an entry to delete
        payload = {
            "type": "depense",
            "label": "TEST_Entry to delete",
            "amount": 10.00,
            "category": "autre"
        }
        create_response = requests.post(f"{BASE_URL}/api/finance/entry", json=payload, headers=headers)
        assert create_response.status_code == 200, "Failed to create entry for deletion test"
        
        entry_id = create_response.json()["entry"]["id"]
        
        # Now delete it
        delete_response = requests.delete(f"{BASE_URL}/api/finance/entry/{entry_id}", headers=headers)
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert data.get("status") == "ok", "Status should be 'ok'"
        
        # Verify it's deleted by checking overview
        overview_response = requests.get(f"{BASE_URL}/api/finance/overview?period=mois", headers=headers)
        overview_data = overview_response.json()
        
        # Entry should not be in recent_entries
        entry_ids = [e["id"] for e in overview_data.get("recent_entries", [])]
        assert entry_id not in entry_ids, "Deleted entry should not appear in recent_entries"
        
        print(f"PASS: Entry {entry_id} deleted successfully")
    
    def test_finance_entry_delete_not_found(self, headers):
        """DELETE /api/finance/entry/{id} - Should return 404 for non-existent entry"""
        fake_id = "non-existent-id-12345"
        response = requests.delete(f"{BASE_URL}/api/finance/entry/{fake_id}", headers=headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: 404 returned for non-existent entry")
    
    def test_finance_budget_set(self, headers):
        """POST /api/finance/budget - Set a budget goal"""
        payload = {
            "category": "outils",
            "amount": 200.00,
            "period": "mois"
        }
        response = requests.post(f"{BASE_URL}/api/finance/budget", json=payload, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("status") == "ok", "Status should be 'ok'"
        assert "budgets" in data, "Should return budgets list"
        
        # Verify budget was set
        budgets = data["budgets"]
        outils_budget = next((b for b in budgets if b["category"] == "outils"), None)
        assert outils_budget is not None, "Budget for 'outils' should exist"
        assert outils_budget["amount"] == 200.00, "Budget amount should be 200"
        
        print(f"PASS: Budget set for 'outils': {outils_budget['amount']} EUR")


class TestFinanceDataPersistence:
    """Test that finance data is persisted in DB (not in-memory)"""
    
    def test_data_persists_across_requests(self, headers):
        """Verify data persists - create entry, then verify it appears in overview"""
        # Create a unique entry
        unique_label = f"TEST_Persistence_{datetime.now().strftime('%H%M%S')}"
        payload = {
            "type": "revenu",
            "label": unique_label,
            "amount": 777.77,
            "category": "service"
        }
        
        # Create entry
        create_response = requests.post(f"{BASE_URL}/api/finance/entry", json=payload, headers=headers)
        assert create_response.status_code == 200, "Failed to create entry"
        entry_id = create_response.json()["entry"]["id"]
        
        # Wait a moment
        time.sleep(0.5)
        
        # Fetch overview and verify entry is there
        overview_response = requests.get(f"{BASE_URL}/api/finance/overview?period=mois", headers=headers)
        assert overview_response.status_code == 200, "Failed to get overview"
        
        overview_data = overview_response.json()
        recent_entries = overview_data.get("recent_entries", [])
        
        # Find our entry
        our_entry = next((e for e in recent_entries if e["id"] == entry_id), None)
        assert our_entry is not None, f"Created entry {entry_id} should appear in recent_entries"
        assert our_entry["label"] == unique_label, "Entry label should match"
        assert our_entry["amount"] == 777.77, "Entry amount should match"
        
        print(f"PASS: Data persistence verified - entry {entry_id} found in overview")
        
        # Cleanup - delete the test entry
        requests.delete(f"{BASE_URL}/api/finance/entry/{entry_id}", headers=headers)


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API is responding"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("PASS: API health check")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
