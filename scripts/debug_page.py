# -*- coding: utf-8 -*-
"""
Debug script - Kiểm tra page source và danh sách element của Coursera week/module page.
Chạy trực tiếp:
    python scripts/debug_page.py
"""
import os
import sys
import time
from pathlib import Path

# Thêm thư mục gốc vào sys.path để có thể dùng config nếu cần
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ["PYTHONUTF8"] = "1"

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

try:
    import config
    DEFAULT_URL = config.COURSE_URL or "https://www.coursera.org/learn/introtoux-principles-and-processes/home/week/1"
except Exception:
    DEFAULT_URL = "https://www.coursera.org/learn/introtoux-principles-and-processes/home/week/1"


def main():
    print(f"Target URL: {DEFAULT_URL}")
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)

    try:
        driver.get(DEFAULT_URL)
        time.sleep(8)

        print("\n=== CURRENT URL ===")
        print(driver.current_url)

        print("\n=== ALL <a> HREFS (first 50) ===")
        links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        hrefs = [l.get_attribute("href") or "" for l in links]
        hrefs = [h for h in hrefs if h]
        print(f"Total <a> tags found: {len(hrefs)}")
        for h in hrefs[:50]:
            print(f"  {h}")

        print("\n=== LINKS CONTAINING LESSON KEYWORDS ===")
        lesson_hrefs = [h for h in hrefs if any(k in h.lower() for k in [
            "/lecture/", "/supplement/", "/discussionprompt/", "/exam/", "/peer/", "/learn/"
        ])]
        for h in lesson_hrefs[:30]:
            print(f"  {h}")

        print("\n=== PAGE SOURCE SNIPPET (contains 'lecture') ===")
        src = driver.page_source
        idx = src.lower().find("lecture")
        if idx > -1:
            print(src[max(0, idx - 200):idx + 500])
        else:
            print("Khong tim thay 'lecture' trong page source!")
            print("Page source length:", len(src))
            print("First 1000 chars:", src[:1000])

    finally:
        input("\nNhan Enter de dong browser...")
        driver.quit()


if __name__ == "__main__":
    main()
