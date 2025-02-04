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

    self.new_users_text = QTextEdit()
    self.new_users_text.setPlaceholderText("Paste multiple IDs or enter one per line")
    self.new_users_text.setStyleSheet("""
        QTextEdit {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            background: white;
        }
    """)
    add_layout.addWidget(self.new_users_text)

    add_btn = QPushButton("Add Users")
    add_btn.setObjectName("actionButton")
    add_btn.clicked.connect(self.add_multiple_users)
    add_layout.addWidget(add_btn)

    # Add tabs to widget
    tab_widget.addTab(existing_users_tab, "Existing Users")
    tab_widget.addTab(add_users_tab, "Add Users")
    users_layout.addWidget(tab_widget)

def show_application_users(self, current_item):
    if not current_item:
        return

    self.existing_users_list.clear()
    app_name = current_item.data(Qt.ItemDataRole.UserRole)
    app_data = self.df[self.df['application_name'] == app_name].iloc[0]
    users = app_data['sids'].split(',')
    
    for user in users:
        if user.strip():
            self.existing_users_list.addItem(user.strip())

def remove_selected_users(self):
    if not self.app_list.currentItem():
        QMessageBox.warning(self, "No Application Selected",
                          "Please select an application first.",
                          QMessageBox.StandardButton.Ok)
        return

    selected_items = self.existing_users_list.selectedItems()
    if not selected_items:
        return

    users_to_remove = [item.text() for item in selected_items]
    app_name = self.app_list.currentItem().data(Qt.ItemDataRole.UserRole)
    
    reply = QMessageBox.question(self, "Confirm Removal",
                               f"Are you sure you want to remove {len(users_to_remove)} user(s)?",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
    if reply == QMessageBox.StandardButton.Yes:
        app_idx = self.df[self.df['application_name'] == app_name].index[0]
        current_sids = set(self.df.at[app_idx, 'sids'].split(','))
        updated_sids = current_sids - set(users_to_remove)
        self.df.at[app_idx, 'sids'] = ','.join(updated_sids)
        self.show_application_users(self.app_list.currentItem())
        self.show_success_message(f"Successfully removed {len(users_to_remove)} user(s)")

def add_multiple_users(self):
    if not self.app_list.currentItem():
        QMessageBox.warning(self, "No Application Selected",
                          "Please select an application first.",
                          QMessageBox.StandardButton.Ok)
        return

    new_users = self.new_users_text.toPlainText().strip()
    if not new_users:
        return

    app_name = self.app_list.currentItem().data(Qt.ItemDataRole.UserRole)
    app_idx = self.df[self.df['application_name'] == app_name].index[0]
    
    # Split by newlines and commas, then clean up
    new_users_list = set()
    for line in new_users.split('\n'):
        new_users_list.update(uid.strip() for uid in line.split(',') if uid.strip())

    current_sids = set(self.df.at[app_idx, 'sids'].split(','))
    updated_sids = current_sids.union(new_users_list)
    
    self.df.at[app_idx, 'sids'] = ','.join(updated_sids)
    self.new_users_text.clear()
    self.show_application_users(self.app_list.currentItem())
    self.show_success_message(f"Successfully added {len(new_users_list)} new user(s)")
