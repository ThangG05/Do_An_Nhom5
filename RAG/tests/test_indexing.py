from types import SimpleNamespace
from uuid import uuid4
from app.knowledge.indexing import point_payload
from app.models.enums import AIDocumentType, AIVisibility


def test_qdrant_payload_contains_retrieval_and_citation_fields() -> None:
    document = SimpleNamespace(id=uuid4(), document_code="TB-1", title="Thông báo",
        document_type=AIDocumentType.ANNOUNCEMENT, academic_year="2025/2026",
        issuer="Học viện Ngân hàng", published_at=None, effective_from=None,
        effective_to=None, visibility=AIVisibility.PUBLIC, group_id=None)
    version = SimpleNamespace(id=uuid4(), source_url="https://hvnh.edu.vn/a.html", version_number=1,
                              metadata_={})
    chunk = SimpleNamespace(id=uuid4(), content="Nội dung", page_start=None, page_end=None,
        section_title="Điều 1", heading_path=["Chương I", "Điều 1"], chunk_index=0,
        content_hash="a" * 64)
    payload = point_payload(document, version, chunk)
    assert payload["is_current"] is True
    assert payload["document_type"] == "ANNOUNCEMENT"
    assert payload["source_url"].startswith("https://")
    assert payload["content"] == "Nội dung"


def test_historical_payload_uses_version_temporal_snapshot() -> None:
    document = SimpleNamespace(id=uuid4(), document_code="QD-1", title="Quy định",
        document_type=AIDocumentType.REGULATION, academic_year="2025/2026",
        issuer="Học viện Ngân hàng", published_at=None, effective_from=None,
        effective_to=None, visibility=AIVisibility.PUBLIC, group_id=None)
    version = SimpleNamespace(id=uuid4(), source_url="https://hvnh.edu.vn/old.pdf", version_number=1,
                              metadata_={"academic_year": "2023/2024", "published_at": "2023-08-01T00:00:00+07:00"})
    chunk = SimpleNamespace(id=uuid4(), content="Nội dung cũ", page_start=None, page_end=None,
        section_title=None, heading_path=[], chunk_index=0, content_hash="b" * 64)
    payload = point_payload(document, version, chunk, is_current=False)
    assert payload["academic_year"] == "2023/2024"
    assert payload["published_at"].startswith("2023-08-01")
    assert payload["is_current"] is False
