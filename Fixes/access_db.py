import pyodbc
import time
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional

class LauncherDB:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.connection_string = self._build_connection_string()

    def _build_connection_string(self):
        """Build the ODBC connection string for Access database"""
        # Check if it's an .accdb (newer) or .mdb (older) file
        if self.db_path.suffix.lower() == '.accdb':
            driver = 'Microsoft Access Driver (*.mdb, *.accdb)'
        else:
            driver = 'Microsoft Access Driver (*.mdb)'
        
        return f'DRIVER={{{driver}}};DBQ={self.db_path};'

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with retry logic"""
        max_attempts = 3
        attempt = 0
        last_error = None

        while attempt < max_attempts:
            try:
                conn = pyodbc.connect(self.connection_string, timeout=20)
                conn.autocommit = True  # Access equivalent to autocommit mode
                
                yield conn
                return
            except pyodbc.Error as e:
                last_error = e
                attempt += 1
                time.sleep(1)
            finally:
                if 'conn' in locals():
                    conn.close()
        
        raise ConnectionError(f"Failed to connect to database after {max_attempts} attempts: {last_error}")

    def _dict_from_row(self, cursor, row):
        """Convert pyodbc row to dictionary"""
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

    def get_user_applications(self, user_sid: str) -> List[Dict[str, Any]]:
        """Get all applications available to a user with related data"""
        query = '''
            SELECT 
                a.*, 
                l.name as lob_name,
                s.name as status_name,
                cc.name as cost_center_name
            FROM (((applications a
            INNER JOIN user_application_access uaa ON a.id = uaa.application_id)
            LEFT JOIN lobs l ON a.lob_id = l.id)
            LEFT JOIN statuses s ON a.status_id = s.id)
            LEFT JOIN cost_centers cc ON a.cost_center_id = cc.id
            WHERE uaa.user_sid = ? AND uaa.is_active = True AND a.is_active = True
        '''
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, user_sid)
            results = []
            for row in cursor.fetchall():
                results.append(self._dict_from_row(cursor, row))
            return results

    def is_sto_member(self, user_sid: str, cost_center_id: int) -> bool:
        """Check if a user is an STO member for a cost center"""
        query = '''
            SELECT COUNT(*) as count_result
            FROM sto_members 
            WHERE sid = ? AND cost_center_id = ? AND is_active = True
        '''
        with self.get_connection() as conn:
            cursor = conn.execute(query, user_sid, cost_center_id)
            result = cursor.fetchone()
            return result.count_result > 0

    def get_user_cost_center(self, user_sid: str) -> Optional[Dict[str, Any]]:
        """Get user's cost center information"""
        query = '''
            SELECT cc.* 
            FROM cost_centers cc
            INNER JOIN users u ON cc.id = u.cost_center_id
            WHERE u.sid = ? AND u.is_active = True
        '''
        with self.get_connection() as conn:
            cursor = conn.execute(query, user_sid)
            row = cursor.fetchone()
            return self._dict_from_row(cursor, row) if row else None

    def grant_application_access(self, user_sid: str, application_id: int, granted_by: str) -> bool:
        """Grant application access to a user"""
        # Access doesn't support INSERT OR REPLACE, so we need to handle it manually
        check_query = '''
            SELECT COUNT(*) as count_result
            FROM user_application_access 
            WHERE user_sid = ? AND application_id = ?
        '''
        
        insert_query = '''
            INSERT INTO user_application_access 
                (user_sid, application_id, granted_by, is_active)
            VALUES (?, ?, ?, True)
        '''
        
        update_query = '''
            UPDATE user_application_access 
            SET granted_by = ?, is_active = True
            WHERE user_sid = ? AND application_id = ?
        '''
        
        try:
            with self.get_connection() as conn:
                # Check if record exists
                cursor = conn.execute(check_query, user_sid, application_id)
                exists = cursor.fetchone().count_result > 0
                
                if exists:
                    conn.execute(update_query, granted_by, user_sid, application_id)
                else:
                    conn.execute(insert_query, user_sid, application_id, granted_by)
                
                return True
        except pyodbc.Error as e:
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
            WHERE f.is_active = True
        '''
        with self.get_connection() as conn:
            cursor = conn.execute(query, application_id)
            results = []
            for row in cursor.fetchall():
                results.append(self._dict_from_row(cursor, row))
            return results

    def insert_application(self, app_data: Dict[str, Any]) -> Optional[int]:
        """Insert a new application"""
        query = '''
            INSERT INTO applications 
                (name, description, executable_path, lob_id, status_id, cost_center_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, True)
        '''
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, 
                    app_data['name'],
                    app_data.get('description', ''),
                    app_data['executable_path'],
                    app_data['lob_id'],
                    app_data['status_id'],
                    app_data['cost_center_id']
                )
                
                # Get the last inserted ID
                id_query = "SELECT @@IDENTITY"
                cursor = conn.execute(id_query)
                app_id = cursor.fetchone()[0]
                
                return int(app_id) if app_id else None
        except pyodbc.Error as e:
            print(f"Error inserting application: {e}")
            return None

    def update_application_status(self, app_id: int, status_id: int, updated_by: str) -> bool:
        """Update application status"""
        query = '''
            UPDATE applications 
            SET status_id = ?, updated_at = Now(), updated_by = ?
            WHERE id = ?
        '''
        try:
            with self.get_connection() as conn:
                conn.execute(query, status_id, updated_by, app_id)
                return True
        except pyodbc.Error as e:
            print(f"Error updating application status: {e}")
            return False

    def bulk_insert_with_checkpoint(self, table: str, data_list: List[Dict], columns: List[str]) -> bool:
        """Perform bulk insert operations"""
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            with self.get_connection() as conn:
                conn.autocommit = False  # Disable autocommit for transaction
                
                try:
                    for data in data_list:
                        values = [data.get(col) for col in columns]
                        conn.execute(query, values)
                    
                    conn.commit()
                    return True
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    conn.autocommit = True  # Re-enable autocommit
                    
        except pyodbc.Error as e:
            print(f"Error in bulk insert: {e}")
            return False

    def refresh_connection(self):
        """Refresh connection - Access doesn't need special refresh like SQLite WAL"""
        # Access doesn't have WAL mode, so this is mostly a no-op
        # We could potentially close and reopen connections if needed
        pass

    def test_connection(self) -> bool:
        """Test if the database connection is working"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False