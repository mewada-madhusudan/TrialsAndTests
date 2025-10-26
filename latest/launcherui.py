"""
Solution Launcher Window - Updated UI
================================================================================
This Module contains the updated code with modern dark theme UI matching the new design.
"""

import datetime
# Python default package imports
import getpass
import os
import shutil
from datetime import datetime

# Python third party package imports
# import awmpy
import pandas as pd
import timedelta
import urllib3
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGridLayout, QFrame, QProgressBar, QScrollArea,
                             QStackedLayout, QMenu, QStackedWidget, QDialog, QButtonGroup)
from requests_ntlm import HttpNtlmAuth
from shareplum import Site

# User created module for functionalities
from access import AccessControlDialog
from security_check import LauncherSecurity
from static import resource_path, APP_DIR, expire_sort, DETAILS, SITE_URL, SID, SHAREPOINT_LIST, \
    BACKUP_FILE_NAME, BACKUP_PATH, ADMIN, add_new_user_to_userbase

# global variable for user id
user_main = getpass.getuser()

# FIXED Modern Dark Theme Colors - Much stronger contrast and better visibility
COLORS = {
    'background_dark': '#0d1117',
    'surface_dark': '#161b22',
    'tile_background': '#21262d',  # Better contrast - lighter than surface
    'tile_hover': '#30363d',  # Even lighter for hover
    'border_dark': '#30363d',
    'border_light': '#484f58',
    'primary': '#238be6',  # Slightly brighter blue
    'text_light': '#f0f6fc',  # Brighter white
    'text_medium': '#c9d1d9',  # Medium gray for better readability
    'text_dark': '#8b949e',  # Darker gray for secondary text
    'uat_bg': 'rgba(234, 179, 8, 0.2)',
    'uat_text': '#eab308',
    'beta_bg': 'rgba(59, 130, 246, 0.2)',
    'beta_text': '#3b82f6',
    'prod_bg': 'rgba(34, 197, 94, 0.2)',
    'prod_text': '#22c55e',
    'green_status': '#22c55e',
    'red_status': '#ef4444',
    'progress_bg': '#30363d',
    'progress_fill': '#238be6',
}


class EnvironmentLabel(QLabel):
    """FIXED environment badge with better contrast"""

    def __init__(self, env_type, parent=None):
        if len(env_type) > 4:
            env_type = env_type[:4]
        super().__init__(env_type, parent)
        self.env_type = env_type
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # FIXED: Better color scheme for environment badges
        if env_type == "PROD":
            bg_color = COLORS['prod_text']
            text_color = 'white'
        elif env_type == "UAT":
            bg_color = COLORS['uat_text']
            text_color = 'white'
        else:  # BETA
            bg_color = COLORS['beta_text']
            text_color = 'white'

        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            border-radius: 10px;
            padding: 3px 8px;
            font-size: 9px;
            font-weight: bold;
            font-family: Inter, sans-serif;
            border: none;
        """)
        self.setFixedHeight(18)
        self.setFixedWidth(45)


class InstallThread(QThread):
    """Thread for handling installation"""

    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, source, destination):
        super().__init__()
        self.source = source
        self.destination = destination

    def run(self):
        try:
            if not os.path.exists(self.source):
                raise FileNotFoundError(f"Source file not found: {self.source}")

            total_size = os.path.getsize(self.source)
            copied_size = 0
            with open(self.source, 'rb') as src, open(self.destination, 'wb') as dst:
                while True:
                    chunk = src.read(1024)
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


# FIXED: Custom MessageBox with proper styling and no title bar
class CustomMessageBox(QDialog):
    """Custom message box with no title bar, centered, and proper contrast"""

    def __init__(self, parent=None, title="", message="", icon_type="info"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setupUI(title, message, icon_type)

        # FIXED: Delay the centering to ensure parent geometry is properly set
        if parent:
            # Use QTimer to delay centering until after the parent is fully rendered
            QTimer.singleShot(0, self.center_on_parent_delayed)
        else:
            self.center_on_screen()

    def setupUI(self, title, message, icon_type):
        # FIXED: Dynamic sizing based on content
        base_width = 450
        base_height = 200

        # Calculate height based on message length and line breaks
        line_count = message.count('\n') + 1
        if len(message) > 100:
            line_count += len(message) // 50  # Add lines for long text

        # Adjust height based on content
        content_height = max(base_height, 150 + (line_count * 20))
        if title:
            content_height += 30

        self.setFixedSize(base_width, content_height)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['tile_background']};
                border: 2px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Icon and title
        if icon_type == "error":
            icon_text = "❌"
            title_color = COLORS['red_status']
        elif icon_type == "warning":
            icon_text = "⚠️"
            title_color = COLORS['uat_text']
        elif icon_type == "info":
            icon_text = "ℹ️"
            title_color = COLORS['primary']
        else:
            icon_text = "✅"
            title_color = COLORS['green_status']

        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("font-size: 32px; border: none;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {title_color};
                font-family: Inter, sans-serif;
                border: none;
                margin: 0px;
                padding: 0px;
            """)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setWordWrap(True)
            layout.addWidget(title_label)

        # Message with FIXED contrast - dark text on light background
        message_label = QLabel(message)
        message_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_light']};
            font-family: Inter, sans-serif;
            border: none;
            margin: 0px;
            padding: 8px;
            background-color: transparent;
            line-height: 1.4;
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        # FIXED: Allow the label to expand to show full content
        message_label.setMinimumHeight(50)
        message_label.adjustSize()
        layout.addWidget(message_label)

        # Add stretch to push button to bottom
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                font-family: Inter, sans-serif;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: rgba(35, 139, 230, 0.8);
            }}
        """)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def center_on_parent_delayed(self):
        """FIXED: Delayed centering with proper geometry validation"""
        if self.parent():
            # Ensure the parent widget is visible and has proper geometry
            parent = self.parent()

            # Wait for parent to be properly shown and positioned
            if hasattr(parent, 'isVisible') and parent.isVisible():
                parent_rect = parent.geometry()

                # FIXED: Validate that parent has proper geometry (not 0,0,x,y)
                if parent_rect.x() == 0 and parent_rect.y() == 0:
                    # If parent geometry is still not set, try to get the window geometry
                    if hasattr(parent, 'window'):
                        window = parent.window()
                        if window and window != parent:
                            parent_rect = window.geometry()

                    # If still at 0,0, center on screen instead
                    if parent_rect.x() == 0 and parent_rect.y() == 0:
                        self.center_on_screen()
                        return

                # Calculate center position
                x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
                y = parent_rect.y() + (parent_rect.height() - self.height()) // 2

                # Ensure the dialog stays within screen bounds
                screen = self.screen().geometry() if self.screen() else None
                if screen:
                    x = max(0, min(x, screen.width() - self.width()))
                    y = max(0, min(y, screen.height() - self.height()))

                self.move(x, y)
            else:
                # Parent not visible yet, try again after a short delay
                QTimer.singleShot(50, self.center_on_parent_delayed)
        else:
            self.center_on_screen()

    def center_on_screen(self):
        """Center the dialog on screen"""
        screen = self.screen().geometry() if self.screen() else None
        if screen:
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)


class ApplicationTile(QFrame):
    """Modern application tile with STRONG contrast and NO BORDERS"""

    def __init__(self, app_name, app_description, shared_drive_path, environment,
                 release_date, validity_period, version_number, registration_id, parent=None):
        super().__init__(parent)

        # Store all the data
        self.app_name = app_name
        self.app_description = app_description
        self.shared_drive_path = shared_drive_path
        self.environment = environment
        self.release_date = release_date
        self.validity_period = validity_period
        self.version_number = version_number
        self.registration_id = registration_id

        # Set up paths
        self.install_path = os.environ.get('USERPROFILE')
        self.install_path = os.path.join(f"{self.install_path}\\{APP_DIR}", app_name)

        # Initialize version tracking
        self.installed_version = self.get_installed_version()
        self.installed = self.is_app_installed(f"{self.install_path}" + "\\" + f"{self.app_name}.exe")

        # Check status
        self.is_expired = self.check_validity()
        self.update_available = self.check_update_available()

        # Initialize flip state
        self.is_flipped = False

        # Create both sides
        self.front_widget = QWidget()
        self.back_widget = QWidget()
        self.stacked_layout = QStackedLayout(self)

        self.setup_front_ui()
        self.setup_back_ui()

        self.stacked_layout.addWidget(self.front_widget)
        self.stacked_layout.addWidget(self.back_widget)

        # Set context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # FIXED: Better sizing and styling
        self.setFixedHeight(200)
        self.setFixedWidth(300)
        self.setup_styles()

        # Add overlay if expired
        if self.is_expired:
            self.add_expired_overlay()

    def setup_styles(self):
        """FIXED: Apply better styling with proper contrast"""
        self.setStyleSheet(f"""
            ApplicationTile {{
                background-color: {COLORS['tile_background']};
                border-radius: 12px;
                border: 1px solid {COLORS['border_dark']};
                margin: 2px;
            }}
            ApplicationTile:hover {{
                background-color: {COLORS['tile_hover']};
                border: 1px solid {COLORS['primary']};
            }}
        """)

    def setup_front_ui(self):
        """FIXED: Setup front side with proper spacing and no overlapping"""
        layout = QVBoxLayout(self.front_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # FIXED: Apply consistent background styling
        self.front_widget.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border: none;
            }}
        """)

        # FIXED: Header with proper spacing
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.env_label = EnvironmentLabel(self.environment)
        header_layout.addWidget(self.env_label)
        header_layout.addStretch()

        # FIXED: Status indicator with better styling
        self.status_indicator = QLabel("Not Installed")
        self.status_indicator.setStyleSheet(f"""
            color: {COLORS['text_dark']};
            font-size: 10px;
            font-weight: 600;
            font-family: Inter, sans-serif;
            border: none;
            padding: 0px;
        """)
        header_layout.addWidget(self.status_indicator)
        layout.addLayout(header_layout)

        # FIXED: App name with better sizing
        self.name_label = QLabel(self.app_name)
        self.name_label.setStyleSheet(f"""
            font-weight: 700;
            font-size: 16px;
            color: {COLORS['text_light']};
            font-family: Inter, sans-serif;
            margin: 0px;
            padding: 0px;
            border: none;
        """)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(40)  # FIXED: Limit height to prevent overflow
        layout.addWidget(self.name_label)

        # FIXED: Description with controlled height
        self.description_label = QLabel(self.app_description.strip())
        self.description_label.setWordWrap(True)
        self.description_label.setFixedHeight(35)  # FIXED: Smaller fixed height
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.description_label.setStyleSheet(f"""
            color: {COLORS['text_medium']};
            font-size: 11px;
            font-family: Inter, sans-serif;
            line-height: 1.3;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
        layout.addWidget(self.description_label)

        # FIXED: Add stretch to push buttons to bottom
        layout.addStretch()

        # FIXED: Progress bar - NO PERCENTAGE, just blue line
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)  # FIXED: Hide percentage text
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {COLORS['progress_bg']};
                height: 8px;
                margin: 4px 0px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['progress_fill']};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # FIXED: Buttons with better layout and spacing
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.install_launch_button = QPushButton("Install")
        self.install_launch_button.clicked.connect(self.on_install_launch_clicked)
        self.install_launch_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                font-family: Inter, sans-serif;
                min-width: 60px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                background-color: rgba(35, 139, 230, 0.9);
            }}
            QPushButton:pressed {{
                background-color: rgba(35, 139, 230, 0.7);
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border_dark']};
                color: {COLORS['text_dark']};
            }}
        """)

        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.setEnabled(True)
        self.uninstall_button.clicked.connect(self.on_uninstall_clicked)
        self.uninstall_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['border_light']};
                color: {COLORS['text_light']};
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                font-family: Inter, sans-serif;
                min-width: 60px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                background-color: rgba(72, 79, 88, 0.9);
            }}
            QPushButton:pressed {{
                background-color: rgba(72, 79, 88, 0.7);
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border_dark']};
                color: {COLORS['text_dark']};
            }}
        """)

        button_layout.addWidget(self.install_launch_button)
        button_layout.addWidget(self.uninstall_button)
        layout.addLayout(button_layout)

        # Update initial button states
        if self.is_app_installed(f'{self.install_path}.exe'):
            self.installed = True
            self.uninstall_button.setEnabled(True)
        self.update_button_states()

    def setup_back_ui(self):
        """FIXED: Setup back side with proper spacing and no text overlap"""
        main_layout = QVBoxLayout(self.back_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # FIXED: Apply consistent background styling
        self.back_widget.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border: none;
            }}
        """)

        # FIXED: Title with proper spacing
        title_label = QLabel("Application Details")
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {COLORS['text_light']};
            font-family: Inter, sans-serif;
            margin-bottom: 8px;
            border: none;
            padding: 0px;
        """)
        main_layout.addWidget(title_label)

        # FIXED: Details with controlled spacing and no overlap
        details = [
            ("IAHub ID", "Not Registered" if pd.isna(self.registration_id) else str(self.registration_id)),
            ("Release Date", str(pd.Timestamp(self.release_date))[:10] if self.release_date else "N/A"),
            ("Version", str(self.version_number) if self.version_number else "1.0"),
            ("Status", "Expired" if self.is_expired else "Active")
        ]

        for title, value in details:
            # FIXED: Each detail in its own container with controlled height
            detail_container = QWidget()
            detail_container.setStyleSheet("border: none;")
            detail_container.setFixedHeight(35)  # FIXED: Control height to prevent overlap
            detail_layout = QVBoxLayout(detail_container)
            detail_layout.setSpacing(2)
            detail_layout.setContentsMargins(0, 2, 0, 2)

            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                color: {COLORS['text_dark']};
                font-size: 9px;
                font-weight: 500;
                font-family: Inter, sans-serif;
                border: none;
                padding: 0px;
                margin: 0px;
            """)
            detail_layout.addWidget(title_label)

            value_label = QLabel(str(value))
            value_label.setStyleSheet(f"""
                color: {COLORS['text_medium']};
                font-size: 11px;
                font-weight: 600;
                font-family: Inter, sans-serif;
                border: none;
                padding: 0px;
                margin: 0px;
            """)
            value_label.setWordWrap(True)
            value_label.setMaximumHeight(20)  # FIXED: Limit height
            detail_layout.addWidget(value_label)

            main_layout.addWidget(detail_container)

        main_layout.addStretch()

    def show_context_menu(self, position):
        """Show context menu for flipping"""
        context_menu = QMenu(self)
        context_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['tile_background']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 12px;
                border-radius: 4px;
                color: {COLORS['text_light']};
                border: none;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary']};
            }}
        """)

        flip_action = context_menu.addAction("Show Details" if not self.is_flipped else "Show Main")
        action = context_menu.exec(self.mapToGlobal(position))
        if action == flip_action:
            self.flip_tile()

    def flip_tile(self):
        """Flip the tile"""
        self.is_flipped = not self.is_flipped
        self.stacked_layout.setCurrentIndex(1 if self.is_flipped else 0)

    def add_expired_overlay(self):
        """Add expired overlay"""
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.6);
            border-radius: 12px;
            border: none;
        """)
        self.overlay.setGeometry(self.rect())
        self.overlay.show()
        self.front_widget.setEnabled(False)

    # Keep all the original methods for functionality
    def on_install_launch_clicked(self):
        if self.update_available:
            self.update_application()
        elif not self.installed:
            self.install_application()
        else:
            self.launch_application()

    def is_app_installed(self, local_path):
        return os.path.exists(local_path)

    def install_application(self):
        # FIXED: Better UI feedback during installation
        self.progress_bar.setVisible(True)
        self.status_indicator.setText("Installing...")
        self.install_launch_button.setEnabled(False)  # FIXED: Disable button during install

        os.makedirs(self.install_path, exist_ok=True)
        destination_file = os.path.join(self.install_path, f"{self.app_name}.exe")

        self.install_thread = InstallThread(self.shared_drive_path, destination_file)
        self.install_thread.progress.connect(self.update_progress)
        self.install_thread.finished.connect(self.installation_finished)
        self.install_thread.error.connect(self.installation_error)
        self.install_thread.start()

    def installation_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.status_indicator.setText("Installation Failed")
        self.install_launch_button.setEnabled(True)  # FIXED: Re-enable button

        # FIXED: Use custom message box with proper contrast
        dialog = CustomMessageBox(
            parent=self.window(),
            title="Installation Error",
            message=f"Failed to install {self.app_name}:\n{error_message}",
            icon_type="error"
        )
        dialog.exec()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def installation_finished(self):
        self.installed = True
        self.save_installed_version()
        self.installed_version = self.version_number
        self.update_available = False
        self.update_button_states()
        self.progress_bar.setVisible(False)
        self.install_launch_button.setEnabled(True)  # FIXED: Re-enable button

        # FIXED: Use custom message box
        dialog = CustomMessageBox(
            parent=self.window(),
            title="Installation Complete",
            message=f"{self.app_name} has been successfully installed.",
            icon_type="success"
        )
        dialog.exec()

    def launch_application(self):
        # pslv_action_entry([{'SID': user_main, 'action': f'Launched {self.app_name}'}])
        executable_path = os.path.join(self.install_path, f"{self.app_name}.exe")
        release_date = pd.Timestamp(self.release_date)
        expiry_date = release_date + timedelta(days=self.validity_period)
        days_remaining = expiry_date - datetime.now()
        if os.path.exists(executable_path):
            try:
                if pd.isna(self.registration_id) and self.environment == 'BETA':
                    # FIXED: Use custom message box
                    dialog = CustomMessageBox(
                        parent=self.window(),
                        title="Action Required",
                        message=f'Application is not registered at IA Hub and will stop working in {days_remaining.days} days.',
                        icon_type="warning"
                    )
                    dialog.exec()
                LauncherSecurity.generate_launch_token(executable_path)
                os.startfile(executable_path)
            except Exception as e:
                # FIXED: Use custom message box
                dialog = CustomMessageBox(
                    parent=self.window(),
                    title="Error",
                    message=f'Failed to launch application: {str(e)}',
                    icon_type="error"
                )
                dialog.exec()
        else:
            # FIXED: Use custom message box
            dialog = CustomMessageBox(
                parent=self.window(),
                title="Error",
                message=f'Application executable not found at {executable_path}',
                icon_type="error"
            )
            dialog.exec()

    def on_uninstall_clicked(self):
        if self.installed:
            try:
                shutil.rmtree(self.install_path)
                self.installed = False
                self.status_indicator.setText("Not Installed")
                self.install_launch_button.setText("Install")
                # pslv_action_entry([{'SID': user_main, 'action': f'Uninstalled {self.app_name}'}])

                # FIXED: Use custom message box
                dialog = CustomMessageBox(
                    parent=self.window(),
                    title="Uninstall Complete",
                    message=f'{self.app_name} has been successfully uninstalled.',
                    icon_type="success"
                )
                dialog.exec()
            except Exception as e:
                # FIXED: Use custom message box
                dialog = CustomMessageBox(
                    parent=self.window(),
                    title="Uninstall Error",
                    message=f'Failed to uninstall {self.app_name}: {str(e)}',
                    icon_type="error"
                )
                dialog.exec()

    def check_validity(self):
        try:
            # release_date = pd.Timestamp(self.release_date)
            # expiry_date = release_date + timedelta(days=self.validity_period)
            # return datetime.now() > expiry_date
            return False
        except Exception as e:
            print(f"Error checking validity: {str(e)}")
            return False

    def check_update_available(self):
        try:
            installed_version = self.get_installed_version()
            if self.version_number and self.installed:
                if installed_version is None:
                    return True
                return float(self.version_number) > float(installed_version)
            return False
        except Exception as e:
            print(f"Error checking for updates: {str(e)}")
            return False

    def update_button_states(self):
        if self.is_expired:
            self.status_indicator.setText("Expired")
            self.status_indicator.setStyleSheet(
                f"color: {COLORS['red_status']}; font-size: 10px; font-weight: 600; border: none; padding: 0px;")
            self.install_launch_button.setEnabled(False)
            self.uninstall_button.setEnabled(False)
            return
        if self.update_available:
            self.install_launch_button.setText("Update")
            self.status_indicator.setText("Update Available")
            self.status_indicator.setStyleSheet(
                f"color: {COLORS['uat_text']}; font-size: 10px; font-weight: 600; border: none; padding: 0px;")
        elif self.installed:
            self.install_launch_button.setText("Launch")
            self.status_indicator.setText("Installed")
            self.status_indicator.setStyleSheet(
                f"color: {COLORS['green_status']}; font-size: 10px; font-weight: 600; border: none; padding: 0px;")
        else:
            self.install_launch_button.setText("Install")
            self.status_indicator.setText("Not Installed")
            self.status_indicator.setStyleSheet(
                f"color: {COLORS['text_dark']}; font-size: 10px; font-weight: 600; border: none; padding: 0px;")

    def get_installed_version(self):
        version_file = os.path.join(self.install_path, "version.txt")
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    return float(f.read().strip())
            except:
                return None
        return None

    def save_installed_version(self):
        try:
            os.makedirs(self.install_path, exist_ok=True)
            version_file = os.path.join(self.install_path, "version.txt")
            with open(version_file, 'w') as f:
                f.write(str(self.version_number))
        except Exception as e:
            print(f"Error saving version info: {str(e)}")

    def update_application(self):
        latest_version = self.version_number
        if latest_version:
            try:
                if os.path.exists(self.install_path):
                    shutil.rmtree(self.install_path)

                self.install_application()
                self.version_number = latest_version
                self.update_available = False
                self.update_button_states()
            except Exception as e:
                # FIXED: Use custom message box
                dialog = CustomMessageBox(
                    parent=self.window(),
                    title="Update Error",
                    message=f"Failed to update {self.app_name}: {str(e)}",
                    icon_type="error"
                )
                dialog.exec()


class NoAccessWidget(QWidget):
    """FIXED: Compact no access widget that matches the design exactly"""

    def __init__(self, is_gfbm_user):
        super().__init__()
        self.is_gfbm_user = is_gfbm_user
        self.setupUI()

    def setupUI(self):
        # FIXED: Set a maximum size for the widget to prevent over-expansion
        self.setMaximumSize(500, 350)
        self.setMinimumSize(500, 350)

        # Main layout with no margins to keep it compact
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # FIXED: Create the message container with exact sizing
        container = QFrame()
        container.setFixedSize(500, 350)  # Exact size matching the design
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['tile_background']};
                border-radius: 12px;
                border: 1px solid {COLORS['border_dark']};
            }}
        """)

        # Container layout with proper spacing
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(32, 32, 32, 32)
        container_layout.setSpacing(16)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # FIXED: Icon - using the red prohibition sign like in the image
        icon_label = QLabel("🚫")
        icon_label.setStyleSheet(f"""
            font-size: 48px;
            color: {COLORS['red_status']};
            border: none;
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(icon_label)

        # FIXED: Title with proper styling
        title_label = QLabel("No Application Access")
        title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['text_light']};
            font-family: Inter, sans-serif;
            border: none;
            margin: 0px;
            padding: 0px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)

        # FIXED: Description with proper line breaks and styling
        description_text = ("Currently, you do not have access to any application.\n"
                          "Please contact administrator for access permissions.")
        if not self.is_gfbm_user:
            description_text = ("Thanks for showing your interest for PSLV.\n"
                              "At present, Application is accessible for Global Finance & Business Management India.")

        description_label = QLabel(description_text)
        description_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_medium']};
            font-family: Inter, sans-serif;
            border: none;
            line-height: 2;
            margin: 0px;
            padding: 0px;
        """)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        container_layout.addWidget(description_label)

        # Add some spacing
        container_layout.addSpacing(8)

        # FIXED: Help Center button with proper styling
        help_button = QPushButton("Help Center")
        help_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                font-family: Inter, sans-serif;
                min-width: 120px;
                max-width: 160px;
            }}
            QPushButton:hover {{
                background-color: rgba(35, 139, 230, 0.9);
            }}
            QPushButton:pressed {{
                background-color: rgba(35, 139, 230, 0.7);
            }}
        """)
        help_button.clicked.connect(self.contact_admin)
        container_layout.addWidget(help_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add the container to main layout
        main_layout.addWidget(container)

    def contact_admin(self):
        """Open help center URL"""
        support_url = QUrl(
            "https://confluence.prod.aws.jpmchase.net/confluence/spaces/GFITECH/pages/5228999093/APPLICATION+OWNER+AND+ADMINS")
        QDesktopServices.openUrl(support_url)


class MainWindow(QMainWindow):
    """Main window with FIXED ApplicationTile integration and custom dialogs"""

    def __init__(self, df, cost_center, userdata):
        super().__init__()
        self.all_tiles = []
        self.access = df
        self.cost_center_df = cost_center
        self.userdata = userdata
        self.user_details = self.get_user_details()
        self.is_gfbm_user = self.is_gfbm_user_check()
        self.username = user_main
        self.current_filter = "All"

        self.setWindowTitle("PSLV by STD, GF&BM India")
        icon_path = resource_path(f"resources/STDJustLogo.PNG")
        self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(1400, 800)

        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background_dark']};
                font-family: Inter, sans-serif;
                border: none;
            }}
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # Main content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(24)

        # Header with title and filters
        header_layout = QHBoxLayout()

        title_label = QLabel("Available Applications")
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {COLORS['text_light']};
            font-family: Inter, sans-serif;
            border: none;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Filter buttons
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setSpacing(8)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_group = QButtonGroup()
        filter_buttons = ["All", "UAT", "BETA", "PROD"]

        for idx, filter_name in enumerate(filter_buttons):
            btn = QPushButton(filter_name)
            btn.setCheckable(True)
            btn.setChecked(filter_name == "All")
            btn.clicked.connect(lambda checked, f=filter_name: self.apply_filter(f))
            self.filter_group.addButton(btn, idx)

            if filter_name == "All":
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['primary']};
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 13px;
                        font-family: Inter, sans-serif;
                    }}
                    QPushButton:checked {{
                        background-color: {COLORS['primary']};
                    }}
                    QPushButton:hover {{
                        background-color: rgba(35, 139, 230, 0.8);
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS['text_dark']};
                        border: none;
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 13px;
                        font-family: Inter, sans-serif;
                    }}
                    QPushButton:checked {{
                        background-color: {COLORS['primary']};
                        color: white;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['surface_dark']};
                        color: {COLORS['text_light']};
                    }}
                """)

            filter_layout.addWidget(btn)

        header_layout.addWidget(filter_container)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search applications...")
        self.search_bar.textChanged.connect(self.filter_applications)
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['surface_dark']};
                border: 2px solid {COLORS['border_dark']};
                border-radius: 8px;
                padding: 12px 16px 12px 40px;
                color: {COLORS['text_light']};
                font-size: 14px;
                min-width: 280px;
                font-family: Inter, sans-serif;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_dark']};
            }}
        """)
        header_layout.addWidget(self.search_bar)
        # Refresh button
        self.refresh_button = QPushButton("⟲")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setToolTip("⟲ Refresh Applications")
        self.refresh_button.clicked.connect(self.refresh_applications)
        self.refresh_button.setStyleSheet("""
                           QPushButton {
                               background-color: transparent;
                               color: white;
                               font-size: 20px;
                               padding: 5px;
                               min-width: 30px;
                               font-weight: bold;
                           }
                           QPushButton:hover {
                               color: #4a90e2;
                           }
                       """)
        header_layout.addWidget(self.refresh_button)

        content_layout.addLayout(header_layout)

        # Scroll area for applications
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {COLORS['background_dark']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border_dark']};
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_dark']};
            }}
        """)

        scroll_content = QWidget()
        self.app_grid = QGridLayout(scroll_content)
        self.app_grid.setSpacing(16)
        self.app_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll_area.setWidget(scroll_content)

        self.search_app = QWidget()
        self.search_app_layout = QVBoxLayout(self.search_app)
        self.search_app_layout.addWidget(scroll_area)

        # Create stacked widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.search_app)

        # Access control widget (if admin)
        if self.is_administrator():
            self.access_control_widget = AccessControlDialog(self.username, [])
            self.stacked_widget.addWidget(self.access_control_widget)

        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_area)

        # Load applications
        if len(self.access) != 0 and self.is_gfbm_user:
            self.load_applications()
        else:
            # FIXED: Clear the grid and add NoAccessWidget properly centered
            self.clear_layout(self.app_grid)
            # FIXED: Center the NoAccessWidget in the middle of the content area
            self.app_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_access_widget = NoAccessWidget(self.is_gfbm_user)
            # FIXED: Add the widget to the center of the grid with proper alignment
            self.app_grid.addWidget(no_access_widget, 0, 0, 1, 1, Qt.AlignmentFlag.AlignCenter)

    def create_sidebar(self):
        """Create modern sidebar"""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface_dark']};
                border: none;
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Logo/Icon placeholder
        logo_label = QLabel("📦")
        logo_label.setStyleSheet("font-size: 64px; border: none;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # User details
        for label_text, icon_name in self.user_details:
            detail_widget = self.create_detail_input(label_text)
            layout.addWidget(detail_widget)

        layout.addStretch()

        # Bottom buttons - NO BORDERS
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 16, 0, 0)

        # About button
        about_btn = QPushButton("ℹ️  About")
        about_btn.clicked.connect(self.show_about_dialog)
        about_btn.setStyleSheet(self.get_sidebar_button_style())
        button_layout.addWidget(about_btn)

        # Help button
        help_btn = QPushButton("❓  Help")
        help_btn.clicked.connect(self.show_help_dialog)
        help_btn.setStyleSheet(self.get_sidebar_button_style())
        button_layout.addWidget(help_btn)

        # Exit button
        exit_btn = QPushButton("🚪  Exit")
        exit_btn.clicked.connect(self.close_application)  # FIXED: Use proper close method
        exit_btn.setStyleSheet(self.get_sidebar_button_style())
        button_layout.addWidget(exit_btn)

        layout.addWidget(button_container)

        return sidebar

    def close_application(self):
        """FIXED: Properly close the application"""
        self.close()

    def get_sidebar_button_style(self):
        return f"""
            QPushButton {{
                background-color: {COLORS['background_dark']};
                color: {COLORS['text_light']};
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                text-align: left;
                font-weight: 500;
                font-family: Inter, sans-serif;
            }}
            QPushButton:hover {{
                background-color: rgba(19, 138, 236, 0.2);
            }}
        """

    def create_detail_input(self, label_text):
        """Create input field for user details"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text.split('\n')[0] if '\n' in label_text else label_text[:20])
        label.setStyleSheet(f"""
            color: {COLORS['text_dark']};
            font-size: 11px;
            font-weight: 500;
            font-family: Inter, sans-serif;
            border: none;
        """)
        layout.addWidget(label)

        input_field = QLineEdit()
        input_field.setText(label_text)
        input_field.setReadOnly(True)
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['background_dark']};
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                color: {COLORS['text_light']};
                font-size: 13px;
                font-family: Inter, sans-serif;
            }}
        """)
        layout.addWidget(input_field)

        return container

    def show_about_dialog(self):
        """FIXED: Show about dialog with no title bar"""
        dialog = CustomMessageBox(
            parent=self,
            title="About Software Center",
            message="Version 3.0\n2024 @STO, GF&BM India",
            icon_type="info"
        )
        dialog.exec()

    def show_help_dialog(self):
        """FIXED: Show help dialog with no title bar"""
        help_text = ("This is the PSLV Software Center.\n\n"
                     "• Browse and install available applications\n"
                     "• Filter by environment (UAT, BETA, PROD)\n"
                     "• Search for specific applications\n"
                     "• Right-click tiles for more options\n\n"
                     "For assistance, contact Think_STO@restricted.chase.com")

        dialog = CustomMessageBox(
            parent=self,
            title="Help",
            message=help_text,
            icon_type="info"
        )
        dialog.exec()

    def apply_filter(self, filter_name):
        """Apply environment filter"""
        self.current_filter = filter_name
        self.update_grid_layout(self.search_bar.text().lower())

        # Update button styles
        for button in self.filter_group.buttons():
            if button.text() == filter_name:
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['primary']};
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 13px;
                        font-family: Inter, sans-serif;
                    }}
                """)
            else:
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS['text_dark']};
                        border: none;
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 13px;
                        font-family: Inter, sans-serif;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['surface_dark']};
                        color: {COLORS['text_light']};
                    }}
                """)

    def load_applications(self):
        """Load applications into grid"""
        try:
            self.clear_layout(self.app_grid)
            self.app_grid.setContentsMargins(0, 0, 0, 0)
            self.app_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.all_tiles.clear()

            self.access['Expired'] = self.access.apply(lambda row: expire_sort(row), axis=1)
            self.access = self.access.sort_values(by=['Expired', 'Solution_Name'], ascending=[True, True])
            self.access.reset_index(inplace=True, drop=True)

            for i, row in self.access.iterrows():
                tile = ApplicationTile(
                    app_name=row['Solution_Name'],
                    app_description=row['Description'],
                    shared_drive_path=row['ApplicationExePath'],
                    environment=row['Status'],
                    release_date=row['Release_Date'],
                    validity_period=row['Validity_Period'],
                    version_number=float(row['Version_Number']) if row['Version_Number'] else 1.0,
                    registration_id=row['UMAT_IAHub_ID']
                )
                self.all_tiles.append(tile)

            self.update_grid_layout("")
        except Exception as e:
            # FIXED: Use custom message box
            dialog = CustomMessageBox(
                parent=self,
                title="Error",
                message=f"Failed to load applications: {str(e)}",
                icon_type="error"
            )
            dialog.exec()

    def filter_applications(self, text):
        self.update_grid_layout(text.lower())

    def update_grid_layout(self, filter_text):
        """Update grid with filtered tiles - 4 tiles per row for better spacing"""
        self.clear_layout(self.app_grid)

        visible_tiles = [
            tile for tile in self.all_tiles
            if (filter_text in tile.app_name.lower()) and
               (self.current_filter == "All" or tile.environment == self.current_filter)
        ]

        # 4 tiles per row for better spacing (matching the uploaded design)
        for i, tile in enumerate(visible_tiles):
            row = i // 4
            col = i % 4
            self.app_grid.addWidget(tile, row, col)
            tile.setVisible(True)

        self.app_grid.setRowStretch(len(visible_tiles) // 4 + 1, 1)

    def clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def get_user_details(self):
        """Get user details"""
        try:
            if self.userdata.empty:
                data = {}  # awmpy.get_phonebook_data(user_main)
                self.cost_center = data['costCenterID']
                details = [
                    (data['standardID'], 'icons8-id-50.png'),
                    (data['nameFull'], 'icons8-user-64.png'),
                    (data['email'], 'icons8-email-50.png'),
                    (data['jobTitle'], 'icons8-new-job-50.png'),
                    (data['buildingName'], 'icons8-location-50.png')
                ]
                add_new_user_to_userbase(
                    [data['standardID'], data['nameFull'], data['email'], data['jobTitle'], data['buildingName'],
                     data['costCenterID']])
            else:
                self.cost_center = str(self.userdata['cost_center_id'].values[0])
                details = [
                    (self.userdata['sid'].values[0], 'icons8-id-50.png'),
                    (self.userdata['display_name'].values[0], 'icons8-user-64.png'),
                    (self.userdata['email'].values[0], 'icons8-email-50.png'),
                    (self.userdata['job_title'].values[0], 'icons8-new-job-50.png'),
                    (self.userdata['building_name'].values[0], 'icons8-location-50.png')
                ]
        except:
            details = DETAILS
        return details

    def is_administrator(self):
        """Check if user is administrator"""
        try:
            cred = HttpNtlmAuth(SID, password="**")
            site = Site(SITE_URL, auth=cred, verify_ssl=False)
            sp_list = site.List(ADMIN)
            query = {'Where': [('Contains', 'sid', user_main)]}
            sp_data = sp_list.GetListItems(query=query)
            df = pd.DataFrame(sp_data)
            df.fillna(value='', inplace=True)
            managed_lob = df['lob'].tolist()
            return len(managed_lob) > 0
        except:
            return False

    def is_gfbm_user_check(self):
        """Check if user is GFBM"""
        self.cost_center_df['cost_center_code'] = self.cost_center_df['cost_center_code'].astype(str)
        cc_column = self.cost_center_df['cost_center_code'].to_list()
        return self.cost_center in cc_column

    def refresh_applications(self):
        """Refresh applications list"""
        self.search_bar.clear()
        try:
            user = user_main.lower()
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            cred = HttpNtlmAuth(SID, password="**")
            site = Site(SITE_URL, auth=cred, verify_ssl=False)
            sp_list = site.List(SHAREPOINT_LIST)
            sp_data = sp_list.GetListItems(view_name=None)
            df_all = pd.DataFrame(sp_data)
            df_all.fillna(value='', inplace=True)
            df_all['SIDs_For_SolutionAccess'] = df_all['SIDs_For_SolutionAccess'].str.lower()
            all_df = df_all[df_all['SIDs_For_SolutionAccess'].str.contains('everyone', na=False)]
            processed_df = df_all[df_all['SIDs_For_SolutionAccess'].str.contains(user, na=False)]
            processed_df = pd.concat([all_df, processed_df])
            processed_df.reset_index(inplace=True)
        except Exception as e:
            if os.path.exists(f"{os.environ.get('USERPROFILE')}/{BACKUP_PATH}/{BACKUP_FILE_NAME}"):
                processed_df = pd.read_excel(f"{os.environ.get('USERPROFILE')}/{BACKUP_PATH}/{BACKUP_FILE_NAME}")
            else:
                processed_df = pd.DataFrame(
                    columns=['Expired', 'Solution_Name', 'Description', 'ApplicationExePath', 'Status',
                             'Release_Date', 'Validity_Period', 'Version_Number', 'UMAT_IAHub_ID'])

        self.access = processed_df
        if len(self.access) > 0:
            self.load_applications()
        else:
            self.clear_layout(self.app_grid)
            self.app_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_access_widget = NoAccessWidget(self.is_gfbm_user)
            self.app_grid.addWidget(no_access_widget, 0, 0, 1, 1, Qt.AlignmentFlag.AlignCenter)

            # FIXED: Use custom message box
            dialog = CustomMessageBox(
                parent=self,
                title="Application",
                message="Refresh Complete...",
                icon_type="info"
            )
            dialog.exec()