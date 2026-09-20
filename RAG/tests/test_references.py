from app.knowledge.references import extract_primary_document_number, extract_references


def test_extracts_and_classifies_vietnamese_document_reference() -> None:
    matches = extract_references(
        "Học viện quyết định giữ nguyên mức thu theo Quyết định số 2450/QĐ-HVNH ngày 25/08/2023."
    )
    assert matches[0].number == "2450/QĐ-HVNH"
    assert matches[0].relation_type == "REFERENCES"


def test_detects_lifecycle_relation() -> None:
    assert extract_references("Bãi bỏ Quyết định số 123/QĐ-HVNH kể từ ngày ký.")[0].relation_type == "REPEALS"
    assert extract_references("Văn bản này thay thế 456/QD-HVNH.")[0].relation_type == "SUPERSEDES"
    assert extract_references("Sửa đổi, bổ sung Nghị quyết 78/NQ-HDHV.")[0].relation_type == "AMENDS"


def test_extracts_primary_number_from_filename_title() -> None:
    assert extract_primary_document_number("e00452_3245 QĐ-HVNH mức thu học phí.pdf") == "3245/QĐ-HVNH"
    assert extract_primary_document_number("47c2_QD 3455 Muc thu hoc phi.pdf") == "3455/QĐ-HVNH"


def test_keeps_government_document_year_in_number() -> None:
    assert extract_references("Căn cứ Nghị định số 81/2021/NĐ-CP của Chính phủ")[0].number == "81/2021/NĐ-CP"


def test_does_not_treat_ordinary_academic_phrase_as_document_number() -> None:
    assert extract_references("Học kỳ 1 khối ngành III áp dụng mức thu mới.") == []
