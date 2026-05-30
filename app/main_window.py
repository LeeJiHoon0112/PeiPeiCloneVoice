"""Giao diện chính (PyQt5) của PeiPei Clone Voice — light theme chuyên nghiệp.

Bố cục: Sidebar (logo · điều hướng · trạng thái · NHẬT KÝ) | Nội dung (thẻ).
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
    QStackedWidget, QFrame, QScrollArea, QProgressBar,
)

from . import config
from .engine import VoiceEngine
from .profiles import ProfileManager
from .workers import Task

# ---------------------------------------------------------------- bảng màu (LIGHT)
C_BG = "#eef0f4"        # nền app (xám rất nhạt)
C_SIDEBAR = "#ffffff"   # nền sidebar (trắng)
C_CARD = "#ffffff"      # nền thẻ
C_CARD2 = "#f1f3f7"     # nền ô nhập
C_BORDER = "#e1e4ec"    # viền nhạt
C_BORDER2 = "#d3d7e0"   # viền đậm hơn (focus phụ)
C_TEXT = "#1f2533"      # chữ chính (xám than)
C_MUTED = "#737a8c"     # chữ phụ
C_ACCENT = "#4f46e5"    # indigo (nút chính)
C_ACCENT2 = "#6366f1"   # indigo sáng (hover)
C_ACCENT_SOFT = "#eef0fe"  # nền nhạt cho mục nav đang chọn
C_OK = "#16a34a"        # xanh "sẵn sàng"
C_WARN = "#d97706"      # cam "đang bận"
C_DANGER = "#dc2626"    # đỏ

STYLE = f"""
* {{ font-family: "Segoe UI", "Inter", sans-serif; }}
QWidget {{ background: {C_BG}; color: {C_TEXT}; font-size: 13px; }}

/* ---- Sidebar ---- */
#Sidebar {{ background: {C_SIDEBAR}; border-right: 1px solid {C_BORDER}; }}
#AppTitle {{ font-size: 17px; font-weight: 800; color: {C_TEXT}; }}
#AppSub {{ font-size: 11px; color: {C_MUTED}; }}
#NavBtn {{
    background: transparent; border: none; border-radius: 9px;
    padding: 11px 14px; text-align: left; font-size: 14px;
    font-weight: 600; color: {C_MUTED};
}}
#NavBtn:hover {{ background: {C_CARD2}; color: {C_TEXT}; }}
#NavBtn:checked {{ background: {C_ACCENT_SOFT}; color: {C_ACCENT}; }}
#SideLabel {{ color: {C_MUTED}; font-size: 11px; font-weight: 700;
             letter-spacing: 0.5px; }}

/* ---- Thẻ ---- */
#Card {{ background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 12px; }}
#CardTitle {{ font-size: 13px; font-weight: 700; color: {C_TEXT}; }}
#PageTitle {{ font-size: 22px; font-weight: 800; color: {C_TEXT}; }}
#PageSub {{ color: {C_MUTED}; font-size: 12px; }}
#FieldLabel {{ color: {C_MUTED}; font-size: 12px; font-weight: 600; }}
#ValueTag {{ color: {C_ACCENT}; font-weight: 700; min-width: 50px; }}

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
QComboBox::down-arrow {{ width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background: #ffffff; border: 1px solid {C_BORDER};
    selection-background-color: {C_ACCENT_SOFT}; selection-color: {C_ACCENT};
    outline: none; padding: 4px;
}}

/* ---- Nút ---- */
QPushButton {{
    background: #ffffff; border: 1px solid {C_BORDER2}; border-radius: 8px;
    padding: 9px 14px; color: {C_TEXT}; font-weight: 600;
}}
QPushButton:hover {{ background: {C_CARD2}; border-color: {C_MUTED}; }}
QPushButton:disabled {{ background: {C_CARD2}; color: #b3b8c4; border-color: {C_BORDER}; }}
QPushButton#Primary {{
    background: {C_ACCENT}; border: none; color: white;
    font-size: 15px; font-weight: 700; padding: 13px;
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
QListWidget::item {{ padding: 10px 12px; border-radius: 7px; color: {C_TEXT}; }}
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

/* ---- Nhật ký (sidebar) ---- */
#Log {{ background: {C_CARD2}; border: 1px solid {C_BORDER}; border-radius: 9px;
        color: {C_MUTED}; font-family: "Consolas","Cascadia Mono",monospace;
        font-size: 11px; padding: 6px; }}

/* ---- Thanh tiến trình ---- */
#Prog {{ background: {C_CARD2}; border: 1px solid {C_BORDER}; border-radius: 8px;
         height: 22px; text-align: center; color: {C_TEXT}; font-weight: 700;
         font-size: 12px; }}
#Prog::chunk {{ background: {C_ACCENT}; border-radius: 7px; }}
#ProgTime {{ color: {C_MUTED}; font-size: 12px; font-weight: 600; }}

/* ---- Status pill ---- */
#StatusPill {{ background: {C_CARD2}; border: 1px solid {C_BORDER};
              border-radius: 9px; padding: 8px; }}
#StatusText {{ font-weight: 700; }}
#StatusDevice {{ color: {C_MUTED}; font-size: 11px; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #cfd3de; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {C_ACCENT}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollArea {{ border: none; background: transparent; }}
QToolTip {{ background: {C_TEXT}; color: white; border: none; padding: 6px 8px;
            border-radius: 6px; }}
"""


def _card(title=None):
    """Tạo một thẻ (frame bo góc) kèm layout dọc; trả về (frame, layout)."""
    f = QFrame()
    f.setObjectName("Card")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(16, 14, 16, 16)
    lay.setSpacing(10)
    if title:
        t = QLabel(title)
        t.setObjectName("CardTitle")
        lay.addWidget(t)
    return f, lay


def _field(label_text):
    """Nhãn nhỏ kiểu 'FieldLabel'."""
    lab = QLabel(label_text)
    lab.setObjectName("FieldLabel")
    return lab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PeiPei Clone Voice")
        self.resize(1040, 780)
        self.setMinimumSize(940, 660)
        self.setStyleSheet(STYLE)

        config.ensure_dirs()
        self.engine = VoiceEngine()
        self.profiles = ProfileManager()
        self._task = None
        self._last_output = None
        self._quality_steps = [("Nhanh", 16), ("Chuẩn", 32), ("Cao", 48)]

        # đồng hồ đo thời gian chạy
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
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(14)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_generate_page())
        self.pages.addWidget(self._build_manage_page())
        cl.addWidget(self.pages, 1)

        root.addWidget(content, 1)
        self.setCentralWidget(central)

    def _build_sidebar(self):
        bar = QFrame()
        bar.setObjectName("Sidebar")
        bar.setFixedWidth(264)
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(16, 20, 16, 16)
        lay.setSpacing(8)

        # logo + tên
        logo = QLabel("🎙️  PeiPei Voice")
        logo.setObjectName("AppTitle")
        sub = QLabel("Nhân bản giọng nói AI")
        sub.setObjectName("AppSub")
        lay.addWidget(logo)
        lay.addWidget(sub)
        lay.addSpacing(18)

        # nav
        self.nav_gen = QPushButton("🔊   Tạo giọng nói")
        self.nav_man = QPushButton("🎚️   Quản lý giọng")
        for i, b in enumerate((self.nav_gen, self.nav_man)):
            b.setObjectName("NavBtn")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, idx=i: self._switch_page(idx))
            lay.addWidget(b)
        self.nav_gen.setChecked(True)

        lay.addSpacing(14)

        # trạng thái model
        pill = QFrame()
        pill.setObjectName("StatusPill")
        pl = QVBoxLayout(pill)
        pl.setContentsMargins(12, 10, 12, 10)
        pl.setSpacing(3)
        self.status_dot = QLabel("●  Đang khởi động")
        self.status_dot.setObjectName("StatusText")
        self.status_dot.setStyleSheet(f"color: {C_WARN};")
        self.status_device = QLabel("")
        self.status_device.setObjectName("StatusDevice")
        self.status_device.setWordWrap(True)
        pl.addWidget(self.status_dot)
        pl.addWidget(self.status_device)
        lay.addWidget(pill)

        # Đăng xuất (bỏ ghi nhớ máy này → lần sau mở app phải nhập lại mật khẩu)
        logout_btn = QPushButton("🔒  Đăng xuất")
        logout_btn.setObjectName("Ghost")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        lay.addWidget(logout_btn)

        lay.addSpacing(12)

        # NHẬT KÝ (logs) — chiếm phần còn lại của sidebar
        log_head = QHBoxLayout()
        log_lbl = QLabel("NHẬT KÝ")
        log_lbl.setObjectName("SideLabel")
        clear_btn = QPushButton("Xóa")
        clear_btn.setObjectName("Ghost")
        clear_btn.setFixedHeight(24)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        clear_btn.clicked.connect(lambda: self.logbox.clear())
        log_head.addWidget(log_lbl)
        log_head.addStretch(1)
        log_head.addWidget(clear_btn)
        lay.addLayout(log_head)

        self.logbox = QPlainTextEdit()
        self.logbox.setObjectName("Log")
        self.logbox.setReadOnly(True)
        lay.addWidget(self.logbox, 1)   # stretch = lấp đầy chiều cao còn lại
        return bar

    def _switch_page(self, idx):
        self.pages.setCurrentIndex(idx)
        self.nav_gen.setChecked(idx == 0)
        self.nav_man.setChecked(idx == 1)

    # ----------------------------------------------------- trang Tạo giọng
    def _build_generate_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        scroll.setWidget(page)
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(14)

        title = QLabel("Tạo giọng nói")
        title.setObjectName("PageTitle")
        psub = QLabel("Chọn nguồn giọng, nhập văn bản và tạo audio.")
        psub.setObjectName("PageSub")
        lay.addWidget(title)
        lay.addWidget(psub)

        # --- thẻ nguồn giọng ---
        cf, cl = _card("Nguồn giọng")
        self.mode = QComboBox()
        self.mode.addItems([
            "Dùng giọng đã lưu",
            "Dùng audio mẫu trực tiếp",
            "Thiết kế giọng (mô tả bằng lời)",
        ])
        self.mode.currentIndexChanged.connect(lambda i: self.mode_stack.setCurrentIndex(i))
        cl.addWidget(self.mode)

        self.mode_stack = QStackedWidget()
        # 0: giọng đã lưu  (+ nút nghe thử)
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
        p1 = QWidget(); l1 = QVBoxLayout(p1); l1.setContentsMargins(0, 0, 0, 0); l1.setSpacing(8)
        self.ref_audio_edit = QLineEdit(); self.ref_audio_edit.setPlaceholderText("Đường dẫn file audio mẫu...")
        rb = QPushButton("Chọn file..."); rb.setObjectName("Ghost"); rb.clicked.connect(self._pick_ref_audio_gen)
        row = QHBoxLayout(); row.addWidget(self.ref_audio_edit, 1); row.addWidget(rb)
        l1.addWidget(_field("Audio mẫu")); l1.addLayout(row)
        self.ref_text_edit = QTextEdit(); self.ref_text_edit.setMaximumHeight(56)
        tb = QPushButton("✨ Tự nhận diện lời thoại"); tb.setObjectName("Ghost")
        tb.clicked.connect(lambda: self._transcribe(self.ref_audio_edit, self.ref_text_edit))
        l1.addWidget(_field("Lời thoại mẫu")); l1.addWidget(self.ref_text_edit); l1.addWidget(tb)
        self.mode_stack.addWidget(p1)
        # 2: thiết kế giọng
        p2 = QWidget(); l2 = QVBoxLayout(p2); l2.setContentsMargins(0, 0, 0, 0); l2.setSpacing(8)
        self.instruct_edit = QTextEdit(); self.instruct_edit.setMaximumHeight(70)
        self.instruct_edit.setPlaceholderText("VD: a calm middle-aged male voice, deep pitch, warm tone")
        l2.addWidget(_field("Mô tả giọng")); l2.addWidget(self.instruct_edit)
        self.mode_stack.addWidget(p2)

        cl.addWidget(self.mode_stack)
        lay.addWidget(cf)

        # --- thẻ tùy chọn ---
        of_card, ol = _card("Tùy chọn")
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignLeft)

        self.lang_combo = QComboBox()
        for label, _code in config.LANGUAGES:
            self.lang_combo.addItem(label)
        form.addRow(_field("Ngôn ngữ"), self.lang_combo)

        self.speed, sw, self.speed_lbl = self._slider(50, 200, 95, lambda v: f"{v/100:.2f}x")
        form.addRow(_field("Tốc độ"), sw)

        self.pause, pw, self.pause_lbl = self._slider(0, 80, 30, lambda v: f"{v/100:.2f}s")
        form.addRow(_field("Ngắt nghỉ giữa câu"), pw)

        self.guidance, gw, self.guidance_lbl = self._slider(
            100, 400, 250, lambda v: f"{v/100:.1f}")
        self.guidance.setToolTip("Cao hơn = giống giọng mẫu hơn (nhưng quá cao dễ cứng/méo). Khuyên 2.5–3.0")
        form.addRow(_field("Độ giống giọng"), gw)

        self.breath, bw, self.breath_lbl = self._slider(0, 100, 45, lambda v: f"{v}%")
        self.breath.setToolTip("Làm nhỏ tiếng thở / tạp âm nền giữa các từ. 0% = tắt.")
        form.addRow(_field("Giảm tiếng thở"), bw)

        self.quality = QComboBox()
        for label, _ in self._quality_steps:
            self.quality.addItem(label)
        self.quality.setCurrentIndex(1)
        form.addRow(_field("Chất lượng"), self.quality)
        ol.addLayout(form)
        lay.addWidget(of_card)

        # --- thẻ văn bản ---
        tf, tl = _card("Văn bản cần đọc")
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Nhập nội dung muốn chuyển thành giọng nói...\nMẹo: viết có dấu chấm câu để ngắt nghỉ tự nhiên.")
        self.text_edit.setMinimumHeight(120)
        tl.addWidget(self.text_edit)
        lay.addWidget(tf)

        # --- nút tạo ---
        self.btn_generate = QPushButton("🔊  Tạo giọng nói")
        self.btn_generate.setObjectName("Primary")
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.clicked.connect(self._do_generate)
        lay.addWidget(self.btn_generate)

        # --- thanh tiến trình + đồng hồ thời gian ---
        prog_row = QHBoxLayout()
        prog_row.setSpacing(10)
        self.prog = QProgressBar()
        self.prog.setObjectName("Prog")
        self.prog.setRange(0, 100)
        self.prog.setValue(0)
        self.prog.setTextVisible(True)
        self.prog.setFormat("%p%")
        self.prog_time = QLabel("")
        self.prog_time.setObjectName("ProgTime")
        self.prog_time.setMinimumWidth(180)
        self.prog_time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        prog_row.addWidget(self.prog, 1)
        prog_row.addWidget(self.prog_time)
        self._prog_row_widget = QWidget()
        self._prog_row_widget.setLayout(prog_row)
        self._prog_row_widget.setVisible(False)
        lay.addWidget(self._prog_row_widget)

        # --- thẻ kết quả ---
        rf, rl = _card("Kết quả")
        self.out_label = QLabel("Chưa có kết quả.")
        self.out_label.setStyleSheet(f"color: {C_MUTED};")
        outrow = QHBoxLayout()
        self.btn_play = QPushButton("▶  Nghe"); self.btn_play.setObjectName("Ghost"); self.btn_play.clicked.connect(self._play)
        self.btn_stop = QPushButton("■  Dừng"); self.btn_stop.setObjectName("Ghost"); self.btn_stop.clicked.connect(self._stop)
        self.btn_saveas = QPushButton("💾  Lưu thành..."); self.btn_saveas.setObjectName("Ghost"); self.btn_saveas.clicked.connect(self._save_as)
        for b in (self.btn_play, self.btn_stop, self.btn_saveas):
            b.setEnabled(False); b.setCursor(Qt.PointingHandCursor)
        outrow.addWidget(self.out_label, 1)
        outrow.addWidget(self.btn_play); outrow.addWidget(self.btn_stop); outrow.addWidget(self.btn_saveas)
        rl.addLayout(outrow)
        lay.addWidget(rf)

        lay.addStretch(1)
        return scroll

    def _slider(self, lo, hi, val, fmt):
        """Tạo (slider, widget-bọc-có-nhãn-giá-trị, label). Cập nhật nhãn khi kéo."""
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
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(14)

        title = QLabel("Quản lý giọng")
        title.setObjectName("PageTitle")
        psub = QLabel("Tạo giọng mới từ audio mẫu hoặc xóa giọng đã lưu.")
        psub.setObjectName("PageSub")
        lay.addWidget(title)
        lay.addWidget(psub)

        # thẻ danh sách
        lf, ll = _card("Các giọng đã lưu")
        self.profile_list = QListWidget()
        self.profile_list.setMinimumHeight(150)
        ll.addWidget(self.profile_list)
        btnrow = QHBoxLayout()
        imp_btn = QPushButton("📥  Import giọng (.pt)..."); imp_btn.setObjectName("Ghost")
        imp_btn.setCursor(Qt.PointingHandCursor)
        imp_btn.clicked.connect(self._import_voices)
        del_btn = QPushButton("🗑  Xóa giọng đang chọn"); del_btn.setObjectName("Danger")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(self._delete_profile)
        btnrow.addWidget(imp_btn); btnrow.addWidget(del_btn)
        ll.addLayout(btnrow)
        lay.addWidget(lf)

        # thẻ tạo mới
        cf, cl = _card("➕ Tạo giọng mới từ audio mẫu")
        self.new_name = QLineEdit(); self.new_name.setPlaceholderText("Tên giọng, vd: Anh Nam")
        cl.addWidget(_field("Tên giọng")); cl.addWidget(self.new_name)

        self.new_ref_audio = QLineEdit(); self.new_ref_audio.setPlaceholderText("Chọn file audio 3–10 giây...")
        pb = QPushButton("Chọn file..."); pb.setObjectName("Ghost"); pb.clicked.connect(self._pick_ref_audio_new)
        row = QHBoxLayout(); row.addWidget(self.new_ref_audio, 1); row.addWidget(pb)
        cl.addWidget(_field("Audio mẫu")); cl.addLayout(row)

        self.new_ref_text = QTextEdit(); self.new_ref_text.setMaximumHeight(64)
        tb = QPushButton("✨ Tự nhận diện lời thoại"); tb.setObjectName("Ghost")
        tb.clicked.connect(lambda: self._transcribe(self.new_ref_audio, self.new_ref_text))
        cl.addWidget(_field("Lời thoại mẫu")); cl.addWidget(self.new_ref_text); cl.addWidget(tb)

        self.btn_create = QPushButton("➕  Tạo & lưu giọng"); self.btn_create.setObjectName("Primary")
        self.btn_create.setCursor(Qt.PointingHandCursor)
        self.btn_create.clicked.connect(self._create_profile)
        cl.addWidget(self.btn_create)
        lay.addWidget(cf)

        lay.addStretch(1)
        return page

    # ============================================================= helpers
    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.logbox.appendPlainText(f"[{ts}] {msg}")

    def _set_status(self, text, color=C_MUTED, device=None):
        self.status_dot.setText(f"●  {text}")
        self.status_dot.setStyleSheet(f"color: {color};")
        if device is not None:
            self.status_device.setText(device)

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
        self._prog_row_widget.setVisible(True)
        self.prog.setRange(0, 0)        # chế độ "đang chạy" (chưa biết %)
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
        """Bộ tham số sinh audio lấy từ các slider hiện tại."""
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
            self.profile_list.addItem("Chưa có giọng nào — hãy tạo ở dưới.")
        has = bool(items)
        if hasattr(self, "btn_preview"):
            self.btn_preview.setEnabled(has and self.engine.ready)

    def _preview_saved_voice(self):
        """Đọc nhanh một câu mẫu bằng giọng đã lưu đang chọn."""
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
        """Cho người dùng chọn 1 hay nhiều file .pt để import thành giọng."""
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
        """Lưu audio ra file, cập nhật thẻ Kết quả, bật các nút và tự phát ngay."""
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
