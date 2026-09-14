"""
Test suite for Connections API - Iteration 155
Tests the 'Mes Connexions' dashboard feature for secure service integrations.
Providers: Brevo, SMTP (active), Gmail, Outlook, WhatsApp, Telegram, OVH (coming soon)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@zayado.net"
ADMIN_PASSWORD = "1@Elshaddai1"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code}")


@pytest.fixture
def auth_headers(admin_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestConnectionsProviders:
    """Tests for GET /api/connections/providers endpoint."""

    def test_get_providers_returns_200(self, auth_headers):
        """GET /api/connections/providers returns 200."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        assert response.status_code == 200

    def test_get_providers_returns_7_providers(self, auth_headers):
        """GET /api/connections/providers returns exactly 7 providers."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        assert len(data) == 7, f"Expected 7 providers, got {len(data)}"

    def test_providers_have_required_fields(self, auth_headers):
        """Each provider has required fields: id, name, description, icon, color, category."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        required_fields = ["id", "name", "description", "icon", "color", "category"]
        for provider in data:
            for field in required_fields:
                assert field in provider, f"Provider {provider.get('id')} missing field: {field}"

    def test_brevo_provider_exists_with_correct_fields(self, auth_headers):
        """Brevo provider exists with correct configuration fields."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        brevo = next((p for p in data if p["id"] == "brevo"), None)
        assert brevo is not None, "Brevo provider not found"
        assert brevo["category"] == "email"
        assert "coming_soon" not in brevo or brevo.get("coming_soon") is False
        # Check fields
        field_keys = [f["key"] for f in brevo.get("fields", [])]
        assert "api_key" in field_keys, "Brevo missing api_key field"
        assert "sender_email" in field_keys, "Brevo missing sender_email field"
        assert "sender_name" in field_keys, "Brevo missing sender_name field"

    def test_smtp_provider_exists_with_correct_fields(self, auth_headers):
        """SMTP provider exists with correct configuration fields."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        smtp = next((p for p in data if p["id"] == "smtp"), None)
        assert smtp is not None, "SMTP provider not found"
        assert smtp["category"] == "email"
        assert "coming_soon" not in smtp or smtp.get("coming_soon") is False
        # Check fields
        field_keys = [f["key"] for f in smtp.get("fields", [])]
        assert "host" in field_keys, "SMTP missing host field"
        assert "port" in field_keys, "SMTP missing port field"
        assert "username" in field_keys, "SMTP missing username field"
        assert "password" in field_keys, "SMTP missing password field"
        assert "sender_email" in field_keys, "SMTP missing sender_email field"
        assert "use_tls" in field_keys, "SMTP missing use_tls field"

    def test_coming_soon_providers_marked_correctly(self, auth_headers):
        """Gmail, Outlook, WhatsApp, Telegram, OVH are marked as coming_soon."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        coming_soon_ids = ["gmail", "outlook", "whatsapp", "telegram", "ovh_phone"]
        for provider_id in coming_soon_ids:
            provider = next((p for p in data if p["id"] == provider_id), None)
            assert provider is not None, f"Provider {provider_id} not found"
            assert provider.get("coming_soon") is True, f"Provider {provider_id} should be coming_soon"

    def test_categories_are_correct(self, auth_headers):
        """Providers are in correct categories: email, messaging, phone."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        
        email_providers = [p for p in data if p["category"] == "email"]
        messaging_providers = [p for p in data if p["category"] == "messaging"]
        phone_providers = [p for p in data if p["category"] == "phone"]
        
        assert len(email_providers) == 4, f"Expected 4 email providers, got {len(email_providers)}"
        assert len(messaging_providers) == 2, f"Expected 2 messaging providers, got {len(messaging_providers)}"
        assert len(phone_providers) == 1, f"Expected 1 phone provider, got {len(phone_providers)}"


class TestConnectionsList:
    """Tests for GET /api/connections endpoint."""

    def test_get_connections_returns_200(self, auth_headers):
        """GET /api/connections returns 200."""
        response = requests.get(f"{BASE_URL}/api/connections", headers=auth_headers)
        assert response.status_code == 200

    def test_get_connections_returns_list(self, auth_headers):
        """GET /api/connections returns a list."""
        response = requests.get(f"{BASE_URL}/api/connections", headers=auth_headers)
        data = response.json()
        assert isinstance(data, list)


class TestConnectionsCRUD:
    """Tests for connections CRUD operations."""

    def test_create_brevo_connection(self, auth_headers):
        """POST /api/connections creates Brevo connection with auto-test."""
        response = requests.post(
            f"{BASE_URL}/api/connections",
            headers=auth_headers,
            json={
                "provider": "brevo",
                "label": "TEST_Brevo_Connection_155",
                "credentials": {
                    "api_key": "test-fake-api-key-155",
                    "sender_email": "test155@example.com",
                    "sender_name": "Test Sender 155"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "brevo"
        assert data["label"] == "TEST_Brevo_Connection_155"
        assert "test_result" in data, "Auto-test result should be included"
        assert "credentials_masked" in data, "Credentials should be masked"
        # Cleanup
        if data.get("id"):
            requests.delete(f"{BASE_URL}/api/connections/{data['id']}", headers=auth_headers)

    def test_create_smtp_connection(self, auth_headers):
        """POST /api/connections creates SMTP connection."""
        response = requests.post(
            f"{BASE_URL}/api/connections",
            headers=auth_headers,
            json={
                "provider": "smtp",
                "label": "TEST_SMTP_Connection_155",
                "credentials": {
                    "host": "smtp.test.com",
                    "port": 587,
                    "username": "testuser",
                    "password": "testpass",
                    "sender_email": "smtp155@example.com",
                    "use_tls": True
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "smtp"
        assert data["label"] == "TEST_SMTP_Connection_155"
        # Cleanup
        if data.get("id"):
            requests.delete(f"{BASE_URL}/api/connections/{data['id']}", headers=auth_headers)

    def test_create_coming_soon_provider_fails(self, auth_headers):
        """POST /api/connections with coming_soon provider returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/connections",
            headers=auth_headers,
            json={
                "provider": "gmail",
                "label": "Test Gmail",
                "credentials": {}
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "prochainement" in data.get("detail", "").lower() or "bientot" in data.get("detail", "").lower()

    def test_create_unknown_provider_fails(self, auth_headers):
        """POST /api/connections with unknown provider returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/connections",
            headers=auth_headers,
            json={
                "provider": "unknown_provider",
                "label": "Test Unknown",
                "credentials": {}
            }
        )
        assert response.status_code == 400

    def test_create_brevo_missing_required_field_fails(self, auth_headers):
        """POST /api/connections with missing required field returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/connections",
            headers=auth_headers,
            json={
                "provider": "brevo",
                "label": "Test Brevo Missing Field",
                "credentials": {
                    "api_key": "test-key"
                    # Missing sender_email which is required
                }
            }
        )
        assert response.status_code == 400

    def test_delete_connection(self, auth_headers):
        """DELETE /api/connections/:id revokes connection."""
        # Create a connection first
        create_response = requests.post(
            f"{BASE_URL}/api/connections",
            headers=auth_headers,
            json={
                "provider": "brevo",
                "label": "TEST_Delete_Connection_155",
                "credentials": {
                    "api_key": "test-delete-key",
                    "sender_email": "delete155@example.com"
                }
            }
        )
        assert create_response.status_code == 200
        conn_id = create_response.json()["id"]
        
        # Delete the connection
        delete_response = requests.delete(f"{BASE_URL}/api/connections/{conn_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["status"] == "revoked"
        
        # Verify it's no longer in the list
        list_response = requests.get(f"{BASE_URL}/api/connections", headers=auth_headers)
        connections = list_response.json()
        assert not any(c["id"] == conn_id for c in connections), "Deleted connection should not appear in list"

    def test_credentials_are_masked(self, auth_headers):
        """Connection credentials are masked in response."""
        response = requests.post(
            f"{BASE_URL}/api/connections",
            headers=auth_headers,
            json={
                "provider": "brevo",
                "label": "TEST_Masked_Credentials_155",
                "credentials": {
                    "api_key": "super-secret-api-key-12345",
                    "sender_email": "masked155@example.com"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        masked_key = data["credentials_masked"]["api_key"]
        assert "****" in masked_key, "API key should be masked"
        assert "super-secret-api-key-12345" not in masked_key, "Full API key should not be visible"
        # Cleanup
        if data.get("id"):
            requests.delete(f"{BASE_URL}/api/connections/{data['id']}", headers=auth_headers)


class TestConnectionsAuth:
    """Tests for authentication requirements."""

    def test_get_providers_requires_auth(self):
        """GET /api/connections/providers requires authentication."""
        response = requests.get(f"{BASE_URL}/api/connections/providers")
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"

    def test_get_connections_requires_auth(self):
        """GET /api/connections requires authentication."""
        response = requests.get(f"{BASE_URL}/api/connections")
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"

    def test_create_connection_requires_auth(self):
        """POST /api/connections requires authentication."""
        response = requests.post(
            f"{BASE_URL}/api/connections",
            json={"provider": "brevo", "credentials": {}}
        )
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
