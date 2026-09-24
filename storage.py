# -*- coding: utf-8 -*-
"""
COURSERA BOT - DATA STORAGE SERVICE
===================================
Quản lý lưu trữ file cấu hình (settings.json) và lịch sử chạy (history.json)
bên trong thư mục data/ (được mount volume trong Docker để đảm bảo bền vững).
"""

import json
import os
import threading
from pathlib import Path
from typing import Dict, Any, List

import config

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
HISTORY_FILE = DATA_DIR / "history.json"

_file_lock = threading.Lock()

# Đảm bảo thư mục data luôn tồn tại
os.makedirs(DATA_DIR, exist_ok=True)


def _get_default_settings() -> Dict[str, Any]:
    """Lấy cấu hình mặc định từ config.py / .env."""
    return {
        "email": config.EMAIL,
        "password": config.PASSWORD,
        "course_url": config.COURSE_URL,
        "video_speed": config.VIDEO_SPEED,
        "reading_wait": config.READING_WAIT,
        "retry_limit": config.RETRY_LIMIT,
        "discussion_text": config.DISCUSSION_TEXT,
        "dashboard_password": config.DASHBOARD_PASSWORD,
        "dashboard_port": config.DASHBOARD_PORT,
    }


def load_settings() -> Dict[str, Any]:
    """Đọc cài đặt từ data/settings.json, nếu chưa có sẽ fallback về default."""
    defaults = _get_default_settings()
    with _file_lock:
        if not SETTINGS_FILE.exists():
            return defaults
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    defaults.update(saved)
        except Exception:
            pass
    return defaults


def save_settings(new_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Cập nhật và ghi cấu hình vào data/settings.json."""
    with _file_lock:
        current = _get_default_settings()
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        current.update(saved)
            except Exception:
                pass

        # Cập nhật các trường mới
        for k, v in new_settings.items():
            if v is not None:
                current[k] = v

        temp_file = SETTINGS_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, SETTINGS_FILE)

    return current


def load_history() -> List[Dict[str, Any]]:
    """Đọc danh sách lịch sử các phiên chạy từ data/history.json."""
    with _file_lock:
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def append_history(record: Dict[str, Any]):
    """Thêm một bản ghi phiên chạy vào data/history.json (giới hạn 50 mục)."""
    with _file_lock:
        history = []
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if not isinstance(history, list):
                        history = []
            except Exception:
                history = []

        # Chèn lên đầu danh sách
        history.insert(0, record)
        history = history[:50]  # Giới hạn 50 bản ghi gần nhất

        temp_file = HISTORY_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, HISTORY_FILE)
