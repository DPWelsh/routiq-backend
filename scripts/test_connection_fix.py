#!/usr/bin/env python3
"""
Test Database Connection Fix for Sync Services
Tests that db.connection.commit() pattern now works
"""

import os
import sys
from pathlib import Path

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Now import the database module
from database import db

def test_connection_fix():
    """Test that the database connection fix works for sync services"""
    print("🔧 Testing Database Connection Fix for Sync Services")
    print("=" * 60)
    
    try:
        print("🔍 Testing db.connection property...")
        
        # This should work now (was failing before)
        connection = db.connection
        print("✅ db.connection property accessible")
        
        print("🔍 Testing db.connection.commit()...")
        
        # This was the exact error: 'SupabaseClient' object has no attribute 'connection'
        connection.commit()
        print("✅ db.connection.commit() works!")
        
        print("🔍 Testing db.connection.rollback()...")
        connection.rollback()
        print("✅ db.connection.rollback() works!")
        
        print("🔍 Testing mixed pattern (context manager + direct connection)...")
        
        # Test the mixed pattern that sync services use
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"   Context manager query result: {result}")
        
        # Then use direct connection (this was failing)
        db.connection.commit()
        print("✅ Mixed pattern works!")
        
        print("🔍 Testing backward compatibility methods...")
        
        # Test connect() method
        success = db.connect()
        print(f"✅ db.connect() returns: {success}")
        
        # Test disconnect() method  
        db.disconnect()
        print("✅ db.disconnect() works")
        
        print("\n🎉 ALL DATABASE CONNECTION FIXES WORKING!")
        print("✅ Sync services should now work without 'connection' attribute errors")
        print("✅ Ready to test actual sync operations")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection fix test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection_fix()
    sys.exit(0 if success else 1) 