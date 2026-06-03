"""Chia cảnh theo Ý NGHĨA bằng API (tùy chọn) — hỗ trợ Gemini / OpenAI / Claude.

Ý tưởng (hybrid): TIMESTAMP luôn lấy từ audio thật (do engine cung cấp), còn AI
chỉ quyết định RANH GIỚI CẢNH — gom các câu cùng một ý vào 1 cảnh, ngắt ở chỗ
chuyển ý. App vẫn ÉP CỨNG ràng buộc thời lượng [min,max] sau khi AI trả về (xem
engine.cues_from_ai_groups), nên AI không thể phá luật về độ dài.

API trả về JSON: {"groups": [[0,1],[2],[3,4,5], ...]} — mỗi nhóm là danh sách
CHỈ SỐ câu (0-based). Module này CHỈ gọi mạng và parse kết quả thành list[list[int]];
việc dựng cue + ép ràng buộc nằm ở engine. Mọi lỗi → ném exception để bên gọi
fallback về thuật toán offline.

Không phụ thuộc SDK riêng của hãng — gọi thẳng REST bằng `requests` (đã có sẵn
trong venv), để bạn bè khỏi cài thêm thư viện nặng.
"""
from __future__ import annotations

import json
import re

PROVIDERS = ("gemini", "openai", "claude")

# Model mặc định cho từng hãng (rẻ + đủ thông minh cho việc chia cảnh).
_DEFAULT_MODEL = {
    "gemini": "gemini-2.0-flash",
    "openai": "gpt-4o-mini",
    "claude": "claude-3-5-haiku-latest",
}

_TIMEOUT = 60  # giây


def _build_prompt(sentences: list[str], target_dur: float,
                  min_dur: float, max_dur: float, kind: str) -> str:
    """Soạn chỉ dẫn cho model. Đính kèm độ dài (giây) ước lượng từng câu để model
    cân nhắc, nhưng nhấn mạnh ưu tiên gom theo Ý NGHĨA."""
    purpose = ("tạo ẢNH TĨNH (mỗi cảnh là một khung hình cần mô tả rõ)"
               if kind == "image" else
               "tạo CLIP VIDEO ĐỘNG (mỗi cảnh là một đoạn quay)")
    lines = []
    for i, s in enumerate(sentences):
        lines.append(f"{i}: {s}")
    numbered = "\n".join(lines)
    return (
        "Bạn là trợ lý dựng video. Tôi có một kịch bản đã tách thành các CÂU đánh "
        f"số từ 0. Mục đích: {purpose}.\n\n"
        "Hãy GOM các câu liên tiếp thành các CẢNH (scene) theo Ý NGHĨA: các câu "
        "cùng một ý/một hình ảnh thì vào chung một cảnh; ngắt cảnh ở chỗ chuyển ý, "
        "đổi bối cảnh, hoặc đổi chủ thể.\n\n"
        "RÀNG BUỘC BẮT BUỘC:\n"
        f"- Mỗi cảnh nên dài khoảng {target_dur:g} giây, trong khoảng "
        f"{min_dur:g}–{max_dur:g} giây (đây là tổng thời lượng đọc của các câu trong cảnh).\n"
        "- KHÔNG được đảo thứ tự câu. Mỗi câu thuộc đúng MỘT cảnh. Phải dùng HẾT "
        "tất cả các câu, không bỏ sót, không thêm.\n\n"
        "Dưới đây là các câu, kèm [độ dài giây] để bạn ước lượng:\n"
        f"{numbered}\n\n"
        "CHỈ trả về JSON đúng định dạng sau, không giải thích gì thêm:\n"
        '{"groups": [[0,1],[2],[3,4,5]]}'
    )


def _annotate_durations(sentences: list[str], durs: list[float]) -> list[str]:
    out = []
    for s, d in zip(sentences, durs):
        out.append(f"{s}  [{d:.1f}s]")
    return out


def _extract_json_groups(text: str) -> list[list[int]]:
    """Bóc {"groups": [...]} từ chuỗi trả về (có thể lẫn ```json hoặc chữ thừa)."""
    if not text:
        raise ValueError("API trả về rỗng.")
    # Gỡ rào ```json ... ```
    text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text.strip())
    # Tìm đối tượng JSON đầu tiên chứa "groups"
    m = re.search(r"\{.*\"groups\".*\}", text, re.DOTALL)
    raw = m.group(0) if m else text
    data = json.loads(raw)
    groups = data.get("groups")
    if not isinstance(groups, list):
        raise ValueError("JSON thiếu 'groups'.")
    out = []
    for g in groups:
        if not isinstance(g, list):
            raise ValueError("'groups' phải là danh sách các danh sách.")
        out.append([int(x) for x in g])
    return out


# ----------------------------------------------------------------- gọi REST API
def _call_gemini(api_key: str, model: str, prompt: str) -> str:
    import requests
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2,
                             "responseMimeType": "application/json"},
    }
    r = requests.post(url, params={"key": api_key}, json=body, timeout=_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_openai(api_key: str, model: str, prompt: str) -> str:
    import requests
    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.post(url, headers=headers, json=body, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _call_claude(api_key: str, model: str, prompt: str) -> str:
    import requests
    url = "https://api.anthropic.com/v1/messages"
    body = {
        "model": model,
        "max_tokens": 4096,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    r = requests.post(url, headers=headers, json=body, timeout=_TIMEOUT)
    r.raise_for_status()
    parts = r.json().get("content", [])
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


_DISPATCH = {"gemini": _call_gemini, "openai": _call_openai, "claude": _call_claude}


def suggest_groups(segments: list[dict], provider: str, api_key: str,
                   target_dur: float, min_dur: float, max_dur: float,
                   kind: str = "image", model: str | None = None) -> list[list[int]]:
    """Gọi API để lấy cách nhóm câu theo ý nghĩa. Ném exception nếu lỗi (mạng,
    key sai, JSON hỏng...) để bên gọi fallback. KHÔNG bắt lỗi ở đây."""
    provider = (provider or "").lower().strip()
    if provider not in _DISPATCH:
        raise ValueError(f"Nhà cung cấp không hỗ trợ: {provider!r}")
    if not api_key or not api_key.strip():
        raise ValueError("Chưa nhập API key.")
    sentences = [(s.get("text") or "").strip() for s in segments]
    durs = [max(0.0, float(s.get("end", 0)) - float(s.get("start", 0)))
            for s in segments]
    prompt = _build_prompt(_annotate_durations(sentences, durs),
                           target_dur, min_dur, max_dur, kind)
    mdl = model or _DEFAULT_MODEL[provider]
    text = _DISPATCH[provider](api_key.strip(), mdl, prompt)
    return _extract_json_groups(text)
