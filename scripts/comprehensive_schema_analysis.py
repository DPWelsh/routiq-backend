#!/usr/bin/env python3
"""
Comprehensive Database Schema Analysis Script
Analyzes the current Supabase PostgreSQL database schema and generates detailed documentation.
"""

import asyncio
import asyncpg
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

class DatabaseSchemaAnalyzer:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.schema_info = {}
        
    async def connect(self):
        """Connect to the database"""
        self.conn = await asyncpg.connect(self.database_url)
        print("✅ Connected to database successfully")
        
    async def disconnect(self):
        """Disconnect from the database"""
        if hasattr(self, 'conn'):
            await self.conn.close()
            print("✅ Disconnected from database")
    
    async def analyze_tables(self):
        """Get detailed information about all tables"""
        query = """
        SELECT 
            t.table_name,
            t.table_type,
            pg_size_pretty(pg_total_relation_size(c.oid)) as table_size,
            obj_description(c.oid) as table_comment,
            c.reltuples::bigint as estimated_row_count
        FROM information_schema.tables t
        LEFT JOIN pg_class c ON c.relname = t.table_name
        WHERE t.table_schema = 'public' 
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name;
        """
        
        tables = await self.conn.fetch(query)
        self.schema_info['tables'] = {}
        
        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = table['table_name']
            print(f"  • {table_name} ({table['table_size']}, ~{table['estimated_row_count']} rows)")
            
            self.schema_info['tables'][table_name] = {
                'type': table['table_type'],
                'size': table['table_size'],
                'estimated_rows': table['estimated_row_count'],
                'comment': table['table_comment'],
                'columns': await self.analyze_columns(table_name),
                'constraints': await self.analyze_constraints(table_name),
                'indexes': await self.analyze_indexes(table_name),
                'foreign_keys': await self.analyze_foreign_keys(table_name)
            }
    
    async def analyze_columns(self, table_name: str):
        """Get detailed column information for a table"""
        query = """
        SELECT 
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.is_nullable,
            c.column_default,
            col_description(pgc.oid, c.ordinal_position) as column_comment
        FROM information_schema.columns c
        LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
        WHERE c.table_schema = 'public' 
        AND c.table_name = $1
        ORDER BY c.ordinal_position;
        """
        
        columns = await self.conn.fetch(query, table_name)
        column_info = {}
        
        for col in columns:
            column_info[col['column_name']] = {
                'type': col['data_type'],
                'max_length': col['character_maximum_length'],
                'precision': col['numeric_precision'],
                'scale': col['numeric_scale'],
                'nullable': col['is_nullable'] == 'YES',
                'default': col['column_default'],
                'comment': col['column_comment']
            }
        
        return column_info
    
    async def analyze_constraints(self, table_name: str):
        """Get constraint information for a table"""
        query = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            tc.is_deferrable,
            tc.initially_deferred
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public' 
        AND tc.table_name = $1
        ORDER BY tc.constraint_type, tc.constraint_name;
        """
        
        constraints = await self.conn.fetch(query, table_name)
        constraint_info = {}
        
        for constraint in constraints:
            constraint_name = constraint['constraint_name']
            if constraint_name not in constraint_info:
                constraint_info[constraint_name] = {
                    'type': constraint['constraint_type'],
                    'columns': [],
                    'deferrable': constraint['is_deferrable'] == 'YES',
                    'initially_deferred': constraint['initially_deferred'] == 'YES'
                }
            
            if constraint['column_name']:
                constraint_info[constraint_name]['columns'].append(constraint['column_name'])
        
        return constraint_info
    
    async def analyze_indexes(self, table_name: str):
        """Get index information for a table"""
        query = """
        SELECT 
            i.indexname,
            i.indexdef,
            pg_size_pretty(pg_relation_size(i.indexname::regclass)) as index_size,
            i.tablespace
        FROM pg_indexes i
        WHERE i.schemaname = 'public' 
        AND i.tablename = $1
        ORDER BY i.indexname;
        """
        
        indexes = await self.conn.fetch(query, table_name)
        index_info = {}
        
        for idx in indexes:
            index_info[idx['indexname']] = {
                'definition': idx['indexdef'],
                'size': idx['index_size'],
                'tablespace': idx['tablespace']
            }
        
        return index_info
    
    async def analyze_foreign_keys(self, table_name: str):
        """Get foreign key relationships for a table"""
        query = """
        SELECT 
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.update_rule,
            rc.delete_rule
        FROM information_schema.table_constraints tc 
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        JOIN information_schema.referential_constraints rc 
            ON tc.constraint_name = rc.constraint_name
            AND tc.table_schema = rc.constraint_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema = 'public'
        AND tc.table_name = $1;
        """
        
        foreign_keys = await self.conn.fetch(query, table_name)
        fk_info = {}
        
        for fk in foreign_keys:
            fk_info[fk['column_name']] = {
                'references_table': fk['foreign_table_name'],
                'references_column': fk['foreign_column_name'],
                'update_rule': fk['update_rule'],
                'delete_rule': fk['delete_rule']
            }
        
        return fk_info
    
    async def analyze_row_level_security(self):
        """Check for Row Level Security policies"""
        query = """
        SELECT 
            schemaname,
            tablename,
            policyname,
            permissive,
            roles,
            cmd,
            qual,
            with_check
        FROM pg_policies
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname;
        """
        
        policies = await self.conn.fetch(query)
        self.schema_info['rls_policies'] = {}
        
        print(f"\n🔒 Row Level Security Policies: {len(policies)}")
        for policy in policies:
            table_name = policy['tablename']
            if table_name not in self.schema_info['rls_policies']:
                self.schema_info['rls_policies'][table_name] = []
            
            self.schema_info['rls_policies'][table_name].append({
                'name': policy['policyname'],
                'permissive': policy['permissive'],
                'roles': policy['roles'],
                'command': policy['cmd'],
                'using': policy['qual'],
                'with_check': policy['with_check']
            })
            
            print(f"  • {table_name}.{policy['policyname']} ({policy['cmd']})")
    
    async def analyze_database_stats(self):
        """Get overall database statistics"""
        queries = {
            'database_size': "SELECT pg_size_pretty(pg_database_size(current_database()));",
            'total_tables': "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';",
            'total_indexes': "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';",
            'total_constraints': "SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'public';",
            'connection_info': "SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"
        }
        
        stats = {}
        for key, query in queries.items():
            result = await self.conn.fetchrow(query)
            if key == 'connection_info':
                stats[key] = dict(result)
            else:
                stats[key] = result[0]
        
        self.schema_info['database_stats'] = stats
        
        print(f"\n📈 Database Statistics:")
        print(f"  • Database: {stats['connection_info']['current_database']}")
        print(f"  • Size: {stats['database_size']}")
        print(f"  • Tables: {stats['total_tables']}")
        print(f"  • Indexes: {stats['total_indexes']}")
        print(f"  • Constraints: {stats['total_constraints']}")
    
    async def generate_relationship_map(self):
        """Generate a map of table relationships"""
        relationships = {}
        
        for table_name, table_info in self.schema_info['tables'].items():
            relationships[table_name] = {
                'references': {},  # Tables this table references
                'referenced_by': {}  # Tables that reference this table
            }
            
            # Tables this table references
            for column, fk_info in table_info['foreign_keys'].items():
                relationships[table_name]['references'][fk_info['references_table']] = {
                    'via_column': column,
                    'to_column': fk_info['references_column']
                }
        
        # Find reverse relationships
        for table_name, table_rels in relationships.items():
            for ref_table, ref_info in table_rels['references'].items():
                if ref_table in relationships:
                    relationships[ref_table]['referenced_by'][table_name] = {
                        'via_column': ref_info['to_column'],
                        'from_column': ref_info['via_column']
                    }
        
        self.schema_info['relationships'] = relationships
        
        print(f"\n🔗 Table Relationships:")
        for table, rels in relationships.items():
            if rels['references'] or rels['referenced_by']:
                print(f"  • {table}:")
                for ref_table in rels['references']:
                    print(f"    → references {ref_table}")
                for ref_table in rels['referenced_by']:
                    print(f"    ← referenced by {ref_table}")
    
    async def save_analysis(self, output_file: str = 'database_schema_analysis.json'):
        """Save the complete analysis to a JSON file"""
        self.schema_info['analysis_metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'database_url': self.database_url.split('@')[-1] if '@' in self.database_url else 'hidden',
            'analyzer_version': '1.0.0'
        }
        
        os.makedirs('reports', exist_ok=True)
        output_path = f'reports/{output_file}'
        
        with open(output_path, 'w') as f:
            json.dump(self.schema_info, f, indent=2, default=str)
        
        print(f"\n💾 Analysis saved to: {output_path}")
        return output_path
    
    async def print_summary(self):
        """Print a summary of the analysis"""
        print(f"\n" + "="*60)
        print(f"DATABASE SCHEMA ANALYSIS SUMMARY")
        print(f"="*60)
        
        total_tables = len(self.schema_info['tables'])
        total_columns = sum(len(table['columns']) for table in self.schema_info['tables'].values())
        total_fks = sum(len(table['foreign_keys']) for table in self.schema_info['tables'].values())
        
        print(f"📊 Tables: {total_tables}")
        print(f"📋 Total Columns: {total_columns}")
        print(f"🔗 Foreign Keys: {total_fks}")
        print(f"🔒 RLS Policies: {len(self.schema_info.get('rls_policies', {}))}")
        
        print(f"\n📝 Table Overview:")
        for table_name, table_info in self.schema_info['tables'].items():
            col_count = len(table_info['columns'])
            fk_count = len(table_info['foreign_keys'])
            idx_count = len(table_info['indexes'])
            
            print(f"  • {table_name:<20} | {col_count:2d} cols | {fk_count:2d} FKs | {idx_count:2d} indexes | {table_info['size']}")

async def main():
    """Main analysis function"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        return
    
    analyzer = DatabaseSchemaAnalyzer(DATABASE_URL)
    
    try:
        await analyzer.connect()
        
        print("🔍 Starting comprehensive database schema analysis...")
        
        # Run all analyses
        await analyzer.analyze_tables()
        await analyzer.analyze_row_level_security()
        await analyzer.analyze_database_stats()
        await analyzer.generate_relationship_map()
        
        # Save results
        output_file = await analyzer.save_analysis()
        
        # Print summary
        await analyzer.print_summary()
        
        print(f"\n✅ Schema analysis complete!")
        print(f"📄 Detailed report saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise
    finally:
        await analyzer.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 