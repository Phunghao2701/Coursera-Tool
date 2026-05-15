"""
Debug: Tu dong login va scan HTML tim selector tich xanh.
Khong can nhap gi ca - chi chay va doc ket qua.
"""
import os, sys, time
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, r"c:\Users\LENOVO\Desktop\tool coursera")

import config
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# URLs can test: 1 reading, 1 video (thay bang URL thuc cua ban neu can)
TEST_URLS = [
    # Reading da completed (Welcome)
    "https://www.coursera.org/learn/introtoux-principles-and-processes/supplement/9xlDj/welcome-to-introduction-to-user-experience",
    # Video da completed (Welcome video ngan)
    "https://www.coursera.org/learn/introtoux-principles-and-processes/lecture/Q6s0b/welcome",
    # Video chua completed (UX Design Overview)
    "https://www.coursera.org/learn/introtoux-principles-and-processes/lecture/pNbmj/ux-design-overview",
]

# --- Setup driver ---
opts = Options()
opts.add_argument("--start-maximized")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
    {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"})

# --- Tu dong login ---
print("[1/3] Dang login Coursera...")
driver.get("https://www.coursera.org/login")
time.sleep(6)

def find_first(selectors, timeout=10):
    for by, sel in selectors:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, sel))
            )
            return el
        except:
            pass
    return None

email_input = find_first([
    (By.CSS_SELECTOR, "input[aria-label='Email']"),
    (By.CSS_SELECTOR, "input#email"),
    (By.CSS_SELECTOR, "input[type='email']"),
])
if email_input:
    email_input.clear()
    email_input.send_keys(config.EMAIL)
    time.sleep(0.5)
    # Continue
    cont = find_first([(By.XPATH, "//button[contains(text(),'Continue')]"),
                       (By.CSS_SELECTOR, "form button[type='submit']")])
    if cont:
        driver.execute_script("arguments[0].click();", cont)
        time.sleep(4)
    pass_input = find_first([
        (By.CSS_SELECTOR, "input[aria-label='Password']"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ])
    if pass_input:
        pass_input.send_keys(config.PASSWORD)
        time.sleep(0.5)
        login_btn = find_first([(By.XPATH, "//button[contains(text(),'Next') or contains(text(),'Log in')]"),
                                (By.CSS_SELECTOR, "form button[type='submit']")])
        if login_btn:
            driver.execute_script("arguments[0].click();", login_btn)
    time.sleep(10)

print(f"[2/3] Da login. URL hien tai: {driver.current_url}")

# --- Scan tung URL ---
for url in TEST_URLS:
    driver.get(url)
    print(f"\nDang load: {url}")
    time.sleep(8)
    print(f"URL sau load: {driver.current_url}")

    print("\n--- Quet elements co 'completed'/'check' trong DOM ---")
    results = driver.execute_script("""
        var results = [];
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            var el = all[i];
            var cls = (typeof el.className === 'string') ? el.className : '';
            var aria = el.getAttribute('aria-label') || '';
            var testid = el.getAttribute('data-testid') || '';
            var tag = el.tagName;
            var clsLow = cls.toLowerCase();
            var ariaLow = aria.toLowerCase();
            var testLow = testid.toLowerCase();

            if (clsLow.includes('completed') || ariaLow.includes('completed') ||
                testLow.includes('completed') || testLow.includes('checkmark') ||
                testLow.includes('check-icon') || ariaLow.includes('checkmark')) {
                results.push({
                    tag: tag,
                    class: cls.substring(0, 100),
                    aria: aria,
                    testid: testid,
                    visible: (el.offsetWidth > 0 && el.offsetHeight > 0),
                    text: (el.textContent || '').trim().substring(0, 60)
                });
            }
        }
        return results;
    """)

    if results:
        print(f"Tim thay {len(results)} elements:")
        for r in results:
            vis = "VISIBLE" if r['visible'] else "hidden"
            print(f"  [{vis}] <{r['tag']}> aria='{r['aria']}' testid='{r['testid']}'")
            print(f"          class='{r['class'][:80]}'")
            if r['text']:
                print(f"          text='{r['text']}'")
    else:
        print("  Khong tim thay element nao co 'completed' trong DOM!")
        print("  => Item NAY CHUA duoc Coursera danh dau completed")
        print("     HOAC tich xanh duoc render bang cach khac")

    # Goi is_item_completed
    import utils.helpers as h
    import importlib; importlib.reload(h)
    result = h.is_item_completed(driver)
    print(f"\n  is_item_completed() => {result}")

print("\n[3/3] Xong! Bot se tu dong dong sau 5s...")
time.sleep(5)
driver.quit()
print("Da dong.")
