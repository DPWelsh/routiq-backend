# 🧪 Routiq Backend Test Suite

**Consolidated & Enhanced Test Structure for Routiq Backend API**

## 🎯 **What This Is**

Single, comprehensive test suite for all Routiq Backend functionality including:
- ✅ **Core API endpoints** (root, health, docs)
- ✅ **Patient management** (basic + enhanced features)  
- ✅ **Enhanced patient visibility** (appointment types, treatment notes, timing)
- ✅ **Performance testing** (response times, load handling)
- ✅ **Integration testing** (full workflows)

## 📁 **Test Organization**

```
tests/
├── conftest.py                        # pytest configuration & markers
├── test_core_api.py                  # Core endpoints (/, /health, /docs)
├── test_patient_endpoints.py         # Basic patient endpoints  
├── test_enhanced_patient_features.py # 🆕 Enhanced visibility features
├── test_api_endpoints.py            # Legacy comprehensive tests
├── test_all_api_endpoints.py        # Legacy all-endpoint tests
├── utils/
│   ├── __init__.py
│   └── api_client.py                # Reusable API testing client
└── README.md                        # This file
```

## 🆕 **Enhanced Patient Visibility Features**

### **New API Endpoints Tested:**
- `GET /api/v1/patients/{org}/active/with-appointments` - Enhanced patient list with priority
- `GET /api/v1/patients/{org}/by-appointment-type/{type}` - Filter by appointment type  
- `GET /api/v1/patients/{org}/appointment-types/summary` - Appointment type statistics

### **New Data Fields Validated:**
- `next_appointment_time` - When is their next appointment
- `next_appointment_type` - What type of appointment is next
- `primary_appointment_type` - Most common appointment type
- `treatment_notes` - Clinical treatment information
- `hours_until_next_appointment` - Time calculation
- `priority` - High/Medium/Low based on appointment timing

## 🚀 **Running Tests**

### **Prerequisites**
```bash
# Install dependencies
pip install pytest requests

# Production server should be running at:
# https://routiq-backend-prod.up.railway.app
```

### **Quick Test Commands**

#### **All Tests**
```bash
cd tests/
python3 -m pytest -v
```

#### **Core API Tests**
```bash
python3 -m pytest test_core_api.py -v
```

#### **Enhanced Patient Features Only**
```bash
python3 -m pytest -m enhanced -v
```

#### **Performance Tests**
```bash
python3 -m pytest -m performance -v
```

#### **Skip Slow Tests**
```bash
python3 -m pytest -m "not slow" -v
```

### **Test Against Different Environments**

#### **Production (Default)**
```bash
python3 -m pytest -v
# Uses: https://routiq-backend-prod.up.railway.app
```

#### **Local Development**
```bash
TEST_SERVER_URL=http://localhost:8000 python3 -m pytest -v
```

#### **Custom Server**
```bash
TEST_SERVER_URL=https://your-server.com python3 -m pytest -v
```

## 📊 **Test Categories & Markers**

### **Pytest Markers Available:**
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance/speed tests
- `@pytest.mark.enhanced` - Enhanced patient visibility tests
- `@pytest.mark.slow` - Tests that take longer to run

### **Example Usage:**
```bash
# Run only enhanced feature tests
pytest -m enhanced

# Run everything except slow tests  
pytest -m "not slow"

# Run unit and integration tests
pytest -m "unit or integration"
```

## 🏥 **Enhanced Patient Feature Tests**

### **What Gets Tested:**

#### **1. Enhanced Data Structure**
```python
# Validates that patient objects now include:
{
    "next_appointment_time": "2024-06-22T14:30:00Z",
    "next_appointment_type": "Initial Consultation", 
    "primary_appointment_type": "Follow-up",
    "treatment_notes": "Patient progress notes...",
    "hours_until_next_appointment": 18.5,
    "priority": "high"  # high/medium/low
}
```

#### **2. Appointment Type Filtering**
```python
# Tests filtering patients by appointment type
GET /api/v1/patients/surfrehab/by-appointment-type/Follow-up
# Returns only patients with Follow-up appointments
```

#### **3. Priority Calculation Logic**
```python
# Validates priority assignment:
# < 24 hours = "high" priority
# 24-72 hours = "medium" priority  
# > 72 hours = "low" priority
```

#### **4. Treatment Notes Integration**
```python
# Validates treatment information is preserved
# Tests that clinical notes are accessible via API
```

## 🔧 **Utilities & Helpers**

### **APITestClient**
Reusable API client with built-in retry logic, error handling, and common patterns:

```python
from utils.api_client import api_client

# Simple GET request
response = api_client.get("/api/v1/patients/surfrehab/active")

# With JSON validation
data = api_client.get_json("/health")

# With performance measurement
response, response_time = api_client.measure_response_time("/")
```

## 📈 **Expected Test Results**

### **Production Server Status:**
- ✅ **Core endpoints** working (/, /health, /docs)
- ✅ **Enhanced endpoints** deployed and accessible  
- ✅ **API documentation** includes new endpoints
- ⚠️  **Patient data** may be limited (depends on Cliniko sync)

### **Common Results:**
```
test_core_api.py::TestCoreAPI::test_root_endpoint PASSED
test_core_api.py::TestCoreAPI::test_health_endpoint PASSED  
test_core_api.py::TestCoreAPI::test_documentation_endpoints PASSED
test_enhanced_patient_features.py::TestEnhancedPatientFeatures::test_enhanced_patient_list_has_new_fields PASSED
```

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **Server Not Accessible**
```
requests.exceptions.ConnectionError: Failed to connect
```
**Solution**: Verify server URL is correct: `https://routiq-backend-prod.up.railway.app`

#### **500 Internal Server Error**
```
Status: 500 - Database connection issues
```
**Solution**: Expected in production without proper database setup. Tests handle this gracefully.

#### **Missing Enhanced Fields**
```
AssertionError: Missing enhanced field: next_appointment_type
```
**Solution**: Enhanced fields will be `null` until Cliniko sync populates them.

## 🎉 **Success Metrics**

### **Test Suite Health:**
- ✅ **Single test folder** (no more duplicates)
- ✅ **Clear organization** by functionality
- ✅ **Enhanced features tested** comprehensively
- ✅ **Production deployment verified**
- ✅ **Backward compatibility maintained**

### **API Enhancement Status:**
- ✅ **Enhanced endpoints deployed** in production
- ✅ **Database schema migrated** successfully
- ✅ **New fields available** in patient API
- ✅ **Appointment type filtering** functional
- ✅ **Priority calculation** implemented

## 📝 **What Was Cleaned Up**

### **Before:**
- ❌ Two confusing test folders (`/test/` and `/tests/`)
- ❌ Duplicate test logic across files
- ❌ No tests for enhanced patient features
- ❌ Different testing approaches (custom runner vs pytest)

### **After:**
- ✅ Single `/tests/` folder (industry standard)
- ✅ Organized by functionality, not source
- ✅ Comprehensive enhanced feature testing
- ✅ Consistent pytest-based approach
- ✅ Reusable test utilities
- ✅ Clear documentation and examples

---

**🎯 Result: Clean, organized, comprehensive test suite ready for enhanced patient visibility validation!** 