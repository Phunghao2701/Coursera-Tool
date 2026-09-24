# Plan: Full-Control Web Dashboard & Selective Learning for Coursera Bot

**Date:** 2026-09-24  
**Mode:** --hard  
**Risk:** normal — multi-file full-stack enhancement (settings API, syllabus scanner, selective runner, 3-tab frontend), fully testable with existing testbed.  
**Spec:** `plans/dashboard-full-control/spec.md`  

---

## Architecture Overview

Hệ thống nâng cấp Dashboard thành trung tâm quản trị toàn năng với 4 khối chính:
1. **Settings & History Data Persistence (`data/`):**
   - Quản lý đọc/ghi an toàn cho `data/settings.json` (tài khoản, thông số bot) và `data/history.json` (nhật ký chạy).
   - Tự động fallback về `.env` khi chưa có file cài đặt.
   - Endpoint bảo mật: `GET /api/settings`, `POST /api/settings`, `GET /api/history`.
2. **Course Syllabus Scanner & Selective Execution:**
   - Endpoint `POST /api/scan`: Chạy tác vụ quét danh sách bài học qua `get_all_course_items()`. Ngăn chặn quét khi bot đang chạy (`running`).
   - Cập nhật `CourseraBot` và `bot_runner`: Nhận tham số `selected_urls: list[str]`. Chỉ xử lý các bài học được tick chọn, bỏ qua các bài còn lại mà vẫn ghi nhận thống kê chính xác.
3. **Tab-based SPA Frontend (Vanilla JS / CSS):**
   - Tái cấu trúc giao diện thành 3 Tab:
     - **Tab 1: Bảng Điều Khiển & Giám Sát:** Form URL + Nút Quét -> Bảng Checklist bài học (kèm 4 nút lọc nhanh) -> Nút Start/Stop -> Thẻ thống kê + Console Log trực tiếp.
     - **Tab 2: Cài Đặt (Settings):** Form trực quan sửa email, password, tốc độ video, thời gian đọc, reply thảo luận.
     - **Tab 3: Lịch Sử (History):** Bảng hiển thị danh sách các khóa học đã chạy, thời gian và số bài hoàn thành.
4. **Data Continuity in Docker:**
   - Sử dụng thư mục `./data` đã được mount volume trong Docker để đảm bảo mọi thay đổi cấu hình và lịch sử không bao giờ bị mất khi restart container.

---

## Phases

- [ ] **phase-01-settings-history-backend**: Xây dựng module lưu trữ JSON, API Settings và API History trong `server.py`.
- [ ] **phase-02-course-scanner-selective-runner**: Xây dựng API Quét khóa học (`/api/scan`) và hỗ trợ lọc bài học (`selected_urls`) trong `CourseraBot`.
- [ ] **phase-03-three-tab-frontend-ui**: Thiết kế lại giao diện 3 Tab, bảng checklist bài học, form cài đặt và bảng lịch sử trong `index.html`, `style.css`, `app.js`.
- [ ] **phase-04-integration-verification**: Kiểm thử tích hợp toàn diện các luồng lưu cài đặt, quét bài, chọn bài và kiểm tra độ bền dữ liệu.

---

## Risks & Mitigations

1. **Bảo mật mật khẩu Coursera:**
   - *Risk:* Mật khẩu tài khoản có thể bị lộ nếu trả về nguyên bản trong API `GET /api/settings`.
   - *Mitigation:* API `GET /api/settings` sẽ ẩn mật khẩu (trả về placeholder `******`), chỉ cập nhật mật khẩu mới khi người dùng thực sự nhập giá trị mới.
2. **Xung đột tài nguyên khi Quét lúc Bot đang chạy:**
   - *Risk:* Quét khóa học trong khi bot đang học có thể gây tranh chấp trình duyệt hoặc quá tải RAM.
   - *Mitigation:* API `/api/scan` sẽ từ chối nếu `state_manager.status == 'running'`.
3. **Quá trình Quét (Scan) bị timeout:**
   - *Risk:* Một số khóa học dài có thể mất 20–30s để load hết các tuần.
   - *Mitigation:* Thiết lập timeout hợp lý, có khối `try/except/finally` đóng driver quét và trả về thông báo lỗi rõ ràng nếu URL không hợp lệ.
