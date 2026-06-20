"""Hộp thoại KÍCH HOẠT bản quyền — hiện khi license chưa hợp lệ.

Khách copy 'Mã máy' gửi người bán để lấy license key, rồi dán key vào kích hoạt.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QApplication,
)

from . import license_client

_STYLE = """
QDialog { background: #eef0f4; }
QLabel#Title { font-size: 20px; font-weight: 800; color: #1f2533; }
QLabel#Sub { color: #737a8c; font-size: 12px; }
QLabel#Err { color: #dc2626; font-size: 12px; font-weight: 600; }
QLabel#Ok { color: #059669; font-size: 12px; font-weight: 600; }
QLabel#MidLabel { color: #737a8c; font-size: 12px; }
QLineEdit {
    background: #ffffff; border: 1px solid #d3d7e0; border-radius: 8px;
    padding: 10px 12px; font-size: 14px; color: #1f2533;
}
QLineEdit:read-only { background: #f3f4f8; color: #1f2533; font-weight: 700; }
QLineEdit:focus { border: 1px solid #4f46e5; }
QPushButton#Primary {
    background: #4f46e5; border: none; border-radius: 8px; color: white;
    font-size: 15px; font-weight: 700; padding: 12px;
}
QPushButton#Primary:hover { background: #6366f1; }
QPushButton#Primary:disabled { background: #a5a3e8; }
QPushButton#Ghost {
    background: #ffffff; border: 1px solid #d3d7e0; border-radius: 8px;
    color: #1f2533; padding: 9px 12px; font-size: 13px;
}
QPushButton#Ghost:hover { border: 1px solid #4f46e5; }
"""


class LicenseDialog(QDialog):
    """Trả về Accepted khi kích hoạt thành công (license VALID/GRACE)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PeiPei Clone Voice — Kích hoạt bản quyền")
        self.setFixedWidth(440)
        self.setStyleSheet(_STYLE)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 24)
        lay.setSpacing(10)

        title = QLabel("🔑  Kích hoạt bản quyền")
        title.setObjectName("Title")
        sub = QLabel("Gửi 'Mã máy' bên dưới cho người bán để nhận license key, "
                     "rồi dán key vào ô và bấm Kích hoạt.")
        sub.setObjectName("Sub")
        sub.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(6)

        # --- Mã máy (machine id) + nút Copy ---
        midlbl = QLabel("Mã máy của bạn:")
        midlbl.setObjectName("MidLabel")
        lay.addWidget(midlbl)
        midrow = QHBoxLayout()
        midrow.setSpacing(8)
        self.mid = QLineEdit(license_client.get_machine_id())
        self.mid.setReadOnly(True)
        self.mid.setCursorPosition(0)
        btn_copy = QPushButton("📋 Copy")
        btn_copy.setObjectName("Ghost")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.clicked.connect(self._copy_mid)
        midrow.addWidget(self.mid, 1)
        midrow.addWidget(btn_copy)
        lay.addLayout(midrow)
        lay.addSpacing(6)

        # --- Ô nhập license key ---
        keylbl = QLabel("License key:")
        keylbl.setObjectName("MidLabel")
        lay.addWidget(keylbl)
        self.key = QLineEdit()
        self.key.setPlaceholderText("Dán license key vào đây...")
        self.key.returnPressed.connect(self._activate)
        lay.addWidget(self.key)

        self.msg = QLabel("")
        self.msg.setObjectName("Err")
        self.msg.setWordWrap(True)
        lay.addWidget(self.msg)

        self.btn = QPushButton("Kích hoạt")
        self.btn.setObjectName("Primary")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self._activate)
        lay.addWidget(self.btn)

        self.key.setFocus()

    def _copy_mid(self):
        QApplication.clipboard().setText(self.mid.text())
        self.msg.setObjectName("Ok")
        self.msg.setStyleSheet("color:#059669; font-weight:600;")
        self.msg.setText("Đã copy mã máy. Gửi cho người bán để lấy key.")

    def _set_err(self, text):
        self.msg.setStyleSheet("color:#dc2626; font-weight:600;")
        self.msg.setText(text)

    def _activate(self):
        key = self.key.text().strip()
        if not key:
            return self._set_err("Hãy dán license key.")
        self.btn.setEnabled(False)
        self.btn.setText("Đang kích hoạt...")
        self.msg.setStyleSheet("color:#737a8c; font-weight:600;")
        self.msg.setText("Đang kết nối server, vui lòng đợi...")
        QApplication.processEvents()
        try:
            ok, info = license_client.activate(key)
        except Exception as e:                       # phòng lỗi bất ngờ
            ok, info = False, f"Lỗi: {e}"
        if ok and license_client.check()["status"] in ("VALID", "GRACE"):
            self.accept()
            return
        self.btn.setEnabled(True)
        self.btn.setText("Kích hoạt")
        self._set_err(info or "Kích hoạt thất bại.")
        self.key.setFocus()
