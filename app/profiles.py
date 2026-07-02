"""Quản lý các giọng đã lưu (voice profiles): lưu/đọc/xóa/liệt kê.

Mỗi giọng nằm trong thư mục riêng:  user_data/voices/<tên>/
    <tên>.pt    -> voice clone prompt (torch.save)
    <tên>.json  -> metadata (tên, audio mẫu, lời thoại mẫu, thời gian tạo)
"""
# Để annotation kiểu list[str] không bị lỗi do method tên 'list' che built-in.
from __future__ import annotations

import os
import json
import datetime

from . import config


def _safe_name(name: str) -> str:
    keep = "-_. ()[]"
    cleaned = "".join(c for c in name.strip() if c.isalnum() or c in keep or ord(c) > 127)
    # Bỏ dấu chấm/khoảng trắng ở HAI ĐẦU: Windows cấm thư mục kết thúc bằng '.' (giọng sẽ
    # "tàng hình" do lệch tên), và chặn tên nguy hiểm như "." / ".." (ghi file ra ngoài voices_dir).
    cleaned = cleaned.strip(" .")
    return cleaned or "voice"


def _as_prompt(obj):
    """Chuẩn hóa về VoiceClonePrompt.

    App tự lưu là VoiceClonePrompt; tool gốc lưu là dict cùng 3 trường
    (ref_audio_tokens, ref_text, ref_rms). Hàm này nhận cả 2 dạng.
    """
    try:
        from omnivoice.models.omnivoice import VoiceClonePrompt
    except Exception:
        return obj  # không có lib (không nên xảy ra khi đã nạp model) → trả nguyên
    if isinstance(obj, VoiceClonePrompt):
        return obj
    if isinstance(obj, dict) and "ref_audio_tokens" in obj:
        return VoiceClonePrompt(
            ref_audio_tokens=obj["ref_audio_tokens"],
            ref_text=obj.get("ref_text", ""),
            ref_rms=float(obj.get("ref_rms", 0.0)),
        )
    return obj


class ProfileManager:
    def __init__(self):
        config.ensure_dirs()
        self.voices_dir = config.VOICES_DIR
        # Danh sách tên giọng người dùng đã CHỦ ĐỘNG xóa — để auto-import KHÔNG
        # khôi phục lại chúng từ tool gốc mỗi lần mở app. Lưu trong user_data.
        self.deleted_file = os.path.join(config.USER_DATA_DIR, "deleted_voices.json")

    # ------------------------------------------------- danh sách giọng đã xóa
    def _load_deleted(self) -> set:
        try:
            with open(self.deleted_file, encoding="utf-8") as f:
                data = json.load(f)
            return set(data) if isinstance(data, list) else set()
        except Exception:
            return set()

    def _save_deleted(self, names: set):
        try:
            with open(self.deleted_file, "w", encoding="utf-8") as f:
                json.dump(sorted(names), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _mark_deleted(self, name: str):
        s = self._load_deleted()
        s.add(_safe_name(name))
        self._save_deleted(s)

    def _unmark_deleted(self, name: str):
        """Bỏ tên khỏi danh sách đã xóa (khi user CHỦ ĐỘNG tạo/import lại giọng đó)."""
        s = self._load_deleted()
        n = _safe_name(name)
        if n in s:
            s.discard(n)
            self._save_deleted(s)

    def list(self) -> list[dict]:
        items = []
        if not os.path.isdir(self.voices_dir):
            return items
        for name in sorted(os.listdir(self.voices_dir)):
            d = os.path.join(self.voices_dir, name)
            pt = os.path.join(d, f"{name}.pt")
            if os.path.isdir(d) and os.path.exists(pt):
                meta = {}
                mj = os.path.join(d, f"{name}.json")
                if os.path.exists(mj):
                    try:
                        with open(mj, encoding="utf-8") as f:
                            meta = json.load(f)
                    except Exception:
                        meta = {}
                items.append({"name": name, "dir": d, "pt": pt, "meta": meta})
        return items

    def exists(self, name: str) -> bool:
        name = _safe_name(name)
        return os.path.exists(os.path.join(self.voices_dir, name, f"{name}.pt"))

    def save(self, name: str, prompt, ref_audio: str = "", ref_text: str = "") -> str:
        import torch

        name = _safe_name(name)
        d = os.path.join(self.voices_dir, name)
        os.makedirs(d, exist_ok=True)
        torch.save(prompt, os.path.join(d, f"{name}.pt"))
        meta = {
            "name": name,
            "ref_audio": ref_audio,
            "ref_text": ref_text,
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        with open(os.path.join(d, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        # User chủ động tạo/lưu lại giọng này → bỏ khỏi danh sách "đã xóa".
        self._unmark_deleted(name)
        return name

    def load_prompt(self, name: str):
        import torch

        name = _safe_name(name)
        pt = os.path.join(self.voices_dir, name, f"{name}.pt")
        if not os.path.exists(pt):
            raise FileNotFoundError(pt)
        obj = torch.load(pt, weights_only=False)
        return _as_prompt(obj)

    def delete(self, name: str):
        import shutil

        name = _safe_name(name)
        d = os.path.join(self.voices_dir, name)
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
        # Ghi nhớ đã xóa → auto-import sẽ KHÔNG khôi phục lại từ tool gốc.
        self._mark_deleted(name)

    # ------------------------------------------------------------- import
    def import_pt_file(self, pt_path: str, name: str | None = None,
                       ref_audio: str = "", ref_text: str = "",
                       overwrite: bool = False) -> str:
        """Import 1 file .pt (định dạng app hoặc tool gốc) thành giọng của app."""
        import torch

        if name is None:
            name = os.path.splitext(os.path.basename(pt_path))[0]
        name = _safe_name(name)
        if self.exists(name) and not overwrite:
            return ""  # đã có → bỏ qua

        obj = torch.load(pt_path, weights_only=False)
        prompt = _as_prompt(obj)
        # Lấy ref_text từ chính prompt nếu chưa truyền
        if not ref_text:
            ref_text = getattr(prompt, "ref_text", "") or ""
        return self.save(name, prompt, ref_audio=ref_audio, ref_text=ref_text)

    def import_from_dir(self, src_dir: str, overwrite: bool = False,
                        skip_deleted: bool = False) -> list[str]:
        """Quét một thư mục giọng kiểu tool gốc (mỗi giọng 1 folder con chứa .pt
        và tùy chọn _metadata.json) và import các giọng chưa có. Trả về tên đã thêm.

        skip_deleted=True: bỏ qua giọng người dùng đã chủ động xóa (dùng cho
        auto-import để không "hồi sinh" giọng đã xóa).
        """
        added: list[str] = []
        if not src_dir or not os.path.isdir(src_dir):
            return added

        deleted = self._load_deleted() if skip_deleted else set()
        for entry in sorted(os.listdir(src_dir)):
            sub = os.path.join(src_dir, entry)
            if not os.path.isdir(sub):
                continue
            # tìm file .pt trong folder con
            pts = [f for f in os.listdir(sub) if f.lower().endswith(".pt")]
            if not pts:
                continue
            pt_path = os.path.join(sub, pts[0])
            name = _safe_name(entry)
            if skip_deleted and name in deleted:
                continue  # giọng đã bị xóa → không khôi phục
            if self.exists(name) and not overwrite:
                continue
            # đọc metadata kèm theo (nếu có) để lấy ref_audio / ref_text
            ref_audio, ref_text = "", ""
            for mf in os.listdir(sub):
                if mf.lower().endswith(".json"):
                    try:
                        with open(os.path.join(sub, mf), encoding="utf-8") as f:
                            m = json.load(f)
                        ref_audio = m.get("ref_audio", "") or ref_audio
                        ref_text = m.get("ref_text", "") or ref_text
                    except Exception:
                        pass
                    break
            try:
                saved = self.import_pt_file(pt_path, name=name, ref_audio=ref_audio,
                                            ref_text=ref_text, overwrite=overwrite)
                if saved:
                    added.append(saved)
            except Exception:
                pass  # bỏ qua giọng lỗi, không làm hỏng cả quá trình
        return added

    def auto_import_old_tool_voices(self) -> list[str]:
        """Tự động import giọng từ tool gốc (nếu thư mục tồn tại trên máy này).
        BỎ QUA giọng người dùng đã xóa để không khôi phục lại chúng."""
        added: list[str] = []
        for d in config.OLD_TOOL_VOICES_DIRS:
            if d and os.path.isdir(d):
                added += self.import_from_dir(d, overwrite=False, skip_deleted=True)
        return added
