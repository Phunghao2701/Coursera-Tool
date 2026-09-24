# Phase 01: Settings & History Backend Services

**Phase ID:** `phase-01-settings-history-backend`  
**Stories Covered:** `P1` (Settings Management), `P2` (History Tracking)  

---

## Mục tiêu
Xây dựng cơ chế lưu trữ dữ liệu an toàn dưới dạng JSON trong thư mục `data/`, cung cấp các endpoint REST API để đọc/ghi cấu hình bot và theo dõi nhật ký các phiên chạy.

## Phạm vi công việc
- Tạo module `storage.py`:
  - `load_settings() -> dict`: Đọc từ `data/settings.json`, nếu chưa có sẽ lấy default từ `config.py`.
  - `save_settings(data: dict)`: Lưu vào `data/settings.json`.
  - `load_history() -> list`: Đọc từ `data/history.json`.
  - `append_history(record: dict)`: Thêm một bản ghi phiên chạy vào đầu danh sách `history.json` (giới hạn tối đa 50 bản ghi gần nhất).
- Cập nhật `server.py`:
  - `GET /api/settings`: Trả về thông tin cấu hình (`email`, `password_masked`, `video_speed`, `reading_wait`, `discussion_text`, `course_url`).
  - `POST /api/settings`: Cập nhật cấu hình mới (nếu password không phải placeholder thì mới đổi).
  - `GET /api/history`: Trả về danh sách các lần chạy trước.
- Kết nối `bot_runner.py`: Tự động gọi `append_history()` khi bot kết thúc hoặc dừng lại.

## Files/Modules bị ảnh hưởng
- `storage.py` (tạo mới)
- `server.py`
- `bot_runner.py`

## Dependencies
- Không phụ thuộc phase nào.

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Gọi `GET /api/settings` trả về JSON cấu hình với password được che giấu dạng `******`.
- Gọi `POST /api/settings` lưu thành công giá trị `video_speed=1.5` -> Đọc lại thấy lưu đúng vào `data/settings.json`.
- Khi bot chạy xong hoặc bị ngắt khẩn cấp, một bản ghi tự động xuất hiện trong `data/history.json`.

## Rủi ro & Ghi chú
- File JSON cần được ghi an toàn (atomic write hoặc flush) để tránh file bị hỏng nếu container bị dừng đột ngột.
