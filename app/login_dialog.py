"""Hộp thoại đăng nhập — nhập mật khẩu mới được mở app."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
)

from . import auth

_STYLE = """
QDialog { background: #eef0f4; }
QLabel#Title { font-size: 20px; font-weight: 800; color: #1f2533; }
QLabel#Sub { color: #737a8c; font-size: 12px; }
QLabel#Err { color: #dc2626; font-size: 12px; font-weight: 600; }
QLineEdit {
    background: #ffffff; border: 1px solid #d3d7e0; border-radius: 8px;
    padding: 10px 12px; font-size: 14px; color: #1f2533;
}
QLineEdit:focus { border: 1px solid #4f46e5; }
QPushButton#Primary {
    background: #4f46e5; border: none; border-radius: 8px; color: white;
    font-size: 15px; font-weight: 700; padding: 12px;
}
QPushButton#Primary:hover { background: #6366f1; }
QCheckBox { color: #737a8c; font-size: 12px; }
"""


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PeiPei Clone Voice — Đăng nhập")
        self.setFixedWidth(380)
        self.setStyleSheet(_STYLE)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 24)
        lay.setSpacing(10)

        title = QLabel("🎙️  PeiPei Clone Voice")
        title.setObjectName("Title")
        sub = QLabel("Nhập mật khẩu để mở ứng dụng.")
        sub.setObjectName("Sub")
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(8)

        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        self.pw.setPlaceholderText("Mật khẩu...")
        self.pw.returnPressed.connect(self._try)
        lay.addWidget(self.pw)

        self.show_cb = QCheckBox("Hiện mật khẩu")
        self.show_cb.toggled.connect(
            lambda on: self.pw.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        lay.addWidget(self.show_cb)

        self.remember_cb = QCheckBox("Ghi nhớ trên máy này (lần sau khỏi nhập)")
        self.remember_cb.setChecked(True)
        lay.addWidget(self.remember_cb)

        self.err = QLabel("")
        self.err.setObjectName("Err")
        lay.addWidget(self.err)

        btn = QPushButton("Đăng nhập")
        btn.setObjectName("Primary")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._try)
        lay.addWidget(btn)

        self._tries = 0
        self.pw.setFocus()

    def _try(self):
        if auth.verify(self.pw.text()):
            if self.remember_cb.isChecked():
                auth.remember_login()
            self.accept()
            return
        self._tries += 1
        self.err.setText(f"Sai mật khẩu. (lần {self._tries})")
        self.pw.selectAll()
        self.pw.setFocus()
