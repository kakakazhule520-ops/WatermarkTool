from PySide6.QtWidgets import QApplication
import sys

from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WatermarkTool")
    app.setOrganizationName("WatermarkTool")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
