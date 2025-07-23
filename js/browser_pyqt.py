import sys
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QSplitter
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, pyqtSignal, QObject
from PyQt5.QtGui import QFont

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.requests = []
        
    def interceptRequest(self, info):
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'url': info.requestUrl().toString(),
            'method': info.requestMethod().data().decode(),
            'resource_type': info.resourceType(),
            'navigation_type': info.navigationType(),
            'is_redirect': info.navigationType() == QWebEngineUrlRequestInfo.NavigationType.NavigationTypeRedirect
        }
        
        self.requests.append(request_data)
        print(f"Request intercepted: {request_data['method']} {request_data['url']}")
        
        # Allow the request to proceed
        return

class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Browser with Request Logging")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create splitter for main layout
        splitter = QSplitter()
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(splitter)
        
        # Left side - Browser
        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        
        # URL bar
        url_layout = QHBoxLayout()
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL here...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.navigate_to_url)
        
        self.back_button = QPushButton("←")
        self.back_button.clicked.connect(self.go_back)
        
        self.forward_button = QPushButton("→")
        self.forward_button.clicked.connect(self.go_forward)
        
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.clicked.connect(self.refresh_page)
        
        url_layout.addWidget(self.back_button)
        url_layout.addWidget(self.forward_button)
        url_layout.addWidget(self.refresh_button)
        url_layout.addWidget(self.url_bar)
        url_layout.addWidget(self.go_button)
        
        browser_layout.addLayout(url_layout)
        
        # Web view
        self.web_view = QWebEngineView()
        
        # Create custom profile and interceptor
        self.profile = QWebEngineProfile.defaultProfile()
        self.interceptor = RequestInterceptor()
        self.profile.setUrlRequestInterceptor(self.interceptor)
        
        # Create custom page with the profile
        self.page = QWebEnginePage(self.profile)
        self.web_view.setPage(self.page)
        
        # Connect signals
        self.web_view.urlChanged.connect(self.url_changed)
        self.web_view.loadFinished.connect(self.load_finished)
        
        browser_layout.addWidget(self.web_view)
        
        # Right side - Request Log
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        log_layout.addWidget(QLabel("Request Log:"))
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setReadOnly(True)
        
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        
        export_button = QPushButton("Export Log")
        export_button.clicked.connect(self.export_log)
        
        log_layout.addWidget(self.log_text)
        log_layout.addWidget(clear_button)
        log_layout.addWidget(export_button)
        
        # Add widgets to splitter
        splitter.addWidget(browser_widget)
        splitter.addWidget(log_widget)
        splitter.setSizes([1000, 400])  # Set initial sizes
        
        # Load initial page
        self.web_view.load(QUrl("https://httpbin.org/redirect/3"))
        
    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.web_view.load(QUrl(url))
        
    def url_changed(self, url):
        self.url_bar.setText(url.toString())
        
    def load_finished(self, success):
        self.update_log_display()
        
    def go_back(self):
        self.web_view.back()
        
    def go_forward(self):
        self.web_view.forward()
        
    def refresh_page(self):
        self.web_view.reload()
        
    def update_log_display(self):
        log_text = ""
        for i, request in enumerate(self.interceptor.requests[-20:]):  # Show last 20 requests
            redirect_marker = " [REDIRECT]" if request['is_redirect'] else ""
            log_text += f"{i+1}. {request['timestamp']}\n"
            log_text += f"   {request['method']} {request['url']}{redirect_marker}\n"
            log_text += f"   Type: {request['resource_type']}\n\n"
        
        self.log_text.setPlainText(log_text)
        # Scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
        
    def clear_log(self):
        self.interceptor.requests.clear()
        self.log_text.clear()
        
    def export_log(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"browser_requests_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.interceptor.requests, f, indent=2)
            print(f"Log exported to {filename}")
        except Exception as e:
            print(f"Error exporting log: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = BrowserWindow()
    window.show()
    
    sys.exit(app.exec_())
