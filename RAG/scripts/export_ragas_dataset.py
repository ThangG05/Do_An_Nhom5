"""Export completed RAG evaluation results to RAGAS SingleTurnSample-compatible JSON."""
import argparse
import json
from pathlib import Path
import sys

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path("evals/results/rag-latest.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/results/ragas-dataset.json"))
    parser.add_argument("--include-refusals", action="store_true")
    parser.add_argument("--gold", type=Path, help="Override references with the normalized gold dataset")
    args = parser.parse_args(); report = json.loads(args.report.read_text(encoding="utf-8"))
    references = {}
    if args.gold:
        references = {case.get("id"): case.get("reference_answer")
                      for case in json.loads(args.gold.read_text(encoding="utf-8"))}
    samples = []
    for row in report.get("results", []):
        if row.get("error") or not row.get("reference"): continue
        if not args.include_refusals and row.get("refused"): continue
        samples.append({"user_input": row["question"], "response": row["response"],
                        "retrieved_contexts": row.get("retrieved_contexts") or [],
                        "reference": references.get(row.get("id")) or row["reference"], "case_id": row.get("id")})
    if not samples: raise SystemExit("No completed samples with references; run scripts.evaluate_rag first")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ragas_samples={len(samples)} output={args.output}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    main()
