# Plan: Docker Containerization & Web Monitor Dashboard for Coursera Bot

**Date:** 2026-09-24  
**Mode:** --hard  
**Risk:** high-risk — touches infrastructure (Docker/Chromium Headless containerization), web authentication, and process lifecycle management.  
**Spec:** `plans/docker-web-monitor/spec.md`  

---

## Architecture Overview

Hệ thống được thiết kế theo mô hình **All-in-One Container** tối ưu cho VPS:
1. **Web Core & State Manager (FastAPI):**
   - Chạy trên Uvicorn, phục vụ static frontend và WebSocket `/ws/logs` + `/ws/status`.
   - Quản lý trạng thái Bot theo finite-state: `IDLE` <-> `RUNNING` -> `STOPPING`.
   - Xác thực bảo mật: Middleware kiểm tra session cookie hoặc token dựa trên `DASHBOARD_PASSWORD`.
2. **Bot Runner & Event Hook:**
   - Bọc `CourseraBot` trong một background worker thread (không block event loop của FastAPI).
   - Custom `WebSocketLogHandler` gắn vào Python logging để stream log trực tiếp qua WebSocket queue.
   - Thêm cờ `stop_requested` và phương thức `emergency_stop()` đóng Chrome WebDriver ngay lập tức.
3. **Frontend Dashboard (Vanilla HTML/CSS/JS):**
   - Single-page application nhẹ, không dùng node_modules cồng kềnh.
   - Hiển thị badge trạng thái, thẻ đếm bài học, thanh tiến trình %, ô đổi `COURSE_URL`, nút Start/Stop.
   - Cửa sổ console log dark mode với tính năng tự động cuộn (auto-scroll) và xóa log (clear).
4. **Docker Packaging:**
   - Base image Debian Slim / Ubuntu cài Chromium & Chromedriver tương thích.
   - Cấu hình `shm_size: 2gb` để Chrome Headless không bị crash OOM trên VPS.
   - Mount Docker volume `./data/chrome-profile` duy trì cookie session đăng nhập giữa các lần restart.

---

## Phases

- [x] **phase-01-web-core-api**: Xây dựng backend FastAPI, xác thực bảo mật và State Manager.
- [x] **phase-02-bot-lifecycle-control**: Nâng cấp `CourseraBot` & `logger.py` hỗ trợ callback sự kiện và ngắt khẩn cấp.
- [x] **phase-03-frontend-dashboard**: Xây dựng giao diện Web Dashboard trực quan và kết nối WebSocket.
- [x] **phase-04-docker-infrastructure**: Đóng gói Dockerfile, docker-compose.yml và cấu hình Volume/SHM.
- [x] **phase-05-e2e-verification**: Kiểm thử luồng toàn diện E2E trên container và tài liệu hướng dẫn.

---

## Session Notes
<!-- Updated by cook automatically — do not edit manually -->

**Last active:** 2026-09-24 12:32  
**Phase in progress:** Completed (All phases finished)  
**Status:** All 5 phases implemented and ready for VPS deployment.  

### Decisions made this session
- Dashboard chạy cố định trên cổng `3987` (`http://<ip-vps>:3987`).
- Lưu trữ đệm chính xác 100 dòng log gần nhất để client mới kết nối hiển thị ngay lập tức.
- Bổ sung `shm_size: 2gb` trong Docker Compose để Chrome Headless không bị crash OOM khi chạy thời gian dài trên VPS.
- Mount Volume `./data/chrome-profile` duy trì cookie đăng nhập giữa các lần restart container.
- Cơ chế Dừng Khẩn Cấp (Emergency Stop) giải phóng WebDriver và dừng luồng tức thì (< 3s).

### Next immediate action
- Triển khai lên VPS bằng lệnh `docker compose up -d --build` hoặc `bash deploy.sh`.

---

## Risks & Mitigations

1. **Chromium crash do thiếu shared memory trong Docker:**
   - *Mitigation:* Thêm `shm_size: 2gb` và cờ `--disable-dev-shm-usage`, `--no-sandbox`, `--disable-gpu`, `--disk-cache-dir=/tmp/cache` trong Chrome options.
2. **Zombie Chrome process khi Stop khẩn cấp:**
   - *Mitigation:* `emergency_stop()` sẽ kill driver instance và dọn sạch tiến trình con thông qua `psutil` hoặc `driver.quit()`.
3. **Mất kết nối WebSocket khi mạng VPS không ổn định:**
   - *Mitigation:* Frontend tự động thử kết nối lại (auto-reconnect) sau mỗi 2 giây.
4. **Bảo mật khi quên cấu hình `DASHBOARD_PASSWORD`:**
   - *Mitigation:* Nếu không có mật khẩu trong `.env`, hệ thống tự sinh mật khẩu ngẫu nhiên tạm thời và in to ra terminal console của server, không bao giờ mở public không mật khẩu.
5. **Đồng bộ đa client WebSocket:**
   - *Mitigation:* Dùng `ConnectionManager` dạng pub/sub broadcast tới tất cả các client đang active, đồng thời lưu buffer 100 dòng log gần nhất để client mới mở tab có ngay lịch sử log.
