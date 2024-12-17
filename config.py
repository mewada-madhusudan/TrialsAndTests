import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QTabWidget, QWidget, QListWidget, 
    QListWidgetItem, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt

class FileMappingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Mapping Application")
        self.setGeometry(100, 100, 800, 600)

        # Constant mapping keys
        self.MAPPING_KEYS = [
            'Mapping1', 'Mapping2', 'Mapping3', 
            'Mapping4', 'Mapping5', 'Mapping6', 
            'Mapping7'
        ]

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Folder selection section
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No folder selected")
        select_folder_btn = QPushButton("Select Folder")
        select_folder_btn.clicked.connect(self.select_folder)
        
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(select_folder_btn)
        main_layout.addLayout(folder_layout)

        # Tabs for mappings
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Prepare tabs
        self.mapping_tabs = {}
        for key in self.MAPPING_KEYS:
            tab = QWidget()
            tab_layout = QVBoxLayout()
            
            # File selection group
            file_group = QGroupBox("Select Files")
            file_layout = QHBoxLayout()
            
            # Worksheet selection group
            worksheet_group = QGroupBox("Select Worksheets")
            worksheet_layout = QHBoxLayout()
            
            # File selection list
            file_list = QListWidget()
            file_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            
            # Worksheet selection list
            worksheet_list = QListWidget()
            worksheet_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            
            file_layout.addWidget(file_list)
            worksheet_layout.addWidget(worksheet_list)
            
            file_group.setLayout(file_layout)
            worksheet_group.setLayout(worksheet_layout)
            
            tab_layout.addWidget(file_group)
            tab_layout.addWidget(worksheet_group)
            
            tab.setLayout(tab_layout)
            
            self.mapping_tabs[key] = {
                'tab': tab,
                'file_list': file_list,
                'worksheet_list': worksheet_list
            }
            
            self.tab_widget.addTab(tab, key)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Store file and worksheet information
        self.files = []
        self.worksheets = {}

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            # Clear previous selections
            self.files.clear()
            self.worksheets.clear()
            
            # Get files (assuming Excel files)
            files = [f for f in os.listdir(folder_path) if f.endswith(('.xlsx', '.xls'))]
            
            if len(files) != 6:
                self.folder_label.setText(f"Please select a folder with exactly 6 files. Current: {len(files)}")
                return
            
            self.files = [os.path.join(folder_path, f) for f in files]
            self.folder_label.setText(f"Selected folder: {folder_path}\nFiles: {', '.join(files)}")
            
            # Populate file lists in tabs
            for key, tab_info in self.mapping_tabs.items():
                tab_info['file_list'].clear()
                tab_info['file_list'].addItems(files)
                
            # Extract worksheets (you'll need to implement this part)
            # This is a placeholder - you'd typically use a library like openpyxl or pandas
            self.extract_worksheets()

    def extract_worksheets(self):
        # Placeholder for worksheet extraction
        # In a real application, you'd use a library to read Excel files
        try:
            import pandas as pd
            
            self.worksheets.clear()
            for file in self.files:
                # Read Excel file and get sheet names
                xls = pd.ExcelFile(file)
                sheet_names = xls.sheet_names
                
                # Populate worksheet lists in tabs
                for key, tab_info in self.mapping_tabs.items():
                    tab_info['worksheet_list'].clear()
                    tab_info['worksheet_list'].addItems(sheet_names)
        
        except ImportError:
            print("pandas library is required. Please install it using 'pip install pandas'")
        except Exception as e:
            print(f"Error extracting worksheets: {e}")

def main():
    app = QApplication(sys.argv)
    main_window = FileMappingApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
