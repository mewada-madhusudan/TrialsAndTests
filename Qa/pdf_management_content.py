from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                           QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
                           QFileDialog, QMessageBox, QProgressBar, QInputDialog,
                           QTabWidget, QLineEdit, QCheckBox, QToolBar, QMenu, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

from pdf_conversion_worker import PDFConversionWorker, BatchConversionWorker


class PDFManagementContent(QWidget):
    """Widget to manage PDF documents within the main window"""
    
    # Signals to communicate with the main application
    kb_updated = pyqtSignal()  # Signal when KBs are updated
    
    def __init__(self, llm_processor, parent=None):
        super().__init__(parent)
        self.llm_processor = llm_processor
        self.current_kb = None
        self.documents = []
        
        # Setup UI
        self.init_ui()
        
        # Populate KB combobox
        self.refresh_kb_list()
    
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # KB management section
        kb_section = QHBoxLayout()
        
        # KB selection
        kb_label = QLabel("Knowledge Base:")
        self.kb_combo = QComboBox()
        self.kb_combo.setSizePolicy(QSize(QSize.Policy.Expanding, QSize.Policy.Fixed))
        self.kb_combo.currentIndexChanged.connect(self.kb_selected)
        
        # KB actions
        create_kb_btn = QPushButton("Create KB")
        create_kb_btn.clicked.connect(self.create_kb)
        
        # Add to KB section layout
        kb_section.addWidget(kb_label)
        kb_section.addWidget(self.kb_combo, 1)
        kb_section.addWidget(create_kb_btn)
        
        main_layout.addLayout(kb_section)
        
        # Document actions section
        doc_actions = QHBoxLayout()
        
        # Add document button
        add_doc_btn = QPushButton("Add PDF Document")
        add_doc_btn.clicked.connect(self.add_document)
        
        # Add batch documents button
        add_batch_btn = QPushButton("Add Multiple PDFs")
        add_batch_btn.clicked.connect(self.add_batch_documents)
        
        # Process selected button
        process_selected_btn = QPushButton("Process Selected")
        process_selected_btn.clicked.connect(self.process_selected_documents)
        
        # Add to actions layout
        doc_actions.addWidget(add_doc_btn)
        doc_actions.addWidget(add_batch_btn)
        doc_actions.addWidget(process_selected_btn)
        
        main_layout.addLayout(doc_actions)
        
        # Documents table
        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(5)
        self.doc_table.setHorizontalHeaderLabels([
            "File Name", "Status", "Progress", "Pages", "Actions"
        ])
        self.doc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # Make table scrollable in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.doc_table)
        
        main_layout.addWidget(scroll_area)
    
    def refresh_kb_list(self):
        """Refresh the knowledge base list"""
        current_text = self.kb_combo.currentText()
        
        # Clear and repopulate
        self.kb_combo.clear()
        kbs = self.llm_processor.get_kb_list()
        self.kb_combo.addItems(kbs)
        
        # Try to restore previous selection
        if current_text and current_text in kbs:
            self.kb_combo.setCurrentText(current_text)
        elif kbs:
            self.kb_selected(0)  # Select first KB
    
    def kb_selected(self, index):
        """Handle selection of a knowledge base"""
        if index < 0:
            self.current_kb = None
            self.documents = []
            self.refresh_document_table()
            return
            
        self.current_kb = self.kb_combo.currentText()
        self.refresh_content()
    
    def refresh_content(self):
        """Refresh the content based on current KB"""
        if not self.current_kb:
            self.documents = []
        else:
            self.documents = self.llm_processor.get_kb_documents(self.current_kb)
            
        self.refresh_document_table()
    
    def refresh_document_table(self):
        """Refresh the document table with current data"""
        self.doc_table.setRowCount(0)  # Clear table
        
        if not self.documents:
            return
            
        for idx, doc in enumerate(self.documents):
            self.doc_table.insertRow(idx)
            
            # File name
            self.doc_table.setItem(idx, 0, QTableWidgetItem(doc.get("original_filename", "")))
            
            # Status
            status = doc.get("conversion_status", "unknown")
            status_item = QTableWidgetItem(self.get_status_text(status))
            self.doc_table.setItem(idx, 1, status_item)
            
            # Progress
            progress = doc.get("conversion_progress", 0)
            progress_bar = QProgressBar()
            progress_bar.setValue(progress)
            progress_bar.setTextVisible(True)
            self.doc_table.setCellWidget(idx, 2, progress_bar)
            
            # Pages
            page_count = doc.get("page_count", 0)
            self.doc_table.setItem(idx, 3, QTableWidgetItem(str(page_count)))
            
            # Actions
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            if status in ["not_started", "failed", "not_required"]:
                process_btn = QPushButton("Process")
                process_btn.setProperty("doc_id", doc.get("id"))
                process_btn.clicked.connect(self.process_document)
                actions_layout.addWidget(process_btn)
            
            view_btn = QPushButton("View")
            view_btn.setProperty("doc_path", doc.get("original_path"))
            view_btn.clicked.connect(self.view_document)
            actions_layout.addWidget(view_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setProperty("doc_id", doc.get("id"))
            delete_btn.clicked.connect(self.delete_document)
            actions_layout.addWidget(delete_btn)
            
            # Create a widget to hold the action buttons
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            self.doc_table.setCellWidget(idx, 4, actions_widget)
    
    def get_status_text(self, status):
        """Convert status code to display text"""
        status_map = {
            "not_started": "Not Processed",
            "in_progress": "Processing...",
            "completed": "Completed",
            "failed": "Failed",
            "not_required": "Ready"
        }
        return status_map.get(status, status)
    
    def create_kb(self):
        """Create a new knowledge base"""
        kb_name, ok = QInputDialog.getText(
            self, "Create Knowledge Base", "Knowledge Base Name:"
        )
        
        if not ok or not kb_name:
            return
            
        # Create KB
        success = self.llm_processor.create_kb(kb_name)
        
        if success:
            # Refresh KB list and select the new one
            self.refresh_kb_list()
            self.kb_combo.setCurrentText(kb_name)
            
            # Emit signal for KB update
            self.kb_updated.emit()
        else:
            QMessageBox.warning(
                self, "Error", f"Failed to create knowledge base '{kb_name}'"
            )
    
    def add_document(self):
        """Add a single PDF document to the current KB"""
        if not self.current_kb:
            QMessageBox.warning(
                self, "Warning", "Please select or create a knowledge base first"
            )
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF Document", "", "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
            
        # Add document to KB
        doc_id = self.llm_processor.add_document_to_kb(self.current_kb, file_path)
        
        if doc_id:
            # Refresh document table
            self.refresh_content()
            QMessageBox.information(
                self, "Success", "Document added successfully"
            )
        else:
            QMessageBox.warning(
                self, "Error", "Failed to add document"
            )
    
    def add_batch_documents(self):
        """Add multiple PDF documents to the current KB"""
        if not self.current_kb:
            QMessageBox.warning(
                self, "Warning", "Please select or create a knowledge base first"
            )
            return
            
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Documents", "", "PDF Files (*.pdf)"
        )
        
        if not file_paths:
            return
            
        # Add each document
        success_count = 0
        for file_path in file_paths:
            doc_id = self.llm_processor.add_document_to_kb(self.current_kb, file_path)
            if doc_id:
                success_count += 1
                
        # Refresh document table
        self.refresh_content()
        
        if success_count > 0:
            QMessageBox.information(
                self, "Success", f"Added {success_count} of {len(file_paths)} documents"
            )
        else:
            QMessageBox.warning(
                self, "Error", "Failed to add any documents"
            )
    
    def process_document(self):
        """Process a single document for text extraction"""
        button = self.sender()
        if not button:
            return
            
        doc_id = button.property("doc_id")
        if not doc_id:
            return
            
        # Find document in list
        doc = None
        for d in self.documents:
            if d.get("id") == doc_id:
                doc = d
                break
                
        if not doc:
            QMessageBox.warning(
                self, "Error", "Document not found"
            )
            return
            
        # Start conversion worker
        worker = PDFConversionWorker(self.llm_processor, doc_id)
        
        # Connect progress updates
        worker.signals.progress.connect(lambda p, d_id=doc_id: self.update_progress(d_id, p))
        worker.signals.finished.connect(lambda d_id=doc_id: self.conversion_finished(d_id))
        worker.signals.error.connect(lambda err, d_id=doc_id: self.conversion_error(d_id, err))
        
        # Update status in UI
        self.update_document_status(doc_id, "in_progress", 0)
        
        # Start worker
        QThreadPool.globalInstance().start(worker)
    
    def process_selected_documents(self):
        """Process all selected documents for text extraction"""
        if not self.current_kb or not self.documents:
            return
            
        # Get selected rows
        selected_rows = self.doc_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information