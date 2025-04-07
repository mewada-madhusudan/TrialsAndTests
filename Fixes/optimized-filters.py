def setup_audit_reports_panel(self):
    audit_widget = QFrame()
    layout = QVBoxLayout(audit_widget)
    layout.setSpacing(15)
    layout.setContentsMargins(20, 20, 20, 20)
    
    # Top section with title and report selection in one row
    top_layout = QHBoxLayout()
    
    # Title
    title = QLabel("Audit Reports")
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
    title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    top_layout.addWidget(title)
    top_layout.addSpacing(20)
    
    # Report selection
    report_label = QLabel("Report Type:")
    report_label.setStyleSheet("font-size: 14px; color: #555;")
    report_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    self.report_combo = QComboBox()
    self.report_combo.setStyleSheet("""
        QComboBox {
            border: 1px solid #cfd4da;
            border-radius: 4px;
            padding: 4px 8px;
            min-height: 28px;
            background-color: white;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 20px;
            border-left: none;
        }
    """)
    self.report_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    self.report_combo.setMinimumWidth(220)
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
    
    # Create a clean filter section without the "Filters" header
    filter_section = QFrame()
    filter_section.setStyleSheet("""
        QFrame {
            border: 1px solid #e0e4e8;
            border-radius: 6px;
            background-color: white;
        }
    """)
    filter_section_layout = QVBoxLayout(filter_section)
    filter_section_layout.setContentsMargins(20, 20, 20, 20)
    filter_section_layout.setSpacing(15)
    
    # Filter container - grid layout for filters
    self.filter_container = QFrame()
    self.filter_layout = QGridLayout(self.filter_container)
    self.filter_layout.setContentsMargins(0, 0, 0, 0)
    self.filter_layout.setHorizontalSpacing(20)
    self.filter_layout.setVerticalSpacing(15)
    filter_section_layout.addWidget(self.filter_container)
    
    # Filter actions - right-aligned
    filter_actions = QHBoxLayout()
    filter_actions.addStretch()
    
    clear_btn = QPushButton("Clear")
    clear_btn.setStyleSheet("""
        QPushButton {
            background-color: #f0f4f8;
            border: 1px solid #cfd4da;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 80px;
            color: #333;
        }
        QPushButton:hover {
            background-color: #e2e8f0;
        }
        QPushButton:pressed {
            background-color: #d2dbe4;
        }
    """)
    clear_btn.clicked.connect(self.clear_filters)
    
    apply_btn = QPushButton("Apply")
    apply_btn.setStyleSheet("""
        QPushButton {
            background-color: #3081D0;
            border: 1px solid #2571C0;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 80px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2571C0;
        }
        QPushButton:pressed {
            background-color: #1e63ad;
        }
    """)
    apply_btn.clicked.connect(self.apply_filters)
    
    filter_actions.addWidget(clear_btn)
    filter_actions.addSpacing(10)
    filter_actions.addWidget(apply_btn)
    
    filter_section_layout.addLayout(filter_actions)
    layout.addWidget(filter_section)
    
    # Report view (table)
    self.report_table = QTableWidget()
    self.report_table.setStyleSheet("""
        QTableWidget {
            border: 1px solid #dfe4e9;
            border-radius: 4px;
            background-color: white;
        }
        QHeaderView::section {
            background-color: #f1f3f5;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #dfe4e9;
            font-weight: bold;
            color: #333;
        }
        QTableWidget::item {
            padding: 6px;
            border-bottom: 1px solid #eef0f2;
        }
        QTableWidget::item:alternate {
            background-color: #f9fafb;
        }
    """)
    self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    self.report_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    self.report_table.setAlternatingRowColors(True)
    layout.addWidget(self.report_table)
    
    # Action buttons
    button_layout = QHBoxLayout()
    
    export_btn = QPushButton("Export to CSV")
    export_btn.setStyleSheet("""
        QPushButton {
            background-color: #f0f4f8;
            border: 1px solid #cfd4da;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 120px;
            color: #333;
        }
        QPushButton:hover {
            background-color: #e2e8f0;
        }
        QPushButton:pressed {
            background-color: #d2dbe4;
        }
    """)
    export_btn.clicked.connect(self.export_report)
    
    refresh_btn = QPushButton("Refresh")
    refresh_btn.setStyleSheet("""
        QPushButton {
            background-color: #f0f4f8;
            border: 1px solid #cfd4da;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 100px;
            color: #333;
        }
        QPushButton:hover {
            background-color: #e2e8f0;
        }
        QPushButton:pressed {
            background-color: #d2dbe4;
        }
    """)
    refresh_btn.clicked.connect(self.refresh_report)
    
    button_layout.addWidget(export_btn)
    button_layout.addSpacing(10)
    button_layout.addWidget(refresh_btn)
    button_layout.addStretch()
    
    layout.addLayout(button_layout)
    
    self.right_stack.addWidget(audit_widget)
    
    # Initialize the first report type
    self.change_report_type("Admin Activity Log")


def add_filter_dropdown(self, label_text, values):
    """Add a filter dropdown in a grid layout to save space"""
    if not hasattr(self, 'filter_row'):
        self.filter_row = 0
        self.filter_col = 0
    
    max_cols = 2  # Reduced from 3 to give filters more space
    
    # Create label
    label = QLabel(f"{label_text}:")
    label.setStyleSheet("font-size: 13px; color: #555;")
    label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    # Create combobox
    combo = QComboBox()
    combo.setStyleSheet("""
        QComboBox {
            border: 1px solid #cfd4da;
            border-radius: 4px;
            padding: 4px 8px;
            min-height: 28px;
            background-color: white;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 20px;
            border-left: none;
        }
    """)
    combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    combo.setMinimumWidth(160)
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
    
    # Add a new row for date filters to give them more space
    self.filter_col = 0
    if self.filter_row > 0:
        self.filter_row += 1
    
    # Add date label
    date_label = QLabel(f"{label_text}:")
    date_label.setStyleSheet("font-size: 13px; color: #555;")
    date_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    # Create a container for the date inputs
    date_container = QFrame()
    date_layout = QHBoxLayout(date_container)
    date_layout.setContentsMargins(0, 0, 0, 0)
    date_layout.setSpacing(15)
    
    # From date
    from_label = QLabel("From:")
    from_label.setStyleSheet("font-size: 13px; color: #555;")
    from_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    from_date = QDateEdit()
    from_date.setStyleSheet("""
        QDateEdit {
            border: 1px solid #cfd4da;
            border-radius: 4px;
            padding: 4px 8px;
            min-height: 28px;
            background-color: white;
        }
        QDateEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 20px;
            border-left: none;
        }
    """)
    from_date.setCalendarPopup(True)
    from_date.setDisplayFormat("yyyy-MM-dd")
    from_date.setDate(QDate.currentDate().addMonths(-1))  # Default to 1 month ago
    
    # To date
    to_label = QLabel("To:")
    to_label.setStyleSheet("font-size: 13px; color: #555;")
    to_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    to_date = QDateEdit()
    to_date.setStyleSheet("""
        QDateEdit {
            border: 1px solid #cfd4da;
            border-radius: 4px;
            padding: 4px 8px;
            min-height: 28px;
            background-color: white;
        }
        QDateEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 20px;
            border-left: none;
        }
    """)
    to_date.setCalendarPopup(True)
    to_date.setDisplayFormat("yyyy-MM-dd")
    to_date.setDate(QDate.currentDate())  # Default to today
    
    # Add to container
    date_layout.addWidget(from_label)
    date_layout.addWidget(from_date)
    date_layout.addWidget(to_label)
    date_layout.addWidget(to_date)
    date_layout.addStretch()
    
    # Add to grid - date filter spans the entire row for better layout
    self.filter_layout.addWidget(date_label, self.filter_row, 0)
    self.filter_layout.addWidget(date_container, self.filter_row, 1, 1, 3)  # Span across 3 columns
    
    # Update position for next filter
    self.filter_row += 1
    self.filter_col = 0
    
    return from_date, to_date
