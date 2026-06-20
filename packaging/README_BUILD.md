# Build & bán PeiPei Clone Voice (DEV — chỉ Boss đọc)

> Mục tiêu: che code (đặc biệt đoạn kiểm tra license) bằng cách **biên dịch
> `app/` thành `.pyd` native với Nuitka (MIỄN PHÍ)**, rồi đóng gói thư mục bán.
> Khách KHÔNG nhận source `app/` → không tắt/sửa được license.

## 0. Một lần: cài công cụ build (đã cài sẵn trong venv dev)
```
pip install nuitka          # Nuitka tự tải trình biên dịch zig/MinGW (free)
```
Không cần Visual Studio. Lần build đầu Nuitka tải zig (~vài chục MB) tự động.

## 1. Trước khi build
- Mở `app/config.py`, đảm bảo **`LICENSE_ENABLED = True`** (bản bán).
- (Tuỳ chọn) tăng `APP_VERSION` nếu ra bản mới.

## 2. Build (1 lệnh)
Bấm đúp **`build.bat`** (ở thư mục gốc). Nó sẽ:
1. Kiểm tra `LICENSE_ENABLED = True` (sai thì dừng).
2. `nuitka --module app` → `build/app.cp313-win_amd64.pyd` (toàn bộ code đã nén thành mã máy).
3. Gom thư mục **`release/`** gồm: `main.py`, `app.*.pyd`, `install.bat`, `run.bat`,
   `requirements.txt`, `HUONG_DAN_KHACH.txt`. **KHÔNG** kèm `app/` source.

## 3. Giao cho khách
- Cách nhanh: nén **`release/`** thành `.zip` → gửi link tải.
- Cách "pro": đóng **installer** bằng [Inno Setup](https://jrsoftware.org/isdl.php) (miễn phí):
  trỏ `[Files]` vào toàn bộ `release\*`, tạo shortcut chạy `run.bat`.
  (Có thể nhúng sẵn Python 3.13 embeddable để khách khỏi tự cài Python — xem mục 5.)

## 4. ⚠️ Ràng buộc QUAN TRỌNG: Python 3.13
- File `.pyd` gắn chặt với **Python 3.13 (cp313, 64-bit)**. Máy khách PHẢI có đúng 3.13.
- `install.bat` (bản khách) đã **bắt buộc 3.13** và báo lỗi rõ nếu thiếu.
- Khi NÂNG CẤP Python dev (vd lên 3.14), phải build lại `.pyd` cho phiên bản mới.

## 5. (Nâng cao, làm sau) Nhúng sẵn Python để khách khỏi cài
Tải "Windows embeddable package (64-bit)" Python 3.13, bỏ vào `release/python/`,
sửa `install.bat`/`run.bat` trỏ tới python đó → khách không cần tự cài Python.
(Hiện chưa làm — bản v1 yêu cầu khách tự cài Python 3.13.)

## 6. Tạo license key để bán
- Dùng **admin GUI** sẵn có (server dùng chung). Tạo key với **product = `peipei-voice`**.
- Đặt giới hạn số máy / hạn dùng theo gói bán.
- ⚠️ TUYỆT ĐỐI không đưa `private_key.pem` / `ADMIN_TOKEN` vào tool/chat/commit.

## 7. Checklist trước khi bán ✅
- [ ] `LICENSE_ENABLED = True` trong `app/config.py`.
- [ ] Chạy `build.bat` → có `release/` (kiểm tra KHÔNG có thư mục `app/` trong đó).
- [ ] Test `release/` trên máy SẠCH (hoặc venv mới): `install.bat` → `run.bat` →
      hiện hộp kích hoạt → dán key thật → vào app → tạo thử 1 giọng.
- [ ] Đã tạo sẵn key (product `peipei-voice`) để giao khách.
- [ ] Gửi kèm `HUONG_DAN_KHACH.txt`.

## 8. Bảo vệ tới đâu?
- `.pyd` là mã máy native → khó dịch ngược hơn `.pyc` rất nhiều.
- Đoạn check license nằm trong `app.pyd` ở **2 lớp**: `main.py`-gate gọi vào,
  và **chốt 2 trong `MainWindow.__init__`** (không gỡ được vì đã biên dịch).
- Cộng với server: khoá theo máy + thu hồi (revoke) + bắt online định kỳ.
- Đủ chặn người dùng phổ thông. (Không có cách nào chống 100% mọi hacker, nhưng
  đây là mức bảo vệ tốt mà MIỄN PHÍ.)
