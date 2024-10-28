import getpass
import os
import shutil
import sqlite3
import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QBrush
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGridLayout, QFrame, QProgressBar, QMessageBox,
                             QScrollArea, QSizePolicy, QTabWidget)


class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def get_user_applications(self, username, environment=None):
        try:
            query = """
                   SELECT a.name, a.description, a.shared_drive_path, a.status,
                          a.release_date, a.validity_period, a.version_number, a.registrationId
                   FROM applications a
                   JOIN user_app_access uaa ON a.id = uaa.app_id
                   JOIN users u ON u.id = uaa.user_id
                   WHERE u.username = ?
               """
            params = [username]

            if environment:
                query += " AND a.status = ?"
                params.append(environment)

            self.cursor.execute(query, tuple(params))
            results = self.cursor.fetchall()
            print(f"Database query results for {environment}: {results}")  # Debug print
            return results
        except Exception as e:
            print(f"Database error: {str(e)}")
            return []

    def get_latest_version(self, app_name):
        query = """
            SELECT version_number, shared_drive_path
            FROM applications
            WHERE name = ?
            ORDER BY release_date DESC
            LIMIT 1
        """
        self.cursor.execute(query, (app_name,))
        return self.cursor.fetchone()

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


class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: #f8f9fa;
                color: #6c757d;
                border: none;
                padding: 12px 50px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: bold;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 3px solid transparent;
            }
            QTabBar::tab:hover {
                background: #e9ecef;
                color: #495057;
            }
            QTabBar::tab:selected {
                background: white;
                color: #4a90e2;
                border-bottom: 3px solid #4a90e2;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)


class EnvironmentLabel(QLabel):
    def __init__(self, text, env_type, parent=None):
        super().__init__(text, parent)
        self.env_type = env_type
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Style based on environment type
        if env_type == "PROD":
            bg_color = "#28a745"
        else:  # UAT
            bg_color = "#fd7e14"

        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: white;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: bold;
        """)
        self.setFixedHeight(20)
        self.setFixedWidth(60)


class ApplicationTile(QFrame):
    def __init__(self, app_name, app_description, shared_drive_path, environment,
                 release_date, validity_period, version_number, registration_id, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.app_description = app_description
        self.shared_drive_path = shared_drive_path
        self.environment = environment
        self.release_date = release_date
        self.validity_period = validity_period
        self.version_number = version_number  # This is the version from DB
        self.registration_id = registration_id

        # Set up paths and database connection
        self.install_path = os.path.join("D:\Download", app_name)
        self.db = Database("launcher.db")

        # Initialize version tracking
        self.installed_version = self.get_installed_version()
        self.installed = self.is_app_installed(f'{self.install_path}\{self.app_name}.exe')

        # Check status
        self.is_expired = self.check_validity()
        self.update_available = self.check_update_available()

        # Set up the UI
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(200)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # Header layout with name and environment label
        header_layout = QHBoxLayout()
        self.name_label = QLabel(self.app_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #333;")
        header_layout.addWidget(self.name_label)

        self.env_label = EnvironmentLabel(self.environment, self.environment)
        header_layout.addWidget(self.env_label, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header_layout)

        # Description label
        self.description_label = QLabel(
            self.app_description[:80] + "..." if len(self.app_description) > 80 else self.app_description)
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.description_label)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(separator)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.install_launch_button = QPushButton("Install")
        self.install_launch_button.clicked.connect(self.on_install_launch_clicked)
        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.clicked.connect(self.on_uninstall_clicked)

        self.install_launch_button.setStyleSheet("""
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

        self.uninstall_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #dc3545;
                border: 1px solid #dc3545;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)

        button_layout.addWidget(self.install_launch_button)
        button_layout.addWidget(self.uninstall_button)
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("Not Installed")
        self.status_label.setStyleSheet("""
            color: #6c757d;
            font-weight: bold;
            margin-top: 5px;
        """)
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f9fa;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Add tile hover effect
        self.setStyleSheet("""
            ApplicationTile {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            ApplicationTile:hover {
                border: 1px solid #4a90e2;
                box-shadow: 0 4px 8px rgba(74, 144, 226, 0.1);
            }
        """)

        # Update initial button states
        if self.is_app_installed(f'{self.install_path}.exe'):
            self.installed = True
        self.update_button_states()

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

    def check_validity(self):
        from datetime import datetime, timedelta
        try:
            release_date = datetime.strptime(self.release_date, "%d/%m/%Y")
            expiry_date = release_date + timedelta(days=self.validity_period)
            return datetime.now() > expiry_date
        except Exception as e:
            print(f"Error checking validity: {str(e)}")
            return False

    def check_update_available(self):
        try:
            latest_version = self.db.get_latest_version(self.app_name)
            installed_version = self.get_installed_version()

            if latest_version and self.installed:
                if installed_version is None:
                    # If version file is missing but app is installed, assume it needs update
                    return True
                return float(latest_version[0]) > float(installed_version)
            return False
        except Exception as e:
            print(f"Error checking for updates: {str(e)}")
            return False

    def update_button_states(self):
        if self.is_expired:
            self.setEnabled(False)
            self.setStyleSheet(self.styleSheet() + """
                        ApplicationTile {
                            background-color: #f8f9fa;
                            opacity: 0.7;
                        }
                    """)
            if self.environment == "UAT":
                self.status_label.setText("UAT Period Expired")
            else:
                self.status_label.setText("Application Expired")
            self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            self.install_launch_button.setEnabled(False)
            self.uninstall_button.setEnabled(False)
            return

        if self.update_available:
            self.install_launch_button.setText("Update")
            self.status_label.setText("Update Available")
            self.status_label.setStyleSheet("color: #ffc107; font-weight: bold;")
        elif self.installed:
            self.install_launch_button.setText("Launch")
            self.status_label.setText("Installed")
            self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.install_launch_button.setText("Install")
            self.status_label.setText("Not Installed")
            self.status_label.setStyleSheet("color: #6c757d; font-weight: bold;")

    def get_installed_version(self):
        """Read the installed version from a version file in the installation directory"""
        version_file = os.path.join(self.install_path, "version.txt")
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    return float(f.read().strip())
            except:
                return None
        return None

    def save_installed_version(self):
        """Save the current version number to a file after installation"""
        try:
            os.makedirs(self.install_path, exist_ok=True)
            version_file = os.path.join(self.install_path, "version.txt")
            with open(version_file, 'w') as f:
                f.write(str(self.version_number))
        except Exception as e:
            print(f"Error saving version info: {str(e)}")

    def on_install_launch_clicked(self):
        if self.update_available:
            self.update_application()
        elif not self.installed:
            self.install_application()
        else:
            self.launch_application()

    def update_application(self):
        latest_version = self.db.get_latest_version(self.app_name)
        if latest_version:
            try:
                if os.path.exists(self.install_path):
                    shutil.rmtree(self.install_path)

                self.shared_drive_path = latest_version[1]
                self.install_application()
                self.version_number = latest_version[0]
                self.update_available = False
                self.update_button_states()

            except Exception as e:
                QMessageBox.critical(self, "Update Error", f"Failed to update {self.app_name}: {str(e)}")

    def installation_finished(self):
        self.installed = True
        self.save_installed_version()  # Save version info after successful installation
        self.installed_version = self.version_number  # Update the installed version
        self.update_available = False  # Reset update flag after successful installation
        self.update_button_states()
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Installation Complete",
                                f"{self.app_name} has been successfully installed.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_tiles = []
        self.username = getpass.getuser()
        self.db = Database("launcher.db")
        self.setWindowTitle("Application Launcher")
        self.setMinimumSize(1200, 720)
        # Set the window style
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
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("C:\\Users\\madhu\\Desktop\\new_logo.png")
        logo_label.setPixmap(logo_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation))
        content_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Applications title and search bar
        # Title and search section
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(15)

        app_title = QLabel("Applications")
        app_title.setStyleSheet("""
                    font-size: 28px;
                    font-weight: bold;
                    color: #2c3e50;
                """)
        header_layout.addWidget(app_title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search applications...")
        self.search_bar.textChanged.connect(self.filter_applications)
        self.search_bar.setStyleSheet("""
                    QLineEdit {
                        border: 2px solid #e0e0e0;
                        border-radius: 25px;
                        padding: 12px 20px;
                        font-size: 14px;
                        background-color: white;
                    }
                    QLineEdit:focus {
                        border-color: #4a90e2;
                        outline: none;
                    }
                """)
        header_layout.addWidget(self.search_bar)
        content_layout.addWidget(header_widget)

        # Custom Tab Widget
        self.tab_widget = CustomTabWidget()
        content_layout.addWidget(self.tab_widget)

        # Create tabs with scroll areas
        self.prod_scroll = QScrollArea()

        for scroll in [self.prod_scroll]:
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setStyleSheet("""
                        QScrollArea {
                            border: none;
                            background-color: transparent;
                        }
                        QScrollBar:vertical {
                            border: none;
                            background: #f0f0f0;
                            width: 8px;
                            border-radius: 4px;
                        }
                        QScrollBar::handle:vertical {
                            background: #c0c0c0;
                            border-radius: 4px;
                        }
                        QScrollBar::handle:vertical:hover {
                            background: #a0a0a0;
                        }
                    """)

        self.prod_widget = QWidget()
        self.prod_layout = QGridLayout(self.prod_widget)

        self.prod_layout.setSpacing(20)
        self.prod_layout.setContentsMargins(0, 0, 20, 0)
        self.prod_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.prod_scroll.setWidget(self.prod_widget)

        self.tab_widget.addTab(self.prod_scroll, "Applications")

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area, 1)

        self.load_applications()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_tile_sizes()

    def load_applications(self):
        self.clear_layout(self.prod_layout)
        self.all_tiles.clear()  # Clear the stored tiles

        try:
            prod_apps = self.db.get_user_applications(self.username, "PROD")
            uat_apps = self.db.get_user_applications(self.username, "UAT")
            all_apps = prod_apps + uat_apps

            for app_data in enumerate(all_apps):
                name, desc, shared_path, env, release_date, validity_period, version_number, registration_id = app_data[
                    1]
                tile = ApplicationTile(
                    app_name=name,
                    app_description=desc,
                    shared_drive_path=shared_path,
                    environment=env,
                    release_date=release_date,
                    validity_period=validity_period,
                    version_number=float(version_number) if version_number else 1.0,
                    registration_id=registration_id
                )
                self.all_tiles.append(tile)  # Store the tile reference

            # Initial layout of all tiles
            self.update_grid_layout("")

        except Exception as e:
            print(f"Error loading applications: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load applications: {str(e)}")

    def filter_applications(self, text):
        self.update_grid_layout(text.lower())

    def update_grid_layout(self, filter_text):
        # Clear the current layout
        self.clear_layout(self.prod_layout)

        # Filter and layout visible tiles
        visible_tiles = [
            tile for tile in self.all_tiles
            if filter_text in tile.app_name.lower()
        ]

        # Add filtered tiles to the grid
        for i, tile in enumerate(visible_tiles):
            row = i // 3  # 3 tiles per row
            col = i % 3
            self.prod_layout.addWidget(tile, row, col)
            tile.setVisible(True)

        # Add stretch to bottom of grid to maintain alignment
        self.prod_layout.setRowStretch(len(visible_tiles) // 3 + 1, 1)

        # Adjust tile sizes
        content_width = self.width() - 250 - 60  # Sidebar width and margins
        tile_width = (content_width - 40) // 3
        self.adjust_layout_tiles(self.prod_layout, tile_width)

    def adjust_tile_sizes(self):
        content_width = self.width() - 250 - 60
        tile_width = (content_width - 40) // 3
        self.adjust_layout_tiles(self.prod_layout, tile_width)

    def adjust_layout_tiles(self, layout, tile_width):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.widget(), ApplicationTile):
                item.widget().setFixedWidth(tile_width)

    def clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)  # Remove wi



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
