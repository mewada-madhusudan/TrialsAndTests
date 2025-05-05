def on_file_double_clicked(self, item):
        """Handle double-click on a file item"""
        if isinstance(item, FileListItem) and item.file_path:
            try:
                # Try to open the file with the default application
                import subprocess
                import platform
                
                system = platform.system()
                if system == 'Windows':
                    os.startfile(item.file_path)
                elif system == 'Darwin':  # macOS
                    subprocess.call(('open', item.file_path))
                else:  # Linux and other Unix-like
                    subprocess.call(('xdg-open', item.file_path))
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
    
    def on_add_file_clicked(self):
        """Handle add file button click"""
        if not self.current_folder or not os.path.isdir(self.current_folder):
            QMessageBox.information(self, "No Folder Selected", "Please select a folder first.")
            return
            
        # Open file selection dialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Add", "", "All Files (*.*)"
        )
        
        if not files:
            return
            
        # Copy files to current folder
        import shutil
        copied_count = 0
        
        for file_path in files:
            try:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.current_folder, filename)
                
                # Check if file already exists
                if os.path.exists(dest_path):
                    result = QMessageBox.question(
                        self, "File Exists",
                        f"File {filename} already exists. Overwrite?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if result == QMessageBox.StandardButton.No:
                        continue
                
                # Copy the file
                shutil.copy2(file_path, dest_path)
                copied_count += 1
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error copying file {filename}: {str(e)}")
        
        # Refresh file list
        if copied_count > 0:
            self.load_folder_files(self.current_folder)
            QMessageBox.information(self, "Files Added", f"Successfully added {copied_count} file(s).")
    
    def on_add_folder_clicked(self):
        """Handle add subfolder button click"""
        if not self.current_folder or not os.path.isdir(self.current_folder):
            QMessageBox.information(self, "No Folder Selected", "Please select a parent folder first.")
            return
            
        # Ask for folder name
        folder_name, ok = QInputDialog.getText(self, "Add Folder", "Folder Name:")
        
        if not ok or not folder_name:
            return
            
        # Create subfolder
        try:
            new_folder_path = os.path.join(self.current_folder, folder_name)
            
            # Check if folder already exists
            if os.path.exists(new_folder_path):
                QMessageBox.warning(self, "Folder Exists", f"Folder {folder_name} already exists.")
                return
                
            # Create the folder
            os.makedirs(new_folder_path)
            
            # Refresh folder tree
            self.load_folder_structure()
            
            QMessageBox.information(self, "Folder Created", f"Successfully created folder {folder_name}.")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error creating folder: {str(e)}")from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QListWidget, QListWidgetItem, QProgressBar, QCheckBox,
                             QMessageBox, QWidget, QGroupBox, QScrollArea, QFormLayout,
                             QTreeWidget, QTreeWidgetItem, QSplitter, QMenu)
from PyQt6.QtCore import Qt, QSize, QThreadPool
from PyQt6.QtGui import QIcon, QColor
from pdf_conversion_worker import PDFConversionWorker, BatchConversionWorker
import os

class DocumentListItem(QWidget):
    """
    Custom widget for displaying document with status in a list
    """
    def __init__(self, doc_data, parent=None):
        super().__init__(parent)
        self.doc_id = doc_data["id"]
        self.doc_data = doc_data
        
        # Main layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Document info layout
        info_layout = QVBoxLayout()
        
        # Document name
        self.name_label = QLabel(doc_data["original_filename"])
        self.name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.name_label)
        
        # Status info
        status_layout = QHBoxLayout()
        
        status_text = doc_data["conversion_status"].replace("_", " ").title()
        status_color = self._get_status_color(doc_data["conversion_status"])
        
        self.status_label = QLabel(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"color: {status_color}")
        status_layout.addWidget(self.status_label)
        
        # Add page count if available
        if doc_data["page_count"] and doc_data["page_count"] > 0:
            self.pages_label = QLabel(f"Pages: {doc_data['page_count']}")
            status_layout.addWidget(self.pages_label)
        
        info_layout.addLayout(status_layout)
        
        # Add progress bar for conversion
        if doc_data["is_scanned"] and doc_data["conversion_status"] in ["pending", "in_progress"]:
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(int(doc_data["conversion_progress"] or 0))
            info_layout.addWidget(self.progress_bar)
        
        self.layout.addLayout(info_layout)
        
        # Add convert button for scanned documents that need conversion
        if doc_data["is_scanned"] and doc_data["conversion_status"] in ["pending", "failed"]:
            self.convert_btn = QPushButton("Convert")
            self.convert_btn.clicked.connect(self.on_convert_clicked)
            self.layout.addWidget(self.convert_btn)
        
        # Add spacer to push content to the left
        self.layout.addStretch()
    
    def _get_status_color(self, status):
        """Get appropriate color for status text"""
        status_colors = {
            "pending": "#FF9800",  # Orange
            "in_progress": "#2196F3",  # Blue
            "completed": "#4CAF50",  # Green
            "failed": "#F44336",  # Red
            "not_required": "#9E9E9E"  # Gray
        }
        return status_colors.get(status, "#000000")
    
    def update_progress(self, progress):
        """Update progress bar value"""
        if hasattr(self, "progress_bar"):
            self.progress_bar.setValue(int(progress))
    
    def update_status(self, status, progress=None):
        """Update status label and progress"""
        status_text = status.replace("_", " ").title()
        status_color = self._get_status_color(status)
        self.status_label.setText(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"color: {status_color}")
        
        if progress is not None and hasattr(self, "progress_bar"):
            self.progress_bar.setValue(int(progress))
    
    def on_convert_clicked(self):
        """Handle convert button click"""
        # This will be connected to the parent dialog's convert method
        pass


class FileListItem(QListWidgetItem):
    """Custom list widget item for files"""
    def __init__(self, filename, file_path=None, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.file_path = file_path
        self.setText(filename)
        
        # Set icon based on file extension if needed
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx']:
            # Here you would set specific icons based on file type
            # For now we'll just use the filetype as part of the display
            self.setText(f"{filename} [{file_ext[1:]}]")


class FolderTreeItem(QTreeWidgetItem):
    """Custom tree widget item for folders"""
    def __init__(self, path, is_root=False, parent=None):
        super().__init__(parent)
        self.path = path
        self.folder_name = os.path.basename(path) if path else "Root"
        self.setText(0, self.folder_name.upper() if is_root else self.folder_name)
        self.doc_count = 0
        self.pending_count = 0
        self.is_root = is_root
        
        # Make root folders bold
        if is_root:
            font = self.font(0)
            font.setBold(True)
            self.setFont(0, font)
            
        self.setCheckState(0, Qt.CheckState.Unchecked)
        
    def update_counts(self, doc_count, pending_count):
        """Update document counts and display"""
        self.doc_count = doc_count
        self.pending_count = pending_count
        
        # Root folder shows subfolders count instead of documents
        if self.is_root:
            child_count = self.childCount()
            # Keep original name without counts for root folders
            self.setText(0, f"{self.folder_name}")
            self.setForeground(0, QColor("#000000"))  # Default color
        elif pending_count > 0:
            self.setText(0, f"{self.folder_name}")
            self.setForeground(0, QColor("#000000"))  # Default color
        else:
            self.setText(0, f"{self.folder_name}")
            self.setForeground(0, QColor("#000000"))  # Default color


class PDFManagementDialog(QDialog):
    """
    Dialog for managing file system structure
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool()
        self.current_folder = None  # Current selected folder
        self.root_folder_path = None  # Root folder path
        
        self.setWindowTitle("File Management")
        self.setMinimumSize(900, 600)
        
        self.setup_ui()
        self.load_folder_structure()
    
    def setup_ui(self):
        """Setup the dialog UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Button to select root folder
        select_folder_layout = QHBoxLayout()
        self.select_folder_btn = QPushButton("Select Root Folder")
        self.select_folder_btn.clicked.connect(self.select_root_folder)
        select_folder_layout.addWidget(self.select_folder_btn)
        select_folder_layout.addStretch()
        main_layout.addLayout(select_folder_layout)
        
        # Create splitter for folder tree and file list
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Folder tree panel (left side)
        folder_group = QGroupBox()
        folder_layout = QVBoxLayout(folder_group)
        
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.itemClicked.connect(self.on_folder_selected)
        folder_layout.addWidget(self.folder_tree)
        
        # Create sample root folders for demonstration initially
        self.create_sample_folders()
        
        splitter.addWidget(folder_group)
        
        # File list panel (right side)
        file_group = QGroupBox()
        file_layout = QVBoxLayout(file_group)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.file_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        file_layout.addWidget(self.file_list)
        
        splitter.addWidget(file_group)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 600])
        main_layout.addWidget(splitter)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add file button
        self.add_file_btn = QPushButton("Add File")
        self.add_file_btn.clicked.connect(self.on_add_file_clicked)
        buttons_layout.addWidget(self.add_file_btn)
        
        # Add folder button
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.on_add_folder_clicked)
        buttons_layout.addWidget(self.add_folder_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_folder_structure)
        buttons_layout.addWidget(self.refresh_btn)
        
        buttons_layout.addStretch()
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def select_root_folder(self):
        """Allow user to select a root folder to browse"""
        root_folder = QFileDialog.getExistingDirectory(
            self, "Select Root Folder", ""
        )
        
        if not root_folder or not os.path.isdir(root_folder):
            return
            
        self.root_folder_path = root_folder
        self.load_folder_structure()
    
    def create_sample_folders(self):
        """Create sample folder structure if no folder is selected"""
        # Clear previous tree
        self.folder_tree.clear()
        
        # Create three root folders as shown in the image
        folder1 = FolderTreeItem("Folder 1", is_root=True)
        folder2 = FolderTreeItem("Folder 2", is_root=True)
        folder3 = FolderTreeItem("Folder 3", is_root=True)
        
        # Add root folders to tree
        self.folder_tree.addTopLevelItem(folder1)
        self.folder_tree.addTopLevelItem(folder2)
        self.folder_tree.addTopLevelItem(folder3)
    
    def load_folder_structure(self):
        """Load actual folder structure from filesystem"""
        # Clear previous tree
        self.folder_tree.clear()
        
        if not hasattr(self, 'root_folder_path') or not self.root_folder_path:
            # If no root folder selected, use sample folders
            self.create_sample_folders()
            return
            
        # Get top-level folders in the root folder
        try:
            folders = [f for f in os.listdir(self.root_folder_path) 
                      if os.path.isdir(os.path.join(self.root_folder_path, f))]
            
            # Create tree items for each folder
            for folder_name in sorted(folders):
                folder_path = os.path.join(self.root_folder_path, folder_name)
                folder_item = FolderTreeItem(folder_path, is_root=True)
                self.folder_tree.addTopLevelItem(folder_item)
                
                # Recursively add subfolders
                self.add_subfolders(folder_item, folder_path)
                
            # Add files directly in the root folder
            self.root_item = FolderTreeItem(self.root_folder_path, is_root=True)
            self.root_item.setText(0, "ROOT")
            self.folder_tree.addTopLevelItem(self.root_item)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading folder structure: {str(e)}")
    
    def add_subfolders(self, parent_item, parent_path):
        """Recursively add subfolders to the tree"""
        try:
            subfolders = [f for f in os.listdir(parent_path) 
                         if os.path.isdir(os.path.join(parent_path, f))]
            
            for subfolder in sorted(subfolders):
                subfolder_path = os.path.join(parent_path, subfolder)
                subfolder_item = FolderTreeItem(subfolder_path, parent=parent_item)
                
                # Recursively add sub-subfolders
                self.add_subfolders(subfolder_item, subfolder_path)
        except Exception as e:
            # Just skip problematic folders
            pass
    
    def on_folder_selected(self, item, column):
        """Handle folder selection in tree"""
        if isinstance(item, FolderTreeItem):
            self.current_folder = item.path
            self.load_folder_files(item.path)
    
    def load_folder_files(self, folder_path):
        """Load actual files from the selected folder"""
        # Clear previous file list
        self.file_list.clear()
        
        if not folder_path or not os.path.isdir(folder_path):
            return
            
        try:
            # Get all files in the folder (not directories)
            files = [f for f in os.listdir(folder_path) 
                   if os.path.isfile(os.path.join(folder_path, f))]
            
            # Add files to the list
            for filename in sorted(files):
                file_path = os.path.join(folder_path, filename)
                file_item = FileListItem(filename, file_path)
                self.file_list.addItem(file_item)
            
            # Update window title to show current folder
            folder_name = os.path.basename(folder_path)
            self.setWindowTitle(f"File Management - {folder_name}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading files: {str(e)}")


class QComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)


class QInputDialog:
    @staticmethod
    def getText(parent, title, label):
        from PyQt6.QtWidgets import QInputDialog
        return QInputDialog.getText(parent, title, label)


class QFileDialog:
    @staticmethod
    def getOpenFileNames(parent, caption, directory, filter):
        from PyQt6.QtWidgets import QFileDialog
        return QFileDialog.getOpenFileNames(parent, caption, directory, filter)
        
    @staticmethod
    def getExistingDirectory(parent, caption, directory):
        from PyQt6.QtWidgets import QFileDialog
        return QFileDialog.getExistingDirectory(parent, caption, directory)


class QProgressDialog:
    def __init__(self, labelText, cancelButtonText, minimum, maximum, parent=None):
        from PyQt6.QtWidgets import QProgressDialog
        self.dialog = QProgressDialog(labelText, cancelButtonText, minimum, maximum, parent)
    
    def setWindowModality(self, modality):
        self.dialog.setWindowModality(modality)
    
    def show(self):
        self.dialog.show()
    
    def close(self):
        self.dialog.close()
    
    def setValue(self, value):
        self.dialog.setValue(value)
    
    def wasCanceled(self):
        return self.dialog.wasCanceled()
