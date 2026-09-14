"""
TheSustain Module Backend Tests - Iteration 146
Tests for:
- POST /api/chat/message (Chatbot Pastoral - non-streaming chat)
- POST /api/chat/image (Content Creation - image generation)
- GET /api/audit/data (Audit 360° - get metrics)
- POST /api/audit/analyze (Audit 360° - AI biblical analysis)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTheSustainAuth:
    """Authentication for TheSustain tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, f"No token in response: {data}"
        return data.get("access_token") or data.get("token")


class TestChatbotPastoral(TestTheSustainAuth):
    """Tests for /api/chat/message endpoint - Chatbot Pastoral"""
    
    def test_chat_message_success(self, auth_token):
        """Test sending a message to chatbot pastoral"""
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "message": "Bonjour, comment puis-je prier aujourd'hui?",
                "system_prompt": "Tu es Gabriel, assistant pastoral bienveillant.",
                "model": "fast"
            },
            timeout=60
        )
        print(f"Chat message response status: {response.status_code}")
        print(f"Chat message response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data or "message" in data, f"No response/message in data: {data}"
        content = data.get("response") or data.get("message")
        assert content and len(content) > 0, "Response content is empty"
        print(f"✓ Chat message returned valid response: {content[:100]}...")
    
    def test_chat_message_empty_message(self, auth_token):
        """Test sending empty message returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "message": "",
                "system_prompt": "Tu es Gabriel",
                "model": "fast"
            },
            timeout=30
        )
        print(f"Empty message response: {response.status_code}")
        assert response.status_code == 400, f"Expected 400 for empty message, got {response.status_code}"
        print("✓ Empty message correctly returns 400")
    
    def test_chat_message_without_auth(self):
        """Test chat message without authentication returns 401/403"""
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            headers={"Content-Type": "application/json"},
            json={
                "message": "Test message",
                "system_prompt": "",
                "model": "fast"
            },
            timeout=30
        )
        print(f"No auth response: {response.status_code}")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Unauthenticated request correctly rejected")
    
    def test_chat_message_with_system_prompt(self, auth_token):
        """Test chat message with custom system prompt"""
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "message": "Donne-moi un verset d'encouragement",
                "system_prompt": "Tu es un assistant pastoral nommé Gabriel. Réponds avec bienveillance et cite des versets bibliques.",
                "model": "fast"
            },
            timeout=60
        )
        print(f"System prompt test response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data or "message" in data
        print("✓ Chat with system prompt works correctly")


class TestContentCreation(TestTheSustainAuth):
    """Tests for /api/chat/image endpoint - Content Creation"""
    
    def test_image_generation_success(self, auth_token):
        """Test image generation endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/chat/image",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "prompt": "Coucher de soleil paisible avec le verset Jean 3:16 en texte visible",
                "style": "verset_illustre"
            },
            timeout=120  # Image generation can take 15-30+ seconds
        )
        print(f"Image generation response status: {response.status_code}")
        print(f"Image generation response: {response.text[:500]}")
        
        # Accept 200 (success) or 402 (insufficient credits)
        assert response.status_code in [200, 402], f"Expected 200 or 402, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            # Check for image data in response
            has_image = (
                data.get("image_base64") or 
                data.get("url") or 
                data.get("image_url") or
                data.get("text")  # May return text if no image generated
            )
            print(f"Image response keys: {list(data.keys())}")
            print("✓ Image generation endpoint responded successfully")
        else:
            print("✓ Image generation returned 402 (insufficient credits) - endpoint working")
    
    def test_image_generation_empty_prompt(self, auth_token):
        """Test image generation with empty prompt returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/chat/image",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "prompt": "",
                "style": "verset_illustre"
            },
            timeout=30
        )
        print(f"Empty prompt response: {response.status_code}")
        assert response.status_code == 400, f"Expected 400 for empty prompt, got {response.status_code}"
        print("✓ Empty prompt correctly returns 400")
    
    def test_image_generation_without_auth(self):
        """Test image generation without authentication"""
        response = requests.post(
            f"{BASE_URL}/api/chat/image",
            headers={"Content-Type": "application/json"},
            json={
                "prompt": "Test image",
                "style": "verset_illustre"
            },
            timeout=30
        )
        print(f"No auth response: {response.status_code}")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Unauthenticated image request correctly rejected")


class TestAudit360(TestTheSustainAuth):
    """Tests for /api/audit/* endpoints - Audit 360° Biblique"""
    
    def test_get_audit_data(self, auth_token):
        """Test GET /api/audit/data returns metrics"""
        response = requests.get(
            f"{BASE_URL}/api/audit/data",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        print(f"Audit data response status: {response.status_code}")
        print(f"Audit data response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify expected fields in response
        assert "metrics" in data, f"No metrics in response: {data}"
        metrics = data["metrics"]
        assert "engagement_global" in metrics or metrics.get("engagement_global") is not None
        print(f"✓ Audit data returned with metrics: engagement_global={metrics.get('engagement_global')}")
    
    def test_audit_analyze(self, auth_token):
        """Test POST /api/audit/analyze returns biblical insights"""
        response = requests.post(
            f"{BASE_URL}/api/audit/analyze",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "org_name": "Église Test",
                "metrics": {
                    "engagement_global": 75,
                    "sentiment_positif": 80,
                    "sentiment_neutre": 15,
                    "sentiment_negatif": 5,
                    "nouveaux_visiteurs": 50,
                    "score_sante": 7.5
                },
                "comments": [
                    {"text": "Le culte était très inspirant", "source": "sondage", "sentiment": "positif"},
                    {"text": "J'aimerais plus d'activités pour les jeunes", "source": "sondage", "sentiment": "neutre"}
                ]
            },
            timeout=90  # AI analysis may take time
        )
        print(f"Audit analyze response status: {response.status_code}")
        print(f"Audit analyze response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "status" in data and data["status"] == "ok", f"Unexpected status: {data}"
        assert "insights" in data, f"No insights in response: {data}"
        insights = data["insights"]
        assert isinstance(insights, list), f"Insights should be a list: {type(insights)}"
        print(f"✓ Audit analyze returned {len(insights)} insights")
        
        if insights:
            first_insight = insights[0]
            print(f"  First insight: {first_insight}")
    
    def test_audit_save(self, auth_token):
        """Test POST /api/audit/save"""
        response = requests.post(
            f"{BASE_URL}/api/audit/save",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "org_name": "TEST_Église Zayado",
                "org_type": "eglise",
                "metrics": {
                    "engagement_global": 72,
                    "sentiment_positif": 85,
                    "sentiment_neutre": 10,
                    "sentiment_negatif": 5,
                    "nouveaux_visiteurs": 124,
                    "score_sante": 8.5
                },
                "comments": []
            },
            timeout=30
        )
        print(f"Audit save response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Save failed: {data}"
        print("✓ Audit save successful")
    
    def test_audit_add_comment(self, auth_token):
        """Test POST /api/audit/comment"""
        response = requests.post(
            f"{BASE_URL}/api/audit/comment",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "author": "TEST_User",
                "text": "TEST_Commentaire de test pour l'audit",
                "source": "sondage",
                "sentiment": "positif"
            },
            timeout=30
        )
        print(f"Add comment response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Add comment failed: {data}"
        assert "comments" in data, f"No comments in response: {data}"
        print(f"✓ Comment added, total comments: {len(data['comments'])}")
    
    def test_audit_data_without_auth(self):
        """Test audit data without authentication"""
        response = requests.get(
            f"{BASE_URL}/api/audit/data",
            timeout=30
        )
        print(f"No auth audit response: {response.status_code}")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Unauthenticated audit request correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
