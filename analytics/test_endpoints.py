#!/usr/bin/env python3
"""
Simple endpoint testing script for reengagement API
"""

import asyncio
import aiohttp
import json
import argparse
from datetime import datetime

async def test_endpoint(session, url, name):
    """Test a single endpoint"""
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ {name}: SUCCESS")
                return True, data
            else:
                print(f"❌ {name}: FAILED (HTTP {response.status})")
                return False, None
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False, None

async def test_reengagement_endpoints(base_url, organization_id):
    """Test all reengagement endpoints"""
    
    print("🔍 Testing Reengagement API Endpoints")
    print("=" * 50)
    
    endpoints = [
        ("/api/v1/reengagement/health", "Health Check"),
        (f"/api/v1/reengagement/{organization_id}/risk-metrics", "Risk Metrics"),
        (f"/api/v1/reengagement/{organization_id}/prioritized", "Prioritized Patients"),
        (f"/api/v1/reengagement/{organization_id}/dashboard-summary", "Dashboard Summary"),
        (f"/api/v1/reengagement/{organization_id}/performance", "Performance Metrics"),
    ]
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for endpoint, name in endpoints:
            url = f"{base_url}{endpoint}"
            success, data = await test_endpoint(session, url, name)
            results[name] = {
                "success": success,
                "endpoint": endpoint,
                "data_preview": str(data)[:200] + "..." if data else None
            }
    
    print("\n📊 Test Results Summary:")
    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)
    print(f"✅ Successful: {successful}/{total} endpoints")
    
    if successful < total:
        print("\n❌ Failed endpoints:")
        for name, result in results.items():
            if not result["success"]:
                print(f"  - {name}: {result['endpoint']}")
    
    return results

async def main():
    parser = argparse.ArgumentParser(description="Test reengagement API endpoints")
    parser.add_argument("--organization-id", required=True, help="Organization ID to test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API")
    
    args = parser.parse_args()
    
    results = await test_reengagement_endpoints(args.base_url, args.organization_id)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analytics/endpoint_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main()) 