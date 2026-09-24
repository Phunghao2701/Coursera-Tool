# Spec: Full-Control Web Dashboard & Selective Learning for Coursera Bot

**Date:** 2026-09-24  
**Status:** Ready  

---

## Problem Statement

Hiện tại, người dùng vẫn phải cấu hình tài khoản (Email/Password) và các thông số (tốc độ video, thời gian đọc) thông qua file `.env` hoặc dòng lệnh, đồng thời bot chỉ có thể chạy tuần tự toàn bộ khóa học mà không cho phép chọn lọc bài học mong muốn. Người dùng cần một **Web Dashboard toàn năng** chia tab trực quan, cho phép chỉnh sửa mọi cấu hình trên web, quét trước danh sách bài học để tick chọn bài cần học, và theo dõi lịch sử các lần chạy.

---

## User Stories

<!-- P1 = MVP (must ship), P2 = nice-to-have, P3 = future/out-of-scope -->

- **[P1]** As a user, I want to edit and save my Coursera account credentials (Email, Password) and bot tunables (Video Speed, Reading Wait Time, Discussion Reply Text) directly in a Settings Tab so that I never have to SSH into the VPS to edit configuration files.
  *Accepted when:* Người dùng nhập thông tin trong tab Cài đặt, bấm "Lưu Cài Đặt", hệ thống ghi vào `data/settings.json`, các phiên chạy sau tự động áp dụng thông số mới.

- **[P1]** As a user, I want to click a "Quét Khóa Học" (Scan) button to discover all lessons across modules/weeks with a visual progress indicator so that I know what content exists in the course.
  *Accepted when:* Bấm nút "Quét", UI hiển thị spinner kèm thông báo đang quét; sau khi quét xong hiển thị danh sách đầy đủ các bài học (tên, loại bài, trạng thái hoàn thành).

- **[P1]** As a user, I want to selectively check/uncheck lessons and use quick filter buttons ("Chọn tất cả", "Chỉ chọn Video", "Chỉ chọn Reading", "Bỏ chọn tất cả") before starting so that I only automate the lessons I care about.
  *Accepted when:* Người dùng tick chọn một số bài và bấm "Khởi Động Bot", bot chỉ xử lý đúng danh sách các bài đã chọn và bỏ qua các bài không được tick.

- **[P1]** As a user, I want the Dashboard to be organized into 3 clear tabs: "Bảng Điều Khiển & Log", "Cài Đặt", and "Lịch Sử" so that navigation is clean, intuitive, and modern.
  *Accepted when:* Người dùng có thể click chuyển đổi qua lại giữa 3 tab mượt mà, không bị mất trạng thái hay đứt kết nối WebSocket log.

- **[P2]** As a user, I want to view a History Tab listing past course runs (Course Name/URL, Date/Time, Items Completed, Status) so that I can keep track of what I have automated.
  *Accepted when:* Khi bot hoàn thành hoặc dừng lại, một bản ghi lịch sử được lưu vào `data/history.json` và hiển thị dạng danh sách trong tab Lịch sử.

- **[P3]** _(Out of scope for this phase)_:
  * Lên lịch tự động chạy theo giờ (Cron job scheduler từ web).
  * Hỗ trợ chuyển đổi nhanh giữa nhiều tài khoản Coursera (Multi-account profile switcher).

---

## Functional Requirements

1. **FR-01: Tab Navigation System**
   * Giao diện SPA chia làm 3 tab:
     * `Tab 1: Bảng Điều Khiển (Dashboard)` (URL, Nút Quét, Checklist bài học, Nút Start/Stop, Cards thống kê, Console log).
     * `Tab 2: Cài Đặt (Settings)` (Form cấu hình tài khoản, thông số bot, đổi mật khẩu dashboard).
     * `Tab 3: Lịch Sử (History)` (Bảng danh sách các khóa học đã chạy).
   * Chuyển tab bằng JavaScript, không reload trang, giữ nguyên kết nối WebSocket log ở nền.

2. **FR-02: Settings API & Data Persistence**
   * Endpoint `GET /api/settings`: Trả về cấu hình hiện tại (ẩn password dưới dạng masked hoặc placeholder `******` để bảo mật).
   * Endpoint `POST /api/settings`: Lưu cấu hình mới vào file `data/settings.json`.
   * Tự động ưu tiên đọc từ `data/settings.json`, nếu chưa có sẽ fallback về `config.py` / `.env`.

3. **FR-03: Course Scanning API & UI Feedback**
   * Endpoint `POST /api/scan`: Nhận `course_url`, khởi động trình duyệt quét cấu trúc khóa học qua `get_all_course_items()`, trả về mảng danh sách bài học: `[{"name": ..., "url": ..., "type": ..., "completed": ...}]`.
   * Giao diện hiển thị modal hoặc banner tiến trình quét (loading animation) trong lúc API xử lý.

4. **FR-04: Selective Learning Execution**
   * Giao diện hiển thị danh sách bài học dạng table/list có checkbox từng bài và các nút bấm tiện ích:
     * *Chọn tất cả* (Select All)
     * *Chỉ chọn Video* (Select Only Videos)
     * *Chỉ chọn Reading* (Select Only Readings)
     * *Bỏ chọn tất cả* (Deselect All)
   * Endpoint `POST /api/start`: Hỗ trợ nhận thêm danh sách `selected_urls: list[str]`.
   * `CourseraBot`: Lọc chỉ chạy các item có URL nằm trong `selected_urls` (nếu danh sách này được truyền vào).

5. **FR-05: History Tracking & Persistence**
   * Tự động ghi lại kết quả phiên chạy vào `data/history.json` khi bot kết thúc hoặc dừng:
     * `id`: timestamp/uuid
     * `course_url`: URL khóa học
     * `started_at`: Thời gian bắt đầu
     * `finished_at`: Thời gian kết thúc
     * `items_completed`: Số lượng bài đã xong
     * `status`: "Completed" | "Stopped" | "Error"
   * Endpoint `GET /api/history`: Trả về danh sách lịch sử sắp xếp từ mới nhất đến cũ nhất.

---

## Non-Functional Requirements

- **Security:** File `data/settings.json` và `data/history.json` nằm ngoài thư mục static, chỉ người dùng đã nhập đúng `DASHBOARD_PASSWORD` mới có quyền đọc/ghi.
- **Performance:** Chuyển đổi giữa các tab diễn ra ngay lập tức (< 50ms).
- **Usability:** Giao diện responsive trên cả mobile và desktop, bảng checklist bài học có thanh cuộn riêng khi danh sách bài dài (> 30 bài).
- **Reliability:** Nếu quá trình quét bị gián đoạn hoặc lỗi, hiển thị thông báo lỗi thân thiện thay vì làm đơ giao diện.

---

## Success Criteria

- [ ] Mở Tab Cài Đặt, đổi Email & Mật khẩu hoặc Tốc độ video sang 1.5x -> Bấm lưu -> Khởi động bot thấy áp dụng ngay tốc độ 1.5x.
- [ ] Nhập URL khóa học, bấm nút "Quét Khóa Học" -> Thấy loading -> Xuất hiện danh sách đầy đủ các bài học kèm phân loại icon (Video, Reading, Discussion).
- [ ] Bấm nút "Chỉ chọn Video" -> Tất cả bài Video được tick, các bài Reading/Discussion bị bỏ tick -> Bấm Start -> Bot chỉ xem video và bỏ qua các bài reading.
- [ ] Khi bot chạy xong, mở Tab Lịch Sử thấy bản ghi phiên chạy hiển thị đầy đủ ngày giờ và số bài hoàn thành.
- [ ] Khởi động lại container Docker (`docker compose restart`), toàn bộ cài đặt trong Tab Settings và lịch sử trong Tab History vẫn còn nguyên vẹn.

---

## Out of Scope

- Chức năng hẹn giờ chạy tự động theo lịch (Cron scheduler).
- Quản lý đồng thời nhiều tài khoản Coursera cùng lúc.

---

## Assumptions

- Người dùng đã cấu hình và đăng nhập thành công vào Web Dashboard qua mật khẩu `DASHBOARD_PASSWORD`.
- Thư mục `./data` đã được mount volume trong `docker-compose.yml` (đã hoàn thành ở đợt trước).

---

## [NEEDS CLARIFICATION]

*(None - Tất cả câu hỏi đã được làm rõ hoàn toàn)*
