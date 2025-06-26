# API Reference - Patient Sync System

Complete reference for all Cliniko patient sync endpoints with real-time monitoring capabilities.

## 🚀 **Sync Management Endpoints**

### POST `/api/v1/cliniko/sync-all/{orgId}`

**Start Full Patient Sync** - Syncs ALL patients from Cliniko (not just active ones)

#### Parameters
- **orgId** (path, required): Organization ID

#### Request
```http
POST /api/v1/cliniko/sync-all/123
Content-Type: application/json
```

#### Response
```json
{
  "success": true,
  "message": "Full patient sync started for organization 123",
  "operation_type": "full_patients",
  "expected_duration": "30-120 seconds"
}
```

#### Status Codes
- `200` - Sync started successfully
- `400` - Invalid organization ID
- `401` - Authentication required
- `404` - Organization not found
- `429` - Sync already in progress

---

### POST `/api/v1/cliniko/sync/{orgId}` ⚠️ **Deprecated**

**Legacy Sync Endpoint** - Now redirects to `/sync-all/` for consistency

#### Migration Note
This endpoint now performs **full patient sync** (not active-only). Update frontend to use `/sync-all/` explicitly.

---

### GET `/api/v1/cliniko/test-connection/{orgId}`

**Test Cliniko API Connection** - Validates credentials and returns patient count

#### Response
```json
{
  "status": "connected",
  "total_patients": 648,
  "api_version": "v1",
  "connection_test": "passed",
  "organization": {
    "name": "Surf Rehab",
    "cliniko_id": "12345"
  }
}
```

#### Status Codes
- `200` - Connection successful
- `401` - Invalid Cliniko credentials
- `403` - Insufficient permissions
- `404` - Organization not found

---

## 📊 **Monitoring & Progress Endpoints**

### GET `/api/v1/cliniko/sync-logs/{orgId}`

**Real-Time Sync Progress** - Primary endpoint for live monitoring

#### Query Parameters
- **limit** (optional): Number of logs to return (default: 10, max: 100)
- **status** (optional): Filter by status (`running`, `completed`, `failed`)
- **operation_type** (optional): Filter by type (`full_patients`, `active_patients`)

#### Request
```http
GET /api/v1/cliniko/sync-logs/123?limit=1
```

#### Response
```json
{
  "logs": [
    {
      "id": 456,
      "organization_id": 123,
      "operation_type": "full_patients",
      "status": "running",
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": null,
      "records_processed": 450,
      "records_success": 448,
      "records_failed": 2,
      "metadata": {
        "patients_found": 648,
        "patients_stored": 448,
        "sync_type": "full_patients",
        "current_page": 9,
        "total_pages": 13,
        "progress_percent": 69.4,
        "estimated_remaining": "45 seconds"
      },
      "error_details": null
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

#### Metadata Fields
- **patients_found**: Total patients detected in Cliniko
- **patients_stored**: Number successfully saved to database
- **current_page**: Current API pagination page
- **total_pages**: Total pages to process
- **progress_percent**: Completion percentage
- **estimated_remaining**: Time remaining estimate

---

### GET `/api/v1/cliniko/status/{orgId}`

**Final Sync Status** - Summary after sync completion

#### Response
```json
{
  "sync_status": "completed",
  "last_sync": "2024-01-15T10:35:22Z",
  "patient_counts": {
    "total_in_cliniko": 648,
    "synced_to_database": 648,
    "success_rate": 100.0
  },
  "sync_duration": "4m 22s",
  "operation_type": "full_patients"
}
```

---

### GET `/api/v1/cliniko/active-patients/{orgId}`

**List Synced Patients** - Post-sync verification endpoint

#### Query Parameters
- **limit** (optional): Results per page (default: 50, max: 500)
- **offset** (optional): Pagination offset
- **search** (optional): Search by name or email
- **last_synced_after** (optional): Filter by sync date (ISO format)

#### Response
```json
{
  "patients": [
    {
      "id": 789,
      "cliniko_patient_id": "12345",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "+61 412 345 678",
      "date_of_birth": "1985-03-15",
      "last_synced": "2024-01-15T10:35:20Z",
      "sync_status": "success"
    }
  ],
  "pagination": {
    "total": 648,
    "limit": 50,
    "offset": 0,
    "has_next": true
  }
}
```

---

## 🔄 **Real-Time Polling Pattern**

### Recommended Implementation

```typescript
// Poll every 2-3 seconds during sync
const pollInterval = 2000

async function monitorSync(orgId: string) {
  while (true) {
    const response = await fetch(`/api/v1/cliniko/sync-logs/${orgId}?limit=1`)
    const data = await response.json()
    
    if (data.logs.length > 0) {
      const log = data.logs[0]
      
      // Update UI with progress
      updateProgress(log)
      
      // Check completion
      if (log.status === 'completed' || log.status === 'failed') {
        break
      }
    }
    
    await sleep(pollInterval)
  }
}
```

### Progress Calculation

```typescript
function calculateProgress(log: SyncLog): number {
  if (log.metadata?.progress_percent) {
    return log.metadata.progress_percent
  }
  
  if (log.records_processed > 0) {
    return (log.records_success / log.records_processed) * 100
  }
  
  return 0
}
```

---

## 🚨 **Error Handling**

### Error Response Format

```json
{
  "error": true,
  "message": "Sync failed: Invalid Cliniko credentials",
  "error_code": "CLINIKO_AUTH_FAILED",
  "details": {
    "organization_id": 123,
    "operation_type": "full_patients",
    "failed_at": "2024-01-15T10:32:15Z"
  }
}
```

### Common Error Codes

| Code | Description | Action |
|------|-------------|--------|
| `CLINIKO_AUTH_FAILED` | Invalid API credentials | Update Cliniko settings |
| `CLINIKO_RATE_LIMITED` | API rate limit exceeded | Retry after delay |
| `DATABASE_CONSTRAINT_ERROR` | Unique constraint violation | Run database migration |
| `SYNC_ALREADY_RUNNING` | Another sync in progress | Wait for completion |
| `ORGANIZATION_NOT_FOUND` | Invalid organization ID | Verify organization exists |

---

## 🔒 **Authentication**

### Headers Required

```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

### Permissions Required

- **Admin Role**: Full access to all sync endpoints
- **Organization Manager**: Access to own organization only
- **Viewer Role**: Read-only access to sync logs and status

---

## 📈 **Rate Limits**

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /sync-all/` | 1 per org | 5 minutes |
| `GET /sync-logs/` | 60 requests | 1 minute |
| `GET /status/` | 120 requests | 1 minute |
| `GET /test-connection/` | 10 requests | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248600
```

---

## 🧪 **Testing Endpoints**

### Development Testing

```bash
# Test connection
curl -X GET "http://localhost:8000/api/v1/cliniko/test-connection/123" \
  -H "Authorization: Bearer {token}"

# Start sync
curl -X POST "http://localhost:8000/api/v1/cliniko/sync-all/123" \
  -H "Authorization: Bearer {token}"

# Monitor progress
curl -X GET "http://localhost:8000/api/v1/cliniko/sync-logs/123?limit=1" \
  -H "Authorization: Bearer {token}"
```

### Production Testing

```bash
# Replace with your production URL
API_BASE="https://your-api.routiq.com"

# Full sync test
curl -X POST "$API_BASE/api/v1/cliniko/sync-all/123" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

---

## 📊 **Performance Metrics**

### Expected Response Times

| Endpoint | Typical Response Time |
|----------|----------------------|
| `POST /sync-all/` | < 200ms (async start) |
| `GET /sync-logs/` | < 100ms |
| `GET /status/` | < 150ms |
| `GET /test-connection/` | 2-5 seconds |

### Sync Performance

| Patient Count | Expected Duration | Memory Usage |
|---------------|-------------------|--------------|
| < 100 | 5-15 seconds | < 50MB |
| 100-500 | 15-45 seconds | 50-150MB |
| 500+ | 45-120 seconds | 150-300MB |

---

## 🔧 **Webhook Support** (Future Enhancement)

Coming soon: Real-time webhooks for sync events

```json
{
  "event": "sync.completed",
  "organization_id": 123,
  "data": {
    "patients_synced": 648,
    "duration": "4m 22s",
    "success_rate": 100.0
  }
}
``` 