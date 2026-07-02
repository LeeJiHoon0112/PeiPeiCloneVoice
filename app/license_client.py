# -*- coding: utf-8 -*-
"""Client license (hybrid): kích hoạt online, xác minh chữ ký Ed25519 offline.

Public key nhúng cứng -> không giả được server. UI nằm ở license_dialog.py.
Lưu ý: license verify client-side về bản chất có thể bị patch nhị phân;
lớp bảo vệ cuối cùng là obfuscation (Nuitka) khi đóng gói + server bắt buộc online.

DÙNG NGUYÊN THÂN file gốc dùng chung nhiều tool — chỉ đổi PRODUCT_ID và cách
import config cho hợp cấu trúc package của tool này (app/config.py).
"""
import base64
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from . import config

# === PUBLIC KEY (lấy từ: python admin.py keygen) ===
PUBLIC_KEY_B64 = "akMkNnMw7EG0hGSK7HBiY/M7ERcKYfFLIAL7hD1Dvy0="

# Mã sản phẩm của TOOL NÀY. Dùng chung 1 server cho nhiều tool -> mỗi tool đặt 1 mã riêng.
# Khi tạo key cho tool này, ở admin chọn product = "peipei-voice".
PRODUCT_ID = "peipei-voice"

# Dung sai chống lùi đồng hồ (cho phép chỉnh giờ hợp lý vài giờ)
CLOCK_TOLERANCE = timedelta(hours=12)
_CSTATE_FILE = os.path.join(config.DATA_DIR, ".cstate.json")


# ---------- thời gian / JSON ----------
def _utcnow():
    return datetime.now(timezone.utc)


def _parse(iso):
    """Parse ISO -> aware UTC (hỗ trợ 'Z' và chuỗi naive)."""
    dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _canonical(payload: dict) -> bytes:
    """PHẢI giống hệt signing.canonical ở server."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _verify(payload, sig_b64) -> bool:
    try:
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY_B64))
        pub.verify(base64.b64decode(sig_b64), _canonical(payload))
        return True
    except Exception:
        return False


# ---------- Machine ID (trộn nhiều nguồn cho khó clone) ----------
def _win_machine_guid():
    try:
        import winreg
        k = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography",
            0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        val, _ = winreg.QueryValueEx(k, "MachineGuid")
        winreg.CloseKey(k)
        return val or ""
    except Exception:
        return ""


def _volume_serial():
    try:
        import ctypes
        serial = ctypes.c_ulong(0)
        ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p("C:\\"), None, 0, ctypes.byref(serial),
            None, None, None, 0)
        return str(serial.value)
    except Exception:
        return ""


def _raw_machine():
    parts = [
        "guid:" + _win_machine_guid(),
        "vol:" + _volume_serial(),
        "node:" + str(uuid.getnode()),
    ]
    return "|".join(parts)


def get_machine_id() -> str:
    h = hashlib.sha256(_raw_machine().encode()).hexdigest().upper()
    return "-".join(h[i:i + 4] for i in range(0, 16, 4))   # 4 nhóm x 4 ký tự


# ---------- lưu / đọc token ----------
def _save_token(data):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_token():
    try:
        with open(config.LICENSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _delete_token():
    try:
        os.remove(config.LICENSE_FILE)
    except OSError:
        pass


# ---------- chống lùi đồng hồ (high-water mark) ----------
def _load_hwm():
    try:
        with open(_CSTATE_FILE, "r", encoding="utf-8") as f:
            return _parse(json.load(f)["hwm"])
    except Exception:
        return None


def _save_hwm(dt):
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(_CSTATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"hwm": dt.isoformat()}, f)
    except Exception:
        pass


def _clock_ok(now):
    """False nếu đồng hồ bị lùi quá dung sai so với mốc lớn nhất từng thấy."""
    hwm = _load_hwm()
    if hwm and now < hwm - CLOCK_TOLERANCE:
        return False
    if not hwm or now > hwm:
        _save_hwm(now)
    return True


def _st(status, message, info=None):
    return {"status": status, "message": message, "info": info}


# ---------- kiểm tra trạng thái (offline) ----------
def check():
    try:
        tok = _load_token()
        if not tok:
            return _st("NOT_ACTIVATED", "Chưa kích hoạt.")
        payload, sig = tok.get("payload"), tok.get("signature")
        if not payload or not sig or not _verify(payload, sig):
            return _st("INVALID_SIGNATURE", "License không hợp lệ (chữ ký sai).")
        if payload.get("machine_id") != get_machine_id():
            return _st("WRONG_MACHINE", "License này không dùng được trên máy hiện tại.")
        if payload.get("product", "default") != PRODUCT_ID:
            return _st("WRONG_PRODUCT", "License này không dành cho phần mềm này.")
        now = _utcnow()
        if not _clock_ok(now):
            return _st("NEEDS_RECHECK", "Phát hiện đồng hồ hệ thống bị chỉnh lùi — cần kết nối mạng để xác thực lại.", payload)
        exp = payload.get("expires_at")
        if exp and _parse(exp) < now:
            return _st("EXPIRED", "License đã hết hạn.", payload)
        token_exp = _parse(payload["token_exp"])
        grace = timedelta(days=int(payload.get("grace_days", 0)))
        if now >= token_exp + grace:
            return _st("NEEDS_RECHECK", "Cần kết nối mạng để xác thực lại.", payload)
        if now >= token_exp:
            return _st("GRACE", "Đang dùng hạn offline tạm thời, hãy kết nối mạng.", payload)
        return _st("VALID", "Hợp lệ.", payload)
    except Exception as e:                       # fail-closed: lỗi bất ngờ -> coi như cần kích hoạt lại
        return _st("INVALID_SIGNATURE", f"Không đọc được license: {e}")


# ---------- gọi server ----------
def _err(r):
    try:
        return r.json().get("detail", f"Lỗi {r.status_code}")
    except Exception:
        return f"Lỗi {r.status_code}: {r.text[:120]}"


def _post(endpoint, license_key):
    mid = get_machine_id()
    r = requests.post(
        config.LICENSE_SERVER_URL.rstrip("/") + endpoint,
        json={"license_key": license_key.strip(), "machine_id": mid},
        timeout=20)
    return r, mid


def activate(license_key):
    try:
        r, mid = _post("/api/activate", license_key)
    except requests.RequestException as e:
        return False, f"Không kết nối được server license: {e}"
    if r.status_code != 200:
        return False, _err(r)
    try:
        data = r.json()
    except ValueError:
        return False, "Phản hồi server không hợp lệ (không phải JSON)."
    payload = data.get("payload", {})
    if not _verify(payload, data.get("signature", "")) \
            or payload.get("machine_id") != mid:
        return False, "Phản hồi server không hợp lệ."
    # Server dùng CHUNG cho nhiều tool → từ chối key của phần mềm khác (tránh 'kích hoạt
    # thành công' nhầm rồi app vẫn báo sai sản phẩm).
    if payload.get("product", "default") != PRODUCT_ID:
        return False, "Key này thuộc phần mềm khác, không dùng cho PeiPei Clone Voice."
    _save_token(data)
    _save_hwm(_utcnow())
    return True, "Kích hoạt thành công."


def refresh():
    """Gia hạn token. Nếu server từ chối dứt khoát (revoke/hết hạn) -> xoá token."""
    tok = _load_token()
    if not tok:
        return False, "Chưa kích hoạt."
    key = (tok.get("payload") or {}).get("key")   # token hỏng cấu trúc -> không crash
    if not key:
        return False, "Token không hợp lệ."
    try:
        r, mid = _post("/api/refresh", key)
    except requests.RequestException:
        return False, "offline"                  # giữ token, dựa vào grace
    if r.status_code == 200:
        try:
            data = r.json()                       # proxy trả 200+HTML -> không crash
        except ValueError:
            return False, "Phản hồi server không hợp lệ."
        if _verify(data.get("payload", {}), data.get("signature", "")) \
                and data["payload"].get("machine_id") == mid:
            _save_token(data)
            _save_hwm(_utcnow())
            return True, "Đã gia hạn."
        return False, "Phản hồi server không hợp lệ."
    if r.status_code in (401, 403, 404):
        # CHỈ xoá token khi CHẮC CHẮN phản hồi đến từ SERVER LICENSE (body JSON đúng dạng,
        # có "detail"/"error"/"code"). Proxy/wifi công cộng trả 403 kèm HTML → GIỮ token,
        # dựa vào grace (tránh xoá nhầm license hợp lệ của khách đã trả tiền).
        try:
            body = r.json()
        except ValueError:
            body = None
        if isinstance(body, dict) and ({"detail", "error", "code"} & set(body)):
            _delete_token()                      # server thật sự thu hồi / hết hạn
            return False, _err(r)
        return False, "offline"                  # không chắc là server license → giữ token
    return False, _err(r)                         # 429/5xx -> giữ token


def _ver_tuple(s):
    out = []
    for x in str(s).split("."):
        try:
            out.append(int(x))
        except ValueError:
            out.append(0)
    return tuple(out)


def check_update():
    """Trả dict {latest,url,message} nếu server có bản mới hơn APP_VERSION, else None."""
    try:
        r = requests.get(config.LICENSE_SERVER_URL.rstrip("/") + "/version", timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        latest = d.get("latest_version", "")
        if latest and _ver_tuple(latest) > _ver_tuple(config.APP_VERSION):
            return {"latest": latest, "url": d.get("download_url", ""),
                    "message": d.get("message", "")}
    except Exception:
        return None
    return None


def maybe_refresh():
    """Best-effort gọi mỗi lần mở app: giúp revoke/gia hạn có hiệu lực sớm khi có mạng."""
    if _load_token():
        try:
            refresh()
        except Exception:
            pass


# ---------- text cho status bar ----------
def status_text():
    st = check()
    p = st.get("info")
    if st["status"] in ("VALID", "GRACE") and p:
        plan = "Trọn đời" if p["plan"] == "lifetime" else "Thuê bao"
        exp = p.get("expires_at")
        try:
            if exp:
                days = max(0, (_parse(exp) - _utcnow()).days)
                return f"License: {plan} | Hết hạn {str(exp)[:10]} (còn {days} ngày)"
        except Exception:
            pass
        return f"License: {plan} (vĩnh viễn)"
    return f"License: {st['message']}"
