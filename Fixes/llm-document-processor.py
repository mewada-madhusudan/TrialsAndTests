import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView

# Assuming you have a module for handling LLM API calls
# Replace this with your actual LLM interaction code
class LLMProcessor:
    def __init__(self):
        self.uploaded_docs = []

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
            return {"result": result, "page": page_number}
        except Exception as e:
            print(f"Error processing query: {e}")
            return {"result": "Error", "page": None}

# Worker for running LLM operations in background
class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

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
                    "page": result["page"]
                })
            self.signals.finished.emit(results)
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
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create splitter for table and PDF view
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Controls and results
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Controls for document upload
        upload_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Documents")
        self.upload_btn.clicked.connect(self.upload_documents)
        self.upload_status = QLabel("No documents uploaded")
        upload_layout.addWidget(self.upload_btn)
        upload_layout.addWidget(self.upload_status)
        left_layout.addLayout(upload_layout)
        
        # Controls for Excel input
        excel_layout = QHBoxLayout()
        self.excel_btn = QPushButton("Load Excel Input")
        self.excel_btn.clicked.connect(self.load_excel)
        self.excel_status = QLabel("No Excel file loaded")
        excel_layout.addWidget(self.excel_btn)
        excel_layout.addWidget(self.excel_status)
        left_layout.addLayout(excel_layout)
        
        # Process button
        self.process_btn = QPushButton("Process Data")
        self.process_btn.clicked.connect(self.process_data)
        self.process_btn.setEnabled(False)
        left_layout.addWidget(self.process_btn)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Data Element", "Procedure", "File", "Result", "Page"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.cellClicked.connect(self.show_pdf_page)
        left_layout.addWidget(self.results_table)
        
        # Right side - PDF viewer
        right_widget = QWidget()  # Create a container for the PDF viewer
        right_layout = QVBoxLayout(right_widget)
        self.pdf_viewer = QPdfView(right_widget)  # Pass the parent widget
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer.setDocument(self.pdf_document)
        right_layout.addWidget(self.pdf_viewer)
        
        # Add widgets to splitter
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([600, 600])
        
        main_layout.addWidget(self.splitter)
        
        # Setup thread pool for background tasks
        self.threadpool = QThreadPool()
        
        # Data storage
        self.excel_data = None
        self.current_results = []

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
            
            self.upload_status.setText(f"{count} documents uploaded to {self.upload_folder}")
            
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
                self.excel_status.setText(f"Loaded {len(df)} queries from Excel")
                
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
        
        # Set up table
        self.results_table.setRowCount(len(results))
        
        # Fill table with results
        for row, item in enumerate(results):
            data_element_item = QTableWidgetItem(item["data_element"])
            procedure_item = QTableWidgetItem(item["procedure"])
            file_item = QTableWidgetItem(item["file"])
            result_item = QTableWidgetItem(item["result"])
            page_item = QTableWidgetItem(str(item["page"]) if item["page"] is not None else "N/A")
            
            # Make items read-only
            data_element_item.setFlags(data_element_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            procedure_item.setFlags(procedure_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            file_item.setFlags(file_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            result_item.setFlags(result_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            page_item.setFlags(page_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.results_table.setItem(row, 0, data_element_item)
            self.results_table.setItem(row, 1, procedure_item)
            self.results_table.setItem(row, 2, file_item)
            self.results_table.setItem(row, 3, result_item)
            self.results_table.setItem(row, 4, page_item)
        
        # Re-enable processing button
        self.process_btn.setEnabled(True)
        self.process_btn.setText("Process Data")
        
        QMessageBox.information(self, "Processing Complete", f"Processed {len(results)} queries")

    def handle_error(self, error_msg):
        QMessageBox.critical(self, "Processing Error", error_msg)
        self.process_btn.setEnabled(True)
        self.process_btn.setText("Process Data")

    def show_pdf_page(self, row, column):
        if not self.current_results or row >= len(self.current_results):
            return
            
        result_item = self.current_results[row]
        file_path = result_item["file"]
        page_number = result_item.get("page")
        
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
                QMessageBox.warning(self, "File Not Found", f"Could not locate file: {file_path}")
                return
        
        # Load PDF
        if os.path.exists(full_path):
            self.pdf_document.load(full_path)
            
            if self.pdf_document.status() == QPdfDocument.Status.Ready:
                if page_number is not None and page_number > 0:
                    # QPdfView uses 0-based indices
                    self.pdf_viewer.pageNavigator().jump(page_number - 1)
                self.pdf_viewer.setVisible(True)
            else:
                QMessageBox.warning(self, "PDF Error", f"Could not load PDF: {full_path}")
        else:
            QMessageBox.warning(self, "File Not Found", f"Could not find file: {full_path}")

def main():
    app = QApplication(sys.argv)
    window = DocumentProcessorApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
