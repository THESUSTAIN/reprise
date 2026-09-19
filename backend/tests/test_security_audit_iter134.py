"""
Test suite for iteration 134 - Security and logic bug fixes from 200-item audit.
Tests the key fixes applied:
1) Email normalization on login/register
2) Password length validation (>72 chars rejected)
3) Finance entry validation (negative amounts, invalid types)
4) Settings protection against internal key overwrite
5) OpenAI key empty validation
6) Health endpoint
7) Chat conversations endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://admin-panel-416.preview.emergentagent.com"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for admin user - module level fixture"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Could not authenticate")


class TestHealthEndpoint:
    """Test /api/health endpoint"""
    
    def test_health_returns_healthy(self):
        """Health endpoint should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "healthy", f"Expected healthy, got {data}"
        print("PASS: /api/health returns healthy")


class TestEmailNormalization:
    """Test email normalization on login (case insensitive)"""
    
    def test_login_lowercase_email(self):
        """Login with lowercase email should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data, "Expected access_token in response"
        assert "user" in data, "Expected user in response"
        print("PASS: Login with lowercase email works")
    
    def test_login_uppercase_email(self):
        """Login with UPPERCASE email should work (case insensitive)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ADMIN@ZAYADO.NET",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data, "Expected access_token in response"
        print("PASS: Login with UPPERCASE email works (case insensitive)")
    
    def test_login_mixed_case_email(self):
        """Login with MixedCase email should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "Admin@Zayado.Net",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Login with MixedCase email works")


class TestPasswordValidation:
    """Test password length validation on register"""
    
    def test_register_rejects_password_over_72_chars(self):
        """Register should reject passwords > 72 characters (bcrypt truncation warning)"""
        long_password = "a" * 73  # 73 characters
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_long_pwd_{os.urandom(4).hex()}@test.com",
            "name": "Test User",
            "password": long_password
        })
        # Should return 400 with error about password length
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "72" in str(data.get("detail", "")), f"Expected error about 72 chars, got: {data}"
        print("PASS: Register rejects passwords > 72 chars")
    
    def test_register_rejects_duplicate_email(self):
        """Register should reject duplicate email"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "name": "Duplicate Test",
            "password": "testpass123"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        # French error message expected
        assert "email" in str(data.get("detail", "")).lower() or "enregistre" in str(data.get("detail", "")).lower(), f"Expected duplicate email error, got: {data}"
        print("PASS: Register rejects duplicate email")


class TestFinanceEntryValidation:
    """Test finance entry validation (negative amounts, invalid types)"""
    
    def test_finance_entry_rejects_negative_amount(self, auth_token):
        """Finance entry should reject negative amounts"""
        response = requests.post(
            f"{BASE_URL}/api/finance/entry",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "revenu",
                "label": "Test negative",
                "amount": -100,
                "category": "autre"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "negatif" in str(data.get("detail", "")).lower(), f"Expected negative amount error, got: {data}"
        print("PASS: Finance entry rejects negative amounts")
    
    def test_finance_entry_rejects_invalid_type(self, auth_token):
        """Finance entry should reject invalid type (not 'revenu' or 'depense')"""
        response = requests.post(
            f"{BASE_URL}/api/finance/entry",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "invalid_type",
                "label": "Test invalid type",
                "amount": 100,
                "category": "autre"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "revenu" in str(data.get("detail", "")).lower() or "depense" in str(data.get("detail", "")).lower(), f"Expected type validation error, got: {data}"
        print("PASS: Finance entry rejects invalid type")
    
    def test_finance_entry_accepts_valid_revenu(self, auth_token):
        """Finance entry should accept valid 'revenu' type"""
        response = requests.post(
            f"{BASE_URL}/api/finance/entry",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "revenu",
                "label": "TEST_valid_revenu",
                "amount": 100.50,
                "category": "autre"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status ok, got: {data}"
        print("PASS: Finance entry accepts valid 'revenu' type")
    
    def test_finance_entry_accepts_valid_depense(self, auth_token):
        """Finance entry should accept valid 'depense' type"""
        response = requests.post(
            f"{BASE_URL}/api/finance/entry",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "depense",
                "label": "TEST_valid_depense",
                "amount": 50.25,
                "category": "autre"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status ok, got: {data}"
        print("PASS: Finance entry accepts valid 'depense' type")


class TestSettingsProtection:
    """Test settings protection against internal key overwrite"""
    
    def test_settings_protects_internal_keys(self, auth_token):
        """Settings endpoint should not allow overwriting protected internal keys"""
        # Try to overwrite protected keys like pending_2fa_code, last_reset_jti
        response = requests.put(
            f"{BASE_URL}/api/auth/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "pending_2fa_code": "123456",
                "last_reset_jti": "malicious_jti",
                "two_factor_enabled": True,
                "theme": "dark"  # This should be allowed
            }
        )
        # Should succeed but protected keys should be ignored
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the protected keys were not set by checking /me
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        settings = user_data.get("settings", {})
        # Protected keys should NOT be set to our malicious values
        assert settings.get("pending_2fa_code") != "123456", "Protected key pending_2fa_code was overwritten!"
        assert settings.get("last_reset_jti") != "malicious_jti", "Protected key last_reset_jti was overwritten!"
        print("PASS: Settings protects internal keys from overwrite")


class TestOpenAIKeyValidation:
    """Test OpenAI key empty validation"""
    
    def test_openai_key_rejects_empty(self, auth_token):
        """OpenAI key endpoint should reject empty key"""
        response = requests.put(
            f"{BASE_URL}/api/auth/openai-key",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"key": ""}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "requise" in str(data.get("detail", "")).lower() or "cle" in str(data.get("detail", "")).lower(), f"Expected empty key error, got: {data}"
        print("PASS: OpenAI key endpoint rejects empty key")
    
    def test_openai_key_rejects_whitespace_only(self, auth_token):
        """OpenAI key endpoint should reject whitespace-only key"""
        response = requests.put(
            f"{BASE_URL}/api/auth/openai-key",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"key": "   "}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("PASS: OpenAI key endpoint rejects whitespace-only key")


class TestChatConversations:
    """Test chat conversations endpoint"""
    
    def test_conversations_returns_list(self, auth_token):
        """Conversations endpoint should return list for authenticated user"""
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASS: /api/chat/conversations returns list ({len(data)} conversations)")
    
    def test_conversations_requires_auth(self):
        """Conversations endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/chat/conversations")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: /api/chat/conversations requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
