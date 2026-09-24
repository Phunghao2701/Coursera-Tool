# Phase 01: Web Core API & State Manager

**Phase ID:** `phase-01-web-core-api`  
**Stories Covered:** `P1` (Password protection, API Server)  

---

## Mục tiêu
Xây dựng khung ứng dụng backend bằng **FastAPI**, tích hợp bảo mật bằng mật khẩu, quản lý trạng thái luồng bot (`idle`, `running`, `stopping`) và hệ thống WebSocket hub để phát tán log/trạng thái.

## Phạm vi công việc
- Thêm `fastapi`, `uvicorn`, `websockets` vào `requirements.txt`.
- Thêm biến `DASHBOARD_PASSWORD` vào `config.py` và `.env.example`.
- Tạo module `server.py`:
  - Khởi tạo FastAPI app.
  - Endpoint xác thực `POST /api/login` (kiểm tra `DASHBOARD_PASSWORD`, trả về session token/cookie).
  - Middleware bảo vệ các API private (`/api/start`, `/api/stop`, `/api/status`, `/ws/*`).
  - Class `BotStateManager`: Thread-safe state tracking (`status`, `current_course`, `current_item`, `stats`).
  - WebSocket hub (`ConnectionManager`) quản lý các client đang mở dashboard để broadcast log và trạng thái.

## Files/Modules bị ảnh hưởng
- `requirements.txt`
- `config.py`
- `.env.example`
- `server.py` (tạo mới)

## Dependencies
- Không phụ thuộc phase nào (Phase nền tảng).

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Chạy `uvicorn server:app --port 8000` thành công.
- Gọi API `/api/status` khi chưa login -> Trả về `401 Unauthorized`.
- Gửi đúng `DASHBOARD_PASSWORD` -> Trả về `200 OK` kèm cookie xác thực.
- Kết nối tới WebSocket `/ws/logs` được chấp nhận khi đã xác thực.

## Rủi ro & Ghi chú
- Cần đảm bảo WebSocket authentication an toàn (hỗ trợ cả qua Cookie và query param token cho các trình duyệt không hỗ trợ gửi custom headers qua WS).
