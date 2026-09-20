"""Build a stratified retrieval regression set from current indexed documents."""
import argparse
import asyncio
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.crawler import AISource, AISourceURL
from app.models.enums import AIDocumentStatus
from app.models.rag import AIDocument, AIDocumentVersion

TEMPLATES = {
    "REGULATION": "Quy định trong tài liệu “{title}” là gì?",
    "DECISION": "Quyết định “{title}” quy định nội dung gì?",
    "ANNOUNCEMENT": "Thông báo “{title}” có nội dung gì?",
    "GUIDE": "Hướng dẫn “{title}” áp dụng như thế nào?",
    "FAQ": "Theo mục hỏi đáp “{title}”, câu trả lời là gì?",
    "OTHER": "Thông tin chính trong bài “{title}” là gì?",
}
NEGATIVES = [
    "Quy chế điều khiển tàu vũ trụ HVNH năm 2099/2100",
    "Thông báo mở ngành khảo cổ học Sao Hỏa năm học 2098/2099",
    "Mức phí nuôi rồng trong ký túc xá năm học 2097/2098",
    "Danh sách giảng viên môn dịch chuyển tức thời năm học 2096/2097",
    "Lịch thi bằng lái phi thuyền năm học 2095/2096",
]


def descriptive_title(title: str) -> bool:
    folded = title.casefold().strip()
    words = re.findall(r"[\wÀ-ỹ]+", folded)
    return (len(words) >= 5 and not re.match(r"^[0-9a-f]{6,}[_ -]", folded)
            and not folded.startswith(("phụ lục", "một số câu hỏi thường gặp"))
            and not folded.endswith((".pdf", ".docx", ".xlsx")))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("evals/retrieval-stratified.json"))
    parser.add_argument("--positive", type=int, default=55)
    args = parser.parse_args()
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(select(
            AIDocument.id, AIDocument.title, AIDocument.document_type, AIDocument.academic_year,
            AIDocument.published_at, AIDocumentVersion.source_url, AISource.id, AISource.name,
        ).join(AIDocumentVersion, AIDocumentVersion.id == AIDocument.current_version_id)
         .join(AISourceURL, AISourceURL.document_id == AIDocument.id)
         .join(AISource, AISource.id == AISourceURL.source_id)
         .where(AIDocument.deleted_at.is_(None), AIDocument.is_current.is_(True),
                AIDocumentVersion.status == AIDocumentStatus.INDEXED,
                AISource.enabled.is_(True))
         .order_by(AISource.name, AIDocument.document_type, AIDocument.published_at.desc().nullslast()))).all()
    await dispose_engine()
    unique = {}
    for row in rows:
        unique.setdefault(str(row.id), row)
    title_counts = Counter(row.title.casefold().strip() for row in unique.values())
    buckets = defaultdict(list)
    for row in unique.values():
        if title_counts[row.title.casefold().strip()] != 1 or not descriptive_title(row.title):
            continue
        buckets[(row.name, row.document_type.value)].append(row)
    selected = []
    keys = sorted(buckets)
    while len(selected) < args.positive and any(buckets.values()):
        for key in keys:
            if buckets[key] and len(selected) < args.positive:
                selected.append(buckets[key].pop(0))
    cases = []
    for number, row in enumerate(selected, 1):
        document_type = row.document_type.value
        safe_id = re.sub(r"[^a-z0-9]+", "-", row.title.casefold()).strip("-")[:35]
        cases.append({
            "id": f"strat-{number:03d}-{safe_id}", "category": document_type.casefold(),
            "query": TEMPLATES[document_type].format(title=row.title),
            "expected_document_id": str(row.id), "expected_title_contains": [row.title],
            "expected_academic_year": row.academic_year, "source_name": row.name,
            "source_url": row.source_url, "synthetic": True,
        })
    for number, query in enumerate(NEGATIVES, 1):
        cases.append({"id": f"negative-{number:02d}", "category": "negative",
                      "query": query, "expected_empty": True, "synthetic": True})
    args.output.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"cases": len(cases), "positive": len(selected), "negative": len(NEGATIVES),
                      "document_types": Counter(row.document_type.value for row in selected),
                      "sources": Counter(row.name for row in selected)}, ensure_ascii=False, default=dict))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
