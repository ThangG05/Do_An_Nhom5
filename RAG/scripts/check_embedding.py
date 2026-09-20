"""Minimal Gemini embedding check without printing source text or vectors."""
import asyncio

from app.rag.embeddings import EmbeddingError, GeminiEmbeddingService


async def main() -> None:
    service = None
    try:
        service = GeminiEmbeddingService()
        vectors = await service.embed_documents(
            ["Quy chế đào tạo của Học viện Ngân hàng."],
            "HVNH embedding health check",
        )
        print("embedding=ok")
        print(f"vectors={len(vectors)}, dimensions={len(vectors[0])}")
    except EmbeddingError:
        print("embedding=error (provider_unavailable)")
        raise SystemExit(1) from None
    finally:
        if service is not None:
            await service.close()


if __name__ == "__main__":
    asyncio.run(main())
