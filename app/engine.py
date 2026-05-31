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


def _chunk_by_words(text: str, max_words: int) -> list[list[str]]:
    """Cắt câu thành các cụm ngắn ≤ max_words từ, độ dài các cụm cân đối nhau.

    VD 11 từ, max=8 → 2 dòng [6, 5] (cân đối) thay vì [8, 3] (lệch).
    """
    import math
    words = text.split()
    if not words:
        return []
    n = len(words)
    max_words = max(1, int(max_words))
    nlines = max(1, math.ceil(n / max_words))
    per = math.ceil(n / nlines)
    return [words[i:i + per] for i in range(0, n, per)]


def segments_to_srt(segments: list[dict], max_words: int = 8) -> str:
    """Dựng nội dung .srt từ danh sách câu [{text,start,end}].

    Mỗi câu được cắt thành các dòng ngắn ≤ max_words từ (cho khớp phần mềm
    dựng video). Thời gian của câu được chia cho các dòng theo TỈ LỆ số từ.
    """
    lines = []
    idx = 1
    for seg in segments:
        text = (seg.get("text") or "").strip()
        chunks = _chunk_by_words(text, max_words)
        if not chunks:
            continue
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        dur = max(0.0, end - start)
        total_words = sum(len(c) for c in chunks)
        t = start
        for k, c in enumerate(chunks):
            w = len(c)
            seg_dur = (dur * w / total_words) if total_words else dur
            cs = t
            ce = end if k == len(chunks) - 1 else t + seg_dur  # dòng cuối khớp đúng end
            t = ce
            lines.append(str(idx)); idx += 1
            lines.append(f"{_fmt_srt_time(cs)} --> {_fmt_srt_time(ce)}")
            lines.append(" ".join(c))
            lines.append("")  # dòng trống ngăn cách
    return "\n".join(lines).strip() + "\n"


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
