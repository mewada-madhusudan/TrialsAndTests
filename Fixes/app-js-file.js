import React, { useState, useEffect, useRef } from 'react';
import { Monitor, Network, Globe, Eye, Download, Trash2, Play, Pause, RefreshCw, AlertCircle, ExternalLink } from 'lucide-react';
import './App.css';

const App = () => {
  const [requests, setRequests] = useState([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [targetUrl, setTargetUrl] = useState('');
  const [currentUrl, setCurrentUrl] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [filters, setFilters] = useState({ method: '', status: '', url: '' });
  const [autoScroll, setAutoScroll] = useState(true);
  const [iframeLoaded, setIframeLoaded] = useState(false);
  const [loadError, setLoadError] = useState('');
  const logContainerRef = useRef(null);
  const iframeRef = useRef(null);
  const requestIdCounter = useRef(0);
  const originalFetch = useRef(null);
  const originalXHR = useRef(null);

  // Intercept network requests in iframe
  const injectNetworkMonitor = () => {
    if (!iframeRef.current || !iframeRef.current.contentWindow) return;

    try {
      const iframeWindow = iframeRef.current.contentWindow;
      const iframeDocument = iframeRef.current.contentDocument;

      // Store original functions
      if (!originalFetch.current) {
        originalFetch.current = iframeWindow.fetch;
      }
      if (!originalXHR.current) {
        originalXHR.current = iframeWindow.XMLHttpRequest;
      }

      // Intercept fetch requests
      iframeWindow.fetch = function(...args) {
        const [resource, options = {}] = args;
        const url = typeof resource === 'string' ? resource : resource.url;
        const method = options.method || 'GET';
        
        const requestId = ++requestIdCounter.current;
        const timestamp = new Date().toISOString();
        const startTime = performance.now();
        
        const request = {
          id: requestId,
          timestamp,
          url: new URL(url, iframeWindow.location.href).href,
          method,
          status: 'pending',
          headers: {
            'Referer': iframeWindow.location.href,
            'User-Agent': navigator.userAgent,
            ...options.headers
          },
          responseHeaders: {},
          responseBody: '',
          duration: 0,
          size: 0,
          type: getResourceType(url),
          source: 'fetch'
        };

        setRequests(prev => [...prev, request]);

        return originalFetch.current.apply(this, args)
          .then(response => {
            const endTime = performance.now();
            const duration = Math.round(endTime - startTime);
            
            // Get response headers
            const responseHeaders = {};
            try {
              response.headers.forEach((value, key) => {
                responseHeaders[key] = value;
              });
            } catch (e) {
              // Headers might not be accessible due to CORS
              responseHeaders['note'] = 'Headers not accessible due to CORS policy';
            }

            // Clone response to read body without consuming it
            const responseClone = response.clone();
            
            // Try to read response body
            responseClone.text()
              .then(text => {
                const size = new Blob([text]).size;
                let responseBody = text;
                
                // Format JSON responses
                try {
                  const json = JSON.parse(text);
                  responseBody = JSON.stringify(json, null, 2);
                } catch (e) {
                  // Not JSON, keep as text
                }

                // Limit response body size for display
                if (responseBody.length > 10000) {
                  responseBody = responseBody.substring(0, 10000) + '\n... (truncated)';
                }

                setRequests(prev => prev.map(req => 
                  req.id === requestId ? {
                    ...req,
                    status: response.status,
                    statusText: response.statusText,
                    duration,
                    size,
                    responseHeaders,
                    responseBody
                  } : req
                ));
              })
              .catch(() => {
                // Couldn't read response body
                setRequests(prev => prev.map(req => 
                  req.id === requestId ? {
                    ...req,
                    status: response.status,
                    statusText: response.statusText,
                    duration,
                    size: 0,
                    responseHeaders,
                    responseBody: 'Response body not accessible'
                  } : req
                ));
              });

            return response;
          })
          .catch(error => {
            const endTime = performance.now();
            const duration = Math.round(endTime - startTime);
            
            setRequests(prev => prev.map(req => 
              req.id === requestId ? {
                ...req,
                status: 'error',
                statusText: error.message,
                duration,
                size: 0,
                responseHeaders: {},
                responseBody: `Error: ${error.message}`
              } : req
            ));
            
            throw error;
          });
      };

      // Intercept XMLHttpRequest
      iframeWindow.XMLHttpRequest = function() {
        const xhr = new originalXHR.current();
        const requestId = ++requestIdCounter.current;
        let requestData = {
          id: requestId,
          timestamp: new Date().toISOString(),
          url: '',
          method: 'GET',
          status: 'pending',
          headers: {},
          responseHeaders: {},
          responseBody: '',
          duration: 0,
          size: 0,
          type: 'xhr',
          source: 'XMLHttpRequest'
        };

        let startTime;

        // Override open method
        const originalOpen = xhr.open;
        xhr.open = function(method, url, async, user, password) {
          requestData.method = method;
          requestData.url = new URL(url, iframeWindow.location.href).href;
          requestData.type = getResourceType(url);
          startTime = performance.now();
          
          setRequests(prev => [...prev, requestData]);
          
          return originalOpen.call(this, method, url, async, user, password);
        };

        // Override send method
        const originalSend = xhr.send;
        xhr.send = function(body) {
          if (body) {
            requestData.requestBody = body;
          }
          return originalSend.call(this, body);
        };

        // Handle state changes
        xhr.addEventListener('readystatechange', function() {
          if (xhr.readyState === XMLHttpRequest.DONE) {
            const endTime = performance.now();
            const duration = startTime ? Math.round(endTime - startTime) : 0;
            
            // Get response headers
            const responseHeaders = {};
            try {
              const headerString = xhr.getAllResponseHeaders();
              if (headerString) {
                headerString.split('\r\n').forEach(line => {
                  const [key, value] = line.split(': ');
                  if (key && value) {
                    responseHeaders[key] = value;
                  }
                });
              }
            } catch (e) {
              responseHeaders['note'] = 'Headers not accessible';
            }

            let responseBody = '';
            let size = 0;
            try {
              responseBody = xhr.responseText || xhr.response || '';
              size = new Blob([responseBody]).size;
              
              // Format JSON responses
              if (xhr.getResponseHeader('content-type')?.includes('application/json')) {
                try {
                  const json = JSON.parse(responseBody);
                  responseBody = JSON.stringify(json, null, 2);
                } catch (e) {
                  // Keep as text
                }
              }
              
              // Limit response body size
              if (responseBody.length > 10000) {
                responseBody = responseBody.substring(0, 10000) + '\n... (truncated)';
              }
            } catch (e) {
              responseBody = 'Response body not accessible';
            }

            setRequests(prev => prev.map(req => 
              req.id === requestId ? {
                ...req,
                status: xhr.status || 'error',
                statusText: xhr.statusText || 'Network Error',
                duration,
                size,
                responseHeaders,
                responseBody
              } : req
            ));
          }
        });

        return xhr;
      };

      // Monitor resource loading (images, scripts, stylesheets)
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              // Monitor script tags
              if (node.tagName === 'SCRIPT' && node.src) {
                logResourceRequest(node.src, 'script');
              }
              // Monitor link tags (CSS)
              if (node.tagName === 'LINK' && node.href && node.rel === 'stylesheet') {
                logResourceRequest(node.href, 'stylesheet');
              }
              // Monitor img tags
              if (node.tagName === 'IMG' && node.src) {
                logResourceRequest(node.src, 'image');
              }
            }
          });
        });
      });

      observer.observe(iframeDocument, { childList: true, subtree: true });

    } catch (error) {
      console.log('Cannot inject network monitor (likely CORS restricted):', error.message);
      setLoadError('Cannot monitor this site due to CORS restrictions. Try a different URL.');
    }
  };

  const logResourceRequest = (url, type) => {
    const requestId = ++requestIdCounter.current;
    const request = {
      id: requestId,
      timestamp: new Date().toISOString(),
      url: new URL(url, currentUrl).href,
      method: 'GET',
      status: 'pending',
      headers: { 'Referer': currentUrl },
      responseHeaders: {},
      responseBody: `${type} resource`,
      duration: 0,
      size: 0,
      type,
      source: 'resource'
    };

    setRequests(prev => [...prev, request]);

    // Simulate completion after a delay
    setTimeout(() => {
      setRequests(prev => prev.map(req => 
        req.id === requestId ? {
          ...req,
          status: 200,
          statusText: 'OK',
          duration: Math.floor(Math.random() * 500) + 100
        } : req
      ));
    }, Math.random() * 1000 + 200);
  };

  const getResourceType = (url) => {
    if (url.includes('.js') || url.includes('javascript')) return 'script';
    if (url.includes('.css')) return 'stylesheet';
    if (url.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/)) return 'image';
    if (url.includes('api/') || url.includes('.json')) return 'xhr';
    if (url.includes('font') || url.match(/\.(woff|woff2|ttf|eot)$/)) return 'font';
    return 'document';
  };

  const getStatusColor = (status) => {
    if (status === 'pending') return 'text-yellow-600';
    if (status === 'error') return 'text-red-600';
    if (status >= 200 && status < 300) return 'text-green-600';
    if (status >= 300 && status < 400) return 'text-blue-600';
    if (status >= 400 && status < 500) return 'text-orange-600';
    if (status >= 500) return 'text-red-600';
    return 'text-gray-600';
  };

  const getMethodColor = (method) => {
    const colors = {
      'GET': 'bg-green-100 text-green-800',
      'POST': 'bg-blue-100 text-blue-800',
      'PUT': 'bg-yellow-100 text-yellow-800',
      'DELETE': 'bg-red-100 text-red-800',
      'PATCH': 'bg-purple-100 text-purple-800'
    };
    return colors[method] || 'bg-gray-100 text-gray-800';
  };

  const handleLoadWebsite = () => {
    if (!targetUrl.trim()) return;
    
    let url = targetUrl.trim();
    
    // Add protocol if missing
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }

    setCurrentUrl(url);
    setLoadError('');
    setIframeLoaded(false);
    clearRequests();

    // Load the website in iframe
    if (iframeRef.current) {
      iframeRef.current.src = url;
    }
  };

  const handleIframeLoad = () => {
    setIframeLoaded(true);
    setLoadError('');
    
    // Wait a bit for the iframe to fully load, then inject monitoring
    setTimeout(() => {
      if (isMonitoring) {
        injectNetworkMonitor();
      }
    }, 1000);
  };

  const handleIframeError = () => {
    setLoadError('Failed to load website. It may block iframe embedding or have CORS restrictions.');
    setIframeLoaded(false);
  };

  const toggleMonitoring = () => {
    setIsMonitoring(!isMonitoring);
    if (!isMonitoring && iframeLoaded) {
      // Start monitoring
      setTimeout(injectNetworkMonitor, 100);
    }
  };

  const filteredRequests = requests.filter(req => {
    const matchesMethod = !filters.method || req.method.toLowerCase().includes(filters.method.toLowerCase());
    const matchesStatus = !filters.status || req.status.toString().includes(filters.status);
    const matchesUrl = !filters.url || req.url.toLowerCase().includes(filters.url.toLowerCase());
    return matchesMethod && matchesStatus && matchesUrl;
  });

  const clearRequests = () => {
    setRequests([]);
    setSelectedRequest(null);
  };

  const exportRequests = () => {
    const dataStr = JSON.stringify(requests, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `network-requests-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Auto-scroll to bottom when new requests arrive
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [requests, autoScroll]);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Monitor className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Iframe Network Monitor</h1>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                isMonitoring ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {isMonitoring ? 'Monitoring Active' : 'Monitoring Inactive'}
              </span>
              {iframeLoaded && (
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  Website Loaded
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <div className="flex-1 min-w-64">
              <input
                type="text"
                placeholder="Enter website URL (e.g., example.com, news.ycombinator.com)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLoadWebsite()}
              />
            </div>
            <button
              onClick={handleLoadWebsite}
              disabled={!targetUrl.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Globe className="h-4 w-4" />
              <span>Load Website</span>
            </button>
            <button
              onClick={toggleMonitoring}
              disabled={!iframeLoaded}
              className={`px-4 py-2 rounded-lg flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed ${
                isMonitoring 
                  ? 'bg-red-600 text-white hover:bg-red-700' 
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {isMonitoring ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              <span>{isMonitoring ? 'Stop Monitor' : 'Start Monitor'}</span>
            </button>
            <button
              onClick={clearRequests}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center space-x-2"
            >
              <Trash2 className="h-4 w-4" />
              <span>Clear</span>
            </button>
            <button
              onClick={exportRequests}
              disabled={requests.length === 0}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>

          {loadError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-red-700">{loadError}</span>
            </div>
          )}

          {/* Current URL Display */}
          {currentUrl && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <ExternalLink className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">Currently loaded:</span>
                <span className="text-sm text-blue-700 break-all">{currentUrl}</span>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-4 pt-4 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Method:</label>
              <input
                type="text"
                placeholder="GET, POST..."
                className="px-3 py-1 border border-gray-300 rounded text-sm w-24"
                value={filters.method}
                onChange={(e) => setFilters(prev => ({ ...prev, method: e.target.value }))}
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Status:</label>
              <input
                type="text"
                placeholder="200, 404..."
                className="px-3 py-1 border border-gray-300 rounded text-sm w-20"
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">URL:</label>
              <input
                type="text"
                placeholder="Filter by URL..."
                className="px-3 py-1 border border-gray-300 rounded text-sm w-40"
                value={filters.url}
                onChange={(e) => setFilters(prev => ({ ...prev, url: e.target.value }))}
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoScroll"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="autoScroll" className="text-sm font-medium text-gray-700">Auto-scroll</label>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Website Iframe */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                  <Globe className="h-5 w-5" />
                  <span>Website Preview</span>
                </h2>
              </div>
              <div className="h-96">
                {currentUrl ? (
                  <iframe
                    ref={iframeRef}
                    src={currentUrl}
                    className="w-full h-full border-0 rounded-b-lg"
                    onLoad={handleIframeLoad}
                    onError={handleIframeError}
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-navigation"
                    title="Website Preview"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <Globe className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                      <p>Enter a website URL to start monitoring</p>
                      <p className="text-sm mt-2">Examples: example.com, news.ycombinator.com</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Request List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                  <Network className="h-5 w-5" />
                  <span>Network Requests ({filteredRequests.length})</span>
                </h2>
              </div>
              <div 
                ref={logContainerRef}
                className="h-96 overflow-y-auto"
              >
                {filteredRequests.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <Network className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                      <p>No network requests yet</p>
                      <p className="text-sm">Load a website and start monitoring to see requests</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {filteredRequests.map((request) => (
                      <div
                        key={request.id}
                        className={`p-3 border-l-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                          selectedRequest?.id === request.id ? 'bg-blue-50 border-l-blue-500' : 'border-l-transparent'
                        }`}
                        onClick={() => setSelectedRequest(request)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <span className={`px-2 py-1 text-xs font-medium rounded ${getMethodColor(request.method)}`}>
                              {request.method}
                            </span>
                            <span className={`font-medium ${getStatusColor(request.status)}`}>
                              {request.status === 'pending' ? '⏳' : request.status === 'error' ? '❌' : request.status}
                            </span>
                            <span className="text-sm text-gray-600 truncate flex-1">
                              {request.url.replace(currentUrl, '').replace(/^\//, '') || '/'}
                            </span>
                          </div>
                          <div className="flex items-center space-x-3 text-sm text-gray-500">
                            <span className="text-xs px-1 py-0.5 bg-gray-100 rounded">{request.type}</span>
                            {request.duration > 0 && <span>{request.duration}ms</span>}
                            {request.size > 0 && <span>{(request.size / 1024).toFixed(1)}KB</span>}
                            <span>{new Date(request.timestamp).toLocaleTimeString()}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Request Details */}
        {selectedRequest && (
          <div className="mt-6 bg-white rounded-lg shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <Eye className="h-5 w-5" />
                <span>Request Details</span>
              </h2>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">General</h3>
                    <div className="space-y-1 text-sm">
                      <div><strong>URL:</strong> <span className="break-all">{selectedRequest.url}</span></div>
                      <div><strong>Method:</strong> {selectedRequest.method}</div>
                      <div><strong>Status:</strong> {selectedRequest.status} {selectedRequest.statusText}</div>
                      <div><strong>Type:</strong> {selectedRequest.type}</div>
                      <div><strong>Source:</strong> {selectedRequest.source}</div>
                      <div><strong>Time:</strong> {new Date(selectedRequest.timestamp).toLocaleString()}</div>
                      {selectedRequest.duration > 0 && (
                        <div><strong>Duration:</strong> {selectedRequest.duration}ms</div>
                      )}
                      {selectedRequest.size > 0 && (
                        <div><strong>Size:</strong> {(selectedRequest.size / 1024).toFixed(1)}KB</div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Request Headers</h3>
                    <div className="bg-gray-50 rounded p-3 text-xs font-mono max-h-32 overflow-y-auto">
                      {Object.entries(selectedRequest.headers).map(([key, value]) => (
                        <div key={key} className="mb-1 break-all">
                          <strong>{key}:</strong> {value}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  {Object.keys(selectedRequest.responseHeaders).length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Response Headers</h3>
                      <div className="bg-gray-50 rounded p-3 text-xs font-mono max-h-32 overflow-y-auto">
                        {Object.entries(selectedRequest.responseHeaders).map(([key, value]) => (
                          <div key={key} className="mb-1 break-all">
                            <strong>{key}:</strong> {value}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedRequest.responseBody && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Response Body</h3>
                      <div className="bg-gray-50 rounded p-3 text-xs font-mono max-h-40 overflow-y-auto">
                        <pre className="whitespace-pre-wrap break-all">{selectedRequest.responseBody}</pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="mt-6 bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Session Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{requests.length}</div>
              <div className="text-sm text-gray-600">Total Requests</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {requests.filter(r => r.status >= 200 && r.status < 300).length}
              </div>
              <div className="text-sm text-gray-600">Successful</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {requests.filter(r => r.status >= 400 || r.status === 'error').length}
              </div>
              <div className="text-sm text-gray-600">Failed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {requests.filter(r => r.status === 'pending').length}
              </div>
              <div className="text-sm text-gray-600">Pending</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {requests.length > 0 ? Math.round(requests.reduce((acc, r) => acc + (r.duration || 0), 0) / requests.length) : 0}ms
              </div>
              <div className="text-sm text-gray-600">Avg Duration</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-600">
                {requests.filter(r => r.type === 'xhr').length}
              </div>
              <div className="text-sm text-gray-600">API Calls</div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-yellow-800 mb-2">How to Use</h3>
          <div className="text-sm text-yellow-700 space-y-2">
            <p><strong>1.</strong> Enter a website URL (e.g., example.com, news.ycombinator.com)</p>
            <p><strong>2.</strong> Click "Load Website" to open it in the iframe</p>
            <p><strong>3.</strong> Click "Start Monitor" to begin tracking network requests</p>
            <p><strong>4.</strong> Interact with the website to see real-time network activity</p>
            <p><strong>Note:</strong> Some websites may block iframe embedding or restrict access due to CORS policies.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
