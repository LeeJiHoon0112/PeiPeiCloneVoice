"""Lớp bọc model OmniVoice: nạp model, nhận diện giọng (Whisper), tạo voice profile và sinh audio.

Đây là phần lõi clone giọng — dùng model mã nguồn mở OmniVoice (Apache-2.0, k2-fsa/OmniVoice).
"""
import re

import numpy as np

from . import config
from . import text_norm


# Giọng mẫu nên ngắn (3-10s, tối đa ~20s). Audio dài hơn vừa làm giảm chất lượng
# clone, vừa khiến Whisper rơi vào chế độ "long-form" gây lỗi → ta tự cắt bớt.
REF_MAX_SECONDS = 20.0


def _fmt_srt_time(t: float) -> str:
    """Đổi giây (float) sang dạng SRT: HH:MM:SS,mmm"""
    if t < 0:
        t = 0.0
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# Liên từ thường dùng làm điểm tách câu dài (Anh + Việt). Tách TRƯỚC từ này.
_SPLIT_CONJUNCTIONS = [
    "and", "but", "because", "while", "so", "when", "however",
    "although", "though", "since", "unless", "whereas", "yet",
    "và", "nhưng", "vì", "bởi", "nên", "khi", "tuy", "mặc dù",
    "trong khi", "cho nên", "rồi", "hoặc",
]

# ── Hỗ trợ chữ viết KHÔNG dùng dấu cách giữa từ (Nhật/Trung/Hàn...) ────────────
# Toàn bộ splitter cũ giả định "từ = cụm ngăn bởi dấu cách" + dấu câu Latin. Với
# tiếng Nhật/Trung (chữ liền, dấu full-width, KHÔNG có khoảng trắng theo sau) thì
# mọi phép tách đó vô hiệu → cả đoạn thành 1 "câu"/1 atom không băm được → cảnh
# SRT dài bằng cả file, vượt số giây người dùng chọn. Ta nhận biết chữ CJK để
# chuyển sang cắt theo KÝ TỰ và dùng dấu câu full-width làm điểm ngắt.
_CJK_RE = re.compile(
    "[぀-ヿ㐀-䶿一-鿿豈-﫿"
    "가-힣ᄀ-ᇿ㄰-㆏ｦ-ﾟ]"
)
# Ngôn ngữ chữ liền — dùng làm gợi ý CƯỠNG BỨC khi có mã ngôn ngữ rõ ràng.
_CJK_LANGS = {"ja", "zh", "ko", "zh-cn", "zh-tw", "zh-hans", "zh-hant", "yue"}
# Dấu kết câu (full & half) — trong CJK KHÔNG có khoảng trắng theo sau.
_CJK_ENDERS = "。！？!?…"
# Dấu ngắt giữa câu (kể cả dấu phẩy full-width) để chia cảnh câu dài.
_CJK_BREAKS = "、，。；：！？!?…·・"
# Dấu đóng ngoặc/nháy: nuốt vào CUỐI câu thay vì rớt sang câu sau.
_CJK_CLOSERS = "」』）)】〉》”’"


def _is_cjk(text: str, lang: str | None = None) -> bool:
    """True nếu văn bản thuộc chữ viết KHÔNG dùng dấu cách giữa từ (Nhật/Trung/Hàn).

    Ưu tiên mã ngôn ngữ nếu có; nếu không (người dùng để 'Tự động') thì TỰ NHẬN
    DIỆN theo tỉ lệ ký tự CJK. Tiếng Việt/Anh lỡ trích 1 chữ Hán vẫn trả về False.
    """
    if lang and lang.lower() in _CJK_LANGS:
        return True
    if not text:
        return False
    cjk = len(_CJK_RE.findall(text))
    if cjk == 0:
        return False
    non_space = sum(1 for c in text if not c.isspace())
    if non_space <= 0:
        return False
    # (a) mật độ chữ CJK cao → chắc chắn là chữ CJK.
    if cjk / non_space >= 0.30:
        return True
    # (b) văn bản GẦN NHƯ không có dấu cách mà vẫn chứa chữ CJK (vd câu Nhật lẫn URL,
    #     tên romaji, nhiều chữ số) → vẫn coi là chữ CJK. Nếu không, cả câu bị xem là
    #     "1 từ khổng lồ" (không dấu cách) → KHÔNG cắt được → cảnh vượt trần số giây.
    spaces = sum(1 for c in text if c == " ")
    return spaces <= non_space * 0.05


def _char_based(text: str, lang: str | None = None) -> bool:
    """True nếu nên cắt theo KÝ TỰ: chữ CJK và HẦU NHƯ không có dấu cách giữa từ
    (Nhật/Trung). Tiếng Hàn tuy là CJK nhưng CÓ dấu cách giữa từ → vẫn cắt theo TỪ."""
    if not _is_cjk(text, lang):
        return False
    body = "".join(text.split())
    if not body:
        return False
    spaces = sum(1 for c in text if c == " ")
    return spaces <= len(body) * 0.05


def _join_texts(parts) -> str:
    """Nối các đoạn text thành 1 cảnh. Nếu TẤT CẢ đều là chữ CJK không-dấu-cách →
    nối SÁT (không chèn khoảng trắng thừa vào phụ đề Nhật/Trung); ngược lại nối
    bằng khoảng trắng như thường (giữ nguyên hành vi tiếng Việt/Anh)."""
    parts = [p.strip() for p in (parts or []) if p and p.strip()]
    if not parts:
        return ""
    # Trong ngữ cảnh chữ CJK, mọi mảnh đều là TOKEN LIỀN (không có dấu cách bên trong):
    # cụm chữ CJK, dấu câu ('。', '……'), hoặc cụm ASCII (URL, tên romaji, chữ số) vốn
    # dính liền trong câu gốc → phải nối SÁT, không chèn dấu cách (nếu không phụ đề
    # Nhật/Trung ra 'りません 。' hay '西暦 2024 年'). Chỉ cần MỘT mảnh có dấu cách bên
    # trong ⇒ đó là cụm nhiều-từ Latin (vi/en) ⇒ nối bằng dấu cách như thường.
    has_cjk = any(_char_based(p) for p in parts)
    any_multiword = any(" " in p for p in parts)
    sep = "" if (has_cjk and not any_multiword) else " "
    return sep.join(parts).strip()


def _split_cjk_sentences(line: str) -> list[str]:
    """Tách câu cho chữ CJK: cắt SAU dấu kết câu 。！？!?… (và '.' không phải số
    thập phân), gộp cụm dấu liên tiếp, nuốt dấu đóng ngoặc/nháy liền sau; KHÔNG
    đòi khoảng trắng theo sau (điều mà tiếng Nhật/Trung không bao giờ có)."""
    out: list[str] = []
    buf: list[str] = []
    n = len(line)
    i = 0
    while i < n:
        ch = line[i]
        buf.append(ch)
        is_end = ch in _CJK_ENDERS
        if ch == "." and not is_end:
            prev = line[i - 1] if i > 0 else ""
            nxt = line[i + 1] if i + 1 < n else ""
            if not (prev.isdigit() and nxt.isdigit()):   # bỏ qua số thập phân "3.14"
                is_end = True
        if is_end:
            j = i + 1
            while j < n and line[j] in (_CJK_ENDERS + "."):   # gộp "!?", "。。", "..."
                buf.append(line[j]); j += 1
            while j < n and line[j] in _CJK_CLOSERS:           # nuốt 」』）) vào cuối câu
                buf.append(line[j]); j += 1
            out.append("".join(buf)); buf = []
            i = j
            continue
        i += 1
    if buf:
        out.append("".join(buf))
    return out


def _split_points(text: str) -> list[int]:
    """Tìm các vị trí (chỉ số ký tự) tốt để tách 1 câu dài.

    Ưu tiên: sau dấu phẩy/chấm phẩy/gạch ngang → rồi tới trước liên từ.
    Trả về danh sách vị trí cắt (sau khoảng trắng), đã sắp xếp.
    """
    points = set()
    # 1) sau các dấu ngắt giữa câu (Latin: cần khoảng trắng theo sau)
    for m in re.finditer(r"[,;:—–]\s+", text):
        points.add(m.end())
    # 1b) CJK: cắt NGAY SAU cụm dấu ngắt/kết câu full-width — KHÔNG đòi khoảng
    #     trắng (tiếng Nhật/Trung không bao giờ có). Đây là điểm cắt tự nhiên để
    #     chia câu CJK dài thành cảnh, thay cho dấu phẩy Latin vốn không xuất hiện.
    for m in re.finditer("[" + re.escape(_CJK_BREAKS) + "]+", text):
        points.add(m.end())
    # 2) trước các liên từ (đứng giữa câu, có khoảng trắng 2 bên)
    low = text.lower()
    for conj in _SPLIT_CONJUNCTIONS:
        for m in re.finditer(r"\s+" + re.escape(conj) + r"\s+", low):
            points.add(m.start() + 1)  # cắt ngay trước liên từ (giữ liên từ ở vế sau)
    return sorted(p for p in points if 0 < p < len(text))


def _word_chunks(text: str, nparts: int) -> list[str]:
    """Chia đều text thành nparts mảnh (dự phòng khi không có dấu/liên từ).

    Chữ CJK không có dấu cách → chia theo KÝ TỰ; còn lại chia theo TỪ như cũ."""
    import math
    if _char_based(text):
        if nparts <= 1 or len(text) <= 1:
            return [text]
        per = math.ceil(len(text) / nparts)
        return [text[i:i + per] for i in range(0, len(text), per)]
    words = text.split()
    if nparts <= 1 or len(words) <= 1:
        return [text]
    per = math.ceil(len(words) / nparts)
    return [" ".join(words[i:i + per]) for i in range(0, len(words), per)]


def _balanced_pieces(text: str, max_chars: float) -> list[str]:
    """Tách text thành các mảnh CÂN ĐỐI, mỗi mảnh ≤ max_chars ký tự.

    Ưu tiên cắt tại dấu phẩy / liên từ; nhắm mỗi mảnh ~ bằng nhau để tránh
    kiểu 5s + 9s. ĐẢM BẢO không mảnh nào dài quá max_chars (cắt theo từ nếu cần).
    """
    import math
    text = text.strip()
    total = len(text)
    if total <= max_chars:
        return [text]

    cjk = _char_based(text)     # chữ liền (Nhật/Trung) → cắt theo KÝ TỰ, không theo từ
    nparts = max(2, math.ceil(total / max_chars))
    target = total / nparts

    # "atom" = các đoạn giữa các điểm tách hợp lý; gom atom thành mảnh cân đối
    cuts = _split_points(text)
    bounds = [0] + cuts + [total]
    atoms = [text[a:b] for a, b in zip(bounds, bounds[1:]) if text[a:b].strip()]
    if len(atoms) <= 1:
        atoms = None  # không có điểm tách → để bước sau cắt theo từ

    pieces: list[str] = []
    if atoms:
        cur = ""
        for k, atom in enumerate(atoms):
            if not cur:
                cur = atom
                continue
            # vượt trần → buộc đóng mảnh
            if len(cur) + len(atom) > max_chars:
                pieces.append(cur)
                cur = atom
                continue
            # đã đạt ~target và chưa phải mảnh cuối → đóng để cân đối
            remaining_atoms = len(atoms) - k
            if len(cur) >= target and remaining_atoms > 1:
                pieces.append(cur)
                cur = atom
            else:
                cur += atom
        if cur.strip():
            pieces.append(cur)
        pieces = [p.strip() for p in pieces if p.strip()]
    else:
        pieces = [text]

    # An toàn TUYỆT ĐỐI: mảnh nào vẫn > max_chars → GOM TỪ THAM LAM theo KÝ TỰ (không
    # chia theo số từ như cũ — chia số từ dễ để lọt mảnh > max_chars khi từ dài không đều).
    # Mỗi mảnh nhiều-từ đảm bảo ≤ max_chars; từ đơn dài hơn max_chars đành để nguyên.
    safe: list[str] = []
    for p in pieces:
        if len(p) > max_chars and cjk:
            # Chữ CJK không có dấu cách → cắt CỨNG theo KÝ TỰ để không mảnh nào vượt
            # trần (đây là lớp chặn cuối, kể cả khi câu không có dấu ngắt nào).
            step = max(1, int(max_chars))
            safe.extend(p[k:k + step] for k in range(0, len(p), step))
        elif len(p) > max_chars and len(p.split()) > 1:
            cur = ""
            for w in p.split():
                if cur and len(cur) + 1 + len(w) > max_chars:
                    safe.append(cur)
                    cur = w
                else:
                    cur = (cur + " " + w) if cur else w
            if cur:
                safe.append(cur)
        else:
            safe.append(p)
    return [s.strip() for s in safe if s.strip()] or [text]


def _split_long_segment(text, start, end, max_dur):
    """Một câu DÀI hơn max_dur giây → tách tại dấu phẩy / liên từ (theo spec).

    Mỗi mảnh ≤ max_dur (đảm bảo cứng), cân đối nhau, hợp vùng lý tưởng 6–8s.
    Mốc thời gian chia theo TỈ LỆ số ký tự để khớp audio.
    """
    dur = max(0.0, end - start)
    text = text.strip()
    # "Không thể cắt": chữ có dấu cách = 1 từ; chữ CJK (liền, không dấu cách) = 1 ký
    # tự. Nếu dùng chung len(text.split())<=1 thì cả đoạn Nhật/Trung (không dấu cách)
    # bị coi là "1 từ" → bỏ qua cắt → cảnh vượt trần. Tách theo loại chữ để sửa.
    indivisible = (len(text) <= 1) if _char_based(text) else (len(text.split()) <= 1)
    if dur <= max_dur or indivisible:
        return [{"text": text, "start": start, "end": end}]

    # Số ký tự tương ứng max_dur giây (theo tốc độ đọc THẬT của câu này, từ audio)
    cps = len(text) / dur if dur > 0 else len(text)
    max_chars = max(1.0, max_dur * cps)

    pieces_txt = _balanced_pieces(text, max_chars)

    # Gán mốc thời gian theo tỉ lệ số ký tự
    total_chars = sum(len(p) for p in pieces_txt) or 1
    out = []
    t = start
    cum = 0
    for k, p in enumerate(pieces_txt):
        cum += len(p)
        ce = end if k == len(pieces_txt) - 1 else start + dur * cum / total_chars
        out.append({"text": p, "start": t, "end": ce})
        t = ce
    return out


def _render_srt(cues: list[dict]) -> str:
    """Render danh sách cue [{start,end,text}] thành chuỗi .srt (UTF-8, LF)."""
    lines = []
    for idx, c in enumerate(cues, 1):
        lines.append(str(idx))
        lines.append(f"{_fmt_srt_time(c['start'])} --> {_fmt_srt_time(c['end'])}")
        lines.append((c.get("text") or "").strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _atomize(segments: list[dict], atom_max: float) -> list[dict]:
    """Băm các câu thành 'atom' mịn (mỗi atom ≲ atom_max giây) để có nhiều điểm
    cắt cho bước ghép tối ưu. Câu dài được tách tại dấu phẩy/liên từ (mốc thời
    gian nội suy theo tỉ lệ ký tự — xem _split_long_segment)."""
    atoms: list[dict] = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        atoms.extend(_split_long_segment(
            text, float(seg.get("start", 0.0)),
            float(seg.get("end", 0.0)), atom_max))
    return atoms


def _dp_partition(atoms: list[dict], target: float,
                  min_dur: float, max_dur: float) -> list[dict]:
    """Ghép các atom liên tiếp thành block sao cho TỔNG 'độ lệch so với target'
    là NHỎ NHẤT trên TOÀN BỘ chuỗi (quy hoạch động), với ràng buộc mỗi block
    nằm trong [min_dur, max_dur] giây. Đây là chìa khóa để KHÔNG còn block quá
    ngắn (<min_dur) hay quá dài (>max_dur) — điều mà cách 'gom tham lam' không
    đảm bảo được vì hay để lại block 'mồ côi' ở ranh giới.
    """
    n = len(atoms)
    if n == 0:
        return []
    INF = float("inf")
    best = [INF] * (n + 1)   # best[i] = tổng phạt tối ưu cho atoms[i:]
    nxt = [-1] * (n + 1)
    best[n] = 0.0
    for i in range(n - 1, -1, -1):
        j = i + 1
        while j <= n:
            d = atoms[j - 1]["end"] - atoms[i]["start"]
            single = (j == i + 1)
            # Vượt trần & không phải atom đơn lẻ → dừng mở rộng block này.
            if d > max_dur and not single:
                break
            if d > max_dur:
                pen = (d - target) ** 2 + 800.0      # atom đơn quá dài (hiếm): cho phép, phạt nặng
            elif d < min_dur:
                # block ngắn (<min): phạt rất nặng + KÈM lệch target để khi 'Mỗi cảnh' đặt
                # lớn, block ngắn luôn ĐẮT hơn mọi phương án gộp hợp lệ (DP ưu tiên gộp).
                pen = (d - target) ** 2 + (min_dur - d) ** 2 * 40.0 + 300.0
            else:
                pen = (d - target) ** 2
            if best[j] + pen < best[i]:
                best[i] = best[j] + pen
                nxt[i] = j
            j += 1
    cues: list[dict] = []
    i = 0
    while i < n and nxt[i] != -1:
        j = nxt[i]
        cues.append({
            "start": atoms[i]["start"],
            "end": atoms[j - 1]["end"],
            "text": _join_texts([a["text"] for a in atoms[i:j]]),
        })
        i = j
    return cues


def build_srt(segments: list[dict], target_dur: float = 8.0,
              min_dur: float = 4.0, max_dur: float = 10.0) -> str:
    """Dựng .srt với MỖI BLOCK NẰM TRONG [min_dur, max_dur] giây, độ dài tiệm
    cận target_dur — phục vụ chia cảnh cho công cụ tạo video/ảnh (vd Veo3, mỗi
    clip ≤ ~10s, không nên < 4s).

    Cách làm: BĂM câu thành atom mịn (tách câu dài tại dấu phẩy/liên từ) rồi
    GHÉP tối ưu (quy hoạch động) để gộp các câu ngắn liền nhau — loại bỏ block
    quá ngắn mà vẫn không vượt giới hạn trên.
    """
    cues = build_cues(segments, target_dur, min_dur, max_dur)
    return _render_srt(cues)


def build_cues(segments: list[dict], target_dur: float = 8.0,
               min_dur: float = 4.0, max_dur: float = 10.0) -> list[dict]:
    """Như build_srt nhưng trả về DANH SÁCH cue [{start,end,text}] thay vì chuỗi
    .srt — để bên gọi tái sử dụng (vd ghép thêm prompt, hoặc dùng cho AI)."""
    if min_dur > max_dur:
        min_dur = max_dur
    target_dur = max(min_dur, min(target_dur, max_dur))
    # Atom đủ mịn để DP có nhiều lựa chọn cắt, nhưng không quá vụn.
    atom_max = max(min_dur, min(target_dur, max_dur * 0.6))
    atoms = _atomize(segments, atom_max)
    return _dp_partition(atoms, target_dur, min_dur, max_dur)


def cues_from_ai_groups(segments: list[dict], groups: list[list[int]],
                        target_dur: float = 8.0, min_dur: float = 4.0,
                        max_dur: float = 10.0) -> list[dict]:
    """Dựng cue từ cách NHÓM CÂU do AI đề xuất, NHƯNG vẫn ÉP CỨNG ràng buộc thời
    lượng [min_dur, max_dur] — AI chỉ gợi ý ranh giới theo ý nghĩa, không được
    phá luật về độ dài.

    - `groups`: danh sách nhóm, mỗi nhóm là danh sách CHỈ SỐ câu (0-based) trong
      `segments`, theo thứ tự. Vd [[0,1],[2],[3,4,5]].
    - Mốc thời gian LẤY TỪ AUDIO THẬT (segments), không để AI bịa.
    - Hậu xử lý: nhóm quá dài (>max_dur) → tách lại bằng DP; nhóm quá ngắn
      (<min_dur) → gộp với hàng xóm ngắn hơn nếu tổng vẫn ≤ max_dur.

    Trả về None nếu groups không hợp lệ (thiếu/sai chỉ số) để bên gọi fallback.
    """
    n = len(segments)
    if not groups:
        return None
    # Kiểm tra: phải phủ ĐỦ và ĐÚNG mọi chỉ số 0..n-1, không trùng, không thiếu.
    flat = [i for g in groups for i in g]
    if sorted(flat) != list(range(n)):
        return None
    # Phải liên tục tăng dần trong từng nhóm và giữa các nhóm (không đảo câu).
    if flat != list(range(n)):
        return None

    # B1: dựng cue thô theo nhóm (mốc thời gian từ segments thật).
    raw = []
    for g in groups:
        if not g:
            continue
        s = segments[g[0]]["start"]
        e = segments[g[-1]]["end"]
        txt = _join_texts([(segments[i].get("text") or "") for i in g])
        raw.append({"start": float(s), "end": float(e), "text": txt,
                    "idx": list(g)})

    # B2: nhóm nào > max_dur → tách lại bằng DP trên các câu con của nhóm đó.
    fixed = []
    for c in raw:
        if (c["end"] - c["start"]) <= max_dur:
            fixed.append({"start": c["start"], "end": c["end"], "text": c["text"]})
            continue
        sub = [segments[i] for i in c["idx"]]
        fixed.extend(build_cues(sub, target_dur, min_dur, max_dur))

    # B3: nhóm nào < min_dur → gộp với hàng xóm NGẮN hơn (nếu tổng ≤ max_dur),
    # lặp đến ổn định để không còn block quá ngắn ở ranh giới.
    changed = True
    while changed and len(fixed) > 1:
        changed = False
        for j in range(len(fixed)):
            if (fixed[j]["end"] - fixed[j]["start"]) >= min_dur:
                continue
            prev_r = (fixed[j]["end"] - fixed[j - 1]["start"]) if j > 0 else None
            next_r = (fixed[j + 1]["end"] - fixed[j]["start"]) if j + 1 < len(fixed) else None
            cand = []
            if prev_r is not None and prev_r <= max_dur:
                cand.append(("prev", prev_r))
            if next_r is not None and next_r <= max_dur:
                cand.append(("next", next_r))
            if not cand:
                continue
            w, _ = min(cand, key=lambda x: x[1])
            if w == "prev":
                fixed[j - 1]["text"] = _join_texts([fixed[j - 1]["text"], fixed[j]["text"]])
                fixed[j - 1]["end"] = fixed[j]["end"]
                del fixed[j]
            else:
                fixed[j]["text"] = _join_texts([fixed[j]["text"], fixed[j + 1]["text"]])
                fixed[j]["end"] = fixed[j + 1]["end"]
                del fixed[j + 1]
            changed = True
            break
    return fixed


def _split_sentences(text: str, lang: str | None = None) -> list[str]:
    """Tách văn bản thành các câu để chèn ngắt nghỉ giữa chúng.

    Tách theo dấu kết câu (. ! ? … 。！？) và xuống dòng. Giữ nguyên dấu câu.

    - Chữ Latin (vi/en...): dấu kết câu PHẢI có khoảng trắng theo sau (để không phá
      số thập phân "3.14" hay viết tắt "Mr.").
    - Chữ CJK (Nhật/Trung/Hàn): dấu 。！？ KHÔNG bao giờ có khoảng trắng theo sau →
      tách ngay sau dấu (nếu không cả đoạn thành 1 "câu" → 1 cảnh dài cả file).
    """
    out: list[str] = []
    for line in text.replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        if _is_cjk(line, lang):
            chunks = _split_cjk_sentences(line)
        else:
            chunks = re.split(r"(?<=[\.\!\?…。！？])\s+", line)
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk:
                out.append(chunk)
    return out


def _reduce_breath(audio: np.ndarray, sr: int, strength: float) -> np.ndarray:
    """Giảm tiếng thở / tạp âm nền bằng 'downward expander'.

    Ý tưởng: tiếng thở luôn nhỏ hơn giọng nói nhiều dB. Ta đo âm lượng theo
    từng khung ngắn; khung nào thấp hơn đỉnh giọng quá ngưỡng thì hạ âm lượng
    (càng thấp hạ càng nhiều), còn phần giọng nói giữ nguyên. strength 0..1.
    """
    if strength <= 0:
        return audio
    x = np.asarray(audio, dtype=np.float32)
    n = x.size
    if n < sr // 10:  # quá ngắn → bỏ qua
        return x

    win = max(1, int(0.025 * sr))   # khung 25ms
    hop = max(1, int(0.010 * sr))   # bước 10ms
    nf = 1 + max(0, (n - win)) // hop

    # RMS theo khung (vectorized bằng cumsum bình phương)
    xs = x * x
    csum = np.concatenate(([0.0], np.cumsum(xs, dtype=np.float64)))
    starts = np.arange(nf) * hop
    ends = np.minimum(starts + win, n)
    env = np.sqrt((csum[ends] - csum[starts]) / np.maximum(ends - starts, 1) + 1e-12)
    env_db = 20.0 * np.log10(env + 1e-9)

    peak_db = float(np.percentile(env_db, 95))   # mức giọng nói
    # Ngưỡng tiến gần đỉnh hơn khi strength cao → bắt cả tiếng thở chỉ nhỏ
    # hơn giọng ~8-16 dB (thường gặp). strength 0→ -16dB, 1→ -9dB.
    thr = peak_db - (16.0 - 7.0 * strength)
    ratio = 1.0 + 6.0 * strength                  # expand mạnh hơn, tối đa ~7:1
    max_red = -(12.0 + 28.0 * strength)           # hạ tối đa tới ~ -40 dB

    gain_db = np.where(env_db < thr, (env_db - thr) * (ratio - 1.0), 0.0)
    gain_db = np.maximum(gain_db, max_red)
    gain = np.power(10.0, gain_db / 20.0).astype(np.float32)

    # Làm mượt gain BẤT ĐỐI XỨNG: hạ nhanh khi gặp tiếng thở (attack nhanh),
    # phục hồi chậm khi vào lại giọng nói (release chậm) → vừa dập được tiếng
    # thở ngắn, vừa không gây 'pumping'/zipper khi bắt đầu nói.
    sm = np.empty_like(gain)
    g = 1.0
    a_attack = 0.85   # gain giảm → bám gần như tức thì
    a_release = 0.12  # gain tăng → mở lại từ từ
    for i in range(gain.size):
        target = gain[i]
        a = a_attack if target < g else a_release
        g = a * target + (1.0 - a) * g
        sm[i] = g

    # Nội suy gain lên độ phân giải mẫu rồi áp vào tín hiệu
    centers = starts + win / 2.0
    gain_full = np.interp(np.arange(n), centers, sm,
                          left=sm[0], right=sm[-1]).astype(np.float32)
    return x * gain_full


def _frame_env_db(x: np.ndarray, sr: int, win_s: float = 0.02, hop_s: float = 0.01):
    """Trả về (env_db theo khung, starts mẫu, win) — RMS theo khung tính nhanh bằng
    cumsum bình phương. Dùng chung cho trim im lặng."""
    n = x.size
    win = max(1, int(win_s * sr))
    hop = max(1, int(hop_s * sr))
    nf = 1 + max(0, (n - win)) // hop
    xs = x.astype(np.float64) ** 2
    csum = np.concatenate(([0.0], np.cumsum(xs)))
    starts = np.arange(nf) * hop
    ends = np.minimum(starts + win, n)
    env = np.sqrt((csum[ends] - csum[starts]) / np.maximum(ends - starts, 1) + 1e-12)
    return 20.0 * np.log10(env + 1e-9), starts, win


def _trim_silence(audio: np.ndarray, sr: int, rel_db: float = -45.0,
                  pad_ms: float = 60.0):
    """Cắt khoảng LẶNG thừa ở ĐẦU và CUỐI toàn bộ audio (không đụng lặng giữa câu).

    rel_db: ngưỡng tính là "lặng" = thấp hơn đỉnh giọng rel_db dB.
    pad_ms: chừa lại một ít đệm để không cắt cụt phụ âm đầu/cuối.
    Trả về (audio_đã_cắt, số_mẫu_cắt_đầu, số_mẫu_cắt_cuối).
    """
    x = np.asarray(audio, dtype=np.float32)
    n = x.size
    if n < sr // 5:                       # quá ngắn → bỏ qua
        return x, 0, 0
    env_db, starts, win = _frame_env_db(x, sr)
    peak_db = float(np.max(env_db))
    thr = peak_db + rel_db
    voiced = np.where(env_db > thr)[0]
    if voiced.size == 0:
        return x, 0, 0
    pad = int(pad_ms / 1000.0 * sr)
    lead = max(0, int(starts[voiced[0]]) - pad)
    last_end = int(starts[voiced[-1]]) + win
    tail = max(0, n - min(n, last_end + pad))
    if lead == 0 and tail == 0:
        return x, 0, 0
    return np.ascontiguousarray(x[lead:n - tail]), lead, tail


def _measure_lufs(audio: np.ndarray, sr: int):
    """Đo độ to tích hợp (LUFS, chuẩn ITU-R BS.1770) bằng pyloudnorm nếu có.
    Trả về None nếu không có thư viện hoặc audio quá ngắn để đo."""
    try:
        import pyloudnorm as pyln
    except Exception:
        return None
    x = np.asarray(audio, dtype=np.float64)
    if x.size < int(0.4 * sr):            # ngắn hơn 1 block 400ms → không đo được
        return None
    try:
        val = float(pyln.Meter(sr).integrated_loudness(x))
        return val if np.isfinite(val) else None
    except Exception:
        return None


def _normalize_loudness(audio: np.ndarray, sr: int, target_lufs: float = -16.0,
                        peak_db: float = -1.0) -> np.ndarray:
    """Kéo độ to về mức chuẩn để MỌI file ra cùng âm lượng, kèm giới hạn đỉnh
    (peak_db, dBFS) chống vỡ tiếng (clip).

    Ưu tiên LUFS (pyloudnorm); không có thư viện / audio quá ngắn → fallback RMS.
    """
    x = np.asarray(audio, dtype=np.float32)
    if x.size == 0:
        return x
    lufs = _measure_lufs(x, sr)
    if lufs is not None:
        gain_db = target_lufs - lufs
    else:
        rms = float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))
        if rms < 1e-7:
            return x
        gain_db = target_lufs - 20.0 * np.log10(rms)   # xấp xỉ: coi target ~ RMS dBFS
    # Chặn gain bất thường (vd audio gần như im lặng → tránh khuếch đại nhiễu lên cực to).
    gain_db = max(-30.0, min(30.0, gain_db))
    y = x * (10.0 ** (gain_db / 20.0))
    ceiling = 10.0 ** (peak_db / 20.0)
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    if peak > ceiling and peak > 0:
        y = y * (ceiling / peak)
    return y.astype(np.float32)


def _apply_fade(audio: np.ndarray, sr: int, fade_ms: float) -> np.ndarray:
    """Fade in/out ở 2 đầu để tránh tiếng 'tách/click' khi bắt đầu/kết thúc hoặc
    khi nối các đoạn lại với nhau. Không đổi độ dài."""
    if fade_ms <= 0:
        return audio
    x = np.asarray(audio, dtype=np.float32)
    f = int(fade_ms / 1000.0 * sr)
    if f <= 0 or x.size < 2 * f:
        return x
    x = x.copy()
    ramp = np.linspace(0.0, 1.0, f, dtype=np.float32)
    x[:f] *= ramp
    x[-f:] *= ramp[::-1]
    return x


def _finalize_audio(audio, sr, segments, target_lufs, trim_silence, fade_ms):
    """Hậu kỳ chung cuối generate(): cắt lặng đầu/cuối (dời mốc thời gian SRT theo),
    chuẩn hóa độ to, rồi fade 2 đầu. Trả về (audio, segments)."""
    if trim_silence:
        audio, lead, _tail = _trim_silence(audio, sr)
        if segments:
            shift = lead / sr
            new_dur = len(audio) / sr
            for s in segments:
                s["start"] = max(0.0, s["start"] - shift)
                s["end"] = min(new_dur, max(s["start"], s["end"] - shift))
    if target_lufs is not None:
        audio = _normalize_loudness(audio, sr, target_lufs)
    if fade_ms and fade_ms > 0:
        audio = _apply_fade(audio, sr, fade_ms)
    return audio, segments


def _load_wav_mono(path: str, max_seconds: float | None = None):
    """Đọc file audio thành (sóng 1-D float32, sample_rate), KHÔNG cần ffmpeg.

    Dùng soundfile (WAV/FLAC/OGG/MP3...), nếu lỗi thì dùng librosa.
    Tự gộp về mono và (tùy chọn) cắt còn `max_seconds` giây đầu.
    Trả về (waveform, sr) dạng tuple để truyền cho model — tránh phụ thuộc ffmpeg.
    """
    try:
        import soundfile as sf
        data, sr = sf.read(path, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
    except Exception:
        import librosa
        data, sr = librosa.load(path, sr=None, mono=True)
        data = np.asarray(data, dtype=np.float32)

    sr = int(sr)
    if max_seconds and data.shape[0] > int(max_seconds * sr):
        data = data[: int(max_seconds * sr)]
    return np.ascontiguousarray(data), sr


class VoiceEngine:
    def __init__(self):
        self.model = None
        self.device = "cpu"
        self.sample_rate = 24000

    @property
    def ready(self) -> bool:
        return self.model is not None

    # ------------------------------------------------------------------ load
    def load(self, log=lambda m: None):
        # Hướng HuggingFace tải model vào ./models/hf-cache (lần đầu, nếu chưa có sẵn)
        config.setup_hf_cache_env()

        import torch
        from omnivoice import OmniVoice

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if self.device == "cuda" else torch.float32

        model_path, _tok_path, is_local = config.resolve_model_dir()
        asr_path, asr_local = config.resolve_asr_dir()

        # Model có thể đã nằm trong cache HuggingFace (tải từ lần trước) dù KHÔNG
        # ở các thư mục local cố định. Coi như "có sẵn" để không báo nhầm "đang tải".
        model_ready = is_local or config.hf_cache_has(config.HF_MODEL_ID)
        asr_ready = asr_local or config.hf_cache_has(config.HF_ASR_ID)

        log(f"Thiết bị: {self.device.upper()}"
            + (f" ({torch.cuda.get_device_name(0)})" if self.device == "cuda" else ""))
        if self.device != "cuda":
            log("⚠ Không thấy GPU NVIDIA — sẽ chạy bằng CPU và RẤT chậm.")
        if not (model_ready and asr_ready):
            log("Lần đầu chạy: đang TẢI MODEL (~4.7GB) về thư mục ./models — có thể mất vài phút...")
        log(f"Model OmniVoice: {'(có sẵn) ' if model_ready else '(tải về) '}{model_path}")
        log(f"Model ASR Whisper: {'(có sẵn) ' if asr_ready else '(tải về) '}{asr_path}")
        log("Đang nạp model, vui lòng đợi...")

        # audio_tokenizer được tự nạp từ <model_path>/audio_tokenizer.
        # load_asr=True nạp luôn Whisper để tự nhận diện lời thoại audio mẫu.
        self.model = OmniVoice.from_pretrained(
            model_path,
            device_map=self.device,
            dtype=dtype,
            load_asr=True,
            asr_model_name=asr_path,
        )
        self.model.eval()
        self.sample_rate = getattr(self.model, "sampling_rate", 24000) or 24000

        if self.device == "cuda":
            used = torch.cuda.memory_allocated() / 1e9
            log(f"✅ Đã nạp xong. VRAM đang dùng: {used:.2f} GB")
        else:
            log("✅ Đã nạp xong (chạy bằng CPU — sẽ chậm).")

    # -------------------------------------------------------------- transcribe
    def transcribe(self, ref_audio: str) -> str:
        """Nhận diện lời thoại trong file audio mẫu bằng Whisper."""
        if not self.ready:
            raise RuntimeError("Model chưa được nạp.")
        wav, sr = _load_wav_mono(ref_audio, max_seconds=REF_MAX_SECONDS)
        text = self.model.transcribe((wav, sr))
        return (text or "").strip()

    # ----------------------------------------------------------- voice profile
    def create_profile(self, ref_audio: str, ref_text: str | None):
        """Tạo 'voice clone prompt' từ audio mẫu — có thể lưu lại tái sử dụng."""
        if not self.ready:
            raise RuntimeError("Model chưa được nạp.")
        wav, sr = _load_wav_mono(ref_audio)
        # Audio mẫu quá dài → tự cắt còn REF_MAX_SECONDS. Nếu người dùng có nhập ref_text
        # (cho CẢ file dài) thì text đó KHÔNG còn khớp đoạn đã cắt → BỎ ref_text để Whisper
        # tự nhận diện đúng đoạn 20s (tránh cặp audio/text lệch làm giọng clone kém).
        if wav.shape[0] > int(REF_MAX_SECONDS * sr):
            wav = np.ascontiguousarray(wav[: int(REF_MAX_SECONDS * sr)])
            ref_text = None
        return self.model.create_voice_clone_prompt(ref_audio=(wav, sr), ref_text=ref_text)

    # -------------------------------------------------------------- generate
    def generate(
        self,
        text: str,
        language: str | None = None,
        speed: float = 1.0,
        num_step: int = 32,
        pause_sec: float = 0.0,
        guidance_scale: float = 2.0,
        breath_reduce: float = 0.0,
        normalize: bool = False,
        target_lufs: float | None = None,
        trim_silence: bool = False,
        fade_ms: float = 0.0,
        voice_clone_prompt=None,
        ref_audio: str | None = None,
        ref_text: str | None = None,
        instruct: str | None = None,
        progress=None,
        with_segments: bool = False,
    ):
        """Sinh audio. Trả về (sr, audio); nếu with_segments=True trả thêm danh sách
        đoạn [{"text", "start", "end"}] (giây) để xuất phụ đề SRT khớp từng câu.

        Hậu kỳ (tùy chọn): normalize=True đọc số/ngày/tiền thành chữ trước khi sinh;
        target_lufs chuẩn hóa độ to; trim_silence cắt lặng đầu/cuối; fade_ms fade 2 đầu.
        """
        if not self.ready:
            raise RuntimeError("Model chưa được nạp.")

        # Tiền xử lý: đọc số/ngày/tiền/% thành chữ để model phát âm đúng (tùy chọn).
        if normalize:
            text = text_norm.normalize_text(text, language)

        def _report(done, total):
            if progress:
                try:
                    progress(done, total)
                except Exception:
                    pass

        # Tham số chung cho mọi câu (trừ chính nội dung `text`)
        base = dict(num_step=int(num_step))
        if language:
            base["language"] = language
        if speed and abs(speed - 1.0) > 1e-3:
            base["speed"] = float(speed)
        # guidance_scale cao hơn = bám theo giọng mẫu sát hơn (giống hơn) nhưng
        # quá cao dễ cứng/méo. Mặc định model là 2.0.
        if guidance_scale and abs(guidance_scale - 2.0) > 1e-3:
            base["guidance_scale"] = float(guidance_scale)

        if voice_clone_prompt is not None:
            base["voice_clone_prompt"] = voice_clone_prompt
        elif ref_audio:
            # Tự dựng prompt từ audio mẫu (qua _load_wav_mono) để tránh ffmpeg.
            base["voice_clone_prompt"] = self.create_profile(ref_audio, ref_text or None)
        elif instruct:
            base["instruct"] = instruct

        # Tách câu để (a) báo tiến độ % theo từng câu, (b) chèn ngắt nghỉ nếu cần.
        # Có nhiều câu → đọc từng câu rồi nối; chỉ chèn khoảng lặng khi pause_sec > 0.
        sr = self.sample_rate
        sentences = _split_sentences(text, language)
        if len(sentences) > 1:
            total = len(sentences)
            gap_n = int(pause_sec * sr) if pause_sec and pause_sec > 0 else 0
            gap = np.zeros(gap_n, dtype=np.float32) if gap_n else None
            pieces: list[np.ndarray] = []
            segments: list[dict] = []
            cur = 0  # vị trí mẫu hiện tại trong audio tổng
            _report(0, total)
            for i, sent in enumerate(sentences):
                audios = self.model.generate(text=sent, **base)
                piece = np.asarray(audios[0], dtype=np.float32)
                piece = _reduce_breath(piece, self.sample_rate, breath_reduce)
                # Fade nhẹ 2 đầu mỗi đoạn để điểm nối câu không nghe tiếng 'tách'.
                if fade_ms and fade_ms > 0:
                    piece = _apply_fade(piece, self.sample_rate, min(8.0, fade_ms))
                if i and gap is not None:
                    pieces.append(gap)
                    cur += gap_n
                start = cur
                pieces.append(piece)
                cur += len(piece)
                segments.append({"text": sent, "start": start / sr, "end": cur / sr})
                _report(i + 1, total)   # đã xong câu thứ (i+1)/total
            audio = np.concatenate(pieces)
            audio, segments = _finalize_audio(
                audio, sr, segments, target_lufs, trim_silence, fade_ms)
            return (sr, audio, segments) if with_segments else (sr, audio)

        # Một câu duy nhất: không biết % giữa chừng → báo 0% rồi 100% khi xong.
        _report(0, 1)
        audios = self.model.generate(text=text.strip(), **base)
        audio = np.asarray(audios[0], dtype=np.float32)
        audio = _reduce_breath(audio, self.sample_rate, breath_reduce)
        seg = ([{"text": text.strip(), "start": 0.0, "end": len(audio) / sr}]
               if with_segments else None)
        audio, seg = _finalize_audio(
            audio, sr, seg, target_lufs, trim_silence, fade_ms)
        _report(1, 1)
        if with_segments:
            return sr, audio, seg
        return sr, audio
