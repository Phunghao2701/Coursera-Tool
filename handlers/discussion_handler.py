from utils.logger import skip

# ============================================================
#  DISCUSSION HANDLER
#  Tạm thời: BỎ QUA như Assignment
# ============================================================

def handle_discussion(driver) -> bool:
    """
    Tạm thời bỏ qua Discussion Prompt.
    Trả về True để bot tiếp tục sang item tiếp theo.
    """
    skip("💬 [DISCUSSION] Tạm thời bỏ qua Discussion.")
    return True
