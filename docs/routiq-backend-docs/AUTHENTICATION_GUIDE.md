# Authentication Guide

## Overview

The Routiq Backend API uses **Clerk** for authentication and implements a multi-tenant architecture with organization-based access control.

## Authentication Flow

### 1. JWT Token Requirements

All API endpoints (except public ones) require a valid JWT token from Clerk:

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Organization Context

Most endpoints require organization context via header:

```http
X-Organization-ID: org_2xwHiNrj68eaRUlX10anlXGvzX7
```

## Public Endpoints (No Auth Required)

- `GET /` - Root information
- `GET /health` - Health check
- `GET /docs` - Swagger documentation
- `GET /redoc` - ReDoc documentation

## Authentication Endpoints

### Verify Token
```http
GET /api/v1/auth/verify
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

**Success Response (200):**
```json
{
  "authenticated": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "message": "Authentication successful"
}
```

**Error Response (401):**
```json
{
  "authenticated": false,
  "organization_id": null,
  "message": "Invalid or expired token"
}
```

### Check Organization Access
```http
GET /api/v1/auth/organization/{organization_id}/access
Authorization: Bearer <token>
```

**Success Response (200):**
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "access_granted": true,
  "message": "Access granted"
}
```

## Implementation Examples

### JavaScript/Fetch
```javascript
const token = 'your-clerk-jwt-token';
const orgId = 'org_2xwHiNrj68eaRUlX10anlXGvzX7';

const response = await fetch('https://routiq-backend-prod.up.railway.app/api/v1/dashboard/' + orgId, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Organization-ID': orgId,
    'Content-Type': 'application/json'
  }
});

if (!response.ok) {
  throw new Error(`HTTP ${response.status}: ${response.statusText}`);
}

const data = await response.json();
```

### cURL
```bash
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/dashboard/org_123" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "X-Organization-ID: org_123" \
  -H "Content-Type: application/json"
```

### Python Requests
```python
import requests

token = "your-clerk-jwt-token"
org_id = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

headers = {
    "Authorization": f"Bearer {token}",
    "X-Organization-ID": org_id,
    "Content-Type": "application/json"
}

response = requests.get(
    f"https://routiq-backend-prod.up.railway.app/api/v1/dashboard/{org_id}",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Error Handling

### Common Authentication Errors

| Status | Error | Description |
|--------|-------|-------------|
| `401` | `Invalid token` | JWT token is malformed or expired |
| `401` | `Missing authorization header` | No Authorization header provided |
| `403` | `Organization access denied` | User doesn't have access to organization |
| `403` | `Invalid organization` | Organization ID is invalid or doesn't exist |

### Error Response Format
```json
{
  "error": "Authentication failed",
  "detail": "Invalid or expired token",
  "timestamp": "2025-06-30T12:00:00.000Z",
  "path": "/api/v1/endpoint"
}
```

## Security Best Practices

### Token Management
- **Never expose tokens** in client-side code
- **Use environment variables** for token storage
- **Implement token refresh** logic
- **Validate tokens server-side** before API calls

### Organization Security
- **Always validate** organization access
- **Use organization-specific** data isolation
- **Implement proper** role-based access control
- **Audit organization** access patterns

### HTTPS Requirements
- **Production**: HTTPS only
- **Development**: HTTP allowed for localhost only
- **All tokens**: Must be transmitted over secure connections

## Testing Authentication

### Test Valid Token
```bash
# Should return 200 with authentication details
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/auth/verify" \
  -H "Authorization: Bearer valid-token" \
  -H "X-Organization-ID: org_123"
```

### Test Invalid Token
```bash
# Should return 401 with error message
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/auth/verify" \
  -H "Authorization: Bearer invalid-token" \
  -H "X-Organization-ID: org_123"
```

### Test Missing Organization
```bash
# Should return 403 with access denied
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/auth/verify" \
  -H "Authorization: Bearer valid-token"
```

## Integration with Frontend

### React/Next.js Example
```typescript
import { useAuth } from '@clerk/nextjs';

export function useRoutiqAPI() {
  const { getToken } = useAuth();
  const orgId = 'org_2xwHiNrj68eaRUlX10anlXGvzX7';

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const token = await getToken();
    
    const response = await fetch(`https://routiq-backend-prod.up.railway.app${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': orgId,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  };

  return { apiCall };
}
```

### Vue.js Example
```typescript
import { useAuth } from '@clerk/vue';

export function useRoutiqAPI() {
  const { getToken } = useAuth();
  
  const makeRequest = async (endpoint: string, options = {}) => {
    const token = await getToken();
    
    return fetch(`https://routiq-backend-prod.up.railway.app${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': 'org_2xwHiNrj68eaRUlX10anlXGvzX7',
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  };

  return { makeRequest };
}
```

## Troubleshooting

### Common Issues

1. **"Invalid or expired token"**
   - Check token expiration
   - Refresh token with Clerk
   - Verify token format

2. **"Organization access denied"**
   - Verify organization ID
   - Check user membership
   - Confirm organization exists

3. **"Missing authorization header"**
   - Ensure Authorization header is set
   - Check header format: `Bearer <token>`
   - Verify header is not being stripped

4. **CORS errors**
   - Ensure domain is in allowed origins
   - Use HTTPS in production
   - Check preflight OPTIONS requests

### Debug Authentication
```bash
# Check token validity
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/auth/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: $ORG_ID" \
  -v
```

---

*For more information, see the [main API documentation](API_DOCUMENTATION.md)* 