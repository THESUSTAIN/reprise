#!/usr/bin/env python3
"""
ZAYADO Backend API Test Suite
Tests all critical endpoints for the demo backend
"""
import requests
import json
import sys
from typing import Dict, Any

# Use the production URL from frontend/.env
BASE_URL = "https://chat-hub-preview-2.preview.emergentagent.com/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")
    print()

def test_health():
    """Test 1: GET /api/health"""
    print(f"{Colors.BLUE}Test 1: GET /api/health{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            data.get("status") == "ok" and
            data.get("mode") == "demo" and
            "time" in data
        )
        
        details = f"Status: {response.status_code}, Response: {json.dumps(data, indent=2)}"
        print_test("Health endpoint", passed, details)
        return passed
    except Exception as e:
        print_test("Health endpoint", False, f"Error: {str(e)}")
        return False

def test_demo_login():
    """Test 2: POST /api/auth/demo-login"""
    print(f"{Colors.BLUE}Test 2: POST /api/auth/demo-login{Colors.END}")
    try:
        payload = {"email": "thomas@zayado.net"}
        response = requests.post(f"{BASE_URL}/auth/demo-login", json=payload, timeout=10)
        data = response.json()
        
        user = data.get("user", {})
        passed = (
            response.status_code == 200 and
            "access_token" in data and
            data.get("token_type") == "bearer" and
            user.get("onboarding_done") == True and
            user.get("email") == "thomas@zayado.net"
        )
        
        details = f"Status: {response.status_code}\n"
        details += f"  Token: {data.get('access_token', 'N/A')}\n"
        details += f"  User email: {user.get('email', 'N/A')}\n"
        details += f"  Onboarding done: {user.get('onboarding_done', 'N/A')}"
        
        print_test("Demo login", passed, details)
        return passed, data.get("access_token")
    except Exception as e:
        print_test("Demo login", False, f"Error: {str(e)}")
        return False, None

def test_auth_me_with_token(token: str):
    """Test 3a: GET /api/auth/me with Authorization header"""
    print(f"{Colors.BLUE}Test 3a: GET /api/auth/me (with token){Colors.END}")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            "email" in data and
            "id" in data
        )
        
        details = f"Status: {response.status_code}\n"
        details += f"  User ID: {data.get('id', 'N/A')}\n"
        details += f"  Email: {data.get('email', 'N/A')}"
        
        print_test("Auth /me with token", passed, details)
        return passed
    except Exception as e:
        print_test("Auth /me with token", False, f"Error: {str(e)}")
        return False

def test_auth_me_without_token():
    """Test 3b: GET /api/auth/me without Authorization header"""
    print(f"{Colors.BLUE}Test 3b: GET /api/auth/me (without token){Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/auth/me", timeout=10)
        
        passed = response.status_code == 401
        
        details = f"Status: {response.status_code} (expected 401)"
        
        print_test("Auth /me without token (should fail)", passed, details)
        return passed
    except Exception as e:
        print_test("Auth /me without token", False, f"Error: {str(e)}")
        return False

def test_ai_chat_initial():
    """Test 4a: POST /api/growth/copilote - Initial message with real AI"""
    print(f"{Colors.BLUE}Test 4a: POST /api/growth/copilote (initial message){Colors.END}")
    try:
        payload = {
            "message": "Donne-moi 2 priorites simples pour un solopreneur aujourdhui, reponse tres courte.",
            "history": []
        }
        response = requests.post(f"{BASE_URL}/growth/copilote?user_id=demo", json=payload, timeout=60)
        data = response.json()
        
        reply = data.get("reply", "")
        
        # Check that it's NOT a fallback message
        is_fallback = (
            "Chat en mode démo — la clé Mammouth n'est pas configurée." in reply or
            "Le service IA est momentanément indisponible." in reply or
            "Le service IA a rencontré une erreur réseau." in reply
        )
        
        passed = (
            response.status_code == 200 and
            reply and
            len(reply) > 10 and
            not is_fallback
        )
        
        details = f"Status: {response.status_code}\n"
        details += f"  Reply length: {len(reply)} chars\n"
        details += f"  Is fallback: {is_fallback}\n"
        details += f"  Reply preview: {reply[:200]}..."
        
        print_test("AI Chat - Initial message (real AI)", passed, details)
        return passed, reply
    except Exception as e:
        print_test("AI Chat - Initial message", False, f"Error: {str(e)}")
        return False, None

def test_ai_chat_followup(previous_reply: str):
    """Test 4b: POST /api/growth/copilote - Follow-up message with history"""
    print(f"{Colors.BLUE}Test 4b: POST /api/growth/copilote (follow-up with history){Colors.END}")
    try:
        payload = {
            "message": "Reformule en une seule phrase.",
            "history": [
                {"role": "user", "content": "Donne-moi 2 priorites simples pour un solopreneur aujourdhui"},
                {"role": "assistant", "content": previous_reply[:100]}  # Use actual previous reply
            ]
        }
        response = requests.post(f"{BASE_URL}/growth/copilote?user_id=demo", json=payload, timeout=60)
        data = response.json()
        
        reply = data.get("reply", "")
        
        # Check that it's NOT a fallback message
        is_fallback = (
            "Chat en mode démo — la clé Mammouth n'est pas configurée." in reply or
            "Le service IA est momentanément indisponible." in reply or
            "Le service IA a rencontré une erreur réseau." in reply
        )
        
        passed = (
            response.status_code == 200 and
            reply and
            len(reply) > 5 and
            not is_fallback
        )
        
        details = f"Status: {response.status_code}\n"
        details += f"  Reply length: {len(reply)} chars\n"
        details += f"  Is fallback: {is_fallback}\n"
        details += f"  Reply preview: {reply[:200]}..."
        
        print_test("AI Chat - Follow-up with history (real AI)", passed, details)
        return passed
    except Exception as e:
        print_test("AI Chat - Follow-up", False, f"Error: {str(e)}")
        return False

def test_chat_messages():
    """Test 5: GET /api/chat/messages"""
    print(f"{Colors.BLUE}Test 5: GET /api/chat/messages{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/chat/messages", timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            isinstance(data, list)
        )
        
        details = f"Status: {response.status_code}\n"
        details += f"  Response type: {type(data).__name__}\n"
        details += f"  Is array: {isinstance(data, list)}"
        
        print_test("Chat messages endpoint", passed, details)
        return passed
    except Exception as e:
        print_test("Chat messages endpoint", False, f"Error: {str(e)}")
        return False

def test_dashboard_summary():
    """Test 6: GET /api/dashboard/summary"""
    print(f"{Colors.BLUE}Test 6: GET /api/dashboard/summary{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/dashboard/summary", timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            (isinstance(data, list) or isinstance(data, dict))
        )
        
        details = f"Status: {response.status_code}\n"
        details += f"  Response type: {type(data).__name__}"
        
        print_test("Dashboard summary endpoint", passed, details)
        return passed
    except Exception as e:
        print_test("Dashboard summary endpoint", False, f"Error: {str(e)}")
        return False

def main():
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}ZAYADO Backend API Test Suite{Colors.END}")
    print(f"{Colors.YELLOW}Testing against: {BASE_URL}{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")
    
    results = []
    
    # Test 1: Health check
    results.append(test_health())
    
    # Test 2: Demo login
    login_passed, token = test_demo_login()
    results.append(login_passed)
    
    # Test 3: Auth /me
    if token:
        results.append(test_auth_me_with_token(token))
    else:
        print(f"{Colors.RED}Skipping auth/me with token test (no token available){Colors.END}\n")
        results.append(False)
    
    results.append(test_auth_me_without_token())
    
    # Test 4: AI Chat (MOST IMPORTANT)
    ai_passed, ai_reply = test_ai_chat_initial()
    results.append(ai_passed)
    
    if ai_passed and ai_reply:
        results.append(test_ai_chat_followup(ai_reply))
    else:
        print(f"{Colors.RED}Skipping follow-up AI chat test (initial test failed){Colors.END}\n")
        results.append(False)
    
    # Test 5: Chat messages
    results.append(test_chat_messages())
    
    # Test 6: Dashboard summary
    results.append(test_dashboard_summary())
    
    # Summary
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Test Summary{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}")
    passed = sum(results)
    total = len(results)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{Colors.GREEN}All tests passed! ✓{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}{total - passed} test(s) failed ✗{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
