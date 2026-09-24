# Phase 03: Frontend Web Dashboard

**Phase ID:** `phase-03-frontend-dashboard`  
**Stories Covered:** `P1` (Dashboard UI, Course URL input, Live logs, Counters), `P2` (Clear log, Auto-scroll toggle)  

---

## Mục tiêu
Xây dựng giao diện Web Dashboard hoàn chỉnh bằng HTML5, CSS3 và Vanilla JS hiện đại, phong cách Dark Mode công nghệ cao, responsive và cập nhật mượt mà theo thời gian thực qua WebSocket.

## Phạm vi công việc
- Tạo cấu trúc thư mục tĩnh: `static/` (hoặc `web/`):
  - `index.html`: Cấu trúc dashboard (Header, Login modal, Thẻ thống kê, Form điều khiển, Cửa sổ log).
  - `style.css`: Thiết kế Dark mode sang trọng, hiệu ứng glassmorphism, badge trạng thái đổi màu theo `IDLE` (xám/vàng), `RUNNING` (xanh lục phát sáng), `STOPPING` (đỏ).
  - `app.js`: Xử lý logic phía client:
    - Quản lý phiên đăng nhập (nhập mật khẩu, lưu token cookie).
    - Kết nối và auto-reconnect WebSocket tới `/ws/logs` và `/ws/status`.
    - Render log ANSI màu vào cửa sổ console giả lập terminal.
    - Cập nhật các thẻ đếm: Tổng bài, Đã học (%), Đang học bài gì, Số bài Video/Reading/Discussion/Graded.
    - Bắt sự kiện bấm nút `Start Bot` (gọi `POST /api/start`) và `Emergency Stop` (gọi `POST /api/stop`).
    - Nút Clear log và bật/tắt auto-scroll.

## Files/Modules bị ảnh hưởng
- `static/index.html` (tạo mới)
- `static/style.css` (tạo mới)
- `static/app.js` (tạo mới)
- `server.py` (mount thư mục static và serve index.html)

## Dependencies
- Phụ thuộc `phase-01-web-core-api` (cần API và WebSocket endpoints).

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Giao diện hiển thị trực quan, không có lỗi JS console (`F12`).
- Nhập mật khẩu đúng -> Giao diện chính mở ra ngay lập tức.
- Bấm nút Start -> Nút chuyển sang trạng thái disabled, nút Stop kích hoạt, log bắt đầu tuôn ra trên cửa sổ console.
- Thanh tiến trình % tăng dần khi bot hoàn thành các bài học.

## Rủi ro & Ghi chú
- Giới hạn số lượng dòng log hiển thị trong DOM (ví dụ tối đa 1000 dòng mới nhất) để tránh làm lag trình duyệt client khi bot chạy nhiều giờ liên tục.
