# Brainstorm: Dashboard Full Control & Selective Learning for Coursera Bot

**Date:** 2026-09-24

## Ideas Explored

1. **Direct Config File Editing (.env / Terminal):** Người dùng phải SSH vào VPS để chỉnh sửa email, mật khẩu hoặc đổi thông số tốc độ. Bất tiện và dễ gõ nhầm khi thao tác trên điện thoại hoặc máy tính từ xa.
2. **Full SQLite Database & ORM:** Lưu trữ cấu hình và khóa học vào bảng cơ sở dữ liệu quan hệ. Mạnh mẽ nhưng quá cồng kềnh (over-engineered) cho một công cụ cá nhân, gây phức tạp khi bảo trì và backup.
3. **Tab-based SPA with JSON Volume Persistence (Selected):** 
   - Tái cấu trúc Dashboard thành **3 Tab trực quan**:
     - **Tab 1 - Điều Khiển (Dashboard):** Quy trình 2 bước (Nhập URL -> Bấm "Quét khóa học" -> Hiện danh sách bài với các nút lọc nhanh -> Chọn bài muốn học -> Bấm "Bắt đầu học").
     - **Tab 2 - Cài Đặt (Settings):** Nhập/sửa tài khoản Coursera (Email/Password), tốc độ video, thời gian đọc, nội dung reply thảo luận. Lưu tự động vào `data/settings.json`.
     - **Tab 3 - Lịch Sử (History):** Nhật ký các khóa học đã chạy, ngày giờ, số bài hoàn thành. Lưu vào `data/history.json`.

## User's Direction

- **100% thao tác qua Web:** Toàn bộ quá trình sử dụng tool từ cấu hình tài khoản, chỉnh thông số bot, chọn bài học đến theo dõi tiến độ đều diễn ra trên Dashboard.
- **Quản lý cài đặt trực tiếp:** Không cần đụng vào file `.env` trên VPS nữa.
- **Học chọn lọc (Selective Learning):** Không ép buộc học tuần tự từ đầu đến cuối mà cho phép quét toàn bộ bài học của khóa và tick chọn bài muốn học (kèm các nút lọc nhanh: "Chọn tất cả", "Chỉ chọn Video", "Chỉ chọn Reading", "Bỏ chọn").
- **Phản hồi trực quan khi quét:** Hiển thị thanh tiến trình / spinner khi bot đang quét các tuần/module của khóa học.
- **Theo dõi lịch sử:** Ghi lại kết quả các phiên chạy trước.

## Open Questions

*(Không còn - Đã được làm rõ toàn bộ qua các câu hỏi Clarification).*

## Risks

1. **Bảo mật file `data/settings.json`:** Chứa mật khẩu Coursera nên tuyệt đối KHÔNG được mount vào thư mục static công khai của web server, chỉ được truy xuất qua authenticated API.
2. **Thời gian Quét (Scan) khóa học:** Quét toàn bộ khóa học mất từ 10–25s tùy số lượng tuần; cần chạy bất đồng bộ hoặc thông báo rõ ràng để người dùng không tưởng bot bị đơ.
3. **Tương thích ngược cấu hình:** Khi người dùng chưa lưu `settings.json`, hệ thống phải tự động fallback về các biến môi trường trong `.env`.
