# 🎙️ PeiPei Clone Voice

App desktop **nhân bản giọng nói (voice clone) + đọc văn bản (TTS)** chạy **offline trên GPU**,
xây dựng trên model mã nguồn mở **OmniVoice** (`k2-fsa/OmniVoice`, Apache-2.0)
và **Whisper large-v3-turbo** (nhận diện lời thoại).

Giao diện hiện đại (PyQt5, dark theme), hỗ trợ **600+ ngôn ngữ** (có **tiếng Việt**).

---

## ✨ Tính năng
- **Clone giọng** từ 1 đoạn audio mẫu ngắn (3–10 giây).
- **Lưu giọng** thành profile để tái sử dụng.
- **Tự nhận diện lời thoại** của audio mẫu bằng Whisper.
- **Thiết kế giọng** bằng mô tả (vd: "calm middle-aged male, deep pitch").
- Chỉnh **tốc độ**, **ngắt nghỉ giữa câu** (nghe tự nhiên như người thật), **chất lượng**.

## 💻 Yêu cầu
- **Windows + GPU NVIDIA** (khuyến nghị ≥ 6GB VRAM; đã test trên RTX 4060 8GB, dùng ~3.7GB).
- ~6GB trống cho model + thư viện.
- Internet cho **lần chạy đầu** (để tải model ~4.7GB về thư mục `models/`).

## 🚀 Cài đặt (lần đầu)
```bash
git clone <repo-cua-ban>
cd PeiPeiCloneVoice
install.bat        # tạo venv + cài torch (CUDA) + omnivoice + PyQt5
```
> `install.bat` sẽ tự dò: nếu máy đã có sẵn môi trường tương thích thì dùng lại;
> nếu chưa, nó tạo `venv` riêng và cài đầy đủ.

## ▶️ Chạy
Double-click **`run.bat`** (hoặc gõ `run.bat` trong cmd).
- Lần đầu: app tự **tải model** về `models/` (mất vài phút, có log tiến độ).
- Các lần sau: nạp model từ đĩa (~10–20 giây) rồi sẵn sàng.

## 📖 Cách dùng
1. **Tạo giọng** (tab *Quản lý giọng*): chọn audio mẫu → *Tự nhận diện lời thoại* → đặt tên → *Tạo & lưu giọng*.
2. **Tạo audio** (tab *Tạo giọng nói*): chọn giọng đã lưu → nhập văn bản → *Tạo giọng nói*.
   Kết quả lưu ở `user_data/outputs/`.

### Mẹo cho giọng tự nhiên
- Viết văn bản **có dấu chấm câu** (app ngắt nghỉ dựa vào đó).
- Tốc độ ~0.90–0.95x, ngắt nghỉ ~0.40s.
- Audio mẫu nên **đọc thong thả, rõ ràng** (clone cả cách nói).

## 🗂️ Cấu trúc
```
main.py              điểm khởi chạy
app/
  config.py          dò đường dẫn model + thư mục dữ liệu (portable)
  engine.py          lõi: nạp model, ASR, tạo profile, sinh audio
  profiles.py        lưu/đọc/xóa giọng đã tạo
  workers.py         chạy tác vụ nặng trên luồng nền (UI không treo)
  main_window.py     giao diện PyQt5
models/              (tự tạo) model tải về — KHÔNG đẩy lên GitHub
user_data/           (tự tạo) voices/ + outputs/ — KHÔNG đẩy lên GitHub
```

## ⚙️ Tùy chỉnh đường dẫn model (nâng cao)
Đặt biến môi trường trước khi chạy nếu muốn trỏ model ở nơi khác:
```bat
set OMNIVOICE_MODEL_DIR=D:\models\OmniVoice
set OMNIVOICE_ASR_DIR=D:\models\whisper-large-v3-turbo
```

## 📜 Giấy phép
Phần ứng dụng do bạn sở hữu. Model OmniVoice & Whisper theo giấy phép gốc (Apache-2.0 / MIT).
Không dùng để mạo danh/lừa đảo — tuân thủ pháp luật địa phương.
