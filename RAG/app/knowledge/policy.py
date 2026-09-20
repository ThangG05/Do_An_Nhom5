"""Source-configurable publication policy shared by every document format and topic."""
from dataclasses import dataclass
import re
import unicodedata
from urllib.parse import unquote


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    code: str | None = None
    reason: str | None = None


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", unquote(value).casefold())
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def assess_url(url: str, source_metadata: dict | None = None) -> PolicyDecision:
    normalized = _normalized(url)
    configured = [
        _normalized(str(pattern)) for pattern in (source_metadata or {}).get("exclude_url_patterns", [])
    ]
    default_sensitive_patterns = (
        "danh-sach-sinh-vien", "danh-sach-hoc-vien", "sinh-vien-no", "hoc-vien-no",
        "danh-sach-nguoi-hoc",
    )
    if any(pattern and pattern in normalized for pattern in (*default_sensitive_patterns, *configured)):
        return PolicyDecision(False, "PII_EXCLUDED", "sensitive_person_list")
    return PolicyDecision(True)


def assess_content(title: str, content: str, source_metadata: dict | None = None) -> PolicyDecision:
    combined = f"{title}\n{content}"
    normalized = _normalized(combined)
    configured = [
        _normalized(str(pattern)) for pattern in (source_metadata or {}).get("exclude_content_patterns", [])
    ]
    if any(pattern and pattern in normalized for pattern in configured):
        return PolicyDecision(False, "POLICY_EXCLUDED", "configured_content_pattern")
    student_codes = re.findall(r"(?<![A-Z0-9])\d{2}[A-Z]\d{6,10}(?![A-Z0-9])", combined.upper())
    sensitive_context = any(token in normalized for token in (
        "danh-sach", "cong-no", "no-hoc-phi", "ky-luat", "canh-cao-hoc-vu",
    ))
    if sensitive_context and len(set(student_codes)) >= 3:
        return PolicyDecision(False, "PII_EXCLUDED", "bulk_student_records")
    return PolicyDecision(True)
