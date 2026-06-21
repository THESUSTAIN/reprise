"""
Iteration 156 - Connections API Tests
Tests for WhatsApp, Telegram, OVH providers (no coming_soon flag)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "paytest@zayado.net"
TEST_PASSWORD = "Test1234!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code}")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestConnectionsProviders:
    """Test /api/connections/providers endpoint."""

    def test_get_providers_returns_200(self, auth_headers):
        """GET /api/connections/providers should return 200."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: GET /api/connections/providers returns 200")

    def test_get_providers_returns_list(self, auth_headers):
        """GET /api/connections/providers should return a list."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        assert isinstance(data, list), "Expected list of providers"
        assert len(data) >= 7, f"Expected at least 7 providers, got {len(data)}"
        print(f"PASS: GET /api/connections/providers returns {len(data)} providers")

    def test_whatsapp_provider_exists_without_coming_soon(self, auth_headers):
        """WhatsApp provider should exist and NOT have coming_soon flag."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        whatsapp = next((p for p in data if p["id"] == "whatsapp"), None)
        
        assert whatsapp is not None, "WhatsApp provider not found"
        assert whatsapp.get("coming_soon") is not True, "WhatsApp should NOT have coming_soon=True"
        assert whatsapp["category"] == "messaging", f"WhatsApp category should be 'messaging', got {whatsapp['category']}"
        print(f"PASS: WhatsApp provider exists without coming_soon flag")

    def test_whatsapp_has_4_fields(self, auth_headers):
        """WhatsApp provider should have 4 fields."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        whatsapp = next((p for p in data if p["id"] == "whatsapp"), None)
        
        assert whatsapp is not None, "WhatsApp provider not found"
        fields = whatsapp.get("fields", [])
        assert len(fields) == 4, f"WhatsApp should have 4 fields, got {len(fields)}"
        
        field_keys = [f["key"] for f in fields]
        expected_keys = ["phone_number_id", "access_token", "verify_token", "business_account_id"]
        for key in expected_keys:
            assert key in field_keys, f"WhatsApp missing field: {key}"
        print(f"PASS: WhatsApp has 4 fields: {field_keys}")

    def test_telegram_provider_exists_without_coming_soon(self, auth_headers):
        """Telegram provider should exist and NOT have coming_soon flag."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        telegram = next((p for p in data if p["id"] == "telegram"), None)
        
        assert telegram is not None, "Telegram provider not found"
        assert telegram.get("coming_soon") is not True, "Telegram should NOT have coming_soon=True"
        assert telegram["category"] == "messaging", f"Telegram category should be 'messaging', got {telegram['category']}"
        print(f"PASS: Telegram provider exists without coming_soon flag")

    def test_telegram_has_3_fields(self, auth_headers):
        """Telegram provider should have 3 fields."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        telegram = next((p for p in data if p["id"] == "telegram"), None)
        
        assert telegram is not None, "Telegram provider not found"
        fields = telegram.get("fields", [])
        assert len(fields) == 3, f"Telegram should have 3 fields, got {len(fields)}"
        
        field_keys = [f["key"] for f in fields]
        expected_keys = ["bot_token", "chat_id", "webhook_url"]
        for key in expected_keys:
            assert key in field_keys, f"Telegram missing field: {key}"
        print(f"PASS: Telegram has 3 fields: {field_keys}")

    def test_ovh_provider_exists_without_coming_soon(self, auth_headers):
        """OVH provider should exist and NOT have coming_soon flag."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        ovh = next((p for p in data if p["id"] == "ovh_phone"), None)
        
        assert ovh is not None, "OVH provider not found"
        assert ovh.get("coming_soon") is not True, "OVH should NOT have coming_soon=True"
        assert ovh["category"] == "phone", f"OVH category should be 'phone', got {ovh['category']}"
        print(f"PASS: OVH provider exists without coming_soon flag")

    def test_ovh_has_5_fields(self, auth_headers):
        """OVH provider should have 5 fields."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        ovh = next((p for p in data if p["id"] == "ovh_phone"), None)
        
        assert ovh is not None, "OVH provider not found"
        fields = ovh.get("fields", [])
        assert len(fields) == 5, f"OVH should have 5 fields, got {len(fields)}"
        
        field_keys = [f["key"] for f in fields]
        expected_keys = ["application_key", "application_secret", "consumer_key", "service_name", "sender"]
        for key in expected_keys:
            assert key in field_keys, f"OVH missing field: {key}"
        print(f"PASS: OVH has 5 fields: {field_keys}")

    def test_categories_are_correct(self, auth_headers):
        """Verify categories: email, messaging, phone."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        
        categories = set(p["category"] for p in data)
        expected_categories = {"email", "messaging", "phone"}
        
        for cat in expected_categories:
            assert cat in categories, f"Missing category: {cat}"
        print(f"PASS: All expected categories present: {categories}")

    def test_messaging_category_has_whatsapp_and_telegram(self, auth_headers):
        """Messaging category should have WhatsApp and Telegram."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        
        messaging_providers = [p for p in data if p["category"] == "messaging"]
        messaging_ids = [p["id"] for p in messaging_providers]
        
        assert "whatsapp" in messaging_ids, "WhatsApp not in messaging category"
        assert "telegram" in messaging_ids, "Telegram not in messaging category"
        print(f"PASS: Messaging category has WhatsApp and Telegram: {messaging_ids}")

    def test_phone_category_has_ovh(self, auth_headers):
        """Phone category should have OVH."""
        response = requests.get(f"{BASE_URL}/api/connections/providers", headers=auth_headers)
        data = response.json()
        
        phone_providers = [p for p in data if p["category"] == "phone"]
        phone_ids = [p["id"] for p in phone_providers]
        
        assert "ovh_phone" in phone_ids, "OVH not in phone category"
        print(f"PASS: Phone category has OVH: {phone_ids}")


class TestConnectionsEndpoint:
    """Test /api/connections endpoint."""

    def test_get_connections_returns_200(self, auth_headers):
        """GET /api/connections should return 200."""
        response = requests.get(f"{BASE_URL}/api/connections", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: GET /api/connections returns 200")

    def test_get_connections_returns_list(self, auth_headers):
        """GET /api/connections should return a list."""
        response = requests.get(f"{BASE_URL}/api/connections", headers=auth_headers)
        data = response.json()
        assert isinstance(data, list), "Expected list of connections"
        print(f"PASS: GET /api/connections returns list with {len(data)} connections")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
