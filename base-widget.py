from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QSplitter)
from PyQt6.QtCore import Qt

class BaseApplicationWidget(QWidget):
    """Base class with common functionality for both widget types"""
    def __init__(self, version: str, parent=None):
        super().__init__(parent)
        self.version = version
        
        # Common style sheets
        self.console_style = "background-color: #2F2F2F; color: white;"
        self.logo_style = "background-color: #87CEEB;"
        self.development_style = "background-color: #FFD43B;"
        self.sidebar_style = "background-color: #4CAF50;"
        
    def _create_header(self):
        """Create the console/log window and logo header"""
        header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        # Console/Log Window
        self.console_frame = QFrame()
        self.console_frame.setStyleSheet(self.console_style)
        console_layout = QHBoxLayout()
        console_label = QLabel("CONSOLE/LOG Window")
        console_label.setStyleSheet("color: white;")
        console_layout.addWidget(console_label)
        self.console_frame.setLayout(console_layout)
        
        # Logo area
        self.logo_frame = QFrame()
        self.logo_frame.setStyleSheet(self.logo_style)
        self.logo_frame.setFixedWidth(150)
        logo_layout = QHBoxLayout()
        logo_label = QLabel("LOGO")
        logo_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.logo_frame.setLayout(logo_layout)
        
        header_layout.addWidget(self.console_frame)
        header_layout.addWidget(self.logo_frame)
        header.setLayout(header_layout)
        return header

class ApplicationWidgetWithSidebar(BaseApplicationWidget):
    """Application widget with sidebar layout (Image 1)"""
    def __init__(self, version: str, parent=None):
        super().__init__(version, parent)
        self._setup_ui()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add header
        main_layout.addWidget(self._create_header())
        
        # Create splitter for sidebar and development area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setStyleSheet(self.sidebar_style)
        sidebar_layout = QVBoxLayout()
        sidebar_label = QLabel("SIDE\nBAR")
        sidebar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(sidebar_label)
        self.sidebar_frame.setLayout(sidebar_layout)
        
        # Development area
        self.development_frame = QFrame()
        self.development_frame.setStyleSheet(self.development_style)
        self.development_layout = QVBoxLayout()
        dev_label = QLabel("DEVELOPEMENT\nAREA")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.development_layout.addWidget(dev_label)
        self.development_frame.setLayout(self.development_layout)
        
        # Add frames to splitter
        splitter.addWidget(self.sidebar_frame)
        splitter.addWidget(self.development_frame)
        
        # Set initial sizes (approximately 20-80 split)
        splitter.setSizes([200, 800])
        
        main_layout.addWidget(splitter)
        
        # Add version label at bottom
        version_label = QLabel(f"PROD:UAT:BETA v{self.version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(version_label)
        
        self.setLayout(main_layout)

class ApplicationWidgetWithoutSidebar(BaseApplicationWidget):
    """Application widget without sidebar layout (Image 2)"""
    def __init__(self, version: str, parent=None):
        super().__init__(version, parent)
        self._setup_ui()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add header
        main_layout.addWidget(self._create_header())
        
        # Development area
        self.development_frame = QFrame()
        self.development_frame.setStyleSheet(self.development_style)
        self.development_layout = QVBoxLayout()
        dev_label = QLabel("DEVELOPEMENT\nAREA")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.development_layout.addWidget(dev_label)
        self.development_frame.setLayout(self.development_layout)
        
        main_layout.addWidget(self.development_frame)
        
        # Add version label at bottom
        version_label = QLabel(f"PROD:UAT:BETA v{self.version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(version_label)
        
        self.setLayout(main_layout)


from PyQt6.QtWidgets import QApplication
import sys

# Create application
app = QApplication(sys.argv)

# Create widget with sidebar
widget_with_sidebar = ApplicationWidgetWithSidebar(version="1.0")
widget_with_sidebar.resize(1024, 768)
widget_with_sidebar.show()

# Or create widget without sidebar
widget_without_sidebar = ApplicationWidgetWithoutSidebar(version="1.0")
widget_without_sidebar.resize(1024, 768)
widget_without_sidebar.show()

# Start event loop
sys.exit(app.exec())
