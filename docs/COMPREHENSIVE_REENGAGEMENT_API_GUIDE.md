# Comprehensive Patient Reengagement API Guide

This guide covers the complete patient reengagement API endpoints that expose rich patient data including **treatment notes**, risk analysis, and engagement metrics.

## 🎯 Overview

The reengagement API provides access to the `patient_reengagement_master` view, which includes:
- **Treatment Notes** - Patient treatment history and notes
- **Engagement Status** - Active, Dormant, or Stale classification  
- **Risk Levels** - High, Medium, Low risk assessment
- **Action Priorities** - 1-4 priority scoring for staff workflow
- **Financial Metrics** - Lifetime value calculations ($140 AUD per appointment)
- **Attendance Analysis** - 90-day appointment compliance metrics

---

## 📊 Core API Endpoints

### 1. Risk Metrics Dashboard
```http
GET /api/v1/reengagement/{organization_id}/risk-metrics
```

**Purpose:** Complete patient reengagement data with risk analysis

**Response Structure:**
```json
{
  "organization_id": "org_123",
  "summary": {
    "total_patients": 156,
    "risk_distribution": {
      "high": 23,
      "medium": 45, 
      "low": 88
    },
    "engagement_distribution": {
      "active": 98,
      "dormant": 45,
      "stale": 13
    },
    "action_priorities": {
      "urgent": 15,    // Priority 1: Dormant + High Risk
      "important": 32, // Priority 2: Active + High Risk, Dormant + Medium
      "medium": 67,    // Priority 3: Other Medium Risk
      "low": 42        // Priority 4: Low Risk, Stale
    }
  },
  "patients": [
    {
      "patient_id": "uuid-here",
      "patient_name": "John Smith",
      "email": "john@example.com",
      "phone": "+61412345678",
      "is_active": true,
      "engagement_status": "dormant",
      "risk_level": "high",
      "risk_score": 75,
      "days_since_last_contact": 45.2,
      "days_to_next_appointment": null,
      "treatment_notes": "Lower back pain management. Last session showed improvement in mobility. Continue with strengthening exercises.",
      "lifetime_value_aud": 2100,
      "action_priority": 1,
      "recommended_action": "URGENT: Call immediately - high-risk dormant patient",
      "contact_success_prediction": "medium",
      "attendance_rate_percent": 78.5,
      "missed_appointments_90d": 2,
      "calculated_at": "2025-01-01T12:00:00.000Z",
      "view_version": "v1.4.2-added-lifetime-value"
    }
  ]
}
```

### 2. Prioritized Patient List
```http
GET /api/v1/reengagement/{organization_id}/prioritized
```

**Purpose:** Filtered and prioritized patient list for targeted reengagement

**Query Parameters:**
| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| `risk_level` | string | `high`, `medium`, `low` | Filter by risk level |
| `engagement_status` | string | `active`, `dormant`, `stale` | Filter by engagement |
| `action_priority` | integer | `1`, `2`, `3`, `4` | Filter by action priority |
| `limit` | integer | 1-200 | Number of results (default: 50) |
| `include_treatment_notes` | boolean | `true`, `false` | Include notes (default: true) |

**Example Requests:**
```http
# High-risk patients only
GET /api/v1/reengagement/org_123/prioritized?risk_level=high&limit=25

# Urgent priority patients with notes
GET /api/v1/reengagement/org_123/prioritized?action_priority=1&include_treatment_notes=true

# Dormant patients for reengagement campaign
GET /api/v1/reengagement/org_123/prioritized?engagement_status=dormant&limit=100
```

### 3. Dashboard Summary
```http
GET /api/v1/reengagement/{organization_id}/dashboard-summary
```

**Purpose:** Executive summary metrics for dashboard widgets

**Response:**
```json
{
  "organization_id": "org_123",
  "summary_metrics": {
    "total_patients": 156,
    "engagement_breakdown": {
      "active": 98,
      "dormant": 45,
      "stale": 13
    },
    "financial_metrics": {
      "total_lifetime_value_aud": 328400.0,
      "avg_lifetime_value_aud": 2105.13
    },
    "engagement_metrics": {
      "avg_days_since_contact": 28.7,
      "avg_attendance_rate_percent": 76.8
    }
  },
  "priority_patients": [
    {
      "patient_id": "uuid",
      "patient_name": "Emergency Contact Patient",
      "engagement_status": "dormant",
      "risk_level": "high",
      "action_priority": 1,
      "recommended_action": "URGENT: Call immediately - high-risk dormant patient",
      "days_since_last_contact": 72.3,
      "lifetime_value_aud": 4200
    }
  ]
}
```

### 4. Individual Patient Details
```http
GET /api/v1/reengagement/{organization_id}/patient/{patient_id}/details
```

**Purpose:** Comprehensive patient profile for detailed reengagement planning

**Response includes:**
- Complete engagement analysis
- Treatment notes and history
- Appointment compliance metrics
- Financial value assessment
- Recommended actions

---

## 🚀 Frontend Integration Examples

### React Dashboard Component
```tsx
import React, { useState, useEffect } from 'react';

const ReengagementDashboard = ({ organizationId }) => {
  const [urgentPatients, setUrgentPatients] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    loadUrgentPatients();
    loadSummary();
  }, [organizationId]);

  const loadUrgentPatients = async () => {
    const response = await fetch(
      `/api/v1/reengagement/${organizationId}/prioritized?action_priority=1&limit=10`,
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    const data = await response.json();
    setUrgentPatients(data.patients);
  };

  const loadSummary = async () => {
    const response = await fetch(
      `/api/v1/reengagement/${organizationId}/dashboard-summary`,
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    const data = await response.json();
    setSummary(data.summary_metrics);
  };

  return (
    <div className="reengagement-dashboard">
      <div className="metrics-row">
        <div className="metric-card urgent">
          <h3>Urgent Action Required</h3>
          <div className="metric-value">{summary?.action_priorities?.urgent}</div>
        </div>
        <div className="metric-card financial">
          <h3>Total Lifetime Value</h3>
          <div className="metric-value">
            ${summary?.financial_metrics?.total_lifetime_value_aud?.toLocaleString()}
          </div>
        </div>
      </div>

      <div className="urgent-patients">
        <h3>Immediate Action Required</h3>
        {urgentPatients.map(patient => (
          <PatientCard key={patient.patient_id} patient={patient} />
        ))}
      </div>
    </div>
  );
};

const PatientCard = ({ patient }) => (
  <div className="patient-card urgent">
    <div className="patient-header">
      <h4>{patient.patient_name}</h4>
      <span className="risk-badge high">{patient.risk_level.toUpperCase()}</span>
    </div>
    
    <div className="patient-contact">
      <p>{patient.email} • {patient.phone}</p>
      <span className="days-since">{patient.days_since_last_contact} days since contact</span>
    </div>
    
    {patient.treatment_notes && (
      <div className="treatment-notes">
        <strong>Treatment Notes:</strong>
        <p>{patient.treatment_notes}</p>
      </div>
    )}
    
    <div className="patient-actions">
      <button 
        className="btn-primary"
        onClick={() => handleContactPatient(patient)}
      >
        Contact Now
      </button>
      <span className="lifetime-value">${patient.lifetime_value_aud}</span>
    </div>
  </div>
);
```

### Advanced Filtering Hook
```typescript
interface ReengagementFilters {
  risk_level?: 'high' | 'medium' | 'low';
  engagement_status?: 'active' | 'dormant' | 'stale';
  action_priority?: 1 | 2 | 3 | 4;
  limit?: number;
  include_treatment_notes?: boolean;
}

const useReengagementPatients = (organizationId: string, filters: ReengagementFilters) => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadPatients = useCallback(async () => {
    setLoading(true);
    
    const queryParams = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });

    try {
      const response = await fetch(
        `/api/v1/reengagement/${organizationId}/prioritized?${queryParams}`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      const data = await response.json();
      setPatients(data.patients);
    } catch (error) {
      console.error('Failed to load patients:', error);
    } finally {
      setLoading(false);
    }
  }, [organizationId, filters]);

  useEffect(() => {
    loadPatients();
  }, [loadPatients]);

  return { patients, loading, reload: loadPatients };
};
```

---

## 🎯 Business Logic Reference

### Engagement Classification
- **ACTIVE**: Recent activity (≤30 days) OR upcoming appointments
- **DORMANT**: Had engagement but gone quiet (>30 days, no upcoming)
- **STALE**: Never had any real engagement (0 appointments, no communication)

### Risk Assessment Logic
- **LOW RISK**: Anyone with upcoming appointments (overrides all other factors)
- **HIGH RISK**: Poor adherence (<60% attendance, 3+ missed) OR long gaps (>90 days)
- **MEDIUM RISK**: Some concerns (30-90 day gaps, <80% attendance)

### Action Priority Matrix
1. **URGENT** (Priority 1): Dormant + High Risk → immediate call required
2. **IMPORTANT** (Priority 2): Active + High Risk, Dormant + Medium Risk  
3. **MEDIUM** (Priority 3): Any Medium Risk patients
4. **LOW** (Priority 4): Active + Low Risk, Stale patients

### Treatment Notes
- **Source**: Patient treatment_notes field from patients table
- **Privacy**: Protected by Row Level Security (RLS)
- **Performance**: Optional in list endpoints to reduce payload size
- **Use Cases**: Staff context, personalized outreach, care continuity

---

## 🔒 Authentication & Security

**Required Headers:**
```http
Authorization: Bearer <clerk_jwt_token>
Content-Type: application/json
```

**Security Features:**
- **Clerk JWT Validation**: All endpoints require valid Clerk session
- **Organization Access Control**: Users can only access their organization's data
- **Row Level Security**: Database-enforced data isolation
- **Treatment Notes Privacy**: Sensitive data protected by RLS policies

**Error Responses:**
```json
// 401 Unauthorized
{
  "detail": "Invalid or missing JWT token"
}

// 403 Forbidden  
{
  "detail": "No access to organization org_123"
}

// 404 Not Found
{
  "detail": "Patient not found"
}
```

---

## 📈 Performance & Optimization

### Database Optimizations
- **Materialized View**: `patient_reengagement_master` view pre-calculates metrics
- **Indexes**: Optimized for filtering by risk_level, engagement_status, action_priority
- **Query Limits**: Default 50, max 200 results per request
- **Selective Fields**: Treatment notes optional to reduce payload

### Caching Strategy
```typescript
// Redis caching for dashboard summary (updates every 15 minutes)
const getCachedDashboardSummary = async (organizationId: string) => {
  const cacheKey = `dashboard:${organizationId}`;
  const cached = await redis.get(cacheKey);
  
  if (cached) {
    return JSON.parse(cached);
  }
  
  const fresh = await fetchDashboardSummary(organizationId);
  await redis.setex(cacheKey, 900, JSON.stringify(fresh)); // 15 min cache
  return fresh;
};
```

### Frontend Performance
```tsx
// Debounced search for real-time filtering
const useDebounceFilter = (filters, delay = 300) => {
  const [debouncedFilters, setDebouncedFilters] = useState(filters);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilters(filters);
    }, delay);

    return () => clearTimeout(timer);
  }, [filters, delay]);

  return debouncedFilters;
};
```

---

## 🚀 Implementation Roadmap

### Phase 1: Core Dashboard (Week 1)
- [ ] Implement dashboard summary endpoint integration
- [ ] Create urgent patients widget
- [ ] Add risk distribution charts
- [ ] Basic patient contact actions

### Phase 2: Advanced Filtering (Week 2)  
- [ ] Multi-criteria patient filtering
- [ ] Treatment notes search functionality
- [ ] Export capabilities (CSV/PDF)
- [ ] Bulk action workflows

### Phase 3: Real-time Updates (Week 3)
- [ ] WebSocket integration for live updates
- [ ] Push notifications for urgent patients
- [ ] Automated reengagement triggers
- [ ] Performance monitoring

### Phase 4: Analytics & Insights (Week 4)
- [ ] Reengagement success tracking
- [ ] ROI analysis dashboard
- [ ] Predictive risk modeling
- [ ] Custom reporting tools

---

## 📞 Support & Next Steps

1. **API Testing**: Use the examples above to test integration
2. **Frontend Framework**: Adapt React examples to your tech stack
3. **Customization**: Modify filtering and display logic as needed
4. **Monitoring**: Add logging and performance tracking
5. **Feedback**: Report issues or feature requests

**Technical Support:**
- Documentation: This guide + inline API docs
- Error Handling: Comprehensive error responses
- Rate Limits: Standard API rate limiting applies
- Monitoring: Built-in performance tracking 