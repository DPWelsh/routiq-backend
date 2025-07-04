#!/bin/bash

# Production API Testing Script
# Tests all reengagement endpoints at https://routiq-backend-prod.up.railway.app

BASE_URL="https://routiq-backend-prod.up.railway.app"
ORG_ID="org_2pVpOw4HIXbG6Yzz8YkFW1dDLrH"

echo "🚀 TESTING PRODUCTION REENGAGEMENT API"
echo "================================================"
echo "Base URL: $BASE_URL"
echo "Organization ID: $ORG_ID"
echo ""

# Test basic health endpoints
echo "📋 HEALTH CHECK ENDPOINTS"
echo "----------------------------------------"

echo "1. Testing Reengagement Health..."
curl -s -w "Status: %{http_code} | Time: %{time_total}s\n" \
  "$BASE_URL/api/v1/reengagement/test" | jq -r '.status // "ERROR"' | head -1

echo "2. Testing Database Connection..."
curl -s -w "Status: %{http_code} | Time: %{time_total}s\n" \
  "$BASE_URL/api/v1/reengagement/test-db" | jq -r '.status // "ERROR"' | head -1

echo "3. Testing No Dependencies..."
curl -s -w "Status: %{http_code} | Time: %{time_total}s\n" \
  "$BASE_URL/api/v1/reengagement/test-no-depends" | jq -r '.status // "ERROR"' | head -1

echo ""

# Test main analytics endpoints
echo "📊 ANALYTICS ENDPOINTS"
echo "----------------------------------------"

echo "4. Testing Risk Metrics..."
RESPONSE=$(curl -s "$BASE_URL/api/v1/reengagement/$ORG_ID/risk-metrics")
PATIENTS=$(echo "$RESPONSE" | jq -r '.summary.total_patients // "ERROR"')
echo "   Total Patients: $PATIENTS"

echo "5. Testing Prioritized Patients..."
RESPONSE=$(curl -s "$BASE_URL/api/v1/reengagement/$ORG_ID/prioritized")
COUNT=$(echo "$RESPONSE" | jq -r '.prioritized_patients | length // "ERROR"')
echo "   Prioritized Count: $COUNT"

echo "6. Testing Dashboard Summary..."
RESPONSE=$(curl -s "$BASE_URL/api/v1/reengagement/$ORG_ID/dashboard-summary")
TOTAL=$(echo "$RESPONSE" | jq -r '.summary_metrics.total_patients // "ERROR"')
echo "   Dashboard Total: $TOTAL"

echo "7. Testing Performance Metrics..."
RESPONSE=$(curl -s "$BASE_URL/api/v1/reengagement/$ORG_ID/performance")
ENGAGEMENT=$(echo "$RESPONSE" | jq -r '.performance_metrics.engagement_health.engagement_rate_percent // "ERROR"')
echo "   Engagement Rate: $ENGAGEMENT%"

echo ""

# Test patient profile endpoints (expected to fail)
echo "🔍 PATIENT PROFILE ENDPOINTS (Expected to fail)"
echo "----------------------------------------"

echo "8. Testing Patient Profiles..."
STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/reengagement/$ORG_ID/patient-profiles")
echo "   HTTP Status: $STATUS"

echo "9. Testing Patient Profiles Debug..."
STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/reengagement/$ORG_ID/patient-profiles/debug")
echo "   HTTP Status: $STATUS"

echo "10. Testing Patient Profiles Summary..."
STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/reengagement/$ORG_ID/patient-profiles/summary")
echo "   HTTP Status: $STATUS"

echo ""
echo "✅ TESTING COMPLETE"
echo "See analytics/PRODUCTION_API_ANALYTICS_REPORT.md for detailed results" 