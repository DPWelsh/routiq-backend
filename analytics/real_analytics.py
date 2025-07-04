#!/usr/bin/env python3
"""
Real Reengagement Analytics using Production API
===============================================

This script uses the live production API at:
https://routiq-backend-prod.up.railway.app/docs
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Production API configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2pVpOw4HIXbG6Yzz8YkFW1dDLrH"  # Replace with actual org ID

async def test_endpoint(session, endpoint_url, name):
    """Test a single endpoint"""
    try:
        print(f"Testing {name}...")
        async with session.get(endpoint_url, timeout=30) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ {name}: SUCCESS")
                return True, data
            else:
                text = await response.text()
                print(f"❌ {name}: FAILED (HTTP {response.status})")
                print(f"   Response: {text[:200]}...")
                return False, None
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False, None

async def run_production_analytics():
    """Run analytics against the production API"""
    
    print("🚀 PRODUCTION REENGAGEMENT ANALYTICS")
    print("=" * 60)
    print(f"API Base URL: {BASE_URL}")
    print(f"Organization ID: {ORG_ID}")
    print()
    
    # Define the endpoints we want to test
    endpoints = [
        # Basic health checks
        (f"{BASE_URL}/api/v1/reengagement/test", "Reengagement Test"),
        (f"{BASE_URL}/api/v1/reengagement/test-db", "Database Test"),
        (f"{BASE_URL}/api/v1/reengagement/test-no-depends", "No Depends Test"),
        
        # Main analytics endpoints
        (f"{BASE_URL}/api/v1/reengagement/{ORG_ID}/risk-metrics", "Risk Metrics"),
        (f"{BASE_URL}/api/v1/reengagement/{ORG_ID}/prioritized", "Prioritized Patients"),
        (f"{BASE_URL}/api/v1/reengagement/{ORG_ID}/dashboard-summary", "Dashboard Summary"),
        (f"{BASE_URL}/api/v1/reengagement/{ORG_ID}/performance", "Performance Metrics"),
        
        # Patient profile endpoints  
        (f"{BASE_URL}/api/v1/reengagement/{ORG_ID}/patient-profiles", "Patient Profiles"),
        (f"{BASE_URL}/api/v1/reengagement/{ORG_ID}/patient-profiles/debug", "Patient Profiles Debug"),
        (f"{BASE_URL}/api/v1/reengagement/{ORG_ID}/patient-profiles/summary", "Patient Profiles Summary"),
    ]
    
    results = {}
    successful_data = {}
    
    async with aiohttp.ClientSession() as session:
        for endpoint_url, name in endpoints:
            success, data = await test_endpoint(session, endpoint_url, name)
            results[name] = success
            if success and data:
                successful_data[name] = data
    
    # Summary
    print("\n📊 RESULTS SUMMARY:")
    print("=" * 40)
    successful = sum(results.values())
    total = len(results)
    print(f"✅ Successful: {successful}/{total} endpoints")
    
    if successful > 0:
        print("\n🎉 Working Endpoints:")
        for name, success in results.items():
            if success:
                print(f"  ✅ {name}")
    
    if successful < total:
        print("\n❌ Failed Endpoints:")
        for name, success in results.items():
            if not success:
                print(f"  ❌ {name}")
    
    # Generate analytics from successful endpoints
    if successful_data:
        print("\n📈 ANALYTICS INSIGHTS:")
        print("=" * 40)
        
        # Risk metrics analysis
        if "Risk Metrics" in successful_data:
            risk_data = successful_data["Risk Metrics"]
            if "summary" in risk_data:
                summary = risk_data["summary"]
                total_patients = summary.get("total_patients", 0)
                
                print(f"📊 Patient Overview:")
                print(f"  • Total Patients: {total_patients:,}")
                
                if "risk_distribution" in summary:
                    risk_dist = summary["risk_distribution"]
                    print(f"  • High Risk: {risk_dist.get('high', 0)} ({risk_dist.get('high', 0)/total_patients*100:.1f}%)")
                    print(f"  • Medium Risk: {risk_dist.get('medium', 0)} ({risk_dist.get('medium', 0)/total_patients*100:.1f}%)")
                    print(f"  • Low Risk: {risk_dist.get('low', 0)} ({risk_dist.get('low', 0)/total_patients*100:.1f}%)")
                
                if "engagement_distribution" in summary:
                    eng_dist = summary["engagement_distribution"]
                    print(f"  • Active: {eng_dist.get('active', 0)} ({eng_dist.get('active', 0)/total_patients*100:.1f}%)")
                    print(f"  • Dormant: {eng_dist.get('dormant', 0)} ({eng_dist.get('dormant', 0)/total_patients*100:.1f}%)")
                    print(f"  • Stale: {eng_dist.get('stale', 0)} ({eng_dist.get('stale', 0)/total_patients*100:.1f}%)")
                
                if "action_priorities" in summary:
                    priorities = summary["action_priorities"]
                    print(f"  • Urgent Actions: {priorities.get('urgent', 0)}")
                    print(f"  • Important Actions: {priorities.get('important', 0)}")
        
        # Dashboard summary analysis
        if "Dashboard Summary" in successful_data:
            dashboard_data = successful_data["Dashboard Summary"]
            if "summary_metrics" in dashboard_data:
                metrics = dashboard_data["summary_metrics"]
                
                if "financial_metrics" in metrics:
                    financial = metrics["financial_metrics"]
                    total_value = financial.get("total_lifetime_value_aud", 0)
                    avg_value = financial.get("avg_lifetime_value_aud", 0)
                    
                    print(f"\n💰 Financial Metrics:")
                    print(f"  • Total Lifetime Value: ${total_value:,.2f} AUD")
                    print(f"  • Average Patient Value: ${avg_value:,.2f} AUD")
        
        # Performance metrics analysis
        if "Performance Metrics" in successful_data:
            perf_data = successful_data["Performance Metrics"]
            if "performance_metrics" in perf_data:
                perf_metrics = perf_data["performance_metrics"]
                
                if "engagement_health" in perf_metrics:
                    engagement = perf_metrics["engagement_health"]
                    engagement_rate = engagement.get("engagement_rate_percent", 0)
                    print(f"\n📊 Performance Metrics:")
                    print(f"  • Engagement Rate: {engagement_rate:.1f}%")
                
                if "contact_metrics" in perf_metrics:
                    contact = perf_metrics["contact_metrics"]
                    contact_rate = contact.get("contact_rate_percent", 0)
                    avg_days_since = contact.get("avg_days_since_contact", 0)
                    print(f"  • Contact Success Rate: {contact_rate:.1f}%")
                    print(f"  • Avg Days Since Contact: {avg_days_since:.1f}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"analytics/production_analytics_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "base_url": BASE_URL,
                "organization_id": ORG_ID,
                "endpoint_results": results,
                "analytics_data": successful_data,
                "summary": {
                    "total_endpoints_tested": total,
                    "successful_endpoints": successful,
                    "success_rate": f"{successful/total*100:.1f}%"
                }
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_file}")
    
    return results, successful_data

if __name__ == "__main__":
    print("Starting production API analytics...")
    asyncio.run(run_production_analytics()) 