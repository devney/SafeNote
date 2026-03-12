import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def app() -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing

    app = QApplication(sys.argv)
    return app


@pytest.fixture
def main_window(app: QApplication):
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from src.safenote_window import MainWindow  # type: ignore

    window = MainWindow()
    yield window
    window.close()

