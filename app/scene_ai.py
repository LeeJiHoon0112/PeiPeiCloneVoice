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

# Các model gợi ý cho từng hãng (phần tử ĐẦU là mặc định — rẻ + đủ thông minh để
# chia cảnh). User vẫn có thể tự gõ tên model khác, hoặc bấm ↻ để lấy danh sách
# MỚI NHẤT trực tiếp từ API (chính xác theo tài khoản). Danh sách dưới chỉ là gợi ý
# ban đầu — cập nhật mốc 2026-06-03 (OpenAI đã ra dòng GPT-5.4).
MODELS = {
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash",
               "gemini-1.5-flash"],
    "openai": ["gpt-5.4-mini", "gpt-5.4", "gpt-5-mini", "gpt-5",
               "gpt-4.1-mini", "gpt-4o-mini"],
    "claude": ["claude-3-5-haiku-latest", "claude-sonnet-4-5",
               "claude-3-5-sonnet-latest"],
}


def default_model(provider: str) -> str:
    """Model mặc định của 1 hãng (phần tử đầu danh sách)."""
    return MODELS.get((provider or "").lower(), ["?"])[0]


# Giữ tương thích tên cũ.
_DEFAULT_MODEL = {p: default_model(p) for p in PROVIDERS}

_TIMEOUT = 60  # giây


def _build_prompt(sentences: list[str], target_dur: float,
                  min_dur: float, max_dur: float, kind: str) -> str:
    """Soạn chỉ dẫn cho model. Đính kèm độ dài (giây) ước lượng từng câu để model
    cân nhắc, nhưng nhấn mạnh ưu tiên gom theo Ý NGHĨA."""
    purpose = ("tạo ẢNH TĨNH minh họa (mỗi cảnh là MỘT khung hình duy nhất, nên "
               "gói trọn một hình ảnh rõ ràng để vẽ)"
               if kind == "image" else
               "tạo CLIP VIDEO ĐỘNG (mỗi cảnh là một đoạn quay liền mạch)")
    lines = []
    for i, s in enumerate(sentences):
        lines.append(f"{i}: {s}")
    numbered = "\n".join(lines)
    return (
        "Bạn là một ĐẠO DIỄN PHÂN CẢNH (storyboard). Tôi có một kịch bản lồng "
        "tiếng đã tách thành các CÂU đánh số từ 0. Audio đã được thu sẵn theo đúng "
        "các câu này — bạn TUYỆT ĐỐI KHÔNG sửa, thêm, bớt hay viết lại chữ; chỉ "
        "quyết định cách GOM câu thành cảnh.\n\n"
        f"Mục đích: {purpose}.\n\n"
        "Hãy đọc HIỂU nội dung, rồi gom các câu liên tiếp thành các CẢNH (scene) "
        "sao cho mỗi cảnh là một đơn vị hình ảnh mạch lạc. NGẮT SANG CẢNH MỚI khi:\n"
        "  • đổi bối cảnh / địa điểm,\n"
        "  • đổi chủ thể hoặc nhân vật được nói tới,\n"
        "  • đổi hành động hoặc mốc thời gian (vd 'mười phút sau'),\n"
        "  • đổi ý/cảm xúc (đang kể chuyển sang đặt câu hỏi, kết luận...).\n"
        "Các câu cùng mô tả MỘT hình ảnh/ý thì để CHUNG một cảnh.\n\n"
        "RÀNG BUỘC BẮT BUỘC:\n"
        f"- Mỗi cảnh nên dài khoảng {target_dur:g} giây, và PHẢI trong khoảng "
        f"{min_dur:g}–{max_dur:g} giây (tổng thời lượng đọc các câu trong cảnh — "
        "dùng [số giây] kèm mỗi câu để cộng).\n"
        f"- Tuyệt đối không tạo cảnh dài quá {max_dur:g} giây; nếu một ý dài hơn "
        "thì tách thành nhiều cảnh tại ranh giới câu hợp lý.\n"
        "- KHÔNG đảo thứ tự câu. Mỗi câu thuộc đúng MỘT cảnh. Phải dùng HẾT tất cả "
        "các câu, không bỏ sót, không thêm câu nào.\n\n"
        "Dưới đây là các câu, kèm [độ dài giây] để bạn cộng dồn:\n"
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
# json_mode=True: ép model trả JSON thuần (dùng khi chia cảnh). Khi chỉ test kết
# nối thì để False — vì OpenAI bắt buộc prompt phải chứa chữ "json" mới cho dùng
# response_format=json_object, nếu không sẽ lỗi 400.
def _call_gemini(api_key: str, model: str, prompt: str, json_mode: bool = True) -> str:
    import requests
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    gen_cfg = {"temperature": 0.2}
    if json_mode:
        gen_cfg["responseMimeType"] = "application/json"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_cfg,
    }
    r = requests.post(url, params={"key": api_key}, json=body, timeout=_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_openai(api_key: str, model: str, prompt: str, json_mode: bool = True) -> str:
    import requests
    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if json_mode:
        # OpenAI yêu cầu prompt có chữ 'json' khi bật chế độ này (đã có trong
        # _build_prompt). Test kết nối dùng json_mode=False nên không vướng.
        body["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.post(url, headers=headers, json=body, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _call_claude(api_key: str, model: str, prompt: str, json_mode: bool = True) -> str:
    import requests
    url = "https://api.anthropic.com/v1/messages"
    body = {
        "model": model,
        "max_tokens": 4096,
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


# ----------------------------------------------- LẤY DANH SÁCH MODEL (LIVE) từ API
def _list_gemini(api_key: str) -> list[str]:
    import requests
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    out, page = [], None
    for _ in range(10):  # phòng phân trang, tối đa 10 trang
        params = {"key": api_key, "pageSize": 200}
        if page:
            params["pageToken"] = page
        r = requests.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        for m in data.get("models", []):
            # Chỉ lấy model hỗ trợ sinh nội dung (generateContent).
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" not in methods:
                continue
            name = (m.get("name") or "").split("/")[-1]  # "models/xxx" → "xxx"
            if name:
                out.append(name)
        page = data.get("nextPageToken")
        if not page:
            break
    return out


def _list_openai(api_key: str) -> list[str]:
    import requests
    url = "https://api.openai.com/v1/models"
    r = requests.get(url, headers={"Authorization": f"Bearer {api_key}"},
                     timeout=_TIMEOUT)
    r.raise_for_status()
    return [m.get("id", "") for m in r.json().get("data", []) if m.get("id")]


def _list_claude(api_key: str) -> list[str]:
    import requests
    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    out, page = [], None
    for _ in range(10):
        params = {"limit": 200}
        if page:
            params["after_id"] = page
        r = requests.get(url, headers=headers, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        for m in data.get("data", []):
            mid = m.get("id", "")
            if mid:
                out.append(mid)
        if data.get("has_more") and data.get("last_id"):
            page = data["last_id"]
        else:
            break
    return out


_LIST_DISPATCH = {"gemini": _list_gemini, "openai": _list_openai,
                  "claude": _list_claude}

# Lọc bỏ các model KHÔNG hợp cho việc sinh văn bản (chia cảnh) — đỡ rối danh sách.
# Áp dụng cho MỌI hãng: bỏ các dòng chuyên audio/ảnh/embedding/robot/preview...
_SKIP_ANY = ("embedding", "whisper", "tts", "dall-e", "audio", "realtime",
             "image", "imagen", "moderation", "transcribe", "search",
             "computer-use", "robotics", "vision", "veo", "live", "guard",
             "aqa", "gemma", "learnlm", "codey", "rerank")


def _is_text_model(provider: str, name: str) -> bool:
    low = name.lower()
    if any(k in low for k in _SKIP_ANY):
        return False
    if provider == "openai":
        # Giữ dòng GPT (gpt-4/4o/4.1/5/5.4...) và dòng reasoning o-series (o1/o3/o4...).
        return bool(low.startswith("gpt") or re.match(r"^o\d", low))
    if provider == "gemini":
        return low.startswith("gemini")
    return True  # claude: API chỉ trả model chat


def _model_sort_key(provider: str, name: str):
    """Khóa sắp xếp: ưu tiên model CHÍNH & MỚI lên đầu.
    Trả (–điểm_ưu_tiên, –phiên_bản, tên) để sort tăng dần = tốt/mới ở trên."""
    low = name.lower()
    # Lấy 2 số phiên bản đầu để so sánh (vd 'gpt-5.4'→(5,4), 'claude-opus-4-8'→(4,8),
    # 'gemini-2.5-pro'→(2,5)). Số thứ 2 phân biệt opus-4-8 > opus-4-6.
    nums = re.findall(r"\d+", low.split("-2025")[0].split("2024")[0])
    ver = float(nums[0]) if nums else 0.0
    ver2 = float(nums[1]) if len(nums) > 1 else 0.0
    # Điểm ưu tiên theo họ model "xịn" + bớt điểm các bản preview/cũ/snapshot ngày.
    pri = 0
    if provider == "openai":
        if low.startswith("gpt"):
            pri += 10
        if re.match(r"^o\d", low):
            pri += 6
    elif provider == "gemini":
        if "pro" in low:
            pri += 6
        if "flash" in low:
            pri += 5
        if "latest" in low:
            pri += 2
    elif provider == "claude":
        if "opus" in low:
            pri += 7
        if "sonnet" in low:
            pri += 6
        if "haiku" in low:
            pri += 5
        if "latest" in low:
            pri += 2
    if "preview" in low or "exp" in low or "beta" in low:
        pri -= 4
    # Bản gắn ngày (snapshot, vd -20250101 hoặc -2025-01-01) xếp sau bản 'latest'.
    if re.search(r"\d{4}-?\d{2}-?\d{2}", low):
        pri -= 1
    return (-pri, -ver, -ver2, low)


def list_models(provider: str, api_key: str) -> list[str]:
    """Lấy TOÀN BỘ model dùng được cho chia cảnh, trực tiếp từ API (theo tài khoản
    của key). Đã lọc bỏ model audio/ảnh/embedding/robot... và sắp xếp model chính &
    mới lên đầu để user dễ chọn. Ném exception nếu lỗi (để UI báo)."""
    provider = (provider or "").lower().strip()
    if provider not in _LIST_DISPATCH:
        raise ValueError(f"Nhà cung cấp không hỗ trợ: {provider!r}")
    if not api_key or not api_key.strip():
        raise ValueError("Chưa nhập API key.")
    raw = _LIST_DISPATCH[provider](api_key.strip())
    seen, out = set(), []
    for name in raw:
        if name and name not in seen and _is_text_model(provider, name):
            seen.add(name)
            out.append(name)
    out.sort(key=lambda n: _model_sort_key(provider, n))
    return out


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
    mdl = model or default_model(provider)
    text = _DISPATCH[provider](api_key.strip(), mdl, prompt)
    return _extract_json_groups(text)


def test_connection(provider: str, api_key: str,
                    model: str | None = None) -> tuple[bool, str]:
    """Kiểm tra nhanh key + model có gọi được không, bằng 1 yêu cầu cực nhỏ.

    Trả về (ok, thông_điệp). KHÔNG ném exception — luôn trả message thân thiện để
    hiện lên UI (vd: 'Sai API key', 'Model không tồn tại', 'Không có mạng'...).
    """
    provider = (provider or "").lower().strip()
    if provider not in _DISPATCH:
        return False, f"Nhà cung cấp không hỗ trợ: {provider!r}"
    if not api_key or not api_key.strip():
        return False, "Chưa nhập API key."
    mdl = model or default_model(provider)
    # Prompt tí hon: chỉ cần model phản hồi là biết key/model/đường truyền OK.
    # json_mode=False để không vướng ràng buộc "prompt phải chứa chữ json" của OpenAI.
    ping = "Trả lời đúng một từ: OK."
    try:
        text = _DISPATCH[provider](api_key.strip(), mdl, ping, json_mode=False)
        snippet = (text or "").strip().replace("\n", " ")[:40]
        return True, f"Kết nối OK ({provider}/{mdl}). Phản hồi: {snippet!r}"
    except Exception as e:
        return False, _friendly_error(e, provider, mdl)


def _friendly_error(e: Exception, provider: str, model: str) -> str:
    """Đổi exception (thường là HTTPError của requests) sang thông điệp dễ hiểu."""
    # Lấy status code nếu là lỗi HTTP từ requests.
    status = None
    resp = getattr(e, "response", None)
    if resp is not None:
        status = getattr(resp, "status_code", None)
    name = type(e).__name__
    if status == 401 or status == 403:
        return f"Sai hoặc thiếu quyền API key ({status})."
    if status == 404:
        return f"Model không tồn tại: '{model}' (404). Hãy chọn model khác."
    if status == 429:
        return "Vượt hạn mức / quá nhiều yêu cầu (429). Thử lại sau."
    if status == 400:
        # Gemini hay trả 400 khi key sai hoặc model sai.
        return (f"Yêu cầu không hợp lệ (400) — thường do API key sai hoặc "
                f"model '{model}' không đúng.")
    if "ConnectionError" in name or "Timeout" in name or "ConnectTimeout" in name:
        return "Không kết nối được — kiểm tra mạng Internet."
    return f"Lỗi: {name}: {str(e)[:80]}"
