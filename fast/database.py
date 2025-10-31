import sqlite3
import json
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DATABASE_URL = "cardholder_management.db"

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Create ROLE_DELEGATIONS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_delegations (
            delegation_id TEXT PRIMARY KEY,
            delegator_sid TEXT NOT NULL,
            delegate_sid TEXT NOT NULL,
            role_id TEXT NOT NULL,
            effective_from DATE NOT NULL,
            effective_to DATE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create DATA_UPLOADS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_uploads (
            upload_id TEXT PRIMARY KEY,
            quarter_id TEXT NOT NULL,
            uploaded_by TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            upload_status TEXT DEFAULT 'processing',
            records_count INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        )
    ''')
    
    # Create CARDHOLDER_DATA table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cardholder_data (
            record_id TEXT PRIMARY KEY,
            upload_id TEXT NOT NULL,
            quarter_id TEXT NOT NULL,
            certifier_id TEXT NOT NULL,
            area_owner_sid TEXT,
            area_owner_name TEXT,
            area_name TEXT,
            employee_sid TEXT,
            employee_name TEXT,
            team TEXT,
            access_to_area_allowed BOOLEAN,
            region TEXT,
            country_name TEXT,
            city TEXT,
            access_type TEXT,
            access_from_date DATE,
            access_to_date DATE,
            public_private_designation TEXT,
            cost_center_code_department_id TEXT,
            cost_center_name_department_name TEXT,
            csh_level_5_name TEXT,
            csh_level_6_name TEXT,
            csh_level_7_name TEXT,
            csh_level_8_name TEXT,
            csh_level_9_name TEXT,
            csh_level_10_name TEXT,
            process_owner_status TEXT DEFAULT 'pending_review',
            area_owner_status TEXT DEFAULT 'pending_confirmation',
            certifier_status TEXT DEFAULT 'pending_review',
            process_owner_comment TEXT,
            area_owner_comment TEXT,
            certifier_comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            history TEXT
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cardholder_quarter ON cardholder_data(quarter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cardholder_certifier ON cardholder_data(certifier_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cardholder_upload ON cardholder_data(upload_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_delegations_active ON role_delegations(is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_delegations_role ON role_delegations(role_id)')
    
    conn.commit()
    conn.close()

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # This allows dict-like access to rows
    try:
        yield conn
    finally:
        conn.close()

class DatabaseManager:
    @staticmethod
    def create_role_delegation(delegation_data: Dict[str, Any]) -> str:
        """Create a new role delegation"""
        delegation_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO role_delegations 
                (delegation_id, delegator_sid, delegate_sid, role_id, effective_from, effective_to, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                delegation_id,
                delegation_data['delegator_sid'],
                delegation_data['delegate_sid'],
                delegation_data['role_id'],
                delegation_data['effective_from'],
                delegation_data['effective_to'],
                delegation_data.get('is_active', True)
            ))
            conn.commit()
        
        return delegation_id
    
    @staticmethod
    def get_role_delegations(is_active: Optional[bool] = None, role_id: Optional[str] = None) -> List[Dict]:
        """Fetch role delegations with optional filters"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM role_delegations WHERE 1=1"
            params = []
            
            if is_active is not None:
                query += " AND is_active = ?"
                params.append(is_active)
            
            if role_id:
                query += " AND role_id = ?"
                params.append(role_id)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def create_data_upload(upload_data: Dict[str, Any]) -> str:
        """Create a new data upload record"""
        upload_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO data_uploads 
                (upload_id, quarter_id, uploaded_by, file_name, file_path, file_size, upload_status, records_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                upload_id,
                upload_data['quarter_id'],
                upload_data['uploaded_by'],
                upload_data['file_name'],
                upload_data['file_path'],
                upload_data['file_size'],
                upload_data.get('upload_status', 'processing'),
                upload_data.get('records_count', 0)
            ))
            conn.commit()
        
        return upload_id
    
    @staticmethod
    def update_upload_status(upload_id: str, status: str, records_count: int):
        """Update upload status and record count"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE data_uploads 
                SET upload_status = ?, records_count = ?, processed_at = CURRENT_TIMESTAMP
                WHERE upload_id = ?
            ''', (status, records_count, upload_id))
            conn.commit()
    
    @staticmethod
    def create_cardholder_record(record_data: Dict[str, Any]) -> str:
        """Create a new cardholder data record"""
        record_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cardholder_data (
                    record_id, upload_id, quarter_id, certifier_id, area_owner_sid, area_owner_name,
                    area_name, employee_sid, employee_name, team, access_to_area_allowed, region,
                    country_name, city, access_type, access_from_date, access_to_date,
                    public_private_designation, cost_center_code_department_id, cost_center_name_department_name,
                    csh_level_5_name, csh_level_6_name, csh_level_7_name, csh_level_8_name,
                    csh_level_9_name, csh_level_10_name, process_owner_status, area_owner_status,
                    certifier_status, history
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record_id, record_data['upload_id'], record_data['quarter_id'], record_data['certifier_id'],
                record_data.get('area_owner_sid'), record_data.get('area_owner_name'),
                record_data.get('area_name'), record_data.get('employee_sid'), record_data.get('employee_name'),
                record_data.get('team'), record_data.get('access_to_area_allowed'), record_data.get('region'),
                record_data.get('country_name'), record_data.get('city'), record_data.get('access_type'),
                record_data.get('access_from_date'), record_data.get('access_to_date'),
                record_data.get('public_private_designation'), record_data.get('cost_center_code_department_id'),
                record_data.get('cost_center_name_department_name'), record_data.get('csh_level_5_name'),
                record_data.get('csh_level_6_name'), record_data.get('csh_level_7_name'), record_data.get('csh_level_8_name'),
                record_data.get('csh_level_9_name'), record_data.get('csh_level_10_name'),
                record_data.get('process_owner_status', 'pending_review'),
                record_data.get('area_owner_status', 'pending_confirmation'),
                record_data.get('certifier_status', 'pending_review'),
                record_data.get('history')
            ))
            conn.commit()
        
        return record_id
    
    @staticmethod
    def get_cardholder_records(quarter_id: Optional[str] = None, certifier_id: Optional[str] = None, 
                              status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Fetch cardholder records with optional filters"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM cardholder_data WHERE 1=1"
            params = []
            
            if quarter_id:
                query += " AND quarter_id = ?"
                params.append(quarter_id)
            
            if certifier_id:
                query += " AND certifier_id = ?"
                params.append(certifier_id)
            
            if status:
                query += " AND (process_owner_status = ? OR area_owner_status = ? OR certifier_status = ?)"
                params.extend([status, status, status])
            
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update_cardholder_record(record_id: str, update_data: Dict[str, Any], updated_by: str):
        """Update a cardholder record"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # First, get the current record to track changes
            cursor.execute("SELECT * FROM cardholder_data WHERE record_id = ?", (record_id,))
            current_record = dict(cursor.fetchone())
            
            # Build update query dynamically
            update_fields = []
            params = []
            changes = {}
            
            for field, new_value in update_data.items():
                if field != 'record_id' and field in current_record:
                    old_value = current_record[field]
                    if old_value != new_value:
                        update_fields.append(f"{field} = ?")
                        params.append(new_value)
                        changes[field] = {"old": old_value, "new": new_value}
            
            if update_fields:
                # Update history
                history = json.loads(current_record['history']) if current_record['history'] else []
                history.append({
                    "action": "updated",
                    "timestamp": datetime.now().isoformat(),
                    "user": updated_by,
                    "changes": changes
                })
                
                update_fields.append("history = ?")
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(json.dumps(history))
                params.append(record_id)
                
                query = f"UPDATE cardholder_data SET {', '.join(update_fields)} WHERE record_id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                return True
            
            return False
    
    @staticmethod
    def get_records_for_report(start_date: date, end_date: date, quarter_id: Optional[str] = None,
                              status_filter: Optional[str] = None, certifier_id: Optional[str] = None) -> List[Dict]:
        """Get records for report generation"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM cardholder_data WHERE created_at BETWEEN ? AND ?"
            params = [start_date, end_date]
            
            if quarter_id:
                query += " AND quarter_id = ?"
                params.append(quarter_id)
            
            if certifier_id:
                query += " AND certifier_id = ?"
                params.append(certifier_id)
            
            if status_filter:
                query += " AND (process_owner_status = ? OR area_owner_status = ? OR certifier_status = ?)"
                params.extend([status_filter, status_filter, status_filter])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_status_counts(quarter_id: Optional[str] = None) -> Dict[str, Dict[str, int]]:
        """Get status counts for all status types"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT process_owner_status, area_owner_status, certifier_status FROM cardholder_data"
            params = []
            
            if quarter_id:
                query += " WHERE quarter_id = ?"
                params.append(quarter_id)
            
            cursor.execute(query, params)
            records = cursor.fetchall()
            
            process_owner_counts = {}
            area_owner_counts = {}
            certifier_counts = {}
            
            for record in records:
                # Process Owner Status
                po_status = record['process_owner_status']
                process_owner_counts[po_status] = process_owner_counts.get(po_status, 0) + 1
                
                # Area Owner Status
                ao_status = record['area_owner_status']
                area_owner_counts[ao_status] = area_owner_counts.get(ao_status, 0) + 1
                
                # Certifier Status
                cert_status = record['certifier_status']
                certifier_counts[cert_status] = certifier_counts.get(cert_status, 0) + 1
            
            return {
                "process_owner": process_owner_counts,
                "area_owner": area_owner_counts,
                "certifier": certifier_counts
            }

# Initialize database on import
init_database()
