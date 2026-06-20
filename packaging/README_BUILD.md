# Build & bán PeiPei Clone Voice (DEV — chỉ Boss đọc)

> Mục tiêu: bán bản KHÁCH KHỎI CÀI GÌ. Code che bằng **Nuitka → `.pyd`** (MIỄN PHÍ),
> kèm sẵn **Python nhúng (embeddable 3.13)**. Khách chỉ giải nén → chạy `run.bat`.
> Khách KHÔNG nhận source `app/` → không tắt/sửa được license.

## 0. Một lần: cài công cụ build (đã cài sẵn trong venv dev)
```
pip install nuitka          # Nuitka tự tải trình biên dịch zig (free, không cần Visual Studio)
```

## 1. Trước khi build
- Mở `app/config.py`, đảm bảo **`LICENSE_ENABLED = True`** (bản bán).
- (Tuỳ chọn) tăng `APP_VERSION` nếu ra bản mới.

## 2. Build (1 lệnh)
Bấm đúp **`build.bat`** (ở thư mục gốc). Nó sẽ:
1. Kiểm tra `LICENSE_ENABLED = True` (sai thì dừng).
2. `nuitka --module app` → `build/app.cp313-win_amd64.pyd` (toàn bộ code thành mã máy).
3. Chuẩn bị **Python nhúng** (`packaging/prep_python.py` tải Python 3.13.9 embeddable +
   bật pip + `._pth`; cache ở `build/python_base`, tải 1 lần).
4. Gom **`release/`** = `python/` + `main.py` + `app.*.pyd` + `setup.bat` + `run.bat` +
   `requirements.txt` + `HUONG_DAN_KHACH.txt`. **KHÔNG** kèm `app/` source.

> `release/` lúc này ~25–30MB (chưa có torch). Torch + thư viện được `run.bat` tự cài
> vào `release/python/` ở **lần đầu khách chạy** (cùng lúc tải model). Phân phối nhẹ.

## 3. Giao cho khách — chọn 1 trong 2
**A) Installer chuyên nghiệp (KHUYÊN):** ra 1 file `Setup.exe` (khách bấm Next → cài → có
icon Desktop).
   1. Cài **Inno Setup 6** (MIỄN PHÍ kể cả bán hàng — banner "purchase a license" chỉ là
      mời quyên góp tự nguyện): https://jrsoftware.org/isdl.php
   2. Chạy **`packaging\build_installer.bat`** → ra **`build\PeiPeiCloneVoice_Setup.exe`** (~14MB).
      (Hoặc mở `packaging\installer.iss` bằng Inno Setup rồi bấm Build/Compile.)
   3. Gửi khách `Setup.exe` (kèm key). Khách: bấm đúp → Next → Install → icon Desktop → chạy.
   - Cài PER-USER vào `%LOCALAPPDATA%\Programs\PeiPeiCloneVoice` (ghi được, KHÔNG cần Admin).
   - (Tuỳ chọn) thêm `packaging\icon.ico` → build.bat tự đưa vào `release\`, installer + icon
     dùng nó. Không có cũng chạy (icon mặc định).

**B) Gói .ZIP đơn giản:** nén **`release/`** thành `.zip` → khách giải nén → bấm `run.bat`.

- (Tuỳ chọn) bản "to nhưng chạy ngay, KHÔNG cài lần đầu": chạy `release\setup.bat` một lần
  trên máy build để cài sẵn torch vào `release\python`, rồi mới nén/đóng installer. Khi đó
  gói ~3–4GB nhưng khách chạy là dùng luôn (chỉ còn tải model).

## 4. ⚠️ Ràng buộc: Python 3.13
- `.pyd` gắn chặt **Python 3.13 (cp313, 64-bit)** — đã kèm đúng Python nhúng 3.13.9 nên khách OK.
- Khi NÂNG CẤP Python dev (vd 3.14), phải build lại `.pyd` **và** sửa `PY_VER` trong
  `packaging/prep_python.py` cho khớp.

## 5. Tạo license key để bán
- Dùng **admin GUI** sẵn có (server dùng chung). Tạo key với **product = `peipei-voice`**.
- Đặt giới hạn số máy / hạn dùng theo gói bán.
- ⚠️ TUYỆT ĐỐI không đưa `private_key.pem` / `ADMIN_TOKEN` vào tool/chat/commit.

## 6. Checklist trước khi bán ✅
- [ ] `LICENSE_ENABLED = True` trong `app/config.py`.
- [ ] Chạy `build.bat` → có `release/` (kiểm tra KHÔNG có thư mục `app/`, CÓ `python/`).
- [ ] Test `release/` trên máy/thư mục SẠCH: chạy `run.bat` → tự cài → hiện hộp kích hoạt →
      dán key thật → vào app → tạo thử 1 giọng.
- [ ] Đã tạo sẵn key (product `peipei-voice`) để giao khách.
- [ ] Đóng gói: chạy `packaging\build_installer.bat` → `build\PeiPeiCloneVoice_Setup.exe`
      (hoặc nén `release/` thành .zip). Test thử trên thư mục/máy sạch.

## 7. Bảo vệ tới đâu?
- `.pyd` là mã máy native (Nuitka) → khó dịch ngược hơn `.pyc` rất nhiều.
- Check license trong `app.pyd` ở **2 lớp**: cổng `main.py` gọi vào + **chốt 2 trong
  `MainWindow.__init__`** (không gỡ được vì đã biên dịch).
- Cộng server: khoá theo máy + thu hồi (revoke) + bắt online định kỳ.
- Đủ chặn người dùng phổ thông, MIỄN PHÍ. (Không có cách nào chống 100% mọi hacker.)
