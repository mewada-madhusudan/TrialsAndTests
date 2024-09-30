import getpass
import os
import shutil
import sqlite3
import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QBrush
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGridLayout, QFrame, QProgressBar, QMessageBox,
                             QScrollArea, QSizePolicy)


class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def get_user_applications(self, username):
        self.cursor.execute("""
            SELECT a.name, a.description, a.shared_drive_path
            FROM applications a
            JOIN user_app_access uaa ON a.id = uaa.app_id
            JOIN users u ON u.id = uaa.user_id
            WHERE u.username = ?
        """, (username,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


class InstallThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, source, destination):
        super().__init__()
        self.source = source
        self.destination = destination

    def run(self):
        try:
            if not os.path.exists(self.source):
                raise FileNotFoundError(f"Source file not found: {self.source}")

            total_size = os.path.getsize(self.source)
            copied_size = 0
            with open(self.source, 'rb') as src, open(self.destination, 'wb') as dst:
                while True:
                    chunk = src.read(1024)
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied_size += len(chunk)
                    progress = int((copied_size / total_size) * 100)
                    self.progress.emit(progress)
            self.finished.emit()
        except FileNotFoundError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Installation error: {str(e)}")


class ApplicationTile(QFrame):
    def __init__(self, app_name, app_description, shared_drive_path, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.shared_drive_path = shared_drive_path
        self.installed = False
        self.install_path = os.path.join("D:/Download", app_name)

        self.setFixedHeight(200)  # Set fixed size for all tiles
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        self.name_label = QLabel(app_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #333;")
        layout.addWidget(self.name_label)

        self.description_label = QLabel(
            app_description[:80] + "..." if len(app_description) > 80 else app_description)
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.description_label)

        button_layout = QHBoxLayout()
        self.install_launch_button = QPushButton("Install")
        self.install_launch_button.clicked.connect(self.on_install_launch_clicked)
        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.clicked.connect(self.on_uninstall_clicked)
        button_layout.addWidget(self.install_launch_button)
        button_layout.addWidget(self.uninstall_button)
        layout.addLayout(button_layout)

        if self.is_app_installed(f'{self.install_path}.exe'):
            self.install_launch_button.setText("Launch")
            self.status_label = QLabel("Installed")
            self.status_label.setStyleSheet("color: green; font-weight: bold; margin-top: 5px;")
        else:
            self.status_label = QLabel("Not Installed")
            self.status_label.setStyleSheet("color: grey; font-weight: bold; margin-top: 5px;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.setStyleSheet("""
            ApplicationTile {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 5px;
            }
        """)

    def on_install_launch_clicked(self):
        if not self.installed:
            self.install_application()
        else:
            self.launch_application()

    def is_app_installed(self, local_path):
        return os.path.exists(local_path)

    def install_application(self):
        self.progress_bar.setVisible(True)
        self.status_label.setText("Installing...")
        self.status_label.setStyleSheet("color: orange;")

        # Create the installation directory if it doesn't exist
        os.makedirs(self.install_path, exist_ok=True)

        # Get the destination file path
        destination_file = os.path.join(self.install_path, f"{self.app_name}.exe")

        self.install_thread = InstallThread(self.shared_drive_path, destination_file)
        self.install_thread.progress.connect(self.update_progress)
        self.install_thread.finished.connect(self.installation_finished)
        self.install_thread.error.connect(self.installation_error)
        self.install_thread.start()

    def installation_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Installation Failed")
        self.status_label.setStyleSheet("color: red;")
        QMessageBox.critical(self, "Installation Error", f"Failed to install {self.app_name}: {error_message}")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def installation_finished(self):
        self.installed = True
        self.status_label.setText("Installed")
        self.status_label.setStyleSheet("color: green;")
        self.install_launch_button.setText("Launch")
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Installation Complete", f"{self.app_name} has been successfully installed.")

    def launch_application(self):
        # Implement application launch logic here
        print(f"Launching {self.app_name}")
        executable_path = os.path.join(self.install_path, f"{self.app_name}.exe")
        if os.path.exists(executable_path):
            try:
                os.startfile(executable_path)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to launch application: {str(e)}')
        else:
            QMessageBox.warning(self, 'Error', f'Application executable not found at {executable_path}')

    def on_uninstall_clicked(self):
        print(self.install_path + '.exe')
        if self.installed:
            try:
                shutil.rmtree(self.install_path)
                self.installed = False
                self.status_label.setText("Not Installed")
                self.status_label.setStyleSheet("color: grey;")
                self.install_launch_button.setText("Install")
                QMessageBox.information(self, "Uninstall Complete",
                                        f"{self.app_name} has been successfully uninstalled.")
            except Exception as e:
                QMessageBox.warning(self, "Uninstall Error", f"Failed to uninstall {self.app_name}: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.username = getpass.getuser()  # Get Windows username
        self.db = Database("launcher.db")  # Initialize database connection
        self.setWindowTitle("Application Launcher")
        self.setMinimumSize(1200, 720)  # Set fixed window size
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

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(250)  # Set fixed width for sidebar
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QLabel {
                padding: 5px;
            }
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                padding: 10px;
                margin: 10px 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5b4bc7;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)

        # Profile picture
        self.profile_pic = QLabel()
        profile_pixmap = QPixmap("D:/Download\download.jpg")
        scaled_pixmap = profile_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                              Qt.TransformationMode.SmoothTransformation)

        # Create a circular mask
        mask = QPixmap(150, 150)
        mask.fill(Qt.GlobalColor.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 150, 150)
        painter.end()

        # Apply the mask to the scaled pixmap
        rounded_pixmap = QPixmap(150, 150)
        rounded_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(0, 0, mask)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()

        self.profile_pic.setPixmap(rounded_pixmap)
        self.profile_pic.setFixedSize(150, 150)
        sidebar_layout.addWidget(self.profile_pic, alignment=Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addWidget(QLabel(f"SID: {self.username}"))
        sidebar_layout.addWidget(QLabel("Name: John Doe"))  # Replace with actual user data
        sidebar_layout.addWidget(QLabel("LOB: CORPORATE"))  # Replace with actual user data
        sidebar_layout.addStretch()
        exit_button = QPushButton("EXIT")
        exit_button.clicked.connect(self.close)
        sidebar_layout.addWidget(exit_button)

        # Main content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("C:\\Users\madhu\Desktop\\new_logo.png")  # Replace with your logo path
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

        # Scroll area for application grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        self.app_grid = QGridLayout(scroll_content)
        self.app_grid.setSpacing(20)
        self.app_grid.setContentsMargins(0, 0, 20, 0)  # Add right margin to prevent cutoff
        # self.app_grid.setColumnStretch(0, 1)
        # self.app_grid.setColumnStretch(1, 1)
        # self.app_grid.setColumnStretch(2, 1)
        self.app_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)  # Align to top-left
        scroll_area.setWidget(scroll_content)
        content_layout.addWidget(scroll_area)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area, 1)

        self.load_applications()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_tile_sizes()

    def adjust_tile_sizes(self):
        content_width = self.width() - 250 - 60  # Subtract sidebar width and content margins
        tile_width = (content_width - 40) // 3  # Subtract grid spacing
        for i in range(self.app_grid.count()):
            item = self.app_grid.itemAt(i).widget()
            if isinstance(item, ApplicationTile):
                item.setFixedWidth(tile_width)

    def load_applications(self):
        apps = self.db.get_user_applications(self.username)
        for i, (name, desc, shared_path) in enumerate(apps):
            tile = ApplicationTile(name, desc, shared_path)
            self.app_grid.addWidget(tile, i // 3, i % 3)

    def filter_applications(self, text):
        for i in range(self.app_grid.count()):
            item = self.app_grid.itemAt(i).widget()
            if isinstance(item, ApplicationTile):
                if text.lower() in item.app_name.lower():
                    item.setVisible(True)
                else:
                    item.setVisible(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
