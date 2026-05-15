# ============================================================
#  COURSERA BOT - CẤU HÌNH
# ============================================================

# --- Tài khoản Coursera ---
EMAIL    = ""
PASSWORD = ""

# --- Khóa học muốn chạy ---
COURSE_URL = ""

# --- Cài đặt bot ---
HEADLESS        = False   # True = chạy ngầm, False = hiện browser
VIDEO_SPEED     = 2.0     # Tốc độ video (1.0 = bình thường, 2.0 = x2)
READING_WAIT    = 35      # Giây đợi ở trang Reading (Coursera yêu cầu 30s)
RETRY_LIMIT     = 3       # Số lần thử lại nếu không thấy tích xanh
DISCUSSION_TEXT = "ok"    # Nội dung reply ở Discussion Prompt

# --- Timeout chung (giây) ---
PAGE_LOAD_TIMEOUT  = 30
ELEMENT_TIMEOUT    = 15
