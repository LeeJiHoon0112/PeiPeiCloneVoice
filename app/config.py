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

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Nơi lưu giọng đã tạo và file audio xuất ra
USER_DATA_DIR = os.path.join(APP_DIR, "user_data")
VOICES_DIR = os.path.join(USER_DATA_DIR, "voices")
OUTPUTS_DIR = os.path.join(USER_DATA_DIR, "outputs")

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


def setup_hf_cache_env():
    """Hướng HuggingFace tải model vào ./models/hf-cache (gọn trong app, dễ chia sẻ)."""
    os.makedirs(HF_CACHE_DIR, exist_ok=True)
    os.environ.setdefault("HF_HOME", HF_CACHE_DIR)
    os.environ.setdefault("HF_HUB_CACHE", HF_CACHE_DIR)
