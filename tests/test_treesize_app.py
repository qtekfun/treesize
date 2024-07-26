import pytest
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from src.main import TreeSizeApp, Worker
from pyfakefs.fake_filesystem_unittest import Patcher

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    main_window = TreeSizeApp()
    qtbot.addWidget(main_window)
    return main_window

def test_initial_state(app):
    assert app.windowTitle() == "TreeSize Tool"
    assert app.directory_label.text() == "No directory selected"
    assert app.tree_widget.topLevelItemCount() == 0

def test_directory_selection(app, qtbot):
    test_directory = "/path/to/test/directory"  # Replace with a valid path for testing
    app.directory_label.setText(test_directory)
    assert app.directory_label.text() == test_directory

def test_worker_thread(app, qtbot):
    with Patcher() as patcher:
        # Set up fake filesystem
        test_directory = "/fake/test/directory"
        patcher.fs.create_dir(test_directory)
        patcher.fs.create_file(f"{test_directory}/file1.txt", contents="content")
        patcher.fs.create_file(f"{test_directory}/file2.txt", contents="content")

        parent_item = QTreeWidgetItem(["Test Parent"])
        worker = Worker(test_directory, parent_item)

        def handle_update(size, item):
            assert size >= 0

        worker.update_tree.connect(handle_update)
        worker.start()
        worker.wait()

        assert not worker.isRunning()
        assert parent_item.childCount() > 0

def test_app_close(app, qtbot):
    app.close()
    assert app.worker is None
