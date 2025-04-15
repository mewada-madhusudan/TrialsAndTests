from PyQt6.QtCore import QThread, pyqtSignal
import os

class UpdateCheckThread(QThread):
    update_available = pyqtSignal(str, str)  # App name, new version
    
    def __init__(self, app_name, install_path, db_path, functional_username=None, functional_password=None):
        super().__init__()
        self.app_name = app_name
        self.install_path = install_path
        self.db_path = db_path
        self.functional_username = functional_username
        self.functional_password = functional_password
        
    def run(self):
        from launcher_db import LauncherDB  # Import here to avoid circular imports
        
        try:
            # Create a LauncherDB instance with local caching
            db = LauncherDB(
                db_path=self.db_path,
                functional_username=self.functional_username,
                functional_password=self.functional_password
            )
            
            # Query for the application to get its version
            with db.get_connection(read_only=True) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version FROM applications WHERE name = ?", (self.app_name,))
                result = cursor.fetchone()
                remote_version = result[0] if result else None
            
            # Get local version
            local_version = self.get_local_version()
            
            # Check if update is needed
            if remote_version and local_version and local_version != remote_version:
                self.update_available.emit(self.app_name, remote_version)
            elif remote_version and not local_version:
                # If local version file doesn't exist but app is installed, 
                # consider it needs an update
                if os.path.exists(os.path.join(self.install_path, f"{self.app_name}.exe")):
                    self.update_available.emit(self.app_name, remote_version)
                    
        except Exception as e:
            print(f"Error in update check thread: {e}")
    
    def get_local_version(self):
        """Get the installed version from a version file"""
        version_file = os.path.join(self.install_path, "version.txt")
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Error reading version file: {e}")
        return None
