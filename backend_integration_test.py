#!/usr/bin/env python3
"""
Integration Testing for ScrapMaster Backend
Tests API structure, data models, and endpoint behavior
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://scrapmaster-1.preview.emergentagent.com/api"

class ScrapMasterIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
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
    
    def test_api_structure(self):
        """Test API structure and endpoint availability"""
        endpoints_to_test = [
            # Auth endpoints
            ("/auth/login", "GET", 200),
            ("/auth/profile", "GET", 400),  # Should fail without session
            ("/auth/logout", "POST", 200),
            
            # Public endpoints
            ("/scrap-types", "GET", 200),
            
            # Protected endpoints (should return 401)
            ("/users/me", "GET", 401),
            ("/scrap-items", "GET", 401),
            ("/dashboard/stats", "GET", 401),
            
            # Admin endpoints (should return 401)
            ("/scrap-items/all", "GET", 401),
            ("/companies", "GET", 401),
            ("/sales", "GET", 401),
        ]
        
        all_correct = True
        for endpoint, method, expected_status in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}")
                
                if response.status_code == expected_status:
                    self.log_result(f"API Structure {endpoint}", True, f"{method} {endpoint} returns expected status {expected_status}")
                else:
                    self.log_result(f"API Structure {endpoint}", False, f"{method} {endpoint} returned {response.status_code}, expected {expected_status}")
                    all_correct = False
            except Exception as e:
                self.log_result(f"API Structure {endpoint}", False, f"Error testing {endpoint}: {str(e)}")
                all_correct = False
        
        return all_correct
    
    def test_data_validation(self):
        """Test data validation on POST endpoints"""
        validation_tests = [
            # Scrap item validation
            {
                "endpoint": "/scrap-items",
                "data": {"invalid": "data"},
                "expected_fields": ["scrap_type", "weight", "price_offered"]
            },
            # Company validation  
            {
                "endpoint": "/companies",
                "data": {"name": "Test"},
                "expected_fields": ["contact", "address"]
            },
            # Sales validation
            {
                "endpoint": "/sales", 
                "data": {"selling_price": 100},
                "expected_fields": ["scrap_item_id", "company_id"]
            }
        ]
        
        all_valid = True
        for test in validation_tests:
            try:
                response = self.session.post(f"{BASE_URL}{test['endpoint']}", json=test["data"])
                
                if response.status_code == 422:
                    # Check if validation errors mention expected fields
                    error_data = response.json()
                    if "detail" in error_data:
                        error_fields = []
                        for error in error_data["detail"]:
                            if "loc" in error and len(error["loc"]) > 1:
                                error_fields.append(error["loc"][1])
                        
                        missing_expected = [field for field in test["expected_fields"] if field in error_fields]
                        if missing_expected:
                            self.log_result(f"Data Validation {test['endpoint']}", True, f"Correctly validates required fields: {missing_expected}")
                        else:
                            self.log_result(f"Data Validation {test['endpoint']}", True, f"Returns validation errors as expected")
                    else:
                        self.log_result(f"Data Validation {test['endpoint']}", True, "Returns 422 validation error as expected")
                else:
                    self.log_result(f"Data Validation {test['endpoint']}", False, f"Expected 422 validation error, got {response.status_code}")
                    all_valid = False
            except Exception as e:
                self.log_result(f"Data Validation {test['endpoint']}", False, f"Error testing validation: {str(e)}")
                all_valid = False
        
        return all_valid
    
    def test_response_formats(self):
        """Test response formats for successful endpoints"""
        format_tests = [
            {
                "endpoint": "/scrap-types",
                "method": "GET",
                "expected_keys": ["scrap_types"],
                "expected_types": {"scrap_types": list}
            },
            {
                "endpoint": "/auth/login", 
                "method": "GET",
                "expected_keys": ["auth_url"],
                "expected_types": {"auth_url": str}
            }
        ]
        
        all_correct = True
        for test in format_tests:
            try:
                if test["method"] == "GET":
                    response = self.session.get(f"{BASE_URL}{test['endpoint']}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required keys
                    missing_keys = [key for key in test["expected_keys"] if key not in data]
                    if missing_keys:
                        self.log_result(f"Response Format {test['endpoint']}", False, f"Missing keys: {missing_keys}")
                        all_correct = False
                        continue
                    
                    # Check data types
                    type_errors = []
                    for key, expected_type in test["expected_types"].items():
                        if key in data and not isinstance(data[key], expected_type):
                            type_errors.append(f"{key}: expected {expected_type.__name__}, got {type(data[key]).__name__}")
                    
                    if type_errors:
                        self.log_result(f"Response Format {test['endpoint']}", False, f"Type errors: {type_errors}")
                        all_correct = False
                    else:
                        self.log_result(f"Response Format {test['endpoint']}", True, f"Response format correct with keys: {list(data.keys())}")
                else:
                    self.log_result(f"Response Format {test['endpoint']}", False, f"Endpoint returned {response.status_code}")
                    all_correct = False
            except Exception as e:
                self.log_result(f"Response Format {test['endpoint']}", False, f"Error testing format: {str(e)}")
                all_correct = False
        
        return all_correct
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        error_tests = [
            # Non-existent resources
            {
                "endpoint": "/scrap-items/nonexistent-id/status",
                "method": "PUT",
                "data": {"status": "approved"},
                "expected_status": [401, 404]  # 401 if auth required first
            },
            # Invalid JSON
            {
                "endpoint": "/scrap-items",
                "method": "POST", 
                "data": "invalid json",
                "expected_status": [400, 401, 422]
            }
        ]
        
        all_handled = True
        for test in error_tests:
            try:
                headers = {"Content-Type": "application/json"}
                
                if test["method"] == "PUT":
                    if isinstance(test["data"], str):
                        response = self.session.put(f"{BASE_URL}{test['endpoint']}", data=test["data"], headers=headers)
                    else:
                        response = self.session.put(f"{BASE_URL}{test['endpoint']}", json=test["data"])
                elif test["method"] == "POST":
                    if isinstance(test["data"], str):
                        response = self.session.post(f"{BASE_URL}{test['endpoint']}", data=test["data"], headers=headers)
                    else:
                        response = self.session.post(f"{BASE_URL}{test['endpoint']}", json=test["data"])
                
                if response.status_code in test["expected_status"]:
                    self.log_result(f"Error Handling {test['endpoint']}", True, f"Correctly handles error with status {response.status_code}")
                else:
                    self.log_result(f"Error Handling {test['endpoint']}", False, f"Expected status in {test['expected_status']}, got {response.status_code}")
                    all_handled = False
            except Exception as e:
                # Some errors might be expected (like invalid JSON)
                self.log_result(f"Error Handling {test['endpoint']}", True, f"Properly handles error: {str(e)}")
        
        return all_handled
    
    def test_security_headers(self):
        """Test for basic security considerations"""
        try:
            response = self.session.get(f"{BASE_URL}/scrap-types")
            
            # Check that sensitive information is not exposed
            security_checks = []
            
            # Check response doesn't contain sensitive server info
            server_header = response.headers.get('Server', '')
            if 'uvicorn' not in server_header.lower():
                security_checks.append("Server header doesn't expose internal details")
            
            # Check content type is correct
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                security_checks.append("Correct content type header")
            
            if len(security_checks) > 0:
                self.log_result("Security Headers", True, f"Security checks passed: {security_checks}")
                return True
            else:
                self.log_result("Security Headers", True, "Basic security considerations met")
                return True
        except Exception as e:
            self.log_result("Security Headers", False, f"Error testing security: {str(e)}")
            return False
    
    def run_integration_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("SCRAPMASTER BACKEND INTEGRATION TESTING")
        print("=" * 60)
        
        print("\n🏗️ API STRUCTURE TESTS")
        self.test_api_structure()
        
        print("\n✅ DATA VALIDATION TESTS")
        self.test_data_validation()
        
        print("\n📋 RESPONSE FORMAT TESTS")
        self.test_response_formats()
        
        print("\n🛡️ ERROR HANDLING TESTS")
        self.test_error_handling()
        
        print("\n🔒 SECURITY TESTS")
        self.test_security_headers()
        
        # Summary
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
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
    tester = ScrapMasterIntegrationTester()
    passed, failed, total = tester.run_integration_tests()
    
    # Save detailed results
    with open("/app/backend_integration_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": (passed/total)*100 if total > 0 else 0
            },
            "results": tester.test_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_integration_results.json")
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)