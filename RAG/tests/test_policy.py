from app.knowledge.policy import assess_content, assess_url


def test_policy_applies_to_any_topic_and_format() -> None:
    assert not assess_url("https://hvnh.edu.vn/files/danh-sach-hoc-vien-ky-luat.xlsx").allowed
    assert not assess_url("https://hvnh.edu.vn/files/private-results.pdf",
                          {"exclude_url_patterns": ["private-results"]}).allowed


def test_bulk_student_records_are_not_publication_safe() -> None:
    content = "Danh sách nợ học phí: 22A1234567, 22A1234568, 22A1234569"
    decision = assess_content("Thông báo", content)
    assert not decision.allowed
    assert decision.code == "PII_EXCLUDED"


def test_normal_public_document_is_allowed() -> None:
    assert assess_content("Quy chế đào tạo", "Điều 1. Phạm vi và đối tượng áp dụng.").allowed
