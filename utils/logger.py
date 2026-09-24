# -*- coding: utf-8 -*-
import logging
import sys
from datetime import datetime

# Màu ANSI cho terminal
COLORS = {
    "RESET":   "\033[0m",
    "GREEN":   "\033[92m",
    "YELLOW":  "\033[93m",
    "RED":     "\033[91m",
    "CYAN":    "\033[96m",
    "MAGENTA": "\033[95m",
    "WHITE":   "\033[97m",
    "BOLD":    "\033[1m",
}

class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG:    COLORS["WHITE"],
        logging.INFO:     COLORS["CYAN"],
        logging.WARNING:  COLORS["YELLOW"],
        logging.ERROR:    COLORS["RED"],
        logging.CRITICAL: COLORS["MAGENTA"],
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, COLORS["RESET"])
        reset = COLORS["RESET"]
        bold  = COLORS["BOLD"]
        record.levelname = f"{color}{bold}[{record.levelname}]{reset}"
        record.msg       = f"{color}{record.msg}{reset}"
        return super().format(record)


# Danh sách callback cho WebSocket hoặc các subscriber khác
_LOG_LISTENERS = []


class BroadcastHandler(logging.Handler):
    """Handler chuyển tiếp log tới các listener (WebSocket, GUI...)."""

    def emit(self, record):
        try:
            now_str = datetime.now().strftime("%H:%M:%S")
            # Tạo message sạch không ANSI cho web hoặc giữ ANSI nếu terminal giả lập
            raw_msg = record.getMessage()
            # Lấy levelname nguyên bản
            level_name = record.levelname.replace("[", "").replace("]", "")
            line = f"[{now_str}] [{level_name}] {raw_msg}"
            for cb in _LOG_LISTENERS:
                try:
                    cb(line)
                except Exception:
                    pass
        except Exception:
            pass


def add_log_listener(callback):
    """Đăng ký hàm nhận log (ví dụ: ws_manager.broadcast_log_sync)."""
    if callback not in _LOG_LISTENERS:
        _LOG_LISTENERS.append(callback)


def remove_log_listener(callback):
    if callback in _LOG_LISTENERS:
        _LOG_LISTENERS.remove(callback)


def get_logger(name: str = "CourseraBot") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # 1. Console stream handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColorFormatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S"
        ))
        logger.addHandler(handler)

        # 2. Broadcast handler cho Web
        bcast_handler = BroadcastHandler()
        logger.addHandler(bcast_handler)

    return logger


# Shortcut helpers
log = get_logger()

def success(msg):  log.info(f"[OK]  {msg}")
def info(msg):     log.info(f"[..]  {msg}")
def warn(msg):     log.warning(f"[!!]  {msg}")
def error(msg):    log.error(f"[XX]  {msg}")
def step(msg):     log.info(f"[>>]  {msg}")
def skip(msg):     log.info(f"[--]  {msg}")
