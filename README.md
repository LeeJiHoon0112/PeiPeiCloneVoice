<div align="center">

# 🎙️ PeiPei Clone Voice

**App desktop nhân bản giọng nói (voice clone) + đọc văn bản (TTS) — chạy hoàn toàn offline trên máy bạn.**

Không cần API key · Không tốn phí · Hỗ trợ 600+ ngôn ngữ (có tiếng Việt)

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows)
![Python](https://img.shields.io/badge/Python-3.10--3.13-3776AB?logo=python&logoColor=white)
![GPU](https://img.shields.io/badge/GPU-NVIDIA%20CUDA-76B900?logo=nvidia&logoColor=white)
![License](https://img.shields.io/badge/License-Apache--2.0-blue)

</div>

---

Xây dựng trên model mã nguồn mở **OmniVoice** (`k2-fsa/OmniVoice`, Apache-2.0) +
**Whisper large-v3-turbo** (nhận diện lời thoại). Giao diện hiện đại (PyQt5, light theme).

## ✨ Tính năng
- 🎤 **Clone giọng** từ một đoạn audio mẫu ngắn (3–10 giây).
- 💾 **Lưu giọng** thành profile để tái sử dụng + **nghe thử** ngay.
- ✨ **Tự nhận diện lời thoại** của audio mẫu bằng Whisper (không cần gõ tay).
- 🎚️ Tinh chỉnh: **tốc độ**, **ngắt nghỉ giữa câu**, **độ giống giọng**, **giảm tiếng thở**, **chất lượng**.
- 📊 **Thanh tiến trình %** + **đồng hồ thời gian** khi tạo.
- 🌍 **Đa ngôn ngữ** (600+, có tiếng Việt) · 🎨 **Thiết kế giọng** bằng mô tả.

## 💻 Yêu cầu
- **Windows 10/11** + **GPU NVIDIA** (khuyên ≥ 6GB VRAM; đã test RTX 4060 8GB, dùng ~3.7GB).
- **~8GB ổ trống** (thư viện + model AI).
- **Internet** cho lần chạy đầu (tải model ~4.7GB). Sau đó chạy offline.

> 💡 Máy không có GPU NVIDIA vẫn chạy được nhưng **rất chậm**.

## 🚀 Cài đặt (làm 1 lần)
> 📄 Xem hướng dẫn chi tiết bằng tiếng Việt trong file **[HUONG_DAN_CAI_DAT.md](HUONG_DAN_CAI_DAT.md)**.

**1.** Cài **Python 3.13** (https://www.python.org/downloads/ — nhớ **tích "Add Python to PATH"**) và **Git** (https://git-scm.com/download/win).

**2.** Tải app về:
```bash
git clone https://github.com/LeeJiHoon0112/PeiPeiCloneVoice.git
cd PeiPeiCloneVoice
```

**3.** Double-click **`install.bat`** (tự cài PyTorch CUDA + omnivoice + PyQt5).

## ▶️ Chạy
Double-click **`run.bat`**.
- **Lần đầu**: app tự tải model AI (~4.7GB) về thư mục `models/` — vài phút, có thanh tiến trình.
- **Lần sau**: nạp model từ đĩa (~10–20s) rồi sẵn sàng.

## 📖 Cách dùng nhanh
1. **Tạo giọng** — tab *🎚️ Quản lý giọng*: chọn audio mẫu → *✨ Tự nhận diện lời thoại* → đặt tên → *➕ Tạo & lưu giọng* (app đọc thử 1 câu cho bạn nghe).
2. **Tạo audio** — tab *🔊 Tạo giọng nói*: chọn giọng đã lưu → nhập văn bản → *🔊 Tạo giọng nói*. File lưu ở `user_data/outputs/`.

### 🌟 Mẹo cho giọng giống & tự nhiên
- Audio mẫu **sạch, rõ, một giọng điệu** (clone cả cách nói) → quan trọng nhất.
- **Độ giống giọng** 2.5–3.0 nếu chưa giống · **Giảm tiếng thở** 45–70% nếu nhiều tiếng thở.
- **Tốc độ** ~0.90–0.95x · **Ngắt nghỉ** ~0.40s · viết văn bản **có dấu chấm câu**.

## 🔄 Cập nhật bản mới
Khi có phiên bản mới, chỉ cần double-click **`update.bat`** — tự tải phần thay đổi,
**không mất** giọng đã tạo, model hay cài đặt của bạn.

## 🗂️ Cấu trúc
```
main.py              điểm khởi chạy
app/
  config.py          dò đường dẫn model + thư mục dữ liệu
  engine.py          lõi: nạp model, ASR, tạo profile, sinh audio + xử lý âm thanh
  profiles.py        lưu/đọc/xóa/import giọng đã tạo
  workers.py         chạy tác vụ nặng trên luồng nền (UI không treo)
  main_window.py     giao diện PyQt5
install.bat / run.bat / update.bat / package.bat
models/              (tự tạo) model tải về — không đẩy lên GitHub
user_data/           (tự tạo) voices/ + outputs/ — không đẩy lên GitHub
```

## ⚙️ Tùy chỉnh đường dẫn model (nâng cao)
```bat
set OMNIVOICE_MODEL_DIR=D:\models\OmniVoice
set OMNIVOICE_ASR_DIR=D:\models\whisper-large-v3-turbo
```

## 📜 Giấy phép & lưu ý
Phần ứng dụng thuộc về tác giả. Model OmniVoice & Whisper theo giấy phép gốc (Apache-2.0 / MIT).
**Không** dùng để mạo danh, lừa đảo hay mục đích trái phép — tuân thủ pháp luật địa phương.
