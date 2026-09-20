"""Review and approve individual cases in the local RAG gold dataset."""
import argparse
import json
from pathlib import Path
import sys

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("list", "show", "approve", "reject")); parser.add_argument("--id")
    parser.add_argument("--dataset", type=Path, default=Path("evals/rag-gold-draft.json"))
    parser.add_argument("--answer", help="Human-verified reference answer"); parser.add_argument("--keywords", nargs="*", default=None)
    parser.add_argument("--notes"); args = parser.parse_args()
    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    if args.action == "list":
        for case in cases: print(f"{case['id']} {case['review_status']}: {case['question']}")
        return
    if not args.id: parser.error("--id is required for show/approve/reject")
    case = next((item for item in cases if item["id"] == args.id), None)
    if case is None: parser.error(f"unknown case id: {args.id}")
    if args.action == "show": print(json.dumps(case, ensure_ascii=False, indent=2)); return
    if args.action == "approve":
        if not case["expected_refused"] and not (args.answer or case.get("reference_answer")):
            parser.error("answered cases require --answer before approval")
        case["review_status"] = "APPROVED"
        if args.answer: case["reference_answer"] = args.answer
        if args.keywords is not None: case["answer_keywords"] = args.keywords
    else: case["review_status"] = "REJECTED"
    if args.notes is not None: case["review_notes"] = args.notes
    args.dataset.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"case={case['id']} status={case['review_status']}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    main()
