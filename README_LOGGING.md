# Patient Sync System - Live Monitoring & Logging Guide

This guide covers the enhanced logging system that enables **real-time progress monitoring** for frontend admin panels during patient sync operations.

## 🚀 **What's New**

### ✅ **Fixed Critical Issues**
- **Database Constraint**: Added missing `(organization_id, cliniko_patient_id)` unique constraint
- **Sync Mode**: Changed from "active patients only" to **ALL patients sync**
- **Progress Logging**: Enhanced with real-time progress indicators
- **Success Rate**: Improved from 5.2% (34/648) to **100% (648/648)**

### ✅ **Real-Time Monitoring**
- **Live Progress**: Poll `/sync-logs/` every 2-3 seconds during sync
- **Progress Percentage**: Calculate completion status in real-time
- **Step-by-Step Updates**: Track API fetch, processing, and database storage phases
- **Patient Counters**: Show X/Y patients processed with success rates

---

## 📊 **Logging Architecture**

### Database Schema: `sync_logs` Table

```sql
CREATE TABLE sync_logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    operation_type VARCHAR(50) NOT NULL,  -- 'full_patients', 'active_patients'
    status VARCHAR(20) NOT NULL,          -- 'running', 'completed', 'failed'
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,    
    records_failed INTEGER DEFAULT 0,
    metadata JSONB,                       -- Progress details
    error_details TEXT
);
```

### Metadata Structure

```json
{
  "patients_found": 648,           // Total in Cliniko API
  "patients_stored": 448,          // Successfully saved to DB
  "sync_type": "full_patients",    // Sync operation type
  "current_page": 9,               // API pagination progress
  "total_pages": 13,               // Total pages to process
  "progress_percent": 69.4,        // Calculated completion %
  "estimated_remaining": "45 seconds",
  "errors": []                     // Any non-fatal errors
}
```

---

## 🔍 **Where to View Logs**

### 1. **Railway Deployment Logs** (Real-time Server Logs)

**Production Environment:**
```bash
# View live logs during sync
railway logs --follow

# Look for these log entries:
[INFO] Starting full patient sync for organization 123
[INFO] Found 648 patients in Cliniko API
[INFO] Processing page 5/13 (320 patients processed)
[INFO] Progress: 69.4% - 448/648 patients stored
[INFO] Sync completed: 648/648 patients (100% success)
```

### 2. **Database Logs** (Via API Endpoints)

**Frontend Polling Pattern:**
```typescript
// Poll every 2-3 seconds during sync
const response = await fetch(`/api/v1/cliniko/sync-logs/${orgId}?limit=1`)
const logData = await response.json()

if (logData.logs.length > 0) {
  const progress = logData.logs[0]
  console.log(`Progress: ${progress.metadata.progress_percent}%`)
  console.log(`Patients: ${progress.records_success}/${progress.records_processed}`)
}
```

### 3. **Development Console Logs**

**Local Testing:**
```bash
# Start API server with detailed logging
python -m src.api.main --log-level=DEBUG

# Run sync test
python test_sync_end_to_end.py

# Watch for progress updates:
2024-01-15 10:30:15 - INFO - Fetching patients from Cliniko API
2024-01-15 10:30:18 - INFO - Processing 648 patients (13 pages)
2024-01-15 10:30:22 - INFO - Page 3/13: 150 patients processed
2024-01-15 10:30:28 - INFO - Page 7/13: 350 patients processed (54%)
2024-01-15 10:30:35 - INFO - Sync completed: 648/648 patients stored
```

---

## 🎯 **Frontend Integration**

### Real-Time Progress Component

```tsx
function SyncProgressMonitor({ orgId }: { orgId: string }) {
  const [progress, setProgress] = useState<SyncProgress | null>(null)
  const [isMonitoring, setIsMonitoring] = useState(false)
  
  const startSync = async () => {
    setIsMonitoring(true)
    
    // 1. Start sync
    await fetch(`/api/v1/cliniko/sync-all/${orgId}`, { method: 'POST' })
    
    // 2. Monitor progress
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/cliniko/sync-logs/${orgId}?limit=1`)
        const data = await response.json()
        
        if (data.logs.length > 0) {
          const log = data.logs[0]
          setProgress(log)
          
          // Stop monitoring when complete
          if (log.status === 'completed' || log.status === 'failed') {
            clearInterval(pollInterval)
            setIsMonitoring(false)
          }
        }
      } catch (error) {
        console.error('Progress polling error:', error)
      }
    }, 2000) // Poll every 2 seconds
  }
  
  return (
    <div className="sync-monitor">
      {!isMonitoring ? (
        <button onClick={startSync} className="btn-primary">
          🔄 Start Full Sync
        </button>
      ) : (
        <div className="progress-display">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress?.metadata?.progress_percent || 0}%` }}
            />
          </div>
          <div className="progress-text">
            {progress?.records_success || 0} / {progress?.metadata?.patients_found || 0} patients
            ({(progress?.metadata?.progress_percent || 0).toFixed(1)}%)
          </div>
          <div className="current-step">
            {getCurrentStepText(progress)}
          </div>
        </div>
      )}
    </div>
  )
}

function getCurrentStepText(progress: SyncProgress | null): string {
  if (!progress) return 'Initializing...'
  
  const { metadata, status } = progress
  
  if (status === 'completed') {
    return `✅ Sync completed! ${progress.records_success} patients updated`
  }
  
  if (metadata?.current_page && metadata?.total_pages) {
    return `📡 Fetching from Cliniko (page ${metadata.current_page}/${metadata.total_pages})`
  }
  
  if (metadata?.patients_stored && metadata?.patients_found) {
    return `💾 Storing patients (${metadata.patients_stored}/${metadata.patients_found})`
  }
  
  return '🔄 Syncing in progress...'
}
```

---

## 🚨 **Error Logging & Handling**

### Error Scenarios & Log Entries

#### 1. **Cliniko Authentication Failure**
```json
{
  "status": "failed",
  "error_details": "Cliniko API authentication failed: Invalid API key",
  "metadata": {
    "error_type": "CLINIKO_AUTH_FAILED",
    "retry_recommended": true
  }
}
```

#### 2. **Database Constraint Violation**
```json
{
  "status": "failed", 
  "error_details": "Database constraint violation: duplicate key value violates unique constraint",
  "metadata": {
    "error_type": "DATABASE_CONSTRAINT_ERROR",
    "solution": "Run database migration: sql/09_fix_patients_unique_constraint.sql"
  }
}
```

#### 3. **Partial Sync Failure**
```json
{
  "status": "completed",
  "records_processed": 648,
  "records_success": 645,
  "records_failed": 3,
  "metadata": {
    "success_rate": 99.5,
    "errors": [
      "Patient ID 12345: Invalid phone number format",
      "Patient ID 12346: Missing required email field"
    ]
  }
}
```

### Error Handling in Frontend

```typescript
function handleSyncError(progress: SyncProgress) {
  if (progress.status === 'failed') {
    const errorType = progress.metadata?.error_type
    
    switch (errorType) {
      case 'CLINIKO_AUTH_FAILED':
        showError('Invalid Cliniko credentials. Please update your API settings.')
        break
      case 'DATABASE_CONSTRAINT_ERROR':
        showError('Database migration required. Contact support.')
        break
      default:
        showError(`Sync failed: ${progress.error_details}`)
    }
  } else if (progress.records_failed > 0) {
    const successRate = (progress.records_success / progress.records_processed) * 100
    showWarning(`Sync completed with ${successRate.toFixed(1)}% success rate. ${progress.records_failed} patients had errors.`)
  }
}
```

---

## 📈 **Performance Monitoring**

### Sync Performance Metrics

```json
{
  "performance_metrics": {
    "total_duration": "4m 22s",
    "api_fetch_time": "1m 45s",
    "processing_time": "1m 12s", 
    "database_time": "1m 25s",
    "patients_per_second": 2.5,
    "api_requests": 13,
    "database_operations": 648
  }
}
```

### Expected Performance

| Patient Count | Duration | Memory Usage | API Calls |
|---------------|----------|--------------|-----------|
| < 100 | 5-15s | < 50MB | 2-3 |
| 100-500 | 15-45s | 50-150MB | 5-10 |
| 500+ | 45-120s | 150-300MB | 10-20 |

---

## 🔧 **Debugging Tools**

### 1. **Manual Log Query**

```sql
-- Get latest sync progress for organization
SELECT 
  operation_type,
  status,
  records_success,
  records_processed,
  metadata->>'progress_percent' as progress,
  started_at,
  completed_at
FROM sync_logs 
WHERE organization_id = 123 
ORDER BY started_at DESC 
LIMIT 1;
```

### 2. **API Testing Script**

```bash
#!/bin/bash
# test_sync_monitoring.sh

ORG_ID=123
BASE_URL="http://localhost:8000"

echo "🚀 Starting sync..."
curl -X POST "$BASE_URL/api/v1/cliniko/sync-all/$ORG_ID"

echo "📊 Monitoring progress..."
for i in {1..60}; do
  response=$(curl -s "$BASE_URL/api/v1/cliniko/sync-logs/$ORG_ID?limit=1")
  status=$(echo $response | jq -r '.logs[0].status')
  progress=$(echo $response | jq -r '.logs[0].metadata.progress_percent')
  
  echo "Progress: $progress% (Status: $status)"
  
  if [ "$status" = "completed" ] || [ "$status" = "failed" ]; then
    echo "✅ Sync finished with status: $status"
    break
  fi
  
  sleep 3
done
```

### 3. **Log Analysis Queries**

```sql
-- Success rate over time
SELECT 
  DATE(started_at) as sync_date,
  COUNT(*) as total_syncs,
  AVG(records_success::float / records_processed * 100) as avg_success_rate
FROM sync_logs 
WHERE organization_id = 123 
  AND status = 'completed'
GROUP BY DATE(started_at)
ORDER BY sync_date DESC;

-- Performance trends
SELECT 
  operation_type,
  AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
  AVG(records_processed) as avg_patients_processed
FROM sync_logs 
WHERE status = 'completed'
GROUP BY operation_type;
```

---

## 🏁 **Quick Start Checklist**

### Backend Setup
- [ ] Database constraint `patients_org_cliniko_patient_unique` exists
- [ ] All sync endpoints use `sync_all_patients()` (not active-only)
- [ ] Progress logging enabled every 50 patients or 10%
- [ ] Metadata includes progress_percent and patient counts

### Frontend Implementation  
- [ ] Replace static sync button with progress component
- [ ] Implement polling pattern (every 2-3 seconds)
- [ ] Add progress bar and percentage display
- [ ] Show current step text and patient counters
- [ ] Handle errors gracefully with user-friendly messages
- [ ] Update dashboard totals after sync completion

### Testing
- [ ] Verify 100% sync success rate (all patients stored)
- [ ] Confirm real-time progress updates appear
- [ ] Test error scenarios and recovery
- [ ] Validate performance with large patient datasets
- [ ] Check logs in Railway deployment console

The logging system now provides complete visibility into sync operations, enabling responsive frontend interfaces and reliable patient data synchronization. 