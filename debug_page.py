"""
Debug script - Kiem tra page source cua Coursera week page
"""
import os, time
os.environ["PYTHONUTF8"] = "1"

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

opts = Options()
opts.add_argument("--start-maximized")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

driver.get("https://www.coursera.org/learn/introtoux-principles-and-processes/home/week/1")
time.sleep(8)

print("=== CURRENT URL ===")
print(driver.current_url)

print("\n=== ALL <a> HREFS (first 50) ===")
links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
hrefs = [l.get_attribute("href") or "" for l in links]
hrefs = [h for h in hrefs if h]
print(f"Total <a> tags found: {len(hrefs)}")
for h in hrefs[:50]:
    print(f"  {h}")

print("\n=== LINKS CONTAINING 'lecture' or 'supplement' or 'discussion' ===")
lesson_hrefs = [h for h in hrefs if any(k in h.lower() for k in [
    "/lecture/", "/supplement/", "/discussionprompt/", "/exam/", "/peer/", "/learn/"
])]
for h in lesson_hrefs[:30]:
    print(f"  {h}")

print("\n=== PAGE SOURCE SNIPPET (contains 'lecture') ===")
src = driver.page_source
idx = src.lower().find("lecture")
if idx > -1:
    print(src[max(0, idx-200):idx+500])
else:
    print("Khong tim thay 'lecture' trong page source!")
    print("Page source length:", len(src))
    print("First 1000 chars:", src[:1000])

input("\nNhan Enter de dong browser...")
driver.quit()
