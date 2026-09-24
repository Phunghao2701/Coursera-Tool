# Phase 04: Integration Verification & Polish

**Phase ID:** `phase-04-integration-verification`  
**Stories Covered:** Tất cả các User Stories  

---

## Mục tiêu
Kiểm thử tích hợp end-to-end các tính năng mới: lưu cài đặt, quét khóa học, chọn lọc bài học, ghi nhận lịch sử và bảo đảm tính bền vững của dữ liệu trong container Docker.

## Phạm vi công việc
- Kiểm tra toàn bộ luồng hoạt động:
  1. Mở Tab Cài Đặt -> Lưu thông số mới -> Kiểm tra file `data/settings.json`.
  2. Mở Tab Bảng Điều Khiển -> Nhập URL -> Bấm "Quét Khóa Học" -> Kiểm tra kết quả trả về.
  3. Sử dụng các nút lọc nhanh -> Bấm "Bắt đầu học" -> Xác nhận bot chỉ chạy các bài đã chọn.
  4. Mở Tab Lịch Sử -> Kiểm tra bản ghi phiên chạy được cập nhật đúng.
  5. Thử nghiệm khởi động lại server hoặc container -> Kiểm tra mọi cài đặt và lịch sử vẫn còn nguyên vẹn.
- Cập nhật tài liệu [`README.md`](file:///d:/tool%20coursera/README.md) mô tả chi tiết giao diện 3 Tab mới và tính năng học chọn lọc.

## Files/Modules bị ảnh hưởng
- `README.md`
- Toàn bộ source code phục vụ sửa lỗi (nếu phát hiện trong quá trình test).

## Dependencies
- Phụ thuộc `phase-01`, `phase-02`, `phase-03`.

## Tests & Tiêu chí nghiệm thu (Acceptance Criteria)
- Đạt 100% các tiêu chí trong [`spec.md`](file:///d:/tool%20coursera/plans/dashboard-full-control/spec.md).
- Không có lỗi JavaScript console (`F12`) trên giao diện web.
- Dữ liệu trong `data/settings.json` và `data/history.json` được bảo toàn sau khi restart.

## Rủi ro & Ghi chú
- Đảm bảo quyền đọc/ghi trên thư mục `data/` trong môi trường Docker không bị lỗi permission denied khi chạy dưới user thông thường.
