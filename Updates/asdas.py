import fdb
import time
import os
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional

class FirebirdLauncherDB:
    def __init__(self, db_path, fb_client_path=None):
        self.db_path = Path(db_path)
        self.fb_client_path = fb_client_path
        
        # Set Firebird client library path if provided
        if fb_client_path:
            # Ensure the directory containing fbclient.dll is in PATH
            fb_dir = Path(fb_client_path).parent
            if str(fb_dir) not in os.environ['PATH']:
                os.environ['PATH'] = str(fb_dir) + os.pathsep + os.environ['PATH']
            
            # Set the library path for fdb
            fdb.load_api(str(fb_client_path))
        
        self._setup_database()

    def _setup_database(self):
        """Initialize the database"""
        # Create database if it doesn't exist
        if not self.db_path.exists():
            self._create_database()
        
        # Set up connection parameters and create tables
        with self.get_connection() as conn:
            self._create_tables(conn)

    def _create_database(self):
        """Create a new Firebird database file"""
        try:
            # Connection string for embedded Firebird
            conn_str = str(self.db_path)
            
            # Create database - using default user for embedded
            con = fdb.create_database(
                dsn=conn_str,
                user='sysdba',  # Default for embedded
                password='masterkey',  # Default for embedded
                page_size=8192,  # 8KB pages
                charset='UTF8'
            )
            con.close()
            print(f"Database created: {self.db_path}")
            
        except Exception as e:
            print(f"Error creating database: {e}")
            raise

    def _create_tables(self, conn):
        """Create database tables with Firebird-specific syntax"""
        schema_sql = """
        -- Enable automatic transaction management
        SET AUTODDL ON;
        
        -- LOBs table
        CREATE TABLE IF NOT EXISTS lobs (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(500),
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Statuses table
        CREATE TABLE IF NOT EXISTS statuses (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(200),
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Cost Centers table
        CREATE TABLE IF NOT EXISTS cost_centers (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            code VARCHAR(20) UNIQUE,
            description VARCHAR(500),
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER NOT NULL PRIMARY KEY,
            sid VARCHAR(50) NOT NULL UNIQUE,
            username VARCHAR(100),
            email VARCHAR(200),
            cost_center_id INTEGER,
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id)
        );
        
        -- Applications table
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description VARCHAR(1000),
            executable_path VARCHAR(500) NOT NULL,
            lob_id INTEGER,
            status_id INTEGER,
            cost_center_id INTEGER,
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            FOREIGN KEY (lob_id) REFERENCES lobs(id),
            FOREIGN KEY (status_id) REFERENCES statuses(id),
            FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id)
        );
        
        -- User Application Access table
        CREATE TABLE IF NOT EXISTS user_application_access (
            id INTEGER NOT NULL PRIMARY KEY,
            user_sid VARCHAR(50) NOT NULL,
            application_id INTEGER NOT NULL,
            granted_by VARCHAR(50),
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id),
            UNIQUE (user_sid, application_id)
        );
        
        -- STO Members table
        CREATE TABLE IF NOT EXISTS sto_members (
            id INTEGER NOT NULL PRIMARY KEY,
            sid VARCHAR(50) NOT NULL,
            cost_center_id INTEGER NOT NULL,
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id),
            UNIQUE (sid, cost_center_id)
        );
        
        -- Fields table
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            field_type VARCHAR(50) NOT NULL,
            is_required SMALLINT DEFAULT 0,
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Application Field Values table
        CREATE TABLE IF NOT EXISTS application_field_values (
            id INTEGER NOT NULL PRIMARY KEY,
            application_id INTEGER NOT NULL,
            field_id INTEGER NOT NULL,
            field_value VARCHAR(1000),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id),
            FOREIGN KEY (field_id) REFERENCES fields(id),
            UNIQUE (application_id, field_id)
        );
        
        -- Create generators (sequences) for auto-increment
        CREATE GENERATOR gen_lobs_id;
        CREATE GENERATOR gen_statuses_id;
        CREATE GENERATOR gen_cost_centers_id;
        CREATE GENERATOR gen_users_id;
        CREATE GENERATOR gen_applications_id;
        CREATE GENERATOR gen_user_app_access_id;
        CREATE GENERATOR gen_sto_members_id;
        CREATE GENERATOR gen_fields_id;
        CREATE GENERATOR gen_app_field_values_id;
        
        -- Create triggers for auto-increment
        CREATE OR ALTER TRIGGER tr_lobs_bi FOR lobs
        ACTIVE BEFORE INSERT POSITION 0
        AS BEGIN
            IF (NEW.id IS NULL) THEN
                NEW.id = GEN_ID(gen_lobs_id, 1);
        END;
        
        -- Similar triggers for other tables...
        -- (You'll need to create triggers for each table with auto-increment)
        """
        
        try:
            # Execute schema in smaller chunks for Firebird
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement and not statement.startswith('--'):
                    try:
                        conn.execute_immediate(statement)
                    except Exception as e:
                        # Ignore "already exists" errors
                        if "already exists" not in str(e).lower():
                            print(f"Warning executing statement: {e}")
            
            conn.commit()
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            conn.rollback()
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with retry logic"""
        max_attempts = 3
        attempt = 0
        last_error = None

        while attempt < max_attempts:
            try:
                # Connection parameters for embedded Firebird
                conn = fdb.connect(
                    dsn=str(self.db_path),
                    user='sysdba',
                    password='masterkey',
                    charset='UTF8'
                )
                
                yield conn
                return
                
            except fdb.Error as e:
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
            cursor = conn.cursor()
            cursor.execute(query, (user_sid,))
            columns = [desc[0].lower() for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results

    def is_sto_member(self, user_sid: str, cost_center_id: int) -> bool:
        """Check if a user is an STO member for a cost center"""
        query = '''
            SELECT COUNT(1) 
            FROM sto_members 
            WHERE sid = ? AND cost_center_id = ? AND is_active = 1
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_sid, cost_center_id))
            result = cursor.fetchone()[0]
            return result > 0

    def get_user_cost_center(self, user_sid: str) -> Optional[Dict[str, Any]]:
        """Get user's cost center information"""
        query = '''
            SELECT cc.* 
            FROM cost_centers cc
            JOIN users u ON cc.id = u.cost_center_id
            WHERE u.sid = ? AND u.is_active = 1
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_sid,))
            if cursor.rowcount > 0:
                columns = [desc[0].lower() for desc in cursor.description]
                row = cursor.fetchone()
                return dict(zip(columns, row)) if row else None
            return None

    def grant_application_access(self, user_sid: str, application_id: int, granted_by: str) -> bool:
        """Grant application access to a user"""
        query = '''
            UPDATE OR INSERT INTO user_application_access 
                (user_sid, application_id, granted_by, is_active)
            VALUES (?, ?, ?, 1)
            MATCHING (user_sid, application_id)
        '''
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_sid, application_id, granted_by))
                conn.commit()
                return True
        except fdb.Error as e:
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
            cursor = conn.cursor()
            cursor.execute(query, (application_id,))
            columns = [desc[0].lower() for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results

    def insert_application(self, app_data: Dict[str, Any]) -> Optional[int]:
        """Insert a new application"""
        query = '''
            INSERT INTO applications 
                (name, description, executable_path, lob_id, status_id, cost_center_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            RETURNING id
        '''
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (
                    app_data['name'],
                    app_data.get('description', ''),
                    app_data['executable_path'],
                    app_data['lob_id'],
                    app_data['status_id'],
                    app_data['cost_center_id']
                ))
                app_id = cursor.fetchone()[0]
                conn.commit()
                return app_id
        except fdb.Error as e:
            print(f"Error inserting application: {e}")
            return None

    def update_application_status(self, app_id: int, status_id: int, updated_by: str) -> bool:
        """Update application status"""
        query = '''
            UPDATE applications 
            SET status_id = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
            WHERE id = ?
        '''
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (status_id, updated_by, app_id))
                conn.commit()
                return True
        except fdb.Error as e:
            print(f"Error updating application status: {e}")
            return False

    def bulk_insert_with_transaction(self, table: str, data_list: List[Dict], columns: List[str]) -> bool:
        """Perform bulk insert operations"""
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for data in data_list:
                    values = [data.get(col) for col in columns]
                    cursor.execute(query, values)
                
                conn.commit()
                return True
        except fdb.Error as e:
            print(f"Error in bulk insert: {e}")
            return False

# Usage example:
if __name__ == "__main__":
    # Option 1: Let fdb find fbclient.dll automatically
    db = FirebirdLauncherDB("launcher.fdb")
    
    # Option 2: Specify fbclient.dll path explicitly
    # db = FirebirdLauncherDB("launcher.fdb", r"C:\path\to\firebird\fbclient.dll")
    
    # Test the connection
    try:
        with db.get_connection() as conn:
            print("Successfully connected to Firebird database!")
    except Exception as e:
        print(f"Connection failed: {e}")
