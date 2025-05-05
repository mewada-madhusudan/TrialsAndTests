import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTableView, QHeaderView,
                             QSplitter, QMessageBox, QLineEdit, QTextEdit, QFrame, 
                             QGridLayout, QSizePolicy, QComboBox, QDialog, QListWidget,
                             QListWidgetItem, QDialogButtonBox, QFormLayout, QAbstractItemView)
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QFont, QPalette, QIcon, QPixmap
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView

# Import PDF management functionality
from pdf_management_ui_complete import PDFManagementDialog
from pdf_conversion_worker import PDFConversionWorker, BatchConversionWorker

# LLMProcessor class with PDF management capabilities
class LLMProcessor:
    def __init__(self):
        self.kb_dirs = {}  # Store KB names and their directories
        self.conversation_ids = {}  # Store conversation IDs for follow-ups
        self.base_dir = "uploads"
        self.db_manager = None  # Will be initialized for PDF management
        
        # Create base directory if it doesn't exist
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
        # Scan for existing KBs
        self._scan_existing_kbs()
        
        # Initialize DB manager for PDF management
        self._init_db_manager()
    
    def _init_db_manager(self):
        """Initialize database manager for PDF documents"""
        # This is a placeholder - you would implement your actual DB manager here
        # The DB manager should handle document tracking for OCR conversion
        class DBManager:
            def get_document_by_id(self, doc_id):
                # Placeholder implementation
                return {"id": doc_id, "kb_id": 1, "original_path": "path/to/doc.pdf"}
                
            def get_knowledge_base_by_id(self, kb_id):
                # Placeholder implementation
                return {"id": kb_id, "name": "Sample KB", "directory": "uploads/Sample KB"}
                
        self.db_manager = DBManager()
            
    def _scan_existing_kbs(self):
        """Scan for existing knowledge bases in the uploads directory"""
        # Same as before

    def create_kb(self, kb_name):
        """Create a new knowledge base directory"""
        # Same as before
    
    def add_document_to_kb(self, kb_name, file_path, is_scanned=False):
        """Add a document to the specified knowledge base"""
        if kb_name not in self.kb_dirs:
            return False
            
        kb_dir = self.kb_dirs[kb_name]
        file_name = os.path.basename(file_path)
        destination = os.path.join(kb_dir, file_name)
        
        try:
            with open(file_path, 'rb') as src_file:
                with open(destination, 'wb') as dst_file:
                    dst_file.write(src_file.read())
                    
            # For PDF management, we would add entry to database
            doc_id = f"doc_{file_name}_{os.path.getmtime(destination)}"
            # In a real implementation, you would store this in a database
                    
            return doc_id
        except Exception as e:
            print(f"Error copying file: {e}")
            return False

    def get_kb_files(self, kb_name):
        """Get list of files in a knowledge base"""
        # Same as before

    def get_kb_list(self):
        """Get list of available knowledge bases"""
        # Same as before

    def process_query(self, data_element, procedure, kb_name):
        """Process query using LLM"""
        # Same as before
    
    def follow_up_query(self, question, conversation_id):
        """Process follow-up question"""
        # Same as before
        
    def get_kb_documents(self, kb_name):
        """Get document details for a knowledge base - for PDF management"""
        # This would normally query a database
        # This is a placeholder implementation
        documents = []
        kb_dir = self.kb_dirs.get(kb_name)
        
        if kb_dir and os.path.exists(kb_dir):
            for file in os.listdir(kb_dir):
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(kb_dir, file)
                    # Create mock document data
                    doc_id = f"doc_{file}"
                    documents.append({
                        "id": doc_id,
                        "kb_id": kb_name,
                        "original_filename": file,
                        "original_path": file_path,
                        "is_scanned": False,  # Default
                        "conversion_status": "not_required",  # Default
                        "conversion_progress": 100,
                        "page_count": 0  # Would be determined by actual code
                    })
        
        return documents
        
    def update_document_conversion(self, doc_id, status, progress=None, 
                                 converted_path=None, page_count=None):
        """Update document conversion status - for PDF management"""
        # This would normally update a database entry
        # This is a placeholder implementation
        print(f"Updating document {doc_id}: status={status}, progress={progress}")
        # In a real implementation, you would update database records


# ResultsTableModel class
# Same as before

# Worker classes (WorkerSignals, LLMWorker, FollowUpWorker)
# Same as before

# NewKBDialog class
# Same as before

# ModernFrame class
# Same as before


# Main application class with PDF management integrated
class DocumentProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.llm_processor = LLMProcessor()
        
        # Initialize UI
        self.setWindowTitle("LLM Document Processor")
        self.setGeometry(100, 100, 1280, 800)
        
        # Apply modern styling
        self.apply_styling()
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # Start with the main selection screen
        self.show_main_screen()
        
        # Initialize other variables
        self.excel_data = None
        self.current_results = []
        self.current_conversation_id = None
        self.selected_row_index = -1
        
        # Setup thread pool for background tasks
        self.threadpool = QThreadPool()

    def apply_styling(self):
        """Apply modern styling to the application"""
        # Same as before

    def show_main_screen(self):
        """Show the initial selection screen with PDF management option"""
        # Clear existing layout
        self.clear_layout(self.main_layout)
        
        # App title
        title_label = QLabel("LLM Document Processor")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078d4; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle = QLabel("Select an option to get started")
        subtitle.setStyleSheet("font-size: 16px; color: #605e5c; margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(subtitle)
        
        # Option buttons layout
        options_layout = QHBoxLayout()
        
        # Create KB button
        create_kb_btn = QPushButton("Create Knowledge Base")
        create_kb_btn.setMinimumHeight(50)
        create_kb_btn.clicked.connect(self.show_add_kb_dialog)
        options_layout.addWidget(create_kb_btn)
        
        # Process data button
        process_btn = QPushButton("Process Documents")
        process_btn.setMinimumHeight(50)
        process_btn.clicked.connect(self.show_process_screen)
        options_layout.addWidget(process_btn)
        
        # PDF Management button - new option
        pdf_mgmt_btn = QPushButton("Manage PDF Documents")
        pdf_mgmt_btn.setMinimumHeight(50)
        pdf_mgmt_btn.clicked.connect(self.show_pdf_management)
        pdf_mgmt_btn.setStyleSheet("background-color: #8e44ad;")
        options_layout.addWidget(pdf_mgmt_btn)
        
        self.main_layout.addLayout(options_layout)
        
        # Available KBs
        kb_list = self.llm_processor.get_kb_list()
        kb_frame = ModernFrame("Available Knowledge Bases")
        
        if kb_list:
            kb_list_widget = QListWidget()
            for kb in kb_list:
                item = QListWidgetItem(kb)
                kb_list_widget.addItem(item)
            kb_frame.layout.addWidget(kb_list_widget)
        else:
            no_kb_label = QLabel("No knowledge bases available. Create one to get started.")
            kb_frame.layout.addWidget(no_kb_label)
        
        self.main_layout.addWidget(kb_frame)

    def show_add_kb_dialog(self):
        """Show dialog to create a new knowledge base"""
        # Same as before

    def show_process_screen(self):
        """Show the processing screen"""
        # Same as before

    def load_excel(self):
        """Load data from Excel file"""
        # Same as before

    def process_data(self):
        """Process data using LLM"""
        # Same as before
    
    def handle_processing_results(self, results):
        """Handle results from LLM processing"""
        # Same as before
    
    def handle_processing_error(self, error_message):
        """Handle errors from LLM processing"""
        # Same as before
    
    def handle_table_click(self, index):
        """Handle clicks on the results table"""
        # Same as before
    
    def load_pdf_document(self, file_path, page=None):
        """Load a PDF document into the viewer"""
        # Same as before
        
    def send_followup(self):
        """Send a follow-up question"""
        # Same as before
    
    def handle_followup_result(self, result):
        """Handle result from follow-up query"""
        # Same as before
    
    def handle_followup_error(self, error_message):
        """Handle error from follow-up query"""
        # Same as before
    
    def clear_layout(self, layout):
        """Clear all items from a layout"""
        if layout is None:
            return
            
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout(item.layout())
                item.layout().deleteLater()
    
    def show_pdf_management(self):
        """Show the PDF management dialog"""
        # Create and show the PDF Management dialog
        dialog = PDFManagementDialog(self.llm_processor, self)
        dialog.exec()
        
        # After closing the dialog, refresh the main screen
        # This ensures the KB list is updated if any changes were made
        self.show_main_screen()


# Main application entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    main_window = DocumentProcessorApp()
    main_window.show()
    
    sys.exit(app.exec())
