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

class TableConfig:
    """Class to store table configuration information"""
    def __init__(self, name, display_name, columns, primary_key, excel_support=False):
        self.name = name  # Database table name
        self.display_name = display_name  # Display name in UI
        self.columns = columns  # List of tuples (column_name, display_name, data_type)
        self.primary_key = primary_key  # Primary key column name
        self.excel_support = excel_support  # Whether table supports Excel import/export

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('access_control.db')
        self.setup_table_configs()
        self.create_tables()

    def setup_table_configs(self):
        """Set up configurations for all tables"""
        self.table_configs = {
            "status_table": TableConfig(
                name="status_table",
                display_name="Status Table",
                columns=[
                    ("status_id", "Status ID", "TEXT"),
                    ("status_name", "Status Name", "TEXT"),
                    ("description", "Description", "TEXT")
                ],
                primary_key="status_id"
            ),
            "field_table": TableConfig(
                name="field_table",
                display_name="Field Table",
                columns=[
                    ("field_id", "Field ID", "TEXT"),
                    ("field_name", "Field Name", "TEXT"),
                    ("field_type", "Field Type", "TEXT")
                ],
                primary_key="field_id"
            ),
            "cost_center": TableConfig(
                name="cost_center",
                display_name="Cost Center",
                columns=[
                    ("center_id", "Center ID", "TEXT"),
                    ("center_name", "Center Name", "TEXT"),
                    ("description", "Description", "TEXT"),
                    ("department", "Department", "TEXT"),
                    ("budget_amount", "Budget Amount", "REAL")
                ],
                primary_key="center_id",
                excel_support=True
            ),
            # Example of adding another table with different column structure
            "user_table": TableConfig(
                name="user_table",
                display_name="User Table",
                columns=[
                    ("user_id", "User ID", "TEXT"),
                    ("username", "Username", "TEXT"),
                    ("email", "Email Address", "TEXT"),
                    ("role", "Role", "TEXT"),
                    ("access_level", "Access Level", "INTEGER"),
                    ("last_login", "Last Login", "TEXT")
                ],
                primary_key="user_id"
            )
        }

    def get_table_configs(self):
        """Return all table configurations"""
        return self.table_configs

    def get_table_names(self, category=None):
        """Get list of table names for a category"""
        if category == "STO":
            return ["status_table", "field_table"]
        elif category == "Admin":
            return ["cost_center", "user_table"]
        else:
            return list(self.table_configs.keys())

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Dynamically create all tables based on configurations
        for table_name, config in self.table_configs.items():
            # Build column definitions
            column_defs = [f"id INTEGER PRIMARY KEY AUTOINCREMENT"]
            for col_name, _, data_type in config.columns:
                column_defs.append(f"{col_name} {data_type} NOT NULL")
            
            # Add standard fields
            column_defs.extend([
                "is_active INTEGER DEFAULT 1",
                "created_date TEXT DEFAULT CURRENT_TIMESTAMP",
                "modified_date TEXT DEFAULT CURRENT_TIMESTAMP"
            ])
            
            # Create table
            create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            cursor.execute(create_stmt)
        
        self.conn.commit()

    def get_table_data(self, table_name):
        table_config = self.table_configs.get(table_name)
        if not table_config:
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
        table_config = self.table_configs.get(table_name)
        if not table_config:
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
                    if data_type == "REAL" and data[display_name]:
                        try:
                            values.append(float(data[display_name]))
                        except ValueError:
                            values.append(0.0)
                    elif data_type == "INTEGER" and data[display_name]:
                        try:
                            values.append(int(data[display_name]))
                        except ValueError:
                            values.append(0)
                    else:
                        values.append(data[display_name])
            
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
        table_config = self.table_configs.get(table_name)
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
        table_config = self.table_configs.get(table_name)
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
                    if data_type == "REAL" and data[display_name]:
                        try:
                            values.append(float(data[display_name]))
                        except ValueError:
                            values.append(0.0)
                    elif data_type == "INTEGER" and data[display_name]:
                        try:
                            values.append(int(data[display_name]))
                        except ValueError:
                            values.append(0)
                    else:
                        values.append(data[display_name])
            
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

    def import_from_excel(self, table_name, file_path):
        table_config = self.table_configs.get(table_name)
        if not table_config or not table_config.excel_support:
            return False, "Excel import not supported for this table"
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Map display names to DB column names
            display_to_db = {col[1]: col[0] for col in table_config.columns}
            db_to_type = {col[0]: col[2] for col in table_config.columns}
            
            cursor = self.conn.cursor()
            
            # Process each row
            success_count = 0
            for _, row in df.iterrows():
                # Prepare column names and values
                db_columns = []
                values = []
                
                for display_name, db_name in display_to_db.items():
                    if display_name in df.columns:
                        db_columns.append(db_name)
                        
                        # Handle data type conversion
                        value = row.get(display_name)
                        data_type = db_to_type.get(db_name)
                        
                        if data_type == "REAL" and pd.notna(value):
                            try:
                                values.append(float(value))
                            except (ValueError, TypeError):
                                values.append(0.0)
                        elif data_type == "INTEGER" and pd.notna(value):
                            try:
                                values.append(int(value))
                            except (ValueError, TypeError):
                                values.append(0)
                        else:
                            values.append(str(value) if pd.notna(value) else "")
                
                if db_columns:
                    # Insert into database
                    columns_str = ", ".join(db_columns)
                    placeholders = ", ".join(["?" for _ in db_columns])
                    
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    cursor.execute(sql, values)
                    success_count += 1
            
            self.conn.commit()
            return True, f"Successfully imported {success_count} records"
        except Exception as e:
            return False, f"Error importing from Excel: {e}"

    def export_to_excel(self, table_name, file_path):
        table_config = self.table_configs.get(table_name)
        if not table_config or not table_config.excel_support:
            return False, "Excel export not supported for this table"
        
        try:
            df = self.get_table_data(table_name)
            df.to_excel(file_path, index=False)
            return True, f"Successfully exported {len(df)} records to {file_path}"
        except Exception as e:
            return False, f"Error exporting to Excel: {e}"

class AddRecordDialog(QDialog):
    def __init__(self, table_config, parent=None):
        super().__init__(parent)
        self.table_config = table_config
        self.setWindowTitle(f"Add {table_config.display_name} Record")
        self.setMinimumWidth(400)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.form_layout = QFormLayout()
        
        # Create form fields based on table config
        self.fields = {}
        
        for _, display_name, data_type in self.table_config.columns:
            field = QLineEdit()
            
            # Set validators or special handling based on data type
            if data_type == "REAL":
                field.setPlaceholderText("0.00")
            elif data_type == "INTEGER":
                field.setPlaceholderText("0")
            
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
            data[field_name] = field.text()
        return data

class TablePanel(QWidget):
    def __init__(self, db_manager, table_name, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.table_name = table_name
        self.table_config = db_manager.get_table_configs().get(table_name)
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(f"{self.table_config.display_name} Management")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Table widget with simple styling
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
        dialog = AddRecordDialog(self.table_config, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if self.db_manager.add_record(self.table_name, data):
                QMessageBox.information(self, "Success", "Record added successfully!")
                self.load_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to add record.")
    
    def delete_record(self):
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
        if not self.table_config.excel_support:
            QMessageBox.warning(self, "Not Supported", "Excel import is not supported for this table.")
            return
            
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)"
            )
            
            if file_path:
                success, message = self.db_manager.import_from_excel(self.table_name, file_path)
                
                if success:
                    QMessageBox.information(self, "Import Successful", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Import Failed", message)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to import Excel file: {e}")
    
    def export_excel(self):
        if not self.table_config.excel_support:
            QMessageBox.warning(self, "Not Supported", "Excel export is not supported for this table.")
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Excel File", "", "Excel Files (*.xlsx)"
            )
            
            if file_path:
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                    
                success, message = self.db_manager.export_to_excel(self.table_name, file_path)
                
                if success:
                    QMessageBox.information(self, "Export Successful", message)
                else:
                    QMessageBox.warning(self, "Export Failed", message)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export Excel file: {e}")

class CategoryPanel(QWidget):
    def __init__(self, db_manager, category, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.category = category
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(f"{self.category} Management")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Table selection
        select_layout = QHBoxLayout()
        
        table_label = QLabel("Select Table:")
        self.table_combo = QComboBox()
        
        # Add tables for this category
        table_names = self.db_manager.get_table_names(self.category)
        for table_name in table_names:
            config = self.db_manager.get_table_configs().get(table_name)
            if config:
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

class AccessControlDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Access Control Management")
        self.setMinimumSize(1200, 700)
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        self.setup_ui()
        
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
        self.menu_list.addItems(["STO Management", "Admin Management"])
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
        
        # Add category panels
        self.sto_panel = CategoryPanel(self.db_manager, "STO")
        self.admin_panel = CategoryPanel(self.db_manager, "Admin")
        
        self.category_stack.addWidget(self.sto_panel)
        self.category_stack.addWidget(self.admin_panel)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        
        # Show first category
        self.menu_list.setCurrentRow(0)
    
    def change_category(self, index):
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
    
    dialog = AccessControlDialog()
    dialog.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
