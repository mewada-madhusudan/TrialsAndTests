# launcher_security.py
import os
import secrets
import time
import json
from pathlib import Path

class LauncherSecurity:
    TOKEN_FILE = "launch_token.json"
    TOKEN_VALIDITY = 30  # seconds
    
    @staticmethod
    def generate_launch_token(app_path):
        """Generate a temporary launch token for an application"""
        token = secrets.token_hex(32)
        timestamp = time.time()
        
        token_data = {
            "token": token,
            "timestamp": timestamp,
            "app_path": str(Path(app_path).resolve())
        }
        
        # Save token to a temporary file
        token_file = Path(os.path.dirname(app_path)) / LauncherSecurity.TOKEN_FILE
        with open(token_file, 'w') as f:
            json.dump(token_data, f)
            
        return token

    @staticmethod
    def verify_launch_token():
        """Verify the launch token for the current process"""
        try:
            # Get the directory of the current executable
            current_dir = Path(os.path.dirname(sys.executable 
                if getattr(sys, 'frozen', False) else __file__))
            token_file = current_dir / LauncherSecurity.TOKEN_FILE
            
            if not token_file.exists():
                return False
                
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                
            # Check token age
            if time.time() - token_data['timestamp'] > LauncherSecurity.TOKEN_VALIDITY:
                return False
                
            # Check if token matches the current executable
            current_path = str(Path(sys.executable 
                if getattr(sys, 'frozen', False) else __file__).resolve())
            if token_data['app_path'] != current_path:
                return False
                
            # Clean up token file
            token_file.unlink()
            return True
            
        except Exception:
            return False

# Modified ApplicationTile class (add to launcherui.py)
def launch_application(self):
    executable_path = os.path.join(self.install_path, f"{self.app_name}.exe")
    if os.path.exists(executable_path):
        try:
            # Generate launch token before starting the application
            LauncherSecurity.generate_launch_token(executable_path)
            os.startfile(executable_path)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to launch application: {str(e)}')
    else:
        QMessageBox.warning(self, 'Error', f'Application executable not found at {executable_path}')

# Example protected application
def main():
    if not LauncherSecurity.verify_launch_token():
        print("Error: This application can only be launched through the authorized launcher.")
        time.sleep(3)  # Give user time to read the message
        sys.exit(1)
        
    # Your actual application code here
    print("Application running...")

if __name__ == "__main__":
    main()
