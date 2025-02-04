from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                           QLineEdit, QTextEdit, QLabel, QApplication)
from PyQt5.QtCore import QThread, pyqtSignal
import requests
import sys
import json

class SharePointWorker(QThread):
    finished = pyqtSignal(str, dict)  # Signal to emit results
    error = pyqtSignal(str)  # Signal for errors

    def __init__(self, site_url, username, password, operation, list_name, item_data=None, item_id=None):
        super().__init__()
        self.site_url = site_url
        self.username = username
        self.password = password
        self.operation = operation
        self.list_name = list_name
        self.item_data = item_data
        self.item_id = item_id
        self.session = requests.Session()
        self.session.auth = (username, password)

    def _get_digest_value(self):
        """Get SharePoint form digest value."""
        try:
            url = f"{self.site_url}/_api/contextinfo"
            response = self.session.post(
                url,
                headers={
                    "Accept": "application/json;odata=verbose",
                    "Content-Type": "application/json;odata=verbose"
                }
            )
            return response.json()['d']['GetContextWebInformation']['FormDigestValue']
        except Exception as e:
            self.error.emit(f"Error getting form digest: {str(e)}")
            return None

    def run(self):
        try:
            if self.operation == 'get':
                self._get_items()
            elif self.operation == 'add':
                self._add_item()
            elif self.operation == 'update':
                self._update_item()
        except Exception as e:
            self.error.emit(f"Operation failed: {str(e)}")

    def _get_items(self):
        """Fetch items from SharePoint list."""
        url = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items"
        response = self.session.get(
            url,
            headers={"Accept": "application/json;odata=verbose"}
        )
        result = response.json()['d']['results']
        self.finished.emit('get', {'items': result})

    def _add_item(self):
        """Add new item to SharePoint list."""
        url = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items"
        digest = self._get_digest_value()
        if not digest:
            return

        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
            "X-RequestDigest": digest
        }
        
        data = {
            "__metadata": {"type": f"SP.Data.{self.list_name}ListItem"},
            **self.item_data
        }
        
        response = self.session.post(url, headers=headers, json=data)
        result = response.json()['d']
        self.finished.emit('add', {'item': result})

    def _update_item(self):
        """Update existing item in SharePoint list."""
        url = f"{self.site_url}/_api/web/lists/getbytitle('{self.list_name}')/items({self.item_id})"
        digest = self._get_digest_value()
        if not digest:
            return

        headers = {
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose",
            "X-RequestDigest": digest,
            "X-HTTP-Method": "MERGE",
            "IF-MATCH": "*"
        }
        
        data = {
            "__metadata": {"type": f"SP.Data.{self.list_name}ListItem"},
            **self.item_data
        }
        
        response = self.session.post(url, headers=headers, json=data)
        success = response.status_code == 204
        self.finished.emit('update', {'success': success})

class SharePointUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.workers = []  # Keep track of worker threads

    def init_ui(self):
        self.setWindowTitle('SharePoint Operations')
        self.setGeometry(100, 100, 600, 400)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add input fields
        self.site_url = QLineEdit()
        self.site_url.setPlaceholderText('SharePoint Site URL')
        layout.addWidget(QLabel('Site URL:'))
        layout.addWidget(self.site_url)

        self.username = QLineEdit()
        self.username.setPlaceholderText('Username')
        layout.addWidget(QLabel('Username:'))
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel('Password:'))
        layout.addWidget(self.password)

        self.list_name = QLineEdit()
        self.list_name.setPlaceholderText('List Name')
        layout.addWidget(QLabel('List Name:'))
        layout.addWidget(self.list_name)

        # Add operation buttons
        self.get_button = QPushButton('Get Items')
        self.get_button.clicked.connect(self.get_items)
        layout.addWidget(self.get_button)

        self.add_button = QPushButton('Add Item')
        self.add_button.clicked.connect(self.add_item)
        layout.addWidget(self.add_button)

        self.update_button = QPushButton('Update Item')
        self.update_button.clicked.connect(self.update_item)
        layout.addWidget(self.update_button)

        # Add results display
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        layout.addWidget(QLabel('Results:'))
        layout.addWidget(self.results)

    def get_items(self):
        worker = SharePointWorker(
            self.site_url.text(),
            self.username.text(),
            self.password.text(),
            'get',
            self.list_name.text()
        )
        worker.finished.connect(self.handle_result)
        worker.error.connect(self.handle_error)
        self.workers.append(worker)  # Prevent garbage collection
        worker.start()

    def add_item(self):
        # Example item data - modify as needed
        item_data = {
            'Title': 'New Item',
            'Description': 'Added via PyQt'
        }
        
        worker = SharePointWorker(
            self.site_url.text(),
            self.username.text(),
            self.password.text(),
            'add',
            self.list_name.text(),
            item_data=item_data
        )
        worker.finished.connect(self.handle_result)
        worker.error.connect(self.handle_error)
        self.workers.append(worker)
        worker.start()

    def update_item(self):
        # Example update - modify as needed
        item_data = {
            'Title': 'Updated Item',
            'Description': 'Updated via PyQt'
        }
        
        worker = SharePointWorker(
            self.site_url.text(),
            self.username.text(),
            self.password.text(),
            'update',
            self.list_name.text(),
            item_data=item_data,
            item_id=1  # Replace with actual item ID
        )
        worker.finished.connect(self.handle_result)
        worker.error.connect(self.handle_error)
        self.workers.append(worker)
        worker.start()

    def handle_result(self, operation, result):
        self.results.append(f"\nOperation: {operation}")
        self.results.append(f"Result: {json.dumps(result, indent=2)}")
        
        # Clean up finished worker
        for worker in self.workers[:]:
            if worker.isFinished():
                self.workers.remove(worker)

    def handle_error(self, error_message):
        self.results.append(f"\nError: {error_message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SharePointUI()
    window.show()
    sys.exit(app.exec_())
