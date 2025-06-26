# 🏥 Routiq Healthcare API

> **Multi-tenant healthcare practice management API with intelligent patient analytics**

[![API Version](https://img.shields.io/badge/API-v2.0.0-blue)](https://routiq-backend-prod.up.railway.app/docs)
[![Status](https://img.shields.io/badge/Status-Production-green)](https://routiq-backend-prod.up.railway.app/health)
[![Documentation](https://img.shields.io/badge/Docs-Interactive-orange)](https://routiq-backend-prod.up.railway.app/docs)

## 🚀 Quick Start

### 1. Check API Status
```bash
curl https://routiq-backend-prod.up.railway.app/health
```

### 2. Explore Interactive Documentation
Visit: **[https://routiq-backend-prod.up.railway.app/docs](https://routiq-backend-prod.up.railway.app/docs)**

### 3. Authentication
All endpoints require Clerk JWT authentication:
```http
Authorization: Bearer <your-jwt-token>
x-organization-id: <your-organization-id>
```

## 📋 Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | 🏠 API welcome & information |
| `/health` | GET | 🔍 System health check |
| `/api/v1/sync/dashboard/{org_id}` | GET | 📊 Sync dashboard data |
| `/api/v1/sync/start/{org_id}` | POST | 🔄 Start patient sync |
| `/api/v1/sync/status/{sync_id}` | GET | 📈 Real-time sync progress |
| `/api/v1/patients/{org_id}/active` | GET | 👥 Active patients |

## 🎯 Common Use Cases

### Dashboard Integration
```javascript
const dashboard = await fetch('/api/v1/sync/dashboard/org_123', {
  headers: {
    'Authorization': 'Bearer ' + token,
    'x-organization-id': 'org_123'
  }
});
```

### Start Patient Sync
```javascript
const sync = await fetch('/api/v1/sync/start/org_123?sync_mode=active', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'x-organization-id': 'org_123'
  }
});
```

## 🔧 Features

- ✅ **Multi-tenant**: Complete data isolation between organizations
- 🔐 **Secure**: Clerk JWT authentication with organization-level access control
- 🔄 **Real-time Sync**: Live progress tracking for data synchronization
- 📊 **Smart Analytics**: Intelligent patient activity analysis
- 🩺 **Cliniko Integration**: Seamless practice management system connectivity
- 💬 **Chatwoot Ready**: Patient communication system integration
- 📱 **RESTful**: Standard HTTP methods and status codes
- 📖 **Well Documented**: Interactive docs with examples

## 🏗️ Architecture

```
Frontend Apps → Clerk Auth → Routiq API → Practice Management Systems
     ↓              ↓            ↓              ↓
  (React)      (JWT Tokens)   (Multi-tenant)  (Cliniko, etc.)
```

## 📚 Documentation

- **[Interactive API Docs](https://routiq-backend-prod.up.railway.app/docs)** - Try endpoints directly
- **[ReDoc Documentation](https://routiq-backend-prod.up.railway.app/redoc)** - Clean, readable format
- **[Full API Guide](docs/API_DOCUMENTATION.md)** - Comprehensive documentation
- **[OpenAPI Spec](https://routiq-backend-prod.up.railway.app/openapi.json)** - Machine-readable specification

## 🚦 Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | ✅ Success | Request completed successfully |
| 401 | 🔒 Unauthorized | Missing or invalid JWT token |
| 403 | 🚫 Forbidden | Invalid organization access |
| 404 | ❌ Not Found | Resource doesn't exist |
| 500 | 💥 Server Error | Internal server issue |

## 🐛 Troubleshooting

### Authentication Issues
```bash
# Check if your token is valid
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "x-organization-id: YOUR_ORG_ID" \
     https://routiq-backend-prod.up.railway.app/api/v1/auth/verify
```

### Sync Issues
```bash
# Check sync status
curl https://routiq-backend-prod.up.railway.app/api/v1/sync/status/SYNC_ID
```

### System Health
```bash
# Verify API is running
curl https://routiq-backend-prod.up.railway.app/health
```

## 🔄 API Versioning

- **Current**: `v2.0.0`
- **Prefix**: All endpoints use `/api/v1/`
- **Compatibility**: Backward compatibility maintained across minor versions

## 📞 Support

- 📖 **Documentation**: [Interactive Docs](https://routiq-backend-prod.up.railway.app/docs)
- 🔍 **Health Check**: [System Status](https://routiq-backend-prod.up.railway.app/health)
- 💡 **Examples**: See [API Documentation](docs/API_DOCUMENTATION.md)

---

**Built with FastAPI, PostgreSQL, and ❤️ for healthcare** 