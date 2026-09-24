# Spec: Docker Containerization & Web Monitor Dashboard for Coursera Bot

**Date:** 2026-09-24
**Status:** Ready

---

## Problem Statement

Hiện tại, Coursera Bot chỉ chạy qua file batch `.bat` trên máy tính cục bộ (Windows), yêu cầu mở máy liên tục và thiếu giao diện quản lý từ xa. Người dùng cần một giải pháp đóng gói Docker có Web Dashboard để triển khai lên VPS chạy 24/7, có thể nhập URL, bấm Start/Stop khẩn cấp, theo dõi tiến độ học và xem log trực tiếp từ bất kỳ trình duyệt nào.

---

## User Stories

<!-- P1 = MVP (must ship), P2 = nice-to-have, P3 = future/out-of-scope -->

- **[P1]** As a user, I want to access a password-protected Web Dashboard via my browser so that unauthorized people on the internet cannot access or control my bot on the VPS.
  *Accepted when:* Truy cập dashboard yêu cầu nhập đúng `DASHBOARD_PASSWORD` mới vào được giao diện chính; nếu sai sẽ từ chối truy cập.

- **[P1]** As a user, I want to enter or change the `COURSE_URL` directly on the Web Dashboard and click "Start" so that I can run new courses without touching config files or restarting the container.
  *Accepted when:* Người dùng nhập URL khóa học, bấm nút "Start", bot nhận đúng URL mới và bắt đầu quét/chạy bài học trong background.

- **[P1]** As a user, I want to see real-time streaming logs in a terminal-like console on the dashboard so that I know exactly what the bot is doing at any given second.
  *Accepted when:* Log từ `logger.py` được đẩy tức thời qua WebSocket lên trình duyệt với độ trễ < 500ms mà không cần reload trang.

- **[P1]** As a user, I want to see live status cards (Bot State: Idle/Running, Current Item Name, Completed / Total, Success / Skipped / Failed counters) so that I have a quick high-level overview of progress.
  *Accepted when:* Khi bot chuyển bài hoặc hoàn thành bài, các thẻ đếm và thanh tiến độ % trên giao diện được cập nhật tự động.

- **[P1]** As a user, I want to click an "Emergency Stop" button to immediately abort bot execution and kill the browser instance so that I can stop it instantly if something goes wrong.
  *Accepted when:* Bấm nút "Stop", trạng thái bot chuyển về `Idle` trong vòng 3 giây, driver đóng lập tức và không còn tiến trình treo.

- **[P1]** As a user, I want the bot and Chrome environment to be fully containerized in Docker with volume mounting for Chrome session data so that I can deploy with a single `docker compose up -d` command and retain login cookies.
  *Accepted when:* Container build thành công từ Dockerfile chuẩn (bao gồm Chromium/Chrome Headless + Python 3), và thư mục user data được mount để không bị mất cookie khi restart container.

- **[P2]** As a user, I want a toggle to clear the current log window or download logs so that I can inspect past runs easily.
  *Accepted when:* Nút "Clear Logs" xóa nội dung hiển thị trên giao diện console web.

- **[P3]** _(Out of scope for this phase)_:
  * Quản lý đa tài khoản cùng lúc trong 1 dashboard.
  * Gửi thông báo hoàn thành khóa học qua Telegram/Discord webhook.

---

## Functional Requirements

1. **FR-01: Docker Containerization**
   * Cung cấp `Dockerfile` tối ưu dựa trên Linux (Debian slim / Ubuntu) cài đặt sẵn Chromium, Chromedriver tương thích và các dependency trong `requirements.txt`.
   * Cung cấp `docker-compose.yml` định nghĩa port mapping (mặc định `8000:8000`), biến môi trường từ `.env`, và volume mount (`./data/chrome-profile` cho browser session, `./logs` cho log files).

2. **FR-02: Web Application Server**
   * Xây dựng server backend bằng **FastAPI** phục vụ static web assets và cung cấp REST API / WebSocket.
   * Quản lý trạng thái bot (`idle`, `running`, `stopping`) qua thread-safe state manager.

3. **FR-03: Security & Authentication**
   * Đọc biến `DASHBOARD_PASSWORD` từ `.env`.
   * Hỗ trợ xác thực bảo vệ (Session token qua cookie hoặc HTTP Basic Auth) cho tất cả các route và WebSocket connection.

4. **FR-04: Real-time Communication (WebSocket)**
   * Tạo WebSocket endpoint `/ws/logs` stream liên tục log messages từ logger về client.
   * Tạo WebSocket endpoint `/ws/status` hoặc gửi kèm payload trạng thái tiến độ bài học (tên bài, % hoàn thành, số lượng đã xong/thất bại).

5. **FR-05: Web Dashboard UI**
   * Giao diện HTML5/CSS3/Vanilla JS hiện đại (Dark theme chuẩn dashboard công nghệ, responsive hoạt động tốt trên cả điện thoại và máy tính).
   * Thanh điều khiển: Ô nhập `Course URL`, nút `Start Bot` (active khi idle), nút `Emergency Stop` (active khi running).
   * Thẻ thống kê (Cards): Trạng thái Bot (Badge), Bài học hiện tại, Tỷ lệ hoàn thành (Progress bar %), Đếm loại bài (Reading, Video, Discussion, Graded/Skipped).
   * Cửa sổ Log Console: Hiển thị log màu, auto-scroll xuống dòng mới nhất, có nút pause auto-scroll và nút clear log.

6. **FR-06: Process & Lifecycle Management**
   * Bot chạy trong background thread hoặc managed subprocess.
   * Khi kích hoạt Stop, thực hiện terminate driver và giải phóng tài nguyên ngay lập tức (< 3s).

---

## Non-Functional Requirements

- **Performance:** Dung lượng RAM sử dụng của toàn bộ container (bao gồm Chrome Headless + FastAPI) không vượt quá 600MB khi chạy ổn định.
- **Latency:** Độ trễ từ khi bot phát sinh 1 dòng log tới khi xuất hiện trên giao diện Web qua WebSocket < 500ms.
- **Security:** Không hiển thị mật khẩu Coursera hay Dashboard password dạng plain text trên giao diện người dùng; port WebSocket phải được xác thực trước khi thiết lập kết nối.
- **Reliability:** Nếu trình duyệt gặp sự cố bất ngờ hoặc crash, backend bắt ngoại lệ, cập nhật trạng thái về `Error/Idle`, giải phóng tiến trình và hiển thị thông báo lỗi lên dashboard mà không làm sập server web.

---

## Success Criteria

- [ ] Build thành công Docker image từ `Dockerfile` và khởi chạy mượt mà bằng `docker compose up -d`.
- [ ] Truy cập `http://<ip-vps>:8000` hiển thị màn hình yêu cầu mật khẩu; sau khi đăng nhập thành công vào được Dashboard.
- [ ] Nhập URL khóa học và bấm "Start", bot khởi động Chrome Headless, đăng nhập Coursera và bắt đầu học.
- [ ] Console trên web hiển thị liên tục các dòng log theo thời gian thực tương đương với log trong terminal trước đây.
- [ ] Bấm nút "Emergency Stop", bot dừng lại ngay lập tức và trình duyệt đóng trong vòng 3 giây.
- [ ] Khởi động lại container (`docker compose restart`), cookie đăng nhập vẫn còn và không bị logout khỏi Coursera.

---

## Out of Scope

- Triển khai cụm Kubernetes hoặc multi-node cluster.
- Cơ chế giải CAPTCHA tự động bằng dịch vụ bên thứ ba (2Captcha, Anti-Captcha) - ưu tiên giữ session profile để tránh bị hỏi CAPTCHA.
- Giao diện chỉnh sửa toàn bộ file cấu hình `.env` từ web (chỉ hỗ trợ nhập URL khóa học và các thông số chạy cơ bản).

---

## Assumptions

- VPS của người dùng sử dụng hệ điều hành Linux (Ubuntu/Debian) có cài đặt sẵn Docker và Docker Compose.
- VPS có tối thiểu 1GB RAM và 10GB dung lượng ổ cứng khả dụng.
- Người dùng có thể mở port (mặc định 8000) trên firewall của VPS (UFW hoặc Security Group của nhà cung cấp Cloud).

---

## [NEEDS CLARIFICATION]

<!-- Đã được làm rõ toàn bộ ở giai đoạn Brainstorm -->
*(None - All questions resolved)*
