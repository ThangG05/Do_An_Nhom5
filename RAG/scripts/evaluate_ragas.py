"""Run RAGAS 0.4 collection metrics over a completed, human-reviewed RAG report."""
import argparse
import asyncio
import json
from pathlib import Path
import statistics
import sys
from datetime import UTC, datetime

from app.core.config import get_settings

METRIC_NAMES = ("faithfulness", "answer_relevancy", "answer_correctness",
                "context_precision", "context_recall")

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("evals/results/ragas-dataset.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/results/ragas-latest.json"))
    parser.add_argument("--metrics", default=",".join(METRIC_NAMES))
    parser.add_argument("--limit", type=int, default=10, help="Bound judge cost; use 0 for all samples")
    parser.add_argument("--resume", action="store_true", help="Resume rows already checkpointed in --output")
    parser.add_argument("--case-delay", type=float, default=0, help="Seconds between samples for provider rate limits")
    parser.add_argument("--rate-limit-delay", type=float, default=65, help="Seconds before retrying HTTP 429")
    args = parser.parse_args()
    try:
        from ragas.llms import llm_factory
        from ragas.metrics.collections import (AnswerCorrectness, AnswerRelevancy, ContextPrecisionWithReference,
                                                ContextRecall, Faithfulness)
    except ImportError as exc:
        raise SystemExit("RAGAS is not installed. Run: pip install -r requirements-eval.txt") from exc
    settings = get_settings()
    judge_name = settings.ragas_judge_provider or settings.llm_provider
    judge_model = settings.ragas_judge_model or settings.llm_model
    judge_key = settings.ragas_judge_api_key or settings.llm_api_key
    judge_base_url = settings.ragas_judge_base_url or settings.llm_base_url
    if not judge_key: raise SystemExit("RAGAS_JUDGE_API_KEY (or LLM_API_KEY fallback) is required")
    provider = "google" if judge_name.casefold() == "gemini" else "openai"
    if provider == "google":
        from google import genai
        from openai import AsyncOpenAI
        from ragas.embeddings import GoogleEmbeddings
        google_client = genai.Client(api_key=judge_key)
        client = AsyncOpenAI(api_key=judge_key,
                             base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        embeddings = GoogleEmbeddings(client=google_client)
        judge_provider = "openai"
    else:
        from openai import AsyncOpenAI
        from ragas.embeddings import OpenAIEmbeddings
        client = AsyncOpenAI(api_key=judge_key,
                             **({"base_url": judge_base_url} if judge_base_url else {}))
        from openai import OpenAI
        embeddings = OpenAIEmbeddings(client=OpenAI(
            api_key=judge_key, **({"base_url": judge_base_url} if judge_base_url else {})))
        judge_provider = "openai"
    llm = llm_factory(judge_model, provider=judge_provider, client=client,
                      max_tokens=8192, temperature=0)
    factories = {"faithfulness": Faithfulness, "answer_relevancy": AnswerRelevancy,
                 "answer_correctness": AnswerCorrectness,
                 "context_precision": ContextPrecisionWithReference, "context_recall": ContextRecall}
    requested = [name.strip() for name in args.metrics.split(",") if name.strip()]
    unknown = set(requested) - set(factories)
    if unknown: parser.error(f"unsupported metrics: {', '.join(sorted(unknown))}")
    metrics = {name: factories[name](llm=llm, **({"embeddings": embeddings}
                                                if name in {"answer_relevancy", "answer_correctness"} else {}))
               for name in requested}
    samples = json.loads(args.dataset.read_text(encoding="utf-8"))
    if args.limit: samples = samples[:args.limit]
    rows = []
    if args.resume and args.output.exists():
        checkpoint = json.loads(args.output.read_text(encoding="utf-8"))
        rows = checkpoint.get("results", [])
    completed_ids = {row.get("case_id") for row in rows}
    for number, sample in enumerate(samples, 1):
        if sample.get("case_id") in completed_ids:
            continue
        if rows and args.case_delay:
            await asyncio.sleep(args.case_delay)
        scores = {}
        for name, metric in metrics.items():
            common = {"user_input": sample["user_input"]}
            if name in {"faithfulness", "answer_relevancy", "answer_correctness"}:
                common["response"] = sample["response"]
            if name in {"faithfulness", "context_precision", "context_recall"}:
                common["retrieved_contexts"] = sample["retrieved_contexts"]
            if name in {"answer_correctness", "context_precision", "context_recall"}:
                common["reference"] = sample["reference"]
            for attempt in range(2):
                try:
                    result = await metric.ascore(**common)
                    break
                except Exception as exc:
                    if attempt or "429" not in str(exc):
                        raise
                    print(f"case={sample.get('case_id', number)} metric={name} rate_limited retrying", flush=True)
                    await asyncio.sleep(args.rate_limit_delay)
            scores[name] = float(result.value)
        rows.append({"case_id": sample.get("case_id", str(number)), "scores": scores})
        print(f"case={rows[-1]['case_id']} " + " ".join(f"{k}={v:.3f}" for k, v in scores.items()), flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"complete": False, "results": rows}, indent=2), encoding="utf-8")
    summary = {name: statistics.fmean(row["scores"][name] for row in rows) for name in requested}
    report = {"complete": True, "generated_at": datetime.now(UTC).isoformat(), "cases": len(rows),
              "judge": {"provider": judge_name, "model": judge_model,
                        "independent_from_answer_model": (judge_name.casefold() != settings.llm_provider.casefold()
                                                          or judge_model != settings.llm_model)},
              "metrics": summary, "results": rows}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
