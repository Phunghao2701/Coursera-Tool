# -*- coding: utf-8 -*-
"""
COURSERA BOT - CẤU HÌNH HỆ THỐNG
================================
Đọc toàn bộ cấu hình từ file .env hoặc biến môi trường hệ thống.
Không lưu trực tiếp thông tin nhạy cảm (email, password) trong file mã nguồn này.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Tìm và load file .env từ thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()  # Fallback to current working directory or environment


def _get_str(key: str, default: str = "", alt_key: str = None) -> str:
    """Lấy giá trị chuỗi từ biến môi trường."""
    val = os.getenv(key)
    if (val is None or val.strip() == "") and alt_key:
        val = os.getenv(alt_key)
    if val is None or val.strip() == "":
        return default
    return val.strip()


def _get_bool(key: str, default: bool = False) -> bool:
    """Chuyển chuỗi trong env (true/false/1/0/yes/no) thành boolean."""
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "y", "on")


def _get_int(key: str, default: int) -> int:
    """Chuyển chuỗi trong env thành integer an toàn."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    """Chuyển chuỗi trong env thành float an toàn."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val.strip())
    except ValueError:
        return default


# ============================================================
#  CÁC GIÁ TRỊ CẤU HÌNH EXPORT
# ============================================================

# --- Tài khoản Coursera (ưu tiên COURSERA_EMAIL, fallback EMAIL) ---
EMAIL = _get_str("COURSERA_EMAIL", alt_key="EMAIL")
PASSWORD = _get_str("COURSERA_PASSWORD", alt_key="PASSWORD")

# --- Khóa học cần chạy ---
COURSE_URL = _get_str("COURSE_URL")

# --- Cài đặt bot ---
HEADLESS = _get_bool("HEADLESS", default=False)
VIDEO_SPEED = _get_float("VIDEO_SPEED", default=2.0)
READING_WAIT = _get_int("READING_WAIT", default=35)
RETRY_LIMIT = _get_int("RETRY_LIMIT", default=3)
DISCUSSION_TEXT = _get_str("DISCUSSION_TEXT", default="ok")

# --- Timeout chung (giây) ---
PAGE_LOAD_TIMEOUT = _get_int("PAGE_LOAD_TIMEOUT", default=30)
ELEMENT_TIMEOUT = _get_int("ELEMENT_TIMEOUT", default=15)

# --- Cấu hình Web Dashboard ---
DASHBOARD_PASSWORD = _get_str("DASHBOARD_PASSWORD", default="coursera123")
DASHBOARD_PORT = _get_int("DASHBOARD_PORT", default=3987)


def validate_config() -> list[str]:
    """
    Kiểm tra tính hợp lệ của cấu hình trước khi chạy bot.
    Trả về danh sách các cảnh báo / lỗi nếu có.
    """
    errors = []
    if not EMAIL or "example.com" in EMAIL:
        errors.append("Chưa cấu hình COURSERA_EMAIL trong file .env")
    if not PASSWORD or PASSWORD == "your_password_here":
        errors.append("Chưa cấu hình COURSERA_PASSWORD trong file .env")
    if not COURSE_URL or "your-course-slug" in COURSE_URL or not COURSE_URL.startswith("http"):
        errors.append("Chưa cấu hình COURSE_URL hợp lệ trong file .env")

    return errors
