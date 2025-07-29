import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                           QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                           QLabel, QLineEdit, QMessageBox, QHeaderView, QStatusBar,
                           QDialog, QFormLayout, QDialogButtonBox, QFrame, QSplitter,
                           QToolBar, QAction, QMenu, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QColor, QIcon, QFont, QPalette, QPixmap, QCursor, QPainter, QBrush, QGradient
from shareplum import Site
from shareplum import Office365
from shareplum.site import Version
import json
import logging
import pandas as pd
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MaterialLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QLineEdit {
                border: none;
                border-bottom: 2px solid #cccccc;
                padding: 8px;
                background-color: #f5f5f5;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #2196F3;
                background-color: #e3f2fd;
            }
        """)
        self.setMinimumHeight(35)

class MaterialButton(QPushButton):
    def __init__(self, text, primary=True, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        
        if primary:
            color = "#2196F3"  # Blue
            hover_color = "#1976D2"  # Darker Blue
            text_color = "white"
        else:
            color = "#e0e0e0"  # Light Gray
            hover_color = "#bdbdbd"  # Darker Gray
            text_color = "#424242"  # Dark Text
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                margin: 1px;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(36)

class UpdateButton(MaterialButton):
    def __init__(self, row_index, *args, **kwargs):
        super().__init__("Update", primary=True, *args, **kwargs)
        self.row_index = row_index
        self.setEnabled(False)  # Initially disabled
        self.setFixedWidth(80)
        
        # Style for disabled state
        self.update_style()
    
    def update_style(self):
        if self.isEnabled():
            color = "#4CAF50"  # Green for enabled
            hover_color = "#45a049"
            text_color = "white"
        else:
            color = "#cccccc"  # Gray for disabled
            hover_color = "#cccccc"
            text_color = "#666666"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                margin: 1px;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)
    
    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.update_style()

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SharePoint Configuration")
        self.resize(450, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 8px;
            }
            QLabel {
                font-size: 14px;
                color: #424242;
                font-weight: bold;
            }
            QDialogButtonBox {
                border: none;
            }
        """)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create header
        header = QLabel("Connect to SharePoint")
        header.setStyleSheet("font-size: 18px; color: #1976D2; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Add description
        description = QLabel("Enter your SharePoint credentials to connect to your list data.")
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 12px; color: #757575; margin-bottom: 20px;")
        description.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description)
        
        # Create form layout
        form = QWidget()
        layout = QFormLayout(form)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Create input fields
        self.site_url = MaterialLineEdit()
        self.site_url.setPlaceholderText("https://contoso.sharepoint.com/sites/mysite")
        
        self.username = MaterialLineEdit()
        self.username.setPlaceholderText("your.email@example.com")
        
        self.password = MaterialLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Your password")
        
        self.list_name = MaterialLineEdit()
        self.list_name.setPlaceholderText("List Name")
        
        # Add fields to form
        layout.addRow("SharePoint Site URL:", self.site_url)
        layout.addRow("Username:", self.username)
        layout.addRow("Password:", self.password)
        layout.addRow("List Name:", self.list_name)
        
        main_layout.addWidget(form)
        
        # Add button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 10, 20, 10)
        
        # Add buttons
        cancel_button = MaterialButton("Cancel", primary=False)
        connect_button = MaterialButton("Connect")
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(connect_button)
        
        main_layout.addWidget(button_container)
        
        # Connect signals
        connect_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        # Load saved config if exists
        self.load_config()
    
    def load_config(self):
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as file:
                    config = json.load(file)
                    self.site_url.setText(config.get('site_url', ''))
                    self.username.setText(config.get('username', ''))
                    # Don't load password for security reasons
                    self.list_name.setText(config.get('list_name', ''))
            except Exception as e:
                logger.error(f"Error loading config: {e}")
    
    def save_config(self):
        config = {
            'site_url': self.site_url.text(),
            'username': self.username.text(),
            'list_name': self.list_name.text()
        }
        try:
            with open('config.json', 'w') as file:
                json.dump(config, file)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_values(self):
        return {
            'site_url': self.site_url.text(),
            'username': self.username.text(),
            'password': self.password.text(),
            'list_name': self.list_name.text()
        }

class MaterialTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e0e0e0;
                border: none;
                border-radius: 4px;
                selection-background-color: #e3f2fd;
                selection-color: #212121;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
                color: #424242;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #212121;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px;
                font-size: 14px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #bdbdbd;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

class SearchBox(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchBox")
        self.setStyleSheet("""
            #searchBox {
                background-color: #f5f5f5;
                border-radius: 20px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Search icon (simulated with a label)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #757575;")
        layout.addWidget(search_icon)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search records...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                font-size: 14px;
                background-color: transparent;
            }
        """)
        layout.addWidget(self.search_input)

class SharepointTableApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.sharepoint_site = None
        self.sharepoint_list = None
        self.df = pd.DataFrame()  # Initialize empty DataFrame
        self.original_df = pd.DataFrame()  # Keep original data for comparison
        self.columns = []
        self.update_buttons = []  # Store update buttons
        self.connected = False
        
        # Set app-wide font
        font = QFont("Segoe UI", 10)
        QApplication.setFont(font)
        
        # Open configuration on startup
        self.show_config_dialog()
    
    def initUI(self):
        self.setWindowTitle("SharePoint List Editor")
        self.setGeometry(100, 100, 1400, 800)  # Slightly wider to accommodate update buttons
        
        # Set stylesheet for the entire application
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QStatusBar {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # Create central widget with a card-like appearance
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 8px;
            margin: 10px;
        """)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("SharePoint List Editor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1976D2;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Create toolbar with material design buttons
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)
        
        self.connect_btn = MaterialButton("Connect", primary=True)
        self.connect_btn.clicked.connect(self.show_config_dialog)
        toolbar_layout.addWidget(self.connect_btn)
        
        self.refresh_btn = MaterialButton("Refresh Data", primary=True)
        self.refresh_btn.clicked.connect(self.fetch_data)
        self.refresh_btn.setEnabled(False)
        toolbar_layout.addWidget(self.refresh_btn)
        
        # Remove the bulk save button since we're using individual row updates
        
        header_layout.addWidget(toolbar_widget)
        
        # Add header to main layout
        main_layout.addWidget(header_widget)
        
        # Add a divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #e0e0e0; height: 1px;")
        main_layout.addWidget(divider)
        
        # Add search box
        search_box = SearchBox()
        self.search_input = search_box.search_input
        self.search_input.textChanged.connect(self.filter_table)
        main_layout.addWidget(search_box)
        
        # Create table widget with Material Design
        self.table = MaterialTableWidget()
        self.table.cellChanged.connect(self.on_cell_changed)
        main_layout.addWidget(self.table)
        
        # Create status bar with progress indicator
        status_layout = QHBoxLayout()
        self.connection_status = QLabel("Not connected to SharePoint")
        self.connection_status.setStyleSheet("color: #757575;")
        status_layout.addWidget(self.connection_status)
        
        status_layout.addStretch()
        
        self.record_count = QLabel("0 records")
        self.record_count.setStyleSheet("color: #757575;")
        status_layout.addWidget(self.record_count)
        
        main_layout.addLayout(status_layout)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Not connected to SharePoint")
        
        self.setCentralWidget(central_widget)
    
    def show_config_dialog(self):
        dialog = ConfigDialog(self)
        if dialog.exec_():
            dialog.save_config()
            config = dialog.get_values()
            self.connect_to_sharepoint(config)
    
    def connect_to_sharepoint(self, config):
        try:
            self.status_bar.showMessage("Connecting to SharePoint...")
            self.connection_status.setText("Connecting...")
            self.connection_status.setStyleSheet("color: #FFA000;") # Amber color for connecting
            
            # Show an animated progress UI effect
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            self.site_url = config['site_url']
            self.username = config['username']
            self.password = config['password']
            self.list_name = config['list_name']
            
            # Connect to SharePoint
            authcookie = Office365(self.site_url, username=self.username, password=self.password).GetCookies()
            self.sharepoint_site = Site(self.site_url, version=Version.v365, authcookie=authcookie)
            self.sharepoint_list = self.sharepoint_site.List(self.list_name)
            
            self.connected = True
            self.refresh_btn.setEnabled(True)
            
            # Update UI to show connected state
            self.connection_status.setText("Connected to SharePoint")
            self.connection_status.setStyleSheet("color: #4CAF50;") # Green color for success
            self.connect_btn.setText("Reconnect")
            
            self.status_bar.showMessage("Connected to SharePoint. Fetching data...")
            self.fetch_data()
            
            QApplication.restoreOverrideCursor()
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            logger.error(f"Error connecting to SharePoint: {e}")
            
            # Update UI to show error state
            self.connection_status.setText("Connection Failed")
            self.connection_status.setStyleSheet("color: #F44336;") # Red color for error
            
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to SharePoint: {str(e)}")
            self.status_bar.showMessage("Connection failed")
            self.connected = False
    
    def fetch_data(self):
        if not self.connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to SharePoint first.")
            return
        
        try:
            # Show loading state
            self.status_bar.showMessage("Fetching data...")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.table.setEnabled(False)
            
            # Get data from SharePoint list
            data = self.sharepoint_list.GetListItems()
            
            # Convert to DataFrame
            if data:
                self.df = pd.DataFrame(data)
                self.original_df = self.df.copy()  # Keep original for comparison
                self.columns = list(self.df.columns)
            else:
                self.df = pd.DataFrame()
                self.original_df = pd.DataFrame()
                self.columns = []
            
            # Restore UI state
            QApplication.restoreOverrideCursor()
            self.table.setEnabled(True)
            
            if self.df.empty:
                self.status_bar.showMessage("No data found in the list")
                self.record_count.setText("0 records")
                return
            
            # Set up table
            self.setup_table()
            self.status_bar.showMessage(f"Loaded {len(self.df)} rows from SharePoint")
            
            # Show success animation - pulse the table briefly
            original_style = self.table.styleSheet()
            self.table.setStyleSheet(original_style + "border: 2px solid #4CAF50;") # Green border
            QTimer.singleShot(800, lambda: self.table.setStyleSheet(original_style)) # Reset after animation
            
        except Exception as e:
            # Restore UI state
            QApplication.restoreOverrideCursor()
            self.table.setEnabled(True)
            
            logger.error(f"Error fetching data: {e}")
            QMessageBox.critical(self, "Data Error", f"Failed to fetch data: {str(e)}")
            self.status_bar.showMessage("Failed to fetch data")
    
    def setup_table(self):
        # Clear
