def display_dataframe(self, df):
    """
    Display a pandas DataFrame in the report table widget with pagination
    """
    # Store the complete dataframe for pagination
    self.full_data = df.copy()
    self.records_per_page = 20
    self.current_page = 1
    self.total_pages = max(1, math.ceil(len(df) / self.records_per_page))
    
    # Create pagination controls if they don't exist
    if not hasattr(self, 'pagination_frame'):
        self.setup_pagination_controls()
    
    # Show pagination frame only if needed
    if len(df) > self.records_per_page:
        self.pagination_frame.setVisible(True)
        self.update_pagination_controls()
    else:
        self.pagination_frame.setVisible(False)
    
    # Display the first page
    self.display_current_page()

def setup_pagination_controls(self):
    """
    Create pagination controls for the report table
    """
    self.pagination_frame = QFrame()
    pagination_layout = QHBoxLayout(self.pagination_frame)
    pagination_layout.setContentsMargins(0, 10, 0, 0)
    
    # Add record count label
    self.record_count_label = QLabel()
    pagination_layout.addWidget(self.record_count_label)
    
    pagination_layout.addStretch()
    
    # Previous page button
    self.prev_btn = QPushButton("< Prev")
    self.prev_btn.setFixedWidth(80)
    self.prev_btn.clicked.connect(self.go_to_prev_page)
    pagination_layout.addWidget(self.prev_btn)
    
    # Page number buttons container
    self.page_buttons_frame = QFrame()
    self.page_buttons_layout = QHBoxLayout(self.page_buttons_frame)
    self.page_buttons_layout.setContentsMargins(0, 0, 0, 0)
    self.page_buttons_layout.setSpacing(5)
    pagination_layout.addWidget(self.page_buttons_frame)
    
    # Next page button
    self.next_btn = QPushButton("Next >")
    self.next_btn.setFixedWidth(80)
    self.next_btn.clicked.connect(self.go_to_next_page)
    pagination_layout.addWidget(self.next_btn)
    
    # Add pagination frame after the table
    layout = self.report_table.parent().layout()
    layout_index = layout.indexOf(self.report_table)
    layout.insertWidget(layout_index + 1, self.pagination_frame)

def update_pagination_controls(self):
    """
    Update pagination controls based on current state
    """
    # Update record count label
    total_records = len(self.full_data)
    start_record = (self.current_page - 1) * self.records_per_page + 1
    end_record = min(start_record + self.records_per_page - 1, total_records)
    self.record_count_label.setText(f"Showing {start_record}-{end_record} of {total_records} records")
    
    # Enable/disable navigation buttons
    self.prev_btn.setEnabled(self.current_page > 1)
    self.next_btn.setEnabled(self.current_page < self.total_pages)
    
    # Clear existing page buttons
    while self.page_buttons_layout.count():
        item = self.page_buttons_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
    
    # Determine which page buttons to show
    visible_pages = self.get_visible_page_numbers()
    
    # Add page buttons
    for page_num in visible_pages:
        if page_num == -1:  # Ellipsis
            label = QLabel("...")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedWidth(30)
            self.page_buttons_layout.addWidget(label)
        else:
            btn = QPushButton(str(page_num))
            btn.setFixedWidth(40)
            # Highlight current page
            if page_num == self.current_page:
                btn.setProperty("current", True)
                btn.setStyleSheet("QPushButton[current=true] { font-weight: bold; background-color: #e0e0e0; }")
            btn.clicked.connect(lambda _, p=page_num: self.go_to_page(p))
            self.page_buttons_layout.addWidget(btn)

def get_visible_page_numbers(self):
    """
    Determine which page numbers to display in pagination
    Will show current page, first page, last page, and pages around current
    """
    visible_pages = []
    
    # Always show first page
    visible_pages.append(1)
    
    # Handle ellipsis and nearby pages
    if self.current_page > 3:
        visible_pages.append(-1)  # Ellipsis
    
    # Pages around current page
    start_nearby = max(2, self.current_page - 1)
    end_nearby = min(self.total_pages - 1, self.current_page + 1)
    
    for i in range(start_nearby, end_nearby + 1):
        visible_pages.append(i)
    
    # Handle ellipsis before last page
    if self.current_page < self.total_pages - 2:
        visible_pages.append(-1)  # Ellipsis
    
    # Always show last page if more than 1 page
    if self.total_pages > 1:
        visible_pages.append(self.total_pages)
    
    return visible_pages

def go_to_page(self, page_num):
    """
    Go to a specific page
    """
    if 1 <= page_num <= self.total_pages:
        self.current_page = page_num
        self.update_pagination_controls()
        self.display_current_page()

def go_to_prev_page(self):
    """
    Go to previous page
    """
    if self.current_page > 1:
        self.go_to_page(self.current_page - 1)

def go_to_next_page(self):
    """
    Go to next page
    """
    if self.current_page < self.total_pages:
        self.go_to_page(self.current_page + 1)

def display_current_page(self):
    """
    Display current page of data in the table
    """
    start_idx = (self.current_page - 1) * self.records_per_page
    end_idx = min(start_idx + self.records_per_page, len(self.full_data))
    
    # Get the current page data
    current_page_data = self.full_data.iloc[start_idx:end_idx]
    
    # Clear the table
    self.report_table.clear()
    self.report_table.setRowCount(0)
    
    if current_page_data.empty:
        # Set up an empty table with message
        self.report_table.setColumnCount(1)
        self.report_table.setHorizontalHeaderLabels(["No data available"])
        return
    
    # Set column headers
    columns = current_page_data.columns.tolist()
    self.report_table.setColumnCount(len(columns))
    self.report_table.setHorizontalHeaderLabels(columns)
    
    # Populate data
    self.report_table.setRowCount(len(current_page_data))
    
    for row_idx, (_, row) in enumerate(current_page_data.iterrows()):
        for col_idx, col_name in enumerate(columns):
            value = str(row[col_name])
            item = QTableWidgetItem(value)
            self.report_table.setItem(row_idx, col_idx, item)
    
    # Auto-resize columns to content
    self.report_table.resizeColumnsToContents()
    
    # If the table is too wide, allow horizontal scrolling
    table_width = sum([self.report_table.columnWidth(i) for i in range(len(columns))])
    if table_width > self.report_table.width():
        self.report_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    else:
        self.report_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

def export_report(self):
    """
    Export the current report data to a CSV file
    """
    # Check if there's data to export
    if not hasattr(self, 'full_data') or self.full_data.empty:
        QMessageBox.information(self, "Export", "No data to export")
        return
    
    # Get the current report type for filename
    report_type = self.report_combo.currentText().replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"{report_type}_{timestamp}.csv"
    
    # Open file dialog
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        "Export to CSV",
        default_filename,
        "CSV Files (*.csv);;All Files (*)"
    )
    
    if file_path:
        try:
            # Export the full dataset, not just the current page
            self.full_data.to_csv(file_path, index=False)
            QMessageBox.information(self, "Export Successful", f"Report exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export report: {e}")

def refresh_report(self):
    """
    Refresh the current report with the same filters
    """
    # Remember current page
    current_page = self.current_page if hasattr(self, 'current_page') else 1
    
    # Re-apply the current filters to refresh the data
    self.apply_filters()
    
    # Try to go back to the previous page if possible
    if hasattr(self, 'total_pages') and current_page <= self.total_pages:
        self.go_to_page(current_page)
    
    # Show a brief status message
    status_bar = self.parent().statusBar()
    if status_bar:
        status_bar.showMessage("Report refreshed", 3000)  # Show for 3 seconds
