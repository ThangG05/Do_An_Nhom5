"""Deterministic, fail-closed checks for claim-level inline citations."""
from dataclasses import dataclass
import re

from app.llm.contracts import ContextBlock, LLMAnswer

_MARKER = re.compile(r"\[([0-9]+(?:\s*,\s*[0-9]+)*)\]")
_CLAIM_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_ANCHOR = re.compile(
    r"(?i:https?://\S+)|(?i:[\w.+-]+@[\w.-]+\.[a-z]{2,})|"
    r"(?<!\w)\d+(?:[.,/\-–]\d+)*(?i:%|đ|vnđ|triệu|tỷ)?(?!\w)|"
    # Codes must contain a digit. Plain abbreviations such as TP or HVNH are
    # named entities, not exact high-risk identifiers.
    r"(?<!\w)(?=[A-ZĐ0-9._/-]*\d)[A-ZĐ]{2,}[A-ZĐ0-9._/-]*(?!\w)",
)


@dataclass(frozen=True, slots=True)
class CitationIssue:
    code: str
    claim: str
    detail: str | None = None


def _canonical_anchor(value: str) -> str:
    normalized = value.rstrip(".,;:)]}").casefold()
    academic_year = re.fullmatch(r"(20\d{2})\s*[/\-–]\s*(20\d{2})", normalized)
    if academic_year:
        return f"academic-year:{academic_year.group(1)}/{academic_year.group(2)}"
    date = re.fullmatch(r"0?(\d{1,2})[/.-]0?(\d{1,2})[/.-](\d{4})", normalized)
    if date:
        return f"date:{int(date.group(1))}/{int(date.group(2))}/{date.group(3)}"
    amount = re.fullmatch(r"(\d[\d.,]*)(%|đ|vnđ|triệu|tỷ)?", normalized)
    if amount:
        digits = re.sub(r"[.,]", "", amount.group(1))
        return f"number:{int(digits)}:{amount.group(2) or ''}"
    return normalized


def _is_substantive(claim: str) -> bool:
    plain = _MARKER.sub("", claim).strip(" -•*\t")
    if not plain or plain.endswith(":"):
        return False
    return len(re.findall(r"\w+", plain, re.UNICODE)) >= 3


def verify_claim_citations(answer: LLMAnswer, contexts: list[ContextBlock],
                           question: str | None = None) -> tuple[CitationIssue, ...]:
    """Require every substantive claim to cite context and validate exact high-risk anchors.

    Semantic entailment remains an evaluation concern; this runtime gate reliably catches
    uncited sentences and invented amounts, dates, codes, emails and URLs without another LLM call.
    """
    if answer.refused:
        return ()
    by_id = {block.id: block for block in contexts}
    issues: list[CitationIssue] = []
    for paragraph in answer.answer.splitlines():
        paragraph_ids = [item for group in _MARKER.findall(paragraph)
                         for item in re.findall(r"[0-9]+", group)]
        for raw_claim in _CLAIM_BOUNDARY.split(paragraph):
            claim = raw_claim.strip()
            if not _is_substantive(claim):
                continue
            ids = [item for group in _MARKER.findall(claim) for item in re.findall(r"[0-9]+", group)]
            ids = ids or paragraph_ids
            if not ids:
                issues.append(CitationIssue("UNCITED_CLAIM", claim[:300]))
                continue
            # Public citations identify source documents. Validate against every
            # retrieved chunk bearing the cited source label, so two chunks from
            # one document do not incorrectly fail exact-anchor verification.
            cited_sources = {
                by_id[context_id].source_key or by_id[context_id].source_label
                for context_id in ids
                if context_id in by_id
            }
            support = " ".join(
                f"{block.source_label} {block.content}"
                for block in contexts
                if block.id in ids or (block.source_key or block.source_label) in cited_sources
            )
            support_anchors = {_canonical_anchor(value) for value in _ANCHOR.findall(support)}
            # A temporal qualifier explicitly supplied by the user may be repeated in the
            # answer. Do not extend this exception to amounts, codes, URLs, or contacts.
            for value in _ANCHOR.findall(question or ""):
                normalized_question_anchor = _canonical_anchor(value)
                if normalized_question_anchor.startswith("academic-year:") or re.fullmatch(
                    r"number:(?:19|20)\d{2}:", normalized_question_anchor
                ):
                    support_anchors.add(normalized_question_anchor)
            plain = _MARKER.sub("", claim)
            for anchor in _ANCHOR.findall(plain):
                normalized = _canonical_anchor(anchor)
                if normalized and normalized not in support_anchors:
                    issues.append(CitationIssue("UNSUPPORTED_ANCHOR", claim[:300], normalized[:100]))
    return tuple(issues)
