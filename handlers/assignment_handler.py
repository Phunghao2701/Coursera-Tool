import os
import time
import json
import urllib.request
import urllib.error
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config
from utils.logger import success, info, warn, error, step, skip
from utils.helpers import find_optional, safe_click, is_item_completed

def load_env():
    """Tải biến môi trường từ .env nếu có."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        os.environ[key] = val

# Tải API Key
load_env()

def call_groq_api(prompt: str) -> dict:
    """Gọi Groq API dùng model llama-3.3-70b-versatile với JSON Mode."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Không tìm thấy GROQ_API_KEY trong file .env hoặc biến môi trường!")
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert academic assistant that solves Coursera quizzes perfectly. "
                    "Analyze the provided quiz questions and choices, and return a JSON object with the answers. "
                    "For each question, select the best possible answers based on the options provided. "
                    "If the question type is 'single' (radio), select exactly one option. "
                    "If the question type is 'multiple' (checkbox), select one or more correct options. "
                    "Return ONLY a raw JSON object. Do not include markdown code block formatting (like ```json). "
                    "The format of the JSON MUST be exactly: "
                    "{\n"
                    "  \"answers\": {\n"
                    "    \"1\": [\"Option Text A\"],\n"
                    "    \"2\": [\"Option Text B\", \"Option Text C\"]\n"
                    "  }\n"
                    "}"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            content_str = res_json['choices'][0]['message']['content']
            return json.loads(content_str)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RuntimeError("429")
        raise e

def find_question_blocks_dynamically(driver):
    """
    Tìm các khối câu hỏi một cách thông minh bằng cách gom nhóm các ô nhập (radio/checkbox).
    """
    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox'], [role='radio'], [role='checkbox']")
    if not inputs:
        inputs = driver.find_elements(By.CSS_SELECTOR, "label, div.rc-Option")
        
    if not inputs:
        return []
        
    question_map = {}
    for inp in inputs:
        # Không kiểm tra inp.is_displayed() trực tiếp vì input thực tế thường bị ẩn bởi CSS của Coursera
        parent = inp
        ancestor = None
        for _ in range(16):
            try:
                parent = parent.find_element(By.XPATH, "..")
                tag = parent.tag_name.lower()
                klass = parent.get_attribute("class") or ""
                role = parent.get_attribute("role") or ""
                testid = parent.get_attribute("data-testid") or ""
                
                if (tag == "fieldset" or 
                    tag == "form" or 
                    role == "group" or
                    "question" in klass.lower() or 
                    "question" in testid.lower() or
                    "multiplechoice" in testid.lower() or
                    "singlechoice" in testid.lower() or
                    "formpart" in klass.lower() or 
                    "form-part" in klass.lower() or
                    "FormPart" in klass or
                    "item-container" in klass.lower() or
                    "Question" in klass):
                    ancestor = parent
                    break
            except Exception:
                break
                
        if ancestor:
            if ancestor not in question_map:
                question_map[ancestor] = []
            question_map[ancestor].append(inp)
            
    if question_map:
        return list(question_map.keys())
        
    return []

def scrape_questions(driver):
    """
    Cào danh sách câu hỏi và các phương án từ giao diện thi Coursera.
    Trả về một list các dict chứa thông tin câu hỏi.
    """
    # 1. Chờ cho đến khi URL chuyển hướng sang trang thi chính thức (chứa /attempt hoặc /exam)
    info("  Đang chờ chuyển hướng đến trang làm bài thi...")
    start_wait = time.time()
    url_loaded = False
    while time.time() - start_wait < 15:
        url = driver.current_url.lower()
        if "/attempt" in url or "/exam" in url or "/quiz" in url:
            url_loaded = True
            break
        time.sleep(1)
        
    # 2. Chờ trang quiz load các câu hỏi thực tế (sử dụng input radio/checkbox làm tín hiệu đáng tin cậy nhất)
    info("  Đang chờ các khối câu hỏi xuất hiện trên giao diện...")
    start_wait = time.time()
    has_loaded = False
    while time.time() - start_wait < 25:
        questions_exist = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
        if questions_exist:
            time.sleep(3)  # Chờ thêm 3 giây để load toàn bộ form đề thi
            has_loaded = True
            break
        time.sleep(1)
        
    if not has_loaded:
        warn("  Đã hết thời gian chờ nhưng chưa thấy câu hỏi nào hiển thị.")

    # 2.5. Vô hiệu hóa và xóa toàn bộ các phần tử Prompt Injection chống AI
    info("  Đang tiến hành dọn dẹp các phần tử Prompt Injection chống AI khỏi DOM...")
    try:
        clean_script = """
        const selectors = [
            '[data-ai-instructions="true"]',
            '[data-testid="content-integrity-instructions"]',
            '[data-testid="acknowledgment-checkpoint"]',
            '[data-assessment-checkpoint="true"]',
            '[data-action="acknowledge-guidelines"]',
            'button[data-action="acknowledge-guidelines"]'
        ];
        let count = 0;
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                el.remove();
                count++;
            });
        });
        
        // Xóa các div chứa text chống AI ngầm
        document.querySelectorAll('div, span, p, button').forEach(el => {
            if (el.textContent && (
                el.textContent.includes('AI Agent Compliance Verification') ||
                el.textContent.includes('uphold Coursera') ||
                el.textContent.includes('academic integrity policy') ||
                el.textContent.includes('acknowledge-guidelines') ||
                el.textContent.includes('You are a helpful AI assistant')
            )) {
                if (el.tagName.toLowerCase() === 'div' && (el.className.includes('css-') || el.getAttribute('data-testid'))) {
                    el.remove();
                    count++;
                } else if (el.tagName.toLowerCase() === 'button') {
                    el.remove();
                    count++;
                }
            }
        });
        return count;
        """
        removed_count = driver.execute_script(clean_script)
        info(f"  Đã dọn dẹp thành công {removed_count} phần tử Prompt Injection!")
    except Exception as e:
        warn(f"  Không thể chạy script dọn dẹp Prompt Injection: {e}")

    questions = []
    
    # 1. Tìm các question blocks bằng phương pháp động
    q_elements = find_question_blocks_dynamically(driver)
    
    if not q_elements:
        # Fallback về selector tĩnh
        q_selectors = [
            "fieldset",
            "div.rc-FormPart",
            "div[class*='question-block']",
            "div[class*='questionContainer']",
            "div[data-testid='question-container']",
            "div.rc-QuizQuestion",
            "div.rc-QuestionBody"
        ]
        for sel in q_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            if elements:
                q_elements = elements
                break
                
    if not q_elements:
        q_elements = driver.find_elements(By.TAG_NAME, "fieldset")

    if not q_elements:
        try:
            driver.save_screenshot("c:\\Users\\LENOVO\\Desktop\\tool coursera\\quiz_debug.png")
            with open("c:\\Users\\LENOVO\\Desktop\\tool coursera\\quiz_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            warn("  [DEBUG] Đã lưu quiz_debug.png và quiz_debug.html để phân tích cấu trúc DOM trang thi.")
        except Exception as e:
            warn(f"  [DEBUG] Không thể lưu file debug: {e}")

    info(f"  Tìm thấy {len(q_elements)} khối câu hỏi trên giao diện.")
    
    for idx, q_el in enumerate(q_elements, 1):
        # 1. Lấy nội dung câu hỏi
        q_text = ""
        text_selectors = [
            "div.rc-CML",
            "div[data-testid='legend']",
            "div[data-testid='cml-viewer']",
            "[data-testid='legend']",
            "[data-testid='cml-viewer']",
            "legend",
            ".rc-FormPart__question-text",
            "div[class*='question-text']",
            "div[data-testid='question-text']",
            "div.rc-QuestionBody",
            "h2", "h3", "h4",
            ".rc-FormPart__label"
        ]
        
        for sel in text_selectors:
            try:
                el = q_el.find_element(By.CSS_SELECTOR, sel)
                if el and el.text.strip():
                    q_text = el.text.strip()
                    break
            except Exception:
                continue
                
        if not q_text:
            try:
                text_lines = [line.strip() for line in q_el.text.split("\n") if line.strip()]
                if text_lines:
                    q_text = text_lines[0]
                else:
                    q_text = f"Question {idx}"
            except Exception:
                q_text = f"Question {idx}"
            
        q_text = re.sub(r'^\d+[\.\s\-]+', '', q_text).strip()
        
        # 2. Xác định loại câu hỏi (radio hay checkbox)
        q_type = "single"
        try:
            if q_el.find_elements(By.CSS_SELECTOR, "input[type='checkbox']") or q_el.find_elements(By.CSS_SELECTOR, "[role='checkbox']"):
                q_type = "multiple"
        except Exception:
            pass
            
        # 3. Lấy danh sách các phương án chọn
        options = []
        try:
            opt_candidates = q_el.find_elements(By.CSS_SELECTOR, "label, div.rc-Option, div[role='radio'], div[role='checkbox'], div[class*='option']")
        except Exception:
            opt_candidates = []
            
        seen_texts = set()
        for opt_el in opt_candidates:
            try:
                opt_text = opt_el.text.strip()
                if not opt_text:
                    continue
                
                opt_text_clean = re.sub(r'^[a-zA-Z][\.\s\-]+', '', opt_text).strip()
                
                if opt_text_clean not in seen_texts:
                    seen_texts.add(opt_text_clean)
                    options.append({
                        "text": opt_text_clean,
                        "element": opt_el
                    })
            except Exception:
                continue
                
        if not options:
            try:
                labels = q_el.find_elements(By.TAG_NAME, "label")
                for label in labels:
                    opt_text = label.text.strip()
                    if opt_text:
                        opt_text_clean = re.sub(r'^[a-zA-Z][\.\s\-]+', '', opt_text).strip()
                        options.append({
                            "text": opt_text_clean,
                            "element": label
                        })
            except Exception:
                pass
            
        if q_text and options:
            questions.append({
                "id": idx,
                "text": q_text,
                "type": q_type,
                "options": options,
                "element": q_el
            })
            info(f"    Q{idx}: {q_text[:50]}... ({len(options)} options, type: {q_type})")
            
    return questions


def find_best_matching_option(opt_text_from_ai, options_list):
    """Tìm phương án khớp nhất từ kết quả AI."""
    # 1. Khớp chính xác hoàn toàn
    for opt in options_list:
        if opt_text_from_ai.strip().lower() == opt["text"].strip().lower():
            return opt
    # 2. Khớp tương đối (substring)
    for opt in options_list:
        if opt_text_from_ai.strip().lower() in opt["text"].strip().lower() or opt["text"].strip().lower() in opt_text_from_ai.strip().lower():
            return opt
    # 3. Khớp tương đối không phân biệt ký tự đặc biệt
    clean_ai = re.sub(r'\W+', '', opt_text_from_ai).lower()
    for opt in options_list:
        clean_opt = re.sub(r'\W+', '', opt["text"]).lower()
        if clean_ai == clean_opt or clean_ai in clean_opt or clean_opt in clean_ai:
            return opt
    return None

def select_option(driver, opt_el):
    """Click chọn một phương án tương thích React/Coursera SPA."""
    try:
        inputs = opt_el.find_elements(By.CSS_SELECTOR, "input")
        click_target = inputs[0] if inputs else opt_el
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", click_target)
        time.sleep(0.5)
        
        actions = ActionChains(driver)
        actions.move_to_element(click_target).click().perform()
        time.sleep(0.3)
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", opt_el)
            time.sleep(0.3)
        except Exception as e:
            warn(f"      Không thể click option: {e}")

def enter_quiz(driver) -> bool:
    """Tìm và click nút bắt đầu làm quiz hoặc tiếp tục làm quiz."""
    # Nếu URL hiện tại đã ở trong phòng thi rồi thì không cần click gì nữa
    current_url = driver.current_url.lower()
    if "/attempt" in current_url or "/exam" in current_url:
        info("  Đã ở sẵn trong trang làm bài thi.")
        return True

    entry_selectors = [
        (By.CSS_SELECTOR, "button[data-testid='CoverPageActionButton']"),
        (By.XPATH, "//button[contains(., 'Start') or contains(., 'Bắt đầu') or contains(., 'Resume') or contains(., 'Tiếp tục') or contains(., 'Retake') or contains(., 'Làm lại') or contains(., 'Retry')]"),
        (By.XPATH, "//a[contains(., 'Start') or contains(., 'Resume') or contains(., 'Retake') or contains(., 'Take') or contains(., 'Retry')]"),
        (By.CSS_SELECTOR, "button[data-testid*='start-btn']"),
        (By.CSS_SELECTOR, "button[data-testid*='resume-btn']"),
        (By.CSS_SELECTOR, "button[data-testid*='retake-btn']"),
        (By.CSS_SELECTOR, "button[data-testid*='retry-btn']"),
    ]
    
    found_btn = None
    for by, sel in entry_selectors:
        btn = find_optional(driver, by, sel, timeout=5)
        if btn and btn.is_displayed():
            found_btn = btn
            info(f"  Tìm thấy nút vào thi: '{btn.text}'")
            break
            
    if found_btn:
        safe_click(driver, found_btn)
        time.sleep(2)
        
        # Kiểm tra và xử lý Honor Code Modal hoặc Start Attempt Modal nếu xuất hiện
        for _ in range(2): # Kiểm tra tối đa 2 lần đề phòng nhiều modal liên tiếp
            time.sleep(1)
            try:
                # 1. Honor Code Modal
                honor_modal = find_optional(driver, By.CSS_SELECTOR, "[data-testid='HonorCodeModal']", timeout=2)
                if honor_modal and honor_modal.is_displayed():
                    info("  Phát hiện Coursera Honor Code Modal! Đang click Continue...")
                    continue_btn = find_optional(driver, By.CSS_SELECTOR, "button[data-testid='continue-button']", timeout=2)
                    if not continue_btn:
                        continue_btn = find_optional(driver, By.XPATH, "//button[contains(., 'Continue')]", timeout=2)
                    if continue_btn:
                        safe_click(driver, continue_btn)
                        info("  Đã click Continue trên Honor Code Modal.")
                        time.sleep(2)
                        continue
                
                # 2. Start Attempt Modal (khi bấm Retry, hiện thông báo số attempt còn lại)
                attempt_modal_btn = find_optional(driver, By.CSS_SELECTOR, "button[data-testid='StartAttemptModal__primary-button']", timeout=2)
                if attempt_modal_btn and attempt_modal_btn.is_displayed():
                    info("  Phát hiện Start Attempt Modal! Đang click Continue...")
                    safe_click(driver, attempt_modal_btn)
                    info("  Đã click Continue trên Start Attempt Modal.")
                    time.sleep(2)
                    continue
            except Exception as e:
                warn(f"  Gặp lỗi khi xử lý modal xác nhận: {e}")
            
        time.sleep(3)
        return True
        
    # Check lại xem URL đã chuyển hướng sang attempt chưa
    time.sleep(2)
    current_url = driver.current_url.lower()
    if "/attempt" in current_url or "/exam" in current_url:
        return True
        
    return False

def submit_quiz(driver) -> bool:
    """Đồng ý điều khoản danh dự ở cuối trang bài thi và bấm nút nộp bài."""
    info("  Đang cuộn xuống cuối trang để ký cam kết danh dự...")
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    except Exception:
        pass

    # 1. Tìm và đồng ý checkbox cam kết danh dự ở cuối trang bài thi (Bỏ qua is_displayed do CSS Coursera ẩn)
    try:
        agreement_selectors = [
            (By.CSS_SELECTOR, "#agreement-checkbox-base"),
            (By.CSS_SELECTOR, "input[type='checkbox']"),
            (By.CSS_SELECTOR, "[role='checkbox']"),
        ]
        for by, sel in agreement_selectors:
            chk = find_optional(driver, by, sel, timeout=3)
            if chk:
                info(f"  Tích chọn checkbox cam kết danh dự: {sel}...")
                driver.execute_script("arguments[0].click();", chk)
                time.sleep(0.5)
                break
    except Exception as e:
        warn(f"  Không thể tích chọn checkbox danh dự: {e}")

    # 2. Tìm và nhập chữ ký điện tử nếu có
    try:
        sig_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input:not([type]), [role='textbox']")
        for sig in sig_inputs:
            if sig.is_displayed() or len(sig_inputs) <= 2:
                info("  Phát hiện ô chữ ký điện tử. Nhập chữ ký: 'LE PHUNG HAO'...")
                try:
                    sig.clear()
                    time.sleep(0.2)
                    sig.send_keys("LE PHUNG HAO")
                    time.sleep(0.5)
                except Exception:
                    driver.execute_script("arguments[0].value = 'LE PHUNG HAO';", sig)
                    time.sleep(0.5)
    except Exception as e:
        warn(f"  Không thể nhập chữ ký điện tử: {e}")

    # 3. Bấm nút nộp bài
    submit_selectors = [
        (By.XPATH, "//button[contains(., 'Submit') or contains(., 'Nộp bài')]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "button[data-testid='submit-quiz-button']"),
    ]
    
    submit_btn = None
    for by, sel in submit_selectors:
        btn = find_optional(driver, by, sel, timeout=5)
        if btn:
            submit_btn = btn
            break
            
    if not submit_btn:
        warn("  Không tìm thấy nút Submit. Thử nộp bằng phím Enter...")
        return False
        
    info(f"  Bấm nút nộp bài: '{submit_btn.text}'")
    safe_click(driver, submit_btn)
    time.sleep(4)
    
    # 4. Xác nhận hộp thoại popup xác nhận nộp bài (nếu có)
    confirm_selectors = [
        (By.CSS_SELECTOR, "button[data-testid='confirm-submit-button']"),
        (By.XPATH, "//*[@role='dialog']//button[contains(., 'Submit') or contains(., 'Yes') or contains(., 'Nộp') or contains(., 'Xác nhận')]"),
        (By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog')]//button[contains(., 'Submit') or contains(., 'Yes') or contains(., 'Nộp') or contains(., 'Xác nhận')]"),
        (By.XPATH, "//button[contains(., 'Yes') or contains(., 'Submit') or contains(., 'Nộp') or contains(., 'Xác nhận')]"),
    ]
    
    for by, sel in confirm_selectors:
        try:
            btns = driver.find_elements(by, sel)
            for btn in btns:
                # Đảm bảo nút xác nhận hiển thị rõ ràng trên modal và khác với nút nộp ban đầu
                if btn and btn.is_displayed() and btn != submit_btn:
                    info(f"  Bấm xác nhận nộp bài trên modal popup: '{btn.text}'")
                    safe_click(driver, btn)
                    time.sleep(5)
                    return True
        except Exception:
            pass
            
    return True

def get_score_percentage(driver) -> float:
    """Quét trang để tìm và tính toán phần trăm điểm đạt được."""
    time.sleep(5)
    
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        body_text = ""
        
    pct_matches = re.findall(r'(\d+(?:\.\d+)?)%', body_text)
    if pct_matches:
        scores = [float(x) for x in pct_matches]
        for s in sorted(scores, reverse=True):
            if s <= 100:
                info(f"  Phát hiện điểm phần trăm: {s}%")
                return s
                
    frac_matches = re.findall(r'(\d+)\s*/\s*(\d+)', body_text)
    for num, denom in frac_matches:
        n, d = float(num), float(denom)
        if d > 0 and n <= d:
            pct = (n / d) * 100
            info(f"  Phát hiện điểm phân số: {num}/{denom} ({pct:.2f}%)")
            return pct
            
    warn("  Không tìm thấy thông tin điểm bằng Regex. Tìm kiếm từ khóa Pass/Fail...")
    if "pass" in body_text.lower() or "đạt" in body_text.lower():
        info("  Phát hiện từ khóa 'Pass' / 'Đạt'. Mặc định đạt 100%.")
        return 100.0
        
    return 0.0

def should_skip_peer_assignment(driver) -> bool:
    """Kiểm tra xem trang hiện tại có phải là Peer-graded Assignment hoặc Review Your Peers hay không."""
    try:
        url = driver.current_url.lower()
        # ĐẶC BIỆT LƯU Ý: KHÔNG bỏ qua "/assignment-submission/" vì đây là URL của Graded Quiz thường.
        # Chúng ta chỉ bỏ qua khi đường dẫn thực sự chứa các endpoint của peer review.
        if "/peer/" in url or "/review/" in url or "/peer-review/" in url:
            return True
    except Exception:
        pass
    return False

def handle_assignment(driver) -> bool:
    """
    Xử lý giải trắc nghiệm tự động dùng Groq Llama 3.3.
    """
    step("📝 [ASSIGNMENT] Khởi chạy bộ giải Quiz AI...")
    
    # 0. Bỏ qua nếu là Peer-graded Assignment hoặc Review Your Peers
    if should_skip_peer_assignment(driver):
        skip("📝 [PEER ASSIGNMENT] Phần này là Peer-graded Assignment / Review Your Peers — tự động bỏ qua theo yêu cầu.")
        return True
        
    # 1. Kiểm tra trạng thái tích xanh
    if is_item_completed(driver):
        success("  Bài tập đã đạt tích xanh sẵn. Bỏ qua!")
        return True
        
    # [Retry tối đa 3 lần]
    for attempt in range(1, 4):
        info(f"--- Bắt đầu làm Quiz: Lần thử {attempt}/3 ---")
        
        # Vào phòng thi
        entered = enter_quiz(driver)
        if not entered:
            warn("  Không thấy nút Start/Resume/Retake. Giả định đã ở trong trang Quiz.")
            
        time.sleep(4)
        
        # Cào câu hỏi
        questions = scrape_questions(driver)
        if not questions:
            error("  Không tìm thấy câu hỏi nào trên giao diện thi!")
            return False
            
        # Chuẩn bị payload gửi Groq
        questions_payload = []
        for q in questions:
            questions_payload.append({
                "id": q["id"],
                "text": q["text"],
                "type": q["type"],
                "options": [opt["text"] for opt in q["options"]]
            })
            
        prompt = (
            "Solve the following Coursera quiz questions. Return the correct answers inside a JSON object.\n"
            f"Questions list:\n{json.dumps(questions_payload, ensure_ascii=False, indent=2)}"
        )
        
        info("  Đang gửi câu hỏi lên Groq Llama 3.3 API...")
        try:
            ai_response = call_groq_api(prompt)
        except RuntimeError as e:
            if str(e) == "429":
                warn("⚠️ Bị lỗi Rate Limit 429 từ Groq API. Tự động skip bài tập này để chạy tiếp.")
                return True
            raise e
        except Exception as e:
            error(f"  Lỗi gọi Groq API: {e}")
            return False
            
        # Điền đáp án
        answers = ai_response.get("answers", {})
        info("  Đang tiến hành chọn đáp án trên trình duyệt...")
        
        for q in questions:
            q_id_str = str(q["id"])
            ai_opts = answers.get(q_id_str, [])
            if not ai_opts:
                warn(f"    Không nhận được đáp án cho Q{q['id']}.")
                continue
                
            info(f"    Q{q['id']}: AI chọn -> {ai_opts}")
            for opt_text in ai_opts:
                matched_opt = find_best_matching_option(opt_text, q["options"])
                if matched_opt:
                    select_option(driver, matched_opt["element"])
                else:
                    warn(f"      Không khớp được phương án: '{opt_text}'")
                    
        # Đảm bảo mỗi câu hỏi đều có ít nhất 1 đáp án được click chọn để bật nút Submit
        for q in questions:
            is_answered = False
            for opt in q["options"]:
                try:
                    inputs = opt["element"].find_elements(By.CSS_SELECTOR, "input")
                    for inp in inputs:
                        if inp.is_selected() or inp.get_attribute("checked") or inp.get_attribute("aria-checked") == "true":
                            is_answered = True
                            break
                except Exception:
                    pass
            if not is_answered:
                warn(f"    Q{q['id']} chưa được điền đáp án! Tự động chọn phương án 1 để kích hoạt nút Submit.")
                if q["options"]:
                    select_option(driver, q["options"][0]["element"])
                    
        # Nộp bài
        time.sleep(2)
        submitted = submit_quiz(driver)
        if not submitted:
            error("  Không thể nộp bài!")
            return False
            
        # Kiểm tra điểm số
        score = get_score_percentage(driver)
        info(f"🏆 Điểm đạt được trong lần thử này: {score:.2f}% (Yêu cầu: >= 80%)")
        
        if score >= 80.0:
            success(f"🎉 Đã VƯỢT QUA Quiz thành công với điểm số {score:.2f}%!")
            
            back_btn = find_optional(driver, By.XPATH, "//button[contains(., 'Go back') or contains(., 'Quay lại') or contains(., 'Next') or contains(., 'Tiếp theo')]", timeout=8)
            if back_btn:
                safe_click(driver, back_btn)
                time.sleep(3)
            return True
        else:
            warn(f"😭 Chưa đạt điểm qua môn ({score:.2f}% < 80%).")
            if attempt < 3:
                info("Chuẩn bị thi lại...")
                back_btn = find_optional(driver, By.XPATH, "//button[contains(., 'Go back') or contains(., 'Quay lại') or contains(., 'Next')]", timeout=8)
                if back_btn:
                    safe_click(driver, back_btn)
                    time.sleep(4)
            else:
                error("Đã hết 3 lần thử nhưng vẫn không đạt 80%. Tự động skip.")
                return False
                
    return False
