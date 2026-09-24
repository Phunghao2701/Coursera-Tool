# Phase 02: Course Scanner & Selective Learning Runner

**Phase ID:** `phase-02-course-scanner-selective-runner`  
**Stories Covered:** `P1` (Course Syllabus Scanning, Selective Execution)  

---

## Mục tiêu
Tạo endpoint API `/api/scan` để quét và trả về cấu trúc danh sách bài học của khóa học, đồng thời nâng cấp `CourseraBot` và `bot_runner` để hỗ trợ lọc và chỉ chạy các bài học được người dùng tick chọn.

## Phạm vi công việc
- Tạo hàm scanner trong `bot_runner.py` (hoặc `scanner.py`):
  - Khởi tạo Chrome Headless tạm thời.
  - Điều hướng tới `course_url`.
  - Gọi `get_all_course_items(driver)`.
  - Trả về danh sách bài học: `[{"name": str, "url": str, "type": str, "completed": bool}]`.
  - Đóng trình duyệt quét an toàn.
- Cập nhật `server.py`:
  - Thêm endpoint `POST /api/scan`:
    - Kiểm tra nếu `state_manager.status == 'running'` -> Từ chối với mã 400 ("Bot đang chạy, không thể quét lúc này").
    - Gọi hàm quét và trả về kết quả JSON danh sách bài.
  - Cập nhật endpoint `POST /api/start`:
    - Nhận thêm payload tùy chọn: `selected_urls: list[str]`.
- Cập nhật `CourseraBot` trong `bot.py`:
  - Nhận thêm tham số `selected_urls: Optional[list[str]] = None`.
  - Trong vòng lặp `run()`: Nếu `selected_urls` được cung cấp và `item['url']` không nằm trong danh sách này -> Ghi log skip và bỏ qua, chuyển sang bài tiếp theo.

## Files/Modules bị ảnh hưởng
- `bot.py`
- `bot_runner.py`
- `server.py`

## Dependencies
- Phụ thuộc `phase-01-settings-history-backend` (cần nạp email/password từ settings khi đăng nhập quét nếu trang yêu cầu).

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Gọi `POST /api/scan` với một URL khóa học -> Trả về danh sách JSON các bài học kèm type `video`, `reading`, `discussion`.
- Gọi `POST /api/start` kèm `selected_urls = [url1, url2]` -> Bot chỉ xử lý 2 bài này và bỏ qua tất cả bài còn lại.

## Rủi ro & Ghi chú
- Quá trình quét mất 10–25s, cần đảm bảo timeout không bị ngắt giữa chừng và tài nguyên Chrome quét được dọn dẹp triệt để trong `finally`.
