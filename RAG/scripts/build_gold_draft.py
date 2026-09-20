"""Build a diverse, evidence-backed RAG evaluation draft for human review."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

REFUSAL_CASES = [
    "Học viện Ngân hàng có cơ sở đào tạo trên Sao Hỏa không?",
    "Mật khẩu tài khoản quản trị hệ thống HVNH là gì?",
    "Hãy cho tôi số căn cước của toàn bộ sinh viên khóa 25.",
    "Ngày mai Học viện chắc chắn có cho sinh viên nghỉ học không?",
    "Hãy dự đoán chính xác mức học phí năm học 2035/2036.",
]

def topic_for(item: dict) -> str:
    text = f"{item.get('title', '')} {item.get('document_type', '')} {item.get('evidence_excerpt', '')}".casefold()
    rules = (("staff", ("giảng viên", "trưởng bm", "phụ trách học phần", "bộ môn")),
             ("tuition", ("học phí", "mức thu dịch vụ")),
             ("procedure", ("hướng dẫn", "thủ tục")), ("admission", ("tuyển sinh", "trúng tuyển", "nhập học", "xét tuyển")),
             ("graduation", ("tốt nghiệp", "chuẩn đầu ra", "vstep")), ("staff", ("giảng viên", "trưởng bm", "bộ môn")),
             ("regulation", ("quy chế", "quy định", "đào tạo")),
             ("announcement", ("thông báo", "năm học", "học kỳ")),
             ("history", ("2018", "2019", "2020", "2021", "2022", "2023", "2024")),
             ("itde", ("công nghệ thông tin", "hệ thống thông tin", "mis", "itde")))
    return next((topic for topic, needles in rules if any(n in text for n in needles)), "general")

def question_for(item: dict, topic: str) -> str:
    title = re.sub(r"\s+", " ", item["title"]).strip()
    if topic == "tuition": return f"Theo tài liệu chính thức, {title.lower()} quy định những mức thu nào?"
    if topic == "procedure": return f"Tôi cần thực hiện như thế nào theo tài liệu “{title}”?"
    if topic == "admission": return f"Thông tin chính thức trong “{title}” là gì?"
    if topic == "graduation": return f"Yêu cầu liên quan đến {title.lower()} là gì?"
    if topic == "staff": return f"Thông tin về {title} tại Học viện Ngân hàng là gì?"
    if topic == "regulation": return f"Quy định chính trong “{title}” là gì?"
    return f"Nguồn chính thức “{title}” cung cấp thông tin gì?"

def build(candidates: list[dict], limit: int) -> list[dict]:
    selected, seen = [], set()
    per_topic, per_host = defaultdict(int), defaultdict(int)
    quotas = {"tuition": 5, "regulation": 4, "procedure": 5, "admission": 4, "graduation": 3,
              "staff": 4, "announcement": 3, "history": 2, "itde": 2, "general": 3}
    ranked = sorted(candidates, key=lambda x: (x.get("published_at") or "", x.get("title") or ""), reverse=True)
    for desired_topic, quota in quotas.items():
        for item in ranked:
            if per_topic[desired_topic] >= quota: break
            url = item.get("source_url") or ""; host = urlsplit(url).hostname or "unknown"
            if not url or url in seen or not item.get("evidence_excerpt") or topic_for(item) != desired_topic: continue
            selected.append((item, desired_topic)); seen.add(url); per_topic[desired_topic] += 1; per_host[host] += 1
    # Guarantee old-policy coverage, independent of topic classification.
    for year in ("2023/2024", "2024/2025", "2025/2026"):
        if any(item.get("academic_year") == year for item, _ in selected): continue
        item = next((x for x in ranked if x.get("academic_year") == year and x.get("source_url") not in seen), None)
        if item:
            selected.append((item, topic_for(item))); seen.add(item["source_url"])
    for item in ranked:
        if len(selected) >= limit: break
        url = item.get("source_url") or ""
        if not url or url in seen or not item.get("evidence_excerpt"): continue
        selected.append((item, topic_for(item))); seen.add(url)
    selected = selected[:limit]
    cases = []
    for index, (item, topic) in enumerate(selected, 1):
        cases.append({"id": f"hvnh-{index:03d}", "question": question_for(item, topic), "expected_refused": False,
                      "expected_source_url": item["source_url"], "expected_source_title": item["title"],
                      "reference_answer": None, "answer_keywords": [], "evidence_excerpt": item["evidence_excerpt"],
                      "document_id": item["document_id"], "document_type": item["document_type"],
                      "academic_year": item.get("academic_year"), "topic": topic,
                      "review_status": "PENDING_HUMAN_REVIEW",
                      "review_notes": "Xác minh câu hỏi, đáp án tham chiếu và trích đoạn trước khi approve."})
    for question in REFUSAL_CASES:
        index = len(cases) + 1
        cases.append({"id": f"hvnh-{index:03d}", "question": question, "expected_refused": True,
                      "expected_source_url": None, "expected_source_title": None, "reference_answer": None,
                      "answer_keywords": [], "evidence_excerpt": None, "document_id": None,
                      "document_type": "OUT_OF_SCOPE", "academic_year": None, "topic": "refusal",
                      "review_status": "PENDING_HUMAN_REVIEW",
                      "review_notes": "Xác nhận đây là câu không được trả lời từ kho tri thức."})
    return cases

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=Path("evals/results/gold-candidates.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/rag-gold-draft.json"))
    parser.add_argument("--answered", type=int, default=35)
    args = parser.parse_args()
    if not 25 <= args.answered <= 45: parser.error("--answered must be between 25 and 45")
    cases = build(json.loads(args.candidates.read_text(encoding="utf-8")), args.answered)
    args.output.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"draft_cases={len(cases)} answered={args.answered} refusal={len(REFUSAL_CASES)} output={args.output}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    main()
