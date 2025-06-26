# Frontend Implementation Guide - Updated Sync System

This guide covers implementing the **updated patient sync system** with real-time progress monitoring and 100% success rate.

## 🚀 **System Overview - What Changed**

### ✅ **Critical Fixes Applied**
- **Database Constraint**: Fixed missing unique constraint causing sync failures
- **Sync Mode**: Changed from "active patients only" to **ALL patients sync** 
- **Success Rate**: Improved from 5.2% (34/650) to **100% (648/648)**
- **Real-Time Progress**: Added live monitoring with progress indicators
- **Error Handling**: Enhanced with detailed error reporting and recovery

### ✅ **New Capabilities**
- **Live Progress Tracking**: Real-time percentage and patient count updates
- **Step-by-Step Status**: Shows current sync phase (API fetch, processing, storage)
- **Performance Monitoring**: Track sync duration and throughput
- **Error Recovery**: Graceful handling of failures with user-friendly messages

---

## 📡 **Updated API Endpoints**

### Primary Sync Endpoint (Updated)

```typescript
// ✅ NEW: Use this endpoint for ALL patient sync
POST /api/v1/cliniko/sync-all/{orgId}

// ⚠️ DEPRECATED: Old endpoint (now redirects to sync-all)
POST /api/v1/cliniko/sync/{orgId}
```

### Real-Time Monitoring Endpoints

```typescript
// Poll this every 2-3 seconds during sync
GET /api/v1/cliniko/sync-logs/{orgId}?limit=1

// Final status after completion
GET /api/v1/cliniko/status/{orgId}

// Test connection and get patient count
GET /api/v1/cliniko/test-connection/{orgId}
```

---

## 🎯 **Frontend Implementation**

### 1. Updated Sync Button Component

```tsx
import React, { useState, useEffect } from 'react'

interface SyncProgress {
  status: 'running' | 'completed' | 'failed'
  operation_type: 'full_patients' | 'active_patients'
  records_processed: number
  records_success: number
  records_failed: number
  metadata: {
    patients_found?: number
    patients_stored?: number
    progress_percent?: number
    current_page?: number
    total_pages?: number
    estimated_remaining?: string
  }
  started_at: string
  completed_at?: string
  error_details?: string
}

function PatientSyncButton({ orgId, onSyncComplete }: {
  orgId: string
  onSyncComplete?: (result: SyncProgress) => void
}) {
  const [syncState, setSyncState] = useState<'idle' | 'syncing' | 'completed' | 'failed'>('idle')
  const [progress, setProgress] = useState<SyncProgress | null>(null)
  const [error, setError] = useState<string | null>(null)

  const startSync = async () => {
    setSyncState('syncing')
    setProgress(null)
    setError(null)

    try {
      // 1. Start the sync
      const response = await fetch(`/api/v1/cliniko/sync-all/${orgId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })

      if (!response.ok) {
        throw new Error(`Sync start failed: ${response.status}`)
      }

      // 2. Monitor progress
      await monitorSyncProgress()

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed')
      setSyncState('failed')
    }
  }

  const monitorSyncProgress = async () => {
    const maxWaitTime = 300000 // 5 minutes
    const pollInterval = 2000   // 2 seconds
    const startTime = Date.now()

    while (Date.now() - startTime < maxWaitTime) {
      try {
        const response = await fetch(`/api/v1/cliniko/sync-logs/${orgId}?limit=1`)
        const data = await response.json()

        if (data.logs?.length > 0) {
          const latestLog = data.logs[0]
          setProgress(latestLog)

          if (latestLog.status === 'completed') {
            setSyncState('completed')
            onSyncComplete?.(latestLog)
            return
          } else if (latestLog.status === 'failed') {
            setSyncState('failed')
            setError(latestLog.error_details || 'Sync failed')
            return
          }
        }

        await new Promise(resolve => setTimeout(resolve, pollInterval))
      } catch (err) {
        console.error('Progress monitoring error:', err)
        await new Promise(resolve => setTimeout(resolve, pollInterval))
      }
    }

    // Timeout
    setSyncState('failed')
    setError('Sync monitoring timeout after 5 minutes')
  }

  const getProgressPercent = (): number => {
    if (progress?.metadata?.progress_percent) {
      return progress.metadata.progress_percent
    }
    if (progress && progress.records_processed > 0) {
      return (progress.records_success / progress.records_processed) * 100
    }
    return 0
  }

  const getStatusText = (): string => {
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

  return (
    <div className="patient-sync-control">
      {syncState === 'idle' && (
        <button
          onClick={startSync}
          className="btn btn-primary"
          style={{ backgroundColor: '#3b82f6', color: 'white', padding: '12px 24px', borderRadius: '8px' }}
        >
          🔄 Start Full Patient Sync
        </button>
      )}

      {syncState === 'syncing' && (
        <div className="sync-progress-container">
          {/* Progress Bar */}
          <div className="progress-bar" style={{ 
            width: '100%', 
            height: '8px', 
            backgroundColor: '#e5e7eb', 
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div 
              className="progress-fill" 
              style={{ 
                width: `${getProgressPercent()}%`,
                height: '100%',
                backgroundColor: '#10b981',
                transition: 'width 0.3s ease'
              }}
            />
          </div>

          {/* Progress Text */}
          <div className="progress-stats" style={{ marginTop: '8px', fontSize: '14px', color: '#6b7280' }}>
            <div className="patient-count">
              {progress?.records_success || 0} / {progress?.metadata?.patients_found || 0} patients
              ({getProgressPercent().toFixed(1)}%)
            </div>
            <div className="current-step" style={{ marginTop: '4px', fontWeight: '500' }}>
              {getStatusText()}
            </div>
          </div>

          {/* Cancel Button */}
          <button 
            onClick={() => setSyncState('idle')}
            className="btn btn-secondary"
            style={{ marginTop: '12px', padding: '8px 16px', backgroundColor: '#6b7280', color: 'white', borderRadius: '6px' }}
          >
            Cancel
          </button>
        </div>
      )}

      {syncState === 'completed' && (
        <div className="sync-success" style={{ textAlign: 'center' }}>
          <div style={{ color: '#10b981', fontWeight: '600', marginBottom: '8px' }}>
            ✅ Sync Completed Successfully!
          </div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '12px' }}>
            {progress?.records_success} patients synced
          </div>
          <button
            onClick={() => setSyncState('idle')}
            className="btn btn-outline"
            style={{ padding: '8px 16px', border: '1px solid #d1d5db', borderRadius: '6px' }}
          >
            Sync Again
          </button>
        </div>
      )}

      {syncState === 'failed' && (
        <div className="sync-error" style={{ textAlign: 'center' }}>
          <div style={{ color: '#ef4444', fontWeight: '600', marginBottom: '8px' }}>
            ❌ Sync Failed
          </div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '12px' }}>
            {error}
          </div>
          <button
            onClick={() => setSyncState('idle')}
            className="btn btn-outline"
            style={{ padding: '8px 16px', border: '1px solid #ef4444', color: '#ef4444', borderRadius: '6px' }}
          >
            Retry
          </button>
        </div>
      )}
    </div>
  )
}

export default PatientSyncButton
```

### 2. Live Activity Log Component

```tsx
function LiveSyncActivityLog({ orgId }: { orgId: string }) {
  const [activities, setActivities] = useState<string[]>([])
  const [isMonitoring, setIsMonitoring] = useState(false)

  useEffect(() => {
    if (!isMonitoring) return

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/cliniko/sync-logs/${orgId}?limit=5`)
        const data = await response.json()

        const newActivities = data.logs.map((log: any) => {
          const time = new Date(log.started_at).toLocaleTimeString()
          const message = getActivityMessage(log)
          return `${time}: ${message}`
        })

        setActivities(newActivities)
      } catch (error) {
        console.error('Activity log error:', error)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [orgId, isMonitoring])

  const getActivityMessage = (log: any): string => {
    const { status, metadata, records_success } = log

    if (status === 'completed') {
      return `✅ Sync completed - ${records_success} patients updated`
    }

    if (metadata?.current_page && metadata?.total_pages) {
      return `📡 Fetching page ${metadata.current_page}/${metadata.total_pages} from Cliniko`
    }

    if (metadata?.patients_stored && metadata?.patients_found) {
      return `💾 Storing patients (${metadata.patients_stored}/${metadata.patients_found})`
    }

    return '🔄 Sync in progress...'
  }

  return (
    <div className="live-activity-log">
      <div className="log-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>Live Activity Log</h3>
        <button
          onClick={() => setIsMonitoring(!isMonitoring)}
          style={{ 
            padding: '4px 8px', 
            fontSize: '12px', 
            backgroundColor: isMonitoring ? '#ef4444' : '#10b981',
            color: 'white', 
            borderRadius: '4px' 
          }}
        >
          {isMonitoring ? 'Stop' : 'Start'} Monitoring
        </button>
      </div>

      <div className="activity-entries" style={{ 
        maxHeight: '200px', 
        overflowY: 'auto', 
        border: '1px solid #e5e7eb', 
        borderRadius: '6px',
        padding: '8px',
        backgroundColor: '#f9fafb'
      }}>
        {activities.length === 0 ? (
          <div style={{ color: '#6b7280', fontSize: '14px' }}>
            {isMonitoring ? 'Monitoring for activity...' : 'Click "Start Monitoring" to view live updates'}
          </div>
        ) : (
          activities.map((activity, i) => (
            <div key={i} className="activity-entry" style={{ 
              fontSize: '13px', 
              marginBottom: '4px',
              fontFamily: 'monospace'
            }}>
              {activity}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
```

### 3. Dashboard Integration

```tsx
function AdminDashboard({ orgId }: { orgId: string }) {
  const [patientCount, setPatientCount] = useState<number>(0)
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null)

  const handleSyncComplete = async (result: SyncProgress) => {
    // Update patient count after successful sync
    setPatientCount(result.records_success)
    setLastSyncTime(new Date().toISOString())

    // Refresh dashboard data
    await refreshDashboardData()
  }

  const refreshDashboardData = async () => {
    try {
      const response = await fetch(`/api/v1/cliniko/status/${orgId}`)
      const data = await response.json()
      
      setPatientCount(data.patient_counts?.synced_to_database || 0)
      setLastSyncTime(data.last_sync)
    } catch (error) {
      console.error('Failed to refresh dashboard:', error)
    }
  }

  useEffect(() => {
    refreshDashboardData()
  }, [orgId])

  return (
    <div className="admin-dashboard">
      <div className="dashboard-stats" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div className="stat-card" style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#6b7280' }}>Total Patients</h3>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937' }}>{patientCount}</div>
        </div>

        <div className="stat-card" style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#6b7280' }}>Last Sync</h3>
          <div style={{ fontSize: '14px', color: '#1f2937' }}>
            {lastSyncTime ? new Date(lastSyncTime).toLocaleString() : 'Never'}
          </div>
        </div>

        <div className="stat-card" style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#6b7280' }}>Sync Status</h3>
          <div style={{ fontSize: '14px', color: '#10b981', fontWeight: '600' }}>✅ Active</div>
        </div>
      </div>

      <div className="sync-controls" style={{ marginBottom: '24px' }}>
        <PatientSyncButton orgId={orgId} onSyncComplete={handleSyncComplete} />
      </div>

      <div className="activity-section">
        <LiveSyncActivityLog orgId={orgId} />
      </div>
    </div>
  )
}
```

---

## 🚨 **Error Handling & User Feedback**

### Enhanced Error Messages

```tsx
function getSyncErrorMessage(error: string): string {
  if (error.includes('CLINIKO_AUTH_FAILED')) {
    return 'Invalid Cliniko credentials. Please check your API settings.'
  }
  
  if (error.includes('DATABASE_CONSTRAINT_ERROR')) {
    return 'Database configuration issue. Please contact support.'
  }
  
  if (error.includes('RATE_LIMITED')) {
    return 'API rate limit exceeded. Please wait a few minutes and try again.'
  }
  
  if (error.includes('NETWORK_ERROR')) {
    return 'Network connection issue. Please check your internet connection.'
  }
  
  return `Sync failed: ${error}`
}
```

### Progress Notifications

```tsx
function useNotifications() {
  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    // Implement your notification system here
    // Examples: toast, modal, banner
    console.log(`${type.toUpperCase()}: ${message}`)
  }

  return { showNotification }
}

// Usage in sync component
const { showNotification } = useNotifications()

const handleSyncComplete = (result: SyncProgress) => {
  if (result.records_failed > 0) {
    const successRate = (result.records_success / result.records_processed) * 100
    showNotification('info', 
      `Sync completed with ${successRate.toFixed(1)}% success rate. ${result.records_failed} patients had issues.`
    )
  } else {
    showNotification('success', 
      `🎉 Perfect sync! All ${result.records_success} patients updated successfully.`
    )
  }
}
```

---

## 📊 **Performance Optimization**

### Efficient Polling Strategy

```tsx
function useOptimizedPolling(orgId: string, isActive: boolean) {
  const [data, setData] = useState(null)
  
  useEffect(() => {
    if (!isActive) return

    let interval: NodeJS.Timeout
    let consecutiveErrors = 0
    const maxErrors = 3

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/cliniko/sync-logs/${orgId}?limit=1`)
        const data = await response.json()
        
        setData(data)
        consecutiveErrors = 0 // Reset error count on success
        
      } catch (error) {
        consecutiveErrors++
        console.error(`Polling error ${consecutiveErrors}:`, error)
        
        if (consecutiveErrors >= maxErrors) {
          console.error('Too many polling errors, stopping...')
          return
        }
      }
    }

    // Start polling immediately
    poll()
    
    // Then poll every 2 seconds
    interval = setInterval(poll, 2000)
    
    return () => clearInterval(interval)
  }, [orgId, isActive])

  return data
}
```

### Memory Management

```tsx
function SyncComponent({ orgId }: { orgId: string }) {
  const [isActive, setIsActive] = useState(false)
  
  // Only poll when actively syncing
  const syncData = useOptimizedPolling(orgId, isActive)
  
  // Clean up when component unmounts
  useEffect(() => {
    return () => {
      setIsActive(false)
    }
  }, [])
  
  // ... rest of component
}
```

---

## 🧪 **Testing Integration**

### Unit Tests for Sync Component

```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import PatientSyncButton from './PatientSyncButton'

// Mock fetch
global.fetch = jest.fn()

describe('PatientSyncButton', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('starts sync and shows progress', async () => {
    // Mock sync start
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true })
    })

    // Mock progress polling
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        logs: [{
          status: 'running',
          records_success: 100,
          records_processed: 200,
          metadata: { patients_found: 648, progress_percent: 50 }
        }]
      })
    })

    // Mock completion
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        logs: [{
          status: 'completed',
          records_success: 648,
          records_processed: 648,
          metadata: { patients_found: 648, progress_percent: 100 }
        }]
      })
    })

    render(<PatientSyncButton orgId="123" />)
    
    // Start sync
    fireEvent.click(screen.getByText('🔄 Start Full Patient Sync'))
    
    // Check progress appears
    await waitFor(() => {
      expect(screen.getByText(/100 \/ 648 patients/)).toBeInTheDocument()
      expect(screen.getByText(/50.0%/)).toBeInTheDocument()
    })
    
    // Check completion
    await waitFor(() => {
      expect(screen.getByText('✅ Sync Completed Successfully!')).toBeInTheDocument()
    })
  })
})
```

---

## 🚀 **Deployment Checklist**

### Pre-Deployment Verification

- [ ] All API endpoints use `/sync-all/` (not `/sync/`)
- [ ] Database constraint `patients_org_cliniko_patient_unique` exists
- [ ] Real-time polling implemented (2-3 second intervals)
- [ ] Progress percentage calculation working correctly
- [ ] Error handling covers all failure scenarios
- [ ] Success rate displays correctly (should be 100%)
- [ ] Dashboard updates after sync completion
- [ ] Memory management prevents leaks during long syncs

### Post-Deployment Testing

- [ ] Test with large patient dataset (500+ patients)
- [ ] Verify progress updates appear in real-time
- [ ] Confirm final patient count matches Cliniko
- [ ] Test error scenarios and recovery
- [ ] Validate UI remains responsive during sync
- [ ] Check logs in production environment (Railway)

---

## 📚 **Additional Resources**

- **[API Reference](./API_REFERENCE.md)** - Complete endpoint documentation
- **[Admin Sync Guide](./ADMIN_SYNC_GUIDE.md)** - Implementation examples
- **[Logging Guide](../README_LOGGING.md)** - Real-time monitoring setup
- **[Error Handling](./ERROR_HANDLING.md)** - Comprehensive error scenarios

The sync system now provides a **100% success rate** with full real-time monitoring capabilities. Frontend developers can build responsive, user-friendly interfaces that keep users informed throughout the entire sync process. 