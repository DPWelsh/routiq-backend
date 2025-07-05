# Phase 1: Dashboard Analytics - Backend Requirements

## Overview
**Priority**: High  
**Estimated Effort**: 2-3 weeks  
**Phase Goal**: Replace hardcoded dashboard metrics with real data from backend APIs

## Current State
The frontend dashboard currently displays hardcoded values:
- Bookings: 247
- Patients: 89  
- ROI: 284%

These need to be replaced with real-time data from your backend systems.

## Critical API Endpoints Required

### 1. Dashboard Analytics Endpoint
**Endpoint**: `GET /api/v1/dashboard/{organizationId}/analytics`

**Purpose**: Core dashboard metrics to replace all hardcoded values

**Request Parameters**:
- `organizationId` (path parameter): Organization identifier
- `timeframe` (query parameter, optional): "7d", "30d", "90d", "1y" (default: "30d")

**Required Response Schema**:
```json
{
  "booking_metrics": {
    "total_bookings": number,
    "period_comparison": number, // percentage change vs previous period
    "bookings_via_ai": number
  },
  "patient_metrics": {
    "total_patients": number,
    "active_patients": number,
    "new_patients": number
  },
  "financial_metrics": {
    "total_revenue": number,
    "avg_revenue_per_patient": number
  },
  "automation_metrics": {
    "total_roi": number, // percentage (e.g., 284 for 284%)
    "automation_bookings": number,
    "efficiency_score": number
  },
  "timeframe": string,
  "last_updated": string // ISO timestamp
}
```

**Business Logic Requirements**:
- Calculate booking metrics based on appointment/booking data
- Determine patient status (active = engaged in last 30 days)
- ROI calculation should be based on revenue generated vs operational costs
- Period comparison should be percentage change from previous equivalent period

## Nice-to-Have Enhancements (Can be deferred)

### 2. Dashboard Charts Data
**Endpoint**: `GET /api/v1/dashboard/{organizationId}/charts`

**Purpose**: Time-series data for dashboard visualizations

**Response Schema**:
```json
{
  "booking_trends": [
    {
      "date": "2024-01-01",
      "bookings": number,
      "revenue": number
    }
  ],
  "patient_satisfaction_trend": [
    {
      "date": "2024-01-01", 
      "satisfaction_score": number, // 1-5 scale
      "response_count": number
    }
  ],
  "automation_performance": [
    {
      "date": "2024-01-01",
      "ai_bookings": number,
      "total_bookings": number,
      "efficiency": number
    }
  ]
}
```

### 3. Real-time Dashboard Updates
**Endpoint**: `WebSocket /api/v1/dashboard/{organizationId}/live`

**Purpose**: Push real-time updates to dashboard metrics

## Frontend Components Affected
- `ClinicOverviewTab` - Main metrics display
- `PatientInsightsTab` - Patient statistics and satisfaction
- `AutomationSummaryTab` - ROI and automation metrics
- `MainDashboardTabs` - Overall dashboard coordination

## Data Sources Required
Your backend will need to aggregate data from:
- Booking/appointment systems
- Patient management systems
- Financial/revenue tracking
- Automation/AI interaction logs
- Patient feedback/satisfaction data

## Success Criteria
- [ ] Dashboard shows real booking counts instead of "247"
- [ ] Patient metrics reflect actual patient database
- [ ] ROI percentage calculated from real revenue/cost data
- [ ] Metrics update based on selected time period
- [ ] Data refreshes without page reload

## Dependencies
- Organization ID routing working
- Basic authentication/authorization in place
- Access to booking, patient, and financial data sources

## Testing Requirements
- Test with multiple organizations to ensure data isolation
- Verify metrics calculation accuracy
- Test various timeframe selections
- Validate period comparison calculations
- Performance testing with large datasets

## Error Handling
- Graceful handling when no data available for time period
- Default values for missing metrics
- Clear error messages for calculation failures
- Timeout handling for slow queries

## Security Considerations
- Ensure organization-level data isolation
- Validate user permissions for organization access
- Sanitize all input parameters
- Rate limiting for dashboard API calls 