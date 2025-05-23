from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from PyQt6.QtWidgets import QApplication
import sys
class BaseApplicationWidget(QWidget):
    """Base class with common functionality for both widget types"""
    def __init__(self, environment: str, version: str, parent=None):
        super().__init__(parent)
        self.environment = environment
        self.version = version
        
        # Define fixed header height
        self.HEADER_HEIGHT = 150  # pixels
        self.LOGO_WIDTH = 350    # pixels
        
        # Common style sheets
        self.console_style = """
            background-color: #2F2F2F;
            color: white;
            padding: 10px;
        """
        self.logo_style = "background-color: white; border: none;"
        self.development_style = "background-color: #FFD43B;"
        self.sidebar_style = "background-color: #4CAF50;"
        self.footer_style = """
            background-color: #F0F0F0;
            border-top: 1px solid #CCCCCC;
            padding: 2px;
        """
        
    def _create_header(self):
        """Create the console/log window and logo header with fixed height"""
        header = QWidget()
        header.setFixedHeight(self.HEADER_HEIGHT)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        # Console/Log Window
        self.console_frame = QFrame()
        self.console_frame.setFixedHeight(self.HEADER_HEIGHT)
        self.console_frame.setStyleSheet(self.console_style)
        console_layout = QHBoxLayout()
        console_label = QLabel("CONSOLE/LOG Window")
        console_label.setStyleSheet("color: white;")
        console_layout.addWidget(console_label)
        self.console_frame.setLayout(console_layout)
        
        # Logo area
        self.logo_frame = QFrame()
        self.logo_frame.setStyleSheet(self.logo_style)
        self.logo_frame.setFixedSize(self.LOGO_WIDTH, self.HEADER_HEIGHT)
        logo_layout = QHBoxLayout()
        
        # Create logo label with the wardrobe image
        logo_label = QLabel()
        pixmap = QPixmap("wardrobe_logo.png")
        scaled_pixmap = pixmap.scaled(self.LOGO_WIDTH - 20, self.HEADER_HEIGHT - 20,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        self.logo_frame.setLayout(logo_layout)
        
        header_layout.addWidget(self.console_frame)
        header_layout.addWidget(self.logo_frame)
        header.setLayout(header_layout)
        return header
    
    def _create_footer(self):
        """Create the footer with version and environment"""
        footer = QWidget()
        footer.setFixedHeight(25)
        footer.setStyleSheet(self.footer_style)
        
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(5, 0, 5, 0)
        
        version_label = QLabel(f"v{self.version}")
        version_label.setStyleSheet("color: #666666;")
        
        env_label = QLabel(self.environment)
        env_label.setStyleSheet("color: #666666;")
        
        footer_layout.addWidget(version_label)
        footer_layout.addStretch()
        footer_layout.addWidget(env_label)
        
        footer.setLayout(footer_layout)
        return footer

class ApplicationWidgetWithSidebar(BaseApplicationWidget):
    """Application widget with sidebar layout"""
    def __init__(self, environment: str, version: str, parent=None):
        super().__init__(environment, version, parent)
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
        splitter.setSizes([200, 800])
        
        main_layout.addWidget(splitter)
        
        # Add footer
        main_layout.addWidget(self._create_footer())
        
        self.setLayout(main_layout)

class ApplicationWidgetWithoutSidebar(BaseApplicationWidget):
    """Application widget without sidebar layout"""
    def __init__(self, environment: str, version: str, parent=None):
        super().__init__(environment, version, parent)
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
        
        # Add footer
        main_layout.addWidget(self._create_footer())
        
        self.setLayout(main_layout)



# Create application
app = QApplication(sys.argv)

# Create widget with sidebar
widget_with_sidebar = ApplicationWidgetWithSidebar(
    environment="UAT:PROD:BETA",
    version="1.0"
)
widget_with_sidebar.resize(1024, 768)
widget_with_sidebar.show()

# Or create widget without sidebar
widget_without_sidebar = ApplicationWidgetWithoutSidebar(
    environment="UAT:PROD:BETA",
    version="1.0"
)
widget_without_sidebar.resize(1024, 768)
widget_without_sidebar.show()

# Start event loop
sys.exit(app.exec())
