#!/usr/bin/env python3
"""
Simple Database Connection Test for RoutIQ Backend
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

def test_connection():
    """Test basic database connection"""
    print("🚀 Testing RoutIQ Backend Database Connection")
    print("=" * 50)
    
    try:
        print("🔌 Connecting to database...")
        success = db.connect()
        
        if not success:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connection successful!")
        
        # Test health check
        print("🔍 Running health check...")
        health = db.health_check()
        
        if not health:
            print("❌ Database health check failed")
            return False
        
        print("✅ Database health check passed!")
        
        # Test basic query
        print("📊 Testing basic queries...")
        
        # Get table count
        tables = db.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   • {table['table_name']}")
        
        # Test data counts
        print("\n📊 Data Summary:")
        
        # Organizations
        try:
            orgs = db.execute_query("SELECT COUNT(*) as count FROM organizations")
            print(f"   Organizations: {orgs[0]['count']}")
        except Exception as e:
            print(f"   Organizations: Error - {e}")
        
        # Contacts
        try:
            contacts = db.execute_query("SELECT COUNT(*) as count FROM contacts")
            print(f"   Contacts: {contacts[0]['count']}")
        except Exception as e:
            print(f"   Contacts: Error - {e}")
        
        # Conversations
        try:
            conversations = db.execute_query("SELECT COUNT(*) as count FROM conversations")
            print(f"   Conversations: {conversations[0]['count']}")
        except Exception as e:
            print(f"   Conversations: Error - {e}")
        
        # Active patients
        try:
            patients = db.execute_query("SELECT COUNT(*) as count FROM active_patients")
            print(f"   Active Patients: {patients[0]['count']}")
        except Exception as e:
            print(f"   Active Patients: Error - {e}")
        
        print("\n🎉 Database connection test successful!")
        print("✅ Ready to proceed with database optimizations!")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    finally:
        # Cleanup
        if hasattr(db, 'disconnect'):
            db.disconnect()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 