import os
import subprocess
import win32net
import win32wnet
from PyQt6.QtCore import QThread, pyqtSignal

class InstallThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, source, destination):
        super().__init__()
        self.source = source
        self.destination = destination
        # Functional account credentials
        self.func_username = "functional_account"  # Replace with actual functional account
        self.func_password = "secure_password"     # Replace with actual password
        self.domain = "DOMAIN"                     # Replace with your domain
        self.network_path = None
        self.current_connection = None

    def connect_network_drive(self):
        try:
            # Construct the full UNC path
            network_path = f"\\\\{self.domain}" + self.source.replace(":", "$")
            
            # Create a connection using the functional account
            win32wnet.WNetAddConnection2(
                0,      # Resource type = disk
                None,   # Local device name (None = no drive mapping)
                network_path,
                None,   # No local device
                f"{self.domain}\\{self.func_username}",
                self.func_password,
                0       # Connection type = permanent
            )
            
            self.network_path = network_path
            self.current_connection = network_path
            return True
            
        except Exception as e:
            self.error.emit(f"Network connection error: {str(e)}")
            return False

    def disconnect_network_drive(self):
        try:
            if self.current_connection:
                win32wnet.WNetCancelConnection2(self.current_connection, 0, 0)
                self.current_connection = None
        except Exception as e:
            print(f"Error disconnecting network drive: {str(e)}")

    def run(self):
        try:
            # Connect to network drive using functional account
            if not self.connect_network_drive():
                return

            if not os.path.exists(self.network_path):
                raise FileNotFoundError(f"Source file not found: {self.network_path}")

            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(self.destination), exist_ok=True)

            # Copy file with progress tracking
            total_size = os.path.getsize(self.network_path)
            copied_size = 0

            with open(self.network_path, 'rb') as src, open(self.destination, 'wb') as dst:
                while True:
                    chunk = src.read(1024 * 1024)  # 1MB chunks for better performance
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied_size += len(chunk)
                    progress = int((copied_size / total_size) * 100)
                    self.progress.emit(progress)

            self.finished.emit()

        except FileNotFoundError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Installation error: {str(e)}")
        finally:
            # Always disconnect from network drive
            self.disconnect_network_drive()

    def __del__(self):
        # Ensure network connection is cleaned up
        self.disconnect_network_drive()
