from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class BaseApplicationWidget(QWidget):
    def __init__(self, version: str, parent=None):
        """
        Initialize the base application widget with common layout.
        
        Args:
            version (str): Version number to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.version = version
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the base UI layout"""
        # Main vertical layout to hold version and horizontal layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Version label at the top
        version_label = QLabel(f"Version {self.version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_label.setStyleSheet("color: blue; padding: 5px;")
        version_label.setFont(QFont("Arial", 8))
        main_layout.addWidget(version_label)
        
        # Horizontal layout for the main sections
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(0)
        
        # Logo area (blue)
        self.logo_frame = QFrame()
        self.logo_frame.setStyleSheet("background-color: #4B8BBE;")
        self.logo_frame.setFixedWidth(200)  # Adjust width as needed
        
        # Content area (yellow)
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("background-color: #FFD43B;")
        self.content_layout = QVBoxLayout()
        self.content_frame.setLayout(self.content_layout)
        
        # User details area (green)
        self.user_frame = QFrame()
        self.user_frame.setStyleSheet("background-color: #4CAF50;")
        self.user_frame.setFixedWidth(200)  # Adjust width as needed
        
        # Add frames to horizontal layout
        horizontal_layout.addWidget(self.logo_frame)
        horizontal_layout.addWidget(self.content_frame, 1)  # Content area stretches
        horizontal_layout.addWidget(self.user_frame)
        
        # Add horizontal layout to main layout
        main_layout.addLayout(horizontal_layout, 1)  # Give it stretch factor
        
        self.setLayout(main_layout)
    
    def set_logo(self, logo_widget: QWidget):
        """
        Set the logo widget in the blue area
        
        Args:
            logo_widget (QWidget): Widget containing the logo
        """
        if self.logo_frame.layout():
            # Clear existing layout
            QWidget().setLayout(self.logo_frame.layout())
        
        logo_layout = QVBoxLayout()
        logo_layout.addWidget(logo_widget)
        self.logo_frame.setLayout(logo_layout)
    
    def set_user_details(self, user_widget: QWidget):
        """
        Set the user details widget in the green area
        
        Args:
            user_widget (QWidget): Widget containing user details
        """
        if self.user_frame.layout():
            # Clear existing layout
            QWidget().setLayout(self.user_frame.layout())
            
        user_layout = QVBoxLayout()
        user_layout.addWidget(user_widget)
        self.user_frame.setLayout(user_layout)
    
    def get_content_layout(self) -> QVBoxLayout:
        """
        Get the layout for the content area (yellow)
        
        Returns:
            QVBoxLayout: Layout where developers can add their widgets
        """
        return self.content_layout
