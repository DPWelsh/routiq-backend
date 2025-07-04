#!/usr/bin/env python3
"""
Deploy Patient Conversation Profile View to Production Database
"""
import os
import sys
import psycopg2
from psycopg2 import sql

def get_database_url():
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    return database_url

def read_sql_file(filename):
    """Read SQL file content"""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ SQL file not found: {filename}")
        sys.exit(1)

def deploy_view():
    """Deploy the patient conversation profile view"""
    print("🚀 Deploying Patient Conversation Profile View...")
    
    # Get database connection
    database_url = get_database_url()
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Read SQL view definition
        sql_content = read_sql_file('sql/patient_conversation_profile_view.sql')
        
        # Execute SQL
        print("📊 Creating patient_conversation_profile view...")
        cursor.execute(sql_content)
        
        # Commit changes
        conn.commit()
        print("✅ View created successfully!")
        
        # Test the view
        print("🧪 Testing view...")
        cursor.execute("SELECT COUNT(*) FROM patient_conversation_profile LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ View is working! Ready to serve data.")
        else:
            print("⚠️  View created but no data found")
            
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    deploy_view() 