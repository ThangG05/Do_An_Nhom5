"""Diagnostic for claim-level citation failures; prints no credentials or hidden prompts."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

from app.db.session import AsyncSessionLocal, dispose_engine
from app.llm.contracts import ContextBlock
from app.rag.citation_verifier import verify_claim_citations
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService, analyze_query
from app.rag.service import RAGService
from app.services.llm import close_llm, get_llm_provider
from app.services.qdrant import close_qdrant


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--dataset", type=Path, default=Path("evals/rag-gold.json"))
    args = parser.parse_args()
    case = next(item for item in json.loads(args.dataset.read_text(encoding="utf-8"))
                if item.get("id") == args.case_id)
    embedder = get_embedding_provider()
    try:
        async with AsyncSessionLocal() as session:
            intent = analyze_query(case["question"])
            hits = await RetrievalService(embedder, session).search(intent.normalized_query)
            blocks = [ContextBlock(id=str(index), content=hit.content,
                                   source_label=RAGService._source_label(hit),
                                   source_key=hit.document_id)
                      for index, hit in enumerate(hits, 1)]
            answer = await get_llm_provider().answer(case["question"], blocks)
            issues = verify_claim_citations(answer, blocks, case["question"])
            print(json.dumps({"answer": answer.answer, "cited_context_ids": answer.cited_context_ids,
                              "issues": [{"code": issue.code, "claim": issue.claim,
                                          "detail": issue.detail} for issue in issues]},
                             ensure_ascii=False, indent=2))
    finally:
        await embedder.close(); await close_llm(); await close_qdrant(); await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
