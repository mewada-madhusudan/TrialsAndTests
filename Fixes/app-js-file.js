import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Monitor, Network, Globe, Eye, Download, Trash2, Play, Pause, RefreshCw, AlertCircle, ExternalLink, Server, Shield, Activity, Clock, FileText } from 'lucide-react';

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
  const [proxyMode, setProxyMode] = useState('iframe');
  const [corsProxyUrl, setCorsProxyUrl] = useState('https://api.allorigins.win/get?url=');
  const [showStats, setShowStats] = useState(true);
  const logContainerRef = useRef(null);
  const iframeRef = useRef(null);
  const requestIdCounter = useRef(0);

  // CORS Proxy Services
  const corsProxies = [
    { 
      name: 'AllOrigins', 
      url: 'https://api.allorigins.win/get?url=', 
      description: 'Free, reliable with content parsing',
      type: 'json'
    },
    { 
      name: 'CORS Anywhere', 
      url: 'https://cors-anywhere.herokuapp.com/', 
      description: 'Popular but requires demo access',
      type: 'direct'
    },
    { 
      name: 'ThingProxy', 
      url: 'https://thingproxy.freeboard.io/fetch/', 
      description: 'Simple and fast',
      type: 'direct'
    },
    { 
      name: 'CORS.SH', 
      url: 'https://cors.sh/', 
      description: 'Modern proxy service',
      type: 'direct'
    },
    { 
      name: 'Proxy Server', 
      url: 'https://api.codetabs.com/v1/proxy?quest=', 
      description: 'CodeTabs proxy service',
      type: 'direct'
    }
  ];

  // Enhanced request logging function
  const logRequest = useCallback((requestData) => {
    const request = {
      id: ++requestIdCounter.current,
      timestamp: new Date().toISOString(),
      startTime: performance.now(),
      ...requestData
    };
    
    setRequests(prev => [...prev, request]);
    return request.id;
  }, []);

  // Update request with response data
  const updateRequest = useCallback((requestId, updateData) => {
    setRequests(prev => prev.map(req => 
      req.id === requestId ? { ...req, ...updateData } : req
    ));
  }, []);

  // CORS Proxy request handler
  const makeProxyRequest = async (url, method = 'GET', options = {}) => {
    const requestId = logRequest({
      url,
      method,
      status: 'pending',
      headers: {
        'User-Agent': navigator.userAgent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': navigator.language,
        ...options.headers
      },
      responseHeaders: {},
      responseBody: '',
      duration: 0,
      size: 0,
      type: getResourceType(url),
      source: 'cors-proxy'
    });

    try {
      const selectedProxy = corsProxies.find(p => p.url === corsProxyUrl);
      let proxyUrl;
      let fetchOptions = {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/json, text/plain, */*',
          'X-Requested-With': 'XMLHttpRequest'
        }
      };

      // Handle different proxy types
      if (selectedProxy?.type === 'json') {
        // AllOrigins format
        proxyUrl = corsProxyUrl + encodeURIComponent(url);
      } else {
        // Direct proxy format
        proxyUrl = corsProxyUrl + encodeURIComponent(url);
      }

      const startTime = performance.now();
      const response = await fetch(proxyUrl, fetchOptions);
      const endTime = performance.now();
      const duration = Math.round(endTime - startTime);
      
      // Get response headers
      const responseHeaders = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });

      let responseBody = '';
      let size = 0;

      if (selectedProxy?.type === 'json') {
        // Handle AllOrigins JSON response
        const jsonResponse = await response.json();
        responseBody = jsonResponse.contents || jsonResponse.data || JSON.stringify(jsonResponse, null, 2);
        
        // Try to parse as JSON for better formatting
        try {
          const parsed = JSON.parse(responseBody);
          responseBody = JSON.stringify(parsed, null, 2);
        } catch (e) {
          // Keep as text
        }
      } else {
        // Handle direct proxy response
        responseBody = await response.text();
      }

      size = new Blob([responseBody]).size;

      // Limit response body size for display
      if (responseBody.length > 10000) {
        responseBody = responseBody.substring(0, 10000) + '\n... (truncated - ' + (responseBody.length - 10000) + ' more characters)';
      }

      updateRequest(requestId, {
        status: response.status,
        statusText: response.statusText,
        duration,
        size,
        responseHeaders,
        responseBody,
        strategy: selectedProxy?.name || 'Unknown Proxy'
      });

    } catch (error) {
      const endTime = performance.now();
      const duration = Math.round(endTime - performance.now());
      
      updateRequest(requestId, {
        status: 'error',
        statusText: error.message,
        duration,
        size: 0,
        responseHeaders: {},
        responseBody: `Proxy Error: ${error.message}\n\nTip: Try a different proxy service or check if the target URL is accessible.`,
        strategy: 'failed'
      });
    }
  };

  // Advanced multi-strategy request
  const makeAdvancedRequest = async (url, method = 'GET', options = {}) => {
    const requestId = logRequest({
      url,
      method,
      status: 'pending',
      headers: {
        'User-Agent': navigator.userAgent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': navigator.language,
        ...options.headers
      },
      responseHeaders: {},
      responseBody: '',
      duration: 0,
      size: 0,
      type: getResourceType(url),
      source: 'advanced-multi'
    });

    const strategies = [
      {
        name: 'Direct CORS',
        execute: () => fetch(url, { method, mode: 'cors', ...options })
      },
      {
        name: 'No-CORS Mode',
        execute: () => fetch(url, { method, mode: 'no-cors', ...options })
      },
      ...(method === 'GET' ? [{
        name: 'JSONP',
        execute: () => makeJSONPRequest(url)
      }] : []),
      {
        name: 'AllOrigins Proxy',
        execute: () => fetch(`https://api.allorigins.win/get?url=${encodeURIComponent(url)}`, { mode: 'cors' })
      },
      {
        name: 'ThingProxy',
        execute: () => fetch(`https://thingproxy.freeboard.io/fetch/${url}`, { mode: 'cors' })
      }
    ];

    const startTime = performance.now();
    let lastError = null;

    for (let i = 0; i < strategies.length; i++) {
      const strategy = strategies[i];
      
      try {
        updateRequest(requestId, {
          status: 'pending',
          statusText: `Trying ${strategy.name}...`,
          strategy: strategy.name
        });

        const response = await strategy.execute();
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);
        
        let responseHeaders = {};
        let responseBody = '';
        let size = 0;
        let status = response.status || 200;
        let statusText = response.statusText || 'OK';

        // Handle different response types
        try {
          if (response.headers) {
            response.headers.forEach((value, key) => {
              responseHeaders[key] = value;
            });
          }

          // Handle AllOrigins response
          if (strategy.name === 'AllOrigins Proxy') {
            const jsonResponse = await response.json();
            responseBody = jsonResponse.contents || JSON.stringify(jsonResponse, null, 2);
            status = jsonResponse.status || 200;
          } else if (response.text) {
            responseBody = await response.text();
            
            // Try to format JSON
            try {
              const json = JSON.parse(responseBody);
              responseBody = JSON.stringify(json, null, 2);
            } catch (e) {
              // Not JSON, keep as text
            }
          } else if (response.data) {
            // JSONP response
            responseBody = JSON.stringify(response.data, null, 2);
          }

          size = new Blob([responseBody]).size;

        } catch (e) {
          if (strategy.name === 'No-CORS Mode') {
            responseBody = 'Response received but content not accessible due to CORS policy (opaque response)';
            status = 'opaque';
            statusText = 'Opaque Response - Request successful but content hidden';
          } else {
            throw e; // Continue to next strategy
          }
        }

        // Limit response body size
        if (responseBody.length > 10000) {
          responseBody = responseBody.substring(0, 10000) + '\n... (truncated)';
        }

        updateRequest(requestId, {
          status,
          statusText,
          duration,
          size,
          responseHeaders,
          responseBody,
          strategy: `${strategy.name} ✓`
        });

        return; // Success, exit the loop
        
      } catch (error) {
        lastError = error;
        console.log(`Strategy "${strategy.name}" failed:`, error.message);
        
        // If this is the last strategy, update with final error
        if (i === strategies.length - 1) {
          const endTime = performance.now();
          const duration = Math.round(endTime - startTime);
          
          updateRequest(requestId, {
            status: 'error',
            statusText: `All strategies failed`,
            duration,
            size: 0,
            responseHeaders: {},
            responseBody: `All ${strategies.length} request strategies failed:\n\n${
              strategies.map((s, idx) => `${idx + 1}. ${s.name}`).join('\n')
            }\n\nLast error: ${lastError.message}\n\nSuggestion: The target URL might not support CORS or may be blocking requests.`,
            strategy: 'All Failed ✗'
          });
        }
      }
    }
  };

  // JSONP implementation
  const makeJSONPRequest = (url) => {
    return new Promise((resolve, reject) => {
      const callbackName = 'jsonp_callback_' + Math.round(100000 * Math.random());
      const script = document.createElement('script');
      
      const separator = url.includes('?') ? '&' : '?';
      const jsonpUrl = `${url}${separator}callback=${callbackName}`;
      
      window[callbackName] = function(data) {
        resolve({ data, status: 200, statusText: 'OK' });
        document.head.removeChild(script);
        delete window[callbackName];
      };

      script.onerror = function() {
        reject(new Error('JSONP request failed - target may not support JSONP'));
        if (document.head.contains(script)) {
          document.head.removeChild(script);
        }
        delete window[callbackName];
      };

      script.src = jsonpUrl;
      document.head.appendChild(script);
      
      setTimeout(() => {
        if (window[callbackName]) {
          reject(new Error('JSONP request timeout (10s)'));
          if (document.head.contains(script)) {
            document.head.removeChild(script);
          }
          delete window[callbackName];
        }
      }, 10000);
    });
  };

  // Iframe network monitoring
  const injectNetworkMonitor = () => {
    if (!iframeRef.current?.contentWindow) return;

    try {
      const iframeWindow = iframeRef.current.contentWindow;
      
      // Override fetch
      const originalFetch = iframeWindow.fetch;
      iframeWindow.fetch = function(...args) {
        const [resource, options = {}] = args;
        const url = typeof resource === 'string' ? resource : resource.url;
        const method = options.method || 'GET';
        
        const requestId = logRequest({
          url: new URL(url, iframeWindow.location.href).href,
          method,
          status: 'pending',
          headers: { 'Referer': iframeWindow.location.href },
          responseHeaders: {},
          responseBody: '',
          duration: 0,
          size: 0,
          type: getResourceType(url),
          source: 'iframe-fetch'
        });
        
        const startTime = performance.now();
        
        return originalFetch.apply(this, args)
          .then(response => {
            const duration = Math.round(performance.now() - startTime);
            updateRequest(requestId, {
              status: response.status,
              statusText: response.statusText,
              duration,
              strategy: 'Iframe Fetch'
            });
            return response;
          })
          .catch(error => {
            const duration = Math.round(performance.now() - startTime);
            updateRequest(requestId, {
              status: 'error',
              statusText: error.message,
              duration,
              responseBody: `Iframe Fetch Error: ${error.message}`,
              strategy: 'Iframe Fetch Failed'
            });
            throw error;
          });
      };

      // Override XMLHttpRequest
      const originalXHR = iframeWindow.XMLHttpRequest;
      iframeWindow.XMLHttpRequest = function() {
        const xhr = new originalXHR();
        let requestUrl = '';
        let requestMethod = 'GET';
        let requestId = null;
        let startTime = 0;

        const originalOpen = xhr.open;
        xhr.open = function(method, url, async, user, password) {
          requestMethod = method;
          requestUrl = new URL(url, iframeWindow.location.href).href;
          startTime = performance.now();
          
          requestId = logRequest({
            url: requestUrl,
            method: requestMethod,
            status: 'pending',
            headers: { 'Referer': iframeWindow.location.href },
            responseHeaders: {},
            responseBody: '',
            duration: 0,
            size: 0,
            type: getResourceType(requestUrl),
            source: 'iframe-xhr'
          });
          
          return originalOpen.call(this, method, url, async, user, password);
        };

        xhr.addEventListener('readystatechange', function() {
          if (xhr.readyState === XMLHttpRequest.DONE && requestId) {
            const duration = Math.round(performance.now() - startTime);
            updateRequest(requestId, {
              status: xhr.status,
              statusText: xhr.statusText,
              duration,
              strategy: 'Iframe XHR'
            });
          }
        });

        return xhr;
      };

      console.log('Network monitor injected successfully');

    } catch (error) {
      console.log('Cannot inject network monitor (CORS/security restricted):', error.message);
      setLoadError('Cannot monitor cross-origin iframe due to security restrictions. Use Proxy Mode for full monitoring.');
    }
  };

  const getResourceType = (url) => {
    if (url.includes('.js') || url.includes('javascript')) return 'script';
    if (url.includes('.css')) return 'stylesheet';
    if (url.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/i)) return 'image';
    if (url.includes('api/') || url.includes('.json')) return 'xhr';
    if (url.includes('font') || url.match(/\.(woff|woff2|ttf|eot)$/i)) return 'font';
    return 'document';
  };

  const getStatusColor = (status) => {
    if (status === 'pending') return 'text-yellow-600';
    if (status === 'error') return 'text-red-600';
    if (status === 'opaque') return 'text-purple-600';
    if (typeof status === 'number') {
      if (status >= 200 && status < 300) return 'text-green-600';
      if (status >= 300 && status < 400) return 'text-blue-600';
      if (status >= 400 && status < 500) return 'text-orange-600';
      if (status >= 500) return 'text-red-600';
    }
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

  const getTypeIcon = (type) => {
    const icons = {
      'script': '📜',
      'stylesheet': '🎨',
      'image': '🖼️',
      'xhr': '📡',
      'font': '🔤',
      'document': '📄'
    };
    return icons[type] || '📄';
  };

  const handleLoadWebsite = () => {
    if (!targetUrl.trim()) return;
    
    let url = targetUrl.trim();
    
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }

    setCurrentUrl(url);
    setLoadError('');
    clearRequests();

    if (proxyMode === 'cors-proxy') {
      makeProxyRequest(url);
    } else if (proxyMode === 'advanced') {
      makeAdvancedRequest(url);
    } else {
      setIframeLoaded(false);
      if (iframeRef.current) {
        iframeRef.current.src = url;
      }
    }
  };

  const handleIframeLoad = () => {
    setIframeLoaded(true);
    setLoadError('');
    
    setTimeout(() => {
      if (isMonitoring) {
        injectNetworkMonitor();
      }
    }, 1000);
  };

  const handleIframeError = () => {
    setLoadError('Failed to load website in iframe. This may be due to X-Frame-Options or CORS policy. Try Proxy Mode or Advanced Mode.');
    setIframeLoaded(false);
  };

  const toggleMonitoring = () => {
    setIsMonitoring(!isMonitoring);
    if (!isMonitoring && iframeLoaded && proxyMode === 'iframe') {
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

  // Statistics
  const stats = {
    total: requests.length,
    successful: requests.filter(r => typeof r.status === 'number' && r.status >= 200 && r.status < 400).length,
    failed: requests.filter(r => r.status === 'error' || (typeof r.status === 'number' && r.status >= 400)).length,
    pending: requests.filter(r => r.status === 'pending').length,
    avgDuration: requests.length > 0 ? Math.round(requests.reduce((sum, r) => sum + (r.duration || 0), 0) / requests.length) : 0,
    totalSize: requests.reduce((sum, r) => sum + (r.size || 0), 0)
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Auto-scroll effect
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [requests, autoScroll]);

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Monitor className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Advanced Network Monitor</h1>
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-green-600" />
                <span className="text-sm text-gray-600">CORS Bypass Enabled</span>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                isMonitoring ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {isMonitoring ? '🟢 Active' : '⚪ Inactive'}
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                proxyMode === 'iframe' ? 'bg-blue-100 text-blue-800' :
                proxyMode === 'cors-proxy' ? 'bg-purple-100 text-purple-800' :
                'bg-orange-100 text-orange-800'
              }`}>
                {proxyMode === 'iframe' ? '🖼️ Iframe' :
                 proxyMode === 'cors-proxy' ? '🌐 Proxy' : '⚡ Advanced'}
              </div>
            </div>
          </div>
        </div>

        {/* Statistics */}
        {showStats && stats.total > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-gray-900">Request Statistics</h3>
              <button
                onClick={() => setShowStats(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-center">
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
                <div className="text-sm text-blue-800">Total</div>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-green-600">{stats.successful}</div>
                <div className="text-sm text-green-800">Success</div>
              </div>
              <div className="bg-red-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
                <div className="text-sm text-red-800">Failed</div>
              </div>
              <div className="bg-yellow-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
                <div className="text-sm text-yellow-800">Pending</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-purple-600">{stats.avgDuration}ms</div>
                <div className="text-sm text-purple-800">Avg Time</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-gray-600">{formatBytes(stats.totalSize)}</div>
                <div className="text-sm text-gray-800">Total Size</div>
              </div>
            </div>
          </div>
        )}

        {/* Mode Selection */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">CORS Bypass Strategy</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {[
              {
                id: 'iframe',
                icon: Globe,
                title: 'Iframe Mode',
                description: 'Load website in iframe with network monitoring. Best for same-origin or CORS-enabled sites.',
                color: 'blue'
              },
              {
                id: 'cors-proxy',
                icon: Server,
                title: 'CORS Proxy',
                description: 'Use external proxy servers to bypass CORS completely. Works with any URL.',
                color: 'purple'
              },
              {
                id: 'advanced',
                icon: RefreshCw,
                title: 'Multi-Strategy',
                description: 'Try multiple approaches: direct, no-cors, JSONP, and proxy fallbacks automatically.',
                color: 'orange'
              }
            ].map(mode => {
              const Icon = mode.icon;
              const isSelected = proxyMode === mode.id;
              return (
                <div
                  key={mode.id}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    isSelected 
                      ? `border-${mode.color}-500 bg-${mode.color}-50 shadow-md` 
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}
                  onClick={() => setProxyMode(mode.id)}
                >
                  <div className="flex items-center space-x-2 mb-2">
                    <Icon className={`h-5 w-5 text-${mode.color}-600`} />
                    <h3 className="font-medium">{mode.title}</h3>
                    {isSelected && <span className="text-sm text-green-600">✓</span>}
                  </div>
                  <p className="text-sm text-gray-600">{mode.description}</p>
                </div>
              );
            })}
          </div>

          {/* CORS Proxy Selection */}
          {proxyMode === 'cors-proxy' && (
            <div className="border-t pt-4">
              <h3 className="font-medium text-gray-900 mb-3">Select CORS Proxy Service</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {corsProxies.map((proxy, index) => (
                  <div
                    key={index}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      corsProxyUrl === proxy.url 
                        ? 'border-purple-500 bg-purple-50 shadow-sm' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setCorsProxyUrl(proxy.url)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-sm flex items-center space-x-1">
                          <span>{proxy.name}</span>
                          {corsProxyUrl === proxy.url && <span className="text-purple-600">✓</span>}
                        </h4>
                        <p className="text-xs text-gray-600">{proxy.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <div className="flex-1 min-w-64">
              <input
                type="text"
                placeholder={`Enter website URL ${
                  proxyMode === 'iframe' ? '(e.g., example.com)' :
                  proxyMode === 'cors-proxy' ? '(any URL - CORS bypass enabled)' :
                  '(any URL - multiple strategies will be tried)'
                }`}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLoadWebsite()}
              />
            </div>
            <button
              onClick={handleLoadWebsite}
              disabled={!targetUrl.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
            >
              <Globe className="h-4 w-4" />
              <span>{proxyMode === 'iframe' ? 'Load Website' : 'Make Request'}</span>
            </button>
            {proxyMode === 'iframe' && (
              <button
                onClick={toggleMonitoring}
                disabled={!iframeLoaded}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${
                  isMonitoring 
                    ? 'bg-red-600 text-white hover:bg-red-700' 
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {isMonitoring ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                <span>{isMonitoring ? 'Stop Monitor' : 'Start Monitor'}</span>
              </button>
            )}
            <button
              onClick={clearRequests}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center space-x-2 transition-colors"
            >
              <Trash2 className="h-4 w-4" />
              <span>Clear</span>
            </button>
            <button
              onClick={exportRequests}
              disabled={requests.length === 0}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>

          {loadError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
              <span className="text-red-700">{loadError}</span>
            </div>
          )}

          {currentUrl && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <ExternalLink className="h-4 w-4 text-blue-600 flex-shrink-0" />
                <span className="text-sm font-medium text-blue-900">Target URL:</span>
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
                className="px-3 py-1 border border-gray-300 rounded text-sm w-24 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                value={filters.method}
                onChange={(e) => setFilters(prev => ({ ...prev, method: e.target.value }))}
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Status:</label>
              <input
                type="text"
                placeholder="200, 404..."
                className="px-3 py-1 border border-gray-300 rounded text-sm w-20 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">URL Contains:</label>
              <input
                type="text"
                placeholder="Filter by URL..."
                className="px-3 py-1 border border-gray-300 rounded text-sm w-40 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
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
                className="text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="autoScroll" className="text-sm font-medium text-gray-700">Auto-scroll</label>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Activity className="h-4 w-4" />
              <span>{filteredRequests.length} of {requests.length} requests</span>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Website Display */}
          {proxyMode === 'iframe' && (
            <div className="bg-white rounded-lg shadow-sm overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h3 className="font-medium text-gray-900 flex items-center space-x-2">
                  <Globe className="h-4 w-4" />
                  <span>Website Preview</span>
                  {iframeLoaded && (
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      Loaded
                    </span>
                  )}
                </h3>
              </div>
              <div className="relative h-96">
                {currentUrl ? (
                  <iframe
                    ref={iframeRef}
                    src={currentUrl}
                    className="w-full h-full border-0"
                    onLoad={handleIframeLoad}
                    onError={handleIframeError}
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
                    title="Website Preview"
                  />
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <Globe className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>Enter a URL to load website</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Request Log */}
          <div className={`bg-white rounded-lg shadow-sm overflow-hidden ${proxyMode === 'iframe' ? '' : 'lg:col-span-2'}`}>
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <h3 className="font-medium text-gray-900 flex items-center space-x-2">
                <Network className="h-4 w-4" />
                <span>Network Requests</span>
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  {filteredRequests.length}
                </span>
              </h3>
            </div>
            <div 
              ref={logContainerRef}
              className="h-96 overflow-y-auto"
            >
              {filteredRequests.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Network className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                    <p>No network requests yet</p>
                    <p className="text-sm text-gray-400 mt-1">
                      {proxyMode === 'iframe' 
                        ? 'Load a website and start monitoring to see requests'
                        : 'Enter a URL and make a request to see the response'
                      }
                    </p>
                  </div>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {filteredRequests.map((request) => (
                    <div
                      key={request.id}
                      className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                        selectedRequest?.id === request.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                      }`}
                      onClick={() => setSelectedRequest(request)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-lg">{getTypeIcon(request.type)}</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getMethodColor(request.method)}`}>
                              {request.method}
                            </span>
                            <span className={`font-medium ${getStatusColor(request.status)}`}>
                              {request.status}
                            </span>
                            {request.strategy && (
                              <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                                {request.strategy}
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-gray-900 font-medium truncate mb-1">
                            {request.url}
                          </div>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span className="flex items-center space-x-1">
                              <Clock className="h-3 w-3" />
                              <span>{request.duration}ms</span>
                            </span>
                            {request.size > 0 && (
                              <span className="flex items-center space-x-1">
                                <FileText className="h-3 w-3" />
                                <span>{formatBytes(request.size)}</span>
                              </span>
                            )}
                            <span>{new Date(request.timestamp).toLocaleTimeString()}</span>
                            <span className="text-xs bg-gray-100 text-gray-600 px-1 rounded">
                              {request.source}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {request.status === 'pending' && (
                            <div className="animate-spin h-4 w-4 border-2 border-yellow-500 border-t-transparent rounded-full"></div>
                          )}
                          <Eye className="h-4 w-4 text-gray-400" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Request Details Modal */}
        {selectedRequest && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
              <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="font-semibold text-gray-900 flex items-center space-x-2">
                  <span className="text-lg">{getTypeIcon(selectedRequest.type)}</span>
                  <span>Request Details</span>
                </h3>
                <button
                  onClick={() => setSelectedRequest(null)}
                  className="text-gray-400 hover:text-gray-600 text-xl font-bold"
                >
                  ×
                </button>
              </div>
              
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                <div className="space-y-6">
                  {/* Request Info */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Request Information</h4>
                    <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm font-medium text-gray-700">Method:</span>
                          <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${getMethodColor(selectedRequest.method)}`}>
                            {selectedRequest.method}
                          </span>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-700">Status:</span>
                          <span className={`ml-2 font-medium ${getStatusColor(selectedRequest.status)}`}>
                            {selectedRequest.status} {selectedRequest.statusText}
                          </span>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-700">Duration:</span>
                          <span className="ml-2 text-sm text-gray-900">{selectedRequest.duration}ms</span>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-700">Size:</span>
                          <span className="ml-2 text-sm text-gray-900">{formatBytes(selectedRequest.size)}</span>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-700">Type:</span>
                          <span className="ml-2 text-sm text-gray-900">{selectedRequest.type}</span>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-700">Source:</span>
                          <span className="ml-2 text-sm text-gray-900">{selectedRequest.source}</span>
                        </div>
                      </div>
                      <div className="pt-2">
                        <span className="text-sm font-medium text-gray-700">URL:</span>
                        <div className="mt-1 p-2 bg-white rounded border text-sm font-mono break-all">
                          {selectedRequest.url}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Request Headers */}
                  {Object.keys(selectedRequest.headers || {}).length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Request Headers</h4>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <pre className="text-sm font-mono text-gray-800 whitespace-pre-wrap">
                          {JSON.stringify(selectedRequest.headers, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Response Headers */}
                  {Object.keys(selectedRequest.responseHeaders || {}).length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Response Headers</h4>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <pre className="text-sm font-mono text-gray-800 whitespace-pre-wrap">
                          {JSON.stringify(selectedRequest.responseHeaders, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Response Body */}
                  {selectedRequest.responseBody && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Response Body</h4>
                      <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                        <pre className="text-sm font-mono text-gray-800 whitespace-pre-wrap">
                          {selectedRequest.responseBody}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
