import sys
import time
from PyQt6.QtWidgets import QApplication, QWidget, QProgressBar, QLabel, QFrame, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
import pandas as pd
from launcherui import MainWindow

class DataLoader(QThread):
    progress_updated = pyqtSignal(int)
    data_loaded = pyqtSignal(object)
    
    def __init__(self, client_id, client_secret, sharepoint_site):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.sharepoint_site = sharepoint_site
        
    def run(self):
        try:
            # Emit 10% progress for starting connection
            self.progress_updated.emit(10)
            
            # Initialize SharePoint client
            credentials = ClientCredential(self.client_id, self.client_secret)
            ctx = ClientContext(self.sharepoint_site).with_credentials(credentials)
            
            # Emit 30% progress for successful connection
            self.progress_updated.emit(30)
            
            # Fetch data from SharePoint list
            target_list = ctx.web.lists.get_by_title("ToolsAccessList")
            items = target_list.items.get().execute_query()
            
            # Emit 60% progress for data fetch
            self.progress_updated.emit(60)
            
            # Convert to DataFrame
            data = []
            for item in items:
                data.append({
                    'Tool': item.properties.get('Title', ''),
                    'UserEmail': item.properties.get('UserEmail', ''),
                    'AccessLevel': item.properties.get('AccessLevel', '')
                })
            
            df = pd.DataFrame(data)
            
            # Process the DataFrame
            # Add your data processing logic here
            processed_df = self.process_data(df)
            
            # Emit 90% progress for processing completion
            self.progress_updated.emit(90)
            
            # Emit the processed data
            self.data_loaded.emit(processed_df)
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            self.data_loaded.emit(None)
    
    def process_data(self, df):
        # Add your DataFrame processing logic here
        # For example, filtering, grouping, etc.
        # This is a placeholder for your specific requirements
        processed_df = df.copy()
        return processed_df

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('STO Application Launcher')
        self.setFixedSize(1100, 500)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.counter = 0
        self.n = 100  # Changed to percentage-based progress
        self.processed_data = None
        
        self.initUI()
        self.initDataLoader()

    def initDataLoader(self):
        # Initialize data loader with your SharePoint credentials
        self.data_loader = DataLoader(
            client_id="your_client_id",
            client_secret="your_client_secret",
            sharepoint_site="your_sharepoint_site_url"
        )
        
        # Connect signals
        self.data_loader.progress_updated.connect(self.updateProgress)
        self.data_loader.data_loaded.connect(self.onDataLoaded)
        
        # Start loading data
        self.data_loader.start()

    def initUI(self):
        # Previous UI initialization code remains the same
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.frame = QFrame()
        layout.addWidget(self.frame)

        self.labelTitle = QLabel(self.frame)
        self.labelTitle.setObjectName('LabelTitle')
        self.labelTitle.resize(self.width() - 10, 150)
        self.labelTitle.move(0, 40)
        self.labelTitle.setText('Application Launcher')
        self.labelTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.labelDescription = QLabel(self.frame)
        self.labelDescription.resize(self.width() - 10, 50)
        self.labelDescription.move(0, self.labelTitle.height())
        self.labelDescription.setObjectName('LabelDesc')
        self.labelDescription.setText('Developed and Maintained by <strong>STO</strong>')
        self.labelDescription.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progressBar = QProgressBar(self.frame)
        self.progressBar.resize(self.width() - 200 - 10, 50)
        self.progressBar.move(100, self.labelDescription.y() + 130)
        self.progressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progressBar.setFormat('%p%')
        self.progressBar.setTextVisible(True)
        self.progressBar.setRange(0, self.n)
        self.progressBar.setValue(0)

        self.labelLoading = QLabel(self.frame)
        self.labelLoading.resize(self.width() - 10, 50)
        self.labelLoading.move(0, self.progressBar.y() + 70)
        self.labelLoading.setObjectName('LabelLoading')
        self.labelLoading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelLoading.setText('Loading...')

    def updateProgress(self, value):
        self.progressBar.setValue(value)
        if value < 30:
            self.labelLoading.setText('Connecting to SharePoint...')
        elif value < 60:
            self.labelLoading.setText('Fetching data...')
        elif value < 90:
            self.labelLoading.setText('Processing data...')
        else:
            self.labelLoading.setText('Launching application...')

    def onDataLoaded(self, data):
        self.processed_data = data
        self.progressBar.setValue(100)
        self.close()
        time.sleep(1)
        app.setStyleSheet(None)
        
        # Pass the processed data to MainWindow
        self.myApp = MainWindow(processed_data=self.processed_data)
        self.myApp.show()
