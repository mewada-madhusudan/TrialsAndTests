import getpass
import os
import shutil
import sqlite3
import sys
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QCursor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QLineEdit, QGridLayout, QFrame, QProgressBar, 
                           QMessageBox, QScrollArea, QSizePolicy, QTabWidget, QMenu, QDialog)

class DetailsDialog(QDialog):
    def __init__(self, tile, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Details - {tile.app_name}")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                padding: 5px;
                font-size: 13px;
            }
            QLabel[heading="true"] {
                font-weight: bold;
                color: #4a90e2;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Create detail rows
        details = [
            ("Application Name", tile.app_name),
            ("Description", tile.app_description),
            ("Environment", tile.environment),
            ("Release Date", tile.release_date),
            ("Validity Period", f"{tile.validity_period} days"),
            ("Version", str(tile.version_number)),
            ("Registration ID", tile.registration_id),
            ("Installation Path", tile.install_path),
            ("Status", "Installed" if tile.installed else "Not Installed"),
            ("Update Available", "Yes" if tile.update_available else "No"),
            ("Is Expired", "Yes" if tile.is_expired else "No")
        ]
        
        for label, value in details:
            row = QHBoxLayout()
            label_widget = QLabel(f"{label}:")
            label_widget.setProperty("heading", "true")
            value_widget = QLabel(str(value))
            value_widget.setWordWrap(True)
            row.addWidget(label_widget)
            row.addWidget(value_widget, 1)
            layout.addLayout(row)
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
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
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

class ApplicationTile(QFrame):
    def __init__(self, app_name, app_description, shared_drive_path, environment,
                 release_date, validity_period, version_number, registration_id, parent=None):
        super().__init__(parent)
        # ... (keep existing initialization code) ...
        
        # Add these new instance variables
        self.is_flipped = False
        self.front_widget = None
        self.back_widget = None
        self.setup_ui()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_ui(self):
        # Create a container widget to hold both front and back sides
        self.container = QWidget(self)
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.container)
        
        # Create front widget
        self.front_widget = QWidget()
        front_layout = QVBoxLayout(self.front_widget)
        # ... (add all your existing UI elements to front_layout) ...
        
        # Create back widget (initially hidden)
        self.back_widget = QWidget()
        self.back_widget.hide()
        back_layout = QVBoxLayout(self.back_widget)
        
        # Add content to back side
        back_title = QLabel("Additional Information")
        back_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")
        back_layout.addWidget(back_title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add more detailed information
        details_layout = QVBoxLayout()
        details = [
            ("Version", str(self.version_number)),
            ("Release Date", self.release_date),
            ("Registration ID", self.registration_id),
            ("Status", "Active" if not self.is_expired else "Expired"),
        ]
        
        for label, value in details:
            row = QHBoxLayout()
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold; color: #666;")
            value_widget = QLabel(value)
            row.addWidget(label_widget)
            row.addWidget(value_widget)
            details_layout.addLayout(row)
        
        back_layout.addLayout(details_layout)
        
        # Add flip back button
        flip_back_btn = QPushButton("Flip Back")
        flip_back_btn.clicked.connect(self.flip_tile)
        flip_back_btn.setStyleSheet("""
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
        back_layout.addWidget(flip_back_btn)
        
        # Stack widgets in container
        stack_layout = QVBoxLayout(self.container)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.addWidget(self.front_widget)
        stack_layout.addWidget(self.back_widget)

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        
        # Add menu actions
        details_action = context_menu.addAction("Show Details")
        flip_action = context_menu.addAction("Flip Tile")
        
        # Show menu and handle selection
        action = context_menu.exec(self.mapToGlobal(position))
        
        if action == details_action:
            self.show_details()
        elif action == flip_action:
            self.flip_tile()

    def show_details(self):
        dialog = DetailsDialog(self, self.window())
        dialog.exec()

    def flip_tile(self):
        # Create flip animation
        self.is_flipped = not self.is_flipped
        
        # Start position
        start_pos = self.container.pos()
        
        # Create animation
        self.anim = QPropertyAnimation(self.container, b"pos")
        self.anim.setDuration(500)  # 500ms duration
        self.anim.setStartValue(start_pos)
        
        # Simulate flip by moving right then left
        if self.is_flipped:
            self.anim.setKeyValueAt(0.5, QPoint(self.width(), start_pos.y()))
            self.anim.setEndValue(start_pos)
            self.anim.finished.connect(lambda: self.complete_flip(True))
        else:
            self.anim.setKeyValueAt(0.5, QPoint(-self.width(), start_pos.y()))
            self.anim.setEndValue(start_pos)
            self.anim.finished.connect(lambda: self.complete_flip(False))
        
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

    def complete_flip(self, show_back):
        if show_back:
            self.front_widget.hide()
            self.back_widget.show()
        else:
            self.back_widget.hide()
            self.front_widget.show()
