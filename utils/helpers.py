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
    # [1] Trang Reading/Supplement: hien thi div/h3 rieng khi done
    (By.CSS_SELECTOR, "[data-testid='completed-text']"),
    (By.XPATH, "//h3[contains(@aria-label,' completed')]"),

    # [2] Sidebar link CUA ITEM DANG XEM:
    # aria-label = "selected link, Video, <ten>, Completed, X min"
    # Dung cho ca Reading va Video - day la indicator chinh xac nhat
    (By.XPATH, "//a[contains(@aria-label,'selected') and contains(@aria-label,'Completed')]"),

    # [3] Class cu cua Coursera (phong truong hop)
    (By.CSS_SELECTOR, ".rc-ItemCompleted"),
    (By.CSS_SELECTOR, ".item-navigation-link--completed"),
]

def is_item_completed(driver) -> bool:
    """
    Kiem tra tich xanh cua ITEM HIEN TAI dang xem.
    Dung sidebar 'selected link' + 'Completed' cho Video.
    Dung data-testid='completed-text' / h3 cho Reading.
    """
    time.sleep(1)

    for by, sel in COMPLETED_SELECTORS:
        try:
            elems = driver.find_elements(by, sel)
            visible = [e for e in elems if e.is_displayed()]
            if visible:
                info(f"  [Tick xanh] {sel[:60]} | text='{visible[0].text[:30]}'")
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
