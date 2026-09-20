from datetime import datetime
from pathlib import Path

import pytest

from app.knowledge.ingestion import DocumentIngestionService, IngestionRequest


def test_ingestion_request_rejects_unsafe_source_url() -> None:
    request = IngestionRequest(
        path=Path("document.pdf"), document_code="QC-01", title="Quy chế",
        source_url="javascript:alert(1)",
    )
    with pytest.raises(ValueError, match="HTTPS"):
        DocumentIngestionService._validate_request(request)


def test_ingestion_request_requires_timezone() -> None:
    request = IngestionRequest(
        path=Path("document.pdf"), document_code="QC-01", title="Quy chế",
        published_at=datetime(2025, 9, 1),
    )
    with pytest.raises(ValueError, match="timezone"):
        DocumentIngestionService._validate_request(request)


def test_ingestion_request_accepts_hvnh_metadata() -> None:
    request = IngestionRequest(
        path=Path("document.pdf"), document_code="QC-2025", title="Quy chế 2025/2026",
        academic_year="2025/2026", source_url="https://hvnh.edu.vn/quy-che",
    )
    DocumentIngestionService._validate_request(request)
