# Routiq Backend API Test Suite

This directory contains comprehensive testing tools for the Routiq Backend API, including connection pool management fixes and extensive endpoint testing.

## 🛠️ Backend Improvements Made

### 1. Connection Pool Management Fix
- **Problem**: The original code used a singleton `db = SupabaseClient()` without proper connection pooling
- **Solution**: Implemented `psycopg2.pool.ThreadedConnectionPool` with configurable min/max connections
- **Benefits**: 
  - Better performance under load
  - Prevents connection exhaustion
  - Automatic connection management
  - Thread-safe operations

### 2. Environment Variables for Database Pool
Add these to your environment:
```bash
DB_MIN_CONNECTIONS=2    # Minimum connections in pool
DB_MAX_CONNECTIONS=20   # Maximum connections in pool
```

## 📋 Test Files Overview

### `test_all_endpoints.py`
Comprehensive pytest-based test suite that tests all API endpoints with various scenarios.

**Features:**
- Tests all discovered endpoints
- Handles authentication requirements (401/403 responses)
- Performance testing with concurrent requests
- JSON response validation
- Comprehensive error reporting

### `run_comprehensive_tests.py`
Standalone test runner that provides detailed reporting and can test against production or local servers.

**Features:**
- Tests all known endpoints from codebase analysis
- Multiple organization ID testing
- Performance analysis
- Detailed categorized reporting
- JSON and text report generation

## 🚀 How to Run Tests

### Option 1: Run Against Production Server (Default)

```bash
# Basic test run against production
cd test/
python run_comprehensive_tests.py

# With custom URL
python run_comprehensive_tests.py --url https://your-server.com
```

### Option 2: Run Against Local Development Server

```bash
# Start your local server first
cd ../
python -m uvicorn src.api.main:app --reload --port 8000

# Then run tests against local server
cd test/
python run_comprehensive_tests.py --local
```

### Option 3: Run pytest Suite

```bash
# Run against production (default)
pytest test_all_endpoints.py -v

# Run against local server
TEST_SERVER_URL=http://localhost:8000 pytest test_all_endpoints.py -v
```

## 📊 All Tested Endpoints

The test suite covers **all** API endpoints identified in your codebase:

### Core Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check with connection pool stats
- `GET /docs` - API documentation
- `GET /openapi.json` - OpenAPI specification

### Admin Endpoints
- `POST /api/v1/admin/migrate/organization-services`
- `GET /api/v1/admin/organization-services/{organization_id}`
- `GET /api/v1/admin/monitoring/system-health` ⭐ *[Your referenced endpoint]*
- `GET /api/v1/admin/sync-logs/all`
- `POST /api/v1/admin/database/cleanup`

### Authentication Endpoints
- `GET /api/v1/auth/verify`
- `GET /api/v1/auth/organization/{organization_id}/access`

### Provider Endpoints
- `GET /api/v1/providers/`
- `GET /api/v1/providers/{provider_id}`

### Patient Endpoints
- `GET /api/v1/patients/{organization_id}/active/summary`
- `GET /api/v1/patients/{organization_id}/active`
- `GET /api/v1/patients/test`

### Sync Manager Endpoints
- `POST /api/v1/sync/trigger`
- `GET /api/v1/sync/status`
- `GET /api/v1/sync/logs`
- `GET /api/v1/sync/scheduler/status`
- `POST /api/v1/sync/scheduler/trigger`

### Cliniko Integration Endpoints (15 endpoints)
- `POST /api/v1/cliniko/sync/{organization_id}`
- `GET /api/v1/cliniko/status/{organization_id}`
- `GET /api/v1/cliniko/test-connection/{organization_id}`
- `POST /api/v1/cliniko/import-patients/{organization_id}`
- `POST /api/v1/cliniko/test-sync/{organization_id}`
- `GET /api/v1/cliniko/sync-logs/{organization_id}`
- `GET /api/v1/cliniko/active-patients/{organization_id}`
- `GET /api/v1/cliniko/active-patients/{organization_id}/summary`
- `GET /api/v1/cliniko/contacts/{organization_id}/with-appointments`
- `POST /api/v1/cliniko/sync/schedule/{organization_id}`
- `GET /api/v1/cliniko/sync/dashboard/{organization_id}`
- `GET /api/v1/cliniko/debug/contacts/{organization_id}`
- `GET /api/v1/cliniko/debug/patient-raw/{organization_id}`
- `GET /api/v1/cliniko/debug/contacts-full/{organization_id}`
- `POST /api/v1/cliniko/debug/sync-detailed/{organization_id}`

### Clerk Admin Endpoints (8 endpoints)
- `GET /api/v1/clerk/status`
- `POST /api/v1/clerk/sync`
- `GET /api/v1/clerk/sync-logs`
- `GET /api/v1/clerk/database-summary`
- `POST /api/v1/clerk/store-credentials`
- `GET /api/v1/clerk/credentials/{organization_id}/{service_name}`
- `GET /api/v1/clerk/organizations`
- `POST /api/v1/clerk/test-connection`

### Onboarding Endpoints
- `POST /api/v1/onboarding/start`
- `GET /api/v1/onboarding/status/{organization_id}`

## 📈 Test Results and Reporting

### Test Categories
Tests are categorized into:
- ✅ **Success** (200 responses)
- 🔐 **Auth Required** (401/403 - expected)
- 🔍 **Not Found** (404 - endpoint/org not found)
- ⚠️ **Client Error** (4xx responses)
- ❌ **Server Error** (5xx responses)
- ⏱️ **Timeout** (request timeout)
- 🔌 **Connection Error** (network issues)

### Generated Reports
- **Text Report**: `api_test_report_YYYYMMDD_HHMMSS.txt`
- **JSON Results**: `api_test_results_YYYYMMDD_HHMMSS.json`

### Sample Report Output
```
🧪 ROUTIQ BACKEND API COMPREHENSIVE TEST REPORT
================================================================
🔗 Server Tested: https://routiq-backend-v10-production.up.railway.app
⏰ Test Start: 2024-01-15T10:30:00
⏰ Test End: 2024-01-15T10:32:15

📊 SUMMARY STATISTICS
--------------------------------------------------
Total Endpoints Tested: 85
Successful Responses: 78
Failed Responses: 7
Success Rate: 91.8%
Average Response Time: 0.245s
Max Response Time: 2.100s
Min Response Time: 0.089s
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Database connection pool settings
DB_MIN_CONNECTIONS=2
DB_MAX_CONNECTIONS=20

# Test configuration
TEST_SERVER_URL=https://your-api-server.com
```

### Test Runner Arguments
```bash
python run_comprehensive_tests.py --help

Options:
  --url URL        Base URL of the API server to test
  --local         Test against local server (http://localhost:8000)
  --no-report     Do not save report to file
```

## 🎯 Testing Your Specific Endpoint

Your referenced endpoint is specifically tested:
```
GET /api/v1/admin/monitoring/system-health
```

This endpoint will show:
- Database connection pool status
- System health metrics
- Response time analysis
- Authentication requirements

## 🚦 Continuous Integration

To integrate with CI/CD:

```bash
# In your CI pipeline
python test/run_comprehensive_tests.py --url $PRODUCTION_URL
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ All API tests passed!"
else
    echo "❌ Some API tests failed!"
    exit 1
fi
```

## 💡 Tips for Development

1. **Run tests locally** before deploying to catch issues early
2. **Monitor response times** - anything over 2s should be investigated
3. **Check authentication** - 401/403 responses are expected for protected endpoints
4. **Review error reports** - focus on 5xx errors as they indicate server issues
5. **Use connection pooling** - the improved database client handles this automatically

## 🔍 Troubleshooting

### Common Issues

1. **Connection timeouts**: Increase timeout in test configuration
2. **Too many database connections**: Adjust `DB_MAX_CONNECTIONS`
3. **Memory issues**: Reduce `DB_MAX_CONNECTIONS` or add connection cleanup
4. **Test failures**: Check server logs for specific error details

### Debug Mode
For detailed debugging, examine the JSON results file which contains:
- Full request/response details
- Headers and response bodies
- Timing information
- Error stack traces 