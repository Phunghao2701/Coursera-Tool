import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import config
from utils.logger import success, info, warn, error, step

# ============================================================
#  DRIVER HELPERS
# ============================================================

def wait_for(driver, by, selector, timeout=None):
    """Chờ element xuất hiện và trả về nó."""
    t = timeout or config.ELEMENT_TIMEOUT
    return WebDriverWait(driver, t).until(
        EC.presence_of_element_located((by, selector))
    )

def wait_for_clickable(driver, by, selector, timeout=None):
    t = timeout or config.ELEMENT_TIMEOUT
    return WebDriverWait(driver, t).until(
        EC.element_to_be_clickable((by, selector))
    )

def safe_click(driver, element):
    """Click an element, scrolling into view if needed."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.4)
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)

def find_optional(driver, by, selector, timeout=5):
    """Tìm element, trả về None nếu không thấy (không raise)."""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        return None

# ============================================================
#  ITEM-TYPE DETECTOR
# ============================================================

ITEM_TYPES = {
    "reading":    ["LectureItemType", "Supplement", "reading"],
    "video":      ["Lecture", "video"],
    "discussion": ["DiscussionPrompt", "discussion", "prompt"],
    "graded":     ["GradedLti", "GradedProgramming", "exam", "quiz",
                   "peer", "assignment", "GradedDiscussion"],
}

def detect_item_type(item_name: str, item_type_hint: str = "") -> str:
    """
    Trả về: 'reading' | 'video' | 'discussion' | 'graded' | 'unknown'
    dựa trên tên & type hint từ sidebar.
    """
    combined = (item_name + " " + item_type_hint).lower()

    graded_kw = ["graded", "peer", "assignment", "quiz", "exam", "test",
                 "programming", "assessment"]
    if any(k in combined for k in graded_kw):
        return "graded"

    if any(k in combined for k in ["video", "lecture"]):
        return "video"

    if any(k in combined for k in ["discussion", "prompt"]):
        return "discussion"

    if any(k in combined for k in ["reading", "supplement", "article"]):
        return "reading"

    return "unknown"

# ============================================================
#  COMPLETION CHECKER (tích xanh)
# ============================================================

COMPLETED_SELECTORS = [
    # Coursera dung aria-label='Completed' tren icon trong sidebar
    (By.CSS_SELECTOR, "svg[aria-label='Completed']"),
    (By.CSS_SELECTOR, "[aria-label='Completed']"),
    # Hoac co class completed trong breadcrumb/header
    (By.CSS_SELECTOR, "[data-testid='completed-icon']"),
    (By.CSS_SELECTOR, ".item-navigation-link--completed"),
    (By.CSS_SELECTOR, "[class*='completed']"),
    # Check URL trang confirm
    (By.XPATH, "//*[contains(@aria-label,'Completed') or contains(@aria-label,'completed')]"),
]

def is_item_completed(driver) -> bool:
    """Kiem tra xem item hien tai da co tich xanh chua."""
    time.sleep(2)
    # Cach 1: Tim selector tren trang
    for by, sel in COMPLETED_SELECTORS:
        try:
            elems = driver.find_elements(by, sel)
            if elems:
                return True
        except Exception:
            pass
    # Cach 2: Kiem tra noi dung page source
    try:
        src = driver.page_source.lower()
        # Sau khi hoan thanh, Coursera co the hien 'well done', 'great job' etc.
        completion_signals = ['well done', 'great job', 'you passed', 'nice work']
        if any(sig in src for sig in completion_signals):
            return True
    except Exception:
        pass
    return False

# ============================================================
#  NAVIGATION
# ============================================================

NEXT_BTN_SELECTORS = [
    # Coursera dung aria-label='Go to next item'
    (By.CSS_SELECTOR, "button[aria-label='Go to next item']"),
    (By.CSS_SELECTOR, "a[aria-label='Go to next item']"),
    (By.CSS_SELECTOR, "[data-testid='next-item-btn']"),
    (By.CSS_SELECTOR, "button.next-btn"),
    (By.XPATH, "//button[contains(@aria-label,'next') or contains(@aria-label,'Next')]"),
    (By.XPATH, "//a[contains(@aria-label,'next') or contains(@aria-label,'Next')]"),
    (By.XPATH, "//button[contains(.,'Next') or contains(.,'Continue') or contains(.,'Go to next item')]"),
]

def click_next_item(driver) -> bool:
    """Bấm nút Next / Continue. Trả về True nếu thành công."""
    for by, sel in NEXT_BTN_SELECTORS:
        try:
            btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((by, sel)))
            safe_click(driver, btn)
            info("Đã bấm Next ▶")
            time.sleep(2)
            return True
        except TimeoutException:
            pass
    warn("Không tìm thấy nút Next.")
    return False

def get_current_url(driver) -> str:
    return driver.current_url
