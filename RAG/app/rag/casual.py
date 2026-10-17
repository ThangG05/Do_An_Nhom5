"""Narrow, low-cost routing for ordinary conversation outside factual RAG."""
import re
import unicodedata


_OFFICIAL_TERMS = (
    "hvnh", "học viện", "ngân hàng", "quy định", "học phí", "học bổng",
    "tuyển sinh", "thời khóa biểu", "lịch thi", "điểm thi", "chương trình đào tạo",
    "giảng viên", "mã sinh viên", "văn bản", "tài liệu", "nghị định", "thông báo",
)
_SENSITIVE_TERMS = (
    "tự tử", "tự hại", "trầm cảm", "bệnh", "thuốc", "chẩn đoán", "đầu tư",
    "chứng khoán", "vay tiền", "pháp luật", "kiện tụng", "mật khẩu", "token",
    "thời tiết", "tin tức", "tỷ giá", "bao nhiêu tiền", "giá hiện tại",
)
_CONVERSATION_CUES = (
    "mình buồn", "tôi buồn", "mình mệt", "tôi mệt", "mình căng thẳng",
    "tôi căng thẳng", "mình stress", "tôi stress", "mình chán", "tôi chán",
    "nói chuyện với mình", "trò chuyện với mình", "tâm sự với mình",
    "kể chuyện vui", "kể một chuyện vui", "kể chuyện cười",
    "động viên mình", "động viên tôi", "gợi ý cách thư giãn",
    "gợi ý hoạt động thư giãn", "làm sao để bớt căng thẳng",
    "làm sao để bớt buồn", "gợi ý cách học hiệu quả",
    "mẹo tập trung học", "làm sao để tập trung học",
    "gợi ý món ăn", "hôm nay ăn gì", "tối nay ăn gì", "mình nên ăn gì",
    "cuối tuần làm gì", "gợi ý hoạt động cuối tuần", "chúc mình", "một lời chúc",
    "bạn khỏe không", "bạn thế nào", "bạn có thể nói chuyện với mình không",
)


def is_casual_conversation(question: str) -> bool:
    """Only explicit, short non-factual intents may use the bounded casual LLM path."""
    normalized = " ".join(re.findall(r"[^\W_]+", unicodedata.normalize(
        "NFKC", question).casefold(), flags=re.UNICODE))
    if not normalized or len(question) > 300 or re.search(r"\d|https?://|@", question):
        return False
    if any(term in normalized for term in (*_OFFICIAL_TERMS, *_SENSITIVE_TERMS)):
        return False
    if any(term in normalized for term in ("ở đâu", "khi nào", "ai là", "có đúng không")):
        return False
    return any(cue in normalized for cue in _CONVERSATION_CUES)
