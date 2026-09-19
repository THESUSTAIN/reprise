"""
Iteration 93 - Vector Memory System & PDF Upload Tests
Tests:
- PDF Upload endpoint (POST /api/chat/upload)
- Vector Memory CRUD (store, search, list, stats, delete)
- Chat streaming endpoint (POST /api/chat/send mode=fast)
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@zayado.net"
TEST_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Verify login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token length: {len(auth_token)}")


class TestPDFUpload:
    """PDF Upload endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_upload_pdf_file(self, auth_token):
        """Test PDF file upload - POST /api/chat/upload"""
        # Create a simple PDF-like content (minimal valid PDF)
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test PDF Content) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
300
%%EOF"""
        
        files = {
            'file': ('test_document.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files, headers=headers)
        
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "No file id in response"
        assert "url" in data, "No url in response"
        assert "name" in data, "No name in response"
        assert data["ext"] == ".pdf", f"Expected .pdf extension, got {data.get('ext')}"
        
        print(f"✓ PDF upload successful: id={data['id']}, url={data['url']}")
        return data
    
    def test_upload_txt_file(self, auth_token):
        """Test TXT file upload"""
        txt_content = b"This is a test text file for Zayado AI assistant."
        
        files = {
            'file': ('test_document.txt', io.BytesIO(txt_content), 'text/plain')
        }
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files, headers=headers)
        
        assert response.status_code == 200, f"Upload failed: {response.status_code}"
        data = response.json()
        assert data["ext"] == ".txt"
        assert "extracted_text" in data
        print(f"✓ TXT upload successful, extracted text length: {len(data.get('extracted_text', ''))}")


class TestVectorMemory:
    """Vector Memory CRUD tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_memory_stats(self, headers):
        """Test GET /api/memory/stats - Get memory statistics"""
        response = requests.get(f"{BASE_URL}/api/memory/stats", headers=headers)
        
        assert response.status_code == 200, f"Stats failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "total_memories" in data, "No total_memories in response"
        assert "categories" in data, "No categories in response"
        assert isinstance(data["total_memories"], int)
        assert isinstance(data["categories"], dict)
        
        print(f"✓ Memory stats: total={data['total_memories']}, categories={data['categories']}")
        return data
    
    def test_memory_list(self, headers):
        """Test GET /api/memory/list - List all memories"""
        response = requests.get(f"{BASE_URL}/api/memory/list?limit=50", headers=headers)
        
        assert response.status_code == 200, f"List failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Memory list: {len(data)} memories found")
        
        # Verify structure of each memory item
        if len(data) > 0:
            mem = data[0]
            assert "id" in mem, "Memory should have id"
            assert "content" in mem, "Memory should have content"
            assert "category" in mem, "Memory should have category"
            print(f"  First memory: id={mem['id']}, category={mem['category']}")
        
        return data
    
    def test_memory_store(self, headers):
        """Test POST /api/memory/store - Store a new memory"""
        test_content = "TEST_ITER93: Mon client principal est une startup fintech basee a Paris specialisee dans les paiements B2B."
        
        payload = {
            "content": test_content,
            "category": "fact",
            "source": "manual"
        }
        
        response = requests.post(f"{BASE_URL}/api/memory/store", json=payload, headers=headers)
        
        assert response.status_code == 200, f"Store failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "id" in data, "No id in response"
        assert data["content"] == test_content, "Content mismatch"
        assert data["category"] == "fact", "Category mismatch"
        assert data["source"] == "manual", "Source mismatch"
        assert "created_at" in data, "No created_at in response"
        
        print(f"✓ Memory stored: id={data['id']}, category={data['category']}")
        return data
    
    def test_memory_search_semantic(self, headers):
        """Test GET /api/memory/search - Semantic search"""
        # Search for something related to the stored memory
        query = "fintech paiement"
        
        response = requests.get(
            f"{BASE_URL}/api/memory/search?q={query}&limit=5&threshold=0.2",
            headers=headers
        )
        
        assert response.status_code == 200, f"Search failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "results" in data, "No results in response"
        assert "query" in data, "No query in response"
        assert "total" in data, "No total in response"
        assert data["query"] == query, "Query mismatch"
        
        print(f"✓ Semantic search for '{query}': {data['total']} results")
        
        # Verify result structure
        if len(data["results"]) > 0:
            result = data["results"][0]
            assert "id" in result, "Result should have id"
            assert "content" in result, "Result should have content"
            assert "score" in result, "Result should have score"
            print(f"  Top result: score={result['score']}, content={result['content'][:50]}...")
        
        return data
    
    def test_memory_delete(self, headers):
        """Test DELETE /api/memory/{id} - Delete a specific memory"""
        # First, create a memory to delete
        payload = {
            "content": "TEST_DELETE_ITER93: This memory will be deleted immediately.",
            "category": "general",
            "source": "manual"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/memory/store", json=payload, headers=headers)
        assert create_response.status_code == 200, f"Create for delete test failed: {create_response.text}"
        memory_id = create_response.json()["id"]
        
        # Now delete it
        delete_response = requests.delete(f"{BASE_URL}/api/memory/{memory_id}", headers=headers)
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.status_code} - {delete_response.text}"
        data = delete_response.json()
        
        assert data.get("ok") == True, "Delete should return ok=True"
        assert data.get("deleted") == memory_id, "Deleted id mismatch"
        
        print(f"✓ Memory deleted: id={memory_id}")
        
        # Verify it's actually deleted by trying to find it in list
        list_response = requests.get(f"{BASE_URL}/api/memory/list?limit=100", headers=headers)
        memories = list_response.json()
        deleted_ids = [m["id"] for m in memories]
        assert memory_id not in deleted_ids, "Deleted memory should not appear in list"
        
        print(f"✓ Verified memory {memory_id} no longer in list")
    
    def test_memory_store_validation(self, headers):
        """Test memory store validation - content too short"""
        payload = {
            "content": "ab",  # Too short (min 3 chars)
            "category": "general"
        }
        
        response = requests.post(f"{BASE_URL}/api/memory/store", json=payload, headers=headers)
        
        # Should fail validation
        assert response.status_code == 422, f"Expected 422 for short content, got {response.status_code}"
        print("✓ Validation works: rejected content < 3 chars")


class TestChatSend:
    """Chat streaming endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_chat_send_fast_mode(self, headers):
        """Test POST /api/chat/send with mode=fast"""
        payload = {
            "message": "Bonjour, dis-moi simplement 'Test OK' en une phrase.",
            "mode": "fast"
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/send", json=payload, headers=headers, stream=True)
        
        assert response.status_code == 200, f"Chat send failed: {response.status_code} - {response.text}"
        
        # Read streaming response
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    full_response += line_str[6:]
        
        assert len(full_response) > 0, "No response content received"
        print(f"✓ Chat send (fast mode) successful, response length: {len(full_response)}")
    
    def test_chat_send_with_conversation_id(self, headers):
        """Test chat send with specific conversation_id"""
        import uuid
        conv_id = str(uuid.uuid4())
        
        payload = {
            "message": "Test avec conversation_id specifique",
            "mode": "fast",
            "conversation_id": conv_id
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/send", json=payload, headers=headers, stream=True)
        
        assert response.status_code == 200, f"Chat send failed: {response.status_code}"
        print(f"✓ Chat send with conversation_id={conv_id[:8]}... successful")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_cleanup_test_memories(self, headers):
        """Clean up TEST_ITER93 prefixed memories"""
        # List all memories
        response = requests.get(f"{BASE_URL}/api/memory/list?limit=100", headers=headers)
        if response.status_code != 200:
            print("Could not list memories for cleanup")
            return
        
        memories = response.json()
        deleted_count = 0
        
        for mem in memories:
            if "TEST_ITER93" in mem.get("content", ""):
                del_response = requests.delete(f"{BASE_URL}/api/memory/{mem['id']}", headers=headers)
                if del_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleanup: deleted {deleted_count} test memories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
