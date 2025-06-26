# RoutIQ Backend API Reference for Frontend

**Base URL**: `https://routiq-backend-prod.up.railway.app`

## 🔐 Authentication

All API endpoints now require **Clerk JWT authentication** via headers:

```javascript
const headers = {
  'Authorization': `Bearer ${clerkToken}`,
  'X-Organization-ID': organizationId,
  'Content-Type': 'application/json'
};
```

## ✅ Available Endpoints

### **Core System**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/` | Root endpoint with API info | ❌ No |
| `GET` | `/health` | Health check | ❌ No |

### **🏥 Cliniko Integration**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/cliniko/status/{orgId}` | Connection status | ✅ Yes |
| `GET` | `/api/v1/cliniko/test-connection/{orgId}` | Test API connection | ✅ Yes |
| `GET` | `/api/v1/cliniko/active-patients/{orgId}` | Active patients list | ✅ Yes |
| `GET` | `/api/v1/cliniko/active-patients-summary/{orgId}` | Patient summary | ✅ Yes |
| `POST` | `/api/v1/cliniko/sync-all/{orgId}` | Start full sync | ✅ Yes |
| `GET` | `/api/v1/cliniko/sync-logs/{orgId}` | Sync progress/logs | ✅ Yes |

### **👥 Patients**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/patients/{orgId}/patients` | List patients | ✅ Yes |
| `GET` | `/api/v1/patients/{orgId}/active/summary` | Active patient summary | ✅ Yes |
| `GET` | `/api/v1/patients/{orgId}/patients/with-appointments` | Patients with appointment details | ✅ Yes |

### **🔄 Sync Management** 

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/sync/start/{orgId}` | Start sync operation | ✅ Yes |
| `GET` | `/api/v1/sync/status/{syncId}` | Get sync status by ID | ✅ Yes |
| `GET` | `/api/v1/sync/status/organization/{orgId}` | Org sync status | ✅ Yes |
| `GET` | `/api/v1/sync/history/{orgId}` | Sync history | ✅ Yes |
| `GET` | `/api/v1/sync/dashboard/{orgId}` | Dashboard data | ✅ Yes |
| `DELETE` | `/api/v1/sync/cancel/{syncId}` | Cancel sync | ✅ Yes |

## 🚨 **IMPORTANT: Deprecated/Non-Existent Endpoints**

These endpoints **DO NOT EXIST** and will return 404:
- ❌ `/api/v1/admin/cliniko/patients/test`
- ❌ `/api/v1/admin/cliniko/sync/test`
- ❌ Any `/api/v1/admin/cliniko/*` paths

## 📋 **Frontend Implementation Examples**

### **1. Sync Dashboard Data**

```javascript
// ✅ CORRECT - Use this endpoint
const getDashboardData = async (orgId) => {
  const response = await fetch(`${BASE_URL}/api/v1/sync/dashboard/${orgId}`, {
    headers: {
      'Authorization': `Bearer ${clerkToken}`,
      'X-Organization-ID': orgId
    }
  });
  return response.json();
};
```

### **2. Sync History**

```javascript
// ✅ CORRECT - Use this endpoint  
const getSyncHistory = async (orgId) => {
  const response = await fetch(`${BASE_URL}/api/v1/sync/history/${orgId}`, {
    headers: {
      'Authorization': `Bearer ${clerkToken}`,
      'X-Organization-ID': orgId
    }
  });
  return response.json();
};
```

### **3. Start Sync Operation**

```javascript
// ✅ CORRECT - Use this endpoint
const startSync = async (orgId) => {
  const response = await fetch(`${BASE_URL}/api/v1/sync/start/${orgId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${clerkToken}`,
      'X-Organization-ID': orgId,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
```

### **4. Alternative Cliniko Sync**

```javascript
// ✅ ALTERNATIVE - This also works
const startClinikoSync = async (orgId) => {
  const response = await fetch(`${BASE_URL}/api/v1/cliniko/sync-all/${orgId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${clerkToken}`,
      'X-Organization-ID': orgId
    }
  });
  return response.json();
};
```

## 🔧 **Error Handling**

### **Common HTTP Status Codes**

| Code | Meaning | Action |
|------|---------|--------|
| `200` | Success | Process response |
| `401` | Unauthorized | Refresh Clerk token |
| `403` | Forbidden | Check organization access |
| `404` | Not Found | Endpoint doesn't exist |
| `429` | Rate Limited | Wait and retry |
| `500` | Server Error | Show error message |

### **Authentication Error Example**

```javascript
const handleApiCall = async (orgId) => {
  try {
    const response = await fetch(`${BASE_URL}/api/v1/sync/dashboard/${orgId}`, {
      headers: {
        'Authorization': `Bearer ${clerkToken}`,
        'X-Organization-ID': orgId
      }
    });
    
    if (response.status === 401) {
      // Token expired - refresh from Clerk
      const newToken = await clerk.session.getToken();
      // Retry request with new token
    } else if (response.status === 404) {
      console.error('Endpoint not found - check API reference');
    }
    
    return response.json();
  } catch (error) {
    console.error('API call failed:', error);
  }
};
```

## 📊 **Response Formats**

### **Sync Dashboard Response**

```json
{
  "organization_id": "org_123",
  "current_sync": {
    "sync_id": "sync_456",
    "status": "running",
    "progress_percentage": 45,
    "current_step": "Fetching appointments"
  },
  "patient_stats": {
    "total_patients": 648,
    "active_patients": 36,
    "patients_with_upcoming": 23,
    "patients_with_recent": 31
  },
  "last_sync": {
    "status": "completed",
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:35:00Z",
    "records_success": 125
  }
}
```

### **Sync History Response**

```json
{
  "organization_id": "org_123",
  "total_syncs": 48,
  "successful_syncs": 31,
  "failed_syncs": 16,
  "last_sync_at": "2024-01-15T10:35:00Z",
  "recent_syncs": [
    {
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:35:00Z",
      "status": "completed",
      "records_processed": 125,
      "records_success": 125,
      "records_failed": 0
    }
  ]
}
```

## 🚀 **Testing Endpoints**

Use this simple test to verify endpoints work:

```bash
# Test sync dashboard
curl -H "Authorization: Bearer YOUR_CLERK_TOKEN" \
     -H "X-Organization-ID: YOUR_ORG_ID" \
     https://routiq-backend-prod.up.railway.app/api/v1/sync/dashboard/YOUR_ORG_ID

# Test sync history  
curl -H "Authorization: Bearer YOUR_CLERK_TOKEN" \
     -H "X-Organization-ID: YOUR_ORG_ID" \
     https://routiq-backend-prod.up.railway.app/api/v1/sync/history/YOUR_ORG_ID
```

## 🔄 **Rate Limiting**

Our new security includes rate limiting:
- **API endpoints**: 100 requests/hour
- **Admin endpoints**: 50 requests/hour  
- **Sync endpoints**: 20 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 📞 **Need Help?**

If you get 404 errors:
1. ✅ Check this documentation for correct endpoints
2. ✅ Verify authentication headers are included
3. ✅ Test with curl first
4. ✅ Check organization ID format

**All endpoints require authentication now!** No more anonymous access. 