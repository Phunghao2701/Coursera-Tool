from utils.logger import skip

# ============================================================
#  ASSIGNMENT HANDLER
#  Graded Assignment / Peer-graded: BỎ QUA
# ============================================================

def handle_assignment(driver) -> bool:
    """
    Bỏ qua các phần Assignment, Graded Quiz, Peer Review.
    Trả về True để bot tiếp tục sang item tiếp theo.
    """
    skip("📝 [ASSIGNMENT] Phần này là Assignment/Graded — bỏ qua.")
    return True  # Không cần làm gì, chỉ skip
