"""Điểm khởi chạy PeiPei Clone Voice (desktop, PyQt5 + OmniVoice)."""
import os
import sys

# Giảm cảnh báo thừa
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Windows không cho tạo symlink nếu không chạy bằng quyền Admin / Developer Mode
# (gây OSError [WinError 1314] khi HuggingFace tải model lần đầu). Tắt symlink →
# HF sẽ COPY file thẳng vào cache, không cần quyền đặc biệt. PHẢI đặt TRƯỚC khi
# import huggingface_hub (hằng số được đọc 1 lần lúc import).
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Tránh lỗi UnicodeEncodeError khi in tiếng Việt ra console Windows (cp1252)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _fix_qt_plugin_path():
    """Sửa lỗi 'Could not find the Qt platform plugin windows'.

    Nguyên nhân: biến môi trường QT_* bị để rỗng/sai khiến Qt không tìm được
    thư mục plugin (chứa qwindows.dll). Ta tự trỏ đúng đường dẫn plugin của
    PyQt5 đang cài, và xóa các biến QT_* rỗng/hỏng. Chạy TRƯỚC khi tạo QApplication.
    """
    # Xóa biến QT_QPA_PLATFORM nếu nó rỗng/khoảng trắng (gây lỗi init platform)
    val = os.environ.get("QT_QPA_PLATFORM")
    if val is not None and val.strip() == "":
        os.environ.pop("QT_QPA_PLATFORM", None)

    try:
        import PyQt5
        base = os.path.dirname(PyQt5.__file__)
        # PyQt5 mới dùng thư mục 'Qt5', bản cũ dùng 'Qt'
        for sub in ("Qt5", "Qt"):
            plugins = os.path.join(base, sub, "plugins")
            platforms = os.path.join(plugins, "platforms")
            if os.path.isdir(platforms):
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms
                os.environ["QT_PLUGIN_PATH"] = plugins
                # Một số bản PyQt5 đọc qua API này
                try:
                    from PyQt5.QtCore import QCoreApplication
                    QCoreApplication.addLibraryPath(plugins)
                except Exception:
                    pass
                break
    except Exception:
        pass


def main():
    _fix_qt_plugin_path()

    from PyQt5.QtWidgets import QApplication, QDialog
    from app.login_dialog import LoginDialog
    from app.main_window import MainWindow

    app = QApplication(sys.argv)

    # Nếu máy này đã "ghi nhớ" và còn khớp mật khẩu hiện hành → bỏ qua đăng nhập.
    from app import auth
    if not auth.is_remembered():
        # Màn hình đăng nhập: sai/đóng thì thoát, không vào app.
        login = LoginDialog()
        if login.exec_() != QDialog.Accepted:
            return 0

    win = MainWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
