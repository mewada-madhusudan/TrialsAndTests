from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QProgressDialog

class AccessControlDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... rest of your init code ...
        
        # Add a progress dialog as a class member
        self.progress_dialog = None
        
    def show_loading_dialog(self):
        """Show an indefinite progress dialog"""
        self.progress_dialog = QProgressDialog("Refreshing data...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Please Wait")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None)  # Remove cancel button
        self.progress_dialog.setMinimumDuration(0)  # Show immediately
        self.progress_dialog.setStyleSheet("""
            QProgressDialog {
                background-color: white;
                min-width: 300px;
            }
            QLabel {
                color: #333;
                font-size: 13px;
                padding: 10px;
            }
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                text-align: center;
                padding: 1px;
            }
            QProgressBar::chunk {
                background-color: #1976d2;
                border-radius: 3px;
            }
        """)
        
    def refresh_data(self):
        """Fetch fresh data from the API"""
        # This should be implemented to match your API call
        # Example implementation:
        try:
            response = your_api_client.get_applications()  # Replace with your actual API call
            self.df = pd.DataFrame(response)
            return True
        except Exception as e:
            print(f"Error refreshing data: {e}")
            return False

    def save_application(self):
        is_update_mode = self.update_mode_checkbox.isChecked()
        
        # Collect form data
        new_data = {field: widget.text() for field, widget in self.add_app_fields.items()}
        
        if not new_data["application_name"]:
            QMessageBox.warning(self, "Required Field",
                              "Application Name is required.",
                              QMessageBox.StandardButton.Ok)
            return

        try:
            if is_update_mode:
                # Update existing application via API
                app_name = self.app_select_combo.currentText()
                response = your_api_client.update_application(app_name, new_data)  # Replace with your API call
            else:
                # Add new application via API
                response = your_api_client.create_application(new_data)  # Replace with your API call
            
            # Show loading dialog
            self.show_loading_dialog()
            
            # Schedule data refresh after a short delay
            QTimer.singleShot(500, self.handle_refresh)
            
        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to {'update' if is_update_mode else 'add'} application: {str(e)}",
                               QMessageBox.StandardButton.Ok)
            if self.progress_dialog:
                self.progress_dialog.close()

    def handle_refresh(self):
        """Handle the data refresh and UI updates"""
        if self.refresh_data():
            # Update UI components
            self.update_app_list()
            self.clear_form()
            
            # Show success message
            action = "updated" if self.update_mode_checkbox.isChecked() else "added"
            self.show_success_message(f"Application has been {action} successfully!")
        else:
            QMessageBox.warning(self, "Refresh Failed",
                              "Failed to refresh data. Please try again.",
                              QMessageBox.StandardButton.Ok)
        
        # Close the progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()

    def update_app_list(self):
        """Update the application list with fresh data"""
        self.app_list.clear()
        if hasattr(self, 'df') and not self.df.empty:
            for _, row in self.df.iterrows():
                item = QListWidgetItem(self.app_list)
                tile_widget = AppTileWidget(row['application_name'], row['description'])
                item.setSizeHint(tile_widget.sizeHint())
                self.app_list.setItemWidget(item, tile_widget)
                item.setData(Qt.ItemDataRole.UserRole, row['application_name'])
