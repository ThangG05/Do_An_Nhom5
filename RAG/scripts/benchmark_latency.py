"""Repeat representative RAG cases and report latency distribution and reliability."""
import argparse
import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

from app.db.session import AsyncSessionLocal, dispose_engine
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService
from app.rag.service import RAGService
from app.services.llm import close_llm, get_llm_provider
from app.services.qdrant import close_qdrant


def summarize(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    percentile = lambda p: ordered[min(round((len(ordered) - 1) * p), len(ordered) - 1)]
    return {"mean_ms": round(statistics.fmean(ordered), 1),
            "p50_ms": round(percentile(.50), 1), "p95_ms": round(percentile(.95), 1),
            "p99_ms": round(percentile(.99), 1), "max_ms": round(ordered[-1], 1)}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("evals/rag-gold.json"))
    parser.add_argument("--case-ids", default="hvnh-003,hvnh-019,hvnh-023,hvnh-042,hvnh-036")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--output", type=Path, default=Path("evals/results/latency-repeated.json"))
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be at least 1")
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
                started = perf_counter()
                try:
                    async with asyncio.timeout(args.timeout):
                        async with AsyncSessionLocal() as session:
                            result = await RAGService(session, RetrievalService(embedder, session),
                                                      get_llm_provider()).ask(case["question"])
                            from app.models.rag import AIMessage
                            message = await session.get(AIMessage, result.message_id)
                            rows.append({"run": run_number, "case_id": case["id"],
                                         "latency_ms": round((perf_counter() - started) * 1000, 1),
                                         "generation_latency_ms": message.latency_ms if message else None,
                                         "refused": result.refused, "error": None})
                except Exception as exc:
                    rows.append({"run": run_number, "case_id": case["id"], "latency_ms": None,
                                 "elapsed_ms": round((perf_counter() - started) * 1000, 1),
                                 "refused": None, "error": type(exc).__name__})
                print(f"run={run_number} case={case['id']} error={rows[-1]['error'] or '-'}", flush=True)
        values = [row["latency_ms"] for row in rows if row["latency_ms"] is not None]
        report = {"generated_at": datetime.now(UTC).isoformat(), "runs": args.runs,
                  "cases_per_run": len(cases), "requests": len(rows),
                  "success_rate": len(values) / len(rows),
                  "latency": summarize(values),
                  "first_pass_latency": summarize([row["latency_ms"] for row in rows
                                                   if row["run"] == 1 and row["latency_ms"] is not None]),
                  "repeat_pass_latency": summarize([row["latency_ms"] for row in rows
                                                    if row["run"] > 1 and row["latency_ms"] is not None]),
                  "results": rows}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({key: report[key] for key in (
            "requests", "success_rate", "latency", "first_pass_latency", "repeat_pass_latency"
        )}, ensure_ascii=False))
        if not values:
            raise SystemExit("All benchmark requests failed; inspect error types in the output file")
    finally:
        await embedder.close(); await close_llm(); await close_qdrant(); await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
