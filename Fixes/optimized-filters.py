def setup_audit_reports_panel(self):
    audit_widget = QFrame()
    layout = QVBoxLayout(audit_widget)
    layout.setSpacing(15)
    layout.setContentsMargins(10, 10, 10, 10)
    
    # Top section with title and report selection in one row
    top_layout = QHBoxLayout()
    
    # Title
    title = QLabel("Audit Reports")
    title.setProperty("heading", True)
    title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    top_layout.addWidget(title)
    top_layout.addSpacing(20)
    
    # Report selection
    report_label = QLabel("Report Type:")
    report_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    self.report_combo = QComboBox()
    self.report_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    self.report_combo.setMinimumWidth(200)
    self.report_combo.addItems([
        "Admin Activity Log",
        "User Access Audit",
        "Application Access Review",
        "Application Lifecycle Report",
        "LoB Application Access",
        "Cost Center User Access"
    ])
    self.report_combo.currentTextChanged.connect(self.change_report_type)
    
    top_layout.addWidget(report_label)
    top_layout.addWidget(self.report_combo)
    top_layout.addStretch()
    
    layout.addLayout(top_layout)
    
    # Create a collapsible filter section
    filter_section = QFrame()
    filter_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 4px; }")
    filter_section_layout = QVBoxLayout(filter_section)
    filter_section_layout.setContentsMargins(10, 10, 10, 10)
    filter_section_layout.setSpacing(10)
    
    # Filter section header with toggle button
    filter_header = QHBoxLayout()
    filter_label = QLabel("Filters")
    filter_label.setStyleSheet("font-weight: bold;")
    
    self.toggle_filter_btn = QPushButton("▼")  # Down arrow
    self.toggle_filter_btn.setFixedSize(24, 24)
    self.toggle_filter_btn.clicked.connect(self.toggle_filters)
    self.filters_expanded = True  # Track state
    
    filter_header.addWidget(filter_label)
    filter_header.addStretch()
    filter_header.addWidget(self.toggle_filter_btn)
    filter_section_layout.addLayout(filter_header)
    
    # Filter container - horizontal layout for filters
    self.filter_container = QFrame()
    self.filter_layout = QGridLayout(self.filter_container)
    self.filter_layout.setContentsMargins(0, 0, 0, 0)
    self.filter_layout.setSpacing(10)
    filter_section_layout.addWidget(self.filter_container)
    
    # Filter actions
    filter_actions = QHBoxLayout()
    apply_btn = QPushButton("Apply Filters")
    apply_btn.clicked.connect(self.apply_filters)
    apply_btn.setFixedWidth(100)
    
    clear_btn = QPushButton("Clear")
    clear_btn.clicked.connect(self.clear_filters)
    clear_btn.setFixedWidth(80)
    
    filter_actions.addWidget(apply_btn)
    filter_actions.addWidget(clear_btn)
    filter_actions.addStretch()
    filter_section_layout.addLayout(filter_actions)
    
    layout.addWidget(filter_section)
    
    # Report view (table)
    self.report_table = QTableWidget()
    self.report_table.setStyleSheet("""
        QTableWidget {
            border: 1px solid #ddd;
            background-color: white;
        }
        QHeaderView::section {
            background-color: #f5f5f5;
            padding: 6px;
            border: none;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }
        QTableWidget::item {
            padding: 4px;
        }
    """)
    self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    self.report_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    self.report_table.setAlternatingRowColors(True)
    layout.addWidget(self.report_table)
    
    # Action buttons
    button_layout = QHBoxLayout()
    
    export_btn = QPushButton("Export to CSV")
    export_btn.clicked.connect(self.export_report)
    
    refresh_btn = QPushButton("Refresh")
    refresh_btn.clicked.connect(self.refresh_report)
    
    button_layout.addWidget(export_btn)
    button_layout.addWidget(refresh_btn)
    button_layout.addStretch()
    
    layout.addLayout(button_layout)
    
    self.right_stack.addWidget(audit_widget)
    
    # Initialize the first report type
    self.change_report_type("Admin Activity Log")

def toggle_filters(self):
    """Toggle filter section visibility"""
    self.filters_expanded = not self.filters_expanded
    self.filter_container.setVisible(self.filters_expanded)
    self.toggle_filter_btn.setText("▼" if self.filters_expanded else "▶")  # Down or right arrow

def change_report_type(self, report_type):
    # Clear existing filters
    while self.filter_layout.count():
        item = self.filter_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
    
    # Reset filter row and column counters
    self.filter_row = 0
    self.filter_col = 0
    max_cols = 3  # Number of filter pairs per row
    
    # Add filter dropdowns based on report type
    if report_type == "Admin Activity Log":
        self.add_filter_dropdown("Admin Username", self.get_unique_values("admin", "username"))
        self.add_filter_dropdown("Action", self.get_unique_values("pslv_launch_history", "action"))
        self.add_date_filter("Action Date")
    
    elif report_type == "User Access Audit":
        self.add_filter_dropdown("User", self.get_unique_values("users", "name"))
        self.add_filter_dropdown("Application", self.get_unique_values("applications", "solution_name"))
        self.add_filter_dropdown("Granted By", self.get_unique_values("admin", "username"))
        self.add_date_filter("Granted Date")
    
    elif report_type == "Application Access Review":
        self.add_filter_dropdown("Application", self.get_unique_values("applications", "solution_name"))
        self.add_filter_dropdown("Status", self.get_unique_values("applications", "status"))
        self.add_filter_dropdown("LoB", self.get_unique_values("applications", "lob"))
    
    elif report_type == "Application Lifecycle Report":
        self.add_filter_dropdown("Application", self.get_unique_values("applications", "solution_name"))
        self.add_filter_dropdown("Status", self.get_unique_values("applications", "status"))
        self.add_date_filter("Release Date")
    
    elif report_type == "LoB Application Access":
        self.add_filter_dropdown("LoB", self.get_unique_values("applications", "lob"))
        self.add_filter_dropdown("Application", self.get_unique_values("applications", "solution_name"))
    
    elif report_type == "Cost Center User Access":
        self.add_filter_dropdown("Cost Center", self.get_unique_values("users", "cost_center"))
        self.add_filter_dropdown("User", self.get_unique_values("users", "name"))
    
    # Apply default filters (show all data)
    self.apply_filters()

def add_filter_dropdown(self, label_text, values):
    """Add a filter dropdown in a grid layout to save space"""
    if not hasattr(self, 'filter_row'):
        self.filter_row = 0
        self.filter_col = 0
    
    max_cols = 3  # Number of filter pairs per row
    
    # Create label
    label = QLabel(f"{label_text}:")
    label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    # Create combobox
    combo = QComboBox()
    combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    combo.setMaximumWidth(200)
    
    # Add "ALL" option first
    combo.addItem("ALL")
    combo.addItems(values)
    
    # Add to grid layout
    self.filter_layout.addWidget(label, self.filter_row, self.filter_col * 2)
    self.filter_layout.addWidget(combo, self.filter_row, self.filter_col * 2 + 1)
    
    # Update position for next filter
    self.filter_col += 1
    if self.filter_col >= max_cols:
        self.filter_col = 0
        self.filter_row += 1
    
    return combo

def add_date_filter(self, label_text):
    """Add a date range filter in a grid layout to save space"""
    if not hasattr(self, 'filter_row'):
        self.filter_row = 0
        self.filter_col = 0
    
    max_cols = 3  # Ensure this is consistent with add_filter_dropdown
    
    # Add date label (spans multiple columns)
    date_label = QLabel(f"{label_text}:")
    date_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    # Create a container for the date inputs
    date_container = QFrame()
    date_layout = QHBoxLayout(date_container)
    date_layout.setContentsMargins(0, 0, 0, 0)
    date_layout.setSpacing(5)
    
    # From date
    from_label = QLabel("From:")
    from_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    from_date = QDateEdit()
    from_date.setCalendarPopup(True)
    from_date.setDisplayFormat("yyyy-MM-dd")
    from_date.setDate(QDate.currentDate().addMonths(-1))  # Default to 1 month ago
    
    # To date
    to_label = QLabel("To:")
    to_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    to_date = QDateEdit()
    to_date.setCalendarPopup(True)
    to_date.setDisplayFormat("yyyy-MM-dd")
    to_date.setDate(QDate.currentDate())  # Default to today
    
    # Add to container
    date_layout.addWidget(from_label)
    date_layout.addWidget(from_date)
    date_layout.addWidget(to_label)
    date_layout.addWidget(to_date)
    date_layout.addStretch()
    
    # Add to grid, spanning multiple columns for the date range
    self.filter_layout.addWidget(date_label, self.filter_row, self.filter_col * 2)
    self.filter_layout.addWidget(date_container, self.filter_row, self.filter_col * 2 + 1)
    
    # Update position for next filter
    self.filter_col += 1
    if self.filter_col >= max_cols:
        self.filter_col = 0
        self.filter_row += 1
    
    return from_date, to_date
