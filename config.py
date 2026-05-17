# ============================================================
#  COURSERA BOT - CAU HINH (tu dong tao boi launcher.py)
# ============================================================

# --- Tai khoan Coursera ---
EMAIL    = "phunghao2701@gmail.com"
PASSWORD = "Lephunghao2005"

# --- Khoa hoc muon chay ---
COURSE_URL = "https://www.coursera.org/learn/understanding-user-needs/supplement/Edq5p/welcome-announcement"

# --- Cai dat bot ---
HEADLESS        = False   # True = chay ngam, False = hien browser
VIDEO_SPEED     = 2.0     # Toc do video (1.0 = binh thuong, 2.0 = x2)
READING_WAIT    = 35      # Giay doi o trang Reading (Coursera yeu cau 30s)
RETRY_LIMIT     = 3       # So lan thu lai neu khong thay tich xanh
DISCUSSION_TEXT = "ok"    # Noi dung reply o Discussion Prompt

# --- Timeout chung (giay) ---
PAGE_LOAD_TIMEOUT  = 30
ELEMENT_TIMEOUT    = 15
