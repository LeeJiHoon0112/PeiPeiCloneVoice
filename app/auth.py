"""Xác thực mật khẩu mở app.

- Mật khẩu KHÔNG lưu dạng chữ thường: chỉ lưu mã băm (SHA-256 có "muối").
  → Người xem code trên GitHub cũng không đọc ra mật khẩu.
- Chủ máy có thể đổi mật khẩu riêng: ghi hash mới vào user_data/password.hash
  (file này KHÔNG đẩy lên GitHub). Nếu có file đó thì ưu tiên dùng nó.

Mật khẩu được chủ app chia sẻ riêng cho người dùng (KHÔNG ghi ở đây).
"""
import os
import hashlib

# "Muối" cố định để hai mật khẩu giống nhau không ra cùng hash với app khác.
_SALT = "ppcv_v1_8f3a"

# Hash của mật khẩu mặc định "PeiPei@2026".
_DEFAULT_HASH = "28ce980a605ba78b7897b5259b84589dab5b786500fa136c1358bdf393478caf"

# Nơi lưu hash tùy chỉnh (nếu chủ máy đổi mật khẩu). Không commit lên git.
from . import config  # noqa: E402

_OVERRIDE_FILE = os.path.join(config.USER_DATA_DIR, "password.hash")
# Dấu "đã ghi nhớ máy này": lưu hash mật khẩu hiện hành. Nếu đổi mật khẩu,
# dấu cũ không còn khớp → máy đó phải nhập lại. Không commit lên git.
_REMEMBER_FILE = os.path.join(config.USER_DATA_DIR, "remember.dat")


def hash_password(pw: str) -> str:
    return hashlib.sha256((_SALT + (pw or "")).encode("utf-8")).hexdigest()


def _current_hash() -> str:
    """Hash đang có hiệu lực: ưu tiên file override, không thì dùng mặc định."""
    try:
        if os.path.exists(_OVERRIDE_FILE):
            with open(_OVERRIDE_FILE, encoding="utf-8") as f:
                h = f.read().strip()
                if len(h) == 64:
                    return h
    except Exception:
        pass
    return _DEFAULT_HASH


def verify(pw: str) -> bool:
    """Trả về True nếu mật khẩu đúng."""
    return hash_password(pw) == _current_hash()


def set_password(new_pw: str):
    """Đổi mật khẩu (lưu hash mới vào user_data/password.hash).

    Đổi mật khẩu cũng XÓA dấu ghi nhớ → mọi máy phải đăng nhập lại.
    """
    config.ensure_dirs()
    with open(_OVERRIDE_FILE, "w", encoding="utf-8") as f:
        f.write(hash_password(new_pw))
    forget_login()


# ------------------------------------------------------------- ghi nhớ máy này
def remember_login():
    """Đánh dấu máy này đã đăng nhập (lưu hash mật khẩu hiện hành)."""
    config.ensure_dirs()
    try:
        with open(_REMEMBER_FILE, "w", encoding="utf-8") as f:
            f.write(_current_hash())
    except Exception:
        pass


def is_remembered() -> bool:
    """True nếu máy này đã ghi nhớ VÀ dấu còn khớp mật khẩu hiện hành."""
    try:
        if os.path.exists(_REMEMBER_FILE):
            with open(_REMEMBER_FILE, encoding="utf-8") as f:
                return f.read().strip() == _current_hash()
    except Exception:
        pass
    return False


def forget_login():
    """Xóa dấu ghi nhớ (đăng xuất khỏi máy này)."""
    try:
        if os.path.exists(_REMEMBER_FILE):
            os.remove(_REMEMBER_FILE)
    except Exception:
        pass
