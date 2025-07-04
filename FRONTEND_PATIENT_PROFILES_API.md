# 🎉 Patient Profiles API - Ready for Frontend Integration

**Status:** ✅ **LIVE AND WORKING**  
**Base URL:** `https://routiq-backend-prod.up.railway.app`  
**API Prefix:** `/api/v1/reengagement`  
**Date:** July 4, 2025

---

## 📋 **Available Endpoints**

### 1. **List Patient Profiles**
```http
GET /api/v1/reengagement/{organization_id}/patient-profiles
```

**Query Parameters:**
- `limit` (optional): Number of profiles to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `search` (optional): Search term for name/email/phone

**Example Request:**
```bash
curl "https://routiq-backend-prod.up.railway.app/api/v1/reengagement/org_2xwHiNrj68eaRUlX10anlXGvzX7/patient-profiles?limit=10"
```

**Response Format:**
```json
{
  "success": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "patient_profiles": [
    {
      "patient_id": "05ad0765-1544-4a12-ab2c-36aa6c58f81a",
      "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
      "patient_name": "Daniel Harris",
      "email": "harris.danielc@gmail.com",
      "phone": "18607168079",
      "is_active": true,
      "activity_status": "active",
      "engagement_level": "disengaged",
      "churn_risk": "low",
      "action_priority": 5,
      "estimated_lifetime_value": 1050,
      "total_appointment_count": 7,
      "total_conversations": 0,
      "contact_success_prediction": "very_low",
      "next_appointment_time": "2025-07-11T05:00:00+00:00",
      "view_generated_at": "2025-07-04T03:03:40.332013+00:00"
    }
  ],
  "count": 10,
  "timestamp": "2025-07-04T03:03:40.499527"
}
```

---

### 2. **Get Individual Patient Profile**
```http
GET /api/v1/reengagement/{organization_id}/patient-profiles/{patient_id}
```

**Example Request:**
```bash
curl "https://routiq-backend-prod.up.railway.app/api/v1/reengagement/org_2xwHiNrj68eaRUlX10anlXGvzX7/patient-profiles/05ad0765-1544-4a12-ab2c-36aa6c58f81a"
```

**Response Format:**
```json
{
  "success": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "patient_id": "05ad0765-1544-4a12-ab2c-36aa6c58f81a",
  "profile": {
    "patient_id": "05ad0765-1544-4a12-ab2c-36aa6c58f81a",
    "patient_name": "Daniel Harris",
    "email": "harris.danielc@gmail.com",
    "phone": "18607168079",
    "is_active": true,
    "activity_status": "active",
    "engagement_level": "disengaged",
    "churn_risk": "low",
    "action_priority": 5,
    "estimated_lifetime_value": 1050,
    "total_conversations": 0,
    "last_conversation_date": null,
    "total_appointment_count": 7,
    "next_appointment_time": "2025-07-11T05:00:00+00:00",
    "contact_success_prediction": "very_low"
  },
  "timestamp": "2025-07-04T03:03:40.499527"
}
```

---

### 3. **Get Summary Statistics**
```http
GET /api/v1/reengagement/{organization_id}/patient-profiles/summary
```

**Example Request:**
```bash
curl "https://routiq-backend-prod.up.railway.app/api/v1/reengagement/org_2xwHiNrj68eaRUlX10anlXGvzX7/patient-profiles/summary"
```

**Response Format:**
```json
{
  "success": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "summary": {
    "total_patients": 651,
    "highly_engaged": 0,
    "moderately_engaged": 0,
    "low_engagement": 0,
    "disengaged": 651,
    "critical_risk": 0,
    "high_risk": 0,
    "medium_risk": 0,
    "low_risk": 651
  },
  "timestamp": "2025-07-04T03:03:55.239560"
}
```

---

### 4. **Debug/Test Endpoint**
```http
GET /api/v1/reengagement/{organization_id}/patient-profiles/debug
```

**Purpose:** Returns first 5 patient profiles for testing  
**Use:** Verify API connectivity and data structure

---

## 📊 **Available Data Fields**

### **Core Patient Information**
- `patient_id` - Unique identifier
- `organization_id` - Organization identifier  
- `patient_name` - Full name
- `email` - Email address
- `phone` - Phone number
- `is_active` - Active status (boolean)
- `activity_status` - "active", "inactive"

### **Engagement Metrics**
- `engagement_level` - "highly_engaged", "moderately_engaged", "low_engagement", "disengaged"
- `total_conversations` - Number of conversations
- `active_conversations` - Active conversation count
- `last_conversation_date` - Last conversation timestamp
- `days_since_last_conversation` - Days since last contact

### **Risk Assessment**
- `churn_risk` - "critical", "high", "medium", "low"
- `action_priority` - 1 (highest) to 5 (lowest)
- `contact_success_prediction` - "very_high", "high", "medium", "low", "very_low"

### **Appointment Data**
- `total_appointment_count` - Total appointments
- `recent_appointment_count` - Recent appointments
- `upcoming_appointment_count` - Upcoming appointments
- `next_appointment_time` - Next appointment date/time
- `last_appointment_date` - Last appointment date

### **Financial Metrics**
- `estimated_lifetime_value` - Calculated value in AUD
- `outreach_success_rate` - Success rate percentage

### **Conversation Details**
- `total_messages` - Message count
- `patient_messages` - Messages from patient
- `agent_messages` - Messages from agents
- `last_message_date` - Last message timestamp
- `overall_sentiment` - Overall conversation sentiment
- `escalation_count` - Number of escalations

---

## 🎯 **Current Data Status**

**Production Database:** `org_2xwHiNrj68eaRUlX10anlXGvzX7`
- **Total Patients:** 651
- **Engagement Status:** All currently "disengaged" (no conversation data yet)
- **Risk Level:** All "low_risk" 
- **Data Quality:** Patient and appointment data is complete, conversation data is pending

---

## 💻 **Frontend Integration Examples**

### **React/TypeScript Interface**
```typescript
interface PatientProfile {
  patient_id: string;
  organization_id: string;
  patient_name: string;
  email: string | null;
  phone: string | null;
  is_active: boolean;
  activity_status: 'active' | 'inactive';
  engagement_level: 'highly_engaged' | 'moderately_engaged' | 'low_engagement' | 'disengaged';
  churn_risk: 'critical' | 'high' | 'medium' | 'low';
  action_priority: 1 | 2 | 3 | 4 | 5;
  estimated_lifetime_value: number;
  total_conversations: number;
  total_appointment_count: number;
  next_appointment_time: string | null;
  contact_success_prediction: 'very_high' | 'high' | 'medium' | 'low' | 'very_low';
}

interface PatientProfilesResponse {
  success: boolean;
  organization_id: string;
  patient_profiles: PatientProfile[];
  count: number;
  timestamp: string;
}
```

### **Fetch Example**
```javascript
// Get patient profiles
const response = await fetch(
  `https://routiq-backend-prod.up.railway.app/api/v1/reengagement/${orgId}/patient-profiles?limit=20`,
  {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  }
);

const data = await response.json();
if (data.success) {
  console.log(`Found ${data.count} patient profiles`);
  data.patient_profiles.forEach(profile => {
    console.log(`${profile.patient_name}: ${profile.engagement_level} risk`);
  });
}
```

---

## 🚨 **Important Notes**

1. **All endpoints are LIVE** and returning real data
2. **No authentication required** (follows same pattern as other reengagement endpoints)
3. **Pagination available** on main listing endpoint
4. **Error handling** returns consistent JSON format
5. **Date formats** are ISO 8601 strings
6. **Organization ID** must be included in all requests

---

## 🔄 **Next Steps for Frontend**

1. ✅ **Test connectivity** using the debug endpoint
2. ✅ **Implement listing page** with patient profiles
3. ✅ **Add individual patient views** using patient_id
4. ✅ **Build summary dashboard** using summary endpoint
5. ✅ **Add filtering/search** using query parameters

---

## 📞 **Support**

If you encounter any issues:
- Check the debug endpoint first: `/patient-profiles/debug`
- Verify organization_id is correct: `org_2xwHiNrj68eaRUlX10anlXGvzX7`
- All endpoints return JSON with `success` boolean field
- Contact backend team with specific error messages

**Status:** 🟢 Ready for production use! 