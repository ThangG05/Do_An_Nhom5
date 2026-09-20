import argparse
import asyncio
import sys
from app.db.session import AsyncSessionLocal, dispose_engine
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService
from app.services.qdrant import close_qdrant


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test BGE-M3 + Qdrant retrieval without an LLM")
    parser.add_argument("query"); parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--show-content", action="store_true")
    args = parser.parse_args(); embedder = get_embedding_provider()
    try:
        async with AsyncSessionLocal() as session:
            hits = await RetrievalService(embedder, session).search(
                args.query, top_k=args.top_k, score_threshold=args.threshold
            )
        if not hits:
            print("retrieval=no_results"); return
        print(f"retrieval=ok hits={len(hits)}")
        for rank, hit in enumerate(hits, 1):
            page = f" pages={hit.page_start}-{hit.page_end}" if hit.page_start else ""
            print(f"[{rank}] score={hit.score:.4f} type={hit.document_type} year={hit.academic_year or '-'}{page}")
            print(f"title={hit.title}\nsource={hit.source_url or '-'}")
            if args.show_content: print(f"content={hit.content[:600].replace(chr(10), ' ')}")
    finally:
        await embedder.close(); await close_qdrant(); await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
