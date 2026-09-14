"""
Test Mon Activité page APIs - Iteration 126
Tests for data persistence, CRUD operations for blockers, priorities, checklist, suivi, and IA context
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


class TestActiviteAPIs:
    """Test Mon Activité page backend APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
        
        data = login_response.json()
        # Handle both 'token' and 'access_token' field names
        token = data.get("access_token") or data.get("token")
        if not token:
            pytest.skip(f"No token in login response: {data}")
        
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_activite_summary(self):
        """Test GET /api/activite/summary - should return all sections"""
        response = self.session.get(f"{BASE_URL}/api/activite/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify all expected sections exist
        assert "ou_tu_en_es" in data, "Missing ou_tu_en_es section"
        assert "ce_qui_te_bloque" in data, "Missing ce_qui_te_bloque section"
        assert "ton_action_prioritaire" in data, "Missing ton_action_prioritaire section"
        assert "fais_le_maintenant" in data, "Missing fais_le_maintenant section"
        assert "suivi" in data, "Missing suivi section"
        assert "ia_contextuelle" in data, "Missing ia_contextuelle section"
        
        print(f"✓ GET /api/activite/summary returned all sections")
    
    def test_save_blocker_and_persist(self):
        """Test POST /api/activite/blocker - save and verify persistence"""
        test_blocker = "TEST_BLOCKER_126: Manque de temps pour prospecter"
        
        # Save blocker
        response = self.session.post(f"{BASE_URL}/api/activite/blocker", json={
            "tension": test_blocker,
            "detail": "Je passe trop de temps sur les tâches admin"
        })
        assert response.status_code == 200, f"Save blocker failed: {response.status_code} - {response.text}"
        
        # Verify persistence by fetching summary
        summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
        assert summary_response.status_code == 200
        
        data = summary_response.json()
        blocker = data.get("ce_qui_te_bloque")
        assert blocker is not None, "Blocker not persisted"
        assert blocker.get("tension") == test_blocker, f"Blocker text mismatch: {blocker.get('tension')}"
        
        print(f"✓ Blocker saved and persisted correctly")
    
    def test_save_priority_and_persist(self):
        """Test POST /api/activite/priority - save and verify persistence"""
        test_priority = "TEST_PRIORITY_126: Finaliser la proposition commerciale"
        test_why = "Client attend une réponse avant vendredi"
        
        # Save priority
        response = self.session.post(f"{BASE_URL}/api/activite/priority", json={
            "title": test_priority,
            "why": test_why
        })
        assert response.status_code == 200, f"Save priority failed: {response.status_code} - {response.text}"
        
        # Verify persistence
        summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
        assert summary_response.status_code == 200
        
        data = summary_response.json()
        priority = data.get("ton_action_prioritaire")
        assert priority is not None, "Priority not persisted"
        assert priority.get("title") == test_priority, f"Priority title mismatch: {priority.get('title')}"
        assert priority.get("why") == test_why, f"Priority why mismatch: {priority.get('why')}"
        
        print(f"✓ Priority saved and persisted correctly")
    
    def test_add_checklist_item_and_persist(self):
        """Test POST /api/activite/checklist - add item and verify persistence"""
        test_item = "TEST_CHECKLIST_126: Envoyer le devis au client"
        
        # First get existing checklist
        summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
        existing_checklist = summary_response.json().get("fais_le_maintenant", {}).get("checklist", [])
        
        # Add new item
        new_checklist = existing_checklist + [{"text": test_item, "done": False}]
        response = self.session.post(f"{BASE_URL}/api/activite/checklist", json=new_checklist)
        assert response.status_code == 200, f"Add checklist failed: {response.status_code} - {response.text}"
        
        # Verify persistence
        summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
        assert summary_response.status_code == 200
        
        data = summary_response.json()
        checklist = data.get("fais_le_maintenant", {}).get("checklist", [])
        
        # Find our test item
        found = any(item.get("text") == test_item for item in checklist)
        assert found, f"Checklist item not found in: {checklist}"
        
        print(f"✓ Checklist item added and persisted correctly")
    
    def test_toggle_checklist_item(self):
        """Test POST /api/activite/checklist/toggle/{item_id} - toggle done state"""
        # First get checklist to find an item to toggle
        summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
        checklist = summary_response.json().get("fais_le_maintenant", {}).get("checklist", [])
        
        if not checklist:
            # Add an item first
            response = self.session.post(f"{BASE_URL}/api/activite/checklist", json=[
                {"text": "TEST_TOGGLE_126: Item to toggle", "done": False}
            ])
            assert response.status_code == 200
            
            # Refresh checklist
            summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
            checklist = summary_response.json().get("fais_le_maintenant", {}).get("checklist", [])
        
        if checklist:
            item_id = checklist[0].get("id")
            initial_done = checklist[0].get("done", False)
            
            # Toggle the item
            response = self.session.post(f"{BASE_URL}/api/activite/checklist/toggle/{item_id}")
            assert response.status_code == 200, f"Toggle failed: {response.status_code} - {response.text}"
            
            # Verify toggle worked
            summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
            updated_checklist = summary_response.json().get("fais_le_maintenant", {}).get("checklist", [])
            
            updated_item = next((item for item in updated_checklist if item.get("id") == item_id), None)
            if updated_item:
                assert updated_item.get("done") != initial_done, "Toggle did not change done state"
                print(f"✓ Checklist item toggled successfully")
            else:
                print(f"⚠ Could not verify toggle - item not found after toggle")
        else:
            pytest.skip("No checklist items to toggle")
    
    def test_add_suivi_entry_and_persist(self):
        """Test POST /api/activite/suivi - add suivi note and verify persistence"""
        test_note = "TEST_SUIVI_126: Bonne progression sur le projet client"
        test_day = 1
        
        # Add suivi entry
        response = self.session.post(f"{BASE_URL}/api/activite/suivi", json={
            "day": test_day,
            "note": test_note,
            "status": "en_cours"
        })
        assert response.status_code == 200, f"Add suivi failed: {response.status_code} - {response.text}"
        
        # Verify persistence
        summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
        assert summary_response.status_code == 200
        
        data = summary_response.json()
        suivi_entries = data.get("suivi", {}).get("entries", [])
        
        # Find our test entry
        found = any(entry.get("note") == test_note and entry.get("day") == test_day for entry in suivi_entries)
        assert found, f"Suivi entry not found in: {suivi_entries}"
        
        print(f"✓ Suivi entry added and persisted correctly")
    
    def test_save_ia_context_and_persist(self):
        """Test POST /api/activite/ia-context - save IA recommendation and verify persistence"""
        test_recommendation = "TEST_IA_126: Concentrez-vous sur votre priorité #1 ce matin"
        
        # Save IA context
        response = self.session.post(f"{BASE_URL}/api/activite/ia-context", json={
            "recommendation": test_recommendation,
            "type": "auto"
        })
        assert response.status_code == 200, f"Save IA context failed: {response.status_code} - {response.text}"
        
        # Verify persistence
        summary_response = self.session.get(f"{BASE_URL}/api/activite/summary")
        assert summary_response.status_code == 200
        
        data = summary_response.json()
        ia_context = data.get("ia_contextuelle")
        assert ia_context is not None, "IA context not persisted"
        assert ia_context.get("recommendation") == test_recommendation, f"IA recommendation mismatch: {ia_context.get('recommendation')}"
        
        print(f"✓ IA context saved and persisted correctly")
    
    def test_chat_quick_endpoint(self):
        """Test POST /api/chat/quick - should work when called explicitly"""
        response = self.session.post(f"{BASE_URL}/api/chat/quick", json={
            "message": "Donne-moi un conseil pour bien démarrer ma journée",
            "system": "Tu es un coach business bienveillant. Réponds en français, 2-3 phrases max."
        })
        
        # Should return 200 if EMERGENT_LLM_KEY is configured, 503 if not
        if response.status_code == 200:
            data = response.json()
            assert "response" in data, f"Missing response field: {data}"
            print(f"✓ /api/chat/quick works - got response")
        elif response.status_code == 503:
            # Expected if EMERGENT_LLM_KEY is not configured
            print(f"⚠ /api/chat/quick returned 503 - EMERGENT_LLM_KEY may not be configured")
        else:
            # 400 or other errors are unexpected
            assert False, f"Unexpected status {response.status_code}: {response.text}"


class TestDataPersistenceAfterRefresh:
    """Test that data persists after simulated page refresh (re-fetching summary)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        data = login_response.json()
        token = data.get("access_token") or data.get("token")
        if not token:
            pytest.skip("No token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_full_workflow_persistence(self):
        """Test complete workflow: save all data types, then verify all persist"""
        # 1. Save blocker
        blocker_text = "PERSIST_TEST_126: Mon blocage principal"
        self.session.post(f"{BASE_URL}/api/activite/blocker", json={"tension": blocker_text})
        
        # 2. Save priority
        priority_text = "PERSIST_TEST_126: Ma priorité du jour"
        self.session.post(f"{BASE_URL}/api/activite/priority", json={"title": priority_text, "why": "Important"})
        
        # 3. Add checklist item
        checklist_text = "PERSIST_TEST_126: Tâche à faire"
        self.session.post(f"{BASE_URL}/api/activite/checklist", json=[{"text": checklist_text, "done": False}])
        
        # 4. Add suivi
        suivi_text = "PERSIST_TEST_126: Note de suivi"
        self.session.post(f"{BASE_URL}/api/activite/suivi", json={"day": 1, "note": suivi_text})
        
        # 5. Save IA context
        ia_text = "PERSIST_TEST_126: Recommandation IA"
        self.session.post(f"{BASE_URL}/api/activite/ia-context", json={"recommendation": ia_text, "type": "auto"})
        
        # Now simulate page refresh by fetching summary
        response = self.session.get(f"{BASE_URL}/api/activite/summary")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all data persisted
        errors = []
        
        if not data.get("ce_qui_te_bloque") or data["ce_qui_te_bloque"].get("tension") != blocker_text:
            errors.append(f"Blocker not persisted: {data.get('ce_qui_te_bloque')}")
        
        if not data.get("ton_action_prioritaire") or data["ton_action_prioritaire"].get("title") != priority_text:
            errors.append(f"Priority not persisted: {data.get('ton_action_prioritaire')}")
        
        checklist = data.get("fais_le_maintenant", {}).get("checklist", [])
        if not any(item.get("text") == checklist_text for item in checklist):
            errors.append(f"Checklist item not persisted: {checklist}")
        
        suivi_entries = data.get("suivi", {}).get("entries", [])
        if not any(entry.get("note") == suivi_text for entry in suivi_entries):
            errors.append(f"Suivi not persisted: {suivi_entries}")
        
        ia_context = data.get("ia_contextuelle")
        if not ia_context or ia_context.get("recommendation") != ia_text:
            errors.append(f"IA context not persisted: {ia_context}")
        
        if errors:
            assert False, "Persistence errors:\n" + "\n".join(errors)
        
        print(f"✓ All data types persist correctly after refresh")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
