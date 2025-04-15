from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QProgressBar, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QObject
import os

class ApplicationTile(QWidget):
    def __init__(self, app_name, app_description, shared_drive_path, app_version=None,
                 db_path=None, functional_username=None, functional_password=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.app_description = app_description
        self.shared_drive_path = shared_drive_path
        self.remote_version = app_version
        self.db_path = db_path
        self.functional_username = functional_username
        self.functional_password = functional_password
        
        # Set local installation path
        appdata = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~/AppData/Local')
        self.install_path = os.path.join(appdata, "LauncherApps", app_name)
        
        # Setup UI
        self.setup_ui()
        
        # Check if app is already installed
        if self.is_app_installed():
            self.installed = True
            self.status_label.setText("Installed")
            self.status_label.setStyleSheet("color: green;")
            self.install_launch_button.setText("Launch")
            
            # Setup the update check thread
            self.update_check_thread = UpdateCheckThread(
                app_name=app_name,
                install_path=self.install_path,
                db_path=self.db_path,
                functional_username=self.functional_username,
                functional_password=self.functional_password
            )
            self.update_check_thread.update_available.connect(self.handle_update_available)
            self.update_check_thread.start()
        else:
            self.installed = False
            self.status_label.setText("Not Installed")
            self.status_label.setStyleSheet("color: red;")
            self.install_launch_button.setText("Install")

    def setup_ui(self):
        # Create layout and components (not shown for brevity)
        layout = QVBoxLayout(self)
        
        # App name label
        self.name_label = QLabel(self.app_name)
        self.name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Description
        self.desc_label = QLabel(self.app_description)
        self.desc_label.setWordWrap(True)
        
        # Status
        self.status_label = QLabel()
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Action button (Install/Launch)
        self.install_launch_button = QPushButton()
        self.install_launch_button.clicked.connect(self.on_button_click)
        
        # Add components to layout
        layout.addWidget(self.name_label)
        layout.addWidget(self.desc_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.install_launch_button)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def is_app_installed(self):
        """Check if the application is installed"""
        executable_path = os.path.join(self.install_path, f"{self.app_name}.exe")
        return os.path.exists(executable_path)
        
    def on_button_click(self):
        """Handle install/launch button click"""
        if self.installed:
            self.launch_application()
        else:
            self.install_application()
            
    def handle_update_available(self, app_name, new_version):
        """Handle update available signal from the thread"""
        self.remote_version = new_version
        self.status_label.setText("Update Available")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
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
                        
    def install_application(self):
        """Install the application from shared drive to local path"""
        # Implementation details for copying files would go here
        # This would use the LauncherDB for accessing the shared drive path
        pass  # Placeholder - implementation would be needed
        
    def installation_finished(self):
        """Called when installation completes"""
        self.installed = True
        self.status_label.setText("Installed")
        self.status_label.setStyleSheet("color: green;")
        self.install_launch_button.setText("Launch")
        self.progress_bar.setVisible(False)
        
        # Save the version information
        if hasattr(self, 'remote_version') and self.remote_version:
            os.makedirs(self.install_path, exist_ok=True)
            version_file = os.path.join(self.install_path, "version.txt")
            with open(version_file, 'w') as f:
                f.write(str(self.remote_version))
        
        QMessageBox.information(self, "Installation Complete", f"{self.app_name} has been successfully installed.")


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
