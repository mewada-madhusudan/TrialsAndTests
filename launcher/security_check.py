import json
import os
import secrets
import sys
import time
import logging
from pathlib import Path


class LauncherSecurity:
    TOKEN_FILE = "launch_token.json"
    TOKEN_VALIDITY = 30  # seconds

    @staticmethod
    def setup_logging():
        """Setup logging for security events"""
        log_dir = Path(os.path.dirname(__file__)) / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            filename=log_dir / "security.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    @staticmethod
    def show_user_error(message):
        """Show user-friendly error message"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Security Error")
            msg.setText(message)
            msg.exec()
        except ImportError:
            print(f"Security Error: {message}")

    @staticmethod
    def log_security_error(message):
        """Log security error for troubleshooting"""
        LauncherSecurity.setup_logging()
        logging.error(message)

    @staticmethod
    def generate_launch_token(app_path):
        """Generate a temporary launch token for an application"""
        try:
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

            LauncherSecurity.log_security_error(f"Launch token generated for: {app_path}")
            return token

        except PermissionError:
            error_msg = "Unable to create security token. Please check file permissions."
            LauncherSecurity.show_user_error(error_msg)
            LauncherSecurity.log_security_error(f"Permission error generating token: {app_path}")
            return None
        except Exception as e:
            error_msg = f"Failed to generate security token: {str(e)}"
            LauncherSecurity.show_user_error(error_msg)
            LauncherSecurity.log_security_error(f"Token generation failed: {str(e)}")
            return None

    @staticmethod
    def verify_launch_token():
        """Verify the launch token for the current process"""
        try:
            # Get the directory of the current executable
            current_dir = Path(os.path.dirname(sys.executable
                                               if getattr(sys, 'frozen', False) else __file__))

            token_file = current_dir / LauncherSecurity.TOKEN_FILE

            if not token_file.exists():
                LauncherSecurity.show_user_error("Security token file not found. Please restart the application.")
                LauncherSecurity.log_security_error("Token file not found during verification")
                return False

            with open(token_file, 'r') as f:
                token_data = json.load(f)

            # Check token age
            if time.time() - token_data['timestamp'] > LauncherSecurity.TOKEN_VALIDITY:
                LauncherSecurity.show_user_error("Security token has expired. Please restart the application.")
                LauncherSecurity.log_security_error("Token expired during verification")
                return False

            # Check if token matches the current executable
            current_path = str(Path(sys.executable
                                    if getattr(sys, 'frozen', False) else __file__).resolve())
            if token_data['app_path'] != current_path:
                LauncherSecurity.show_user_error("Security token mismatch. Please restart the application.")
                LauncherSecurity.log_security_error(
                    f"Token path mismatch: expected {current_path}, got {token_data['app_path']}")
                return False

            # Clean up token file
            token_file.unlink()
            LauncherSecurity.log_security_error("Token verification successful")
            return True

        except FileNotFoundError:
            LauncherSecurity.show_user_error("Security token file not found. Please restart the application.")
            LauncherSecurity.log_security_error("Token file not found during verification")
            return False
        except json.JSONDecodeError:
            LauncherSecurity.show_user_error("Security token corrupted. Please restart the application.")
            LauncherSecurity.log_security_error("Token file corrupted - JSON decode error")
            return False
        except PermissionError:
            LauncherSecurity.show_user_error("Unable to access security token. Please check file permissions.")
            LauncherSecurity.log_security_error("Permission error accessing token file")
            return False
        except Exception as e:
            LauncherSecurity.log_security_error(f"Token verification failed: {str(e)}")
            LauncherSecurity.show_user_error("Security verification failed. Please contact support.")
            return False