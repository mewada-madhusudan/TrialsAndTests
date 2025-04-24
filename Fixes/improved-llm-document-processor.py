import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTableView, QHeaderView,
                             QSplitter, QMessageBox, QLineEdit, QTextEdit, QFrame, 
                             QGridLayout, QSizePolicy, QStyledItemDelegate, QAbstractItemView)
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QFont, QPalette, QIcon
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView

# Assuming you have a module for handling LLM API calls
# Replace this with your actual LLM interaction code
class LLMProcessor:
    def __init__(self):
        self.uploaded_docs = []
        self.conversation_ids = {}  # Store conversation IDs for follow-ups

    def add_document(self, file_path):
        self.uploaded_docs.append(file_path)
        return True

    def process_query(self, data_element, procedure, file_path):
        """
        Replace this with your actual LLM API code
        This should return the result and page number where info was found
        """
        # This is a placeholder - replace with your actual LLM API call
        try:
            # Simulate finding information in a document
            result = f"Result for {data_element} using {procedure}"
            page_number = 2  # Example page number
            
            # Generate a conversation ID (in a real app, this would come from your LLM API)
            conversation_id = f"conv_{data_element}_{procedure}".replace(" ", "_")
            self.conversation_ids[(data_element, procedure, file_path)] = conversation_id
            
            return {"result": result, "page": page_number, "conversation_id": conversation_id}
        except Exception as e:
            print(f"Error processing query: {e}")
            return {"result": "Error", "page": None, "conversation_id": None}
    
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

# Custom Table Model for better data display
class ResultsTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data if data is not None else []
        self._headers = ["Data Element", "Procedure", "File", "Result", "Page"]
        
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
                return os.path.basename(self._data[row]["file"])  # Just show filename
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

# Worker for running LLM operations in background
class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    followup_finished = pyqtSignal(object)

class LLMWorker(QRunnable):
    def __init__(self, processor, data_elements, procedures, files):
        super().__init__()
        self.processor = processor
        self.data_elements = data_elements
        self.procedures = procedures
        self.files = files
        self.signals = WorkerSignals()

    def run(self):
        try:
            results = []
            for i in range(len(self.data_elements)):
                result = self.processor.process_query(
                    self.data_elements[i],
                    self.procedures[i],
                    self.files[i]
                )
                results.append({
                    "data_element": self.data_elements[i],
                    "procedure": self.procedures[i],
                    "file": self.files[i],
                    "result": result["result"],
                    "page": result["page"],
                    "conversation_id": result["conversation_id"]
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

class DocumentProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.llm_processor = LLMProcessor()
        self.upload_folder = "uploads"
        self.setup_folders()
        
        # Initialize UI
        self.setWindowTitle("LLM Document Processor")
        self.setGeometry(100, 100, 1280, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b78e7;
            }
            QPushButton:pressed {
                background-color: #3367d6;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                color: #333333;
            }
            QTableView {
                border: 1px solid #dddddd;
                gridline-color: #eeeeee;
                selection-background-color: #e0e0ff;
                selection-color: #000000;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #dddddd;
                padding: 4px;
                font-weight: bold;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QFrame.section {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #dddddd;
            }
        """)
        
        # Create main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top section for controls
        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.Shape.StyledPanel)
        top_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        top_layout = QGridLayout(top_frame)
        
        # Document upload section
        upload_btn = QPushButton("Upload Documents")
        upload_btn.setIcon(QIcon.fromTheme("document-open"))
        upload_btn.clicked.connect(self.upload_documents)
        self.upload_status = QLabel("No documents uploaded")
        self.upload_status.setStyleSheet("color: #666;")
        
        # Excel input section
        excel_btn = QPushButton("Load Excel Input")
        excel_btn.setIcon(QIcon.fromTheme("x-office-spreadsheet"))
        excel_btn.clicked.connect(self.load_excel)
        self.excel_status = QLabel("No Excel file loaded")
        self.excel_status.setStyleSheet("color: #666;")
        
        # Process button
        self.process_btn = QPushButton("Process Data")
        self.process_btn.setIcon(QIcon.fromTheme("system-run"))
        self.process_btn.clicked.connect(self.process_data)
        self.process_btn.setEnabled(False)
        
        # Add controls to top layout
        top_layout.addWidget(QLabel("<b>Step 1:</b>"), 0, 0)
        top_layout.addWidget(upload_btn, 0, 1)
        top_layout.addWidget(self.upload_status, 0, 2)
        top_layout.addWidget(QLabel("<b>Step 2:</b>"), 1, 0)
        top_layout.addWidget(excel_btn, 1, 1)
        top_layout.addWidget(self.excel_status, 1, 2)
        top_layout.addWidget(QLabel("<b>Step 3:</b>"), 2, 0)
        top_layout.addWidget(self.process_btn, 2, 1)
        
        # Add top section to main layout
        main_layout.addWidget(top_frame)
        
        # Create splitter for main content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Results table and follow-up section
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Results section
        results_frame = QFrame()
        results_frame.setFrameShape(QFrame.Shape.StyledPanel)
        results_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        results_layout = QVBoxLayout(results_frame)
        
        results_header = QLabel("<h3>Analysis Results</h3>")
        results_layout.addWidget(results_header)
        
        # Use custom QTableView with model instead of QTableWidget
        self.results_table = QTableView()
        self.table_model = ResultsTableModel()
        self.results_table.setModel(self.table_model)
        
        # Configure table appearance
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setShowGrid(True)
        self.results_table.clicked.connect(self.handle_table_click)
        
        results_layout.addWidget(self.results_table)
        
        # Follow-up question section
        followup_frame = QFrame()
        followup_frame.setFrameShape(QFrame.Shape.StyledPanel)
        followup_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        followup_layout = QVBoxLayout(followup_frame)
        
        followup_header = QLabel("<h3>Follow-up Questions</h3>")
        followup_layout.addWidget(followup_header)
        
        self.selected_element_label = QLabel("No item selected")
        self.selected_element_label.setStyleSheet("font-weight: bold; color: #333;")
        followup_layout.addWidget(self.selected_element_label)
        
        # Question input
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
        
        # Add results and follow-up sections to left layout
        left_layout.addWidget(results_frame, 3)
        left_layout.addWidget(followup_frame, 2)
        
        # Right panel - PDF viewer
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # PDF Viewer frame
        pdf_frame = QFrame()
        pdf_frame.setFrameShape(QFrame.Shape.StyledPanel)
        pdf_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        pdf_layout = QVBoxLayout(pdf_frame)
        
        pdf_header = QLabel("<h3>Document Viewer</h3>")
        pdf_layout.addWidget(pdf_header)
        
        self.pdf_filename_label = QLabel("No document selected")
        self.pdf_filename_label.setStyleSheet("font-style: italic; color: #666;")
        pdf_layout.addWidget(self.pdf_filename_label)
        
        self.pdf_viewer = QPdfView()
        self.pdf_document = QPdfDocument()
        self.pdf_viewer.setDocument(self.pdf_document)
        pdf_layout.addWidget(self.pdf_viewer)
        
        right_layout.addWidget(pdf_frame)
        
        # Add widgets to splitter
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([600, 600])
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)
        
        # Setup thread pool for background tasks
        self.threadpool = QThreadPool()
        
        # Data storage
        self.excel_data = None
        self.current_results = []
        self.current_conversation_id = None
        self.selected_row_index = -1

    def setup_folders(self):
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def upload_documents(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents", "", "PDF Files (*.pdf)"
        )
        
        if files:
            count = 0
            for file in files:
                # Copy file to upload folder
                file_name = os.path.basename(file)
                destination = os.path.join(self.upload_folder, file_name)
                
                # If the file doesn't exist in the uploads folder, copy it
                if not os.path.exists(destination):
                    try:
                        # Using the built-in file operations to copy
                        with open(file, 'rb') as src_file:
                            with open(destination, 'wb') as dst_file:
                                dst_file.write(src_file.read())
                        
                        # Add to LLM processor
                        self.llm_processor.add_document(destination)
                        count += 1
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to copy file {file_name}: {str(e)}")
                else:
                    # Just add to LLM processor if already exists
                    self.llm_processor.add_document(destination)
                    count += 1
            
            self.upload_status.setText(f"{count} documents uploaded to '{self.upload_folder}' folder")
            
            if self.excel_data is not None:
                self.process_btn.setEnabled(True)

    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel Input File", "", "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            try:
                df = pd.read_excel(file_path)
                required_columns = ["data elements", "procedure", "files"]
                
                # Check if Excel has the required columns
                if not all(col in df.columns for col in required_columns):
                    QMessageBox.warning(self, "Invalid Excel Format", 
                                       f"Excel file must contain these columns: {', '.join(required_columns)}")
                    return
                
                self.excel_data = df
                self.excel_status.setText(f"Loaded {len(df)} queries from '{os.path.basename(file_path)}'")
                
                if len(self.llm_processor.uploaded_docs) > 0:
                    self.process_btn.setEnabled(True)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Excel file: {str(e)}")

    def process_data(self):
        if self.excel_data is None:
            QMessageBox.warning(self, "No Data", "Please load an Excel file first")
            return
            
        if not self.llm_processor.uploaded_docs:
            QMessageBox.warning(self, "No Documents", "Please upload documents first")
            return
            
        # Disable processing button during operation
        self.process_btn.setEnabled(False)
        self.process_btn.setText("Processing...")
        
        # Get data from Excel
        data_elements = self.excel_data["data elements"].tolist()
        procedures = self.excel_data["procedure"].tolist()
        files = self.excel_data["files"].tolist()
        
        # Create worker to process in background
        worker = LLMWorker(self.llm_processor, data_elements, procedures, files)
        worker.signals.finished.connect(self.display_results)
        worker.signals.error.connect(self.handle_error)
        
        # Start worker
        self.threadpool.start(worker)

    def display_results(self, results):
        self.current_results = results
        
        # Update table with results
        self.table_model.set_data(results)
        
        # Re-enable processing button
        self.process_btn.setEnabled(True)
        self.process_btn.setText("Process Data")
        
        # Reset follow-up section
        self.selected_element_label.setText("No item selected")
        self.question_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.conversation_display.clear()
        
        QMessageBox.information(self, "Processing Complete", f"Processed {len(results)} queries")

    def handle_error(self, error_msg):
        QMessageBox.critical(self, "Processing Error", error_msg)
        self.process_btn.setEnabled(True)
        self.process_btn.setText("Process Data")

    def handle_table_click(self, index):
        # Get the row index
        row = index.row()
        self.selected_row_index = row
        
        if row >= 0 and row < len(self.current_results):
            result_item = self.current_results[row]
            
            # Update selected element label
            self.selected_element_label.setText(
                f"Selected: <b>{result_item['data_element']}</b> ({result_item['procedure']})"
            )
            
            # Enable follow-up input
            self.question_input.setEnabled(True)
            self.send_btn.setEnabled(True)
            
            # Store conversation ID for follow-up
            self.current_conversation_id = result_item.get("conversation_id")
            
            # Clear previous conversation
            self.conversation_display.clear()
            self.conversation_display.setHtml(
                f"<p><b>Initial Result:</b> {result_item['result']}</p>"
                "<p><i>Ask a follow-up question to learn more...</i></p>"
            )
            
            # Show PDF
            self.show_pdf(result_item["file"], result_item.get("page"))

    def show_pdf(self, file_path, page_number=None):
        # Check if file exists
        full_path = ""
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            # Try finding in upload folder
            potential_path = os.path.join(self.upload_folder, os.path.basename(file_path))
            if os.path.exists(potential_path):
                full_path = potential_path
            else:
                self.pdf_filename_label.setText(f"File not found: {os.path.basename(file_path)}")
                return
        
        # Load PDF
        if os.path.exists(full_path):
            self.pdf_document.load(full_path)
            self.pdf_filename_label.setText(f"Viewing: {os.path.basename(full_path)}")
            
            if self.pdf_document.status() == QPdfDocument.Status.Ready:
                if page_number is not None and page_number > 0:
                    # QPdfView uses 0-based indices
                    self.pdf_viewer.pageNavigator().jump(page_number - 1)
                self.pdf_viewer.setVisible(True)
            else:
                self.pdf_filename_label.setText(f"Error loading: {os.path.basename(full_path)}")
        else:
            self.pdf_filename_label.setText("File not found")

    def send_followup(self):
        question = self.question_input.text().strip()
        if not question:
            return
            
        if self.current_conversation_id is None:
            QMessageBox.warning(self, "No Context", "Please select an item from the results table first")
            return
            
        # Disable send button while processing
        self.send_btn.setEnabled(False)
        self.question_input.setEnabled(False)
        
        # Show question in conversation display
        current_html = self.conversation_display.toHtml()
        self.conversation_display.setHtml(
            f"{current_html}<p><b>You:</b> {question}</p>"
            "<p><i>Processing...</i></p>"
        )
        
        # Run follow-up in background
        worker = FollowUpWorker(self.llm_processor, question, self.current_conversation_id)
        worker.signals.followup_finished.connect(self.display_followup_result)
        worker.signals.error.connect(self.handle_followup_error)
        
        # Start worker
        self.threadpool.start(worker)
        
        # Clear input field
        self.question_input.clear()

    def display_followup_result(self, result):
        # Replace the "Processing..." text with the actual response
        current_html = self.conversation_display.toHtml()
        current_html = current_html.replace("<p><i>Processing...</i></p>", "")
        
        self.conversation_display.setHtml(
            f"{current_html}<p><b>Assistant:</b> {result['response']}</p>"
        )
        
        # Re-enable input
        self.send_btn.setEnabled(True)
        self.question_input.setEnabled(True)
        self.question_input.setFocus()

    def handle_followup_error(self, error_msg):
        # Update conversation display with error
        current_html = self.conversation_display.toHtml()
        current_html = current_html.replace("<p><i>Processing...</i></p>", "")
        
        self.conversation_display.setHtml(
            f"{current_html}<p style='color: red;'><b>Error:</b> {error_msg}</p>"
        )
        
        # Re-enable input
        self.send_btn.setEnabled(True)
        self.question_input.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    window = DocumentProcessorApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
