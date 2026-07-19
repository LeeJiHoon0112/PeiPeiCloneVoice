"""Đường dẫn model + thư mục dữ liệu.

Thiết kế để CHIA SẺ QUA GITHUB: không phụ thuộc đường dẫn cứng của một máy cụ thể.
Thứ tự dò model:
  1. Biến môi trường người dùng tự đặt (nếu có)
  2. Thư mục ./models trong chính folder app (gói sẵn / đã tải về)
  3. Cache HuggingFace của máy (nếu từng tải)
  4. (chỉ máy tác giả) tool gốc — tiện dùng lại, máy khác sẽ bỏ qua
Không tìm thấy → trả về ID HuggingFace để TỰ TẢI VỀ lần đầu (vào ./models/hf-cache).
"""
import os
import json

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Nơi lưu giọng đã tạo và file audio xuất ra
USER_DATA_DIR = os.path.join(APP_DIR, "user_data")
VOICES_DIR = os.path.join(USER_DATA_DIR, "voices")
OUTPUTS_DIR = os.path.join(USER_DATA_DIR, "outputs")

# ----------------------------------------------------- Bản quyền (license)
# Hệ thống license hybrid (ký số Ed25519), dùng chung 1 server cho nhiều tool.
#   LICENSE_ENABLED = True  -> bản BÁN (.exe build Nuitka): bắt kích hoạt license.
#                   = False -> chạy TỰ DO khi DEV (bỏ qua license, dùng đăng nhập cũ).
# 🔴 ĐANG BẬT (True) — bản bán: bắt kích hoạt license. Đổi về False nếu muốn DEV chạy tự do.
LICENSE_ENABLED = True
LICENSE_SERVER_URL = "https://yt-license-server.onrender.com"
APP_VERSION = "1.0.2"   # để tự báo bản mới (so với manifest bên dưới)
# Manifest cập nhật: 1 file JSON TĨNH trên GitHub Releases, chứa NHIỀU tool; app tra
# theo key product của mình ("peipei-voice"). Bên web ra bản mới chỉ cần đổi số
# latest_version trong file này → app khách tự báo. download_url là link CỐ ĐỊNH
# (up đè cùng tên khi có bản mới).
UPDATE_MANIFEST_URL = (
    "https://github.com/LeeJiHoon0112/peipei-downloads/"
    "releases/download/v1.0/versions.json"
)
# Token license + mốc chống lùi đồng hồ lưu ở %APPDATA%\PeiPeiCloneVoice (NẰM NGOÀI
# thư mục cài → sống qua cập nhật/cài lại). TUYỆT ĐỐI không commit các file này.
DATA_DIR = os.path.join(os.environ.get("APPDATA") or USER_DATA_DIR, "PeiPeiCloneVoice")
LICENSE_FILE = os.path.join(DATA_DIR, "license.json")

# Thư mục model nằm trong app (gói sẵn hoặc nơi HuggingFace tải về) — portable theo GitHub
MODELS_DIR = os.path.join(APP_DIR, "models")
HF_CACHE_DIR = os.path.join(MODELS_DIR, "hf-cache")

# Đường dẫn tiện ích chỉ đúng trên máy tác giả (máy khác không có → tự bỏ qua)
_AUTHOR_TOOL_DIR = r"C:\Users\Admin\Desktop\Clone\Tool\user_data\omnivoice\cached_models\materialized"

# Nơi tool gốc lưu các giọng đã tạo (định dạng .pt + _metadata.json) — để IMPORT lại.
# Máy khác không có thư mục này → tự bỏ qua.
OLD_TOOL_VOICES_DIRS = [
    os.environ.get("OMNIVOICE_OLD_VOICES_DIR"),
    r"C:\Users\Admin\Desktop\Clone\Tool\user_data\omnivoice\created_voices",
]

# Các vị trí có thể chứa model OmniVoice đã tải sẵn (ưu tiên từ trên xuống)
_OMNI_CANDIDATES = [
    os.environ.get("OMNIVOICE_MODEL_DIR"),
    os.path.join(MODELS_DIR, "k2-fsa--OmniVoice"),
    os.path.join(MODELS_DIR, "OmniVoice"),
    os.path.join(_AUTHOR_TOOL_DIR, "k2-fsa--OmniVoice"),
]
_ASR_CANDIDATES = [
    os.environ.get("OMNIVOICE_ASR_DIR"),
    os.path.join(MODELS_DIR, "openai--whisper-large-v3-turbo"),
    os.path.join(MODELS_DIR, "whisper-large-v3-turbo"),
    os.path.join(_AUTHOR_TOOL_DIR, "openai--whisper-large-v3-turbo"),
]

# ID HuggingFace dùng làm phương án dự phòng (sẽ tự tải về nếu không có sẵn)
HF_MODEL_ID = "k2-fsa/OmniVoice"
HF_ASR_ID = "openai/whisper-large-v3-turbo"

# 12 ngôn ngữ chính được model hỗ trợ tốt nhất (có tiếng Việt)
LANGUAGES = [
    ("(Tự động)", None),
    ("Tiếng Việt", "vi"),
    ("English", "en"),
    ("中文 (Chinese)", "zh"),
    ("日本語 (Japanese)", "ja"),
    ("한국어 (Korean)", "ko"),
    ("Français", "fr"),
    ("Deutsch", "de"),
    ("Español", "es"),
    ("Italiano", "it"),
    ("Português", "pt"),
    ("Русский", "ru"),
    ("العربية (Arabic)", "ar"),
]


def _first_existing(candidates):
    for c in candidates:
        if c and os.path.isdir(c):
            return c
    return None


def hf_cache_has(repo_id: str) -> bool:
    """True nếu model `repo_id` ĐÃ nằm trong cache HuggingFace (tải trước đó).

    HF lưu cache theo cấu trúc: <cache>/models--<org>--<name>/snapshots/<hash>/...
    Hàm này dò ở ./models/hf-cache (và HF_HOME/HF_HUB_CACHE nếu người dùng tự đặt),
    để app KHÔNG báo nhầm "đang tải model" khi model thực ra đã có trong cache.
    """
    folder = "models--" + repo_id.replace("/", "--")
    bases = [HF_CACHE_DIR, os.path.join(HF_CACHE_DIR, "hub")]
    for env in ("HF_HUB_CACHE", "HF_HOME"):
        v = os.environ.get(env)
        if v:
            bases.append(v)
            bases.append(os.path.join(v, "hub"))
    for base in bases:
        snaps = os.path.join(base, folder, "snapshots")
        if os.path.isdir(snaps):
            for s in os.listdir(snaps):
                sp = os.path.join(snaps, s)
                if os.path.isdir(sp) and os.listdir(sp):  # snapshot không rỗng
                    return True
    return False


def resolve_model_dir():
    """Trả về (model_path, audio_tokenizer_path, is_local)."""
    local = _first_existing(_OMNI_CANDIDATES)
    if local:
        tok = os.path.join(local, "audio_tokenizer")
        return local, (tok if os.path.isdir(tok) else local), True
    return HF_MODEL_ID, HF_MODEL_ID, False


def resolve_asr_dir():
    local = _first_existing(_ASR_CANDIDATES)
    if local:
        return local, True
    return HF_ASR_ID, False


def ensure_dirs():
    os.makedirs(VOICES_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    os.makedirs(HF_CACHE_DIR, exist_ok=True)


# ------------------------------------------------------- cài đặt người dùng
# Lưu các tùy chọn theo máy (thư mục tự động lưu, bật/tắt...) vào user_data.
# File này KHÔNG đẩy lên GitHub.
SETTINGS_FILE = os.path.join(USER_DATA_DIR, "settings.json")


def load_settings() -> dict:
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                return json.load(f) or {}
    except Exception:
        pass
    return {}


def save_settings(d: dict):
    ensure_dirs()
    # Ghi an toàn: tạo chuỗi JSON TRƯỚC, chỉ mở file ghi khi chắc chắn không lỗi
    # (tránh để lại file rỗng nếu có sự cố). Lỗi I/O thật sẽ ném ra để thấy được.
    text = json.dumps(d, ensure_ascii=False, indent=2)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        f.write(text)


def get_setting(key, default=None):
    return load_settings().get(key, default)


def set_setting(key, value):
    d = load_settings()
    d[key] = value
    save_settings(d)


def delete_setting(key):
    """Xóa hẳn 1 khóa khỏi settings.json (dùng cho migration cài đặt cũ)."""
    d = load_settings()
    if key in d:
        d.pop(key)
        save_settings(d)


def setup_hf_cache_env():
    """Hướng HuggingFace tải model vào ./models/hf-cache (gọn trong app, dễ chia sẻ)."""
    os.makedirs(HF_CACHE_DIR, exist_ok=True)
    os.environ.setdefault("HF_HOME", HF_CACHE_DIR)
    os.environ.setdefault("HF_HUB_CACHE", HF_CACHE_DIR)
