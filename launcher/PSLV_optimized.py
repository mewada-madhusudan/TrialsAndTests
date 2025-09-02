# PSLV SplashScreen launch node - OPTIMIZED VERSION
# =============================================================================
# This module contains the optimized starting code for PSLV Launcher with performance improvements
# Key optimizations:
# - SharePoint connection pooling and caching
# - Async operations where possible
# - Progressive UI loading
# - Optimized DataFrame operations
# ***

import getpass
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import json
from datetime import datetime, timedelta

# Lazy imports to reduce startup time
def get_pandas():
    global pd
    if 'pd' not in globals():
        import pandas as pd
    return pd

def get_urllib3():
    global urllib3
    if 'urllib3' not in globals():
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return urllib3

def get_pyqt_modules():
    global Qt, QThread, pyqtSignal, QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton, QIcon, QTimer
    if 'Qt' not in globals():
        from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton
    return Qt, QThread, pyqtSignal, QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton, QIcon, QTimer

def get_sharepoint_modules():
    global HttpNtlmAuth, Site
    if 'HttpNtlmAuth' not in globals():
        from requests_ntlm import HttpNtlmAuth
        from sharepoint import Site
    return HttpNtlmAuth, Site

# Import static constants immediately (lightweight)
from static import resource_path, SID, SITE_URL, BACKUP_PATH, SHAREPOINT_LIST, BACKUP_FILE_NAME, LABEL_TEXT, USERBASE, user_main, COST_CENTER

# Cache manager for SharePoint data
class CacheManager:
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = f"{os.environ.get('LOCALAPPDATA')}/{BACKUP_PATH}/cache"
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_timeout = 300  # 5 minutes
    
    def get_cache_path(self, cache_key):
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def is_cache_valid(self, cache_key):
        cache_path = self.get_cache_path(cache_key)
        if not os.path.exists(cache_path):
            return False
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', '1970-01-01'))
            return (datetime.now() - cache_time).total_seconds() < self.cache_timeout
        except:
            return False
    
    def get_cached_data(self, cache_key):
        if not self.is_cache_valid(cache_key):
            return None
        
        try:
            cache_path = self.get_cache_path(cache_key)
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            return cache_data.get('data')
        except:
            return None
    
    def save_to_cache(self, cache_key, data):
        try:
            cache_path = self.get_cache_path(cache_key)
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Cache save error: {e}")

# SharePoint connection manager with pooling
class SharePointManager:
    _instance = None
    _connection_pool = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache_manager = CacheManager()
        return cls._instance
    
    def get_connection(self, site_url):
        if site_url not in self._connection_pool:
            HttpNtlmAuth, Site = get_sharepoint_modules()
            cred = HttpNtlmAuth(SID, password='')
            self._connection_pool[site_url] = Site(site_url, auth=cred, verify_ssl=False)
        return self._connection_pool[site_url]
    
    def fetch_with_cache(self, list_name, cache_key, fetch_func):
        # Try cache first
        cached_data = self.cache_manager.get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fetch fresh data
        try:
            data = fetch_func()
            self.cache_manager.save_to_cache(cache_key, data)
            return data
        except Exception as e:
            print(f"SharePoint fetch error: {e}")
            # Return cached data even if expired as fallback
            cache_path = self.cache_manager.get_cache_path(cache_key)
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        cache_data = json.load(f)
                    return cache_data.get('data')
                except:
                    pass
            return None

# Optimized data fetching functions
@lru_cache(maxsize=32)
def fetch_cost_centers_optimized(site_url):
    """Optimized cost centers fetch with caching"""
    def _fetch():
        site = SharePointManager().get_connection(site_url)
        sp_list = site.List(COST_CENTER)
        sp_data = sp_list.GetListItems(view_name=None)
        
        pd = get_pandas()
        df = pd.DataFrame(sp_data)
        # Optimized fillna operation
        df = df.fillna('', limit=None)
        return df.to_dict('records')
    
    return SharePointManager().fetch_with_cache(COST_CENTER, f"cost_centers_{user_main}", _fetch)

@lru_cache(maxsize=32)
def fetch_user_data_optimized(site_url):
    """Optimized user data fetch with caching"""
    def _fetch():
        site = SharePointManager().get_connection(site_url)
        sp_list = site.List(USERBASE)
        query = {'Where': [('Contains', 'sid', user_main)]}
        sp_data = sp_list.GetListItems(query=query)
        
        pd = get_pandas()
        df = pd.DataFrame(sp_data)
        # Optimized fillna operation
        df = df.fillna('', limit=None)
        return df.to_dict('records')
    
    return SharePointManager().fetch_with_cache(USERBASE, f"user_data_{user_main}", _fetch)

class OptimizedDataLoader(QThread):
    """Optimized DataLoader with parallel operations and caching"""
    progress_updated = pyqtSignal(int, str)
    data_loaded = pyqtSignal(object, object, object)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.sharepoint_manager = SharePointManager()
        
    def run(self):
        try:
            # Create backup directory
            os.makedirs(name=f"{os.environ.get('LOCALAPPDATA')}/{BACKUP_PATH}", exist_ok=True)
            
            user = getpass.getuser().lower()
            
            # Progress tracking
            self.progress_updated.emit(5, "Checking cache...")
            
            # Try to load from cache first for immediate UI response
            cached_main_data = self.sharepoint_manager.cache_manager.get_cached_data(f"main_data_{user}")
            if cached_main_data:
                self.progress_updated.emit(30, "Loading from cache...")
                pd = get_pandas()
                processed_df = pd.DataFrame(cached_main_data)
                
                # Load additional data in parallel while showing cached main data
                with ThreadPoolExecutor(max_workers=2) as executor:
                    cc_future = executor.submit(self._load_cost_centers)
                    user_future = executor.submit(self._load_user_data)
                    
                    self.progress_updated.emit(60, "Loading additional data...")
                    cc_data = cc_future.result()
                    user_data = user_future.result()
                
                self.progress_updated.emit(100, "Cache loaded!")
                self.data_loaded.emit(processed_df, cc_data, user_data)
                
                # Refresh data in background
                threading.Thread(target=self._refresh_data_background, daemon=True).start()
                return
            
            # If no cache, load fresh data
            self.progress_updated.emit(15, "Connecting to SharePoint...")
            site = self.sharepoint_manager.get_connection(SITE_URL)
            
            self.progress_updated.emit(35, "Fetching application data...")
            
            # Parallel data fetching
            with ThreadPoolExecutor(max_workers=3) as executor:
                main_future = executor.submit(self._fetch_main_data, site, user)
                cc_future = executor.submit(self._load_cost_centers)
                user_future = executor.submit(self._load_user_data)
                
                # Get main data
                processed_df = main_future.result()
                self.progress_updated.emit(75, "Processing data...")
                
                # Get additional data
                cc_data = cc_future.result()
                user_data = user_future.result()
            
            self.progress_updated.emit(85, "Saving backup...")
            # Save to both Excel and cache
            self._save_backup(processed_df)
            
            self.progress_updated.emit(100, "Loading complete!")
            self.data_loaded.emit(processed_df, cc_data, user_data)
            
        except Exception as e:
            self._handle_error(str(e))
    
    def _fetch_main_data(self, site, user):
        """Fetch and process main application data"""
        sp_list = site.List(SHAREPOINT_LIST)
        sp_data = sp_list.GetListItems(view_name=None)
        
        pd = get_pandas()
        df_all = pd.DataFrame(sp_data)
        
        # Optimized DataFrame operations
        df_all = df_all.fillna('', limit=None)  # Vectorized operation
        df_all['SIDs_For_SolutionAccess'] = df_all['SIDs_For_SolutionAccess'].str.lower()
        
        # Vectorized filtering
        all_df = df_all[df_all['SIDs_For_SolutionAccess'].str.contains('everyone', na=False)]
        user_df = df_all[df_all['SIDs_For_SolutionAccess'].str.contains(user, na=False)]
        
        processed_df = pd.concat([all_df, user_df], ignore_index=True)
        
        # Cache the processed data
        self.sharepoint_manager.cache_manager.save_to_cache(
            f"main_data_{user}", 
            processed_df.to_dict('records')
        )
        
        return processed_df
    
    def _load_cost_centers(self):
        """Load cost centers data"""
        data = fetch_cost_centers_optimized(SITE_URL)
        if data:
            pd = get_pandas()
            return pd.DataFrame(data)
        return pd.DataFrame()
    
    def _load_user_data(self):
        """Load user data"""
        data = fetch_user_data_optimized(SITE_URL)
        if data:
            pd = get_pandas()
            return pd.DataFrame(data)
        return pd.DataFrame()
    
    def _save_backup(self, df):
        """Save backup to Excel"""
        try:
            df.reset_index(inplace=True)
            df.to_excel(
                excel_writer=f"{os.environ.get('LOCALAPPDATA')}/{BACKUP_PATH}/{BACKUP_FILE_NAME}",
                index=False
            )
        except Exception as e:
            print(f"Backup save error: {e}")
    
    def _refresh_data_background(self):
        """Refresh data in background after cache load"""
        try:
            time.sleep(2)  # Small delay to not interfere with UI
            user = getpass.getuser().lower()
            site = self.sharepoint_manager.get_connection(SITE_URL)
            
            # Refresh main data
            fresh_df = self._fetch_main_data(site, user)
            
            # Refresh additional data
            with ThreadPoolExecutor(max_workers=2) as executor:
                cc_future = executor.submit(self._load_cost_centers)
                user_future = executor.submit(self._load_user_data)
                cc_data = cc_future.result()
                user_data = user_future.result()
            
            # Save fresh backup
            self._save_backup(fresh_df)
            
        except Exception as e:
            print(f"Background refresh error: {e}")
    
    def _handle_error(self, error_msg):
        """Handle errors with fallback to backup"""
        print(f'Error loading data: {error_msg}')
        self.error_occurred.emit("Failed to connect to SharePoint. Loading from backup...")
        
        # Try to load from backup
        backup_path = f"{os.environ.get('LOCALAPPDATA')}/{BACKUP_PATH}/{BACKUP_FILE_NAME}"
        if os.path.exists(backup_path):
            try:
                pd = get_pandas()
                processed_df = pd.read_excel(backup_path)
                self.progress_updated.emit(100, "Loaded from backup")
                self.data_loaded.emit(processed_df, pd.DataFrame(), pd.DataFrame())
                return
            except Exception as e:
                print(f"Backup load error: {e}")
        
        # Create empty DataFrame as last resort
        pd = get_pandas()
        processed_df = pd.DataFrame(
            columns=['Expired', 'Solution_Name', 'Description', 'ApplicationExePath', 'Status', 
                    'Release_Date', 'Validity_Period', 'Version_Number', 'UMAT_IAHub_ID']
        )
        self.error_occurred.emit("No backup data available. Please check your connection.")
        self.data_loaded.emit(processed_df, pd.DataFrame(), pd.DataFrame())

class OptimizedSplashScreen(QWidget):
    """Optimized SplashScreen with progressive loading"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize critical UI components first
        self.setup_critical_ui()
        
        # Initialize data loader
        self.init_data_loader()
        
        # Load secondary UI components progressively
        Qt, QThread, pyqtSignal, QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton, QIcon, QTimer = get_pyqt_modules()
        QTimer.singleShot(50, self.setup_secondary_ui)
        QTimer.singleShot(100, self.apply_styles)
    
    def setup_critical_ui(self):
        """Setup only critical UI components for immediate display"""
        Qt, QThread, pyqtSignal, QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton, QIcon, QTimer = get_pyqt_modules()
        
        # Window setup
        icon_path = resource_path(f"resources/STOJustLogo.PNG")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle('STO Application Launcher')
        self.setFixedSize(1100, 500)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Basic layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.frame = QFrame()
        layout.addWidget(self.frame)
        
        # Essential labels
        self.labelTitle = QLabel(self.frame)
        self.labelTitle.setObjectName('LabelTitle')
        self.labelTitle.resize(self.width() - 10, 150)
        self.labelTitle.move(0, 40)
        self.labelTitle.setText('Python Solution Launcher for VDI')
        self.labelTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progressBar = QProgressBar(self.frame)
        self.progressBar.resize(self.width() - 200 - 10, 50)
        self.progressBar.move(100, 250)
        self.progressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progressBar.setFormat('%p%')
        self.progressBar.setTextVisible(True)
        self.progressBar.setRange(minimum=0, maximum=100)
        self.progressBar.setValue(0)
        
        # Loading label
        self.labelLoading = QLabel(self.frame)
        self.labelLoading.resize(self.width() - 10, 50)
        self.labelLoading.move(0, 320)
        self.labelLoading.setObjectName('LabelLoading')
        self.labelLoading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelLoading.setText('Initializing...')
        
        # Initialize variables
        self.counter = 0
        self.n = 100
        self.processed_data = None
        self.can_cancel = False
    
    def setup_secondary_ui(self):
        """Setup secondary UI components"""
        Qt, QThread, pyqtSignal, QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton, QIcon, QTimer = get_pyqt_modules()
        
        # Description label
        self.labelDescription = QLabel(self.frame)
        self.labelDescription.resize(self.width() - 10, 50)
        self.labelDescription.move(0, 190)
        self.labelDescription.setObjectName('LabelDesc')
        self.labelDescription.setText(LABEL_TEXT)
        self.labelDescription.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Cancel button
        self.cancelButton = QPushButton("Cancel", self.frame)
        self.cancelButton.resize(100, 30)
        self.cancelButton.move(self.width() // 2 - 50, 370)
        self.cancelButton.setObjectName('CancelButton')
        self.cancelButton.hide()
        self.cancelButton.clicked.connect(self.cancel_loading)
    
    def apply_styles(self):
        """Apply styles after UI is set up"""
        # Get current app and apply compiled stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.get_compiled_stylesheet())
    
    def get_compiled_stylesheet(self):
        """Compiled stylesheet for better performance"""
        return '''
            #LabelTitle {
                font-size: 60px;
                color: #93deed;
                font-family: Montserrat, serif;
            }
            #LabelDesc {
                font-size: 20px;
                color: #c2ced1;
                font-family: Montserrat, serif;
            }
            #LabelLoading {
                font-size: 20px;
                color: #e8e8eb;
            }
            #CancelButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 14px;
                font-family: Montserrat, serif;
            }
            #CancelButton:hover {
                background-color: #d32f2f;
            }
            QFrame {
                background-color: #2F4454;
                color: rgb(220, 220, 220);
            }
            QProgressBar {
                background-color: #f3f8f5;
                color: rgb(173, 172, 176);
                border-style: none;
                border-radius: 10px;
                text-align: center;
                font-size: 30px;
            }
            QProgressBar::chunk {
                border-radius: 10px;
                background-color: qlineargradient(spread:pad x1:0, x2:1, y1:0.511364, y2:0.523, stop:0 #1C3334, stop:1 #376E6F);
            }
        '''
    
    def init_data_loader(self):
        """Initialize optimized data loader"""
        Qt, QThread, pyqtSignal, QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton, QIcon, QTimer = get_pyqt_modules()
        
        self.data_loader = OptimizedDataLoader()
        
        # Connect signals
        self.data_loader.progress_updated.connect(self.update_progress)
        self.data_loader.data_loaded.connect(self.on_data_loaded)
        self.data_loader.error_occurred.connect(self.on_error)
        
        # Start loading data
        self.data_loader.start()
    
    def update_progress(self, value, task_name="Loading..."):
        """Update progress with task feedback"""
        self.progressBar.setValue(value)
        self.labelLoading.setText(task_name)
        
        # Show cancel button after initial connection attempt
        if value > 20 and not self.can_cancel:
            self.can_cancel = True
            if hasattr(self, 'cancelButton'):
                self.cancelButton.show()
    
    def on_error(self, error_message):
        """Handle error messages"""
        self.labelLoading.setText(error_message)
        self.labelLoading.setStyleSheet("color: #ff9800;")
    
    def cancel_loading(self):
        """Cancel the loading process"""
        if self.data_loader.isRunning():
            self.data_loader.terminate()
            self.data_loader.wait()
        self.close()
    
    def on_data_loaded(self, data, cost_centers, user_data):
        """Handle data loaded signal and initialize main window"""
        self.processed_data = data
        self.progressBar.setValue(100)
        
        # Lazy import of MainWindow
        from launcherui import MainWindow
        
        # Clear app stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(None)
        
        # Create and show main window
        self.myApp = MainWindow(self.processed_data, cost_centers, user_data)
        self.myApp.show()
        self.close()

if __name__ == '__main__':
    # Lazy import of QApplication
    Qt, QThread, pyqtSignal, QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout, QPushButton, QIcon, QTimer = get_pyqt_modules()
    
    app = QApplication(sys.argv)
    
    # Suppress SSL warnings
    get_urllib3()
    
    splash = OptimizedSplashScreen()
    splash.show()
    
    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window...')