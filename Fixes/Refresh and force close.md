I was thinking to create a ui in python where I can give dropdown options to auditor to select the respective fields and have "ALL" in all dropdowns if they need everything based on selected option if dropdown selection is empty then not to use that column. How can I modify it. I am using sqlitedbEditI'll help you create a more flexible UI for auditors with dropdown filters that include an "ALL" option for each field. This will let users filter reports dynamically without writing any SQL queries. Here's how we can modify the audit reports panel:

def setup_audit_reports_panel(self):
    audit_widget = QFrame()
    layout = QVBoxLayout(audit_widget)
    layout.setSpacing(20)
    
    # Title
    title = QLabel("Audit Reports")
    title.setProperty("heading", True)
    layout.addWidget(title)
    
    # Report selection
    select_layout = QHBoxLayout()
    
    report_label = QLabel("Select Report Type:")
    self.report_combo = QComboBox()
    self.report_combo.addItems([
        "Admin Activity Log",
        "User Access Audit",
        "Application Access Review",
        "Application Lifecycle Report",
        "LoB Application Access",
        "Cost Center User Access"
    ])
    self.report_combo.currentTextChanged.connect(self.change_report_type)
    
    select_layout.addWidget(report_label)
    select_layout.addWidget(self.report_combo)
    select_layout.addStretch()
    
    layout.addLayout(select_layout)
    
    # Dynamic filter section
    self.filter_frame = QFrame()
    self.filter_layout = QVBoxLayout(self.filter_frame)
    layout.addWidget(self.filter_frame)
    
    # Apply button
    button_row = QHBoxLayout()
    apply_btn = QPushButton("Apply Filters")
    apply_btn.clicked.connect(self.apply_filters)
    clear_btn = QPushButton("Clear Filters")
    clear_btn.clicked.connect(self.clear_filters)
    button_row.addWidget(apply_btn)
    button_row.addWidget(clear_btn)
    button_row.addStretch()
    layout.addLayout(button_row)
    
    # Report view
    self.report_table = QTableWidget()
    self.report_table.setStyleSheet("""
        QTableWidget {
            border: 1px solid #ddd;
            background-color: white;
        }
        QHeaderView::section {
            background-color: #f5f5f5;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }
        QTableWidget::item {
            padding: 5px;
        }
    """)
    self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only
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

def clear_filters(self):
    # Reset all filters to "ALL"
    for i in range(self.filter_layout.count()):
        widget = self.filter_layout.itemAt(i).widget()
        if isinstance(widget, QFrame):
            for j in range(widget.layout().count()):
                w = widget.layout().itemAt(j).widget()
                if isinstance(w, QComboBox):
                    w.setCurrentText("ALL")
    
    # Refresh the report with no filters
    self.apply_filters()

def change_report_type(self, report_type):
    # Clear existing filters
    while self.filter_layout.count():
        child = self.filter_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
    
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
    frame = QFrame()
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 5)
    
    label = QLabel(f"{label_text}:")
    combo = QComboBox()
    
    # Add "ALL" option first
    combo.addItem("ALL")
    combo.addItems(values)
    
    layout.addWidget(label)
    layout.addWidget(combo)
    layout.addStretch()
    
    self.filter_layout.addWidget(frame)
    return combo

def add_date_filter(self, label_text):
    frame = QFrame()
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 5)
    
    label = QLabel(f"{label_text}:")
    
    from_label = QLabel("From:")
    from_date = QLineEdit()
    from_date.setPlaceholderText("YYYY-MM-DD")
    
    to_label = QLabel("To:")
    to_date = QLineEdit()
    to_date.setPlaceholderText("YYYY-MM-DD")
    
    layout.addWidget(label)
    layout.addWidget(from_label)
    layout.addWidget(from_date)
    layout.addWidget(to_label)
    layout.addWidget(to_date)
    layout.addStretch()
    
    self.filter_layout.addWidget(frame)
    return from_date, to_date

def get_unique_values(self, table, column):
    try:
        cursor = self.db.conn.cursor()
        cursor.execute(f"SELECT DISTINCT {column} FROM {table} ORDER BY {column}")
        values = [row[0] for row in cursor.fetchall()]
        return values
    except Exception as e:
        print(f"Error getting unique values: {e}")
        return []

def apply_filters(self):
    # Get the current report type
    report_type = self.report_combo.currentText()
    
    # Build query based on report type and filters
    if report_type == "Admin Activity Log":
        query, params = self.build_admin_activity_query()
    elif report_type == "User Access Audit":
        query, params = self.build_user_access_audit_query()
    elif report_type == "Application Access Review":
        query, params = self.build_application_access_review_query()
    elif report_type == "Application Lifecycle Report":
        query, params = self.build_application_lifecycle_query()
    elif report_type == "LoB Application Access":
        query, params = self.build_lob_application_access_query()
    elif report_type == "Cost Center User Access":
        query, params = self.build_cost_center_user_access_query()
    
    # Execute query
    try:
        df = pd.read_sql_query(query, self.db.conn, params=params)
        self.display_dataframe(df)
    except Exception as e:
        QMessageBox.warning(self, "Query Error", f"Error executing query: {e}")
        print(f"Query error: {e}")


query builder db function 
def build_admin_activity_query(self):
    # Get filter values
    admin_combo = None
    action_combo = None
    from_date = None
    to_date = None
    
    for i in range(self.filter_layout.count()):
        widget = self.filter_layout.itemAt(i).widget()
        if isinstance(widget, QFrame):
            label_text = widget.layout().itemAt(0).widget().text()
            
            if label_text == "Admin Username:":
                admin_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Action:":
                action_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Action Date:":
                from_date = widget.layout().itemAt(2).widget()
                to_date = widget.layout().itemAt(4).widget()
    
    # Base query
    query = '''
        SELECT a.username, p.description, p.action, p.action_date
        FROM pslv_launch_history p
        JOIN admin a ON p.sid = a.sid
        WHERE 1=1
    '''
    
    params = {}
    
    # Apply filters
    if admin_combo and admin_combo.currentText() != "ALL":
        query += " AND a.username = :admin"
        params['admin'] = admin_combo.currentText()
    
    if action_combo and action_combo.currentText() != "ALL":
        query += " AND p.action = :action"
        params['action'] = action_combo.currentText()
    
    if from_date and from_date.text():
        query += " AND p.action_date >= :from_date"
        params['from_date'] = from_date.text()
    
    if to_date and to_date.text():
        query += " AND p.action_date <= :to_date"
        params['to_date'] = to_date.text()
    
    query += " ORDER BY p.action_date DESC"
    
    return query, params

def build_user_access_audit_query(self):
    # Get filter values
    user_combo = None
    app_combo = None
    granted_by_combo = None
    from_date = None
    to_date = None
    
    for i in range(self.filter_layout.count()):
        widget = self.filter_layout.itemAt(i).widget()
        if isinstance(widget, QFrame):
            label_text = widget.layout().itemAt(0).widget().text()
            
            if label_text == "User:":
                user_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Application:":
                app_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Granted By:":
                granted_by_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Granted Date:":
                from_date = widget.layout().itemAt(2).widget()
                to_date = widget.layout().itemAt(4).widget()
    
    # Base query
    query = '''
        SELECT u.sid, u.name, u.email, a.solution_name, ua.granted_date, 
               adm.username as granted_by
        FROM user_application_access ua
        JOIN users u ON ua.user_id = u.sid
        JOIN applications a ON ua.application_id = a.application_id
        JOIN admin adm ON ua.granted_by = adm.sid
        WHERE 1=1
    '''
    
    params = {}
    
    # Apply filters
    if user_combo and user_combo.currentText() != "ALL":
        query += " AND u.name = :user"
        params['user'] = user_combo.currentText()
    
    if app_combo and app_combo.currentText() != "ALL":
        query += " AND a.solution_name = :app"
        params['app'] = app_combo.currentText()
    
    if granted_by_combo and granted_by_combo.currentText() != "ALL":
        query += " AND adm.username = :admin"
        params['admin'] = granted_by_combo.currentText()
    
    if from_date and from_date.text():
        query += " AND ua.granted_date >= :from_date"
        params['from_date'] = from_date.text()
    
    if to_date and to_date.text():
        query += " AND ua.granted_date <= :to_date"
        params['to_date'] = to_date.text()
    
    query += " ORDER BY ua.granted_date DESC"
    
    return query, params

def build_application_access_review_query(self):
    # Get filter values
    app_combo = None
    status_combo = None
    lob_combo = None
    
    for i in range(self.filter_layout.count()):
        widget = self.filter_layout.itemAt(i).widget()
        if isinstance(widget, QFrame):
            label_text = widget.layout().itemAt(0).widget().text()
            
            if label_text == "Application:":
                app_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Status:":
                status_combo = widget.layout().itemAt(1).widget()
            elif label_text == "LoB:":
                lob_combo = widget.layout().itemAt(1).widget()
    
    # Base query
    query = '''
        SELECT a.application_id, a.solution_name, a.status, a.lob,
               COUNT(ua.user_id) as user_count,
               GROUP_CONCAT(u.name, ', ') as users
        FROM applications a
        LEFT JOIN user_application_access ua ON a.application_id = ua.application_id
        LEFT JOIN users u ON ua.user_id = u.sid
        WHERE 1=1
    '''
    
    params = {}
    
    # Apply filters
    if app_combo and app_combo.currentText() != "ALL":
        query += " AND a.solution_name = :app"
        params['app'] = app_combo.currentText()
    
    if status_combo and status_combo.currentText() != "ALL":
        query += " AND a.status = :status"
        params['status'] = status_combo.currentText()
    
    if lob_combo and lob_combo.currentText() != "ALL":
        query += " AND a.lob = :lob"
        params['lob'] = lob_combo.currentText()
    
    query += " GROUP BY a.application_id ORDER BY a.solution_name"
    
    return query, params

def build_application_lifecycle_query(self):
    # Get filter values
    app_combo = None
    status_combo = None
    from_date = None
    to_date = None
    
    for i in range(self.filter_layout.count()):
        widget = self.filter_layout.itemAt(i).widget()
        if isinstance(widget, QFrame):
            label_text = widget.layout().itemAt(0).widget().text()
            
            if label_text == "Application:":
                app_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Status:":
                status_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Release Date:":
                from_date = widget.layout().itemAt(2).widget()
                to_date = widget.layout().itemAt(4).widget()
    
    # Base query
    query = '''
        SELECT application_id, solution_name, release_date, 
               validity_period, status, beta_transition_date
        FROM applications
        WHERE 1=1
    '''
    
    params = {}
    
    # Apply filters
    if app_combo and app_combo.currentText() != "ALL":
        query += " AND solution_name = :app"
        params['app'] = app_combo.currentText()
    
    if status_combo and status_combo.currentText() != "ALL":
        query += " AND status = :status"
        params['status'] = status_combo.currentText()
    
    if from_date and from_date.text():
        query += " AND release_date >= :from_date"
        params['from_date'] = from_date.text()
    
    if to_date and to_date.text():
        query += " AND release_date <= :to_date"
        params['to_date'] = to_date.text()
    
    query += " ORDER BY release_date DESC"
    
    return query, params

def build_lob_application_access_query(self):
    # Get filter values
    lob_combo = None
    app_combo = None
    
    for i in range(self.filter_layout.count()):
        widget = self.filter_layout.itemAt(i).widget()
        if isinstance(widget, QFrame):
            label_text = widget.layout().itemAt(0).widget().text()
            
            if label_text == "LoB:":
                lob_combo = widget.layout().itemAt(1).widget()
            elif label_text == "Application:":
                app_combo = widget.layout().itemAt(1).widget()
    
    # Base query
    query = '''
        SELECT a.lob, a.application_id, a.solution_name,
               COUNT(ua.user_id) as user_count,
               GROUP_CONCAT(u.name, ', ') as users
        FROM applications a
        LEFT JOIN user_application_access ua ON a.application_id = ua.application_id
        LEFT JOIN users u ON ua.user_id = u.sid
        WHERE 1=1
    '''
    
    params = {}
    
    # Apply filters
    if lob_combo and lob_combo.currentText() != "ALL":
        query += " AND a.lob = :lob"
        params['lob'] = lob_combo.currentText()
    
    if app_combo and app_combo.currentText() != "ALL":
        query += " AND a.solution_name = :app"
        params['app'] = app_combo.currentText()
    
    query += " GROUP BY a.lob, a.application_id ORDER BY a.lob, a.solution_name"
    
    return query, params

def build_cost_center_user_access_query(self):
    # Get filter values
    cc_combo = None
    user_combo = None
    
    for i in range(self.filter_layout.count()):
        widget = self.filter_layout.itemAt(i).widget()
        if isinstance(widget, QFrame):
            label_text = widget.layout().itemAt(0).widget().text()
            
            if label_text == "Cost Center:":
                cc_combo = widget.layout().itemAt(1).widget()
            elif label_text == "User:":
                user_combo = widget.layout().itemAt(1).widget()
    
    # Base query
    query = '''
        SELECT u.cost_center, u.sid, u.name,
               COUNT(ua.application_id) as app_count,
               GROUP_CONCAT(a.solution_name, ', ') as applications
        FROM users u
        LEFT JOIN user_application_access ua ON u.sid = ua.user_id
        LEFT JOIN applications a ON ua.application_id = a.application_id
        WHERE 1=1
    '''
    
    params = {}
    
    # Apply filters
    if cc_combo and cc_combo.currentText() != "ALL":
        query += " AND u.cost_center = :cc"
        params['cc'] = cc_combo.currentText()
    
    if user_combo and user_combo.currentText() != "ALL":
        query += " AND u.name = :user"
        params['user'] = user_combo.currentText()
    
    query += " GROUP BY u.cost_center, u.sid ORDER BY u.cost_center, u.name"
    
    return query, params
