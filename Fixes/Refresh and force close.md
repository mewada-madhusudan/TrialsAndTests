def build_admin_activity_query(self):
    """Build query for Admin Activity Log report with filters from grid layout"""
    query = """
        SELECT a.username AS "Admin", 
               h.action AS "Action", 
               h.timestamp AS "Timestamp", 
               h.details AS "Details"
        FROM pslv_launch_history h
        JOIN admin a ON h.admin_id = a.id
        WHERE 1=1
    """
    
    params = {}
    
    # Get filter values from grid layout
    admin_filter = self.get_filter_value("Admin Username")
    action_filter = self.get_filter_value("Action")
    date_from, date_to = self.get_date_filter_values("Action Date")
    
    # Add filter conditions
    if admin_filter != "ALL":
        query += " AND a.username = :admin"
        params["admin"] = admin_filter
    
    if action_filter != "ALL":
        query += " AND h.action = :action"
        params["action"] = action_filter
    
    if date_from:
        query += " AND h.timestamp >= :date_from"
        params["date_from"] = date_from
    
    if date_to:
        query += " AND h.timestamp <= :date_to"
        params["date_to"] = date_to
    
    query += " ORDER BY h.timestamp DESC"
    
    return query, params

def build_user_access_audit_query(self):
    """Build query for User Access Audit report with filters from grid layout"""
    query = """
        SELECT u.name AS "User Name", 
               a.solution_name AS "Application", 
               ua.granted_date AS "Access Granted Date",
               adm.username AS "Granted By"
        FROM user_access ua
        JOIN users u ON ua.user_id = u.id
        JOIN applications a ON ua.app_id = a.id
        JOIN admin adm ON ua.granted_by = adm.id
        WHERE 1=1
    """
    
    params = {}
    
    # Get filter values from grid layout
    user_filter = self.get_filter_value("User")
    app_filter = self.get_filter_value("Application")
    admin_filter = self.get_filter_value("Granted By")
    date_from, date_to = self.get_date_filter_values("Granted Date")
    
    # Add filter conditions
    if user_filter != "ALL":
        query += " AND u.name = :user"
        params["user"] = user_filter
    
    if app_filter != "ALL":
        query += " AND a.solution_name = :app"
        params["app"] = app_filter
    
    if admin_filter != "ALL":
        query += " AND adm.username = :admin"
        params["admin"] = admin_filter
    
    if date_from:
        query += " AND ua.granted_date >= :date_from"
        params["date_from"] = date_from
    
    if date_to:
        query += " AND ua.granted_date <= :date_to"
        params["date_to"] = date_to
    
    query += " ORDER BY ua.granted_date DESC"
    
    return query, params

def build_application_access_review_query(self):
    """Build query for Application Access Review report with filters from grid layout"""
    query = """
        SELECT a.solution_name AS "Application",
               a.status AS "Status",
               a.lob AS "Line of Business",
               COUNT(ua.id) AS "User Count"
        FROM applications a
        LEFT JOIN user_access ua ON a.id = ua.app_id
        WHERE 1=1
    """
    
    params = {}
    
    # Get filter values from grid layout
    app_filter = self.get_filter_value("Application")
    status_filter = self.get_filter_value("Status")
    lob_filter = self.get_filter_value("LoB")
    
    # Add filter conditions
    if app_filter != "ALL":
        query += " AND a.solution_name = :app"
        params["app"] = app_filter
    
    if status_filter != "ALL":
        query += " AND a.status = :status"
        params["status"] = status_filter
    
    if lob_filter != "ALL":
        query += " AND a.lob = :lob"
        params["lob"] = lob_filter
    
    query += " GROUP BY a.solution_name, a.status, a.lob ORDER BY a.solution_name"
    
    return query, params

def build_application_lifecycle_query(self):
    """Build query for Application Lifecycle Report with filters from grid layout"""
    query = """
        SELECT a.solution_name AS "Application",
               a.status AS "Status",
               a.release_date AS "Release Date",
               a.last_review_date AS "Last Review Date",
               a.next_review_date AS "Next Review Date"
        FROM applications a
        WHERE 1=1
    """
    
    params = {}
    
    # Get filter values from grid layout
    app_filter = self.get_filter_value("Application")
    status_filter = self.get_filter_value("Status")
    date_from, date_to = self.get_date_filter_values("Release Date")
    
    # Add filter conditions
    if app_filter != "ALL":
        query += " AND a.solution_name = :app"
        params["app"] = app_filter
    
    if status_filter != "ALL":
        query += " AND a.status = :status"
        params["status"] = status_filter
    
    if date_from:
        query += " AND a.release_date >= :date_from"
        params["date_from"] = date_from
    
    if date_to:
        query += " AND a.release_date <= :date_to"
        params["date_to"] = date_to
    
    query += " ORDER BY a.solution_name"
    
    return query, params

def build_lob_application_access_query(self):
    """Build query for LoB Application Access report with filters from grid layout"""
    query = """
        SELECT a.lob AS "Line of Business",
               a.solution_name AS "Application",
               COUNT(ua.id) AS "User Count"
        FROM applications a
        LEFT JOIN user_access ua ON a.id = ua.app_id
        WHERE 1=1
    """
    
    params = {}
    
    # Get filter values from grid layout
    lob_filter = self.get_filter_value("LoB")
    app_filter = self.get_filter_value("Application")
    
    # Add filter conditions
    if lob_filter != "ALL":
        query += " AND a.lob = :lob"
        params["lob"] = lob_filter
    
    if app_filter != "ALL":
        query += " AND a.solution_name = :app"
        params["app"] = app_filter
    
    query += " GROUP BY a.lob, a.solution_name ORDER BY a.lob, a.solution_name"
    
    return query, params

def build_cost_center_user_access_query(self):
    """Build query for Cost Center User Access report with filters from grid layout"""
    query = """
        SELECT u.cost_center AS "Cost Center",
               u.name AS "User Name",
               COUNT(ua.id) AS "Application Count"
        FROM users u
        LEFT JOIN user_access ua ON u.id = ua.user_id
        WHERE 1=1
    """
    
    params = {}
    
    # Get filter values from grid layout
    cc_filter = self.get_filter_value("Cost Center")
    user_filter = self.get_filter_value("User")
    
    # Add filter conditions
    if cc_filter != "ALL":
        query += " AND u.cost_center = :cc"
        params["cc"] = cc_filter
    
    if user_filter != "ALL":
        query += " AND u.name = :user"
        params["user"] = user_filter
    
    query += " GROUP BY u.cost_center, u.name ORDER BY u.cost_center, u.name"
    
    return query, params

def get_filter_value(self, label_text):
    """
    Find a filter dropdown by label text and return its value
    Works with grid layout
    """
    # Search through all grid items for the matching label
    for row in range(self.filter_layout.rowCount()):
        for col in range(0, self.filter_layout.columnCount(), 2):  # Step by 2 since labels are in even columns
            label_item = self.filter_layout.itemAtPosition(row, col)
            if label_item and label_item.widget():
                label = label_item.widget()
                if isinstance(label, QLabel) and label.text().startswith(f"{label_text}:"):
                    # Found label, get the corresponding combobox
                    combo_item = self.filter_layout.itemAtPosition(row, col + 1)
                    if combo_item and combo_item.widget():
                        widget = combo_item.widget()
                        if isinstance(widget, QComboBox):
                            return widget.currentText()
                        elif isinstance(widget, QFrame):  # For date filters
                            # This is a container for date widgets
                            # For date filters we return None here since they're handled separately
                            return None
    
    return "ALL"  # Default if not found

def get_date_filter_values(self, label_text):
    """
    Find date filter inputs by label text and return from/to values
    Works with grid layout
    """
    for row in range(self.filter_layout.rowCount()):
        for col in range(0, self.filter_layout.columnCount(), 2):  # Step by 2 since labels are in even columns
            label_item = self.filter_layout.itemAtPosition(row, col)
            if label_item and label_item.widget():
                label = label_item.widget()
                if isinstance(label, QLabel) and label.text().startswith(f"{label_text}:"):
                    # Found label, get the corresponding date container
                    container_item = self.filter_layout.itemAtPosition(row, col + 1)
                    if container_item and container_item.widget():
                        container = container_item.widget()
                        if isinstance(container, QFrame):
                            # Find the date inputs within the container
                            date_inputs = []
                            layout = container.layout()
                            for i in range(layout.count()):
                                widget = layout.itemAt(i).widget()
                                if isinstance(widget, QDateEdit):
                                    date_inputs.append(widget)
                            
                            if len(date_inputs) >= 2:
                                from_date = date_inputs[0].date().toString("yyyy-MM-dd")
                                to_date = date_inputs[1].date().toString("yyyy-MM-dd")
                                return from_date, to_date
    
    return None, None  # Default if not found
