"""OCR provider abstraction for scanned source documents."""
import asyncio
from dataclasses import dataclass
from typing import Protocol

from app.core.config import get_settings


class OCRError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OCRResult:
    content: str
    page_count: int
    page_ranges: list[tuple[int, int, int]]
    engine: str


class OCRProvider(Protocol):
    async def extract_pdf(self, body: bytes) -> OCRResult: ...


class ModalOCRProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        try:
            import modal
            self.remote = modal.Cls.from_name(
                self.settings.modal_ocr_app, self.settings.modal_ocr_class
            )()
        except Exception as exc:
            raise OCRError("Modal OCR provider is not configured") from exc

    async def extract_pdf(self, body: bytes) -> OCRResult:
        result = None
        for attempt in range(self.settings.ocr_max_retries + 1):
            try:
                async with asyncio.timeout(self.settings.ocr_timeout_seconds):
                    result = await asyncio.to_thread(
                        self.remote.extract.remote, body, self.settings.ocr_max_pages
                    )
                break
            except Exception as exc:
                if attempt == self.settings.ocr_max_retries:
                    raise OCRError("Modal OCR provider unavailable") from exc
                await asyncio.sleep(2 ** attempt)
        if not isinstance(result, dict) or len(str(result.get("content", "")).strip()) < 40:
            raise OCRError("OCR provider returned invalid content")
        ranges = [tuple(map(int, row)) for row in result.get("page_ranges", []) if len(row) == 3]
        return OCRResult(
            content=str(result["content"]),
            page_count=int(result.get("page_count", 0)),
            page_ranges=ranges,
            engine=str(result.get("engine", "unknown")),
        )


def get_ocr_provider() -> OCRProvider:
    if get_settings().ocr_provider.casefold() == "modal":
        return ModalOCRProvider()
    raise OCRError("unsupported OCR provider")
