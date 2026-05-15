import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException

import config
from utils.logger import success, info, warn, error, step
from utils.helpers import find_optional, safe_click, is_item_completed, click_next_item

# ============================================================
#  VIDEO HANDLER
#  1. Tìm video player
#  2. Tua nhanh lên x2
#  3. Đợi video chạy xong
#  4. Bấm Next
# ============================================================

VIDEO_PLAYER_SELECTORS = [
    (By.CSS_SELECTOR, "video"),
    (By.CSS_SELECTOR, ".vjs-tech"),
    (By.CSS_SELECTOR, "[data-testid='video-player'] video"),
]

SPEED_BTN_SELECTORS = [
    # Coursera dung aria-label='Video playback rate switcher'
    (By.CSS_SELECTOR, "button[aria-label='Video playback rate switcher']"),
    (By.CSS_SELECTOR, ".vjs-playback-rate .vjs-menu-item"),
    (By.CSS_SELECTOR, "[data-testid='playback-rate-button']"),
    (By.XPATH, "//button[contains(@aria-label,'playback') or contains(@aria-label,'rate') or contains(@aria-label,'speed')]"),
    (By.CSS_SELECTOR, ".rc-VideoControlBar button[aria-label*='speed' i]"),
]


def handle_video(driver) -> bool:
    """
    Xử lý phần Video.
    Trả về True nếu hoàn thành.
    """
    step("🎬 [VIDEO] Bắt đầu xử lý...")
    time.sleep(3)  # Chờ player load

    video = _find_video(driver)
    if not video:
        warn("Không tìm thấy video player — bỏ qua.")
        return False

    # Đảm bảo video đang chạy
    _play_video(driver, video)

    # Set tốc độ x2
    _set_playback_speed(driver, config.VIDEO_SPEED)

    # Đợi video chạy xong
    duration = _get_duration(driver, video)
    _wait_for_video_end(driver, video, duration)

    # Bấm Next
    click_next_item(driver)
    time.sleep(2)

    if is_item_completed(driver):
        success("Video đã hoàn thành ✔")
        return True
    else:
        # Thử kiểm tra thêm một lần nữa sau 3s
        time.sleep(3)
        if is_item_completed(driver):
            success("Video đã hoàn thành ✔")
            return True
        warn("Chưa thấy tích xanh ở Video.")
        return False


def _find_video(driver):
    for by, sel in VIDEO_PLAYER_SELECTORS:
        el = find_optional(driver, by, sel, timeout=10)
        if el:
            return el
    return None


def _play_video(driver, video):
    """Bấm play nếu video đang pause."""
    try:
        paused = driver.execute_script("return arguments[0].paused;", video)
        if paused:
            driver.execute_script("arguments[0].play();", video)
            info("▶ Video đã bắt đầu phát.")
        else:
            info("Video đã đang chạy.")
    except Exception as e:
        warn(f"Không thể play video via JS: {e}")
        # Thử click vào video
        try:
            safe_click(driver, video)
        except Exception:
            pass


def _set_playback_speed(driver, speed: float):
    """
    Thử set playback speed qua:
    1. JavaScript (nhanh nhất, đáng tin cậy nhất)
    2. Click UI button nếu JS thất bại
    """
    # Cách 1: JS trực tiếp
    try:
        videos = driver.find_elements(By.CSS_SELECTOR, "video")
        if videos:
            driver.execute_script(f"arguments[0].playbackRate = {speed};", videos[0])
            actual = driver.execute_script("return arguments[0].playbackRate;", videos[0])
            info(f"⚡ Tốc độ video: x{actual}")
            return
    except JavascriptException:
        pass

    # Cách 2: Click UI speed button
    _click_speed_button_ui(driver, speed)


def _click_speed_button_ui(driver, speed: float):
    """Click vào nút speed control trên UI Coursera."""
    speed_str = str(speed).rstrip('0').rstrip('.')  # "2.0" -> "2"

    # Tìm nút mở dropdown speed
    speed_toggles = [
        (By.CSS_SELECTOR, ".vjs-playback-rate"),
        (By.XPATH, "//button[contains(@aria-label,'playback rate') or contains(@aria-label,'speed')]"),
        (By.CSS_SELECTOR, ".rc-VideoControlBar [data-testid*='speed']"),
    ]
    for by, sel in speed_toggles:
        btn = find_optional(driver, by, sel, timeout=5)
        if btn:
            safe_click(driver, btn)
            time.sleep(0.5)
            break

    # Chọn tốc độ trong menu
    menu_items = driver.find_elements(
        By.XPATH,
        f"//*[contains(@class,'menu-item') or contains(@class,'playback') or contains(@class,'speed')]"
        f"[contains(text(),'{speed_str}') or contains(text(),'{speed}')]"
    )
    for item in menu_items:
        if speed_str in item.text or str(speed) in item.text:
            safe_click(driver, item)
            info(f"⚡ Đã chọn tốc độ x{speed} từ menu")
            return

    warn(f"Không tìm thấy menu item x{speed} — giữ tốc độ mặc định.")


def _get_duration(driver, video) -> float:
    """Lấy tổng thời lượng video (giây)."""
    try:
        dur = driver.execute_script("return arguments[0].duration;", video)
        if dur and dur > 0:
            mins = int(dur) // 60
            secs = int(dur) % 60
            info(f"⏱ Thời lượng video: {mins}m{secs:02d}s (sẽ đợi ~{dur/config.VIDEO_SPEED:.0f}s ở x{config.VIDEO_SPEED})")
            return float(dur)
    except Exception:
        pass
    info("Không lấy được thời lượng — ước tính 10 phút.")
    return 600.0


def _wait_for_video_end(driver, video, duration: float):
    """
    Đợi video xem xong bằng cách poll currentTime.
    Tính thời gian thực tế = duration / speed.
    """
    speed = config.VIDEO_SPEED
    real_wait = max((duration / speed) + 5, 10)  # Thêm 5s buffer
    poll_interval = 3
    elapsed = 0

    info(f"⏳ Đợi video kết thúc (~{real_wait:.0f}s thực tế)...")

    while elapsed < real_wait + 30:  # 30s buffer thêm
        time.sleep(poll_interval)
        elapsed += poll_interval

        try:
            current_time = driver.execute_script("return arguments[0].currentTime;", video)
            dur          = driver.execute_script("return arguments[0].duration;", video)
            ended        = driver.execute_script("return arguments[0].ended;", video)

            if ended or (dur and current_time and current_time >= dur - 1):
                info("🏁 Video đã kết thúc!")
                return

            # Hiển thị tiến trình
            if dur and dur > 0:
                pct = (current_time / dur) * 100
                print(f"\r  [VIDEO] {pct:5.1f}% ({int(current_time)}s/{int(dur)}s)", end="", flush=True)

        except Exception:
            pass  # Player có thể bị unload khi chuyển trang

    print()
    warn("Timeout đợi video — tiếp tục.")
