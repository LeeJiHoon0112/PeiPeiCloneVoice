"""Giao diện chính (PyQt5) của PeiPei Clone Voice — light theme, bố cục ngang.

Bố cục (giống kiểu tool cổ điển, nhìn thấy hết không phải cuộn):
  [Tabs] ............................................. [Thiết bị · trạng thái]
  ┌─────────────────────────────┬──────────────────────────┐
  │ TRÁI: nguồn giọng + văn bản  │ PHẢI: bảng tùy chọn      │
  │       + nút tạo + kết quả    │       (các thanh trượt)  │
  └─────────────────────────────┴──────────────────────────┘
  Tiến trình: [=====] %  ·  thời gian
  Nhật ký: ......
"""
import os
import time
import datetime

import soundfile as sf
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QPlainTextEdit,
    QSlider, QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QStackedWidget, QFrame, QProgressBar,
)

from . import config
from .engine import VoiceEngine
from .profiles import ProfileManager
from .workers import Task

# ---------------------------------------------------------------- bảng màu (LIGHT)
C_BG = "#eef0f4"
C_PANEL = "#ffffff"
C_CARD2 = "#f1f3f7"
C_BORDER = "#e1e4ec"
C_BORDER2 = "#d3d7e0"
C_TEXT = "#1f2533"
C_MUTED = "#737a8c"
C_ACCENT = "#4f46e5"
C_ACCENT2 = "#6366f1"
C_ACCENT_SOFT = "#eef0fe"
C_OK = "#16a34a"
C_WARN = "#d97706"
C_DANGER = "#dc2626"

STYLE = f"""
* {{ font-family: "Segoe UI", "Inter", sans-serif; }}
QWidget {{ background: {C_BG}; color: {C_TEXT}; font-size: 13px; }}

/* ---- Thanh tab trên cùng ---- */
#TopBar {{ background: {C_PANEL}; border-bottom: 1px solid {C_BORDER}; }}
#TabBtn {{
    background: transparent; border: none; border-radius: 8px;
    padding: 9px 18px; font-size: 14px; font-weight: 700; color: {C_MUTED};
}}
#TabBtn:hover {{ background: {C_CARD2}; color: {C_TEXT}; }}
#TabBtn:checked {{ background: {C_ACCENT_SOFT}; color: {C_ACCENT}; }}
#DeviceLbl {{ color: {C_MUTED}; font-size: 12px; }}
#StatusText {{ font-weight: 700; font-size: 12px; }}

/* ---- Khối / nhóm ---- */
#Panel {{ background: {C_PANEL}; border: 1px solid {C_BORDER}; border-radius: 12px; }}
#GroupTitle {{ font-size: 13px; font-weight: 800; color: {C_TEXT}; }}
#FieldLabel {{ color: {C_MUTED}; font-size: 12px; font-weight: 600; }}
#ValueTag {{ color: {C_ACCENT}; font-weight: 700; min-width: 52px; }}
#Hint {{ color: {C_MUTED}; font-size: 11px; }}

/* ---- Ô nhập ---- */
QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {C_CARD2}; border: 1px solid {C_BORDER}; border-radius: 8px;
    padding: 8px 10px; color: {C_TEXT}; selection-background-color: {C_ACCENT};
    selection-color: white;
}}
QComboBox:hover, QLineEdit:hover, QTextEdit:hover {{ border: 1px solid {C_BORDER2}; }}
QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {C_ACCENT}; background: #ffffff;
}}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{
    background: #ffffff; border: 1px solid {C_BORDER};
    selection-background-color: {C_ACCENT_SOFT}; selection-color: {C_ACCENT};
    outline: none; padding: 4px;
}}

/* ---- Nút ---- */
QPushButton {{
    background: #ffffff; border: 1px solid {C_BORDER2}; border-radius: 8px;
    padding: 8px 13px; color: {C_TEXT}; font-weight: 600;
}}
QPushButton:hover {{ background: {C_CARD2}; border-color: {C_MUTED}; }}
QPushButton:disabled {{ background: {C_CARD2}; color: #b3b8c4; border-color: {C_BORDER}; }}
QPushButton#Primary {{
    background: {C_ACCENT}; border: none; color: white;
    font-size: 15px; font-weight: 700; padding: 12px;
}}
QPushButton#Primary:hover {{ background: {C_ACCENT2}; }}
QPushButton#Primary:disabled {{ background: #c3c6d4; color: #ffffff; }}
QPushButton#Ghost {{ background: #ffffff; border: 1px solid {C_BORDER2}; }}
QPushButton#Ghost:hover {{ background: {C_CARD2}; }}
QPushButton#Accent {{ background: {C_ACCENT_SOFT}; border: 1px solid #c7ccfb;
                      color: {C_ACCENT}; font-weight: 700; }}
QPushButton#Accent:hover {{ background: #e2e6fd; }}
QPushButton#Danger {{ background: #ffffff; border: 1px solid #f0b4b4; color: {C_DANGER}; }}
QPushButton#Danger:hover {{ background: #fdecec; }}

/* ---- Danh sách giọng ---- */
QListWidget {{
    background: {C_CARD2}; border: 1px solid {C_BORDER}; border-radius: 9px;
    padding: 4px; outline: none;
}}
QListWidget::item {{ padding: 9px 12px; border-radius: 7px; color: {C_TEXT}; }}
QListWidget::item:selected {{ background: {C_ACCENT_SOFT}; color: {C_ACCENT}; }}
QListWidget::item:hover {{ background: #e8eaf1; }}

/* ---- Slider ---- */
QSlider::groove:horizontal {{ height: 6px; background: #dfe2ea; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {C_ACCENT}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: #ffffff; border: 2px solid {C_ACCENT};
    width: 14px; height: 14px; margin: -6px 0; border-radius: 9px;
}}
QSlider::handle:horizontal:hover {{ background: {C_ACCENT_SOFT}; }}

/* ---- Nhật ký + tiến trình (đáy) ---- */
#Log {{ background: {C_CARD2}; border: 1px solid {C_BORDER}; border-radius: 8px;
        color: {C_MUTED}; font-family: "Consolas","Cascadia Mono",monospace;
        font-size: 11px; padding: 4px 6px; }}
#Prog {{ background: {C_CARD2}; border: 1px solid {C_BORDER}; border-radius: 8px;
         height: 20px; text-align: center; color: {C_TEXT}; font-weight: 700;
         font-size: 11px; }}
#Prog::chunk {{ background: {C_ACCENT}; border-radius: 7px; }}
#ProgTime {{ color: {C_MUTED}; font-size: 12px; font-weight: 600; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #cfd3de; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {C_ACCENT}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QToolTip {{ background: {C_TEXT}; color: white; border: none; padding: 6px 8px;
            border-radius: 6px; }}
"""


def _panel():
    f = QFrame()
    f.setObjectName("Panel")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(14, 12, 14, 14)
    lay.setSpacing(9)
    return f, lay


def _group_title(text):
    t = QLabel(text)
    t.setObjectName("GroupTitle")
    return t


def _field(text):
    lab = QLabel(text)
    lab.setObjectName("FieldLabel")
    return lab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PeiPei Clone Voice")
        self.resize(1080, 720)
        self.setMinimumSize(960, 600)
        self.setStyleSheet(STYLE)

        config.ensure_dirs()
        self.engine = VoiceEngine()
        self.profiles = ProfileManager()
        self._task = None
        self._last_output = None
        self._quality_steps = [("Nhanh", 16), ("Chuẩn", 32), ("Cao", 48)]

        self._t0 = 0.0
        self._prog_total = 0
        self._last_pct = 0
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._tick)

        self._build_ui()
        self._refresh_profiles()
        self._load_model()

    # ================================================================= UI
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 14, 16, 12)
        bl.setSpacing(12)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_generate_page())
        self.pages.addWidget(self._build_manage_page())
        bl.addWidget(self.pages, 1)

        bl.addWidget(self._build_bottom())

        root.addWidget(body, 1)
        self.setCentralWidget(central)

    def _build_topbar(self):
        bar = QFrame()
        bar.setObjectName("TopBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(8)

        self.tab_gen = QPushButton("🔊  Tạo giọng nói")
        self.tab_man = QPushButton("🎚️  Quản lý giọng")
        for i, b in enumerate((self.tab_gen, self.tab_man)):
            b.setObjectName("TabBtn")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, idx=i: self._switch_page(idx))
            lay.addWidget(b)
        self.tab_gen.setChecked(True)

        lay.addStretch(1)

        self.device_lbl = QLabel("")
        self.device_lbl.setObjectName("DeviceLbl")
        lay.addWidget(self.device_lbl)

        self.status_dot = QLabel("●  Đang khởi động")
        self.status_dot.setObjectName("StatusText")
        self.status_dot.setStyleSheet(f"color: {C_WARN};")
        lay.addWidget(self.status_dot)

        self.logout_btn = QPushButton("🔒  Đăng xuất")
        self.logout_btn.setObjectName("Ghost")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.clicked.connect(self._logout)
        lay.addWidget(self.logout_btn)
        return bar

    def _switch_page(self, idx):
        self.pages.setCurrentIndex(idx)
        self.tab_gen.setChecked(idx == 0)
        self.tab_man.setChecked(idx == 1)

    def _build_bottom(self):
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # hàng tiến trình
        prow = QHBoxLayout()
        prow.setSpacing(10)
        plbl = QLabel("Tiến trình:")
        plbl.setObjectName("FieldLabel")
        self.prog = QProgressBar()
        self.prog.setObjectName("Prog")
        self.prog.setRange(0, 100)
        self.prog.setValue(0)
        self.prog.setTextVisible(True)
        self.prog.setFormat("Sẵn sàng")
        self.prog_time = QLabel("")
        self.prog_time.setObjectName("ProgTime")
        self.prog_time.setMinimumWidth(190)
        self.prog_time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        prow.addWidget(plbl)
        prow.addWidget(self.prog, 1)
        prow.addWidget(self.prog_time)
        lay.addLayout(prow)

        # hàng nhật ký (gọn) + nút xóa
        lrow = QHBoxLayout()
        lrow.setSpacing(8)
        self.logbox = QPlainTextEdit()
        self.logbox.setObjectName("Log")
        self.logbox.setReadOnly(True)
        self.logbox.setFixedHeight(70)
        clear_btn = QPushButton("Xóa log")
        clear_btn.setObjectName("Ghost")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self.logbox.clear())
        lrow.addWidget(self.logbox, 1)
        lrow.addWidget(clear_btn, 0, Qt.AlignBottom)
        lay.addLayout(lrow)
        return wrap

    # ----------------------------------------------------- trang Tạo giọng
    def _build_generate_page(self):
        page = QWidget()
        split = QHBoxLayout(page)
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(12)

        # ============ CỘT TRÁI: nguồn giọng + văn bản + nút + kết quả ============
        left, ll = _panel()

        ll.addWidget(_group_title("Nguồn giọng"))
        self.mode = QComboBox()
        self.mode.addItems([
            "Dùng giọng đã lưu",
            "Dùng audio mẫu trực tiếp",
            "Thiết kế giọng (mô tả bằng lời)",
        ])
        self.mode.currentIndexChanged.connect(lambda i: self.mode_stack.setCurrentIndex(i))
        ll.addWidget(self.mode)

        self.mode_stack = QStackedWidget()
        # 0: giọng đã lưu (+ nghe thử)
        p0 = QWidget(); l0 = QVBoxLayout(p0); l0.setContentsMargins(0, 0, 0, 0); l0.setSpacing(8)
        rowc = QHBoxLayout()
        self.profile_combo = QComboBox()
        btn_refresh = QPushButton("↻"); btn_refresh.setObjectName("Ghost")
        btn_refresh.setFixedWidth(42); btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setToolTip("Làm mới danh sách giọng")
        btn_refresh.clicked.connect(self._refresh_profiles)
        rowc.addWidget(self.profile_combo, 1); rowc.addWidget(btn_refresh)
        l0.addLayout(rowc)
        self.btn_preview = QPushButton("🔊  Nghe thử giọng này")
        self.btn_preview.setObjectName("Accent")
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        self.btn_preview.setToolTip("Đọc nhanh một câu mẫu bằng giọng đang chọn")
        self.btn_preview.clicked.connect(self._preview_saved_voice)
        l0.addWidget(self.btn_preview)
        self.mode_stack.addWidget(p0)
        # 1: audio mẫu trực tiếp
        p1 = QWidget(); l1 = QVBoxLayout(p1); l1.setContentsMargins(0, 0, 0, 0); l1.setSpacing(6)
        self.ref_audio_edit = QLineEdit(); self.ref_audio_edit.setPlaceholderText("Đường dẫn file audio mẫu...")
        rb = QPushButton("Chọn..."); rb.setObjectName("Ghost"); rb.clicked.connect(self._pick_ref_audio_gen)
        row = QHBoxLayout(); row.addWidget(self.ref_audio_edit, 1); row.addWidget(rb)
        l1.addLayout(row)
        self.ref_text_edit = QTextEdit(); self.ref_text_edit.setMaximumHeight(48)
        self.ref_text_edit.setPlaceholderText("Lời thoại mẫu (có thể tự nhận diện)")
        tb = QPushButton("✨ Tự nhận diện lời thoại"); tb.setObjectName("Ghost")
        tb.clicked.connect(lambda: self._transcribe(self.ref_audio_edit, self.ref_text_edit))
        l1.addWidget(self.ref_text_edit); l1.addWidget(tb)
        self.mode_stack.addWidget(p1)
        # 2: thiết kế giọng
        p2 = QWidget(); l2 = QVBoxLayout(p2); l2.setContentsMargins(0, 0, 0, 0); l2.setSpacing(6)
        self.instruct_edit = QTextEdit(); self.instruct_edit.setMaximumHeight(60)
        self.instruct_edit.setPlaceholderText("VD: a calm middle-aged male voice, deep pitch, warm tone")
        l2.addWidget(self.instruct_edit)
        self.mode_stack.addWidget(p2)
        ll.addWidget(self.mode_stack)

        # văn bản — chiếm phần lớn cột trái
        ll.addSpacing(2)
        ll.addWidget(_group_title("Văn bản cần đọc"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Nhập nội dung muốn chuyển thành giọng nói...\nMẹo: viết có dấu chấm câu để ngắt nghỉ tự nhiên.")
        ll.addWidget(self.text_edit, 1)

        self.btn_generate = QPushButton("🔊  Tạo giọng nói")
        self.btn_generate.setObjectName("Primary")
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.clicked.connect(self._do_generate)
        ll.addWidget(self.btn_generate)

        # kết quả
        outrow = QHBoxLayout()
        self.out_label = QLabel("Chưa có kết quả.")
        self.out_label.setObjectName("Hint")
        self.btn_play = QPushButton("▶  Nghe"); self.btn_play.setObjectName("Ghost"); self.btn_play.clicked.connect(self._play)
        self.btn_stop = QPushButton("■  Dừng"); self.btn_stop.setObjectName("Ghost"); self.btn_stop.clicked.connect(self._stop)
        self.btn_saveas = QPushButton("💾  Lưu..."); self.btn_saveas.setObjectName("Ghost"); self.btn_saveas.clicked.connect(self._save_as)
        for b in (self.btn_play, self.btn_stop, self.btn_saveas):
            b.setEnabled(False); b.setCursor(Qt.PointingHandCursor)
        outrow.addWidget(self.out_label, 1)
        outrow.addWidget(self.btn_play); outrow.addWidget(self.btn_stop); outrow.addWidget(self.btn_saveas)
        ll.addLayout(outrow)

        # ============ CỘT PHẢI: bảng tùy chọn ============
        right, rl = _panel()
        right.setFixedWidth(360)
        rl.addWidget(_group_title("Tùy chọn"))
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.lang_combo = QComboBox()
        for label, _code in config.LANGUAGES:
            self.lang_combo.addItem(label)
        form.addRow(_field("Ngôn ngữ"), self.lang_combo)

        self.speed, sw, self.speed_lbl = self._slider(50, 200, 95, lambda v: f"{v/100:.2f}x")
        form.addRow(_field("Tốc độ"), sw)

        self.pause, pw, self.pause_lbl = self._slider(0, 80, 30, lambda v: f"{v/100:.2f}s")
        form.addRow(_field("Ngắt nghỉ giữa câu"), pw)

        self.guidance, gw, self.guidance_lbl = self._slider(100, 400, 250, lambda v: f"{v/100:.1f}")
        self.guidance.setToolTip("Cao hơn = giống giọng mẫu hơn (quá cao dễ cứng/méo). Khuyên 2.5–3.0")
        form.addRow(_field("Độ giống giọng"), gw)

        self.breath, bw, self.breath_lbl = self._slider(0, 100, 45, lambda v: f"{v}%")
        self.breath.setToolTip("Làm nhỏ tiếng thở / tạp âm nền giữa các từ. 0% = tắt.")
        form.addRow(_field("Giảm tiếng thở"), bw)

        self.quality = QComboBox()
        for label, _ in self._quality_steps:
            self.quality.addItem(label)
        self.quality.setCurrentIndex(1)
        form.addRow(_field("Chất lượng"), self.quality)
        rl.addLayout(form)

        hint = QLabel("💡 Mẹo: audio mẫu sạch & rõ → giọng giống hơn.\n"
                      "Tốc độ ~0.95x, Độ giống 2.5–3.0, Giảm tiếng thở 45–70%.")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        rl.addWidget(hint)
        rl.addStretch(1)

        split.addWidget(left, 1)
        split.addWidget(right, 0)
        return page

    def _slider(self, lo, hi, val, fmt):
        s = QSlider(Qt.Horizontal)
        s.setRange(lo, hi)
        lbl = QLabel(fmt(val)); lbl.setObjectName("ValueTag"); lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        s.valueChanged.connect(lambda v: lbl.setText(fmt(v)))
        s.setValue(val)
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(s, 1); h.addWidget(lbl)
        return s, w, lbl

    # ------------------------------------------------- trang Quản lý giọng
    def _build_manage_page(self):
        page = QWidget()
        split = QHBoxLayout(page)
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(12)

        # trái: danh sách
        left, ll = _panel()
        ll.addWidget(_group_title("Các giọng đã lưu"))
        self.profile_list = QListWidget()
        ll.addWidget(self.profile_list, 1)
        btnrow = QHBoxLayout()
        imp_btn = QPushButton("📥  Import giọng (.pt)..."); imp_btn.setObjectName("Ghost")
        imp_btn.setCursor(Qt.PointingHandCursor)
        imp_btn.clicked.connect(self._import_voices)
        del_btn = QPushButton("🗑  Xóa giọng đang chọn"); del_btn.setObjectName("Danger")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(self._delete_profile)
        btnrow.addWidget(imp_btn); btnrow.addWidget(del_btn)
        ll.addLayout(btnrow)

        # phải: tạo mới
        right, rl = _panel()
        right.setFixedWidth(420)
        rl.addWidget(_group_title("➕ Tạo giọng mới từ audio mẫu"))
        self.new_name = QLineEdit(); self.new_name.setPlaceholderText("Tên giọng, vd: Anh Nam")
        rl.addWidget(_field("Tên giọng")); rl.addWidget(self.new_name)

        self.new_ref_audio = QLineEdit(); self.new_ref_audio.setPlaceholderText("Chọn file audio 3–10 giây...")
        pb = QPushButton("Chọn..."); pb.setObjectName("Ghost"); pb.clicked.connect(self._pick_ref_audio_new)
        row = QHBoxLayout(); row.addWidget(self.new_ref_audio, 1); row.addWidget(pb)
        rl.addWidget(_field("Audio mẫu")); rl.addLayout(row)

        self.new_ref_text = QTextEdit(); self.new_ref_text.setMaximumHeight(70)
        tb = QPushButton("✨ Tự nhận diện lời thoại"); tb.setObjectName("Ghost")
        tb.clicked.connect(lambda: self._transcribe(self.new_ref_audio, self.new_ref_text))
        rl.addWidget(_field("Lời thoại mẫu")); rl.addWidget(self.new_ref_text); rl.addWidget(tb)

        self.btn_create = QPushButton("➕  Tạo & lưu giọng"); self.btn_create.setObjectName("Primary")
        self.btn_create.setCursor(Qt.PointingHandCursor)
        self.btn_create.clicked.connect(self._create_profile)
        rl.addWidget(self.btn_create)
        rl.addStretch(1)

        split.addWidget(left, 1)
        split.addWidget(right, 0)
        return page

    # ============================================================= helpers
    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.logbox.appendPlainText(f"[{ts}] {msg}")

    def _set_status(self, text, color=C_MUTED, device=None):
        self.status_dot.setText(f"●  {text}")
        self.status_dot.setStyleSheet(f"color: {color};")
        if device is not None:
            self.device_lbl.setText(device)

    def _error(self, msg):
        self._log("LỖI: " + msg)
        QMessageBox.critical(self, "Lỗi", msg)

    def _busy(self, on, msg=None, color=C_WARN):
        if msg:
            self._set_status(msg, color)
        ready = self.engine.ready
        for b in (self.btn_generate, self.btn_create, self.btn_preview):
            b.setEnabled(not on and ready)

    def _run(self, fn, on_done, busy_msg, pass_log=False, pass_progress=False):
        if self._task and self._task.isRunning():
            QMessageBox.information(self, "Đang bận", "Vui lòng đợi tác vụ hiện tại hoàn tất.")
            return
        self._busy(True, busy_msg)
        self._start_progress()
        t = Task(fn, pass_log=pass_log, pass_progress=pass_progress)
        t.log.connect(self._log)
        t.progress.connect(self._on_progress)
        t.done.connect(lambda r: (self._stop_progress(True), self._busy(False, "Sẵn sàng", C_OK), on_done(r)))
        t.failed.connect(lambda m: (self._stop_progress(False), self._busy(False, "Sẵn sàng", C_OK), self._error(m)))
        t.finished.connect(lambda: setattr(self, "_task", None))
        self._task = t
        t.start()

    # --------------------------------------------------- tiến trình + thời gian
    @staticmethod
    def _fmt_dur(secs: float) -> str:
        s = int(round(secs))
        if s < 60:
            return f"{s} giây"
        return f"{s // 60} phút {s % 60} giây"

    def _start_progress(self):
        self._t0 = time.time()
        self._prog_total = 0
        self._last_pct = 0
        self.prog.setRange(0, 0)
        self.prog.setFormat("Đang chạy...")
        self.prog_time.setText("⏱ 0 giây")
        if not self._timer.isActive():
            self._timer.start()

    def _on_progress(self, done: int, total: int):
        self._prog_total = total
        if total > 1:
            if self.prog.maximum() == 0:
                self.prog.setRange(0, 100)
                self.prog.setFormat("%p%")
            self._last_pct = int(done / total * 100)
            self.prog.setValue(self._last_pct)
        self._tick()

    def _tick(self):
        el = time.time() - self._t0
        if self._prog_total > 1:
            self.prog_time.setText(f"⏱ {self._last_pct}%  ·  {self._fmt_dur(el)}")
        else:
            self.prog_time.setText(f"⏱ Đang xử lý  ·  {self._fmt_dur(el)}")

    def _stop_progress(self, ok: bool):
        if self._timer.isActive():
            self._timer.stop()
        el = time.time() - self._t0
        self.prog.setRange(0, 100)
        self.prog.setValue(100 if ok else max(self._last_pct, 1))
        self.prog.setFormat("%p%")
        if ok:
            self.prog_time.setText(f"✅ Hoàn tất trong {self._fmt_dur(el)}")
        else:
            self.prog_time.setText(f"⏹ Dừng sau {self._fmt_dur(el)}")

    def _lang_code(self):
        return config.LANGUAGES[self.lang_combo.currentIndex()][1]

    def _gen_params(self):
        return dict(
            language=self._lang_code(),
            speed=self.speed.value() / 100.0,
            num_step=self._quality_steps[self.quality.currentIndex()][1],
            pause_sec=self.pause.value() / 100.0,
            guidance_scale=self.guidance.value() / 100.0,
            breath_reduce=self.breath.value() / 100.0,
        )

    # --------------------------------------------------------- model load
    def _load_model(self):
        self._busy(True, "Đang nạp model...", C_WARN)
        self._start_progress()
        t = Task(self.engine.load, pass_log=True)
        t.log.connect(self._log)
        t.done.connect(lambda _: (self._stop_progress(True), self._on_model_loaded()))
        t.failed.connect(lambda m: (self._stop_progress(False),
                                    self._set_status("Nạp model thất bại", C_DANGER),
                                    self._error(m)))
        t.finished.connect(lambda: setattr(self, "_task", None))
        self._task = t
        t.start()

    def _on_model_loaded(self):
        dev = "GPU" if self.engine.device == "cuda" else "CPU"
        self._set_status("Sẵn sàng", C_OK, device=f"Thiết bị: {dev}")
        self._busy(False)
        try:
            added = self.profiles.auto_import_old_tool_voices()
            if added:
                self._log(f"Đã import {len(added)} giọng cũ: {', '.join(added)}")
                self._refresh_profiles()
        except Exception as e:
            self._log(f"Bỏ qua import giọng cũ: {e}")

    # ----------------------------------------------------------- profiles
    def _refresh_profiles(self):
        items = self.profiles.list()
        self.profile_combo.clear()
        self.profile_list.clear()
        for it in items:
            self.profile_combo.addItem(it["name"])
            preview = (it["meta"].get("ref_text") or "").strip()
            label = "🎤  " + it["name"] + (f"   —  “{preview[:46]}…”" if preview else "")
            li = QListWidgetItem(label)
            li.setData(Qt.UserRole, it["name"])
            self.profile_list.addItem(li)
        if not items:
            self.profile_list.addItem("Chưa có giọng nào — tạo ở cột bên phải.")
        if hasattr(self, "btn_preview"):
            self.btn_preview.setEnabled(bool(items) and self.engine.ready)

    def _preview_saved_voice(self):
        if not self.engine.ready:
            return self._error("Model chưa nạp xong.")
        name = self.profile_combo.currentText().strip()
        if not name:
            return self._error("Chưa có giọng đã lưu để nghe thử.")
        params = self._gen_params()
        sample_text = f"Xin chào, đây là giọng {name}. Bạn nghe thử xem có giống không nhé."

        def job(log=None, progress=None):
            prompt = self.profiles.load_prompt(name)
            return self.engine.generate(sample_text, voice_clone_prompt=prompt,
                                        progress=progress, **params)

        def done(result):
            sr, audio = result
            self._present_audio(sr, audio, prefix="preview")

        self._run(job, done, f"Đang tạo câu mẫu cho '{name}'...", pass_progress=True)

    def _create_profile(self):
        name = self.new_name.text().strip()
        ref_audio = self.new_ref_audio.text().strip()
        ref_text = self.new_ref_text.toPlainText().strip()
        if not name:
            return self._error("Hãy nhập tên giọng.")
        if not ref_audio or not os.path.exists(ref_audio):
            return self._error("Hãy chọn file audio mẫu hợp lệ.")
        if self.profiles.exists(name):
            r = QMessageBox.question(self, "Ghi đè?", f"Giọng '{name}' đã tồn tại. Ghi đè?")
            if r != QMessageBox.Yes:
                return

        sample_text = f"Xin chào, đây là giọng {name}. Bạn nghe thử xem có giống không nhé."
        params = self._gen_params()

        def job(log=None, progress=None):
            prompt = self.engine.create_profile(ref_audio, ref_text or None)
            saved = self.profiles.save(name, prompt, ref_audio=ref_audio, ref_text=ref_text)
            sr, audio = self.engine.generate(sample_text, voice_clone_prompt=prompt,
                                             progress=progress, **params)
            return saved, sr, audio

        def done(result):
            saved, sr, audio = result
            self._log(f"Đã lưu giọng: {saved} — đang phát câu mẫu để nghe thử.")
            self.new_name.clear(); self.new_ref_audio.clear(); self.new_ref_text.clear()
            self._refresh_profiles()
            self._present_audio(sr, audio, prefix="sample")
            QMessageBox.information(
                self, "Xong",
                f"Đã tạo giọng '{saved}'.\n\nĐang phát câu mẫu để bạn nghe thử — "
                "nếu chưa giống, hãy thử lại với audio mẫu rõ và dài hơn.")

        self._run(job, done, f"Đang tạo giọng & câu mẫu '{name}'...", pass_progress=True)

    def _delete_profile(self):
        it = self.profile_list.currentItem()
        if not it:
            return
        name = it.data(Qt.UserRole)
        if not name:
            return
        r = QMessageBox.question(self, "Xóa giọng", f"Xóa giọng '{name}'?")
        if r == QMessageBox.Yes:
            self.profiles.delete(name)
            self._log(f"Đã xóa giọng: {name}")
            self._refresh_profiles()

    def _import_voices(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Chọn file giọng (.pt) để import", "", "Voice profile (*.pt);;Tất cả (*.*)")
        if not paths:
            return
        added, skipped = [], 0
        for p in paths:
            try:
                name = self.profiles.import_pt_file(p, overwrite=False)
                if name:
                    added.append(name)
                else:
                    skipped += 1
            except Exception as e:
                self._log(f"Lỗi import {os.path.basename(p)}: {e}")
        self._refresh_profiles()
        msg = f"Đã import {len(added)} giọng."
        if skipped:
            msg += f" Bỏ qua {skipped} giọng (đã tồn tại)."
        self._log(msg)
        QMessageBox.information(self, "Import giọng", msg)

    # --------------------------------------------------------- transcribe
    def _transcribe(self, audio_edit: QLineEdit, text_target: QTextEdit):
        if not self.engine.ready:
            return self._error("Model chưa nạp xong.")
        path = audio_edit.text().strip()
        if not path or not os.path.exists(path):
            return self._error("Hãy chọn file audio mẫu trước.")

        def job(log=None):
            return self.engine.transcribe(path)

        def done(text):
            text_target.setPlainText(text)
            self._log(f"Nhận diện: {text!r}")

        self._run(job, done, "Đang nhận diện lời thoại...")

    # ----------------------------------------------------------- generate
    def _do_generate(self):
        if not self.engine.ready:
            return self._error("Model chưa nạp xong.")
        text = self.text_edit.toPlainText().strip()
        if not text:
            return self._error("Hãy nhập văn bản cần đọc.")
        common = self._gen_params()
        mode = self.mode.currentIndex()

        if mode == 0:
            name = self.profile_combo.currentText().strip()
            if not name:
                return self._error("Chưa có giọng đã lưu. Hãy tạo ở tab Quản lý giọng.")

            def job(log=None, progress=None):
                prompt = self.profiles.load_prompt(name)
                return self.engine.generate(text, voice_clone_prompt=prompt,
                                            progress=progress, **common)
        elif mode == 1:
            ra = self.ref_audio_edit.text().strip()
            rt = self.ref_text_edit.toPlainText().strip()
            if not ra or not os.path.exists(ra):
                return self._error("Hãy chọn file audio mẫu hợp lệ.")

            def job(log=None, progress=None):
                return self.engine.generate(text, ref_audio=ra, ref_text=rt or None,
                                            progress=progress, **common)
        else:
            ins = self.instruct_edit.toPlainText().strip()

            def job(log=None, progress=None):
                return self.engine.generate(text, instruct=ins or None,
                                            progress=progress, **common)

        self._run(job, self._on_generated, "Đang tạo giọng nói...", pass_progress=True)

    def _on_generated(self, result):
        sr, audio = result
        self._present_audio(sr, audio, prefix="output")

    def _present_audio(self, sr, audio, prefix="output"):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = os.path.join(config.OUTPUTS_DIR, f"{prefix}_{ts}.wav")
        sf.write(out, audio, sr)
        self._last_output = out
        dur = len(audio) / sr
        self.out_label.setText(f"✅  {os.path.basename(out)}   ·   {dur:.1f}s")
        self.out_label.setStyleSheet(f"color: {C_TEXT};")
        self._log(f"Đã lưu: {out}")
        for b in (self.btn_play, self.btn_stop, self.btn_saveas):
            b.setEnabled(True)
        self._play()
        return out

    # ----------------------------------------------------------- playback
    def _play(self):
        if not self._last_output or not os.path.exists(self._last_output):
            return
        try:
            import winsound
            winsound.PlaySound(self._last_output, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            self._log(f"Không phát được audio: {e}")

    def _stop(self):
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

    def _save_as(self):
        if not self._last_output:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Lưu audio", "output.wav", "WAV (*.wav)")
        if path:
            import shutil
            shutil.copyfile(self._last_output, path)
            self._log(f"Đã lưu thành: {path}")

    # --------------------------------------------------------- pick files
    def _pick_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn audio mẫu", "",
            "Audio (*.wav *.mp3 *.flac *.m4a *.ogg *.aac);;Tất cả (*.*)")
        return path

    def _pick_ref_audio_gen(self):
        p = self._pick_audio()
        if p:
            self.ref_audio_edit.setText(p)

    def _pick_ref_audio_new(self):
        p = self._pick_audio()
        if p:
            self.new_ref_audio.setText(p)

    def _logout(self):
        from app import auth
        r = QMessageBox.question(
            self, "Đăng xuất",
            "Bỏ ghi nhớ trên máy này? Lần sau mở app sẽ phải nhập lại mật khẩu.\n"
            "(App sẽ đóng lại.)")
        if r == QMessageBox.Yes:
            auth.forget_login()
            self.close()

    def closeEvent(self, e):
        self._stop()
        super().closeEvent(e)
