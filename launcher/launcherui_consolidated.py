"""
Consolidated Launcher UI
Combines functionality from uploads/launcherui.py and related launcher components
"""

import sys
import os
import json
import logging
import subprocess
import time
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QMessageBox, QDialog,
    QLineEdit, QComboBox, QTextEdit, QProgressBar, QStatusBar,
    QMenuBar, QMenu, QAction, QToolBar, QSplitter, QTabWidget,
    QGroupBox, QCheckBox, QSpinBox, QDateEdit, QTimeEdit,
    QSlider, QProgressDialog, QFileDialog, QColorDialog,
    QFontDialog, QInputDialog, QErrorMessage, QWizard,
    QWizardPage, QTreeWidget, QTreeWidgetItem, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPoint, QRect,
    QSettings, QStandardPaths, QUrl, QMimeData, QByteArray,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, QVariantAnimation, QAbstractAnimation,
    QEvent, QObject, QRunnable, QThreadPool, QMutex, QWaitCondition
)
from PyQt6.QtGui import (
    QFont, QPixmap, QIcon, QPalette, QColor, QBrush, QPen,
    QLinearGradient, QRadialGradient, QConicalGradient,
    QPainter, QFontMetrics, QValidator, QIntValidator,
    QDoubleValidator, QRegularExpressionValidator, QAction,
    QKeySequence, QShortcut, QCursor, QDrag, QClipboard,
    QDesktopServices, QStandardItemModel, QStandardItem
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('launcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LauncherSecurity:
    """Security management for launcher applications"""
    
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
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Security Error")
            msg.setText(message)
            msg.exec()
        except Exception:
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

        except Exception as e:
            LauncherSecurity.log_security_error(f"Token verification failed: {str(e)}")
            LauncherSecurity.show_user_error("Security verification failed. Please contact support.")
            return False

class ApplicationTile(QFrame):
    """Custom widget for displaying application tiles in the launcher"""
    
    clicked = pyqtSignal(str)  # Emits application path when clicked
    
    def __init__(self, app_name, app_path, description="", icon_path=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.app_path = app_path
        self.description = description
        self.icon_path = icon_path
        self.is_selected = False
        
        self.setFixedSize(200, 150)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Setup the tile UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Icon (placeholder for now)
        self.icon_label = QLabel("📱")  # Using emoji as placeholder
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(self.icon_label)

        # Application name
        self.name_label = QLabel(self.app_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.name_label)

        # Description
        if self.description:
            self.desc_label = QLabel(self.description[:50] + "..." if len(self.description) > 50 else self.description)
            self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.desc_label.setWordWrap(True)
            self.desc_label.setStyleSheet("font-size: 10px; color: #666;")
            layout.addWidget(self.desc_label)

        layout.addStretch()

    def apply_styles(self):
        """Apply styling to the tile"""
        self.setStyleSheet("""
            ApplicationTile {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin: 5px;
            }
            ApplicationTile:hover {
                border-color: #1976d2;
                background-color: #f5f5f5;
            }
        """)

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.app_path)
        super().mousePressEvent(event)

    def set_selected(self, selected):
        """Set the selected state of the tile"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                ApplicationTile {
                    background-color: #e3f2fd;
                    border: 2px solid #1976d2;
                    border-radius: 8px;
                    margin: 5px;
                }
            """)
        else:
            self.apply_styles()

class LauncherMainWindow(QMainWindow):
    """Main launcher window with application management capabilities"""
    
    def __init__(self):
        super().__init__()
        self.applications = {}  # Dictionary to store application data
        self.selected_app = None
        self.settings = QSettings("LauncherApp", "Settings")
        
        self.setWindowTitle("Application Launcher")
        self.setMinimumSize(1000, 700)
        
        # Initialize security
        self.security = LauncherSecurity()
        
        self.setup_ui()
        self.load_applications()
        self.apply_styles()

    def setup_ui(self):
        """Setup the main UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Left panel for categories and controls
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel for applications grid
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 3)
        
        # Setup menu bar
        self.setup_menu_bar()
        
        # Setup status bar
        self.setup_status_bar()

    def create_left_panel(self):
        """Create the left control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(250)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Application Launcher")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search applications...")
        self.search_box.textChanged.connect(self.filter_applications)
        layout.addWidget(self.search_box)
        
        # Categories
        categories_group = QGroupBox("Categories")
        categories_layout = QVBoxLayout(categories_group)
        
        self.category_buttons = {}
        categories = ["All", "Productivity", "Development", "Games", "Utilities", "Other"]
        
        for category in categories:
            btn = QPushButton(category)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, cat=category: self.filter_by_category(cat))
            self.category_buttons[category] = btn
            categories_layout.addWidget(btn)
        
        # Set "All" as default
        self.category_buttons["All"].setChecked(True)
        
        layout.addWidget(categories_group)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.add_app_btn = QPushButton("Add Application")
        self.add_app_btn.clicked.connect(self.add_application)
        actions_layout.addWidget(self.add_app_btn)
        
        self.remove_app_btn = QPushButton("Remove Application")
        self.remove_app_btn.clicked.connect(self.remove_application)
        self.remove_app_btn.setEnabled(False)
        actions_layout.addWidget(self.remove_app_btn)
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        actions_layout.addWidget(self.settings_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        return panel

    def create_right_panel(self):
        """Create the right applications panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.apps_count_label = QLabel("Applications: 0")
        self.apps_count_label.setStyleSheet("font-size: 14px; color: #666;")
        header_layout.addWidget(self.apps_count_label)
        
        header_layout.addStretch()
        
        self.view_mode_btn = QPushButton("Grid View")
        self.view_mode_btn.clicked.connect(self.toggle_view_mode)
        header_layout.addWidget(self.view_mode_btn)
        
        layout.addLayout(header_layout)
        
        # Applications area
        self.apps_scroll = QScrollArea()
        self.apps_scroll.setWidgetResizable(True)
        self.apps_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.apps_container = QWidget()
        self.apps_layout = QGridLayout(self.apps_container)
        self.apps_layout.setSpacing(10)
        
        self.apps_scroll.setWidget(self.apps_container)
        layout.addWidget(self.apps_scroll)
        
        return panel

    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        add_action = QAction("Add Application", self)
        add_action.setShortcut(QKeySequence.StandardKey.New)
        add_action.triggered.connect(self.add_application)
        file_menu.addAction(add_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self.refresh_applications)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def apply_styles(self):
        """Apply application-wide styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QPushButton:checked {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLineEdit {
                border: 1px solid #e0e0e0;
                padding: 8px;
                border-radius: 4px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #1976d2;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

    def load_applications(self):
        """Load applications from settings or default locations"""
        # Load from settings
        self.applications = {}
        
        # Add some default applications for demonstration
        default_apps = [
            {
                "name": "Notepad",
                "path": "notepad.exe",
                "description": "Simple text editor",
                "category": "Productivity"
            },
            {
                "name": "Calculator",
                "path": "calc.exe", 
                "description": "Windows calculator",
                "category": "Utilities"
            },
            {
                "name": "Paint",
                "path": "mspaint.exe",
                "description": "Image editor",
                "category": "Productivity"
            }
        ]
        
        for app in default_apps:
            self.applications[app["name"]] = app
        
        self.refresh_applications()

    def refresh_applications(self):
        """Refresh the applications display"""
        # Clear existing tiles
        for i in reversed(range(self.apps_layout.count())):
            child = self.apps_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add application tiles
        row, col = 0, 0
        max_cols = 4
        
        for app_name, app_data in self.applications.items():
            tile = ApplicationTile(
                app_name,
                app_data["path"],
                app_data.get("description", ""),
                app_data.get("icon", None)
            )
            tile.clicked.connect(self.launch_application)
            
            self.apps_layout.addWidget(tile, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Update count
        self.apps_count_label.setText(f"Applications: {len(self.applications)}")
        self.status_bar.showMessage(f"Loaded {len(self.applications)} applications")

    def filter_applications(self, search_text):
        """Filter applications based on search text"""
        # Implementation for filtering applications
        pass

    def filter_by_category(self, category):
        """Filter applications by category"""
        # Uncheck other category buttons
        for cat, btn in self.category_buttons.items():
            btn.setChecked(cat == category)

    def launch_application(self, app_path):
        """Launch the selected application with security checks"""
        try:
            # Generate security token
            token = self.security.generate_launch_token(app_path)
            if not token:
                return
            
            # Launch the application
            if os.path.exists(app_path):
                subprocess.Popen([app_path])
                self.status_bar.showMessage(f"Launched: {app_path}")
                logger.info(f"Successfully launched application: {app_path}")
            else:
                # Try to launch as system command
                subprocess.Popen([app_path], shell=True)
                self.status_bar.showMessage(f"Launched: {app_path}")
                logger.info(f"Successfully launched system command: {app_path}")
                
        except Exception as e:
            error_msg = f"Failed to launch application: {str(e)}"
            QMessageBox.critical(self, "Launch Error", error_msg)
            logger.error(f"Failed to launch {app_path}: {str(e)}")

    def add_application(self):
        """Add a new application to the launcher"""
        dialog = AddApplicationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            app_data = dialog.get_application_data()
            self.applications[app_data["name"]] = app_data
            self.refresh_applications()
            self.status_bar.showMessage(f"Added application: {app_data['name']}")

    def remove_application(self):
        """Remove the selected application"""
        if self.selected_app and self.selected_app in self.applications:
            reply = QMessageBox.question(
                self,
                "Remove Application",
                f"Are you sure you want to remove '{self.selected_app}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                del self.applications[self.selected_app]
                self.refresh_applications()
                self.selected_app = None
                self.remove_app_btn.setEnabled(False)
                self.status_bar.showMessage("Application removed")

    def show_settings(self):
        """Show the settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()

    def toggle_view_mode(self):
        """Toggle between grid and list view"""
        pass

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Application Launcher",
            "Application Launcher v1.0\n\n"
            "A comprehensive application launcher with security features.\n"
            "Built with PyQt6."
        )

class AddApplicationDialog(QDialog):
    """Dialog for adding new applications"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Application")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Form fields
        form_layout = QVBoxLayout()
        
        # Name
        form_layout.addWidget(QLabel("Application Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter application name")
        form_layout.addWidget(self.name_edit)
        
        # Path
        form_layout.addWidget(QLabel("Application Path:"))
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Enter or browse for application path")
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_application)
        path_layout.addWidget(browse_btn)
        
        form_layout.addLayout(path_layout)
        
        # Description
        form_layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter application description (optional)")
        form_layout.addWidget(self.description_edit)
        
        # Category
        form_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Productivity", "Development", "Games", "Utilities", "Other"])
        form_layout.addWidget(self.category_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.accept)
        add_btn.setDefault(True)
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)

    def browse_application(self):
        """Browse for application executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Application",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            self.path_edit.setText(file_path)
            if not self.name_edit.text():
                # Auto-fill name from filename
                name = Path(file_path).stem
                self.name_edit.setText(name)

    def get_application_data(self):
        """Get the application data from the form"""
        return {
            "name": self.name_edit.text(),
            "path": self.path_edit.text(),
            "description": self.description_edit.toPlainText(),
            "category": self.category_combo.currentText()
        }

class SettingsDialog(QDialog):
    """Settings dialog for launcher configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the settings dialog UI"""
        layout = QVBoxLayout(self)
        
        # Tab widget for different settings categories
        tab_widget = QTabWidget()
        
        # General settings
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        general_layout.addWidget(QLabel("Startup Settings:"))
        self.startup_check = QCheckBox("Launch with Windows")
        general_layout.addWidget(self.startup_check)
        
        general_layout.addWidget(QLabel("Display Settings:"))
        self.grid_size_label = QLabel("Grid Size:")
        general_layout.addWidget(self.grid_size_label)
        
        self.grid_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.grid_size_slider.setRange(2, 6)
        self.grid_size_slider.setValue(4)
        general_layout.addWidget(self.grid_size_slider)
        
        general_layout.addStretch()
        
        tab_widget.addTab(general_tab, "General")
        
        # Security settings
        security_tab = QWidget()
        security_layout = QVBoxLayout(security_tab)
        
        security_layout.addWidget(QLabel("Security Options:"))
        self.token_check = QCheckBox("Enable security tokens")
        self.token_check.setChecked(True)
        security_layout.addWidget(self.token_check)
        
        self.logging_check = QCheckBox("Enable security logging")
        self.logging_check.setChecked(True)
        security_layout.addWidget(self.logging_check)
        
        security_layout.addStretch()
        
        tab_widget.addTab(security_tab, "Security")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Application Launcher")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("LauncherApp")
    
    # Create and show main window
    window = LauncherMainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
