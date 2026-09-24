# -*- coding: utf-8 -*-
"""
COURSERA BOT - BOT RUNNER
=========================
Điều phối vòng đời của bot (start, stop khẩn cấp, cập nhật trạng thái nền, ghi nhận lịch sử).
Chạy trên background thread để không block Web Server FastAPI.
"""

import threading
import time
from datetime import datetime
from typing import Optional, List

from bot import CourseraBot
import storage
from utils.logger import log, info, warn, error, success, add_log_listener

_runner_lock = threading.Lock()
_current_bot: Optional[CourseraBot] = None
_bot_thread: Optional[threading.Thread] = None
_log_listener_registered = False


def is_running() -> bool:
    """Kiểm tra xem bot có đang chạy trong thread không."""
    global _bot_thread
    return _bot_thread is not None and _bot_thread.is_alive()


def start(course_url: str, state_mgr, ws_mgr, selected_urls: Optional[List[str]] = None) -> bool:
    """Khởi động luồng chạy bot mới kèm danh sách bài chọn lọc (nếu có)."""
    global _current_bot, _bot_thread, _log_listener_registered

    with _runner_lock:
        if is_running():
            warn("Bot đã đang chạy rồi, không thể start thêm.")
            return False

        # Đăng ký listener để logger bắn thẳng vào WebSocket hub
        if not _log_listener_registered:
            add_log_listener(ws_mgr.broadcast_log_sync)
            _log_listener_registered = True

        state_mgr.reset_for_run(course_url)
        ws_mgr.broadcast_status_sync()

        start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def _on_item_change(idx: int, total: int, name: str, item_type: str):
            state_mgr.update_item(idx, total, name, item_type)
            ws_mgr.broadcast_status_sync()

        def _on_stats_change(stats: dict):
            state_mgr.update_stats(stats)
            ws_mgr.broadcast_status_sync()

        def _worker():
            global _current_bot
            err_msg = None
            try:
                info(f"Khởi động phiên chạy bot cho khóa học: {course_url}")
                if selected_urls:
                    info(f"Chế độ học chọn lọc: {len(selected_urls)} bài được chọn.")

                _current_bot = CourseraBot(
                    course_url=course_url,
                    selected_urls=selected_urls,
                    on_item_change=_on_item_change,
                    on_stats_change=_on_stats_change
                )
                _current_bot.setup_driver()

                if _current_bot.stop_requested:
                    return

                _current_bot.login()

                if _current_bot.stop_requested:
                    return

                _current_bot.run()
                success("Phiên chạy bot đã hoàn tất thành công!")
            except Exception as e:
                # Nếu do người dùng chủ động emergency stop thì không tính là crash
                if _current_bot and _current_bot.stop_requested:
                    warn("Bot đã dừng lại theo yêu cầu của người dùng.")
                else:
                    err_msg = str(e)
                    error(f"Lỗi trong quá trình chạy bot: {e}")
                    import traceback
                    traceback.print_exc()
            finally:
                if _current_bot:
                    try:
                        _current_bot.quit()
                    except Exception:
                        pass
                state_mgr.set_idle(error_msg=err_msg)
                ws_mgr.broadcast_status_sync()

                # Ghi nhận lịch sử phiên chạy
                total_done = (
                    state_mgr.stats["reading"]["done"]
                    + state_mgr.stats["video"]["done"]
                    + state_mgr.stats["discussion"]["done"]
                )
                is_stopped = bool(_current_bot and _current_bot.stop_requested)
                status_label = "Hoàn thành" if not is_stopped and not err_msg else ("Đã dừng" if is_stopped else "Lỗi")
                storage.append_history({
                    "id": int(time.time()),
                    "course_url": course_url,
                    "started_at": start_time_str,
                    "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": status_label,
                    "total_items": state_mgr.total_items,
                    "completed_items": total_done,
                    "stats": state_mgr.stats
                })

                info("Bot thread đã kết thúc an toàn và lưu lịch sử.")

        _bot_thread = threading.Thread(target=_worker, name="CourseraBotWorker", daemon=True)
        _bot_thread.start()
        return True


def emergency_stop():
    """Kích hoạt ngắt khẩn cấp, đóng browser lập tức."""
    global _current_bot, _bot_thread

    with _runner_lock:
        if _current_bot:
            warn("Gửi tín hiệu emergency stop tới CourseraBot...")
            _current_bot.emergency_stop()
