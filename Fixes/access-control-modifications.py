# Add these imports at the top of your file
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QDateEdit, QComboBox, QMessageBox
from PyQt6.QtCore import QDate

# Modify the setup_right_panel method to include the new fields
def setup_right_panel(self):
    # Add Application/Update Panel with scrolling
    add_update_widget = QWidget()
    main_layout = QHBoxLayout(add_update_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Create a scroll area for the form
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    # Create container widget for the form
    form_container = QWidget()
    add_layout = QVBoxLayout(form_container)
    add_layout.setContentsMargins(30, 20, 30, 20)
    add_layout.setSpacing(20)

    # Title section
    title = QLabel("Application Details")
    title.setProperty("heading", True)
    add_layout.addWidget(title)

    description = QLabel("Enter the application details below.")
    description.setProperty("subheading", True)
    add_layout.addWidget(description)

    # Application selection for update mode
    select_layout = QHBoxLayout()
    self.update_mode_checkbox = QCheckBox("Update Existing Application")
    self.app_select_combo = QComboBox()
    self.app_select_combo.setMinimumWidth(200)
    self.app_select_combo.setEnabled(False)
    
    select_layout.addWidget(self.update_mode_checkbox)
    select_layout.addWidget(self.app_select_combo)
    select_layout.addStretch()
    add_layout.addLayout(select_layout)

    # Form fields
    # Standard text fields
    text_fields = [
        ("application_name", "Application Name", "Enter the name of the application"),
        ("description", "Application Description", "Enter a brief description"),
        ("exe_path", "Executable Path", "Enter the full path to the executable"),
        ("lob", "Line of Business", "Enter the business unit or department"),
        ("version", "Version", "Enter application version"),
        ("owner", "Owner", "Enter application owner"),
        ("support_contact", "Support Contact", "Enter support contact information"),
        ("deployment_date", "Deployment Date", "Enter deployment date"),
        ("last_update", "Last Update Date", "Enter last update date"),
        ("environment", "Environment", "Enter deployment environment"),
        ("dependencies", "Dependencies", "Enter application dependencies"),
        ("backup_location", "Backup Location", "Enter backup location"),
        ("registration_id", "Registration ID", "Enter registration ID once in PROD"),
        ("sids", "Security IDs", "Enter comma-separated security IDs")
    ]

    self.add_app_fields = {}
    for field_name, label_text, placeholder in text_fields:
        field_layout = QVBoxLayout()
        field_layout.setSpacing(6)

        label = QLabel(label_text)
        label.setProperty("fieldLabel", True)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setProperty("formInput", True)

        self.add_app_fields[field_name] = line_edit
        field_layout.addWidget(label)
        field_layout.addWidget(line_edit)

        add_layout.addLayout(field_layout)

    # Add status combobox
    status_layout = QVBoxLayout()
    status_layout.setSpacing(6)
    status_label = QLabel("Status")
    status_label.setProperty("fieldLabel", True)
    self.status_combo = QComboBox()
    self.status_combo.addItems(["UAT", "PROD"])
    self.status_combo.setProperty("formInput", True)
    self.add_app_fields["status"] = self.status_combo  # Store in the same dictionary
    
    status_layout.addWidget(status_label)
    status_layout.addWidget(self.status_combo)
    add_layout.addLayout(status_layout)
    
    # Add validity date field
    validity_layout = QVBoxLayout()
    validity_layout.setSpacing(6)
    validity_label = QLabel("Validity Period")
    validity_label.setProperty("fieldLabel", True)
    self.validity_date = QDateEdit()
    self.validity_date.setCalendarPopup(True)
    self.validity_date.setDate(QDate.currentDate().addYears(1))  # Default 1 year validity
    self.validity_date.setProperty("formInput", True)
    self.add_app_fields["validity_period"] = self.validity_date  # Store in the same dictionary
    
    validity_layout.addWidget(validity_label)
    validity_layout.addWidget(self.validity_date)
    add_layout.addLayout(validity_layout)

    # Button section
    button_layout = QHBoxLayout()
    self.save_btn = QPushButton("Save Application")
    self.save_btn.setObjectName("actionButton")
    self.save_btn.setFixedWidth(140)
    
    self.clear_btn = QPushButton("Clear Form")
    self.clear_btn.setObjectName("secondaryButton")
    self.clear_btn.setFixedWidth(140)
    
    button_layout.addStretch()
    button_layout.addWidget(self.clear_btn)
    button_layout.addWidget(self.save_btn)

    add_layout.addLayout(button_layout)
    add_layout.addStretch()

    # Set the form container as the scroll area widget
    scroll_area.setWidget(form_container)
    main_layout.addWidget(scroll_area)

    # Connect signals
    self.update_mode_checkbox.toggled.connect(self.toggle_update_mode)
    self.app_select_combo.currentTextChanged.connect(self.load_application_data)
    self.save_btn.clicked.connect(self.save_application)
    self.clear_btn.clicked.connect(self.clear_form)
    self.status_combo.currentTextChanged.connect(self.handle_status_change)

    self.right_stack.addWidget(add_update_widget)
    
    # Continue with the rest of your existing setup_right_panel code for manage access...

# Initialize the DataFrame with new columns in the __init__ method
def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Access Control")
    self.setMinimumSize(900, 600)
    
    # Update the DataFrame initialization to include the new fields
    self.df = pd.DataFrame({
        'application_name': ['App1', 'App2', 'App3'],
        'description': ['First application description', 'Second application description',
                        'Third application description'],
        'exe_path': ['/path1', '/path2', '/path3'],
        'lob': ['LOB1', 'LOB2', 'LOB1'],
        'sids': ['SID1,SID2', 'SID3', 'SID4,SID5,SID6'],
        'status': ['UAT', 'PROD', 'UAT'],
        'validity_period': [(datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
                           (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
                           (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')],
        'registration_id': ['', 'REG12345', ''],
        'prod_transition_date': ['', datetime.now().strftime('%Y-%m-%d'), '']
    })
    
    # Track the current user's role (for demo purposes)
    self.is_super_admin = False  # Toggle this for testing
    
    self.setup_ui()

# Add new methods to handle the business logic
def handle_status_change(self, new_status):
    """Handle logic when status changes to PROD"""
    if new_status == "PROD":
        # Show warning about registration ID requirement
        QMessageBox.information(
            self, 
            "Status Change", 
            "Changing status to PROD requires Registration ID to be added within 30 days.\n"
            "Validity period will be locked once saved in PROD status.",
            QMessageBox.StandardButton.Ok
        )

def load_application_data(self, app_name):
    """Load application data with special handling for the new fields"""
    if not app_name or not self.update_mode_checkbox.isChecked():
        return
    
    app_data = self.df[self.df['application_name'] == app_name].iloc[0]
    
    # Check if editing is restricted for this application
    if self.is_editing_restricted(app_data) and not self.is_super_admin:
        QMessageBox.warning(
            self,
            "Restricted Access",
            "This application has been in PROD status for over 30 days without a Registration ID.\n"
            "Only super admins can edit it now.",
            QMessageBox.StandardButton.Ok
        )
        self.clear_form()
        self.update_mode_checkbox.setChecked(False)
        return
    
    # Load standard text fields
    for field_name, input_widget in self.add_app_fields.items():
        if field_name in app_data and field_name not in ["status", "validity_period"]:
            input_widget.setText(str(app_data[field_name]))
    
    # Handle status combobox
    if 'status' in app_data:
        self.status_combo.setCurrentText(app_data['status'])
    
    # Handle validity date
    if 'validity_period' in app_data and app_data['validity_period']:
        try:
            date_obj = datetime.strptime(app_data['validity_period'], '%Y-%m-%d').date()
            self.validity_date.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        except (ValueError, TypeError):
            # Handle invalid date format
            self.validity_date.setDate(QDate.currentDate().addYears(1))
    
    # Lock validity date if in PROD
    self.validity_date.setEnabled(app_data['status'] != "PROD")

def is_editing_restricted(self, app_data):
    """Check if editing should be restricted based on the business rules"""
    # If not in PROD status, no restrictions
    if app_data['status'] != "PROD":
        return False
    
    # If it has a registration ID, no restrictions
    if app_data['registration_id']:
        return False
    
    # Check if it's been more than 30 days since PROD transition
    if app_data['prod_transition_date']:
        try:
            transition_date = datetime.strptime(app_data['prod_transition_date'], '%Y-%m-%d')
            days_since_transition = (datetime.now() - transition_date).days
            return days_since_transition > 30
        except (ValueError, TypeError):
            return False
    
    return False

def save_application(self):
    """Save application with the new business logic"""
    is_update_mode = self.update_mode_checkbox.isChecked()
    
    # Collect form data
    new_data = {}
    for field, widget in self.add_app_fields.items():
        if field == "status":
            new_data[field] = widget.currentText()
        elif field == "validity_period":
            new_data[field] = widget.date().toString("yyyy-MM-dd")
        else:
            new_data[field] = widget.text()
    
    if not new_data["application_name"]:
        QMessageBox.warning(self, "Required Field",
                          "Application Name is required.",
                          QMessageBox.StandardButton.Ok)
        return
    
    # Check if transitioning to PROD status
    is_prod_transition = False
    
    if is_update_mode:
        # Update existing application
        app_name = self.app_select_combo.currentText()
        idx = self.df[self.df['application_name'] == app_name].index[0]
        
        # Check if status is changing from UAT to PROD
        current_status = self.df.at[idx, 'status']
        new_status = new_data["status"]
        
        if current_status != "PROD" and new_status == "PROD":
            is_prod_transition = True
            new_data["prod_transition_date"] = datetime.now().strftime('%Y-%m-%d')
        
        # Update the dataframe
        for field, value in new_data.items():
            if field in self.df.columns:
                self.df.at[idx, field] = value
    else:
        # Add new application
        if new_data["status"] == "PROD":
            new_data["prod_transition_date"] = datetime.now().strftime('%Y-%m-%d')
        else:
            new_data["prod_transition_date"] = ""
            
        self.df = pd.concat([self.df, pd.DataFrame([new_data])], ignore_index=True)

    # Update UI
    self.update_app_list()
    self.clear_form()
    
    # Show appropriate success message
    if is_prod_transition:
        self.show_success_message(
            "Application has been moved to PROD status.\n"
            "Remember to add a Registration ID within 30 days to maintain edit access."
        )
    else:
        action = "updated" if is_update_mode else "added"
        self.show_success_message(f"Application has been {action} successfully!")

def clear_form(self):
    """Clear form with special handling for new field types"""
    for field, widget in self.add_app_fields.items():
        if field == "status":
            widget.setCurrentText("UAT")  # Default to UAT
        elif field == "validity_period":
            widget.setDate(QDate.currentDate().addYears(1))  # Reset to default 1 year from now
        else:
            widget.clear()
    
    # Reset the validity date to be editable
    self.validity_date.setEnabled(True)
    self.update_mode_checkbox.setChecked(False)

# Add these styles to your apply_styles method
def apply_styles(self):
    # Keep your existing styles
    additional_styles = """
        QDateEdit {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            min-height: 36px;
        }
        QDateEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 20px;
            border-left: 1px solid #e0e0e0;
        }
        QDateEdit:disabled {
            background-color: #f5f5f5;
            color: #999;
        }
        QLabel[warning="true"] {
            color: #f44336;
            font-weight: bold;
        }
        QComboBox {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            min-height: 36px;
            background: white;
        }
        QComboBox:disabled {
            background: #f5f5f5;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 20px;
            border-left: 1px solid #e0e0e0;
        }
    """
    # Add the additional styles to your existing stylesheet
    current_style = self.styleSheet()
    self.setStyleSheet(current_style + additional_styles)

# Add a toggle method for testing super admin role
def toggle_super_admin(self):
    self.is_super_admin = not self.is_super_admin
    status = "enabled" if self.is_super_admin else "disabled"
    QMessageBox.information(
        self,
        "Super Admin Mode",
        f"Super admin mode {status}",
        QMessageBox.StandardButton.Ok
    )
