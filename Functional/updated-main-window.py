from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, db_path, user_sid, functional_username=None, functional_password=None):
        super().__init__()
        self.db_path = db_path
        self.user_sid = user_sid
        self.functional_username = functional_username
        self.functional_password = functional_password
        
        # Set up UI components (not shown for brevity)
        self.setup_ui()
        
        # Set up status bar for sync information
        self.sync_status_label = self.statusBar().addPermanentWidget(QLabel("Checking sync status..."))
        
        # Set up background refresh thread
        self.refresh_thread = RefreshThread(
            db_path=self.db_path,
            user_sid=self.user_sid,
            functional_username=self.functional_username,
            functional_password=self.functional_password,
            refresh_interval=30  # Check every 30 seconds
        )
        self.refresh_thread.apps_changed.connect(self.handle_apps_changed)
        self.refresh_thread.sync_status_changed.connect(self.handle_sync_status_changed)
        self.refresh_thread.start()

    def handle_apps_changed(self, new_apps):
        """Handle applications list changes from the refresh thread"""
        self.clear_application_grid()
        
        # Reload the applications grid with new data
        for i, app_info in enumerate(new_apps):
            # Unpack app_info tuple based on LauncherDB's column order
            app_id, name, exe_path, description, lob, version, last_updated = app_info
            
            tile = ApplicationTile(
                app_name=name, 
                app_description=description, 
                shared_drive_path=exe_path,
                app_version=version,
                db_path=self.db_path,
                functional_username=self.functional_username,
                functional_password=self.functional_password
            )
            self.app_grid.addWidget(tile, i // 3, i % 3)
        
        self.adjust_tile_sizes()
        
        # Optional notification - might be too frequent if database changes often
        # self.statusBar().showMessage("Applications updated", 3000)

    def handle_sync_status_changed(self, is_synced, local_time, source_time):
        """Update the sync status in the UI"""
        if is_synced:
            self.sync_status_label.setText(f"Synced: {local_time}")
            self.sync_status_label.setStyleSheet("color: green;")
        else:
            self.sync_status_label.setText(f"Out of sync - Local: {local_time}, Source: {source_time}")
            self.sync_status_label.setStyleSheet("color: orange;")

    def force_sync_database(self):
        """Force sync the database - can be connected to a button"""
        from launcher_db import LauncherDB
        
        try:
            db = LauncherDB(
                db_path=self.db_path,
                functional_username=self.functional_username,
                functional_password=self.functional_password
            )
            
            success = db.force_sync()
            if success:
                QMessageBox.information(self, "Sync Complete", "Database has been synchronized successfully.")
                # Refresh the applications display
                with db.get_connection(read_only=True) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT a.* FROM applications a
                        JOIN user_access ua ON a.id = ua.app_id
                        WHERE ua.user_sid = ?
                    """, (self.user_sid,))
                    new_apps = cursor.fetchall()
                    self.handle_apps_changed(new_apps)
            else:
                QMessageBox.warning(self, "Sync Failed", "Could not synchronize with the source database.")
        except Exception as e:
            QMessageBox.critical(self, "Sync Error", f"Error during synchronization: {str(e)}")

    def closeEvent(self, event):
        """Stop the refresh thread when closing the application"""
        self.refresh_thread.stop()
        self.refresh_thread.wait()  # Wait for the thread to finish
        event.accept()
