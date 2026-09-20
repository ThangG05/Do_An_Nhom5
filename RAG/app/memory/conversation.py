"""Bounded conversation memory used only for query rewriting, never as RAG evidence."""
from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.llm.contracts import ConversationTurn, LLMProvider, LLMServiceError
from app.models.enums import AIMessageRole
from app.models.rag import AIConversation, AIMessage


@dataclass(frozen=True, slots=True)
class PreparedQuestion:
    original_question: str
    standalone_question: str
    depends_on_history: bool
    summary: str | None = None
    summary_until_sequence: int | None = None


class ConversationMemoryService:
    def __init__(self, session: AsyncSession, llm: LLMProvider) -> None:
        self.session, self.llm = session, llm
        self.settings = get_settings()

    async def prepare(self, question: str, conversation_id: UUID | None,
                      user_id: UUID | None = None) -> PreparedQuestion:
        if conversation_id is None:
            return PreparedQuestion(question, question, False)
        conversation = await self.session.scalar(select(AIConversation).where(
            AIConversation.id == conversation_id, AIConversation.deleted_at.is_(None),
            AIConversation.user_id == user_id))
        if conversation is None: raise ValueError("conversation not found")
        latest_sequence = int(await self.session.scalar(select(func.max(AIMessage.sequence_number)).where(
            AIMessage.conversation_id == conversation.id)) or 0)
        summary, summary_until = conversation.summary, conversation.summary_until_sequence
        unsummarized = latest_sequence - summary_until
        if unsummarized >= self.settings.conversation_summary_trigger_messages:
            cutoff = max(summary_until, latest_sequence - self.settings.conversation_recent_messages)
            old_rows = list((await self.session.scalars(select(AIMessage).where(
                AIMessage.conversation_id == conversation.id,
                AIMessage.sequence_number > summary_until,
                AIMessage.sequence_number <= cutoff,
            ).order_by(AIMessage.sequence_number))).all())
            if old_rows:
                try:
                    result = await self.llm.summarize_conversation(summary, self._turns(old_rows))
                    summary, summary_until = result.summary, cutoff
                except LLMServiceError:
                    pass  # Summary compaction is optional; never lose a valid chat turn.
        recent_rows = list((await self.session.scalars(select(AIMessage).where(
            AIMessage.conversation_id == conversation.id,
            AIMessage.sequence_number > max(summary_until, latest_sequence - self.settings.conversation_recent_messages),
        ).order_by(AIMessage.sequence_number))).all())
        if not recent_rows and not summary:
            return PreparedQuestion(question, question, False)
        rewritten = await self.llm.rewrite_question(question, self._turns(recent_rows), summary)
        return PreparedQuestion(question, rewritten.standalone_question,
                                rewritten.depends_on_history, summary, summary_until)

    @staticmethod
    def _turns(rows: list[AIMessage]) -> list[ConversationTurn]:
        return [ConversationTurn(role=row.role.value, content=row.content)
                for row in rows if row.role in {AIMessageRole.USER, AIMessageRole.ASSISTANT}]
