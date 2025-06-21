#!/usr/bin/env python3
"""
Check Sync Configuration - Why sync_logs is empty
"""

import os
import sys
from pathlib import Path

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def check_sync_configuration():
    """Check why sync_logs is empty"""
    print("🔍 Checking Sync Configuration")
    print("=" * 50)
    
    try:
        # 1. Check organizations
        print("1️⃣ Organizations:")
        orgs = db.execute_query("SELECT id, name, created_at FROM organizations ORDER BY created_at DESC")
        for org in orgs:
            print(f"   • {org['name']} ({org['id']})")
        
        # 2. Check organization_services table
        print(f"\n2️⃣ Organization Services:")
        services = db.execute_query("""
            SELECT os.*, o.name as org_name 
            FROM organization_services os
            JOIN organizations o ON o.id = os.organization_id
            ORDER BY os.created_at DESC
        """)
        
        if not services:
            print("   ❌ No services configured in organization_services table")
            print("   💡 This explains why sync_logs is empty!")
        else:
            for service in services:
                print(f"   • {service['org_name']}: {service['service_name']}")
                print(f"     - Active: {service['is_active']}")
                print(f"     - Sync Enabled: {service['sync_enabled']}")
                print(f"     - Last Sync: {service.get('last_sync_at', 'Never')}")
        
        # 3. Check for Cliniko services specifically
        print(f"\n3️⃣ Cliniko Services:")
        cliniko_services = db.execute_query("""
            SELECT os.*, o.name as org_name 
            FROM organization_services os
            JOIN organizations o ON o.id = os.organization_id
            WHERE os.service_name = 'cliniko'
        """)
        
        if not cliniko_services:
            print("   ❌ No Cliniko services configured")
            print("   💡 Sync cannot run without Cliniko service configuration")
        else:
            for service in cliniko_services:
                print(f"   • {service['org_name']}: Cliniko configured")
                print(f"     - Active: {service['is_active']}")
                print(f"     - Sync Enabled: {service['sync_enabled']}")
        
        # 4. Check api_credentials table
        print(f"\n4️⃣ API Credentials:")
        creds = db.execute_query("""
            SELECT service_name, organization_id, created_at 
            FROM api_credentials 
            ORDER BY created_at DESC
        """)
        
        if not creds:
            print("   ❌ No API credentials stored")
            print("   💡 Sync cannot run without Cliniko API credentials")
        else:
            for cred in creds:
                print(f"   • {cred['service_name']}: {cred['organization_id']}")
        
        # 5. Check sync_logs (should be empty)
        print(f"\n5️⃣ Sync Logs:")
        logs = db.execute_query("SELECT COUNT(*) as count FROM sync_logs")
        log_count = logs[0]['count'] if logs else 0
        print(f"   📊 Total sync logs: {log_count}")
        
        if log_count == 0:
            print("   ❌ No sync logs found")
            print("   💡 This confirms sync operations are not running or failing silently")
        
        # 6. Summary and recommendations
        print(f"\n📋 DIAGNOSIS:")
        if not services:
            print("   🔴 ROOT CAUSE: No organization services configured")
            print("   💡 SOLUTION: Need to set up Cliniko service for organizations")
        elif not cliniko_services:
            print("   🔴 ROOT CAUSE: No Cliniko services configured")
            print("   💡 SOLUTION: Need to add Cliniko service configuration")
        elif not creds:
            print("   🔴 ROOT CAUSE: No API credentials stored")
            print("   💡 SOLUTION: Need to add Cliniko API credentials")
        else:
            print("   🟡 PARTIAL SETUP: Services configured but sync may be failing")
            print("   💡 SOLUTION: Database connection fix should resolve sync issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking sync configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_sync_configuration()
    sys.exit(0 if success else 1) 