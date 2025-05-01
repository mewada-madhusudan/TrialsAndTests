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
        self.process_btn.setText("Process Data")
        self.process_btn.setEnabled(True)
        
        # Show success message
        count = len(results)
        if HAS_FLUENT:
            InfoBar.success(
                title="Processing Complete",
                content=f"Successfully processed {count} queries",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
        else:
            QMessageBox.information(self, "Processing Complete", f"Successfully processed {count} queries")
    
    def handle_processing_error(self, error_message):
        """Handle errors from LLM processing"""
        # Re-enable processing button
        self.process_btn.setText("Process Data")
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
            self.pdf_document.load(file_path)
            
            # Set the document in the viewer
            self.pdf_viewer.setDocument(self.pdf_document)
            
            # Set zoom mode for better viewing
            self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitInView)
            
            # Update file name label
            self.pdf_filename_label.setText(os.path.basename(file_path))
            
            # Jump to the specific page if provided
            if page is not None and page > 0 and page <= self.pdf_document.pageCount():
                # QPdfView uses 0-based page indexing
                self.pdf_viewer.setCurrentPage(page - 1)
                
        except Exception as e:
            self.pdf_filename_label.setText(f"Error loading document: {str(e)}")
    
    def send_followup(self):
        """Send a follow-up question"""
        if not self.current_conversation_id:
            return
            
        question = self.question_input.text().strip()
        if not question:
            return
            
        # Disable input while processing
        self.question_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # Add question to conversation display
        self.conversation_display.append(f"<b>You:</b> {question}<br>")
        
        # Clear input field
        self.question_input.clear()
        
        # Create and run worker for follow-up
        worker = FollowUpWorker(self.llm_processor, question, self.current_conversation_id)
        worker.signals.followup_finished.connect(self.handle_followup_result)
        worker.signals.error.connect(self.handle_followup_error)
        
        # Start the worker
        self.threadpool.start(worker)
    
    def handle_followup_result(self, result):
        """Handle result from follow-up query"""
        # Add response to conversation display
        self.conversation_display.append(f"<b>Response:</b> {result['response']}<br>")
        
        # Re-enable input
        self.question_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.question_input.setFocus()
        
        # Scroll to bottom of conversation
        scrollbar = self.conversation_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def handle_followup_error(self, error_message):
        """Handle error from follow-up query"""
        # Add error to conversation display
        self.conversation_display.append(f"<b>Error:</b> {error_message}<br>")
        
        # Re-enable input
        self.question_input.setEnabled(True)
        self.send_btn.setEnabled(True)
    
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


# Main application entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    main_window = DocumentProcessorApp()
    main_window.show()
    
    sys.exit(app.exec())