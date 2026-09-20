"""Local document loader. Network URLs are intentionally not fetched here."""
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from app.rag.chunker import normalize_text


MAX_FILE_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class LoadedDocument:
    content: str
    mime_type: str
    page_ranges: tuple[tuple[int, int, int], ...] = ()

    def pages_for(self, start: int, end: int) -> tuple[int | None, int | None]:
        pages = [page for page, page_start, page_end in self.page_ranges
                 if page_start < end and page_end > start]
        return (min(pages), max(pages)) if pages else (None, None)


def load_local_document(path: Path) -> LoadedDocument:
    path = path.resolve(strict=True)
    if not path.is_file():
        raise ValueError("source must be a regular file")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("source file exceeds 25 MiB")
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        mime = "text/markdown" if suffix == ".md" else "text/plain"
        return LoadedDocument(path.read_text(encoding="utf-8-sig"), mime)
    if suffix != ".pdf":
        raise ValueError("only .pdf, .txt, and .md files are supported")

    reader = PdfReader(str(path))
    parts: list[str] = []
    ranges: list[tuple[int, int, int]] = []
    offset = 0
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = normalize_text(page.extract_text() or "")
        if not page_text:
            continue
        if parts:
            parts.append("\n\n")
            offset += 2
        start = offset
        parts.append(page_text)
        offset += len(page_text)
        ranges.append((page_number, start, offset))
    return LoadedDocument("".join(parts), "application/pdf", tuple(ranges))
