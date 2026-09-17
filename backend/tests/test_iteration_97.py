"""
Iteration 97 - Backend API Tests
Testing conversation rename, delete, and folder rename endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestConversationAPIs:
    """Test conversation rename and delete endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_get_conversations(self):
        """Test GET /api/chat/conversations returns list"""
        res = requests.get(f"{BASE_URL}/api/chat/conversations", headers=self.headers)
        assert res.status_code == 200, f"Get conversations failed: {res.text}"
        data = res.json()
        assert isinstance(data, list), "Expected list of conversations"
        print(f"PASS: GET /api/chat/conversations - Found {len(data)} conversations")
        return data
    
    def test_rename_conversation_endpoint(self):
        """Test PUT /api/chat/conversations/{id}/rename with {title}"""
        # First get a conversation
        convs = self.test_get_conversations()
        if len(convs) == 0:
            pytest.skip("No conversations to test rename")
        
        conv_id = convs[0]["id"]
        original_title = convs[0].get("title", "")
        new_title = f"TEST_Renamed_{original_title[:20]}"
        
        # Test rename endpoint
        res = requests.put(
            f"{BASE_URL}/api/chat/conversations/{conv_id}/rename",
            headers=self.headers,
            json={"title": new_title}
        )
        assert res.status_code == 200, f"Rename failed: {res.text}"
        data = res.json()
        print(f"PASS: PUT /api/chat/conversations/{conv_id}/rename - Response: {data}")
        
        # Verify the rename persisted
        verify_res = requests.get(f"{BASE_URL}/api/chat/conversations/{conv_id}", headers=self.headers)
        if verify_res.status_code == 200:
            verify_data = verify_res.json()
            assert verify_data.get("title") == new_title, f"Title not updated: {verify_data.get('title')}"
            print(f"PASS: Verified rename persisted - Title is now '{new_title}'")
        
        # Restore original title
        requests.put(
            f"{BASE_URL}/api/chat/conversations/{conv_id}/rename",
            headers=self.headers,
            json={"title": original_title}
        )
    
    def test_delete_conversation_endpoint(self):
        """Test DELETE /api/chat/conversations/{id}"""
        # First create a test conversation by sending a message
        # For now, just test with an existing conversation if available
        convs = self.test_get_conversations()
        
        # Find a test conversation to delete (one with TEST_ prefix)
        test_conv = next((c for c in convs if c.get("title", "").startswith("TEST_")), None)
        
        if test_conv:
            conv_id = test_conv["id"]
            res = requests.delete(f"{BASE_URL}/api/chat/conversations/{conv_id}", headers=self.headers)
            assert res.status_code in [200, 204], f"Delete failed: {res.text}"
            print(f"PASS: DELETE /api/chat/conversations/{conv_id} - Deleted test conversation")
            
            # Verify deletion
            verify_res = requests.get(f"{BASE_URL}/api/chat/conversations/{conv_id}", headers=self.headers)
            assert verify_res.status_code == 404, f"Conversation still exists after delete"
            print(f"PASS: Verified conversation {conv_id} no longer exists")
        else:
            # Just verify the endpoint exists by checking a non-existent ID
            res = requests.delete(f"{BASE_URL}/api/chat/conversations/non-existent-id", headers=self.headers)
            assert res.status_code in [404, 200, 204], f"Unexpected status: {res.status_code}"
            print(f"PASS: DELETE endpoint exists (returned {res.status_code} for non-existent ID)")


class TestFolderAPIs:
    """Test folder rename endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_get_folders(self):
        """Test GET /api/folders returns list"""
        res = requests.get(f"{BASE_URL}/api/folders", headers=self.headers)
        assert res.status_code == 200, f"Get folders failed: {res.text}"
        data = res.json()
        assert isinstance(data, list), "Expected list of folders"
        print(f"PASS: GET /api/folders - Found {len(data)} folders")
        return data
    
    def test_create_folder(self):
        """Test POST /api/folders to create a test folder"""
        res = requests.post(
            f"{BASE_URL}/api/folders",
            headers=self.headers,
            json={"name": "TEST_Folder_97", "color": "#3182CE"}
        )
        assert res.status_code in [200, 201], f"Create folder failed: {res.text}"
        data = res.json()
        assert "id" in data, "No folder ID returned"
        print(f"PASS: POST /api/folders - Created folder with ID {data['id']}")
        return data
    
    def test_rename_folder_endpoint(self):
        """Test PUT /api/folders/{id} with {name}"""
        # First get or create a folder
        folders = self.test_get_folders()
        
        if len(folders) == 0:
            # Create a test folder
            folder = self.test_create_folder()
            folder_id = folder["id"]
            original_name = folder.get("name", "")
        else:
            folder_id = folders[0]["id"]
            original_name = folders[0].get("name", "")
        
        new_name = f"TEST_Renamed_{original_name[:15]}"
        
        # Test rename endpoint
        res = requests.put(
            f"{BASE_URL}/api/folders/{folder_id}",
            headers=self.headers,
            json={"name": new_name}
        )
        assert res.status_code == 200, f"Rename folder failed: {res.text}"
        data = res.json()
        print(f"PASS: PUT /api/folders/{folder_id} - Response: {data}")
        
        # Verify the rename persisted
        verify_res = requests.get(f"{BASE_URL}/api/folders", headers=self.headers)
        if verify_res.status_code == 200:
            folders_after = verify_res.json()
            renamed_folder = next((f for f in folders_after if f["id"] == folder_id), None)
            if renamed_folder:
                assert renamed_folder.get("name") == new_name, f"Name not updated: {renamed_folder.get('name')}"
                print(f"PASS: Verified folder rename persisted - Name is now '{new_name}'")
        
        # Restore original name
        requests.put(
            f"{BASE_URL}/api/folders/{folder_id}",
            headers=self.headers,
            json={"name": original_name}
        )
    
    def test_delete_folder_endpoint(self):
        """Test DELETE /api/folders/{id}"""
        # Find a test folder to delete
        folders = self.test_get_folders()
        test_folder = next((f for f in folders if f.get("name", "").startswith("TEST_")), None)
        
        if test_folder:
            folder_id = test_folder["id"]
            res = requests.delete(f"{BASE_URL}/api/folders/{folder_id}", headers=self.headers)
            assert res.status_code in [200, 204], f"Delete folder failed: {res.text}"
            print(f"PASS: DELETE /api/folders/{folder_id} - Deleted test folder")
        else:
            print("SKIP: No test folder to delete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
