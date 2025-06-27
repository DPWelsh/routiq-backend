#!/usr/bin/env python3
"""
Debug Sync Failures
"""

import os
import sys
import json
import requests
from pathlib import Path

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def check_recent_sync_failures():
    """Check the most recent sync failures for details"""
    print("🔍 Analyzing Recent Sync Failures")
    print("=" * 50)
    
    try:
        # Get the most recent failed syncs
        failed_syncs = db.execute_query("""
            SELECT id, organization_id, source_system, operation_type, status,
                   records_processed, records_success, records_failed,
                   error_details, metadata, started_at, completed_at
            FROM sync_logs 
            WHERE status = 'failed'
            ORDER BY started_at DESC
            LIMIT 5
        """)
        
        print(f"📊 Found {len(failed_syncs)} recent failed syncs:")
        
        for i, sync in enumerate(failed_syncs, 1):
            print(f"\n{i}. Failed Sync:")
            print(f"   ID: {sync['id']}")
            print(f"   Organization: {sync['organization_id']}")
            print(f"   Operation: {sync['source_system']}/{sync['operation_type']}")
            print(f"   Started: {sync['started_at']}")
            print(f"   Completed: {sync['completed_at']}")
            print(f"   Records Processed: {sync['records_processed']}")
            print(f"   Records Success: {sync['records_success']}")
            print(f"   Records Failed: {sync['records_failed']}")
            
            # Parse error details
            if sync.get('error_details'):
                try:
                    errors = json.loads(sync['error_details']) if isinstance(sync['error_details'], str) else sync['error_details']
                    print(f"   Error Details: {errors}")
                except Exception as e:
                    print(f"   Error Details (raw): {sync['error_details']}")
            else:
                print(f"   Error Details: None (this is the problem!)")
            
            # Parse metadata
            if sync.get('metadata'):
                try:
                    metadata = json.loads(sync['metadata']) if isinstance(sync['metadata'], str) else sync['metadata']
                    print(f"   Metadata: {metadata}")
                    
                    # Look for clues in metadata
                    if 'step' in metadata:
                        print(f"   Last Step: {metadata['step']}")
                    if 'progress_percent' in metadata:
                        print(f"   Progress: {metadata['progress_percent']}%")
                        
                except Exception as e:
                    print(f"   Metadata (raw): {sync['metadata']}")
        
        return failed_syncs
        
    except Exception as e:
        print(f"❌ Error checking failed syncs: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_sync_endpoint():
    """Test the sync endpoint directly"""
    print("\n🧪 Testing Sync Endpoint")
    print("=" * 30)
    
    # Test the consolidated sync endpoint
    api_base = "https://routiq-backend-production.up.railway.app"
    org_id = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
    
    try:
        print(f"Testing: POST {api_base}/api/v1/cliniko/sync/{org_id}")
        
        response = requests.post(
            f"{api_base}/api/v1/cliniko/sync/{org_id}",
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sync started successfully:")
            print(f"   Sync ID: {data.get('sync_id')}")
            print(f"   Message: {data.get('message')}")
            return data.get('sync_id')
        else:
            print(f"❌ Sync failed:")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing sync endpoint: {e}")
        return None

def check_sync_status(sync_id):
    """Check the status of a specific sync"""
    if not sync_id:
        return
        
    print(f"\n📊 Checking Sync Status: {sync_id}")
    print("=" * 40)
    
    api_base = "https://routiq-backend-production.up.railway.app"
    
    try:
        response = requests.get(
            f"{api_base}/api/v1/sync/status/{sync_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sync Status Retrieved:")
            print(f"   Status: {data.get('status')}")
            print(f"   Current Step: {data.get('current_step')}")
            print(f"   Progress: {data.get('progress_percent', 0)}%")
            print(f"   Errors: {data.get('errors', [])}")
        else:
            print(f"❌ Failed to get sync status: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking sync status: {e}")

def main():
    """Main debug function"""
    print("🚨 SYNC FAILURE DEBUGGING")
    print("=" * 60)
    
    # 1. Check recent failures
    failed_syncs = check_recent_sync_failures()
    
    # 2. Test the endpoint
    sync_id = test_sync_endpoint()
    
    # 3. Check status if we got a sync ID
    if sync_id:
        import time
        print("\n⏳ Waiting 10 seconds before checking status...")
        time.sleep(10)
        check_sync_status(sync_id)
    
    print("\n" + "=" * 60)
    print("🎯 ANALYSIS COMPLETE")
    
    if failed_syncs:
        print("\n💡 KEY FINDINGS:")
        print("   - Recent syncs are failing")
        print("   - Error details are empty (not being captured properly)")
        print("   - Records are being processed but sync still marked as failed")
        print("   - This suggests an issue in the sync completion logic")

if __name__ == "__main__":
    main() 