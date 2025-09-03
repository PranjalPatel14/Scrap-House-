#!/usr/bin/env python3
"""
Comprehensive Backend Testing for ScrapMaster System
Tests authentication, CRUD operations, role-based access, and data integrity
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://scrapmaster-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ScrapMasterTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{BASE_URL}/scrap-types")
            if response.status_code == 200:
                data = response.json()
                if "scrap_types" in data and len(data["scrap_types"]) > 0:
                    self.log_result("API Health Check", True, "API is accessible and returns scrap types")
                    return True
                else:
                    self.log_result("API Health Check", False, "API accessible but invalid scrap types response", {"response": data})
                    return False
            else:
                self.log_result("API Health Check", False, f"API returned status {response.status_code}", {"response": response.text})
                return False
        except Exception as e:
            self.log_result("API Health Check", False, f"Failed to connect to API: {str(e)}")
            return False
    
    def test_auth_login_endpoint(self):
        """Test authentication login endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/auth/login")
            if response.status_code == 200:
                data = response.json()
                if "auth_url" in data and "auth.emergentagent.com" in data["auth_url"]:
                    self.log_result("Auth Login Endpoint", True, "Login endpoint returns valid auth URL")
                    return True
                else:
                    self.log_result("Auth Login Endpoint", False, "Invalid auth URL format", {"response": data})
                    return False
            else:
                self.log_result("Auth Login Endpoint", False, f"Login endpoint returned status {response.status_code}", {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Auth Login Endpoint", False, f"Login endpoint error: {str(e)}")
            return False
    
    def test_auth_profile_without_session(self):
        """Test profile endpoint without session (should fail)"""
        try:
            response = self.session.get(f"{BASE_URL}/auth/profile")
            if response.status_code == 400:
                self.log_result("Auth Profile No Session", True, "Profile endpoint correctly rejects requests without session ID")
                return True
            else:
                self.log_result("Auth Profile No Session", False, f"Profile endpoint should return 400, got {response.status_code}", {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Auth Profile No Session", False, f"Profile endpoint error: {str(e)}")
            return False
    
    def test_protected_endpoints_without_auth(self):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ("/users/me", "GET"),
            ("/scrap-items", "GET"),
            ("/scrap-items", "POST"),
            ("/dashboard/stats", "GET")
        ]
        
        all_protected = True
        for endpoint, method in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json={})
                
                if response.status_code == 401:
                    self.log_result(f"Protected Endpoint {endpoint}", True, f"{method} {endpoint} correctly requires authentication")
                else:
                    self.log_result(f"Protected Endpoint {endpoint}", False, f"{method} {endpoint} should return 401, got {response.status_code}")
                    all_protected = False
            except Exception as e:
                self.log_result(f"Protected Endpoint {endpoint}", False, f"Error testing {endpoint}: {str(e)}")
                all_protected = False
        
        return all_protected
    
    def test_admin_endpoints_without_admin_role(self):
        """Test that admin endpoints require admin role"""
        admin_endpoints = [
            ("/scrap-items/all", "GET"),
            ("/companies", "GET"),
            ("/companies", "POST"),
            ("/sales", "GET"),
            ("/sales", "POST")
        ]
        
        # First test without any auth
        all_protected = True
        for endpoint, method in admin_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json={})
                
                if response.status_code in [401, 403]:
                    self.log_result(f"Admin Endpoint {endpoint}", True, f"{method} {endpoint} correctly requires admin access")
                else:
                    self.log_result(f"Admin Endpoint {endpoint}", False, f"{method} {endpoint} should return 401/403, got {response.status_code}")
                    all_protected = False
            except Exception as e:
                self.log_result(f"Admin Endpoint {endpoint}", False, f"Error testing admin endpoint {endpoint}: {str(e)}")
                all_protected = False
        
        return all_protected
    
    def test_scrap_item_creation_without_auth(self):
        """Test scrap item creation without authentication"""
        try:
            scrap_data = {
                "scrap_type": "Metal",
                "weight": 5.0,
                "price_offered": 100.0,
                "description": "Test metal scrap"
            }
            
            response = self.session.post(f"{BASE_URL}/scrap-items", json=scrap_data)
            
            if response.status_code == 401:
                self.log_result("Scrap Item Creation No Auth", True, "Scrap item creation correctly requires authentication")
                return True
            else:
                self.log_result("Scrap Item Creation No Auth", False, f"Should return 401, got {response.status_code}", {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Scrap Item Creation No Auth", False, f"Error testing scrap item creation: {str(e)}")
            return False
    
    def test_company_creation_without_auth(self):
        """Test company creation without authentication"""
        try:
            company_data = {
                "name": "Test Recycling Co",
                "contact": "+1234567890",
                "address": "123 Test Street",
                "email": "test@recycling.com"
            }
            
            response = self.session.post(f"{BASE_URL}/companies", json=company_data)
            
            if response.status_code in [401, 403]:
                self.log_result("Company Creation No Auth", True, "Company creation correctly requires admin authentication")
                return True
            else:
                self.log_result("Company Creation No Auth", False, f"Should return 401/403, got {response.status_code}", {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Company Creation No Auth", False, f"Error testing company creation: {str(e)}")
            return False
    
    def test_dashboard_stats_without_auth(self):
        """Test dashboard stats without authentication"""
        try:
            response = self.session.get(f"{BASE_URL}/dashboard/stats")
            
            if response.status_code == 401:
                self.log_result("Dashboard Stats No Auth", True, "Dashboard stats correctly requires authentication")
                return True
            else:
                self.log_result("Dashboard Stats No Auth", False, f"Should return 401, got {response.status_code}", {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Dashboard Stats No Auth", False, f"Error testing dashboard stats: {str(e)}")
            return False
    
    def test_scrap_types_endpoint(self):
        """Test scrap types endpoint (public)"""
        try:
            response = self.session.get(f"{BASE_URL}/scrap-types")
            
            if response.status_code == 200:
                data = response.json()
                expected_types = ["Metal", "Paper", "Plastic", "Glass", "Electronics"]
                
                if "scrap_types" in data:
                    returned_types = data["scrap_types"]
                    if all(t in returned_types for t in expected_types):
                        self.log_result("Scrap Types Endpoint", True, f"Returns all expected scrap types: {returned_types}")
                        return True
                    else:
                        self.log_result("Scrap Types Endpoint", False, f"Missing expected types. Got: {returned_types}", {"expected": expected_types})
                        return False
                else:
                    self.log_result("Scrap Types Endpoint", False, "Response missing 'scrap_types' field", {"response": data})
                    return False
            else:
                self.log_result("Scrap Types Endpoint", False, f"Should return 200, got {response.status_code}", {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Scrap Types Endpoint", False, f"Error testing scrap types: {str(e)}")
            return False
    
    def test_logout_endpoint(self):
        """Test logout endpoint"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/logout")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "logged out" in data["message"].lower():
                    self.log_result("Logout Endpoint", True, "Logout endpoint works correctly")
                    return True
                else:
                    self.log_result("Logout Endpoint", False, "Invalid logout response format", {"response": data})
                    return False
            else:
                self.log_result("Logout Endpoint", False, f"Should return 200, got {response.status_code}", {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Logout Endpoint", False, f"Error testing logout: {str(e)}")
            return False
    
    def test_invalid_endpoints(self):
        """Test invalid endpoints return 404"""
        invalid_endpoints = [
            "/invalid-endpoint",
            "/api/invalid",
            "/scrap-items/invalid-action"
        ]
        
        all_return_404 = True
        for endpoint in invalid_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 404:
                    self.log_result(f"Invalid Endpoint {endpoint}", True, f"Correctly returns 404 for {endpoint}")
                else:
                    self.log_result(f"Invalid Endpoint {endpoint}", False, f"Should return 404, got {response.status_code}")
                    all_return_404 = False
            except Exception as e:
                self.log_result(f"Invalid Endpoint {endpoint}", False, f"Error testing invalid endpoint: {str(e)}")
                all_return_404 = False
        
        return all_return_404
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        try:
            response = self.session.options(f"{BASE_URL}/scrap-types")
            
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            missing_headers = []
            for header in cors_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if not missing_headers:
                self.log_result("CORS Headers", True, "All required CORS headers present")
                return True
            else:
                self.log_result("CORS Headers", False, f"Missing CORS headers: {missing_headers}")
                return False
        except Exception as e:
            self.log_result("CORS Headers", False, f"Error testing CORS headers: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("SCRAPMASTER BACKEND TESTING")
        print("=" * 60)
        
        # Basic connectivity and health checks
        print("\n🔍 BASIC CONNECTIVITY TESTS")
        self.test_health_check()
        self.test_cors_headers()
        self.test_invalid_endpoints()
        
        # Authentication tests
        print("\n🔐 AUTHENTICATION TESTS")
        self.test_auth_login_endpoint()
        self.test_auth_profile_without_session()
        self.test_logout_endpoint()
        
        # Authorization tests
        print("\n🛡️ AUTHORIZATION TESTS")
        self.test_protected_endpoints_without_auth()
        self.test_admin_endpoints_without_admin_role()
        
        # Specific endpoint tests
        print("\n📊 ENDPOINT FUNCTIONALITY TESTS")
        self.test_scrap_types_endpoint()
        self.test_scrap_item_creation_without_auth()
        self.test_company_creation_without_auth()
        self.test_dashboard_stats_without_auth()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = sum(1 for r in self.test_results if not r["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed, failed, total

if __name__ == "__main__":
    tester = ScrapMasterTester()
    passed, failed, total = tester.run_all_tests()
    
    # Save detailed results
    with open("/app/backend_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": (passed/total)*100 if total > 0 else 0
            },
            "results": tester.test_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)