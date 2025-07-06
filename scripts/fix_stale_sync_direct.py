#!/usr/bin/env python3
"""
Direct Database Fix for Stale Sync
Connect directly to the database and fix the stuck sync
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def fix_stale_sync():
    """Fix the specific stale sync that's stuck"""
    stale_sync_id = "f5cce669-a656-4a26-b756-8199d4a99be6"
    
    print("🔧 Fixing Stale Sync in Database")
    print("=" * 50)
    print(f"Target Sync ID: {stale_sync_id}")
    
    try:
        with db.get_cursor() as cursor:
            # First, check current status
            cursor.execute("""
                SELECT id, status, started_at, completed_at, operation_type, organization_id
                FROM sync_logs 
                WHERE id = %s
            """, (stale_sync_id,))
            
            current_record = cursor.fetchone()
            
            if not current_record:
                print(f"❌ Sync {stale_sync_id} not found in database")
                return False
            
            print(f"📋 Current Status: {current_record['status']}")
            print(f"📅 Started: {current_record['started_at']}")
            print(f"🏢 Organization: {current_record['organization_id']}")
            print(f"🔧 Operation: {current_record['operation_type']}")
            
            if current_record['status'] != 'running':
                print(f"ℹ️  Sync is already in '{current_record['status']}' status - no cleanup needed")
                return False
            
            # Calculate how long it's been running
            started_at = current_record['started_at']
            if started_at:
                elapsed = datetime.now(timezone.utc) - started_at.replace(tzinfo=timezone.utc)
                minutes_running = elapsed.total_seconds() / 60
                print(f"⏰ Running for: {minutes_running:.1f} minutes")
            
            # Update the sync to failed status
            print("\n🔄 Updating sync status to 'failed'...")
            
            cursor.execute("""
                UPDATE sync_logs 
                SET status = %s,
                    completed_at = %s,
                    error_details = %s,
                    metadata = %s
                WHERE id = %s
            """, (
                'failed',
                datetime.now(timezone.utc),
                json.dumps({"error": "Sync cleaned up due to stale status (stuck in running)", "cleanup_reason": "manual_cleanup"}),
                json.dumps({
                    "cleanup_reason": "stale_sync_cleanup",
                    "original_status": "running", 
                    "cleanup_time": datetime.now(timezone.utc).isoformat(),
                    "minutes_running": minutes_running if started_at else 0
                }),
                stale_sync_id
            ))
            
            # Commit the changes
            db.connection.commit()
            
            print("✅ Sync status updated successfully!")
            
            # Verify the update
            cursor.execute("""
                SELECT id, status, started_at, completed_at, operation_type
                FROM sync_logs 
                WHERE id = %s
            """, (stale_sync_id,))
            
            updated_record = cursor.fetchone()
            print(f"\n📊 Updated Status: {updated_record['status']}")
            print(f"📅 Completed: {updated_record['completed_at']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error fixing stale sync: {e}")
        return False

if __name__ == "__main__":
    success = fix_stale_sync()
    if success:
        print("\n🎉 Stale sync cleanup completed successfully!")
    else:
        print("\n❌ Stale sync cleanup failed or was not needed") 