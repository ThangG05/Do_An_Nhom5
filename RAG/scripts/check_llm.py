"""Minimal Gemini connectivity check without printing prompts or generated text."""
import asyncio

from app.llm.contracts import ContextBlock
from app.services.llm import LLMConfigurationError, LLMServiceError, close_llm, get_llm_provider


async def main() -> None:
    provider = None
    try:
        provider = get_llm_provider()
        result = await provider.answer(
            "Tên hệ thống trong ngữ cảnh là gì?",
            [ContextBlock(id="health-check", source_label="Health check",
                          content="Tên hệ thống là HVNH Hub.")],
        )
        print("llm=ok")
        print(f"structured_output=ok, refused={str(result.refused).lower()}")
    except LLMConfigurationError:
        print("llm=error (configuration)")
        raise SystemExit(1) from None
    except LLMServiceError as exc:
        print(f"llm=error ({exc.code})")
        print(f"diagnostic={exc.diagnostic}")
        raise SystemExit(1) from None
    finally:
        if provider is not None:
            await close_llm()


if __name__ == "__main__":
    asyncio.run(main())
