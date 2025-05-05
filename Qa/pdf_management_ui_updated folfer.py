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


class FolderTreeItem(QTreeWidgetItem):
    """Custom tree widget item for folders"""
    def __init__(self, path, is_root=False, parent=None):
        super().__init__(parent)
        self.path = path
        self.folder_name = os.path.basename(path)
        self.setText(0, self.folder_name)
        self.doc_count = 0
        self.pending_count = 0
        self.is_root = is_root
        self.setCheckState(0, Qt.CheckState.Unchecked)
        
    def update_counts(self, doc_count, pending_count):
        """Update document counts and display"""
        self.doc_count = doc_count
        self.pending_count = pending_count
        
        # Root folder shows subfolders count instead of documents
        if self.is_root:
            child_count = self.childCount()
            self.setText(0, f"{self.folder_name} ({child_count} subfolders)")
            self.setForeground(0, QColor("#000000"))  # Default color
        elif pending_count > 0:
            self.setText(0, f"{self.folder_name} ({pending_count}/{doc_count} need OCR)")
            self.setForeground(0, QColor("#FF9800"))  # Orange for pending
        else:
            self.setText(0, f"{self.folder_name} ({doc_count} docs)")
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
        
        self.setWindowTitle("PDF Document Management")
        self.setMinimumSize(900, 600)
        
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
        
        # Create splitter for folder tree and document list
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Folder tree
        folder_group = QGroupBox("Folders")
        folder_layout = QVBoxLayout(folder_group)
        
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.itemClicked.connect(self.on_folder_selected)
        folder_layout.addWidget(self.folder_tree)
        
        # Folder action buttons
        folder_actions = QHBoxLayout()
        self.add_root_folder_btn = QPushButton("Select Root Folder")
        self.add_root_folder_btn.clicked.connect(self.on_select_root_folder)
        folder_actions.addWidget(self.add_root_folder_btn)
        
        self.refresh_folders_btn = QPushButton("Refresh")
        self.refresh_folders_btn.clicked.connect(self.refresh_folder_tree)
        folder_actions.addWidget(self.refresh_folders_btn)
        folder_layout.addLayout(folder_actions)
        
        splitter.addWidget(folder_group)
        
        # Document list
        doc_group = QGroupBox("Documents")
        doc_layout = QVBoxLayout(doc_group)
        
        self.document_list = QListWidget()
        self.document_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.document_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        doc_layout.addWidget(self.document_list)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.convert_folder_btn = QPushButton("Convert Selected Folder")
        self.convert_folder_btn.clicked.connect(self.on_convert_folder_clicked)
        self.convert_folder_btn.setEnabled(False)
        action_layout.addWidget(self.convert_folder_btn)
        
        self.batch_convert_btn = QPushButton("Batch Convert All Checked")
        self.batch_convert_btn.clicked.connect(self.on_batch_convert_clicked)
        self.batch_convert_btn.setEnabled(False)
        action_layout.addWidget(self.batch_convert_btn)
        
        doc_layout.addLayout(action_layout)
        splitter.addWidget(doc_group)
        
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
        
        # Context menu for folder tree
        self.folder_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(self.show_folder_context_menu)
    
    def load_knowledge_bases(self):
        """Load available knowledge bases into combo box"""
        self.kb_combo.clear()
        kb_list = self.llm_processor.get_kb_list()
        
        if kb_list:
            self.kb_combo.addItems(kb_list)
        else:
            # No KBs available
            self.folder_tree.clear()
            self.document_list.clear()
            self.add_root_folder_btn.setEnabled(False)
            self.batch_convert_btn.setEnabled(False)
    
    def on_kb_changed(self, index):
        """Handle knowledge base selection change"""
        if index >= 0:
            kb_name = self.kb_combo.currentText()
            self.refresh_folder_tree()
            self.add_root_folder_btn.setEnabled(True)
        else:
            self.folder_tree.clear()
            self.document_list.clear()
            self.add_root_folder_btn.setEnabled(False)
            self.batch_convert_btn.setEnabled(False)
    
    def on_select_root_folder(self):
        """Handle selecting a root folder containing subfolders"""
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Open folder selection dialog
        root_folder = QFileDialog.getExistingDirectory(
            self, "Select Root Folder Containing PDF Documents", ""
        )
        
        if not root_folder or not os.path.isdir(root_folder):
            return
        
        # Ask if these are scanned documents
        is_scanned = QMessageBox.question(
            self, "Document Type",
            "Are these scanned documents that need OCR?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes
        
        # Process all PDF files in the folder and subfolders
        self.process_folder_structure(kb_name, root_folder, is_scanned)
        
        # Refresh the folder tree
        self.refresh_folder_tree()
    
    def process_folder_structure(self, kb_name, root_folder, is_scanned):
        """Process the folder structure and add documents to KB"""
        # Show progress dialog
        progress_dialog = QProgressDialog("Processing folders...", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.show()
        
        # First, collect all folders and PDF files
        all_folders = []
        total_pdfs = 0
        
        for root, dirs, files in os.walk(root_folder):
            pdfs = [f for f in files if f.lower().endswith('.pdf')]
            if pdfs:  # Only add folders containing PDFs
                all_folders.append((root, pdfs))
                total_pdfs += len(pdfs)
        
        if not all_folders:
            progress_dialog.close()
            QMessageBox.information(self, "No PDFs Found", "No PDF files were found in the selected folder structure.")
            return
        
        # Generate unique code for this import batch
        import datetime
        import uuid
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        batch_id = f"{date_str}_{str(uuid.uuid4())[:8]}"
        
        # Process all files, maintaining folder structure
        processed = 0
        for folder_path, pdfs in all_folders:
            # Create relative path from root folder to maintain structure
            rel_path = os.path.relpath(folder_path, root_folder)
            if rel_path == '.':  # Files in root folder
                folder_code = f"batch_{batch_id}_root"
            else:
                # Create a folder code with the relative path
                folder_code = f"batch_{batch_id}_{rel_path.replace(os.sep, '_')}"
            
            for pdf in pdfs:
                file_path = os.path.join(folder_path, pdf)
                
                # Add document to KB with folder code metadata
                doc_id = self.llm_processor.add_document_to_kb(kb_name, file_path, is_scanned)
                
                # Add folder code metadata if document was added successfully
                if doc_id:
                    # Assuming there's an update_document_metadata method or similar
                    self.llm_processor.update_document_metadata(doc_id, {
                        "folder_code": folder_code,
                        "original_folder": folder_path,
                        "relative_path": rel_path,
                        "batch_id": batch_id
                    })
                
                # Update progress
                processed += 1
                progress_value = int((processed / total_pdfs) * 100)
                progress_dialog.setValue(progress_value)
                
                # Check if user canceled
                if progress_dialog.wasCanceled():
                    break
            
            if progress_dialog.wasCanceled():
                break
        
        # Close progress dialog
        progress_dialog.close()
        
        # Show completion message
        QMessageBox.information(
            self, "Import Complete", 
            f"Successfully processed {processed} PDF files from {len(all_folders)} folders.\nBatch ID: {batch_id}"
        )
    
    def refresh_folder_tree(self):
        """Refresh the folder tree with document folders"""
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
        
        # Clear previous tree
        self.folder_tree.clear()
        
        # Get documents for current KB
        documents = self.llm_processor.get_kb_documents(kb_name)
        
        # Organize by root folders and their subfolders
        root_folders = {}
        
        for doc in documents:
            folder_path = os.path.dirname(doc["original_path"])
            # Find the root folder (assuming structure of root/subfolder/...)
            path_parts = folder_path.split(os.sep)
            
            # Skip if path is too short
            if len(path_parts) < 2:
                continue
                
            # Determine root folder
            # Start with the complete path
            for i in range(len(path_parts)-1, 0, -1):
                possible_root = os.sep.join(path_parts[:i])
                # If this is a known root folder or we're at the base, use it
                if possible_root in root_folders:
                    root_folder_path = possible_root
                    break
            else:
                # Default to first level if no match found
                root_folder_path = path_parts[0]
                if os.sep in folder_path:
                    root_folder_path = folder_path.split(os.sep)[0]
            
            # Initialize root folder if needed
            if root_folder_path not in root_folders:
                root_folders[root_folder_path] = {
                    "subfolders": {},
                    "docs": [],
                    "pending": 0
                }
            
            # Add to the appropriate subfolder or directly to root
            if folder_path != root_folder_path:
                if folder_path not in root_folders[root_folder_path]["subfolders"]:
                    root_folders[root_folder_path]["subfolders"][folder_path] = {
                        "docs": [],
                        "pending": 0
                    }
                
                root_folders[root_folder_path]["subfolders"][folder_path]["docs"].append(doc)
                if doc["is_scanned"] and doc["conversion_status"] in ["pending", "failed"]:
                    root_folders[root_folder_path]["subfolders"][folder_path]["pending"] += 1
            else:
                # Document is directly in root folder
                root_folders[root_folder_path]["docs"].append(doc)
                if doc["is_scanned"] and doc["conversion_status"] in ["pending", "failed"]:
                    root_folders[root_folder_path]["pending"] += 1
        
        # Create tree structure
        for root_path, root_data in root_folders.items():
            # Create root item
            root_item = FolderTreeItem(root_path, is_root=True)
            self.folder_tree.addTopLevelItem(root_item)
            
            # Add docs in root folder (if any)
            if root_data["docs"]:
                root_item.update_counts(
                    len(root_data["docs"]), 
                    root_data["pending"]
                )
            
            # Add subfolders
            for subfolder_path, subfolder_data in root_data["subfolders"].items():
                subfolder_item = FolderTreeItem(subfolder_path, parent=root_item)
                subfolder_item.update_counts(
                    len(subfolder_data["docs"]), 
                    subfolder_data["pending"]
                )
            
            # Update root folder counts
            root_item.update_counts(
                len(root_data["docs"]), 
                root_data["pending"]
            )
            
            # Expand the root item
            root_item.setExpanded(True)
        
        # Sort folders by name
        self.folder_tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        
        # Enable/disable batch convert button
        has_folders = self.folder_tree.topLevelItemCount() > 0
        self.batch_convert_btn.setEnabled(has_folders)
    
    def on_folder_selected(self, item, column):
        """Handle folder selection in tree"""
        if isinstance(item, FolderTreeItem):
            self.current_folder = item.path
            self.load_folder_documents(item.path)
            self.convert_folder_btn.setEnabled(item.pending_count > 0)
    
    def load_folder_documents(self, folder_path):
        """Load documents for selected folder"""
        kb_name = self.kb_combo.currentText()
        if not kb_name or not folder_path:
            return
        
        # Clear previous document list
        self.document_list.clear()
        self.document_widgets = {}
        
        # Get documents for current KB
        all_documents = self.llm_processor.get_kb_documents(kb_name)
        
        # Filter documents by folder
        folder_documents = [doc for doc in all_documents if os.path.dirname(doc["original_path"]) == folder_path]
        
        for doc in folder_documents:
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
        
        # Get document metadata to determine output folder structure
        metadata = self.llm_processor.get_document_metadata(doc_id)
        folder_code = metadata.get("folder_code", "default")
        
        # Set up output directory with folder structure
        base_output_dir = os.path.join(kb["directory"], "converted")
        if not os.path.exists(base_output_dir):
            os.makedirs(base_output_dir)
        
        # Create subfolder for this batch if folder_code exists
        if folder_code != "default":
            output_dir = os.path.join(base_output_dir, folder_code)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
        else:
            output_dir = base_output_dir
        
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
    
    def on_convert_folder_clicked(self):
        """Convert all pending documents in the selected folder"""
        if not self.current_folder:
            return
        
        # Get KB name
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
            
        # Get all documents for current KB
        all_documents = self.llm_processor.get_kb_documents(kb_name)
        
        # Filter documents by folder and status
        folder_docs = [
            doc for doc in all_documents 
            if os.path.dirname(doc["original_path"]) == self.current_folder
            and doc["is_scanned"] 
            and doc["conversion_status"] in ["pending", "failed"]
        ]
        
        if not folder_docs:
            QMessageBox.information(
                self, "No Documents", "No documents requiring conversion in this folder."
            )
            return
            
        # Confirm conversion
        result = QMessageBox.question(
            self, "Convert Folder",
            f"Start OCR conversion for {len(folder_docs)} document(s) in this folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Start conversion for each document
            for doc in folder_docs:
                self.start_conversion(doc["id"])
    
    def on_batch_convert_clicked(self):
        """Start batch conversion for all checked folders"""
        # Get checked folders (including both root and subfolders)
        checked_folders = []
        
        # Process root folders first
        for i in range(self.folder_tree.topLevelItemCount()):
            root_item = self.folder_tree.topLevelItem(i)
            
            # Add root folder if checked
            if root_item.checkState(0) == Qt.CheckState.Checked:
                checked_folders.append(root_item.path)
            
            # Check subfolders
            for j in range(root_item.childCount()):
                child_item = root_item.child(j)
                if child_item.checkState(0) == Qt.CheckState.Checked:
                    checked_folders.append(child_item.path)
        
        if not checked_folders:
            QMessageBox.information(
                self, "No Selection", "Please check at least one folder to convert."
            )
            return
        
        # Get KB name
        kb_name = self.kb_combo.currentText()
        if not kb_name:
            return
            
        # Get all documents for current KB
        all_documents = self.llm_processor.get_kb_documents(kb_name)
        
        # Filter documents by folders and status
        docs_to_convert = [
            doc for doc in all_documents 
            if os.path.dirname(doc["original_path"]) in checked_folders
            and doc["is_scanned"] 
            and doc["conversion_status"] in ["pending", "failed"]
        ]
        
        if not docs_to_convert:
            QMessageBox.information(
                self, "No Documents", "No documents requiring conversion in selected folders."
            )
            return
        
        # Group documents by batch_id/folder_code to maintain structure
        grouped_docs = {}
        for doc in docs_to_convert:
            # Get metadata to find batch_id and folder_code
            metadata = self.llm_processor.get_document_metadata(doc["id"])
            batch_id = metadata.get("batch_id", "unknown")
            folder_code = metadata.get("folder_code", "default")
            
            key = f"{batch_id}_{folder_code}"
            if key not in grouped_docs:
                grouped_docs[key] = []
            
            grouped_docs[key].append(doc)
        
        # Confirm conversion
        result = QMessageBox.question(
            self, "Batch Convert",
            f"Start OCR conversion for {len(docs_to_convert)} document(s) in {len(checked_folders)} folder(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Create progress dialog
            progress_dialog = QProgressDialog("Starting conversions...", "Cancel", 0, len(docs_to_convert), self)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.show()
            
            # Process each group to maintain folder structure in output
            processed = 0
            for folder_group, docs in grouped_docs.items():
                # Create output subfolder based on the folder_code
                for doc in docs:
                    self.start_conversion(doc["id"])
                    processed += 1
                    progress_dialog.setValue(processed)
                    
                    # Process events to keep UI responsive
                    from PyQt6.QtCore import QCoreApplication
                    QCoreApplication.processEvents()
                    
                    if progress_dialog.wasCanceled():
                        break
                
                if progress_dialog.wasCanceled():
                    break
            
            progress_dialog.close()
    
    def show_folder_context_menu(self, position):
        """Show context menu for folder items"""
        item = self.folder_tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        check_action = menu.addAction("Check All")
        uncheck_action = menu.addAction("Uncheck All")
        
        action = menu.exec(self.folder_tree.viewport().mapToGlobal(position))
        
        if action == check_action:
            self.check_all_folders(True)
        elif action == uncheck_action:
            self.check_all_folders(False)
    
    def check_all_folders(self, checked):
        """Check or uncheck all folders"""
        check_state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        
        for i in range(self.folder_tree.topLevelItemCount()):
            item = self.folder_tree.topLevelItem(i)
            item.setCheckState(0, check_state)
    
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
            
        # Update folder counts in tree
        self.refresh_folder_tree()
        
        # If current folder is selected, reload its documents
        if self.current_folder:
            current_folder_items = self.folder_tree.findItems(
                os.path.basename(self.current_folder),
                Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
                0
            )
            if current_folder_items:
                self.convert_folder_btn.setEnabled(
                    current_folder_items[0].pending_count > 0
                )
    
    def on_conversion_error(self, doc_id, error_msg):
        """Handle conversion error"""
        # Update database
        self.llm_processor.update_document_conversion(doc_id, "failed", progress=0)
        
        # Update UI
        if doc_id in self.document_widgets:
            self.document_widgets[doc_id].update_status("failed", 0)
        
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
