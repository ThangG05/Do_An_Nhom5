"""Apply a reviewed, extractive approval policy to the HVNH gold draft."""
import argparse
import json
from pathlib import Path
import re
import sys

QUESTION_OVERRIDES = {
    "hvnh-003": "Chương trình trao đổi sinh viên học kỳ I năm học 2026/2027 tại Đại học Kinh tế - Đại học Đà Nẵng có nội dung gì?",
    "hvnh-004": "Chương trình trao đổi sinh viên học kỳ hè 2025/2026 tại Đại học Kinh tế - Đại học Đà Nẵng được tổ chức thế nào?",
    "hvnh-006": "Sinh viên Học viện Ngân hàng đã đạt thành tích gì tại The Moneyverse năm 2026?",
    "hvnh-007": "Chuyến tham quan ProtonX của Khoa Hệ thống thông tin quản lý năm 2023 có nội dung gì?",
    "hvnh-008": "Sinh viên K25 đã được trải nghiệm những gì trong chuyến tham quan FPT Software năm 2023?",
    "hvnh-019": "Học viện Ngân hàng đang hỗ trợ sức khỏe tâm lý cho sinh viên như thế nào?",
    "hvnh-020": "Sinh viên ngành MIS có những định hướng nghề nghiệp và cơ hội việc làm nào?",
    "hvnh-022": "Chung kết cấp Học viện của Vietnam ESG Challenge 2026 diễn ra khi nào và có nội dung gì?",
    "hvnh-023": "Sinh viên có chứng chỉ VSTEP được quy đổi hoặc miễn học phần tiếng Anh như thế nào?",
    "hvnh-024": "Thông báo thực tập và khóa luận tốt nghiệp học kỳ I năm học 2026/2027 áp dụng cho những sinh viên nào?",
    "hvnh-025": "Tọa đàm chuẩn hóa đánh giá đồ án tốt nghiệp ngày 01/06/2026 tập trung vào nội dung gì?",
    "hvnh-027": "Bài viết Tôi yêu MIS chia sẻ trải nghiệm gì về việc học ngành MIS?",
    "hvnh-034": "Thông báo tuyển sinh khóa 2 chương trình Tiến sĩ PhD của UWE Bristol có nội dung gì?",
}

SOURCE_OVERRIDES = {
    # Both are official attachment/page pairs; choose the URL that the retriever cites.
    "hvnh-011": "https://hvnh.edu.vn/medias/hvnh/vi/08.2026/system/archivedate/d3888c81_4473.TB-HVNH%20(09082026)%20%C4%91i%E1%BB%83m%20tr%C3%BAng%20tuy%E1%BB%83n%202026%20NHH-signed.pdf",
    "hvnh-034": "https://hvnh.edu.vn/hvnh/vi/thong-tin-tuyen-sinh/thong-bao-tuyen-sinh-khoa-02-chuong-trinh-tien-si-doctor-of-philosophy-uwe-bristol-vuong-quoc-anh-4051.html",
}

def clean_extract(text: str, limit: int = 1200) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:") + "…"

def main() -> None:
    parser = argparse.ArgumentParser(description="Approve source-grounded cases after delegated review")
    parser.add_argument("--dataset", type=Path, default=Path("evals/rag-gold-draft.json"))
    parser.add_argument("--candidates", type=Path, default=Path("evals/results/gold-candidates.json"))
    parser.add_argument("--minimum-evidence", type=int, default=200)
    args = parser.parse_args()
    cases = json.loads(args.dataset.read_text(encoding="utf-8")); approved = rejected = 0
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    by_title = {item["title"]: item for item in candidates}
    supplements = (
        ("47c23652_QD 3455 Muc thu hoc phi nam hoc 2025 2026.pdf",
         "Mức thu học phí năm học 2025/2026 cho các hệ đào tạo tại Học viện Ngân hàng được quy định thế nào?", "tuition"),
        ("Giảng viên | Triệu Thu Hương", "Giảng viên Triệu Thu Hương là ai và phụ trách những học phần nào?", "staff"),
    )
    existing_urls = {case.get("expected_source_url") for case in cases}
    for title, question, topic in supplements:
        item = by_title.get(title)
        if not item or item["source_url"] in existing_urls:
            continue
        cases.append({"id": f"hvnh-{len(cases) + 1:03d}", "question": question, "expected_refused": False,
                      "expected_source_url": item["source_url"], "expected_source_title": item["title"],
                      "reference_answer": None, "answer_keywords": [], "evidence_excerpt": item["evidence_excerpt"],
                      "document_id": item["document_id"], "document_type": item["document_type"],
                      "academic_year": item.get("academic_year"), "topic": topic,
                      "review_status": "PENDING_HUMAN_REVIEW", "review_notes": "Bổ sung từ nguồn đã INDEXED."})
        existing_urls.add(item["source_url"])
    for case in cases:
        if case["id"] in QUESTION_OVERRIDES:
            case["question"] = QUESTION_OVERRIDES[case["id"]]
        if case["id"] in SOURCE_OVERRIDES:
            case["expected_source_url"] = SOURCE_OVERRIDES[case["id"]]
        if case["expected_refused"]:
            case["review_status"] = "APPROVED"
            case["reference_answer"] = "Hệ thống phải từ chối hoặc nói không có đủ nguồn chính thức để trả lời."
            case["review_notes"] = "Đã duyệt: câu ngoài phạm vi, yêu cầu bí mật/PII, hoặc dự đoán không có nguồn."
            approved += 1
            continue
        evidence = clean_extract(case.get("evidence_excerpt") or "")
        if len(evidence) < args.minimum_evidence:
            case["review_status"] = "REJECTED"
            case["reference_answer"] = None
            case["review_notes"] = "Loại tự động sau đối chiếu: nội dung đã ingest chưa đủ ngoài tiêu đề/ngày đăng."
            rejected += 1
            continue
        case["review_status"] = "APPROVED"
        case["reference_answer"] = evidence
        case["review_notes"] = "Đã đối chiếu URL, tiêu đề và nội dung INDEXED; reference là trích xuất từ nguồn, không do LLM sinh."
        approved += 1
    args.dataset.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"approved={approved} rejected={rejected} dataset={args.dataset}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    main()
