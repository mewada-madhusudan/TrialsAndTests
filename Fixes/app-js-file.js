import React, { useState, useEffect, useRef } from 'react';
import { Monitor, Network, Globe, Eye, Download, Trash2, Play, Pause, RefreshCw, AlertCircle } from 'lucide-react';
import './App.css';

const App = () => {
  const [requests, setRequests] = useState([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [targetUrl, setTargetUrl] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [filters, setFilters] = useState({ method: '', status: '', url: '' });
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef(null);
  const requestIdCounter = useRef(0);

  // Real network request function
  const makeActualRequest = async (url, method = 'GET', options = {}) => {
    const requestId = ++requestIdCounter.current;
    const timestamp = new Date().toISOString();
    const startTime = performance.now();
    
    const request = {
      id: requestId,
      timestamp,
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
      type: getResourceType(url)
    };

    setRequests(prev => [...prev, request]);

    try {
      // Make actual fetch request
      const fetchOptions = {
        method,
        mode: 'cors', // Handle CORS
        ...options
      };

      const response = await fetch(url, fetchOptions);
      const endTime = performance.now();
      const duration = Math.round(endTime - startTime);
      
      // Get response headers
      const responseHeaders = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });

      // Get response body (handle different content types)
      let responseBody = '';
      let size = 0;
      
      try {
        const contentType = response.headers.get('content-type') || '';
        
        if (contentType.includes('application/json')) {
          const jsonData = await response.clone().json();
          responseBody = JSON.stringify(jsonData, null, 2);
        } else if (contentType.includes('text/')) {
          responseBody = await response.clone().text();
        } else {
          responseBody = `[${contentType || 'Binary data'}] - ${response.size || 'Unknown size'}`;
        }
        
        // Estimate size
        size = new Blob([responseBody]).size;
      } catch (e) {
        responseBody = 'Unable to read response body';
      }

      // Update request with response data
      setRequests(prev => prev.map(req => 
        req.id === requestId ? {
          ...req,
          status: response.status,
          statusText: response.statusText,
          duration,
          size,
          responseHeaders,
          responseBody: responseBody.length > 10000 ? responseBody.substring(0, 10000) + '...' : responseBody
        } : req
      ));

    } catch (error) {
      const endTime = performance.now();
      const duration = Math.round(endTime - startTime);
      
      // Update request with error
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
    }
  };

  const getResourceType = (url) => {
    if (url.includes('.js')) return 'script';
    if (url.includes('.css')) return 'stylesheet';
    if (url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/)) return 'image';
    if (url.includes('api/') || url.includes('.json')) return 'xhr';
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

  const handleMakeRequest = async () => {
    if (!targetUrl.trim()) return;
    
    let url = targetUrl.trim();
    
    // Add protocol if missing
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }

    // Make the actual request
    await makeActualRequest(url);
  };

  // Test different types of requests
  const testRequests = [
    { name: 'JSON API', url: 'https://jsonplaceholder.typicode.com/posts/1' },
    { name: 'Image', url: 'https://httpbin.org/image/png' },
    { name: 'Headers', url: 'https://httpbin.org/headers' },
    { name: 'Status 404', url: 'https://httpbin.org/status/404' },
    { name: 'Delay 2s', url: 'https://httpbin.org/delay/2' }
  ];

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
              <h1 className="text-2xl font-bold text-gray-900">Network Request Monitor</h1>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                isMonitoring ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {isMonitoring ? 'Monitoring Active' : 'Ready to Monitor'}
              </span>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <div className="flex-1 min-w-64">
              <input
                type="text"
                placeholder="Enter URL (e.g., api.example.com/data or https://httpbin.org/get)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleMakeRequest()}
              />
            </div>
            <button
              onClick={handleMakeRequest}
              disabled={!targetUrl.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Globe className="h-4 w-4" />
              <span>Make Request</span>
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

          {/* Quick Test Buttons */}
          <div className="flex flex-wrap items-center gap-2 mb-4 p-4 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700 mr-2">Quick Tests:</span>
            {testRequests.map((test, index) => (
              <button
                key={index}
                onClick={() => makeActualRequest(test.url)}
                className="px-3 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-100"
              >
                {test.name}
              </button>
            ))}
          </div>

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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Request List */}
          <div className="lg:col-span-2">
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
                      <p className="text-sm">Enter a URL and click "Make Request" or try the Quick Tests</p>
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
                              {request.url}
                            </span>
                          </div>
                          <div className="flex items-center space-x-3 text-sm text-gray-500">
                            <span>{request.type}</span>
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

          {/* Request Details */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                  <Eye className="h-5 w-5" />
                  <span>Request Details</span>
                </h2>
              </div>
              <div className="h-96 overflow-y-auto p-4">
                {selectedRequest ? (
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">General</h3>
                      <div className="space-y-1 text-sm">
                        <div><strong>URL:</strong> <span className="break-all">{selectedRequest.url}</span></div>
                        <div><strong>Method:</strong> {selectedRequest.method}</div>
                        <div><strong>Status:</strong> {selectedRequest.status} {selectedRequest.statusText}</div>
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
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <Eye className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                      <p>Select a request to view details</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-6 bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Session Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;