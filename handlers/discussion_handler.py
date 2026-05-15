import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

import config
from utils.logger import success, info, warn, error, step
from utils.helpers import find_optional, safe_click, is_item_completed, click_next_item

# ============================================================
#  DISCUSSION HANDLER
#  Điền "ok" vào ô reply và submit
# ============================================================

REPLY_BOX_SELECTORS = [
    (By.CSS_SELECTOR, "[data-testid='reply-text-area'] textarea"),
    (By.CSS_SELECTOR, "textarea[placeholder*='response' i]"),
    (By.CSS_SELECTOR, "textarea[placeholder*='reply' i]"),
    (By.CSS_SELECTOR, "div[contenteditable='true']"),
    (By.CSS_SELECTOR, ".ql-editor"),               # Quill editor
    (By.CSS_SELECTOR, "[role='textbox']"),
    (By.XPATH, "//textarea[contains(@placeholder,'response') or contains(@placeholder,'write') or contains(@placeholder,'share')]"),
]

SUBMIT_BTN_SELECTORS = [
    (By.CSS_SELECTOR, "[data-testid='submit-reply-btn']"),
    (By.CSS_SELECTOR, "button[data-testid*='submit']"),
    (By.XPATH, "//button[contains(text(),'Submit') or contains(text(),'Post') or contains(text(),'Reply')]"),
    (By.CSS_SELECTOR, "button.reply-submit-btn"),
    (By.CSS_SELECTOR, "button[type='submit']"),
]


def handle_discussion(driver) -> bool:
    """
    Xử lý phần Discussion Prompt.
    1. Tìm ô nhập text
    2. Điền config.DISCUSSION_TEXT ("ok")
    3. Submit
    4. Kiểm tra tích xanh
    Trả về True nếu hoàn thành.
    """
    step("💬 [DISCUSSION] Bắt đầu xử lý...")
    time.sleep(3)

    # ---- Kiểm tra xem đã reply chưa ----
    if _already_replied(driver):
        info("Đã có reply trước đó — bỏ qua nhập lại.")
        time.sleep(2)
        if is_item_completed(driver):
            success("Discussion đã hoàn thành ✔")
            return True

    # ---- Tìm ô input ----
    reply_box = _find_reply_box(driver)
    if not reply_box:
        warn("Không tìm thấy ô nhập reply — thử cuộn và tìm lại.")
        _scroll_to_prompt(driver)
        reply_box = _find_reply_box(driver)

    if not reply_box:
        error("Không tìm thấy ô nhập Discussion reply.")
        return False

    # ---- Điền text ----
    _type_reply(driver, reply_box, config.DISCUSSION_TEXT)

    # ---- Submit ----
    submitted = _submit_reply(driver)
    if not submitted:
        warn("Không tìm thấy nút Submit — thử Enter.")
        reply_box.send_keys(Keys.CONTROL + Keys.RETURN)

    time.sleep(3)

    # ---- Bấm Next ----
    click_next_item(driver)
    time.sleep(2)

    if is_item_completed(driver):
        success("Discussion đã hoàn thành ✔")
        return True
    else:
        time.sleep(3)
        if is_item_completed(driver):
            success("Discussion đã hoàn thành ✔")
            return True
        warn("Chưa thấy tích xanh ở Discussion.")
        return False


def _already_replied(driver) -> bool:
    """Kiểm tra xem đã có reply trước đó chưa."""
    markers = [
        (By.CSS_SELECTOR, "[data-testid='your-response']"),
        (By.CSS_SELECTOR, ".rc-DiscussionPrompt--submitted"),
        (By.XPATH, "//*[contains(@class,'submitted') or contains(@class,'your-response')]"),
        (By.XPATH, "//*[contains(text(),'Your response') or contains(text(),'Your reply')]"),
    ]
    for by, sel in markers:
        el = find_optional(driver, by, sel, timeout=3)
        if el:
            return True
    return False


def _find_reply_box(driver):
    """Tìm ô nhập reply."""
    for by, sel in REPLY_BOX_SELECTORS:
        el = find_optional(driver, by, sel, timeout=5)
        if el and el.is_displayed():
            return el
    return None


def _scroll_to_prompt(driver):
    """Cuộn đến phần Discussion."""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(1)


def _type_reply(driver, element, text: str):
    """Điền text vào ô reply."""
    try:
        # Clear trước
        element.clear()
    except Exception:
        try:
            driver.execute_script("arguments[0].innerHTML = '';", element)
        except Exception:
            pass

    time.sleep(0.3)

    try:
        element.click()
        time.sleep(0.3)
        element.send_keys(text)
        info(f"Đã nhập: '{text}'")
    except Exception:
        # Fallback: JS input
        driver.execute_script(f"arguments[0].value = '{text}';", element)
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {{ bubbles: true }}));",
            element
        )
        info(f"Đã nhập (JS): '{text}'")


def _submit_reply(driver) -> bool:
    """Bấm nút Submit/Post."""
    for by, sel in SUBMIT_BTN_SELECTORS:
        btn = find_optional(driver, by, sel, timeout=5)
        if btn and btn.is_displayed() and btn.is_enabled():
            safe_click(driver, btn)
            info("Đã bấm Submit ✓")
            return True
    return False
