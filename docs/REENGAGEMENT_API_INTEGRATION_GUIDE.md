# 🎯 Reengagement API Integration Guide
## For Frontend Development Team

**API Status:** ✅ **READY FOR INTEGRATION**  
**Backend Views:** ✅ **DEPLOYED**  
**Authentication:** ✅ **Required (Clerk JWT)**

---

## 🎯 Overview

The reengagement API provides access to the `patient_reengagement_master` view, which includes:
- **Treatment Notes** - Patient treatment history and notes
- **Engagement Status** - Active, Dormant, or Stale classification
- **Risk Levels** - High, Medium, Low risk assessment
- **Action Priorities** - 1-4 priority scoring for staff workflow
- **Financial Metrics** - Lifetime value calculations
- **Attendance Analysis** - 90-day appointment compliance metrics

---

## 📋 **Overview**

The new Reengagement API transforms generic patient stats into **actionable, risk-based metrics** for patient retention and recovery. All endpoints use optimized PostgreSQL views for fast performance.

### **Key Benefits:**
- **Risk-based prioritization** instead of generic counts
- **Actionable recommendations** for each patient
- **Performance tracking** for outreach efforts
- **Real-time risk alerts** for critical patients

---

## 🔌 **Base Configuration**

### **API Base URL**
```
Production: https://routiq-backend-prod.up.railway.app
Development: http://localhost:8000
```

### **Authentication**
All endpoints require Clerk JWT token:
```javascript
const headers = {
  'Authorization': `Bearer ${clerkToken}`,
  'Content-Type': 'application/json'
}
```

---

## 🚨 **Priority 1: Risk Dashboard**

### **GET `/api/v1/reengagement/{org_id}/risk-metrics`**

**Purpose:** Get risk summary and alert counts for dashboard cards

#### **Example Request:**
```javascript
const response = await fetch(
  `${API_BASE}/api/v1/reengagement/${orgId}/risk-metrics`,
  { headers }
);
const data = await response.json();
```

#### **Response Structure:**
```json
{
  "organization_id": "org_2abc123",
  "risk_summary": {
    "critical": 12,    // 🔴 45+ days no contact
    "high": 8,         // 🟠 30-44 days no contact  
    "medium": 15,      // 🟡 14-29 days no contact
    "low": 23,         // 🟢 7-13 days no contact
    "engaged": 45      // ✅ Recent contact
  },
  "alerts": {
    "missed_appointments_14d": 7,
    "failed_communications": 3,
    "no_future_appointments": 18
  },
  "immediate_actions_required": 15,
  "last_updated": "2025-06-30T08:00:00Z"
}
```

#### **Frontend Implementation:**
```jsx
// Replace generic "36 active patients" with:
<div className="dashboard-cards">
  <AlertCard 
    title="Critical Risk" 
    count={data.risk_summary.critical}
    color="red"
    action="immediate_contact_required"
  />
  <AlertCard 
    title="High Risk" 
    count={data.risk_summary.high}
    color="orange"
    action="contact_within_24h"
  />
  <AlertCard 
    title="Immediate Actions" 
    count={data.immediate_actions_required}
    color="red"
    priority="urgent"
  />
</div>
```

---

## 📊 **Priority 2: Performance Tracking**

### **GET `/api/v1/reengagement/{org_id}/performance`**

**Purpose:** Track reengagement campaign effectiveness

#### **Query Parameters:**
- `timeframe`: `last_7_days` | `last_30_days` | `last_90_days`

#### **Example Request:**
```javascript
const response = await fetch(
  `${API_BASE}/api/v1/reengagement/${orgId}/performance?timeframe=last_30_days`,
  { headers }
);
```

#### **Response Structure:**
```json
{
  "timeframe": "last_30_days",
  "reengagement_metrics": {
    "outreach_attempts": 145,
    "successful_contacts": 89,
    "contact_success_rate": 61.4,
    "appointments_scheduled": 67,
    "conversion_rate": 75.3,
    "avg_days_to_reengage": 8.5
  },
  "communication_channels": {
    "sms": {
      "sent": 95,
      "delivered": 87,
      "responded": 52,
      "response_rate": 59.8
    },
    "email": {
      "sent": 78,
      "opened": 45,
      "responded": 23,
      "response_rate": 51.1
    },
    "phone": {
      "attempted": 34,
      "connected": 28,
      "appointment_booked": 21,
      "conversion_rate": 75.0
    }
  },
  "benchmark_comparison": {
    "industry_avg_contact_rate": 55.0,
    "industry_avg_conversion": 68.0,
    "our_performance": "above_average"
  }
}
```

#### **Frontend Implementation:**
```jsx
// Performance dashboard component
<PerformanceDashboard>
  <MetricCard 
    title="Contact Success Rate"
    value={`${data.reengagement_metrics.contact_success_rate}%`}
    benchmark={55.0}
    status={data.benchmark_comparison.our_performance}
  />
  
  <ChannelBreakdown>
    {Object.entries(data.communication_channels).map(([channel, stats]) => (
      <ChannelCard 
        key={channel}
        name={channel}
        responseRate={stats.response_rate}
        totalSent={stats.sent}
      />
    ))}
  </ChannelBreakdown>
</PerformanceDashboard>
```

---

## 📋 **Priority 3: Prioritized Patient List**

### **GET `/api/v1/reengagement/{org_id}/patients/prioritized`**

**Purpose:** Get actionable patient list with risk scores and recommendations

#### **Query Parameters:**
- `risk_level`: `critical` | `high` | `medium` | `low` | `engaged` | `all`
- `limit`: Number of patients (max 200, default 50)

#### **Example Request:**
```javascript
// Get critical risk patients only
const response = await fetch(
  `${API_BASE}/api/v1/reengagement/${orgId}/patients/prioritized?risk_level=critical&limit=20`,
  { headers }
);
```

#### **Response Structure:**
```json
{
  "patients": [
    {
      "id": "patient_123",
      "name": "John Smith",
      "phone": "+1234567890",
      "email": "john.smith@email.com",
      "risk_level": "critical",
      "risk_score": 85,
      "days_since_last_contact": 47,
      "last_appointment_date": "2025-05-14T00:00:00Z",
      "next_scheduled_appointment": null,
      "recommended_action": "DORMANT: Re-engagement campaign needed",
      "action_priority": 1,
      "previous_response_rate": 78.5,
      "total_lifetime_appointments": 12,
      "missed_appointments_last_90d": 2
    }
  ],
  "summary": {
    "total_returned": 20,
    "filters_applied": {
      "risk_level": "critical",
      "limit": 20
    }
  },
  "timestamp": "2025-06-30T12:00:00Z"
}
```

#### **Frontend Implementation:**
```jsx
// Prioritized patient list component
<PrioritizedPatientList>
  {data.patients.map(patient => (
    <PatientCard 
      key={patient.id}
      patient={patient}
      riskLevel={patient.risk_level}
      actionRequired={patient.recommended_action}
      priority={patient.action_priority}
      onContactClick={() => handleContact(patient)}
    />
  ))}
</PrioritizedPatientList>

// Risk-based styling
const getRiskColor = (level) => {
  switch(level) {
    case 'critical': return '#DC2626'; // Red
    case 'high': return '#EA580C';     // Orange  
    case 'medium': return '#CA8A04';   // Yellow
    case 'low': return '#16A34A';      // Green
    case 'engaged': return '#059669';  // Emerald
    default: return '#6B7280';         // Gray
  }
};
```

---

## 📈 **Priority 4: Trends & Analytics**

### **GET `/api/v1/reengagement/{org_id}/trends`**

**Purpose:** Show reengagement trends over time

#### **Query Parameters:**
- `period`: `7d` | `30d` | `90d` | `6m` | `1y`
- `metrics`: `risk_levels` | `success_rates` | `channel_performance`

#### **Example Request:**
```javascript
const response = await fetch(
  `${API_BASE}/api/v1/reengagement/${orgId}/trends?period=30d&metrics=risk_levels`,
  { headers }
);
```

#### **Response Structure:**
```json
{
  "period": "30d",
  "daily_trends": [
    {
      "date": "2025-06-01",
      "new_at_risk": 3,
      "reengaged_successfully": 7,
      "outreach_attempts": 15,
      "appointments_scheduled": 5
    }
  ],
  "channel_performance_trends": {
    "sms": {"success_rate_trend": "improving", "change_pct": 12.3},
    "email": {"success_rate_trend": "stable", "change_pct": -2.1},
    "phone": {"success_rate_trend": "improving", "change_pct": 5.4}
  },
  "risk_distribution_changes": {
    "critical_trend": "decreasing",
    "high_trend": "stable",
    "overall_improvement": true
  },
  "current_risk_distribution": {
    "critical": 12,
    "high": 8,
    "medium": 15,
    "low": 23,
    "engaged": 45
  }
}
```

---

## 📝 **Logging Outreach Attempts**

### **POST `/api/v1/reengagement/{org_id}/log-outreach`**

**Purpose:** Track outreach attempts for performance metrics

#### **Request Body:**
```json
{
  "patient_id": "patient_123",
  "method": "sms",
  "outcome": "success",
  "notes": "Patient responded positively, appointment booked"
}
```

#### **Method Options:**
- `sms` | `email` | `phone`

#### **Outcome Options:**
- `success` | `no_response` | `failed`

#### **Example Implementation:**
```javascript
const logOutreach = async (patientId, method, outcome, notes = '') => {
  const response = await fetch(
    `${API_BASE}/api/v1/reengagement/${orgId}/log-outreach`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        patient_id: patientId,
        method,
        outcome,
        notes
      })
    }
  );
  
  return response.json();
};

// Usage in contact buttons
<button onClick={() => {
  // Show SMS interface
  // After sending, log the attempt:
  logOutreach(patient.id, 'sms', 'success', 'Appointment reminder sent');
}}>
  Send SMS
</button>
```

---

## 🎯 **Complete Dashboard Integration**

### **GET `/api/v1/reengagement/{org_id}/dashboard`**

**Purpose:** Single endpoint for comprehensive dashboard data

#### **Response Structure:**
```json
{
  "organization_id": "org_2abc123",
  "summary": {
    "total_patients": 103,
    "risk_breakdown": {
      "critical": {"count": 12, "avg_score": 83.5},
      "high": {"count": 8, "avg_score": 72.1},
      "medium": {"count": 15, "avg_score": 58.3},
      "low": {"count": 23, "avg_score": 42.7},
      "engaged": {"count": 45, "avg_score": 15.2}
    },
    "immediate_actions_needed": 15
  },
  "top_priority_patients": [
    {
      "id": "patient_456",
      "name": "Jane Doe",
      "risk_level": "critical",
      "risk_score": 89,
      "action": "DORMANT: Re-engagement campaign needed",
      "days_since_contact": 52
    }
  ],
  "last_updated": "2025-06-30T12:00:00Z"
}
```

---

## 🔧 **Implementation Strategy**

### **Phase 1: Replace Generic Stats (Week 1)**
1. Replace "36 active patients" with risk-based cards
2. Add "Critical Risk: 12 patients" alert
3. Show "Immediate Actions: 15" urgent counter

### **Phase 2: Add Patient Prioritization (Week 1)**  
1. Replace patient list with prioritized risk list
2. Add risk-level color coding
3. Show action recommendations per patient

### **Phase 3: Add Performance Tracking (Week 2)**
1. Add performance metrics dashboard
2. Implement outreach logging buttons
3. Show success rate vs industry benchmarks

### **Phase 4: Add Trends (Week 2)**
1. Add trend charts for risk levels
2. Show channel performance over time
3. Track improvement metrics

---

## 🚀 **Error Handling**

```javascript
try {
  const response = await fetch(endpoint, { headers });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  const data = await response.json();
  return data;
  
} catch (error) {
  console.error('Reengagement API Error:', error);
  
  // Fallback to show error state
  return {
    error: true,
    message: 'Unable to load reengagement data',
    fallback_data: {
      risk_summary: { critical: 0, high: 0, medium: 0, low: 0, engaged: 0 }
    }
  };
}
```

---

## 📊 **Expected Data Flow**

### **Current State:**
```
"36 active patients" → Meaningless for staff
"100% activity rate" → False metric
```

### **New State:**
```
"Critical Risk: 12 patients" → Immediate action needed
"Contact Success: 61.4%" → Above 55% industry average  
"Top Priority: Jane Doe - 52 days no contact" → Specific action
```

---

## 🔮 **Future Enhancements**

Once basic integration is complete, these features can be added:

1. **Real-time Alerts** - WebSocket notifications for new critical patients
2. **Campaign Management** - Bulk outreach with templates
3. **Predictive Modeling** - ML-based risk scoring improvements
4. **Advanced Analytics** - Cohort analysis and patient journey tracking

---

## 📞 **Support & Questions**

The reengagement API is built on robust PostgreSQL views and should provide consistent, fast performance. All endpoints include proper error handling and follow the existing authentication patterns.

**Backend Views Used:**
- `patient_reengagement_master_view` - Risk scoring and patient prioritization
- `reengagement_performance_view` - Performance metrics aggregation  
- `outreach_log` table - Communication tracking

**Performance:** Sub-100ms response times expected for all endpoints due to optimized views and proper indexing. 