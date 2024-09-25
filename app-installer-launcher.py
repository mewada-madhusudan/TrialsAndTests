import sys
import os
import shutil
import sqlite3
import getpass
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox,
                             QLabel, QProgressBar, QGridLayout, QScrollArea)
from PyQt5.QtGui import QIcon, QFont, QPainter, QLinearGradient, QColor, QBrush
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QPoint

# Database setup
def setup_database():
    conn = sqlite3.connect('app_launcher.db')
    c = conn.cursor()
    
    # Create applications table
    c.execute('''CREATE TABLE IF NOT EXISTS applications
                 (id INTEGER PRIMARY KEY, name TEXT, path TEXT)''')
    
    # Create user_access table
    c.execute('''CREATE TABLE IF NOT EXISTS user_access
                 (id INTEGER PRIMARY KEY, username TEXT, app_id INTEGER,
                  FOREIGN KEY(app_id) REFERENCES applications(id))''')
    
    # Insert sample data (you would replace this with your actual data)
    c.execute("INSERT OR IGNORE INTO applications VALUES (1, 'App 1', '\\\\shared_drive\\path\\to\\app1.exe')")
    c.execute("INSERT OR IGNORE INTO applications VALUES (2, 'App 2', '\\\\shared_drive\\path\\to\\app2.exe')")
    c.execute("INSERT OR IGNORE INTO user_access VALUES (1, 'testuser', 1)")
    c.execute("INSERT OR IGNORE INTO user_access VALUES (2, 'testuser', 2)")
    
    conn.commit()
    conn.close()

class InstallThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, source_path, dest_path):
        super().__init__()
        self.source_path = source_path
        self.dest_path = dest_path

    def run(self):
        try:
            os.makedirs(os.path.dirname(self.dest_path), exist_ok=True)
            total_size = os.path.getsize(self.source_path)
            copied_size = 0
            with open(self.source_path, 'rb') as src, open(self.dest_path, 'wb') as dst:
                while True:
                    chunk = src.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied_size += len(chunk)
                    self.progress.emit(int(copied_size * 100 / total_size))
            self.finished.emit(True, "Installation completed successfully!")
        except Exception as e:
            self.finished.emit(False, f"Installation failed: {str(e)}")

class ApplicationTile(QWidget):
    def __init__(self, app_name, shared_path, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.shared_path = shared_path
        self.local_path = os.path.join(os.path.expanduser('~'), 'InstalledApps', f"{app_name}.exe")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.nameLabel = QLabel(self.app_name)
        self.nameLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.nameLabel)

        self.installButton = QPushButton('Install', self)
        self.installButton.clicked.connect(self.install_app)
        layout.addWidget(self.installButton)

        self.launchButton = QPushButton('Launch', self)
        self.launchButton.clicked.connect(self.launch_app)
        layout.addWidget(self.launchButton)

        self.progressBar = QProgressBar(self)
        self.progressBar.setVisible(False)
        layout.addWidget(self.progressBar)

        self.setLayout(layout)
        self.setFixedSize(200, 150)
        self.update_button_states()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create a linear gradient for 3D effect
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(240, 240, 240))
        gradient.setColorAt(1, QColor(200, 200, 200))

        # Draw rounded rectangle with gradient
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

        # Add a subtle shadow
        painter.setBrush(QColor(0, 0, 0, 30))
        painter.drawRoundedRect(QRect(5, 5, self.width()-5, self.height()-5), 10, 10)

    def install_app(self):
        self.install_thread = InstallThread(self.shared_path, self.local_path)
        self.install_thread.progress.connect(self.update_progress)
        self.install_thread.finished.connect(self.installation_finished)
        
        self.progressBar.setVisible(True)
        self.installButton.setEnabled(False)
        self.install_thread.start()

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def installation_finished(self, success, message):
        self.progressBar.setVisible(False)
        if success:
            QMessageBox.information(self, 'Success', message)
        else:
            QMessageBox.critical(self, 'Error', message)
        self.update_button_states()

    def launch_app(self):
        try:
            os.startfile(self.local_path)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to launch application: {str(e)}')

    def is_app_installed(self):
        return os.path.exists(self.local_path)

    def update_button_states(self):
        is_installed = self.is_app_installed()
        self.installButton.setEnabled(not is_installed)
        self.launchButton.setEnabled(is_installed)

class AppInstallerLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.username = getpass.getuser()  # Get Windows username
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('STO App Installer/Launcher')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                font-size: 16px;
                margin-bottom: 10px;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)
        
        main_layout = QVBoxLayout()
        
        # Add logo and developer info
        logo_label = QLabel('Developed by STO Team', self)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("""
            font-size: 24px;
            color: #333;
            font-weight: bold;
            padding: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
        """)
        main_layout.addWidget(logo_label)
        
        self.statusLabel = QLabel(f'Welcome, {self.username}! Here are your available applications:', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.statusLabel)
        
        # Create a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget(scroll)
        
        # Grid layout for application tiles
        grid_layout = QGridLayout(scroll_content)
        
        # Add application tiles
        self.add_application_tiles(grid_layout)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)

    def add_application_tiles(self, layout):
        conn = sqlite3.connect('app_launcher.db')
        c = conn.cursor()
        
        # Fetch applications the user has access to
        c.execute('''SELECT a.name, a.path FROM applications a
                     JOIN user_access ua ON a.id = ua.app_id
                     WHERE ua.username = ?''', (self.username,))
        
        applications = c.fetchall()
        
        conn.close()

        row = 0
        col = 0
        for app_name, shared_path in applications:
            tile = ApplicationTile(app_name, shared_path)
            layout.addWidget(tile, row, col)
            col += 1
            if col > 2:  # 3 tiles per row
                col = 0
                row += 1

if __name__ == '__main__':
    setup_database()  # Set up the database before running the app
    app = QApplication(sys.argv)
    ex = AppInstallerLauncher()
    ex.show()
    sys.exit(app.exec_())
