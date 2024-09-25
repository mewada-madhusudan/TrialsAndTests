import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QGridLayout, QScrollArea)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal

class ProfilePhoto(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.setStyleSheet("""
            border: 2px solid #333;
            border-radius: 50px;
            background-color: #ddd;
        """)
        self.setText("Photo")
        self.setAlignment(Qt.AlignCenter)

class ApplicationTile(QFrame):
    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        layout = QVBoxLayout(self)
        
        self.nameLabel = QLabel(app_name)
        self.nameLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.nameLabel)
        
        self.installButton = QPushButton("Install")
        layout.addWidget(self.installButton)
        
        self.uninstallButton = QPushButton("Uninstall")
        layout.addWidget(self.uninstallButton)

class AppLauncherUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('STO Application Launcher')
        self.setGeometry(100, 100, 800, 600)

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QHBoxLayout(centralWidget)

        # Left Panel
        leftPanel = QWidget()
        leftLayout = QVBoxLayout(leftPanel)
        leftPanel.setFixedWidth(200)
        leftPanel.setStyleSheet("background-color: #f0f0f0;")

        profilePhoto = ProfilePhoto()
        leftLayout.addWidget(profilePhoto, alignment=Qt.AlignCenter)

        usernameLabel = QLabel("Username")
        usernameLabel.setAlignment(Qt.AlignCenter)
        leftLayout.addWidget(usernameLabel)

        exitButton = QPushButton("Exit")
        exitButton.clicked.connect(self.close)
        leftLayout.addWidget(exitButton)

        leftLayout.addStretch()

        # Right Panel
        rightPanel = QWidget()
        rightLayout = QVBoxLayout(rightPanel)

        stoImage = QLabel("STO Image")
        stoImage.setStyleSheet("border: 1px solid black; min-height: 100px;")
        stoImage.setAlignment(Qt.AlignCenter)
        rightLayout.addWidget(stoImage)

        # Application Tiles
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollContent = QWidget()
        gridLayout = QGridLayout(scrollContent)

        # Add some sample application tiles
        for i in range(6):
            tile = ApplicationTile(f"App {i+1}")
            gridLayout.addWidget(tile, i // 3, i % 3)

        scrollArea.setWidget(scrollContent)
        rightLayout.addWidget(scrollArea)

        # Footer
        footer = QLabel("Developed By STO")
        footer.setAlignment(Qt.AlignRight)
        rightLayout.addWidget(footer)

        mainLayout.addWidget(leftPanel)
        mainLayout.addWidget(rightPanel)

        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AppLauncherUI()
    ex.show()
    sys.exit(app.exec_())
