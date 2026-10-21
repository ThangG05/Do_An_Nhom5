"""Secure, temporal and access-aware hybrid retrieval without answer generation."""
import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import logging
import re
from time import perf_counter
from uuid import UUID

from qdrant_client import models
from sqlalchemy import Float, String, and_, cast, func, literal_column, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.knowledge.crawler.metadata import infer_academic_year, infer_document_type
from app.knowledge.crawler.security import canonicalize_url, is_in_scope
from app.llm.security import InputKind, PromptGuard
from app.models.enums import AIDocumentStatus, AIDocumentType, AIVisibility
from app.models.crawler import AISource
from app.models.rag import AIDocument, AIDocumentChunk, AIDocumentVersion
from app.rag.embeddings import EmbeddingProvider
from app.rag.query_cache import QueryEmbeddingCache, SharedQueryEmbeddingCache
from app.rag.reranker import HeuristicReranker, RerankContext
from app.services.qdrant import get_qdrant_client, qdrant_retry
from app.services.redis import get_redis_client

logger = logging.getLogger(__name__)
_query_cache: QueryEmbeddingCache | None = None


def _get_query_cache() -> QueryEmbeddingCache:
    global _query_cache
    settings = get_settings()
    if _query_cache is None or (_query_cache.max_entries, _query_cache.ttl_seconds) != (
        settings.retrieval_query_cache_entries, settings.retrieval_query_cache_ttl_seconds
    ):
        _query_cache = QueryEmbeddingCache(settings.retrieval_query_cache_entries,
                                           settings.retrieval_query_cache_ttl_seconds)
    return _query_cache


@dataclass(frozen=True, slots=True)
class AccessScope:
    authenticated: bool = False
    group_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class QueryIntent:
    normalized_query: str
    academic_year: str | None
    document_type: AIDocumentType | None
    latest: bool
    historical: bool


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    point_id: str
    score: float
    chunk_id: str
    document_id: str
    document_version_id: str
    title: str
    content: str
    source_url: str | None
    document_type: str
    academic_year: str | None
    published_at: str | None
    page_start: int | None
    page_end: int | None
    section_title: str | None


_LEXICAL_STOPWORDS = {
    "ai", "gì", "là", "và", "của", "tại", "cho", "về", "một", "những",
    "thông", "tin", "học", "viện", "ngân", "hàng", "được", "có", "không",
    "thế", "nào", "như", "nội", "dung", "tổ", "chức", "theo", "tài", "liệu",
    "chính", "thức", "những", "gồm", "bao",
}


def _terms(value: str) -> set[str]:
    return {token for token in re.findall(r"\w+", value.casefold(), flags=re.UNICODE)
            if len(token) >= 2 and token not in _LEXICAL_STOPWORDS}


def _lexical_scores(query: str, payload: dict) -> tuple[float, float]:
    query_terms = _terms(query)
    if not query_terms:
        return 0.0, 0.0
    title_terms = _terms(str(payload.get("title", "")))
    content_terms = _terms(str(payload.get("content", "")))
    return (len(query_terms & title_terms) / len(query_terms),
            len(query_terms & content_terms) / len(query_terms))


def _rrf(vector_ids: list[str], lexical_ids: list[str], k: int = 60) -> dict[str, float]:
    """Fuse rankings without assuming vector and PostgreSQL scores share a scale."""
    scores: dict[str, float] = {}
    for ranking in (vector_ids, lexical_ids):
        for rank, chunk_id in enumerate(ranking, 1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


def analyze_query(query: str) -> QueryIntent:
    settings = get_settings()
    guarded = PromptGuard(settings.llm_max_input_chars, settings.llm_max_context_chars).inspect(query, InputKind.USER)
    normalized = re.sub(r"\s+", " ", guarded.value).strip()
    inferred_type = infer_document_type(normalized)
    document_type = inferred_type if inferred_type != AIDocumentType.OTHER else None
    latest = bool(re.search(
        r"\b(mới nhất|gần nhất|hiện tại|mới đây|hôm nay|ngày mai)\b",
        normalized, re.IGNORECASE,
    ))
    academic_year = infer_academic_year(normalized)
    historical = bool(academic_year or re.search(
        r"\b(phiên bản cũ|bản cũ|quy định cũ|trước đây|trước kia|lịch sử|so sánh|thay đổi qua)\b",
        normalized, re.IGNORECASE,
    ))
    return QueryIntent(normalized, academic_year, document_type, latest, historical)


def _per_document_limit(query: str, configured: int) -> int:
    """Allow supporting table/procedure chunks while keeping source diversity."""
    if "học bổng" in query.casefold() and any(
        phrase in query.casefold() for phrase in ("điều kiện", "tiêu chuẩn", "tiêu chí")
    ):
        return max(configured, 4)
    expanded = bool(re.search(
        r"\b(mức thu|học phí|bao nhiêu|hướng dẫn|đăng nhập|truy cập|thủ tục|"
        r"nội dung|trải nghiệm)\b", query, re.IGNORECASE,
    ))
    return max(configured, 3) if expanded else configured


def build_filter(intent: QueryIntent, access: AccessScope) -> models.Filter:
    must: list = []
    if intent.academic_year:
        must.append(models.FieldCondition(key="academic_year", match=models.MatchValue(value=intent.academic_year)))
    elif not intent.historical:
        must.append(models.FieldCondition(key="is_current", match=models.MatchValue(value=True)))
    # Keep inferred type soft: a page can be ANNOUNCEMENT while its attachment is DECISION.
    # Hard filtering here would hide otherwise relevant newly crawled documents.
    access_conditions: list = [models.FieldCondition(key="visibility", match=models.MatchValue(value="PUBLIC"))]
    if access.authenticated:
        access_conditions.append(models.FieldCondition(key="visibility", match=models.MatchValue(value="AUTHENTICATED")))
    if access.group_ids:
        access_conditions.append(models.Filter(must=[
            models.FieldCondition(key="visibility", match=models.MatchValue(value="GROUP")),
            models.FieldCondition(key="group_id", match=models.MatchAny(any=[str(item) for item in access.group_ids])),
        ]))
    return models.Filter(must=must, min_should=models.MinShould(conditions=access_conditions, min_count=1))


def _published_timestamp(value: str | None) -> float:
    if not value:
        return 0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0


def _authorized_chunk(chunk: AIDocumentChunk, version: AIDocumentVersion,
                      document: AIDocument, intent: QueryIntent, access: AccessScope,
                      source: AISource | None = None) -> bool:
    """PostgreSQL is authoritative; vector payloads are only candidate pointers."""
    if document.deleted_at is not None or (document.metadata_ or {}).get("retrieval_excluded") is True:
        return False
    if (version.metadata_ or {}).get("security_review") == "QUARANTINED":
        return False
    if version.source_url:
        try:
            canonicalize_url(version.source_url)
        except ValueError:
            return False
    source_id = (document.metadata_ or {}).get("source_id")
    if source_id:
        if source is None or not source.enabled or str(source.id) != str(source_id) or not version.source_url:
            return False
        try:
            if not is_in_scope(canonicalize_url(version.source_url), source.allowed_domains,
                               source.allowed_path_prefixes):
                return False
        except ValueError:
            return False
    if version.document_id != document.id or chunk.document_version_id != version.id:
        return False
    if document.visibility == AIVisibility.PRIVATE:
        return False
    if document.visibility == AIVisibility.AUTHENTICATED and not access.authenticated:
        return False
    if document.visibility == AIVisibility.GROUP and document.group_id not in access.group_ids:
        return False
    if document.visibility not in {AIVisibility.PUBLIC, AIVisibility.AUTHENTICATED, AIVisibility.GROUP}:
        return False
    if intent.academic_year:
        if ((version.metadata_ or {}).get("academic_year") or document.academic_year) != intent.academic_year:
            return False
    elif not intent.historical and document.current_version_id != version.id:
        return False
    if not intent.historical:
        now = datetime.now(UTC)
        if document.effective_from and document.effective_from > now:
            return False
        if document.effective_to and document.effective_to < now:
            return False
    if version.status not in ({AIDocumentStatus.INDEXED, AIDocumentStatus.ARCHIVED}
                              if intent.historical else {AIDocumentStatus.INDEXED}):
        return False
    return hashlib.sha256(chunk.content.encode("utf-8")).hexdigest() == chunk.content_hash


class RetrievalService:
    def __init__(self, embedder: EmbeddingProvider, session: AsyncSession | None = None,
                 reranker: HeuristicReranker | None = None) -> None:
        self.settings = get_settings()
        self.embedder = embedder
        self.session = session
        self.client = get_qdrant_client()
        if reranker is None and self.settings.retrieval_reranker != "heuristic":
            raise ValueError(f"unsupported reranker: {self.settings.retrieval_reranker}")
        self.reranker = reranker or HeuristicReranker()

    async def _lexical_search(self, intent: QueryIntent, access: AccessScope) -> list[RetrievalHit]:
        if self.session is None or not self.settings.retrieval_hybrid_enabled:
            return []
        search_vector = func.to_tsvector(
            literal_column("'simple'::regconfig"),
            func.coalesce(AIDocumentChunk.content, literal_column("''")),
        )
        # AND prevents common institutional terms from crowding exact entities/codes out of the
        # bounded candidate set. Semantic retrieval remains the high-recall fallback.
        lexical_query = " ".join(sorted(_terms(intent.normalized_query))) or intent.normalized_query
        search_query = func.plainto_tsquery("simple", lexical_query)
        rank = cast(func.ts_rank_cd(search_vector, search_query), Float).label("lexical_rank")
        visibility = [AIDocument.visibility == AIVisibility.PUBLIC]
        if access.authenticated:
            visibility.append(AIDocument.visibility == AIVisibility.AUTHENTICATED)
        if access.group_ids:
            visibility.append(and_(AIDocument.visibility == AIVisibility.GROUP,
                                   AIDocument.group_id.in_(access.group_ids)))
        predicates = [AIDocument.deleted_at.is_(None), or_(*visibility),
                      search_vector.op("@@")(search_query),
                      AIDocumentVersion.status.in_((AIDocumentStatus.INDEXED, AIDocumentStatus.ARCHIVED)
                                                    if intent.historical else (AIDocumentStatus.INDEXED,)),
                      func.coalesce(AIDocument.metadata_["retrieval_excluded"].astext, "false") != "true",
                      func.coalesce(AIDocumentVersion.metadata_["security_review"].astext, "") != "QUARANTINED"]
        if intent.academic_year:
            predicates.append(func.coalesce(
                AIDocumentVersion.metadata_["academic_year"].astext,
                AIDocument.academic_year,
            ) == intent.academic_year)
        elif not intent.historical:
            predicates.append(AIDocument.current_version_id == AIDocumentVersion.id)
        statement = (select(AIDocumentChunk, AIDocumentVersion, AIDocument, AISource, rank)
                     .join(AIDocumentVersion, AIDocumentVersion.id == AIDocumentChunk.document_version_id)
                     .join(AIDocument, AIDocument.id == AIDocumentVersion.document_id)
                     .outerjoin(AISource, cast(AISource.id, String) == AIDocument.metadata_["source_id"].astext)
                     .where(*predicates).order_by(rank.desc(), AIDocument.published_at.desc().nullslast())
                     .limit(self.settings.retrieval_lexical_candidate_k))
        try:
            # Isolate an optional branch so a timeout cannot poison the conversation transaction.
            async with asyncio.timeout(self.settings.retrieval_lexical_timeout_seconds):
                async with AsyncSessionLocal() as lexical_session:
                    rows = (await lexical_session.execute(statement)).all()
        except (SQLAlchemyError, TimeoutError):
            logger.warning("lexical retrieval unavailable; using vector results only")
            return []
        return [RetrievalHit(str(chunk.qdrant_point_id), min(float(lexical_rank), 1.0), str(chunk.id),
                str(document.id), str(version.id), document.title, chunk.content, version.source_url,
                document.document_type.value,
                (version.metadata_ or {}).get("academic_year") or document.academic_year,
                (version.metadata_ or {}).get("published_at") or (
                    document.published_at.isoformat() if document.published_at else None),
                chunk.page_start, chunk.page_end, chunk.section_title)
                for chunk, version, document, source, lexical_rank in rows
                if _authorized_chunk(chunk, version, document, intent, access, source)]

    async def _verified_vector_hits(self, points: list, intent: QueryIntent,
                                    access: AccessScope) -> list[RetrievalHit]:
        candidates: dict[UUID, object] = {}
        for point in points:
            try:
                chunk_id = UUID(str((point.payload or {}).get("chunk_id")))
            except (TypeError, ValueError, AttributeError):
                continue
            candidates[chunk_id] = point
        if not candidates:
            return []
        statement = (select(AIDocumentChunk, AIDocumentVersion, AIDocument, AISource)
                     .join(AIDocumentVersion, AIDocumentVersion.id == AIDocumentChunk.document_version_id)
                     .join(AIDocument, AIDocument.id == AIDocumentVersion.document_id)
                     .outerjoin(AISource, cast(AISource.id, String) == AIDocument.metadata_["source_id"].astext)
                     .where(AIDocumentChunk.id.in_(candidates)))
        if self.session is None:
            async with AsyncSessionLocal() as session:
                rows = (await session.execute(statement)).all()
        else:
            rows = (await self.session.execute(statement)).all()
        verified = {}
        for chunk, version, document, source in rows:
            point = candidates[chunk.id]
            payload = point.payload or {}
            if (str(point.id) != str(chunk.qdrant_point_id)
                    or payload.get("document_id") != str(document.id)
                    or payload.get("document_version_id") != str(version.id)
                    or payload.get("content_hash") != chunk.content_hash
                    or not _authorized_chunk(chunk, version, document, intent, access, source)):
                continue
            metadata = version.metadata_ or {}
            verified[chunk.id] = RetrievalHit(
                str(chunk.qdrant_point_id), float(point.score), str(chunk.id),
                str(document.id), str(version.id), document.title, chunk.content,
                version.source_url, document.document_type.value,
                metadata.get("academic_year") or document.academic_year,
                metadata.get("published_at") or (
                    document.published_at.isoformat() if document.published_at else None),
                chunk.page_start, chunk.page_end, chunk.section_title,
            )
        if len(verified) != len(candidates):
            logger.warning("rag_vector_candidates_rejected", extra={
                "candidate_count": len(candidates), "rejected_count": len(candidates) - len(verified),
            })
        return [verified[chunk_id] for chunk_id in candidates if chunk_id in verified]

    async def search(self, query: str, access: AccessScope | None = None,
                     top_k: int | None = None, score_threshold: float | None = None) -> list[RetrievalHit]:
        intent = analyze_query(query)
        scope = access or AccessScope()
        configured_threshold = self.settings.retrieval_score_threshold
        query_threshold = min(configured_threshold, self.settings.retrieval_candidate_score_threshold) \
            if score_threshold is None else score_threshold

        async def vector_search():
            embedding_started = perf_counter()
            async def embed_with_shared_cache() -> list[float]:
                if not self.settings.retrieval_shared_embedding_cache_enabled:
                    return await self.embedder.embed_query(intent.normalized_query)
                shared = SharedQueryEmbeddingCache(
                    get_redis_client(), self.settings.embedding_dimensions,
                    self.settings.retrieval_query_cache_ttl_seconds,
                    self.settings.retrieval_shared_embedding_cache_timeout_seconds,
                )
                return await shared.get_or_embed(
                    self.settings.embedding_model, intent.normalized_query,
                    lambda: self.embedder.embed_query(intent.normalized_query),
                )
            vector = await _get_query_cache().get_or_embed(
                self.settings.embedding_model, intent.normalized_query,
                embed_with_shared_cache)
            embedding_ms = round((perf_counter() - embedding_started) * 1000)
            qdrant_started = perf_counter()
            response = await qdrant_retry(lambda: self.client.query_points(
                collection_name=self.settings.qdrant_collection, query=vector,
                query_filter=build_filter(intent, scope), limit=self.settings.retrieval_candidate_k,
                with_payload=True, with_vectors=False, score_threshold=query_threshold,
            ))
            return response, embedding_ms, round((perf_counter() - qdrant_started) * 1000)

        async def lexical_search():
            started = perf_counter()
            hits = await self._lexical_search(intent, scope)
            return hits, round((perf_counter() - started) * 1000)

        # PostgreSQL full-text search does not depend on the remote embedding call.
        # Running both branches together removes their additive network latency.
        retrieval_started = perf_counter()
        (response, embedding_ms, qdrant_ms), (lexical_hits, lexical_ms) = await asyncio.gather(
            vector_search(), lexical_search()
        )
        verification_started = perf_counter()
        vector_hits = await self._verified_vector_hits(response.points, intent, scope)
        verification_ms = round((perf_counter() - verification_started) * 1000)

        by_id = {hit.chunk_id: hit for hit in vector_hits}
        by_id.update({hit.chunk_id: hit for hit in lexical_hits})
        fused = _rrf([hit.chunk_id for hit in vector_hits], [hit.chunk_id for hit in lexical_hits])
        vector_scores = {hit.chunk_id: hit.score for hit in vector_hits}
        ordered = self.reranker.rerank(
            list(by_id.values()),
            RerankContext(intent.normalized_query, intent.academic_year, intent.latest,
                          intent.document_type.value if intent.document_type else None),
            fused,
        )

        lexical_ids = {hit.chunk_id for hit in lexical_hits}
        per_document: dict[str, int] = {}
        per_document_limit = _per_document_limit(intent.normalized_query,
                                                 self.settings.retrieval_max_chunks_per_document)
        hits: list[RetrievalHit] = []
        for hit in ordered:
            if score_threshold is None and hit.chunk_id not in lexical_ids \
                    and vector_scores.get(hit.chunk_id, 0) < configured_threshold:
                continue
            if per_document.get(hit.document_id, 0) >= per_document_limit:
                continue
            per_document[hit.document_id] = per_document.get(hit.document_id, 0) + 1
            if hit.chunk_id in vector_scores:
                hit = RetrievalHit(hit.point_id, vector_scores[hit.chunk_id], hit.chunk_id, hit.document_id,
                                   hit.document_version_id, hit.title, hit.content, hit.source_url,
                                   hit.document_type, hit.academic_year, hit.published_at, hit.page_start,
                                   hit.page_end, hit.section_title)
            hits.append(hit)
            if len(hits) >= (top_k or self.settings.retrieval_top_k):
                break
        logger.info("rag_retrieval_completed", extra={
            "embedding_ms": embedding_ms, "qdrant_ms": qdrant_ms,
            "lexical_ms": lexical_ms, "verification_ms": verification_ms,
            "retrieval_ms": round((perf_counter() - retrieval_started) * 1000),
            "vector_candidates": len(response.points), "lexical_candidates": len(lexical_hits),
        })
        return hits
