from __future__ import annotations

import re
from urllib.parse import urlparse


SCHOOL_NAME = "Học viện Ngân hàng (BAV)"

FACULTIES = (
    "Khoa Ngân hàng",
    "Khoa Tài chính",
    "Khoa Kế toán - Kiểm toán",
    "Khoa Quản trị kinh doanh",
    "Khoa Kinh doanh quốc tế",
    "Khoa Công nghệ thông tin và Kinh tế số",
    "Khoa Ngoại ngữ",
    "Khoa Luật",
    "Khoa Kinh tế",
    "Viện Đào tạo quốc tế",
)

FACULTY_ALIASES = {
    "Công nghệ thông tin": "Khoa Công nghệ thông tin và Kinh tế số",
    "Công nghệ thông tin và Kinh tế số": "Khoa Công nghệ thông tin và Kinh tế số",
    "Kế toán - Kiểm toán": "Khoa Kế toán - Kiểm toán",
    "Ngân hàng": "Khoa Ngân hàng",
    "Tài chính": "Khoa Tài chính",
}

PROVINCES = (
    "Hà Nội", "Cao Bằng", "Tuyên Quang", "Điện Biên", "Lai Châu", "Sơn La",
    "Lào Cai", "Thái Nguyên", "Lạng Sơn", "Quảng Ninh", "Bắc Ninh", "Phú Thọ",
    "Hải Phòng", "Hưng Yên", "Ninh Bình", "Thanh Hóa", "Nghệ An", "Hà Tĩnh",
    "Quảng Trị", "Huế", "Đà Nẵng", "Quảng Ngãi", "Gia Lai", "Khánh Hòa",
    "Đắk Lắk", "Lâm Đồng", "Đồng Nai", "Thành phố Hồ Chí Minh", "Tây Ninh",
    "Đồng Tháp", "Vĩnh Long", "An Giang", "Cần Thơ", "Cà Mau",
)

SOCIAL_HOSTS = {
    "facebook": ("facebook.com", "www.facebook.com", "m.facebook.com"),
    "instagram": ("instagram.com", "www.instagram.com"),
    "linkedin": ("linkedin.com", "www.linkedin.com"),
}


def derive_course_year(student_code: str | None) -> str | None:
    if not student_code:
        return None
    match = re.match(r"^(\d{2})", student_code.strip())
    if not match:
        return None
    cohort = int(match.group(1))
    if cohort < 18 or cohort > 60:
        return None
    start_year = 1997 + cohort
    return f"K{cohort} ({start_year}-{start_year + 4})"


def normalize_faculty(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    if not normalized:
        return ""
    normalized = FACULTY_ALIASES.get(normalized, normalized)
    if normalized not in FACULTIES:
        raise ValueError("Vui lòng chọn khoa/chuyên ngành trong danh sách của Học viện.")
    return normalized


def normalize_province(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    if not normalized:
        return ""
    normalized = re.sub(r"^(Tỉnh|Thành phố)\s+", "", normalized, flags=re.IGNORECASE)
    if normalized == "Hồ Chí Minh":
        normalized = "Thành phố Hồ Chí Minh"
    if normalized not in PROVINCES:
        raise ValueError("Vui lòng chọn một trong 34 tỉnh/thành phố hiện hành.")
    return normalized


def normalize_social_links(value: dict[str, str] | None) -> dict[str, str] | None:
    if value is None:
        return None
    result: dict[str, str] = {}
    unknown = set(value) - set(SOCIAL_HOSTS)
    if unknown:
        raise ValueError("Chỉ hỗ trợ liên kết Facebook, Instagram và LinkedIn.")
    for network, raw_url in value.items():
        url = raw_url.strip()
        if not url:
            continue
        if len(url) > 500:
            raise ValueError(f"Liên kết {network} quá dài.")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in SOCIAL_HOSTS[network]:
            raise ValueError(f"Liên kết {network} không đúng định dạng.")
        result[network] = url
    return result
