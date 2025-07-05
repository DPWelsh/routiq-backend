# Phase 4: Connected Services - Backend Requirements

## Overview
**Priority**: Low  
**Estimated Effort**: 1-2 weeks  
**Phase Goal**: Replace static integration status with real integration health monitoring

## Current State
The frontend IntegrationsPage currently shows:
- Static integration status (hardcoded connected/disconnected states)
- No real health monitoring or metrics
- No actual integration management capabilities
- No error reporting or troubleshooting information

## Critical API Endpoints Required

### 1. Integration Status Endpoint
**Endpoint**: `GET /api/v1/integrations/{organizationId}/status`

**Purpose**: Show real integration connection status and basic health metrics

**Request Parameters**:
- `organizationId` (path parameter): Organization identifier

**Required Response Schema**:
```json
{
  "integrations": [
    {
      "id": string,
      "name": string,
      "type": "chatwoot" | "cliniko" | "whatsapp" | "instagram" | "stripe" | "n8n",
      "status": "connected" | "disconnected" | "error" | "warning",
      "last_sync": string, // ISO timestamp
      "next_sync": string, // ISO timestamp, nullable
      "connection_health": "excellent" | "good" | "fair" | "poor",
      "error_message": string, // nullable
      "configuration": {
        "endpoint": string,
        "authenticated": boolean,
        "permissions": [string]
      }
    }
  ],
  "overall_health": "excellent" | "good" | "fair" | "poor",
  "total_integrations": number,
  "active_integrations": number,
  "last_updated": string // ISO timestamp
}
```

### 2. Integration Configuration
**Endpoint**: `GET /api/v1/integrations/{organizationId}/config/{integrationId}`

**Purpose**: Get detailed configuration for a specific integration

**Required Response Schema**:
```json
{
  "integration": {
    "id": string,
    "name": string,
    "type": string,
    "status": string,
    "configuration": {
      "endpoint": string,
      "api_key_status": "valid" | "invalid" | "expired",
      "permissions": [string],
      "webhook_urls": [string],
      "rate_limits": {
        "requests_per_minute": number,
        "current_usage": number
      }
    },
    "last_test": {
      "timestamp": string,
      "success": boolean,
      "response_time": number, // in milliseconds
      "error_details": string // nullable
    }
  }
}
```

## Nice-to-Have Enhancements (Can be deferred)

### 3. Integration Health Monitoring
**Endpoint**: `GET /api/v1/integrations/{organizationId}/health`

**Purpose**: Detailed health metrics and monitoring data

**Response Schema**:
```json
{
  "health_summary": {
    "overall_score": number, // 0-100
    "uptime_percentage": number, // 0-100
    "avg_response_time": number, // in milliseconds
    "error_rate": number, // 0-1
    "last_24h_errors": number
  },
  "integration_health": [
    {
      "integration_id": string,
      "health_score": number, // 0-100
      "uptime": number, // percentage
      "avg_response_time": number,
      "error_count": number,
      "last_error": {
        "timestamp": string,
        "error_type": string,
        "message": string
      }
    }
  ],
  "recent_incidents": [
    {
      "integration_id": string,
      "timestamp": string,
      "incident_type": "connection_failed" | "rate_limit" | "authentication_error",
      "severity": "low" | "medium" | "high" | "critical",
      "resolved": boolean,
      "resolution_time": number // in minutes, nullable
    }
  ]
}
```

### 4. Integration Usage Analytics
**Endpoint**: `GET /api/v1/integrations/{organizationId}/usage`

**Purpose**: Usage statistics and analytics for integrations

**Response Schema**:
```json
{
  "usage_summary": {
    "total_api_calls": number,
    "api_calls_today": number,
    "data_synced": {
      "patients": number,
      "appointments": number,
      "messages": number
    },
    "costs": {
      "total_monthly": number,
      "current_month": number,
      "projected_month": number
    }
  },
  "integration_usage": [
    {
      "integration_id": string,
      "api_calls": number,
      "data_transferred": number, // in MB
      "rate_limit_usage": number, // percentage
      "cost": number
    }
  ],
  "usage_trends": [
    {
      "date": string,
      "api_calls": number,
      "data_transferred": number,
      "costs": number
    }
  ]
}
```

### 5. Integration Testing
**Endpoint**: `POST /api/v1/integrations/{organizationId}/test/{integrationId}`

**Purpose**: Test integration connection and functionality

**Request Body**:
```json
{
  "test_type": "connection" | "authentication" | "data_sync" | "full",
  "parameters": object // Optional test parameters
}
```

**Response Schema**:
```json
{
  "test_results": {
    "success": boolean,
    "test_type": string,
    "timestamp": string,
    "duration": number, // in milliseconds
    "results": [
      {
        "check": string,
        "passed": boolean,
        "message": string,
        "details": object // Optional additional details
      }
    ],
    "recommendations": [string] // Optional improvement suggestions
  }
}
```

### 6. Integration Management
**Endpoint**: `POST /api/v1/integrations/{organizationId}/manage/{integrationId}`

**Purpose**: Manage integration settings and trigger actions

**Request Body**:
```json
{
  "action": "enable" | "disable" | "reset" | "sync" | "update_config",
  "parameters": object // Action-specific parameters
}
```

## Frontend Components Affected
- `IntegrationsPage` - Main integration status display
- Dashboard integration health widgets
- Navigation alerts for integration issues
- Settings integration configuration

## Data Sources Required
Your backend will need to monitor:
- WhatsApp Business API status and quotas
- Instagram API connection and permissions
- Chatwoot system health and connectivity
- Cliniko API status and sync operations
- Stripe payment processing status
- N8N workflow execution status
- Other third-party service integrations

## Business Logic Requirements

### Integration Status Determination
- **Connected**: Active API connection with successful recent calls
- **Disconnected**: No active connection or failed authentication
- **Error**: Connection exists but encountering errors
- **Warning**: Connected but with degraded performance or approaching limits

### Health Score Calculation
- Factor in uptime percentage, response time, error rate
- Weight recent performance more heavily than historical
- Consider rate limit usage and quota consumption
- Include webhook delivery success rates

### Error Classification
- **Authentication errors**: Invalid API keys, expired tokens
- **Rate limiting**: API quota exceeded, throttling active
- **Connection errors**: Network issues, service unavailable
- **Data sync errors**: Inconsistent data, validation failures

## Success Criteria
- [ ] IntegrationsPage shows real connection status instead of static data
- [ ] Integration health scores reflect actual system performance
- [ ] Error messages provide actionable troubleshooting information
- [ ] Integration testing functionality works correctly
- [ ] Usage analytics display accurate API consumption data
- [ ] Alerts trigger for integration issues

## Dependencies
- Organization ID routing functional
- Authentication tokens for all integrated services
- Monitoring infrastructure for API calls
- Webhook handling for real-time status updates

## Testing Requirements
- Test with various integration combinations
- Verify error handling for different failure scenarios
- Test rate limiting and quota management
- Validate health score calculations
- Test integration management actions
- Verify data isolation between organizations

## Error Handling
- Graceful handling of integration service outages
- Clear error messages for configuration issues
- Fallback behavior when monitoring systems are unavailable
- Proper timeout handling for integration tests
- Recovery procedures for failed integrations

## Security Considerations
- Secure storage of API keys and tokens
- Encrypted communication with all integrated services
- Audit logging for integration configuration changes
- Validation of webhook signatures and authenticity
- Rate limiting for integration management endpoints

## Performance Considerations
- Cache integration status to avoid excessive API calls
- Efficient polling intervals for status updates
- Batch processing for usage analytics
- Optimize database queries for health metrics
- Consider background jobs for integration testing

## Monitoring & Alerting
- Set up alerts for integration failures
- Monitor API quota usage and approaching limits
- Track integration performance trends
- Alert on configuration changes or security issues
- Implement escalation procedures for critical failures

## Compliance & Governance
- Ensure integration configurations meet security standards
- Implement approval workflows for integration changes
- Maintain audit trails for all integration activities
- Document integration dependencies and data flows
- Regular security reviews of integration configurations 