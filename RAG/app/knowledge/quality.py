"""Format-neutral extraction quality checks run before publication/indexing."""
from dataclasses import dataclass
from collections import Counter
import re

from app.knowledge.crawler.extractors import ExtractedDocument


@dataclass(frozen=True, slots=True)
class ExtractionQuality:
    score: float
    accepted: bool
    code: str | None
    metrics: dict[str, float | int]


def assess_extraction(document: ExtractedDocument, *, allow_short: bool = False) -> ExtractionQuality:
    text = document.content.strip()
    characters = len(text)
    tokens = re.findall(r"\w+", text, flags=re.UNICODE)
    replacement_ratio = text.count("�") / max(characters, 1)
    alphanumeric_ratio = sum(ch.isalnum() for ch in text) / max(characters, 1)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    repeated_lines = sum(count - 1 for count in Counter(lines).values() if count > 1)
    repetition_ratio = repeated_lines / max(len(lines), 1)
    score = 1.0
    if characters < 120: score -= 0.35
    if alphanumeric_ratio < 0.45: score -= 0.30
    if replacement_ratio > 0.01: score -= 0.30
    if repetition_ratio > 0.50: score -= 0.25
    score = round(max(0.0, score), 3)
    accepted = allow_short or (characters >= 40 and score >= 0.45)
    code = None if accepted else "LOW_EXTRACTION_QUALITY"
    return ExtractionQuality(score, accepted, code, {
        "characters": characters, "tokens": len(tokens), "alphanumeric_ratio": round(alphanumeric_ratio, 3),
        "replacement_ratio": round(replacement_ratio, 3), "repetition_ratio": round(repetition_ratio, 3),
        "section_count": len(document.sections), "table_count": len(document.tables),
    })
