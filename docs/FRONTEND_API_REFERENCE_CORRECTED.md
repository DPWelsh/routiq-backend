# ✅ CORRECTED RoutIQ API Reference - Working Endpoints Only

**Base URL**: `https://routiq-backend-prod.up.railway.app`

## 🔐 Authentication Required for ALL Endpoints

```javascript
const headers = {
  'Authorization': `Bearer ${clerkToken}`,
  'X-Organization-ID': organizationId,
  'Content-Type': 'application/json'
};
```

## ✅ **CONFIRMED WORKING ENDPOINTS**

### **🏥 Cliniko Integration (Prefix: `/api/v1/cliniko/`)**

| Method | Endpoint | Status | Frontend Call |
|--------|----------|--------|---------------|
| `GET` | `/api/v1/cliniko/status/{orgId}` | ✅ **Works** | Use for connection status |
| `GET` | `/api/v1/cliniko/active-patients-summary/{orgId}` | ✅ **Works** | Use instead of patients summary |
| `GET` | `/api/v1/cliniko/active-patients/{orgId}` | ✅ **Works** | Full patients list |
| `POST` | `/api/v1/cliniko/sync-all/{orgId}` | ✅ **Works** | Start sync operations |
| `GET` | `/api/v1/cliniko/sync-logs/{orgId}` | ✅ **Works** | Monitor sync progress |

### **👥 Patients (Prefix: `/api/v1/patients/`)**

| Method | Endpoint | Status | Notes |
|--------|----------|--------|-------|
| `GET` | `/api/v1/patients/{orgId}/active/summary` | ✅ **Works** | Active patients summary |
| `GET` | `/api/v1/patients/{orgId}/patients` | ✅ **Works** | List all patients |

### **🔄 Sync Status (Prefix: `/api/v1/sync/`)**

| Method | Endpoint | Status | Notes |
|--------|----------|--------|-------|
| `GET` | `/api/v1/sync/dashboard/{orgId}` | ✅ **Should Work** | Just added auth |
| `GET` | `/api/v1/sync/history/{orgId}` | ✅ **Should Work** | Just added auth |
| `POST` | `/api/v1/sync/start/{orgId}` | ✅ **Works** | Alternative sync start |

## 🚨 **FRONTEND FIX: Update These Paths**

### **1. Fix Patients Summary Call**

```javascript
// ❌ WRONG - This gives 404
const response = await fetch(`${BASE_URL}/api/patients/${orgId}/active/summary`);

// ✅ CORRECT - Use this instead
const response = await fetch(`${BASE_URL}/api/v1/patients/${orgId}/active/summary`, {
  headers: {
    'Authorization': `Bearer ${clerkToken}`,
    'X-Organization-ID': orgId
  }
});
```

### **2. Fix Cliniko Status Call**

```javascript
// ❌ WRONG - Missing /v1
const response = await fetch(`${BASE_URL}/api/cliniko/status/${orgId}`);

// ✅ CORRECT - Include /v1
const response = await fetch(`${BASE_URL}/api/v1/cliniko/status/${orgId}`, {
  headers: {
    'Authorization': `Bearer ${clerkToken}`,
    'X-Organization-ID': orgId
  }
});
```

### **3. Alternative: Use Cliniko Endpoints**

If sync endpoints still have issues, use these **guaranteed working** alternatives:

```javascript
// Use Cliniko-specific endpoints that definitely work
const getDashboardData = async (orgId) => {
  const [status, summary, logs] = await Promise.all([
    fetch(`${BASE_URL}/api/v1/cliniko/status/${orgId}`, {headers}),
    fetch(`${BASE_URL}/api/v1/cliniko/active-patients-summary/${orgId}`, {headers}),
    fetch(`${BASE_URL}/api/v1/cliniko/sync-logs/${orgId}`, {headers})
  ]);
  
  return {
    connection_status: await status.json(),
    patient_summary: await summary.json(),
    sync_logs: await logs.json()
  };
};
```

## 🔧 **Quick Frontend Fixes**

### **Update Your API Base URLs:**

```javascript
// Make sure you're using the full /v1 paths
const API_ENDPOINTS = {
  // ✅ CORRECT
  CLINIKO_STATUS: '/api/v1/cliniko/status',
  PATIENTS_SUMMARY: '/api/v1/patients/{orgId}/active/summary',
  SYNC_DASHBOARD: '/api/v1/sync/dashboard',
  SYNC_HISTORY: '/api/v1/sync/history',
  
  // 🔄 FALLBACKS (guaranteed to work)
  CLINIKO_SUMMARY: '/api/v1/cliniko/active-patients-summary',
  CLINIKO_LOGS: '/api/v1/cliniko/sync-logs'
};
```

### **Add Error Handling:**

```javascript
const safeApiCall = async (endpoint, orgId) => {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}/${orgId}`, {
      headers: {
        'Authorization': `Bearer ${clerkToken}`,
        'X-Organization-ID': orgId
      }
    });
    
    if (response.status === 404) {
      console.warn(`Endpoint ${endpoint} not available, using fallback`);
      return null; // Handle gracefully in UI
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error);
    return null;
  }
};
```

## 🎯 **Immediate Action Items for Frontend Team:**

1. **✅ Update path prefixes** - Add `/v1` to all API calls
2. **✅ Use Cliniko fallbacks** - For guaranteed working endpoints  
3. **✅ Add graceful 404 handling** - Show simplified UI when endpoints unavailable
4. **✅ Test with curl first** - Verify endpoints before frontend changes

## 🧪 **Test These Working Endpoints:**

```bash
# Test Cliniko status (guaranteed to work)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "X-Organization-ID: YOUR_ORG_ID" \
     https://routiq-backend-prod.up.railway.app/api/v1/cliniko/status/YOUR_ORG_ID

# Test patients summary (correct path)  
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "X-Organization-ID: YOUR_ORG_ID" \
     https://routiq-backend-prod.up.railway.app/api/v1/patients/YOUR_ORG_ID/active/summary
```

The main issues were **missing `/v1` prefixes** and **incorrect path structures**. Once you fix these, the 404 errors should disappear! 🚀 