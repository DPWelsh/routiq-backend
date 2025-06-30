# Routiq Backend API Documentation

**Version:** 2.0.0  
**Base URL:** `https://routiq-backend-prod.up.railway.app`  
**Environment:** Production  

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Core Endpoints](#core-endpoints)
5. [Patient Management](#patient-management)
6. [Dashboard & Analytics](#dashboard--analytics)
7. [Sync Management](#sync-management)
8. [Cliniko Integration](#cliniko-integration)
9. [Administration](#administration)
10. [Error Handling](#error-handling)
11. [Examples](#examples)

---

## Overview

The Routiq Backend API is a multi-tenant healthcare practice management system with integrated data synchronization from external services like Cliniko. It provides comprehensive patient management, appointment tracking, and analytics capabilities.

### Key Features

- **Multi-tenant Architecture**: Organization-based data isolation
- **Clerk Authentication**: Secure JWT-based authentication
- **Automated Sync**: Hourly synchronization with external systems
- **Real-time Analytics**: Dashboard metrics and engagement tracking
- **Rate Limiting**: Tiered rate limiting for different endpoint types
- **HIPAA Compliance**: Audit logging and secure data handling

### API Characteristics

- **Protocol**: HTTPS only (production)
- **Format**: JSON
- **Authentication**: Bearer token (JWT)
- **Rate Limiting**: Yes (see Rate Limiting section)
- **CORS**: Enabled for approved domains

---

## Authentication

All API endpoints (except health checks) require authentication using JWT tokens from Clerk.

### Authentication Header

```http
Authorization: Bearer <jwt_token>
```

### Organization Context

Most endpoints require an organization context, provided via:

```http
X-Organization-ID: org_2xwHiNrj68eaRUlX10anlXGvzX7
```

### Authentication Endpoints

#### Verify Authentication
```http
GET /api/v1/auth/verify
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

**Response:**
```json
{
  "authenticated": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "message": "Authentication successful"
}
```

#### Check Organization Access
```http
GET /api/v1/auth/organization/{organization_id}/access
Authorization: Bearer <token>
```

**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "access_granted": true,
  "message": "Access granted"
}
```

---

## Rate Limiting

The API implements tiered rate limiting to protect against abuse:

### Rate Limit Tiers

| Tier | Endpoints | Limit | Window |
|------|-----------|-------|---------|
| **Public** | `/`, `/health`, `/docs` | 100 requests | 15 minutes |
| **API** | `/api/v1/*` | 1000 requests | 15 minutes |
| **Sync** | `/api/v1/sync/*` | 100 requests | 15 minutes |
| **Admin** | `/api/v1/admin/*` | 50 requests | 15 minutes |

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
Retry-After: 900
```

### Rate Limit Exceeded Response

```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Try again in 60 seconds.",
  "rate_limit": {
    "limit": 1000,
    "remaining": 0,
    "reset_time": 1640995200,
    "retry_after": 60
  }
}
```

---

## Core Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-30T12:00:00.000Z",
  "version": "2.0.0",
  "environment": {
    "APP_ENV": "production",
    "PORT": "8000",
    "authentication_configured": true,
    "database_configured": true,
    "encryption_configured": true
  }
}
```

### Root Information
```http
GET /
```

**Response:**
```json
{
  "message": "Routiq Backend API",
  "version": "2.0.0",
  "status": "healthy",
  "timestamp": "2025-06-30T12:00:00.000Z",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

## Patient Management

### List Active Patients
```http
GET /api/v1/patients/{organization_id}/patients
Authorization: Bearer <token>
```

**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "patients": [
    {
      "id": "uuid-here",
      "name": "John Doe",
      "phone": "0412345678",
      "email": "john@example.com",
      "cliniko_patient_id": "12345",
      "is_active": true,
      "activity_status": "active",
      "recent_appointment_count": 2,
      "upcoming_appointment_count": 1,
      "total_appointment_count": 15,
      "first_appointment_date": "2024-01-15T09:00:00.000Z",
      "last_appointment_date": "2025-06-25T14:30:00.000Z",
      "next_appointment_time": "2025-07-02T10:00:00.000Z",
      "next_appointment_type": "Physiotherapy",
      "primary_appointment_type": "Physiotherapy",
      "treatment_notes": "Lower back pain treatment",
      "recent_appointments": [...],
      "upcoming_appointments": [...],
      "last_synced_at": "2025-06-30T11:00:00.000Z",
      "created_at": "2024-01-15T09:00:00.000Z",
      "updated_at": "2025-06-30T11:00:00.000Z"
    }
  ],
  "total_count": 37,
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Get Active Patients Summary
```http
GET /api/v1/patients/{organization_id}/active/summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "total_active_patients": 37,
  "patients_with_recent_appointments": 32,
  "patients_with_upcoming_appointments": 24,
  "avg_recent_appointments": 1.2,
  "avg_total_appointments": 8.7,
  "last_sync_date": "2025-06-30T11:00:00.000Z",
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### List Patients with Appointment Details
```http
GET /api/v1/patients/{organization_id}/patients/with-appointments
Authorization: Bearer <token>
```

**Response includes additional fields:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "patients": [
    {
      "id": "uuid-here",
      "name": "Jane Smith",
      "priority": "high",
      "hours_until_next_appointment": 18.5,
      "days_until_next_appointment": 0.8,
      // ... other patient fields
    }
  ],
  "total_count": 37,
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Filter Patients by Appointment Type
```http
GET /api/v1/patients/{organization_id}/patients/by-appointment-type/{appointment_type}
Authorization: Bearer <token>
```

**Example:**
```http
GET /api/v1/patients/org_123/patients/by-appointment-type/Physiotherapy
```

### Get Appointment Types Summary
```http
GET /api/v1/patients/{organization_id}/patients/appointment-types/summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "appointment_types": [
    {
      "next_appointment_type": "Physiotherapy",
      "primary_appointment_type": "Physiotherapy",
      "patient_count": 25,
      "patients_with_upcoming": 18,
      "earliest_upcoming": "2025-07-01T09:00:00.000Z",
      "latest_upcoming": "2025-08-15T16:30:00.000Z"
    }
  ],
  "total_types": 5,
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

---

## Dashboard & Analytics

### Get Dashboard Summary
```http
GET /api/v1/dashboard/{organization_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "summary": {
    "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
    "total_patients": 650,
    "active_patients": 37,
    "patients_with_upcoming": 24,
    "patients_with_recent": 32,
    "total_upcoming_appointments": 28,
    "total_recent_appointments": 45,
    "total_all_appointments": 1247,
    "avg_upcoming_per_patient": 0.76,
    "avg_recent_per_patient": 1.22,
    "avg_total_per_patient": 33.7,
    "engagement_rate": 8.1,
    "last_sync_time": "2025-06-30T11:00:00.000Z",
    "synced_patients": 650,
    "sync_percentage": 100.0,
    "integration_status": "Connected",
    "activity_status": "Active",
    "generated_at": "2025-06-30T12:00:00.000Z"
  },
  "recent_activity": [
    {
      "id": "sync_123",
      "source_system": "cliniko",
      "operation_type": "comprehensive_sync",
      "status": "completed",
      "records_processed": 651,
      "records_success": 651,
      "records_failed": 0,
      "started_at": "2025-06-30T11:00:00.000Z",
      "completed_at": "2025-06-30T11:06:00.000Z",
      "activity_type": "sync",
      "description": "Comprehensive patient and appointment sync",
      "minutes_ago": 54.2
    }
  ],
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Get Dashboard Summary Only
```http
GET /api/v1/dashboard/{organization_id}/summary
Authorization: Bearer <token>
```

### Get Recent Activity Only
```http
GET /api/v1/dashboard/{organization_id}/activity?limit=20
Authorization: Bearer <token>
```

---

## Sync Management

### Trigger Manual Sync
```http
POST /api/v1/sync/trigger
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

**Response:**
```json
{
  "message": "Sync started successfully",
  "sync_started": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Get Scheduler Status
```http
GET /api/v1/sync/scheduler/status
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "sync_running": false,
  "last_sync_time": "2025-06-30T11:00:00.000Z",
  "scheduler_active": true,
  "message": "Scheduler status retrieved successfully"
}
```

### Trigger Scheduled Sync
```http
POST /api/v1/sync/scheduler/trigger
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

### Get Sync Progress
```http
GET /api/v1/sync/progress/{sync_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "sync_id": "sync_org_123_20250630_120000",
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "status": "running",
  "progress_percentage": 75.5,
  "current_step": "Processing appointments",
  "total_steps": 4,
  "completed_steps": 3,
  "started_at": "2025-06-30T12:00:00.000Z",
  "estimated_completion": "2025-06-30T12:06:00.000Z",
  "records_processed": 490,
  "records_total": 650
}
```

### Get Sync History
```http
GET /api/v1/sync/history/{organization_id}?limit=10
Authorization: Bearer <token>
```

**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "total_syncs": 48,
  "successful_syncs": 47,
  "failed_syncs": 1,
  "last_sync_at": "2025-06-30T11:00:00.000Z",
  "last_successful_sync_at": "2025-06-30T11:00:00.000Z",
  "average_sync_duration_seconds": 360.5,
  "recent_syncs": [
    {
      "started_at": "2025-06-30T11:00:00.000Z",
      "completed_at": "2025-06-30T11:06:00.000Z",
      "status": "completed",
      "records_processed": 651,
      "records_success": 651,
      "records_failed": 0,
      "metadata": {
        "sync_type": "comprehensive",
        "patients_processed": 651,
        "appointments_processed": 296
      }
    }
  ]
}
```

---

## Cliniko Integration

### Trigger Cliniko Sync
```http
POST /api/v1/cliniko/sync/{organization_id}?mode=comprehensive
Authorization: Bearer <token>
```

**Query Parameters:**
- `mode`: `comprehensive` (default), `basic`, `patients-only`

**Response:**
```json
{
  "success": true,
  "message": "Comprehensive Cliniko sync started successfully",
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "sync_mode": "comprehensive",
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Get Cliniko Status
```http
GET /api/v1/cliniko/status/{organization_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "cliniko_connected": true,
  "api_region": "au4",
  "last_sync": "2025-06-30T11:00:00.000Z",
  "total_patients": 650,
  "sync_enabled": true,
  "credentials_valid": true
}
```

### Test Cliniko Connection
```http
GET /api/v1/cliniko/test-connection/{organization_id}
Authorization: Bearer <token>
```

### Import Patients from Cliniko
```http
POST /api/v1/cliniko/import-patients/{organization_id}
Authorization: Bearer <token>
```

### Debug Cliniko Data
```http
GET /api/v1/cliniko/debug/{organization_id}
Authorization: Bearer <token>
```

---

## Administration

### System Health Check
```http
GET /api/v1/admin/monitoring/system-health
Authorization: Bearer <token>
```

**Response:**
```json
{
  "database": {
    "status": "healthy",
    "connected": true
  },
  "metrics": {
    "total_organizations": 5,
    "total_patients": 3250,
    "active_patients": 185,
    "configured_services": {
      "cliniko": 5,
      "chatwoot": 2
    }
  },
  "integrations": {
    "cliniko": {
      "status": "operational",
      "total_connections": 5,
      "healthy_connections": 5
    }
  },
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Database Cleanup
```http
POST /api/v1/admin/database/cleanup?days_old=90
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "days_cleaned": 90,
  "cleanup_results": [
    "Deleted 1250 old sync logs",
    "Deleted 850 old audit logs"
  ],
  "completed_at": "2025-06-30T12:00:00.000Z"
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "timestamp": "2025-06-30T12:00:00.000Z",
  "path": "/api/v1/endpoint"
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Access denied |
| `404` | Not Found | Resource not found |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

### Authentication Errors

```json
{
  "error": "Authentication failed",
  "detail": "Invalid or expired token",
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Validation Errors

```json
{
  "error": "Validation error",
  "detail": "Invalid organization_id format",
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

---

## Examples

### Complete Patient Workflow

```bash
# 1. Authenticate
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/auth/verify" \
  -H "Authorization: Bearer <token>" \
  -H "X-Organization-ID: org_2xwHiNrj68eaRUlX10anlXGvzX7"

# 2. Get dashboard overview
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/dashboard/org_2xwHiNrj68eaRUlX10anlXGvzX7" \
  -H "Authorization: Bearer <token>"

# 3. List active patients
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/patients/org_2xwHiNrj68eaRUlX10anlXGvzX7/patients" \
  -H "Authorization: Bearer <token>"

# 4. Trigger sync if needed
curl -X POST "https://routiq-backend-prod.up.railway.app/api/v1/cliniko/sync/org_2xwHiNrj68eaRUlX10anlXGvzX7?mode=comprehensive" \
  -H "Authorization: Bearer <token>"
```

### JavaScript/TypeScript Example

```typescript
const API_BASE = 'https://routiq-backend-prod.up.railway.app';
const ORG_ID = 'org_2xwHiNrj68eaRUlX10anlXGvzX7';

class RoutiqAPI {
  constructor(private token: string) {}

  private async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        'X-Organization-ID': ORG_ID,
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async getDashboard() {
    return this.request(`/api/v1/dashboard/${ORG_ID}`);
  }

  async getPatients() {
    return this.request(`/api/v1/patients/${ORG_ID}/patients`);
  }

  async triggerSync() {
    return this.request(`/api/v1/cliniko/sync/${ORG_ID}?mode=comprehensive`, {
      method: 'POST',
    });
  }
}

// Usage
const api = new RoutiqAPI('your-jwt-token');
const dashboard = await api.getDashboard();
console.log(`Active patients: ${dashboard.summary.active_patients}`);
```

---

## Interactive API Documentation

For interactive API exploration, visit:
- **Swagger UI**: https://routiq-backend-prod.up.railway.app/docs
- **ReDoc**: https://routiq-backend-prod.up.railway.app/redoc

---

*Last updated: June 30, 2025* 