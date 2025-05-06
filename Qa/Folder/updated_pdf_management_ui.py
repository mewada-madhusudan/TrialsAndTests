from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QListWidget, QListWidgetItem, QProgressBar, QCheckBox,
                             QMessageBox, QWidget, QGroupBox, QScrollArea, QFormLayout,
                             QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QSize, QThreadPool
from PyQt6.QtGui import QIcon, QColor
from pdf_conversion_worker import PDFConversionWorker, BatchConversionWorker
import os

class DocumentListItem(QWidget):
    """
    Custom widget for displaying document with status in a list
    """
    # Same as before

class FolderTreeItem(QTreeWidgetItem):
    """
    Custom tree widget item for displaying folder structure
    """
    def __init__(self, path, is_folder=True, doc_data=None, parent=None):
        super().__init__(parent)
        self.path = path
        self.is_folder = is_folder
        self.doc_data = doc_data
        
        # Set display name (folder or file name)
        self.setText(0, os.path.basename(path))
        
        # Set icon based on type
        if is_folder:
            self.setIcon(0, QIcon.fromTheme("folder"))
        else:
            self.setIcon(0, QIcon.fromTheme("document"))
            
            # For files, add status information
            if doc_data:
                status_text = doc_data["conversion_status"].replace("_", " ").title()
                self.setText(1, status_text)
                
                # Set status color
                status_color = self._get_status_color(doc_data["conversion_status"])
                self.setForeground(1, QColor(status_color))
                
                # Add page count if available
                if doc_data["page_count"] and doc_data["page_count"] > 0:
                    self.setText(2, str(doc_data["page_count"]))
    
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
    
    def update_status(self, status, progress=None):
        """Update status text and color"""
        if not self.is_folder and self.doc_data:
            status_text = status.replace("_", " ").title()
            self.setText(1, status_text)
            
            status_color = self._get_status_color(status)
            self.setForeground(1, QColor(status_color))


class PDFManagementDialog(QDialog):
    """
    Dialog for managing PDF documents in knowledge bases
    """
    def __init__(self, llm_processor, parent=None):
        super().__init__(parent)
        self.llm_processor = llm_processor
        self.thread_pool = QThreadPool()
        self.document_widgets = {}  # Store widgets by doc_id for updates
        self.document_tree_items = {}  # Store tree items by doc_id
        
        self.setWindowTitle("PDF Document Management")
        self.setMinimumSize(800, 600)
        
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
        
        # Document tree
        doc_group = QGroupBox("Documents")
        doc_layout = QVBoxLayout(doc_group)
        
        self.document_tree = QTreeWidget()
        self.document_tree.setHeaderLabels(["Name", "Status", "Pages"])
        self.document_tree.setColumnWidth(0, 400)
        self.document_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        doc_layout.addWidget(self.document_tree)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.add_doc_btn = QPushButton("Add Document")
        self.add_doc_btn.clicked.connect(self.on_add_document_clicked)
        action_layout.addWidget(self.add_doc_btn)
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.on_add_folder_clicked)
        action_layout.addWidget(self.add_folder_btn)
        
        self.batch_convert_btn = QPushButton("Batch Convert")
        self.batch_convert_btn.clicked.connect(self.on_batch_convert_clicked)
        action_layout.addWidget(self.batch_convert_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_document_list)
        action_layout.addWidget(self.refresh_btn)
        
        doc_layout.addLayout(action_layout)
        main_layout.addWidget(doc_group)
        
        # Context menu for tree
        self.document_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.document_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # Close button
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        main_layout.addLayout(buttons_layout)
    
    def load_knowledge_bases(self):
        """Load available knowledge bases into combo box"""
        # Same as before
    
    def on_kb_changed(self, index):
        """Handle knowledge base selection change"""
        if index >= 0:
            kb_name = self.kb_combo.currentText()
            self.refresh_document_list()
            self.add_doc_btn.setEnabled(True)
            self.add_folder_btn.setEnabled(True)
            self.batch_convert_btn.setEnabled(True)
        else:
            self.document_tree.clear()
            self.add_doc_btn.setEnabled(False)
            self.add_folder_btn.setEnabled(False)
            self.batch_convert_btn.setEnabled(False)
    
    def refresh_document_list(self):
        """Refresh the document list for current KB"""
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Clear previous document tree
        self.document_tree.clear()
        self.document_widgets = {}
        self.document_tree_items = {}
        
        # Get KB info
        kb = self.llm_processor.db_manager.get_knowledge_base_by_name(kb_name)
        if not kb:
            return
            
        # Get documents for current KB
        documents = self.llm_processor.get_kb_documents(kb_name)
        
        # Build folder structure
        self.build_folder_tree(kb["directory"], documents)
        
        # Expand top-level items
        for i in range(self.document_tree.topLevelItemCount()):
            self.document_tree.topLevelItem(i).setExpanded(True)
    
    def build_folder_tree(self, kb_directory, documents):
        """Build folder tree structure from documents"""
        # Create mapping of relative paths to documents
        doc_map = {}
        folder_map = {}
        
        for doc in documents:
            rel_path = os.path.relpath(doc["original_path"], kb_directory)
            doc_map[rel_path] = doc
            
            # Add all parent folders to the folder map
            folder_path = os.path.dirname(rel_path)
            while folder_path and folder_path != ".":
                folder_map[folder_path] = True
                folder_path = os.path.dirname(folder_path)
        
        # First add all folders
        folder_items = {}
        
        # Add root item
        root_item = FolderTreeItem(kb_directory, is_folder=True)
        root_item.setText(0, os.path.basename(kb_directory) + " (Root)")
        self.document_tree.addTopLevelItem(root_item)
        folder_items[""] = root_item
        
        # Add all folders
        for folder_path in sorted(folder_map.keys()):
            parent_path = os.path.dirname(folder_path)
            if parent_path not in folder_items:
                parent_path = ""
                
            folder_item = FolderTreeItem(
                os.path.join(kb_directory, folder_path), 
                is_folder=True,
                parent=folder_items[parent_path]
            )
            folder_items[folder_path] = folder_item
        
        # Then add all files
        for rel_path, doc in doc_map.items():
            parent_path = os.path.dirname(rel_path)
            if parent_path not in folder_items:
                parent_path = ""
                
            file_item = FolderTreeItem(
                os.path.join(kb_directory, rel_path),
                is_folder=False,
                doc_data=doc,
                parent=folder_items[parent_path]
            )
            
            # Store reference for updates
            self.document_tree_items[doc["id"]] = file_item
    
    def show_context_menu(self, position):
        """Show context menu for tree items"""
        item = self.document_tree.itemAt(position)
        if item and isinstance(item, FolderTreeItem) and not item.is_folder:
            # Only show for document items
            doc_data = item.doc_data
            if doc_data and doc_data["is_scanned"] and doc_data["conversion_status"] in ["pending", "failed"]:
                menu = QMenu(self)
                convert_action = menu.addAction("Convert")
                action = menu.exec(self.document_tree.mapToGlobal(position))
                
                if action == convert_action:
                    self.start_conversion(doc_data["id"])
    
    def on_add_kb_clicked(self):
        """Handle add knowledge base button click"""
        # Same as before
    
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
        
        # Open folder dialog
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Folder Containing PDFs", ""
        )
        
        if not folder_path:
            return
        
        # Ask if these are scanned documents
        is_scanned = QMessageBox.question(
            self, "Document Type",
            "Are these scanned documents that need OCR?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes
        
        # Get KB base directory
        kb = self.llm_processor.db_manager.get_knowledge_base_by_name(kb_name)
        if not kb:
            return
            
        # Find all PDFs in the folder structure
        pdf_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        if not pdf_files:
            QMessageBox.information(self, "No PDFs Found", 
                                   "No PDF files were found in the selected folder structure.")
            return
            
        # Confirm with count
        proceed = QMessageBox.question(
            self, "Confirm Import",
            f"Found {len(pdf_files)} PDF files. Do you want to proceed with import?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes
        
        if not proceed:
            return
            
        # Add documents maintaining folder structure
        added_docs = []
        for file_path in pdf_files:
            # Calculate relative path from selected folder
            rel_path = os.path.relpath(file_path, folder_path)
            
            # Create target path in KB directory
            target_dir = os.path.join(kb["directory"], os.path.dirname(rel_path))
            
            # Create directories if needed
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            # Add document preserving the relative path
            doc_id = self.llm_processor.add_document_to_kb(
                kb_name, file_path, is_scanned, preserve_path=rel_path
            )
            
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
        
        # Preserve folder structure for output
        rel_path = os.path.relpath(doc["original_path"], kb["directory"])
        output_dir = os.path.join(kb["directory"], "converted", os.path.dirname(rel_path))
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Update status to in_progress
        self.llm_processor.update_document_conversion(doc_id, "in_progress", progress=0)
        if doc_id in self.document_tree_items:
            self.document_tree_items[doc_id].update_status("in_progress")
        
        # Create worker for conversion
        worker = PDFConversionWorker(doc_id, doc["original_path"], output_dir)
        
        # Connect signals
        worker.signals.progress.connect(self.on_conversion_progress)
        worker.signals.completed.connect(self.on_conversion_completed)
        worker.signals.error.connect(self.on_conversion_error)
        
        # Start conversion
        self.thread_pool.start(worker)
    
    def on_batch_convert_clicked(self):
        """Start batch conversion for all pending documents"""
        # Get current KB
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Create batch worker that preserves folder structure  
        base_dir = os.path.dirname(self.llm_processor.base_dir)
        worker = BatchConversionWorker(self.llm_processor.db_manager, base_dir, preserve_structure=True)
        
        # Connect signals
        worker.signals.progress.connect(self.on_conversion_progress)
        worker.signals.completed.connect(self.on_conversion_completed)
        worker.signals.error.connect(self.on_conversion_error)
        
        # Start batch processing
        self.thread_pool.start(worker)
    
    def on_conversion_progress(self, doc_id, progress):
        """Handle conversion progress update"""
        # Update database
        self.llm_processor.update_document_conversion(doc_id, "in_progress", progress=progress)
        
        # Update UI - no progress bar in tree view
    
    def on_conversion_completed(self, doc_id, output_path, page_count):
        """Handle conversion completion"""
        # Update database
        self.llm_processor.update_document_conversion(
            doc_id, "completed", progress=100,
            converted_path=output_path, page_count=page_count
        )
        
        # Update UI
        if doc_id in self.document_tree_items:
            self.document_tree_items[doc_id].update_status("completed")
            self.document_tree_items[doc_id].setText(2, str(page_count))
    
    def on_conversion_error(self, doc_id, error_msg):
        """Handle conversion error"""
        # Update database
        self.llm_processor.update_document_conversion(doc_id, "failed", progress=0)
        
        # Update UI
        if doc_id in self.document_tree_items:
            self.document_tree_items[doc_id].update_status("failed")
        
        # Show error message
        QMessageBox.warning(self, "Conversion Error", f"Error converting document: {error_msg}")


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
    def getExistingDirectory(parent, caption, directory=""):
        from PyQt6.QtWidgets import QFileDialog
        return QFileDialog.getExistingDirectory(parent, caption, directory)


class QMenu:
    def __init__(self, parent=None):
        from PyQt6.QtWidgets import QMenu
        self.menu = QMenu(parent)
        
    def addAction(self, text):
        return self.menu.addAction(text)
        
    def exec(self, position):
        return self.menu.exec(position)
