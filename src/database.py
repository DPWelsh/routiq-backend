"""
Database client for SurfRehab v2 - Supabase integration with Connection Pooling
"""

import os
import logging
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import threading
from urllib.parse import urlparse
import atexit

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Enhanced PostgreSQL client for Supabase with connection pooling"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SupabaseClient, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.connection_string = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
        self.connection_pool = None
        self._current_connection = None  # For backward compatibility
        self._initialized = True
        
        if not self.connection_string:
            raise ValueError("SUPABASE_DB_URL or DATABASE_URL environment variable is required")
        
        # Parse connection string to extract parameters
        parsed = urlparse(self.connection_string)
        self.db_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password,
        }
        
        # Initialize connection pool
        self._init_connection_pool()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_database)
    
    @property
    def connection(self):
        """
        Backward compatibility: provide direct connection access
        WARNING: This connection should be manually returned when done
        """
        if not self._current_connection or self._current_connection.closed:
            if self._current_connection:
                # Return old connection if it exists
                self.return_connection(self._current_connection)
            self._current_connection = self.get_connection()
            logger.debug("Created new persistent connection for backward compatibility")
        return self._current_connection
    
    def connect(self) -> bool:
        """Backward compatibility: connect method"""
        try:
            # Test connection
            test_conn = self.get_connection()
            self.return_connection(test_conn)
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Backward compatibility: disconnect method"""
        if self._current_connection:
            try:
                if not self._current_connection.closed:
                    self.return_connection(self._current_connection)
                    logger.debug("Returned persistent connection to pool")
            except Exception as e:
                logger.warning(f"Error returning connection: {e}")
            finally:
                self._current_connection = None
    
    def _init_connection_pool(self):
        """Initialize the connection pool with optimized settings"""
        try:
            # Enhanced connection pool configuration with better defaults
            min_connections = int(os.getenv('DB_MIN_CONNECTIONS', '3'))  # Increased from 2
            max_connections = int(os.getenv('DB_MAX_CONNECTIONS', '25'))  # Reasonable default
            
            # Production optimization: Use larger pool for high-load scenarios
            if os.getenv('APP_ENV') == 'production':
                min_connections = max(min_connections, 5)  # Ensure min 5 in production
                max_connections = max(max_connections, 30)  # Ensure reasonable max
            
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=min_connections,
                maxconn=max_connections,
                host=self.db_params['host'],
                port=self.db_params['port'],
                database=self.db_params['database'],
                user=self.db_params['user'],
                password=self.db_params['password'],
                cursor_factory=RealDictCursor,
                # Connection pool optimizations
                options='-c statement_timeout=30s -c idle_in_transaction_session_timeout=300s'
            )
            
            logger.info(f"✅ Database connection pool initialized: {min_connections}-{max_connections} connections")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool with enhanced error handling"""
        if not self.connection_pool:
            raise Exception("Connection pool not initialized")
        
        try:
            connection = self.connection_pool.getconn()
            if connection is None:
                raise Exception("Failed to get connection from pool - pool may be exhausted")
            return connection
        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            raise
    
    def return_connection(self, connection):
        """Return a connection to the pool with enhanced error handling"""
        if self.connection_pool and connection:
            try:
                # Check if connection is still valid before returning
                if connection.closed == 0:  # 0 means connection is open
                    self.connection_pool.putconn(connection)
                else:
                    logger.warning("Attempted to return closed connection - discarding")
            except Exception as e:
                logger.error(f"Error returning connection to pool: {e}")
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            try:
                self.connection_pool.closeall()
                logger.info("✅ All database connections closed")
            except Exception as e:
                logger.error(f"Error closing connections: {e}")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get detailed connection pool statistics"""
        if not self.connection_pool:
            return {"error": "Pool not initialized"}
        
        try:
            return {
                'minconn': self.connection_pool.minconn,
                'maxconn': self.connection_pool.maxconn,
                'closed': self.connection_pool.closed,
                'pool_type': 'ThreadedConnectionPool',
                'current_connection_persistent': self._current_connection is not None
            }
        except AttributeError:
            return {'status': 'pool_active', 'details': 'limited_stats_available'}
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor with enhanced connection pooling"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            yield cursor
            connection.commit()
        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                    logger.debug("Transaction rolled back due to error")
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {rollback_error}")
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception as e:
                    logger.warning(f"Error closing cursor: {e}")
            if connection:
                self.return_connection(connection)
    
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
            return cursor.rowcount
    
    def execute_batch(self, query: str, params_list: List[tuple]) -> int:
        """Execute batch operations efficiently"""
        total_affected = 0
        with self.get_cursor() as cursor:
            for params in params_list:
                cursor.execute(query, params)
                total_affected += cursor.rowcount
        return total_affected
    
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
            return result['id']
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check with connection pool stats"""
        try:
            # Test database connectivity
            result = self.execute_single("SELECT 1 as health, NOW() as timestamp")
            
            # Get enhanced connection pool stats
            pool_stats = self.get_pool_stats()
            
            return {
                'database_connected': True,
                'health_check': result.get('health') == 1 if result else False,
                'timestamp': result.get('timestamp').isoformat() if result and result.get('timestamp') else None,
                'connection_pool': pool_stats
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'database_connected': False,
                'error': str(e),
                'connection_pool': {}
            }

    def cleanup_database(self):
        """Enhanced cleanup for graceful shutdown"""
        try:
            # Clean up persistent connection
            if self._current_connection:
                self.disconnect()
            
            # Close all pool connections
            self.close_all_connections()
            
            logger.info("✅ Database cleanup completed")
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")

# Global database client instance with connection pooling
db = SupabaseClient()

# Enhanced cleanup function for graceful shutdown
def cleanup_database():
    """Cleanup database connections on shutdown"""
    global db
    if db:
        db.cleanup_database() 