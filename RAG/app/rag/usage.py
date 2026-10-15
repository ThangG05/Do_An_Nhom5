"""Request-scoped, provider-reported LLM usage; never estimates tokens from text."""
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.rag import RAGTokenUsage


@dataclass(slots=True)
class UsageEntry:
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    usage_source: str
    status: str


@dataclass(slots=True)
class UsageCollector:
    user_id: UUID | None
    request_id: UUID = field(default_factory=uuid4)
    entries: list[UsageEntry] = field(default_factory=list)
    saved: bool = False

    def add(self, entry: UsageEntry) -> None:
        if self.user_id is not None:
            self.entries.append(entry)

    def _rows(self) -> list[RAGTokenUsage]:
        return [RAGTokenUsage(user_id=self.user_id, request_id=self.request_id,
                              call_index=index, provider=item.provider, model=item.model,
                              input_tokens=item.input_tokens, output_tokens=item.output_tokens,
                              total_tokens=item.total_tokens, usage_source=item.usage_source,
                              status=item.status)
                for index, item in enumerate(self.entries, 1)]

    def attach(self, session: AsyncSession) -> None:
        if self.entries:
            session.add_all(self._rows())

    async def persist_after_error(self) -> None:
        if self.saved or not self.entries:
            return
        async with AsyncSessionLocal() as session:
            session.add_all(self._rows())
            await session.commit()
        self.saved = True


_active: ContextVar[UsageCollector | None] = ContextVar("rag_token_collector", default=None)


def activate(collector: UsageCollector) -> Token:
    return _active.set(collector)


def reset(token: Token) -> None:
    _active.reset(token)


def _count(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def capture_gemini_usage(response: object, model: str) -> None:
    collector = _active.get()
    if collector is None or collector.user_id is None:
        return
    usage = getattr(response, "usage_metadata", None)
    input_tokens = _count(getattr(usage, "prompt_token_count", None))
    output_tokens = _count(getattr(usage, "candidates_token_count", None))
    total_tokens = _count(getattr(usage, "total_token_count", None))
    collector.add(UsageEntry("gemini", str(getattr(response, "model_version", None) or model),
                             input_tokens, output_tokens, total_tokens,
                             "provider" if usage else "missing", "SUCCESS"))


def capture_deepseek_usage(data: dict, model: str, status: str = "SUCCESS") -> None:
    collector = _active.get()
    if collector is None or collector.user_id is None:
        return
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else None
    collector.add(UsageEntry("deepseek", str(data.get("model") or model),
                             _count(usage.get("prompt_tokens")) if usage else None,
                             _count(usage.get("completion_tokens")) if usage else None,
                             _count(usage.get("total_tokens")) if usage else None,
                             "provider" if usage else "missing", status))
