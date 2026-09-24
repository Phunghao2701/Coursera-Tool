# Phase 02: Bot Lifecycle Control & Event Hooks

**Phase ID:** `phase-02-bot-lifecycle-control`  
**Stories Covered:** `P1` (Start/Stop emergency control, Real-time log streaming, Progress tracking)  

---

## Mục tiêu
Tái cấu trúc `CourseraBot` và hệ thống logger để có thể chạy độc lập trong background thread, truyền nhận dữ liệu sự kiện (log, tiến độ bài học) tới WebSocket hub, và ngắt khẩn cấp ngay lập tức khi nhận tín hiệu Stop.

## Phạm vi công việc
- **Nâng cấp `utils/logger.py`:**
  - Thêm một `BroadcastLogHandler` kế thừa từ `logging.Handler` để đẩy mọi dòng log vào hàng đợi (queue) phát tán của WebSocket mà vẫn giữ nguyên màu ANSI trên terminal.
- **Nâng cấp `bot.py` (`CourseraBot`):**
  - Nhận tham số tùy chọn: `course_url`, `on_progress_callback`, `on_status_callback`.
  - Thêm cờ `self.stop_requested = False`.
  - Triển khai phương thức `emergency_stop()`: Đặt `stop_requested = True`, chủ động gọi `self.driver.quit()` hoặc kill process Chrome ngay lập tức.
  - Chèn kiểm tra `if self.stop_requested: break` vào các vòng lặp polling (`_wait_for_video_end`, `_countdown`, vòng lặp duyệt `items`).
  - Hỗ trợ lưu trữ Chrome user-data-dir nếu có cấu hình thư mục lưu session.
- **Tạo `bot_runner.py`:**
  - Điều phối chạy `CourseraBot` trên `threading.Thread`.
  - Cập nhật `BotStateManager` khi bot bắt đầu, đổi bài, hoàn thành hoặc gặp lỗi.

## Files/Modules bị ảnh hưởng
- `utils/logger.py`
- `bot.py`
- `bot_runner.py` (tạo mới)

## Dependencies
- Phụ thuộc `phase-01-web-core-api` (cần `BotStateManager` và WebSocket hub để nhận event).

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Khởi động bot bằng hàm `bot_runner.start(course_url)` từ Python script mà không bị block luồng chính.
- Mọi log từ bot được gửi tới callback queue trong thời gian < 100ms.
- Khi gọi `bot_runner.emergency_stop()`, bot ngừng hoạt động và Chrome đóng trong vòng < 3 giây mà không ném ngoại lệ chưa xử lý.

## Rủi ro & Ghi chú
- Selenium có thể raise `WebDriverException` khi driver bị `quit()` từ thread khác; cần catch ngoại lệ này để clean-up một cách êm ái, coi đó là trạng thái "Stopped by user".
