# -*- coding: utf-8 -*-
"""
Handlers package: Xử lý các dạng bài học trên Coursera.
"""

from .reading_handler import handle_reading
from .video_handler import handle_video
from .discussion_handler import handle_discussion
from .assignment_handler import handle_assignment

__all__ = [
    "handle_reading",
    "handle_video",
    "handle_discussion",
    "handle_assignment",
]
