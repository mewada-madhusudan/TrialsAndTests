class ApplicationTile(QFrame):
    def __init__(self, app_name, app_description, shared_drive_path, environment,
                 release_date, validity_period, version_number, registration_id, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.app_description = app_description
        self.shared_drive_path = shared_drive_path
        self.environment = environment
        self.release_date = release_date
        self.validity_period = validity_period
        self.version_number = version_number
        self.registration_id = registration_id
        self.installed = False
        self.install_path = os.path.join("D:/Download", app_name)
        self.db = Database("launcher.db")
        self.installed_version = self.get_installed_version()

        # Check if application is expired
        self.is_expired = self.check_validity()
        # Check if update is available
        self.update_available = self.check_update_available()

        self.setup_ui()
        
        # Add overlay if expired
        if self.is_expired:
            self.add_expired_overlay()

    def setup_ui(self):
        self.setFixedHeight(200)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # Create a container widget for the content
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Header layout with name and environment label
        header_layout = QHBoxLayout()
        self.name_label = QLabel(self.app_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #333;")
        header_layout.addWidget(self.name_label)

        self.env_label = EnvironmentLabel(self.environment, self.environment)
        header_layout.addWidget(self.env_label, alignment=Qt.AlignmentFlag.AlignRight)
        content_layout.addLayout(header_layout)

        # Description label
        self.description_label = QLabel(
            self.app_description[:80] + "..." if len(self.app_description) > 80 else self.app_description)
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        content_layout.addWidget(self.description_label)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        content_layout.addWidget(separator)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.install_launch_button = QPushButton("Install")
        self.install_launch_button.clicked.connect(self.on_install_launch_clicked)
        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.clicked.connect(self.on_uninstall_clicked)

        self.install_launch_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)

        self.uninstall_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #dc3545;
                border: 1px solid #dc3545;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)

        button_layout.addWidget(self.install_launch_button)
        button_layout.addWidget(self.uninstall_button)
        content_layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("Not Installed")
        self.status_label.setStyleSheet("""
            color: #6c757d;
            font-weight: bold;
            margin-top: 5px;
        """)
        content_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f9fa;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 5px;
            }
        """)
        content_layout.addWidget(self.progress_bar)

        # Add content widget to main layout
        layout.addWidget(self.content_widget)

        # Basic tile style
        self.setStyleSheet("""
            ApplicationTile {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            ApplicationTile:hover {
                border: 1px solid #4a90e2;
                box-shadow: 0 4px 8px rgba(74, 144, 226, 0.1);
            }
        """)

        # Update initial button states
        if self.is_app_installed(f'{self.install_path}.exe'):
            self.installed = True
        self.update_button_states()

    def add_expired_overlay(self):
        # Create overlay widget
        self.overlay = QWidget(self)
        overlay_layout = QVBoxLayout(self.overlay)
        
        # Create expired message label
        expire_msg = "UAT Period Expired" if self.environment == "UAT" else "Application Expired"
        expire_label = QLabel(expire_msg)
        expire_label.setStyleSheet("""
            color: #dc3545;
            font-weight: bold;
            font-size: 16px;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
        """)
        expire_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add label to overlay layout with centering
        overlay_layout.addStretch()
        overlay_layout.addWidget(expire_label, alignment=Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addStretch()
        
        # Style the overlay
        self.overlay.setStyleSheet("""
            background-color: rgba(169, 169, 169, 0.7);
            border-radius: 10px;
        """)
        
        # Ensure overlay covers the entire tile
        self.overlay.setGeometry(self.rect())
        self.overlay.show()
        
        # Disable all controls
        self.content_widget.setEnabled(False)
        
        # Update the resize event to handle overlay positioning
        def resizeEvent(self, event):
            super().resizeEvent(event)
            if hasattr(self, 'overlay'):
                self.overlay.setGeometry(self.rect())
        
        # Add the resizeEvent method to the class
        self.resizeEvent = resizeEvent.__get__(self, type(self))

    def update_button_states(self):
        if self.is_expired:
            self.status_label.setText("Application Expired" if self.environment == "PROD" else "UAT Period Expired")
            self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            self.install_launch_button.setEnabled(False)
            self.uninstall_button.setEnabled(False)
            return

        if self.update_available:
            self.install_launch_button.setText("Update")
            self.status_label.setText("Update Available")
            self.status_label.setStyleSheet("color: #ffc107; font-weight: bold;")
        elif self.installed:
            self.install_launch_button.setText("Launch")
            self.status_label.setText("Installed")
            self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.install_launch_button.setText("Install")
            self.status_label.setText("Not Installed")
            self.status_label.setStyleSheet("color: #6c757d; font-weight: bold;")
