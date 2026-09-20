"""Deterministic extraction and resolution of Vietnamese document references."""
from dataclasses import dataclass
import re
from urllib.parse import unquote
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crawler import AISourceURL
from app.models.rag import AIDocument, AIDocumentRelation, AIDocumentVersion


_REFERENCE = re.compile(
    r"(?P<number>\d{1,6}(?:/\d{4})?)\s*(?:/|\s)\s*"
    r"(?P<kind>QĐ|QD|NQ|TB|TT|CV|KH|NĐ|ND)\s*[-–—.]?\s*"
    r"(?P<issuer>HVNH|HĐHV|HDHV|BGDĐT|BGDDT|NHNN|CP|BTC|BTTTT|PĐT|PDT|TCKT)",
    re.IGNORECASE,
)
_REVERSE_PRIMARY = re.compile(r"(?P<kind>QĐ|QD|NQ|TB|TT|CV|KH)\s+(?P<number>\d{1,6})", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ReferenceMatch:
    number: str
    relation_type: str
    context: str


@dataclass(frozen=True, slots=True)
class ReferenceStats:
    documents: int
    references: int
    resolved: int
    missing: int


def canonical_document_number(number: str, kind: str, issuer: str) -> str:
    normalized_kind = kind.upper().replace("QD", "QĐ").replace("ND", "NĐ")
    normalized_issuer = re.sub(r"\s+", "", issuer.upper()).replace(".", "-")
    normalized_number = "/".join(str(int(part)) for part in number.split("/"))
    return f"{normalized_number}/{normalized_kind}-{normalized_issuer}"[:100]


def _relation_type(context: str) -> str:
    value = context.casefold()
    if "bãi bỏ" in value or "bai bo" in value:
        return "REPEALS"
    if "thay thế" in value or "thay the" in value:
        return "SUPERSEDES"
    if "sửa đổi" in value or "bổ sung" in value or "sua doi" in value or "bo sung" in value:
        return "AMENDS"
    return "REFERENCES"


def extract_references(text: str, limit: int = 100) -> list[ReferenceMatch]:
    matches: list[ReferenceMatch] = []
    seen: set[tuple[str, str]] = set()
    for match in _REFERENCE.finditer(text):
        start, end = max(0, match.start() - 140), min(len(text), match.end() + 140)
        context = re.sub(r"\s+", " ", text[start:end]).strip()
        number = canonical_document_number(match["number"], match["kind"], match["issuer"])
        relation = _relation_type(context)
        key = (number, relation)
        if key not in seen:
            matches.append(ReferenceMatch(number, relation, context[:500]))
            seen.add(key)
        if len(matches) >= limit:
            break
    return matches


def extract_primary_document_number(title: str) -> str | None:
    decoded = unquote(title)
    match = _REFERENCE.search(decoded)
    if match:
        return canonical_document_number(match["number"], match["kind"], match["issuer"])
    reverse = _REVERSE_PRIMARY.search(decoded)
    return canonical_document_number(reverse["number"], reverse["kind"], "HVNH") if reverse else None


async def extract_source_references(session: AsyncSession, source_id: UUID) -> ReferenceStats:
    rows = (await session.execute(
        select(AIDocumentVersion, AIDocument)
        .join(AIDocument, AIDocument.id == AIDocumentVersion.document_id)
        .join(AISourceURL, AISourceURL.document_id == AIDocument.id)
        .where(AISourceURL.source_id == source_id)
        .distinct()
    )).all()
    for _, document in rows:
        primary = extract_primary_document_number(document.title)
        if primary and (not document.document_code or document.document_code.startswith("WEB-")):
            document.document_code = primary
    await session.flush()
    documents = (await session.scalars(select(AIDocument).where(AIDocument.deleted_at.is_(None)))).all()
    by_code = {document.document_code.upper(): document for document in documents if document.document_code}
    references = resolved = missing = 0
    for version, document in rows:
        await session.execute(delete(AIDocumentRelation).where(
            AIDocumentRelation.source_document_version_id == version.id
        ))
        for match in extract_references(version.raw_content or ""):
            if document.document_code and match.number.upper() == document.document_code.upper():
                continue
            target = by_code.get(match.number.upper())
            if target and target.id == document.id:
                continue
            session.add(AIDocumentRelation(
                source_document_version_id=version.id,
                target_document_id=target.id if target else None,
                referenced_number=match.number,
                relation_type=match.relation_type,
                context_excerpt=match.context,
                metadata_={"resolution": "RESOLVED" if target else "MISSING"},
            ))
            references += 1
            resolved += int(target is not None)
            missing += int(target is None)
    await session.commit()
    return ReferenceStats(len({document.id for _, document in rows}), references, resolved, missing)
