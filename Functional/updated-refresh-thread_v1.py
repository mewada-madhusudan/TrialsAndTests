from PyQt6.QtCore import QThread, pyqtSignal
import time

class RefreshThread(QThread):
    apps_changed = pyqtSignal(list)  # Signal to emit when apps have changed
    sync_status_changed = pyqtSignal(bool, str, str)  # Is synced, local time, source time
    
    def __init__(self, db_path, user_sid, functional_username=None, functional_password=None, refresh_interval=10):
        super().__init__()
        self.db_path = db_path
        self.user_sid = user_sid
        self.functional_username = functional_username
        self.functional_password = functional_password
        self.refresh_interval = refresh_interval  # seconds
        self.last_known_apps = set()
        self.running = True
        
    def run(self):
        from launcher_db import LauncherDB  # Import here to avoid circular imports
        
        # Create a LauncherDB instance with local caching
        db = LauncherDB(
            db_path=self.db_path,
            functional_username=self.functional_username,
            functional_password=self.functional_password
        )
        
        while self.running:
            try:
                # Check sync status first
                is_synced, local_time, source_time = db.check_synced()
                self.sync_status_changed.emit(is_synced, local_time, source_time)
                
                # Force sync if needed - this will pull latest changes from source
                if not is_synced:
                    db.force_sync()
                
                # Get current applications for this user
                current_apps = db.get_user_applications(self.user_sid)
                
                # Convert to a comparable format
                current_apps_set = set()
                for app in current_apps:
                    # Extract fields based on the column order in LauncherDB
                    # This may need adjustment based on actual column order
                    app_id, name, exe_path, description, lob, version, last_updated = app
                    current_apps_set.add((name, description, exe_path, version))
                
                if not self.last_known_apps:
                    # First run, just store the state
                    self.last_known_apps = current_apps_set
                    # On first load, always emit the data
                    self.apps_changed.emit(current_apps)
                elif current_apps_set != self.last_known_apps:
                    # Data has changed, notify the main thread
                    self.last_known_apps = current_apps_set
                    self.apps_changed.emit(current_apps)
            
            except Exception as e:
                print(f"Error in refresh thread: {e}")
                # Sleep a bit on error before retrying
                time.sleep(2)
                continue
                
            # Sleep for the refresh interval
            # Divide into smaller sleeps to allow stopping the thread quickly
            sleep_chunk = 1  # 1 second chunks
            for _ in range(int(self.refresh_interval / sleep_chunk)):
                if not self.running:
                    break
                self.msleep(sleep_chunk * 1000)
    
    def stop(self):
        self.running = False
