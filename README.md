# 🤖 Coursera Auto Bot & Web Monitor Dashboard

Công cụ tự động hóa học tập trên nền tảng Coursera sử dụng **Python**, **Selenium (Chrome Headless)** và **FastAPI Web Dashboard**, hỗ trợ triển khai **Docker trên VPS 24/7**.

---

## 🌟 Tính năng nổi bật

* 🌐 **Web Dashboard Trực Quan (Port 3987):** Theo dõi tiến độ bài học (%), số lượng hoàn thành và stream log thời gian thực qua WebSocket.
* 🛑 **Điều Khiển Linh Hoạt:** Đổi nhanh URL khóa học và hỗ trợ nút **Dừng Khẩn Cấp (Emergency Stop)** ngắt trình duyệt tức thì.
* 🔒 **Bảo Mật VPS:** Xác thực bằng mật khẩu (`DASHBOARD_PASSWORD`), bảo vệ truy cập trái phép từ internet.
* 🐳 **Triển Khai Docker 1-Click:** Đóng gói trọn gói Chromium Headless + Chromedriver + Web Server, mount Volume lưu giữ cookie phiên đăng nhập.
* 🛡️ **Anti-Detection:** Giả lập trình duyệt người dùng thật, ẩn cờ tự động hóa `navigator.webdriver`.

---

## 📁 Cấu trúc thư mục dự án

```text
coursera-tool/
├── .env                     # Biến môi trường bảo mật (KHÔNG commit)
├── .env.example             # File mẫu mô tả tất cả biến cấu hình
├── .gitignore               # Loại bỏ .env, __pycache__, log, data khỏi Git
├── Dockerfile               # Đóng gói Chromium Headless & FastAPI trên Linux
├── docker-compose.yml       # Cấu hình container, port 3987, shm_size 2gb & volumes
├── deploy.sh                # Script triển khai nhanh 1-click trên VPS Linux
├── requirements.txt         # Khai báo các thư viện cần thiết
├── config.py                # Module nạp cấu hình từ .env và validate dữ liệu
├── server.py                # FastAPI Web Server, API điều khiển & WebSocket hub
├── bot_runner.py            # Quản lý luồng worker chạy bot ngầm & ngắt khẩn cấp
├── bot.py                   # Lớp điều phối CourseraBot chính
├── main.py                  # Điểm khởi chạy terminal cục bộ
├── static/                  # Giao diện Web Dashboard (Dark Theme)
│   ├── index.html           # Layout dashboard & login modal
│   ├── style.css            # Dark mode glassmorphism
│   └── app.js               # Logic điều khiển, render log & WebSocket
├── handlers/                # Các module xử lý từng dạng bài học
│   ├── reading_handler.py    # Xử lý bài Reading / Supplement
│   ├── video_handler.py      # Xử lý bài Video (x2 tốc độ, auto-play)
│   ├── discussion_handler.py # Xử lý bài Discussion Prompt (tự post reply)
│   └── assignment_handler.py # Bỏ qua bài kiểm tra / nộp bài an toàn
└── utils/                   # Tiện ích bổ trợ (logger, helpers, navigator)
```

---

## 🚀 Hướng Dẫn Triển Khai Trên VPS 24/7 (Docker)

### Bước 1: Chuẩn bị trên VPS
Đảm bảo VPS Linux (Ubuntu/Debian) đã cài đặt **Docker** và **Docker Compose**:
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2
```

### Bước 2: Tải mã nguồn lên VPS
Copy toàn bộ thư mục dự án lên VPS (qua Git, SCP hoặc SFTP):
```bash
cd /opt/coursera-tool
```

### Bước 3: Cấu hình biến môi trường (`.env`)
Tạo file `.env` từ file mẫu:
```bash
cp .env.example .env
nano .env
```
Điền các thông số cơ bản:
```env
COURSERA_EMAIL=email_cua_ban@gmail.com
COURSERA_PASSWORD=mat_khau_coursera

# Khóa học muốn chạy mặc định
COURSE_URL=https://www.coursera.org/learn/ten-khoa-hoc/home/welcome

# Mật khẩu bảo vệ Web Dashboard trên VPS
DASHBOARD_PASSWORD=mat_khau_dashboard_cua_ban
DASHBOARD_PORT=3987
```

### Bước 4: Mở cổng Firewall trên VPS
Mở cổng `3987` trên tường lửa (UFW hoặc Security Group của Cloud Provider):
```bash
sudo ufw allow 3987/tcp
```

### Bước 5: Khởi chạy container
Chạy lệnh bằng Docker Compose:
```bash
docker compose up -d --build
```
*(Hoặc cấp quyền và chạy script: `chmod +x deploy.sh && ./deploy.sh`)*

### Bước 6: Truy cập Web Dashboard
Mở trình duyệt trên máy tính hoặc điện thoại:
```
http://<IP-VPS-CỦA-BẠN>:3987
```
1. Nhập mật khẩu `DASHBOARD_PASSWORD`.
2. Kiểm tra/nhập URL khóa học.
3. Bấm **Khởi Động Bot** để bắt đầu học.
4. Xem log trực tiếp tuôn ra trên màn hình. Nếu muốn dừng ngay lập tức, bấm **Dừng Khẩn Cấp**.

---

## 🛠️ Các Lệnh Quản Trị Docker Hữu Ích

* **Xem log container:**
  ```bash
  docker compose logs -f
  ```
* **Khởi động lại bot:**
  ```bash
  docker compose restart
  ```
* **Dừng container:**
  ```bash
  docker compose down
  ```
* **Cập nhật mã nguồn mới:**
  ```bash
  docker compose up -d --build
  ```

---

## 💻 Chạy Trực Tiếp Trên Máy Windows (Tùy chọn)

Nếu bạn muốn chạy cục bộ trên máy cá nhân:
1. **Chạy Web Dashboard:**
   ```bash
   python -m uvicorn server:app --port 3987
   ```
   Sau đó mở trình duyệt tại `http://localhost:3987`.
2. **Chạy qua Batch script:** Double-click [`run_bot.bat`](file:///d:/tool%20coursera/run_bot.bat).
3. **Chạy qua Terminal:** `python main.py`.
