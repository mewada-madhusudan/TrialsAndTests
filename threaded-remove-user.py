from PyQt6.QtCore import QThread, pyqtSignal
from functools import partial

class RemoveUserWorker(QThread):
    error_occurred = pyqtSignal(str)
    
    def __init__(self, user, app_name, api_client):
        super().__init__()
        self.user = user
        self.app_name = app_name
        self.api_client = api_client
        
    def run(self):
        try:
            # Make API call to remove user
            success = self.api_client.remove_user(self.app_name, self.user)
            if not success:
                self.error_occurred.emit("Failed to remove user from application")
        except Exception as e:
            self.error_occurred.emit(str(e))

class AccessControlDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... rest of your init code ...
        self.active_threads = []  # Keep track of running threads
    
    def remove_user(self, user, app_name):
        """Remove user from application without confirmation dialog"""
        # Update local DataFrame first
        app_idx = self.df[self.df['application_name'] == app_name].index[0]
        current_sids = self.df.at[app_idx, 'sids'].split(',')
        
        if user in current_sids:
            current_sids.remove(user)
            self.df.at[app_idx, 'sids'] = ','.join(current_sids)
            
            # Update UI immediately
            self.show_application_users(self.app_list.currentItem())
            
            # Start worker thread for API call
            worker = RemoveUserWorker(user, app_name, your_api_client)  # Replace with your API client
            worker.error_occurred.connect(partial(self.handle_remove_user_error, user, app_name))
            worker.finished.connect(worker.deleteLater)
            worker.finished.connect(lambda: self.active_threads.remove(worker))
            
            self.active_threads.append(worker)
            worker.start()

    def handle_remove_user_error(self, user, app_name, error_message):
        """Handle errors from the remove user API call"""
        # Revert local changes
        app_idx = self.df[self.df['application_name'] == app_name].index[0]
        current_sids = self.df.at[app_idx, 'sids'].split(',')
        if user not in current_sids:
            current_sids.append(user)
            self.df.at[app_idx, 'sids'] = ','.join(current_sids)
            self.show_application_users(self.app_list.currentItem())
        
        # Show error message
        QMessageBox.critical(self, "Error",
                           f"Failed to remove user: {error_message}",
                           QMessageBox.StandardButton.Ok)

    def closeEvent(self, event):
        """Handle cleanup when closing the dialog"""
        # Wait for any active threads to finish
        for thread in self.active_threads:
            thread.wait()
        super().closeEvent(event)

    def create_sid_tag(self, sid):
        """Create a SID tag with remove button"""
        tag = QFrame()
        tag.setObjectName("sidTag")
        layout = QHBoxLayout(tag)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        label = QLabel(sid)
        remove_btn = QPushButton("Remove")
        remove_btn.setObjectName("removeBtn")
        remove_btn.setFixedWidth(70)

        layout.addWidget(label)
        layout.addWidget(remove_btn)
        layout.addStretch()

        # Connect remove button directly to remove_user without confirmation
        remove_btn.clicked.connect(
            lambda: self.remove_user(sid.strip(), self.app_list.currentItem().data(Qt.ItemDataRole.UserRole))
        )

        return tag, remove_btn
