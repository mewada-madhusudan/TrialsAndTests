def clear_filters(self):
    """Reset all filter dropdowns and date fields to their default values"""
    # Reset all comboboxes to the "ALL" option (first item)
    for child in self.filter_container.findChildren(QComboBox):
        child.setCurrentIndex(0)
    
    # Reset date fields to their default values
    for child in self.filter_container.findChildren(QDateEdit):
        if "from" in child.objectName().lower():
            # Set "from date" to 1 month ago
            child.setDate(QDate.currentDate().addMonths(-1))
        else:
            # Set "to date" to today
            child.setDate(QDate.currentDate())
    
    # Optional: Visual feedback that filters were cleared
    QMessageBox.information(self, "Filters Cleared", "All filters have been reset to default values.")

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
    
    # Add object name for identification during clear operation
    combo.setObjectName(f"filter_{label_text.lower().replace(' ', '_')}")
    
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
    from_date.setObjectName(f"from_date_{label_text.lower().replace(' ', '_')}")
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
    to_date.setObjectName(f"to_date_{label_text.lower().replace(' ', '_')}")
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
