"""DeepSeek/OpenAI-compatible provider with the secure RAG answer contract."""
import asyncio
import json
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.llm.contracts import (ContextBlock, ConversationSummary, ConversationTurn,
                               LLMAnswer, LLMServiceError, QuestionRewrite)
from app.llm.prompts import (REWRITE_SYSTEM_INSTRUCTION, SUMMARY_SYSTEM_INSTRUCTION,
                             SYSTEM_INSTRUCTION, answer_guidance)
from app.llm.security import InputKind, PromptGuard, PromptSecurityError


class DeepSeekProvider:
    provider_name = "deepseek"

    def __init__(self, settings: Settings | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is not configured")
        base_url = (self.settings.llm_base_url or "https://api.deepseek.com").rstrip("/")
        parsed = urlsplit(base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise RuntimeError("LLM_BASE_URL must be a safe HTTPS URL")
        self.guard = PromptGuard(
            self.settings.llm_max_input_chars,
            self.settings.llm_max_context_chars,
        )
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {self.settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.settings.llm_timeout_seconds),
        )

    async def answer(self, question: str, context: list[ContextBlock]) -> LLMAnswer:
        safe_question = self.guard.inspect(question, InputKind.USER).value
        safe_context: list[dict[str, str]] = []
        total_context_chars = 0
        for block in context:
            content = self.guard.inspect(block.content, InputKind.CONTEXT).value
            total_context_chars += len(content)
            if total_context_chars > self.settings.llm_max_context_chars:
                raise PromptSecurityError("context_too_long")
            safe_context.append({
                "id": block.id,
                "source_label": block.source_label,
                "content": content,
            })

        payload = json.dumps(
            {"USER_QUESTION": safe_question, "ANSWER_GUIDANCE": answer_guidance(safe_question),
             "CONTEXT_BLOCKS": safe_context},
            ensure_ascii=False,
        )
        response = await self._post_with_retry({
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION + (
                    "\nReturn valid JSON with exactly these fields: answer (string), refused (boolean), "
                    "refusal_reason (string or null), cited_context_ids (array of context ID strings)."
                )},
                {"role": "user", "content": payload},
            ],
            "temperature": self.settings.llm_temperature,
            "max_tokens": self.settings.llm_max_output_tokens,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "stream": False,
        })
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            answer = LLMAnswer.model_validate_json(content)
            allowed_ids = {block["id"] for block in safe_context}
            if any(citation_id not in allowed_ids for citation_id in answer.cited_context_ids):
                raise ValueError("unknown citation context ID")
            safe_answer = self.guard.inspect_output(answer.answer).value
            return answer.model_copy(update={"answer": safe_answer})
        except (KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
            raise LLMServiceError("invalid_response", type(exc).__name__) from exc

    async def _post_with_retry(self, body: dict) -> httpx.Response:
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                response = await self.client.post("/chat/completions", json=body)
            except httpx.TimeoutException as exc:
                if attempt == self.settings.llm_max_retries:
                    raise LLMServiceError("timeout", "httpx_timeout") from exc
            except httpx.RequestError as exc:
                if attempt == self.settings.llm_max_retries:
                    raise LLMServiceError("provider_unavailable", type(exc).__name__) from exc
            else:
                if response.is_success:
                    return response
                if response.status_code not in {429, 500, 502, 503, 504} or attempt == self.settings.llm_max_retries:
                    code = {
                        400: "invalid_request", 401: "invalid_api_key",
                        402: "insufficient_balance", 403: "access_denied",
                        404: "model_unavailable", 429: "rate_limited",
                        504: "timeout",
                    }.get(response.status_code, "provider_unavailable")
                    raise LLMServiceError(code, f"api_{response.status_code}")
            await asyncio.sleep(self.settings.llm_retry_base_seconds * (2 ** attempt))
        raise LLMServiceError("provider_unavailable", "retry_exhausted")

    def _safe_history(self, history: list[ConversationTurn]) -> list[dict[str, str]]:
        safe, total = [], 0
        for turn in history:
            kind = InputKind.USER if turn.role == "USER" else InputKind.CONTEXT
            content = self.guard.inspect(turn.content, kind).value
            total += len(content)
            if total > self.settings.llm_max_context_chars: raise PromptSecurityError("history_too_long")
            safe.append({"role": turn.role, "content": content})
        return safe

    async def _memory_request(self, instruction: str, payload: dict, schema):
        response = await self._post_with_retry({
            "model": self.settings.llm_model,
            "messages": [{"role": "system", "content": instruction},
                         {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            "temperature": 0, "max_tokens": min(self.settings.llm_max_output_tokens, 1024),
            "response_format": {"type": "json_object"}, "thinking": {"type": "disabled"}, "stream": False,
        })
        try: return schema.model_validate_json(response.json()["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
            raise LLMServiceError("invalid_response", type(exc).__name__) from exc

    async def rewrite_question(self, question: str, history: list[ConversationTurn],
                               summary: str | None) -> QuestionRewrite:
        safe_question = self.guard.inspect(question, InputKind.USER).value
        safe_summary = self.guard.inspect(summary, InputKind.CONTEXT).value if summary else None
        result = await self._memory_request(REWRITE_SYSTEM_INSTRUCTION,
            {"SUMMARY": safe_summary, "HISTORY": self._safe_history(history),
             "LATEST_USER_QUESTION": safe_question}, QuestionRewrite)
        return result.model_copy(update={"standalone_question": self.guard.inspect_output(result.standalone_question).value})

    async def summarize_conversation(self, previous_summary: str | None,
                                     history: list[ConversationTurn]) -> ConversationSummary:
        safe_summary = self.guard.inspect(previous_summary, InputKind.CONTEXT).value if previous_summary else None
        result = await self._memory_request(SUMMARY_SYSTEM_INSTRUCTION,
            {"PREVIOUS_SUMMARY": safe_summary, "HISTORY_TO_SUMMARIZE": self._safe_history(history)},
            ConversationSummary)
        return result.model_copy(update={"summary": self.guard.inspect_output(result.summary).value[:self.settings.conversation_summary_max_chars]})

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
