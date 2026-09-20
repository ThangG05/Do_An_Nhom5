from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.llm.contracts import QuestionRewrite
from app.memory.conversation import ConversationMemoryService
from app.models.enums import AIMessageRole


class _ScalarRows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "follow_up",
    [
        "Thầy dạy những môn học nào?",
        "Người này còn phụ trách công việc gì?",
        "Thông tin vừa rồi áp dụng cho khóa nào?",
        "Hãy cho tôi biết thêm chi tiết.",
        "Yêu cầu về chuẩn đầu ra ngoại ngữ của sinh viên là gì?",
    ],
)
async def test_every_followup_with_history_is_rewritten(follow_up: str) -> None:
    conversation_id, user_id = uuid4(), uuid4()
    conversation = SimpleNamespace(
        id=conversation_id,
        summary=None,
        summary_until_sequence=0,
    )
    session = SimpleNamespace(
        scalar=AsyncMock(side_effect=[conversation, 2]),
        scalars=AsyncMock(return_value=_ScalarRows([
            SimpleNamespace(role=AIMessageRole.USER, content="Giảng viên Nguyễn Thanh Thụy là ai?"),
            SimpleNamespace(role=AIMessageRole.ASSISTANT, content="Thông tin về Nguyễn Thanh Thụy."),
        ])),
    )
    llm = SimpleNamespace(rewrite_question=AsyncMock(return_value=QuestionRewrite(
        standalone_question="Giảng viên Nguyễn Thanh Thụy dạy những môn học nào?",
        depends_on_history=True,
    )))

    result = await ConversationMemoryService(session, llm).prepare(
        follow_up, conversation_id, user_id
    )

    llm.rewrite_question.assert_awaited_once()
    assert result.depends_on_history is True
    assert "Nguyễn Thanh Thụy" in result.standalone_question

