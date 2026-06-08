# 🔧 Hướng dẫn khôi phục môi trường Dev sau khi cài lại Windows

> Tài liệu này dành cho **chủ dự án (Boss)** — khôi phục lại toàn bộ môi trường lập trình của **PeiPei Clone Voice** sau khi cài lại Win, để tiếp tục dev.
>
> **Repo:** https://github.com/LeeJiHoon0112/PeiPeiCloneVoice.git
> **Cập nhật:** 2026-06-08

---

## 📦 Trước khi cài lại Win — SAO LƯU (bắt buộc!)

GitHub đã có **toàn bộ code**, nhưng **KHÔNG** chứa 2 thứ sau (bị `.gitignore` loại ra). Phải tự backup:

1. 📁 Thư mục **`user_data/`** — giọng đã tạo (.pt) + API key + cài đặt cá nhân.
2. 📄 File **`context.md`** — ghi chú kỹ thuật nội bộ của dự án.

**Cách làm:** copy 2 thứ này ra **Google Drive / USB / ổ cứng ngoài**.
*(Hoặc dùng file ZIP backup đã tạo sẵn: `PeiPei_Backup_<ngày>.zip` — chỉ ~2 MB.)*

> ⚠️ **KHÔNG cần backup:** thư mục `venv/` và `models/` — chúng được tạo lại / tải lại tự động (xem bên dưới).

---

## 🖥️ Sau khi cài lại Win — Khôi phục từng bước

### Bước 1 — Cài phần mềm nền
Cài 3 thứ này (theo đúng thứ tự, mỗi cái next-next-finish):

1. **Python 3.13** — tải tại https://www.python.org/downloads/
   - ⚠️ **QUAN TRỌNG:** khi cài, **TÍCH vào ô "Add Python to PATH"** rồi mới bấm Install.
   - *(Dự án test trên Python 3.13.9; chấp nhận 3.10–3.13.)*

2. **Git** — tải tại https://git-scm.com/download/win (để clone code + dùng `update.bat`).

3. **Driver NVIDIA** mới nhất — tải tại https://www.nvidia.com/Download/index.aspx
   - Cần cho GPU chạy nhanh. *(Không có GPU vẫn chạy được nhưng rất chậm.)*

> 💡 Kiểm tra nhanh sau khi cài: mở **Command Prompt**, gõ `python --version` và `git --version` — nếu hiện số phiên bản là OK.

### Bước 2 — Tải code về (clone từ GitHub)
1. Mở thư mục muốn đặt dự án (ví dụ tạo lại `C:\Users\<Tên>\Desktop\psylo`).
2. Chuột phải vào khoảng trống → **Open Git Bash here** (hoặc mở Command Prompt rồi `cd` vào đó).
3. Gõ lệnh:
   ```
   git clone https://github.com/LeeJiHoon0112/PeiPeiCloneVoice.git
   ```
4. Xong sẽ có thư mục **`PeiPeiCloneVoice`** chứa toàn bộ code.

### Bước 3 — Khôi phục dữ liệu cá nhân
1. Lấy bản backup đã lưu (Google Drive/USB), giải nén nếu là ZIP.
2. Copy **`user_data/`** và **`context.md`** vào **trong** thư mục `PeiPeiCloneVoice` vừa clone.
   - Kết quả đúng: `PeiPeiCloneVoice\user_data\voices\...` (chứa lại các giọng cũ).

> Nếu bỏ qua bước này: app vẫn chạy nhưng **mất hết giọng đã tạo và API key** — phải tạo/nhập lại.

### Bước 4 — Cài môi trường (venv + thư viện)
1. Vào thư mục `PeiPeiCloneVoice`.
2. Nháy đúp **`install.bat`** → đợi nó tự làm:
   - Tạo môi trường ảo `venv`
   - Cài PyTorch (CUDA 12.8) + OmniVoice + PyQt5 + các thư viện
   - Tự kiểm tra cuối ("OK - torch ... | CUDA: True")
3. Quá trình này tải vài GB thư viện → cần **mạng** và **vài phút đến vài chục phút**.

> ⚠️ Lưu ý: `install.bat` có đoạn ưu tiên dùng venv của tool cũ ở
> `C:\Users\Admin\Desktop\Clone\Tool\venv`. Sau khi cài lại Win, đường dẫn đó
> không còn → nó sẽ **tự tạo venv mới ngay trong thư mục dự án**. Đây là hành vi đúng.
> *(Nếu lỡ có venv cũ mà muốn tạo lại sạch: chạy `install.bat force`.)*

### Bước 5 — Chạy app lần đầu
1. Nháy đúp **`run.bat`**.
2. **Lần chạy đầu sẽ tải model AI (~4.7 GB)** về thư mục `models/` — chỉ tải 1 lần, cần mạng. Các lần sau mở nhanh.
3. Nhập **mật khẩu** đăng nhập (mật khẩu Boss đã đặt — xem mục bên dưới nếu quên).
4. App mở lên, các giọng cũ (từ `user_data`) sẽ có sẵn → **tiếp tục dev bình thường.**

---

## 💻 Tiếp tục công việc Dev

- **Sửa code**: mở thư mục `PeiPeiCloneVoice` bằng VS Code (hoặc trình soạn thảo quen dùng).
- **Chạy thử / test bằng Python của venv**:
  ```
  PeiPeiCloneVoice\venv\Scripts\python.exe  <file_cần_chạy>.py
  ```
- **Lưu thay đổi lên GitHub**:
  ```
  git add .
  git commit -m "Mô tả thay đổi"
  git push origin main
  ```
- **Lấy bản mới nhất về** (nếu sửa ở máy khác): nháy đúp `update.bat` (hoặc `git pull`).

---

## 🔑 Ghi nhớ quan trọng

| Thứ | Khôi phục từ đâu |
|---|---|
| Code tool | `git clone` từ GitHub |
| Giọng đã tạo + API key | Bản backup `user_data` (Drive/USB) |
| Ghi chú dự án | Bản backup `context.md` |
| venv + thư viện | `install.bat` tự cài |
| Model AI ~4.7 GB | `run.bat` tự tải lần đầu |
| Mật khẩu đăng nhập | Lưu trong code (`app/auth.py`, dạng mã hóa). Quên thì đổi lại bằng cách sửa `_DEFAULT_HASH`. Hỏi Claude nếu cần. |

> 🧩 **Mẹo backup định kỳ:** mỗi khi tạo thêm giọng mới quan trọng, nén lại `user_data` + `context.md` rồi cập nhật lên Drive. (Có thể nhờ Claude tạo file `backup.bat` để bấm 1 lần là xong.)

---

*PeiPei Clone Voice — Hướng dẫn khôi phục Dev. Giữ file này trong repo để luôn có sẵn.*
