from __future__ import annotations

import os
from typing import Any, Dict

from PySide6.QtCore import QObject, Signal, Slot

from core.file_manager import build_output_path, scan_image_files, validate_source_dir
from core.image_processor import process_one_image


class ProcessingWorker(QObject):
    log = Signal(str)
    progress = Signal(int, int, str)
    finished = Signal(dict)

    def __init__(self, settings: Dict[str, Any]):
        super().__init__()
        self.settings = settings
        self.cancel_requested = False

    def stop(self):
        self.cancel_requested = True

    @Slot()
    def run(self):
        try:
            ok, error = validate_source_dir(self.settings.get("source_dir", ""))
            if not ok:
                self.finished.emit({"success": 0, "failed": 1, "skipped": 0, "cancelled": False, "error": error})
                return

            files = scan_image_files(self.settings.get("source_dir", ""))
            total = len(files)
            self.progress.emit(0, total, "开始扫描源目录")
            self.log.emit(f"[INFO] 共发现 {total} 张图片。")

            success_count = 0
            skip_count = 0
            fail_count = 0

            for index, source_path in enumerate(files, start=1):
                if self.cancel_requested:
                    self.log.emit("[WARN] 用户中止处理任务。")
                    break

                output_path = build_output_path(
                    source_path,
                    self.settings.get("output_dir", ""),
                    self.settings.get("output_format", "keep"),
                )
                if self.settings.get("resume_enabled", True) and os.path.exists(output_path):
                    skip_count += 1
                    self.log.emit(f"[SKIP] {os.path.basename(source_path)}（目标文件已存在）")
                    self.progress.emit(index, total, f"跳过 {index}/{total}")
                    continue

                self.log.emit(f"[RUN] 正在处理：{os.path.basename(source_path)}")
                success, message, final_path = process_one_image(
                    source_path,
                    output_path,
                    self.settings.get("watermark_path", ""),
                    self.settings,
                    index=index,
                )

                if success:
                    success_count += 1
                    self.log.emit(f"[OK] 处理成功：{os.path.basename(source_path)}")
                else:
                    fail_count += 1
                    self.log.emit(f"[ERROR] 处理失败：{os.path.basename(source_path)}（{message}）")

                self.progress.emit(index, total, f"已处理 {index}/{total}")

            self.finished.emit({
                "success": success_count,
                "failed": fail_count,
                "skipped": skip_count,
                "cancelled": self.cancel_requested,
                "error": "",
            })
        except Exception as exc:
            self.log.emit(f"[ERROR] 批量处理异常：{exc}")
            self.finished.emit({
                "success": 0,
                "failed": 1,
                "skipped": 0,
                "cancelled": False,
                "error": str(exc),
            })
