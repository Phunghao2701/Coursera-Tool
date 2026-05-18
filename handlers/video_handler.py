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
#  Flow:
#    1. Tìm video player
#    2. Đảm bảo video đang play (JS + click)
#    3. Set x2 speed
#    4. Đợi video xem xong (poll currentTime)
#    5. Bấm "Go to next item"
#    6. Kiểm tra tích xanh → retry nếu chưa
# ============================================================

VIDEO_PLAYER_SELECTORS = [
    (By.CSS_SELECTOR, "video"),
    (By.CSS_SELECTOR, ".vjs-tech"),
    (By.CSS_SELECTOR, "[data-testid='video-player'] video"),
]

PLAY_BTN_SELECTORS = [
    (By.CSS_SELECTOR, "button[aria-label='Play']"),
    (By.CSS_SELECTOR, "button[title='Play']"),
    (By.CSS_SELECTOR, ".vjs-play-control.vjs-paused"),
    (By.CSS_SELECTOR, ".rc-VideoMiniPlayer button[aria-label*='play' i]"),
    (By.XPATH, "//button[contains(@aria-label,'Play') and not(contains(@aria-label,'replay'))]"),
]


def handle_video(driver) -> bool:
    """
    Xử lý phần Video.
    Trả về True nếu hoàn thành (có tích xanh).
    """
    step("🎬 [VIDEO] Bắt đầu xử lý...")
    time.sleep(4)  # Chờ player load đầy đủ

    # --- UU TIEN: Neu da co tich xanh roi thi skip ---
    if is_item_completed(driver):
        success("Da co tich xanh - bo qua Video nay.")
        return True

    # --- Tìm video ---
    video = _find_video(driver)
    if not video:
        warn("Không tìm thấy video player — bỏ qua.")
        return False

    # --- Play video ---
    _ensure_playing(driver, video)

    # --- Set x2 speed ---
    _set_playback_speed(driver, config.VIDEO_SPEED)

    # --- Đợi xem xong ---
    duration = _get_duration(driver, video)
    _wait_for_video_end(driver, video, duration)

    # --- Đợi tích xanh xuất hiện TRƯỚC KHI BẤM NEXT (Theo yêu cầu) ---
    info("⏳ Đang chờ hệ thống Coursera xác nhận hoàn thành và xuất hiện tích xanh...")
    has_tick = False
    for attempt in range(5):
        time.sleep(2)
        if is_item_completed(driver):
            has_tick = True
            break

    if has_tick:
        success("Video đã hoàn thành và đạt tích xanh ✔. Bấm sang bài tiếp theo.")
        click_next_item(driver)
        time.sleep(2)
        return True

    # Chưa tích → có thể video chưa xem hết thực sự, tiến hành reload và xem lại (seek/retry)
    warn("⚠️ Vẫn chưa thấy tích xanh sau video — chạy cơ chế xem lại...")
    retry_ok = _retry_video(driver)
    if retry_ok:
        info("Đã đạt tích xanh sau khi xem lại. Bấm sang bài tiếp theo.")
        click_next_item(driver)
        time.sleep(2)
        return True
        
    return False


def _retry_video(driver) -> bool:
    """Quay lại trang hiện tại, xem lại video, kiểm tra lại."""
    for attempt in range(1, config.RETRY_LIMIT + 1):
        info(f"  Lần thử {attempt}/{config.RETRY_LIMIT}...")

        # Reload trang (giữ nguyên URL)
        current_url = driver.current_url
        driver.get(current_url)
        time.sleep(5)

        video = _find_video(driver)
        if not video:
            warn("Không tìm thấy video sau reload.")
            continue

        # Seek về cuối video để Coursera đánh dấu đã xem
        duration = _get_duration(driver, video)
        if duration > 0:
            try:
                # Seek đến 95% thời lượng rồi play tiếp
                seek_to = duration * 0.95
                driver.execute_script(f"arguments[0].currentTime = {seek_to};", video)
                driver.execute_script("arguments[0].play();", video)
                _set_playback_speed(driver, config.VIDEO_SPEED)
                info(f"  Seek đến {seek_to:.0f}s/{duration:.0f}s rồi play...")
                time.sleep(8)  # Đợi vài giây để Coursera ghi nhận
            except Exception as e:
                warn(f"  Không seek được: {e}")

        # Đảm bảo video ended
        try:
            driver.execute_script("arguments[0].currentTime = arguments[0].duration - 0.1;", video)
            driver.execute_script("arguments[0].play();", video)
            time.sleep(3)
        except Exception:
            pass

        # Kiểm tra tích xanh
        if is_item_completed(driver):
            success(f"Video hoàn thành ✔ (lần thử {attempt})")
            return True

        time.sleep(5)

    warn("Vẫn chưa thấy tích xanh sau nhiều lần thử.")
    return False


def _find_video(driver):
    for by, sel in VIDEO_PLAYER_SELECTORS:
        el = find_optional(driver, by, sel, timeout=10)
        if el:
            return el
    return None


def _ensure_playing(driver, video):
    """Đảm bảo video đang play bằng nhiều phương pháp."""
    # Cách 1: Click vào vùng video để focus
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", video)
        time.sleep(0.5)
    except Exception:
        pass

    # Cách 2: JS play()
    try:
        paused = driver.execute_script("return arguments[0].paused;", video)
        if paused:
            driver.execute_script("arguments[0].play();", video)
            time.sleep(1)
            # Kiểm tra lại
            paused = driver.execute_script("return arguments[0].paused;", video)
            if not paused:
                info("▶ Video đã bắt đầu phát (JS).")
                return
    except Exception:
        pass

    # Cách 3: Click nút Play trên UI
    for by, sel in PLAY_BTN_SELECTORS:
        btn = find_optional(driver, by, sel, timeout=3)
        if btn and btn.is_displayed():
            try:
                safe_click(driver, btn)
                info("▶ Video đã bắt đầu phát (click UI).")
                time.sleep(1)
                return
            except Exception:
                pass

    # Cách 4: Click vào video element
    try:
        safe_click(driver, video)
        info("▶ Click vào video player.")
    except Exception:
        pass


def _set_playback_speed(driver, speed: float):
    """Set tốc độ phát bằng JS (đáng tin cậy nhất)."""
    try:
        videos = driver.find_elements(By.CSS_SELECTOR, "video")
        if videos:
            driver.execute_script(f"arguments[0].playbackRate = {speed};", videos[0])
            actual = driver.execute_script("return arguments[0].playbackRate;", videos[0])
            info(f"⚡ Tốc độ video: x{actual}")
            return
    except JavascriptException:
        pass

    warn(f"Không set được tốc độ x{speed} qua JS.")


def _get_duration(driver, video) -> float:
    """Lấy tổng thời lượng video (giây)."""
    try:
        dur = driver.execute_script("return arguments[0].duration;", video)
        if dur and dur > 0:
            mins = int(dur) // 60
            secs = int(dur) % 60
            info(f"⏱ Thời lượng video: {mins}m{secs:02d}s (đợi ~{dur/config.VIDEO_SPEED:.0f}s ở x{config.VIDEO_SPEED})")
            return float(dur)
    except Exception:
        pass
    info("Không lấy được thời lượng — ước tính 10 phút.")
    return 600.0


def _wait_for_video_end(driver, video, duration: float):
    """
    Đợi video xem xong bằng cách poll currentTime.
    Thời gian thực tế = duration / speed.
    """
    speed = config.VIDEO_SPEED
    real_wait = max((duration / speed) + 5, 10)
    poll_interval = 3
    elapsed = 0

    info(f"⏳ Đợi video kết thúc (~{real_wait:.0f}s thực tế)...")

    stall_count = 0  # Đếm số lần video bị stall (progress không tăng)
    last_time = 0

    while elapsed < real_wait + 30:
        time.sleep(poll_interval)
        elapsed += poll_interval

        try:
            current_time = driver.execute_script("return arguments[0].currentTime;", video)
            dur          = driver.execute_script("return arguments[0].duration;", video)
            ended        = driver.execute_script("return arguments[0].ended;", video)

            if ended or (dur and current_time and current_time >= dur - 1):
                print()
                info("🏁 Video đã kết thúc!")
                return

            # Phát hiện video bị stall (pause giữa chừng)
            if current_time == last_time and elapsed > 10:
                stall_count += 1
                if stall_count >= 3:  # Stall 9 giây → thử play lại
                    warn("  Video bị dừng — thử play lại...")
                    try:
                        driver.execute_script("arguments[0].play();", video)
                        driver.execute_script(f"arguments[0].playbackRate = {speed};", video)
                    except Exception:
                        pass
                    stall_count = 0
            else:
                stall_count = 0
            last_time = current_time

            # Hiển thị tiến trình
            if dur and dur > 0:
                pct = (current_time / dur) * 100
                print(f"\r  [VIDEO] {pct:5.1f}% ({int(current_time)}s/{int(dur)}s)", end="", flush=True)

        except Exception:
            pass

    print()
    warn("Timeout đợi video — tiếp tục.")
