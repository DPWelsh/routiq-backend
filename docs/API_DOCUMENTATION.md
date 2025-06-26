# 🏥 Routiq Healthcare API Documentation

## Overview

The **Routiq Healthcare API** is a comprehensive multi-tenant SaaS platform designed for healthcare practices. It integrates with various practice management systems, patient communication tools, and provides intelligent patient analytics.

### 🚀 Base URLs
- **Production**: `https://routiq-backend-prod.up.railway.app`
- **Development**: `http://localhost:8000`

### 📋 Quick Reference
- **Interactive Docs**: `/docs` - Try endpoints directly in your browser
- **ReDoc**: `/redoc` - Clean, readable documentation
- **Health Check**: `/health` - System status
- **OpenAPI Spec**: `/openapi.json` - Machine-readable specification

---

## 🔐 Authentication

All API endpoints (except `/` and `/health`) require **Clerk JWT authentication**.

### Headers Required
```http
Authorization: Bearer <your-jwt-token>
x-organization-id: <your-organization-id>
Content-Type: application/json
```

### Getting Your JWT Token
1. Sign up/Login through your Routiq frontend application
2. The JWT token is automatically managed by Clerk
3. Include it in the `Authorization` header as `Bearer <token>`

---

## 🏢 Multi-Tenant Architecture

Every request must include the `x-organization-id` header to specify which healthcare organization's data to access. This ensures complete data isolation between different practices.

---

## 📊 Core Endpoints

### 🏠 System Status

#### `GET /`
**Welcome & API Information**
- No authentication required
- Returns API version, status, and quick links
- Perfect for testing basic connectivity

#### `GET /health`
**Comprehensive Health Check**
- No authentication required  
- Returns system status, configuration, and environment info
- Use for monitoring and troubleshooting

---

## 🔐 Authentication Endpoints

### `POST /api/v1/auth/verify`
**Verify JWT Token & Organization Access**
- Validates your JWT token
- Confirms access to specified organization
- Returns authentication status

**Headers:**
```http
Authorization: Bearer <jwt-token>
x-organization-id: <org-id>
```

---

## 👥 Patient Management

### `GET /api/v1/patients/{organization_id}`
**List All Patients**
- Returns paginated list of patients
- Supports filtering and search

### `GET /api/v1/patients/{organization_id}/active`
**Get Active Patients**
- Returns patients with recent or upcoming appointments
- Configurable time window (default: 30 days)

### `GET /api/v1/patients/{organization_id}/active/with-appointments`
**Active Patients with Appointment Details**
- Enhanced patient data including appointment information
- Perfect for dashboard analytics

### `GET /api/v1/patients/{organization_id}/by-appointment-type/{appointment_type}`
**Patients by Appointment Type**
- Filter patients by specific appointment types
- Useful for targeted communication campaigns

### `GET /api/v1/patients/{organization_id}/appointment-types/summary`
**Appointment Types Summary**
- Statistical overview of appointment types
- Patient counts per appointment type

---

## 🔄 Sync Management

### `POST /api/v1/sync/start/{organization_id}`
**Start Data Synchronization**
- Initiates sync with practice management system
- Returns sync ID for progress tracking
- Supports different sync modes

**Query Parameters:**
- `sync_mode`: `"active"` (recommended) or `"full"`
- `force_refresh`: `true` to bypass cache

**Example:**
```http
POST /api/v1/sync/start/org_123?sync_mode=active
```

### `GET /api/v1/sync/dashboard/{organization_id}`
**Sync Dashboard Data**
- Current sync status and progress
- Patient statistics and counts
- Last sync information

### `GET /api/v1/sync/history/{organization_id}`
**Sync History**
- Historical sync operations
- Success/failure rates
- Performance metrics

---

## 📊 Real-time Sync Status

### `GET /api/v1/sync/status/{sync_id}`
**Real-time Sync Progress**
- Live progress updates
- Current step information
- Estimated completion time
- Error reporting

**Response Example:**
```json
{
  "sync_id": "sync_org_123_20250115_143022",
  "status": "running",
  "progress_percentage": 75,
  "current_step": "Analyzing patient data...",
  "patients_found": 245,
  "appointments_found": 89,
  "active_patients_identified": 67
}
```

---

## 🩺 Cliniko Integration

### `GET /api/v1/cliniko/test-connection/{organization_id}`
**Test Cliniko API Connection**
- Validates API credentials
- Tests connectivity to Cliniko servers
- Returns connection status and basic info

### `POST /api/v1/cliniko/configure/{organization_id}`
**Configure Cliniko Integration**
- Set up Cliniko API credentials
- Configure sync preferences
- Enable/disable specific data types

---

## ⚙️ Admin Endpoints

### `POST /api/v1/admin/migrate/organization-services`
**Database Migration**
- System-level database migrations
- Multi-integration support setup

### `POST /api/v1/admin/database/cleanup`
**Database Cleanup**
- Remove old sync logs and audit data
- System maintenance

---

## 📈 Response Formats

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2025-01-15T10:30:00.123456Z"
}
```

### Error Response
```json
{
  "error": "Authentication failed",
  "detail": "JWT token is expired or invalid",
  "timestamp": "2025-01-15T10:30:00.123456Z"
}
```

---

## 🚦 HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## 🔧 Common Use Cases

### 1. Dashboard Integration
```javascript
// Get dashboard data
const response = await fetch('/api/v1/sync/dashboard/org_123', {
  headers: {
    'Authorization': 'Bearer ' + jwtToken,
    'x-organization-id': 'org_123'
  }
});
```

### 2. Start Patient Sync
```javascript
// Start active patient sync
const syncResponse = await fetch('/api/v1/sync/start/org_123?sync_mode=active', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + jwtToken,
    'x-organization-id': 'org_123'
  }
});

const { sync_id } = await syncResponse.json();

// Poll for progress
const statusResponse = await fetch(`/api/v1/sync/status/${sync_id}`);
```

### 3. Get Active Patients
```javascript
// Get patients with recent appointments
const patients = await fetch('/api/v1/patients/org_123/active/with-appointments', {
  headers: {
    'Authorization': 'Bearer ' + jwtToken,
    'x-organization-id': 'org_123'
  }
});
```

---

## 🐛 Troubleshooting

### Authentication Issues
1. **401 Unauthorized**: Check JWT token validity
2. **403 Forbidden**: Verify organization ID access
3. **Missing Headers**: Ensure both `Authorization` and `x-organization-id` headers

### Sync Issues
1. **504 Timeout**: Large syncs may take time, use status endpoint
2. **Sync Not Found**: Check sync ID format and organization access
3. **Credential Errors**: Verify Cliniko API credentials in admin panel

### Common Errors
```json
// Invalid organization ID
{
  "error": "Organization not found",
  "detail": "Organization 'org_invalid' does not exist or access denied"
}

// Sync already running
{
  "error": "Sync in progress",
  "detail": "Another sync is already running for this organization"
}
```

---

## 📞 Support

- **Documentation**: Visit `/docs` for interactive testing
- **Health Check**: Use `/health` to verify system status
- **Error Logs**: Check response details for specific error information

---

## 🔄 API Versioning

Current version: **v2.0.0**

All endpoints are prefixed with `/api/v1/` for future compatibility. When breaking changes are introduced, a new version prefix will be added while maintaining backward compatibility.

---

*Last updated: January 2025* 