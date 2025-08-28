"""
Solution Launcher Window - FIXED VERSION
================================================================================
This Module contains the refactored code for the PSLV Launcher with improved architecture,
responsive design, and better navigation patterns.

Key Improvements:
- Responsive layout instead of fixed window size
- Better component separation
- Improved search functionality with real-time feedback
- Consistent navigation patterns
"""

# Python default package imports
import getpass
import os
import shutil
from datetime import datetime, timedelta

# Python third party package imports
import awmpy
import pandas as pd
import numpy as np
import urllib3
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont, QDesktopServices, QMouseEvent
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGridLayout, QFrame, QProgressBar, QMessageBox,
                             QScrollArea, QStackedLayout, QSpacerItem, QMenu, QStackedWidget, QDialog, QSizePolicy)
from requests_ntlm import HttpNtlmAuth
from shareplum import Site

# User created module for functionalities
from access import AccessControlDialog
from security_check import LauncherSecurity
from static import resource_path, BETA, UAT, PROD, APP_DIR, expire_sort, DETAILS, SITE_URL, SID, SHAREPOINT_LIST, \
    BACKUP_FILE_NAME, BACKUP_PATH, STO_CONFIG, LOB, ADMIN, pslv_action_entry, add_new_user_to_userbase

# global variable for user id
user_main = getpass.getuser()


class SearchBar(QWidget):
    """Separated search bar component with real-time feedback"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)
        
        # Search input with improved styling
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search applications... (start typing for instant results)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 12px 15px;
                font-size: 14px;
                background-color: transparent;
                font-family: Montserrat, serif;
            }
            QLineEdit:focus {
                outline: none;
            }
        """)
        
        # Results counter
        self.results_label = QLabel("")
        self.results_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                font-style: italic;
                padding: 5px;
            }
        """)
        
        # Refresh button
        self.refresh_button = QPushButton("⟲")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setToolTip("Refresh Applications")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #000000;
                font-size: 20px;
                padding: 5px;
                min-width: 30px;
                font-weight: bold;
                border-radius: 15px;
            }
            QPushButton:hover {
                color: #4a90e2;
                background-color: #f0f0f0;
            }
        """)
        
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.results_label)
        layout.addWidget(self.refresh_button)
        
        # Style the container
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                border-radius: 20px;
                background-color: white;
                margin-bottom: 10px;
            }
            QWidget:focus-within {
                border-color: #4a90e2;
            }
        """)
        
    def update_results_count(self, count, total):
        """Update the results counter with real-time feedback"""
        if count == total:
            self.results_label.setText(f"{total} applications")
        else:
            self.results_label.setText(f"{count} of {total} applications")


class ApplicationGrid(QWidget):
    """Separated application grid component with responsive layout"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_tiles = []
        self.visible_tiles = []
        self.setup_ui()
        
    def setup_ui(self):
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)
        
        # Create scroll content
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_area.setWidget(self.scroll_content)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
        
    def add_tiles(self, tiles):
        """Add application tiles to the grid"""
        self.all_tiles = tiles
        self.update_layout("")
        
    def update_layout(self, filter_text):
        """Update grid layout with filtering"""
        # Clear current layout
        self.clear_layout()
        
        # Filter tiles
        self.visible_tiles = [
            tile for tile in self.all_tiles
            if filter_text.lower() in tile.app_name.lower()
        ]
        
        # Calculate responsive columns based on available width
        # This replaces the fixed 3-column layout
        columns = max(1, min(4, self.width() // 300))  # Responsive columns
        
        # Add filtered tiles to grid
        for i, tile in enumerate(self.visible_tiles):
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(tile, row, col)
            tile.setVisible(True)
            
        # Add stretch to maintain alignment
        if self.visible_tiles:
            self.grid_layout.setRowStretch(len(self.visible_tiles) // columns + 1, 1)
            
    def clear_layout(self):
        """Clear the grid layout"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                
    def get_visible_count(self):
        """Get count of visible tiles"""
        return len(self.visible_tiles)
        
    def get_total_count(self):
        """Get total count of tiles"""
        return len(self.all_tiles)


class Sidebar(QWidget):
    """Separated sidebar component"""
    
    access_control_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()
    
    def __init__(self, user_details, is_admin=False, parent=None):
        super().__init__(parent)
        self.user_details = user_details
        self.is_admin = is_admin
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedWidth(250)
        self.setStyleSheet("""
            QWidget {
                background-color: #242526;
                color: white;
                font-family: Montserrat, serif;
            }
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                padding: 10px;
                margin: 10px 5px;
                border-radius: 5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5b4bc7;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Logo
        logo_label = QLabel()
        logo_path = resource_path("/images/logo.jpg")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Spacer
        layout.addItem(QSpacerItem(10, 50))
        
        # User details
        for label, icon_name in self.user_details:
            detail_widget = self.create_detail_widget(label, icon_name)
            layout.addWidget(detail_widget)
            
        layout.addStretch()
        
        # Access control button (only for admins)
        if self.is_admin:
            self.access_control_button = QPushButton("Access Management")
            self.access_control_button.setStyleSheet("""
                QPushButton {
                    background-color: #2670A9;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3380CD;
                }
            """)
            self.access_control_button.clicked.connect(self.access_control_clicked.emit)
            layout.addWidget(self.access_control_button)
            
        # Exit button
        exit_button = QPushButton("Exit")
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #A6150B;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C42010;
            }
        """)
        exit_button.clicked.connect(self.exit_clicked.emit)
        layout.addWidget(exit_button)
        
    def create_detail_widget(self, value, icon_name):
        """Create user detail widget"""
        widget = QFrame()
        widget.setStyleSheet("QFrame { padding: 2px; }")
        
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Icon
        icon_label = QLabel()
        icon_path = resource_path(f"resources/{icon_name}")
        icon = QIcon(icon_path)
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(25, 25))
        layout.addWidget(icon_label)
        
        # Text
        text_label = QLabel(value)
        text_label.setFont(QFont('Montserrat', 10, QFont.Weight.DemiBold))
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        layout.addStretch()
        return widget


# Import the existing ApplicationTile and other classes from the original file
# (keeping them as they are since they're working well)
from launcherui import ApplicationTile, NoAccessWidget, EnvironmentLabel, InstallThread


class MainWindow(QMainWindow):
    """
    Refactored Main window with improved architecture and responsive design
    """
    
    def __init__(self, df, cost_center, userdata):
        super().__init__()
        self.access = df
        self.cost_center_df = cost_center
        self.userdata = userdata
        self.user_details = self.get_user_details()
        self.is_gfbm_user = self.is_gfbm_user_check()
        self.username = user_main
        
        # Initialize components
        self.search_bar = None
        self.app_grid = None
        self.sidebar = None
        self.access_control_widget = None
        
        self.setup_window()
        self.setup_ui()
        self.load_initial_data()
        
    def setup_window(self):
        """Setup main window properties with responsive design"""
        self.setWindowTitle("PSLV by STO, GF&BM India")
        icon_path = resource_path("resources/STOJustLogo.PNG")
        self.setWindowIcon(QIcon(icon_path))
        
        # FIXED: Replace fixed size with minimum size and responsive behavior
        self.setMinimumSize(1000, 600)  # Minimum usable size
        self.resize(1200, 720)  # Default size, but resizable
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f2f4f6;
                font-family: Montserrat, serif;
            }
        """)
        
    def setup_ui(self):
        """Setup the main UI with improved component separation"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create sidebar
        is_admin = self.is_administrator()
        self.sidebar = Sidebar(self.user_details, is_admin)
        self.sidebar.access_control_clicked.connect(self.show_access_control)
        self.sidebar.exit_clicked.connect(self.close)
        main_layout.addWidget(self.sidebar)
        
        # Create content area
        content_area = self.create_content_area()
        main_layout.addWidget(content_area, 1)  # Stretch factor for responsive behavior
        
    def create_content_area(self):
        """Create the main content area with responsive layout"""
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QVBoxLayout(content_widget)
        
        # Header logo
        logo_label = QLabel()
        logo_path = resource_path("resources/Full /images/Logo.jpg")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
        content_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        
        # Applications view
        apps_widget = self.create_applications_view()
        self.stacked_widget.addWidget(apps_widget)
        
        # Access control view (placeholder for now)
        if hasattr(self, 'access_control_widget') and self.access_control_widget:
            self.stacked_widget.addWidget(self.access_control_widget)
        else:
            placeholder = QLabel("Access Control Panel")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stacked_widget.addWidget(placeholder)
            
        content_layout.addWidget(self.stacked_widget, 1)
        
        # Footer
        footer = self.create_footer()
        content_layout.addWidget(footer)
        
        return content_widget
        
    def create_applications_view(self):
        """Create the applications view with search and grid"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search bar with real-time feedback
        self.search_bar = SearchBar()
        self.search_bar.search_input.textChanged.connect(self.on_search_changed)
        self.search_bar.refresh_button.clicked.connect(self.refresh_applications)
        layout.addWidget(self.search_bar)
        
        # Application grid
        self.app_grid = ApplicationGrid()
        layout.addWidget(self.app_grid, 1)
        
        return widget
        
    def create_footer(self):
        """Create footer with version info"""
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 2, 0, 0)
        
        version_label = QLabel("PSLV by STO v3.1 - Enhanced")
        version_label.setStyleSheet("""
            QLabel {
                color: #595858;
                font-size: 11px;
                font-style: italic;
                font-family: Montserrat, serif;
            }
        """)
        
        footer_layout.addStretch()
        footer_layout.addWidget(version_label)
        
        return footer_widget
        
    def load_initial_data(self):
        """Load initial application data"""
        if len(self.access) != 0 and self.is_gfbm_user:
            self.load_applications()
        else:
            # Show no access widget
            no_access = NoAccessWidget(self.is_gfbm_user)
            self.app_grid.grid_layout.addWidget(no_access, 0, 0, Qt.AlignmentFlag.AlignCenter)
            
    def load_applications(self):
        """Load applications with improved error handling"""
        try:
            # Process and sort data
            self.access['Expired'] = self.access.apply(lambda row: expire_sort(row), axis=1)
            self.access = self.access.sort_values(by=['Expired', 'Solution_Name'], ascending=[True, True])
            self.access.reset_index(inplace=True, drop=True)
            
            # Create application tiles
            tiles = []
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
                tiles.append(tile)
                
            # Add tiles to grid
            self.app_grid.add_tiles(tiles)
            self.update_search_results()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load applications: {str(e)}")
            
    def on_search_changed(self, text):
        """Handle search text changes with real-time feedback"""
        if self.app_grid:
            self.app_grid.update_layout(text)
            self.update_search_results()
            
    def update_search_results(self):
        """Update search results counter"""
        if self.search_bar and self.app_grid:
            visible = self.app_grid.get_visible_count()
            total = self.app_grid.get_total_count()
            self.search_bar.update_results_count(visible, total)
            
    def show_access_control(self):
        """Toggle between applications and access control views"""
        current_index = self.stacked_widget.currentIndex()
        if current_index == 0:
            self.stacked_widget.setCurrentIndex(1)
            if hasattr(self.sidebar, 'access_control_button'):
                self.sidebar.access_control_button.setText("Applications")
        else:
            self.stacked_widget.setCurrentIndex(0)
            if hasattr(self.sidebar, 'access_control_button'):
                self.sidebar.access_control_button.setText("Access Management")
                
    def refresh_applications(self):
        """Refresh applications with improved feedback"""
        if self.search_bar:
            self.search_bar.search_input.clear()
            
        try:
            # Show loading feedback
            if self.search_bar:
                self.search_bar.results_label.setText("Refreshing...")
                
            # Refresh data (simplified version of the original refresh logic)
            user = user_main.lower()
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            cred = HttpNtlmAuth(SID, password="")
            site = Site(SITE_URL, auth=cred, verify_ssl=False)
            
            sp_list = site.List(SHAREPOINT_LIST)
            sp_data = sp_list.GetListItems(view_name=None)
            df_all = pd.DataFrame(sp_data)
            df_all.fillna(value='', inplace=True)
            df_all['SIDs_For_SolutionAccess'] = df_all['SIDs_For_SolutionAccess'].str.lower()
            
            all_df = df_all[df_all['SIDs_For_SolutionAccess'].str.contains('everyone', na=False)]
            processed_df = df_all[df_all['SIDs_For_SolutionAccess'].str.contains(user, na=False)]
            processed_df = pd.concat([all_df, processed_df])
            processed_df.reset_index(inplace=True, drop=True)
            
            self.access = processed_df
            
            if len(self.access) > 0:
                self.load_applications()
            else:
                self.app_grid.clear_layout()
                no_access = NoAccessWidget(self.is_gfbm_user)
                self.app_grid.grid_layout.addWidget(no_access, 0, 0, Qt.AlignmentFlag.AlignCenter)
                
            QMessageBox.information(self, "Success", "Applications refreshed successfully!")
            
        except Exception as e:
            # Fallback to backup data
            backup_path = f"{os.environ.get('USERPROFILE')}/{BACKUP_PATH}/{BACKUP_FILE_NAME}"
            if os.path.exists(backup_path):
                try:
                    self.access = pd.read_excel(backup_path)
                    self.load_applications()
                    QMessageBox.warning(self, "Offline Mode", "Loaded from backup data. Some information may be outdated.")
                except:
                    QMessageBox.critical(self, "Error", "Failed to refresh applications and backup data is corrupted.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to refresh applications: {str(e)}")
                
    def resizeEvent(self, event):
        """Handle window resize for responsive behavior"""
        super().resizeEvent(event)
        if self.app_grid:
            # Update grid layout when window is resized
            QTimer.singleShot(100, lambda: self.app_grid.update_layout(
                self.search_bar.search_input.text() if self.search_bar else ""
            ))
            
    # Keep the existing methods from the original MainWindow
    def get_user_details(self):
        """Get user details (keeping original implementation)"""
        try:
            if self.userdata.empty:
                data = awmpy.get_phonebook_data(user_main)
                self.cost_center = data['costCenterID']
                data['email'] = data['email'].replace('@', '@ ')
                details = [
                    (data['standardID'], 'icons8-id-50.png'),
                    (data['nameFull'], 'icons8-user-64.png'),
                    (data['email'], 'icons8-email-50.png'),
                    (data['jobTitle'], 'icons8-new-job-50.png'),
                    (data['buildingName'], '/images/photo1756414685.jpg')
                ]
                add_new_user_to_userbase([
                    data['standardID'], data['nameFull'], data['email'], 
                    data['jobTitle'], data['buildingName'], data['costCenterID']
                ])
            else:
                self.cost_center = self.userdata['cost_center_id'].values[0]
                details = [
                    (self.userdata['sid'].values[0], 'icons8-id-50.png'),
                    (self.userdata['display_name'].values[0], 'icons8-user-64.png'),
                    (self.userdata['email'].values[0], 'icons8-email-50.png'),
                    (self.userdata['job_title'].values[0], 'icons8-new-job-50.png'),
                    (self.userdata['building_name'].values[0], '/images/photo1756414685.jpg')
                ]
        except:
            details = DETAILS
        return details
        
    def is_administrator(self):
        """Check if user is administrator (keeping original implementation)"""
        try:
            cred = HttpNtlmAuth(SID, password="")
            site = Site(SITE_URL, auth=cred, verify_ssl=False)
            sp_list = site.List(ADMIN)
            query = {'Where': [('Contains', 'sid', user_main)]}
            sp_data = sp_list.GetListItems(query=query)
            df = pd.DataFrame(sp_data)
            df.fillna(value='', inplace=True)
            managed_lob = df['lob'].tolist()
            self.access_control_widget = AccessControlDialog(self.username, managed_lob)
            return len(managed_lob) > 0
        except:
            self.access_control_widget = QDialog()
            return False
            
    def is_gfbm_user_check(self):
        """Check if user is GFBM user (keeping original implementation)"""
        self.cost_center_df['cost_center_code'] = self.cost_center_df['cost_center_code'].astype(str)
        cc_column = self.cost_center_df['cost_center_code'].to_list()
        return self.cost_center in cc_column