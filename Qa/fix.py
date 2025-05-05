from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
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
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.setText(filename)
        # Set icon based on file type if needed
        # self.setIcon(QIcon("path/to/file_icon.png"))


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
    Dialog for managing PDF documents in knowledge bases
    """
    def __init__(self, llm_processor, parent=None):
        super().__init__(parent)
        self.llm_processor = llm_processor
        self.thread_pool = QThreadPool()
        self.document_widgets = {}  # Store widgets by doc_id for updates
        self.current_folder = None  # Current selected folder
        
        self.setWindowTitle("File Management")
        self.setMinimumSize(900, 600)
        
        self.setup_ui()
        self.load_folder_structure()
    
    def setup_ui(self):
        """Setup the dialog UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for folder tree and file list
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Folder tree panel (left side)
        folder_group = QGroupBox()
        folder_layout = QVBoxLayout(folder_group)
        
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.itemClicked.connect(self.on_folder_selected)
        folder_layout.addWidget(self.folder_tree)
        
        # Create sample root folders for demonstration
        self.create_sample_folders()
        
        splitter.addWidget(folder_group)
        
        # File list panel (right side)
        file_group = QGroupBox()
        file_layout = QVBoxLayout(file_group)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.file_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        file_layout.addWidget(self.file_list)
        
        splitter.addWidget(file_group)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 600])
        main_layout.addWidget(splitter)
        
        # Close button
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        main_layout.addLayout(buttons_layout)
    
    def create_sample_folders(self):
        """Create sample folder structure for demonstration"""
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
        """Load folder structure - in a real app, this would load actual folders"""
        # This is a placeholder - in a real application, you would load actual folders
        # For now, we're using the sample folders created in create_sample_folders
        pass
    
    def on_folder_selected(self, item, column):
        """Handle folder selection in tree"""
        if isinstance(item, FolderTreeItem):
            self.current_folder = item.path
            self.load_folder_files(item.path)
    
    def load_folder_files(self, folder_path):
        """Load files for selected folder"""
        # Clear previous file list
        self.file_list.clear()
        
        # In a real application, you would load actual files from the folder
        # For demonstration, we'll add some sample files based on the folder
        
        if folder_path == "Folder 1":
            # Add sample files for Folder 1
            self.file_list.addItem(FileListItem("FILE 1"))
            self.file_list.addItem(FileListItem("File 2"))
        elif folder_path:
            # For other folders, just add placeholder files
            self.file_list.addItem(FileListItem("Sample File 1.pdf"))
            self.file_list.addItem(FileListItem("Sample File 2.pdf"))


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
