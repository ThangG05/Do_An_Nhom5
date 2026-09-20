from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

from app.models.enums import AIDocumentType

VIETNAM_TZ = timezone(timedelta(hours=7))


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    document_type: AIDocumentType
    academic_year: str | None
    published_at: datetime | None


def infer_document_type(title: str) -> AIDocumentType:
    value = title.casefold().strip(" []")
    if re.search(r"\b(quy chế|nội quy|quy định)\b", value):
        return AIDocumentType.REGULATION
    if re.search(r"\bquyết định\b", value):
        return AIDocumentType.DECISION
    if re.search(r"\b(thông báo|thông tin tuyển sinh)\b", value):
        return AIDocumentType.ANNOUNCEMENT
    if re.search(r"\b(hướng dẫn|cẩm nang|sổ tay)\b", value):
        return AIDocumentType.GUIDE
    if re.search(r"\b(faq|hỏi đáp|câu hỏi thường gặp)\b", value):
        return AIDocumentType.FAQ
    return AIDocumentType.OTHER


def infer_academic_year(text: str) -> str | None:
    match = re.search(r"(?<!\d)([12]\d{3})\s*[/\-–—]\s*([12]\d{3})(?!\d)", text)
    if not match:
        match = re.search(r"(?<!\d)([12]\d{3})([12]\d{3})(?!\d)", text)
    if not match:
        return None
    first, second = int(match.group(1)), int(match.group(2))
    return f"{first}/{second}" if second == first + 1 else None


def infer_published_at(text: str) -> datetime | None:
    # Require a publication/issuance label to avoid treating application deadlines as publication dates.
    match = re.search(
        r"\b(?:Ngày(?:\s+đăng)?|Đăng\s+ngày|Cập\s+nhật)\s*:?\s*"
        r"([0-3]?\d)[/\-]([01]?\d)[/\-]([12]\d{3})\b",
        text, re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r"\b(?:Hà\s+Nội\s*,?\s*)?ngày\s+([0-3]?\d)\s+tháng\s+([01]?\d)\s+năm\s+([12]\d{3})\b",
            text[:2000], re.IGNORECASE,
        )
    if not match:
        return None
    try:
        return datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)), tzinfo=VIETNAM_TZ)
    except ValueError:
        return None


def infer_metadata(title: str, content: str,
                   published_at: datetime | None = None) -> DocumentMetadata:
    academic_year = infer_academic_year(title)
    if academic_year is None:
        labelled = re.search(
            r"(?:năm\s*học|nam\s*hoc)\s*[:\-]?\s*((?:[12]\d{3})\s*[/\-–—]\s*(?:[12]\d{3}))",
            content[:3000], re.IGNORECASE,
        )
        if labelled:
            academic_year = infer_academic_year(labelled.group(1))
    return DocumentMetadata(infer_document_type(title), academic_year,
                            published_at or infer_published_at(content[:5000]))
