# -*- coding: utf-8 -*-
"""
Utils package: Các hàm hỗ trợ logger, helper và navigator.
"""

from .logger import log, success, info, warn, error, step, skip
from .helpers import (
    wait_for,
    wait_for_clickable,
    safe_click,
    find_optional,
    detect_item_type,
    is_item_completed,
    click_next_item,
    get_current_url,
)
from .navigator import get_all_course_items, navigate_to_item

__all__ = [
    "log",
    "success",
    "info",
    "warn",
    "error",
    "step",
    "skip",
    "wait_for",
    "wait_for_clickable",
    "safe_click",
    "find_optional",
    "detect_item_type",
    "is_item_completed",
    "click_next_item",
    "get_current_url",
    "get_all_course_items",
    "navigate_to_item",
]
