# # PSLV SplashScreen launch node - Updated with Modern Dark Theme
# # =============================================================================
# # This module contains the updated starting code for PSLV Launcher with modern dark theme
# # Single window that transitions from loading screen to main application
# # ***
#
import os
import sys
from time import sleep

import pandas as pd
import urllib3
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton, \
    QStackedWidget

from launcherui import MainWindow
from static import resource_path, BACKUP_PATH, BACKUP_FILE_NAME

# Suppress ssl warnings for sharepoint api calls
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COLORS = {
    'background_dark': '#0d1117',
    'surface_dark': '#161b22',
    'border_dark': '#30363d',
    'primary': '#138aec',
    'text_light': '#e6edf3',
    'text_dark': '#7d8590',
}


def fetch_cost_centers(site):
    """
    Fetch cost centers from SharePoint list.
    """
    try:
        # sp_list = site.List(COST_CENTER)
        # sp_data = sp_list.GetListItems(view_name=None)
        # df = pd.DataFrame(sp_data)
        # df.fillna(value='', inplace=True)
        df = pd.read_csv("cost_center.csv")
        return df
    except Exception as e:
        print(f'Error fetching cost centers: {str(e)}')
        return pd.DataFrame(columns=['cost_center_code', 'cost_center_name', 'is_gfbm'])


def fetch_user_data(site):
    """
    Fetch user data from SharePoint list.
    """
    try:
        # sp_list = site.List(USERBASE)
        # query = {'Where': [('Contains', 'sid', user_main)]}
        # sp_data = sp_list.GetListItems(query=query)
        # df = pd.DataFrame(sp_data)
        # df.fillna(value='', inplace=True)
        df = pd.read_csv("users.csv")
        return df
    except Exception as e:
        print(f'Error fetching user data: {str(e)}')
        return pd.DataFrame(columns=['sid', 'display_name', 'email', 'job_title', 'building_name', 'cost_center_id'])


class DataLoader(QThread):
    """
    DataLoader threaded class which loads the data from sharepoint while keeping UI live.
    """
    progress_updated = pyqtSignal(int, str)
    data_loaded = pyqtSignal(object, object, object)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        """
        Default run function for threaded processing
        """
        try:
            # os.makedirs(name=f"{os.environ.get('LOCALAPPDATA')}/{BACKUP_PATH}", exist_ok=True)
            #
            # user = getpass.getuser()
            # user = user.lower()
            #
            # # SharePoint client initialization
            # self.progress_updated.emit(5, "Initializing connection...")
            # cred = HttpNtlmAuth(SID, password='')
            #
            # self.progress_updated.emit(15, "Connecting to SharePoint...")
            # site = Site(SITE_URL, auth=cred, verify_ssl=False)
            #
            # self.progress_updated.emit(35, "Fetching application data...")
            # sp_list = site.List(SHAREPOINT_LIST)
            # sp_data = sp_list.GetListItems(view_name=None)
            # df_all = pd.DataFrame(sp_data)
            self.progress_updated.emit(10, "starting load...")
            sleep(10)
            processed_df = pd.read_csv("application.csv")
            # df_all.fillna(value='', inplace=True)
            # df_all['SIDs_For_SolutionAccess'] = df_all['SIDs_For_SolutionAccess'].str.lower()
            # df_all.fillna(value='', inplace=True)
            # all_df = df_all[df_all['SIDs_For_SolutionAccess'].str.contains('everyone', na=False)]
            # processed_df = df_all[df_all['SIDs_For_SolutionAccess'].str.contains(user, na=False)]

            # self.progress_updated.emit(60, "Processing user access...")
            # processed_df = pd.concat([all_df, processed_df])

            self.progress_updated.emit(75, "Saving local backup...")
            processed_df.reset_index(inplace=True)
            # processed_df.to_excel(excel_writer=f"{os.environ.get('LOCALAPPDATA')}/{BACKUP_PATH}/{BACKUP_FILE_NAME}",
            #                       index=False)

            self.progress_updated.emit(85, "Loading additional data...")
            cc = fetch_cost_centers("site")
            user_data = fetch_user_data("site")

            self.progress_updated.emit(100, "Loading complete!")
            self.data_loaded.emit(processed_df, cc, user_data)

        except Exception as e:
            error_msg = f'Error loading data: {str(e)}'
            print(error_msg)
            self.error_occurred.emit("Failed to connect to SharePoint. Loading from backup...")

            if os.path.exists(f"{os.environ.get('LOCALAPPDATA')}/{BACKUP_PATH}/{BACKUP_FILE_NAME}"):
                processed_df = pd.read_excel(f"{os.environ.get('LOCALAPPDATA')}/{BACKUP_PATH}/{BACKUP_FILE_NAME}")
                self.progress_updated.emit(100, "Loaded from backup")
                self.data_loaded.emit(processed_df, pd.DataFrame(), pd.DataFrame())
            else:
                processed_df = pd.DataFrame(
                    columns=['Expired', 'Solution_Name', 'Description', 'ApplicationExePath', 'Status', 'Release_Date',
                             'Validity_Period', 'Version_Number', 'UMAT_IAHub_ID'])
                self.error_occurred.emit("No backup data available. Please check your connection.")
                self.data_loaded.emit(processed_df, pd.DataFrame(), pd.DataFrame())


class LoadingScreen(QWidget):
    """Loading screen widget that will be shown first"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.can_cancel = False
        self.initUI()

    def initUI(self):
        # Main layout fills the entire window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Center container
        container = QFrame()
        container.setFixedSize(400, 200)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
        """)
        layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(20)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon/Logo area
        self.iconLabel = QLabel("📦")
        self.iconLabel.setStyleSheet(f"""
            font-size: 48px;
            color: {COLORS['primary']};
        """)
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.iconLabel)

        # Loading status label - this shows "Loading applications..."
        self.labelLoading = QLabel('Loading applications...')
        self.labelLoading.setStyleSheet(f"""
            font-size: 16px;
            color: {COLORS['text_light']};
            font-family: Inter, sans-serif;
            font-weight: 500;
        """)
        self.labelLoading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.labelLoading)

        # Progress bar with modern styling
        self.progressBar = QProgressBar()
        self.progressBar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {COLORS['border_dark']};
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 4px;
            }}
        """)
        self.progressBar.setTextVisible(False)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setFixedHeight(6)
        self.progressBar.setFixedWidth(300)
        container_layout.addWidget(self.progressBar, alignment=Qt.AlignmentFlag.AlignCenter)

    def updateProgress(self, value, task_name="Loading applications..."):
        """Update progress bar with real task feedback"""
        self.progressBar.setValue(value)
        # Keep the main loading text, don't change it based on task_name
        self.labelLoading.setText("Loading applications...")

    def onError(self, error_message):
        """Handle error messages"""
        self.labelLoading.setText(error_message)
        self.labelLoading.setStyleSheet(f"""
            font-size: 16px;
            color: #eab308;
            font-family: Inter, sans-serif;
            font-weight: 500;
        """)


class MainWindowWidget(QWidget):
    """Wrapper widget for MainWindow content"""

    def __init__(self, data, cost_centers, user_data):
        super().__init__()

        # Create the main window instance
        self.main_window = MainWindow(data, cost_centers, user_data)

        # Extract the central widget content
        main_content = self.main_window.centralWidget()

        # Create layout for this widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_content)

        # Apply the same styling as MainWindow
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background_dark']};
                font-family: Inter, sans-serif;
            }}
        """)


class ApplicationWindow(QMainWindow):
    """Single window that transitions from loading screen to main application"""

    def __init__(self):
        super().__init__()
        icon_path = resource_path(f"resources/STOJustLogo.PNG")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle('Software Center')

        # Set fixed size for both loading and main application - same size throughout
        self.setFixedSize(1400, 800)

        # Center the window on screen from the start
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background_dark']};
                font-family: Inter, sans-serif;
            }}
        """)

        # Create stacked widget to switch between loading and main app
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create and add loading screen
        self.loading_screen = LoadingScreen()
        self.stacked_widget.addWidget(self.loading_screen)

        # Initialize data loader
        self.initDataLoader()

        # Main window widget placeholder
        self.main_window_widget = None

    def initDataLoader(self):
        """Initialize data loader thread"""
        self.data_loader = DataLoader()
        self.data_loader.progress_updated.connect(self.loading_screen.updateProgress)
        self.data_loader.data_loaded.connect(self.onDataLoaded)
        self.data_loader.error_occurred.connect(self.loading_screen.onError)
        self.data_loader.start()

    def onDataLoaded(self, data, cost_centers, user_data):
        """Handle data loaded signal and transition to main application"""
        self.loading_screen.progressBar.setValue(100)

        # Small delay before transitioning
        QTimer.singleShot(500, lambda: self.showMainApplication(data, cost_centers, user_data))

    def showMainApplication(self, data, cost_centers, user_data):
        """Transition from loading screen to main application"""
        # Create main window content as a widget
        self.main_window_widget = MainWindowWidget(data, cost_centers, user_data)

        # Add to stacked widget
        self.stacked_widget.addWidget(self.main_window_widget)

        # Switch to main application (no resizing needed - same size throughout)
        self.stacked_widget.setCurrentWidget(self.main_window_widget)

        # Update window title
        self.setWindowTitle('PSLV by STD, GF&BM India')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set application-wide stylesheet for modern dark theme
    app.setStyleSheet(f"""
        * {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
    """)

    window = ApplicationWindow()
    window.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window...')