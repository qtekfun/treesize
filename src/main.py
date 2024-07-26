import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QFileDialog, QLabel, QWidget, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QThread

class Worker(QThread):
    update_tree = pyqtSignal(float, QTreeWidgetItem)
    work_done = pyqtSignal()

    def __init__(self, directory, parent_item):
        super().__init__()
        self.directory = directory
        self.parent_item = parent_item
        self._is_running = True

    def run(self):
        self.scan_directory(self.directory, self.parent_item)
        self.work_done.emit()

    def scan_directory(self, directory, parent_item):
        total_size = 0
        if not self._is_running:
            return 0

        try:
            for item in os.listdir(directory):
                if not self._is_running:
                    return 0
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    child_item = QTreeWidgetItem([item, "Calculating..."])
                    parent_item.addChild(child_item)
                    size = self.scan_directory(item_path, child_item)
                    self.update_tree.emit(size / (1024 ** 2), child_item)
                    total_size += size
                else:
                    size = self.get_file_size(item_path)
                    total_size += size

            parent_item.setText(1, f"{total_size / (1024 ** 2):.2f} MB")
        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")
        return total_size

    def get_file_size(self, file_path):
        try:
            return os.path.getsize(file_path)
        except (FileNotFoundError, PermissionError, OSError):
            return 0

    def stop(self):
        self._is_running = False

class TreeSizeApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TreeSize Tool")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
        self.directory_label = QLabel("No directory selected")
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Name", "Size (MB)"])

        self.select_button = QPushButton("Select Directory")
        self.select_button.clicked.connect(self.select_directory)

        self.layout.addWidget(self.directory_label)
        self.layout.addWidget(self.select_button)
        self.layout.addWidget(self.tree_widget)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.worker = None  # Placeholder for the worker thread

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.directory_label.setText(directory)
            self.tree_widget.clear()
            root_item = QTreeWidgetItem(self.tree_widget, [os.path.basename(directory), "Calculating..."])
            self.start_worker(directory, root_item)

    def start_worker(self, directory, root_item):
        if self.worker:
            self.worker.stop()
            self.worker.wait()

        self.worker = Worker(directory, root_item)
        self.worker.update_tree.connect(self.update_tree_item)
        self.worker.work_done.connect(self.worker_finished)
        self.worker.start()

    def update_tree_item(self, size, item):
        item.setText(1, f"{size:.2f} MB")

    def worker_finished(self):
        self.worker = None
        print("Directory scanning completed.")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TreeSizeApp()
    window.show()
    sys.exit(app.exec_())
