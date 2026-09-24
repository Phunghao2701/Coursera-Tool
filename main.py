# -*- coding: utf-8 -*-
"""
COURSERA BOT - MAIN RUNNER
==========================
Điểm khởi chạy chính của dự án.
Kiểm tra cấu hình môi trường, khởi động bot và điều phối tiến trình.
"""

import os
import sys

# Đảm bảo mã hóa UTF-8 trên Windows console
os.environ["PYTHONUTF8"] = "1"

import config
from utils.logger import success, info, warn, error, step, log
from bot import CourseraBot


def _mask_email(email: str) -> str:
    """Ẩn bớt ký tự email khi in ra màn hình."""
    if not email or "@" not in email:
        return "N/A"
    user, domain = email.split("@", 1)
    if len(user) <= 3:
        masked_user = user[0] + "***"
    else:
        masked_user = user[:3] + "***"
    return f"{masked_user}@{domain}"


def main():
    print("\n" + "=" * 62)
    print("       🤖 COURSERA AUTO BOT - PHIÊN BẢN TỰ ĐỘNG HỌC")
    print("=" * 62)

    # 1. Kiểm tra cấu hình .env
    config_errors = config.validate_config()
    if config_errors:
        print("\n[!] LỖI CẤU HÌNH BIẾN MÔI TRƯỜNG:")
        for err in config_errors:
            error(f"- {err}")
        print("\n👉 Vui lòng mở file .env và cập nhật đầy đủ thông tin trước khi chạy.")
        return 1

    # 2. Hiển thị thông tin phiên chạy
    info(f"Tài khoản : {_mask_email(config.EMAIL)}")
    info(f"Khóa học  : {config.COURSE_URL}")
    info(f"Chế độ    : {'Chạy ngầm (Headless)' if config.HEADLESS else 'Giao diện trực quan'}")
    info(f"Tốc độ    : x{config.VIDEO_SPEED} | Đọc tài liệu: {config.READING_WAIT}s")
    print("-" * 62 + "\n")

    # 3. Khởi tạo và chạy bot
    bot = CourseraBot()
    try:
        bot.setup_driver()
        bot.login()
        bot.run()
        success("🎉 HOÀN THÀNH TẤT CẢ CÁC BÀI HỌC TRONG KHÓA!")
    except KeyboardInterrupt:
        warn("Bot đã được dừng bởi người dùng (Ctrl+C).")
    except Exception as e:
        error(f"Đã xảy ra lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            input("\n[Xong] Nhấn Enter để kết thúc và đóng trình duyệt...")
        except Exception:
            pass
        bot.quit()

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
