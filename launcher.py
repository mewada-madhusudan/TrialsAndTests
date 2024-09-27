import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGridLayout, QFrame)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt


class ApplicationTile(QFrame):
    def __init__(self, app_name, app_description, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        icon_label = QLabel()
        icon_label.setPixmap(QPixmap("path_to_app_icon.png").scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.name_label = QLabel(app_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.name_label)

        self.description_label = QLabel(app_description)
        self.description_label.setStyleSheet("color: #666;")
        layout.addWidget(self.description_label)

        button_layout = QHBoxLayout()
        self.install_launch_button = QPushButton("Install/Launch")
        self.uninstall_button = QPushButton("Uninstall")
        button_layout.addWidget(self.install_launch_button)
        button_layout.addWidget(self.uninstall_button)
        layout.addLayout(button_layout)

        self.setStyleSheet("""
            ApplicationTile {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5b4bc7;
            }
        """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Application Launcher")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar
        sidebar = QWidget()
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

        profile_pic = QLabel()
        pixmap = QPixmap("path_to_profile_pic.jpg").scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                                                           Qt.TransformationMode.SmoothTransformation)
        profile_pic.setPixmap(pixmap)
        profile_pic.setStyleSheet("border-radius: 75px; border: 2px solid white;")
        sidebar_layout.addWidget(profile_pic, alignment=Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addWidget(QLabel("SID: SID Value"))
        sidebar_layout.addWidget(QLabel("Name: RAhul"))
        sidebar_layout.addWidget(QLabel("LOB: COPORATE"))
        sidebar_layout.addStretch()
        exit_button = QPushButton("EXIT")
        exit_button.clicked.connect(self.close)
        sidebar_layout.addWidget(exit_button)

        # Main content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)

        # Search bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search")
        search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 16px;
                margin-bottom: 20px;
            }
        """)
        content_layout.addWidget(search_bar)

        # Applications label
        app_label = QLabel("Applications")
        app_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        content_layout.addWidget(app_label)

        # Application grid
        self.app_grid = QGridLayout()
        self.app_grid.setSpacing(20)
        content_layout.addLayout(self.app_grid)

        main_layout.addWidget(sidebar, 1)
        main_layout.addWidget(content_area, 3)

        self.load_applications()

    def load_applications(self):
        # This method would typically query the database and create ApplicationTiles
        # For demonstration, we'll create some dummy tiles
        for i in range(6):
            tile = ApplicationTile(f"Application Name", "application short description")
            self.app_grid.addWidget(tile, i // 3, i % 3)

    def check_user_access(self, app_name):
        # TODO: Implement database check for user access
        pass

    def install_application(self, app_name):
        # TODO: Implement copying exe from shared drive to user machine
        pass

    def uninstall_application(self, app_name):
        # TODO: Implement removing exe from user machine
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())