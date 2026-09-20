"""Grounded RAG orchestration with durable conversations and citation snapshots."""
from dataclasses import dataclass
from datetime import UTC, datetime
import re
from time import perf_counter
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.llm.contracts import ContextBlock, LLMAnswer, LLMProvider, LLMServiceError
from app.models.enums import AIMessageRole
from app.models.rag import AIConversation, AIMessage, AIMessageCitation
from app.memory.conversation import ConversationMemoryService, PreparedQuestion
from app.rag.retriever import AccessScope, RetrievalHit, RetrievalService, analyze_query
from app.rag.citation_verifier import verify_claim_citations


_CAPITALIZED_WORD = r"[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯẠ-Ỹ][\wÀ-ỹ]*"


def unsupported_named_entities(question: str, hits: list[RetrievalHit]) -> tuple[str, ...]:
    """Find explicit multi-word proper names absent from every retrieved context."""
    entities = re.findall(rf"(?<!\w)({_CAPITALIZED_WORD}(?:\s+{_CAPITALIZED_WORD})+)", question)
    corpus = " ".join(f"{hit.title} {hit.content}" for hit in hits).casefold()
    return tuple(entity for entity in entities if entity.casefold() not in corpus)


@dataclass(frozen=True, slots=True)
class Citation:
    order: int
    title: str
    source_url: str | None
    page_start: int | None
    page_end: int | None
    section_title: str | None
    relevance_score: float


@dataclass(frozen=True, slots=True)
class RAGResult:
    conversation_id: UUID
    message_id: UUID
    answer: str
    refused: bool
    refusal_reason: str | None
    citations: tuple[Citation, ...]
    rewritten_question: str


class RAGService:
    def __init__(self, session: AsyncSession, retriever: RetrievalService,
                 llm: LLMProvider) -> None:
        self.session, self.retriever, self.llm = session, retriever, llm
        self.settings = get_settings()

    async def ask(self, question: str, conversation_id: UUID | None = None,
                  access: AccessScope | None = None, user_id: UUID | None = None) -> RAGResult:
        started = perf_counter()
        prepared = await ConversationMemoryService(self.session, self.llm).prepare(question, conversation_id, user_id)
        intent = analyze_query(prepared.standalone_question)
        hits = await self.retriever.search(intent.normalized_query, access=access)
        if self._relative_date_without_fresh_evidence(intent.normalized_query, hits):
            hits = []
        unsupported_entities = unsupported_named_entities(intent.normalized_query, hits)
        if unsupported_entities:
            hits = []
        if hits:
            blocks = [ContextBlock(id=str(index), content=hit.content,
                                   source_label=self._source_label(hit), source_key=hit.document_id)
                      for index, hit in enumerate(hits, 1)]
            answer = await self._answer_with_contract_retry(intent.normalized_query, blocks)
        else:
            answer = LLMAnswer(answer="Tôi chưa tìm thấy thông tin phù hợp trong các nguồn chính thức đã được lập chỉ mục.",
                               refused=True, refusal_reason="insufficient_context", cited_context_ids=[])
        latency_ms = round((perf_counter() - started) * 1000)
        return await self._persist(prepared, intent, hits, answer, latency_ms, conversation_id, user_id)

    async def _answer_with_contract_retry(self, question: str,
                                          blocks: list[ContextBlock]) -> LLMAnswer:
        """Retry malformed structured output once, then fail closed without an uncited answer."""
        for attempt in range(self.settings.rag_contract_max_attempts):
            try:
                answer = await self.llm.answer(question, blocks)
                self._validate_answer_citations(answer, len(blocks), blocks, question)
                return answer
            except LLMServiceError as exc:
                if exc.code != "invalid_response":
                    raise
                if attempt == self.settings.rag_contract_max_attempts - 1:
                    return LLMAnswer(
                        answer="Tôi chưa thể tạo câu trả lời có trích dẫn hợp lệ từ các nguồn đã tìm thấy.",
                        refused=True,
                        refusal_reason="invalid_grounded_response",
                        cited_context_ids=[],
                    )
        raise AssertionError("unreachable")

    @staticmethod
    def _source_label(hit: RetrievalHit) -> str:
        location = f", trang {hit.page_start}-{hit.page_end}" if hit.page_start else ""
        section = f", mục {hit.section_title}" if hit.section_title else ""
        academic_year = f", năm học {hit.academic_year}" if hit.academic_year else ""
        # ai_message_citations.source_label_snapshot is varchar(255) in Neon V2.
        return f"{hit.title}{academic_year}{section}{location}"[:255]

    @staticmethod
    def _relative_date_without_fresh_evidence(question: str, hits: list[RetrievalHit]) -> bool:
        """Fail closed for today/tomorrow claims unless a newly published source supports them."""
        if not re.search(r"\b(hôm nay|ngày mai)\b", question, re.IGNORECASE):
            return False
        now = datetime.now(UTC)
        for hit in hits:
            if not hit.published_at:
                continue
            try:
                published = datetime.fromisoformat(hit.published_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if published.tzinfo is None:
                published = published.replace(tzinfo=UTC)
            if 0 <= (now - published).days <= 7:
                return False
        return True

    @staticmethod
    def _validate_answer_citations(answer: LLMAnswer, context_count: int,
                                   blocks: list[ContextBlock] | None = None,
                                   question: str | None = None) -> None:
        if answer.refused: return
        allowed = {str(index) for index in range(1, context_count + 1)}
        cited = set(answer.cited_context_ids)
        markers = {item for group in re.findall(r"\[([0-9]+(?:\s*,\s*[0-9]+)*)\]", answer.answer)
                   for item in re.findall(r"[0-9]+", group)}
        if not cited or cited != markers or not cited.issubset(allowed):
            raise LLMServiceError("invalid_response", "citation_marker_mismatch")
        if blocks:
            issues = verify_claim_citations(answer, blocks, question)
            if issues:
                raise LLMServiceError("invalid_response", issues[0].code.casefold())

    @staticmethod
    def _renumber_citation_markers(text: str, context_ids: list[str]) -> str:
        mapping = {context_id: str(order) for order, context_id in enumerate(context_ids, 1)}

        def replace(match: re.Match[str]) -> str:
            ids = re.findall(r"[0-9]+", match.group(1))
            return "[" + ", ".join(mapping[item] for item in ids) + "]"

        return re.sub(r"\[([0-9]+(?:\s*,\s*[0-9]+)*)\]", replace, text)

    async def _persist(self, prepared: PreparedQuestion, intent, hits: list[RetrievalHit], answer: LLMAnswer,
                       latency_ms: int, conversation_id: UUID | None, user_id: UUID | None) -> RAGResult:
        if conversation_id:
            conversation = await self.session.scalar(select(AIConversation).where(
                AIConversation.id == conversation_id, AIConversation.deleted_at.is_(None),
                AIConversation.user_id == user_id,
            ).with_for_update())
            if conversation is None: raise ValueError("conversation not found")
        else:
            conversation = AIConversation(user_id=user_id, title=prepared.original_question[:500],
                academic_year_context=intent.academic_year,
                metadata_={"channel": "public_rag" if user_id else "internal_rag"})
            self.session.add(conversation); await self.session.flush()
        latest = int(await self.session.scalar(select(func.max(AIMessage.sequence_number)).where(
            AIMessage.conversation_id == conversation.id)) or 0)
        filters = {"academic_year": intent.academic_year,
                   "document_type": intent.document_type.value if intent.document_type else None,
                   "latest": intent.latest, "score_threshold": self.settings.retrieval_score_threshold}
        user_message = AIMessage(conversation_id=conversation.id, sequence_number=latest + 1,
            role=AIMessageRole.USER, content=prepared.original_question,
            rewritten_question=intent.normalized_query, retrieval_filters=filters,
            metadata_={"depends_on_history": prepared.depends_on_history})
        self.session.add(user_message)
        display_answer = self._renumber_citation_markers(answer.answer, answer.cited_context_ids)
        assistant = AIMessage(conversation_id=conversation.id, sequence_number=latest + 2,
            role=AIMessageRole.ASSISTANT, content=display_answer, retrieval_filters=filters,
            model_name=self.settings.llm_model if hits else None, latency_ms=latency_ms,
            metadata_={"refused": answer.refused, "refusal_reason": answer.refusal_reason})
        self.session.add(assistant); await self.session.flush()
        citations = []
        for order, context_id in enumerate(answer.cited_context_ids, 1):
            retrieval_rank = int(context_id); hit = hits[retrieval_rank - 1]
            self.session.add(AIMessageCitation(message_id=assistant.id, chunk_id=UUID(hit.chunk_id),
                citation_order=order, retrieval_rank=retrieval_rank, relevance_score=hit.score,
                # Preserve the exact evidence seen by the answer model. Truncating
                # this snapshot made citation review and faithfulness evaluation
                # falsely treat claims supported later in the chunk as unsupported.
                quoted_text=hit.content, document_title_snapshot=hit.title,
                source_url_snapshot=hit.source_url, source_label_snapshot=self._source_label(hit),
                page_start_snapshot=hit.page_start, page_end_snapshot=hit.page_end,
                section_title_snapshot=hit.section_title))
            citations.append(Citation(order, hit.title, hit.source_url, hit.page_start, hit.page_end,
                                      hit.section_title, hit.score))
        conversation.last_message_at = datetime.now(UTC)
        conversation.academic_year_context = intent.academic_year or conversation.academic_year_context
        if prepared.summary_until_sequence is not None:
            conversation.summary = prepared.summary
            conversation.summary_until_sequence = prepared.summary_until_sequence
        await self.session.commit()
        return RAGResult(conversation.id, assistant.id, display_answer, answer.refused,
                         answer.refusal_reason, tuple(citations), intent.normalized_query)
