import sys
import json
import tempfile
import shutil
import os
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QSplitter, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, pyqtSignal, QObject, QTimer, QWebChannel
from PyQt5.QtGui import QFont

class NetworkMonitor(QObject):
    request_finished = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.requests = []
        self.pending_requests = {}
        self.response_cache = {}
        
    def add_request(self, request_data):
        """Add a new request to tracking"""
        request_id = f"{request_data['url']}_{request_data['timestamp']}"
        request_data['request_id'] = request_id
        request_data['response_received'] = None
        
        self.pending_requests[request_id] = request_data
        self.requests.append(request_data)
        print(f"📡 Request: {request_data['method']} {request_data['url']}")
        
    def update_response(self, url, response_data):
        """Update request with response data using URL matching"""
        for request_id, request in list(self.pending_requests.items()):
            if request['url'] == url and request.get('response_received') is None:
                request['response_received'] = response_data
                print(f"📨 Response: {response_data.get('status', 'N/A')} for {url}")
                self.request_finished.emit(request)
                del self.pending_requests[request_id]
                break

class IncognitoInterceptor(QWebEngineUrlRequestInterceptor):
    """Interceptor that allows auth flows but prevents caching like Chrome incognito"""
    
    def __init__(self, network_monitor, parent=None):
        super().__init__(parent)
        self.network_monitor = network_monitor
        
    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        method = info.requestMethod().data().decode()
        
        # Log the request but DON'T block authentication flows
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'method': method,
            'resource_type': self._get_resource_type_name(info.resourceType()),
            'navigation_type': self._get_navigation_type_name(info.navigationType()),
            'is_redirect': info.navigationType() == QWebEngineUrlRequestInfo.NavigationType.NavigationTypeRedirect,
            'first_party_url': info.firstPartyUrl().toString(),
            'blocked_auth': False
        }
        
        # Only block obviously malicious or unwanted requests
        if self._should_block_request(info):
            print(f"🚫 BLOCKED: Unwanted request to {url}")
            info.block(True)
            request_data['blocked_auth'] = True
        
        self.network_monitor.add_request(request_data)
        
    def _should_block_request(self, info):
        """Only block clearly unwanted requests, not auth flows"""
        url = info.requestUrl().toString().lower()
        
        # Block tracking and analytics, but allow auth
        blocked_patterns = [
            'google-analytics.com',
            'googletagmanager.com',
            'facebook.com/tr',
            'doubleclick.net',
            'googlesyndication.com'
        ]
        
        for pattern in blocked_patterns:
            if pattern in url:
                return True
                
        return False
        
    def _get_resource_type_name(self, resource_type):
        type_map = {
            0: "MainFrame", 1: "SubFrame", 2: "Stylesheet", 3: "Script",
            4: "Image", 5: "FontResource", 6: "SubResource", 7: "Object",
            8: "Media", 9: "Worker", 10: "SharedWorker", 11: "Prefetch",
            12: "Favicon", 13: "Xhr", 14: "Ping", 15: "ServiceWorker",
            16: "CspReport", 17: "PluginResource"
        }
        return type_map.get(resource_type, f"Unknown({resource_type})")
    
    def _get_navigation_type_name(self, nav_type):
        type_map = {
            0: "LinkClicked", 1: "TypedUrl", 2: "FormSubmitted",
            3: "BackForward", 4: "Reload", 5: "Other", 6: "Redirect"
        }
        return type_map.get(nav_type, f"Unknown({nav_type})")

class IncognitoPage(QWebEnginePage):
    """Custom page that handles authentication like Chrome incognito"""
    
    def __init__(self, profile, network_monitor, parent=None):
        super().__init__(profile, parent)
        self.network_monitor = network_monitor
        
        # Connect authentication signals - but handle them properly
        self.authenticationRequired.connect(self._handle_authentication)
        self.proxyAuthenticationRequired.connect(self._handle_proxy_authentication)
        
        # Clear any cached data after loads
        self.loadFinished.connect(self._on_load_finished)
        
    def _handle_authentication(self, requestUrl, authenticator):
        """Handle authentication like Chrome incognito - show dialog but don't cache"""
        url = requestUrl.toString()
        print(f"🔐 AUTH REQUIRED for: {url}")
        
        # Clear any stored credentials to prevent caching
        authenticator.setUser("")
        authenticator.setPassword("")
        
        # Return False to show the default authentication dialog
        # This is the key difference - we ALLOW the auth dialog
        return False
        
    def _handle_proxy_authentication(self, requestUrl, authenticator, proxyHost):
        """Handle proxy authentication"""
        url = requestUrl.toString()
        print(f"🔐 PROXY AUTH REQUIRED for: {url} via {proxyHost}")
        return False
        
    def _on_load_finished(self, success):
        """Clear any stored credentials after page load"""
        if success:
            # Clear browser storage but don't interfere with the page loading
            self._clear_stored_credentials()
            
    def _clear_stored_credentials(self):
        """Clear stored credentials without breaking functionality"""
        js_code = '''
        // Clear storage that might contain credentials
        try {
            if (window.localStorage) {
                // Only clear auth-related items, not all localStorage
                for (let i = localStorage.length - 1; i >= 0; i--) {
                    const key = localStorage.key(i);
                    if (key && (key.includes('auth') || key.includes('token') || key.includes('credential'))) {
                        localStorage.removeItem(key);
                    }
                }
            }
            if (window.sessionStorage) {
                // Same for session storage
                for (let i = sessionStorage.length - 1; i >= 0; i--) {
                    const key = sessionStorage.key(i);
                    if (key && (key.includes('auth') || key.includes('token') || key.includes('credential'))) {
                        sessionStorage.removeItem(key);
                    }
                }
            }
            console.log("🧹 Stored credentials cleared");
        } catch (e) {
            console.log("Note: Could not clear all stored data");
        }
        '''
        
        self.runJavaScript(js_code)

class TrueIncognitoBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🕵️ TRUE INCOGNITO Browser - Like Chrome Incognito")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create temporary directory for this session
        self.temp_dir = tempfile.mkdtemp(prefix="incognito_browser_")
        print(f"🗂️ Temporary session directory: {self.temp_dir}")
        
        # Create network monitor
        self.network_monitor = NetworkMonitor()
        self.network_monitor.request_finished.connect(self.on_request_finished)
        
        # Setup UI
        self._setup_ui()
        
        # Create proper incognito profile
        self.profile = self._create_incognito_profile()
        
        # Create interceptor that allows auth flows
        self.interceptor = IncognitoInterceptor(self.network_monitor)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        
        # Create custom page
        self.page = IncognitoPage(self.profile, self.network_monitor)
        self.web_view.setPage(self.page)
        
        # Connect signals
        self.web_view.urlChanged.connect(self.url_changed)
        self.web_view.loadFinished.connect(self.load_finished)
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_log_display)
        self.update_timer.start(1000)
        
        # Start with a blank page
        self.web_view.load(QUrl("about:blank"))
        print("🚀 True incognito browser ready - Auth dialogs enabled, caching disabled!")
        
    def _create_incognito_profile(self):
        """Create proper incognito profile like Chrome"""
        # Create profile with temporary directory
        profile = QWebEngineProfile("TrueIncognito", self)
        
        # Set temporary cache directory
        cache_dir = os.path.join(self.temp_dir, "cache")
        profile.setCachePath(cache_dir)
        
        # Set temporary data directory  
        data_dir = os.path.join(self.temp_dir, "data")
        profile.setPersistentStoragePath(data_dir)
        
        # Configure like Chrome incognito
        profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)  # Use memory cache, not disk
        profile.setHttpCacheMaximumSize(10 * 1024 * 1024)  # 10MB memory cache
        profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        
        # Disable spell checking to prevent data leakage
        profile.setSpellCheckEnabled(False)
        
        # Set proper user agent
        profile.setHttpUserAgent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Download path to temp directory
        profile.setDownloadPath(os.path.join(self.temp_dir, "downloads"))
        
        print("🔒 Incognito profile created - Auth enabled, no persistent data")
        return profile
        
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        splitter = QSplitter()
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(splitter)
        
        # Browser side
        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        self.incognito_status = QLabel("🕵️ INCOGNITO MODE")
        self.incognito_status.setStyleSheet(
            "color: #6c5ce7; font-weight: bold; font-size: 12px; "
            "padding: 5px 10px; background-color: #f8f9ff; border-radius: 5px; "
            "border: 2px solid #6c5ce7;"
        )
        
        self.auth_status = QLabel("🔐 AUTH DIALOGS: ENABLED")
        self.auth_status.setStyleSheet(
            "color: #00b894; font-weight: bold; font-size: 10px; "
            "padding: 3px 8px; background-color: #d1f2eb; border-radius: 3px;"
        )
        
        status_layout.addWidget(self.incognito_status)
        status_layout.addWidget(self.auth_status)
        status_layout.addStretch()
        
        browser_layout.addLayout(status_layout)
        
        # URL bar
        url_layout = QHBoxLayout()
        
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL - Auth dialogs will appear, credentials won't be saved")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        
        self.go_button = QPushButton("🚀 GO")
        self.go_button.clicked.connect(self.navigate_to_url)
        
        self.clear_session_button = QPushButton("🧹 CLEAR SESSION")
        self.clear_session_button.clicked.connect(self.clear_session)
        self.clear_session_button.setStyleSheet("background-color: #fd79a8; color: white; font-weight: bold;")
        
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_bar)
        url_layout.addWidget(self.go_button)
        url_layout.addWidget(self.clear_session_button)
        
        browser_layout.addLayout(url_layout)
        
        # Web view
        self.web_view = QWebEngineView()
        browser_layout.addWidget(self.web_view)
        
        # Log side
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        log_layout.addWidget(QLabel("🔍 Network Activity Log"))
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Courier", 8))
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #2d3436; color: #00cec9; border: 1px solid #636e72;")
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        
        download_log_button = QPushButton("📥 Download Log")
        download_log_button.clicked.connect(self.download_log)
        download_log_button.setStyleSheet("background-color: #0984e3; color: white; font-weight: bold;")
        
        # Test buttons for various auth scenarios
        test_basic_auth = QPushButton("Test Basic Auth")
        test_basic_auth.clicked.connect(lambda: self.test_url("https://httpbin.org/basic-auth/testuser/testpass"))
        
        test_bearer_auth = QPushButton("Test Bearer Auth") 
        test_bearer_auth.clicked.connect(lambda: self.test_url("https://httpbin.org/bearer"))
        
        test_redirect_auth = QPushButton("Test Redirect Auth")
        test_redirect_auth.clicked.connect(lambda: self.test_url("https://httpbin.org/redirect-to?url=https%3A//httpbin.org/basic-auth/user/pass"))
        
        button_layout.addWidget(clear_button)
        button_layout.addWidget(download_log_button)
        button_layout.addWidget(test_basic_auth)
        button_layout.addWidget(test_bearer_auth)
        button_layout.addWidget(test_redirect_auth)
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(button_layout)
        
        # Add to splitter
        splitter.addWidget(browser_widget)
        splitter.addWidget(log_widget)
        splitter.setSizes([1000, 600])
        
    def navigate_to_url(self):
        """Navigate to URL with proper incognito behavior"""
        url = self.url_bar.text().strip()
        if not url:
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        print(f"🚀 Navigating to: {url}")
        self.web_view.load(QUrl(url))
        
    def test_url(self, url):
        """Test specific URL"""
        print(f"🧪 Testing: {url}")
        self.url_bar.setText(url)
        self.navigate_to_url()
        
    def clear_session(self):
        """Clear session data but keep the browser functional"""
        print("🧹 Clearing session data...")
        
        # Clear caches
        try:
            if hasattr(self.profile, 'clearHttpCache'):
                self.profile.clearHttpCache()
            if hasattr(self.profile, 'clearAllVisitedLinks'):
                self.profile.clearAllVisitedLinks()
        except:
            pass
            
        # Clear stored credentials
        self.page.runJavaScript('''
            try {
                if (window.localStorage) window.localStorage.clear();
                if (window.sessionStorage) window.sessionStorage.clear();
                console.log("🧹 Browser storage cleared");
            } catch (e) {
                console.log("Storage clear attempt completed");
            }
        ''')
        
        print("✅ Session data cleared - ready for fresh requests")
        
    def url_changed(self, url):
        self.url_bar.setText(url.toString())
        
    def load_finished(self, success):
        if success:
            self.auth_status.setText("🔐 AUTH DIALOGS: ENABLED")
            self.auth_status.setStyleSheet(
                "color: #00b894; font-weight: bold; font-size: 10px; "
                "padding: 3px 8px; background-color: #d1f2eb; border-radius: 3px;"
            )
        else:
            self.auth_status.setText("🔐 LOAD FAILED")
            self.auth_status.setStyleSheet(
                "color: #e17055; font-weight: bold; font-size: 10px; "
                "padding: 3px 8px; background-color: #ffeaa7; border-radius: 3px;"
            )
        
    def on_request_finished(self, request_data):
        """Handle completed request-response pairs"""
        status = request_data.get('response_received', {}).get('status', 'N/A')
        print(f"✅ Complete: {request_data['method']} {request_data['url']} → {status}")
        
    def update_log_display(self):
        """Update the log display"""
        log_text = "=== INCOGNITO BROWSER LOG ===\\n\\n"
        recent_requests = self.network_monitor.requests[-15:]
        
        for i, request in enumerate(recent_requests):
            timestamp = request['timestamp'].split('T')[1][:8]  # Just time
            status_marker = "✅" if request.get('response_received') else "⏳"
            blocked_marker = "🚫" if request.get('blocked_auth') else ""
            
            log_text += f"[{timestamp}] {status_marker}{blocked_marker} {request['method']} {request['resource_type']}\\n"
            log_text += f"    {request['url'][:80]}{'...' if len(request['url']) > 80 else ''}\\n"
            
            # Show response details
            if request.get('response_received'):
                response = request['response_received']
                status = response.get('status', 'N/A')
                log_text += f"    → {status}\\n"
                    
            log_text += "\\n"
        
        # Add session info
        log_text += f"\\n=== SESSION INFO ===\\n"
        log_text += f"Total Requests: {len(self.network_monitor.requests)}\\n"
        log_text += f"Completed: {len([r for r in self.network_monitor.requests if r.get('response_received')])}\\n"
        log_text += f"Blocked: {len([r for r in self.network_monitor.requests if r.get('blocked_auth')])}\\n"
        
        self.log_text.setPlainText(log_text)
        
        # Auto scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
        
    def clear_log(self):
        """Clear the request log"""
        self.network_monitor.requests.clear()
        self.network_monitor.pending_requests.clear()
        self.log_text.clear()
        print("📝 Log cleared")
        
    def closeEvent(self, event):
        """Clean up temporary directory on close"""
        print("🧹 Cleaning up incognito session...")
        
        try:
            # Remove temporary directory
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"🗑️ Removed: {self.temp_dir}")
        except Exception as e:
            print(f"Error cleaning up: {e}")
            
        print("👻 Incognito session erased")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set Chromium flags for proper incognito behavior
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--incognito "
        "--disable-web-security "
        "--disable-background-timer-throttling "
        "--disable-backgrounding-occluded-windows "
        "--disable-renderer-backgrounding "
        "--disable-field-trial-config "
        "--password-store=basic "
        "--use-mock-keychain "
    )
    
    print("🚀 Starting TRUE INCOGNITO browser...")
    
    window = TrueIncognitoBrowser()
    window.show()
    
    sys.exit(app.exec_())
