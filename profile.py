from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
from PyQt6.QtGui import QPixmap, QFont, QIcon, QImage
from PyQt6.QtCore import Qt, QByteArray
import base64

class UserSidebar(QWidget):
    def __init__(self, user_details):
        super().__init__()
        self.user_details = user_details
        self.image_label = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top partition
        top_partition = QWidget()
        top_layout = QVBoxLayout(top_partition)
        top_layout.setSpacing(5)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_partition.setStyleSheet("background-color: #1e40af;")

        # User image
        self.image_label = QLabel()
        self.image_label.setFixedSize(80, 80)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2563eb;
                border-radius: 40px;
                border: 2px solid #93c5fd;
            }
        """)
        
        # Load image from base64
        if 'image_data' in self.user_details:
            self.load_image_from_base64(self.user_details['image_data'])
        
        top_layout.addWidget(self.image_label)

        # User name
        name_label = QLabel(self.user_details.get('name', ''))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        name_label.setStyleSheet("color: white; padding-bottom: 5px;")
        top_layout.addWidget(name_label)

        main_layout.addWidget(top_partition)

        # Bottom partition
        bottom_partition = QScrollArea()
        bottom_partition.setWidgetResizable(True)
        bottom_partition.setStyleSheet("""
            QScrollArea {
                background-color: #2563eb;
                border: none;
            }
            QScrollBar:vertical {
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #1e40af;
                border-radius: 4px;
            }
        """)

        bottom_content = QWidget()
        bottom_layout = QVBoxLayout(bottom_content)
        bottom_layout.setSpacing(3)
        bottom_layout.setContentsMargins(8, 8, 8, 8)

        # User details
        details = [
            ('SID', 'user', 'sid'),
            ('Email', 'mail', 'email'),
            ('Job Title', 'briefcase', 'job_title'),
            ('Manager', 'users', 'manager'),
            ('Cost Center', 'building', 'cost_center')
        ]

        for label, icon_name, key in details:
            detail_widget = self.create_detail_widget(label, self.user_details.get(key, ''), icon_name)
            bottom_layout.addWidget(detail_widget)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #1e40af;")
        separator.setFixedHeight(1)
        bottom_layout.addWidget(separator)

        # Exit button
        exit_button = QPushButton("EXIT")
        exit_button.setFixedHeight(30)
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                padding: 5px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        bottom_layout.addWidget(exit_button)

        bottom_partition.setWidget(bottom_content)
        main_layout.addWidget(bottom_partition)

        self.setFixedWidth(250)
        self.setMinimumHeight(400)

    def create_detail_widget(self, label, value, icon_name):
        widget = QFrame()
        widget.setStyleSheet("QFrame { padding: 2px; }")
        
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(2, 2, 2, 2)
        
        icon_label = QLabel()
        icon = QIcon(f"path/to/{icon_name}_icon.png")
        icon_label.setPixmap(icon.pixmap(16, 16))
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-weight: bold; color: #e2e8f0; font-size: 11px;")
        text_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet("color: white; font-size: 11px;")
        text_layout.addWidget(value_widget)

        layout.addLayout(text_layout)
        layout.addStretch()
        
        return widget

    def load_image_from_base64(self, base64_string):
        try:
            # Remove the data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 string
            image_data = base64.b64decode(base64_string)
            
            # Create QImage from the decoded data
            image = QImage()
            image.loadFromData(image_data)
            
            if not image.isNull():
                # Convert to pixmap and scale
                pixmap = QPixmap.fromImage(image)
                pixmap = pixmap.scaled(80, 80, 
                                     Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                     Qt.TransformationMode.SmoothTransformation)
                
                # Create circular mask
                rounded = QPixmap(pixmap.size())
                rounded.fill(Qt.GlobalColor.transparent)
                
                self.image_label.setPixmap(pixmap)
            
        except Exception as e:
            print(f"Error loading image: {str(e)}")

# Usage example:
# user_data = {
#     'sid': '123456',
#     'name': 'Rahul',
#     'email': 'rahul@example.com',
#     'job_title': 'Software Engineer',
#     'manager': 'John Doe',
#     'cost_center': 'CORPORATE',
#     'image_data': 'data:image/gif;base64,R0lGODlh...'  # Your base64 image string here
# }
# sidebar = UserSidebar(user_data)
