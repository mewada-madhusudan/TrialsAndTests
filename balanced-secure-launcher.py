# launcher_security.py
import os
import sys
import time
import json
import hmac
import uuid
import psutil
import socket
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
from base64 import b64encode, b64decode

class LauncherSecurity:
    """Security manager for the launcher application"""
    
    # Security configuration
    TOKEN_VALIDITY = 30  # seconds
    SECRET_KEY = b"your-secret-key-here"  # Change this in production
    VERIFICATION_PORT = 55555  # Choose an appropriate port
    
    def __init__(self):
        self.fernet = Fernet(b64encode(hmac.new(self.SECRET_KEY, b"ENCRYPTION_KEY", "sha256").digest()))
        self.running_apps = {}
        
    def prepare_launch(self, app_path):
        """Prepare application for secure launch"""
        launch_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().timestamp()
        
        # Create launch manifest
        manifest = {
            'launch_id': launch_id,
            'timestamp': timestamp,
            'app_path': str(Path(app_path).resolve()),
            'launcher_pid': os.getpid(),
            'verification_port': self.VERIFICATION_PORT
        }
        
        # Encrypt manifest
        encrypted_manifest = self.fernet.encrypt(json.dumps(manifest).encode())
        
        # Save encrypted manifest
        manifest_path = Path(app_path).parent / 'launch_manifest.bin'
        with open(manifest_path, 'wb') as f:
            f.write(encrypted_manifest)
        
        # Start verification server if not already running
        self._ensure_verification_server()
        
        return launch_id, manifest_path
    
    def _ensure_verification_server(self):
        """Ensure the verification server is running"""
        if not hasattr(self, 'server_socket'):
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('localhost', self.VERIFICATION_PORT))
            self.server_socket.listen(5)
            
            # Start accepting connections in a separate thread
            import threading
            thread = threading.Thread(target=self._accept_connections, daemon=True)
            thread.start()
    
    def _accept_connections(self):
        """Accept and verify connections from launched applications"""
        while True:
            try:
                client, addr = self.server_socket.accept()
                data = client.recv(1024)
                if data:
                    try:
                        # Decrypt and verify the launch ID
                        decrypted_data = self.fernet.decrypt(data)
                        verify_data = json.loads(decrypted_data)
                        launch_id = verify_data.get('launch_id')
                        
                        if launch_id in self.running_apps:
                            # Send success response
                            client.send(self.fernet.encrypt(b'OK'))
                        else:
                            client.send(self.fernet.encrypt(b'FAIL'))
                    except:
                        client.send(self.fernet.encrypt(b'FAIL'))
                client.close()
            except:
                continue

class ApplicationVerifier:
    """Security verification for launched applications"""
    
    def __init__(self):
        self.manifest = None
        self.fernet = None
    
    def verify_launch(self):
        """Verify that the application was launched correctly"""
        try:
            # Find and load manifest
            manifest_path = Path(sys.executable if getattr(sys, 'frozen', False) else __file__).parent / 'launch_manifest.bin'
            if not manifest_path.exists():
                return False
            
            # Read and decrypt manifest
            with open(manifest_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Initialize Fernet with the same key as launcher
            self.fernet = Fernet(b64encode(hmac.new(LauncherSecurity.SECRET_KEY, b"ENCRYPTION_KEY", "sha256").digest()))
            
            # Decrypt manifest
            decrypted_data = self.fernet.decrypt(encrypted_data)
            self.manifest = json.loads(decrypted_data)
            
            # Verify timestamp
            if time.time() - self.manifest['timestamp'] > LauncherSecurity.TOKEN_VALIDITY:
                return False
            
            # Verify launcher is running
            if not self._verify_launcher():
                return False
            
            # Verify with launcher server
            if not self._verify_with_server():
                return False
            
            # Clean up manifest
            manifest_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def _verify_launcher(self):
        """Verify the launcher process is running"""
        try:
            launcher_pid = self.manifest['launcher_pid']
            launcher_process = psutil.Process(launcher_pid)
            return launcher_process.is_running()
        except:
            return False
    
    def _verify_with_server(self):
        """Verify launch with the launcher's verification server"""
        try:
            # Connect to verification server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', self.manifest['verification_port']))
            
            # Send verification request
            verify_data = {
                'launch_id': self.manifest['launch_id'],
                'app_path': str(Path(sys.executable if getattr(sys, 'frozen', False) else __file__).resolve())
            }
            sock.send(self.fernet.encrypt(json.dumps(verify_data).encode()))
            
            # Get response
            response = self.fernet.decrypt(sock.recv(1024))
            sock.close()
            
            return response == b'OK'
        except:
            return False

# Modified ApplicationTile launch method (add to launcherui.py)
def launch_application(self):
    executable_path = os.path.join(self.install_path, f"{self.app_name}.exe")
    if os.path.exists(executable_path):
        try:
            # Initialize security
            security = LauncherSecurity()
            
            # Prepare launch
            launch_id, manifest_path = security.prepare_launch(executable_path)
            
            # Track this launch
            security.running_apps[launch_id] = {
                'path': executable_path,
                'launch_time': time.time()
            }
            
            # Launch the application
            os.startfile(executable_path)
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to launch application: {str(e)}')
    else:
        QMessageBox.warning(self, 'Error', f'Application executable not found at {executable_path}')

# Example protected application code
def main():
    verifier = ApplicationVerifier()
    if not verifier.verify_launch():
        print("Error: This application can only be launched through the authorized launcher.")
        print("Unauthorized launch attempt detected.")
        time.sleep(3)
        sys.exit(1)
    
    # Your actual application code here
    print("Application running with verified launch...")

if __name__ == "__main__":
    main()
