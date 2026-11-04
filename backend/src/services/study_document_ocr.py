"""Modal OCR adapter shared by Study-document moderation jobs."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import io
import re

from PIL import Image, ImageOps
from pypdf import PdfReader
from src.config import settings


class StudyOCRError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class StudyOCRResult:
    content: str
    page_count: int
    page_ranges: list[tuple[int, int, int]]
    engine: str


class ModalStudyOCR:
    def __init__(self) -> None:
        try:
            import modal

            self.remote = modal.Cls.from_name(
                settings.STUDY_MODERATION_OCR_APP,
                settings.STUDY_MODERATION_OCR_CLASS,
            )()
        except Exception as exc:
            raise StudyOCRError("Modal study-document OCR is not configured") from exc

    async def extract_pdf(self, pdf_bytes: bytes) -> StudyOCRResult:
        if not pdf_bytes or len(pdf_bytes) > 25 * 1024 * 1024:
            raise StudyOCRError("OCR PDF must be non-empty and no larger than 25 MiB")

        last_error: Exception | None = None
        for attempt in range(settings.STUDY_MODERATION_OCR_MAX_RETRIES + 1):
            try:
                async with asyncio.timeout(settings.STUDY_MODERATION_OCR_TIMEOUT_SECONDS):
                    result = await asyncio.to_thread(
                        self.remote.extract.remote,
                        pdf_bytes,
                        settings.STUDY_MODERATION_OCR_MAX_PAGES,
                    )
                if not isinstance(result, dict) or len(str(result.get("content", "")).strip()) < 40:
                    raise StudyOCRError("Modal OCR returned too little text")
                ranges = [tuple(map(int, row)) for row in result.get("page_ranges", [])
                          if isinstance(row, (list, tuple)) and len(row) == 3]
                return StudyOCRResult(
                    content=str(result["content"]),
                    page_count=int(result.get("page_count", 0)),
                    page_ranges=ranges,
                    engine=str(result.get("engine", "unknown")),
                )
            except Exception as exc:
                last_error = exc
                if attempt < settings.STUDY_MODERATION_OCR_MAX_RETRIES:
                    await asyncio.sleep(2 ** attempt)
        raise StudyOCRError("Modal OCR provider unavailable") from last_error


def pdf_needs_ocr(data: bytes) -> bool:
    """Match the RAG crawler's low-text and broken-font OCR trigger."""
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        content = "\n".join(page.extract_text() or "" for page in reader.pages[:100])
    except Exception:
        return True
    tokens = re.findall(r"\w+", content, flags=re.UNICODE)
    single_character_ratio = (sum(len(token) == 1 for token in tokens) / len(tokens)) if tokens else 1.0
    wrong_font_glyphs = sum(content.count(char) for char in "äöüÄÖÜ")
    vietnamese_glyphs = sum(content.count(char) for char in "ăâêôơưđĂÂÊÔƠƯĐ")
    broken_font_map = (wrong_font_glyphs >= 20 and wrong_font_glyphs / max(len(content), 1) >= 0.01
                       and vietnamese_glyphs * 10 < wrong_font_glyphs)
    replacement_glyphs = content.count("\ufffd") >= max(10, len(content) // 200)
    return (len(content) < 40 or (len(tokens) >= 50 and single_character_ratio > 0.55)
            or broken_font_map or replacement_glyphs)


def image_to_pdf(data: bytes) -> bytes:
    """Wrap a raster image in a one-page PDF accepted by the deployed Modal OCR class."""
    with Image.open(io.BytesIO(data)) as source:
        image = ImageOps.exif_transpose(source)
        if image.width * image.height > 40_000_000:
            raise StudyOCRError("Image exceeds the configured OCR pixel limit")
        output = io.BytesIO()
        image.convert("RGB").save(output, format="PDF", resolution=200.0)
        pdf_bytes = output.getvalue()
    if len(pdf_bytes) > 25 * 1024 * 1024:
        raise StudyOCRError("Converted image exceeds the Modal OCR size limit")
    return pdf_bytes


async def ocr_document(data: bytes, extension: str, provider: ModalStudyOCR) -> StudyOCRResult:
    payload = data if extension.casefold() == "pdf" else await asyncio.to_thread(image_to_pdf, data)
    return await provider.extract_pdf(payload)
