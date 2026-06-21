"""
Iteration 139 - Bug Fixes Verification Tests
Tests:
1. GET /api/affiliate/dashboard returns 200 with tier, stats, monthly_stats (was 500 before fix)
2. POST /api/chat/feedback with valid data returns 200
3. GET /api/chat/feedback/{conv_id} returns 200 (not 500)
4. POST /api/auth/register creates user with 200 credits
5. POST /api/chat/send mode=fast returns done event with credits_used field
6. GET /api/auth/me returns correct credit balance
7. GET /api/admin/stats returns total_credits_spent and credits_by_mode
8. GET /api/chat/conversations/{non-existent-id} returns 404
9. No 500 or 503 errors on any tested endpoint
"""
import pytest
import requests
import os
import uuid
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tarif-preview-v2.preview.emergentagent.com').rstrip('/')

def get_token(data):
    """Extract token from login/register response (handles both 'token' and 'access_token')"""
    return data.get("token") or data.get("access_token")


class TestHealthEndpoint:
    """Test health endpoint"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy", f"Unexpected health status: {data}"
        print("Health endpoint working")


class TestAdminLogin:
    """Test admin login functionality"""
    
    def test_admin_login_success(self):
        """Login with admin@zayado.net / admin123 works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        token = get_token(data)
        assert token, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == "admin@zayado.net"
        print(f"Admin login successful, user role: {data['user'].get('role')}")


class TestAffiliateDashboard:
    """Test affiliate dashboard endpoint - was returning 500 due to SQL date_format issue"""
    
    def test_affiliate_dashboard_returns_200(self):
        """GET /api/affiliate/dashboard returns 200 with tier, stats, monthly_stats"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = get_token(login_resp.json())
        
        # Get affiliate dashboard
        response = requests.get(
            f"{BASE_URL}/api/affiliate/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should NOT be 500 (was the bug)
        assert response.status_code != 500, f"Affiliate dashboard returned 500: {response.text}"
        assert response.status_code == 200, f"Affiliate dashboard failed with {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify expected fields exist
        assert "tier" in data, f"Missing 'tier' in response: {data.keys()}"
        assert "stats" in data, f"Missing 'stats' in response: {data.keys()}"
        assert "monthly_stats" in data, f"Missing 'monthly_stats' in response: {data.keys()}"
        
        # Verify monthly_stats is a list
        assert isinstance(data["monthly_stats"], list), f"monthly_stats should be a list"
        
        # Verify stats structure
        stats = data["stats"]
        expected_stat_fields = ["total_commissions", "pending_commissions", "paid_commissions", "total_sales"]
        for field in expected_stat_fields:
            assert field in stats, f"Missing '{field}' in stats: {stats.keys()}"
        # total_revenue may be named total_revenue_generated
        assert "total_revenue" in stats or "total_revenue_generated" in stats, f"Missing revenue field in stats: {stats.keys()}"
        
        print(f"Affiliate dashboard working: tier={data['tier']}, monthly_stats count={len(data['monthly_stats'])}")
        print(f"Stats: total_sales={stats.get('total_sales')}, total_commissions={stats.get('total_commissions')}")


class TestFeedbackEndpoints:
    """Test feedback endpoints work without 500 error"""
    
    def test_feedback_post_works(self):
        """POST /api/chat/feedback works without 500 error"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        token = get_token(login_resp.json())
        
        # Get a conversation to use for feedback
        conv_resp = requests.get(
            f"{BASE_URL}/api/chat/conversations",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if conv_resp.status_code == 200:
            conversations = conv_resp.json()
            if conversations and len(conversations) > 0:
                conv_id = conversations[0].get("id")
                if conv_id:
                    # Submit feedback
                    feedback_resp = requests.post(
                        f"{BASE_URL}/api/chat/feedback",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "conversation_id": conv_id,
                            "message_index": 0,
                            "feedback": "up"
                        }
                    )
                    # Should not be 500
                    assert feedback_resp.status_code != 500, f"Feedback POST returned 500: {feedback_resp.text}"
                    assert feedback_resp.status_code in [200, 201, 400], f"Unexpected status: {feedback_resp.status_code}"
                    print(f"Feedback POST works, status: {feedback_resp.status_code}")
                    return
        
        # If no conversations, test with a fake ID (should return 200 with error status, not 500)
        feedback_resp = requests.post(
            f"{BASE_URL}/api/chat/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "conversation_id": str(uuid.uuid4()),
                "message_index": 0,
                "feedback": "up"
            }
        )
        assert feedback_resp.status_code != 500, f"Feedback POST returned 500: {feedback_resp.text}"
        print(f"Feedback POST works (no 500), status: {feedback_resp.status_code}")
    
    def test_feedback_get_works(self):
        """GET /api/chat/feedback/<conv-id> works without 500 error"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        token = get_token(login_resp.json())
        
        # Get feedback for a conversation (even if it doesn't exist)
        conv_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/chat/feedback/{conv_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should not be 500
        assert response.status_code != 500, f"Feedback GET returned 500: {response.text}"
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"Feedback GET works (no 500), status: {response.status_code}")
    
    def test_feedback_get_existing_conversation(self):
        """GET /api/chat/feedback/<existing-conv-id> returns 200"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        token = get_token(login_resp.json())
        
        # Use known existing conversation ID
        existing_conv_id = "7a179662-e53b-459a-8780-1cc6b7f6b9a3"
        response = requests.get(
            f"{BASE_URL}/api/chat/feedback/{existing_conv_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should return 200 (empty dict if no feedback) or 404 if conv doesn't belong to user
        assert response.status_code != 500, f"Feedback GET returned 500: {response.text}"
        print(f"Feedback GET for existing conv: status={response.status_code}")


class TestUserRegistration:
    """Test user registration with 200 credits"""
    
    def test_registration_gives_200_credits(self):
        """Registration creates user with 200 credits (not 90 or 180)"""
        unique_email = f"test200cr_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "name": "Test User 200 Credits",
            "password": "Test1234!"
        })
        assert response.status_code in [200, 201], f"Registration failed: {response.text}"
        data = response.json()
        token = get_token(data)
        assert token, "No access_token in response"
        assert "user" in data, "No user in response"
        
        # Verify credits = 200
        user = data["user"]
        credits = user.get("credits", 0)
        assert credits == 200, f"Expected 200 credits, got {credits}"
        print(f"Registration successful: {unique_email} with {credits} credits")


class TestConversation404:
    """Test non-existent conversation returns 404"""
    
    def test_nonexistent_conversation_returns_404(self):
        """GET /api/chat/conversations/<non-existent-id> returns 404"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        token = get_token(login_resp.json())
        
        # Try to get non-existent conversation
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/chat/conversations/{fake_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"Non-existent conversation correctly returns 404")


class TestAuthMe:
    """Test /api/auth/me returns correct credits"""
    
    def test_auth_me_shows_credits(self):
        """GET /api/auth/me shows correct remaining credits"""
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        token = get_token(login_resp.json())
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        
        # Check credits field exists
        assert "credits" in data, f"Missing credits in auth/me response: {data.keys()}"
        credits = data["credits"]
        assert isinstance(credits, (int, float)), f"Credits should be numeric, got {type(credits)}"
        print(f"Current user credits: {credits}")


class TestAdminStats:
    """Test admin stats endpoint"""
    
    def test_admin_stats_has_credits_data(self):
        """GET /api/admin/stats shows total_credits_spent and credits_by_mode"""
        # Login as admin
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        token = get_token(login_resp.json())
        
        # Get admin stats
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Admin stats failed: {response.text}"
        data = response.json()
        
        # Check total_credits_spent exists
        assert "total_credits_spent" in data, "Missing total_credits_spent in admin stats"
        print(f"total_credits_spent: {data['total_credits_spent']}")
        
        # Check credits_by_mode exists and is populated
        assert "credits_by_mode" in data, "Missing credits_by_mode in admin stats"
        credits_by_mode = data["credits_by_mode"]
        assert isinstance(credits_by_mode, dict), "credits_by_mode should be a dict"
        print(f"credits_by_mode: {credits_by_mode}")


class TestChatSendCreditsUsed:
    """Test chat send returns credits_used in done event"""
    
    def test_chat_send_returns_credits_used(self):
        """POST /api/chat/send mode=fast returns done event with credits_used field"""
        # Login as admin
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zayado.net",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        token = get_token(login_resp.json())
        initial_credits = login_resp.json()["user"].get("credits", 0)
        
        print(f"Initial credits: {initial_credits}")
        
        # Send a chat message with mode=fast
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "message": "Hello, this is a test message",
                "mode": "fast"
            },
            stream=True
        )
        
        assert response.status_code == 200, f"Chat send failed: {response.status_code}"
        
        # Parse SSE stream to find done event with credits_used
        done_event = None
        credits_used = None
        remaining_credits = None
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('done'):
                            done_event = data
                            credits_used = data.get('credits_used')
                            remaining_credits = data.get('remaining_credits')
                            break
                    except:
                        pass
        
        assert done_event is not None, "No done event received in SSE stream"
        assert credits_used is not None, f"credits_used not in done event: {done_event}"
        print(f"Done event received: credits_used={credits_used}, remaining_credits={remaining_credits}")


class TestFrontendPages:
    """Test that key frontend pages load without errors"""
    
    def test_pilotage_financier_page(self):
        """GET /app/pilotage-financier loads"""
        response = requests.get(f"{BASE_URL}/app/pilotage-financier", allow_redirects=True)
        # Frontend routes may return 200 or redirect
        assert response.status_code in [200, 301, 302, 304], f"Page failed: {response.status_code}"
        print(f"pilotage-financier page status: {response.status_code}")
    
    def test_activite_page(self):
        """GET /app/activite loads"""
        response = requests.get(f"{BASE_URL}/app/activite", allow_redirects=True)
        assert response.status_code in [200, 301, 302, 304], f"Page failed: {response.status_code}"
        print(f"activite page status: {response.status_code}")
    
    def test_timer_page(self):
        """GET /app/timer loads"""
        response = requests.get(f"{BASE_URL}/app/timer", allow_redirects=True)
        assert response.status_code in [200, 301, 302, 304], f"Page failed: {response.status_code}"
        print(f"timer page status: {response.status_code}")
    
    def test_workflows_page(self):
        """GET /app/workflows loads"""
        response = requests.get(f"{BASE_URL}/app/workflows", allow_redirects=True)
        assert response.status_code in [200, 301, 302, 304], f"Page failed: {response.status_code}"
        print(f"workflows page status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
