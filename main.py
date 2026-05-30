"""Điểm khởi chạy PeiPei Clone Voice (desktop, PyQt5 + OmniVoice)."""
import os
import sys

# Giảm cảnh báo thừa
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Tránh lỗi UnicodeEncodeError khi in tiếng Việt ra console Windows (cp1252)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    from PyQt5.QtWidgets import QApplication
    from app.main_window import MainWindow

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
