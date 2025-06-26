#!/usr/bin/env python3
"""
Backend API Analysis Report Generator
Analyzes test results and creates comprehensive reports
"""

import json
from datetime import datetime

def analyze_test_results(filename):
    """Analyze the test results and create a comprehensive report"""
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    print("🔍 BACKEND API ANALYSIS REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Session: {data['test_session']['timestamp']}")
    print(f"Success Rate: {data['test_session']['success_rate']}")
    print()
    
    # Analyze working endpoints
    print("✅ WORKING ENDPOINTS ANALYSIS:")
    print("-" * 40)
    
    for result in data['detailed_results']:
        if result['success']:
            print(f"\n🟢 {result['endpoint_name']}")
            print(f"   URL: {result['url']}")
            print(f"   Response Time: {result['response_time_ms']}ms")
            
            # Extract key data from each endpoint
            response_data = result.get('response_data', {})
            
            if result['endpoint_name'] == "Cliniko Connection Test":
                print(f"   📊 Data: {response_data.get('total_patients_available', 'N/A')} total patients")
                print(f"   📊 Practitioners: {response_data.get('practitioners_count', 'N/A')}")
                print(f"   📊 Status: {response_data.get('message', 'N/A')}")
                
            elif result['endpoint_name'] == "Active Patients Summary":
                print(f"   📊 Active Patients: {response_data.get('total_active_patients', 'N/A')}")
                print(f"   📊 Avg Recent Appointments: {response_data.get('avg_recent_appointments', 'N/A')}")
                print(f"   📊 Avg Upcoming Appointments: {response_data.get('avg_upcoming_appointments', 'N/A')}")
                
            elif result['endpoint_name'] == "Organization Services":
                services = response_data.get('services', [])
                print(f"   📊 Services Count: {len(services)}")
                if services:
                    for service in services[:3]:  # Show first 3
                        print(f"   📊 Service: {service.get('name', 'Unknown')}")
                        
            elif result['endpoint_name'] == "Sync History/Logs":
                logs = response_data.get('recent_syncs', [])
                stats = response_data.get('organization_id', 'N/A')
                print(f"   📊 Organization: {stats}")
                print(f"   📊 Recent Syncs: {len(logs)} entries")
                
            elif result['endpoint_name'] == "Cliniko Status":
                print(f"   📊 Total Patients: {response_data.get('total_patients', 'N/A')}")
                print(f"   📊 Active Patients: {response_data.get('active_patients', 'N/A')}")
                print(f"   📊 Synced Patients: {response_data.get('synced_patients', 'N/A')}")
                print(f"   📊 Sync %: {response_data.get('sync_percentage', 'N/A')}%")
                
            elif "Sync" in result['endpoint_name'] and "Start" in result['endpoint_name']:
                print(f"   📊 Sync Started: {response_data.get('success', 'N/A')}")
                print(f"   📊 Message: {response_data.get('message', 'N/A')}")
    
    # Analyze broken endpoints
    print("\n\n❌ BROKEN/MISSING ENDPOINTS ANALYSIS:")
    print("-" * 40)
    
    for result in data['detailed_results']:
        if not result['success']:
            print(f"\n🔴 {result['endpoint_name']}")
            print(f"   URL: {result['url']}")
            print(f"   Status: {result.get('status_code', 'ERROR')}")
            print(f"   Error: {result.get('error', 'Unknown error')[:100]}")
    
    # Key insights
    print("\n\n🎯 KEY INSIGHTS:")
    print("-" * 20)
    
    # Find total patients from different endpoints
    patients_data = {}
    for result in data['detailed_results']:
        if result['success']:
            response_data = result.get('response_data', {})
            if 'total_patients_available' in response_data:
                patients_data['connection_test'] = response_data['total_patients_available']
            if 'total_active_patients' in response_data:
                patients_data['active_summary'] = response_data['total_active_patients'] 
            if 'total_patients' in response_data:
                patients_data['status'] = response_data['total_patients']
    
    print(f"📊 Patient Data Consistency:")
    for source, count in patients_data.items():
        print(f"   {source}: {count} patients")
    
    # Performance analysis
    working_endpoints = [r for r in data['detailed_results'] if r['success']]
    avg_response_time = sum(r['response_time_ms'] for r in working_endpoints) / len(working_endpoints)
    slowest = max(working_endpoints, key=lambda x: x['response_time_ms'])
    fastest = min(working_endpoints, key=lambda x: x['response_time_ms'])
    
    print(f"\n⚡ Performance Analysis:")
    print(f"   Average Response Time: {avg_response_time:.1f}ms")
    print(f"   Slowest Endpoint: {slowest['endpoint_name']} ({slowest['response_time_ms']}ms)")
    print(f"   Fastest Endpoint: {fastest['endpoint_name']} ({fastest['response_time_ms']}ms)")
    
    # Frontend impact assessment
    print(f"\n🎨 Frontend Impact Assessment:")
    critical_endpoints = [
        "Active Patients Summary",
        "Cliniko Connection Test", 
        "Sync Dashboard Data",
        "Organization Services"
    ]
    
    working_critical = [r for r in working_endpoints if r['endpoint_name'] in critical_endpoints]
    print(f"   Critical Endpoints Working: {len(working_critical)}/{len(critical_endpoints)}")
    
    missing_sync_monitoring = [
        "Sync Status by ID (MISSING)",
        "Sync Status Monitoring (MISSING)",
        "Organization Sync Status (MISSING)"
    ]
    
    print(f"   Missing Sync Monitoring: {len(missing_sync_monitoring)} endpoints")
    print(f"   Frontend Can Display: Patient data, basic sync controls")
    print(f"   Frontend Cannot Display: Real-time sync progress, sync status monitoring")

if __name__ == "__main__":
    import sys
    
    # Use the latest test results file
    import glob
    result_files = glob.glob("backend_api_test_results_*.json")
    if result_files:
        latest_file = max(result_files)
        print(f"Using: {latest_file}\n")
        analyze_test_results(latest_file)
    else:
        print("No test results found. Run test_backend_endpoints.py first.") 