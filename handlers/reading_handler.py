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
#  Flow:
#    1. Cuộn xuống cuối (trigger timer Coursera)
#    2. Nếu có audio → play audio
#    3. Đợi READING_WAIT giây
#    4. Bấm "Mark as completed" (nếu có)
#    5. Bấm "Go to next item"
#    6. Kiểm tra tích xanh → retry nếu chưa
# ============================================================

MARK_COMPLETE_SELECTORS = [
    (By.XPATH, "//button[contains(text(),'Mark as completed')]"),
    (By.XPATH, "//button[contains(text(),'Mark as Complete')]"),
    (By.XPATH, "//button[normalize-space()='Mark as completed']"),
    (By.CSS_SELECTOR, "button[data-testid='mark-as-completed-btn']"),
    (By.CSS_SELECTOR, "button[data-testid='mark-complete-button']"),
    (By.XPATH, "//button[contains(@aria-label,'Mark as completed')]"),
]

AUDIO_PLAY_SELECTORS = [
    (By.CSS_SELECTOR, "button[aria-label='Play']"),
    (By.CSS_SELECTOR, "button[title='Play']"),
    (By.CSS_SELECTOR, ".vjs-play-control"),
    (By.CSS_SELECTOR, "audio"),
    (By.XPATH, "//button[contains(@class,'play') and not(contains(@class,'replay'))]"),
]


def handle_reading(driver) -> bool:
    """
    Xử lý phần Reading/Supplement.
    Trả về True nếu hoàn thành (có tích xanh).
    """
    step("📖 [READING] Bắt đầu xử lý...")

    # --- UU TIEN: Neu da co tich xanh roi thi skip ---
    if is_item_completed(driver):
        success("Da co tich xanh - bo qua Reading nay.")
        return True

    # 1. Cuộn xuống cuối để trigger timer Coursera
    _scroll_to_bottom(driver)

    # 2. Nếu có audio/video nhỏ → play để đảm bảo hoàn thành
    _play_audio_if_present(driver)

    # 3. Đợi timer Coursera
    wait_secs = config.READING_WAIT
    info(f"⏳ Đang đợi {wait_secs}s (Coursera timer)...")
    _countdown(wait_secs)

    # 4. Bấm "Mark as completed" (quan trọng!)
    _click_mark_as_completed(driver)

    # 5. Bấm "Go to next item"
    clicked = click_next_item(driver)
    if not clicked:
        warn("Không tìm thấy nút Next ở trang Reading này.")

    time.sleep(3)

    # 6. Kiểm tra tích xanh
    if is_item_completed(driver):
        success("Reading đã hoàn thành ✔")
        return True

    # Chưa tích → thử lại: có thể chưa click Mark as completed
    warn("Chưa thấy tích xanh — thử lại Mark as completed...")
    _click_mark_as_completed(driver)
    time.sleep(2)

    if is_item_completed(driver):
        success("Reading đã hoàn thành ✔ (retry)")
        return True

    # Vẫn chưa → thử play audio rồi đợi thêm
    warn("Thử play audio và đợi thêm 15s...")
    _play_audio_if_present(driver)
    _countdown(15)
    _click_mark_as_completed(driver)
    time.sleep(2)

    if is_item_completed(driver):
        success("Reading đã hoàn thành ✔ (retry audio)")
        return True

    warn("Chưa thấy tích xanh ở Reading sau 3 lần thử.")
    return False


def _click_mark_as_completed(driver):
    """Tìm và bấm nút 'Mark as completed'."""
    for by, sel in MARK_COMPLETE_SELECTORS:
        btn = find_optional(driver, by, sel, timeout=3)
        if btn and btn.is_displayed() and btn.is_enabled():
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", btn)
                info("Đã bấm 'Mark as completed' ✓")
                time.sleep(1)
                return True
            except Exception:
                try:
                    safe_click(driver, btn)
                    info("Đã bấm 'Mark as completed' ✓")
                    time.sleep(1)
                    return True
                except Exception:
                    pass
    info("Không tìm thấy nút 'Mark as completed' (trang này không cần).")
    return False


def _play_audio_if_present(driver):
    """Nếu trang có audio player → tự động play."""
    # Thử play bằng JS trước (nhanh nhất)
    try:
        audio_elements = driver.find_elements(By.CSS_SELECTOR, "audio")
        if audio_elements:
            for audio in audio_elements:
                driver.execute_script("arguments[0].play();", audio)
            info("▶ Đã play audio (JS)")
            return True
    except Exception:
        pass

    # Thử click nút Play
    for by, sel in AUDIO_PLAY_SELECTORS:
        btn = find_optional(driver, by, sel, timeout=3)
        if btn and btn.is_displayed():
            try:
                safe_click(driver, btn)
                info("▶ Đã click Play audio")
                return True
            except Exception:
                pass

    return False


def _scroll_to_bottom(driver):
    """Cuộn từ từ xuống cuối trang."""
    scroll_pause = 0.4
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    for _ in range(25):
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
    print()
