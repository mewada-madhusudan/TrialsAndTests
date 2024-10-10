# Modified MainWindow class for launcherui.py

class NoAccessWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Create a container for the message with some styling
        message_container = QFrame()
        message_container.setObjectName("messageContainer")
        message_container.setStyleSheet("""
            #messageContainer {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
        """)
        
        container_layout = QVBoxLayout(message_container)
        
        # Add an icon (you can replace with your own icon path)
        icon_label = QLabel()
        icon_pixmap = QPixmap("C:/path/to/your/icon.png")  # Replace with your icon path
        if icon_pixmap.isNull():
            # Fallback text if icon isn't found
            icon_label.setText("🔒")
            icon_label.setStyleSheet("""
                QLabel {
                    font-size: 48px;
                    color: #6c757d;
                }
            """)
        else:
            icon_label.setPixmap(icon_pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(icon_label)
        
        # Add message text
        message_label = QLabel("No Application Access")
        message_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #343a40;
                margin: 10px 0;
            }
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(message_label)
        
        description_label = QLabel(
            "You currently don't have access to any applications.\n"
            "Please contact your administrator for access permissions."
        )
        description_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #6c757d;
                margin: 10px 0;
            }
        """)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(description_label)
        
        # Add contact button
        contact_button = QPushButton("Contact Administrator")
        contact_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                max-width: 200px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        contact_button.clicked.connect(self.contact_admin)
        container_layout.addWidget(contact_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add everything to the main layout
        layout.addWidget(message_container, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
    
    def contact_admin(self):
        # You can customize this to open email client or show contact information
        QMessageBox.information(
            self,
            "Contact Administrator",
            "Please contact your administrator at:\nEmail: admin@company.com\nPhone: (555) 123-4567"
        )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.username = getpass.getuser()  # Get Windows username
        self.db = Database("launcher.db")  # Initialize database connection
        self.setWindowTitle("Application Launcher")
        self.setMinimumSize(1200, 720)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create and add sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # Create main content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Add logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("path/to/logo.png")  # Replace with your logo path
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation))
            content_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Applications title and search bar
        app_title = QLabel("Applications")
        app_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        content_layout.addWidget(app_title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search applications")
        self.search_bar.textChanged.connect(self.filter_applications)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 16px;
                margin-bottom: 20px;
            }
        """)
        content_layout.addWidget(self.search_bar)

        # Scroll area for application grid or no access message
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Get user applications
        apps = self.db.get_user_applications(self.username)
        
        if apps:
            # Create grid for applications
            scroll_content = QWidget()
            self.app_grid = QGridLayout(scroll_content)
            self.app_grid.setSpacing(20)
            self.app_grid.setContentsMargins(0, 0, 20, 0)
            self.app_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            # Add applications to grid
            for i, (name, desc, shared_path) in enumerate(apps):
                tile = ApplicationTile(name, desc, shared_path)
                self.app_grid.addWidget(tile, i // 3, i % 3)
            
            scroll_area.setWidget(scroll_content)
        else:
            # Show no access message
            self.search_bar.setVisible(False)  # Hide search bar when no apps
            scroll_area.setWidget(NoAccessWidget())

        content_layout.addWidget(scroll_area)
        main_layout.addWidget(content_area, 1)

    def create_sidebar(self):
        # Your existing sidebar creation code here
        ...

    def filter_applications(self, text):
        if hasattr(self, 'app_grid'):
            for i in range(self.app_grid.count()):
                item = self.app_grid.itemAt(i).widget()
                if isinstance(item, ApplicationTile):
                    if text.lower() in item.app_name.lower():
                        item.setVisible(True)
                    else:
                        item.setVisible(False)
