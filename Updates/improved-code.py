import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional

class LauncherDB:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self._setup_database()

    def _setup_database(self):
        """Initialize the database with aggressive checkpoint settings"""
        with self.get_connection() as conn:
            # Enable WAL mode for better concurrent access
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=30000')  # Increased timeout
            conn.execute('PRAGMA foreign_keys=ON')
            
            # Aggressive checkpoint settings for immediate visibility
            conn.execute('PRAGMA wal_autocheckpoint=1')    # Checkpoint after every page!
            conn.execute('PRAGMA synchronous=NORMAL')      
            conn.execute('PRAGMA cache_size=-32000')       # Smaller cache to force writes
            
            # Force immediate checkpoint
            conn.execute('PRAGMA wal_checkpoint(RESTART)')
            
            # Read and execute schema from file or string
            conn.executescript("""/* Schema SQL from above */""")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with aggressive checkpoint"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=30,
                isolation_level=None  # Autocommit mode
            )
            conn.row_factory = sqlite3.Row
            
            # Set connection-level pragmas for immediate writes
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=-8000')  # Small cache
            
            yield conn
            
        finally:
            if conn:
                try:
                    # Force aggressive checkpoint on connection close
                    conn.execute('PRAGMA wal_checkpoint(RESTART)')
                except:
                    pass
                conn.close()

    def _force_checkpoint(self):
        """Force a WAL checkpoint to make changes immediately visible"""
        with self.get_connection() as conn:
            conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')

    def get_user_applications(self, user_sid: str) -> List[Dict[str, Any]]:
        """Get all applications available to a user with related data"""
        query = '''
            SELECT 
                a.*, 
                l.name as lob_name,
                s.name as status_name,
                cc.name as cost_center_name
            FROM applications a
            JOIN user_application_access uaa ON a.id = uaa.application_id
            LEFT JOIN lobs l ON a.lob_id = l.id
            LEFT JOIN statuses s ON a.status_id = s.id
            LEFT JOIN cost_centers cc ON a.cost_center_id = cc.id
            WHERE uaa.user_sid = ? AND uaa.is_active = 1 AND a.is_active = 1
        '''
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, (user_sid,))
            return [dict(row) for row in cursor.fetchall()]

    def is_sto_member(self, user_sid: str, cost_center_id: int) -> bool:
        """Check if a user is an STO member for a cost center"""
        query = '''
            SELECT EXISTS (
                SELECT 1 FROM sto_members 
                WHERE sid = ? AND cost_center_id = ? AND is_active = 1
            )
        '''
        with self.get_connection() as conn:
            result = conn.execute(query, (user_sid, cost_center_id)).fetchone()[0]
            return bool(result)

    def get_user_cost_center(self, user_sid: str) -> Optional[Dict[str, Any]]:
        """Get user's cost center information"""
        query = '''
            SELECT cc.* 
            FROM cost_centers cc
            JOIN users u ON cc.id = u.cost_center_id
            WHERE u.sid = ? AND u.is_active = 1
        '''
        with self.get_connection() as conn:
            result = conn.execute(query, (user_sid,)).fetchone()
            return dict(result) if result else None

    def grant_application_access(self, user_sid: str, application_id: int, granted_by: str) -> bool:
        """Grant application access with immediate forced commit"""
        query = '''
            INSERT OR REPLACE INTO user_application_access 
                (user_sid, application_id, granted_by, is_active)
            VALUES (?, ?, ?, 1)
        '''
        try:
            with self.get_connection() as conn:
                # Execute with immediate commit
                conn.execute(query, (user_sid, application_id, granted_by))
                
                # Multiple aggressive checkpoints
                conn.execute('PRAGMA wal_checkpoint(RESTART)')
                conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                
                # Verify the insert worked
                verify_query = "SELECT COUNT(*) FROM user_application_access WHERE user_sid = ? AND application_id = ?"
                result = conn.execute(verify_query, (user_sid, application_id)).fetchone()[0]
                
                return result > 0
        except sqlite3.Error as e:
            print(f"Error granting access: {e}")
            return False

    def get_application_fields(self, application_id: int) -> List[Dict[str, Any]]:
        """Get all field values for an application"""
        query = '''
            SELECT 
                f.name, f.field_type, f.is_required,
                afv.field_value
            FROM fields f
            LEFT JOIN application_field_values afv 
                ON f.id = afv.field_id 
                AND afv.application_id = ?
            WHERE f.is_active = 1
        '''
        with self.get_connection() as conn:
            cursor = conn.execute(query, (application_id,))
            return [dict(row) for row in cursor.fetchall()]

    def insert_application(self, app_data: Dict[str, Any]) -> Optional[int]:
        """Insert a new application with immediate visibility"""
        query = '''
            INSERT INTO applications 
                (name, description, executable_path, lob_id, status_id, cost_center_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        '''
        try:
            with self.get_connection() as conn:
                conn.execute('BEGIN IMMEDIATE')
                cursor = conn.execute(query, (
                    app_data['name'],
                    app_data.get('description', ''),
                    app_data['executable_path'],
                    app_data['lob_id'],
                    app_data['status_id'],
                    app_data['cost_center_id']
                ))
                app_id = cursor.lastrowid
                conn.execute('COMMIT')
                
                # Force checkpoint
                conn.execute('PRAGMA wal_checkpoint(PASSIVE)')
                
                return app_id
        except sqlite3.Error as e:
            print(f"Error inserting application: {e}")
            return None

    def update_application_status(self, app_id: int, status_id: int, updated_by: str) -> bool:
        """Update application status with immediate visibility"""
        query = '''
            UPDATE applications 
            SET status_id = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
            WHERE id = ?
        '''
        try:
            with self.get_connection() as conn:
                conn.execute('BEGIN IMMEDIATE')
                conn.execute(query, (status_id, updated_by, app_id))
                conn.execute('COMMIT')
                
                # Force checkpoint
                conn.execute('PRAGMA wal_checkpoint(PASSIVE)')
                
                return True
        except sqlite3.Error as e:
            print(f"Error updating application status: {e}")
            return False

    def bulk_insert_with_checkpoint(self, table: str, data_list: List[Dict], columns: List[str]) -> bool:
        """Perform bulk insert operations with checkpoint"""
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            with self.get_connection() as conn:
                conn.execute('BEGIN IMMEDIATE')
                
                for data in data_list:
                    values = [data.get(col) for col in columns]
                    conn.execute(query, values)
                
                conn.execute('COMMIT')
                
                # Force checkpoint to ensure immediate visibility
                conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                
                return True
        except sqlite3.Error as e:
            print(f"Error in bulk insert: {e}")
            return False

    def refresh_connection(self):
        """Manually refresh by forcing a checkpoint - useful for read operations"""
        try:
            with self.get_connection() as conn:
                conn.execute('PRAGMA wal_checkpoint(RESTART)')
        except sqlite3.Error:
            pass  # Ignore checkpoint errors
    
    def diagnose_wal_status(self):
        """Diagnose WAL file status and blocking transactions"""
        try:
            with self.get_connection() as conn:
                # Check WAL file size
                wal_info = conn.execute('PRAGMA wal_checkpoint').fetchall()
                print(f"WAL checkpoint result: {wal_info}")
                
                # Check journal mode
                journal_mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
                print(f"Journal mode: {journal_mode}")
                
                # Check if there are any locks
                try:
                    conn.execute('BEGIN IMMEDIATE')
                    conn.execute('ROLLBACK')
                    print("No blocking transactions detected")
                except sqlite3.OperationalError as e:
                    print(f"Blocking transaction detected: {e}")
                
                # Force aggressive checkpoint
                result = conn.execute('PRAGMA wal_checkpoint(RESTART)').fetchone()
                print(f"RESTART checkpoint result: {result}")
                
        except Exception as e:
            print(f"Diagnosis error: {e}")
    
    def force_wal_reset(self):
        """Nuclear option: Reset WAL mode completely"""
        try:
            with self.get_connection() as conn:
                # Switch to DELETE mode temporarily
                conn.execute('PRAGMA journal_mode=DELETE')
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                print("WAL mode reset complete")
        except Exception as e:
            print(f"WAL reset error: {e}")
