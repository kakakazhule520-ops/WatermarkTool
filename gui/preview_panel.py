from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel("预览区域")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.label.setStyleSheet("border: 1px solid #c0c0c0; background: #f8f8f8;")
        self.label.setMinimumHeight(220)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

    def set_preview(self, image_path: str | None = None, text: str = "未加载预览"):
        if image_path and Path(image_path).exists():
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.label.setPixmap(scaled)
                self.label.setText("")
                return
        self.label.setPixmap(QPixmap())
        self.label.setText(text)
