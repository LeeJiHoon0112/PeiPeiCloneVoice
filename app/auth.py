"""Xác thực mật khẩu mở app.

- Mật khẩu KHÔNG lưu dạng chữ thường: chỉ lưu mã băm (SHA-256 có "muối").
  → Người xem code trên GitHub cũng không đọc ra mật khẩu.
- Chủ máy có thể đổi mật khẩu riêng: ghi hash mới vào user_data/password.hash
  (file này KHÔNG đẩy lên GitHub). Nếu có file đó thì ưu tiên dùng nó.

Mật khẩu mặc định: PeiPei@2026   (đổi bằng hàm set_password hoặc nút trong app)
"""
import os
import hashlib

# "Muối" cố định để hai mật khẩu giống nhau không ra cùng hash với app khác.
_SALT = "ppcv_v1_8f3a"

# Hash của mật khẩu mặc định "PeiPei@2026".
_DEFAULT_HASH = "972f5ec2f864bb7c9b0a1c72c0da74831e3464893d65f42de6212f4f0f02e806"

# Nơi lưu hash tùy chỉnh (nếu chủ máy đổi mật khẩu). Không commit lên git.
from . import config  # noqa: E402

_OVERRIDE_FILE = os.path.join(config.USER_DATA_DIR, "password.hash")


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
    """Đổi mật khẩu (lưu hash mới vào user_data/password.hash)."""
    config.ensure_dirs()
    with open(_OVERRIDE_FILE, "w", encoding="utf-8") as f:
        f.write(hash_password(new_pw))
