# Brainstorm: Docker Containerization & Web Monitor Dashboard for Coursera Bot

**Date:** 2026-09-24

## Ideas Explored

1. **Native Batch Execution (.bat on Windows):** Chạy trực tiếp trong command line Windows. Đơn giản nhưng không phù hợp để chạy 24/7 trên VPS, thiếu giao diện điều khiển từ xa.
2. **Multi-container Architecture (Web + Redis + Celery):** Tách riêng Web Server, message broker và worker. Mạnh mẽ nhưng quá cồng kềnh (over-engineered) đối với công cụ cá nhân, ngốn nhiều tài nguyên VPS.
3. **Single Container with FastAPI & WebSocket (Selected):** Đóng gói Chrome Headless, Python web server (FastAPI) và CourseraBot trong một Dockerfile duy nhất. Giao diện web trực quan, stream log thời gian thực qua WebSocket, bảo mật bằng mật khẩu, điều khiển Start/Stop khẩn cấp và lưu cookies qua Docker Volume.

## User's Direction

- **Triển khai VPS 24/7:** Chạy nền liên tục bên trong môi trường Docker trên server.
- **Web Dashboard:** Thay thế script batch bằng giao diện web hiển thị thẻ đếm tiến độ trực quan, cho phép nhập URL khóa học trước khi Start, và stream log trực tiếp dạng terminal console.
- **Dừng khẩn cấp (Emergency Stop):** Khi bấm nút Stop trên web, hệ thống phải ngắt tác vụ và đóng trình duyệt lập tức.
- **Bảo mật:** Tích hợp mật khẩu bảo vệ đơn giản để ngăn truy cập trái phép từ internet khi mở port trên VPS.
- **Lưu phiên đăng nhập:** Mount volume lưu dữ liệu Chrome (cookies / user-data-dir) để duy trì session đăng nhập sau khi khởi động lại container.

## Open Questions

- Cổng mặc định cho Web Dashboard (dự kiến: `8000` hoặc `8080`).
- Phương thức notify khi hoàn thành khóa học (Web notification, Telegram bot hook tương lai).

## Risks

1. **Chrome Headless Crash / Memory Leak trên VPS cấu hình thấp:** Trình duyệt chạy lâu có thể chiếm nhiều RAM nếu không set cờ tối ưu (`--disable-dev-shm-usage`, memory limit).
2. **Coursera Cloudflare / Captcha Block:** Chạy trên dải IP data center của VPS có khả năng bị Coursera yêu cầu Captcha khi đăng nhập lần đầu; việc lưu cookie profile qua Docker volume là thiết yếu để giảm thiểu rủi ro này.
3. **Thread Safety khi dừng khẩn cấp:** Cần xử lý kill process / driver an toàn trong Python thread để không để lại tiến trình Chrome mồ côi (zombie processes) ngầm trong container.
