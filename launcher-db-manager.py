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
        """Initialize the database with optimizations"""
        with self.get_connection() as conn:
            # Enable WAL mode for better concurrent access
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            conn.execute('PRAGMA foreign_keys=ON')
            
            # Read and execute schema from file or string
            # You would need to put the schema SQL here
            conn.executescript("""/* Schema SQL from above */""")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with retry logic"""
        max_attempts = 3
        attempt = 0
        last_error = None

        while attempt < max_attempts:
            try:
                conn = sqlite3.connect(self.db_path, timeout=20)
                conn.row_factory = sqlite3.Row  # Enable row factory for named columns
                yield conn
                return
            except sqlite3.OperationalError as e:
                last_error = e
                attempt += 1
                time.sleep(1)
            finally:
                if 'conn' in locals():
                    conn.close()
        
        raise ConnectionError(f"Failed to connect to database after {max_attempts} attempts: {last_error}")

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
        """Grant application access to a user"""
        query = '''
            INSERT OR REPLACE INTO user_application_access 
                (user_sid, application_id, granted_by, is_active)
            VALUES (?, ?, ?, 1)
        '''
        try:
            with self.get_connection() as conn:
                conn.execute(query, (user_sid, application_id, granted_by))
                conn.commit()
                return True
        except sqlite3.Error:
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
