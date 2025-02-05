import sys
import os
import importlib.util
import types
from pathlib import Path
from PyQt5 import QtWidgets
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import traceback

class PythonUIReloader(FileSystemEventHandler):
    def __init__(self, app, python_file):
        self.app = app
        self.python_file = python_file
        self.current_window = None
        self.module = None
        self.load_window()

    def import_module_from_file(self):
        """Dynamically import the Python module containing the UI code"""
        try:
            # Generate a unique module name
            module_name = f"dynamic_ui_{abs(hash(self.python_file))}"
            
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, self.python_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
        except Exception as e:
            raise ImportError(f"Error importing module: {str(e)}")

    def load_window(self):
        try:
            # Close existing window if it exists
            if self.current_window is not None:
                self.current_window.close()
                self.current_window.deleteLater()

            # Reload the module
            self.module = self.import_module_from_file()

            # Find the main window class in the module
            main_window_class = None
            for item_name in dir(self.module):
                item = getattr(self.module, item_name)
                if isinstance(item, type) and issubclass(item, QtWidgets.QWidget) and item != QtWidgets.QWidget:
                    main_window_class = item
                    break

            if main_window_class is None:
                raise Exception("No QWidget subclass found in the module")

            # Create and show the window
            self.current_window = main_window_class()
            self.current_window.show()
            print("UI reloaded successfully")

        except Exception as e:
            error_dialog = QtWidgets.QMessageBox()
            error_dialog.setWindowTitle("Error")
            error_dialog.setText(f"Error loading UI:\n{str(e)}\n\n{traceback.format_exc()}")
            error_dialog.exec_()

    def on_modified(self, event):
        if event.src_path == str(Path(self.python_file).absolute()):
            print(f"Detected change in {self.python_file}, reloading...")
            self.app.processEvents()
            self.load_window()

def start_live_preview(python_file):
    """
    Start the live preview tool for a Python file containing PyQt UI code
    
    Args:
        python_file (str): Path to the Python file to watch
    """
    app = QtWidgets.QApplication(sys.argv)
    
    # Create the UI reloader
    reloader = PythonUIReloader(app, python_file)
    
    # Set up file watcher
    observer = Observer()
    observer.schedule(reloader, path=str(Path(python_file).parent), recursive=False)
    observer.start()

    try:
        app.exec_()
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python live_preview.py <path_to_python_file>")
        sys.exit(1)
        
    python_file = sys.argv[1]
    if not os.path.exists(python_file):
        print(f"Error: Python file '{python_file}' not found")
        sys.exit(1)
        
    start_live_preview(python_file)
