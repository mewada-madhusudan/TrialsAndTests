from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QListWidget, QListWidgetItem, QProgressBar, QCheckBox,
                             QMessageBox, QWidget, QGroupBox, QScrollArea, QFormLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QColor

class DocumentListItem(QWidget):
    """
    Custom widget for displaying document with status in a list
    """
    def __init__(self, doc_data, parent=None):
        super().__init__(parent)
        self.doc_id = doc_data["id"]
        self.doc_data = doc_data
        
        # Main layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Document info layout
        info_layout = QVBoxLayout()
        
        # Document name
        self.name_label = QLabel(doc_data["original_filename"])
        self.name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.name_label)
        
        # Status info
        status_layout = QHBoxLayout()
        
        status_text = doc_data["conversion_status"].replace("_", " ").title()
        status_color = self._get_status_color(doc_data["conversion_status"])
        
        self.status_label = QLabel(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"color: {status_color}")
        status_layout.addWidget(self.status_label)
        
        # Add page count if available
        if doc_data["