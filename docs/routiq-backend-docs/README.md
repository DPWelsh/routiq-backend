# Routiq Backend API Documentation

Welcome to the comprehensive documentation for the Routiq Backend API - a multi-tenant healthcare practice management system with integrated data synchronization.

## 📚 Documentation Index

### Core Documentation
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference with all endpoints
- **[Authentication Guide](AUTHENTICATION_GUIDE.md)** - Detailed authentication and security guide
- **[Sync Management Guide](SYNC_MANAGEMENT_GUIDE.md)** - Comprehensive sync operations and monitoring

### Quick Start
- **[Setup Guide](HOURLY_SYNC_SETUP.md)** - Environment setup and configuration
- **[Interactive Docs](https://routiq-backend-prod.up.railway.app/docs)** - Swagger UI
- **[ReDoc](https://routiq-backend-prod.up.railway.app/redoc)** - Alternative documentation interface

## 🚀 Quick Start

### 1. Authentication
```bash
# Get your JWT token from Clerk
export TOKEN="your-clerk-jwt-token"
export ORG_ID="org_2xwHiNrj68eaRUlX10anlXGvzX7"

# Test authentication
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/auth/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: $ORG_ID"
```

### 2. Get Dashboard Overview
```bash
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/dashboard/$ORG_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. List Patients
```bash
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/patients/$ORG_ID/patients" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Trigger Sync
```bash
curl -X POST "https://routiq-backend-prod.up.railway.app/api/v1/cliniko/sync/$ORG_ID?mode=comprehensive" \
  -H "Authorization: Bearer $TOKEN"
```

## 🏗️ API Overview

### Base URL
```
https://routiq-backend-prod.up.railway.app
```

### Key Features
- **Multi-tenant Architecture** with organization isolation
- **Clerk Authentication** with JWT tokens
- **Automated Hourly Sync** with external systems
- **Real-time Dashboard** metrics and analytics
- **Rate Limiting** for API protection
- **HIPAA Compliance** with audit logging

### Endpoint Categories

| Category | Prefix | Description |
|----------|--------|-------------|
| **Authentication** | `/api/v1/auth` | Token verification and organization access |
| **Patients** | `/api/v1/patients` | Patient management and queries |
| **Dashboard** | `/api/v1/dashboard` | Analytics and summary data |
| **Sync Management** | `/api/v1/sync` | Manual and scheduled synchronization |
| **Cliniko Integration** | `/api/v1/cliniko` | Cliniko-specific operations |
| **Administration** | `/api/v1/admin` | System administration |

## 📊 Response Format

All API responses follow a consistent JSON format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Error Response
```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "timestamp": "2025-06-30T12:00:00.000Z",
  "path": "/api/v1/endpoint"
}
```

## 🔐 Authentication

All endpoints require authentication except:
- `GET /` - Root information
- `GET /health` - Health check
- `GET /docs` - Documentation

### Required Headers
```http
Authorization: Bearer <jwt_token>
X-Organization-ID: <organization_id>
Content-Type: application/json
```

## 🚦 Rate Limiting

| Tier | Endpoints | Limit | Window |
|------|-----------|-------|---------|
| Public | `/`, `/health`, `/docs` | 100 req | 15 min |
| API | `/api/v1/*` | 1000 req | 15 min |
| Sync | `/api/v1/sync/*` | 100 req | 15 min |
| Admin | `/api/v1/admin/*` | 50 req | 15 min |

## 📈 Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| `200` | OK | Successful request |
| `400` | Bad Request | Invalid parameters |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Access denied |
| `404` | Not Found | Resource not found |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

## 🔄 Sync Operations

### Automatic Sync
- **Frequency**: Every hour
- **Scope**: All organizations with active patients
- **Type**: Comprehensive (patients + appointments)

### Manual Sync
- **Trigger**: API endpoint
- **Progress**: Real-time tracking
- **Modes**: Comprehensive, basic, patients-only

### Monitoring
- **Status**: Live sync status endpoint
- **History**: Complete sync history with metrics
- **Cleanup**: Automatic stale sync cleanup

## 💾 Data Models

### Patient
```json
{
  "id": "uuid",
  "name": "string",
  "phone": "string",
  "email": "string",
  "is_active": "boolean",
  "recent_appointment_count": "integer",
  "upcoming_appointment_count": "integer",
  "total_appointment_count": "integer",
  "next_appointment_time": "datetime",
  "next_appointment_type": "string",
  "last_synced_at": "datetime"
}
```

### Dashboard Summary
```json
{
  "total_patients": "integer",
  "active_patients": "integer",
  "patients_with_upcoming": "integer",
  "patients_with_recent": "integer",
  "engagement_rate": "float",
  "avg_upcoming_per_patient": "float",
  "integration_status": "string",
  "last_sync_time": "datetime"
}
```

## 🛠️ Development Tools

### Interactive Documentation
- **Swagger UI**: https://routiq-backend-prod.up.railway.app/docs
- **ReDoc**: https://routiq-backend-prod.up.railway.app/redoc

### Testing Endpoints
- **Health Check**: `GET /health`
- **Authentication**: `GET /api/v1/auth/verify`
- **Test Endpoint**: `GET /api/v1/patients/test`

### Client Libraries

#### JavaScript/TypeScript
```typescript
class RoutiqAPI {
  constructor(private token: string, private orgId: string) {}
  
  private async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`https://routiq-backend-prod.up.railway.app${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'X-Organization-ID': this.orgId,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
  
  async getDashboard() {
    return this.request(`/api/v1/dashboard/${this.orgId}`);
  }
  
  async getPatients() {
    return this.request(`/api/v1/patients/${this.orgId}/patients`);
  }
  
  async triggerSync() {
    return this.request(`/api/v1/cliniko/sync/${this.orgId}?mode=comprehensive`, {
      method: 'POST'
    });
  }
}
```

#### Python
```python
import requests

class RoutiqAPI:
    def __init__(self, token: str, org_id: str):
        self.token = token
        self.org_id = org_id
        self.base_url = "https://routiq-backend-prod.up.railway.app"
    
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Organization-ID": self.org_id,
            "Content-Type": "application/json"
        }
    
    def get_dashboard(self):
        response = requests.get(
            f"{self.base_url}/api/v1/dashboard/{self.org_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_patients(self):
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{self.org_id}/patients",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def trigger_sync(self):
        response = requests.post(
            f"{self.base_url}/api/v1/cliniko/sync/{self.org_id}?mode=comprehensive",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
```

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify JWT token is valid
   - Check organization ID format
   - Ensure headers are properly set

2. **Rate Limiting**
   - Monitor rate limit headers
   - Implement exponential backoff
   - Use appropriate endpoint tiers

3. **Sync Issues**
   - Check Cliniko credentials
   - Monitor sync progress
   - Use cleanup endpoint for stale syncs

4. **CORS Errors**
   - Verify domain is approved
   - Use HTTPS in production
   - Check preflight requests

### Debug Commands

```bash
# Health check
curl -X GET "https://routiq-backend-prod.up.railway.app/health"

# Authentication test
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/auth/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: $ORG_ID" \
  -v

# Sync status
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/sync/scheduler/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: $ORG_ID"
```

## 📞 Support

### Resources
- **Documentation**: This repository
- **Interactive Docs**: https://routiq-backend-prod.up.railway.app/docs
- **API Status**: Monitor via health endpoint

### Best Practices
- Always use HTTPS in production
- Implement proper error handling
- Monitor rate limits
- Use organization context headers
- Validate all user inputs
- Implement retry logic for transient errors

---

## 📄 Documentation Files

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete endpoint reference
- **[AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md)** - Security and auth details
- **[SYNC_MANAGEMENT_GUIDE.md](SYNC_MANAGEMENT_GUIDE.md)** - Sync operations guide
- **[HOURLY_SYNC_SETUP.md](HOURLY_SYNC_SETUP.md)** - Environment configuration

---

*Last updated: June 30, 2025 | Version: 2.0.0* 