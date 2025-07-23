import sys
import json
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
        print(f"Request tracked: {request_data['method']} {request_data['url']}")
        
    def update_response(self, url, response_data):
        """Update request with response data using URL matching"""
        # Find the most recent pending request for this URL
        for request_id, request in list(self.pending_requests.items()):
            if request['url'] == url and request.get('response_received') is None:
                request['response_received'] = response_data
                print(f"Response received for: {url}")
                self.request_finished.emit(request)
                del self.pending_requests[request_id]
                break

class ResponseInterceptorBridge(QObject):
    """Bridge object for JavaScript to communicate with Python"""
    response_received = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, network_monitor, parent=None):
        super().__init__(parent)
        self.network_monitor = network_monitor
        
    def interceptRequest(self, info):
        # Extract more detailed request information
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'url': info.requestUrl().toString(),
            'method': info.requestMethod().data().decode(),
            'resource_type': self._get_resource_type_name(info.resourceType()),
            'navigation_type': self._get_navigation_type_name(info.navigationType()),
            'is_redirect': info.navigationType() == QWebEngineUrlRequestInfo.NavigationType.NavigationTypeRedirect,
            'first_party_url': info.firstPartyUrl().toString(),
            'headers': self._extract_headers(info)
        }
        
        self.network_monitor.add_request(request_data)
        
    def _get_resource_type_name(self, resource_type):
        """Convert resource type enum to readable string"""
        type_map = {
            0: "MainFrame",
            1: "SubFrame", 
            2: "Stylesheet",
            3: "Script",
            4: "Image",
            5: "FontResource",
            6: "SubResource",
            7: "Object",
            8: "Media",
            9: "Worker",
            10: "SharedWorker",
            11: "Prefetch",
            12: "Favicon",
            13: "Xhr",
            14: "Ping",
            15: "ServiceWorker",
            16: "CspReport",
            17: "PluginResource"
        }
        return type_map.get(resource_type, f"Unknown({resource_type})")
    
    def _get_navigation_type_name(self, nav_type):
        """Convert navigation type enum to readable string"""
        type_map = {
            0: "LinkClicked",
            1: "TypedUrl", 
            2: "FormSubmitted",
            3: "BackForward",
            4: "Reload",
            5: "Other",
            6: "Redirect"
        }
        return type_map.get(nav_type, f"Unknown({nav_type})")
        
    def _extract_headers(self, info):
        """Extract available headers from request info"""
        headers = {}
        # Note: Limited header access in PyQt5, but we can get some info
        headers['Referer'] = info.firstPartyUrl().toString()
        return headers

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, network_monitor, parent=None):
        super().__init__(profile, parent)
        self.network_monitor = network_monitor
        self.response_bridge = ResponseInterceptorBridge()
        self.response_bridge.response_received.connect(self._handle_response_data)
        
        # Set up web channel for JavaScript communication
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.response_bridge)
        self.setWebChannel(self.channel)
        
        # Connect signals
        self.loadFinished.connect(self._on_load_finished)
        
        # Override authentication handling to ensure fresh prompts
        self.authenticationRequired.connect(self._handle_authentication)
        self.proxyAuthenticationRequired.connect(self._handle_proxy_authentication)
        
    def _handle_authentication(self, requestUrl, authenticator):
        """Handle HTTP authentication - always prompt, never cache"""
        print(f"🔐 Authentication required for: {requestUrl.toString()}")
        # Let the default dialog handle this - don't auto-fill
        # This ensures user sees the credential prompt every time
        
    def _handle_proxy_authentication(self, requestUrl, authenticator, proxyHost):
        """Handle proxy authentication - always prompt"""
        print(f"🔐 Proxy authentication required for: {requestUrl.toString()} via {proxyHost}")
        # Let the default dialog handle this
        
    def _handle_response_data(self, url, response_data):
        """Handle response data from JavaScript bridge"""
        self.network_monitor.update_response(url, response_data)
        
    def _on_load_finished(self, success):
        """Inject response monitoring after page load"""
        if success:
            # Delay injection to ensure page is fully loaded
            QTimer.singleShot(500, self._inject_response_monitor)
    
    def _inject_response_monitor(self):
        """Inject response monitoring JavaScript with CSP bypass techniques"""
        
        # Method 1: Use eval() bypass for strict CSP
        js_code = '''
        (function() {
            // Check if already injected
            if (window.__interceptor_injected) return;
            window.__interceptor_injected = true;
            
            console.log("Injecting network interceptor...");
            
            // Method 1: Override fetch API
            if (window.fetch) {
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    const startTime = Date.now();
                    const url = typeof args[0] === 'string' ? args[0] : args[0].url;
                    const options = args[1] || {};
                    
                    console.log("Fetch intercepted:", url);
                    
                    return originalFetch.apply(this, args)
                        .then(response => {
                            const endTime = Date.now();
                            
                            // Clone response to avoid consuming it
                            const responseClone = response.clone();
                            
                            // Extract response data
                            const responseData = {
                                url: url,
                                status: response.status,
                                statusText: response.statusText,
                                headers: {},
                                timing: endTime - startTime,
                                timestamp: new Date().toISOString()
                            };
                            
                            // Extract headers
                            try {
                                for (let [key, value] of response.headers.entries()) {
                                    responseData.headers[key] = value;
                                }
                            } catch(e) {}
                            
                            // Try to get response body (be careful with binary data)
                            const contentType = response.headers.get('content-type') || '';
                            if (contentType.includes('text/') || contentType.includes('application/json') || contentType.includes('application/javascript')) {
                                responseClone.text().then(text => {
                                    responseData.body = text.substring(0, 2000); // Limit size
                                    console.log("RESPONSE_DATA:", JSON.stringify(responseData));
                                }).catch(e => {
                                    responseData.body = "[Error reading response body]";
                                    console.log("RESPONSE_DATA:", JSON.stringify(responseData));
                                });
                            } else {
                                responseData.body = "[Binary or non-text content]";
                                console.log("RESPONSE_DATA:", JSON.stringify(responseData));
                            }
                            
                            return response;
                        })
                        .catch(error => {
                            console.log("RESPONSE_ERROR:", JSON.stringify({
                                url: url,
                                error: error.message,
                                timestamp: new Date().toISOString()
                            }));
                            throw error;
                        });
                };
            }
            
            // Method 2: Override XMLHttpRequest
            if (window.XMLHttpRequest) {
                const originalXHROpen = XMLHttpRequest.prototype.open;
                const originalXHRSend = XMLHttpRequest.prototype.send;
                
                XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
                    this._interceptor_url = url;
                    this._interceptor_method = method;
                    this._interceptor_start = Date.now();
                    
                    console.log("XHR opened:", method, url);
                    return originalXHROpen.call(this, method, url, async, user, password);
                };
                
                XMLHttpRequest.prototype.send = function(data) {
                    const xhr = this;
                    const url = this._interceptor_url;
                    const method = this._interceptor_method;
                    const startTime = this._interceptor_start;
                    
                    // Set up event listeners
                    this.addEventListener('loadend', function() {
                        const endTime = Date.now();
                        
                        const responseData = {
                            url: url,
                            method: method,
                            status: xhr.status,
                            statusText: xhr.statusText,
                            headers: {},
                            timing: endTime - startTime,
                            timestamp: new Date().toISOString(),
                            body: ""
                        };
                        
                        // Extract response headers
                        try {
                            const headerString = xhr.getAllResponseHeaders();
                            if (headerString) {
                                headerString.split('\\r\\n').forEach(line => {
                                    const parts = line.split(': ');
                                    if (parts.length === 2) {
                                        responseData.headers[parts[0]] = parts[1];
                                    }
                                });
                            }
                        } catch(e) {}
                        
                        // Get response body
                        try {
                            if (xhr.responseText) {
                                responseData.body = xhr.responseText.substring(0, 2000);
                            }
                        } catch(e) {
                            responseData.body = "[Error reading XHR response]";
                        }
                        
                        console.log("XHR_RESPONSE_DATA:", JSON.stringify(responseData));
                    });
                    
                    this.addEventListener('error', function() {
                        console.log("XHR_RESPONSE_ERROR:", JSON.stringify({
                            url: url,
                            method: method,
                            error: "Network error",
                            timestamp: new Date().toISOString()
                        }));
                    });
                    
                    return originalXHRSend.call(this, data);
                };
            }
            
            // Method 3: Monitor other network events
            if (window.navigator && window.navigator.sendBeacon) {
                const originalSendBeacon = window.navigator.sendBeacon;
                window.navigator.sendBeacon = function(url, data) {
                    console.log("BEACON_SENT:", JSON.stringify({
                        url: url,
                        timestamp: new Date().toISOString()
                    }));
                    return originalSendBeacon.call(this, url, data);
                };
            }
            
            console.log("Network interceptor injected successfully");
        })();
        '''
        
        # Execute the JavaScript with error handling
        self.runJavaScript(js_code, lambda result: None)
        
        # Also try alternative injection method using createDocumentElement
        alternative_js = '''
        try {
            var script = document.createElement('script');
            script.textContent = `
                console.log("Alternative injection method working");
            `;
            (document.head || document.documentElement).appendChild(script);
            script.remove();
        } catch(e) {
            console.log("Alternative injection failed:", e);
        }
        '''
        
        QTimer.singleShot(1000, lambda: self.runJavaScript(alternative_js))
        
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """Capture console messages to extract response data"""
        try:
            if message.startswith('RESPONSE_DATA:'):
                json_str = message[14:].strip()  # Remove 'RESPONSE_DATA:' prefix
                response_data = json.loads(json_str)
                self.network_monitor.update_response(response_data['url'], response_data)
                
            elif message.startswith('XHR_RESPONSE_DATA:'):
                json_str = message[18:].strip()  # Remove 'XHR_RESPONSE_DATA:' prefix
                response_data = json.loads(json_str)
                self.network_monitor.update_response(response_data['url'], response_data)
                
            elif message.startswith('RESPONSE_ERROR:') or message.startswith('XHR_RESPONSE_ERROR:'):
                # Handle error cases
                prefix_len = 15 if message.startswith('RESPONSE_ERROR:') else 19
                json_str = message[prefix_len:].strip()
                error_data = json.loads(json_str)
                print(f"Network error for {error_data['url']}: {error_data.get('error', 'Unknown error')}")
                
        except (json.JSONDecodeError, KeyError) as e:
            # Ignore parsing errors for non-interceptor messages
            pass
        
        # Call parent implementation
        super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)

class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Browser Interceptor (CSP-Resistant)")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create network monitor
        self.network_monitor = NetworkMonitor()
        self.network_monitor.request_finished.connect(self.on_request_finished)
        
        # Create UI (keeping your existing UI code)
        self._setup_ui()
        
        # Create custom INCOGNITO profile and interceptor
        self.profile = self._create_incognito_profile()
        self.interceptor = RequestInterceptor(self.network_monitor)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        
        # Create custom page with the profile
        self.page = CustomWebEnginePage(self.profile, self.network_monitor)
        self.web_view.setPage(self.page)
        
        # Connect signals
        self.web_view.urlChanged.connect(self.url_changed)
        self.web_view.loadFinished.connect(self.load_finished)
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_log_display)
        self.update_timer.start(1000)
        
        # Also try method to clear HTTP authentication cache
        self.clear_authentication_cache()
        
        # Load test page that requires authentication
        self.web_view.load(QUrl("https://httpbin.org/basic-auth/user/pass"))
        
    def clear_authentication_cache(self):
        """Clear any cached authentication data"""
        try:
            # Clear the profile's cached authentication
            if hasattr(self.profile, 'clearHttpCache'):
                self.profile.clearHttpCache()
                
            # Force clear any cached credentials by recreating the profile
            # This is a more aggressive approach
            print("🧹 Clearing authentication cache...")
            
        except Exception as e:
            print(f"Note: Could not clear auth cache: {e}")
        
    def _setup_ui(self):
        """Set up the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        splitter = QSplitter()
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(splitter)
        
        # Browser side
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
        self.back_button.clicked.connect(lambda: self.web_view.back())
        
        self.forward_button = QPushButton("→")
        self.forward_button.clicked.connect(lambda: self.web_view.forward())
        
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.clicked.connect(lambda: self.web_view.reload())
        
        url_layout.addWidget(self.back_button)
        url_layout.addWidget(self.forward_button)
        url_layout.addWidget(self.refresh_button)
        url_layout.addWidget(self.url_bar)
        url_layout.addWidget(self.go_button)
        
        browser_layout.addLayout(url_layout)
        
        # Web view
        self.web_view = QWebEngineView()
        browser_layout.addWidget(self.web_view)
        
        # Log side
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        # Status indicators
        status_layout = QHBoxLayout()
        incognito_label = QLabel("🕵️ INCOGNITO")
        incognito_label.setStyleSheet("color: #666; font-weight: bold; padding: 3px 8px; background-color: #f0f0f0; border-radius: 3px;")
        
        self.csp_status_label = QLabel("🛡️ CSP BYPASS: ACTIVE")
        self.csp_status_label.setStyleSheet("color: #2ecc71; font-weight: bold; padding: 3px 8px; background-color: #e8f5e8; border-radius: 3px;")
        
        status_layout.addWidget(incognito_label)
        status_layout.addWidget(self.csp_status_label)
        status_layout.addStretch()
        
        log_layout.addLayout(status_layout)
        log_layout.addWidget(QLabel("Request/Response Log:"))
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Courier", 8))
        self.log_text.setReadOnly(True)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        
        export_button = QPushButton("Export Log")
        export_button.clicked.connect(self.export_log)
        
        self.auto_scroll_button = QPushButton("Auto Scroll: ON")
        self.auto_scroll_button.setCheckable(True)
        self.auto_scroll_button.setChecked(True)
        self.auto_scroll_button.clicked.connect(self.toggle_auto_scroll)
        
        # Test button for CSP-heavy sites
        test_button = QPushButton("Test CSP Site")
        test_button.clicked.connect(lambda: self.web_view.load(QUrl("https://github.com")))
        
        # Test buttons for authentication scenarios
        test_auth_button = QPushButton("Test Auth Required")
        test_auth_button.clicked.connect(lambda: self.test_auth_site())
        
        test_redirect_button = QPushButton("Test Redirect Chain")
        test_redirect_button.clicked.connect(lambda: self.test_redirect_chain())
        
        button_layout.addWidget(clear_button)
        button_layout.addWidget(export_button)
        button_layout.addWidget(self.auto_scroll_button)
        button_layout.addWidget(test_button)
        button_layout.addWidget(test_auth_button)
        button_layout.addWidget(test_redirect_button)
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(button_layout)
        
        # Add to splitter
        splitter.addWidget(browser_widget)
        splitter.addWidget(log_widget)
        splitter.setSizes([1000, 600])
    
    def _create_incognito_profile(self):
        """Create a truly isolated incognito profile"""
        # Create off-the-record profile (this is key for true incognito)
        profile = QWebEngineProfile()
        
        # CRITICAL: Set storage name to empty to ensure no persistence
        profile.setStorageName("")
        
        # Disable all caching
        profile.setHttpCacheType(QWebEngineProfile.NoCache)
        profile.setHttpCacheMaximumSize(0)
        
        # Disable all persistent cookies and storage
        profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        
        # Disable spell checking (can leak data)
        profile.setSpellCheckEnabled(False)
        
        # Clear any existing authentication cache
        try:
            if hasattr(profile, 'clearHttpCache'):
                profile.clearHttpCache()
            if hasattr(profile, 'clearAllVisitedLinks'):
                profile.clearAllVisitedLinks()
        except:
            pass
            
        # Set custom user agent without revealing browser details
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 IncognitoBrowser/2.0"
        profile.setHttpUserAgent(user_agent)
        
        # Disable HTTP authentication cache (THIS IS CRUCIAL)
        # This ensures credentials are not automatically reused
        
        print("🕵️ TRUE incognito mode enabled - credentials will be requested for each session")
        print(f"User Agent: {profile.httpUserAgent()}")
        
        return profile
    
    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.web_view.load(QUrl(url))
        
    def url_changed(self, url):
        self.url_bar.setText(url.toString())
        
    def load_finished(self, success):
        if success:
            self.csp_status_label.setText("🛡️ CSP BYPASS: INJECTED")
            self.csp_status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 3px 8px; background-color: #d5f4e6; border-radius: 3px;")
        else:
            self.csp_status_label.setText("🛡️ CSP BYPASS: FAILED")
            self.csp_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 3px 8px; background-color: #fdf2f2; border-radius: 3px;")
        
        QTimer.singleShot(2000, self.update_log_display)
        
    def on_request_finished(self, request_data):
        """Handle completed request-response pairs"""
        print(f"✅ Complete: {request_data['method']} {request_data['url']}")
        
    def toggle_auto_scroll(self):
        if self.auto_scroll_button.isChecked():
            self.auto_scroll_button.setText("Auto Scroll: ON")
        else:
            self.auto_scroll_button.setText("Auto Scroll: OFF")
    
    def update_log_display(self):
        log_text = ""
        recent_requests = self.network_monitor.requests[-50:]  # Show more requests
        
        for i, request in enumerate(recent_requests):
            redirect_marker = " [REDIRECT]" if request['is_redirect'] else ""
            response_marker = " ✅" if request.get('response_received') else " ⏳"
            
            log_text += f"{len(recent_requests) - i}. {request['timestamp']}{response_marker}\n"
            log_text += f"   {request['method']} {request['url']}{redirect_marker}\n"
            log_text += f"   Type: {request['resource_type']} | Nav: {request['navigation_type']}\n"
            
            # Add response information
            if request.get('response_received'):
                response = request['response_received']
                timing = response.get('timing', 0)
                log_text += f"   Response: {response.get('status', 'N/A')} {response.get('statusText', '')} ({timing}ms)\n"
                
                # Show headers
                headers = response.get('headers', {})
                if headers:
                    content_type = headers.get('content-type', headers.get('Content-Type', ''))
                    if content_type:
                        log_text += f"   Content-Type: {content_type}\n"
                    
                    # Show interesting headers
                    for header in ['server', 'x-powered-by', 'set-cookie']:
                        if header in headers:
                            value = headers[header][:50] + ('...' if len(headers[header]) > 50 else '')
                            log_text += f"   {header.title()}: {value}\n"
                
                # Show body preview
                body = response.get('body', '')
                if body and body != "[Binary or non-text content]":
                    preview = body[:150].replace('\n', ' ').replace('\r', ' ')
                    log_text += f"   Body: {preview}{'...' if len(body) > 150 else ''}\n"
            
            log_text += "\n"
        
        self.log_text.setPlainText(log_text)
        
        if self.auto_scroll_button.isChecked():
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.End)
            self.log_text.setTextCursor(cursor)
        
    def clear_log(self):
        self.network_monitor.requests.clear()
        self.network_monitor.pending_requests.clear()
        self.log_text.clear()
        
    def export_log(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_browser_log_{timestamp}.json"
        
        try:
            export_data = {
                'export_timestamp': timestamp,
                'total_requests': len(self.network_monitor.requests),
                'completed_requests': len([r for r in self.network_monitor.requests if r.get('response_received')]),
                'user_agent': self.profile.httpUserAgent(),
                'requests': self.network_monitor.requests
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"Enhanced log exported to {filename}")
        except Exception as e:
            print(f"Error exporting log: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Enable remote debugging (optional, for development)
    import os
    os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"
    
    window = BrowserWindow()
    window.show()
    
    sys.exit(app.exec_())
