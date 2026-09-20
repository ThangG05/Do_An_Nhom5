"""Select an explicit, reproducible subset from a RAGAS dataset."""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ids", required=True, help="Comma-separated case IDs in output order")
    args = parser.parse_args()
    rows = json.loads(args.input.read_text(encoding="utf-8"))
    by_id = {row.get("case_id") or row.get("id"): row for row in rows}
    requested = [value.strip() for value in args.ids.split(",") if value.strip()]
    missing = [case_id for case_id in requested if case_id not in by_id]
    if missing:
        parser.error(f"unknown case IDs: {', '.join(missing)}")
    selected = [by_id[case_id] for case_id in requested]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"selected={len(selected)} output={args.output}")


if __name__ == "__main__":
    main()
