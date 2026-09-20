"""Deterministic structure-aware chunking for Vietnamese institutional documents."""
from dataclasses import dataclass
import hashlib
import re
import unicodedata

CHUNKING_VERSION = "structure-v2"
_HEADING = re.compile(
    r"^(?:#{1,6}\s+.+|(?:chương|phần)\s+[0-9ivxlcdm]+\b.*|mục\s+\d+\b.*|"
    r"điều\s+\d+[a-z]?\b.*|(?:[0-9]+(?:\.[0-9]+)*)[.):]\s+\S.*)$", re.IGNORECASE,
)
_TOKEN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


@dataclass(frozen=True, slots=True)
class TextChunk:
    index: int
    content: str
    content_hash: str
    token_count: int
    start_offset: int
    end_offset: int
    section_title: str | None
    heading_path: tuple[str, ...]


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value.replace("\r\n", "\n").replace("\r", "\n"))
    value = "".join(c if c in "\n\t" or unicodedata.category(c) not in {"Cc", "Cf", "Cs"} else " " for c in value)
    value = re.sub(r"[\t\f\v ]+", " ", value.replace("\x00", ""))
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _heading_path(text: str, offset: int) -> tuple[str, ...]:
    hierarchy: dict[int, str] = {}
    for line in text[:offset].splitlines():
        raw = line.strip()
        heading = raw.lstrip("# ")
        if not heading or not _HEADING.match(raw): continue
        lower = heading.casefold()
        level = 1 if lower.startswith(("chương ", "phần ")) else 2 if lower.startswith("mục ") else 3 if lower.startswith("điều ") else 4
        hierarchy[level] = heading[:500]
        hierarchy = {key: value for key, value in hierarchy.items() if key <= level}
    return tuple(hierarchy[key] for key in sorted(hierarchy))


def chunk_text(text: str, size: int = 1800, overlap: int = 250) -> list[TextChunk]:
    if size < 1 or overlap < 0 or overlap >= size: raise ValueError("chunk size must be positive and overlap smaller than size")
    normalized = normalize_text(text)
    if not normalized: raise ValueError("document contains no indexable text")
    chunks, start = [], 0
    while start < len(normalized):
        limit = min(start + size, len(normalized)); end = limit
        if limit < len(normalized):
            boundary = max(normalized.rfind("\n\n", start + size // 2, limit),
                           normalized.rfind(". ", start + size // 2, limit),
                           normalized.rfind("\n", start + size // 2, limit))
            if boundary > start: end = boundary + (2 if normalized[boundary:boundary + 2] == "\n\n" else 1)
        content = normalized[start:end].strip()
        if content:
            path = _heading_path(normalized, start)
            chunks.append(TextChunk(len(chunks), content, hashlib.sha256(content.encode()).hexdigest(),
                                    max(1, len(_TOKEN.findall(content))), start, end,
                                    path[-1] if path else None, path))
        if end >= len(normalized): break
        next_start = max(end - overlap, start + 1)
        whitespace = normalized.find(" ", next_start, min(end, next_start + 80))
        start = whitespace + 1 if whitespace >= 0 else next_start
    return chunks
