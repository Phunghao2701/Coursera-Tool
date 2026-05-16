# 🎓 Coursera Bot — Tự động hoàn thành khóa học

> Tool tự động xử lý Video, Reading, Quiz và Graded Assignment trên Coursera.  
> **By @phunghao2701(https://github.com/phunghao2701)**

---

## ✅ Tính năng hiện tại

| Loại nội dung | Trạng thái | Mô tả |
|---|---|---|
| 📹 Video | ✅ | Tăng tốc x2, chờ đến cuối |
| 📖 Reading | ✅ | Cuộn xuống, đợi 35s theo yêu cầu Coursera |
| 📝 Graded Quiz | ⏭️ | Comming soon |
| 💬 Discussion | ⏭️ | Comming soon |
| 📄 Assignment | ⏭️ | Comming soon |

---

## 🚀 Hướng dẫn cài đặt

### Yêu cầu
- **Python 3.10+** — [tải tại đây](https://www.python.org/)
- **Google Chrome** (bắt buộc) — [tải tại đây](https://www.google.com/chrome/)


### Bước 1 — Cài đặt thư viện
```
double-click setup.bat
```

### Bước 2 — Chạy bot
```
double-click run_bot.bat
```
Điền vào form: Email, Mật khẩu, URL khóa học

---

## 📁 Cấu trúc dự án

```
tool coursera/
├── bot.py                  # Bot chính
├── launcher.py             # GUI launcher
├── config.py               # Cấu hình
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

---

## 🎉

*© Distributed by phunghao2701 (https://github.com/phunghao2701)*