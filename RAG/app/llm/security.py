import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class InputKind(StrEnum):
    USER = "user"
    CONTEXT = "context"


class PromptSecurityError(ValueError):
    """Safe public error for rejected LLM input."""

    def __init__(self, code: str) -> None:
        super().__init__("Input rejected by security policy")
        self.code = code


@dataclass(frozen=True)
class GuardedText:
    value: str
    risk_signals: tuple[str, ...] = ()


_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("instruction_override", re.compile(
        r"\b(ignore|disregard|forget)\b.{0,40}\b(previous|prior|system|developer)\b.{0,30}\b(instruction|prompt|rule)s?\b",
        re.IGNORECASE | re.DOTALL)),
    ("instruction_override_vi", re.compile(
        r"\b(bỏ qua|phớt lờ|không tuân theo)\b.{0,50}\b(chỉ dẫn|hướng dẫn|quy tắc|prompt)\b.{0,35}\b(trước đó|hệ thống|system|developer)\b",
        re.IGNORECASE | re.DOTALL)),
    ("prompt_extraction", re.compile(
        r"\b(reveal|show|print|repeat|leak|display)\b.{0,40}\b(system|developer|hidden)\b.{0,20}\b(prompt|instruction|message)s?\b",
        re.IGNORECASE | re.DOTALL)),
    ("prompt_extraction_vi", re.compile(
        r"\b(tiết lộ|hiển thị|in ra|lặp lại)\b.{0,60}\b(prompt|chỉ dẫn|hướng dẫn)\b.{0,30}\b(hệ thống|ẩn|developer)\b",
        re.IGNORECASE | re.DOTALL)),
    ("safety_bypass", re.compile(
        r"\b(bypass|disable|override|circumvent)\b.{0,40}\b(safety|guardrail|filter|policy|restriction)s?\b",
        re.IGNORECASE | re.DOTALL)),
    ("role_hijack", re.compile(
        r"\b(you are now|act as|switch to)\b.{0,50}\b(developer mode|system|unrestricted|jailbreak)\b",
        re.IGNORECASE | re.DOTALL)),
    ("role_hijack_vi", re.compile(
        r"\b(bây giờ bạn là|hãy đóng vai|chuyển sang)\b.{0,50}\b(hệ thống|developer|không giới hạn|jailbreak)\b",
        re.IGNORECASE | re.DOTALL)),
    ("fake_role_marker", re.compile(
        r"(^|\n)\s*(system|developer|assistant)\s*:\s*", re.IGNORECASE)),
    ("hidden_markup", re.compile(
        r"<(script|iframe|object|embed|style|meta)\b|\[!\[.*?\]\(https?://",
        re.IGNORECASE | re.DOTALL)),
)
_ENCODED_BLOB = re.compile(r"(?:[A-Za-z0-9+/]{80,}={0,2}|(?:[0-9a-fA-F]{2}){80,})")


def injection_signal_spans(value: str) -> tuple[tuple[str, int, int], ...]:
    """Return deterministic signal locations for trusted quarantine-review tooling."""
    normalized = PromptGuard._normalize(value)
    spans = [(name, match.start(), match.end())
             for name, pattern in _INJECTION_PATTERNS
             for match in pattern.finditer(normalized)]
    spans.extend(("encoded_payload", match.start(), match.end())
                 for match in _ENCODED_BLOB.finditer(normalized))
    return tuple(sorted(spans, key=lambda item: (item[1], item[0])))


class PromptGuard:
    def __init__(self, max_user_chars: int, max_context_chars: int) -> None:
        self.max_user_chars = max_user_chars
        self.max_context_chars = max_context_chars

    def inspect(self, value: str, kind: InputKind) -> GuardedText:
        normalized = self._normalize(value)
        limit = self.max_user_chars if kind is InputKind.USER else self.max_context_chars
        if not normalized:
            raise PromptSecurityError("empty_input")
        if len(normalized) > limit:
            raise PromptSecurityError("input_too_long")
        signals = tuple(dict.fromkeys(name for name, _, _ in injection_signal_spans(normalized)))
        if signals:
            raise PromptSecurityError(f"{kind.value}_prompt_injection")
        return GuardedText(normalized)

    def inspect_output(self, value: str) -> GuardedText:
        normalized = self._normalize(value)
        if not normalized:
            raise PromptSecurityError("empty_output")
        output_patterns = (
            re.compile(r"<(script|iframe|object|embed|meta)\b", re.IGNORECASE),
            re.compile(r"\b(javascript|data)\s*:", re.IGNORECASE),
            re.compile(r"\b(system|developer) (prompt|instruction)s?\s*(is|:)", re.IGNORECASE),
        )
        if any(pattern.search(normalized) for pattern in output_patterns):
            raise PromptSecurityError("unsafe_output")
        return GuardedText(normalized)

    @staticmethod
    def _normalize(value: str) -> str:
        if not isinstance(value, str):
            raise PromptSecurityError("invalid_input_type")
        value = unicodedata.normalize("NFKC", value)
        value = "".join(
            char if char in "\n\t" or unicodedata.category(char) not in {"Cc", "Cf", "Cs"} else " "
            for char in value
        )
        return value.replace("\r\n", "\n").replace("\r", "\n").strip()
