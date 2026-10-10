import pytest

from src.core.profile_options import (
    SCHOOL_NAME,
    derive_course_year,
    normalize_faculty,
    normalize_province,
    normalize_social_links,
)
from src.models.user import ProfileUpdateRequest


def test_course_year_is_derived_from_student_code() -> None:
    assert derive_course_year("26A4041668") == "K26 (2023-2027)"
    assert derive_course_year("admin_su_kien") is None


def test_profile_choices_are_normalized_and_invalid_values_are_rejected() -> None:
    assert normalize_faculty("Công nghệ thông tin") == "Khoa Công nghệ thông tin và Kinh tế số"
    assert normalize_province("Thành phố Hà Nội") == "Hà Nội"
    with pytest.raises(ValueError):
        normalize_faculty("Khoa nhập tùy ý")
    with pytest.raises(ValueError):
        normalize_province("Tỉnh không tồn tại")


def test_profile_payload_restricts_school_and_social_domains() -> None:
    payload = ProfileUpdateRequest(
        education=SCHOOL_NAME,
        socialLinks={"facebook": "https://facebook.com/hvnh"},
    )
    assert payload.education == SCHOOL_NAME
    assert payload.socialLinks == {"facebook": "https://facebook.com/hvnh"}
    with pytest.raises(ValueError):
        ProfileUpdateRequest(education="Trường tùy ý")
    with pytest.raises(ValueError):
        normalize_social_links({"facebook": "https://example.com/not-facebook"})
