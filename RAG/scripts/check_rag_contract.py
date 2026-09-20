import asyncio
import sys
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService
from app.llm.contracts import ContextBlock
from app.services.llm import close_llm, get_llm_provider
from app.services.qdrant import close_qdrant


async def main() -> None:
    question = "Chuẩn đầu ra ngoại ngữ VSTEP cho sinh viên Học viện Ngân hàng như thế nào?"
    embedder = get_embedding_provider()
    try:
        hits = await RetrievalService(embedder).search(question)
        blocks = [ContextBlock(id=str(i), content=hit.content, source_label=hit.title[:500]) for i, hit in enumerate(hits, 1)]
        answer = await get_llm_provider().answer(question, blocks)
        print(f"refused={str(answer.refused).lower()} cited_context_ids={answer.cited_context_ids}")
        print(f"answer={answer.answer}")
    finally:
        await embedder.close(); await close_llm(); await close_qdrant()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
