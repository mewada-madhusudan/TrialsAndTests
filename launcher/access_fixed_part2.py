    def setup_ui(self):
        # Main layout setup
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left panel
        left_panel = self.setup_left_panel()
        main_layout.addWidget(left_panel)

        # Right panel
        self.right_stack = QStackedWidget()
        self.setup_right_panel()
        main_layout.addWidget(self.right_stack)

        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QPushButton {
                border: none;
                padding: 8px 16px;
                color: #666;
                text-align: left;
                font-size: 13px;
                border-radius: 4px;
                margin: 2px 8px;
                font-family: Montserrat, serif;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                color: #1976d2;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                color: #1976d2;
                font-weight: bold;
            }
            QPushButton#actionButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                min-width: 140px;
                min-height: 20px;
                text-align: center;
            }
            QPushButton#actionButton:hover {
                background-color: #1565c0;
            }
            QPushButton#secondaryButton {
                background-color: #f5f5f5;
                color: #666;
                border: 1px solid #e0e0e0;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                min-width: 140px;
                min-height: 20px;
                text-align: center;
            }
            QPushButton#secondaryButton:hover {
                background-color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QFrame#leftPanel {
                background-color: #fafafa;
                border-right: 1px solid #e0e0e0;
            }
            QLabel[heading="true"] {
                font-size: 15px;
                font-weight: bold;
                color: #1976d2;
                padding: 16px;
            }
            QLabel[appheading="true"] {
                font-size: 15px;
                font-weight: bold;
                color: #1976d2;
                padding-bottom: 5px;
            }
            QLabel[subheading="true"] {
                font-size: 14px;
                font-weight: 500;
                color: #666;
                padding-bottom: 5px;
            }
            QLabel[fieldLabel="true"] {
                font-weight: 500;
                margin-bottom: 4px;
            }
        """)

    def setup_left_panel(self):
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_panel.setFixedWidth(220)
        layout = QVBoxLayout(left_panel)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Access Controls")
        title.setProperty("heading", True)
        layout.addWidget(title)

        # Navigation buttons
        self.add_app_btn = QPushButton("⊞ Add Application")
        self.manage_access_btn = QPushButton("⚙ Manage Access")

        self.add_app_btn.setCheckable(True)
        self.manage_access_btn.setCheckable(True)

        layout.addWidget(self.add_app_btn)
        layout.addWidget(self.manage_access_btn)
        layout.addStretch()

        self.add_app_btn.clicked.connect(lambda: self.switch_panel(0))
        self.manage_access_btn.clicked.connect(lambda: self.switch_panel(1))

        return left_panel

    def app_filled_widget(self, fields):
        field_name, label_text, placeholder, options, field_type, validation_type, required = fields
        field_layout = QVBoxLayout()
        field_layout.setSpacing(6)

        label = QLabel(label_text + (" *" if required else ""))
        label.setProperty("fieldLabel", True)
        
        if field_type == "dropdown":
            field = QComboBox()
            field.setPlaceholderText(placeholder)
            if field_name == "LoB":
                options = self.lob
            field.addItems(options)
            field.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        else:
            field = ValidatingLineEdit(validation_type, required)
            field.setPlaceholderText(placeholder)

        self.add_app_fields[field_name] = field
        field_layout.addWidget(label)
        field_layout.addWidget(field)
        return field_layout

    def setup_right_panel(self):
        # Add Application Panel
        add_update_widget = QWidget()
        main_layout = QVBoxLayout(add_update_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header section
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 0, 30, 10)
        header_layout.setSpacing(10)

        title = QLabel("Application Details")
        title.setProperty("appheading", True)
        header_layout.addWidget(title)

        description = QLabel("Enter the application details below. Fields marked with * are required.")
        description.setProperty("subheading", True)
        header_layout.addWidget(description)

        # Update mode checkbox
        select_layout = QHBoxLayout()
        self.update_mode_checkbox = QCheckBox("Update Existing Application")
        self.app_select_combo = QComboBox()
        self.app_select_combo.setMinimumWidth(400)
        self.app_select_combo.setEnabled(False)

        select_layout.addWidget(self.update_mode_checkbox)
        select_layout.addWidget(self.app_select_combo)
        select_layout.addStretch()
        header_layout.addLayout(select_layout)

        main_layout.addWidget(header_widget)

        # Form with grouped sections
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        form_container = QWidget()
        add_layout = QVBoxLayout(form_container)
        add_layout.setContentsMargins(30, 20, 30, 20)
        add_layout.setSpacing(15)

        self.add_app_fields = {}
        
        # Group fields logically as recommended in fixes document
        sections = {
            "Basic Information": ["Solution_Item_Epic_ID", "Solution_Name", "Description", "Version_Number"],
            "Technical Details": ["ApplicationExePath", "TechnologyUsed", "Developer_By"],
            "Business Information": ["Line_of_Business", "AAMI_Lead_ID"],
            "Release Information": ["Release_Date", "Status"]
        }

        for section_name, field_names in sections.items():
            group_box = QGroupBox(section_name)
            group_layout = QVBoxLayout(group_box)
            group_layout.setSpacing(10)
            
            for field in FIELDS:
                field_name = field[0]
                if field_name in field_names:
                    group_layout.addLayout(self.app_filled_widget(field))
            
            add_layout.addWidget(group_box)

        # Buttons with consistent sizing
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

        scroll_area.setWidget(form_container)
        main_layout.addWidget(scroll_area)

        # Connect signals
        self.update_mode_checkbox.toggled.connect(self.toggle_update_mode)
        self.app_select_combo.currentTextChanged.connect(self.load_application_data)
        self.save_btn.clicked.connect(self.save_application)
        self.clear_btn.clicked.connect(self.clear_form)

        # Manage Access Panel (simplified for now)
        manage_widget = QWidget()
        manage_layout = QVBoxLayout(manage_widget)
        manage_layout.setContentsMargins(20, 20, 20, 20)
        
        manage_title = QLabel("User Access Management")
        manage_title.setProperty("appheading", True)
        manage_layout.addWidget(manage_title)
        
        manage_desc = QLabel("Select an application from the left panel to manage user access.")
        manage_desc.setProperty("subheading", True)
        manage_layout.addWidget(manage_desc)
        
        manage_layout.addStretch()

        self.right_stack.addWidget(add_update_widget)
        self.right_stack.addWidget(manage_widget)

    def switch_panel(self, index):
        self.add_app_btn.setChecked(index == 0)
        self.manage_access_btn.setChecked(index == 1)
        self.right_stack.setCurrentIndex(index)

    def toggle_update_mode(self):
        is_update_mode = self.update_mode_checkbox.isChecked()
        self.app_select_combo.setEnabled(is_update_mode)
        
        if hasattr(self, 'add_app_fields') and "Solution_Name" in self.add_app_fields:
            self.add_app_fields["Solution_Name"].setEnabled(not is_update_mode)

        if is_update_mode:
            self.app_select_combo.clear()
            if hasattr(self, 'df') and not self.df.empty:
                self.app_select_combo.addItems(self.df['Solution_Name'].tolist())
            self.save_btn.setText("Update Application")
        else:
            self.clear_form()
            self.save_btn.setText("Save Application")

    def load_application_data(self, app_name):
        if not app_name or not self.update_mode_checkbox.isChecked():
            return

        if hasattr(self, 'df') and not self.df.empty:
            app_data = self.df[self.df['Solution_Name'] == app_name].iloc[0]
            for field_name, input_widget in self.add_app_fields.items():
                if field_name in app_data and field_name not in ['LoB', 'Status']:
                    input_widget.setText(str(app_data[field_name]))
                elif field_name in ['LoB', 'Status']:
                    value = app_data.get(field_name)
                    index = input_widget.findText(value)
                    if index >= 0:
                        input_widget.setCurrentIndex(index)

    def clear_form(self):
        if hasattr(self, 'add_app_fields'):
            for field_name, input_widget in self.add_app_fields.items():
                input_widget.clear()
                if field_name == "LoB":
                    input_widget.addItems(self.lob)
                elif field_name == 'Status':
                    input_widget.addItems(STATUS)
        self.update_mode_checkbox.setChecked(False)

    def show_success_message(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(message)
        msg.setWindowTitle("Success")
        msg.exec()

    def update_sharepoint_db(self, dictionary_as_list, operation):
        cred = HttpNtlmAuth(SID, "")
        site = Site(SITE_URL, auth=cred, verify_ssl=False)
        sp_list = site.List(SHAREPOINT_LIST)
        sp_list.UpdateListItems(data=dictionary_as_list, kind=operation)

    def update_app_list(self):
        # Placeholder for app list update
        pass

    def handle_selection_changed(self):
        # Placeholder for selection handling
        pass