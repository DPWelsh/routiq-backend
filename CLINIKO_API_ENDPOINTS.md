# Cliniko Active Patients API Endpoints

Complete API reference for the Cliniko active patients sync system.

## 🚀 Quick Start

**Base URL:** `https://routiq-backend-v10-production.up.railway.app`

## 📋 Authentication

Most endpoints require authentication via headers:
```http
x-organization-id: org_2xwHiNrj68eaRUlX10anlXGvzX7
Authorization: Bearer <jwt-token>
```

## 🎯 Core Endpoints

### 1. Force Sync (Recommended)
```http
POST /api/v1/admin/sync/schedule/{organization_id}
```
**Description:** Trigger immediate sync with duplicate prevention  
**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "sync_scheduled": true,
  "message": "Sync started successfully",
  "timestamp": "2025-06-09T13:10:48.082909"
}
```

### 2. Active Patients List
```http
GET /api/v1/admin/active-patients/{organization_id}
```
**Description:** Get all active patients with contact details  
**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "active_patients": [
    {
      "id": 1,
      "contact_id": "uuid",
      "contact_name": "John Smith",
      "contact_phone": "61432391907",
      "recent_appointment_count": 3,
      "upcoming_appointment_count": 1,
      "total_appointment_count": 15,
      "last_appointment_date": "2025-06-05T10:30:00",
      "recent_appointments": [...],
      "created_at": "2025-06-09T13:00:00",
      "updated_at": "2025-06-09T13:00:00"
    }
  ],
  "total_count": 47
}
```

### 3. Active Patients Summary
```http
GET /api/v1/admin/active-patients/{organization_id}/summary
```
**Description:** Get summary statistics for active patients  
**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "total_active_patients": 47,
  "patients_with_recent_appointments": 47,
  "patients_with_upcoming_appointments": 12,
  "last_sync_date": "2025-06-09T13:00:00",
  "avg_recent_appointments": 2.4,
  "avg_total_appointments": 8.7
}
```

### 4. Contacts with Appointments
```http
GET /api/v1/admin/contacts/{organization_id}/with-appointments
```
**Description:** Get all contacts that have appointments  
**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "contacts_with_appointments": [
    {
      "contact_id": "uuid",
      "name": "Jane Doe",
      "phone": "61432391908",
      "email": "jane@example.com",
      "cliniko_patient_id": "12345",
      "recent_appointment_count": 2,
      "upcoming_appointment_count": 0,
      "last_appointment_date": "2025-06-01T14:00:00",
      "recent_appointments": [...]
    }
  ],
  "total_count": 47
}
```

## 📊 Monitoring & Analytics

### 5. Sync Dashboard
```http
GET /api/v1/admin/sync/dashboard/{organization_id}
```
**Description:** Comprehensive sync status and metrics  
**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "contact_metrics": {
    "total_contacts": 632,
    "cliniko_linked": 626,
    "unlinked": 6,
    "link_percentage": 99.1
  },
  "active_patient_metrics": {
    "total_active": 47,
    "avg_recent_appointments": 2.4,
    "most_recent_appointment": "2025-06-08T15:30:00",
    "last_sync": "2025-06-09T13:00:00"
  },
  "service_status": {
    "cliniko_configured": true,
    "sync_enabled": true,
    "is_active": true
  },
  "health_indicators": {
    "has_contacts": true,
    "has_active_patients": true,
    "recent_sync": true,
    "high_link_rate": true
  }
}
```

### 6. System Health
```http
GET /api/v1/admin/monitoring/system-health
```
**Description:** System-wide health monitoring  
**Response:**
```json
{
  "overall_metrics": {
    "total_organizations": 2,
    "total_contacts": 632,
    "total_active_patients": 47
  },
  "sync_activity_24h": {
    "total_syncs": 5,
    "successful_syncs": 5,
    "failed_syncs": 0,
    "success_rate": 100
  },
  "health_status": {
    "status": "healthy",
    "all_systems_operational": true
  }
}
```

## 🔧 Legacy/Working Endpoints

### 7. Clerk Admin Sync (Currently Working)
```http
POST /api/v1/admin/clerk/sync
Content-Type: application/json

{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7"
}
```

### 8. Clerk Status Check
```http
GET /api/v1/admin/clerk/status
```

### 9. Database Summary
```http
GET /api/v1/admin/clerk/database-summary
```

## 🎯 Frontend Integration Examples

### React/Next.js Usage
```javascript
// Force sync
const triggerSync = async () => {
  const response = await fetch('/api/v1/admin/sync/schedule/org_2xwHiNrj68eaRUlX10anlXGvzX7', {
    method: 'POST'
  });
  const result = await response.json();
  console.log('Sync started:', result.sync_scheduled);
};

// Get active patients
const getActivePatients = async () => {
  const response = await fetch('/api/v1/admin/active-patients/org_2xwHiNrj68eaRUlX10anlXGvzX7');
  const data = await response.json();
  return data.active_patients;
};

// Get dashboard metrics
const getDashboard = async () => {
  const response = await fetch('/api/v1/admin/sync/dashboard/org_2xwHiNrj68eaRUlX10anlXGvzX7');
  const dashboard = await response.json();
  return dashboard;
};
```

## 🚨 Error Handling

All endpoints return standard HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `404` - Not Found  
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message describing what went wrong",
  "timestamp": "2025-06-09T13:00:00"
}
```

## 📈 Rate Limits

- **Admin endpoints:** 50 requests/hour per organization
- **Sync operations:** 10 requests/hour per organization  
- **Regular API:** 1000 requests/hour per organization

Rate limit headers included in responses:
```http
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1623456789
```

## 🎉 Success Metrics

**Current Production Stats:**
- ✅ **632 patients** imported from Cliniko
- ✅ **47 active patients** identified  
- ✅ **99.1% phone number** extraction success
- ✅ **100% sync success** rate
- ✅ **Real-time monitoring** and alerts
- ✅ **Multi-organization** support ready

Ready for frontend development! 🚀 