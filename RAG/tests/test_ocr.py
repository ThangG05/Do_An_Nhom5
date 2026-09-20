from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.knowledge.ocr import ModalOCRProvider, OCRError
from app.knowledge.policy import assess_url


def test_sensitive_student_debt_attachment_is_excluded() -> None:
    url = ("https://hvnh.edu.vn/medias/77444535_Danh%20s%C3%A1ch%20sinh%20vi%C3%AAn%20"
           "n%E1%BB%A3%20h%E1%BB%8Dc%20ph%C3%AD%20HK02.pdf")
    assert not assess_url(url).allowed
    assert assess_url("https://hvnh.edu.vn/medias/QD-muc-thu-hoc-phi.pdf").allowed


@pytest.mark.asyncio
async def test_modal_ocr_provider_validates_result() -> None:
    provider = object.__new__(ModalOCRProvider)
    provider.settings = SimpleNamespace(ocr_max_retries=0, ocr_timeout_seconds=10, ocr_max_pages=20)
    provider.remote = SimpleNamespace(extract=SimpleNamespace(remote=Mock(return_value={
        "content": "Nội dung OCR hợp lệ của văn bản Học viện Ngân hàng.",
        "page_count": 1,
        "page_ranges": [(1, 0, 53)],
        "engine": "test",
    })))
    result = await provider.extract_pdf(b"pdf")
    assert result.page_count == 1
    assert result.engine == "test"


@pytest.mark.asyncio
async def test_modal_ocr_provider_rejects_short_result() -> None:
    provider = object.__new__(ModalOCRProvider)
    provider.settings = SimpleNamespace(ocr_max_retries=0, ocr_timeout_seconds=10, ocr_max_pages=20)
    provider.remote = SimpleNamespace(extract=SimpleNamespace(remote=Mock(return_value={
        "content": "short", "page_count": 1, "page_ranges": [], "engine": "test",
    })))
    with pytest.raises(OCRError):
        await provider.extract_pdf(b"pdf")
