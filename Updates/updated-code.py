def show_process_screen(self):
    """Show the processing screen that matches the wireframe design"""
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
    
    # Create main horizontal splitter (left-right layout per wireframe)
    main_splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # LEFT PANEL - contains all control sections and results
    left_panel = QWidget()
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(0, 0, 0, 0)
    
    # 1. TOP CONTROL PANEL
    control_panel = ModernFrame()
    control_layout = QGridLayout()
    control_layout.setContentsMargins(10, 10, 10, 10)
    control_layout.setSpacing(10)
    
    # KB Selection dropdown
    kb_label = QLabel("Select Knowledge Base:")
    self.kb_combo = QComboBox()
    self.kb_combo.addItems(kb_list)
    control_layout.addWidget(kb_label, 0, 0)
    control_layout.addWidget(self.kb_combo, 0, 1)
    
    # Excel input section
    excel_btn = QPushButton("Load Excel")
    excel_btn.clicked.connect(self.load_excel)
    self.excel_status = QLabel("No Excel file loaded")
    control_layout.addWidget(QLabel("Excel File:"), 1, 0)
    control_layout.addWidget(excel_btn, 1, 1)
    control_layout.addWidget(self.excel_status, 1, 2)
    
    # Process button
    self.process_btn = QPushButton("Process")
    self.process_btn.clicked.connect(self.process_data)
    self.process_btn.setEnabled(False)
    control_layout.addWidget(self.process_btn, 0, 2)
    
    control_panel.setLayout(control_layout)
    left_layout.addWidget(control_panel)
    
    # Create vertical splitter for Analysis Results and Follow Up
    results_followup_splitter = QSplitter(Qt.Orientation.Vertical)
    
    # 2. ANALYSIS RESULTS PANEL
    results_panel = ModernFrame("Analysis Results")
    results_layout = QVBoxLayout()
    
    # Results table
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
    results_panel.setLayout(results_layout)
    
    # 3. FOLLOW UP PANEL
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
    
    # Add both panels to the vertical splitter
    results_followup_splitter.addWidget(results_panel)
    results_followup_splitter.addWidget(followup_panel)
    results_followup_splitter.setSizes([500, 300])  # Set initial sizes
    
    # Add the vertical splitter to the left panel
    left_layout.addWidget(results_followup_splitter)
    
    # RIGHT PANEL - Document viewer
    right_panel = ModernFrame("Document Viewer")
    right_layout = QVBoxLayout()
    
    self.pdf_filename_label = QLabel("No document selected")
    self.pdf_filename_label.setStyleSheet("font-style: italic; color: #666;")
    right_layout.addWidget(self.pdf_filename_label)
    
    self.pdf_viewer = QPdfView()
    self.pdf_document = QPdfDocument()
    self.pdf_viewer.setDocument(self.pdf_document)
    self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)
    right_layout.addWidget(self.pdf_viewer)
    
    right_panel.setLayout(right_layout)
    
    # Add panels to main splitter
    main_splitter.addWidget(left_panel)
    main_splitter.addWidget(right_panel)
    main_splitter.setSizes([600, 600])  # Set initial sizes
    
    # Add main splitter to main layout
    self.main_layout.addWidget(main_splitter)

def load_pdf_document(self, file_path, page=None):
    """Load a PDF document into the viewer and navigate to specific page"""
    if not file_path or not os.path.exists(file_path):
        self.pdf_filename_label.setText("No document available")
        return
        
    try:
        # Load the PDF document
        self.pdf_document.close()
        load_status = self.pdf_document.load(file_path)
        if load_status == QPdfDocument.Error.None_:
            self.pdf_filename_label.setText(f"Document: {os.path.basename(file_path)}")
            
            # Navigate to specific page if provided
            if page is not None and page > 0 and page <= self.pdf_document.pageCount():
                # PDF page numbers are 0-indexed internally
                self.pdf_viewer.pageNavigator().jumpToPage(page - 1)
        else:
            self.pdf_filename_label.setText(f"Error loading document: {load_status}")
    except Exception as e:
        self.pdf_filename_label.setText(f"Error: {str(e)}")

def send_followup(self):
    """Send a follow-up question and display the response"""
    question = self.question_input.text().strip()
    if not question or not self.current_conversation_id:
        return
        
    # Clear the input field
    self.question_input.clear()
    
    # Display the question
    self.conversation_display.append(f"<b>You:</b> {question}<br>")
    
    # Create and run worker for follow-up
    worker = FollowUpWorker(self.llm_processor, question, self.current_conversation_id)
    worker.signals.followup_finished.connect(self.handle_followup_response)
    worker.signals.error.connect(self.handle_followup_error)
    
    # Disable controls while processing
    self.question_input.setEnabled(False)
    self.send_btn.setEnabled(False)
    
    # Start the worker
    self.threadpool.start(worker)

def handle_followup_response(self, result):
    """Handle the follow-up response from LLM"""
    # Display the response
    self.conversation_display.append(f"<b>Claude:</b> {result['response']}<br>")
    
    # Re-enable controls
    self.question_input.setEnabled(True)
    self.send_btn.setEnabled(True)
    self.question_input.setFocus()

def handle_followup_error(self, error_message):
    """Handle errors from follow-up processing"""
    # Display error message
    self.conversation_display.append(f"<b>Error:</b> {error_message}<br>")
    
    # Re-enable controls
    self.question_input.setEnabled(True)
    self.send_btn.setEnabled(True)
