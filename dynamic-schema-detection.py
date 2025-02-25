import json
import os
import sys
import sqlite3
from datetime import datetime

import pandas as pd
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QWidget, QStackedWidget,
                             QFrame, QScrollArea, QListWidget, QApplication, 
                             QMainWindow, QStatusBar, QComboBox, QFileDialog,
                             QFormLayout, QDialogButtonBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

class DatabaseManager:
    def __init__(self, db_path='access_control.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_sample_tables()  # Create sample tables if new database
        self.table_configs = {}      # Will be populated dynamically
    
    def get_database_tables(self):
        """Get list of all user tables in the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, table_name):
        """Get schema information for a table"""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()
    
    def get_table_config(self, table_name):
        """Dynamically generate table configuration based on database schema"""
        # Check if we've already cached this config
        if table_name in self.table_configs:
            return self.table_configs[table_name]
        
        # Get schema information
        schema_info = self.get_table_schema(table_name)
        
        # Build column information
        columns = []
        primary_key = None
        
        for col_info in schema_info:
            cid, name, type_name, notnull, default_value, pk = col_info
            
            # Skip auto-generated ID and standard fields
            if name in ('id', 'is_active', 'created_date', 'modified_date'):
                continue
            
            # Generate display name from column name (convert snake_case to Title Case)
            display_name = ' '.join(word.capitalize() for word in name.split('_'))
            
            # Add column to list
            columns.append((name, display_name, type_name))
            
            # Set primary key if this column is marked as PK
            if pk == 1:
                primary_key = name
        
        # If no explicit PK found in columns, use first column as implicit PK
        if not primary_key and columns:
            primary_key = columns[0][0]
        
        # Determine Excel support based on table name or other criteria
        # For example, enable for tables with "data" or "report" in the name
        excel_support = any(keyword in table_name.lower() 
                           for keyword in ['center', 'data', 'report', 'user'])
        
        # Create and cache the config
        config = TableConfig(
            name=table_name,
            display_name=self.generate_display_name(table_name),
            columns=columns,
            primary_key=primary_key,
            excel_support=excel_support
        )
        
        self.table_configs[table_name] = config
        return config
    
    def generate_display_name(self, table_name):
        """Generate a user-friendly display name from the table name"""
        # Convert snake_case to Title Case
        words = table_name.split('_')
        return ' '.join(word.capitalize() for word in words)
    
    def infer_field_type(self, column_name, data_type):
        """Infer proper field type for UI based on column name and data type"""
        column_lower = column_name.lower()
        
        # Check if it's a special field type based on name
        if any(keyword in column_lower for keyword in ['email', 'mail']):
            return 'email'
        elif any(keyword in column_lower for keyword in ['password', 'pwd']):
            return 'password'
        elif any(keyword in column_lower for keyword in ['date', 'time']):
            return 'datetime'
        elif any(keyword in column_lower for keyword in ['description', 'notes', 'comment']):
            return 'textarea'
        
        # Check based on data type
        if data_type in ('INTEGER', 'INT'):
            return 'integer'
        elif data_type in ('REAL', 'FLOAT', 'DOUBLE'):
            return 'float'
        elif data_type in ('BOOLEAN', 'BOOL'):
            return 'boolean'
        
        # Default to text
        return 'text'
    
    def get_table_data(self, table_name):
        """Get data from table dynamically without relying on predefined config"""
        # Get dynamic table configuration
        table_config = self.get_table_config(table_name)
        
        if not table_config.columns:
            return pd.DataFrame()
        
        cursor = self.conn.cursor()
        
        # Build columns for SELECT
        column_names = [col[0] for col in table_config.columns]
        columns_str = ", ".join(column_names)
        
        # Execute query
        cursor.execute(f"""
            SELECT {columns_str} 
            FROM {table_name} 
            WHERE is_active = 1
        """)
        
        rows = cursor.fetchall()
        columns = [col[1] for col in table_config.columns]  # Use display names
        
        return pd.DataFrame(rows, columns=columns)
    
    def add_record(self, table_name, data):
        """Add a record to the specified table"""
        table_config = self.get_table_config(table_name)
        if not table_config.columns:
            return False
        
        cursor = self.conn.cursor()
        try:
            # Prepare column names and placeholders
            column_names = []
            placeholders = []
            values = []
            
            for col_info in table_config.columns:
                db_col_name = col_info[0]  # Database column name
                display_name = col_info[1]  # Display name
                data_type = col_info[2]  # Data type
                
                if display_name in data:
                    column_names.append(db_col_name)
                    placeholders.append("?")
                    
                    # Convert value based on data type
                    value = data[display_name]
                    if data_type == "REAL" and value:
                        try:
                            values.append(float(value))
                        except ValueError:
                            values.append(0.0)
                    elif data_type in ("INTEGER", "INT") and value:
                        try:
                            values.append(int(value))
                        except ValueError:
                            values.append(0)
                    else:
                        values.append(value)
            
            # Execute INSERT
            columns_str = ", ".join(column_names)
            placeholders_str = ", ".join(placeholders)
            
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str})"
            cursor.execute(sql, values)
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding record: {e}")
            return False
    
    def soft_delete_record(self, table_name, identifier):
        """Soft delete a record (set is_active to 0)"""
        table_config = self.get_table_config(table_name)
        if not table_config:
            return False
        
        cursor = self.conn.cursor()
        try:
            # Get primary key
            primary_key = table_config.primary_key
            
            # Execute soft delete
            cursor.execute(f"""
                UPDATE {table_name} 
                SET is_active = 0, modified_date = CURRENT_TIMESTAMP
                WHERE {primary_key} = ?
            """, (identifier,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error soft deleting record: {e}")
            return False
    
    def update_record(self, table_name, identifier, data):
        """Update an existing record"""
        table_config = self.get_table_config(table_name)
        if not table_config:
            return False
        
        cursor = self.conn.cursor()
        try:
            # Prepare SET clause
            set_clauses = []
            values = []
            
            for col_info in table_config.columns:
                db_col_name = col_info[0]  # Database column name
                display_name = col_info[1]  # Display name
                data_type = col_info[2]  # Data type
                
                # Skip the primary key in updates
                if db_col_name == table_config.primary_key:
                    continue
                
                if display_name in data:
                    set_clauses.append(f"{db_col_name} = ?")
                    
                    # Convert value based on data type
                    value = data[display_name]
                    if data_type == "REAL" and value:
                        try:
                            values.append(float(value))
                        except ValueError:
                            values.append(0.0)
                    elif data_type in ("INTEGER", "INT") and value:
                        try:
                            values.append(int(value))
                        except ValueError:
                            values.append(0)
                    else:
                        values.append(value)
            
            # Add timestamp for modification
            set_clauses.append("modified_date = CURRENT_TIMESTAMP")
            
            # Add identifier for WHERE clause
            values.append(identifier)
            
            # Execute UPDATE
            set_str = ", ".join(set_clauses)
            primary_key = table_config.primary_key
            
            sql = f"""
                UPDATE {table_name} 
                SET {set_str}
                WHERE {primary_key} = ? AND is_active = 1
            """
            cursor.execute(sql, values)
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False
    
    def create_sample_tables(self):
        """Create some sample tables if database is empty"""
        cursor = self.conn.cursor()
        
        # Check if tables already exist
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        count = cursor.fetchone()[0]
        
        if count > 0:
            return  # Tables already exist
        
        # Create some sample tables with standard fields
        sample_tables = [
            ("status_table", [
                "status_id TEXT NOT NULL",
                "status_name TEXT NOT NULL",
                "description TEXT"
            ]),
            ("field_table", [
                "field_id TEXT NOT NULL",
                "field_name TEXT NOT NULL",
                "field_type TEXT"
            ]),
            ("cost_center", [
                "center_id TEXT NOT NULL",
                "center_name TEXT NOT NULL",
                "description TEXT",
                "department TEXT",
                "budget_amount REAL"
            ]),
            ("user_table", [
                "user_id TEXT NOT NULL",
                "username TEXT NOT NULL",
                "email TEXT",
                "role TEXT",
                "access_level INTEGER",
                "last_login TEXT"
            ]),
            # Add more sample tables as needed
        ]
        
        # Create each table
        for table_name, columns in sample_tables:
            # Add standard fields
            all_columns = [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                *columns,
                "is_active INTEGER DEFAULT 1",
                "created_date TEXT DEFAULT CURRENT_TIMESTAMP",
                "modified_date TEXT DEFAULT CURRENT_TIMESTAMP"
            ]
            
            # Create table
            create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(all_columns)})"
            cursor.execute(create_stmt)
        
        self.conn.commit()

# The TableConfig class remains the same
class TableConfig:
    """Class to store table configuration information"""
    def __init__(self, name, display_name, columns, primary_key, excel_support=False):
        self.name = name  # Database table name
        self.display_name = display_name  # Display name in UI
        self.columns = columns  # List of tuples (column_name, display_name, data_type)
        self.primary_key = primary_key  # Primary key column name
        self.excel_support = excel_support  # Whether table supports Excel import/export

class DynamicAddRecordDialog(QDialog):
    def __init__(self, db_manager, table_name, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.table_name = table_name
        self.table_config = db_manager.get_table_config(table_name)
        
        self.setWindowTitle(f"Add {self.table_config.display_name} Record")
        self.setMinimumWidth(400)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.form_layout = QFormLayout()
        
        # Create form fields based on table config
        self.fields = {}
        
        for col_name, display_name, data_type in self.table_config.columns:
            # Infer field type
            field_type = self.db_manager.infer_field_type(col_name, data_type)
            
            # Create appropriate field widget
            if field_type == 'password':
                field = QLineEdit()
                field.setEchoMode(QLineEdit.EchoMode.Password)
            elif field_type == 'textarea':
                field = QLineEdit()  # Could use QTextEdit for multiline
                field.setMinimumWidth(300)
            elif field_type == 'integer':
                field = QLineEdit()
                field.setPlaceholderText("0")
            elif field_type == 'float':
                field = QLineEdit()
                field.setPlaceholderText("0.00")
            elif field_type == 'boolean':
                field = QComboBox()
                field.addItems(["True", "False"])
            elif field_type == 'email':
                field = QLineEdit()
                field.setPlaceholderText("example@domain.com")
            elif field_type == 'datetime':
                field = QLineEdit()
                field.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
            else:  # Default to text
                field = QLineEdit()
            
            self.fields[display_name] = field
            self.form_layout.addRow(f"{display_name}:", field)
        
        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(self.button_box)
        
    def get_data(self):
        data = {}
        for field_name, field in self.fields.items():
            if isinstance(field, QComboBox):
                data[field_name] = field.currentText()
            else:
                data[field_name] = field.text()
        return data

class TablePanel(QWidget):
    def __init__(self, db_manager, table_name, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.table_name = table_name
        self.table_config = db_manager.get_table_config(table_name)
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(f"{self.table_config.display_name} Management")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.setStyleSheet("""
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
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        layout.addWidget(self.table_widget)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Record")
        delete_btn = QPushButton("Delete Selected")
        save_btn = QPushButton("Save Changes")
        
        add_btn.clicked.connect(self.add_record)
        delete_btn.clicked.connect(self.delete_record)
        save_btn.clicked.connect(self.save_changes)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(save_btn)
        
        # Add Excel buttons if supported
        if self.table_config.excel_support:
            import_excel_btn = QPushButton("Import from Excel")
            export_excel_btn = QPushButton("Export to Excel")
            
            import_excel_btn.clicked.connect(self.import_excel)
            export_excel_btn.clicked.connect(self.export_excel)
            
            button_layout.addWidget(import_excel_btn)
            button_layout.addWidget(export_excel_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def load_data(self):
        # Get data from database
        df = self.db_manager.get_table_data(self.table_name)
        
        # Set up table
        self.table_widget.setRowCount(len(df))
        self.table_widget.setColumnCount(len(df.columns))
        self.table_widget.setHorizontalHeaderLabels(df.columns)
        
        # Populate table
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.table_widget.setItem(i, j, item)
        
        # Adjust columns to content
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_widget.horizontalHeader().setMinimumSectionSize(100)
    
    def add_record(self):
        dialog = DynamicAddRecordDialog(self.db_manager, self.table_name, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if self.db_manager.add_record(self.table_name, data):
                QMessageBox.information(self, "Success", "Record added successfully!")
                self.load_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to add record.")
    
    def delete_record(self):
        # Implementation remains similar
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a row to delete.")
            return
            
        reply = QMessageBox.question(self, "Confirm Deletion",
                                   "Are you sure you want to delete the selected row(s)?",
                                   QMessageBox.StandardButton.Yes |
                                   QMessageBox.StandardButton.No)
                                   
        if reply == QMessageBox.StandardButton.Yes:
            # Get primary key column index
            pk_display_name = None
            for _, display_name, _ in self.table_config.columns:
                if self.table_config.primary_key == _:
                    pk_display_name = display_name
                    break
                    
            if not pk_display_name:
                QMessageBox.warning(self, "Error", "Could not determine primary key column.")
                return
                
            # Find primary key column index
            pk_index = -1
            for i in range(self.table_widget.columnCount()):
                if self.table_widget.horizontalHeaderItem(i).text() == pk_display_name:
                    pk_index = i
                    break
            
            if pk_index == -1:
                QMessageBox.warning(self, "Error", "Primary key column not found in table.")
                return
            
            # Get unique rows to delete
            rows_to_delete = set()
            for item in selected_items:
                rows_to_delete.add(item.row())
            
            # Delete records
            for row in sorted(rows_to_delete, reverse=True):
                identifier = self.table_widget.item(row, pk_index).text()
                if self.db_manager.soft_delete_record(self.table_name, identifier):
                    self.table_widget.removeRow(row)
            
            QMessageBox.information(self, "Success", "Selected records deleted successfully!")
    
    def save_changes(self):
        # Implementation remains similar
        try:
            rows = self.table_widget.rowCount()
            cols = self.table_widget.columnCount()
            
            # Get column headers
            headers = [self.table_widget.horizontalHeaderItem(i).text() 
                      for i in range(cols)]
            
            # Find primary key column index
            pk_display_name = None
            for _, display_name, _ in self.table_config.columns:
                if self.table_config.primary_key == _:
                    pk_display_name = display_name
                    break
                    
            if not pk_display_name or pk_display_name not in headers:
                QMessageBox.warning(self, "Error", "Primary key column not found.")
                return
                
            pk_index = headers.index(pk_display_name)
            
            # Save each row
            for row in range(rows):
                row_data = {}
                for col in range(cols):
                    item = self.table_widget.item(row, col)
                    row_data[headers[col]] = item.text() if item else ""
                
                # Update or insert based on whether it has valid ID
                identifier = row_data[headers[pk_index]]  # Primary key value
                if not identifier:
                    continue  # Skip empty rows
                    
                # Check if row exists in database
                existing_data = self.db_manager.get_table_data(self.table_name)
                existing_ids = existing_data[headers[pk_index]].tolist() if not existing_data.empty else []
                
                if identifier in existing_ids:
                    self.db_manager.update_record(self.table_name, identifier, row_data)
                else:
                    self.db_manager.add_record(self.table_name, row_data)
            
            QMessageBox.information(self, "Success", 
                                  "Changes saved successfully!",
                                  QMessageBox.StandardButton.Ok)
                                  
            # Refresh the table
            self.load_data()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save changes: {e}")
    
    def import_excel(self):
        # Implementation for Excel import would be similar but use the dynamic table config
        pass
    
    def export_excel(self):
        # Implementation for Excel export would be similar but use the dynamic table config
        pass

class CategoryPanel(QWidget):
    def __init__(self, db_manager, category_tables, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.category_tables = category_tables
        self.category_name = self.get_category_name()
        
        self.setup_ui()
        
    def get_category_name(self):
        # Generate a friendly name based on the tables in this category
        if any('status' in table.lower() for table in self.category_tables):
            return "Status Management"
        elif any('user' in table.lower() for table in self.category_tables):
            return "User Administration"
        elif any('cost' in table.lower() for table in self.category_tables):
            return "Cost Management"
        else:
            return "Table Administration"
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(self.category_name)
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Table selection
        select_layout = QHBoxLayout()
        
        table_label = QLabel("Select Table:")
        self.table_combo = QComboBox()
        
        # Add tables for this category
        for table_name in self.category_tables:
            config = self.db_manager.get_table_config(table_name)
            self.table_combo.addItem(config.display_name, table_name)
        
        self.table_combo.currentIndexChanged.connect(self.change_table)
        
        select_layout.addWidget(table_label)
        select_layout.addWidget(self.table_combo)
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # Stacked widget for tables
        self.table_stack = QStackedWidget()
        layout.addWidget(self.table_stack)
        
        # Add table panels
        for i in range(self.table_combo.count()):
            table_name = self.table_combo.itemData(i)
            table_panel = TablePanel(self.db_manager, table_name)
            self.table_stack.addWidget(table_panel)
        
        # Show first table
        if self.table_combo.count() > 0:
            self.table_stack.setCurrentIndex(0)
    
    def change_table(self, index):
        if index >= 0:
            self.table_stack.setCurrentIndex(index)
            
            # Refresh data in current table
            current_panel = self.table_stack.currentWidget()
            if current_panel:
                current_panel.load_data()

class DynamicAccessControlDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dynamic Access Control Management")
        self.setMinimumSize(1200, 700)
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Get all tables and categorize them
        self.categorize_tables()
        
        self.setup_ui()
        
    def categorize_tables(self):
        """Categorize tables into logical groups based on their names or structures"""
        all_tables = self.db_manager.get_database_tables()
        
        # Create categories based on table name patterns
        self.categories = {}
        
        for table in all_tables:
            if 'status' in table.lower() or 'field' in table.lower():
                category = "Status Management"
            elif 'user' in table.lower() or 'role' in table.lower() or 'permission' in table.lower():
                category = "User Management"
            elif 'cost' in table.lower() or 'budget' in table.lower() or 'finance' in table.lower():
                category = "Financial"
            else:
                category = "Other Tables"
                
            if category not in self.categories:
                self.categories[category] = []
            
            self.categories[category].append(table)
    
    def setup_ui(self):
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Left sidebar
        left_panel = QFrame()
        left_panel.setMaximumWidth(250)
        left_panel.setStyleSheet("background-color: #f5f5f5;")
        left_layout = QVBoxLayout(left_panel)
        
        # Menu items
        self.menu_list = QListWidget()
        # Add categories to menu
        for category in self.categories.keys():
            self.menu_list.addItem(category)
            
        self.menu_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            QListWidget::item:selected {
                background-color: #e0e0e0;
            }
        """)
        self.menu_list.currentRowChanged.connect(self.change_category)
        left_layout.addWidget(self.menu_list)
        
        # Right content area
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        # Stacked widget for different categories
        self.category_stack = QStackedWidget()
        right_layout.addWidget(self.category_stack)
        
        # Add category panels dynamically
        for category, tables in self.categories.items():
            category_panel = CategoryPanel(self.db_manager, tables)
            self.category_stack.addWidget(category_panel)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        
        # Show first category
        if self.menu_list.count() > 0:
            self.menu_list.setCurrentRow(0)
    
    def change_category(self, index):
        if 0 <= index < self.category_stack.count():
            self.category_stack.setCurrentIndex(index)

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Apply global stylesheet
    app.setStyleSheet("""
        QLabel[heading="true"] {
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0;
        }
        QPushButton {
            padding: 6px 12px;
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QLineEdit, QComboBox {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
    """)
    
    dialog = DynamicAccessControlDialog()
    dialog.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
