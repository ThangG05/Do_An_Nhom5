"""Standalone Gemini client for advisory Study-library moderation.

This client intentionally does not import or initialize the RAG application.
"""

from __future__ import annotations

import asyncio

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel

from src.config import settings


class StudyModerationLLM:
    def __init__(self) -> None:
        if not settings.STUDY_MODERATION_API_KEY:
            raise ValueError("STUDY_MODERATION_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.STUDY_MODERATION_API_KEY)

    async def generate_structured(self, instruction: str, payload: str, schema: type[BaseModel], *,
                                  max_output_tokens: int = 550) -> BaseModel:
        config = types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
            response_schema=schema,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        for attempt in range(settings.STUDY_MODERATION_MAX_RETRIES + 1):
            try:
                async with asyncio.timeout(settings.STUDY_MODERATION_TIMEOUT_SECONDS):
                    response = await self.client.aio.models.generate_content(
                        model=settings.STUDY_MODERATION_MODEL,
                        contents=payload,
                        config=config,
                    )
                if response.parsed is not None:
                    return schema.model_validate(response.parsed)
                if response.text:
                    return schema.model_validate_json(response.text)
                raise ValueError("empty_moderation_response")
            except (APIError, TimeoutError) as exc:
                status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                retryable = isinstance(exc, TimeoutError) or status in {429, 500, 502, 503, 504}
                if not retryable or attempt == settings.STUDY_MODERATION_MAX_RETRIES:
                    raise
                await asyncio.sleep(min(2 ** attempt, 8))
        raise RuntimeError("moderation_retry_exhausted")

    async def close(self) -> None:
        await self.client.aio.aclose()
