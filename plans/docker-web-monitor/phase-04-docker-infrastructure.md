# Phase 04: Docker Infrastructure & Packaging

**Phase ID:** `phase-04-docker-infrastructure`  
**Stories Covered:** `P1` (Docker Containerization, Session persistence via Volumes)  

---

## Mục tiêu
Đóng gói toàn bộ ứng dụng (FastAPI server + Chromium Headless + Chromedriver + Python dependencies) vào Docker, cung cấp `docker-compose.yml` để người dùng có thể triển khai lên VPS chỉ với một câu lệnh.

## Phạm vi công việc
- Tạo `Dockerfile`:
  - Base image: `python:3.11-slim` hoặc `ubuntu:22.04`.
  - Cài đặt Chromium, Chromium-driver và các thư viện hệ thống cần thiết cho headless browser.
  - Cài đặt Python requirements (`requirements.txt`).
  - Thiết lập user không phải root (nếu cần) hoặc flags phù hợp (`--no-sandbox`, `--disable-dev-shm-usage`).
  - Thiết lập lệnh chạy khởi động: `CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]`.
- Tạo `docker-compose.yml`:
  - Map port `8000:8000`.
  - Thiết lập `shm_size: '2gb'` để ngăn ngừa Chromium bị crash khi render video/DOM nặng.
  - Mount file `.env` vào container.
  - Mount volume `./data/chrome-profile:/app/data/chrome-profile` để lưu giữ cookie đăng nhập Coursera.
  - Mount volume `./logs:/app/logs`.
- Cập nhật `.gitignore` để bỏ qua `data/chrome-profile/`.
- Cung cấp script hỗ trợ trên Linux: `deploy.sh` hoặc hướng dẫn nhanh.

## Files/Modules bị ảnh hưởng
- `Dockerfile` (tạo mới)
- `docker-compose.yml` (tạo mới)
- `.dockerignore` (tạo mới)
- `.gitignore` (bổ sung ignore thư mục `data/`)

## Dependencies
- Phụ thuộc `phase-01-web-core-api`, `phase-02-bot-lifecycle-control`, `phase-03-frontend-dashboard`.

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Chạy lệnh `docker compose build` không có lỗi.
- Chạy lệnh `docker compose up -d` container khởi động ở trạng thái `healthy`/`running`.
- Truy cập `http://localhost:8000` (hoặc IP VPS) hiển thị giao diện dashboard.
- Đăng nhập thử, khởi động bot bên trong container, kiểm tra Chrome Headless mở và chạy thành công mà không bị crash `DevToolsActivePort`.
- Restart container (`docker compose restart`), cookie session trong `./data/chrome-profile` vẫn được bảo toàn.

## Rủi ro & Ghi chú
- Chrome và Chromedriver trên Linux phải cùng phiên bản; sử dụng gói `chromium` và `chromium-driver` chính thức của APT repository để đảm bảo tuyệt đối tương thích phiên bản.
