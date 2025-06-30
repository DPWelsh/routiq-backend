# Sync Management Guide

## Overview

The Routiq Backend API provides comprehensive sync management for integrating with external healthcare systems like Cliniko. This guide covers all sync-related endpoints, monitoring, and best practices.

## Sync Types

### 1. Manual Sync
Triggered on-demand via API calls for immediate data synchronization.

### 2. Scheduled Sync
Automatic hourly synchronization managed by the built-in scheduler.

### 3. Comprehensive Sync
Full patient and appointment data synchronization with proper relationship mapping.

## Sync Endpoints

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

**Response:**
```json
{
  "message": "Scheduled sync triggered successfully",
  "sync_started": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Start Sync with Progress Tracking
```http
POST /api/v1/sync/start/{organization_id}?sync_mode=comprehensive
Authorization: Bearer <token>
```

**Query Parameters:**
- `sync_mode`: `active` (default) or `comprehensive`

**Response:**
```json
{
  "message": "Sync started successfully in comprehensive mode",
  "sync_id": "sync_org_123_20250630_120000",
  "sync_mode": "comprehensive",
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "started_at": "2025-06-30T12:00:00.000Z"
}
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
  "records_total": 650,
  "current_operation": "Syncing patient appointments",
  "errors": []
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

### Cleanup Stale Syncs
```http
POST /api/v1/sync/cleanup
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Cleaned up 2 stale syncs",
  "cleaned_syncs": 2,
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

## Cliniko-Specific Sync

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
  "credentials_valid": true,
  "sync_status": "healthy"
}
```

### Test Cliniko Connection
```http
GET /api/v1/cliniko/test-connection/{organization_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "connection_status": "healthy",
  "api_region": "au4",
  "response_time_ms": 245,
  "test_timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Import Patients from Cliniko
```http
POST /api/v1/cliniko/import-patients/{organization_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Patient import started successfully",
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "import_id": "import_123456",
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

## Sync Status Monitoring

### Sync Status Values

| Status | Description |
|--------|-------------|
| `starting` | Sync is initializing |
| `running` | Sync is actively processing data |
| `completed` | Sync finished successfully |
| `failed` | Sync encountered an error |
| `cancelled` | Sync was manually cancelled |

### Progress Tracking

The API provides real-time progress tracking for long-running sync operations:

```javascript
async function monitorSync(syncId) {
  let status = 'starting';
  
  while (status === 'starting' || status === 'running') {
    const response = await fetch(`/api/v1/sync/progress/${syncId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const progress = await response.json();
    status = progress.status;
    
    console.log(`Progress: ${progress.progress_percentage}% - ${progress.current_step}`);
    
    if (status === 'running') {
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
    }
  }
  
  console.log(`Sync ${status}`);
}
```

## Automated Sync Scheduler

### Configuration

The scheduler is configured via environment variables:

```bash
ENABLE_SYNC_SCHEDULER=true
SYNC_INTERVAL_MINUTES=60
```

### Scheduler Behavior

- **Runs every hour** by default
- **Processes all organizations** with active patients
- **Prevents duplicate syncs** for the same organization
- **Handles errors gracefully** with retry logic
- **Logs all operations** for monitoring

### Monitoring Scheduler

Check scheduler logs in Railway for messages like:

```
🔄 Starting sync scheduler with 60 minute intervals
✅ Sync scheduler started successfully
Starting automated sync for organization org_2xwHiNrj68eaRUlX10anlXGvzX7
✅ Comprehensive sync completed: - Patients: 651 processed - Appointments: 296 processed
```

## Error Handling

### Common Sync Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Credentials not found` | Missing API credentials | Configure Cliniko credentials |
| `API connection failed` | Network or API issues | Check Cliniko API status |
| `Rate limit exceeded` | Too many API calls | Wait and retry |
| `Invalid data format` | Malformed API response | Contact support |
| `Database error` | Database connectivity | Check database status |

### Error Response Format

```json
{
  "success": false,
  "error": "Sync failed",
  "details": {
    "error_type": "api_connection_failed",
    "message": "Unable to connect to Cliniko API",
    "retry_after": 300,
    "error_code": "CLINIKO_API_TIMEOUT"
  },
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

## Best Practices

### 1. Sync Frequency
- **Manual syncs**: Use sparingly for immediate updates
- **Scheduled syncs**: Rely on hourly automation
- **Monitor performance**: Check sync duration and success rates

### 2. Error Handling
```javascript
async function safeTriggerSync(orgId) {
  try {
    const response = await fetch(`/api/v1/cliniko/sync/${orgId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || 'Sync failed');
    }

    return result;
  } catch (error) {
    console.error('Sync failed:', error.message);
    
    // Handle specific error types
    if (error.message.includes('Rate limit')) {
      // Wait and retry
      await new Promise(resolve => setTimeout(resolve, 60000));
      return safeTriggerSync(orgId);
    }
    
    throw error;
  }
}
```

### 3. Monitoring and Alerting

```javascript
// Check sync health
async function checkSyncHealth(orgId) {
  const history = await fetch(`/api/v1/sync/history/${orgId}?limit=5`);
  const data = await history.json();
  
  const recentFailures = data.recent_syncs.filter(sync => 
    sync.status === 'failed' && 
    new Date(sync.started_at) > new Date(Date.now() - 24 * 60 * 60 * 1000)
  ).length;
  
  if (recentFailures > 2) {
    console.warn(`High failure rate: ${recentFailures} failures in last 24h`);
    // Send alert
  }
  
  const avgDuration = data.average_sync_duration_seconds;
  if (avgDuration > 600) { // 10 minutes
    console.warn(`Slow sync performance: ${avgDuration}s average`);
    // Send alert
  }
}
```

## Integration Examples

### React Hook for Sync Management

```typescript
import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';

export function useSyncManager(organizationId: string) {
  const { getToken } = useAuth();
  const [syncStatus, setSyncStatus] = useState<string>('idle');
  const [progress, setProgress] = useState<number>(0);

  const triggerSync = async () => {
    const token = await getToken();
    
    const response = await fetch(`/api/v1/cliniko/sync/${organizationId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      setSyncStatus('running');
      // Start monitoring progress
      monitorProgress();
    }
  };

  const monitorProgress = async () => {
    // Implementation for progress monitoring
  };

  return {
    syncStatus,
    progress,
    triggerSync
  };
}
```

### Python Sync Client

```python
import requests
import time
from typing import Dict, Any

class RoutiqSyncClient:
    def __init__(self, token: str, org_id: str):
        self.token = token
        self.org_id = org_id
        self.base_url = "https://routiq-backend-prod.up.railway.app"
        
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Organization-ID": self.org_id,
            "Content-Type": "application/json"
        }
    
    def trigger_sync(self) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/cliniko/sync/{self.org_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_sync_status(self) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/v1/sync/scheduler/status",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_sync_completion(self, sync_id: str, timeout: int = 600) -> Dict[str, Any]:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.base_url}/api/v1/sync/progress/{sync_id}",
                headers=self._headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] in ['completed', 'failed']:
                    return data
                    
                print(f"Progress: {data['progress_percentage']}%")
            
            time.sleep(5)
        
        raise TimeoutError("Sync did not complete within timeout")

# Usage
client = RoutiqSyncClient("your-token", "org_123")
result = client.trigger_sync()
print(f"Sync started: {result['message']}")
```

## Troubleshooting

### Common Issues

1. **Sync appears stuck**
   - Check sync progress endpoint
   - Use cleanup endpoint to clear stale syncs
   - Monitor Railway logs for errors

2. **High failure rate**
   - Check Cliniko API credentials
   - Verify network connectivity
   - Review sync history for error patterns

3. **Slow sync performance**
   - Monitor database performance
   - Check for large datasets
   - Consider sync optimization

4. **Scheduler not running**
   - Verify environment variables
   - Check Railway deployment logs
   - Ensure scheduler startup succeeded

### Debug Commands

```bash
# Check sync status
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/sync/scheduler/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: $ORG_ID"

# Get recent sync history
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/sync/history/$ORG_ID?limit=5" \
  -H "Authorization: Bearer $TOKEN"

# Clean up stale syncs
curl -X POST "https://routiq-backend-prod.up.railway.app/api/v1/sync/cleanup" \
  -H "Authorization: Bearer $TOKEN"

# Test Cliniko connection
curl -X GET "https://routiq-backend-prod.up.railway.app/api/v1/cliniko/test-connection/$ORG_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

*For more information, see the [main API documentation](API_DOCUMENTATION.md)* 