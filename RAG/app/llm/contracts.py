from typing import Protocol

from pydantic import BaseModel, Field, model_validator


class LLMConfigurationError(RuntimeError):
    pass


class LLMServiceError(RuntimeError):
    """Generic provider error that never exposes a raw upstream response."""

    def __init__(self, code: str = "provider_unavailable", diagnostic: str = "unknown") -> None:
        super().__init__("LLM request could not be completed")
        self.code = code
        self.diagnostic = diagnostic if diagnostic.replace("_", "").isalnum() else "unknown"


class ContextBlock(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    source_label: str = Field(min_length=1, max_length=500)
    # Internal grouping key; excluded from provider payloads and prompts.
    source_key: str | None = Field(default=None, exclude=True)


class LLMAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=12000)
    refused: bool = False
    refusal_reason: str | None = Field(default=None, max_length=500)
    cited_context_ids: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_refusal(self) -> "LLMAnswer":
        if self.refused and not self.refusal_reason:
            raise ValueError("A refused answer must include a reason")
        if self.refused and self.cited_context_ids:
            raise ValueError("A refused answer cannot contain citations")
        if not self.refused and not self.cited_context_ids:
            raise ValueError("A grounded answer must contain at least one citation")
        if len(self.cited_context_ids) != len(set(self.cited_context_ids)):
            raise ValueError("Citation context IDs must be unique")
        return self


class ConversationTurn(BaseModel):
    role: str = Field(pattern="^(USER|ASSISTANT)$")
    content: str = Field(min_length=1, max_length=12000)


class QuestionRewrite(BaseModel):
    standalone_question: str = Field(min_length=1, max_length=4000)
    depends_on_history: bool


class ConversationSummary(BaseModel):
    summary: str = Field(min_length=1, max_length=4000)


class LLMProvider(Protocol):
    async def answer(self, question: str, context: list[ContextBlock]) -> LLMAnswer: ...
    async def rewrite_question(self, question: str, history: list[ConversationTurn], summary: str | None) -> QuestionRewrite: ...
    async def summarize_conversation(self, previous_summary: str | None, history: list[ConversationTurn]) -> ConversationSummary: ...
    async def close(self) -> None: ...
