"""Repeat representative RAG cases and report latency distribution and reliability."""
import argparse
import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
import statistics
import sys

from app.db.session import AsyncSessionLocal, dispose_engine
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService
from app.rag.service import RAGService
from app.services.llm import close_llm, get_llm_provider
from app.services.qdrant import close_qdrant


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("evals/rag-gold.json"))
    parser.add_argument("--case-ids", default="hvnh-003,hvnh-019,hvnh-023,hvnh-042,hvnh-036")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--output", type=Path, default=Path("evals/results/latency-repeated.json"))
    args = parser.parse_args()
    wanted = set(args.case_ids.split(","))
    cases = [case for case in json.loads(args.dataset.read_text(encoding="utf-8"))
             if case.get("id") in wanted and case.get("review_status") == "APPROVED"]
    if not cases:
        raise SystemExit("No matching approved cases")
    rows = []
    embedder = get_embedding_provider()
    try:
        for run_number in range(1, args.runs + 1):
            for case in cases:
                try:
                    async with asyncio.timeout(args.timeout):
                        async with AsyncSessionLocal() as session:
                            result = await RAGService(session, RetrievalService(embedder, session),
                                                      get_llm_provider()).ask(case["question"])
                            from app.models.rag import AIMessage
                            message = await session.get(AIMessage, result.message_id)
                            rows.append({"run": run_number, "case_id": case["id"],
                                         "latency_ms": message.latency_ms if message else None,
                                         "refused": result.refused, "error": None})
                except Exception as exc:
                    rows.append({"run": run_number, "case_id": case["id"], "latency_ms": None,
                                 "refused": None, "error": type(exc).__name__})
                print(f"run={run_number} case={case['id']} error={rows[-1]['error'] or '-'}", flush=True)
        values = sorted(row["latency_ms"] for row in rows if row["latency_ms"] is not None)
        percentile = lambda p: values[min(round((len(values) - 1) * p), len(values) - 1)]
        report = {"generated_at": datetime.now(UTC).isoformat(), "runs": args.runs,
                  "cases_per_run": len(cases), "requests": len(rows),
                  "success_rate": len(values) / len(rows),
                  "latency": {"mean_ms": round(statistics.fmean(values), 1),
                              "p50_ms": percentile(.50), "p95_ms": percentile(.95),
                              "p99_ms": percentile(.99), "max_ms": max(values)}, "results": rows}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({key: report[key] for key in ("requests", "success_rate", "latency")}, ensure_ascii=False))
    finally:
        await embedder.close(); await close_llm(); await close_qdrant(); await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
