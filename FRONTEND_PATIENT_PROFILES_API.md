# Patient Profiles API - Frontend Integration Guide

## Overview

The Patient Profiles API provides comprehensive patient conversation data for building reengagement dashboards. This API exposes rich patient profiles from the `patient_conversation_profile` view with 40+ data fields per patient.

**Base URL**: `https://routiq-backend-prod.up.railway.app/api/v1/reengagement`

## Authentication

**No authentication required** - These endpoints follow the dashboard pattern and are accessible without authentication headers.

## Endpoints Summary

| Endpoint | Purpose | Use Case |
|----------|---------|----------|
| `GET /{org_id}/patient-profiles/debug` | Development testing | Get 5 sample patients for UI development |
| `GET /{org_id}/patient-profiles/summary` | Dashboard metrics | Show total counts and engagement breakdown |
| `GET /{org_id}/patient-profiles` | Main patient list | Paginated list with search and filtering |
| `GET /{org_id}/patient-profiles/{patient_id}` | Individual patient | Detailed patient profile view |

---

## 1. Debug Endpoint (Development Only)

**Purpose**: Get sample patient data for development and testing.

```typescript
GET /{organization_id}/patient-profiles/debug
```

### Example Request
```typescript
const response = await fetch(
  'https://routiq-backend-prod.up.railway.app/api/v1/reengagement/org_2xwHiNrj68eaRUlX10anlXGvzX7/patient-profiles/debug'
);
const data = await response.json();
```

### Response
```json
{
  "success": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "debug_profiles": [
    {
      "patient_id": "05ad0765-1544-4a12-ab2c-36aa6c58f81a",
      "patient_name": "Daniel Harris",
      "email": "harris.danielc@gmail.com",
      "phone": "18607168079",
      "estimated_lifetime_value": 1050,
      "engagement_level": "disengaged",
      "churn_risk": "low",
      "total_appointment_count": 7,
      "next_appointment_time": "2025-07-11T05:00:00+00:00"
    }
  ],
  "count": 5,
  "view_exists": true,
  "timestamp": "2025-07-04T08:49:54.328565"
}
```

---

## 2. Summary Endpoint

**Purpose**: Get dashboard summary statistics for patient engagement overview.

```typescript
GET /{organization_id}/patient-profiles/summary
```

### Example Request
```typescript
const getSummary = async (organizationId: string) => {
  const response = await fetch(
    `https://routiq-backend-prod.up.railway.app/api/v1/reengagement/${organizationId}/patient-profiles/summary`
  );
  return await response.json();
};
```

### Response
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
  "timestamp": "2025-07-04T08:48:59.377235"
}
```

### Summary Interface
```typescript
interface PatientSummary {
  total_patients: number;
  highly_engaged: number;
  moderately_engaged: number;
  low_engagement: number;
  disengaged: number;
  critical_risk: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
}

interface SummaryResponse {
  success: boolean;
  organization_id: string;
  summary: PatientSummary;
  timestamp: string;
}
```

---

## 3. Main Patient Profiles Endpoint

**Purpose**: Get paginated list of patient profiles with search and filtering capabilities.

```typescript
GET /{organization_id}/patient-profiles?limit={limit}&offset={offset}&search={search}
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 50 | Number of patients to return (max: 200) |
| `offset` | number | 0 | Number of patients to skip for pagination |
| `search` | string | - | Search by patient name, email, or phone |

### Example Requests

**Basic pagination:**
```typescript
const getPatients = async (organizationId: string, page: number = 0, pageSize: number = 50) => {
  const offset = page * pageSize;
  const response = await fetch(
    `https://routiq-backend-prod.up.railway.app/api/v1/reengagement/${organizationId}/patient-profiles?limit=${pageSize}&offset=${offset}`
  );
  return await response.json();
};
```

**Search functionality:**
```typescript
const searchPatients = async (organizationId: string, searchTerm: string) => {
  const response = await fetch(
    `https://routiq-backend-prod.up.railway.app/api/v1/reengagement/${organizationId}/patient-profiles?search=${encodeURIComponent(searchTerm)}&limit=100`
  );
  return await response.json();
};

// Usage examples:
await searchPatients(orgId, "Daniel");           // Search by name
await searchPatients(orgId, "harris@gmail.com"); // Search by email  
await searchPatients(orgId, "18607168079");      // Search by phone
```

### Response
```json
{
  "success": true,
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "patient_profiles": [
    {
      "patient_id": "05ad0765-1544-4a12-ab2c-36aa6c58f81a",
      "patient_name": "Daniel Harris",
      "email": "harris.danielc@gmail.com",
      "phone": "18607168079",
      "estimated_lifetime_value": 1050,
      "engagement_level": "disengaged",
      "churn_risk": "low"
    }
  ],
  "count": 2,
  "timestamp": "2025-07-04T08:50:05.938845"
}
```

---

## 4. Individual Patient Endpoint

**Purpose**: Get detailed profile for a specific patient.

```typescript
GET /{organization_id}/patient-profiles/{patient_id}
```

### Example Request
```typescript
const getPatientProfile = async (organizationId: string, patientId: string) => {
  const response = await fetch(
    `https://routiq-backend-prod.up.railway.app/api/v1/reengagement/${organizationId}/patient-profiles/${patientId}`
  );
  return await response.json();
};
```

### Response
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
    "estimated_lifetime_value": 1050
  },
  "timestamp": "2025-07-04T08:50:29.719069"
}
```

---

## Complete TypeScript Interfaces

```typescript
// Core patient profile interface - all 40+ fields available
interface PatientProfile {
  // Identity & Contact
  patient_id: string;
  organization_id: string;
  patient_name: string;
  email: string | null;
  phone: string | null;
  cliniko_patient_id: string;
  
  // Status & Activity
  is_active: boolean;
  activity_status: 'active' | 'recently_active' | 'inactive' | 'upcoming_only';
  contact_type: string;
  patient_status: string;
  medical_record_number: string | null;
  
  // Treatment & Notes
  treatment_summary: string | null;
  last_treatment_note: string | null;
  treatment_notes: string | null;
  
  // Appointment Metrics
  total_appointment_count: number;
  recent_appointment_count: number;
  upcoming_appointment_count: number;
  first_appointment_date: string | null;
  last_appointment_date: string | null;
  next_appointment_time: string | null;
  next_appointment_type: string | null;
  primary_appointment_type: string | null;
  
  // Current Appointment Details
  current_appointment_type: string | null;
  current_appointment_status: string | null;
  current_appointment_notes: string | null;
  
  // Next Appointment Details
  next_appointment_date: string | null;
  next_appointment_status: string | null;
  next_appointment_notes: string | null;
  
  // Conversation Metrics
  total_conversations: number;
  active_conversations: number;
  last_conversation_date: string | null;
  days_since_last_conversation: number | null;
  overall_sentiment: string | null;
  avg_sentiment_score: number | null;
  escalation_count: number;
  quality_rating_avg: number | null;
  
  // Message Metrics
  total_messages: number;
  patient_messages: number;
  agent_messages: number;
  last_message_date: string | null;
  last_message_sentiment: string | null;
  avg_message_sentiment: string | null;
  days_since_last_message: number | null;
  
  // Outreach Metrics
  total_outreach_attempts: number;
  successful_outreach: number;
  last_outreach_date: string | null;
  last_outreach_method: string | null;
  last_outreach_outcome: string | null;
  outreach_success_rate: number;
  days_since_last_outreach: number | null;
  
  // Engagement & Risk Assessment
  engagement_level: 'highly_engaged' | 'moderately_engaged' | 'low_engagement' | 'disengaged';
  churn_risk: 'critical' | 'high' | 'medium' | 'low';
  estimated_lifetime_value: number;
  contact_success_prediction: 'very_high' | 'high' | 'medium' | 'low' | 'very_low';
  action_priority: number; // 1=urgent, 2=important, 3=medium, 4=low, 5=minimal
  
  // Time Calculations
  days_since_last_appointment: number | null;
  days_until_next_appointment: number | null;
  days_until_next_appointment_detailed: number | null;
  
  // Metadata
  patient_created_at: string;
  patient_updated_at: string;
  last_synced_at: string;
  view_generated_at: string;
}

// API Response interfaces
interface PatientProfilesResponse {
  success: boolean;
  organization_id: string;
  patient_profiles: PatientProfile[];
  count: number;
  timestamp: string;
}

interface IndividualPatientResponse {
  success: boolean;
  organization_id: string;
  patient_id: string;
  profile: PatientProfile;
  timestamp: string;
}

interface DebugResponse {
  success: boolean;
  organization_id: string;
  debug_profiles: PatientProfile[];
  count: number;
  view_exists: boolean;
  timestamp: string;
}
```

---

## Implementation Examples

### React Hook for Patient Profiles

```typescript
import { useState, useEffect } from 'react';

interface UsePatientProfilesProps {
  organizationId: string;
  pageSize?: number;
}

export const usePatientProfiles = ({ organizationId, pageSize = 50 }: UsePatientProfilesProps) => {
  const [profiles, setProfiles] = useState<PatientProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const loadProfiles = async (page: number = 0, search?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const offset = page * pageSize;
      const searchParam = search ? `&search=${encodeURIComponent(search)}` : '';
      
      const response = await fetch(
        `https://routiq-backend-prod.up.railway.app/api/v1/reengagement/${organizationId}/patient-profiles?limit=${pageSize}&offset=${offset}${searchParam}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data: PatientProfilesResponse = await response.json();
      
      if (page === 0) {
        setProfiles(data.patient_profiles);
      } else {
        setProfiles(prev => [...prev, ...data.patient_profiles]);
      }
      
      setHasMore(data.patient_profiles.length === pageSize);
      setCurrentPage(page);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patient profiles');
    } finally {
      setLoading(false);
    }
  };

  const searchProfiles = (searchTerm: string) => {
    setCurrentPage(0);
    loadProfiles(0, searchTerm);
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      loadProfiles(currentPage + 1);
    }
  };

  useEffect(() => {
    loadProfiles(0);
  }, [organizationId]);

  return {
    profiles,
    loading,
    error,
    hasMore,
    searchProfiles,
    loadMore,
    refresh: () => loadProfiles(0)
  };
};
```

### Patient Search Component

```typescript
import React, { useState, useCallback } from 'react';
import { debounce } from 'lodash';

interface PatientSearchProps {
  organizationId: string;
  onResults: (profiles: PatientProfile[]) => void;
  onLoading: (loading: boolean) => void;
}

export const PatientSearch: React.FC<PatientSearchProps> = ({
  organizationId,
  onResults,
  onLoading
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const performSearch = useCallback(
    debounce(async (term: string) => {
      if (!term.trim()) {
        onResults([]);
        return;
      }

      onLoading(true);
      try {
        const response = await fetch(
          `https://routiq-backend-prod.up.railway.app/api/v1/reengagement/${organizationId}/patient-profiles?search=${encodeURIComponent(term)}&limit=100`
        );
        
        const data: PatientProfilesResponse = await response.json();
        onResults(data.patient_profiles);
      } catch (error) {
        console.error('Search failed:', error);
        onResults([]);
      } finally {
        onLoading(false);
      }
    }, 300),
    [organizationId, onResults, onLoading]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    performSearch(value);
  };

  return (
    <div className="patient-search">
      <input
        type="text"
        value={searchTerm}
        onChange={handleInputChange}
        placeholder="Search by name, email, or phone..."
        className="search-input"
      />
      <div className="search-help">
        <small>
          Try: "Daniel", "harris@gmail.com", or "18607168079"
        </small>
      </div>
    </div>
  );
};
```

---

## Key Implementation Notes

### 1. **No Authentication Required**
These endpoints follow the dashboard pattern - no auth headers needed.

### 2. **Search is Flexible**
- Searches across `patient_name`, `email`, and `phone` fields
- Case-insensitive partial matching using `ILIKE`
- Works with partial terms (e.g., "Dan" finds "Daniel")

### 3. **Pagination Strategy**
- Use `limit` and `offset` for pagination
- Default limit is 50, maximum is 200
- Check `count` in response to determine if more data available

### 4. **Data Freshness**
- Data comes from `patient_conversation_profile` view
- Updated via Cliniko sync process
- Check `last_synced_at` and `view_generated_at` for data freshness

### 5. **Rich Data Available**
- 40+ fields per patient including engagement metrics, risk scores, financial data
- Appointment history and upcoming appointments
- Conversation and outreach tracking
- Calculated fields like `days_until_next_appointment`

### 6. **Performance Considerations**
- Use search instead of loading all patients and filtering client-side
- Implement debounced search to avoid excessive API calls
- Consider virtual scrolling for large patient lists
- Cache summary data as it changes infrequently

---

## Quick Start Checklist

1. ✅ **Test endpoints** using the debug endpoint first
2. ✅ **Implement summary** dashboard using summary endpoint  
3. ✅ **Build patient list** with pagination and search
4. ✅ **Add patient detail** views using individual patient endpoint
5. ✅ **Handle errors** gracefully with user-friendly messages
6. ✅ **Optimize performance** with debounced search and caching

The API is production-ready and provides comprehensive patient data for building powerful reengagement dashboards. All endpoints are tested and working with 651 patients available. 