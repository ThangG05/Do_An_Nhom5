import argparse
import asyncio
import json
from pathlib import Path
import sys

from app.db.session import AsyncSessionLocal, dispose_engine
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService
from app.services.qdrant import close_qdrant


def _is_relevant(result, case: dict) -> bool:
    document_id = case.get("expected_document_id")
    if document_id:
        return result.document_id == document_id
    title = result.title.casefold()
    url = (result.source_url or "").casefold()
    titles = case.get("expected_title_contains") or []
    if isinstance(titles, str):
        titles = [titles]
    title_ok = not titles or any(value.casefold() in title for value in titles)
    url_part = case.get("expected_url_contains")
    url_ok = not url_part or url_part.casefold() in url
    year = case.get("expected_academic_year")
    year_ok = not year or result.academic_year == year
    return title_ok and url_ok and year_ok


async def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate hybrid retrieval Hit@K, MRR and empty-result accuracy")
    parser.add_argument("--dataset", type=Path, default=Path("evals/retrieval.json"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-hit-rate", type=float, default=0.80)
    parser.add_argument("--min-empty-accuracy", type=float, default=1.0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    embedder = get_embedding_provider()
    relevant = hits = reciprocal_rank = empty_cases = correct_empty = 0
    details: list[dict] = []
    try:
        async with AsyncSessionLocal() as session:
            service = RetrievalService(embedder, session)
            for number, case in enumerate(cases, 1):
                results = await service.search(case["query"], top_k=args.top_k)
                if case.get("expected_empty"):
                    empty_cases += 1
                    passed = not results
                    correct_empty += int(passed)
                    rank = None
                else:
                    relevant += 1
                    rank = next((index for index, result in enumerate(results, 1)
                                 if _is_relevant(result, case)), None)
                    passed = rank is not None
                    if rank:
                        hits += 1
                        reciprocal_rank += 1 / rank
                details.append({"id": case.get("id", str(number)), "category": case.get("category"),
                                "passed": passed, "rank": rank,
                                "returned_titles": [item.title for item in results]})
                print(f"case={case.get('id', number)} category={case.get('category', '-')} "
                      f"result={'pass' if passed else 'fail'} rank={rank or '-'} hits={len(results)}")
        hit_at_k = hits / relevant if relevant else 0.0
        mrr = reciprocal_rank / relevant if relevant else 0.0
        empty_accuracy = correct_empty / empty_cases if empty_cases else 1.0
        report = {"cases": len(cases), f"hit_at_{args.top_k}": hit_at_k, "mrr": mrr,
                  "correct_empty": empty_accuracy, "details": details}
        print(json.dumps({key: value for key, value in report.items() if key != "details"}, ensure_ascii=False))
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if hit_at_k < args.min_hit_rate or empty_accuracy < args.min_empty_accuracy:
            raise SystemExit(1)
    finally:
        await embedder.close()
        await close_qdrant()
        await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
