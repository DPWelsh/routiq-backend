#!/usr/bin/env python3
"""
Fix Stale Sync Operation
Clean up the sync that's been stuck in "running" state for 24+ minutes
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Set the database URL
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def fix_stale_syncs():
    """Fix the stale sync operations"""
    print("🔧 Fixing Stale Sync Operations")
    print("=" * 50)
    
    # The two stale sync IDs from the dashboard
    stale_sync_ids = [
        "7cab64c9-63fc-45d7-aadc-a4cb091f5cb6",
        "fada42b6-19e9-4f24-b55d-cd6784ec7932"
    ]
    
    try:
        with db.get_cursor() as cursor:
            for sync_id in stale_sync_ids:
                print(f"\n🔄 Processing stale sync: {sync_id}")
                
                # Check current status
                cursor.execute("""
                    SELECT status, started_at, operation_type
                    FROM sync_logs 
                    WHERE id = %s
                """, (sync_id,))
                
                current_record = cursor.fetchone()
                if current_record:
                    print(f"📋 Current status: {current_record['status']}")
                    print(f"📅 Started at: {current_record['started_at']}")
                    print(f"🔧 Operation: {current_record['operation_type']}")
                    
                    # Update the sync to failed status
                    cursor.execute("""
                        UPDATE sync_logs 
                        SET status = 'failed',
                            completed_at = %s
                        WHERE id = %s
                    """, (
                        datetime.now(timezone.utc),
                        sync_id
                    ))
                    
                    print(f"✅ Updated sync {sync_id} to 'failed' status")
                else:
                    print(f"❌ Sync {sync_id} not found")
            
            print(f"\n🎉 Cleanup complete!")
            print(f"📊 Updated {len(stale_sync_ids)} stale sync records")
            
    except Exception as e:
        print(f"❌ Error fixing stale syncs: {e}")

if __name__ == "__main__":
    fix_stale_syncs() 