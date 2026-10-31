"""Core package export helpers for WatermarkTool."""

from __future__ import annotations

__all__ = [
    "main",
]


def main() -> None:
    """Run the GUI application."""
    from PySide6.QtWidgets import QApplication
    from gui.main_window import MainWindow
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("WatermarkTool")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
