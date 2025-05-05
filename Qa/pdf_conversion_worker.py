import os
import sys
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

# Import PDFProcessor from the convert_to_pdf module
sys.path.append("Fixes")  # Adjust path as needed
from convert_to_pdf import PDFProcessor


class PDFConversionSignals(QObject):
    """
    Signals for PDF conversion process
    """
    started = pyqtSignal(int)  # document_id
    progress = pyqtSignal(int, float)  # document_id, progress (0-100)
    page_processed = pyqtSignal(int, int, int)  # document_id, current_page, total_pages
    completed = pyqtSignal(int, str, int)  # document_id, output_path, page_count
    error = pyqtSignal(int, str)  # document_id, error_message


class CustomTQDM:
    """
    Custom TQDM-like progress tracker that emits signals for UI updates
    """
    def __init__(self, signals, doc_id, total):
        self.signals = signals
        self.doc_id = doc_id
        self.total = total
        self.n = 0
        self.last_progress = 0
    
    def update(self, n=1):
        """Update progress by n units"""
        self.n += n
        # Calculate progress as percentage
        progress = (self.n / self.total) * 100 if self.total > 0 else 0
        
        # Only emit signal if progress changed significantly (reduces UI updates)
        if progress - self.last_progress >= 1.0 or progress >= 100:
            self.signals.progress.emit(self.doc_id, progress)
            self.signals.page_processed.emit(self.doc_id, self.n, self.total)
            self.last_progress = progress


class PDFConversionWorker(QRunnable):
    """
    Worker for handling PDF conversion in background thread
    """
    def __init__(self, doc_id, file_path, output_dir, use_llm=False):
        super().__init__()
        self.doc_id = doc_id
        self.file_path = file_path
        self.output_dir = output_dir
        self.use_llm = use_llm
        self.signals = PDFConversionSignals()
    
    @pyqtSlot()
    def run(self):
        """Execute the PDF conversion process"""
        try:
            self.signals.started.emit(self.doc_id)
            
            # Initialize custom progress tracker
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            
            # Initialize the PDF processor
            processor = PDFProcessor(output_dir=self.output_dir)
            
            # Get page count first to have total for progress tracking
            try:
                images = processor.convert_pdf_to_images(self.file_path)
                total_pages = len(images)
            except Exception as e:
                self.signals.error.emit(self.doc_id, f"Error getting page count: {str(e)}")
                return
            
            # Create a custom progress tracking function for tqdm
            def custom_progress_callback(current_page, total_pages):
                progress = (current_page / total_pages) * 100
                self.signals.progress.emit(self.doc_id, progress)
                self.signals.page_processed.emit(self.doc_id, current_page, total_pages)
            
            # Monkey patch tqdm in the processor to use our progress callback
            def process_page_with_progress(self, args):
                page_num, image, use_llm = args
                
                # Call progress callback
                custom_progress_callback(page_num + 1, total_pages)
                
                # Call original method
                return processor.process_page(args)
            
            # Replace the process_page method temporarily
            original_process_page = processor.process_page
            processor.process_page = process_page_with_progress.__get__(processor, type(processor))
            
            # Process the PDF
            output_path = processor.process_pdf(self.file_path, use_llm=self.use_llm)
            
            # Restore original method
            processor.process_page = original_process_page
            
            # Signal completion
            self.signals.completed.emit(self.doc_id, output_path, total_pages)
            
        except Exception as e:
            self.signals.error.emit(self.doc_id, f"Conversion error: {str(e)}")


class BatchConversionWorker(QRunnable):
    """
    Worker for processing a batch of PDF conversions sequentially
    """
    def __init__(self, db_manager, output_base_dir):
        super().__init__()
        self.db_manager = db_manager
        self.output_base_dir = output_base_dir
        self.signals = PDFConversionSignals()
        self.is_running = True  # Flag to allow stopping the worker
    
    def stop(self):
        """Stop the batch processing"""
        self.is_running = False
    
    @pyqtSlot()
    def run(self):
        """Process all pending conversions"""
        # Get all pending documents
        pending_docs = self.db_manager.get_pending_conversions()
        
        for doc in pending_docs:
            if not self.is_running:
                break  # Stop if requested
                
            doc_id = doc["id"]
            file_path = doc["original_path"]
            kb_name = doc["kb_name"]
            
            # Update status to in_progress
            self.db_manager.update_document_conversion(doc_id, "in_progress", progress=0)
            
            # Create output directory for this KB
            output_dir = os.path.join(self.output_base_dir, kb_name, "converted")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            try:
                # Signal that conversion started
                self.signals.started.emit(doc_id)
                
                # Initialize the PDF processor
                processor = PDFProcessor(output_dir=output_dir)
                
                # Get page count first
                images = processor.convert_pdf_to_images(file_path)
                total_pages = len(images)
                
                # Create a custom progress tracking function
                def custom_progress_callback(current_page, total_pages):
                    progress = (current_page / total_pages) * 100
                    self.signals.progress.emit(doc_id, progress)
                    self.signals.page_processed.emit(doc_id, current_page, total_pages)
                    # Update progress in database
                    self.db_manager.update_document_conversion(doc_id, "in_progress", progress=progress)
                
                # Replace the process_page method temporarily
                def process_page_with_progress(self, args):
                    page_num, image, use_llm = args
                    
                    # Call progress callback
                    custom_progress_callback(page_num + 1, total_pages)
                    
                    # Call original method
                    return processor.process_page(args)
                
                original_process_page = processor.process_page
                processor.process_page = process_page_with_progress.__get__(processor, type(processor))
                
                # Process the PDF (without LLM for batch processing)
                output_path = processor.process_pdf(file_path, use_llm=False)
                
                # Restore original method
                processor.process_page = original_process_page
                
                # Update database with completed status
                self.db_manager.update_document_conversion(
                    doc_id, "completed", progress=100, 
                    converted_path=output_path, page_count=total_pages
                )
                
                # Signal completion
                self.signals.completed.emit(doc_id, output_path, total_pages)
                
            except Exception as e:
                error_msg = f"Conversion error: {str(e)}"
                self.db_manager.update_document_conversion(doc_id, "failed", progress=0)
                self.signals.error.emit(doc_id, error_msg)