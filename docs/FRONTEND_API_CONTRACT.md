# 🎯 Frontend API Contract - Source of Truth

**Version:** Backend v1.3  
**Updated:** December 2024  
**Status:** ✅ AUTHORITATIVE - Backend is source of truth

This document defines the **exact API contract** that the backend provides. Frontend must match these **exact property names and method signatures**.

---

## 🚨 **Critical Fixes Needed**

The following frontend errors must be fixed by updating to match backend property names:

### **Property Name Mismatches:**
| ❌ Frontend Expects | ✅ Backend Returns | Fix Required |
|-------------------|------------------|-------------|
| `sync_in_progress` | `sync_running` | Update frontend |
| `last_sync` | `last_sync_time` | Update frontend |
| `clerk_api_connected` | `connected` | Update frontend |
| `database_counts` | Not provided | Remove or handle missing |

### **Method Name Mismatches:**
| ❌ Frontend Calls | ✅ Backend Provides | Fix Required |
|-------------------|------------------|-------------|
| `triggerClerkSync()` | `triggerSync()` | Update frontend method name |
| `getDatabaseSummary()` | `get_database_summary()` endpoint | Update API call |

---

## 📊 **1. Sync Status API**

### **Endpoint:** `GET /api/v1/sync-manager/scheduler/status`

**Exact Response Structure:**
```typescript
interface SchedulerStatusResponse {
  organization_id: string;
  sync_running: boolean;           // ✅ NOT sync_in_progress  
  last_sync_time: string | null;   // ✅ NOT last_sync
  scheduler_active: boolean;
  message: string;
}
```

**Example Response:**
```json
{
  "organization_id": "org_123",
  "sync_running": false,
  "last_sync_time": "2024-12-30T10:15:00Z",
  "scheduler_active": true,
  "message": "Scheduler status retrieved successfully"
}
```

**Frontend Usage:**
```typescript
// ✅ CORRECT - Use these exact property names
const response = await api.get(`/sync-manager/scheduler/status`);
const isRunning = response.sync_running;        // NOT sync_in_progress
const lastSync = response.last_sync_time;       // NOT last_sync
const isActive = response.scheduler_active;
```

---

## 👥 **2. Clerk Admin API**

### **Trigger Sync:** `POST /api/v1/clerk-admin/sync`

**Method Name:**
```typescript
// ✅ CORRECT
async triggerSync(): Promise<SyncTriggerResponse>

// ❌ WRONG - This method doesn't exist
async triggerClerkSync(): Promise<SyncTriggerResponse>
```

**Response Structure:**
```typescript
interface SyncTriggerResponse {
  success: boolean;
  message: string;
  sync_id: string | null;
  estimated_duration: string | null;
}
```

### **Sync Status:** `GET /api/v1/clerk-admin/status`

**Response Structure:**
```typescript
interface ClerkSyncStatusResponse {
  clerk_api_connected: boolean;    // ✅ Backend provides this
  database_counts: {               // ✅ Backend provides this
    users: number;
    organizations: number;
    organization_members: number;
  };
  last_sync: string | null;        // ✅ Backend provides this
  sync_in_progress: boolean;       // ✅ Backend provides this
}
```

### **Database Summary:** `GET /api/v1/clerk-admin/database-summary`

**Method Name:**
```typescript
// ✅ CORRECT
async getDatabaseSummary(): Promise<DatabaseSummaryResponse>
```

**Response Structure:**
```typescript
interface DatabaseSummaryResponse {
  users: {
    total_users: number;
    users_last_7_days: number;
    users_with_login: number;
  };
  organizations: {
    total_organizations: number;
    orgs_last_7_days: number;
    active_organizations: number;
  };
  memberships: {
    total_memberships: number;
    active_memberships: number;
    orgs_with_members: number;
    users_with_orgs: number;
  };
  role_distribution: Array<{
    role: string;
    count: number;
  }>;
}
```

---

## 🎯 **3. Reengagement API**

### **Risk Metrics:** `GET /api/v1/reengagement/{org_id}/risk-metrics`

**Response Structure:**
```typescript
interface RiskMetricsResponse {
  organization_id: string;
  summary: {
    total_patients: number;
    engagement_distribution: {
      active: number;                // Recent activity or upcoming appointments
      dormant: number;               // Had engagement but gone quiet
      stale: number;                 // Never had real engagement
    };
    risk_distribution: {
      high: number;                  // Poor adherence or long gaps
      medium: number;                // Some concerning patterns  
      low: number;                   // Good engagement and adherence
    };
    action_priorities: {
      urgent: number;                // Dormant + High Risk (Priority 1)
      important: number;             // Active + High Risk OR Dormant + Medium Risk (Priority 2)
      monitor: number;               // Any Medium Risk (Priority 3) 
      maintain: number;              // Active + Low Risk, Stale (Priority 4)
    };
    avg_risk_score: number;
  };
  patients: PatientRiskData[];
  view_version: string;            // "v1.4-cleaner-business-logic"
  calculated_at: string;
  timestamp: string;
}
```

**Patient Risk Data:**
```typescript
interface PatientRiskData {
  patient_id: string;
  patient_name: string;
  email: string;
  phone: string;
  is_active: boolean;
  activity_status: string;
  
  // === CLEANER BUSINESS CLASSIFICATIONS ===
  engagement_status: "active" | "dormant" | "stale";
  risk_level: "high" | "medium" | "low";
  risk_score: number;              // 0-100 for sorting
  
  days_since_last_contact: number | null;
  days_to_next_appointment: number | null;
  last_appointment_date: string | null;
  next_appointment_time: string | null;
  last_communication_date: string | null;
  recent_appointment_count: number;
  upcoming_appointment_count: number;
  total_appointment_count: number;
  missed_appointments_90d: number;
  scheduled_appointments_90d: number;
  attendance_rate_percent: number | null;
  conversations_90d: number;
  last_conversation_sentiment: string;
  action_priority: number;         // 1-4 (1=most urgent)
  is_stale: boolean;
  recommended_action: string;
  contact_success_prediction: "very_high" | "high" | "medium" | "low" | "very_low";
  attendance_benchmark: "above_industry_avg" | "at_industry_avg" | "below_industry_avg";
  engagement_benchmark: "good_engagement" | "poor_engagement" | "no_engagement";
}
```

**New Action Recommendations:**
```typescript
type RecommendedAction = 
  | "NEW: Schedule initial consultation"                          // Stale patients
  | "URGENT: Call immediately - high-risk dormant patient"       // Dormant + High Risk
  | "PRIORITY: Address adherence issues while engaged"           // Active + High Risk  
  | "FOLLOW-UP: Re-engage dormant patient"                       // Dormant + Medium/Low Risk
  | "MONITOR: Check in and prevent issues"                       // Any Medium Risk
  | "MAINTAIN: Continue current care plan";                      // Active + Low Risk
```

---

## 🏥 **4. Patients API**

### **Enhanced Patient List:** `GET /api/v1/patients/{org_id}/list`

**Query Parameters:**
```typescript
interface PatientListParams {
  page?: number;                   // Default: 1
  limit?: number;                  // Default: 50, max: 200
  search?: string;                 // Search name, email, phone, Cliniko ID
  active_only?: boolean;           // Default: true
  engagement_filter?: "engaged" | "inactive" | "never_engaged";
}
```

**Response Structure:**
```typescript
interface EnhancedPatientListResponse {
  organization_id: string;
  patients: EnhancedPatientData[];
  pagination: {
    page: number;
    limit: number;
    total_patients: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  filters_applied: PatientListParams;
  timestamp: string;
}
```

### **Engagement Statistics:** `GET /api/v1/patients/{org_id}/engagement-stats`

**Response Structure:**
```typescript
interface EngagementStatsResponse {
  organization_id: string;
  total_active_patients: number;
  engagement_breakdown: Array<{
    status: "engaged" | "inactive" | "never_engaged";
    patient_count: number;
    percentage: number;
    avg_recent_appointments: number;
    avg_upcoming_appointments: number;
    avg_total_appointments: number;
  }>;
  timestamp: string;
}
```

---

## 🔧 **5. Sync Dashboard API**

### **Dashboard Data:** `GET /api/v1/sync/dashboard/{org_id}`

**Response Structure:**
```typescript
interface SyncDashboardResponse {
  organization_id: string;
  current_sync: {
    sync_id: string;
    status: string;
    progress_percentage: number;
    current_step: string;
    patients_found: number;
    appointments_found: number;
    active_patients_identified: number;
    active_patients_stored: number;
  } | null;
  patient_stats: {
    total_patients: number;
    active_patients: number;
    patients_with_upcoming: number;
    patients_with_recent: number;
    last_sync_time: string | null;
  };
  last_sync: {
    status: string;
    started_at: string;
    completed_at: string;
    records_success: number;
  } | null;
  sync_available: boolean;
}
```

---

## 🔐 **6. RBAC (Role-Based Access Control)**

### **User Roles Enum:**
```typescript
enum UserRole {
  OWNER = "owner",
  ADMIN = "admin", 
  MEMBER = "member"
}
```

**Frontend Fix:**
```typescript
// ❌ WRONG - Type mismatch
if (userRole === UserRole.OWNER) { ... }

// ✅ CORRECT - Match backend string values
if (userRole === "owner") { ... }
```

---

## 📝 **7. Frontend TypeScript Fixes**

### **Fix useRBAC.ts:**
```typescript
// ❌ WRONG
const roleHierarchy = {
  [UserRole.OWNER]: 3,
  [UserRole.ADMIN]: 2, 
  [UserRole.MEMBER]: 1
};

// ✅ CORRECT
const roleHierarchy = {
  "owner": 3,
  "admin": 2,
  "member": 1
};
```

### **Fix useRoutiqData.ts:**
```typescript
// ❌ WRONG - Property names don't exist
const syncInProgress = data.sync_in_progress;
const lastSync = data.last_sync;
const apiConnected = data.clerk_api_connected;

// ✅ CORRECT - Use actual backend property names
const syncInProgress = data.sync_running;
const lastSync = data.last_sync_time;
const apiConnected = data.connected;
```

### **Fix API Method Names:**
```typescript
// ❌ WRONG - Method doesn't exist
await api.triggerClerkSync();
await api.getDatabaseSummary();

// ✅ CORRECT - Use actual backend endpoints
await api.post('/clerk-admin/sync');
await api.get('/clerk-admin/database-summary');
```

---

## 🚀 **8. Complete API Client Interface**

```typescript
interface RoutiqAPI {
  // Sync Management
  triggerSync(): Promise<SyncTriggerResponse>;
  getSchedulerStatus(orgId: string): Promise<SchedulerStatusResponse>;
  
  // Reengagement
  getRiskMetrics(orgId: string): Promise<RiskMetricsResponse>;
  
  // Patients
  getPatients(orgId: string, params?: PatientListParams): Promise<EnhancedPatientListResponse>;
  getEngagementStats(orgId: string): Promise<EngagementStatsResponse>;
  
  // Clerk Admin
  getClerkStatus(): Promise<ClerkSyncStatusResponse>;
  getDatabaseSummary(): Promise<DatabaseSummaryResponse>;
  
  // Sync Dashboard
  getSyncDashboard(orgId: string): Promise<SyncDashboardResponse>;
}
```

---

## ✅ **9. Immediate Action Items**

### **High Priority Fixes:**

1. **Update Property Names:**
   - `sync_in_progress` → `sync_running`
   - `last_sync` → `last_sync_time`
   - `clerk_api_connected` → `connected`

2. **Update Method Names:**
   - `triggerClerkSync()` → `triggerSync()`
   - Remove references to non-existent methods

3. **Update UserRole Usage:**
   - Use string literals instead of enum comparison
   - `UserRole.OWNER` → `"owner"`

4. **Add Missing Properties Handling:**
   - Handle missing `database_counts` gracefully
   - Use optional chaining for undefined properties

### **File-Specific Fixes:**

**useRBAC.ts:**
```typescript
// Line 105: Fix type comparison
- if (userRole === UserRole.OWNER) {
+ if (userRole === "owner") {

// Lines 108-109: Fix parameter types  
- hasPermission(userRole as UserRole, requiredRole)
+ hasPermission(userRole, requiredRole)
```

**useRoutiqData.ts:**
```typescript
// Line 39: Fix method name
- api.triggerClerkSync()
+ api.post('/clerk-admin/sync')

// Lines 56-58: Fix property names
- sync_in_progress: data.sync_in_progress,
- last_sync: data.last_sync,
- clerk_api_connected: data.clerk_api_connected,
+ sync_running: data.sync_running,
+ last_sync_time: data.last_sync_time,
+ connected: data.connected,

// Line 147: Fix method name
- api.getDatabaseSummary()
+ api.get('/clerk-admin/database-summary')
```

**organization-context.ts:**
```typescript
// Line 3: Create missing file or update import path
+ export interface OrganizationContext { ... }
```

---

## 📋 **10. Testing Checklist**

After making these fixes, verify:

- [ ] All TypeScript compilation errors resolved
- [ ] API calls use correct endpoint URLs
- [ ] Property names match backend responses exactly
- [ ] Method names exist in API client
- [ ] UserRole comparisons use string literals
- [ ] Optional chaining used for potentially missing properties

---

**🎯 This document is the authoritative source. Backend property names and method signatures are final.**

---

## 🔄 **BREAKING CHANGE: v1.4 Cleaner Business Logic**

**Updated:** December 2024  
**Database View:** `v1.4-cleaner-business-logic`

### **What Changed:**

**Old System (v1.3):**
- Single `risk_level`: "critical" | "high" | "medium" | "low" | "stale"
- Mixed engagement status with risk assessment
- Complex prioritization logic

**New System (v1.4):**
- **Two-dimensional classification:**
  - `engagement_status`: "active" | "dormant" | "stale" 
  - `risk_level`: "high" | "medium" | "low"
- **Cleaner business logic** aligned with staff workflow
- **Action priorities** based on engagement + risk combinations

### **Frontend Migration Required:**

1. **Update Response Interfaces:**
   ```typescript
   // ❌ OLD v1.3
   interface OldResponse {
     risk_level: "critical" | "high" | "medium" | "low" | "stale";
     summary: {
       risk_distribution: {
         critical: number;
         high: number;
         medium: number; 
         low: number;
         stale: number;
       };
     };
   }

   // ✅ NEW v1.4
   interface NewResponse {
     engagement_status: "active" | "dormant" | "stale";
     risk_level: "high" | "medium" | "low";
     summary: {
       engagement_distribution: {
         active: number;
         dormant: number;
         stale: number;
       };
       risk_distribution: {
         high: number;
         medium: number;
         low: number;
       };
       action_priorities: {
         urgent: number;
         important: number;
         monitor: number;
         maintain: number;
       };
     };
   }
   ```

2. **Update Risk Level Filtering:**
   ```typescript
   // ❌ OLD - Risk levels included engagement
   const criticalPatients = patients.filter(p => p.risk_level === 'critical');
   
   // ✅ NEW - Separate dimensions
   const dormantHighRisk = patients.filter(p => 
     p.engagement_status === 'dormant' && p.risk_level === 'high'
   );
   const urgentPatients = patients.filter(p => p.action_priority === 1);
   ```

3. **Update Dashboard Components:**
   ```typescript
   // ✅ NEW dashboard structure
   <EngagementStatusChart data={summary.engagement_distribution} />
   <RiskLevelChart data={summary.risk_distribution} />
   <ActionPriorityChart data={summary.action_priorities} />
   ```

--- 