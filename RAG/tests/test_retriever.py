import asyncio
from datetime import UTC, datetime, timedelta
import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
import pytest
from app.models.enums import AIDocumentStatus, AIDocumentType, AIVisibility
from app.rag.retriever import (AccessScope, RetrievalService, _lexical_scores, _per_document_limit,
                               _rrf, _authorized_chunk, analyze_query, build_filter)


def test_query_intent_extracts_year_type_and_latest() -> None:
    intent = analyze_query("Thông báo mới nhất năm học 2026–2027")
    assert intent.academic_year == "2026/2027"
    assert intent.document_type == AIDocumentType.ANNOUNCEMENT
    assert intent.latest is True


def test_query_intent_extracts_academic_year_across_century_boundary() -> None:
    assert analyze_query("Quy chế năm học 2099/2100").academic_year == "2099/2100"


def test_query_without_year_requires_current_public_data() -> None:
    query_filter = build_filter(analyze_query("Chuẩn đầu ra VSTEP"), AccessScope())
    dumped = query_filter.model_dump(mode="json", exclude_none=True)
    assert dumped["must"][0]["key"] == "is_current"
    assert dumped["min_should"]["conditions"][0]["match"]["value"] == "PUBLIC"


def test_historical_query_without_year_allows_archived_versions() -> None:
    intent = analyze_query("So sánh quy định cũ và quy định hiện tại")
    assert intent.historical is True
    dumped = build_filter(intent, AccessScope()).model_dump(mode="json", exclude_none=True)
    assert "is_current" not in {condition.get("key") for condition in dumped.get("must", [])}


def test_plain_query_is_not_treated_as_historical() -> None:
    intent = analyze_query("Quy định học phí là gì?")
    assert intent.historical is False


def test_group_access_adds_scoped_group_condition() -> None:
    query_filter = build_filter(analyze_query("Quy chế năm học 2024/2025"),
                                AccessScope(authenticated=True, group_ids=(uuid4(),)))
    dumped = query_filter.model_dump(mode="json", exclude_none=True)
    assert dumped["must"][0]["key"] == "academic_year"
    assert len(dumped["min_should"]["conditions"]) == 3


def test_inferred_document_type_is_not_a_hard_filter() -> None:
    query_filter = build_filter(analyze_query("Quy định học phí năm học 2025/2026"), AccessScope())
    dumped = query_filter.model_dump(mode="json", exclude_none=True)
    assert "document_type" not in {condition.get("key") for condition in dumped["must"]}


def test_lexical_title_match_prioritizes_named_entity() -> None:
    title_score, content_score = _lexical_scores(
        "Giảng viên Triệu Thu Hương là ai?",
        {"title": "Giảng viên | Triệu Thu Hương", "content": "Hồ sơ chính thức"},
    )
    assert title_score == 1
    assert content_score == 0


def test_rrf_rewards_chunks_found_by_both_retrievers() -> None:
    scores = _rrf(["semantic", "both"], ["both", "lexical"])
    assert scores["both"] > scores["semantic"]
    assert scores["both"] > scores["lexical"]


def test_structured_question_allows_three_chunks_from_one_document() -> None:
    assert _per_document_limit("Mức thu học phí là bao nhiêu?", 2) == 3
    assert _per_document_limit("Giảng viên Triệu Thu Hương là ai?", 2) == 2
    assert _per_document_limit("Điều kiện xét học bổng là gì?", 2) == 4


@pytest.mark.asyncio
async def test_slow_optional_lexical_branch_times_out_without_failing_retrieval(monkeypatch) -> None:
    class SlowSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def execute(self, *_):
            await asyncio.sleep(1)

    monkeypatch.setattr("app.rag.retriever.AsyncSessionLocal", SlowSession)
    service = RetrievalService.__new__(RetrievalService)
    service.session = object()
    service.settings = SimpleNamespace(retrieval_hybrid_enabled=True,
                                       retrieval_lexical_candidate_k=20,
                                       retrieval_lexical_timeout_seconds=0.01)
    assert await service._lexical_search(analyze_query("Chuẩn đầu ra VSTEP"), AccessScope()) == []


def _knowledge_row():
    document_id, version_id, chunk_id, point_id = (uuid4() for _ in range(4))
    content = "Điều kiện học bổng được quy định trong văn bản chính thức."
    document = SimpleNamespace(
        id=document_id, title="Quy định học bổng", document_type=AIDocumentType.REGULATION,
        academic_year=None, published_at=None, effective_from=None, effective_to=None,
        visibility=AIVisibility.PUBLIC, group_id=None, current_version_id=version_id,
        deleted_at=None, metadata_={},
    )
    version = SimpleNamespace(
        id=version_id, document_id=document_id, source_url="https://hvnh.edu.vn/quy-dinh.pdf",
        status=AIDocumentStatus.INDEXED, metadata_={},
    )
    chunk = SimpleNamespace(
        id=chunk_id, document_version_id=version_id, qdrant_point_id=point_id,
        content=content, content_hash=hashlib.sha256(content.encode()).hexdigest(),
        page_start=1, page_end=1, section_title=None,
    )
    return chunk, version, document


@pytest.mark.asyncio
async def test_vector_payload_cannot_replace_database_content_or_permissions() -> None:
    chunk, version, document = _knowledge_row()
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(
        all=lambda: [(chunk, version, document, None)])))
    service = RetrievalService.__new__(RetrievalService)
    service.session = session
    point = SimpleNamespace(id=chunk.qdrant_point_id, score=0.9, payload={
        "chunk_id": str(chunk.id), "document_id": str(document.id),
        "document_version_id": str(version.id), "content_hash": chunk.content_hash,
        "title": "Forged title", "content": "Forged answer", "visibility": "PUBLIC",
    })
    hits = await service._verified_vector_hits([point], analyze_query("Học bổng là gì?"), AccessScope())
    assert len(hits) == 1
    assert hits[0].content == chunk.content
    assert hits[0].title == document.title
    document.visibility = AIVisibility.GROUP
    document.group_id = uuid4()
    assert await service._verified_vector_hits([point], analyze_query("Học bổng là gì?"), AccessScope()) == []
    point.payload["content_hash"] = "0" * 64
    assert await service._verified_vector_hits([point], analyze_query("Học bổng là gì?"),
                                               AccessScope(authenticated=True, group_ids=(document.group_id,))) == []


def test_retrieval_rejects_expired_and_revoked_sources() -> None:
    chunk, version, document = _knowledge_row()
    intent = analyze_query("Học bổng là gì?")
    document.effective_to = datetime.now(UTC) - timedelta(days=1)
    assert not _authorized_chunk(chunk, version, document, intent, AccessScope())
    document.effective_to = None
    document.metadata_ = {"source_id": str(uuid4())}
    assert not _authorized_chunk(chunk, version, document, intent, AccessScope())
    source = SimpleNamespace(id=document.metadata_["source_id"], enabled=False,
                             allowed_domains=["hvnh.edu.vn"], allowed_path_prefixes=[])
    assert not _authorized_chunk(chunk, version, document, intent, AccessScope(), source)
    source.enabled = True
    assert _authorized_chunk(chunk, version, document, intent, AccessScope(), source)
