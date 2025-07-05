# Phase 3: Patient Journey Tracking - Backend Requirements

## Overview
**Priority**: Medium  
**Estimated Effort**: 2-3 weeks  
**Phase Goal**: Replace mock patient data with real patient profiles and journey tracking

## Current State
The frontend patient insights components currently use:
- Mock patient data hardcoded in components
- Placeholder risk analysis with fake percentages
- Static patient journey information
- No real engagement tracking or automation state

## Critical API Endpoints Required

### 1. Patient Profiles Endpoint
**Endpoint**: `GET /api/v1/patients/{organizationId}/profiles`

**Purpose**: Replace mock patient data in AllPatientsTab and other patient components

**Request Parameters**:
- `organizationId` (path parameter): Organization identifier
- `limit` (query parameter, optional): Number of patients to return (default: 100)
- `offset` (query parameter, optional): Pagination offset (default: 0)
- `status` (query parameter, optional): "active", "dormant", "at_risk", "all" (default: "all")
- `sort` (query parameter, optional): "name", "ltv", "last_appointment", "risk_score" (default: "name")

**Required Response Schema**:
```json
{
  "patients": [
    {
      "id": string,
      "name": string,
      "phone": string,
      "email": string,
      "ltv": number, // Lifetime value
      "total_sessions": number,
      "last_appointment": string, // ISO timestamp
      "next_appointment": string, // ISO timestamp, nullable
      "status": "active" | "dormant" | "at_risk",
      "risk_score": number, // 0-100
      "engagement_score": number, // 0-100
      "created_at": string, // ISO timestamp
      "updated_at": string // ISO timestamp
    }
  ],
  "total_count": number,
  "has_more": boolean,
  "summary": {
    "total_patients": number,
    "active_patients": number,
    "dormant_patients": number,
    "at_risk_patients": number
  }
}
```

### 2. Patient Risk Summary
**Endpoint**: `GET /api/v1/patients/{organizationId}/risk-summary`

**Purpose**: Basic risk distribution for EngagementOverviewTab

**Required Response Schema**:
```json
{
  "risk_distribution": {
    "low_risk": number,
    "medium_risk": number,
    "high_risk": number
  },
  "total_patients": number,
  "risk_trends": {
    "improving": number,
    "stable": number,
    "declining": number
  },
  "last_calculated": string // ISO timestamp
}
```

### 3. Individual Patient Profile
**Endpoint**: `GET /api/v1/patients/{organizationId}/profile/{patientId}`

**Purpose**: Detailed patient information for individual patient views

**Required Response Schema**:
```json
{
  "patient": {
    "id": string,
    "name": string,
    "phone": string,
    "email": string,
    "date_of_birth": string, // ISO date
    "address": {
      "street": string,
      "city": string,
      "state": string,
      "zip": string
    },
    "medical_info": {
      "conditions": [string],
      "allergies": [string],
      "medications": [string]
    },
    "engagement_metrics": {
      "ltv": number,
      "total_sessions": number,
      "avg_session_value": number,
      "last_appointment": string,
      "next_appointment": string,
      "appointment_history": [
        {
          "date": string,
          "type": string,
          "value": number,
          "notes": string
        }
      ]
    },
    "risk_assessment": {
      "risk_score": number,
      "risk_level": "low" | "medium" | "high",
      "risk_factors": [string],
      "last_assessed": string
    },
    "communication_preferences": {
      "preferred_channel": "phone" | "sms" | "email" | "whatsapp",
      "marketing_consent": boolean,
      "appointment_reminders": boolean
    }
  }
}
```

## Nice-to-Have Enhancements (Can be deferred)

### 4. Patient Journey Tracking
**Endpoint**: `GET /api/v1/patients/{organizationId}/journey/{patientId}`

**Purpose**: Advanced patient journey and automation state tracking

**Response Schema**:
```json
{
  "journey": {
    "patient_id": string,
    "current_stage": string,
    "journey_start": string, // ISO timestamp
    "stages_completed": [
      {
        "stage": string,
        "completed_at": string,
        "outcome": string
      }
    ],
    "automation_state": {
      "current_sequence": string,
      "current_step": string,
      "progress": number, // 0-100
      "next_action": string,
      "next_action_date": string
    },
    "touchpoints": [
      {
        "type": "appointment" | "message" | "call" | "email",
        "timestamp": string,
        "outcome": string,
        "notes": string
      }
    ]
  }
}
```

### 5. Patient Engagement Analytics
**Endpoint**: `GET /api/v1/patients/{organizationId}/engagement/overview`

**Purpose**: Detailed engagement metrics and patient flow analysis

**Response Schema**:
```json
{
  "engagement_overview": {
    "total_patients": number,
    "new_patients_this_month": number,
    "returning_patients": number,
    "engagement_trends": [
      {
        "date": string,
        "new_patients": number,
        "returning_patients": number,
        "engagement_score": number
      }
    ],
    "satisfaction_metrics": {
      "avg_satisfaction": number, // 1-5
      "satisfaction_distribution": {
        "very_satisfied": number,
        "satisfied": number,
        "neutral": number,
        "dissatisfied": number,
        "very_dissatisfied": number
      },
      "nps_score": number // -100 to 100
    }
  }
}
```

### 6. Reengagement Opportunities
**Endpoint**: `GET /api/v1/patients/{organizationId}/opportunities`

**Purpose**: Identify patients for proactive reengagement

**Response Schema**:
```json
{
  "opportunities": [
    {
      "patient_id": string,
      "patient_name": string,
      "opportunity_type": "overdue_appointment" | "inactive_patient" | "high_value_risk",
      "priority": "high" | "medium" | "low",
      "last_contact": string, // ISO timestamp
      "suggested_action": string,
      "estimated_value": number,
      "success_probability": number // 0-1
    }
  ],
  "total_opportunities": number,
  "potential_revenue": number
}
```

## Frontend Components Affected
- `AllPatientsTab` - Patient list and profiles
- `EngagementOverviewTab` - Risk distribution and engagement metrics
- `TopOpportunitiesTab` - Reengagement opportunities
- `PatientJourneyTracker` - Individual patient journey tracking
- `PatientRiskTable` - Risk assessment display
- `UpcomingAppointments` - Appointment scheduling

## Data Sources Required
Your backend will need to integrate with:
- Patient management system (EHR/EMR)
- Appointment scheduling system
- Financial/billing system for LTV calculations
- Communication logs (calls, messages, emails)
- Satisfaction survey data
- Automation/workflow systems
- Risk assessment algorithms

## Business Logic Requirements

### Patient Status Classification
- **Active**: Engaged within last 30 days or has upcoming appointment
- **Dormant**: No engagement in 30-90 days but has appointment history
- **At Risk**: No engagement in 90+ days or shows declining engagement pattern

### Risk Score Calculation
- Consider appointment frequency, communication responsiveness, payment history
- Factor in time since last contact and missed appointments
- Include satisfaction scores and complaint history
- Weight recent activities more heavily than older data

### Engagement Score Calculation
- Track appointment attendance rates
- Monitor communication responsiveness
- Include satisfaction ratings
- Consider referral activity and treatment compliance

### LTV Calculation
- Sum of all historical revenue from patient
- Factor in average appointment value and frequency
- Consider potential future value based on treatment plans
- Include referral value if applicable

## Success Criteria
- [ ] AllPatientsTab displays real patient profiles instead of mock data
- [ ] Risk distribution shows actual calculated percentages
- [ ] Patient profiles load with real engagement metrics
- [ ] LTV calculations reflect actual patient value
- [ ] Risk assessment updates based on patient behavior
- [ ] Appointment history displays correctly
- [ ] Patient filtering and sorting works properly

## Dependencies
- Organization ID routing functional
- Patient management system integration
- Appointment scheduling system access
- Financial/billing system integration
- Communication platform integrations

## Testing Requirements
- Test with various patient dataset sizes
- Verify risk calculation accuracy
- Test pagination with large patient lists
- Validate LTV calculations
- Test patient status classification logic
- Verify data privacy and HIPAA compliance

## Error Handling
- Handle missing patient data gracefully
- Manage calculation errors for risk/engagement scores
- Provide defaults for missing metrics
- Clear error messages for data access failures
- Fallback for when patient systems are unavailable

## Security Considerations
- Ensure HIPAA compliance for patient data
- Implement proper data access controls
- Encrypt sensitive patient information
- Audit logging for patient data access
- Validate user permissions for patient viewing

## Performance Considerations
- Implement efficient pagination for large patient lists
- Cache frequently accessed patient profiles
- Optimize risk calculation queries
- Consider data aggregation for large datasets
- Implement proper indexing for patient searches

## Privacy & Compliance
- Ensure patient data is properly anonymized in analytics
- Implement data retention policies
- Handle patient consent for data usage
- Provide data export capabilities for patient requests
- Maintain audit trails for patient data access 