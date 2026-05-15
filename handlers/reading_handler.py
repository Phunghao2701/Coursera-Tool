import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import config
from utils.logger import success, info, warn, error, step
from utils.helpers import find_optional, safe_click, is_item_completed, click_next_item

# ============================================================
#  READING HANDLER
#  Coursera bắt chờ 30 giây rồi mới cho bấm "Go to next item"
# ============================================================

def handle_reading(driver) -> bool:
    """
    Xử lý phần Reading/Supplement.
    1. Cuộn xuống cuối trang để trigger timer
    2. Đợi READING_WAIT giây
    3. Bấm Next
    4. Kiểm tra tích xanh
    Trả về True nếu hoàn thành.
    """
    step("📖 [READING] Bắt đầu xử lý...")

    # Cuộn xuống cuối để Coursera nhận biết đã đọc
    _scroll_to_bottom(driver)

    wait_secs = config.READING_WAIT
    info(f"⏳ Đang đợi {wait_secs}s (Coursera timer)...")
    _countdown(wait_secs)

    # Thử bấm nút "Go to next item" / "Next"
    clicked = click_next_item(driver)
    if not clicked:
        # Một số trang Reading không có nút Next riêng — vẫn tính là done
        warn("Không có nút Next ở trang Reading này.")

    time.sleep(2)
    if is_item_completed(driver):
        success("Reading đã hoàn thành ✔")
        return True
    else:
        warn("Chưa thấy tích xanh ở Reading.")
        return False


def _scroll_to_bottom(driver):
    """Cuộn từ từ xuống cuối trang."""
    scroll_pause = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    for _ in range(20):  # tối đa 20 bước
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(scroll_pause)
        new_height = driver.execute_script(
            "return window.pageYOffset + window.innerHeight"
        )
        total_height = driver.execute_script("return document.body.scrollHeight")
        if new_height >= total_height - 50:
            break
    info("Đã cuộn xuống cuối trang Reading.")


def _countdown(secs: int):
    for remaining in range(secs, 0, -1):
        print(f"\r  [TIMER] Con {remaining:3d}s...", end="", flush=True)
        time.sleep(1)
    print()  # newline sau countdown
