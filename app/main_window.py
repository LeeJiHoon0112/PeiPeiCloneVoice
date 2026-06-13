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
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QPlainTextEdit,
    QSlider, QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QStackedWidget, QFrame, QProgressBar, QCheckBox, QSpinBox,
    QDialog, QDialogButtonBox,
)

from . import config
from .engine import VoiceEngine, build_cues, cues_from_ai_groups, _render_srt
from . import scene_ai
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

/* ---- Ô chọn Model (nổi bật, chữ đen đậm dễ nhìn) ---- */
#ModelLabel {{ color: #000000; font-size: 13px; font-weight: 800; }}
#ModelBox {{
    background: #ffffff; border: 2px solid {C_ACCENT}; border-radius: 8px;
    /* chừa chỗ bên phải (36px) cho nút xổ xuống, tránh chữ bị đè */
    padding: 7px 40px 7px 12px; color: #000000; font-size: 14px; font-weight: 700;
}}
#ModelBox:hover {{ border: 2px solid {C_ACCENT2}; }}
#ModelBox:focus {{ border: 2px solid {C_ACCENT}; background: #ffffff; }}
#ModelBox QLineEdit {{
    background: transparent; border: none; padding: 0; margin: 0;
    color: #000000; font-size: 14px; font-weight: 700;
}}
/* Vùng xổ xuống = 1 NÚT TÍM RÕ (nền tím nhạt, viền trái). Mũi tên ▼ là 1 QLabel
   riêng (#ModelArrow) đè lên — luôn hiển thị, không bị render lỗi như vẽ CSS. */
#ModelBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: top right;
    width: 30px; border-left: 2px solid {C_ACCENT}; background: {C_ACCENT_SOFT};
    border-top-right-radius: 6px; border-bottom-right-radius: 6px;
}}
#ModelBox::drop-down:hover {{ background: {C_ACCENT2}; }}
#ModelArrow {{ color: {C_ACCENT}; font-size: 13px; font-weight: 900; background: transparent; }}
#ModelBox QAbstractItemView {{
    background: #ffffff; border: 2px solid {C_ACCENT};
    selection-background-color: {C_ACCENT}; selection-color: #ffffff;
    color: #000000; font-size: 14px; outline: none; padding: 4px;
}}
#ModelBox QAbstractItemView::item {{ min-height: 28px; padding: 4px 8px; color: #000000; }}

/* Nút 'Cập nhật model' — khung rõ ràng, màu nhấn để dễ nhận biết */
QPushButton#ModelBtn {{
    background: {C_ACCENT_SOFT}; border: 2px solid {C_ACCENT}; border-radius: 8px;
    padding: 7px 14px; color: {C_ACCENT}; font-weight: 700;
}}
QPushButton#ModelBtn:hover {{ background: {C_ACCENT}; color: #ffffff; }}
QPushButton#ModelBtn:disabled {{
    background: {C_CARD2}; border-color: {C_BORDER}; color: #b3b8c4;
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


def _safe_filename(name: str) -> str:
    """Bỏ ký tự không hợp lệ cho tên file Windows."""
    bad = '<>:"/\\|?*'
    cleaned = "".join("_" if c in bad else c for c in (name or "").strip())
    cleaned = cleaned.strip(" .")
    return cleaned or "output"


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

        # Hàng đợi: danh sách kịch bản chờ chuyển thành giọng. Mỗi item là dict
        # {name, text, voice, status}. _queue_running = đang chạy cả loạt.
        self._queue = []
        self._queue_running = False
        self._queue_stop = False

        # Tự động lưu audio: nhớ thư mục người dùng đã chọn (theo máy)
        self._name_hint = "output"
        self.autosave_dir = config.get_setting("autosave_dir", config.OUTPUTS_DIR)
        self.autosave_on = bool(config.get_setting("autosave_on", True))
        # Mỗi GIỌNG nhớ 1 thư mục lưu RIÊNG: {tên_giọng: đường_dẫn}. Chọn giọng nào
        # thì ô "Tự động lưu" hiện thư mục của giọng đó; đổi thư mục -> nhớ cho giọng đó.
        self.voice_dirs = dict(config.get_setting("voice_dirs", {}) or {})
        self.srt_on = bool(config.get_setting("srt_on", True))
        # Phụ đề dùng để CHIA CẢNH dựng video. User chọn 1 trong 2 mục đích, app
        # xuất 1 file <tên>.srt. Mỗi block ≥ SRT_MIN_DUR và ≤ trần riêng từng mode:
        #   mode 0 = Video ảnh tĩnh  → mỗi cảnh < 8s  (ảnh cần mô tả chi tiết)
        #   mode 1 = Clip từ ảnh     → mỗi cảnh < 10s (≈ 1 clip Veo3)
        self.srt_mode_idx = int(config.get_setting("srt_mode_idx", 0))
        self.SRT_MIN_DUR = 4.0
        self.SRT_MAX_IMG = 8.0   # trần cảnh ảnh tĩnh
        self.SRT_MAX_VID = 10.0  # trần cảnh clip Veo3
        self.srt_img_dur = float(config.get_setting("srt_img_dur", 7.0))
        self.srt_vid_dur = float(config.get_setting("srt_vid_dur", 8.0))

        # Chia cảnh bằng AI (tùy chọn): gom câu theo Ý NGHĨA qua API. Timestamp vẫn
        # lấy từ audio; tắt/lỗi/không key → tự fallback thuật toán offline.
        # API key lưu trong user_data/settings.json (đã gitignore — không lên GitHub).
        self.srt_ai_on = bool(config.get_setting("srt_ai_on", False))
        self.srt_ai_provider = str(config.get_setting("srt_ai_provider", "gemini"))
        # Lưu key RIÊNG cho từng provider {provider: key} → giữ cả 3 loại cùng lúc.
        self.srt_ai_keys = dict(config.get_setting("srt_ai_keys", {}) or {})
        # Tương thích bản cũ (chỉ có 1 key chung srt_ai_key) → đổ vào provider cũ.
        _old_key = str(config.get_setting("srt_ai_key", ""))
        if _old_key and not self.srt_ai_keys.get(self.srt_ai_provider):
            self.srt_ai_keys[self.srt_ai_provider] = _old_key
        # Model chọn riêng cho từng provider (dict {provider: model}); trống = mặc định.
        self.srt_ai_models = dict(config.get_setting("srt_ai_models", {}) or {})
        # Danh sách model lấy LIVE từ API, cache theo provider {provider: [model,...]}.
        # Nếu có → dùng thay danh sách cứng trong scene_ai.MODELS.
        self.srt_ai_model_lists = dict(config.get_setting("srt_ai_model_lists", {}) or {})

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
        self.pages.addWidget(self._build_queue_page())
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
        self.tab_queue = QPushButton("📋  Hàng đợi")
        for i, b in enumerate((self.tab_gen, self.tab_man, self.tab_queue)):
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
        self.tab_queue.setChecked(idx == 2)

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
        self.mode.currentIndexChanged.connect(self._on_voice_changed)
        ll.addWidget(self.mode)

        self.mode_stack = QStackedWidget()
        # 0: giọng đã lưu (+ nghe thử)
        p0 = QWidget(); l0 = QVBoxLayout(p0); l0.setContentsMargins(0, 0, 0, 0); l0.setSpacing(8)
        rowc = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._on_voice_changed)
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

        # tự động lưu vào thư mục người dùng chọn
        asrow = QHBoxLayout()
        asrow.setSpacing(8)
        self.autosave_cb = QCheckBox("Tự động lưu vào:")
        self.autosave_cb.setChecked(self.autosave_on)
        self.autosave_cb.toggled.connect(self._toggle_autosave)
        self.autosave_lbl = QLabel("")
        self.autosave_lbl.setObjectName("Hint")
        btn_pick_dir = QPushButton("Đổi thư mục...")
        btn_pick_dir.setObjectName("Ghost")
        btn_pick_dir.setCursor(Qt.PointingHandCursor)
        btn_pick_dir.clicked.connect(self._pick_autosave_dir)
        btn_open_dir = QPushButton("Mở")
        btn_open_dir.setObjectName("Ghost")
        btn_open_dir.setCursor(Qt.PointingHandCursor)
        btn_open_dir.setToolTip("Mở thư mục tự động lưu")
        btn_open_dir.clicked.connect(self._open_autosave_dir)
        asrow.addWidget(self.autosave_cb)
        asrow.addWidget(self.autosave_lbl, 1)
        asrow.addWidget(btn_pick_dir)
        asrow.addWidget(btn_open_dir)
        ll.addLayout(asrow)
        self._update_autosave_label()

        # Tùy chọn xuất kèm 1 file phụ đề .SRT để CHIA CẢNH dựng video.
        # User chọn 1 trong 2 mục đích; chỉ xuất 1 file <tên>.srt.
        # Mọi block luôn trong [4s, 10s].
        srtrow = QHBoxLayout()
        srtrow.setSpacing(8)
        self.srt_cb = QCheckBox("Xuất phụ đề .SRT (chia cảnh)")
        self.srt_cb.setChecked(self.srt_on)
        self.srt_cb.setToolTip(
            "Xuất 1 file <tên>.srt chia cảnh để dựng video.\n"
            "Mọi block đều dài 4–10 giây (không quá ngắn, không vượt giới hạn Veo3).")
        self.srt_cb.toggled.connect(self._toggle_srt)

        # Mục đích: 0 = Video ảnh tĩnh, 1 = Clip từ ảnh (tạo ảnh trước → tạo clip).
        self.srt_mode = QComboBox()
        self.srt_mode.addItem("🖼️ Video ảnh tĩnh")
        self.srt_mode.addItem("🎬 Clip từ ảnh")
        self.srt_mode.setToolTip(
            "Chọn loại video bạn muốn dựng:\n"
            "  • Video ảnh tĩnh — mỗi cảnh = 1 ẢNH (cần mô tả chi tiết → cảnh ngắn hơn).\n"
            "  • Clip từ ảnh — tạo ảnh trước rồi tạo CLIP ĐỘNG từ ảnh đó (mỗi cảnh ≈ 1 clip Veo3).")
        self.srt_mode.setCurrentIndex(int(self.srt_mode_idx))
        self.srt_mode.currentIndexChanged.connect(self._on_srt_mode)

        self.srt_dur_spin = QSpinBox()
        self.srt_dur_spin.setSuffix(" s")
        self.srt_dur_spin.setToolTip(
            "Độ dài đích mỗi cảnh. Ảnh tĩnh: 4–8s. Clip từ ảnh: 4–10s.")
        self.srt_dur_spin.valueChanged.connect(self._set_srt_dur)
        self._sync_srt_spin_range()  # đặt khoảng + giá trị theo mode đang chọn

        srtrow.addWidget(self.srt_cb)
        srtrow.addWidget(self.srt_mode)
        srtrow.addWidget(QLabel("·  Mỗi cảnh:"))
        srtrow.addWidget(self.srt_dur_spin)
        srtrow.addStretch(1)
        ll.addLayout(srtrow)

        # Hàng AI: chia cảnh theo Ý NGHĨA bằng API (tùy chọn). Tắt → dùng offline.
        airow = QHBoxLayout()
        airow.setSpacing(8)
        self.ai_cb = QCheckBox("Chia cảnh bằng AI")
        self.ai_cb.setChecked(self.srt_ai_on)
        self.ai_cb.setToolTip(
            "Dùng API để gom câu thành cảnh theo Ý NGHĨA (mạch lạc hơn chia máy móc).\n"
            "Mốc thời gian vẫn lấy từ audio; vẫn ép mỗi cảnh trong giới hạn giây.\n"
            "Tắt / lỗi mạng / chưa nhập key → tự dùng thuật toán offline.")
        self.ai_cb.toggled.connect(self._toggle_ai)

        self.ai_provider = QComboBox()
        for label, val in (("Gemini", "gemini"), ("OpenAI", "openai"), ("Claude", "claude")):
            self.ai_provider.addItem(label, val)
        idx = max(0, self.ai_provider.findData(self.srt_ai_provider))
        self.ai_provider.setCurrentIndex(idx)
        self.ai_provider.setToolTip("Chọn nhà cung cấp API tương ứng với key bạn có.")
        self.ai_provider.currentIndexChanged.connect(self._on_ai_provider)

        # Ô chọn model (editable — user gõ tên khác cũng được). Style nổi bật để dễ nhìn.
        self.ai_model = QComboBox()
        self.ai_model.setObjectName("ModelBox")
        self.ai_model.setEditable(True)
        # min vừa phải để hàng co giãn được (tránh đè nút bên cạnh khi panel hẹp);
        # stretch=1 ở addWidget sẽ cho nó giãn rộng khi còn chỗ.
        self.ai_model.setMinimumWidth(130)
        self.ai_model.setMinimumHeight(38)
        self.ai_model.setToolTip("Chọn hoặc gõ tên model. Mục đầu là mặc định (rẻ, nhanh).")
        # editTextChanged bắt cả khi user gõ tay lẫn chọn từ danh sách.
        self.ai_model.editTextChanged.connect(self._set_ai_model)

        # Mũi tên ▼ thật (ký tự Unicode) đè lên vùng tím bên phải ô Model — để user
        # nhận biết bấm vào chọn được. Dùng label thay vì vẽ CSS (CSS hay render lỗi).
        self.ai_model_arrow = QLabel("▼", self.ai_model)
        self.ai_model_arrow.setObjectName("ModelArrow")
        # Cho click xuyên qua mũi tên xuống combobox (vẫn mở được danh sách).
        self.ai_model_arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        # Tự canh mũi tên về sát mép phải khi ô đổi kích thước.
        self.ai_model.installEventFilter(self)

        # Nút lấy danh sách model MỚI NHẤT trực tiếp từ API của hãng.
        self.ai_refresh_btn = QPushButton("↻ Cập nhật model")
        self.ai_refresh_btn.setObjectName("ModelBtn")
        self.ai_refresh_btn.setCursor(Qt.PointingHandCursor)
        self.ai_refresh_btn.setToolTip(
            "Lấy model mới nhất từ API cho CẢ 3 loại đã lưu key.")
        self.ai_refresh_btn.clicked.connect(self._refresh_ai_models_live)

        self.ai_model.setToolTip("Bấm vào để xổ danh sách model và chọn (hoặc gõ tên).")
        airow.addWidget(self.ai_cb)
        airow.addWidget(self.ai_provider)
        model_lbl = QLabel("Chọn Model ▾")
        model_lbl.setObjectName("ModelLabel")
        airow.addWidget(model_lbl)
        airow.addWidget(self.ai_model, 1)
        airow.addSpacing(8)
        airow.addWidget(self.ai_refresh_btn)
        ll.addLayout(airow)

        # Hàng key + nút Lưu key + nút Test kết nối
        airow2 = QHBoxLayout()
        airow2.setSpacing(8)
        self.ai_key_edit = QLineEdit()
        self.ai_key_edit.setText(self._cur_ai_key())
        self.ai_key_edit.setEchoMode(QLineEdit.Password)
        self.ai_key_edit.setPlaceholderText("Dán API key của nhà cung cấp đang chọn...")
        self.ai_key_edit.setToolTip(
            "Key lưu RIÊNG cho từng nhà cung cấp (giữ cả 3 loại). "
            "Lưu cục bộ trong user_data (không đẩy lên GitHub).")
        self.ai_save_key_btn = QPushButton("💾 Lưu key")
        self.ai_save_key_btn.setObjectName("Ghost")
        self.ai_save_key_btn.setCursor(Qt.PointingHandCursor)
        self.ai_save_key_btn.setToolTip("Lưu API key cho nhà cung cấp đang chọn.")
        self.ai_save_key_btn.clicked.connect(self._save_ai_key)
        self.ai_test_btn = QPushButton("🔌 Test")
        self.ai_test_btn.setObjectName("Ghost")
        self.ai_test_btn.setCursor(Qt.PointingHandCursor)
        self.ai_test_btn.clicked.connect(self._test_ai)
        airow2.addWidget(QLabel("API key:"))
        airow2.addWidget(self.ai_key_edit, 1)
        airow2.addWidget(self.ai_save_key_btn)
        airow2.addWidget(self.ai_test_btn)
        ll.addLayout(airow2)

        # Nạp danh sách model cho provider đang chọn (đặt sau khi tạo ai_model).
        self._reload_ai_models(initial=True)
        self._update_srt_enabled()

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

        self.speed, sw, self.speed_lbl = self._slider(50, 200, 100, lambda v: f"{v/100:.2f}x")
        form.addRow(_field("Tốc độ"), sw)

        self.pause, pw, self.pause_lbl = self._slider(0, 80, 30, lambda v: f"{v/100:.2f}s")
        form.addRow(_field("Ngắt nghỉ giữa câu"), pw)

        self.guidance, gw, self.guidance_lbl = self._slider(100, 400, 250, lambda v: f"{v/100:.1f}")
        self.guidance.setToolTip("Cao hơn = giống giọng mẫu hơn (quá cao dễ cứng/méo). Khuyên 2.5–3.0")
        form.addRow(_field("Độ giống giọng"), gw)

        self.breath, bw, self.breath_lbl = self._slider(0, 100, 30, lambda v: f"{v}%")
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

    # ------------------------------------------------------- trang Hàng đợi
    def _build_queue_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        lay.addWidget(_group_title("📋 Hàng đợi chuyển kịch bản thành giọng nói"))
        hint = QLabel("Thêm nhiều kịch bản, chọn giọng cho từng cái, rồi bấm Chạy. "
                      "App đọc lần lượt, mỗi kịch bản ra 1 thư mục con chứa audio + .srt.")
        hint.setObjectName("Hint"); hint.setWordWrap(True)
        lay.addWidget(hint)

        # Hàng nút thêm / xóa
        btnrow = QHBoxLayout(); btnrow.setSpacing(8)
        b_txt = QPushButton("➕ Thêm từ file .txt...")
        b_txt.setObjectName("Ghost"); b_txt.setCursor(Qt.PointingHandCursor)
        b_txt.clicked.connect(self._queue_add_files)
        b_paste = QPushButton("➕ Dán kịch bản...")
        b_paste.setObjectName("Ghost"); b_paste.setCursor(Qt.PointingHandCursor)
        b_paste.clicked.connect(self._queue_add_paste)
        b_voice = QPushButton("🎙 Đổi giọng mục đang chọn")
        b_voice.setObjectName("Ghost"); b_voice.setCursor(Qt.PointingHandCursor)
        b_voice.clicked.connect(self._queue_set_voice)
        b_del = QPushButton("🗑 Xóa mục đang chọn")
        b_del.setObjectName("Danger"); b_del.setCursor(Qt.PointingHandCursor)
        b_del.clicked.connect(self._queue_remove)
        b_clear = QPushButton("Xóa hết")
        b_clear.setObjectName("Ghost"); b_clear.setCursor(Qt.PointingHandCursor)
        b_clear.clicked.connect(self._queue_clear)
        for b in (b_txt, b_paste, b_voice, b_del):
            btnrow.addWidget(b)
        btnrow.addStretch(1)
        btnrow.addWidget(b_clear)
        lay.addLayout(btnrow)

        # Danh sách hàng đợi
        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(240)
        lay.addWidget(self.queue_list, 1)

        # Hàng chạy / dừng
        runrow = QHBoxLayout(); runrow.setSpacing(8)
        self.btn_queue_run = QPushButton("▶  Chạy hàng đợi")
        self.btn_queue_run.setObjectName("Primary")
        self.btn_queue_run.setCursor(Qt.PointingHandCursor)
        self.btn_queue_run.clicked.connect(self._queue_run)
        self.btn_queue_stop = QPushButton("■  Dừng")
        self.btn_queue_stop.setObjectName("Ghost")
        self.btn_queue_stop.setCursor(Qt.PointingHandCursor)
        self.btn_queue_stop.setEnabled(False)
        self.btn_queue_stop.clicked.connect(self._queue_request_stop)
        runrow.addWidget(self.btn_queue_run, 1)
        runrow.addWidget(self.btn_queue_stop)
        lay.addLayout(runrow)
        return page

    # ------------------------------------------------- logic Hàng đợi
    _Q_STATUS = {"wait": "⏳ Chờ", "run": "▶ Đang chạy", "done": "✅ Xong", "err": "❌ Lỗi"}

    def _queue_refresh(self):
        """Vẽ lại danh sách hàng đợi từ self._queue."""
        cur = self.queue_list.currentRow()
        self.queue_list.clear()
        for it in self._queue:
            st = self._Q_STATUS.get(it["status"], it["status"])
            voice = it["voice"] or "(chưa chọn giọng)"
            d = it.get("out_dir") or ""
            dshort = ("📁 …" + d[-30:]) if len(d) > 32 else (f"📁 {d}" if d else "")
            self.queue_list.addItem(f"{st}  |  {it['name']}  —  🎤 {voice}   {dshort}")
        if 0 <= cur < self.queue_list.count():
            self.queue_list.setCurrentRow(cur)

    def _queue_default_voice(self):
        """Giọng mặc định cho item mới: giọng đang chọn ở tab Tạo giọng (nếu có)."""
        try:
            v = self.profile_combo.currentText().strip()
            return v or None
        except Exception:
            return None

    def _queue_add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Chọn các file kịch bản (.txt)", "", "Văn bản (*.txt);;Tất cả (*.*)")
        if not paths:
            return
        added = 0
        for p in paths:
            try:
                with open(p, encoding="utf-8") as f:
                    text = f.read().strip()
            except Exception:
                try:
                    with open(p, encoding="utf-8-sig", errors="replace") as f:
                        text = f.read().strip()
                except Exception as e:
                    self._log(f"⚠ Không đọc được {os.path.basename(p)}: {e}")
                    continue
            if not text:
                self._log(f"⚠ Bỏ qua file rỗng: {os.path.basename(p)}")
                continue
            name = os.path.splitext(os.path.basename(p))[0]
            voice = self._queue_default_voice()
            self._queue.append({"name": _safe_filename(name), "text": text,
                                "voice": voice, "out_dir": self._dir_for_voice(voice),
                                "status": "wait"})
            added += 1
        if added:
            self._queue_refresh()
            self._log(f"Đã thêm {added} kịch bản vào hàng đợi.")

    def _queue_add_paste(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Dán kịch bản vào hàng đợi")
        dl = QVBoxLayout(dlg)
        dl.addWidget(_field("Tên (dùng làm tên file/thư mục):"))
        name_edit = QLineEdit(); name_edit.setPlaceholderText("VD: Tap 01 - Mo dau")
        dl.addWidget(name_edit)
        dl.addWidget(_field("Chọn giọng:"))
        voice_combo = QComboBox()
        for it in self.profiles.list():
            voice_combo.addItem(it["name"])
        dl.addWidget(voice_combo)
        dl.addWidget(_field("Nội dung kịch bản:"))
        text_edit = QTextEdit(); text_edit.setMinimumSize(480, 220)
        dl.addWidget(text_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        dl.addWidget(bb)
        if dlg.exec_() != QDialog.Accepted:
            return
        text = text_edit.toPlainText().strip()
        name = name_edit.text().strip() or f"kichban_{len(self._queue) + 1}"
        if not text:
            return self._error("Chưa nhập nội dung kịch bản.")
        voice = voice_combo.currentText().strip() or None
        self._queue.append({"name": _safe_filename(name), "text": text,
                            "voice": voice, "out_dir": self._dir_for_voice(voice),
                            "status": "wait"})
        self._queue_refresh()
        self._log(f"Đã thêm kịch bản '{name}' vào hàng đợi.")

    def _queue_set_voice(self):
        row = self.queue_list.currentRow()
        if not (0 <= row < len(self._queue)):
            return self._error("Hãy chọn 1 mục trong hàng đợi.")
        voices = [it["name"] for it in self.profiles.list()]
        if not voices:
            return self._error("Chưa có giọng nào. Tạo giọng ở tab Quản lý giọng trước.")
        cur = self._queue[row]["voice"]
        idx = voices.index(cur) if cur in voices else 0
        dlg = QDialog(self); dlg.setWindowTitle("Chọn giọng cho mục này")
        dl = QVBoxLayout(dlg)
        dl.addWidget(_field(f"Kịch bản: {self._queue[row]['name']}"))
        combo = QComboBox(); combo.addItems(voices); combo.setCurrentIndex(idx)
        dl.addWidget(combo)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        dl.addWidget(bb)
        if dlg.exec_() == QDialog.Accepted:
            nv = combo.currentText().strip()
            self._queue[row]["voice"] = nv
            # Đổi giọng -> cập nhật thư mục lưu theo thư mục đã nhớ của giọng mới.
            self._queue[row]["out_dir"] = self._dir_for_voice(nv)
            self._queue_refresh()

    def _queue_remove(self):
        row = self.queue_list.currentRow()
        if 0 <= row < len(self._queue):
            if self._queue_running and self._queue[row]["status"] == "run":
                return self._error("Không thể xóa mục đang chạy.")
            del self._queue[row]
            self._queue_refresh()

    def _queue_clear(self):
        if self._queue_running:
            return self._error("Đang chạy hàng đợi — hãy Dừng trước khi xóa hết.")
        if self._queue and QMessageBox.question(
                self, "Xóa hết", "Xóa toàn bộ hàng đợi?") == QMessageBox.Yes:
            self._queue.clear()
            self._queue_refresh()

    def _queue_request_stop(self):
        self._queue_stop = True
        self._log("Đã yêu cầu dừng — sẽ dừng sau khi xong kịch bản đang chạy.")
        self.btn_queue_stop.setEnabled(False)

    def _queue_run(self):
        if not self.engine.ready:
            return self._error("Model chưa nạp xong.")
        if self._queue_running:
            return
        if self._task and self._task.isRunning():
            return self._error("Đang có tác vụ khác chạy. Vui lòng đợi.")
        pending = [it for it in self._queue if it["status"] in ("wait", "err")]
        if not pending:
            return self._error("Hàng đợi trống (hoặc tất cả đã xong). Hãy thêm kịch bản.")
        # Mọi item phải có giọng hợp lệ.
        voices = {it["name"] for it in self.profiles.list()}
        missing = [it["name"] for it in pending if not it["voice"] or it["voice"] not in voices]
        if missing:
            return self._error("Các mục sau chưa chọn giọng hợp lệ: " + ", ".join(missing[:5]))

        # Chụp cấu hình ở main thread (an toàn cho luồng nền).
        common = self._gen_params()
        srt_cfg = self._srt_snapshot()
        targets = list(pending)  # tham chiếu chính các dict trong self._queue
        # Mỗi item lưu vào THƯ MỤC RIÊNG của giọng nó (đã gắn lúc thêm vào hàng đợi).
        for it in targets:
            if not it.get("out_dir"):
                it["out_dir"] = self._dir_for_voice(it.get("voice"))

        self._queue_running = True
        self._queue_stop = False
        self.btn_queue_run.setEnabled(False)
        self.btn_queue_stop.setEnabled(True)
        self._busy(True, f"Đang chạy hàng đợi (0/{len(targets)})...", C_WARN)
        self._start_progress()

        def job(log=None, progress=None):
            _log = log or (lambda m: None)
            done_n, total = 0, len(targets)
            results = []
            for it in targets:
                if self._queue_stop:
                    _log("Đã dừng hàng đợi theo yêu cầu.")
                    break
                it["status"] = "run"
                # cập nhật UI list từ luồng nền là không an toàn tuyệt đối, nhưng
                # chỉ đọc/sửa text -> dùng log để báo; refresh ở done.
                _log(f"[{done_n + 1}/{total}] Đang đọc: {it['name']} (giọng {it['voice']})")
                try:
                    prompt = self.profiles.load_prompt(it["voice"])
                    sr, audio, segs = self.engine.generate(
                        it["text"], voice_clone_prompt=prompt, progress=progress,
                        with_segments=True, **common)
                    srt_text, _ = self._make_srt_text(segs, srt_cfg, _log)
                    # Mỗi kịch bản 1 thư mục con, NẰM TRONG thư mục riêng của giọng.
                    item_base = it.get("out_dir") or config.OUTPUTS_DIR
                    sub = os.path.join(item_base, _safe_filename(it["name"]))
                    os.makedirs(sub, exist_ok=True)
                    wav_path = os.path.join(sub, _safe_filename(it["name"]) + ".wav")
                    sf.write(wav_path, audio, sr)
                    if srt_text:
                        with open(os.path.join(sub, _safe_filename(it["name"]) + ".srt"),
                                  "w", encoding="utf-8", newline="\n") as f:
                            f.write(srt_text)
                    it["status"] = "done"
                    results.append((it["name"], True, wav_path))
                    _log(f"   ✅ Xong: {wav_path}")
                except Exception as e:
                    it["status"] = "err"
                    results.append((it["name"], False, str(e)))
                    _log(f"   ❌ Lỗi ở '{it['name']}': {e}")
                done_n += 1
                if progress:
                    progress(done_n, total)
            return results

        def done(results):
            self._queue_running = False
            self._queue_stop = False
            self.btn_queue_run.setEnabled(True)
            self.btn_queue_stop.setEnabled(False)
            self._queue_refresh()
            ok = sum(1 for _, s, _ in results if s)
            fail = len(results) - ok
            self._log(f"Hàng đợi xong: {ok} thành công, {fail} lỗi.")
            QMessageBox.information(
                self, "Hàng đợi hoàn tất",
                f"Đã xử lý {len(results)} kịch bản.\n"
                f"✅ Thành công: {ok}\n❌ Lỗi: {fail}\n\n"
                f"Mỗi kịch bản lưu vào thư mục riêng của giọng nó.")

        self._run(job, done, f"Đang chạy hàng đợi (0/{len(targets)})...",
                  pass_log=True, pass_progress=True)

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
        # Nút "Chạy hàng đợi" cũng khóa khi bận (trừ khi chính hàng đợi đang chạy
        # — lúc đó nút Dừng mới là cái điều khiển).
        if hasattr(self, "btn_queue_run"):
            self.btn_queue_run.setEnabled(not on and ready and not self._queue_running)

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

    # --------------------------------------------------- tự động lưu thư mục
    def _update_autosave_label(self):
        v = self._cur_voice_name() if hasattr(self, "mode") else None
        p = self._dir_for_voice(v) if v else (self.autosave_dir or config.OUTPUTS_DIR)
        self.autosave_lbl.setToolTip(
            (f"Thư mục lưu cho giọng '{v}':\n" if v else "") + p)
        disp = p if len(p) <= 38 else "…" + p[-37:]
        if v:
            disp = f"[{v}] " + disp
        self.autosave_lbl.setText(disp)
        self.autosave_lbl.setEnabled(self.autosave_on)

    def _toggle_autosave(self, on):
        self.autosave_on = bool(on)
        config.set_setting("autosave_on", self.autosave_on)
        self._update_autosave_label()

    # --- Thư mục lưu RIÊNG theo từng giọng ---
    def _cur_voice_name(self):
        """Tên giọng đang chọn ở 'Nguồn giọng' (chỉ khi dùng giọng đã lưu)."""
        try:
            if self.mode.currentIndex() == 0:
                return self.profile_combo.currentText().strip() or None
        except Exception:
            pass
        return None

    def _dir_for_voice(self, voice):
        """Thư mục lưu đã nhớ cho 1 giọng; chưa có thì dùng thư mục chung gần nhất."""
        if voice and self.voice_dirs.get(voice):
            return self.voice_dirs[voice]
        return self.autosave_dir or config.OUTPUTS_DIR

    def _on_voice_changed(self, *_):
        """Đổi giọng đang chọn -> ô 'Tự động lưu vào' hiện thư mục của giọng đó."""
        v = self._cur_voice_name()
        if v:
            self.autosave_dir = self._dir_for_voice(v)
        self._update_autosave_label()

    def _toggle_srt(self, on):
        self.srt_on = bool(on)
        config.set_setting("srt_on", self.srt_on)
        self._update_srt_enabled()

    def _update_srt_enabled(self):
        """Bật/tắt combo mục đích + ô giây + hàng AI theo trạng thái checkbox SRT."""
        on = self.srt_on
        if hasattr(self, "srt_mode"):
            self.srt_mode.setEnabled(on)
            self.srt_dur_spin.setEnabled(on)
        if hasattr(self, "ai_cb"):
            self.ai_cb.setEnabled(on)
            ai = on and self.srt_ai_on
            self.ai_provider.setEnabled(ai)
            self.ai_model.setEnabled(ai)
            self.ai_refresh_btn.setEnabled(ai)
            self.ai_key_edit.setEnabled(ai)
            self.ai_save_key_btn.setEnabled(ai)
            self.ai_test_btn.setEnabled(ai)

    def _toggle_ai(self, on):
        self.srt_ai_on = bool(on)
        config.set_setting("srt_ai_on", self.srt_ai_on)
        self._update_srt_enabled()

    def _cur_ai_key(self) -> str:
        """Key của nhà cung cấp đang chọn (lưu riêng từng loại)."""
        return (self.srt_ai_keys.get(self.srt_ai_provider) or "").strip()

    def _on_ai_provider(self, _=None):
        """Đổi nhà cung cấp → nạp lại model + hiện key đã lưu của hãng đó."""
        self.srt_ai_provider = self.ai_provider.currentData() or "gemini"
        config.set_setting("srt_ai_provider", self.srt_ai_provider)
        self._reload_ai_models()
        # Hiện key đã lưu của provider mới vào ô nhập.
        if hasattr(self, "ai_key_edit"):
            self.ai_key_edit.blockSignals(True)
            self.ai_key_edit.setText(self._cur_ai_key())
            self.ai_key_edit.blockSignals(False)

    def _reload_ai_models(self, initial=False):
        """Nạp danh sách model cho provider đang chọn; chọn model đã nhớ (nếu có).
        Ưu tiên danh sách LIVE đã cache (lấy từ API), nếu chưa có thì dùng danh
        sách cứng trong scene_ai.MODELS."""
        prov = self.srt_ai_provider
        saved = (self.srt_ai_models.get(prov) or "").strip()
        items = self.srt_ai_model_lists.get(prov) or scene_ai.MODELS.get(prov, [])
        self.ai_model.blockSignals(True)
        self.ai_model.clear()
        self.ai_model.addItems(items)
        # Hiển thị model đã nhớ, nếu chưa có thì để mặc định (mục đầu).
        self.ai_model.setCurrentText(saved or scene_ai.default_model(prov))
        self.ai_model.blockSignals(False)
        if not initial:
            # Lưu lại lựa chọn hiện hành cho provider mới (đồng bộ settings).
            self._set_ai_model()

    def _refresh_ai_models_live(self):
        """Bấm ↻: quét TẤT CẢ nhà cung cấp đã lưu key, lấy TOÀN BỘ model dùng được
        (đã lọc sạch) mỗi loại (luồng nền), cache lại để user tự chọn. Loại nào
        chưa có key thì bỏ qua."""
        # Lưu key đang gõ (nếu có) trước khi quét.
        self._save_ai_key(silent=True)
        keys = {p: (self.srt_ai_keys.get(p) or "").strip() for p in scene_ai.PROVIDERS}
        have = {p: k for p, k in keys.items() if k}
        if not have:
            return self._error("Chưa lưu API key nào. Hãy nhập key và bấm 💾 Lưu key.")

        self.ai_refresh_btn.setEnabled(False)
        self.ai_refresh_btn.setText("⏳ Đang lấy...")

        # Job tự bắt lỗi từng provider → trả dict {provider: (ok, data)}.
        def job(log=None):
            out = {}
            for p, k in have.items():
                try:
                    models = scene_ai.list_models(p, k)
                    out[p] = (True, models)
                    log(f"{p}: lấy được {len(models)} model.")
                except Exception as e:
                    out[p] = (False, scene_ai._friendly_error(e, p, ""))
                    log(f"{p}: lỗi — {out[p][1]}")
            return out

        def done(result):
            self.ai_refresh_btn.setEnabled(True)
            self.ai_refresh_btn.setText("↻ Cập nhật model")
            lines, any_ok = [], False
            for p in scene_ai.PROVIDERS:
                if p not in result:
                    continue
                ok, data = result[p]
                if ok and data:
                    self.srt_ai_model_lists[p] = data
                    any_ok = True
                    # Hiện vài model đầu cho gọn, kèm tổng số.
                    head = ", ".join(data[:3])
                    more = f" … (+{len(data) - 3})" if len(data) > 3 else ""
                    lines.append(f"✅ {p}: {len(data)} model — {head}{more}")
                elif ok:
                    lines.append(f"⚠ {p}: API không trả model nào.")
                else:
                    lines.append(f"❌ {p}: {data}")
            if any_ok:
                config.set_setting("srt_ai_model_lists", self.srt_ai_model_lists)
                # Nạp lại combo cho provider đang chọn (giữ model đang chọn nếu còn).
                cur = self._cur_ai_model()
                self._reload_ai_models(initial=True)
                if cur:
                    self.ai_model.setCurrentText(cur)
            for ln in lines:
                self._log(ln)
            QMessageBox.information(self, "Cập nhật model",
                                   "\n".join(lines) or "Không có gì để cập nhật.")

        self._run(job, done, f"Đang lấy model cho {len(have)} nhà cung cấp...",
                  pass_log=True)

    def eventFilter(self, obj, event):
        """Canh mũi tên ▼ về sát mép phải ô Model mỗi khi nó đổi kích thước/hiện."""
        if obj is getattr(self, "ai_model", None) and event.type() in (
                QEvent.Resize, QEvent.Show, QEvent.Move):
            self._place_model_arrow()
        return super().eventFilter(obj, event)

    def _place_model_arrow(self):
        """Đặt label ▼ vào giữa vùng tím (30px) bên phải ô Model."""
        a = getattr(self, "ai_model_arrow", None)
        if not a:
            return
        h = self.ai_model.height()
        a.setFixedSize(30, h - 6)
        a.setAlignment(Qt.AlignCenter)
        a.move(self.ai_model.width() - 30, 3)
        a.raise_()

    def _cur_ai_model(self) -> str:
        """Tên model đang chọn (rỗng → để scene_ai dùng mặc định)."""
        return self.ai_model.currentText().strip()

    def _set_ai_model(self, _=None):
        self.srt_ai_models[self.srt_ai_provider] = self._cur_ai_model()
        config.set_setting("srt_ai_models", self.srt_ai_models)

    def _set_ai_provider(self, _=None):
        # Giữ tương thích (không còn nối trực tiếp; _on_ai_provider thay thế).
        self._on_ai_provider()

    def _save_ai_key(self, silent=False):
        """Lưu API key cho nhà cung cấp ĐANG CHỌN (mỗi loại 1 key riêng)."""
        key = self.ai_key_edit.text().strip()
        self.srt_ai_keys[self.srt_ai_provider] = key
        config.set_setting("srt_ai_keys", self.srt_ai_keys)
        if not silent:
            n = sum(1 for v in self.srt_ai_keys.values() if v)
            self._log(f"💾 Đã lưu API key cho {self.srt_ai_provider} (tổng {n} key đã lưu).")

    def _test_ai(self):
        """Bấm 'Test': gọi API tí hon ở luồng nền, báo OK/lỗi."""
        provider = self.srt_ai_provider
        key = self.ai_key_edit.text().strip()
        model = self._cur_ai_model()
        if not key:
            return self._error("Hãy nhập API key trước khi test.")
        # Lưu key/model hiện tại để lần sau dùng luôn.
        self._save_ai_key(silent=True)
        self._set_ai_model()
        self.ai_test_btn.setEnabled(False)
        self.ai_test_btn.setText("⏳")

        def job(log=None):
            return scene_ai.test_connection(provider, key, model)

        def done(result):
            ok, msg = result
            self.ai_test_btn.setEnabled(True)
            self.ai_test_btn.setText("🔌 Test")
            self._log(("✅ " if ok else "❌ ") + msg)
            if ok:
                QMessageBox.information(self, "Test kết nối", msg)
            else:
                QMessageBox.warning(self, "Test kết nối thất bại", msg)

        self._run(job, done, f"Đang test API {provider}...")

    def _cur_srt_dur(self) -> float:
        """Độ dài đích của mode đang chọn (0=ảnh tĩnh, 1=clip từ ảnh)."""
        return self.srt_img_dur if self.srt_mode_idx == 0 else self.srt_vid_dur

    def _cur_srt_max(self) -> float:
        """Trần độ dài 1 cảnh theo mode (ảnh <8s, clip <10s)."""
        return self.SRT_MAX_IMG if self.srt_mode_idx == 0 else self.SRT_MAX_VID

    def _sync_srt_spin_range(self):
        """Đặt lại khoảng cho ô giây theo trần của mode đang chọn, kẹp giá trị."""
        hi = int(self._cur_srt_max())
        self.srt_dur_spin.blockSignals(True)
        self.srt_dur_spin.setRange(int(self.SRT_MIN_DUR), hi)
        self.srt_dur_spin.setValue(min(int(self._cur_srt_dur()), hi))
        self.srt_dur_spin.blockSignals(False)

    def _on_srt_mode(self, idx):
        """Đổi mục đích SRT → cập nhật khoảng + giá trị ô giây của mode đó."""
        self.srt_mode_idx = int(idx)
        config.set_setting("srt_mode_idx", self.srt_mode_idx)
        self._sync_srt_spin_range()

    def _set_srt_dur(self, _=None):
        """Lưu độ dài đích cho ĐÚNG mode đang chọn (đã kẹp trong [min, trần])."""
        val = float(self.srt_dur_spin.value())
        if self.srt_mode_idx == 0:
            self.srt_img_dur = val
            config.set_setting("srt_img_dur", val)
        else:
            self.srt_vid_dur = val
            config.set_setting("srt_vid_dur", val)

    def _pick_autosave_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục tự động lưu audio", self.autosave_dir or "")
        if not d:
            return
        self.autosave_dir = d
        config.set_setting("autosave_dir", d)   # thư mục chung gần nhất (dự phòng)
        # Nếu đang chọn 1 giọng -> NHỚ thư mục này RIÊNG cho giọng đó.
        v = self._cur_voice_name()
        if v:
            self.voice_dirs[v] = d
            config.set_setting("voice_dirs", self.voice_dirs)
            self._log(f"Thư mục lưu cho giọng '{v}': {d}")
        else:
            self._log(f"Thư mục tự động lưu: {d}")
        self._update_autosave_label()

    def _open_autosave_dir(self):
        d = self.autosave_dir or config.OUTPUTS_DIR
        try:
            os.makedirs(d, exist_ok=True)
            os.startfile(d)  # Windows
        except Exception as e:
            self._error(f"Không mở được thư mục: {e}")

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
    def _srt_snapshot(self) -> dict:
        """Chụp lại cấu hình SRT ở MAIN THREAD để job nền dùng an toàn (không
        đụng widget từ luồng khác)."""
        return {
            "on": self.srt_on,
            "kind": "image" if self.srt_mode_idx == 0 else "video",
            "target": self._cur_srt_dur(),
            "min": self.SRT_MIN_DUR,
            "max": self._cur_srt_max(),
            "ai_on": self.srt_ai_on,
            "provider": self.srt_ai_provider,
            "key": self._cur_ai_key(),
            "model": self._cur_ai_model(),
        }

    def _make_srt_text(self, segments, cfg, log=lambda m: None):
        """Dựng nội dung .srt (chạy trong LUỒNG NỀN). Nếu bật AI + có key → thử
        gom cảnh theo ý nghĩa; lỗi/không hợp lệ → fallback thuật toán offline.
        Trả về (srt_text | None, used_ai: bool)."""
        if not cfg["on"] or not segments:
            return None, False
        # Mặc định: offline (luôn có, làm phương án dự phòng).
        offline_cues = build_cues(segments, cfg["target"], cfg["min"], cfg["max"])
        if not (cfg["ai_on"] and cfg["key"].strip()):
            return _render_srt(offline_cues), False
        try:
            log(f"Đang gọi AI ({cfg['provider']}) để chia cảnh theo ý nghĩa...")
            groups = scene_ai.suggest_groups(
                segments, cfg["provider"], cfg["key"],
                cfg["target"], cfg["min"], cfg["max"], kind=cfg["kind"],
                model=cfg.get("model") or None)
            cues = cues_from_ai_groups(segments, groups, cfg["target"],
                                       cfg["min"], cfg["max"])
            if not cues:
                raise ValueError("AI trả về cách nhóm không hợp lệ.")
            log(f"AI chia thành {len(cues)} cảnh.")
            return _render_srt(cues), True
        except Exception as e:
            log(f"⚠ AI chia cảnh lỗi ({e}). Dùng cách chia offline.")
            return _render_srt(offline_cues), False

    def _do_generate(self):
        if not self.engine.ready:
            return self._error("Model chưa nạp xong.")
        text = self.text_edit.toPlainText().strip()
        if not text:
            return self._error("Hãy nhập văn bản cần đọc.")
        common = self._gen_params()
        mode = self.mode.currentIndex()
        srt_cfg = self._srt_snapshot()   # chụp cấu hình SRT ngay ở main thread

        if mode == 0:
            name = self.profile_combo.currentText().strip()
            if not name:
                return self._error("Chưa có giọng đã lưu. Hãy tạo ở tab Quản lý giọng.")
            self._name_hint = _safe_filename(name)

            def job(log=None, progress=None):
                prompt = self.profiles.load_prompt(name)
                sr, audio, segs = self.engine.generate(
                    text, voice_clone_prompt=prompt, progress=progress,
                    with_segments=True, **common)
                srt_text, _ = self._make_srt_text(segs, srt_cfg, log or (lambda m: None))
                return sr, audio, srt_text
        elif mode == 1:
            ra = self.ref_audio_edit.text().strip()
            rt = self.ref_text_edit.toPlainText().strip()
            if not ra or not os.path.exists(ra):
                return self._error("Hãy chọn file audio mẫu hợp lệ.")
            self._name_hint = "clone"

            def job(log=None, progress=None):
                sr, audio, segs = self.engine.generate(
                    text, ref_audio=ra, ref_text=rt or None, progress=progress,
                    with_segments=True, **common)
                srt_text, _ = self._make_srt_text(segs, srt_cfg, log or (lambda m: None))
                return sr, audio, srt_text
        else:
            ins = self.instruct_edit.toPlainText().strip()
            self._name_hint = "design"

            def job(log=None, progress=None):
                sr, audio, segs = self.engine.generate(
                    text, instruct=ins or None, progress=progress,
                    with_segments=True, **common)
                srt_text, _ = self._make_srt_text(segs, srt_cfg, log or (lambda m: None))
                return sr, audio, srt_text

        self._run(job, self._on_generated, "Đang tạo giọng nói...", pass_progress=True)

    def _on_generated(self, result):
        # result = (sr, audio, srt_text) — srt_text có thể None nếu tắt SRT.
        sr, audio, srt_text = result
        # Lưu thẳng vào thư mục người dùng đã chọn (nếu bật tự động lưu).
        target = self.autosave_dir if self.autosave_on else None
        self._present_audio(sr, audio, prefix=self._name_hint or "output",
                            target_dir=target, srt_text=srt_text)

    def _present_audio(self, sr, audio, prefix="output", target_dir=None,
                       srt_text=None):
        """Lưu audio (vào target_dir nếu có, không thì outputs), cập nhật UI, tự phát.

        srt_text: nội dung .srt ĐÃ dựng sẵn (ở luồng nền) — nếu có thì ghi kèm
        file .srt cùng tên với .wav. Nếu lưu vào target_dir thất bại (thư mục bị
        xóa, không quyền...) thì tự lưu tạm vào user_data/outputs để không mất kết quả.
        """
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{_safe_filename(prefix)}_{ts}"
        out_dir = target_dir or config.OUTPUTS_DIR
        autosaved = bool(target_dir)
        out = os.path.join(out_dir, base_name + ".wav")
        try:
            os.makedirs(out_dir, exist_ok=True)
            sf.write(out, audio, sr)
        except Exception as e:
            # Dự phòng: lưu vào outputs mặc định
            out_dir = config.OUTPUTS_DIR
            out = os.path.join(out_dir, base_name + ".wav")
            os.makedirs(out_dir, exist_ok=True)
            sf.write(out, audio, sr)
            autosaved = False
            self._log(f"⚠ Không lưu được vào thư mục đã chọn ({e}). Đã lưu tạm vào outputs.")

        # Ghi kèm 1 file phụ đề chia cảnh <tên>.srt (nội dung đã dựng sẵn ở luồng nền).
        srt_path = None
        if srt_text:
            try:
                srt_path = os.path.join(out_dir, base_name + ".srt")
                # UTF-8 KHÔNG BOM, xuống dòng LF (\n) đúng spec.
                with open(srt_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(srt_text)
            except Exception as e:
                srt_path = None
                self._log(f"⚠ Không ghi được file SRT: {e}")

        self._last_output = out
        dur = len(audio) / sr
        tag = "💾 Đã tự động lưu" if autosaved else "✅"
        extra = "  + .srt" if srt_path else ""
        self.out_label.setText(f"{tag}: {os.path.basename(out)}{extra}   ·   {dur:.1f}s")
        self.out_label.setStyleSheet(f"color: {C_TEXT};")
        self._log(("Đã tự động lưu: " if autosaved else "Đã lưu: ") + out)
        if srt_path:
            self._log("Đã xuất phụ đề: " + srt_path)
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
