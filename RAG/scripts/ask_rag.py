import argparse
import asyncio
from dataclasses import asdict
import json
import sys
from uuid import UUID
from app.db.session import AsyncSessionLocal, dispose_engine
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService
from app.rag.service import RAGService
from app.services.llm import close_llm, get_llm_provider
from app.services.qdrant import close_qdrant


async def main() -> None:
    parser = argparse.ArgumentParser(description="Internal end-to-end grounded RAG smoke test")
    parser.add_argument("question"); parser.add_argument("--conversation-id", type=UUID)
    args = parser.parse_args(); embedder = get_embedding_provider()
    try:
        async with AsyncSessionLocal() as session:
            result = await RAGService(session, RetrievalService(embedder, session), get_llm_provider()).ask(
                args.question, args.conversation_id)
        print(f"rag=ok refused={str(result.refused).lower()}")
        print(f"conversation_id={result.conversation_id}\nmessage_id={result.message_id}")
        print(f"rewritten_question={result.rewritten_question}")
        print(result.answer)
        print("citations=" + json.dumps([asdict(item) for item in result.citations], ensure_ascii=False))
    finally:
        await embedder.close(); await close_llm(); await close_qdrant(); await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
