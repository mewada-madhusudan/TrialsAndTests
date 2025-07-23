import sys
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QSplitter, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont

class NetworkMonitor(QObject):
    request_finished = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.requests = []
        self.pending_requests = {}  # Track requests waiting for responses
        
    def add_request(self, request_data):
        """Add a new request to tracking"""
        request_id = f"{request_data['url']}_{request_data['timestamp']}"
        request_data['request_id'] = request_id
        request_data['response_received'] = None
        
        self.pending_requests[request_id] = request_data
        self.requests.append(request_data)
        print(f"Request tracked: {request_data['method']} {request_data['url']}")
        
    def update_response(self, request_id, response_data):
        """Update request with response data"""
        if request_id in self.pending_requests:
            self.pending_requests[request_id]['response_received'] = response_data
            print(f"Response received for: {self.pending_requests[request_id]['url']}")
            self.request_finished.emit(self.pending_requests[request_id])
            del self.pending_requests[request_id]

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, network_monitor, parent=None):
        super().__init__(parent)
        self.network_monitor = network_monitor
        
    def interceptRequest(self, info):
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'url': info.requestUrl().toString(),
            'method': info.requestMethod().data().decode(),
            'resource_type': info.resourceType(),
            'navigation_type': info.navigationType(),
            'is_redirect': info.navigationType() == QWebEngineUrlRequestInfo.NavigationType.NavigationTypeRedirect,
            'headers': self._extract_headers(info)
        }
        
        self.network_monitor.add_request(request_data)
        # Allow the request to proceed
        return
        
    def _extract_headers(self, info):
        """Extract available headers from request info"""
        headers = {}
        # Note: PyQt5 doesn't provide direct access to request headers
        # This is a limitation of the QWebEngineUrlRequestInterceptor
        headers['User-Agent'] = 'Available in full implementation'
        return headers

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, network_monitor, parent=None):
        super().__init__(profile, parent)
        self.network_monitor = network_monitor
        self.response_cache = {}
        
        # Set up JavaScript injection to capture response data
        self.loadFinished.connect(self._inject_response_interceptor)
        
    def _inject_response_interceptor(self, success):
        """Inject JavaScript to intercept fetch responses"""
        js_code = '''
        (function() {
            // Store original fetch
            const originalFetch = window.fetch;
            
            // Override fetch to capture responses
            window.fetch = function(...args) {
                const url = args[0];
                const options = args[1] || {};
                
                return originalFetch.apply(this, arguments)
                    .then(response => {
                        // Clone response to read it without consuming it
                        const responseClone = response.clone();
                        
                        // Try to read response data
                        responseClone.text().then(text => {
                            const responseData = {
                                url: url,
                                status: response.status,
                                statusText: response.statusText,
                                headers: Object.fromEntries(response.headers.entries()),
                                body: text.substring(0, 1000) // Limit body size
                            };
                            
                            // Send to Qt application
                            if (window.qt && window.qt.webChannelTransport) {
                                console.log('Response captured:', JSON.stringify(responseData));
                            }
                        }).catch(e => {
                            console.log('Error reading response:', e);
                        });
                        
                        return response;
                    });
            };
            
            // Override XMLHttpRequest
            const originalXHROpen = XMLHttpRequest.prototype.open;
            const originalXHRSend = XMLHttpRequest.prototype.send;
            
            XMLHttpRequest.prototype.open = function(method, url) {
                this._url = url;
                this._method = method;
                return originalXHROpen.apply(this, arguments);
            };
            
            XMLHttpRequest.prototype.send = function(data) {
                const xhr = this;
                const url = this._url;
                const method = this._method;
                
                this.addEventListener('load', function() {
                    const responseData = {
                        url: url,
                        method: method,
                        status: xhr.status,
                        statusText: xhr.statusText,
                        headers: xhr.getAllResponseHeaders(),
                        body: xhr.responseText ? xhr.responseText.substring(0, 1000) : ''
                    };
                    
                    console.log('XHR Response captured:', JSON.stringify(responseData));
                });
                
                return originalXHRSend.apply(this, arguments);
            };
        })();
        '''
        
        self.runJavaScript(js_code)
        
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """Capture console messages to get response data"""
        if message.startswith('Response captured:') or message.startswith('XHR Response captured:'):
            try:
                # Extract JSON from console message
                json_str = message.split(':', 1)[1].strip()
                response_data = json.loads(json_str)
                
                # Find matching request and update it
                self._update_request_with_response(response_data)
                
            except (json.JSONDecodeError, IndexError) as e:
                print(f"Error parsing response data: {e}")
        
        # Call parent implementation
        super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)
        
    def _update_request_with_response(self, response_data):
        """Update the corresponding request with response data"""
        url = response_data.get('url', '')
        
        # Find the most recent request matching this URL
        for request in reversed(self.network_monitor.requests):
            if request['url'] == url and request.get('response_received') is None:
                request['response_received'] = response_data
                self.network_monitor.request_finished.emit(request)
                break
class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Browser with Request/Response Logging")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create network monitor
        self.network_monitor = NetworkMonitor()
        self.network_monitor.request_finished.connect(self.on_request_finished)
        
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
        self.interceptor = RequestInterceptor(self.network_monitor)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        
        # Create custom page with the profile
        self.page = CustomWebEnginePage(self.profile, self.network_monitor)
        self.web_view.setPage(self.page)
        
        # Connect signals
        self.web_view.urlChanged.connect(self.url_changed)
        self.web_view.loadFinished.connect(self.load_finished)
        
        browser_layout.addWidget(self.web_view)
        
        # Right side - Request/Response Log
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
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
        
        button_layout.addWidget(clear_button)
        button_layout.addWidget(export_button)
        button_layout.addWidget(self.auto_scroll_button)
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(button_layout)
        
        # Add widgets to splitter
        splitter.addWidget(browser_widget)
        splitter.addWidget(log_widget)
        splitter.setSizes([1000, 600])  # Set initial sizes
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_log_display)
        self.update_timer.start(1000)  # Update every second
        
        # Load initial page
        self.web_view.load(QUrl("https://httpbin.org/redirect/3"))
        
    def on_request_finished(self, request_data):
        """Handle when a request-response pair is complete"""
        print(f"Request-Response pair completed for: {request_data['url']}")
        
    def toggle_auto_scroll(self):
        """Toggle auto-scroll functionality"""
        if self.auto_scroll_button.isChecked():
            self.auto_scroll_button.setText("Auto Scroll: ON")
        else:
            self.auto_scroll_button.setText("Auto Scroll: OFF")
    
    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.web_view.load(QUrl(url))
        
    def url_changed(self, url):
        self.url_bar.setText(url.toString())
        
    def load_finished(self, success):
        # Small delay to allow responses to be captured
        QTimer.singleShot(2000, self.update_log_display)
        
    def go_back(self):
        self.web_view.back()
        
    def go_forward(self):
        self.web_view.forward()
        
    def refresh_page(self):
        self.web_view.reload()
        
    def update_log_display(self):
        log_text = ""
        recent_requests = self.network_monitor.requests[-30:]  # Show last 30 requests
        
        for i, request in enumerate(recent_requests):
            redirect_marker = " [REDIRECT]" if request['is_redirect'] else ""
            response_marker = " ✓" if request.get('response_received') else " ⏳"
            
            log_text += f"{len(recent_requests) - i}. {request['timestamp']}{response_marker}\n"
            log_text += f"   {request['method']} {request['url']}{redirect_marker}\n"
            log_text += f"   Type: {request['resource_type']}\n"
            
            # Add response information if available
            if request.get('response_received'):
                response = request['response_received']
                log_text += f"   Response: {response.get('status', 'N/A')} {response.get('statusText', '')}\n"
                
                # Show some response headers
                headers = response.get('headers', {})
                if isinstance(headers, dict) and headers:
                    content_type = headers.get('content-type', headers.get('Content-Type', ''))
                    if content_type:
                        log_text += f"   Content-Type: {content_type}\n"
                
                # Show response body preview (first 100 chars)
                body = response.get('body', '')
                if body and len(body) > 0:
                    preview = body[:100].replace('\n', ' ').replace('\r', '')
                    log_text += f"   Body Preview: {preview}{'...' if len(body) > 100 else ''}\n"
            
            log_text += "\n"
        
        self.log_text.setPlainText(log_text)
        
        # Auto scroll to bottom if enabled
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
        filename = f"browser_requests_responses_{timestamp}.json"
        
        try:
            # Create export data with better formatting
            export_data = {
                'export_timestamp': timestamp,
                'total_requests': len(self.network_monitor.requests),
                'requests_with_responses': len([r for r in self.network_monitor.requests if r.get('response_received')]),
                'requests': self.network_monitor.requests
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"Log exported to {filename}")
        except Exception as e:
            print(f"Error exporting log: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = BrowserWindow()
    window.show()
    
    sys.exit(app.exec_())
