# -*- coding: utf-8 -*-
"""
COURSERA BOT - Main Entry Point
================================
Tu dong hoan thanh cac items trong khoa hoc Coursera:
  Reading    -> doi 30s
  Video      -> x2 toc do, doi het
  Discussion -> reply 'ok'
  Assignment -> bo qua
"""

import os, time, sys

# Set encoding truoc khi import bat ky thu gi in ra terminal
os.environ["PYTHONUTF8"] = "1"

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False

import config
from utils.logger import success, info, warn, error, step, skip, log
from utils.helpers import detect_item_type, is_item_completed, click_next_item, get_current_url
from utils.navigator import get_all_course_items, navigate_to_item

from handlers.reading_handler    import handle_reading
from handlers.video_handler      import handle_video
from handlers.discussion_handler import handle_discussion
from handlers.assignment_handler import handle_assignment

# ============================================================
#  COURSERA BOT CLASS
# ============================================================

class CourseraBot:
    def __init__(self):
        self.driver  = None
        self.stats   = {
            "reading":    {"done": 0, "failed": 0},
            "video":      {"done": 0, "failed": 0},
            "discussion": {"done": 0, "failed": 0},
            "graded":     {"skipped": 0},
            "unknown":    {"skipped": 0},
        }

    # ----------------------------------------------------------
    #  SETUP
    # ----------------------------------------------------------
    def setup_driver(self):
        """Khoi tao Chrome WebDriver."""
        step("Khoi tao Chrome WebDriver...")
        opts = Options()

        if config.HEADLESS:
            opts.add_argument("--headless=new")

        # Anti-bot options
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--window-size=1440,900")
        opts.add_argument("--start-maximized")

        # User agent thuc te
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

        if USE_WDM:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=opts)
        else:
            self.driver = webdriver.Chrome(options=opts)

        # An webdriver flag
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        success("Chrome da khoi dong!")

    # ----------------------------------------------------------
    #  LOGIN
    # ----------------------------------------------------------
    def login(self):
        """Dang nhap vao Coursera."""
        step("Dang dang nhap vao Coursera...")

        self.driver.get("https://www.coursera.org/login")
        time.sleep(6)

        # Dong popup neu co
        self._close_popups()

        # ---- Kiem tra da login san chua ----
        if self._is_logged_in():
            success("Da co session - khong can dang nhap lai!")
            return

        # ---- BUOC 1: Nhap email ----
        # Coursera dung aria-label='Email' tren input
        email_selectors = [
            (By.CSS_SELECTOR, "input[aria-label='Email']"),
            (By.CSS_SELECTOR, "input#email"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[autocomplete='email']"),
        ]
        email_input = self._find_first(email_selectors, timeout=15)
        if not email_input:
            error("Khong tim thay o nhap email!")
            raise RuntimeError("Login failed: email field not found")

        email_input.clear()
        time.sleep(0.4)
        email_input.send_keys(config.EMAIL)
        info(f"Da nhap email: {config.EMAIL}")
        time.sleep(0.5)

        # ---- BUOC 2: Bam "Continue" ----
        # Nut Continue xuat hien sau khi nhap email
        continue_selectors = [
            (By.XPATH, "//button[contains(text(),'Continue')]"),
            (By.XPATH, "//button[text()='Continue']"),
            (By.CSS_SELECTOR, "button.css-hsv6bp"),
            (By.CSS_SELECTOR, "form button[type='submit']"),
        ]
        cont_btn = self._find_first(continue_selectors, timeout=10)
        if cont_btn:
            try:
                self.driver.execute_script("arguments[0].click();", cont_btn)
                info("Da bam Continue...")
            except Exception:
                cont_btn.click()
        else:
            from selenium.webdriver.common.keys import Keys
            email_input.send_keys(Keys.RETURN)
            info("Da bam Enter o email field...")

        time.sleep(4)  # Cho password field xuat hien

        # ---- BUOC 3: Nhap password ----
        # Coursera dung aria-label='Password'
        pass_selectors = [
            (By.CSS_SELECTOR, "input[aria-label='Password']"),
            (By.CSS_SELECTOR, "input#password"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
        ]
        pass_input = self._find_first(pass_selectors, timeout=15)
        if not pass_input:
            warn("Khong thay password field - thu them 10s...")
            time.sleep(10)
            pass_input = self._find_first(pass_selectors, timeout=10)

        if not pass_input:
            error("Khong tim thay o nhap password!")
            raise RuntimeError("Login failed: password field not found")

        pass_input.clear()
        time.sleep(0.3)
        pass_input.send_keys(config.PASSWORD)
        info("Da nhap password.")
        time.sleep(0.5)

        # ---- BUOC 4: Bam "Next" (nut Log in cuoi cung) ----
        login_selectors = [
            (By.XPATH, "//button[contains(text(),'Next') or contains(text(),'Log in') or contains(text(),'Sign in')]"),
            (By.CSS_SELECTOR, "button.css-5wsq95"),
            (By.CSS_SELECTOR, "form button[type='submit']"),
        ]
        login_btn = self._find_first(login_selectors, timeout=10)
        if login_btn:
            try:
                self.driver.execute_script("arguments[0].click();", login_btn)
                info("Da bam Next/Log in...")
            except Exception:
                login_btn.click()
        else:
            from selenium.webdriver.common.keys import Keys
            pass_input.send_keys(Keys.RETURN)

        info("Da bam Log in - dang cho redirect...")
        time.sleep(10)

        # ---- Kiem tra ket qua ----
        if self._is_logged_in():
            success("Dang nhap thanh cong!")
        else:
            warn("Chua confirm duoc login - doi them 20s...")
            time.sleep(20)
            if self._is_logged_in():
                success("Dang nhap thanh cong!")
            else:
                warn("Bot se tiep tuc nhung co the chua login.")


    def _close_popups(self):
        """Dong cac popup/overlay neu co (cookie banner, modal...)."""
        close_selectors = [
            (By.CSS_SELECTOR, "button[aria-label='Close']"),
            (By.CSS_SELECTOR, "button[aria-label='close']"),
            (By.XPATH, "//button[contains(@class,'close') or contains(@class,'dismiss')]"),
            (By.CSS_SELECTOR, "[data-testid='close-button']"),
        ]
        for by, sel in close_selectors:
            try:
                btns = self.driver.find_elements(by, sel)
                for btn in btns:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(0.5)
            except Exception:
                pass

    def _is_logged_in(self) -> bool:
        """Kiem tra da dang nhap chua."""
        # Cach tin cay nhat: tim element chi co khi da dang nhap
        logged_in_indicators = [
            (By.CSS_SELECTOR, "[data-testid='user-avatar']"),
            (By.CSS_SELECTOR, "[data-testid='nav-logged-in']"),
            (By.CSS_SELECTOR, "#user-avatar"),
            (By.CSS_SELECTOR, ".c-ph-avatar"),
            (By.XPATH, "//*[@aria-label='Open user menu' or @aria-label='User menu']"),
        ]
        for by, sel in logged_in_indicators:
            try:
                el = self.driver.find_element(by, sel)
                if el.is_displayed():
                    return True
            except Exception:
                pass

        # Kiem tra URL: neu dang o /learn/ -> da vao khoa hoc -> da login
        url = self.driver.current_url.lower()
        if "/learn/" in url and "/login" not in url and "authmode" not in url:
            # Kiem tra them: page co content khoa hoc khong
            try:
                src = self.driver.page_source
                if len(src) > 10000 and "coursera" in src.lower():
                    # Co the da login, kiem tra khong co form login
                    if "id=\"email\"" not in src and 'name="email"' not in src:
                        return True
            except Exception:
                pass

        return False

    # ----------------------------------------------------------
    #  MAIN RUNNER
    # ----------------------------------------------------------
    def run(self):
        """Chay bot qua toan bo khoa hoc."""
        step(f"Bat dau chay khoa hoc: {config.COURSE_URL}")
        self.driver.get(config.COURSE_URL)
        time.sleep(4)

        # Lay danh sach tat ca items
        info("Dang quet danh sach items trong khoa hoc...")
        items = get_all_course_items(self.driver)

        if not items:
            warn("Khong lay duoc danh sach items tu sidebar - chay tuan tu tu trang dau.")
            self._run_sequential()
            return

        info(f"Tong cong {len(items)} items tim thay.")
        self._print_item_list(items)

        # Xu ly tung item
        for idx, item in enumerate(items, 1):
            log.info("\n" + "="*60)
            log.info(f"[{idx}/{len(items)}] {item['name']} | Type: {item['type']}")
            log.info(f"   URL: {item['url']}")

            if item.get("completed"):
                success("Da hoan thanh truoc do - bo qua.")
                continue

            self._process_item(item, retry=config.RETRY_LIMIT)

        self._print_stats()

    def _run_sequential(self):
        """Fallback: chay tuan tu bang nut Next."""
        step("Chay che do tuan tu (khong can sidebar)...")
        self.driver.get(config.COURSE_URL)
        time.sleep(3)

        # Tim nut "Start" hoac item dau tien
        start_selectors = [
            (By.XPATH, "//a[contains(text(),'Start') or contains(text(),'Resume')]"),
            (By.CSS_SELECTOR, "a[href*='/item/']"),
        ]
        start_btn = self._find_first(start_selectors, timeout=10)
        if start_btn:
            start_btn.click()
            time.sleep(3)

        visited = set()
        count   = 0

        while count < 300:
            url = get_current_url(self.driver)
            if url in visited:
                break
            visited.add(url)

            # Phat hien loai item tu URL + noi dung trang
            item_type = self._detect_current_type()
            item = {"name": f"Item {count+1}", "url": url, "type": item_type}

            log.info("\n" + "="*60)
            log.info(f"[{count+1}] Type: {item_type} | URL: {url}")

            self._process_item(item, retry=config.RETRY_LIMIT)
            count += 1

            moved = click_next_item(self.driver)
            if not moved:
                break
            time.sleep(2)

        self._print_stats()

    # ----------------------------------------------------------
    #  ITEM PROCESSOR
    # ----------------------------------------------------------
    def _process_item(self, item: dict, retry: int = 3):
        """Xu ly mot item, thu lai neu that bai."""
        navigate_to_item(self.driver, item)
        item_type = item.get("type", "unknown")

        # --- UU TIEN: Check tich xanh LIVE tren trang thuc te ---
        # Neu da co roi thi skip, khong can lam gi
        if item_type not in ("graded", "unknown"):
            time.sleep(2)  # Doi trang load
            if is_item_completed(self.driver):
                success(f"Da co tich xanh - bo qua [{item['name'][:40]}]")
                self._update_stats(item_type, True)
                return

        ok = False
        for attempt in range(1, retry + 1):
            if attempt > 1:
                warn(f"  Thu lai lan {attempt}/{retry}...")
                time.sleep(3)
                # Check lai truoc moi lan retry
                if is_item_completed(self.driver):
                    success(f"Da co tich xanh - dung retry.")
                    ok = True
                    break

            ok = self._dispatch(item_type)

            if ok:
                break
            elif attempt == retry:
                error(f"Sau {retry} lan thu van that bai: {item['name']}")

        # Cap nhat stats
        self._update_stats(item_type, ok)

    def _dispatch(self, item_type: str) -> bool:
        """Phan phoi handler theo loai item."""
        if item_type == "reading":
            return handle_reading(self.driver)
        elif item_type == "video":
            return handle_video(self.driver)
        elif item_type == "discussion":
            return handle_discussion(self.driver)
        elif item_type == "graded":
            return handle_assignment(self.driver)
        else:
            # Unknown: thu detect lai tu trang thuc te
            detected = self._detect_current_type()
            if detected != "unknown":
                info(f"Re-detected as: {detected}")
                return self._dispatch(detected)
            skip(f"Loai '{item_type}' khong xac dinh - bo qua.")
            return True

    def _detect_current_type(self) -> str:
        """Phat hien loai item hien tai tu URL va noi dung trang."""
        url = self.driver.current_url.lower()
        try:
            page_src = self.driver.page_source.lower()[:3000]
        except Exception:
            page_src = ""

        combined = url + " " + page_src

        # Graded (uu tien cao nhat - khong lam)
        graded_kw = ["graded", "peer-review", "peer review", "assignment",
                     "quiz", "exam", "programming-assignment"]
        if any(k in combined for k in graded_kw):
            return "graded"

        # Video
        if any(k in combined for k in ["video", "lecture", "vjs", "vimeo", "youtube"]):
            return "video"

        # Discussion
        if any(k in combined for k in ["discussion", "prompt", "forum"]):
            return "discussion"

        # Reading
        if any(k in combined for k in ["reading", "supplement", "article"]):
            return "reading"

        # Kiem tra co video player khong
        try:
            vids = self.driver.find_elements(By.CSS_SELECTOR, "video")
            if vids:
                return "video"
        except Exception:
            pass

        return "unknown"

    # ----------------------------------------------------------
    #  HELPERS
    # ----------------------------------------------------------
    def _find_first(self, selectors: list, timeout: int = 10):
        for by, sel in selectors:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, sel))
                )
                return el
            except TimeoutException:
                pass
        return None

    def _print_item_list(self, items: list):
        log.info("\n" + "-"*60)
        log.info("DANH SACH ITEMS:")
        for i, it in enumerate(items, 1):
            status = "[done]" if it.get("completed") else "[    ]"
            log.info(f"  {status} [{i:3d}] [{it['type']:12s}] {it['name']}")
        log.info("-"*60 + "\n")

    def _update_stats(self, item_type: str, ok: bool):
        if item_type in ("graded", "unknown"):
            key = item_type if item_type in self.stats else "unknown"
            self.stats[key]["skipped"] = self.stats[key].get("skipped", 0) + 1
        elif item_type in self.stats:
            k = "done" if ok else "failed"
            self.stats[item_type][k] += 1

    def _print_stats(self):
        log.info("\n" + "="*60)
        log.info("KET QUA CUOI CUNG:")
        log.info(f"  Reading:    [OK] {self.stats['reading']['done']} done | [XX] {self.stats['reading']['failed']} failed")
        log.info(f"  Video:      [OK] {self.stats['video']['done']} done | [XX] {self.stats['video']['failed']} failed")
        log.info(f"  Discussion: [OK] {self.stats['discussion']['done']} done | [XX] {self.stats['discussion']['failed']} failed")
        log.info(f"  Graded:     [--] {self.stats['graded']['skipped']} skipped")
        log.info("="*60)

    # ----------------------------------------------------------
    #  CLEANUP
    # ----------------------------------------------------------
    def quit(self):
        if self.driver:
            self.driver.quit()
            info("Browser da dong.")


# ============================================================
#  ENTRY POINT
# ============================================================

def main():
    print("\n" + "="*60)
    print("   [BOT] COURSERA BOT  |  Tu dong hoan thanh khoa hoc")
    print("="*60 + "\n")

    bot = CourseraBot()
    try:
        bot.setup_driver()
        bot.login()
        bot.run()
        success("XONG! Hoan thanh toan bo khoa hoc!")
    except KeyboardInterrupt:
        warn("Bot bi dung boi nguoi dung (Ctrl+C).")
    except Exception as e:
        error(f"Loi khong mong muon: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            input("\n[Bot da xong] Nhan Enter de dong browser...")
        except Exception:
            pass
        bot.quit()


if __name__ == "__main__":
    main()
