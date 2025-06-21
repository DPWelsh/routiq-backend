#!/usr/bin/env python3
"""
Check Sync Logs Schema and Data
"""

import os
import sys
from pathlib import Path

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def check_sync_logs_schema():
    """Check sync_logs table schema and data"""
    print("🔍 Checking Sync Logs Schema and Data")
    print("=" * 50)
    
    try:
        # Check schema
        print("1️⃣ sync_logs table schema:")
        schema = db.execute_query("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'sync_logs' 
            ORDER BY ordinal_position
        """)
        
        for col in schema:
            print(f"   • {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Get sample data with basic columns
        print(f"\n2️⃣ Sample sync_logs records:")
        logs = db.execute_query("SELECT * FROM sync_logs ORDER BY started_at DESC LIMIT 3")
        
        for i, log in enumerate(logs, 1):
            print(f"\n{i}. Record:")
            for key, value in log.items():
                # Truncate long values
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {key}: {value}")
        
        # Count total records
        count = db.execute_query("SELECT COUNT(*) as count FROM sync_logs")
        total = count[0]['count'] if count else 0
        print(f"\n📊 Total sync_logs records: {total}")
        
        # Check recent records
        if total > 0:
            recent = db.execute_query("""
                SELECT started_at, completed_at, status, organization_id, source_system, operation_type
                FROM sync_logs 
                ORDER BY started_at DESC 
                LIMIT 5
            """)
            
            print(f"\n🕐 Recent sync operations:")
            for log in recent:
                print(f"   • {log['started_at']}: {log['status']} - {log['source_system']}/{log['operation_type']} ({log['organization_id']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking sync logs: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_sync_logs_schema()
    sys.exit(0 if success else 1) 