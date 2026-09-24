# Phase 05: E2E Verification & Documentation

**Phase ID:** `phase-05-e2e-verification`  
**Stories Covered:** Tất cả các User Stories  

---

## Mục tiêu
Kiểm thử toàn bộ hệ thống từ đầu đến cuối (End-to-End), tối ưu hóa tài nguyên (RAM, CPU), xử lý các ngoại lệ biên và cập nhật tài liệu hướng dẫn triển khai trên VPS vào `README.md`.

## Phạm vi công việc
- Kiểm thử luồng hoàn chỉnh:
  1. Khởi động container bằng `docker compose up -d`.
  2. Mở trình duyệt truy cập Dashboard -> Xác thực mật khẩu.
  3. Nhập URL khóa học thử nghiệm -> Bấm `Start`.
  4. Quan sát WebSocket log hiển thị real-time, kiểm tra bot điều hướng qua các bài học.
  5. Thử nghiệm nút `Emergency Stop` giữa chừng -> Kiểm tra bot dừng ngay lập tức và Chrome đóng an toàn.
  6. Khởi động lại bot -> Kiểm tra tiếp tục học bài tiếp theo.
- Đo lường mức sử dụng tài nguyên (`docker stats`): Đảm bảo RAM < 600MB.
- Cập nhật `README.md`:
  - Thêm phần "Hướng dẫn triển khai Docker trên VPS 24/7".
  - Hướng dẫn mở port, cấu hình `DASHBOARD_PASSWORD`, các lệnh quản trị Docker cơ bản (`up`, `down`, `logs`).

## Files/Modules bị ảnh hưởng
- `README.md`
- Toàn bộ source code để tinh chỉnh bug (nếu phát hiện trong quá trình test).

## Dependencies
- Phụ thuộc tất cả các phase trước (`phase-01`, `phase-02`, `phase-03`, `phase-04`).

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Đạt toàn bộ Success Criteria trong file `spec.md`.
- `README.md` có hướng dẫn rõ ràng, người dùng mới có thể làm theo từng bước để deploy lên VPS mà không gặp trở ngại.

## Rủi ro & Ghi chú
- Đảm bảo các hướng dẫn tường lửa (UFW / AWS Security Group / DigitalOcean Firewall) được lưu ý để người dùng không quên mở port 8000.
