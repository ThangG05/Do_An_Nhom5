"""Aggregate checkpointed RAGAS runs and enforce acceptance thresholds."""
import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import statistics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--case-ids", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum", type=float, default=0.80)
    args = parser.parse_args()
    requested = [value.strip() for value in args.case_ids.split(",") if value.strip()]
    latest: dict[str, dict] = {}
    provenance: dict[str, str] = {}
    for path in args.runs:
        report = json.loads(path.read_text(encoding="utf-8"))
        for row in report.get("results", []):
            case_id = row.get("case_id")
            if case_id in requested:
                latest[case_id] = row
                provenance[case_id] = path.as_posix()
    missing = [case_id for case_id in requested if case_id not in latest]
    if missing:
        parser.error(f"missing scored cases: {', '.join(missing)}")
    rows = [{**latest[case_id], "source_report": provenance[case_id]} for case_id in requested]
    metric_names = sorted(set.intersection(*(set(row["scores"]) for row in rows)))
    metrics = {name: statistics.fmean(row["scores"][name] for row in rows)
               for name in metric_names}
    accepted = all(metrics.get(name, 0) >= args.minimum
                   for name in ("faithfulness", "answer_correctness"))
    output = {
        "complete": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "cases": len(rows),
        "minimum": args.minimum,
        "accepted": accepted,
        "metrics": metrics,
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"accepted": accepted, "cases": len(rows), "metrics": metrics},
                     ensure_ascii=False))
    if not accepted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
