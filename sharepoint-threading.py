import requests
import threading
from queue import Queue
from typing import Dict, List, Any
import json
from datetime import datetime
import time

class SharePointAPI:
    def __init__(self, site_url: str, username: str, password: str):
        self.site_url = site_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.request_queue = Queue()
        self.response_queue = Queue()
        self.worker_threads: List[threading.Thread] = []
        self.running = True

    def _get_digest_value(self) -> str:
        """Get SharePoint form digest value for POST requests."""
        url = f"{self.site_url}/_api/contextinfo"
        response = self.session.post(
            url,
            headers={
                "Accept": "application/json;odata=verbose",
                "Content-Type": "application/json;odata=verbose"
            }
        )
        return response.json()['d']['GetContextWebInformation']['FormDigestValue']

    def _worker(self):
        """Worker thread to process SharePoint requests."""
        while self.running:
            try:
                if not self.request_queue.empty():
                    task = self.request_queue.get()
                    if task is None:
                        break

                    operation, params = task
                    if operation == 'get':
                        result = self._get_items(**params)
                    elif operation == 'add':
                        result = self._add_item(**params)
                    elif operation == 'update':
                        result = self._update_item(**params)
                    
                    self.response_queue.put((operation, result))
                    self.request_queue.task_done()
                else:
                    time.sleep(0.1)  # Prevent CPU spinning
            except Exception as e:
                self.response_queue.put(('error', str(e)))
                self.request_queue.task_done()

    def _get_items(self, list_name: str) -> List[Dict]:
        """Fetch items from SharePoint list."""
        url = f"{self.site_url}/_api/web/lists/getbytitle('{list_name}')/items"
        response = self.session.get(
            url,
            headers={"Accept": "application/json;odata=verbose"}
        )
        return response.json()['d']['results']

    def _add_item(self, list_name: str, item_data: Dict) -> Dict:
        """Add new item to SharePoint list."""
        url = f"{self.site_url}/_api/web/lists/getbytitle('{list_name}')/items"
        digest = self._get_digest_value()
        
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
            "X-RequestDigest": digest
        }
        
        data = {
            "__metadata": {"type": f"SP.Data.{list_name}ListItem"},
            **item_data
        }
        
        response = self.session.post(url, headers=headers, json=data)
        return response.json()['d']

    def _update_item(self, list_name: str, item_id: int, item_data: Dict) -> bool:
        """Update existing item in SharePoint list."""
        url = f"{self.site_url}/_api/web/lists/getbytitle('{list_name}')/items({item_id})"
        digest = self._get_digest_value()
        
        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
            "X-RequestDigest": digest,
            "X-HTTP-Method": "MERGE",
            "IF-MATCH": "*"
        }
        
        data = {
            "__metadata": {"type": f"SP.Data.{list_name}ListItem"},
            **item_data
        }
        
        response = self.session.post(url, headers=headers, json=data)
        return response.status_code == 204

    def start_workers(self, num_threads: int = 3):
        """Start worker threads."""
        self.running = True
        for _ in range(num_threads):
            thread = threading.Thread(target=self._worker)
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)

    def stop_workers(self):
        """Stop worker threads."""
        self.running = False
        for _ in self.worker_threads:
            self.request_queue.put(None)
        for thread in self.worker_threads:
            thread.join()
        self.worker_threads.clear()

    def queue_operation(self, operation: str, **params):
        """Queue a SharePoint operation."""
        self.request_queue.put((operation, params))

    def get_results(self) -> List[tuple]:
        """Get results from completed operations."""
        results = []
        while not self.response_queue.empty():
            results.append(self.response_queue.get())
        return results


# Initialize SharePoint API
sharepoint = SharePointAPI(
    site_url="https://your-sharepoint-site.com",
    username="your_username",
    password="your_password"
)

# Start worker threads
sharepoint.start_workers(num_threads=3)

try:
    # Queue multiple operations
    sharepoint.queue_operation('get', list_name='YourList')
    
    sharepoint.queue_operation('add', list_name='YourList', 
                             item_data={'Title': 'New Item', 
                                      'Description': 'Added via threading'})
    
    sharepoint.queue_operation('update', list_name='YourList',
                             item_id=1,
                             item_data={'Title': 'Updated Item'})

    # Wait for operations to complete
    time.sleep(2)  # Give some time for operations to process

    # Get results
    results = sharepoint.get_results()
    for operation, result in results:
        print(f"Operation: {operation}")
        print(f"Result: {result}\n")

finally:
    # Clean up
    sharepoint.stop_workers()
