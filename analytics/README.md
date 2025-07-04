# Reengagement Analytics Module

This module provides comprehensive analytics for the reengagement API endpoints, generating insights and reports from patient engagement data.

## Overview

The analytics module tests and analyzes data from the following reengagement API endpoints:

- `GET /api/v1/reengagement/health` - Health check
- `GET /api/v1/reengagement/{organization_id}/risk-metrics` - Risk metrics and priorities
- `GET /api/v1/reengagement/{organization_id}/prioritized` - Prioritized patient list
- `GET /api/v1/reengagement/{organization_id}/dashboard-summary` - Dashboard summary
- `GET /api/v1/reengagement/{organization_id}/performance` - Performance metrics

## Files

### Core Analytics
- `reengagement_analytics.py` - Main analytics engine
- `test_endpoints.py` - Endpoint testing utility
- `demo_analytics.py` - Demo script showing usage

### Generated Reports
- `reports/` - Directory containing generated analytics reports
- `demo_reports/` - Directory for demo reports

## Installation

Install required dependencies:

```bash
pip install aiohttp asyncio
```

## Usage

### 1. Test Endpoints First

Before running analytics, test that your API endpoints are working:

```bash
python analytics/test_endpoints.py --organization-id your-org-id
```

### 2. Run Analytics Report

Generate a comprehensive analytics report:

```bash
python analytics/reengagement_analytics.py --organization-id your-org-id
```

### 3. Custom Configuration

You can customize the base URL and output directory:

```bash
python analytics/reengagement_analytics.py \
  --organization-id your-org-id \
  --base-url http://localhost:8000 \
  --output-dir analytics/custom_reports
```

### 4. Demo Usage

Run the demo to see how the module works:

```bash
python analytics/demo_analytics.py
```

## Configuration Options

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--organization-id` | Organization ID to analyze | Required |
| `--base-url` | Base URL for API | `http://localhost:8000` |
| `--output-dir` | Output directory for reports | `analytics/reports` |

### Environment Variables

You can also set these via environment variables:

```bash
export REENGAGEMENT_BASE_URL="http://localhost:8000"
export REENGAGEMENT_ORG_ID="your-org-id"
```

## Report Structure

The analytics generate two types of reports:

### 1. Executive Summary
- API health status
- Total patients analyzed
- Key risk metrics
- Action priorities
- Automated recommendations

### 2. Detailed Analytics Report
- Raw API response data
- Risk distribution analysis
- Engagement breakdown
- Performance metrics
- Trend analysis

## Example Output

```
================================================================================
REENGAGEMENT ANALYTICS REPORT - EXECUTIVE SUMMARY
================================================================================
📊 Organization ID: your-org-id
🕐 Generated: 2024-01-15T10:30:00
🏥 API Health: healthy
👥 Total Patients: 1,250
🔗 Endpoints Tested: 5

📈 KEY METRICS:
  🔴 High Risk Patients: 45
  😴 Dormant Patients: 120
  🚨 Urgent Priority Patients: 25

🎯 RECOMMENDATIONS:
  ⚠️ High dormancy rate: 9.6% of patients are dormant
  📝 Review and optimize engagement strategies
================================================================================
```

## API Endpoint Analysis

### Working Endpoints

Based on the analysis, these endpoints are **working**:

- ✅ Health Check
- ✅ Risk Metrics (uses `patient_reengagement_master` view)
- ✅ Prioritized Patients
- ✅ Dashboard Summary
- ✅ Performance Metrics

### Broken Endpoints

These endpoints are **not working** (need to be fixed):

- ❌ Patient Profiles (trying to use `patient_conversation_profile` view)
- ❌ Individual Patient Details
- ❌ Debug endpoints

## Data Sources

The analytics module pulls data from:

1. **patient_reengagement_master** view - Main data source for working endpoints
2. **patient_conversation_profile** view - Intended data source (not implemented)
3. **patients** table - Fallback data source

## Insights Generated

The module automatically generates insights on:

### Risk Analysis
- High-risk patient percentage
- Dormant patient rate
- Engagement distribution
- Priority breakdowns

### Performance Metrics
- Contact success rates
- Engagement rates
- Financial risk assessment
- Attendance patterns

### Recommendations
- Prioritized action items
- Risk mitigation strategies
- Engagement optimization
- Resource allocation

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Ensure API server is running
   - Check base URL is correct
   - Verify network connectivity

2. **Authentication Issues**
   - API endpoints should not require authentication
   - Check if organization ID exists

3. **Data Issues**
   - Ensure database views exist
   - Check data freshness
   - Verify organization has patient data

### Debug Mode

Run with verbose logging:

```bash
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from analytics.reengagement_analytics import *
# Your code here
"
```

## Development

### Adding New Endpoints

To add new endpoints to the analytics:

1. Add endpoint to `collect_data()` method
2. Create analysis method for the new data
3. Update insights generation
4. Add to test script

### Custom Analytics

You can extend the analytics by:

1. Subclassing `ReengagementAnalytics`
2. Adding custom analysis methods
3. Implementing custom report formats

## Next Steps

1. **Fix Broken Endpoints**: Update reengagement.py to properly use `patient_conversation_profile` view
2. **Add More Metrics**: Implement additional performance indicators
3. **Visualization**: Add charts and graphs to reports
4. **Real-time**: Implement streaming analytics
5. **Alerts**: Add threshold-based alerting system

## Contact

For questions or issues with the analytics module, please refer to the main project documentation or contact the development team. 