from uuid import uuid4
from app.models.enums import AIDocumentType
from app.rag.retriever import (AccessScope, _lexical_scores, _per_document_limit,
                               _rrf, analyze_query, build_filter)


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
