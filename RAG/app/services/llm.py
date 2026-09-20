import asyncio
import json

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.llm.contracts import (
    ContextBlock,
    ConversationSummary,
    ConversationTurn,
    LLMAnswer,
    LLMConfigurationError,
    LLMProvider,
    LLMServiceError,
    QuestionRewrite,
)
from app.llm.prompts import (REWRITE_SYSTEM_INSTRUCTION, SUMMARY_SYSTEM_INSTRUCTION,
                             SYSTEM_INSTRUCTION, answer_guidance)
from app.llm.security import InputKind, PromptGuard, PromptSecurityError


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.llm_api_key:
            raise LLMConfigurationError("LLM_API_KEY is not configured")
        self.settings = settings
        self.guard = PromptGuard(settings.llm_max_input_chars, settings.llm_max_context_chars)
        self.client = genai.Client(api_key=settings.llm_api_key)

    async def _generate_content(self, payload: str, config: types.GenerateContentConfig):
        max_retries = self.settings.llm_max_retries
        for attempt in range(max_retries + 1):
            try:
                async with asyncio.timeout(self.settings.llm_timeout_seconds):
                    return await self.client.aio.models.generate_content(
                        model=self.settings.llm_model,
                        contents=payload,
                        config=config,
                    )
            except TimeoutError as exc:
                if attempt == max_retries:
                    raise LLMServiceError("timeout", "asyncio_timeout") from exc
            except APIError as exc:
                status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                if status_code not in {429, 500, 502, 503, 504} or attempt == max_retries:
                    code = {
                        400: "invalid_request",
                        401: "invalid_api_key",
                        403: "access_denied",
                        404: "model_unavailable",
                        429: "rate_limited",
                        500: "provider_unavailable",
                        502: "provider_unavailable",
                        503: "provider_unavailable",
                        504: "timeout",
                    }.get(status_code, "provider_unavailable")
                    raise LLMServiceError(code, f"api_{status_code or 'unknown'}") from exc

            delay = self.settings.llm_retry_base_seconds * (2 ** attempt)
            await asyncio.sleep(delay)

        raise LLMServiceError("provider_unavailable", "retry_exhausted")

    async def answer(self, question: str, context: list[ContextBlock]) -> LLMAnswer:
        safe_question = self.guard.inspect(question, InputKind.USER).value
        safe_context: list[dict[str, str]] = []
        total_context_chars = 0
        for block in context:
            content = self.guard.inspect(block.content, InputKind.CONTEXT).value
            total_context_chars += len(content)
            if total_context_chars > self.settings.llm_max_context_chars:
                raise PromptSecurityError("context_too_long")
            safe_context.append({"id": block.id, "source_label": block.source_label, "content": content})

        payload = json.dumps(
            {"USER_QUESTION": safe_question, "ANSWER_GUIDANCE": answer_guidance(safe_question),
             "CONTEXT_BLOCKS": safe_context},
            ensure_ascii=False,
        )
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=self.settings.llm_temperature,
            max_output_tokens=self.settings.llm_max_output_tokens,
            response_mime_type="application/json",
            response_schema=LLMAnswer,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            safety_settings=[
                types.SafetySetting(category=category, threshold="BLOCK_MEDIUM_AND_ABOVE")
                for category in (
                    "HARM_CATEGORY_HARASSMENT",
                    "HARM_CATEGORY_HATE_SPEECH",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "HARM_CATEGORY_DANGEROUS_CONTENT",
                )
            ],
        )
        try:
            response = await self._generate_content(payload, config)
            if response.parsed is not None:
                answer = LLMAnswer.model_validate(response.parsed)
            else:
                if not response.text:
                    raise LLMServiceError("unsafe_or_empty_response", "empty_response")
                answer = LLMAnswer.model_validate_json(response.text)
            allowed_ids = {block["id"] for block in safe_context}
            if any(citation_id not in allowed_ids for citation_id in answer.cited_context_ids):
                raise LLMServiceError("invalid_response", "unknown_citation_id")
            safe_answer = self.guard.inspect_output(answer.answer).value
            return answer.model_copy(update={"answer": safe_answer})
        except PromptSecurityError:
            raise
        except LLMServiceError:
            raise
        except (ValidationError, ValueError, TypeError) as exc:
            raise LLMServiceError("invalid_response", type(exc).__name__) from exc
        except Exception as exc:
            raise LLMServiceError("provider_unavailable", type(exc).__name__) from exc

    async def _structured_memory(self, payload: dict, schema: type[BaseModel],
                                 instruction: str) -> BaseModel:
        config = types.GenerateContentConfig(
            system_instruction=instruction, temperature=0,
            max_output_tokens=min(self.settings.llm_max_output_tokens, 1024),
            response_mime_type="application/json", response_schema=schema,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        try:
            response = await self._generate_content(json.dumps(payload, ensure_ascii=False), config)
            if response.parsed is not None: return schema.model_validate(response.parsed)
            if not response.text: raise LLMServiceError("unsafe_or_empty_response", "empty_memory_response")
            return schema.model_validate_json(response.text)
        except LLMServiceError: raise
        except (ValidationError, ValueError, TypeError) as exc:
            raise LLMServiceError("invalid_response", type(exc).__name__) from exc

    def _safe_history(self, history: list[ConversationTurn]) -> list[dict[str, str]]:
        safe, total = [], 0
        for turn in history:
            kind = InputKind.USER if turn.role == "USER" else InputKind.CONTEXT
            content = self.guard.inspect(turn.content, kind).value
            total += len(content)
            if total > self.settings.llm_max_context_chars: raise PromptSecurityError("history_too_long")
            safe.append({"role": turn.role, "content": content})
        return safe

    async def rewrite_question(self, question: str, history: list[ConversationTurn],
                               summary: str | None) -> QuestionRewrite:
        safe_question = self.guard.inspect(question, InputKind.USER).value
        safe_summary = self.guard.inspect(summary, InputKind.CONTEXT).value if summary else None
        result = await self._structured_memory({"SUMMARY": safe_summary, "HISTORY": self._safe_history(history),
            "LATEST_USER_QUESTION": safe_question}, QuestionRewrite, REWRITE_SYSTEM_INSTRUCTION)
        assert isinstance(result, QuestionRewrite)
        standalone = self.guard.inspect_output(result.standalone_question).value
        return result.model_copy(update={"standalone_question": standalone})

    async def summarize_conversation(self, previous_summary: str | None,
                                     history: list[ConversationTurn]) -> ConversationSummary:
        safe_summary = self.guard.inspect(previous_summary, InputKind.CONTEXT).value if previous_summary else None
        result = await self._structured_memory({"PREVIOUS_SUMMARY": safe_summary,
            "HISTORY_TO_SUMMARIZE": self._safe_history(history)}, ConversationSummary,
            SUMMARY_SYSTEM_INSTRUCTION)
        assert isinstance(result, ConversationSummary)
        summary = self.guard.inspect_output(result.summary).value[:self.settings.conversation_summary_max_chars]
        return result.model_copy(update={"summary": summary})

    async def close(self) -> None:
        await self.client.aio.aclose()


_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        settings = get_settings()
        provider_name = settings.llm_provider.strip().lower()
        if provider_name == "gemini":
            _provider = GeminiProvider()
        elif provider_name == "deepseek":
            from app.llm.providers.deepseek import DeepSeekProvider

            try:
                _provider = DeepSeekProvider(settings=settings)
            except RuntimeError as exc:
                raise LLMConfigurationError(str(exc)) from None
        else:
            raise LLMConfigurationError("Unsupported LLM provider")
    return _provider


async def close_llm() -> None:
    global _provider
    if _provider is not None:
        await _provider.close()
        _provider = None
