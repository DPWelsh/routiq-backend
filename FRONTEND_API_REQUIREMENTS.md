# Frontend API Requirements for Backend Team

## 🎯 **Overview**

The Routiq frontend requires specific API endpoints to support the unified data flow architecture. All endpoints should follow REST conventions and include proper authentication via Clerk JWT tokens.

**Base URL:** `https://routiq-backend-prod.up.railway.app`

## 🔐 **Authentication**

All requests will include:
- **Authorization Header**: `Bearer <clerk_jwt_token>`
- **Organization Header**: `x-organization-id: <organization_id>`

## 📊 **Required API Endpoints**

### 1. **Dashboard Data Endpoint**

**Purpose**: Unified dashboard data with patient metrics and sync activity

```
GET /api/v1/dashboard/{organizationId}
```

**Request Headers:**
```
Authorization: Bearer <clerk_jwt_token>
x-organization-id: <organization_id>
Content-Type: application/json
```

**Response Structure:**
```typescript
{
  "success": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "summary": {
    "total_patients": 650,
    "active_patients": 37,
    "patients_with_upcoming": 23,
    "patients_with_recent": 32,
    "total_upcoming_appointments": 44,
    "total_recent_appointments": 67,
    "total_all_appointments": 292,
    "avg_upcoming_per_patient": 1.91,
    "avg_recent_per_patient": 2.09,
    "avg_total_per_patient": 4.57,
    "last_sync_time": "2024-12-27T11:32:22.000Z",
    "synced_patients": 650,
    "sync_percentage": 100,
    "integration_status": "Connected",
    "activity_status": "Active",
    "engagement_rate": 8.5,
    "generated_at": "2024-12-27T11:38:15.123Z"
  },
  "recent_activity": [
    {
      "id": "sync_123",
      "source_system": "cliniko",
      "operation_type": "full_patients",
      "status": "completed", // "running", "failed", "completed"
      "records_processed": 650,
      "records_success": 650,
      "records_failed": 0,
      "started_at": "2024-12-27T11:30:00.000Z",
      "completed_at": "2024-12-27T11:32:22.000Z",
      "activity_type": "sync",
      "description": "Comprehensive sync: 650 patients + appointments",
      "minutes_ago": 6
    }
  ]
}
```

**Frontend Usage:**
- Main dashboard display
- Real-time sync monitoring
- Patient statistics cards
- Activity timeline

---

### 2. **Patients Data Endpoint**

**Purpose**: Patient list with appointment details for patient management

```
GET /api/v1/patients/{organizationId}
```

**Optional Query Parameters:**
- `?page=1&limit=100` (pagination)
- `?search=john` (name/phone/email search)
- `?active_only=true` (filter active patients)

**Response Structure:**
```typescript
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "patients": [
    {
      "id": "pat_123",
      "name": "John Smith",
      "phone": "+1234567890",
      "email": "john@example.com",
      "is_active": true,
      "recent_appointment_count": 3,
      "upcoming_appointment_count": 2,
      "next_appointment_time": "2024-12-28T10:00:00.000Z",
      "next_appointment_type": "Follow-up"
    }
  ],
  "total_count": 650,
  "page": 1,
  "limit": 100,
  "total_pages": 7
}
```

**Frontend Usage:**
- Patient list page
- Search and filtering
- Engagement level calculations
- Navigation to conversations

---

### 3. **Sync Trigger Endpoint**

**Purpose**: Trigger data synchronization from external systems

```
POST /api/v1/cliniko/sync/{organizationId}
```

**Request Body (Optional):**
```typescript
{
  "sync_type": "comprehensive", // "basic", "patients-only"
  "force_refresh": false
}
```

**Response Structure:**
```typescript
{
  "success": true,
  "sync_id": "sync_456",
  "message": "Sync initiated successfully",
  "estimated_duration": "2-3 minutes"
}
```

**Frontend Usage:**
- Manual sync triggers
- Dashboard refresh buttons
- Sync progress monitoring

---

### 4. **Upcoming Appointments Endpoint** *(New Requirement)*

**Purpose**: Detailed upcoming appointments for dashboard widgets

```
GET /api/v1/appointments/upcoming/{organizationId}
```

**Optional Query Parameters:**
- `?days_ahead=7` (default: 7 days)
- `?limit=10` (default: 20)

**Response Structure:**
```typescript
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "appointments": [
    {
      "id": "apt_789",
      "patient_id": "pat_123",
      "patient_name": "John Smith",
      "patient_phone": "+1234567890",
      "appointment_time": "2024-12-28T10:00:00.000Z",
      "appointment_type": "Follow-up",
      "practitioner": "Dr. Sarah Johnson",
      "status": "confirmed", // "pending", "confirmed", "cancelled"
      "duration_minutes": 30,
      "notes": "Regular check-up"
    }
  ],
  "total_count": 44,
  "date_range": {
    "start": "2024-12-27T00:00:00.000Z",
    "end": "2024-01-03T23:59:59.000Z"
  }
}
```

**Frontend Usage:**
- Dashboard upcoming appointments widget
- Patient engagement tracking
- Quick appointment overview

---

### 5. **Conversation History Endpoint** *(New Requirement)*

**Purpose**: Chat/call history for specific patients

```
GET /api/v1/conversations/{organizationId}/patient/{patientId}
```

**Alternative by Phone:**
```
GET /api/v1/conversations/{organizationId}/phone/{phoneNumber}
```

**Response Structure:**
```typescript
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "patient": {
    "id": "pat_123",
    "name": "John Smith",
    "phone": "+1234567890"
  },
  "conversations": [
    {
      "id": "conv_456",
      "channel": "phone", // "chat", "email", "sms"
      "direction": "inbound", // "outbound"
      "started_at": "2024-12-27T14:30:00.000Z",
      "ended_at": "2024-12-27T14:35:00.000Z",
      "duration_seconds": 300,
      "status": "completed",
      "summary": "Patient called to reschedule appointment",
      "sentiment_score": 0.8, // 0-1 scale
      "messages": [
        {
          "id": "msg_789",
          "timestamp": "2024-12-27T14:30:15.000Z",
          "sender": "patient", // "agent", "system"
          "content": "Hi, I need to reschedule my appointment",
          "message_type": "text"
        }
      ]
    }
  ],
  "total_count": 12
}
```

**Frontend Usage:**
- Conversation detail pages
- Patient communication history
- Sentiment analysis display

---

## 🚦 **Error Handling**

All endpoints should return consistent error responses:

**4xx Client Errors:**
```typescript
{
  "success": false,
  "error": "Invalid organization ID",
  "error_code": "INVALID_ORG_ID",
  "status": 400
}
```

**5xx Server Errors:**
```typescript
{
  "success": false,
  "error": "Database connection failed",
  "error_code": "DATABASE_ERROR", 
  "status": 500,
  "retry_after": 30 // seconds
}
```

**Rate Limiting (429):**
```typescript
{
  "success": false,
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMITED",
  "status": 429,
  "retry_after": 60,
  "limit": 100,
  "remaining": 0
}
```

---

## 🔄 **Real-time Updates**

### Sync Status Monitoring

The frontend polls the dashboard endpoint every:
- **5 seconds** during active syncs
- **30 seconds** during normal operation

**Active Sync Detection:**
Frontend detects active syncs by checking `recent_activity` array for items with `status: "running"`

### Expected Sync Statuses:
- `"running"` - Sync in progress
- `"completed"` - Sync finished successfully  
- `"failed"` - Sync encountered errors
- `"cancelled"` - Sync was cancelled

---

## 🏥 **Organization Context**

### Multi-tenancy Requirements:
1. All data must be isolated by `organization_id`
2. Users can switch between organizations seamlessly
3. JWT tokens contain organization membership info
4. API responses must include `organization_id` for verification

### Test Organizations:
- **Surf Rehab**: `org_2xwHiNrj68eaRUlX10anlXGvzX7`
- **Daniel Personal**: `org_2xwHiNrj68eaRUlX10anlXGvzX8`

---

## 🚀 **Performance Requirements**

### Response Times:
- **Dashboard endpoint**: < 2 seconds
- **Patients endpoint**: < 3 seconds  
- **Sync trigger**: < 1 second (async operation)
- **Conversations**: < 2 seconds

### Caching:
- Frontend caches responses for 10-30 seconds
- Include `Cache-Control` headers where appropriate
- Support ETags for conditional requests

### Pagination:
- Default page size: 50 items
- Maximum page size: 200 items
- Include pagination metadata in responses

---

## 🧪 **Testing Endpoints**

### Health Check:
```
GET /api/v1/health
Response: { "status": "healthy", "timestamp": "2024-12-27T11:38:15.123Z" }
```

### Organization Validation:
```
GET /api/v1/organizations/{organizationId}/validate
Response: { "valid": true, "organization_name": "Surf Rehab" }
```

---

## 🔧 **Implementation Priority**

1. **HIGH PRIORITY**: Dashboard endpoint (required for main dashboard)
2. **HIGH PRIORITY**: Patients endpoint (required for patient management)
3. **MEDIUM PRIORITY**: Sync trigger endpoint (manual refresh functionality)
4. **MEDIUM PRIORITY**: Upcoming appointments endpoint (dashboard widget)
5. **LOW PRIORITY**: Conversation history endpoint (detailed views)

---

## 📋 **Development Notes**

### Authentication Integration:
- Frontend automatically includes Clerk JWT tokens
- Tokens are refreshed automatically by Clerk
- No manual token management required

### Error Recovery:
- Frontend implements automatic retry with exponential backoff
- Users can manually retry failed requests
- Network errors are handled gracefully

### Organization Switching:
- Frontend clears cache when switching organizations
- New requests automatically include new organization headers
- No additional backend work required for org switching

---

## ✅ **Current Status**

**Already Working:**
- ✅ Basic sync trigger (`POST /api/v1/cliniko/sync/{organizationId}`)
- ✅ Health check endpoint
- ✅ Authentication via Clerk JWT

**Needs Implementation:**
- ❌ Unified dashboard endpoint
- ❌ Enhanced patients endpoint  
- ❌ Upcoming appointments endpoint
- ❌ Conversation history endpoint

---

This documentation provides everything your backend team needs to implement the required endpoints for full frontend functionality. The frontend is already configured to use these endpoints once they're available. 