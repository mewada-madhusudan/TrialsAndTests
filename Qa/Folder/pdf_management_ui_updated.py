from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QListWidget, QListWidgetItem, QProgressBar, QCheckBox,
                             QMessageBox, QWidget, QGroupBox, QScrollArea, QFormLayout,
                             QComboBox, QInputDialog, QFileDialog)
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


class FolderConversionItem(QWidget):
    """
    Custom widget for displaying folder with conversion status in a list
    """
    def __init__(self, folder_data, parent=None):
        super().__init__(parent)
        self.folder_id = folder_data["id"]
        self.folder_data = folder_data
        
        # Main layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Folder info layout
        info_layout = QVBoxLayout()
        
        # Folder name
        self.name_label = QLabel(folder_data["folder_name"])
        self.name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.name_label)
        
        # Status info
        status_layout = QHBoxLayout()
        
        status_text = folder_data["conversion_status"].replace("_", " ").title()
        status_color = self._get_status_color(folder_data["conversion_status"])
        
        self.status_label = QLabel(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"color: {status_color}")
        status_layout.addWidget(self.status_label)
        
        # Add file count if available
        if folder_data.get("file_count", 0) > 0:
            self.files_label = QLabel(f"Files: {folder_data['file_count']}")
            status_layout.addWidget(self.files_label)
            
            # Add processed files if in progress
            if folder_data["conversion_status"] == "in_progress":
                processed = folder_data.get("processed_files", 0)
                self.processed_label = QLabel(f"Processed: {processed}/{folder_data['file_count']}")
                status_layout.addWidget(self.processed_label)
        
        info_layout.addLayout(status_layout)
        
        # Add progress bar for conversion
        if folder_data["conversion_status"] in ["pending", "in_progress"]:
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(int(folder_data.get("conversion_progress", 0) or 0))
            info_layout.addWidget(self.progress_bar)
        
        self.layout.addLayout(info_layout)
        
        # Add convert button for folders that need conversion
        if folder_data["conversion_status"] in ["pending", "failed"]:
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
    
    def update_progress(self, progress, processed_files=None, total_files=None):
        """Update progress bar value and processed files count"""
        if hasattr(self, "progress_bar"):
            self.progress_bar.setValue(int(progress))
            
        if processed_files is not None and total_files is not None and hasattr(self, "processed_label"):
            self.processed_label.setText(f"Processed: {processed_files}/{total_files}")
    
    def update_status(self, status, progress=None, processed_files=None, total_files=None):
        """Update status label and progress"""
        status_text = status.replace("_", " ").title()
        status_color = self._get_status_color(status)
        self.status_label.setText(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"color: {status_color}")
        
        if progress is not None and hasattr(self, "progress_bar"):
            self.progress_bar.setValue(int(progress))
            
        if processed_files is not None and total_files is not None and hasattr(self, "processed_label"):
            self.processed_label.setText(f"Processed: {processed_files}/{total_files}")
    
    def on_convert_clicked(self):
        """Handle convert button click"""
        # This will be connected to the parent dialog's convert method
        pass


class PDFManagementDialog(QDialog):
    """
    Dialog for managing PDF documents in knowledge bases
    """
    def __init__(self, llm_processor, parent=None):
        super().__init__(parent)
        self.llm_processor = llm_processor
        self.thread_pool = QThreadPool()
        self.document_widgets = {}  # Store widgets by doc_id for updates
        self.folder_widgets = {}    # Store folder widgets by folder_id
        
        self.setWindowTitle("PDF Document Management")
        self.setMinimumSize(700, 500)
        
        self.setup_ui()
        self.load_knowledge_bases()
    
    def setup_ui(self):
        """Setup the dialog UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Knowledge base selector
        kb_layout = QHBoxLayout()
        kb_layout.addWidget(QLabel("Knowledge Base:"))
        self.kb_combo = QComboBox()
        self.kb_combo.currentIndexChanged.connect(self.on_kb_changed)
        kb_layout.addWidget(self.kb_combo)
        
        # Add KB button
        self.add_kb_btn = QPushButton("Add New KB")
        self.add_kb_btn.clicked.connect(self.on_add_kb_clicked)
        kb_layout.addWidget(self.add_kb_btn)
        
        main_layout.addLayout(kb_layout)
        
        # Create tabs for individual documents and folders
        self.tabs = QTabWidget()
        
        # Document tab
        self.doc_tab = QWidget()
        doc_layout = QVBoxLayout(self.doc_tab)
        
        # Document list
        self.document_list = QListWidget()
        self.document_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.document_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        doc_layout.addWidget(self.document_list)
        
        # Document action buttons
        doc_action_layout = QHBoxLayout()
        
        self.add_doc_btn = QPushButton("Add Document")
        self.add_doc_btn.clicked.connect(self.on_add_document_clicked)
        doc_action_layout.addWidget(self.add_doc_btn)
        
        self.doc_refresh_btn = QPushButton("Refresh")
        self.doc_refresh_btn.clicked.connect(self.refresh_document_list)
        doc_action_layout.addWidget(self.doc_refresh_btn)
        
        doc_layout.addLayout(doc_action_layout)
        
        # Folder tab
        self.folder_tab = QWidget()
        folder_layout = QVBoxLayout(self.folder_tab)
        
        # Folder list
        self.folder_list = QListWidget()
        self.folder_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.folder_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        folder_layout.addWidget(self.folder_list)
        
        # Folder action buttons
        folder_action_layout = QHBoxLayout()
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.on_add_folder_clicked)
        folder_action_layout.addWidget(self.add_folder_btn)
        
        self.batch_convert_btn = QPushButton("Batch Convert")
        self.batch_convert_btn.clicked.connect(self.on_batch_convert_clicked)
        folder_action_layout.addWidget(self.batch_convert_btn)
        
        self.folder_refresh_btn = QPushButton("Refresh")
        self.folder_refresh_btn.clicked.connect(self.refresh_folder_list)
        folder_action_layout.addWidget(self.folder_refresh_btn)
        
        folder_layout.addLayout(folder_action_layout)
        
        # Add tabs to the main layout
        self.tabs.addTab(self.doc_tab, "Documents")
        self.tabs.addTab(self.folder_tab, "Folders")
        main_layout.addWidget(self.tabs)
        
        # Close button
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        main_layout.addLayout(buttons_layout)
    
    def load_knowledge_bases(self):
        """Load available knowledge bases into combo box"""
        self.kb_combo.clear()
        kb_list = self.llm_processor.get_kb_list()
        
        if kb_list:
            self.kb_combo.addItems(kb_list)
        else:
            # No KBs available
            self.document_list.clear()
            self.folder_list.clear()
            self.add_doc_btn.setEnabled(False)
            self.add_folder_btn.setEnabled(False)
            self.batch_convert_btn.setEnabled(False)
    
    def on_kb_changed(self, index):
        """Handle knowledge base selection change"""
        if index >= 0:
            kb_name = self.kb_combo.currentText()
            self.refresh_document_list()
            self.refresh_folder_list()
            self.add_doc_btn.setEnabled(True)
            self.add_folder_btn.setEnabled(True)
            self.batch_convert_btn.setEnabled(True)
        else:
            self.document_list.clear()
            self.folder_list.clear()
            self.add_doc_btn.setEnabled(False)
            self.add_folder_btn.setEnabled(False)
            self.batch_convert_btn.setEnabled(False)
    
    def refresh_document_list(self):
        """Refresh the document list for current KB"""
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Clear previous document list
        self.document_list.clear()
        self.document_widgets = {}
        
        # Get documents for current KB
        documents = self.llm_processor.get_kb_documents(kb_name)
        
        for doc in documents:
            # Skip documents that belong to folder-based imports
            if doc.get("folder_id"):
                continue
                
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(QSize(self.document_list.width(), 80))  # Height depends on content
            
            # Create widget for document display
            doc_widget = DocumentListItem(doc)
            # Connect convert button if exists
            if hasattr(doc_widget, "convert_btn"):
                doc_widget.convert_btn.clicked.connect(
                    lambda checked, doc_id=doc["id"]: self.start_conversion(doc_id)
                )
            
            # Store widget reference
            self.document_widgets[doc["id"]] = doc_widget
            
            # Add to list
            self.document_list.addItem(item)
            self.document_list.setItemWidget(item, doc_widget)
    
    def refresh_folder_list(self):
        """Refresh the folder list for current KB"""
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Clear previous folder list
        self.folder_list.clear()
        self.folder_widgets = {}
        
        # Get folders for current KB
        folders = self.llm_processor.get_kb_folders(kb_name)
        
        for folder in folders:
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(QSize(self.folder_list.width(), 80))
            
            # Create widget for folder display
            folder_widget = FolderConversionItem(folder)
            # Connect convert button if exists
            if hasattr(folder_widget, "convert_btn"):
                folder_widget.convert_btn.clicked.connect(
                    lambda checked, folder_id=folder["id"]: self.start_folder_conversion(folder_id)
                )
            
            # Store widget reference
            self.folder_widgets[folder["id"]] = folder_widget
            
            # Add to list
            self.folder_list.addItem(item)
            self.folder_list.setItemWidget(item, folder_widget)
    
    def on_add_kb_clicked(self):
        """Handle add knowledge base button click"""
        kb_name, ok = QInputDialog.getText(self, "Add Knowledge Base", "KB Name:")
        
        if ok and kb_name:
            # Create KB
            success = self.llm_processor.create_kb(kb_name)
            
            if success:
                # Refresh KB list
                self.load_knowledge_bases()
                # Select the new KB
                index = self.kb_combo.findText(kb_name)
                if index >= 0:
                    self.kb_combo.setCurrentIndex(index)
            else:
                QMessageBox.warning(self, "Error", "Failed to create knowledge base. Name may already exist.")
    
    def on_add_document_clicked(self):
        """Handle add document button click"""
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Open file dialog to select PDFs
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Documents", "", "PDF Files (*.pdf)"
        )
        
        if not files:
            return
        
        # Ask if these are scanned documents
        is_scanned = QMessageBox.question(
            self, "Document Type",
            "Are these scanned documents that need OCR?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes
        
        # Add documents to KB
        added_docs = []
        for file_path in files:
            doc_id = self.llm_processor.add_document_to_kb(kb_name, file_path, is_scanned)
            if doc_id:
                added_docs.append(doc_id)
        
        # Refresh document list
        self.refresh_document_list()
        
        # Ask if user wants to start conversion for scanned documents
        if is_scanned and added_docs:
            start_conversion = QMessageBox.question(
                self, "Start Conversion",
                "Do you want to start converting the added documents now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes
            
            if start_conversion:
                for doc_id in added_docs:
                    self.start_conversion(doc_id)
    
    def on_add_folder_clicked(self):
        """Handle add folder button click"""
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Open directory dialog to select folder
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Folder Containing PDF Documents"
        )
        
        if not folder_path:
            return
        
        # Count PDF files in the folder and subfolders
        pdf_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        if not pdf_files:
            QMessageBox.warning(self, "No PDFs Found", 
                               f"No PDF files were found in the selected folder: {folder_path}")
            return
        
        # Add folder to KB
        folder_id = self.llm_processor.add_folder_to_kb(
            kb_name, 
            folder_path, 
            os.path.basename(folder_path),
            len(pdf_files)
        )
        
        if not folder_id:
            QMessageBox.warning(self, "Error", "Failed to add folder to knowledge base.")
            return
        
        # Refresh folder list
        self.refresh_folder_list()
        
        # Ask if user wants to start conversion for the folder
        start_conversion = QMessageBox.question(
            self, "Start Conversion",
            f"Do you want to start converting {len(pdf_files)} PDF files in the folder now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes
        
        if start_conversion:
            self.start_folder_conversion(folder_id)
    
    def start_conversion(self, doc_id):
        """Start conversion for a specific document"""
        # Get document info
        doc = self.llm_processor.db_manager.get_document_by_id(doc_id)
        if not doc:
            return
        
        # Get KB info 
        kb = self.llm_processor.db_manager.get_knowledge_base_by_id(doc["kb_id"])
        if not kb:
            return
        
        # Set up output directory
        output_dir = os.path.join(kb["directory"], "converted")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Update status to in_progress
        self.llm_processor.update_document_conversion(doc_id, "in_progress", progress=0)
        if doc_id in self.document_widgets:
            self.document_widgets[doc_id].update_status("in_progress", 0)
        
        # Create worker for conversion
        worker = PDFConversionWorker(doc_id, doc["original_path"], output_dir)
        
        # Connect signals
        worker.signals.progress.connect(self.on_conversion_progress)
        worker.signals.completed.connect(self.on_conversion_completed)
        worker.signals.error.connect(self.on_conversion_error)
        
        # Start conversion
        self.thread_pool.start(worker)
    
    def start_folder_conversion(self, folder_id):
        """Start conversion for all PDF files in a folder"""
        # Get folder info
        folder = self.llm_processor.db_manager.get_folder_by_id(folder_id)
        if not folder:
            return
        
        # Get KB info
        kb = self.llm_processor.db_manager.get_knowledge_base_by_id(folder["kb_id"])
        if not kb:
            return
        
        # Set up output directory
        output_dir = os.path.join(kb["directory"], "converted")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Update folder status to in_progress
        self.llm_processor.update_folder_conversion(folder_id, "in_progress", progress=0)
        if folder_id in self.folder_widgets:
            self.folder_widgets[folder_id].update_status("in_progress", 0, 0, folder["file_count"])
        
        # Create worker for folder conversion
        worker = FolderConversionWorker(
            folder_id,
            folder["folder_path"], 
            output_dir,
            kb["id"],
            self.llm_processor.db_manager
        )
        
        # Connect signals
        worker.signals.progress.connect(self.on_folder_progress)
        worker.signals.completed.connect(self.on_folder_completed)
        worker.signals.error.connect(self.on_folder_error)
        worker.signals.file_completed.connect(self.on_file_completed)
        
        # Start conversion
        self.thread_pool.start(worker)
    
    def on_batch_convert_clicked(self):
        """Start batch conversion for all pending folders"""
        # Get current KB
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Get all pending folders
        pending_folders = self.llm_processor.get_pending_folders(kb_name)
        
        if not pending_folders:
            QMessageBox.information(self, "No Pending Folders", 
                                   "No folders are pending conversion.")
            return
        
        # Process each folder
        for folder in pending_folders:
            self.start_folder_conversion(folder["id"])
    
    def on_conversion_progress(self, doc_id, progress):
        """Handle conversion progress update"""
        # Update database
        self.llm_processor.update_document_conversion(doc_id, "in_progress", progress=progress)
        
        # Update UI
        if doc_id in self.document_widgets:
            self.document_widgets[doc_id].update_progress(progress)
    
    def on_conversion_completed(self, doc_id, output_path, page_count):
        """Handle conversion completion"""
        # Update database
        self.llm_processor.update_document_conversion(
            doc_id, "completed", progress=100,
            converted_path=output_path, page_count=page_count
        )
        
        # Update UI
        if doc_id in self.document_widgets:
            self.document_widgets[doc_id].update_status("completed", 100)
    
    def on_conversion_error(self, doc_id, error_msg):
        """Handle conversion error"""
        # Update database
        self.llm_processor.update_document_conversion(doc_id, "failed", progress=0)
        
        # Update UI
        if doc_id in self.document_widgets:
            self.document_widgets[doc_id].update_status("failed", 0)
        
        # Show error message
        QMessageBox.warning(self, "Conversion Error", f"Error converting document: {error_msg}")
    
    def on_folder_progress(self, folder_id, progress, processed_files, total_files):
        """Handle folder conversion progress update"""
        # Update database
        self.llm_processor.update_folder_conversion(
            folder_id, "in_progress", 
            progress=progress,
            processed_files=processed_files
        )
        
        # Update UI
        if folder_id in self.folder_widgets:
            self.folder_widgets[folder_id].update_progress(progress, processed_files, total_files)
    
    def on_file_completed(self, folder_id, doc_id, output_path, page_count):
        """Handle individual file completion within a folder conversion"""
        # Update document status
        self.llm_processor.update_document_conversion(
            doc_id, "completed", progress=100,
            converted_path=output_path, page_count=page_count
        )
    
    def on_folder_completed(self, folder_id):
        """Handle folder conversion completion"""
        # Update database
        folder = self.llm_processor.db_manager.get_folder_by_id(folder_id)
        if folder:
            self.llm_processor.update_folder_conversion(
                folder_id, "completed", progress=100,
                processed_files=folder["file_count"]
            )
            
            # Update UI
            if folder_id in self.folder_widgets:
                self.folder_widgets[folder_id].update_status(
                    "completed", 100, 
                    folder["file_count"], folder["file_count"]
                )
    
    def on_folder_error(self, folder_id, error_msg):
        """Handle folder conversion error"""
        # Update database
        self.llm_processor.update_folder_conversion(folder_id, "failed", progress=0)
        
        # Update UI
        if folder_id in self.folder_widgets:
            folder = self.llm_processor.db_manager.get_folder_by_id(folder_id)
            if folder:
                processed = folder.get("processed_files", 0)
                total = folder.get("file_count", 0)
                self.folder_widgets[folder_id].update_status("failed", 0, processed, total)
        
        # Show error message
        QMessageBox.warning(self, "Folder Conversion Error", f"Error converting folder: {error_msg}")


class FolderConversionWorker(BatchConversionWorker):
    """Worker to handle conversion of all PDFs in a folder"""
    def __init__(self, folder_id, folder_path, output_dir, kb_id, db_manager):
        super().__init__(db_manager, output_dir)  # Base initialization
        
        # Override with folder-specific properties
        self.folder_id = folder_id
        self.folder_path = folder_path
        self.kb_id = kb_id
        
        # Progress tracking variables
        self.processed_files = 0
        self.total_files = 0
        self.current_progress = 0
        
        # Define additional signals
        from PyQt6.QtCore import pyqtSignal, QObject
        
        class FolderSignals(QObject):
            progress = pyqtSignal(str, int, int, int)  # folder_id, progress, processed, total
            completed = pyqtSignal(str)  # folder_id
            error = pyqtSignal(str, str)  # folder_id, error_message
            file_completed = pyqtSignal(str, str, str, int)  # folder_id, doc_id, output_path, page_count
        
        self.signals = FolderSignals()
    
    def run(self):
        """Execute folder conversion"""
        try:
            # Find all PDF files in folder and subfolders
            pdf_files = []
            for root, _, files in os.walk(self.folder_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
            
            self.total_files = len(pdf_files)
            
            if self.total_files == 0:
                self.signals.error.emit(self.folder_id, "No PDF files found in folder.")
                return
            
            # Process each file
            for index, pdf_path in enumerate(pdf_files):
                # Check if we should stop processing
                if self.should_stop:
                    break
                
                try:
                    # Calculate progress
                    file_progress = (index / self.total_files) * 100
                    self.signals.progress.emit(
                        self.folder_id, 
                        int(file_progress), 
                        index, 
                        self.total_files
                    )
                    
                    # Check if document already exists in database
                    file_name = os.path.basename(pdf_path)
                    relative_path = os.path.relpath(pdf_path, self.folder_path)
                    existing_doc = self.db_manager.get_document_by_path_and_kb(pdf_path, self.kb_id)
                    
                    if existing_doc:
                        doc_id = existing_doc["id"]
                    else:
                        # Add document to database
                        doc_id = self.db_manager.add_document(
                            kb_id=self.kb_id,
                            original_filename=file_name,
                            original_path=pdf_path,
                            is_scanned=True,
                            conversion_status="in_progress",
                            folder_id=self.folder_id,
                            relative_path=relative_path
                        )
                    
                    # Create output path
                    output_filename = f"{os.path.splitext(file_name)[0]}_converted.pdf"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    # Perform OCR conversion
                    result = self._convert_pdf(pdf_path, output_path)
                    
                    if result["success"]:
                        # Update document in database
                        self.db_manager.update_document(
                            doc_id=doc_id,
                            conversion_status="completed",
                            converted_path=output_path,
                            page_count=result["page_count"],
                            conversion_progress=100
                        )
                        
                        # Emit file completed signal
                        self.signals.file_completed.emit(
                            self.folder_id, 
                            doc_id, 
                            output_path, 
                            result["page_count"]
                        )
                    else:
                        # Update document with failed status
                        self.db_manager.update_document(
                            doc_id=doc_id,
                            conversion_status="failed",
                            conversion_progress=0
                        )
                    
                    # Update processed files count
                    self.processed_files = index + 1
                    
                except Exception as e:
                    # Log error but continue with next file
                    print(f"Error processing {pdf_path}: {str(e)}")
            
            # All files processed
            if not self.should_stop:
                self.signals.completed.emit(self.folder_id)
            
        except Exception as e:
            self.signals.error.emit(self.folder_id, str(e))
    
    def _convert_pdf(self, input_path, output_path):
        """
        Perform OCR on a PDF file
        Returns dict with success status and page count
        """
        try:
            # Implementation of PDF OCR conversion
            # This would use a library like PyMuPDF, pytesseract, etc.
            # For this example, we'll simulate the conversion
            
            import time
            import random
            from PyPDF2 import PdfReader
            
            # Simulate processing time based on file size
            time.sleep(1)
            
            # Get actual page count if possible
            try:
                with open(input_path, 'rb') as f:
                    pdf = PdfReader(f)
                    page_count = len(pdf.pages)
            except:
                # If can't read PDF, use a random number for simulation
                page_count = random.randint(1, 30)
            
            # Create a simple output file for simulation
            with open(output_path, 'w') as f:
                f.write("This is a simulated OCR output")
            
            return {
                "success": True,
                "page_count": page_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }