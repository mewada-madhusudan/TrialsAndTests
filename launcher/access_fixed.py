import asyncio
import re
from datetime import datetime

import numpy
import pandas as pd
import urllib3
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread, QSize, QTimer
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QMessageBox, QWidget, QStackedWidget,
                             QFrame, QScrollArea, QListWidget, QListWidgetItem, QCheckBox, QComboBox, QProgressDialog,
                             QTextEdit, QTabWidget, QGroupBox)
from requests_ntlm import HttpNtlmAuth
from shareplum import Site

from static import SHAREPOINT_LIST, SITE_URL, SID, FIELDS, split_user,LOB, STATUS, pslv_action_entry, user_main

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FormValidator:
    @staticmethod
    def validate_text(text):
        """Validate text field is not empty and contains valid characters"""
        return bool(text and text.strip() and not re.search('[^]', text))

    @staticmethod
    def validate_app_path(text):
        """Validate text field is not empty and contains an exe path"""
        return True if text.endswith('.exe') else False

    @staticmethod
    def validate_date(date_str):
        """Validate date in DD-MM-YYYY format"""
        try:
            if not date_str:
                return True
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_version(version):
        """Validate version is a valid float"""
        try:
            if not version:
                return True
            float(version)
            return True
        except ValueError:
            return False


class ValidatingLineEdit(QLineEdit):
    def __init__(self, validation_type, required=False, parent=None):
        super().__init__(parent)
        self.validation_type = validation_type
        self.required = required
        self.valid = True
        self.textChanged.connect(self.on_text_changed)

        # Store original stylesheet
        self.default_style = """
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #1976d2;
            }
        """
        self.error_style = """
            QLineEdit {
                border: 1px solid #f44336;
                border-radius: 4px;
                padding: 8px;
                background: #fff5f5;
            }
        """
        self.setStyleSheet(self.default_style)

    def validate(self):
        text = self.text().strip()

        # Check if field is required and empty
        if self.required and not text:
            self.set_invalid()
            return False

        # If field is optional and empty, it's valid
        if not self.required and not text:
            self.set_valid()
            return True

        # Validate based on type
        if self.validation_type == 'text':
            valid = FormValidator.validate_text(text)
        elif self.validation_type == 'date':
            valid = FormValidator.validate_date(text)
        elif self.validation_type == 'version':
            valid = FormValidator.validate_version(text)
        elif self.validation_type == 'app':
            valid = FormValidator.validate_app_path(text)
        else:
            valid = True

        if valid:
            self.set_valid()
        else:
            self.set_invalid()

        return valid

    def set_valid(self):
        self.valid = True
        self.setStyleSheet(self.default_style)

    def set_invalid(self):
        self.valid = False
        self.setStyleSheet(self.error_style)

    def on_text_changed(self):
        """Reset validation state when user starts typing"""
        if not self.valid:
            self.setStyleSheet(self.default_style)


class AppTileWidget(QFrame):
    def __init__(self, name, description, parent=None):
        super().__init__(parent)
        self.setObjectName("appTile")
        self.is_selected = False
        self.setFixedSize(300, 100)
        self.setup_ui(name, description)

    def setup_ui(self, name, description):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        # App name with icon in horizontal layout
        name_layout = QHBoxLayout()

        name_label = QLabel(name)
        name_label.setProperty("appName", True)
        name_label.setWordWrap(True)
        name_layout.addWidget(name_label)
        name_layout.addStretch()

        # Description
        desc_label = QLabel(description)
        desc_label.setProperty("appDescription", True)
        desc_label.setWordWrap(True)

        layout.addLayout(name_layout)
        layout.addWidget(desc_label)
        layout.addStretch()

    def set_selected(self, selected):
        self.is_selected = selected
        if selected:
            self.setProperty("selected", True)
        else:
            self.setProperty("selected", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def sizeHint(self):
        return QSize(300, 100)


class VerificationWorker(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, user_ids):
        super().__init__()
        self.user_ids = user_ids

    async def verify_user_id(self, user_id):
        """
        Verify a single user ID using the API
        Replace the URL and any necessary headers/auth for your API
        """
        try:
            # Replace with your actual API endpoint
            response = numpy.get_phonebook_data(user_id)
            return user_id, response['standardID'] == user_id
        except:
            return user_id, False

    async def verify_multiple_ids(self):
        """
        Verify multiple user IDs concurrently
        """
        tasks = [self.verify_user_id(uid) for uid in self.user_ids]
        results = await asyncio.gather(*tasks)
        return {uid: is_valid for uid, is_valid in results}

    def run(self):
        """
        Run the verification process
        """
        async def run_async():
            results = await self.verify_multiple_ids()
            self.finished.emit(results)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async())
        loop.close()


def is_valid(text):
    return bool(text.strip())


class AccessControlDialog(QDialog):
    def __init__(self, username, lob, parent=None):
        super().__init__(parent)
        self.username = username
        self.lob = lob
        self.existing_users_list = None
        self.progress_dialog = None
        self.workers = []  # Keep track of running threads
        self.setWindowTitle("Access Management")
        self.setMinimumSize(900, 600)
        self.refresh_data()
        self.setup_ui()

    def show_loading_dialog(self):
        """Show task-based progress dialog with better UX"""
        self.progress_dialog = QProgressDialog("Processing your request...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle("Please Wait")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)  # Show immediately
        self.progress_dialog.setStyleSheet("""
            QProgressDialog {
                background-color: white;
                min-width: 350px;
                min-height: 120px;
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
                min-height: 20px;
            }
            QProgressBar::chunk {
                background-color: #1976d2;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

    def refresh_data(self):
        """Fetch fresh data from the API"""
        try:
            # Create sharepoint session for sharepoint list
            cred = HttpNtlmAuth(SID, "")
            site = Site(SITE_URL, auth=cred, verify_ssl=True)

            # Fetch data from SharePoint list
            sp_list = site.List(SHAREPOINT_LIST)
            sp_data = sp_list.GetListItems(view_name=None)
            df_all = pd.DataFrame(sp_data)
            df_all.fillna('', inplace=True)
            self.df = df_all[df_all['LOB'].isin(self.lob)]
            self.df['Description'] = self.df['Description'].str.slice(0, 50)
            self.df.reset_index(inplace=True, drop=True)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Connection Error",
                                f"Unable to connect to SharePoint: {str(e)}. Please check your network connection and try again.",
                                QMessageBox.StandardButton.Ok)
            return False

    def save_application(self):
        # Validate all fields
        all_valid = True
        for field_name, input_widget in self.add_app_fields.items():
            if isinstance(input_widget, ValidatingLineEdit):
                if not input_widget.validate():
                    all_valid = False

        if not all_valid:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please check the form for errors:\n\n" +
                "• Required fields must not be empty\n" +
                "• Dates must be in YYYY-MM-DD format\n" +
                "• Executable Path must end with .exe\n" +
                "• Version must be a valid number",
                QMessageBox.StandardButton.Ok
            )
            return

        is_update_mode = self.update_mode_checkbox.isChecked()

        # Collect form data
        new_data = {}
        for field, widget in self.add_app_fields.items():
            if isinstance(widget, ValidatingLineEdit):  # QLineEdit for text fields
                new_data[field] = widget.text()
            elif isinstance(widget, QComboBox):  # QComboBox for dropdown fields
                new_data[field] = widget.currentText()
            else:
                raise TypeError(f"Unsupported widget type for field '{field}'")

        if not new_data["Solution_Name"]:
            QMessageBox.warning(self, "Required Field",
                                "Application Name is required.",
                                QMessageBox.StandardButton.Ok)
            return

        try:
            if is_update_mode:
                # Update existing application
                pslv_action_entry([{'SID':user_main, 'action':f'Updated details for app {new_data["Solution_Name"]}'}])
                app_name = self.app_select_combo.currentText()
                idx = self.df[self.df['Solution_Name'] == app_name].index[0]
                for field, value in new_data.items():
                    if field in self.df.columns:
                        self.df.at[idx, field] = value
                data_dictionary = self.df.iloc[idx].to_dict()
                self.update_sharepoint_db(dictionary_as_list=[data_dictionary], operation='Update')
                success_msg = f"Application '{new_data['Solution_Name']}' has been updated successfully!"
            else:
                # Add new application
                pslv_action_entry([{'SID':user_main, 'action':f'New App Registration: {new_data["Solution_Name"]}'}])
                self.df = pd.concat([self.df, pd.DataFrame([new_data])], ignore_index=True)
                self.update_sharepoint_db(dictionary_as_list=[new_data], operation='New')
                success_msg = f"Application '{new_data['Solution_Name']}' has been registered successfully!"
            
            # Show loading dialog with task-based progress
            self.show_loading_dialog()
            # Schedule data refresh after a short delay
            QTimer.singleShot(500, lambda: self.handle_refresh(success_msg))
            
        except Exception as e:
            error_msg = f"Registration failed for '{new_data['Solution_Name']}'.\n\nError details: {str(e)}\n\nPlease try again or contact support if the issue persists."
            QMessageBox.critical(self, "Registration Failed", error_msg, QMessageBox.StandardButton.Ok)

    def handle_refresh(self, success_msg):
        """Handle the data refresh and UI updates"""
        if self.refresh_data():
            # Update UI components
            self.update_app_list()
            self.clear_form()
            # Close the progress dialog
            if self.progress_dialog:
                self.progress_dialog.close()

            # Show success message
            self.show_success_message(success_msg)
        else:
            if self.progress_dialog:
                self.progress_dialog.close()
            QMessageBox.warning(self, "Refresh Failed",
                                "Operation completed but failed to refresh data. Please restart the application.",
                                QMessageBox.StandardButton.Ok)