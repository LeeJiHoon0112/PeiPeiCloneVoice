"""Lớp bọc model OmniVoice: nạp model, nhận diện giọng (Whisper), tạo voice profile và sinh audio.

Đây là phần lõi clone giọng — dùng model mã nguồn mở OmniVoice (Apache-2.0, k2-fsa/OmniVoice).
"""
import re

import numpy as np

from . import config


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


def _split_points(text: str) -> list[int]:
    """Tìm các vị trí (chỉ số ký tự) tốt để tách 1 câu dài.

    Ưu tiên: sau dấu phẩy/chấm phẩy/gạch ngang → rồi tới trước liên từ.
    Trả về danh sách vị trí cắt (sau khoảng trắng), đã sắp xếp.
    """
    points = set()
    # 1) sau các dấu ngắt giữa câu
    for m in re.finditer(r"[,;:—–]\s+", text):
        points.add(m.end())
    # 2) trước các liên từ (đứng giữa câu, có khoảng trắng 2 bên)
    low = text.lower()
    for conj in _SPLIT_CONJUNCTIONS:
        for m in re.finditer(r"\s+" + re.escape(conj) + r"\s+", low):
            points.add(m.start() + 1)  # cắt ngay trước liên từ (giữ liên từ ở vế sau)
    return sorted(p for p in points if 0 < p < len(text))


def _word_chunks(text: str, nparts: int) -> list[str]:
    """Chia đều text theo TỪ thành nparts mảnh (dự phòng khi không có dấu/liên từ)."""
    import math
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

    # An toàn TUYỆT ĐỐI: mảnh nào vẫn > max_chars (vd 1 vế dài, không dấu) → cắt theo từ
    safe: list[str] = []
    for p in pieces:
        if len(p) > max_chars and len(p.split()) > 1:
            sub = max(2, math.ceil(len(p) / max_chars))
            safe.extend(_word_chunks(p, sub))
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
    if dur <= max_dur or len(text.split()) <= 1:
        return [{"text": text, "start": start, "end": end}]

    # Số ký tự tương ứng max_dur giây (theo tốc độ đọc thật của câu này)
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
                pen = (min_dur - d) ** 2 * 40.0 + 300.0  # block ngắn: phạt rất nặng để né
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
            "text": " ".join(a["text"] for a in atoms[i:j]).strip(),
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
        txt = " ".join((segments[i].get("text") or "").strip() for i in g).strip()
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
                fixed[j - 1]["text"] = (fixed[j - 1]["text"] + " " + fixed[j]["text"]).strip()
                fixed[j - 1]["end"] = fixed[j]["end"]
                del fixed[j]
            else:
                fixed[j]["text"] = (fixed[j]["text"] + " " + fixed[j + 1]["text"]).strip()
                fixed[j]["end"] = fixed[j + 1]["end"]
                del fixed[j + 1]
            changed = True
            break
    return fixed


def _split_sentences(text: str) -> list[str]:
    """Tách văn bản thành các câu để chèn ngắt nghỉ giữa chúng.

    Tách theo dấu kết câu (. ! ? … 。！？) và xuống dòng. Giữ nguyên dấu câu.
    """
    out: list[str] = []
    for line in text.replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        for chunk in re.split(r"(?<=[\.\!\?…。！？])\s+", line):
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

        log(f"Thiết bị: {self.device.upper()}"
            + (f" ({torch.cuda.get_device_name(0)})" if self.device == "cuda" else ""))
        if self.device != "cuda":
            log("⚠ Không thấy GPU NVIDIA — sẽ chạy bằng CPU và RẤT chậm.")
        if not (is_local and asr_local):
            log("Lần đầu chạy: đang TẢI MODEL (~4.7GB) về thư mục ./models — có thể mất vài phút...")
        log(f"Model OmniVoice: {'(có sẵn) ' if is_local else '(tải về) '}{model_path}")
        log(f"Model ASR Whisper: {'(có sẵn) ' if asr_local else '(tải về) '}{asr_path}")
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
        wav, sr = _load_wav_mono(ref_audio, max_seconds=REF_MAX_SECONDS)
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
        voice_clone_prompt=None,
        ref_audio: str | None = None,
        ref_text: str | None = None,
        instruct: str | None = None,
        progress=None,
        with_segments: bool = False,
    ):
        """Sinh audio. Trả về (sr, audio); nếu with_segments=True trả thêm danh sách
        đoạn [{"text", "start", "end"}] (giây) để xuất phụ đề SRT khớp từng câu.
        """
        if not self.ready:
            raise RuntimeError("Model chưa được nạp.")

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
        sentences = _split_sentences(text)
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
                if i and gap is not None:
                    pieces.append(gap)
                    cur += gap_n
                start = cur
                pieces.append(piece)
                cur += len(piece)
                segments.append({"text": sent, "start": start / sr, "end": cur / sr})
                _report(i + 1, total)   # đã xong câu thứ (i+1)/total
            audio = np.concatenate(pieces)
            return (sr, audio, segments) if with_segments else (sr, audio)

        # Một câu duy nhất: không biết % giữa chừng → báo 0% rồi 100% khi xong.
        _report(0, 1)
        audios = self.model.generate(text=text.strip(), **base)
        audio = np.asarray(audios[0], dtype=np.float32)
        audio = _reduce_breath(audio, self.sample_rate, breath_reduce)
        _report(1, 1)
        if with_segments:
            seg = [{"text": text.strip(), "start": 0.0, "end": len(audio) / sr}]
            return sr, audio, seg
        return sr, audio
