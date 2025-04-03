1. Auto-refresh in a background thread
from PyQt6.QtCore import QTimer, QThread, pyqtSignal

class RefreshThread(QThread):
    apps_changed = pyqtSignal(list)  # Signal to emit when apps have changed
    
    def __init__(self, db_path, username):
        super().__init__()
        self.db_path = db_path
        self.username = username
        self.last_known_apps = set()
        self.running = True
        
    def run(self):
        while self.running:
            # Create a new database connection in this thread
            db = Database(self.db_path)
            current_apps = db.get_user_applications(self.username)
            current_apps_set = set((name, desc, path) for name, desc, path in current_apps)
            
            if not self.last_known_apps:
                # First run, just store the state
                self.last_known_apps = current_apps_set
            elif current_apps_set != self.last_known_apps:
                # Data has changed, notify the main thread
                self.last_known_apps = current_apps_set
                self.apps_changed.emit(current_apps)
            
            db.close()
            # Sleep for 10 seconds
            for _ in range(10):
                if not self.running:
                    break
                self.msleep(1000)  # Sleep in small chunks to allow stopping the thread quickly
    
    def stop(self):
        self.running = False

Now, let's modify the MainWindow to use this thread:
# In MainWindow class:
def __init__(self):
    # ... existing code ...
    
    # Set up background refresh thread
    self.refresh_thread = RefreshThread("launcher.db", self.username)
    self.refresh_thread.apps_changed.connect(self.handle_apps_changed)
    self.refresh_thread.start()

def handle_apps_changed(self, new_apps):
    """Handle applications list changes from the refresh thread"""
    self.clear_application_grid()
    
    # Reload the applications grid with new data
    for i, (name, desc, shared_path) in enumerate(new_apps):
        tile = ApplicationTile(name, desc, shared_path)
        self.app_grid.addWidget(tile, i // 3, i % 3)
    
    self.adjust_tile_sizes()
    
    # Notify the user about the change
    QMessageBox.information(self, "Applications Updated", 
                           "Your available applications have been updated.")

def closeEvent(self, event):
    """Stop the refresh thread when closing the application"""
    self.refresh_thread.stop()
    self.refresh_thread.wait()  # Wait for the thread to finish
    event.accept()



2. Application update in a background thread
Let's create another thread for checking and handling application updates:
class UpdateCheckThread(QThread):
    update_available = pyqtSignal(str, str)  # App name, new version
    
    def __init__(self, app_name, install_path, db_path):
        super().__init__()
        self.app_name = app_name
        self.install_path = install_path
        self.db_path = db_path
        
    def run(self):
        # Connect to database to get remote version
        db = Database(self.db_path)
        remote_version = db.get_application_version(self.app_name)
        db.close()
        
        # Get local version
        local_version = self.get_local_version()
        
        # Check if update is needed
        if remote_version and local_version != remote_version:
            self.update_available.emit(self.app_name, remote_version)
    
    def get_local_version(self):
        """Get the installed version from a version file"""
        version_file = os.path.join(self.install_path, "version.txt")
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
        return None

Now, let's modify the ApplicationTile class to use threading for updates:

# In ApplicationTile class:
def __init__(self, app_name, app_description, shared_drive_path, parent=None):
    # ... existing code ...
    
    # Setup the update check thread
    self.update_check_thread = UpdateCheckThread(app_name, self.install_path, "launcher.db")
    self.update_check_thread.update_available.connect(self.handle_update_available)
    
    # Start the update check if app is installed
    if self.is_app_installed(f'{self.install_path}.exe'):
        self.update_check_thread.start()

def handle_update_available(self, app_name, new_version):
    """Handle update available signal from the thread"""
    self.remote_version = new_version
    self.status_label.setText("Update Available")
    self.status_label.setStyleSheet("color: orange; font-weight: bold; margin-top: 5px;")

def launch_application(self):
    """Launch the application, checking for updates first"""
    executable_path = os.path.join(self.install_path, f"{self.app_name}.exe")
    
    # Check if update is needed based on status
    if self.status_label.text() == "Update Available":
        # Use a separate thread for closing the application
        self.close_thread = QThread()
        self.close_worker = ForceCloseWorker(self.app_name)
        self.close_worker.moveToThread(self.close_thread)
        self.close_thread.started.connect(self.close_worker.close_app)
        self.close_worker.closed.connect(self.handle_app_closed)
        self.close_worker.closed.connect(self.close_thread.quit)
        self.close_thread.start()
    else:
        # Continue with normal launch
        if os.path.exists(executable_path):
            try:
                os.startfile(executable_path)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to launch application: {str(e)}')
        else:
            QMessageBox.warning(self, 'Error', f'Application executable not found at {executable_path}')

def handle_app_closed(self, success):
    """Handle when an app has been closed for updating"""
    if success:
        reply = QMessageBox.question(self, "Update Available", 
                               f"A new version of {self.app_name} is available. Would you like to update now?",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
        if reply == QMessageBox.StandardButton.Yes:
            self.install_application()
        else:
            # User declined update, launch anyway
            executable_path = os.path.join(self.install_path, f"{self.app_name}.exe")
            if os.path.exists(executable_path):
                try:
                    os.startfile(executable_path)
                except Exception as e:
                    QMessageBox.critical(self, 'Error', f'Failed to launch application: {str(e)}')


Let's also create a worker class for force closing applications:

class ForceCloseWorker(QObject):
    closed = pyqtSignal(bool)  # Signal to indicate completion and success
    
    def __init__(self, app_name):
        super().__init__()
        self.app_name = app_name
        
    def close_app(self):
        """Force close any running instance of the application"""
        import subprocess
        import psutil
        
        app_process_name = f"{self.app_name}.exe"
        success = False
        
        # Find and kill the process
        for process in psutil.process_iter(['pid', 'name']):
            try:
                if process.info['name'] == app_process_name:
                    # Found the process, terminate it
                    subprocess.call(['taskkill', '/F', '/PID', str(process.info['pid'])])
                    success = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Emit signal indicating whether we successfully closed anything
        self.closed.emit(success)


Adding the version tracking functionality
For the Database class, we need to add the version tracking functionality:
pythonCopy# Add to Database class:
def get_application_version(self, app_name):
    """Get the latest version of an application"""
    self.cursor.execute("""
        SELECT version FROM applications
        WHERE name = ?
    """, (app_name,))
    result = self.cursor.fetchone()
    return result[0] if result else None
Installation finished method update
Don't forget to update the installation_finished method to save the version information:
pythonCopydef installation_finished(self):
    self.installed = True
    self.status_label.setText("Installed")
    self.status_label.setStyleSheet("color: green;")
    self.install_launch_button.setText("Launch")
    self.progress_bar.setVisible(False)
    
    # Save the version information
    if hasattr(self, 'remote_version') and self.remote_version:
        version_file = os.path.join(self.install_path, "version.txt")
        with open(version_file, 'w') as f:
            f.write(str(self.remote_version))
    
    QMessageBox.information(self, "Installation Complete", f"{self.app_name} has been successfully installed.")
Summary of changes

Added a RefreshThread class to check for application changes in the background
Added an UpdateCheckThread class to check for application updates in the background
Added a ForceCloseWorker class to handle closing applications in a separate thread
Modified the MainWindow and ApplicationTile classes to use these threads
Made sure database connections are properly closed in each thread
Added proper cleanup when closing the application

These changes will keep the UI responsive while performing background tasks, and users will still be able to interact with the launcher while updates and refreshes happen in the background
