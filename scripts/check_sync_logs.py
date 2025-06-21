#!/usr/bin/env python3
"""
Check Sync Logs Details
"""

import os
import sys
import json
from pathlib import Path

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def check_sync_logs():
    """Check sync logs details"""
    print("🔍 Checking Sync Logs Details")
    print("=" * 50)
    
    try:
        # Get all sync logs
        logs = db.execute_query("""
            SELECT id, organization_id, sync_type, status, 
                   started_at, completed_at, results, error_details,
                   source_system, operation_type, records_processed,
                   records_success, records_failed
            FROM sync_logs 
            ORDER BY started_at DESC
        """)
        
        print(f"📊 Found {len(logs)} sync logs:")
        
        for i, log in enumerate(logs, 1):
            print(f"\n{i}. Sync Log:")
            print(f"   ID: {log['id']}")
            print(f"   Organization: {log['organization_id']}")
            print(f"   Type: {log.get('sync_type', 'N/A')}")
            print(f"   Source System: {log.get('source_system', 'N/A')}")
            print(f"   Operation: {log.get('operation_type', 'N/A')}")
            print(f"   Status: {log['status']}")
            print(f"   Started: {log['started_at']}")
            print(f"   Completed: {log['completed_at']}")
            
            # Records processed
            if log.get('records_processed'):
                print(f"   Records Processed: {log['records_processed']}")
                print(f"   Records Success: {log.get('records_success', 'N/A')}")
                print(f"   Records Failed: {log.get('records_failed', 'N/A')}")
            
            # Parse results if available
            if log.get('results'):
                try:
                    results = json.loads(log['results']) if isinstance(log['results'], str) else log['results']
                    print(f"   Results: {results}")
                except Exception as e:
                    print(f"   Results (raw): {log['results']}")
            
            if log.get('error_details'):
                print(f"   Errors: {log['error_details']}")
        
        # Summary analysis
        if logs:
            print(f"\n📋 SYNC LOGS ANALYSIS:")
            
            latest = logs[0]
            print(f"   🕐 Most Recent Sync: {latest['started_at']}")
            print(f"   📊 Status: {latest['status']}")
            print(f"   🏢 Organization: {latest['organization_id']}")
            
            # Count by status
            statuses = {}
            for log in logs:
                status = log['status']
                statuses[status] = statuses.get(status, 0) + 1
            
            print(f"   📈 Status Summary:")
            for status, count in statuses.items():
                print(f"     - {status}: {count}")
            
            # Check for recent successful syncs
            successful_syncs = [log for log in logs if log['status'] in ['completed', 'success']]
            failed_syncs = [log for log in logs if log['status'] in ['failed', 'error']]
            
            print(f"   ✅ Successful syncs: {len(successful_syncs)}")
            print(f"   ❌ Failed syncs: {len(failed_syncs)}")
            
            if successful_syncs:
                print(f"   🕐 Last successful sync: {successful_syncs[0]['started_at']}")
            
            if failed_syncs:
                print(f"   🕐 Last failed sync: {failed_syncs[0]['started_at']}")
                if failed_syncs[0].get('error_details'):
                    print(f"   ❌ Last error: {failed_syncs[0]['error_details']}")
        
        else:
            print("   ❌ No sync logs found")
            print("   💡 This means sync operations have never run or are not being logged")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking sync logs: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_sync_logs()
    sys.exit(0 if success else 1) 