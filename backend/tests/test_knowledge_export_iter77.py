"""
Test Knowledge Base and Export Email Features - Iteration 77
Tests:
1. POST /api/team/knowledge/upload - Upload TXT file, verify text extraction
2. GET /api/team/knowledge/files - List uploaded files
3. DELETE /api/team/knowledge/files/{file_id} - Delete file
4. POST /api/team/public/chat - RAG integration with knowledge base
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"
TEAM_CODE = "ZAYA-CFCC72"


class TestKnowledgeBase:
    """Knowledge Base API tests - upload, list, delete, RAG"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Auth response uses 'access_token' not 'token'
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def upload_headers(self, auth_token):
        """Headers for file upload (no Content-Type, let requests set it)"""
        return {
            "Authorization": f"Bearer {auth_token}"
        }
    
    def test_01_upload_txt_file(self, upload_headers):
        """Test uploading a TXT file and verify text extraction"""
        # Create a test TXT file content
        test_content = """Extension IA Tarifs 2024
        
Plan Gratuit: 0 EUR/mois - 180 credits
Plan Pro: 19 EUR/mois - 2000 credits
Plan Business: 49 EUR/mois - 5000 credits
Plan Team: 99 EUR/mois - credits illimites

Fonctionnalites:
- Chatbot IA intelligent
- Base de connaissances RAG
- Export des leads
- Integration site web
"""
        
        # Create file-like object
        files = {
            'file': ('test_tarifs.txt', io.BytesIO(test_content.encode('utf-8')), 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/team/knowledge/upload",
            headers=upload_headers,
            files=files
        )
        
        print(f"Upload response status: {response.status_code}")
        print(f"Upload response: {response.text}")
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain file id"
        assert data.get("filename") == "test_tarifs.txt", f"Filename mismatch: {data.get('filename')}"
        assert data.get("status") == "active", f"Status should be active: {data.get('status')}"
        assert data.get("text_length", 0) > 0, f"Text should be extracted: {data.get('text_length')}"
        assert data.get("size", 0) > 0, f"Size should be > 0: {data.get('size')}"
        
        # Store file_id for later tests
        TestKnowledgeBase.uploaded_file_id = data.get("id")
        print(f"Uploaded file ID: {TestKnowledgeBase.uploaded_file_id}")
        print(f"Text length extracted: {data.get('text_length')}")
    
    def test_02_list_knowledge_files(self, headers):
        """Test listing knowledge files - should include uploaded file"""
        response = requests.get(
            f"{BASE_URL}/api/team/knowledge/files",
            headers=headers
        )
        
        print(f"List files response status: {response.status_code}")
        print(f"List files response: {response.text}")
        
        assert response.status_code == 200, f"List failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Find our uploaded file
        uploaded_file = next((f for f in data if f.get("filename") == "test_tarifs.txt"), None)
        assert uploaded_file is not None, f"Uploaded file not found in list: {data}"
        assert uploaded_file.get("status") == "active", f"File status should be active"
        assert uploaded_file.get("text_length", 0) > 0, f"Text length should be > 0"
        
        print(f"Found {len(data)} knowledge files")
    
    def test_03_public_chat_with_rag(self, headers):
        """Test public chat uses knowledge base content (RAG)"""
        # Ask about tarifs - should reference the uploaded knowledge
        response = requests.post(
            f"{BASE_URL}/api/team/public/chat",
            headers=headers,
            json={
                "team_code": TEAM_CODE,
                "message": "Quels sont les tarifs de Extension IA?",
                "user_name": "Test User",
                "user_email": "test@example.com",
                "history": []
            }
        )
        
        print(f"Chat response status: {response.status_code}")
        print(f"Chat response: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Chat failed: {response.text}"
        
        data = response.json()
        assert "reply" in data, f"Response should contain reply: {data}"
        
        reply = data.get("reply", "").lower()
        # The reply should reference pricing info from the knowledge base
        # Check for any pricing-related terms
        pricing_terms = ["19", "49", "99", "gratuit", "pro", "business", "team", "credits", "plan", "tarif", "prix", "eur"]
        found_terms = [term for term in pricing_terms if term in reply]
        
        print(f"Reply: {data.get('reply')[:300]}...")
        print(f"Found pricing terms in reply: {found_terms}")
        
        # At least some pricing info should be in the reply
        assert len(found_terms) > 0, f"Reply should reference knowledge base content. Reply: {reply[:200]}"
    
    def test_04_delete_knowledge_file(self, headers):
        """Test deleting a knowledge file"""
        file_id = getattr(TestKnowledgeBase, 'uploaded_file_id', None)
        
        if not file_id:
            # Try to get a file to delete
            list_response = requests.get(
                f"{BASE_URL}/api/team/knowledge/files",
                headers=headers
            )
            if list_response.status_code == 200:
                files = list_response.json()
                test_file = next((f for f in files if f.get("filename") == "test_tarifs.txt"), None)
                if test_file:
                    file_id = test_file.get("id")
        
        assert file_id, "No file ID to delete"
        
        response = requests.delete(
            f"{BASE_URL}/api/team/knowledge/files/{file_id}",
            headers=headers
        )
        
        print(f"Delete response status: {response.status_code}")
        print(f"Delete response: {response.text}")
        
        assert response.status_code == 200, f"Delete failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Delete should return success: {data}"
        
        # Verify file is gone
        list_response = requests.get(
            f"{BASE_URL}/api/team/knowledge/files",
            headers=headers
        )
        if list_response.status_code == 200:
            files = list_response.json()
            deleted_file = next((f for f in files if f.get("id") == file_id), None)
            assert deleted_file is None, f"File should be deleted but still exists"
        
        print("File successfully deleted")
    
    def test_05_upload_invalid_format(self, upload_headers):
        """Test uploading unsupported file format returns error"""
        files = {
            'file': ('test.exe', io.BytesIO(b'fake exe content'), 'application/octet-stream')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/team/knowledge/upload",
            headers=upload_headers,
            files=files
        )
        
        print(f"Invalid upload response status: {response.status_code}")
        print(f"Invalid upload response: {response.text}")
        
        # Should return 400 for unsupported format
        assert response.status_code == 400, f"Should reject unsupported format: {response.status_code}"


class TestTeamConversations:
    """Test team conversations endpoint for export functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_team_conversations(self, headers):
        """Test getting team conversations for export"""
        response = requests.get(
            f"{BASE_URL}/api/team/conversations",
            headers=headers
        )
        
        print(f"Conversations response status: {response.status_code}")
        print(f"Conversations response: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), f"Response should be a list: {type(data)}"
        
        # Each conversation should have required fields for export
        if len(data) > 0:
            conv = data[0]
            print(f"Sample conversation: {conv}")
            # Check expected fields exist
            expected_fields = ["id", "title", "user_name", "user_email", "message_count"]
            for field in expected_fields:
                assert field in conv, f"Conversation missing field: {field}"
        
        print(f"Found {len(data)} conversations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
