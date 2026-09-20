from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from app.llm.contracts import ConversationTurn, QuestionRewrite
from app.llm.security import PromptGuard
from app.services.llm import GeminiProvider


@pytest.mark.asyncio
async def test_gemini_rewrites_followup_as_standalone_question() -> None:
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.settings = SimpleNamespace(llm_max_context_chars=5000)
    provider.guard = PromptGuard(max_user_chars=1000, max_context_chars=5000)
    provider._structured_memory = AsyncMock(return_value=QuestionRewrite(
        standalone_question="Yêu cầu VSTEP của sinh viên là gì?", depends_on_history=True))
    result = await provider.rewrite_question("Còn VSTEP thì sao?", [
        ConversationTurn(role="USER", content="Điều kiện ngoại ngữ là gì?"),
        ConversationTurn(role="ASSISTANT", content="Thông tin trước đó [1]."),
    ], None)
    assert result.depends_on_history is True
    assert result.standalone_question.startswith("Yêu cầu VSTEP")


def test_conversation_turn_rejects_unknown_role() -> None:
    with pytest.raises(ValueError):
        ConversationTurn(role="SYSTEM", content="unsafe")
