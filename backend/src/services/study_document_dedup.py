"""Exact and text near-duplicate fingerprints for study-library uploads."""

from __future__ import annotations

import hashlib
import io
import logging
import re
import unicodedata
import zipfile
import asyncio
from collections import Counter
from xml.etree import ElementTree

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader
from src.config import settings
from src.services.study_document_ocr import ModalStudyOCR, ocr_document, pdf_needs_ocr

SIMHASH_BITS = 64
SIMHASH_HAMMING_LIMIT = 10
SIMHASH_VERSION = 2
logger = logging.getLogger(__name__)
MIN_SIMHASH_TOKENS = 20
MAX_EXTRACTED_CHARS = 1_000_000
MAX_ARCHIVE_ENTRIES = 2_000
MAX_ARCHIVE_EXPANDED_BYTES = 100 * 1024 * 1024


def normalize_document_text(value: str) -> str:
    """Normalize layout noise while retaining Vietnamese diacritics and word order."""
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def compute_simhash64(value: str) -> str | None:
    """Return a stable 64-bit SimHash over normalized 3-word shingles.

    Repeated shingles are capped at weight 3 so copied headers and repeated table
    labels do not dominate the document fingerprint. Very short text is skipped
    because it is not discriminative enough for near-duplicate decisions.
    """
    normalized = normalize_document_text(value)
    tokens = normalized.split()
    if len(tokens) < MIN_SIMHASH_TOKENS:
        return None

    shingles = [" ".join(tokens[index:index + 3]) for index in range(len(tokens) - 2)]
    frequencies = Counter(shingles)
    accumulators = [0] * SIMHASH_BITS
    for shingle, frequency in frequencies.items():
        weight = min(frequency, 3)
        digest = int.from_bytes(
            hashlib.blake2b(shingle.encode("utf-8"), digest_size=8).digest(),
            byteorder="big",
            signed=False,
        )
        for bit in range(SIMHASH_BITS):
            accumulators[bit] += weight if (digest >> bit) & 1 else -weight

    signature = sum(1 << bit for bit, value in enumerate(accumulators) if value >= 0)
    return f"{signature:016x}"


def hamming_distance(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def simhash_bands(signature: str) -> list[tuple[int, int]]:
    """Split 64 bits into 11 disjoint bands for lossless radius-10 candidate lookup.

    By the pigeonhole principle, any two signatures differing in at most ten
    bits must have at least one identical band. Candidate matches are still
    verified with their full Hamming distance before being returned.
    """
    value = int(signature, 16)
    bands: list[tuple[int, int]] = []
    offset = 0
    for band_index in range(11):
        width = 6 if band_index < 9 else 5
        bands.append((band_index, (value >> offset) & ((1 << width) - 1)))
        offset += width
    return bands


async def extract_document_text_for_fingerprint(
    data: bytes,
    extension: str,
    ocr_provider: ModalStudyOCR | None = None,
) -> tuple[str, str, ModalStudyOCR | None]:
    """Extract native text and OCR images/scanned PDFs using the RAG Modal OCR class."""
    extension = extension.lower().lstrip(".")
    text_value, status = extract_text(data, extension)
    needs_ocr = extension in {"jpg", "jpeg", "png", "webp"} or (
        extension == "pdf" and await asyncio.to_thread(pdf_needs_ocr, data)
    )
    if not needs_ocr:
        return text_value, status, ocr_provider
    if not settings.STUDY_MODERATION_OCR_ENABLED:
        return "", "OCR_UNAVAILABLE", ocr_provider
    try:
        if ocr_provider is None:
            ocr_provider = ModalStudyOCR()
        result = await ocr_document(data, extension, ocr_provider)
        return result.content[:MAX_EXTRACTED_CHARS], "OCR_SCANNED", ocr_provider
    except Exception as exc:
        logger.warning("study_document_duplicate_ocr_failed", extra={
            "extension": extension, "error_type": type(exc).__name__,
        })
        return "", "OCR_UNAVAILABLE", ocr_provider


def extract_text(data: bytes, extension: str) -> tuple[str, str]:
    """Extract text for supported formats; return text plus a scan-status label.

    Scanned PDFs, images, and legacy binary Office files do not have reliable
    machine-readable text here and are marked UNSUPPORTED/NO_TEXT rather than
    being reported as a clean near-duplicate scan. Their SHA-256 check remains
    available.
    """
    extension = extension.lower().lstrip(".")
    parts: list[str] = []
    try:
        if extension == "pdf":
            reader = PdfReader(io.BytesIO(data), strict=False)
            if getattr(reader, "is_encrypted", False):
                return "", "UNSUPPORTED"
            for page in reader.pages[:200]:
                parts.append(page.extract_text() or "")
                if sum(map(len, parts)) >= MAX_EXTRACTED_CHARS:
                    break
        elif extension == "docx":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if len(archive.infolist()) > MAX_ARCHIVE_ENTRIES or sum(
                    item.file_size for item in archive.infolist()
                ) > MAX_ARCHIVE_EXPANDED_BYTES:
                    return "", "UNSUPPORTED"
            document = Document(io.BytesIO(data))
            parts.extend(paragraph.text for paragraph in document.paragraphs)
            for table in document.tables[:100]:
                for row in table.rows[:1_000]:
                    parts.append(" | ".join(cell.text for cell in row.cells[:50]))
        elif extension == "xlsx":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_ARCHIVE_ENTRIES or sum(
                    item.file_size for item in entries
                ) > MAX_ARCHIVE_EXPANDED_BYTES:
                    return "", "UNSUPPORTED"
            workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            try:
                for sheet in workbook.worksheets[:30]:
                    parts.append(sheet.title)
                    for row in sheet.iter_rows(max_row=1_000, max_col=50, values_only=True):
                        parts.append(" | ".join(str(item) for item in row if item is not None))
                        if sum(map(len, parts)) >= MAX_EXTRACTED_CHARS:
                            break
            finally:
                workbook.close()
        elif extension == "pptx":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_ARCHIVE_ENTRIES or sum(
                    item.file_size for item in entries
                ) > MAX_ARCHIVE_EXPANDED_BYTES:
                    return "", "UNSUPPORTED"
                slides: list[tuple[int, str]] = []
                for item in entries:
                    match = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", item.filename)
                    if match:
                        slides.append((int(match.group(1)), item.filename))
                for _, name in sorted(slides)[:200]:
                    root = ElementTree.fromstring(archive.read(name))
                    parts.append(" ".join(
                        node.text or "" for node in root.iter()
                        if node.tag.endswith("}t")
                    ))
        else:
            return "", "UNSUPPORTED"
    except Exception:
        return "", "UNSUPPORTED"

    text = "\n".join(parts)[:MAX_EXTRACTED_CHARS]
    normalized = normalize_document_text(text)
    if len(normalized.split()) < MIN_SIMHASH_TOKENS:
        return "", "NO_TEXT"
    return text, "SCANNED"
