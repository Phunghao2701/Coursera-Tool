import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

import config
from utils.logger import success, info, warn, error, step, skip

# ============================================================
#  NAVIGATOR — Lay danh sach items va dieu huong
#
#  Coursera href patterns (THUC TE tu HTML inspection):
#   /learn/SLUG/lecture/ID/name      -> Video
#   /learn/SLUG/supplement/ID/name   -> Reading
#   /learn/SLUG/discussionPrompt/ID/name -> Discussion
#   /learn/SLUG/assignment-submission/ID/name -> Graded (skip)
#   /learn/SLUG/exam/...             -> Graded Quiz (skip)
#   /learn/SLUG/peer/...             -> Peer Assignment (skip)
# ============================================================

# Loai item va pattern tuong ung
TYPE_PATTERNS = {
    "video":      ["/lecture/"],
    "reading":    ["/supplement/"],
    "discussion": ["/discussionprompt/", "/discussion-prompt/"],
    "quiz":       ["/exam/"],  # exam = graded quiz
    "graded":     ["/assignment-submission/", "/peer/",
                   "/gradedlti/", "/programming/", "/graded-lti/"],
}

# Tên slug của khóa học hiện tại (set khi get_all_course_items chạy)
_COURSE_SLUG = ""


def get_all_course_items(driver) -> list[dict]:
    """
    Quét khoa hoc va tra ve danh sach items theo tung week.
    """
    global _COURSE_SLUG

    base_url = _get_base_url(driver)
    _COURSE_SLUG = base_url.split("/learn/")[-1].rstrip("/")
    info(f"Course slug: {_COURSE_SLUG}")
    info(f"Base URL: {base_url}")

    all_items = []
    seen_urls = set()

    # Quét /home/week/N hoac /home/module/N (Coursera doi sang module)
    empty_count = 0
    found_pattern = None  # "week" hoac "module"

    for week_num in range(1, 20):
        # Thu /home/week/ truoc, neu redirect sang /module/ thi dung module
        if found_pattern is None or found_pattern == "week":
            week_url = f"{base_url}/home/week/{week_num}"
        else:
            week_url = f"{base_url}/home/module/{week_num}"

        driver.get(week_url)
        time.sleep(8)  # Doi React render

        current = driver.current_url
        info(f"  [Module {week_num}] URL: {current}")

        # Phat hien pattern URL
        if "/home/module/" in current:
            found_pattern = "module"
        elif "/home/week/" in current:
            found_pattern = "week"

        # Kiem tra co phai la trang module/week khong
        pattern_check = f"/home/module/{week_num}" if found_pattern == "module" else f"/home/week/{week_num}"
        if pattern_check not in current:
            info(f"Module {week_num} khong ton tai — dung scan.")
            break

        # Debug: dem so <a> tags
        try:
            all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
            info(f"  [Module {week_num}] So <a> tags: {len(all_links)}")
            # In 5 hrefs dau tien de debug
            lesson_links = [l.get_attribute("href") or "" for l in all_links
                           if any(k in (l.get_attribute("href") or "").lower()
                                  for k in ["/lecture/", "/supplement/", "/discussion"])]
            if lesson_links:
                info(f"  [Module {week_num}] Lesson links: {lesson_links[:3]}")
        except Exception:
            pass

        week_items = _extract_items_from_page(driver, seen_urls)
        if week_items:
            info(f"  Week {week_num}: {len(week_items)} items")
            all_items.extend(week_items)
            empty_count = 0
        else:
            empty_count += 1
            info(f"  Week {week_num}: 0 items")
            if empty_count >= 3:
                info("3 tuan lien tiep trong — ket thuc scan.")
                break

    info(f"Tong cong: {len(all_items)} items tim thay.")
    return all_items


def _get_base_url(driver) -> str:
    """Lay base URL cua khoa hoc."""
    url = driver.current_url
    if "/learn/" in url:
        parts = url.split("/learn/")
        slug = parts[1].split("/")[0]
        return f"https://www.coursera.org/learn/{slug}"
    return url


def _extract_items_from_page(driver, seen_urls: set) -> list[dict]:
    """
    Trich xuat tat ca lesson items tu trang hien tai.
    Dua vao href cua <a> tags - KHONG dung /item/ (Coursera moi).
    """
    items = []

    try:
        # Scroll xuong de load lazy items
        _scroll_page(driver)
        time.sleep(2)

        # Lay tat ca <a> tags
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")

        for link in all_links:
            try:
                href = link.get_attribute("href") or ""
                if not href:
                    continue

                # Phan loai URL
                item_type = _classify_url(href)
                if not item_type:
                    continue

                # Deduplicate
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                # Lay ten item
                name = _get_name(driver, link, href)

                # RE-CLASSIFY: Neu URL la graded nhung ten co 'quiz' hoac 'exam', no thuc chat la quiz!
                if item_type == "graded":
                    name_lower = name.lower()
                    if "quiz" in name_lower or "exam" in name_lower:
                        item_type = "quiz"

                # Kiem tra completed (tim SVG checkmark hoac aria)
                completed = _check_completed(driver, link)

                items.append({
                    "name":      name,
                    "url":       href,
                    "type":      item_type,
                    "completed": completed,
                })

            except StaleElementReferenceException:
                continue
            except Exception:
                continue

    except Exception as e:
        warn(f"Loi khi extract items: {e}")

    return items


def _classify_url(href: str) -> str:
    """
    Phan loai URL thanh loai item.
    Tra ve 'video' | 'reading' | 'discussion' | 'graded' | None
    """
    href_lower = href.lower()

    # Phai chua /learn/ moi la lesson link
    if "/learn/" not in href_lower:
        return None

    for item_type, patterns in TYPE_PATTERNS.items():
        if any(p in href_lower for p in patterns):
            return item_type

    return None


def _get_name(driver, link_element, href: str) -> str:
    """Lay ten item tu link element."""
    try:
        # Lay aria-label - thong tin day du nhat
        # Format: "Video, Welcome, Completed, 1 min"
        aria = link_element.get_attribute("aria-label") or ""
        if aria:
            parts = [p.strip() for p in aria.split(",")]
            if len(parts) >= 2:
                name_candidate = parts[1].strip()
                # Loai bo cac gia tri khong phai ten
                skip_vals = {"completed", "not submitted", "passed", "failed", 
                             "not started", "graded", "video", "reading"}
                if name_candidate.lower() not in skip_vals:
                    return name_candidate

        # Lay text truc tiep tu link
        text = link_element.text.strip()
        if text and len(text) > 2:
            return text[:80]

        # Tim <p> hoac <span> ben trong
        try:
            inner = link_element.find_element(By.CSS_SELECTOR, "p, span, h3")
            inner_text = inner.text.strip()
            if inner_text and len(inner_text) > 2:
                return inner_text[:80]
        except Exception:
            pass

    except Exception:
        pass

    # Fallback tu URL
    parts = href.rstrip("/").split("/")
    if parts:
        return parts[-1].replace("-", " ").title()[:60]
    return "Unknown Item"


def _check_completed(driver, link_element) -> bool:
    """Kiem tra item da hoan thanh chua tu context cua no trong list."""
    try:
        # 1. Kiem tra qua aria-label (day du va chinh xac nhat vi chua text 'Completed' cho screen reader)
        aria = link_element.get_attribute("aria-label") or ""
        if aria:
            aria_lower = aria.lower()
            if "completed" in aria_lower or "passed" in aria_lower or "submitted" in aria_lower:
                return True

        # 2. Lay HTML cua phan chua link (co the chua SVG checkmark hoac completed text)
        parent = link_element.find_element(By.XPATH, "..")
        parent_html = parent.get_attribute("outerHTML").lower()
        if 'aria-label="completed"' in parent_html or "aria-label='completed'" in parent_html or "completed" in parent_html or "passed" in parent_html:
            return True
        
        # 3. Hoac class chua "completed"
        if "completed" in (parent.get_attribute("class") or "").lower():
            return True
    except Exception:
        pass
    return False


def _scroll_page(driver):
    """Scroll xuong de trigger lazy load."""
    try:
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.3)
        driver.execute_script("window.scrollTo(0, 0);")
    except Exception:
        pass


def navigate_to_item(driver, item: dict):
    """Dieu huong den URL cua item."""
    url = item.get("url", "")
    if url and driver.current_url.rstrip("/") != url.rstrip("/"):
        driver.get(url)
        time.sleep(3)
