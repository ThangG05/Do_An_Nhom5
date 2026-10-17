"""Grounded RAG orchestration with durable conversations and citation snapshots."""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import re
from time import perf_counter
import unicodedata
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.llm.contracts import ContextBlock, LLMAnswer, LLMProvider, LLMServiceError
from app.llm.security import InputKind, PromptGuard, PromptSecurityError
from app.models.enums import AIMessageRole
from app.models.rag import AIConversation, AIMessage, AIMessageCitation
from app.memory.conversation import ConversationMemoryService, PreparedQuestion
from app.rag.retriever import AccessScope, RetrievalHit, RetrievalService, analyze_query
from app.rag.citation_verifier import verify_claim_citations
from app.rag.casual import is_casual_conversation
from app.rag.usage import UsageCollector, activate, reset
from app.services.rate_limit import enforce_casual_daily_limit


_CAPITALIZED_WORD = r"[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯẠ-Ỹ][\wÀ-ỹ]*"
logger = logging.getLogger(__name__)

_SOCIAL_REPLIES = {
    "chào": "Chào bạn! Mình là Trợ lý HVNH Hub. Bạn có thể hỏi mình về thông tin học tập và hoạt động của Học viện Ngân hàng.",
    "giới thiệu": "Mình là Trợ lý HVNH Hub. Mình có thể giúp bạn tìm thông tin về học tập và hoạt động của Học viện từ các nguồn đã được lập chỉ mục.",
    "cảm ơn": "Không có gì! Khi cần tìm thông tin về Học viện, bạn cứ hỏi mình nhé.",
    "tạm biệt": "Tạm biệt bạn! Hẹn gặp lại trên HVNH Hub nhé.",
    "xác nhận": "Mình hiểu rồi. Bạn cứ chia sẻ tiếp, hoặc hỏi mình điều bạn đang cần nhé.",
}
_SOCIAL_PHRASES = {
    "chào": {"chào", "chào bạn", "chào bạn nhé", "xin chào", "xin chào bạn",
             "chào trợ lý", "xin chào trợ lý", "chào bot", "hello", "hi", "alo"},
    "giới thiệu": {"bạn là ai", "bạn có thể làm gì", "bạn giúp được gì", "trợ lý là ai"},
    "cảm ơn": {"cảm ơn", "cảm ơn bạn", "cảm ơn bạn nhiều", "cảm ơn nhiều",
                "cám ơn", "cám ơn bạn", "cám ơn nhiều", "cam on", "cam on ban", "thank you", "thanks"},
    "tạm biệt": {"tạm biệt", "tạm biệt bạn", "tạm biệt nhé", "hẹn gặp lại", "bye", "goodbye"},
    "xác nhận": {"ok", "oke", "được rồi", "ừ", "ừ đúng rồi", "đúng rồi", "hay quá", "haha"},
}


def social_reply(question: str) -> str | None:
    """Handle only complete, harmless social utterances; mixed questions use normal RAG."""
    normalized = unicodedata.normalize("NFKC", question).casefold()
    normalized = " ".join(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE))
    for kind, phrases in _SOCIAL_PHRASES.items():
        if normalized in phrases:
            return _SOCIAL_REPLIES[kind]
    return None


@dataclass(frozen=True, slots=True)
class SocialAnswer:
    answer: str
    refused: bool = False
    refusal_reason: str | None = None
    cited_context_ids: tuple[str, ...] = ()
    kind: str = "social"


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
        collector = UsageCollector(user_id)
        context_token = activate(collector)
        try:
            return await self._ask_with_usage(question, conversation_id, access, user_id, collector)
        finally:
            reset(context_token)
            if not collector.saved:
                try:
                    await collector.persist_after_error()
                except Exception:
                    logger.warning("rag_usage_persist_failed")

    async def _ask_with_usage(self, question: str, conversation_id: UUID | None,
                              access: AccessScope | None, user_id: UUID | None,
                              collector: UsageCollector) -> RAGResult:
        started = perf_counter()
        safe_question = PromptGuard(self.settings.llm_max_input_chars,
                                    self.settings.llm_max_context_chars).inspect(question, InputKind.USER).value
        greeting = social_reply(safe_question)
        if greeting is not None:
            intent = analyze_query(safe_question)
            prepared = PreparedQuestion(safe_question, safe_question, False)
            result = await self._persist(prepared, intent, [], SocialAnswer(greeting),
                                         round((perf_counter() - started) * 1000), conversation_id, user_id)
            collector.saved = True
            logger.info("rag_social_reply_completed")
            return result
        if is_casual_conversation(safe_question):
            # Validate ownership before spending any LLM tokens on a conversation.
            if conversation_id is not None:
                existing = await self.session.scalar(select(AIConversation.id).where(
                    AIConversation.id == conversation_id,
                    AIConversation.deleted_at.is_(None),
                    AIConversation.user_id == user_id,
                ))
                if existing is None:
                    raise ValueError("conversation not found")
            await enforce_casual_daily_limit(f"user:{user_id}" if user_id else "internal")
            casual = await self.llm.answer_casual(safe_question)
            # A casual response must never smuggle in uncited institutional facts.
            if re.search(r"https?://|\[[0-9]+\]|\b(?:hvnh|học viện ngân hàng)\b",
                         casual.answer, re.IGNORECASE):
                logger.warning("rag_casual_output_rejected")
                casual_text = "Mình có thể trò chuyện nhẹ với bạn. Nếu bạn cần thông tin cụ thể về Học viện, hãy hỏi riêng để mình tra nguồn nhé."
            else:
                casual_text = casual.answer
            intent = analyze_query(safe_question)
            prepared = PreparedQuestion(safe_question, safe_question, False)
            collector.attach(self.session)
            result = await self._persist(prepared, intent, [], SocialAnswer(casual_text, kind="casual"),
                                         round((perf_counter() - started) * 1000), conversation_id, user_id)
            collector.saved = True
            logger.info("rag_casual_reply_completed")
            return result
        prepared = await ConversationMemoryService(self.session, self.llm).prepare(question, conversation_id, user_id)
        prepared_at = perf_counter()
        intent = analyze_query(prepared.standalone_question)
        hits = await self.retriever.search(intent.normalized_query, access=access)
        retrieved_at = perf_counter()
        hits = self._safe_evidence(hits)
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
        generated_at = perf_counter()
        latency_ms = round((generated_at - started) * 1000)
        collector.attach(self.session)
        result = await self._persist(prepared, intent, hits, answer, latency_ms, conversation_id, user_id)
        collector.saved = True
        logger.info("rag_request_completed", extra={
            "memory_ms": round((prepared_at - started) * 1000),
            "retrieval_ms": round((retrieved_at - prepared_at) * 1000),
            "answer_ms": round((generated_at - retrieved_at) * 1000),
            "persistence_ms": round((perf_counter() - generated_at) * 1000),
            "evidence_count": len(hits), "refused": answer.refused,
        })
        return result

    def _safe_evidence(self, hits: list[RetrievalHit]) -> list[RetrievalHit]:
        """Remove unsafe retrieved material before it can influence entity checks or the LLM."""
        guard = PromptGuard(self.settings.llm_max_input_chars, self.settings.llm_max_context_chars)
        safe: list[RetrievalHit] = []
        for hit in hits:
            try:
                guard.inspect(hit.content, InputKind.CONTEXT)
                guard.inspect(hit.title, InputKind.CONTEXT)
                guard.inspect(self._source_label(hit), InputKind.CONTEXT)
            except PromptSecurityError:
                continue
            safe.append(hit)
        if len(safe) != len(hits):
            logger.warning("rag_evidence_rejected", extra={
                "candidate_count": len(hits), "rejected_count": len(hits) - len(safe),
            })
        return safe

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
    def _renumber_citation_markers(text: str, context_ids: Sequence[str]) -> str:
        mapping = {context_id: str(order) for order, context_id in enumerate(context_ids, 1)}

        def replace(match: re.Match[str]) -> str:
            ids = re.findall(r"[0-9]+", match.group(1))
            return "[" + ", ".join(mapping[item] for item in ids) + "]"

        return re.sub(r"\[([0-9]+(?:\s*,\s*[0-9]+)*)\]", replace, text)

    async def _persist(self, prepared: PreparedQuestion, intent, hits: list[RetrievalHit],
                       answer: LLMAnswer | SocialAnswer,
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
            metadata_={"refused": answer.refused, "refusal_reason": answer.refusal_reason,
                       "response_kind": answer.kind if isinstance(answer, SocialAnswer) else "grounded"})
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
