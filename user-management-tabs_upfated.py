def setup_user_management(self, users_container):
    users_layout = QVBoxLayout(users_container)
    users_layout.setContentsMargins(20, 20, 20, 20)

    # Title
    users_title = QLabel("Manage Users")
    users_title.setProperty("heading", True)
    users_layout.addWidget(users_title)

    # Tab widget
    tab_widget = QTabWidget()
    tab_widget.setStyleSheet("""
        QTabWidget::pane {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background: white;
            padding: 10px;
        }
        QTabBar::tab {
            background: #f5f5f5;
            border: 1px solid #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom-color: white;
        }
    """)

    # Existing Users Tab
    existing_users_tab = QWidget()
    existing_layout = QVBoxLayout(existing_users_tab)
    
    existing_label = QLabel("Select users to remove access:")
    existing_label.setProperty("subheading", True)
    existing_layout.addWidget(existing_label)

    self.existing_users_list = QListWidget()
    self.existing_users_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
    self.existing_users_list.setStyleSheet("""
        QListWidget {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            background: white;
        }
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        QListWidget::item:selected {
            background: #e3f2fd;
            color: #1976d2;
        }
    """)
    existing_layout.addWidget(self.existing_users_list)

    remove_btn = QPushButton("Remove Selected Users")
    remove_btn.setObjectName("actionButton")
    remove_btn.clicked.connect(self.remove_selected_users)
    existing_layout.addWidget(remove_btn)

    # Add Users Tab
    add_users_tab = QWidget()
    add_layout = QVBoxLayout(add_users_tab)
    
    add_label = QLabel("Enter user IDs (one per line):")
    add_label.setProperty("subheading", True)
    add_layout.addWidget(add_label)

    # Replace QTextEdit with QListWidget for consistent look
    self.new_users_list = QListWidget()
    self.new_users_list.setStyleSheet("""
        QListWidget {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            background: white;
        }
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f0f0f0;
        }
    """)
    add_layout.addWidget(self.new_users_list)

    # Add input field for single user
    input_layout = QHBoxLayout()
    self.user_input = QLineEdit()
    self.user_input.setPlaceholderText("Enter user ID")
    self.user_input.setStyleSheet("""
        QLineEdit {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            background: white;
        }
    """)
    input_layout.addWidget(self.user_input)

    add_single_btn = QPushButton("Add")
    add_single_btn.setObjectName("actionButton")
    add_single_btn.clicked.connect(self.add_single_user)
    input_layout.addWidget(add_single_btn)
    add_layout.addLayout(input_layout)

    # Add paste button
    paste_btn = QPushButton("Paste Multiple Users")
    paste_btn.setObjectName("actionButton")
    paste_btn.clicked.connect(self.paste_multiple_users)
    add_layout.addWidget(paste_btn)

    add_btn = QPushButton("Add All Users")
    add_btn.setObjectName("actionButton")
    add_btn.clicked.connect(self.add_multiple_users)
    add_layout.addWidget(add_btn)

    # Add tabs to widget
    tab_widget.addTab(existing_users_tab, "Existing Users")
    tab_widget.addTab(add_users_tab, "Add Users")
    users_layout.addWidget(tab_widget)

def add_single_user(self):
    user_id = self.user_input.text().strip()
    if user_id:
        self.new_users_list.addItem(user_id)
        self.user_input.clear()

def paste_multiple_users(self):
    clipboard = QApplication.clipboard()
    text = clipboard.text()
    if text:
        # Split by newlines and commas, then clean up
        for line in text.split('\n'):
            for uid in line.split(','):
                if uid.strip():
                    self.new_users_list.addItem(uid.strip())

def add_multiple_users(self):
    if not self.app_list.currentItem():
        QMessageBox.warning(self, "No Application Selected",
                          "Please select an application first.",
                          QMessageBox.StandardButton.Ok)
        return

    new_users_list = set()
    for i in range(self.new_users_list.count()):
        new_users_list.add(self.new_users_list.item(i).text())

    if not new_users_list:
        return

    app_name = self.app_list.currentItem().data(Qt.ItemDataRole.UserRole)
    app_idx = self.df[self.df['application_name'] == app_name].index[0]
    
    current_sids = set(self.df.at[app_idx, 'sids'].split(','))
    updated_sids = current_sids.union(new_users_list)
    
    self.df.at[app_idx, 'sids'] = ','.join(updated_sids)
    self.new_users_list.clear()
    self.show_application_users(self.app_list.currentItem())
    self.show_success_message(f"Successfully added {len(new_users_list)} new user(s)")
