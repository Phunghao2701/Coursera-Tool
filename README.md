# 🎓 Coursera Bot — Tự động hoàn thành khóa học

> Tool tự động xử lý Video, Reading, Quiz và Graded Assignment trên Coursera.  
> **By [@phunghao2701](https://github.com/phunghao2701)**

---

## ✅ Tính năng hiện tại

| Loại nội dung | Trạng thái | Mô tả |
|---|---|---|
| 📹 Video | ✅ | Tăng tốc x2, chờ đến cuối |
| 📖 Reading | ✅ | Cuộn xuống, đợi 35s theo yêu cầu Coursera |
| 📝 Graded Quiz | ✅ | Submit → đọc feedback → retry với đáp án đúng |
| 💬 Discussion | ⏭️ | Bỏ qua |

---

## 🚀 Hướng dẫn cài đặt

### Yêu cầu
- **Python 3.10+** — [tải tại đây](https://www.python.org/)
- **Google Chrome** (bắt buộc)

### Bước 1 — Cài đặt thư viện
```
double-click setup.bat
```

### Bước 2 — Chạy bot
```
double-click run_bot.bat
```
Điền vào form: Email, Mật khẩu, URL khóa học, Gemini API Key (tùy chọn).

---

## 🔑 Gemini API Key (tùy chọn)

Dùng để AI trả lời Quiz ngay lần đầu (tăng tỷ lệ đạt 80 không cần retry).

Lấy **miễn phí** tại: https://aistudio.google.com/app/apikey

---

## ⚙️ Cấu hình nâng cao

Sau khi chạy lần đầu, mở `config.py` để chỉnh:

```python
HEADLESS   = True   # Chạy ngầm (không hiện browser)
VIDEO_SPEED = 2.0   # Tốc độ video (1.0 = bình thường)
```

---

## 📁 Cấu trúc dự án

```
tool coursera/
├── bot.py                  # Bot chính
├── launcher.py             # GUI launcher
├── config.py               # Cấu hình (không commit)
├── run_bot.bat             # Chạy bot (Windows)
├── setup.bat               # Cài đặt lần đầu
├── handlers/
│   ├── assignment_handler.py
│   ├── discussion_handler.py
│   ├── reading_handler.py
│   └── video_handler.py
└── utils/
    ├── helpers.py
    ├── logger.py
    └── navigator.py
```

---

## ⚠️ Lưu ý

- Tool chỉ dùng cho mục đích **học tập cá nhân**.
- Quiz có giới hạn **3 lần thử / 8 giờ** — bot tự động bảo toàn số lần.
- Không commit `config.py` hay `user_config.json` lên GitHub.

---

*© 2026 phunghao2701 — All rights reserved*
