import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import config
from utils.logger import success, info, warn, error, step
from utils.helpers import find_optional, safe_click, is_item_completed

def handle_discussion(driver) -> bool:
    """
    Xử lý Discussion Prompt:
    1. Nhập văn bản thảo luận (nếu có ô nhập)
    2. Đợi 3 giây
    3. Ấn Reply / Post / Submit
    4. Kiểm tra hoàn thành.
    """
    step("💬 [DISCUSSION] Bắt đầu xử lý Discussion Prompt...")

    # [1] Tìm ô nhập phản hồi
    # Có thể cần click vào nút "Reply" hoặc "Reply to prompt" trước để hiện textarea
    reply_triggers = [
        (By.XPATH, "//button[contains(span/text(), 'Reply to prompt') or contains(text(), 'Reply to prompt')]"),
        (By.XPATH, "//button[contains(., 'Reply to prompt')]"),
        (By.XPATH, "//button[contains(., 'Start a conversation')]"),
        (By.XPATH, "//button[contains(., 'Add a response')]"),
        (By.XPATH, "//button[contains(., 'Reply') and not(contains(@aria-label, 'comment'))]"),
    ]

    # Cuộn xuống một chút để đảm bảo các thành phần thảo luận load/hiển thị
    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(1.5)

    # Thử click trigger mở form nếu có
    for by, sel in reply_triggers:
        btn = find_optional(driver, by, sel, timeout=3)
        if btn and btn.is_displayed():
            info(f"  Tìm thấy nút mở form thảo luận: {sel}")
            safe_click(driver, btn)
            time.sleep(1.5)
            break

    # Các selector cho ô nhập Text Area thảo luận
    textarea_selectors = [
        (By.CSS_SELECTOR, "textarea"),
        (By.CSS_SELECTOR, "[data-testid='comment-textarea']"),
        (By.CSS_SELECTOR, "div[role='textbox']"),
        (By.XPATH, "//textarea[contains(@placeholder, 'thought') or contains(@placeholder, 'response') or contains(@placeholder, 'reply') or contains(@placeholder, 'post')]"),
        (By.XPATH, "//div[contains(@contenteditable, 'true')]"),
    ]

    textarea = None
    for by, sel in textarea_selectors:
        textarea = find_optional(driver, by, sel, timeout=5)
        if textarea and textarea.is_displayed():
            info(f"  Tìm thấy ô nhập thảo luận: {sel}")
            break

    if not textarea:
        warn("Không tìm thấy ô nhập thảo luận. Có thể đã hoàn thành hoặc thiết kế khác.")
        # Thử kiểm tra tích xanh luôn
        if is_item_completed(driver):
            success("  Discussion đã hoàn thành sẵn!")
            return True
        return False

    # Nhập nội dung thảo luận
    text_to_type = getattr(config, "DISCUSSION_TEXT", "ok")
    
    try:
        # Click để focus
        textarea.click()
        time.sleep(0.5)
        
        # Kiểm tra loại phần tử (contenteditable hay textarea/input thông thường)
        is_contenteditable = textarea.get_attribute("contenteditable") == "true" or textarea.get_attribute("role") == "textbox"
        
        if is_contenteditable:
            # Đối với rich text editor (Draft.js) của Coursera, TUYỆT ĐỐI không dùng innerHTML vì sẽ phá vỡ cấu trúc DOM của React.
            # Chúng ta dùng ActionChains click và gõ ký tự trực tiếp.
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.common.keys import Keys
            
            # Click để focus bằng ActionChains
            actions = ActionChains(driver)
            actions.move_to_element(textarea).click().perform()
            time.sleep(0.3)
            
            # Xóa sạch text cũ nếu có (Ctrl+A -> Backspace)
            try:
                textarea.send_keys(Keys.CONTROL + "a")
                time.sleep(0.2)
                textarea.send_keys(Keys.BACK_SPACE)
                time.sleep(0.2)
            except Exception:
                pass
                
            # Gõ từng ký tự một (Draft.js cần sự kiện phím tuần tự để cập nhật React state)
            for char in text_to_type:
                textarea.send_keys(char)
                time.sleep(0.05)
                
            # Dispatch thêm sự kiện input để React chắc chắn đồng bộ
            driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));"
                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                textarea
            )
        else:
            # Ô input/textarea thông thường
            try:
                textarea.clear()
            except Exception:
                pass
            
            # Gõ trực tiếp bằng send_keys
            textarea.send_keys(text_to_type)
            
            # Dispatch sự kiện input
            driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));"
                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                textarea, text_to_type
            )

        # Mô phỏng gõ thêm dấu cách và xoá đi (trigger trigger vật lý cuối cùng)
        from selenium.webdriver.common.keys import Keys
        textarea.send_keys(" ")
        time.sleep(0.2)
        textarea.send_keys(Keys.BACK_SPACE)
        time.sleep(0.2)
        
        info(f"  Đã nhập thảo luận và kích hoạt sự kiện React: '{text_to_type}'")
    except Exception as e:
        warn(f"Lỗi kích hoạt React Event: {e}. Thử gõ trực tiếp...")
        try:
            textarea.clear()
        except Exception:
            pass
        textarea.send_keys(text_to_type)

    # YÊU CẦU: đợi 3 giây rồi mới ấn reply
    info("  Đợi 3 giây trước khi bấm Reply/Post theo yêu cầu...")
    time.sleep(3)

    # Nút Post / Submit / Reply
    submit_selectors = [
        (By.XPATH, "//button[contains(.,'Post') or contains(.,'post')]"),
        (By.XPATH, "//button[contains(.,'Submit') or contains(.,'submit')]"),
        (By.XPATH, "//button[contains(.,'Reply') or contains(.,'reply')]"),
        (By.XPATH, "//button[span[text()='Post' or text()='Submit' or text()='Reply']]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "button[data-testid='submit-button']"),
    ]

    submit_btn = None
    for by, sel in submit_selectors:
        btn = find_optional(driver, by, sel, timeout=3)
        if btn and btn.is_displayed():
            submit_btn = btn
            info(f"  Tìm thấy nút gửi: '{btn.text}' ({sel})")
            break

    submitted = False
    if submit_btn:
        from selenium.webdriver.common.keys import Keys
        # Nếu nút bị disable, thử click/gõ thêm lần nữa để kích hoạt
        if not submit_btn.is_enabled():
            warn("  Nút gửi bị disable. Thử gõ thêm một ký tự kích hoạt...")
            try:
                textarea.click()
                textarea.send_keys(" ")
                time.sleep(0.2)
                textarea.send_keys(Keys.BACK_SPACE)
                time.sleep(0.5)
            except Exception:
                pass
                
        # Kiểm tra lại xem đã enabled chưa
        if submit_btn.is_enabled():
            safe_click(driver, submit_btn)
            success("  Đã bấm gửi phản hồi thảo luận!")
            submitted = True
            time.sleep(3)
        else:
            warn("  Nút gửi vẫn bị disable. Thử bấm ép bằng Javascript...")
            try:
                driver.execute_script("arguments[0].removeAttribute('disabled');", submit_btn)
                time.sleep(0.2)
                driver.execute_script("arguments[0].click();", submit_btn)
                submitted = True
                success("  Đã force click nút submit!")
                time.sleep(3)
            except Exception as e:
                error(f"  Không thể bấm nút submit: {e}")

    if not submitted:
        warn("Không tìm thấy nút gửi phản hồi hoạt động. Thử nhấn Ctrl+Enter...")
        try:
            from selenium.webdriver.common.keys import Keys
            textarea.send_keys(Keys.CONTROL + Keys.ENTER)
            submitted = True
            time.sleep(3)
        except Exception as e:
            error(f"Không thể gửi phản hồi thảo luận bằng phím nóng: {e}")

    # Kiểm tra tích xanh
    if is_item_completed(driver):
        success("💬 [DISCUSSION] Hoàn thành phần thảo luận!")
        return True

    # Trả về True nếu gửi thành công để bot có cơ hội đi tiếp
    return submitted
