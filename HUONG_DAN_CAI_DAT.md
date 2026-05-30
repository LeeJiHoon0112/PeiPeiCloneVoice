# 🎙️ PeiPei Clone Voice — Hướng dẫn cài đặt

App nhân bản giọng nói AI chạy **offline trên máy bạn**. Làm theo 4 bước dưới đây.

---

## ⚙️ Yêu cầu máy
- **Windows 10/11**
- **GPU NVIDIA** (khuyên ≥ 6GB VRAM, vd RTX 3060/4060 trở lên).
  *Không có GPU NVIDIA vẫn chạy được nhưng RẤT chậm.*
- **~8GB ổ trống** (cho thư viện + model AI).
- **Mạng internet** cho lần chạy đầu (để tải model ~4.7GB).

---

## 📥 Bước 1 — Cài Python
1. Tải Python 3.13 tại: https://www.python.org/downloads/
2. Khi cài, **TÍCH vào ô "Add Python to PATH"** (rất quan trọng) rồi bấm Install.

> Đã có Python 3.10–3.13 sẵn thì bỏ qua bước này.

## 📂 Bước 2 — Tải app
**Cách 1 — GitHub (khuyên dùng, để update dễ):**
1. Cài Git: https://git-scm.com/download/win (next-next-finish).
2. Mở thư mục muốn chứa app, chuột phải → *Open Git Bash here* (hoặc mở CMD), gõ:
   ```
   git clone <LINK-REPO-CUA-BAN>
   ```
**Cách 2 — File ZIP:** giải nén ra một thư mục bất kỳ (vd: `D:\PeiPeiCloneVoice`).

> 🔄 **Cập nhật sau này:** nếu tải bằng GitHub, mỗi lần có bản mới chỉ cần **double-click `update.bat`** (tự tải phần thay đổi, KHÔNG mất giọng/model của bạn). Nếu dùng ZIP thì phải xin file ZIP mới.

## 🔧 Bước 3 — Cài đặt (chạy 1 lần)
- Mở thư mục app, **double-click `install.bat`**.
- Đợi nó tải & cài PyTorch + thư viện (~2–3GB, vài phút tuỳ mạng).
- Khi thấy dòng **"Done! Now run: run.bat"** là xong.

## ▶️ Bước 4 — Chạy app
- **Double-click `run.bat`**.
- **Lần đầu**: app tự tải model AI (~4.7GB) về thư mục `models/` — mất vài phút, có thanh tiến trình.
- Các lần sau: chỉ ~10–20 giây để nạp model rồi sẵn sàng.

---

## 🎤 Cách dùng nhanh
1. **Tạo giọng** (tab *Quản lý giọng*): chọn 1 file audio mẫu **3–10 giây** (giọng rõ, không nhạc nền) → bấm *✨ Tự nhận diện lời thoại* → đặt tên → *➕ Tạo & lưu giọng*. App sẽ đọc thử 1 câu cho bạn nghe.
2. **Tạo audio** (tab *Tạo giọng nói*): chọn giọng đã lưu → nhập văn bản (nhớ **có dấu chấm câu**) → bấm *🔊 Tạo giọng nói*. File lưu ở `user_data/outputs/`.

### Mẹo cho giọng hay & tự nhiên
- **Độ giống giọng**: kéo 2.5–3.0 nếu chưa giống.
- **Giảm tiếng thở**: kéo 45–70% nếu nghe nhiều tiếng thở.
- **Tốc độ** ~0.90–0.95x, **Ngắt nghỉ** ~0.40s cho nhịp người thật.
- Audio mẫu càng **sạch, rõ, một giọng điệu** thì clone càng giống.

---

## ❓ Gặp lỗi?
- **"Python not found"** → chưa cài Python hoặc quên tích "Add to PATH". Cài lại Python.
- **Chạy rất chậm** → máy không có GPU NVIDIA (đang chạy CPU). Cần GPU để nhanh.
- **Lần đầu tạo giọng hơi lâu (~1–2 phút)** → bình thường (GPU khởi động nguội), các lần sau nhanh.
- **Cài lại từ đầu**: chạy `install.bat force`.
