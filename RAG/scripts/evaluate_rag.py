import argparse
import asyncio
import json
from pathlib import Path
import re
import statistics
import sys

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.rag import AIConversation, AIMessage, AIMessageCitation
from app.rag.embeddings import get_embedding_provider
from app.rag.retriever import RetrievalService
from app.rag.service import RAGService
from app.services.llm import close_llm, get_llm_provider
from app.services.qdrant import close_qdrant

_FACT_STOPWORDS = {"của", "và", "là", "có", "cho", "trong", "về", "được", "những", "theo", "với", "một", "các"}


def _fact_supported(fact: str, answer: str) -> bool:
    fact_tokens = {token for token in re.findall(r"[\wÀ-ỹ]+", fact.casefold())
                   if len(token) > 2 and token not in _FACT_STOPWORDS}
    answer_tokens = set(re.findall(r"[\wÀ-ỹ]+", answer.casefold()))
    overlap = len(fact_tokens & answer_tokens)
    return not fact_tokens or overlap >= min(5, max(2, round(len(fact_tokens) * 0.30)))

async def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate grounded answers against a human-reviewed dataset")
    parser.add_argument("--dataset", type=Path, default=Path("evals/rag-gold.json"))
    parser.add_argument("--include-pending", action="store_true", help="Diagnostic only; not an official gold score")
    parser.add_argument("--output", type=Path, default=Path("evals/results/rag-latest.json"))
    parser.add_argument("--case-id", help="Run one approved case")
    parser.add_argument("--case-timeout", type=float, default=120.0)
    args = parser.parse_args()
    all_cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    cases = all_cases if args.include_pending else [c for c in all_cases if c.get("review_status") == "APPROVED"]
    if args.case_id:
        cases = [case for case in cases if case.get("id") == args.case_id]
    if not cases:
        raise SystemExit("No APPROVED cases. Review with: python -m scripts.review_gold list")
    embedder = get_embedding_provider(); results = []
    try:
        for index, case in enumerate(cases, 1):
            print(f"case={case.get('id', index)} status=running", flush=True)
            try:
                async with asyncio.timeout(args.case_timeout):
                    async with AsyncSessionLocal() as session:
                        result = await RAGService(session, RetrievalService(embedder, session), get_llm_provider()).ask(case["question"])
                        assistant_message = await session.get(AIMessage, result.message_id)
                        latency_ms = assistant_message.latency_ms if assistant_message else None
                        conversation = await session.get(AIConversation, result.conversation_id)
                        conversation.metadata_ = {**(conversation.metadata_ or {}), "evaluation": True,
                                                  "evaluation_dataset": args.dataset.name, "evaluation_case_id": case.get("id")}
                        await session.commit()
                        retrieved_contexts = list((await session.scalars(
                            select(AIMessageCitation.quoted_text)
                            .where(AIMessageCitation.message_id == result.message_id)
                            .order_by(AIMessageCitation.citation_order)
                        )).all())
            except (TimeoutError, Exception) as exc:
                row = {"id": case.get("id"), "passed": False, "error": type(exc).__name__}
                results.append(row)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps({"complete": False, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"case={case.get('id', index)} result=error error={type(exc).__name__}", flush=True)
                continue
            refusal_ok = result.refused == case["expected_refused"]
            if case["expected_refused"]:
                citation_ok = not result.citations
            else:
                expected_url = case.get("expected_source_url")
                expected_title = (case.get("expected_source_title") or case.get("expected_source_title_contains") or "").casefold()
                citation_ok = any((expected_url and citation.source_url == expected_url)
                                  or (expected_title and expected_title in citation.title.casefold())
                                  for citation in result.citations)
            answer_folded = result.answer.casefold(); keywords = case.get("answer_keywords") or []
            keywords_ok = all(keyword.casefold() in answer_folded for keyword in keywords)
            required_facts = case.get("required_facts") or []
            facts_passed = sum(_fact_supported(fact, result.answer) for fact in required_facts)
            fact_coverage = facts_passed / len(required_facts) if required_facts else 1.0
            facts_ok = case["expected_refused"] or fact_coverage >= 0.80
            ok = refusal_ok and citation_ok and keywords_ok and facts_ok
            results.append({"id": case.get("id"), "passed": ok, "refusal_ok": refusal_ok,
                            "citation_ok": citation_ok, "keywords_ok": keywords_ok, "refused": result.refused,
                            "expected_refused": case["expected_refused"],
                            "facts_ok": facts_ok, "fact_coverage": fact_coverage,
                            "citation_count": len(result.citations), "conversation_id": str(result.conversation_id),
                            "message_id": str(result.message_id),
                            "question": case["question"], "response": result.answer,
                            "reference": case.get("reference_answer"),
                            "latency_ms": latency_ms,
                            "retrieved_contexts": retrieved_contexts,
                            "citations": [{"title": citation.title, "source_url": citation.source_url}
                                          for citation in result.citations]})
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"complete": False, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"case={case.get('id', index)} result={'pass' if ok else 'fail'} refused={str(result.refused).lower()} citations={len(result.citations)}", flush=True)
        passed = sum(row["passed"] for row in results)
        completed = [row for row in results if not row.get("error")]
        latencies = [row["latency_ms"] for row in completed if row.get("latency_ms") is not None]
        latency_summary = {}
        if latencies:
            ordered = sorted(latencies)
            latency_summary = {
                "mean_ms": round(statistics.fmean(ordered), 1),
                "p50_ms": round(statistics.median(ordered), 1),
                "p95_ms": ordered[max(0, int(0.95 * len(ordered) + 0.999999) - 1)],
                "max_ms": max(ordered),
            }
        report = {"dataset": str(args.dataset), "official_score": not args.include_pending,
                  "cases": len(results), "passed": passed, "pass_rate": passed / len(results),
                  "errors": len(results) - len(completed),
                  "citation_accuracy": (sum(row["citation_ok"] for row in completed) / len(completed)
                                        if completed else 0.0),
                  "refusal_accuracy": (sum(row["refusal_ok"] for row in completed) / len(completed)
                                       if completed else 0.0),
                  "latency": latency_summary, "results": results}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"pass_rate={report['pass_rate']:.3f} cases={len(results)} official={str(report['official_score']).lower()} output={args.output}")
        if passed != len(results): raise SystemExit(1)
    finally:
        await embedder.close(); await close_llm(); await close_qdrant(); await dispose_engine()

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
