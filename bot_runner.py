# -*- coding: utf-8 -*-
"""
COURSERA BOT - BOT RUNNER
=========================
Điều phối vòng đời của bot (start, stop khẩn cấp, cập nhật trạng thái nền).
Chạy trên background thread để không block Web Server FastAPI.
"""

import threading
import time
from typing import Optional

from bot import CourseraBot
from utils.logger import log, info, warn, error, success, add_log_listener

_runner_lock = threading.Lock()
_current_bot: Optional[CourseraBot] = None
_bot_thread: Optional[threading.Thread] = None
_log_listener_registered = False


def is_running() -> bool:
    """Kiểm tra xem bot có đang chạy trong thread không."""
    global _bot_thread
    return _bot_thread is not None and _bot_thread.is_alive()


def start(course_url: str, state_mgr, ws_mgr) -> bool:
    """Khởi động luồng chạy bot mới."""
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
                _current_bot = CourseraBot(
                    course_url=course_url,
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
                info("Bot thread đã kết thúc an toàn.")

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

        # Không block lâu, thread worker sẽ dọn dẹp và kết thúc
