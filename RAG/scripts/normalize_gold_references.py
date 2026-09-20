"""Build concise, extractive references and required facts from reviewed evidence."""
import argparse
import json
from pathlib import Path
import re
import sys

STOPWORDS = {
    "của", "và", "là", "có", "cho", "trong", "về", "được", "những", "nào", "như",
    "thế", "tại", "theo", "với", "một", "các", "học", "viện", "ngân", "hàng", "thông",
    "tin", "nội", "dung", "sinh", "viên",
}
BOILERPLATE = ("cộng hòa xã hội", "độc lập - tự do", "căn cứ nghị định", "giám đốc học viện")

# Concise facts manually grounded against each stored evidence excerpt. These replace raw OCR/HTML
# excerpts as scoring references; no fact below is inferred from the model answer.
CURATED = {
    "hvnh-003": ["Địa điểm học tại Trường Đại học Kinh tế - Đại học Đà Nẵng, 71 Ngũ Hành Sơn.",
                 "Thời gian học 12 tuần từ 17/08/2026 đến 14/11/2026; lịch thi dự kiến 23/11/2026 đến 05/12/2026."],
    "hvnh-004": ["Đối tượng là sinh viên đại học chính quy đang học tại Học viện Ngân hàng.",
                 "Học tại Đại học Kinh tế - Đại học Đà Nẵng từ 06/07/2026 đến 24/07/2026; thi dự kiến 27-28/07/2026."],
    "hvnh-005": ["Sinh viên chưa hoàn thành nghĩa vụ tài chính bị hủy kết quả đăng ký học phần và tạm dừng quyền lợi học tập.",
                 "Sinh viên cần liên hệ Phòng Tài chính - Kế toán trước 11h ngày 04/03/2026 nếu cần rà soát."],
    "hvnh-006": ["Sinh viên Học viện Ngân hàng lọt vào Tứ kết The Moneyverse - Vũ trụ đồng tiền cấp quốc gia năm 2026."],
    "hvnh-007": ["Khoa Hệ thống thông tin quản lý tham dự sự kiện ProtonX giới thiệu nền tảng CourseMind ngày 31/07/2023.",
                 "Buổi gặp mở ra cơ hội hợp tác ứng dụng CourseMind trong giảng dạy và học tập tại Khoa."],
    "hvnh-008": ["Sinh viên K25 tham quan Hola Park và Trung tâm ươm mầm, đào tạo tại Hòa Lạc ngày 13/02/2023.",
                 "Sinh viên được chia sẻ về ngành CNTT, nghề FSOFTER, giao lưu chuyên gia và tìm hiểu cơ hội việc làm."],
    "hvnh-011": ["Thí sinh tra cứu kết quả xét tuyển từ 14h ngày 10/08/2026.",
                 "Thí sinh trúng tuyển phải xác nhận nhập học trực tuyến trên hệ thống của Bộ và theo dõi hướng dẫn nhập học của Học viện."],
    "hvnh-013": ["Sinh viên đăng ký chương trình thứ hai trước một tuần so với thời điểm bắt đầu học kỳ mới.",
                 "Sinh viên phải ở trình độ tối thiểu năm thứ hai và đáp ứng điều kiện học lực, ngưỡng bảo đảm chất lượng hoặc điều kiện trúng tuyển."],
    "hvnh-014": ["Sinh viên chuyển chương trình không được đang ở năm thứ nhất, năm cuối hoặc thuộc diện xem xét buộc thôi học.",
                 "Sinh viên nộp đơn Mẫu 14 tại Phòng Đào tạo và cần sự đồng ý của các đơn vị phụ trách cùng Giám đốc Học viện."],
    "hvnh-019": ["Học viện triển khai hệ sinh thái hỗ trợ tích hợp sức khỏe tinh thần, năng lực nghề nghiệp và việc làm cho sinh viên.",
                 "Mô hình có Không gian hỗ trợ và tư vấn tâm lý để giúp sinh viên an tâm học tập."],
    "hvnh-020": ["Khoa Hệ thống thông tin quản lý tổ chức tọa đàm định hướng nghề nghiệp thường niên để sinh viên tiếp cận cơ hội việc làm đúng chuyên ngành.",
                 "Tọa đàm có sự tham gia của các ngân hàng và doanh nghiệp công nghệ, hệ thống thông tin."],
    "hvnh-021": ["Sinh viên ngành Hệ thống thông tin quản lý từ khóa K19 được miễn chuẩn đầu ra Kỹ năng sử dụng CNTT trong năm học 2019/2020."],
    "hvnh-022": ["Chung kết cấp Học viện Vietnam ESG Challenge 2026 diễn ra tối 26/08/2026 tại Hội trường 310A.",
                 "Chương trình gồm khai mạc, phần thi của các đội và đánh giá của Ban Giám khảo."],
    "hvnh-023": ["Sinh viên có chứng chỉ VSTEP đạt mức điểm theo quy định được quy đổi kết quả và miễn các học phần Tiếng Anh tương ứng."],
    "hvnh-024": ["Thông báo áp dụng cho sinh viên ngành Công nghệ thông tin và Hệ thống thông tin quản lý đủ điều kiện thực tập, làm đồ án tốt nghiệp đợt 1 năm 2026/2027."],
    "hvnh-025": ["Tọa đàm tập trung chuẩn hóa đánh giá đồ án tốt nghiệp từ chuẩn đầu ra đến tiêu chí chấm và minh chứng đánh giá."],
    "hvnh-027": ["Người viết chọn ngành MIS vì yêu công nghệ và khẳng định không hối hận với lựa chọn này.",
                 "Năm đầu học MIS đem lại nhiều môn học, thuật ngữ và trải nghiệm mới."],
    "hvnh-028": ["Sinh viên đăng nhập LMS tại https://lms.hvnh.edu.vn bằng tài khoản mã sinh viên @hvnh.edu.vn và mật khẩu cổng online.",
                 "Sau đăng nhập, sinh viên truy cập học phần qua danh sách thời khóa biểu hoặc mục My Courses."],
    "hvnh-029": ["Hội thảo Chuyển đổi số: từ Dữ liệu đến Tự động hóa do Học viện Ngân hàng và FPT Software đồng tổ chức ngày 09/12/2022."],
    "hvnh-030": ["Hội thảo khoa học quốc gia ngày 09/12/2022 do Học viện Ngân hàng phối hợp FPT Software tổ chức dưới sự chủ trì của Ngân hàng Nhà nước Việt Nam."],
    "hvnh-031": ["Buổi chia sẻ ngày 12/05/2026 có Co-Founder Min Software Kiều Xuân Tùng và sinh viên K26CNTT.",
                 "Nội dung gồm nhu cầu ứng dụng công nghệ, kiến trúc giải pháp, kinh nghiệm triển khai và định hướng nghề nghiệp."],
    "hvnh-032": ["Nghề MIS tạo dựng và duy trì nguồn thông tin nhằm mang lại lợi thế cạnh tranh cho doanh nghiệp.",
                 "Người làm MIS cần kiến thức về công nghệ thông tin và nghiệp vụ kinh tế."],
    "hvnh-033": ["Thông tin sai lệch về bầu cử có thể được tạo có chủ đích để gây hiểu nhầm về ứng viên, quy trình hoặc kết quả bầu cử.",
                 "Trong môi trường số, nội dung sai lệch lan truyền nhanh và ảnh hưởng nhận thức người tiếp nhận."],
    "hvnh-041": ["Quyết định 3455/QĐ-HVNH có hiệu lực trong năm học 2025/2026.",
                 "Đại học chính quy sau tự chủ có mức 785.000 đồng/tín chỉ khối III, 830.000 đồng/tín chỉ khối V và 800.000 đồng/tín chỉ khối VII."],
    "hvnh-042": ["Triệu Thu Hương là Trưởng Bộ môn CNTT, thuộc Bộ môn Tin học quản lý.",
                 "Cô phụ trách Tin học đại cương, Cơ sở lập trình 1 và Lập trình Web."],
}

QUESTION_FIXES = {
    "hvnh-005": "Sinh viên còn nợ học phí học kỳ II năm học 2025/2026 bị xử lý thế nào và cần liên hệ khi nào?",
    "hvnh-028": "Sinh viên đăng nhập và truy cập học phần trên hệ thống LMS như thế nào?",
}


def tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[\wÀ-ỹ]+", text.casefold())
            if len(token) > 2 and token not in STOPWORDS}


def sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    clean = re.sub(r"\s+Ngày(?:\s+đăng)?\s*:?\s*\d{1,2}/\d{1,2}/\d{4}\s+[\d,.]+\s+lượt\s+xem\s+",
                   ". ", clean, flags=re.IGNORECASE)
    return [part.strip(" -•") for part in re.split(r"(?<=[.!?;])\s+", clean)
            if 25 <= len(part.strip()) <= 500]


def select_reference(question: str, evidence: str, max_facts: int = 2) -> list[str]:
    question_tokens = tokens(question)
    question_numbers = set(re.findall(r"\d+(?:[/.-]\d+)*", question))
    ranked = []
    for index, sentence in enumerate(sentences(evidence)):
        folded = sentence.casefold()
        if any(marker in folded for marker in BOILERPLATE):
            continue
        sentence_tokens = tokens(sentence)
        overlap = len(question_tokens & sentence_tokens)
        number_overlap = len(question_numbers & set(re.findall(r"\d+(?:[/.-]\d+)*", sentence)))
        specificity = min(3, len(re.findall(r"\d+(?:[/.-]\d+)*|[A-ZĐ]{2,}", sentence)))
        score = overlap * 3 + number_overlap * 4 + specificity
        if score:
            ranked.append((score, index, sentence))
    if not ranked or ranked[0][0] < 6:
        return []
    best = max(row[0] for row in ranked)
    chosen = sorted([row for row in sorted(ranked, reverse=True)
                     if row[0] >= max(6, best * .55)][:max_facts], key=lambda row: row[1])
    return [row[2] for row in chosen]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("evals/rag-gold-draft.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/rag-gold.json"))
    parser.add_argument("--max-facts", type=int, default=2)
    args = parser.parse_args()
    cases = json.loads(args.input.read_text(encoding="utf-8"))
    normalized = skipped = 0
    for case in cases:
        if case.get("review_status") != "APPROVED":
            continue
        if case.get("expected_refused"):
            case["required_facts"] = []
            case["reference_policy"] = "refusal_v1"
            continue
        if case["id"] in QUESTION_FIXES:
            case["question"] = QUESTION_FIXES[case["id"]]
        if case["id"] == "hvnh-034":
            case["review_status"] = "NEEDS_REFERENCE_REVIEW"
            case["review_notes"] = "OCR nguồn bị vỡ ký tự; không dùng làm gold cho tới khi OCR lại."
            skipped += 1
            continue
        if case["id"] in CURATED:
            facts = CURATED[case["id"]]
            case["required_facts"] = facts
            case["reference_answer"] = " ".join(facts)
            case["reference_policy"] = "evidence_grounded_curated_v3"
            case["review_notes"] = "Reference v3: facts ngắn đã đối chiếu evidence, không lấy từ output của RAG."
            normalized += 1
            continue
        facts = select_reference(case["question"], case.get("evidence_excerpt") or "", args.max_facts)
        if not facts:
            case["review_status"] = "NEEDS_REFERENCE_REVIEW"
            case["review_notes"] = "Không tìm được câu extractive liên quan đủ mạnh trong evidence."
            skipped += 1
            continue
        case["required_facts"] = facts
        case["reference_answer"] = " ".join(facts)
        case["reference_policy"] = "extractive_required_facts_v2"
        case["review_notes"] = "Reference v2: câu trích nguyên văn từ evidence, chọn theo độ liên quan câu hỏi."
        normalized += 1
    args.output.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"normalized={normalized} needs_review={skipped} output={args.output}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
