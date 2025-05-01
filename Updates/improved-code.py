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


# Assuming you have a module for handling LLM API calls
class LLMProcessor:
    def __init__(self):
        self.kb_dirs = {}  # Store KB names and their directories
        self.conversation_ids = {}  # Store conversation IDs for follow-ups
        self.base_dir = "uploads"
        
        # Create base directory if it doesn't exist
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
        # Scan for existing KBs
        self._scan_existing_kbs()
    
    def _scan_existing_kbs(self):
        """Scan for existing knowledge bases in the uploads directory"""
        if os.path.exists(self.base_dir):
            for item in os.listdir(self.base_dir):
                full_path = os.path.join(self.base_dir, item)
                if os.path.isdir(full_path):
                    self.kb_dirs[item] = full_path

    def create_kb(self, kb_name):
        """Create a new knowledge base directory"""
        kb_dir = os.path.join(self.base_dir, kb_name)
        if not os.path.exists(kb_dir):
            os.makedirs(kb_dir)
            self.kb_dirs[kb_name] = kb_dir
            return True
        return False
    
    def add_document_to_kb(self, kb_name, file_path):
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
            return True
        except Exception as e:
            print(f"Error copying file: {e}")
            return False

    def get_kb_files(self, kb_name):
        """Get list of files in a knowledge base"""
        if kb_name not in self.kb_dirs:
            return []
            
        kb_dir = self.kb_dirs[kb_name]
        files = []
        
        if os.path.exists(kb_dir):
            for item in os.listdir(kb_dir):
                if item.lower().endswith('.pdf'):
                    files.append(os.path.join(kb_dir, item))
                    
        return files

    def get_kb_list(self):
        """Get list of available knowledge bases"""
        return list(self.kb_dirs.keys())

    def process_query(self, data_element, procedure, kb_name):
        """
        Replace this with your actual LLM API code
        This should return the result and page number where info was found
        """
        # This is a placeholder - replace with your actual LLM API call
        try:
            # In a real implementation, you would query against the files in the KB
            files = self.get_kb_files(kb_name)
            file_path = files[0] if files else "No file available"
            
            # Simulate finding information in a document
            result = f"Result for {data_element} using {procedure} from KB: {kb_name}"
            page_number = 2  # Example page number
            
            # Generate a conversation ID (in a real app, this would come from your LLM API)
            conversation_id = f"conv_{data_element}_{procedure}".replace(" ", "_")
            self.conversation_ids[(data_element, procedure, kb_name)] = conversation_id
            
            return {
                "result": result, 
                "page": page_number, 
                "conversation_id": conversation_id,
                "file": file_path,  # Return the file path
                "kb_name": kb_name
            }
        except Exception as e:
            print(f"Error processing query: {e}")
            return {"result": f"Error: {str(e)}", "page": None, "conversation_id": None, "file": None, "kb_name": kb_name}
    
    def follow_up_query(self, question, conversation_id):
        """
        Process a follow-up question using the existing conversation context
        Replace with your actual follow-up API call
        """
        # This is a placeholder - replace with your actual follow-up API call
        try:
            # Simulate a follow-up response
            response = f"Follow-up answer to: {question}"
            return {"response": response, "conversation_id": conversation_id}
        except Exception as e:
            print(f"Error processing follow-up: {e}")
            return {"response": f"Error: {str(e)}", "conversation_id": conversation_id}


# Custom Table Model for results display
class ResultsTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data if data is not None else []
        self._headers = ["Data Element", "Procedure", "Knowledge Base", "Result", "Page"]
        
    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None
            
        row = index.row()
        col = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return self._data[row]["data_element"]
            elif col == 1:
                return self._data[row]["procedure"]
            elif col == 2:
                return self._data[row]["kb_name"]
            elif col == 3:
                return self._data[row]["result"]
            elif col == 4:
                return str(self._data[row]["page"]) if self._data[row]["page"] is not None else "N/A"
                
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Alternate row colors for better readability
            if row % 2 == 0:
                return QColor(245, 245, 245)
                
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 4:  # Center-align page numbers
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                
        return None
        
    def rowCount(self, parent=None):
        return len(self._data)
        
    def columnCount(self, parent=None):
        return len(self._headers)
        
    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None
        
    def set_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()


# Worker signals and classes for background processing
class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    followup_finished = pyqtSignal(object)

class LLMWorker(QRunnable):
    def __init__(self, processor, data_elements, procedures, kb_name):
        super().__init__()
        self.processor = processor
        self.data_elements = data_elements
        self.procedures = procedures
        self.kb_name = kb_name
        self.signals = WorkerSignals()

    def run(self):
        try:
            results = []
            for i in range(len(self.data_elements)):
                result = self.processor.process_query(
                    self.data_elements[i],
                    self.procedures[i],
                    self.kb_name
                )
                results.append({
                    "data_element": self.data_elements[i],
                    "procedure": self.procedures[i],
                    "kb_name": self.kb_name,
                    "result": result["result"],
                    "page": result["page"],
                    "conversation_id": result["conversation_id"],
                    "file": result["file"]
                })
            self.signals.finished.emit(results)
        except Exception as e:
            self.signals.error.emit(str(e))

class FollowUpWorker(QRunnable):
    def __init__(self, processor, question, conversation_id):
        super().__init__()
        self.processor = processor
        self.question = question
        self.conversation_id = conversation_id
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.processor.follow_up_query(self.question, self.conversation_id)
            self.signals.followup_finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


# Dialog for creating a new Knowledge Base
class NewKBDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Knowledge Base")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # KB name input
        form_layout = QFormLayout()
        self.kb_name_input = QLineEdit()
        form_layout.addRow("Knowledge Base Name:", self.kb_name_input)
        layout.addLayout(form_layout)
        
        # File selection
        layout.addWidget(QLabel("Select Documents:"))
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)
        
        file_btn_layout = QHBoxLayout()
        add_file_btn = QPushButton("Add Files")
        add_file_btn.clicked.connect(self.add_files)
        remove_file_btn = QPushButton("Remove Selected")
        remove_file_btn.clicked.connect(self.remove_selected_file)
        file_btn_layout.addWidget(add_file_btn)
        file_btn_layout.addWidget(remove_file_btn)
        layout.addLayout(file_btn_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.selected_files = []
        
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents", "", "PDF Files (*.pdf)"
        )
        
        if files:
            for file in files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
                    item = QListWidgetItem(os.path.basename(file))
                    item.setToolTip(file)  # Store full path as tooltip
                    self.file_list.addItem(item)
    
    def remove_selected_file(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            file_path = item.toolTip()
            self.selected_files.remove(file_path)
            self.file_list.takeItem(self.file_list.row(item))
    
    def validate_and_accept(self):
        kb_name = self.kb_name_input.text().strip()
        if not kb_name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for the knowledge base.")
            return
            
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select at least one document file.")
            return
            
        self.accept()
    
    def get_data(self):
        return {
            "kb_name": self.kb_name_input.text().strip(),
            "files": self.selected_files
        }


# Modern styled frame 
class ModernFrame(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333333;")
            self.layout.addWidget(title_label)


# Main application class
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
        # Use custom styling for a modern look
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                color: #323130;
            }
            QTableView {
                border: 1px solid #edebe9;
                gridline-color: #f3f2f1;
                selection-background-color: #e1dfdd;
                selection-color: #201f1e;
            }
            QHeaderView::section {
                background-color: #f3f2f1;
                border: 1px solid #edebe9;
                padding: 6px;
                font-weight: bold;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #8a8886;
                border-radius: 2px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #0078d4;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #8a8886;
                border-radius: 2px;
            }
            QComboBox:focus {
                border: 1px solid #0078d4;
            }
        """)

    def show_main_screen(self):
        """Show the initial selection screen"""
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
        dialog = NewKBDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            kb_name = data["kb_name"]
            files = data["files"]
            
            # Create the knowledge base
            if self.llm_processor.create_kb(kb_name):
                # Add documents to the KB
                success_count = 0
                for file in files:
                    if self.llm_processor.add_document_to_kb(kb_name, file):
                        success_count += 1
                
                QMessageBox.information(self, "KB Created", 
                                      f"Knowledge base '{kb_name}' created successfully with {success_count} documents.")
                
                # Refresh the main screen
                self.show_main_screen()
            else:
                QMessageBox.warning(self, "KB Error", f"Knowledge base '{kb_name}' already exists.")

    def show_process_screen(self):
        """Show the processing screen (matches the design in the image)"""
        # Check if there are any KBs available
        kb_list = self.llm_processor.get_kb_list()
        if not kb_list:
            QMessageBox.warning(self, "No Knowledge Bases", 
                              "No knowledge bases available. Please create one first.")
            return
        
        # Clear existing layout
        self.clear_layout(self.main_layout)
        
        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setMaximumWidth(100)
        back_btn.clicked.connect(self.show_main_screen)
        self.main_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Top control panel
        control_panel = ModernFrame()
        control_layout = QGridLayout()
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # KB Selection
        kb_label = QLabel("Select Knowledge Base:")
        self.kb_combo = QComboBox()
        self.kb_combo.addItems(kb_list)
        self.kb_combo.setStyleSheet("border: 1px solid black; padding: 5px;")
        control_layout.addWidget(kb_label, 0, 0)
        control_layout.addWidget(self.kb_combo, 0, 1)
        
        # Excel input section
        excel_btn = QPushButton("Load Excel")
        excel_btn.clicked.connect(self.load_excel)
        excel_btn.setStyleSheet("background-color: #4CAF50;")
        self.excel_status = QLabel("No Excel file loaded")
        control_layout.addWidget(QLabel("Excel File:"), 1, 0)
        control_layout.addWidget(excel_btn, 1, 1)
        control_layout.addWidget(self.excel_status, 1, 2)
        
        # Process button
        self.process_btn = QPushButton("Process")
        self.process_btn.clicked.connect(self.process_data)
        self.process_btn.setEnabled(False)
        self.process_btn.setStyleSheet("background-color: #FF5722;")
        control_layout.addWidget(self.process_btn, 0, 2)
        
        control_panel.setLayout(control_layout)
        self.main_layout.addWidget(control_panel)
        
        # Main content area - using splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - contains a vertical splitter for results and follow-up
        left_panel = QSplitter(Qt.Orientation.Vertical)
        
        # Results panel
        results_panel = ModernFrame("Analysis Results")
        results_layout = QVBoxLayout()
        
        # Results table
        self.results_table = QTableView()
        self.table_model = ResultsTableModel()
        self.results_table.setModel(self.table_model)
        
        # Configure table appearance for modern look
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setShowGrid(True)
        self.results_table.clicked.connect(self.handle_table_click)
        
        results_layout.addWidget(self.results_table)
        results_panel.setLayout(results_layout)
        
        # Follow-up panel
        followup_panel = ModernFrame("Follow Up")
        followup_layout = QVBoxLayout()
        
        self.selected_element_label = QLabel("No item selected")
        self.selected_element_label.setStyleSheet("font-weight: bold;")
        followup_layout.addWidget(self.selected_element_label)
        
        # Question input with send button
        question_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Type your follow-up question here...")
        self.question_input.setEnabled(False)
        self.question_input.returnPressed.connect(self.send_followup)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_followup)
        
        question_layout.addWidget(self.question_input, 4)
        question_layout.addWidget(self.send_btn, 1)
        followup_layout.addLayout(question_layout)
        
        # Conversation history
        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setPlaceholderText("Follow-up conversation will appear here.")
        followup_layout.addWidget(self.conversation_display)
        
        followup_panel.setLayout(followup_layout)
        
        # Add both panels to left splitter
        left_panel.addWidget(results_panel)
        left_panel.addWidget(followup_panel)
        left_panel.setSizes([500, 300])  # Set initial sizes
        
        # Right panel - Document viewer
        right_panel = ModernFrame("Document Viewer")
        right_layout = QVBoxLayout()
        
        self.pdf_filename_label = QLabel("No document selected")
        self.pdf_filename_label.setStyleSheet("font-style: italic; color: #666;")
        right_layout.addWidget(self.pdf_filename_label)
        
        self.pdf_viewer = QPdfView()
        self.pdf_document = QPdfDocument()
        self.pdf_viewer.setDocument(self.pdf_document)
        right_layout.addWidget(self.pdf_viewer)
        
        right_panel.setLayout(right_layout)
        
        # Add panels to main splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 600])  # Set initial sizes
        
        # Add splitter to main layout
        self.main_layout.addWidget(splitter)

    def load_excel(self):
        """Load data from Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel Input File", "", "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            try:
                df = pd.read_excel(file_path)
                required_columns = ["data elements", "procedure"]
                
                # Check if Excel has the required columns
                if not all(col in df.columns for col in required_columns):
                    QMessageBox.warning(self, "Invalid Excel Format", 
                                      f"Excel file must contain these columns: {', '.join(required_columns)}")
                    return
                
                self.excel_data = df
                self.excel_status.setText(f"Loaded {len(df)} queries from '{os.path.basename(file_path)}'")
                self.process_btn.setEnabled(True)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Excel file: {str(e)}")

    def process_data(self):
        """Process data using LLM"""
        if self.excel_data is None:
            QMessageBox.warning(self, "No Data", "Please load an Excel file first")
            return
            
        selected_kb = self.kb_combo.currentText()
        if not selected_kb:
            QMessageBox.warning(self, "No KB Selected", "Please select a knowledge base")
            return
            
        kb_files = self.llm_processor.get_kb_files(selected_kb)
        if not kb_files:
            QMessageBox.warning(self, "Empty KB", f"The selected knowledge base '{selected_kb}' doesn't contain any documents")
            return
        
        # Extract data from Excel
        data_elements = self.excel_data["data elements"].tolist()
        procedures = self.excel_data["procedure"].tolist()
        
        # Show processing indicator
        self.process_btn.setEnabled(False)
        self.process_btn.setText("Processing...")
        
        # Create and run worker thread
        worker = LLMWorker(self.llm_processor, data_elements, procedures, selected_kb)
        worker.signals.finished.connect(self.handle_processing_results)
        worker.signals.error.connect(self.handle_processing_error)
        
        # Start the worker
        self.threadpool.start(worker)
    
    def handle_processing_results(self, results):
        """Handle results from LLM processing"""
        self.current_results = results
        self.table_model.set_data(results)
        
        # Re-enable processing button
        self.process_btn.setText("Process")
        self.process_btn.setEnabled(True)
        
        # Show success message
        count = len(results)
        QMessageBox.information(self, "Processing Complete", f"Successfully processed {count} queries")
    
    def handle_processing_error(self, error_message):
        """Handle errors from LLM processing"""
        # Re-enable processing button
        self.process_btn.setText("Process")
        self.process_btn.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Processing Error", f"Error processing data: {error_message}")
    
    def handle_table_click(self, index):
        """Handle clicks on the results table"""
        self.selected_row_index = index.row()
        
        if 0 <= self.selected_row_index < len(self.current_results):
            selected_result = self.current_results[self.selected_row_index]
            
            # Update selected element label
            self.selected_element_label.setText(
                f"Selected: {selected_result['data_element']} - {selected_result['procedure']}"
            )
            
            # Enable follow-up question controls
            self.question_input.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.current_conversation_id = selected_result.get("conversation_id")
            
            # Clear previous conversation
            self.conversation_display.clear()
            self.conversation_display.append(f"<b>Initial Query:</b> {selected_result['data_element']} - {selected_result['procedure']}")
            self.conversation_display.append(f"<b>Response:</b> {selected_result['result']}<br>")
            
            # Load the PDF if available
            self.load_pdf_document(selected_result.get("file"), selected_result.get("page"))
    
    def load_pdf_document(self, file_path, page=None):
        """Load a PDF document into the viewer"""
        if not file_path or not os.path.exists(file_path):
            self.pdf_filename_label.setText("No document available")
            return
            
        try:
            # Load the PDF document
            self.pdf_document.close()
            