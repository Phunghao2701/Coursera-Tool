# -*- coding: utf-8 -*-
import logging
import sys

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


def get_logger(name: str = "CourseraBot") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColorFormatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S"
        ))
        logger.addHandler(handler)
    return logger


# Shortcut helpers
log = get_logger()

def success(msg):  log.info(f"[OK]  {msg}")
def info(msg):     log.info(f"[..]  {msg}")
def warn(msg):     log.warning(f"[!!]  {msg}")
def error(msg):    log.error(f"[XX]  {msg}")
def step(msg):     log.info(f"[>>]  {msg}")
def skip(msg):     log.info(f"[--]  {msg}")
