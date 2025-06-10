# Routiq Backend API Test Suite

Comprehensive test suite for the Routiq Backend API with organized Cliniko endpoints.

## 🎯 **Test Organization**

### **API Structure (Reorganized)**
All patient endpoints are now properly organized under Cliniko:

```
/api/v1/admin/cliniko/
├── patients/
│   ├── {organization_id}/active/summary    # GET - Patient summary
│   ├── {organization_id}/active            # GET - List active patients  
│   ├── test                                # GET - Test endpoint
│   └── debug/
│       ├── organizations                   # GET - Debug organizations
│       ├── sample                          # GET - Sample patient data
│       └── simple-test                     # GET - Simple DB test
├── sync/{organization_id}                  # POST - Trigger sync
└── status/{organization_id}                # GET - Sync status
```

## 🧪 **Test Categories**

### **1. Core Endpoint Tests**
- ✅ Root endpoint (`/`)
- ✅ Health check (`/health`)
- ✅ API documentation endpoints

### **2. Cliniko Patient Tests**
- ✅ Patient summary endpoint
- ✅ Active patients list
- ✅ Debug endpoints
- ✅ Test connectivity

### **3. Cliniko Admin Tests**
- ✅ Sync trigger endpoint
- ✅ Status check endpoint

### **4. Error Handling Tests**
- ✅ 404 for invalid endpoints
- ✅ 405 for wrong HTTP methods
- ✅ Invalid organization ID formats
- ✅ Database connectivity issues

### **5. Performance Tests**
- ✅ Response time validation
- ✅ Concurrent request handling
- ✅ Load testing (basic)

### **6. Integration Tests**
- ✅ Full Cliniko workflow
- ✅ Multi-step operations

## 🚀 **Running Tests**

### **Prerequisites**
1. **Start the API server:**
   ```bash
   python3 -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Install test dependencies:**
   ```bash
   pip3 install pytest requests
   ```

### **Test Commands**

#### **Quick Test (Single endpoint):**
```bash
python3 -m pytest tests/test_api_endpoints.py::TestAPIEndpoints::test_root_endpoint -v
```

#### **All Tests:**
```bash
python3 -m pytest tests/ -v
```

#### **Fast Tests Only (exclude slow/load tests):**
```bash
python3 -m pytest tests/ -m "not slow" -v
```

#### **Integration Tests:**
```bash
python3 -m pytest tests/ -m "integration" -v
```

#### **Load Tests:**
```bash
python3 -m pytest tests/ -m "load" -v
```

#### **With Coverage:**
```bash
python3 -m pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### **Using the Test Runner Script**
```bash
# Run all tests
python3 run_tests.py

# Run only fast tests
python3 run_tests.py fast

# Run with verbose output
python3 run_tests.py all -v

# Stop on first failure
python3 run_tests.py all -x
```

## 📊 **Test Results Example**

```
=========================================== test session starts ============================================
platform darwin -- Python 3.11.11, pytest-8.4.0, pluggy-1.6.0
collected 25 items

tests/test_api_endpoints.py::TestAPIEndpoints::test_server_is_running PASSED                         [  4%]
tests/test_api_endpoints.py::TestAPIEndpoints::test_root_endpoint PASSED                            [  8%]
tests/test_api_endpoints.py::TestAPIEndpoints::test_health_endpoint PASSED                          [ 12%]
tests/test_api_endpoints.py::TestAPIEndpoints::test_cliniko_patients_test_endpoint PASSED           [ 16%]
tests/test_api_endpoints.py::TestAPIEndpoints::test_cliniko_patients_debug_simple_test PASSED       [ 20%]
...
============================================ 25 passed in 2.34s =============================================
```

## 🔧 **Test Configuration**

### **Environment Variables**
```bash
export TEST_BASE_URL="http://localhost:8000"  # Default API URL
export TEST_ORGANIZATION_ID="test_org_123"    # Test organization ID
```

### **Test Markers**
- `@pytest.mark.slow` - Slow tests (load, performance)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.load` - Load testing

## 📝 **Test Standards**

### **✅ What We Test**
1. **Response Status Codes** - Correct HTTP status codes
2. **Response Structure** - Required fields present
3. **Data Types** - Correct data types returned
4. **Error Handling** - Proper error responses
5. **Performance** - Response times under thresholds
6. **Content Types** - Proper JSON content types
7. **CORS Headers** - Cross-origin support

### **✅ Test Patterns**
```python
def test_endpoint_name(self):
    """Test description"""
    # Arrange
    url = f"{self.base_url}/api/v1/endpoint"
    
    # Act
    response = requests.get(url, headers=self.headers)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "required_field" in data
    assert isinstance(data["field"], expected_type)
```

## 🐛 **Debugging Failed Tests**

### **Common Issues**
1. **Server not running:**
   ```
   requests.exceptions.ConnectionError: Failed to connect
   ```
   **Solution:** Start the API server first

2. **Database not configured:**
   ```
   500 Internal Server Error: database connection failed
   ```
   **Solution:** Tests handle this gracefully, checking for 500 status

3. **Missing dependencies:**
   ```
   ModuleNotFoundError: No module named 'pytest'
   ```
   **Solution:** Install test dependencies

### **Verbose Output**
```bash
python3 -m pytest tests/ -v -s  # -s shows print statements
```

### **Stop on First Failure**
```bash
python3 -m pytest tests/ -x
```

## 📈 **Test Coverage**

Install coverage tools:
```bash
pip3 install pytest-cov
```

Generate coverage report:
```bash
python3 -m pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

## 🔄 **Continuous Integration**

### **GitHub Actions Example**
```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest requests
      - name: Start API server
        run: |
          python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
          sleep 10
      - name: Run tests
        run: python -m pytest tests/ -v
```

## 📚 **Best Practices**

### **✅ Standard Testing Practices**
1. **Test Isolation** - Each test is independent
2. **Descriptive Names** - Clear test method names
3. **AAA Pattern** - Arrange, Act, Assert
4. **Error Scenarios** - Test both success and failure cases
5. **Performance Testing** - Response time validation
6. **Integration Testing** - End-to-end workflows
7. **Load Testing** - Concurrent request handling

### **✅ API Testing Standards**
1. **Status Code Validation** - Always check HTTP status
2. **Response Structure** - Validate JSON structure
3. **Data Type Checking** - Ensure correct types
4. **Error Message Validation** - Check error responses
5. **Content Type Headers** - Verify JSON content type
6. **CORS Support** - Test cross-origin requests

## 🎉 **Summary**

This test suite provides comprehensive coverage of the Routiq Backend API with:

- **25+ test cases** covering all endpoints
- **Organized structure** with Cliniko endpoints properly grouped
- **Multiple test types** (unit, integration, load, performance)
- **Error handling** for various failure scenarios
- **Easy-to-use test runner** with different test categories
- **Standard testing practices** following industry best practices

The reorganized API structure now properly groups all patient-related endpoints under Cliniko, making the API more intuitive and maintainable. 