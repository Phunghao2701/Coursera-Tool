# Phase 03: Three-Tab Frontend UI & Interactive Controls

**Phase ID:** `phase-03-three-tab-frontend-ui`  
**Stories Covered:** `P1` (Tab-based Navigation, Selective Learning UI, Settings UI), `P2` (History UI)  

---

## Mục tiêu
Tái cấu trúc giao diện Dashboard thành hệ thống 3 Tab hiện đại, bổ sung giao diện quét và chọn lọc bài học với các nút lọc nhanh, form cài đặt tài khoản/thông số, và bảng hiển thị lịch sử chạy.

## Phạm vi công việc
- **Cập nhật `static/index.html`:**
  - Thêm thanh điều hướng Tab Bar ở đầu trang:
    - `Tab 1: 🎮 Điều Khiển & Log`
    - `Tab 2: ⚙️ Cài Đặt`
    - `Tab 3: 📜 Lịch Sử`
  - **Nội dung Tab 1 (Bảng Điều Khiển):**
    - Input URL + Nút **"🔍 Quét Khóa Học"** + Nút **"Khởi Động Bot"** + Nút **"Dừng Khẩn Cấp"**.
    - Khu vực hiển thị danh sách bài học sau khi quét:
      - Thanh công cụ chọn nhanh: *"Chọn tất cả"*, *"Chỉ chọn Video"*, *"Chỉ chọn Reading"*, *"Bỏ chọn tất cả"*.
      - Bảng/checklist bài học: Checkbox, Icon phân loại (🎬 Video, 📖 Đọc, 💬 Thảo luận, 📝 Bài tập), Tên bài học, Trạng thái (Đã xong hay chưa).
    - Grid 4 thẻ thống kê + Cửa sổ terminal log console trực tiếp.
  - **Nội dung Tab 2 (Cài Đặt):**
    - Form trực quan: Email Coursera, Mật khẩu Coursera, Tốc độ video (1x, 1.25x, 1.5x, 2x), Thời gian đọc (giây), Nội dung reply thảo luận, Mật khẩu Web Dashboard.
    - Nút "💾 Lưu Cài Đặt".
  - **Nội dung Tab 3 (Lịch Sử):**
    - Bảng hiển thị danh sách các phiên chạy: Tên/URL khóa học, Thời gian bắt đầu/kết thúc, Số bài đã hoàn thành, Trạng thái (Badge màu).
- **Cập nhật `static/style.css`:**
  - Style cho Tab Bar, active tab indicator, tab transition.
  - Style cho bảng checklist bài học (cuộn riêng, checkbox tùy chỉnh, badge loại bài).
  - Style cho form cài đặt và bảng lịch sử.
  - Spinner/Loading overlay khi đang quét khóa học.
- **Cập nhật `static/app.js`:**
  - Logic chuyển đổi tab không reload trang.
  - Xử lý nút "Quét Khóa Học": Hiện loading spinner, gọi `POST /api/scan`, render bảng checklist bài học.
  - Xử lý các nút lọc nhanh: Check/uncheck bài học theo phân loại.
  - Cập nhật hàm Start: Thu thập danh sách `selected_urls` từ các checkbox đang tick và gửi lên `POST /api/start`.
  - Xử lý Tab Cài đặt: Nạp dữ liệu từ `GET /api/settings`, lưu dữ liệu qua `POST /api/settings`.
  - Xử lý Tab Lịch sử: Nạp và render danh sách từ `GET /api/history`.

## Files/Modules bị ảnh hưởng
- `static/index.html`
- `static/style.css`
- `static/app.js`

## Dependencies
- Phụ thuộc `phase-01-settings-history-backend` và `phase-02-course-scanner-selective-runner`.

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Chuyển đổi qua lại giữa 3 Tab mượt mà, không bị ngắt kết nối WebSocket logs.
- Nhập URL, bấm "Quét" -> Hiện spinner -> Danh sách bài học xuất hiện đầy đủ.
- Bấm "Chỉ chọn Video" -> Chỉ các bài Video được tick chọn.
- Vào Tab Cài Đặt, sửa tốc độ video thành 1.5x và bấm Lưu -> Thông báo lưu thành công.
- Vào Tab Lịch Sử -> Hiển thị danh sách các phiên chạy trước.

## Rủi ro & Ghi chú
- Giữ giao diện responsive trên màn hình điện thoại di động (Tab bar cuộn ngang hoặc tự thu gọn).
