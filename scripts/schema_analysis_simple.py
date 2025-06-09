#!/usr/bin/env python3
"""
Comprehensive Database Schema Analysis for RoutIQ Backend
Uses the existing database connection pattern to analyze schema structure.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Now import the database module
from database import db

def analyze_schema():
    """Perform comprehensive schema analysis"""
    print("🔍 RoutIQ Backend - Comprehensive Database Schema Analysis")
    print("=" * 60)
    
    schema_info = {
        'analysis_metadata': {
            'timestamp': datetime.now().isoformat(),
            'analyzer': 'RoutIQ Schema Analyzer v1.0'
        },
        'tables': {},
        'relationships': {},
        'summary': {}
    }
    
    try:
        print("🔌 Connecting to database...")
        success = db.connect()
        
        if not success:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connection successful!")
        
        # Get all tables
        print("\n📊 Analyzing tables...")
        tables = db.execute_query("""
            SELECT 
                t.table_name,
                t.table_type,
                obj_description(c.oid) as table_comment
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name
        """)
        
        print(f"Found {len(tables)} tables:")
        
        # Analyze each table
        for table in tables:
            table_name = table['table_name']
            print(f"  📋 Analyzing {table_name}...")
            
            # Get columns
            columns = db.execute_query("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default,
                    ordinal_position
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            # Get constraints
            constraints = db.execute_query("""
                SELECT 
                    tc.constraint_name,
                    tc.constraint_type,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = 'public' 
                AND tc.table_name = %s
                ORDER BY tc.constraint_type, tc.constraint_name
            """, (table_name,))
            
            # Get foreign keys
            foreign_keys = db.execute_query("""
                SELECT 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc 
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = 'public'
                AND tc.table_name = %s
            """, (table_name,))
            
            # Get indexes
            indexes = db.execute_query("""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public' 
                AND tablename = %s
                ORDER BY indexname
            """, (table_name,))
            
            # Get row count
            try:
                row_count = db.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = row_count[0]['count'] if row_count else 0
            except:
                row_count = 0
            
            # Store table info
            schema_info['tables'][table_name] = {
                'type': table['table_type'],
                'comment': table['table_comment'],
                'row_count': row_count,
                'columns': {col['column_name']: {
                    'type': col['data_type'],
                    'max_length': col['character_maximum_length'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default'],
                    'position': col['ordinal_position']
                } for col in columns},
                'constraints': {},
                'foreign_keys': {fk['column_name']: {
                    'references_table': fk['foreign_table_name'],
                    'references_column': fk['foreign_column_name']
                } for fk in foreign_keys},
                'indexes': {idx['indexname']: idx['indexdef'] for idx in indexes}
            }
            
            # Group constraints by type
            constraints_by_type = {}
            for constraint in constraints:
                constraint_type = constraint['constraint_type']
                if constraint_type not in constraints_by_type:
                    constraints_by_type[constraint_type] = []
                constraints_by_type[constraint_type].append({
                    'name': constraint['constraint_name'],
                    'column': constraint['column_name']
                })
            
            schema_info['tables'][table_name]['constraints'] = constraints_by_type
            
            print(f"    ✅ {len(columns)} columns, {len(foreign_keys)} FKs, {len(indexes)} indexes, {row_count} rows")
        
        # Analyze relationships
        print("\n🔗 Analyzing table relationships...")
        relationships = {}
        
        for table_name, table_info in schema_info['tables'].items():
            relationships[table_name] = {
                'references': [],  # Tables this table references
                'referenced_by': []  # Tables that reference this table
            }
            
            # Tables this table references
            for column, fk_info in table_info['foreign_keys'].items():
                relationships[table_name]['references'].append({
                    'table': fk_info['references_table'],
                    'via_column': column,
                    'to_column': fk_info['references_column']
                })
        
        # Find reverse relationships
        for table_name, table_rels in relationships.items():
            for ref in table_rels['references']:
                ref_table = ref['table']
                if ref_table in relationships:
                    relationships[ref_table]['referenced_by'].append({
                        'table': table_name,
                        'via_column': ref['to_column'],
                        'from_column': ref['via_column']
                    })
        
        schema_info['relationships'] = relationships
        
        # Print relationship summary
        for table, rels in relationships.items():
            if rels['references'] or rels['referenced_by']:
                print(f"  📋 {table}:")
                for ref in rels['references']:
                    print(f"    → references {ref['table']}")
                for ref in rels['referenced_by']:
                    print(f"    ← referenced by {ref['table']}")
        
        # Generate summary
        total_tables = len(schema_info['tables'])
        total_columns = sum(len(table['columns']) for table in schema_info['tables'].values())
        total_fks = sum(len(table['foreign_keys']) for table in schema_info['tables'].values())
        total_rows = sum(table['row_count'] for table in schema_info['tables'].values())
        
        schema_info['summary'] = {
            'total_tables': total_tables,
            'total_columns': total_columns,
            'total_foreign_keys': total_fks,
            'total_rows': total_rows
        }
        
        # Save analysis
        output_dir = Path(__file__).parent.parent / "reports"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "database_schema_analysis.json"
        
        with open(output_file, 'w') as f:
            json.dump(schema_info, f, indent=2, default=str)
        
        # Print summary
        print(f"\n" + "="*60)
        print(f"SCHEMA ANALYSIS SUMMARY")
        print(f"="*60)
        print(f"📊 Tables: {total_tables}")
        print(f"📋 Total Columns: {total_columns}")
        print(f"🔗 Foreign Keys: {total_fks}")
        print(f"📈 Total Rows: {total_rows}")
        
        print(f"\n📝 Table Details:")
        for table_name, table_info in schema_info['tables'].items():
            col_count = len(table_info['columns'])
            fk_count = len(table_info['foreign_keys'])
            idx_count = len(table_info['indexes'])
            row_count = table_info['row_count']
            
            print(f"  • {table_name:<20} | {col_count:2d} cols | {fk_count:2d} FKs | {idx_count:2d} indexes | {row_count:6d} rows")
        
        print(f"\n💾 Detailed analysis saved to: {output_file}")
        print("✅ Schema analysis complete!")
        
        return schema_info
        
    except Exception as e:
        print(f"❌ Schema analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Cleanup
        if hasattr(db, 'disconnect'):
            db.disconnect()
            print("🔌 Database connection closed")

def compare_with_guide():
    """Compare current schema with the BACKEND_API_SYNC_GUIDE.md expectations"""
    print(f"\n" + "="*60)
    print(f"SCHEMA vs GUIDE COMPARISON")
    print(f"="*60)
    
    # Expected tables from the guide
    expected_tables = {
        'organizations': "Core organization table with multi-tenant setup",
        'organization_users': "User-organization relationships", 
        'patients': "Patient data with Cliniko integration",
        'active_patients': "Patient analytics and appointment data",
        'conversations': "Multi-source conversation data",
        'messages': "Conversation messages",
        'chatwoot_contacts': "Chatwoot contact sync",
        'chatwoot_conversations': "Chatwoot conversation sync", 
        'chatwoot_messages': "Chatwoot message sync"
    }
    
    # Tables mentioned in guide but using different naming
    guide_mentions = {
        'organization_members': 'organization_users',  # Guide uses organization_members
        'api_credentials': 'API credentials storage',
        'appointments': 'Appointment data',
        'sync_logs': 'Synchronization tracking',
        'audit_logs': 'Audit trail'
    }
    
    print("📋 Expected vs Actual Tables:")
    
    # Check what we have vs what's expected
    schema_info = analyze_schema()
    if not schema_info:
        print("❌ Could not analyze current schema")
        return
    
    current_tables = set(schema_info['tables'].keys())
    
    print("\n✅ Tables that match guide expectations:")
    for table, description in expected_tables.items():
        if table in current_tables:
            print(f"  • {table} - {description}")
    
    print("\n🔍 Tables in database but not explicitly mentioned in guide:")
    unexpected_tables = current_tables - set(expected_tables.keys()) - set(guide_mentions.keys())
    for table in sorted(unexpected_tables):
        print(f"  • {table}")
    
    print("\n❓ Tables mentioned in guide but not found in database:")
    missing_tables = set(expected_tables.keys()) - current_tables
    for table in sorted(missing_tables):
        print(f"  • {table} - {expected_tables[table]}")
    
    print("\n📝 Architecture Observations:")
    
    # Check for multi-tenant patterns
    org_id_tables = []
    for table_name, table_info in schema_info['tables'].items():
        if 'organization_id' in table_info['columns']:
            org_id_tables.append(table_name)
    
    print(f"  • Multi-tenant pattern (organization_id): {len(org_id_tables)} tables")
    for table in sorted(org_id_tables):
        print(f"    - {table}")
    
    # Check for audit patterns
    audit_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    tables_with_audit = []
    for table_name, table_info in schema_info['tables'].items():
        has_audit = any(field in table_info['columns'] for field in audit_fields)
        if has_audit:
            tables_with_audit.append(table_name)
    
    print(f"  • Audit trail pattern: {len(tables_with_audit)} tables have audit fields")
    
    # Check for external ID patterns
    external_id_patterns = ['cliniko_', 'chatwoot_', 'stripe_', 'clerk_']
    tables_with_external_ids = []
    for table_name, table_info in schema_info['tables'].items():
        has_external = any(
            any(pattern in col_name for pattern in external_id_patterns)
            for col_name in table_info['columns'].keys()
        )
        if has_external:
            tables_with_external_ids.append(table_name)
    
    print(f"  • External system integration: {len(tables_with_external_ids)} tables have external IDs")

if __name__ == "__main__":
    schema_info = analyze_schema()
    if schema_info:
        compare_with_guide()
        sys.exit(0)
    else:
        sys.exit(1) 