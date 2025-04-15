import sqlite3
import time
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
import hashlib

class LauncherDB:
    def __init__(self, db_path, local_cache_dir=None, functional_username=None, functional_password=None, force_local_cache=False):
        """
        Initialize the LauncherDB with options for functional account access and local caching.
        
        Args:
            db_path: Path to the database on the shared drive
            local_cache_dir: Directory to store local cache (defaults to user's appdata)
            functional_username: Username for functional account with shared drive access
            functional_password: Password for functional account
            force_local_cache: If True, always use local cache even if direct access is available
        """
        self.db_path = Path(db_path)
        self.functional_username = functional_username
        self.functional_password = functional_password
        self.force_local_cache = force_local_cache
        
        # Check if we need to use local cache
        self.use_local_cache = force_local_cache or not self._has_direct_access()
        
        # Setup local cache if needed
        if self.use_local_cache:
            if local_cache_dir:
                self.local_cache_dir = Path(local_cache_dir)
            else:
                appdata = os.environ.get('APPDATA') or os.path.expanduser('~/.local/share')
                self.local_cache_dir = Path(appdata) / "LauncherDB" / "cache"
            
            self.local_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate a unique filename based on the original path
            db_name_hash = hashlib.md5(str(db_path).encode()).hexdigest()[:8]
            db_filename = f"{self.db_path.stem}_{db_name_hash}.db"
            self.local_db_path = self.local_cache_dir / db_filename
            
            # Setup metadata file to track last sync
            self.metadata_path = self.local_cache_dir / f"{db_filename}.meta"
        
        # Initialize the database
        self._setup_database()

    def _has_direct_access(self):
        """Check if we can directly access the shared database."""
        try:
            # Try to open the database for reading
            if os.path.exists(self.db_path):
                with open(self.db_path, 'rb') as f:
                    # Just read a small chunk to test access
                    f.read(1)
                return True
        except (PermissionError, FileNotFoundError, OSError):
            pass
        return False

    def _map_network_drive(self):
        """Map the network drive using the functional account credentials."""
        if not self.functional_username or not self.functional_password:
            return False
            
        # Only proceed if we have a UNC path
        if not str(self.db_path).startswith('\\\\'):
            return False
            
        # Extract share path from DB path
        parts = str(self.db_path).split('\\')
        if len(parts) >= 4:
            server = parts[2]
            share = parts[3]
            share_path = f"\\\\{server}\\{share}"
            
            # Find an available drive letter
            for letter in "ZYXWVUTSRQPONMLKJIHGFED":
                if not os.path.exists(f"{letter}:"):
                    drive_letter = f"{letter}:"
                    break
            else:
                return False  # No available drive letters
            
            # Map the drive
            cmd = f'net use {drive_letter} {share_path} /user:{self.functional_username} {self.functional_password} /persistent:no'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Convert the UNC path to mapped drive path
                relative_path = '\\'.join(parts[4:])
                self.mapped_db_path = Path(f"{drive_letter}\\{relative_path}")
                return True
        
        return False

    def _unmap_network_drive(self):
        """Unmap the network drive if one was mapped."""
        if hasattr(self, 'mapped_db_path') and self.mapped_db_path:
            drive_letter = self.mapped_db_path.drive
            if drive_letter:
                subprocess.run(f'net use {drive_letter} /delete /y', shell=True, capture_output=True)

    def _get_source_modified_time(self):
        """Get the last modified time of the source database."""
        try:
            # Try to access the source directly
            if os.path.exists(self.db_path):
                return os.path.getmtime(self.db_path)
            
            # If that fails and we have credentials, try mapping the drive
            if self.functional_username and self._map_network_drive():
                try:
                    if hasattr(self, 'mapped_db_path') and os.path.exists(self.mapped_db_path):
                        return os.path.getmtime(self.mapped_db_path)
                finally:
                    self._unmap_network_drive()
        except Exception as e:
            print(f"Warning: Could not get source modified time: {e}")
        
        # If all fails, return 0 to force a sync check
        return 0

    def _get_last_sync_time(self):
        """Get the last time the local cache was synchronized."""
        if not hasattr(self, 'metadata_path') or not self.metadata_path.exists():
            return 0
            
        try:
            with open(self.metadata_path, 'r') as f:
                return float(f.read().strip())
        except Exception:
            return 0

    def _update_sync_time(self, timestamp=None):
        """Update the last synchronization timestamp."""
        if not hasattr(self, 'metadata_path'):
            return

        if timestamp is None:
            timestamp = time.time()
            
        try:
            with open(self.metadata_path, 'w') as f:
                f.write(str(timestamp))
        except Exception as e:
            print(f"Warning: Could not update sync metadata: {e}")

    def _needs_sync(self):
        """Check if the local database needs to be synchronized with the source."""
        # If not using local cache or local copy doesn't exist, we definitely need to sync
        if not self.use_local_cache:
            return False
        if not hasattr(self, 'local_db_path') or not self.local_db_path.exists():
            return True
            
        # Check if source is newer than our last sync
        source_mtime = self._get_source_modified_time()
        last_sync_time = self._get_last_sync_time()
        
        return source_mtime > last_sync_time

    def _sync_database(self, force=False):
        """Synchronize the local database with the source."""
        if not self.use_local_cache:
            return True
        if not force and not self._needs_sync():
            return True
            
        # Backup current local DB if it exists
        if hasattr(self, 'local_db_path') and self.local_db_path.exists():
            backup_path = self.local_db_path.with_suffix(f".bak-{int(time.time())}")
            try:
                shutil.copy2(self.local_db_path, backup_path)
            except Exception as e:
                print(f"Warning: Could not create backup: {e}")
        
        # Try to copy the source database
        try:
            # Try direct access first
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, self.local_db_path)
                self._update_sync_time(os.path.getmtime(self.db_path))
                return True
                
            # If that fails and we have credentials, try using the functional account
            if self.functional_username and self._map_network_drive():
                try:
                    if hasattr(self, 'mapped_db_path') and os.path.exists(self.mapped_db_path):
                        shutil.copy2(self.mapped_db_path, self.local_db_path)
                        self._update_sync_time(os.path.getmtime(self.mapped_db_path))
                        return True
                finally:
                    self._unmap_network_drive()
                    
            # If we can't access the source and don't have a local copy, create a new DB
            if not self.local_db_path.exists():
                # Create a new empty database
                conn = sqlite3.connect(self.local_db_path)
                conn.close()
                return self._initialize_schema()
                
            return False
                
        except Exception as e:
            print(f"Error syncing database: {e}")
            # If sync fails but we have a backup, restore it
            if 'backup_path' in locals() and os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, self.local_db_path)
                    print(f"Restored database from backup")
                except Exception as restore_error:
                    print(f"Error restoring backup: {restore_error}")
            return False

    def _initialize_schema(self):
        """Initialize the database schema."""
        target_db = self.local_db_path if self.use_local_cache else self.db_path
        
        try:
            conn = sqlite3.connect(target_db, timeout=20)
            try:
                # Enable WAL mode for better concurrent access
                conn.execute('PRAGMA journal_mode=WAL')
                # Set a smaller timeout for busy situations
                conn.execute('PRAGMA busy_timeout=5000')
                # Enable foreign keys
                conn.execute('PRAGMA foreign_keys=ON')
                
                # Create tables if they don't exist
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS applications (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        exe_path TEXT NOT NULL,
                        description TEXT,
                        lob TEXT,
                        version TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS user_access (
                        user_sid TEXT,
                        app_id INTEGER,
                        granted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_sid, app_id),
                        FOREIGN KEY (app_id) REFERENCES applications(id)
                    );

                    -- Add indexes for better performance
                    CREATE INDEX IF NOT EXISTS idx_user_access_sid 
                    ON user_access(user_sid);
                ''')
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            print(f"Error initializing schema: {e}")
            return False

    def _setup_database(self):
        """Set up the database, syncing from source if needed."""
        if self.use_local_cache:
            # Sync the database from source
            self._sync_database(force=True)
        
        # Ensure schema is initialized (for both direct and cached access)
        if not self._initialize_schema():
            raise Exception("Failed to initialize database schema")

    def _connect(self):
        """Create a new database connection with retry logic."""
        max_attempts = 3
        attempt = 0
        last_error = None

        # Sync the database if needed (only applies when using local cache)
        if self.use_local_cache:
            self._sync_database()
            target_db = self.local_db_path
        else:
            target_db = self.db_path
        
        while attempt < max_attempts:
            try:
                conn = sqlite3.connect(target_db, timeout=20)
                conn.execute('PRAGMA foreign_keys=ON')
                return conn
            except sqlite3.OperationalError as e:
                last_error = e
                attempt += 1
                time.sleep(1)  # Wait before retrying
        
        raise ConnectionError(f"Failed to connect to database after {max_attempts} attempts: {last_error}")

    @contextmanager
    def get_connection(self, read_only=False):
        """
        Context manager for database connections with sync capabilities.
        
        Args:
            read_only: If True, won't attempt to push changes back to source
        """
        # Make sure we're working with the latest version if using local cache
        if self.use_local_cache:
            self._sync_database()
        
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    def get_user_applications(self, user_sid):
        """Get all applications available to a user."""
        query = '''
            SELECT a.* FROM applications a
            JOIN user_access ua ON a.id = ua.app_id
            WHERE ua.user_sid = ?
        '''
        
        with self.get_connection(read_only=True) as conn:
            cursor = conn.execute(query, (user_sid,))
            return cursor.fetchall()

    def add_application(self, name, exe_path, description=None, lob=None, version=None):
        """Add a new application."""
        query = '''
            INSERT INTO applications (name, exe_path, description, lob, version)
            VALUES (?, ?, ?, ?, ?)
        '''
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, (name, exe_path, description, lob, version))
            conn.commit()
            return cursor.lastrowid

    def grant_access(self, user_sid, app_id):
        """Grant access to a user for an application."""
        query = '''
            INSERT OR IGNORE INTO user_access (user_sid, app_id)
            VALUES (?, ?)
        '''
        
        with self.get_connection() as conn:
            conn.execute(query, (user_sid, app_id))
            conn.commit()
            
    def check_synced(self):
        """
        Check if the local cache is in sync with the source database.
        Returns: (is_synced, local_time, source_time) or None if not using local cache
        """
        if not self.use_local_cache:
            return None
            
        source_time = self._get_source_modified_time()
        local_time = self._get_last_sync_time()
        is_synced = source_time <= local_time
        
        return (is_synced, 
                datetime.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S') if local_time else "Never",
                datetime.fromtimestamp(source_time).strftime('%Y-%m-%d %H:%M:%S') if source_time else "Unknown")
                
    def force_sync(self):
        """Force synchronization with the source database."""
        if not self.use_local_cache:
            return False  # No need to sync when using source directly
        return self._sync_database(force=True)
        
    def is_using_local_cache(self):
        """Return whether we're using local cache or direct access."""
        return self.use_local_cache
