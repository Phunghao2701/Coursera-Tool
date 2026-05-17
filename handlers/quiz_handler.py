# -*- coding: utf-8 -*-
"""
QUIZ HANDLER
============
Tu dong xu ly Graded Quiz tren Coursera:
  1. Navigate den trang /attempt (tu dong click Start/Resume neu can)
  2. Scrape cau hoi va options tu DOM (multiple-choice & checkbox)
  3. Gui len Groq API (llama-3.3-70b-versatile)
  4. Click dap an dung, tick honor code, Submit
  5. Kiem tra passing score - retry toi da QUIZ_MAX_RETRY lan
  6. Neu gap 429 (rate limit) -> log warning -> return True (skip)
"""

import os, time, json, re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.logger import success, info, warn, error, step, skip
from utils.helpers import safe_click

# ---- Load .env ----------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL     = "llama-3.3-70b-versatile"
GROQ_ENDPOINT  = "https://api.groq.com/openai/v1/chat/completions"
QUIZ_MAX_RETRY = 3

# =========================================================================
#  POPUP DISMISSER
# =========================================================================

def _dismiss_honor_code_popup(driver):
    """
    Tu dong kiem tra va tat modal 'Coursera Honor Code' neu no xuat hien che khuat man hinh.
    """
    try:
        closed = driver.execute_script("""
            var dialogs = document.querySelectorAll("div[role='dialog'], [class*='modal'], [class*='Modal']");
            for (var i = 0; i < dialogs.length; i++) {
                var txt = (dialogs[i].innerText || "");
                if (txt.includes("Honor Code") || txt.includes("honor code") || txt.includes("integrity of your work") || txt.includes("dedicated to protecting")) {
                    // Tim nut 'Continue'
                    var buttons = dialogs[i].querySelectorAll("button");
                    for (var j = 0; j < buttons.length; j++) {
                        var btnTxt = (buttons[j].innerText || "").trim().toLowerCase();
                        if (btnTxt === "continue" || btnTxt.includes("continue") || btnTxt === "ok" || btnTxt.includes("accept")) {
                            buttons[j].click();
                            return true;
                        }
                    }
                    // Fallback: tim nut close 'X'
                    var closeBtn = dialogs[i].querySelector("button[aria-label*='close' i], button[aria-label*='Close' i], [class*='close' i]");
                    if (closeBtn) {
                        closeBtn.click();
                        return true;
                    }
                }
            }
            return false;
        """)
        if closed:
            from utils.logger import success
            success("  [Quiz] Da tu dong dong popup 'Coursera Honor Code' che khuat man hinh!")
            time.sleep(2)
    except Exception:
        pass


# =========================================================================
#  NAVIGATE TO ATTEMPT PAGE
# =========================================================================

def _ensure_attempt_page(driver) -> bool:
    """
    Dam bao dang o trang /attempt.
    Click Resume (CoverPageActionButton) hoac Start/Retry neu can.
    """
    _dismiss_honor_code_popup(driver)
    if "/attempt" in driver.current_url:
        _dismiss_honor_code_popup(driver)
        info("  [Quiz] Da o trang /attempt.")
        return True

    # 1. Kiem tra xem co the o tren dialog confirm modal san hay khong
    _confirm_start_attempt_modal(driver)

    # 2. Tim kiem va click nut vao attempt
    btn_selectors = [
        (By.CSS_SELECTOR, "button[data-testid='CoverPageActionButton']"),
        (By.CSS_SELECTOR, "button[data-testid='start-attempt-button']"),
        (By.CSS_SELECTOR, "button[data-testid='resume-attempt-button']"),
        (By.XPATH, "//button[contains(text(),'Resume') or contains(text(),'Start') or contains(text(),'Continue') or contains(text(),'Retry') or contains(text(),'Retake')]"),
        (By.XPATH, "//a[contains(@href,'attempt')]"),
    ]
    
    clicked = False
    for by, sel in btn_selectors:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, sel)))
            lbl = btn.text.strip() or btn.get_attribute("href") or "?"
            info(f"  [Quiz] Click '{lbl[:30]}'")
            safe_click(driver, btn)
            clicked = True
            break
        except TimeoutException:
            pass

    if clicked:
        time.sleep(2)
        # Check xem co modal "Start new attempt?" hien ra khong
        _confirm_start_attempt_modal(driver)

    # Doi /attempt URL xuat hien
    try:
        WebDriverWait(driver, 8).until(
            lambda d: "/attempt" in d.current_url
        )
        _dismiss_honor_code_popup(driver)
        return True
    except TimeoutException:
        pass

    # Fallback direct navigation
    cur = driver.current_url
    if "/assignment-submission/" in cur and "/attempt" not in cur:
        attempt_url = cur.split("/attempt")[0].rstrip("/") + "/attempt"
        info(f"  [Quiz] Navigate truc tiep: {attempt_url}")
        driver.get(attempt_url)
        time.sleep(6)
        _dismiss_honor_code_popup(driver)
        if "/attempt" in driver.current_url:
            return True

    return "/attempt" in driver.current_url


def _confirm_start_attempt_modal(driver) -> bool:
    """Phuong thuc xac nhan popup Start/Resume attempt moi neu co bang JS/WebDriver."""
    # Quet nhanh cac selector xac nhan modal
    for confirm_sel in [
        (By.CSS_SELECTOR, "button[data-testid='ModalActionButton']"),
        (By.CSS_SELECTOR, "button[data-testid='dialog-confirm-button']"),
        (By.XPATH, "//button[contains(text(),'Continue') or contains(text(),'Start new') or contains(text(),'Confirm') or contains(text(),'Start Attempt')]"),
    ]:
        try:
            confirm = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(confirm_sel)
            )
            info(f"  [Quiz] Confirm modal: click '{confirm.text.strip()[:30]}'")
            safe_click(driver, confirm)
            time.sleep(3)
            return True
        except TimeoutException:
            pass
    return False


# =========================================================================
#  DOM SCRAPERS
# =========================================================================

def _scrape_questions(driver) -> list[dict]:
    """
    Scrape cau hoi + options tu trang /attempt.

    Coursera structure (da confirm qua live DOM):
    - KHONG dung fieldset
    - #TUNNELVISIONWRAPPER_CONTENT_ID chua toan bo quiz
    - Moi cau hoi co: text heading + N input[type='radio'] moi la 1 option
    - Label cua moi option: class='cds-checkboxAndRadio-label'
    - Honor code: input#agreement-checkbox-base (bo qua)

    Strategy: group tat ca radio inputs theo vi tri
    (10 cau x 4 opts = 40 radios, tu dong chia theo name attribute hoac theo label proximity)
    """
    questions = []

    # Doi DOM render xong - retry toi da 6 lan x 5s = 30s
    for wait_round in range(6):
        _dismiss_honor_code_popup(driver)
        n_radios = driver.execute_script(
            "return document.querySelectorAll('input[type=radio], input[type=checkbox]').length"
        )
        if n_radios > 0:
            break
        info(f"  [Quiz] Cho DOM render... ({wait_round+1}/6)")
        time.sleep(5)
    else:
        warn("  [Quiz] Timeout doi inputs xuat hien (30s).")
        return []

    # Scroll xuong va len de lazy-load het toan bo cau hoi tren trang attempt
    info("  [Quiz] Scrolling to lazy-load all questions and options...")
    try:
        for _ in range(8):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.4)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1.5)
    except Exception:
        pass

    n_inputs = driver.execute_script(
        "return document.querySelectorAll('input[type=radio], input[type=checkbox]').length"
    )
    info(f"  [Quiz] Phat hien {n_inputs} inputs.")

    # Lay tat ca labels (moi label bao 1 radio)
    all_labels = driver.find_elements(
        By.CSS_SELECTOR, "label.cds-checkboxAndRadio-label"
    )
    # Bo qua honor code
    valid_labels = []
    valid_inputs = []
    for lbl in all_labels:
        try:
            inp = lbl.find_element(By.CSS_SELECTOR, "input")
            if inp.get_attribute("id") == "agreement-checkbox-base":
                continue
            valid_labels.append(lbl)
            valid_inputs.append(inp)
        except NoSuchElementException:
            pass

    if not valid_inputs:
        warn("  [Quiz] Khong tim duoc input trong labels.")
        return []

    info(f"  [Quiz] {len(valid_inputs)} valid options (sau khi bo honor code).")

    # Group inputs theo 'name' attribute (moi question co cung name)
    groups = {}
    for lbl, inp in zip(valid_labels, valid_inputs):
        name = inp.get_attribute("name") or inp.get_attribute("id") or "unknown"
        if name not in groups:
            groups[name] = {"labels": [], "inputs": []}
        groups[name]["labels"].append(lbl)
        groups[name]["inputs"].append(inp)

    info(f"  [Quiz] Chia thanh {len(groups)} question groups.")

    # Lay question text cho moi group
    # Strategy: tim common ancestor cua tat ca inputs trong group,
    # cat phan text truoc option dau tien de lay question text
    for i, (name, grp) in enumerate(groups.items()):
        inputs_in_group = grp["inputs"]
        first_inp       = inputs_in_group[0]
        last_inp        = inputs_in_group[-1]
        opt_texts       = [lbl.text.strip() for lbl in grp["labels"]]
        q_text          = ""

        try:
            q_text = driver.execute_script("""
                var firstInp = arguments[0];
                
                // 1. Walk up parents and look at previous siblings first (highly precise for current Coursera layout)
                var el = firstInp;
                while (el && el.tagName !== 'BODY') {
                    var sib = el.previousElementSibling;
                    while (sib) {
                        var text = (sib.innerText || '').trim();
                        if (text.length > 10 && !text.includes('Report') && !text.includes('Flag') && !text.includes('agreement') && !text.includes('understand')) {
                            // Clear point values like '1 / 1 point', '1 point'
                            text = text.replace(/\\d+\\s*\\/\\s*\\d+\\s*points?/i, '');
                            text = text.replace(/\\d+\\s*points?/i, '');
                            return text.trim();
                        }
                        var nested = sib.querySelector("legend, [class*='prompt'], [class*='Question'], h1, h2, h3, h4, h5");
                        if (nested && nested.innerText.trim().length > 10 && !nested.innerText.includes('agreement') && !nested.innerText.includes('understand')) {
                            var nestedText = nested.innerText.trim();
                            nestedText = nestedText.replace(/\\d+\\s*\\/\\s*\\d+\\s*points?/i, '');
                            nestedText = nestedText.replace(/\\d+\\s*points?/i, '');
                            return nestedText.trim();
                        }
                        sib = sib.previousElementSibling;
                    }
                    el = el.parentElement;
                }
                
                // 2. Fallback to highly localized closest Question container query (so we never scan outside this question card)
                var qContainer = firstInp.closest("[class*='Question'], [class*='rc-FormPartsQuestion'], fieldset");
                if (qContainer) {
                    var promptEl = qContainer.querySelector("[class*='prompt'], legend, h2, h3, h4, [class*='QuestionTitle']");
                    if (promptEl && promptEl.innerText.trim().length > 8 && !promptEl.innerText.includes('agreement') && !promptEl.innerText.includes('understand')) {
                        var pText = promptEl.innerText.trim();
                        pText = pText.replace(/\\d+\\s*\\/\\s*\\d+\\s*points?/i, '');
                        pText = pText.replace(/\\d+\\s*points?/i, '');
                        return pText.trim();
                    }
                }
                
                return 'Cau hoi';
            """, first_inp)
        except Exception as ex:
            warn(f"  [Quiz] JS error lay q_text Q{i+1}: {ex}")

        if not q_text or len(q_text.strip()) < 5:
            q_text = f"Cau hoi {i+1} (khong doc duoc de)"

        first_type = inputs_in_group[0].get_attribute("type") or "radio"
        q_type = "checkbox" if first_type == "checkbox" else "radio"

        questions.append({
            "index":    i,
            "q":        q_text.strip()[:400],
            "type":     q_type,
            "options":  opt_texts,
            "elements": inputs_in_group,
        })
        info(f"  [Q{i+1}] {q_text.strip()[:70]} ({q_type}, {len(opt_texts)} opts)")

    return questions


# =========================================================================
#  GROQ API
# =========================================================================

def _ask_groq(questions: list[dict]):
    """
    Gui danh sach cau hoi len Groq.
    Tra ve dict {question_index: [option_indices]} hoac "RATE_LIMITED" hoac None.
    """
    if not GROQ_API_KEY:
        error("[Quiz] GROQ_API_KEY chua duoc cau hinh trong .env!")
        return None

    n = len(questions)
    lines = [
        "You are an expert at answering multiple-choice and multi-select exam questions.\n"
        f"There are exactly {n} questions below (Q0 to Q{n-1}). "
        f"You MUST provide answers for ALL {n} questions — do not skip any.\n"
        "Answer ONLY with a JSON object — no explanation, no extra text.\n"
    ]
    for i, q in enumerate(questions):
        lines.append(f"Q{i} ({q['type']}): {q['q']}")
        for j, opt in enumerate(q["options"]):
            lines.append(f"  {chr(65+j)}. {opt}")
        lines.append("")

    lines.append(
        f'JSON format (MUST include all keys 0 to {n-1}): {{"0": [0], "1": [1, 2], ..., "{n-1}": [0]}} '
        "(key = 0-based question index, value = list of 0-based correct option indices). "
        "For radio (single answer) pick exactly 1 index. For checkbox pick all correct indices. "
        "Return ONLY the JSON object, nothing else."
    )
    prompt = "\n".join(lines)

    import requests
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens":  512,
    }

    try:
        resp = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=30)
        if resp.status_code == 429:
            warn("[Quiz] Groq rate limit (429) - bo qua quiz nay.")
            return "RATE_LIMITED"
        if resp.status_code != 200:
            error(f"[Quiz] Groq API loi {resp.status_code}: {resp.text[:200]}")
            return None

        content = resp.json()["choices"][0]["message"]["content"].strip()
        info(f"  [Groq] Raw response: {content[:150]}")

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            raw = json.loads(match.group())
            return {int(k): [int(x) for x in v] for k, v in raw.items()}
        error(f"[Quiz] Khong parse duoc JSON: {content[:200]}")
        return None

    except Exception as ex:
        error(f"[Quiz] Loi goi Groq: {ex}")
        return None


# =========================================================================
#  CLICK ANSWERS
# =========================================================================

def _click_answers(driver, questions: list[dict], answers: dict):
    """Click cac option dung theo answers dict."""
    _dismiss_honor_code_popup(driver)
    for q_idx, q in enumerate(questions):
        opt_indices = answers.get(q_idx)
        
        # FALLBACK: Neu cau hoi khong co trong answers hoac danh sach rong,
        # chon mac dinh option dau tien (index 0) de dam bao luon co cau tra loi!
        if not opt_indices:
            warn(f"  [Quiz] Cau hoi {q_idx+1} khong co cau tra loi tu Groq. Dung fallback chon option dau tien (index 0).")
            opt_indices = [0]

        for opt_idx in opt_indices:
            if opt_idx >= len(q["elements"]):
                warn(f"  [Quiz] Opt idx {opt_idx} out of range (Q{q_idx+1} co {len(q['elements'])} opts). Dung index 0.")
                opt_idx = 0
            inp = q["elements"][opt_idx]
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
                time.sleep(0.3)
                
                # Click vao label hoac input
                clicked = False
                try:
                    label = driver.execute_script(
                        "return arguments[0].closest('label');", inp
                    )
                    if label:
                        safe_click(driver, label)
                        clicked = True
                except Exception:
                    pass
                
                if not clicked:
                    safe_click(driver, inp)

                time.sleep(0.4)
                
                # VERIFICATION: Kiem tra xem element da thuc su duoc tick chua
                is_checked = driver.execute_script("return arguments[0].checked;", inp)
                if not is_checked:
                    warn(f"  [Quiz] Option {opt_idx} cua Q{q_idx+1} chua duoc tick. Dung JS force click!")
                    driver.execute_script("arguments[0].click();", inp)
                    time.sleep(0.3)

                opt_txt = q["options"][opt_idx] if opt_idx < len(q["options"]) else "?"
                info(f"  [Quiz] Click Q{q_idx+1} opt[{opt_idx}]: {opt_txt[:50]}")
                time.sleep(0.5)
            except Exception as ex:
                warn(f"  [Quiz] Khong click duoc Q{q_idx+1} opt {opt_idx}: {ex}")


# =========================================================================
#  HONOR CODE + SUBMIT
# =========================================================================

def _tick_honor_code(driver):
    """Tick honor code checkbox neu co."""
    try:
        hc = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "agreement-checkbox-base"))
        )
        if not hc.is_selected():
            safe_click(driver, hc)
            info("  [Quiz] Da tick honor code.")
            time.sleep(1)
    except TimeoutException:
        pass  # Khong co honor code thi thoi


def _submit(driver) -> bool:
    """Tick honor code roi bam Submit (bao gom ca buoc confirm modal neu co)."""
    _dismiss_honor_code_popup(driver)
    _tick_honor_code(driver)

    # 1. Click nut Submit chinh
    submit_selectors = [
        (By.CSS_SELECTOR, "button[data-testid='submit-button']"),
        (By.XPATH, "//button[contains(text(),'Submit')]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
    ]
    clicked_main = False
    for by, sel in submit_selectors:
        try:
            btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((by, sel)))
            safe_click(driver, btn)
            info(f"  [Quiz] Da click nut Submit chinh ({sel}).")
            clicked_main = True
            break
        except TimeoutException:
            pass

    if not clicked_main:
        warn("  [Quiz] Khong tim thay nut Submit chinh.")
        return False

    time.sleep(2)

    # 2. Xac nhan modal phu neu co ("Are you sure you want to submit?" hoac "Ready to submit?")
    info("  [Quiz] Dang cho va click Modal confirm...")
    for confirm_attempt in range(6):
        clicked_modal = driver.execute_script("""
            // 1. Tim bang data-testid quen thuoc cua Coursera
            var btn = document.querySelector("button[data-testid='ModalActionButton']");
            if (!btn) {
                // 2. Scan tat ca cac nut trong dialog hoac modal co chu 'Submit' hoac 'Confirm'
                var els = document.querySelectorAll("div[role='dialog'] button, div[role='dialog'] [role='button'], div[role='dialog'] a, [class*='modal'] button, [class*='modal'] [role='button'], button, [role='button']");
                // Tim kiem match chinh xac truoc
                for (var i = 0; i < els.length; i++) {
                    var txt = (els[i].innerText || els[i].textContent || '').trim().toLowerCase();
                    if (txt === "submit" || txt === "confirm") {
                        btn = els[i];
                        break;
                    }
                }
                // Neu khong co match chinh xac, tim match chua tu
                if (!btn) {
                    for (var i = 0; i < els.length; i++) {
                        var txt = (els[i].innerText || els[i].textContent || '').trim().toLowerCase();
                        if (txt.includes("submit") || txt.includes("confirm")) {
                            btn = els[i];
                            break;
                        }
                    }
                }
            }
            if (btn) {
                btn.scrollIntoView({block: 'center'});
                btn.click();
                return true;
            }
            return false;
        """)
        if clicked_modal:
            info("  [Quiz] Da click xac nhan Submit tren Modal bang JS!")
            time.sleep(5)
            return True
        time.sleep(1)

    info("  [Quiz] Khong thay hoac khong click duoc Modal confirm, tiep tuc.")
    return True


# =========================================================================
#  CHECK SCORE
# =========================================================================

def _check_passed(driver) -> bool:
    """
    Kiem tra da pass chua sau khi submit.
    Lay diem tu DOM (JavaScript) - chinh xac hon page_source.
    Tra ve True neu score >= 80.
    """
    # Doi va retry vi page co the load cham truoc khi cap nhat diem
    for attempt in range(6):
        info(f"  [Quiz] Dang check diem trong DOM (lan {attempt+1}/6)...")
        try:
            score_js = driver.execute_script("""
                var els = document.querySelectorAll(
                    '[data-testid*=grade], [data-testid*=score], [class*=grade], [class*=score], h2, h3, h4, strong, p, span, div'
                );
                for (var i = 0; i < els.length; i++) {
                    var txt = (els[i].innerText || '').trim();
                    var lower = txt.toLowerCase();
                    
                    // Loc cac cau chu thong tin/huong dan de tranh nhan nham muc tieu 80% can pass
                    if (lower.includes("pass") || lower.includes("need") || lower.includes("least") || 
                        lower.includes("highest") || lower.includes("keep") || lower.includes("receive") || 
                        lower.includes("higher") || lower.includes("weight")) {
                        continue;
                    }
                    
                    // Tim dang '80%', '40%', 'Grade: 80%'
                    var m = txt.match(/(\\d+)\\s*%/);
                    if (m) return parseInt(m[1]);
                    
                    // Tim dang '4 / 10', '8/10'
                    var m2 = txt.match(/(\\d+)\\s*\\/\\s*(\\d+)/);
                    if (m2 && parseInt(m2[2]) > 0) {
                        return Math.round(parseInt(m2[1]) / parseInt(m2[2]) * 100);
                    }
                }
                return -1;
            """)
            if score_js is not None and score_js >= 0:
                if score_js >= 80:
                    success(f"  [Quiz] Score: {score_js}% — PASSED!")
                    return True
                else:
                    warn(f"  [Quiz] Score: {score_js}% — FAILED (can < 80%).")
                    return False
        except Exception as ex:
            warn(f"  [Quiz] JS score check error: {ex}")
        time.sleep(5)


    # 2. Fallback: text signals
    try:
        page = driver.execute_script("return document.body.innerText || '';").lower()
    except Exception:
        page = driver.page_source.lower()

    failed_signals = [
        "you did not pass", "didn't pass", "not passed",
        "try again", "retake quiz", "did not meet", "below passing",
    ]
    passed_signals = [
        "congratulations", "you passed", "you've passed",
        "you have passed", "great job",
    ]

    for sig in failed_signals:
        if sig in page:
            warn(f"  [Quiz] Failed signal: '{sig}'")
            return False

    for sig in passed_signals:
        if sig in page:
            info(f"  [Quiz] Passed signal: '{sig}'")
            return True

    warn("  [Quiz] Khong xac dinh duoc ket qua - gia su failed (an toan).")
    return False  # An toan hon: neu khong biet thi coi la failed -> retry


def _reset_for_retry(driver):
    """Click Retake / Reload de thu lai."""
    reset_selectors = [
        (By.XPATH, "//button[contains(text(),'Retake') or contains(text(),'Try Again')]"),
        (By.CSS_SELECTOR, "button[data-testid='retake-button']"),
    ]
    for by, sel in reset_selectors:
        try:
            btn = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((by, sel)))
            safe_click(driver, btn)
            time.sleep(4)
            return
        except TimeoutException:
            pass
    driver.refresh()
    time.sleep(5)


def _is_already_passed(driver) -> bool:
    """Kiem tra xem landing page da co diem dat (>= 80%) hay chua."""
    try:
        score = driver.execute_script("""
            var els = document.querySelectorAll(
                '[data-testid*=grade], [data-testid*=score], [class*=grade], [class*=score], h2, h3, h4, strong, p, span, div'
            );
            for (var i = 0; i < els.length; i++) {
                var txt = (els[i].innerText || '').trim();
                var lower = txt.toLowerCase();
                
                // Loc cac cau chu thong tin/huong dan de tranh nhan nham muc tieu 80% can pass
                if (lower.includes("pass") || lower.includes("need") || lower.includes("least") || 
                    lower.includes("highest") || lower.includes("keep") || lower.includes("receive") || 
                    lower.includes("higher") || lower.includes("weight")) {
                    continue;
                }
                
                // Tim dang '80%', '100%', 'Grade: 80%'
                var m = txt.match(/(\\d+)\\s*%/);
                if (m) {
                    var pct = parseInt(m[1]);
                    if (pct >= 0 && pct <= 100) return pct;
                }
                // Tim dang '8/10', '9/10'
                var m2 = txt.match(/(\\d+)\\s*\\/\\s*(\\d+)/);
                if (m2 && parseInt(m2[2]) > 0) {
                    var pct = Math.round(parseInt(m2[1]) / parseInt(m2[2]) * 100);
                    if (pct >= 0 && pct <= 100) return pct;
                }
            }
            return -1;
        """)
        if score is not None and score >= 0:
            if score >= 80:
                success(f"  [Quiz] Phat hien diem da dat tren trang landing: {score}%! Khong can lam lai.")
                return True
            else:
                info(f"  [Quiz] Diem hien tai tren trang landing: {score}% (chua dat >= 80%). Tien hanh lam Quiz...")
    except Exception as ex:
        warn(f"  [Quiz] Loi kiem tra diem cu: {ex}")
    return False


# =========================================================================
#  MAIN HANDLER
# =========================================================================

def handle_quiz(driver) -> bool:
    """
    Xu ly Graded Quiz. Tra ve True de bot tiep tuc.
    """
    step("📝 [QUIZ] Bat dau xu ly Quiz...")
    time.sleep(3)

    # 0. Uu tien check xem da dat (>= 80%) hay chua, neu dat roi thi bo qua (chuyen sang next item)
    if _is_already_passed(driver):
        success("✅ [QUIZ] Quiz nay da dat >= 80% tu truoc. Bo qua va sang bai tiep theo!")
        return True

    for attempt in range(1, QUIZ_MAX_RETRY + 1):
        info(f"\n  [Quiz] === Lan thu {attempt}/{QUIZ_MAX_RETRY} ===")

        # Vao trang attempt neu chua vao o moi attempt loop
        if not _ensure_attempt_page(driver):
            warn(f"  [Quiz] Lan {attempt}: Khong vao duoc trang attempt.")
            if attempt < QUIZ_MAX_RETRY:
                time.sleep(5)
                continue
            skip("📝 [QUIZ] Skip (khong vao duoc attempt page).")
            return True

        # 1. Scrape
        questions = _scrape_questions(driver)
        if not questions:
            warn("  [Quiz] Khong scrape duoc cau hoi.")
            if attempt < QUIZ_MAX_RETRY:
                time.sleep(5)
                continue
            skip("📝 [QUIZ] Skip (khong doc duoc cau hoi).")
            return True

        info(f"  [Quiz] Scrape duoc {len(questions)} cau hoi.")

        # 2. Hoi Groq
        answers = _ask_groq(questions)
        if answers == "RATE_LIMITED":
            skip("📝 [QUIZ] Skip do Groq 429 rate limit.")
            return True
        if not answers:
            warn("  [Quiz] Groq khong tra ve dap an.")
            if attempt < QUIZ_MAX_RETRY:
                time.sleep(5)
                continue
            skip("📝 [QUIZ] Skip sau khi Groq that bai nhieu lan.")
            return True

        # 3. Click dap an
        _click_answers(driver, questions, answers)

        # 4. Submit
        submitted = _submit(driver)
        if not submitted:
            warn("  [Quiz] Submit that bai.")
            if attempt < QUIZ_MAX_RETRY:
                _reset_for_retry(driver)
                continue
            return True

        # 5. Kiem tra ket qua
        passed = _check_passed(driver)
        if passed:
            success(f"✅ [QUIZ] PASSED (lan {attempt})!")
            return True

        warn(f"  [Quiz] Trot lan {attempt}.")
        if attempt < QUIZ_MAX_RETRY:
            info("  [Quiz] Thu lai sau 5s...")
            time.sleep(5)
            _reset_for_retry(driver)
        else:
            error(f"[Quiz] Da thu {QUIZ_MAX_RETRY} lan van trot.")

    return True
