from PyQt6.QtCore import QRunnable, pyqtSignal, QObject, QThread
import os
import time
import traceback

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    progress = pyqtSignal(str, int)  # doc_id, progress percentage
    completed = pyqtSignal(str, str, int)  # doc_id, output_path, page_count
    error = pyqtSignal(str, str)  # doc_id, error message


class PDFConversionWorker(QRunnable):
    """
    Worker thread for PDF OCR conversion
    """
    def __init__(self, doc_id, input_path, output_dir):
        super().__init__()
        self.doc_id = doc_id
        self.input_path = input_path
        self.output_dir = output_dir
        self.signals = WorkerSignals()
        self.should_stop = False
    
    def run(self):
        """Execute the OCR conversion"""
        try:
            # Create output filename
            filename = os.path.basename(self.input_path)
            output_filename = f"{os.path.splitext(filename)[0]}_converted.pdf"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Check if output directory exists
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            
            # This would be where you implement your actual OCR logic
            # For example, using pytesseract, PyMuPDF, or other libraries
            
            # For this example, we'll simulate the OCR process
            total_pages = self._simulate_ocr(output_path)
            
            # Signal completion
            self.signals.completed.emit(self.doc_id, output_path, total_pages)
            
        except Exception as e:
            # Signal error with traceback
            error_message = f"{str(e)}\n{traceback.format_exc()}"
            self.signals.error.emit(self.doc_id, error_message)
    
    def _simulate_ocr(self, output_path):
        """Simulate OCR processing for example purposes"""
        # In a real implementation, you would use OCR libraries here
        import random
        from PyPDF2 import PdfReader
        
        # Try to get actual page count
        try:
            with open(self.input_path, 'rb') as f:
                pdf = PdfReader(f)
                total_pages = len(pdf.pages)
        except:
            # If we can't read the PDF, use random page count for simulation
            total_pages = random.randint(1, 30)
        
        # Simulate processing each page
        for page in range(total_pages):
            if self.should_stop:
                break
                
            # Calculate progress percentage
            progress = int((page + 1) / total_pages * 100)
            self.signals.progress.emit(self.doc_id, progress)
            
            # Simulate processing time
            time.sleep(0.1)
        
        # Create a dummy output file
        with open(output_path, 'w') as f:
            f.write("This is a simulated OCR output")
        
        return total_pages
    
    def stop(self):
        """Request worker to stop processing"""
        self.should_stop = True


class BatchConversionWorker(QRunnable):
    """
    Worker thread for batch conversion of multiple documents
    """
    def __init__(self, db_manager, output_dir):
        super().__init__()
        self.db_manager = db_manager
        self.output_dir = output_dir
        self.should_stop = False
        
        class BatchSignals(QObject):
            progress = pyqtSignal(str, int)  # doc_id, progress
            completed = pyqtSignal(str, str, int)  # doc_id, output_path, page_count
            error = pyqtSignal(str, str)  # doc_id, error message
        
        self.signals = BatchSignals()
    
    def run(self):
        """Execute batch conversion"""
        try:
            # Get all pending documents that need conversion
            pending_docs = self.db_manager.get_documents_by_status(["pending"])
            
            for doc in pending_docs:
                if self.should_stop:
                    break
                
                # Check if document exists
                if not os.path.exists(doc["original_path"]):
                    self.signals.error.emit(
                        doc["id"], 
                        f"Original file not found: {doc['original_path']}"
                    )
                    continue
                
                # Create individual conversion worker
                worker = PDFConversionWorker(doc["id"], doc["original_path"], self.output_dir)
                
                # Connect signals
                worker.signals.progress.connect(
                    lambda doc_id, progress: self.signals.progress.emit(doc_id, progress)
                )
                worker.signals.completed.connect(
                    lambda doc_id, path, pages: self.signals.completed.emit(doc_id, path, pages)
                )
                worker.signals.error.connect(
                    lambda doc_id, error: self.signals.error.emit(doc_id, error)
                )
                
                # Run conversion synchronously in this thread
                worker.run()
                
                if self.should_stop:
                    break
                
        except Exception as e:
            # Since this is a batch worker, we don't have a specific doc_id for the error
            self.signals.error.emit("batch", str(e))
    
    def stop(self):
        """Request worker to stop processing"""
        self.should_stop = True
