# secure_launcher/security.py
import os
import sys
import time
import json
import hmac
import uuid
import psutil
import socket
import hashlib
import secrets
import threading
import win32api
import win32con
import win32security
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class LauncherSecurityConfig:
    # Security settings
    TOKEN_VALIDITY = 30  # seconds
    HEARTBEAT_INTERVAL = 5  # seconds
    MAX_HEARTBEAT_MISSES = 3
    PORT_RANGE = (49152, 65535)  # Dynamic/private ports
    
    # Encryption keys directory
    KEYS_DIR = Path(os.getenv('APPDATA')) / 'SecureLauncher' / 'keys'
    
    @classmethod
    def initialize(cls):
        """Initialize security configuration and create necessary directories"""
        cls.KEYS_DIR.mkdir(parents=True, exist_ok=True)
        if not (cls.KEYS_DIR / 'private_key.pem').exists():
            cls._generate_keypair()

    @classmethod
    def _generate_keypair(cls):
        """Generate new RSA keypair for the launcher"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Save private key
        with open(cls.KEYS_DIR / 'private_key.pem', 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        with open(cls.KEYS_DIR / 'public_key.pem', 'wb') as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

class ProcessGuard:
    """Monitors and verifies process integrity"""
    
    @staticmethod
    def get_process_chain():
        """Get the process chain from current process to root"""
        process_chain = []
        try:
            current_pid = os.getpid()
            while current_pid != 0:
                process = psutil.Process(current_pid)
                process_info = {
                    'pid': process.pid,
                    'name': process.name(),
                    'exe': process.exe(),
                    'cmdline': process.cmdline(),
                    'create_time': process.create_time()
                }
                process_chain.append(process_info)
                current_pid = process.ppid()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return process_chain

    @staticmethod
    def verify_process_integrity(expected_launcher_path):
        """Verify the process was launched by the correct launcher"""
        process_chain = ProcessGuard.get_process_chain()
        if len(process_chain) < 2:  # Should at least have current process and launcher
            return False
            
        launcher_process = process_chain[1]  # Parent process should be the launcher
        return Path(launcher_process['exe']).resolve() == Path(expected_launcher_path).resolve()

class SecureChannel:
    """Handles secure communication between launcher and application"""
    
    def __init__(self, is_launcher=False):
        self.is_launcher = is_launcher
        self.socket = None
        self.encryption_key = None
        self.fernet = None
        self._initialize_crypto()
        
    def _initialize_crypto(self):
        """Initialize encryption keys and Fernet instance"""
        salt = b'SecureLauncherSalt'  # In production, use a proper secure salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.b64encode(kdf.derive(b'SecureLauncherKey'))  # In production, use a proper secure key
        self.fernet = Fernet(key)
        
    def start_server(self):
        """Start communication server (launcher side)"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = self._find_available_port()
        self.socket.bind(('localhost', port))
        self.socket.listen(1)
        return port
        
    def connect_to_server(self, port):
        """Connect to communication server (application side)"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('localhost', port))
        
    def _find_available_port(self):
        """Find an available port in the specified range"""
        for port in range(LauncherSecurityConfig.PORT_RANGE[0], 
                         LauncherSecurityConfig.PORT_RANGE[1]):
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.bind(('localhost', port))
                test_socket.close()
                return port
            except socket.error:
                continue
        raise RuntimeError("No available ports found")

    def send_message(self, message):
        """Send encrypted message"""
        encrypted_message = self.fernet.encrypt(json.dumps(message).encode())
        self.socket.sendall(encrypted_message + b'\n')
        
    def receive_message(self):
        """Receive and decrypt message"""
        data = self.socket.recv(4096)
        if not data:
            return None
        decrypted_message = self.fernet.decrypt(data.strip())
        return json.loads(decrypted_message)

class LauncherSecurity:
    """Main security manager for the launcher"""
    
    def __init__(self):
        LauncherSecurityConfig.initialize()
        self.secure_channel = SecureChannel(is_launcher=True)
        self.running_applications = {}
        
    def prepare_launch(self, app_path):
        """Prepare for application launch"""
        # Generate unique launch token
        token = secrets.token_hex(32)
        launch_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().timestamp()
        
        # Start communication server
        port = self.secure_channel.start_server()
        
        # Create launch manifest
        manifest = {
            'launch_id': launch_id,
            'token': token,
            'timestamp': timestamp,
            'app_path': str(Path(app_path).resolve()),
            'launcher_path': str(Path(sys.executable).resolve()),
            'port': port
        }
        
        # Sign the manifest
        with open(LauncherSecurityConfig.KEYS_DIR / 'private_key.pem', 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        
        manifest_bytes = json.dumps(manifest).encode()
        signature = private_key.sign(
            manifest_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Save encrypted manifest
        manifest_path = Path(app_path).parent / 'launch_manifest.bin'
        encrypted_data = self.secure_channel.fernet.encrypt(
            json.dumps({
                'manifest': manifest,
                'signature': signature.hex()
            }).encode()
        )
        with open(manifest_path, 'wb') as f:
            f.write(encrypted_data)
            
        return launch_id, manifest_path
        
    def monitor_application(self, launch_id, process):
        """Monitor running application"""
        self.running_applications[launch_id] = {
            'process': process,
            'last_heartbeat': time.time(),
            'missed_heartbeats': 0
        }
        
        def heartbeat_monitor():
            while launch_id in self.running_applications:
                time.sleep(LauncherSecurityConfig.HEARTBEAT_INTERVAL)
                app_info = self.running_applications[launch_id]
                
                if time.time() - app_info['last_heartbeat'] > LauncherSecurityConfig.HEARTBEAT_INTERVAL:
                    app_info['missed_heartbeats'] += 1
                    
                if app_info['missed_heartbeats'] >= LauncherSecurityConfig.MAX_HEARTBEAT_MISSES:
                    print(f"Application {launch_id} failed to respond. Terminating.")
                    process.terminate()
                    del self.running_applications[launch_id]
                    break
                    
        threading.Thread(target=heartbeat_monitor, daemon=True).start()

class ApplicationVerifier:
    """Security verification for launched applications"""
    
    def __init__(self):
        self.secure_channel = SecureChannel(is_launcher=False)
        self.launch_id = None
        self.manifest = None
        
    def verify_launch(self):
        """Verify application launch is authorized"""
        try:
            # Find and decrypt manifest
            manifest_path = Path(sys.executable).parent / 'launch_manifest.bin'
            if not manifest_path.exists():
                return False
                
            with open(manifest_path, 'rb') as f:
                encrypted_data = f.read()
                
            # Decrypt and verify manifest
            decrypted_data = self.secure_channel.fernet.decrypt(encrypted_data)
            data = json.loads(decrypted_data)
            self.manifest = data['manifest']
            signature_bytes = bytes.fromhex(data['signature'])
            
            # Verify signature
            with open(LauncherSecurityConfig.KEYS_DIR / 'public_key.pem', 'rb') as key_file:
                public_key = serialization.load_pem_public_key(key_file.read())
                
            try:
                public_key.verify(
                    signature_bytes,
                    json.dumps(self.manifest).encode(),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            except:
                return False
                
            # Verify timestamp
            if time.time() - self.manifest['timestamp'] > LauncherSecurityConfig.TOKEN_VALIDITY:
                return False
                
            # Verify process integrity
            if not ProcessGuard.verify_process_integrity(self.manifest['launcher_path']):
                return False
                
            # Connect to launcher
            self.secure_channel.connect_to_server(self.manifest['port'])
            self.launch_id = self.manifest['launch_id']
            
            # Start heartbeat
            self._start_heartbeat()
            
            # Clean up manifest
            manifest_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False
            
    def _start_heartbeat(self):
        """Start sending heartbeat to launcher"""
        def heartbeat_sender():
            while True:
                try:
                    self.secure_channel.send_message({
                        'type': 'heartbeat',
                        'launch_id': self.launch_id,
                        'timestamp': time.time()
                    })
                    time.sleep(LauncherSecurityConfig.HEARTBEAT_INTERVAL)
                except:
                    break
                    
        threading.Thread(target=heartbeat_sender, daemon=True).start()

# Example usage in launcher
def launch_application(self):
    executable_path = os.path.join(self.install_path, f"{self.app_name}.exe")
    if os.path.exists(executable_path):
        try:
            security = LauncherSecurity()
            launch_id, manifest_path = security.prepare_launch(executable_path)
            
            # Launch the application
            process = subprocess.Popen([executable_path])
            
            # Start monitoring
            security.monitor_application(launch_id, process)
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to launch application: {str(e)}')
    else:
        QMessageBox.warning(self, 'Error', f'Application executable not found at {executable_path}')

# Example usage in target application
def main():
    verifier = ApplicationVerifier()
    if not verifier.verify_launch():
        print("Error: Unauthorized launch attempt detected.")
        print("This application can only be launched through the authorized launcher.")
        time.sleep(3)
        sys.exit(1)
        
    # Your actual application code here
    print("Application running securely...")

if __name__ == "__main__":
    main()
