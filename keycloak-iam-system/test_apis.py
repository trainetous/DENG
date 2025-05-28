#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Keycloak IAM System
This script tests all API endpoints with and without valid tokens
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
FLASK_URL = "http://localhost:5000"
KEYCLOAK_CREDENTIALS = {
    "admin": {"username": "admin", "password": "adminpassword"},
    "testuser": {"username": "testuser", "password": "testpassword"}
}
SIMPLE_JWT_CREDENTIALS = {"username": "admin", "password": "password"}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.keycloak_tokens = {}
        self.simple_jwt_token = None
        self.test_results = []
        
    def log(self, message, color=Colors.END):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {message}{Colors.END}")
        
    def log_success(self, message):
        self.log(f"✅ {message}", Colors.GREEN)
        
    def log_error(self, message):
        self.log(f"❌ {message}", Colors.RED)
        
    def log_warning(self, message):
        self.log(f"⚠️  {message}", Colors.YELLOW)
        
    def log_info(self, message):
        self.log(f"ℹ️  {message}", Colors.BLUE)
        
    def record_test(self, test_name, passed, details=""):
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
    def test_public_api(self):
        """Test public API endpoint"""
        self.log_info("Testing public API endpoint...")
        
        try:
            response = self.session.get(f"{FLASK_URL}/api/public")
            if response.status_code == 200:
                data = response.json()
                self.log_success(f"Public API: {data['message']}")
                self.record_test("Public API", True, "Accessible without authentication")
                return True
            else:
                self.log_error(f"Public API failed: HTTP {response.status_code}")
                self.record_test("Public API", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"Public API error: {e}")
            self.record_test("Public API", False, str(e))
            return False
            
    def get_keycloak_token(self, user_type="admin"):
        """Get Keycloak token for specified user"""
        if user_type in self.keycloak_tokens:
            return self.keycloak_tokens[user_type]
            
        self.log_info(f"Getting Keycloak token for {user_type}...")
        
        try:
            credentials = KEYCLOAK_CREDENTIALS[user_type]
            response = self.session.post(
                f"{FLASK_URL}/api/keycloak-login",
                json=credentials,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data['access_token']
                self.keycloak_tokens[user_type] = token
                self.log_success(f"Keycloak token obtained for {user_type}")
                self.record_test(f"Keycloak Login ({user_type})", True, f"User: {data['user']['username']}")
                return token
            else:
                self.log_error(f"Keycloak login failed for {user_type}: HTTP {response.status_code}")
                self.record_test(f"Keycloak Login ({user_type})", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_error(f"Keycloak login error for {user_type}: {e}")
            self.record_test(f"Keycloak Login ({user_type})", False, str(e))
            return None
            
    def get_simple_jwt_token(self):
        """Get simple JWT token"""
        if self.simple_jwt_token:
            return self.simple_jwt_token
            
        self.log_info("Getting simple JWT token...")
        
        try:
            response = self.session.post(
                f"{FLASK_URL}/api/login",
                json=SIMPLE_JWT_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.simple_jwt_token = data['token']
                self.log_success("Simple JWT token obtained")
                self.record_test("Simple JWT Login", True, f"User: {data['user']['username']}")
                return self.simple_jwt_token
            else:
                self.log_error(f"Simple JWT login failed: HTTP {response.status_code}")
                self.record_test("Simple JWT Login", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_error(f"Simple JWT login error: {e}")
            self.record_test("Simple JWT Login", False, str(e))
            return None
            
    def test_keycloak_protected_api(self, user_type="admin"):
        """Test Keycloak protected API endpoint"""
        self.log_info(f"Testing Keycloak protected API with {user_type} token...")
        
        token = self.get_keycloak_token(user_type)
        if not token:
            return False
            
        try:
            response = self.session.get(
                f"{FLASK_URL}/api/protected",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_success(f"Keycloak protected API: {data['message']}")
                self.record_test(f"Keycloak Protected API ({user_type})", True, f"Auth method: {data['auth_method']}")
                return True
            else:
                self.log_error(f"Keycloak protected API failed: HTTP {response.status_code}")
                self.record_test(f"Keycloak Protected API ({user_type})", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"Keycloak protected API error: {e}")
            self.record_test(f"Keycloak Protected API ({user_type})", False, str(e))
            return False
            
    def test_simple_jwt_protected_api(self):
        """Test simple JWT protected API endpoint"""
        self.log_info("Testing simple JWT protected API...")
        
        token = self.get_simple_jwt_token()
        if not token:
            return False
            
        try:
            response = self.session.get(
                f"{FLASK_URL}/api/protected-simple",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_success(f"Simple JWT protected API: {data['message']}")
                self.record_test("Simple JWT Protected API", True, f"Auth method: {data['auth_method']}")
                return True
            else:
                self.log_error(f"Simple JWT protected API failed: HTTP {response.status_code}")
                self.record_test("Simple JWT Protected API", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"Simple JWT protected API error: {e}")
            self.record_test("Simple JWT Protected API", False, str(e))
            return False
            
    def test_unauthorized_access(self):
        """Test that protected endpoints block unauthorized requests"""
        self.log_info("Testing unauthorized access (should be blocked)...")
        
        endpoints = [
            ("/api/protected", "Keycloak Protected"),
            ("/api/protected-simple", "Simple JWT Protected")
        ]
        
        all_blocked = True
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{FLASK_URL}{endpoint}")
                if response.status_code == 401:
                    self.log_success(f"{name} correctly blocked unauthorized access")
                    self.record_test(f"Unauthorized Access Block ({name})", True, "HTTP 401")
                else:
                    self.log_error(f"{name} should have blocked unauthorized access (got HTTP {response.status_code})")
                    self.record_test(f"Unauthorized Access Block ({name})", False, f"HTTP {response.status_code}")
                    all_blocked = False
            except Exception as e:
                self.log_error(f"{name} unauthorized test error: {e}")
                self.record_test(f"Unauthorized Access Block ({name})", False, str(e))
                all_blocked = False
                
        return all_blocked
        
    def test_invalid_token(self):
        """Test that invalid tokens are rejected"""
        self.log_info("Testing invalid token rejection...")
        
        invalid_token = "invalid.jwt.token"
        endpoints = [
            ("/api/protected", "Keycloak Protected"),
            ("/api/protected-simple", "Simple JWT Protected")
        ]
        
        all_rejected = True
        for endpoint, name in endpoints:
            try:
                response = self.session.get(
                    f"{FLASK_URL}{endpoint}",
                    headers={"Authorization": f"Bearer {invalid_token}"}
                )
                if response.status_code == 401:
                    self.log_success(f"{name} correctly rejected invalid token")
                    self.record_test(f"Invalid Token Rejection ({name})", True, "HTTP 401")
                else:
                    self.log_error(f"{name} should have rejected invalid token (got HTTP {response.status_code})")
                    self.record_test(f"Invalid Token Rejection ({name})", False, f"HTTP {response.status_code}")
                    all_rejected = False
            except Exception as e:
                self.log_error(f"{name} invalid token test error: {e}")
                self.record_test(f"Invalid Token Rejection ({name})", False, str(e))
                all_rejected = False
                
        return all_rejected
        
    def test_health_endpoint(self):
        """Test health check endpoint"""
        self.log_info("Testing health endpoint...")
        
        try:
            response = self.session.get(f"{FLASK_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_success(f"Health check: {data['status']}")
                self.record_test("Health Check", True, data['status'])
                return True
            else:
                self.log_error(f"Health check failed: HTTP {response.status_code}")
                self.record_test("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"Health check error: {e}")
            self.record_test("Health Check", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run all API tests"""
        self.log(f"{Colors.BOLD}{Colors.CYAN}🧪 Starting Comprehensive API Testing{Colors.END}")
        self.log(f"{Colors.BOLD}Target: {FLASK_URL}{Colors.END}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Public API", self.test_public_api),
            ("Keycloak Admin Login", lambda: self.get_keycloak_token("admin") is not None),
            ("Keycloak Test User Login", lambda: self.get_keycloak_token("testuser") is not None),
            ("Simple JWT Login", lambda: self.get_simple_jwt_token() is not None),
            ("Keycloak Protected API (Admin)", lambda: self.test_keycloak_protected_api("admin")),
            ("Keycloak Protected API (Test User)", lambda: self.test_keycloak_protected_api("testuser")),
            ("Simple JWT Protected API", self.test_simple_jwt_protected_api),
            ("Unauthorized Access Prevention", self.test_unauthorized_access),
            ("Invalid Token Rejection", self.test_invalid_token)
        ]
        
        for test_name, test_func in tests:
            print()
            try:
                test_func()
            except Exception as e:
                self.log_error(f"Test '{test_name}' crashed: {e}")
            time.sleep(0.5)  # Brief pause between tests
            
        self.print_test_summary()
        
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print()
        print("=" * 60)
        self.log(f"{Colors.BOLD}{Colors.CYAN}📊 Test Summary{Colors.END}")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        # Overall status
        if passed == total:
            self.log(f"{Colors.BOLD}{Colors.GREEN}🎉 ALL TESTS PASSED ({passed}/{total}){Colors.END}")
        else:
            self.log(f"{Colors.BOLD}{Colors.RED}⚠️  SOME TESTS FAILED ({passed}/{total}){Colors.END}")
        
        print()
        
        # Detailed results
        for result in self.test_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            color = Colors.GREEN if result['passed'] else Colors.RED
            details = f" - {result['details']}" if result['details'] else ""
            print(f"{color}{status}{Colors.END} {result['test']}{details}")
        
        print()
        
        # Security validation summary
        self.print_security_summary()
        
        # Return exit code
        return 0 if passed == total else 1
        
    def print_security_summary(self):
        """Print security-focused test summary"""
        print("🔒 Security Validation:")
        print("-" * 25)
        
        security_tests = [
            ("Unauthorized access blocked", any(r['test'].startswith('Unauthorized Access Block') and r['passed'] for r in self.test_results)),
            ("Invalid tokens rejected", any(r['test'].startswith('Invalid Token Rejection') and r['passed'] for r in self.test_results)),
            ("Keycloak authentication working", any(r['test'].startswith('Keycloak Login') and r['passed'] for r in self.test_results)),
            ("JWT authentication working", any(r['test'] == 'Simple JWT Login' and r['passed'] for r in self.test_results)),
            ("Protected endpoints secured", any(r['test'].endswith('Protected API') and r['passed'] for r in self.test_results))
        ]
        
        for check, passed in security_tests:
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
        
        print()

def main():
    """Main function"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           Keycloak IAM System API Tester                ║")
    print("║                                                          ║")
    print("║  This script comprehensively tests all API endpoints    ║")
    print("║  with proper authentication and security validation     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    # Check if Flask app is accessible
    try:
        response = requests.get(f"{FLASK_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"{Colors.RED}❌ Flask app is not accessible at {FLASK_URL}{Colors.END}")
            print(f"{Colors.YELLOW}   Make sure the services are running: docker-compose up -d{Colors.END}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"{Colors.RED}❌ Cannot connect to Flask app at {FLASK_URL}{Colors.END}")
        print(f"{Colors.YELLOW}   Make sure the services are running: docker-compose up -d{Colors.END}")
        sys.exit(1)
    
    # Run tests
    tester = APITester()
    exit_code = tester.run_all_tests()
    
    print()
    print(f"{Colors.BOLD}🔗 Useful URLs:{Colors.END}")
    print(f"   Flask App: {FLASK_URL}")
    print(f"   Keycloak:  http://localhost:8080")
    print(f"   Admin:     http://localhost:8080 (admin/admin)")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()