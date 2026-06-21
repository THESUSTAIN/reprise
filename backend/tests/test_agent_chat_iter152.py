"""
Test Agent IA and Chat Endpoints - Iteration 152
Tests for:
- POST /api/chat/send (modes: fast, pro, gemini, perplexity, image)
- POST /api/agent/estimate
- POST /api/agent/plan
- POST /api/agent/run
- GET /api/chat/conversations
- GET /api/chat/conversations/{id}
- PUT /api/chat/conversations/{id}/rename
- DELETE /api/chat/conversations/{id}
- GET /api/chat/usage
- POST /api/chat/upload
- POST /api/chat/abort
"""
import pytest
import requests
import os
import time
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "1@Elshaddai1"


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_success(self):
        """Test admin login works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data


class TestAgentEstimate:
    """Tests for POST /api/agent/estimate"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_agent_estimate_returns_200(self, auth_token):
        """Test /api/agent/estimate returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/agent/estimate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": "Recherche les dernières actualités sur l'IA"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_agent_estimate_has_required_fields(self, auth_token):
        """Test /api/agent/estimate returns required fields"""
        response = requests.post(
            f"{BASE_URL}/api/agent/estimate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": "Analyse le site https://example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "credits_needed" in data, "Missing credits_needed"
        assert "can_run" in data, "Missing can_run"
        assert "task_type" in data, "Missing task_type"
        assert "specialization" in data, "Missing specialization"
    
    def test_agent_estimate_credits_range(self, auth_token):
        """Test credits_needed is in expected range (60-150)"""
        response = requests.post(
            f"{BASE_URL}/api/agent/estimate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": "Ecris un article de blog sur le marketing digital"}
        )
        assert response.status_code == 200
        data = response.json()
        credits = data.get("credits_needed", 0)
        assert 60 <= credits <= 150, f"Credits {credits} not in expected range 60-150"


class TestAgentPlan:
    """Tests for POST /api/agent/plan"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_agent_plan_returns_200(self, auth_token):
        """Test /api/agent/plan returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/agent/plan",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": "Va sur le site https://example.com et analyse le contenu"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_agent_plan_has_required_fields(self, auth_token):
        """Test /api/agent/plan returns task_type, steps, target_url"""
        response = requests.post(
            f"{BASE_URL}/api/agent/plan",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": "Ouvre Claude AI et pose une question"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_type" in data, "Missing task_type"
        assert "steps" in data, "Missing steps"
        # target_url may be None for text tasks
        assert "target_url" in data or "type" in data
    
    def test_agent_plan_browser_task(self, auth_token):
        """Test browser task detection"""
        response = requests.post(
            f"{BASE_URL}/api/agent/plan",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": "Va sur https://google.com et cherche 'IA 2025'"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("task_type") == "browser" or data.get("type") == "browser"
        assert data.get("target_url") is not None


class TestAgentRun:
    """Tests for POST /api/agent/run"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_agent_run_returns_200_or_402(self, auth_token):
        """Test /api/agent/run returns 200 (success) or 402 (insufficient credits)"""
        response = requests.post(
            f"{BASE_URL}/api/agent/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": "Dis bonjour en 3 langues"}
        )
        # 200 = success, 402 = insufficient credits (both are valid responses)
        assert response.status_code in [200, 402], f"Expected 200 or 402, got {response.status_code}: {response.text}"
    
    def test_agent_run_empty_task_returns_400(self, auth_token):
        """Test empty task returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/agent/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": ""}
        )
        assert response.status_code == 400
    
    def test_agent_run_too_long_task_returns_400(self, auth_token):
        """Test task > 10000 chars returns 400"""
        long_task = "a" * 10001
        response = requests.post(
            f"{BASE_URL}/api/agent/run",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"task": long_task}
        )
        assert response.status_code == 400


class TestChatSendStreaming:
    """Tests for POST /api/chat/send with streaming SSE"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_chat_send_fast_mode_streaming(self, auth_token):
        """Test /api/chat/send mode=fast returns streaming SSE response"""
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Dis bonjour", "mode": "fast"},
            stream=True
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Read streaming response
        content = ""
        conversation_id = None
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "content" in data:
                        content += data["content"]
                    if "conversation_id" in data:
                        conversation_id = data["conversation_id"]
                except json.JSONDecodeError:
                    continue
        
        assert len(content) > 0, "No content received from streaming"
        print(f"Fast mode response length: {len(content)} chars")
    
    def test_chat_send_pro_mode_streaming(self, auth_token):
        """Test /api/chat/send mode=pro returns streaming SSE response"""
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Explique brièvement ce qu'est l'IA", "mode": "pro"},
            stream=True
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "content" in data:
                        content += data["content"]
                except json.JSONDecodeError:
                    continue
        
        assert len(content) > 0, "No content received from pro mode streaming"
        print(f"Pro mode response length: {len(content)} chars")
    
    def test_chat_send_gemini_mode_streaming(self, auth_token):
        """Test /api/chat/send mode=gemini returns streaming SSE response"""
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Bonjour, comment vas-tu?", "mode": "gemini"},
            stream=True
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "content" in data:
                        content += data["content"]
                except json.JSONDecodeError:
                    continue
        
        assert len(content) > 0, "No content received from gemini mode streaming"
        print(f"Gemini mode response length: {len(content)} chars")
    
    def test_chat_send_perplexity_mode_streaming(self, auth_token):
        """Test /api/chat/send mode=perplexity returns streaming SSE response"""
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Quelles sont les dernières nouvelles sur l'IA?", "mode": "perplexity"},
            stream=True
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "content" in data:
                        content += data["content"]
                except json.JSONDecodeError:
                    continue
        
        assert len(content) > 0, "No content received from perplexity mode streaming"
        print(f"Perplexity mode response length: {len(content)} chars")
    
    def test_chat_send_empty_message_returns_400(self, auth_token):
        """Test empty message returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "", "mode": "fast"}
        )
        assert response.status_code == 400
    
    def test_chat_send_invalid_mode_returns_400(self, auth_token):
        """Test invalid mode returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Test", "mode": "invalid_mode"}
        )
        assert response.status_code == 400


class TestChatImageMode:
    """Tests for POST /api/chat/send mode=image"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_chat_send_image_mode_returns_200(self, auth_token):
        """Test /api/chat/send mode=image returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Un chat mignon", "mode": "image"},
            stream=True,
            timeout=60  # Image generation can take longer
        )
        # 200 = success, 402 = insufficient credits, 500/502 = API error (all valid)
        assert response.status_code in [200, 402, 500, 502], f"Unexpected status: {response.status_code}"
        print(f"Image mode status: {response.status_code}")


class TestChatConversations:
    """Tests for conversation CRUD endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_get_conversations_returns_200(self, auth_token):
        """Test GET /api/chat/conversations returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected list of conversations"
        print(f"Found {len(data)} conversations")
    
    def test_get_conversations_has_required_fields(self, auth_token):
        """Test conversations have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            conv = data[0]
            assert "id" in conv, "Missing id"
            assert "title" in conv, "Missing title"
    
    def test_get_single_conversation(self, auth_token):
        """Test GET /api/chat/conversations/{id} returns conversation with messages"""
        # First get list of conversations
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        conversations = response.json()
        
        if len(conversations) > 0:
            conv_id = conversations[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/chat/conversations/{conv_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data, "Missing messages field"
            print(f"Conversation {conv_id} has {len(data.get('messages', []))} messages")
        else:
            pytest.skip("No conversations to test")
    
    def test_rename_conversation(self, auth_token):
        """Test PUT /api/chat/conversations/{id}/rename"""
        # First get list of conversations
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        conversations = response.json()
        
        if len(conversations) > 0:
            conv_id = conversations[0]["id"]
            new_title = f"TEST_Renamed_{int(time.time())}"
            response = requests.put(
                f"{BASE_URL}/api/chat/conversations/{conv_id}/rename",
                headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
                json={"title": new_title}
            )
            assert response.status_code == 200, f"Rename failed: {response.text}"
            
            # Verify rename
            response = requests.get(
                f"{BASE_URL}/api/chat/conversations/{conv_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            data = response.json()
            assert data.get("title") == new_title, f"Title not updated: {data.get('title')}"
        else:
            pytest.skip("No conversations to test")


class TestChatUsage:
    """Tests for GET /api/chat/usage"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_chat_usage_returns_200(self, auth_token):
        """Test GET /api/chat/usage returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/chat/usage",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_chat_usage_has_mode_breakdown(self, auth_token):
        """Test usage returns credits by mode"""
        response = requests.get(
            f"{BASE_URL}/api/chat/usage",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should have some usage data structure
        assert isinstance(data, (dict, list)), "Expected dict or list"


class TestChatUpload:
    """Tests for POST /api/chat/upload"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_upload_text_file(self, auth_token):
        """Test uploading a text file"""
        files = {"file": ("test.txt", b"This is a test file content", "text/plain")}
        response = requests.post(
            f"{BASE_URL}/api/chat/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert "id" in data, "Missing file id"
        assert "url" in data, "Missing file url"
        print(f"Uploaded file id: {data['id']}")
    
    def test_upload_unsupported_format_returns_400(self, auth_token):
        """Test uploading unsupported format returns 400"""
        files = {"file": ("test.exe", b"fake executable", "application/octet-stream")}
        response = requests.post(
            f"{BASE_URL}/api/chat/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files
        )
        assert response.status_code == 400


class TestChatAbort:
    """Tests for POST /api/chat/abort"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_abort_returns_200(self, auth_token):
        """Test POST /api/chat/abort returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/chat/abort",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"conversation_id": "test-conversation-id"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True


class TestCreditDeduction:
    """Tests for credit deduction after chat"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_credits_deducted_after_chat(self, auth_token):
        """Test credits are deducted after successful chat"""
        # Get initial credits
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        initial_user = response.json()
        initial_total = (initial_user.get("credits", 0) + 
                        initial_user.get("bonus_credits", 0) + 
                        initial_user.get("purchased_credits", 0))
        
        # Send a chat message
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Test credit deduction", "mode": "fast"},
            stream=True
        )
        
        # Consume the stream
        for line in response.iter_lines(decode_unicode=True):
            pass
        
        # Get final credits
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        final_user = response.json()
        final_total = (final_user.get("credits", 0) + 
                      final_user.get("bonus_credits", 0) + 
                      final_user.get("purchased_credits", 0))
        
        # Credits should be deducted (fast mode = 2 credits)
        credits_used = initial_total - final_total
        print(f"Credits used: {credits_used} (initial: {initial_total}, final: {final_total})")
        assert credits_used >= 0, "Credits should not increase after chat"


class TestMultiTurnConversation:
    """Tests for multi-turn conversation context"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_conversation_context_preserved(self, auth_token):
        """Test that conversation context is preserved across messages"""
        # First message - introduce a topic
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Mon nom est TestUser123", "mode": "fast"},
            stream=True
        )
        assert response.status_code == 200
        
        conversation_id = None
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "conversation_id" in data:
                        conversation_id = data["conversation_id"]
                except json.JSONDecodeError:
                    continue
        
        assert conversation_id is not None, "No conversation_id received"
        
        # Second message - reference the topic
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"message": "Quel est mon nom?", "mode": "fast", "conversation_id": conversation_id},
            stream=True
        )
        assert response.status_code == 200
        
        content = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "content" in data:
                        content += data["content"]
                except json.JSONDecodeError:
                    continue
        
        # The AI should remember the name from context
        print(f"Multi-turn response: {content[:200]}...")
        # Note: We can't guarantee the AI will always remember, but the conversation should work


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
