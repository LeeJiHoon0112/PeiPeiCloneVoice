# PeiPei Clone Voice — Tài liệu hướng dẫn sử dụng

> **Gửi Cowork:** Đây là nội dung nguồn để bạn tạo giúp **một file PDF hướng dẫn sử dụng** (tiếng Việt) cho người dùng cuối của ứng dụng "PeiPei Clone Voice".
>
> **Yêu cầu khi làm PDF:**
> - Trình bày đẹp, dễ đọc, có mục lục, đánh số trang.
> - Đối tượng đọc: **người dùng phổ thông, không rành kỹ thuật** → diễn đạt đơn giản, nhiều gạch đầu dòng, tránh thuật ngữ.
> - Mỗi bước thao tác nên có **chỗ chừa để chèn ảnh chụp màn hình** (ghi rõ "[Ảnh: ...]" tại vị trí phù hợp — người dùng sẽ tự chèn ảnh sau).
> - Dùng icon/emoji giống trong app để người đọc dễ đối chiếu nút bấm.
> - Tông giọng: thân thiện, hướng dẫn từng bước.

---

## 1. Giới thiệu

**PeiPei Clone Voice** là ứng dụng máy tính (Windows) giúp **nhân bản giọng nói (clone voice)** bằng trí tuệ nhân tạo. Bạn đưa vào một đoạn ghi âm giọng mẫu, ứng dụng sẽ học giọng đó và đọc **bất kỳ văn bản nào** bằng chính giọng ấy.

**Dùng để làm gì:**
- Tạo giọng đọc (voice-over) cho video YouTube, TikTok, phim kể chuyện…
- Đọc kịch bản dài bằng một giọng cố định, ổn định.
- Xuất kèm **file phụ đề .SRT chia cảnh** để dựng video (tạo ảnh/clip theo từng cảnh).

**Điểm mạnh:**
- Hỗ trợ nhiều ngôn ngữ, trong đó có **tiếng Việt**.
- Lưu lại giọng đã tạo để dùng nhiều lần.
- Tự điều chỉnh tốc độ, ngắt nghỉ, độ giống giọng, giảm tiếng thở.

---

## 2. Yêu cầu máy tính

| Hạng mục | Yêu cầu |
|---|---|
| Hệ điều hành | Windows 10/11 (64-bit) |
| Card đồ họa | **Khuyến nghị mạnh: GPU NVIDIA** (ví dụ RTX 3050 trở lên). Không có GPU vẫn chạy được nhưng **rất chậm** |
| Ổ cứng trống | Khoảng **6 GB** (để tải model AI lần đầu) |
| Internet | Cần cho **lần chạy đầu tiên** (tải model ~4.7 GB) và khi dùng tính năng "Chia cảnh bằng AI" |

> 💡 **Lần đầu mở app sẽ lâu** vì máy phải tải model AI về (vài phút đến vài chục phút tùy mạng). Những lần sau mở nhanh hơn nhiều.

---

## 3. Cài đặt

1. Tải/giải nén thư mục ứng dụng về máy (ví dụ đặt ở Desktop).
2. Mở thư mục, **nháy đúp vào `install.bat`** → đợi quá trình cài đặt hoàn tất (chỉ làm 1 lần).
3. Sau khi cài xong, **nháy đúp vào `run.bat`** mỗi khi muốn mở ứng dụng.

> [Ảnh: thư mục ứng dụng, khoanh tròn file `install.bat` và `run.bat`]

---

## 4. Đăng nhập

- Lần đầu mở, ứng dụng yêu cầu **nhập mật khẩu** (mật khẩu được người chia sẻ ứng dụng cung cấp riêng cho bạn).
- Tích chọn **"Ghi nhớ trên máy này"** để lần sau **không phải nhập lại** mật khẩu.
- Muốn thoát tài khoản: bấm nút **🔒 Đăng xuất** ở góc giao diện.

> [Ảnh: màn hình đăng nhập]

---

## 5. Tổng quan giao diện

Ứng dụng có **2 thẻ (tab)** chính ở phía trên:

- **🔊 Tạo giọng nói** — nơi nhập văn bản và tạo audio.
- **🎚️ Quản lý giọng** — nơi tạo giọng mới, xem và xóa các giọng đã lưu.

Góc trên bên phải hiển thị **trạng thái** ("Đang khởi động" → "Sẵn sàng") và **thiết bị** đang dùng (GPU/CPU).

> [Ảnh: toàn bộ giao diện, đánh dấu 2 tab và khu trạng thái]

---

## 6. Hướng dẫn nhanh (làm theo là chạy được ngay)

### Bước 1 — Tạo một giọng mới
1. Vào tab **🎚️ Quản lý giọng**.
2. Ở phần **"➕ Tạo giọng mới từ audio mẫu"**:
   - **Tên giọng**: đặt tên dễ nhớ, ví dụ *Anh Nam*.
   - **Audio mẫu**: bấm **"Chọn..."** rồi chọn file ghi âm giọng mẫu (**3–10 giây**, nói rõ, không ồn).
   - **Lời thoại mẫu**: bấm **"✨ Tự nhận diện lời thoại"** để app tự điền (hoặc tự gõ lại đúng câu trong file).
3. Bấm **"➕ Tạo & lưu giọng"**.
4. App sẽ tạo xong và **tự phát một câu mẫu** bằng giọng vừa tạo để bạn nghe thử có giống không.

> [Ảnh: phần Tạo giọng mới]

### Bước 2 — Tạo audio từ văn bản
1. Vào tab **🔊 Tạo giọng nói**.
2. Phần **"Nguồn giọng"**: chọn **"Dùng giọng đã lưu"** rồi chọn tên giọng vừa tạo.
3. Phần **"Văn bản cần đọc"**: dán nội dung muốn đọc.
4. Bấm **"🔊 Tạo giọng nói"** → đợi xử lý (có thanh tiến trình).
5. Xong, dùng **▶ Nghe** để nghe, **💾 Lưu...** để lưu file ra nơi khác.

> [Ảnh: tab Tạo giọng nói, đánh dấu Nguồn giọng / Văn bản / nút Tạo]

---

## 7. Chi tiết các chức năng

### 7.1. Nguồn giọng (tab Tạo giọng nói)
Có 3 cách chọn giọng:
- **Dùng giọng đã lưu** — chọn giọng đã tạo trước đó. Có nút **🔊 Nghe thử giọng này** để nghe trước, nút **↻** để làm mới danh sách.
- **Dùng audio mẫu trực tiếp** — đưa thẳng file ghi âm vào mà không cần lưu giọng.
- **Thiết kế giọng (mô tả bằng lời)** — gõ mô tả giọng mong muốn bằng tiếng Anh (ví dụ: *a calm middle-aged male voice, deep pitch, warm tone*).

### 7.2. Bảng "Tùy chọn" (cột phải)
- **Ngôn ngữ**: chọn ngôn ngữ của văn bản (có Tiếng Việt, English…).
- **Tốc độ**: nhanh/chậm khi đọc (mặc định 1.00x).
- **Ngắt nghỉ giữa câu**: thêm khoảng lặng giữa các câu cho tự nhiên (mặc định 0.30s).
- **Độ giống giọng**: càng cao càng giống giọng mẫu, nhưng quá cao dễ bị cứng/méo (mặc định 2.5 — khuyên 2.5–3.0).
- **Giảm tiếng thở**: làm nhỏ tiếng thở/tạp âm nền (mặc định 30%).
- **Chất lượng**: Nhanh / Chuẩn / Cao (càng cao càng đẹp nhưng lâu hơn).

> [Ảnh: bảng Tùy chọn với các thanh trượt]

> 💡 **Mẹo giọng giống hơn:** dùng audio mẫu **sạch, rõ, không nhạc nền**; nếu chưa giống thì tăng "Độ giống giọng" hoặc dùng mẫu dài/rõ hơn.

### 7.3. Tự động lưu
- Tích **"Tự động lưu vào:"** để mỗi lần tạo xong tự lưu file vào thư mục bạn chọn.
- **"Đổi thư mục..."** để chọn nơi lưu; **"Mở"** để mở nhanh thư mục đó.

### 7.4. Xuất phụ đề .SRT (chia cảnh) — dành cho người dựng video
Tính năng này tạo kèm **file .srt** chia kịch bản thành từng **cảnh** để bạn dựng video (mỗi cảnh = 1 ảnh hoặc 1 clip).

- Tích **"Xuất phụ đề .SRT (chia cảnh)"**.
- Chọn mục đích:
  - **🖼️ Video ảnh tĩnh** — mỗi cảnh ngắn hơn (hợp khi tạo ảnh tĩnh, cần mô tả chi tiết).
  - **🎬 Clip từ ảnh** — mỗi cảnh dài hơn (hợp khi tạo clip động, ví dụ bằng Veo3).
- **"Mỗi cảnh: ___ s"** — chỉnh độ dài mong muốn mỗi cảnh.
- Mọi cảnh luôn nằm trong khoảng **4–10 giây** (không quá ngắn, không vượt giới hạn công cụ làm video).

File .srt được lưu cùng tên và cùng thư mục với file audio.

> [Ảnh: hàng tùy chọn SRT]

### 7.5. Chia cảnh bằng AI (tùy chọn — cần API key riêng)
Bình thường app tự chia cảnh bằng thuật toán. Nếu muốn chia cảnh **thông minh hơn theo ý nghĩa** (gom các câu cùng một ý vào một cảnh), bạn có thể bật AI:

1. Tích **"Chia cảnh bằng AI"**.
2. Chọn **nhà cung cấp**: Gemini / OpenAI / Claude (tùy bạn có loại API key nào).
3. Dán **API key** của bạn vào ô **"API key"**, bấm **💾 Lưu key**.
4. Bấm **🔌 Test** để kiểm tra key có hoạt động không.
5. Bấm **↻ Cập nhật model** để lấy danh sách model mới nhất, rồi bấm vào ô **"Chọn Model ▾"** để chọn model.

> Lưu ý:
> - Mỗi loại (Gemini/OpenAI/Claude) lưu **key riêng**, không ghi đè lên nhau.
> - Nếu **không bật AI** hoặc **chưa có key**, app vẫn chia cảnh bình thường bằng thuật toán có sẵn.
> - **Mốc thời gian luôn lấy từ audio thật**, AI chỉ quyết định chỗ ngắt cảnh → file SRT luôn khớp tiếng và đúng giới hạn 4–10 giây.
> - API key được lưu **trên máy bạn**, không gửi đi đâu khác.

> [Ảnh: hàng tùy chọn Chia cảnh bằng AI + ô Model + ô API key]

### 7.6. Kết quả
Sau khi tạo xong:
- **▶ Nghe** — nghe thử audio vừa tạo.
- **■ Dừng** — dừng phát.
- **💾 Lưu...** — lưu file audio ra nơi bạn chọn.

---

## 8. Quản lý giọng (tab 🎚️ Quản lý giọng)

- **Các giọng đã lưu**: danh sách giọng. Chọn 1 giọng rồi bấm **🗑 Xóa giọng đang chọn** để xóa.
- **📥 Import giọng (.pt)...**: nạp giọng từ file `.pt` có sẵn (chọn được nhiều file cùng lúc).
- **➕ Tạo giọng mới từ audio mẫu**: như đã hướng dẫn ở Mục 6 — Bước 1.

> 💡 Khi bạn xóa một giọng, app **ghi nhớ** và sẽ **không tự khôi phục lại** giọng đó ở lần mở sau.

---

## 9. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân & cách xử lý |
|---|---|
| **Lần đầu mở rất lâu / đứng ở 1%** | Đang tải model AI (~4.7 GB). Đợi mạng tải xong. Nếu báo lỗi tải, kiểm tra Internet rồi mở lại. |
| **Clone giọng chậm bất thường** | Có thể bạn đang **mở 2 cửa sổ app cùng lúc** → cạn bộ nhớ GPU. Hãy chỉ mở **một** cửa sổ. (Bản mới đã tự chặn mở 2 lần.) |
| **Chạy bằng CPU, rất chậm** | Máy không có GPU NVIDIA hoặc driver chưa đúng. App vẫn chạy nhưng chậm — nên dùng máy có GPU. |
| **Giọng tạo ra không giống** | Dùng audio mẫu rõ hơn/dài hơn, không có nhạc nền; tăng "Độ giống giọng" lên 2.8–3.0. |
| **Bật AI báo lỗi (401/400…)** | Kiểm tra đã dán **đúng key của đúng nhà cung cấp** chưa, bấm 💾 Lưu key rồi 🔌 Test lại. Lỗi AI **không** làm hỏng việc xuất SRT (app tự dùng cách chia offline). |
| **Audio mẫu quá dài** | Nên dùng mẫu **3–10 giây**; mẫu quá dài bị cắt bớt và có thể giảm chất lượng. |

---

## 10. Câu hỏi thường gặp (FAQ)

**Hỏi: Tôi có cần Internet để tạo giọng không?**
Đáp: Chỉ cần Internet ở **lần đầu** (tải model) và khi dùng **Chia cảnh bằng AI**. Việc tạo giọng bình thường chạy offline trên máy bạn.

**Hỏi: File audio và giọng đã tạo lưu ở đâu?**
Đáp: Trong thư mục `user_data` của ứng dụng (giọng nằm trong `user_data/voices`, audio xuất ra trong `user_data/outputs`). **Không nên xóa thư mục này.**

**Hỏi: Có tốn tiền không?**
Đáp: Ứng dụng và việc tạo giọng **miễn phí**. Chỉ khi bạn **tự dùng API key trả phí** cho tính năng "Chia cảnh bằng AI" thì mới phát sinh chi phí theo nhà cung cấp đó.

**Hỏi: Dùng được tiếng Việt không?**
Đáp: Có. Chọn "Tiếng Việt" ở phần Ngôn ngữ.

---

*Tài liệu nguồn cho Cowork — phiên bản 2026-06-04. Vui lòng chuyển thành PDF hướng dẫn hoàn chỉnh theo các yêu cầu ở đầu tài liệu.*
