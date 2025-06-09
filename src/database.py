"""
Database client for SurfRehab v2 - Supabase integration
"""

import os
import logging
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Enhanced PostgreSQL client for Supabase with connection pooling"""
    
    def __init__(self):
        self.connection_string = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
        self.connection = None
        
        if not self.connection_string:
            raise ValueError("SUPABASE_DB_URL or DATABASE_URL environment variable is required")
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = False
            logger.info("Connected to Supabase database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from database")
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        if not self.connection:
            if not self.connect():
                raise Exception("Could not establish database connection")
        
        cursor = self.connection.cursor()
        try:
            yield cursor
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute a SELECT query and return single result"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            self.connection.commit()
            return affected_rows
    
    def insert_contact(self, contact_data: Dict[str, Any]) -> str:
        """Insert or update a contact, return contact ID"""
        query = """
            INSERT INTO contacts (phone, email, name, contact_type, cliniko_patient_id, 
                                status, organization_id, metadata)
            VALUES (%(phone)s, %(email)s, %(name)s, %(contact_type)s, %(cliniko_patient_id)s,
                   %(status)s, %(organization_id)s, %(metadata)s)
            ON CONFLICT (phone) 
            DO UPDATE SET 
                email = EXCLUDED.email,
                name = EXCLUDED.name,
                contact_type = EXCLUDED.contact_type,
                cliniko_patient_id = EXCLUDED.cliniko_patient_id,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, contact_data)
            result = cursor.fetchone()
            self.connection.commit()
            return result['id']
    
    def insert_active_patient(self, patient_data: Dict[str, Any]) -> int:
        """Insert or update active patient record"""
        query = """
            INSERT INTO active_patients (contact_id, recent_appointment_count, 
                                       upcoming_appointment_count, total_appointment_count,
                                       last_appointment_date, recent_appointments,
                                       upcoming_appointments, search_date_from,
                                       search_date_to, organization_id)
            VALUES (%(contact_id)s, %(recent_appointment_count)s, %(upcoming_appointment_count)s,
                   %(total_appointment_count)s, %(last_appointment_date)s,
                   %(recent_appointments)s, %(upcoming_appointments)s,
                   %(search_date_from)s, %(search_date_to)s, %(organization_id)s)
            ON CONFLICT (contact_id)
            DO UPDATE SET
                recent_appointment_count = EXCLUDED.recent_appointment_count,
                upcoming_appointment_count = EXCLUDED.upcoming_appointment_count,
                total_appointment_count = EXCLUDED.total_appointment_count,
                last_appointment_date = EXCLUDED.last_appointment_date,
                recent_appointments = EXCLUDED.recent_appointments,
                upcoming_appointments = EXCLUDED.upcoming_appointments,
                updated_at = NOW()
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, patient_data)
            result = cursor.fetchone()
            self.connection.commit()
            return result['id']
    
    def insert_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Insert or update conversation record"""
        query = """
            INSERT INTO conversations (contact_id, source, external_id, 
                                     chatwoot_conversation_id, phone_number,
                                     status, organization_id, metadata)
            VALUES (%(contact_id)s, %(source)s, %(external_id)s,
                   %(chatwoot_conversation_id)s, %(phone_number)s,
                   %(status)s, %(organization_id)s, %(metadata)s)
            ON CONFLICT (external_id)
            DO UPDATE SET
                status = EXCLUDED.status,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, conversation_data)
            result = cursor.fetchone()
            self.connection.commit()
            return result['id']
    
    def log_sync_operation(self, sync_data: Dict[str, Any]) -> str:
        """Log a sync operation"""
        query = """
            INSERT INTO sync_logs (source_system, operation_type, status,
                                 records_processed, records_success, records_failed,
                                 error_details, started_at, completed_at,
                                 metadata, organization_id)
            VALUES (%(source_system)s, %(operation_type)s, %(status)s,
                   %(records_processed)s, %(records_success)s, %(records_failed)s,
                   %(error_details)s, %(started_at)s, %(completed_at)s,
                   %(metadata)s, %(organization_id)s)
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, sync_data)
            result = cursor.fetchone()
            self.connection.commit()
            return result['id']
    
    def get_contact_stats(self, organization_id: str = None) -> Dict[str, Any]:
        """Get contact statistics for organization"""
        query = """
            SELECT 
                contact_type,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE cliniko_patient_id IS NOT NULL) as with_cliniko_id
            FROM contacts 
            WHERE deleted_at IS NULL
            AND (%(organization_id)s IS NULL OR organization_id = %(organization_id)s)
            GROUP BY contact_type
        """
        
        results = self.execute_query(query, {'organization_id': organization_id})
        return {row['contact_type']: dict(row) for row in results}
    
    def get_recent_sync_logs(self, organization_id: str = None, limit: int = 10) -> List[Dict]:
        """Get recent sync operations"""
        query = """
            SELECT * FROM sync_logs
            WHERE (%(organization_id)s IS NULL OR organization_id = %(organization_id)s)
            ORDER BY started_at DESC
            LIMIT %(limit)s
        """
        
        return self.execute_query(query, {
            'organization_id': organization_id,
            'limit': limit
        })
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            result = self.execute_single("SELECT 1 as health")
            return result and result.get('health') == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global database client instance
db = SupabaseClient() 