"""Provider-neutral, deterministic reranking for hybrid retrieval candidates."""
from dataclasses import dataclass
from datetime import datetime
import re
import unicodedata
from typing import Protocol, TypeVar


class RerankableHit(Protocol):
    chunk_id: str
    title: str
    content: str
    academic_year: str | None
    published_at: str | None
    document_type: str


HitT = TypeVar("HitT", bound=RerankableHit)


@dataclass(frozen=True, slots=True)
class RerankContext:
    query: str
    academic_year: str | None = None
    latest: bool = False
    document_type: str | None = None


_STOPWORDS = {
    "ai", "gì", "là", "và", "của", "tại", "cho", "về", "một", "những",
    "thông", "tin", "học", "viện", "ngân", "hàng", "được", "có", "không",
    "thế", "nào", "như", "nội", "dung", "tổ", "chức", "theo", "tài", "liệu",
    "chính", "thức", "những", "gồm", "bao",
}


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"\w+", value.casefold(), re.UNICODE)
            if len(token) >= 2 and token not in _STOPWORDS}


def _fold(value: str) -> str:
    """Accent-insensitive matching for Vietnamese titles and ASCII PDF filenames."""
    decomposed = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return "".join(character for character in decomposed
                   if unicodedata.category(character) != "Mn")


def _timestamp(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


class HeuristicReranker:
    """Reranks exact entities/codes safely; can later be replaced by a cross-encoder."""

    def rerank(self, hits: list[HitT], context: RerankContext,
               fusion_scores: dict[str, float]) -> list[HitT]:
        query_terms = _tokens(context.query)
        normalized_query = context.query.casefold()
        quantitative = any(term in normalized_query for term in (
            "mức thu", "bao nhiêu", "chi phí", "đơn giá", "tỷ lệ",
        ))
        tuition_query = "hoc phi" in _fold(normalized_query)
        scholarship_query = "hoc bong" in _fold(normalized_query)
        procedural = any(term in normalized_query for term in (
            "như thế nào", "cách", "hướng dẫn", "đăng nhập", "truy cập", "thủ tục",
        ))

        def score(hit: HitT) -> tuple[float, float]:
            title_terms = _tokens(hit.title)
            content_terms = _tokens(hit.content)
            denominator = max(len(query_terms), 1)
            title_coverage = len(query_terms & title_terms) / denominator
            content_coverage = len(query_terms & content_terms) / denominator
            exact_title = 1.0 if context.query.casefold().strip(" ?.") in hit.title.casefold() else 0.0
            # Long tokens and codes usually identify a person, system, decision or event. Give
            # them enough weight to beat repeated site-wide navigation vocabulary.
            distinctive = {term for term in query_terms if len(term) >= 7 or any(ch.isdigit() for ch in term)}
            distinctive_title = len(distinctive & title_terms) / max(len(distinctive), 1)
            year_match = 1.0 if context.academic_year and hit.academic_year == context.academic_year else 0.0
            type_match = 1.0 if context.document_type and hit.document_type == context.document_type else 0.0
            numeric_evidence = 1.0 if quantitative and re.search(
                r"\d[\d.,]*\s*(?:đồng|vnđ|%|/\s*tín\s*chỉ)", hit.content, re.IGNORECASE
            ) else 0.0
            procedural_evidence = 1.0 if procedural and re.search(
                r"(?:bước\s*\d+|đăng nhập|tài khoản|my\s+courses|thời khóa biểu)",
                hit.content, re.IGNORECASE,
            ) else 0.0
            folded_title = _fold(hit.title)
            tuition_title = 1.0 if tuition_query and "hoc phi" in folded_title else 0.0
            scholarship_title = 1.0 if scholarship_query and "hoc bong" in folded_title else 0.0
            scholarship_content = 1.0 if scholarship_query and "hoc bong" in _fold(hit.content) else 0.0
            unrelated_fee_title = 1.0 if tuition_query and "dich vu" in folded_title \
                and "hoc phi" not in folded_title else 0.0
            relevance = (fusion_scores.get(hit.chunk_id, 0.0) * 20.0
                         + 0.55 * title_coverage + 0.15 * content_coverage
                         + 0.25 * exact_title + 0.20 * year_match + 0.08 * type_match
                         + 0.45 * distinctive_title + 0.45 * numeric_evidence
                         + 0.35 * procedural_evidence + 0.55 * tuition_title
                         + 0.85 * scholarship_title + 0.20 * scholarship_content
                         - 0.40 * unrelated_fee_title)
            freshness = _timestamp(hit.published_at) if context.latest else 0.0
            # An explicit latest/current request is temporal first: an older notice
            # must not outrank the newest applicable version merely because its title
            # repeats more query terms. Other queries remain relevance first.
            return (freshness, relevance) if context.latest else (relevance, freshness)

        return sorted(hits, key=score, reverse=True)
