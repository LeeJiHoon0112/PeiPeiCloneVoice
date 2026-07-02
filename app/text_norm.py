"""Tiền xử lý văn bản trước khi đưa vào model: đọc SỐ / NGÀY / TIỀN / % / viết tắt
thành CHỮ để model phát âm đúng.

Vì sao cần: kịch bản YouTube đầy số liệu, ngày tháng, tiền tệ. Model đọc số "thô"
hay sai hoặc ngập ngừng (vd "1234", "50.000đ", "13/06/2026"). Đọc đúng thành chữ
ngay từ đầu giúp voice-over chuẩn mà không phải sửa tay rồi sinh lại.

Hỗ trợ 2 ngôn ngữ: Tiếng Việt ("vi") và English ("en"). Nếu không truyền language
thì tự đoán theo dấu tiếng Việt. Quy ước dấu phân cách KHÁC nhau theo ngôn ngữ:
  - vi: dấu '.' là phân cách hàng nghìn, ',' là dấu thập phân  → 1.234,5
  - en: dấu ',' là phân cách hàng nghìn, '.' là dấu thập phân  → 1,234.5

Thiết kế an toàn: chỗ nào không chắc (token số kỳ lạ) thì GIỮ NGUYÊN, không bịa.
"""
import re

# --------------------------------------------------------------- nhận diện ngôn ngữ
# Các ký tự CHỈ tiếng Việt mới có (đủ để phân biệt với English).
_VI_CHARS = "ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
_VI_RE = re.compile("[" + _VI_CHARS + "]")


def _detect_lang(text: str) -> str:
    return "vi" if _VI_RE.search(text or "") else "en"


# ------------------------------------------------------------- đọc số: Tiếng Việt
_VI_DIGITS = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
_VI_SCALE = ["", "nghìn", "triệu", "tỉ"]


def _vi_three(n: int, full: bool) -> str:
    """Đọc số 0..999. full=True: luôn đọc hàng trăm (kể cả 0 → 'không trăm')."""
    tr, ch, dv = n // 100, (n % 100) // 10, n % 10
    parts = []
    if tr > 0 or full:
        parts.append(_VI_DIGITS[tr] + " trăm")
    if ch == 0:
        if dv > 0 and (tr > 0 or full):
            parts.append("lẻ " + _VI_DIGITS[dv])     # "một trăm lẻ năm"
        elif dv > 0:
            parts.append(_VI_DIGITS[dv])
    elif ch == 1:
        parts.append("mười")
        if dv == 5:
            parts.append("lăm")                       # "mười lăm"
        elif dv > 0:
            parts.append(_VI_DIGITS[dv])              # "mười một".."mười chín"
    else:
        parts.append(_VI_DIGITS[ch] + " mươi")
        if dv == 1:
            parts.append("mốt")                       # "hai mươi mốt"
        elif dv == 4:
            parts.append("tư")                        # "hai mươi tư"
        elif dv == 5:
            parts.append("lăm")                       # "hai mươi lăm"
        elif dv > 0:
            parts.append(_VI_DIGITS[dv])
    return " ".join(parts)


def _vi_scale_word(pos: int) -> str:
    """Từ chỉ bậc theo nhóm 3 chữ số: 1=nghìn, 2=triệu, 3=tỉ, 4=nghìn tỉ, ..."""
    if pos < 4:
        return _VI_SCALE[pos]
    # pos>=4: ghép "tỉ" lặp. 4→nghìn tỉ, 5→triệu tỉ, 6→tỉ tỉ, 7→nghìn tỉ tỉ...
    head = _VI_SCALE[pos % 3]
    tail = " ".join(["tỉ"] * (pos // 3))
    return (head + " " + tail).strip()


def _vi_int(n: int) -> str:
    if n == 0:
        return "không"
    neg = n < 0
    n = abs(n)
    groups = []
    while n > 0:
        groups.append(n % 1000)
        n //= 1000
    groups.reverse()
    L = len(groups)
    out = []
    for i, g in enumerate(groups):
        if g == 0:
            continue
        words = _vi_three(g, full=(i > 0))   # nhóm sau nhóm cao nhất → đọc đủ trăm
        pos = L - 1 - i
        if pos > 0:
            words = (words + " " + _vi_scale_word(pos)).strip()
        out.append(words)
    res = " ".join(out)
    return ("âm " + res) if neg else res


# ------------------------------------------------------------------- đọc số: English
_EN_UNDER20 = ["zero", "one", "two", "three", "four", "five", "six", "seven",
               "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
               "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_EN_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
            "eighty", "ninety"]
_EN_SCALE = ["", "thousand", "million", "billion", "trillion", "quadrillion",
             "quintillion"]


def _en_below_1000(n: int) -> str:
    parts = []
    if n >= 100:
        parts.append(_EN_UNDER20[n // 100] + " hundred")
        n %= 100
    if n >= 20:
        t = _EN_TENS[n // 10]
        if n % 10:
            t += "-" + _EN_UNDER20[n % 10]
        parts.append(t)
    elif n > 0:
        parts.append(_EN_UNDER20[n])
    return " ".join(parts)


def _en_int(n: int) -> str:
    if n == 0:
        return "zero"
    neg = n < 0
    n = abs(n)
    groups = []
    while n > 0:
        groups.append(n % 1000)
        n //= 1000
    out = []
    for i in range(len(groups) - 1, -1, -1):
        g = groups[i]
        if g == 0:
            continue
        seg = _en_below_1000(g)
        if 0 < i < len(_EN_SCALE):
            seg += " " + _EN_SCALE[i]
        out.append(seg)
    res = " ".join(out)
    return ("negative " + res) if neg else res


def _read_int(n: int, lang: str) -> str:
    return _vi_int(n) if lang == "vi" else _en_int(n)


def _read_digits(s: str, lang: str) -> str:
    names = _VI_DIGITS if lang == "vi" else _EN_UNDER20[:10]
    return " ".join(names[int(c)] for c in s if c.isdigit())


def _read_number(tok: str, lang: str):
    """Đọc 1 token số (đã tách khỏi đơn vị). Trả None nếu không hợp lệ → giữ nguyên."""
    sign = ""
    if tok.startswith("-"):
        sign = "âm " if lang == "vi" else "negative "
        tok = tok[1:]
    dec, thou = (",", ".") if lang == "vi" else (".", ",")
    if dec in tok:
        ip, fp = tok.split(dec, 1)
    else:
        ip, fp = tok, None
    # Dấu phân cách hàng nghìn xử lý CHẶT: chỉ bỏ khi ĐÚNG định dạng nhóm-3 (1.234.567).
    # 1 dấu lẻ (3.5, 1.75, 8.5) → hiểu là dấu THẬP PHÂN (người Việt hay gõ chấm). Nhiều
    # dấu lung tung (1.2.3, 192.168.1.1) → GIỮ NGUYÊN, không bịa (theo thiết kế an toàn).
    if thou in ip:
        if re.fullmatch(r"\d{1,3}(?:" + re.escape(thou) + r"\d{3})+", ip):
            ip = ip.replace(thou, "")
        elif ip.count(thou) == 1 and fp is None:
            a, b = ip.split(thou)
            if a.isdigit() and b.isdigit():
                ip, fp = a, b
            else:
                return None
        else:
            return None
    if ip == "":
        ip = "0"
    if not ip.isdigit():
        return None
    # Mã/điện thoại: nhiều chữ số bắt đầu bằng 0, không phần thập phân → đọc từng số.
    if fp is None and len(ip) > 1 and ip[0] == "0":
        return (sign + _read_digits(ip, lang)).strip()
    # Số quá lớn (hiếm) → đọc từng chữ số cho an toàn.
    if len(ip) > 18:
        return (sign + _read_digits(ip, lang)).strip()
    intword = _read_int(int(ip), lang)
    if fp is not None:
        if fp == "" or not fp.isdigit():
            return None
        conn = "phẩy" if lang == "vi" else "point"
        return (sign + intword + " " + conn + " " + _read_digits(fp, lang)).strip()
    return (sign + intword).strip()


# ----------------------------------------------------------------- tháng (cho ngày)
_VI_MONTHS = {i: f"tháng {_vi_int(i)}" for i in range(1, 13)}
_EN_MONTHS = ["", "January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]


# ----------------------------------------------------------------- viết tắt English
# Danh xưng: PHÂN BIỆT HOA/THƯỜNG (không re.I) để "ms." (mili-giây) không thành "Miss",
# "Dr" chỉ khớp khi viết hoa. "vs" thêm \b hai đầu để không dính "vsync".
_EN_ABBR = [
    (re.compile(r"\bMrs\."), "Missus"),
    (re.compile(r"\bMr\."), "Mister"),
    (re.compile(r"\bMs\."), "Miss"),
    (re.compile(r"\bDr\."), "Doctor"),
    (re.compile(r"\bProf\."), "Professor"),
    (re.compile(r"\bvs\b\.?"), "versus"),
    (re.compile(r"\betc\.", re.I), "et cetera"),
    (re.compile(r"\be\.g\.", re.I), "for example"),
    (re.compile(r"\bi\.e\.", re.I), "that is"),
]


def normalize_text(text: str, language: str | None = None) -> str:
    """Chuẩn hóa văn bản: đọc số/ngày/tiền/%/độ/viết tắt thành chữ.

    language: "vi" | "en" | None (tự đoán). Trả về văn bản đã chuẩn hóa.
    """
    if not text or not text.strip():
        return text
    lang = language if language in ("vi", "en") else _detect_lang(text)
    out = text
    # Token số: kết thúc bằng chữ số → không "ngậm" dấu câu. Cho phép '-' đứng đầu là
    # SỐ ÂM CHỈ khi phía trước KHÔNG phải chữ/số → tránh nuốt gạch nối ("COVID-19",
    # "5-10", "2024-2025", "F-16") thành số âm dính chữ. Số âm thật (" -7", "(-7)") vẫn đúng.
    num = r"(?:(?<!\w)-)?\d[\d.,]*\d|(?:(?<!\w)-)?\d"

    # 1) NGÀY dd/mm/yyyy (hoặc d-m-yyyy). vi: ngày–tháng–năm; en: tháng/ngày/năm.
    #    vi: nuốt luôn chữ "ngày" có sẵn phía trước để khỏi lặp "ngày ngày".
    def _date(m):
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if lang == "vi":
            if not (1 <= a <= 31 and 1 <= b <= 12):
                return m.group(0)
            return f"ngày {_vi_int(a)} {_VI_MONTHS[b]} năm {_vi_int(y)}"
        else:
            mo, day = a, b   # en mặc định month/day
            if mo > 12 and 1 <= b <= 12 and 1 <= a <= 31:
                mo, day = b, a   # kiểu Anh (UK): dd/mm → hoán đổi
            if not (1 <= mo <= 12 and 1 <= day <= 31):
                return m.group(0)
            return f"{_EN_MONTHS[mo]} {_en_int(day)}, {_en_int(y)}"

    out = re.sub(r"(?:ngày\s+)?\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b",
                 _date, out, flags=re.I)

    # 2) TIỀN: ký hiệu $ đứng trước số.
    def _usd(m):
        val = _read_number(m.group(1), lang)
        if val is None:
            return m.group(0)
        return val + (" đô la" if lang == "vi" else " dollars")

    out = re.sub(r"\$\s*(" + num + r")", _usd, out)

    # 3) TIỀN Việt: số đứng trước đ / đồng / vnđ / vnd.
    if lang == "vi":
        def _vnd(m):
            val = _read_number(m.group(1), lang)
            return (val + " đồng") if val is not None else m.group(0)
        out = re.sub(r"(" + num + r")\s*(?:đồng|vn[dđ]|đ)\b", _vnd, out, flags=re.I)

    # 4) PHẦN TRĂM
    def _pct(m):
        val = _read_number(m.group(1), lang)
        if val is None:
            return m.group(0)
        return val + (" phần trăm" if lang == "vi" else " percent")

    out = re.sub(r"(" + num + r")\s*%", _pct, out)

    # 5) ĐỘ C / ĐỘ F
    def _deg(m):
        val = _read_number(m.group(1), lang)
        if val is None:
            return m.group(0)
        unit = m.group(2).upper()
        if lang == "vi":
            return f"{val} độ {unit}"
        name = "Celsius" if unit == "C" else "Fahrenheit"
        return f"{val} degrees {name}"

    out = re.sub(r"(" + num + r")\s*°\s*([CF])", _deg, out)

    # 5b) GIỜ hh:mm (phút BẮT BUỘC 2 chữ số để không đụng tỷ số "2:1").
    def _time(m):
        h, mi = int(m.group(1)), int(m.group(2))
        if lang == "vi":
            return f"{_vi_int(h)} giờ" + (f" {_vi_int(mi)} phút" if mi else "")
        return f"{_en_int(h)}" + (f" {_en_int(mi)}" if mi else " o'clock")

    out = re.sub(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", _time, out)

    # 6) SỐ đứng riêng (sau khi đã xử lý các dạng có đơn vị ở trên).
    def _num(m):
        val = _read_number(m.group(0), lang)
        return val if val is not None else m.group(0)

    out = re.sub(num, _num, out)

    # 7) Viết tắt + ký hiệu '&'
    if lang == "en":
        for rx, rep in _EN_ABBR:
            out = rx.sub(rep, out)
    out = re.sub(r"[ \t]*&[ \t]*", (" và " if lang == "vi" else " and "), out)

    # Gộp khoảng trắng thừa do thay thế tạo ra (giữ nguyên xuống dòng).
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    samples = [
        ("vi", "Tôi có 1234 con vịt và 25 con gà."),
        ("vi", "Giá là 50.000đ, giảm 15% còn 42.500 đồng."),
        ("vi", "Ngày 13/06/2026 nhiệt độ 35°C."),
        ("vi", "Anh ấy kiếm 2.500.000.000 đồng một năm."),
        ("vi", "Khoảng 3,14 và -7 độ."),
        ("vi", "Mã vùng 0084 và số 007."),
        ("vi", "Một trăm lẻ năm: 105, và 1000005."),
        ("en", "I have 1,234 ducks and 25 hens."),
        ("en", "It costs $1,200.50, down 15% from before."),
        ("en", "On 06/13/2026 it was 35°C, Mr. Smith vs. Dr. Lee, etc."),
        ("en", "He earns $2,500,000 a year, e.g. a lot."),
        ("en", "Pi is about 3.14 and -7 degrees."),
        (None, "Plain 42 and 3.5 with no diacritics."),
        (None, "Có 42 con và 3,5 lít."),
    ]
    for lg, s in samples:
        print(f"[{lg}] {s}")
        print(f"   -> {normalize_text(s, lg)}\n")
