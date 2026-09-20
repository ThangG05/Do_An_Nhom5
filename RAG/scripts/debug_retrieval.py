"""Inspect retrieval candidates without calling the answer LLM."""
import argparse
import asyncio
import sys

from app.db.session import AsyncSessionLocal, dispose_engine
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService
from app.services.qdrant import close_qdrant

async def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=10); parser.add_argument("--threshold", type=float)
    args = parser.parse_args(); embedder = get_embedding_provider()
    try:
        async with AsyncSessionLocal() as session:
            hits = await RetrievalService(embedder, session).search(args.query, top_k=args.top_k,
                                                                      score_threshold=args.threshold)
        for rank, hit in enumerate(hits, 1):
            print(f"rank={rank} score={hit.score:.4f} year={hit.academic_year or '-'} type={hit.document_type} title={hit.title}")
            print(f"url={hit.source_url}")
        print(f"hits={len(hits)}")
    finally:
        await embedder.close(); await close_qdrant(); await dispose_engine()

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
