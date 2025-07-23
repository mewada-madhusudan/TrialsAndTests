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

class AuthenticationInterceptor(QWebEngineUrlRequestInterceptor):
    """Aggressive interceptor that blocks authentication caching"""
    
    def __init__(self, network_monitor, parent=None):
        super().__init__(parent)
        self.network_monitor = network_monitor
        self.blocked_auth_headers = set()
        
    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        method = info.requestMethod().data().decode()
        
        # Block requests with cached authentication
        if self._has_cached_auth(info):
            print(f"🚫 BLOCKED: Cached auth detected for {url}")
            info.block(True)  # Block the request
            return
            
        # Strip authentication headers to force fresh auth
        if 'authorization' in url.lower() or method in ['OPTIONS']:
            print(f"🧹 Stripping potential auth headers from {url}")
        
        # Log the request
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
        
        self.network_monitor.add_request(request_data)
        
    def _has_cached_auth(self, info):
        """Detect if request might be using cached authentication"""
        url = info.requestUrl().toString()
        
        # Check for common authentication patterns that shouldn't be auto-handled
        auth_patterns = [
            '/oauth/',
            '/auth/',
            '/login',
            '/authenticate',
            'basic-auth',
            'bearer'
        ]
        
        for pattern in auth_patterns:
            if pattern in url.lower():
                return False  # Don't block actual auth endpoints
                
        # Block requests to previously failed auth URLs
        if url in self.blocked_auth_headers:
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

class TrueIncognitoPage(QWebEnginePage):
    """Custom page that aggressively prevents authentication caching"""
    
    def __init__(self, profile, network_monitor, parent=None):
        super().__init__(profile, parent)
        self.network_monitor = network_monitor
        self.auth_prompts_shown = set()
        
        # Connect authentication signals
        self.authenticationRequired.connect(self._handle_authentication)
        self.proxyAuthenticationRequired.connect(self._handle_proxy_authentication)
        
        # Force authentication dialog on every request
        self.loadFinished.connect(self._on_load_finished)
        
    def _handle_authentication(self, requestUrl, authenticator):
        """Force authentication dialog every time"""
        url = requestUrl.toString()
        print(f"🔐 FORCED AUTH PROMPT for: {url}")
        
        # Always clear any stored credentials
        authenticator.setUser("")
        authenticator.setPassword("")
        
        # Mark that we've shown auth for this URL
        self.auth_prompts_shown.add(url)
        
        # Let the default authentication dialog handle this
        # Return False to show the dialog
        return False
        
    def _handle_proxy_authentication(self, requestUrl, authenticator, proxyHost):
        """Handle proxy authentication"""
        url = requestUrl.toString()
        print(f"🔐 PROXY AUTH PROMPT for: {url} via {proxyHost}")
        return False
        
    def _on_load_finished(self, success):
        """Clear authentication cache after each load"""
        if success:
            # Inject JavaScript to clear any stored credentials
            self._clear_browser_auth_cache()
            
    def _clear_browser_auth_cache(self):
        """Inject JavaScript to clear browser authentication cache"""
        js_code = '''
        // Clear any stored authentication
        if (window.localStorage) {
            window.localStorage.clear();
        }
        if (window.sessionStorage) {
            window.sessionStorage.clear();
        }
        
        // Clear any cached credentials
        document.querySelectorAll('input[type="password"]').forEach(input => {
            input.value = '';
            input.autocomplete = 'off';
        });
        
        // Disable password managers
        document.querySelectorAll('form').forEach(form => {
            form.autocomplete = 'off';
        });
        
        console.log("🧹 Browser auth cache cleared");
        '''
        
        self.runJavaScript(js_code)

class TrulyIncognitoBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🕵️ TRULY INCOGNITO Browser - Zero Auth Caching")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create temporary directory for this session
        self.temp_dir = tempfile.mkdtemp(prefix="incognito_browser_")
        print(f"🗂️ Temporary session directory: {self.temp_dir}")
        
        # Create network monitor
        self.network_monitor = NetworkMonitor()
        self.network_monitor.request_finished.connect(self.on_request_finished)
        
        # Setup UI
        self._setup_ui()
        
        # Create the most isolated profile possible
        self.profile = self._create_nuclear_incognito_profile()
        
        # Create aggressive authentication interceptor
        self.auth_interceptor = AuthenticationInterceptor(self.network_monitor)
        self.profile.setUrlRequestInterceptor(self.auth_interceptor)
        
        # Create custom page
        self.page = TrueIncognitoPage(self.profile, self.network_monitor)
        self.web_view.setPage(self.page)
        
        # Connect signals
        self.web_view.urlChanged.connect(self.url_changed)
        self.web_view.loadFinished.connect(self.load_finished)
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_log_display)
        self.update_timer.start(1000)
        
        # Start with a test page
        self.web_view.load(QUrl("about:blank"))
        print("🚀 Truly incognito browser ready - ZERO authentication caching!")
        
    def _create_nuclear_incognito_profile(self):
        """Create the most isolated profile possible"""
        # Create profile with temporary directory
        profile = QWebEngineProfile("TrueIncognito", self)
        
        # Set temporary cache directory
        cache_dir = os.path.join(self.temp_dir, "cache")
        profile.setCachePath(cache_dir)
        
        # Set temporary data directory  
        data_dir = os.path.join(self.temp_dir, "data")
        profile.setPersistentStoragePath(data_dir)
        
        # NUCLEAR option: Disable ALL caching and storage
        profile.setHttpCacheType(QWebEngineProfile.NoCache)
        profile.setHttpCacheMaximumSize(0)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        
        # Disable spell checking and other features that might cache data
        profile.setSpellCheckEnabled(False)
        
        # Set aggressive user agent
        profile.setHttpUserAgent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 NUCLEAR_INCOGNITO/1.0"
        )
        
        # Download path to temp directory
        profile.setDownloadPath(os.path.join(self.temp_dir, "downloads"))
        
        print("☢️ NUCLEAR INCOGNITO profile created - maximum isolation enabled")
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
        
        self.incognito_status = QLabel("☢️ NUCLEAR INCOGNITO MODE")
        self.incognito_status.setStyleSheet(
            "color: #e74c3c; font-weight: bold; font-size: 12px; "
            "padding: 5px 10px; background-color: #fdf2f2; border-radius: 5px; "
            "border: 2px solid #e74c3c;"
        )
        
        self.auth_status = QLabel("🔐 AUTH BLOCKING: ACTIVE")
        self.auth_status.setStyleSheet(
            "color: #2ecc71; font-weight: bold; font-size: 10px; "
            "padding: 3px 8px; background-color: #d5f4e6; border-radius: 3px;"
        )
        
        status_layout.addWidget(self.incognito_status)
        status_layout.addWidget(self.auth_status)
        status_layout.addStretch()
        
        browser_layout.addLayout(status_layout)
        
        # URL bar
        url_layout = QHBoxLayout()
        
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL - Fresh session for every request")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        
        self.go_button = QPushButton("🚀 GO")
        self.go_button.clicked.connect(self.navigate_to_url)
        
        self.nuclear_reload_button = QPushButton("☢️ NUCLEAR RELOAD")
        self.nuclear_reload_button.clicked.connect(self.nuclear_reload)
        self.nuclear_reload_button.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_bar)
        url_layout.addWidget(self.go_button)
        url_layout.addWidget(self.nuclear_reload_button)
        
        browser_layout.addLayout(url_layout)
        
        # Web view
        self.web_view = QWebEngineView()
        browser_layout.addWidget(self.web_view)
        
        # Log side
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        log_layout.addWidget(QLabel("🕵️ Incognito Request/Response Log"))
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Courier", 8))
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #00ff00; border: 1px solid #333;")
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        
        # Test buttons for various auth scenarios
        test_basic_auth = QPushButton("Test Basic Auth")
        test_basic_auth.clicked.connect(lambda: self.test_url("https://httpbin.org/basic-auth/testuser/testpass"))
        
        test_bearer_auth = QPushButton("Test Bearer Auth") 
        test_bearer_auth.clicked.connect(lambda: self.test_url("https://httpbin.org/bearer"))
        
        test_redirect_auth = QPushButton("Test Redirect→Auth")
        test_redirect_auth.clicked.connect(lambda: self.test_url("https://httpbin.org/redirect-to?url=https%3A//httpbin.org/basic-auth/user/pass"))
        
        session_nuke_button = QPushButton("🧨 NUKE SESSION")
        session_nuke_button.clicked.connect(self.nuke_session)
        session_nuke_button.setStyleSheet("background-color: #8b0000; color: white; font-weight: bold;")
        
        button_layout.addWidget(clear_button)
        button_layout.addWidget(test_basic_auth)
        button_layout.addWidget(test_bearer_auth)
        button_layout.addWidget(test_redirect_auth)
        button_layout.addWidget(session_nuke_button)
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(button_layout)
        
        # Add to splitter
        splitter.addWidget(browser_widget)
        splitter.addWidget(log_widget)
        splitter.setSizes([1000, 600])
        
    def navigate_to_url(self):
        """Navigate with completely fresh session"""
        url = self.url_bar.text().strip()
        if not url:
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        print(f"🚀 FRESH SESSION navigation to: {url}")
        
        # Nuclear option: Clear everything before navigation
        self.nuke_session()
        
        # Load the URL
        self.web_view.load(QUrl(url))
        
    def test_url(self, url):
        """Test specific URL with fresh session"""
        print(f"🧪 Testing: {url}")
        self.url_bar.setText(url)
        self.navigate_to_url()
        
    def nuclear_reload(self):
        """Nuclear reload - completely fresh session"""
        current_url = self.web_view.url().toString()
        if current_url and current_url != "about:blank":
            print(f"☢️ NUCLEAR RELOAD: {current_url}")
            self.nuke_session()
            self.web_view.load(QUrl(current_url))
        
    def nuke_session(self):
        """Completely destroy and recreate the browsing session"""
        print("🧨 NUKING SESSION - Complete reset")
        
        # Clear all caches and data
        try:
            if hasattr(self.profile, 'clearHttpCache'):
                self.profile.clearHttpCache()
            if hasattr(self.profile, 'clearAllVisitedLinks'):
                self.profile.clearAllVisitedLinks()
        except:
            pass
            
        # Clear the page
        self.web_view.load(QUrl("about:blank"))
        
        # Clear auth interceptor state
        self.auth_interceptor.blocked_auth_headers.clear()
        if hasattr(self.page, 'auth_prompts_shown'):
            self.page.auth_prompts_shown.clear()
            
        # Clear JavaScript caches
        self.page.runJavaScript('''
            if (window.localStorage) window.localStorage.clear();
            if (window.sessionStorage) window.sessionStorage.clear();
            console.log("🧹 JavaScript storage nuked");
        ''')
        
        print("💥 Session completely destroyed - next request will be 100% fresh")
        
    def url_changed(self, url):
        self.url_bar.setText(url.toString())
        
    def load_finished(self, success):
        if success:
            self.auth_status.setText("🔐 AUTH BLOCKING: ACTIVE")
            self.auth_status.setStyleSheet(
                "color: #2ecc71; font-weight: bold; font-size: 10px; "
                "padding: 3px 8px; background-color: #d5f4e6; border-radius: 3px;"
            )
        else:
            self.auth_status.setText("🔐 AUTH BLOCKING: ERROR")
            self.auth_status.setStyleSheet(
                "color: #e74c3c; font-weight: bold; font-size: 10px; "
                "padding: 3px 8px; background-color: #fdf2f2; border-radius: 3px;"
            )
        
    def on_request_finished(self, request_data):
        """Handle completed request-response pairs"""
        status = request_data.get('response_received', {}).get('status', 'N/A')
        print(f"✅ Complete: {request_data['method']} {request_data['url']} → {status}")
        
    def update_log_display(self):
        """Update the log display with hacker-style formatting"""
        log_text = "=== NUCLEAR INCOGNITO SESSION LOG ===\\n\\n"
        recent_requests = self.network_monitor.requests[-20:]
        
        for i, request in enumerate(recent_requests):
            timestamp = request['timestamp'].split('T')[1][:8]  # Just time
            status_marker = "✅" if request.get('response_received') else "⏳"
            
            log_text += f"[{timestamp}] {status_marker} {request['method']} {request['resource_type']}\\n"
            log_text += f"    URL: {request['url']}\\n"
            
            # Show response details
            if request.get('response_received'):
                response = request['response_received']
                status = response.get('status', 'N/A')
                timing = response.get('timing', 0)
                log_text += f"    RESPONSE: {status} ({timing}ms)\\n"
                
                # Show authentication-related headers
                headers = response.get('headers', {})
                auth_headers = [h for h in headers.keys() if 'auth' in h.lower() or 'www-authenticate' in h.lower()]
                if auth_headers:
                    log_text += f"    AUTH HEADERS: {', '.join(auth_headers)}\\n"
                    
            log_text += "\\n"
        
        # Add session status
        log_text += f"\\n=== SESSION STATUS ===\\n"
        log_text += f"Temp Directory: {self.temp_dir}\\n"
        log_text += f"Total Requests: {len(self.network_monitor.requests)}\\n"
        log_text += f"Completed: {len([r for r in self.network_monitor.requests if r.get('response_received')])}\\n"
        
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
        print("🧹 Cleaning up temporary incognito session...")
        
        try:
            # Remove temporary directory
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"🗑️ Removed: {self.temp_dir}")
        except Exception as e:
            print(f"Error cleaning up: {e}")
            
        print("👻 Incognito session completely erased - no traces left")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set Chromium flags for maximum privacy
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--incognito "
        "--disable-web-security "
        "--disable-features=VizDisplayCompositor "
        "--disable-http-cache "
        "--disable-application-cache "
        "--disable-offline-web-application-cache "
        "--disable-gpu-sandbox "
        "--disable-software-rasterizer "
        "--disable-background-timer-throttling "
        "--disable-backgrounding-occluded-windows "
        "--disable-renderer-backgrounding "
        "--disable-field-trial-config "
        "--disable-ipc-flooding-protection "
        "--password-store=basic "
        "--use-mock-keychain "
    )
    
    print("🚀 Starting NUCLEAR INCOGNITO browser...")
    
    window = TrulyIncognitoBrowser()
    window.show()
    
    sys.exit(app.exec_())
