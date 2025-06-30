# Enhanced Patients API Endpoints

This document describes the new enhanced patients API endpoints that leverage the `patients_summary` database view for optimal performance and rich data.

## Endpoints Overview

### 1. Enhanced Patient Listing
**Endpoint:** `GET /api/v1/patients/{organization_id}/list`

### 2. Engagement Statistics
**Endpoint:** `GET /api/v1/patients/{organization_id}/engagement-stats`

---

## 1. Enhanced Patient Listing

### Endpoint
```http
GET /api/v1/patients/{organization_id}/list
Authorization: Bearer <jwt_token>
```

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number for pagination |
| `limit` | integer | 50 | Results per page (max: 200) |
| `search` | string | null | Search by name, email, phone, or Cliniko ID |
| `active_only` | boolean | true | Filter to active patients only |
| `engagement_filter` | string | null | Filter by engagement status: `engaged`, `inactive`, `never_engaged` |

### Example Requests

**Basic request:**
```http
GET /api/v1/patients/org_123/list
```

**With search and pagination:**
```http
GET /api/v1/patients/org_123/list?search=john&page=2&limit=25
```

**Filter by engagement:**
```http
GET /api/v1/patients/org_123/list?engagement_filter=engaged&active_only=true
```

### Response Structure

```json
{
  "organization_id": "org_123",
  "patients": [
    {
      "id": "uuid-here",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "0412345678",
      "contact_type": "cliniko_patient",
      "cliniko_patient_id": "12345",
      "is_active": true,
      "activity_status": "active",
      
      // Appointment counts
      "recent_appointment_count": 2,
      "upcoming_appointment_count": 1,
      "total_appointment_count": 15,
      
      // Dates
      "first_appointment_date": "2024-01-15T09:00:00.000Z",
      "last_appointment_date": "2025-06-25T14:30:00.000Z",
      "next_appointment_time": "2025-07-02T10:00:00.000Z",
      "next_appointment_type": "Physiotherapy",
      "primary_appointment_type": "Physiotherapy",
      
      // Treatment
      "treatment_notes": "Lower back pain treatment",
      
      // Engagement metrics (calculated by view)
      "engagement_status": "engaged",
      "days_until_next_appointment": 7,
      "days_since_last_appointment": 5,
      "has_upcoming_appointment": true,
      "has_recent_appointment": true,
      
      // UI helpers
      "display_name": "John Doe",
      "primary_contact": "john@example.com",
      
      // Timestamps
      "last_synced_at": "2025-06-30T11:00:00.000Z",
      "created_at": "2024-01-15T09:00:00.000Z",
      "updated_at": "2025-06-30T11:00:00.000Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_count": 125,
    "page_size": 50,
    "has_next": true,
    "has_prev": false
  },
  "filters": {
    "search": null,
    "active_only": true,
    "engagement_filter": null
  },
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Key Features

1. **Smart Sorting**: Patients are automatically sorted by priority:
   - Patients with upcoming appointments first
   - Then patients with recent appointments
   - Then patients with historical appointments
   - Finally, patients who never had appointments

2. **Rich Engagement Data**: Each patient includes calculated engagement metrics:
   - `engagement_status`: 'engaged', 'inactive', or 'never_engaged'
   - `days_until_next_appointment`: Time until next appointment
   - `days_since_last_appointment`: Time since last appointment
   - Boolean flags for recent/upcoming appointments

3. **UI-Friendly Fields**:
   - `display_name`: Never null patient name
   - `primary_contact`: Best available contact method

4. **Advanced Search**: Search across name, email, phone, and Cliniko patient ID

5. **Flexible Filtering**: Filter by engagement status or active status

---

## 2. Engagement Statistics

### Endpoint
```http
GET /api/v1/patients/{organization_id}/engagement-stats
Authorization: Bearer <jwt_token>
```

### Example Request
```http
GET /api/v1/patients/org_123/engagement-stats
```

### Response Structure

```json
{
  "organization_id": "org_123",
  "total_active_patients": 37,
  "engagement_breakdown": [
    {
      "status": "engaged",
      "patient_count": 25,
      "percentage": 67.6,
      "avg_recent_appointments": 1.8,
      "avg_upcoming_appointments": 1.2,
      "avg_total_appointments": 12.4
    },
    {
      "status": "inactive",
      "patient_count": 8,
      "percentage": 21.6,
      "avg_recent_appointments": 0.0,
      "avg_upcoming_appointments": 0.0,
      "avg_total_appointments": 5.2
    },
    {
      "status": "never_engaged",
      "patient_count": 4,
      "percentage": 10.8,
      "avg_recent_appointments": 0.0,
      "avg_upcoming_appointments": 0.0,
      "avg_total_appointments": 0.0
    }
  ],
  "timestamp": "2025-06-30T12:00:00.000Z"
}
```

### Key Features

1. **Engagement Breakdown**: Shows patient distribution across engagement levels
2. **Percentages**: Automatic percentage calculations
3. **Appointment Averages**: Average appointment counts per engagement status
4. **Ordered Results**: Results ordered by engagement priority

---

## Frontend Integration Examples

### React Hook for Patient List

```typescript
const usePatients = (organizationId: string, filters = {}) => {
  const [patients, setPatients] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchPatients = async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        ...filters
      });
      
      const response = await fetch(
        `/api/v1/patients/${organizationId}/list?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      const data = await response.json();
      setPatients(data.patients);
      setPagination(data.pagination);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    } finally {
      setLoading(false);
    }
  };

  return { patients, pagination, loading, fetchPatients };
};
```

### Search and Filter Component

```typescript
const PatientFilters = ({ onFilterChange }) => {
  const [search, setSearch] = useState('');
  const [engagementFilter, setEngagementFilter] = useState('');

  const handleFilterChange = () => {
    onFilterChange({
      search: search || undefined,
      engagement_filter: engagementFilter || undefined,
      active_only: true
    });
  };

  return (
    <div className="flex gap-4 mb-4">
      <input
        type="text"
        placeholder="Search patients..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        onBlur={handleFilterChange}
      />
      
      <select
        value={engagementFilter}
        onChange={(e) => {
          setEngagementFilter(e.target.value);
          handleFilterChange();
        }}
      >
        <option value="">All Engagement Levels</option>
        <option value="engaged">Engaged</option>
        <option value="inactive">Inactive</option>
        <option value="never_engaged">Never Engaged</option>
      </select>
    </div>
  );
};
```

---

## Performance Notes

1. **Database View**: These endpoints use the optimized `patients_summary` view
2. **Indexes**: Proper indexes are created for common query patterns
3. **Pagination**: Built-in pagination prevents large data transfers
4. **Calculated Fields**: Engagement metrics are pre-calculated in the database

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (no access to organization)
- `500`: Internal server error

Error responses include detailed error messages:

```json
{
  "detail": "Failed to retrieve patients: Database connection error"
}
```

---

## Rate Limits

These endpoints are subject to the standard API rate limits:
- **API Tier**: 1000 requests per 15 minutes
- **Admin Tier**: 50 requests per 15 minutes (for engagement stats) 