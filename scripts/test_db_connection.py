#!/usr/bin/env python3
"""
Database Connection Test for RoutIQ Backend
Tests connection, schema, and basic operations
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment variables"""
    print("🔧 Testing Environment Configuration...")
    
    # Check for database URL
    db_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ Missing database URL environment variable")
        print("   Set SUPABASE_DB_URL or DATABASE_URL")
        return False
    
    # Mask the password in the URL for display
    masked_url = db_url.replace(db_url.split(':')[2].split('@')[0], '***')
    print(f"✅ Database URL found: {masked_url}")
    
    return True

def test_basic_connection():
    """Test basic database connection"""
    print("\n🔌 Testing Basic Database Connection...")
    
    try:
        # Test connection
        success = db.connect()
        if not success:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connection successful")
        
        # Test health check
        health = db.health_check()
        if not health:
            print("❌ Database health check failed")
            return False
        
        print("✅ Database health check passed")
        return True
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_schema_structure():
    """Test that all expected tables exist"""
    print("\n📊 Testing Database Schema...")
    
    expected_tables = [
        'organizations',
        'users', 
        'organization_members',
        'api_credentials',
        'contacts',
        'active_patients',
        'conversations',
        'messages',
        'appointments',
        'sync_logs',
        'audit_logs'
    ]
    
    try:
        # Query to get all tables
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        
        tables = db.execute_query(query)
        table_names = [table['table_name'] for table in tables]
        
        print(f"📋 Found {len(table_names)} tables in database:")
        for table_name in table_names:
            print(f"   • {table_name}")
        
        # Check for expected tables
        missing_tables = []
        for expected_table in expected_tables:
            if expected_table in table_names:
                print(f"✅ {expected_table}")
            else:
                print(f"❌ {expected_table} (missing)")
                missing_tables.append(expected_table)
        
        if missing_tables:
            print(f"\n⚠️  Missing tables: {', '.join(missing_tables)}")
            return False
        
        print("✅ All expected tables found")
        return True
        
    except Exception as e:
        print(f"❌ Schema check error: {e}")
        return False

def test_table_structure():
    """Test specific table structures"""
    print("\n🏗️  Testing Table Structures...")
    
    # Test key tables and their important columns
    table_tests = {
        'contacts': ['id', 'phone', 'email', 'name', 'contact_type', 'organization_id'],
        'organizations': ['id', 'name', 'subscription_status', 'created_at'],
        'active_patients': ['id', 'contact_id', 'organization_id', 'recent_appointment_count'],
        'conversations': ['id', 'contact_id', 'source', 'organization_id'],
        'messages': ['id', 'conversation_id', 'content', 'sender_type'],
        'sync_logs': ['id', 'source_system', 'status', 'started_at']
    }
    
    all_passed = True
    
    for table_name, expected_columns in table_tests.items():
        try:
            # Get column information
            query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """
            
            columns = db.execute_query(query, (table_name,))
            column_names = [col['column_name'] for col in columns]
            
            print(f"\n📋 {table_name} ({len(column_names)} columns):")
            
            missing_columns = []
            for expected_col in expected_columns:
                if expected_col in column_names:
                    # Find the column details
                    col_info = next(col for col in columns if col['column_name'] == expected_col)
                    print(f"   ✅ {expected_col} ({col_info['data_type']})")
                else:
                    print(f"   ❌ {expected_col} (missing)")
                    missing_columns.append(expected_col)
            
            if missing_columns:
                print(f"   ⚠️  Missing columns in {table_name}: {', '.join(missing_columns)}")
                all_passed = False
            
        except Exception as e:
            print(f"❌ Error checking {table_name}: {e}")
            all_passed = False
    
    return all_passed

def test_data_samples():
    """Test basic data operations"""
    print("\n🔍 Testing Data Operations...")
    
    try:
        # Test organizations
        orgs = db.execute_query("SELECT COUNT(*) as count FROM organizations")
        org_count = orgs[0]['count'] if orgs else 0
        print(f"📊 Organizations: {org_count}")
        
        # Test contacts
        contacts = db.execute_query("SELECT COUNT(*) as count FROM contacts")
        contact_count = contacts[0]['count'] if contacts else 0
        print(f"📊 Contacts: {contact_count}")
        
        # Test conversations
        conversations = db.execute_query("SELECT COUNT(*) as count FROM conversations")
        conv_count = conversations[0]['count'] if conversations else 0
        print(f"📊 Conversations: {conv_count}")
        
        # Test sync logs
        sync_logs = db.execute_query("SELECT COUNT(*) as count FROM sync_logs")
        sync_count = sync_logs[0]['count'] if sync_logs else 0
        print(f"📊 Sync Logs: {sync_count}")
        
        print("✅ Basic data queries successful")
        return True
        
    except Exception as e:
        print(f"❌ Data operation error: {e}")
        return False

def test_indexes():
    """Test database indexes"""
    print("\n🗂️  Testing Database Indexes...")
    
    try:
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
        """
        
        indexes = db.execute_query(query)
        
        # Group by table
        table_indexes = {}
        for idx in indexes:
            table = idx['tablename']
            if table not in table_indexes:
                table_indexes[table] = []
            table_indexes[table].append(idx['indexname'])
        
        total_indexes = len(indexes)
        print(f"📋 Found {total_indexes} indexes:")
        
        for table, idx_list in table_indexes.items():
            print(f"   📊 {table}: {len(idx_list)} indexes")
            for idx_name in idx_list:
                print(f"      • {idx_name}")
        
        print("✅ Index information retrieved successfully")
        return True
        
    except Exception as e:
        print(f"❌ Index check error: {e}")
        return False

def test_rls_policies():
    """Test Row Level Security policies"""
    print("\n🔒 Testing Row Level Security...")
    
    try:
        query = """
        SELECT 
            schemaname,
            tablename,
            policyname,
            permissive,
            roles,
            cmd,
            qual
        FROM pg_policies 
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname
        """
        
        policies = db.execute_query(query)
        
        if not policies:
            print("⚠️  No RLS policies found")
            return True
        
        # Group by table
        table_policies = {}
        for policy in policies:
            table = policy['tablename']
            if table not in table_policies:
                table_policies[table] = []
            table_policies[table].append(policy['policyname'])
        
        print(f"📋 Found RLS policies on {len(table_policies)} tables:")
        for table, policy_list in table_policies.items():
            print(f"   🔒 {table}: {len(policy_list)} policies")
            for policy_name in policy_list:
                print(f"      • {policy_name}")
        
        print("✅ RLS policies checked successfully")
        return True
        
    except Exception as e:
        print(f"❌ RLS check error: {e}")
        return False

def run_all_tests():
    """Run all database tests"""
    print("🚀 RoutIQ Backend Database Connection Test")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Basic Connection", test_basic_connection),
        ("Schema Structure", test_schema_structure),
        ("Table Structure", test_table_structure),
        ("Data Operations", test_data_samples),
        ("Database Indexes", test_indexes),
        ("RLS Policies", test_rls_policies),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database is ready for optimization.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    # Set the database URL if not already set
    if not os.getenv('DATABASE_URL') and not os.getenv('SUPABASE_DB_URL'):
        # Use the URL you provided
        os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'
        print("🔧 Using provided database URL")
    
    success = run_all_tests()
    
    # Cleanup
    if hasattr(db, 'disconnect'):
        db.disconnect()
    
    sys.exit(0 if success else 1) 