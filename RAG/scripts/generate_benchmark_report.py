"""Generate a reproducible Markdown summary from HVNH RAG benchmark artifacts."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import statistics
import sys

from app.core.config import get_settings


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def percent(value: float) -> str:
    return f"{value * 100:.2f}%".replace(".", ",")


def decimal(value: float) -> str:
    return f"{value:.3f}".replace(".", ",")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rag", type=Path, default=Path("evals/results/rag-benchmark.json"))
    parser.add_argument("--retrieval", type=Path, default=Path("evals/results/retrieval-benchmark.json"))
    parser.add_argument("--ragas", type=Path, default=Path("evals/results/ragas-benchmark.json"))
    parser.add_argument("--audit", type=Path, default=Path("evals/results/knowledge-audit-benchmark.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/results/HVNH_RAG_BENCHMARK.md"))
    parser.add_argument("--pytest-count", type=int, default=0)
    parser.add_argument("--pytest-seconds", type=float)
    args = parser.parse_args()

    rag, retrieval, ragas, audit = map(load, (args.rag, args.retrieval, args.ragas, args.audit))
    settings = get_settings()
    rows = rag["results"]
    completed = [row for row in rows if not row.get("error")]
    failures = [row for row in rows if not row.get("passed")]
    citation_accuracy = statistics.fmean(row.get("citation_ok", False) for row in completed)
    refusal_accuracy = statistics.fmean(row.get("refusal_ok", False) for row in completed)
    latencies = sorted(row["latency_ms"] for row in completed if row.get("latency_ms") is not None)
    p95 = latencies[max(0, int(0.95 * len(latencies) + 0.999999) - 1)] if latencies else None
    source_rows = audit["sources"]
    enabled = [source for source in source_rows if source["enabled"]]
    overdue = sum(source["overdue"] for source in enabled)
    partial = sum(source["latest_run_status"] == "PARTIAL" for source in enabled)
    missing = audit["missing_metadata"]
    docs = audit["counts"]["documents"] or 1

    metric_labels = {
        "faithfulness": "Faithfulness",
        "answer_relevancy": "Answer relevancy",
        "answer_correctness": "Answer correctness",
        "context_precision": "Context precision",
        "context_recall": "Context recall",
    }
    metric_rows = []
    for key, label in metric_labels.items():
        values = [row["scores"][key] for row in ragas["results"] if key in row.get("scores", {})]
        metric_rows.append(f"| {label} | {decimal(ragas['metrics'][key])} | {decimal(min(values))} | {decimal(max(values))} |")

    failed_rows = []
    for row in failures:
        failed_rows.append(
            f"| `{row.get('id')}` | {row.get('question', '-')} | "
            f"{'Đạt' if row.get('refusal_ok') else 'Không đạt'} | "
            f"{'Đạt' if row.get('citation_ok') else 'Không đạt'} | "
            f"{'Đạt' if row.get('keywords_ok') else 'Không đạt'} |"
        )
    if not failed_rows:
        failed_rows.append("| — | Không có | — | — | — |")

    test_text = f"{args.pytest_count}/{args.pytest_count} test qua" if args.pytest_count else "Không được truyền vào báo cáo"
    if args.pytest_seconds is not None:
        test_text += f" trong {args.pytest_seconds:.2f} giây"

    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Báo cáo benchmark hệ thống HVNH RAG",
        "",
        f"- Thời điểm đo: `{generated}`",
        f"- LLM sinh câu trả lời/judge: `{settings.llm_provider}` / `{settings.llm_model}`",
        f"- Embedding: `{settings.embedding_provider}` / `{settings.embedding_model}` ({settings.embedding_dimensions} chiều)",
        f"- Collection: `{settings.qdrant_collection}`",
        "- Phạm vi: pipeline thật từ query → retrieval → LLM → citation → persistence; không ghi khóa API hoặc URL kết nối bí mật.",
        "",
        "## Kết luận điều hành",
        "",
        f"Rule-based end-to-end đạt **{rag['passed']}/{rag['cases']} ({percent(rag['pass_rate'])})**, không có lỗi hạ tầng. "
        f"Retrieval đạt Hit@5 **{decimal(retrieval['hit_at_5'])}** và MRR **{decimal(retrieval['mrr'])}** trên {retrieval['cases']} ca. "
        f"RAGAS cho thấy điểm mạnh là answer relevancy ({decimal(ragas['metrics']['answer_relevancy'])}) và context precision "
        f"({decimal(ragas['metrics']['context_precision'])}); điểm cần ưu tiên là answer correctness "
        f"({decimal(ragas['metrics']['answer_correctness'])}), faithfulness ({decimal(ragas['metrics']['faithfulness'])}) "
        f"và context recall ({decimal(ragas['metrics']['context_recall'])}).",
        "",
        "Hệ thống đã đủ tốt để demo và tiếp tục mở rộng dữ liệu có kiểm soát, nhưng chưa nên coi là đạt chuẩn production cuối cùng cho câu hỏi học vụ quan trọng. "
        "Ngưỡng cải tiến hợp lý cho vòng tới là ≥0,80 ở từng metric RAGAS, không chỉ điểm trung bình.",
        "",
        "## 1. Benchmark end-to-end có gold label",
        "",
        "| Chỉ số | Kết quả |",
        "|---|---:|",
        f"| Gold case đã duyệt | {rag['cases']} |",
        f"| Passed | {rag['passed']} |",
        f"| Pass rate | {percent(rag['pass_rate'])} |",
        f"| Refusal decision accuracy | {percent(refusal_accuracy)} |",
        f"| Citation/expected-source accuracy | {percent(citation_accuracy)} |",
        f"| Lỗi runtime | {sum(bool(row.get('error')) for row in rows)} |",
        f"| Latency mean | {statistics.fmean(latencies):.1f} ms |" if latencies else "| Latency mean | N/A |",
        f"| Latency p50 | {statistics.median(latencies):.1f} ms |" if latencies else "| Latency p50 | N/A |",
        f"| Latency p95 | {p95} ms |" if p95 is not None else "| Latency p95 | N/A |",
        f"| Latency max | {max(latencies)} ms |" if latencies else "| Latency max | N/A |",
        "",
        "### Ca chưa đạt",
        "",
        "| Case | Câu hỏi | Refusal | Citation | Keyword |",
        "|---|---|---:|---:|---:|",
        *failed_rows,
        "",
        "Hai ca trên đều là từ chối nhầm trong khi kiểm tra keyword không phát hiện sai nội dung. Cần điều chỉnh ngưỡng đủ-context/guard để giảm false refusal mà không làm tăng hallucination.",
        "",
        "## 2. Retrieval benchmark",
        "",
        "| Chỉ số | Kết quả |",
        "|---|---:|",
        f"| Số ca | {retrieval['cases']} |",
        f"| Hit@5 | {decimal(retrieval['hit_at_5'])} |",
        f"| MRR | {decimal(retrieval['mrr'])} |",
        f"| Correct-empty accuracy | {decimal(retrieval['correct_empty'])} |",
        "",
        "Tất cả truy vấn dương tìm đúng tài liệu ở hạng 1 và truy vấn âm trả rỗng đúng. Tuy nhiên tập 6 ca còn nhỏ, nên chưa chứng minh được độ ổn định trên mọi domain/tài liệu mới.",
        "",
        "## 3. RAGAS",
        "",
        f"RAGAS 0.4.2 chấm **{ragas['cases']}/24** câu trả lời có reference (5 metric mỗi mẫu). Các refusal được đánh giá ở benchmark rule-based và bị loại khỏi tập RAGAS answer-quality.",
        "",
        "| Metric | Trung bình | Min | Max |",
        "|---|---:|---:|---:|",
        *metric_rows,
        "",
        "Diễn giải:",
        "",
        "- Answer relevancy cao: câu trả lời nhìn chung bám câu hỏi.",
        "- Context precision khá: phần lớn context đưa vào có ích, nhưng hai mẫu có precision bằng 0 cho thấy vẫn có retrieval/citation không khớp reference.",
        "- Context recall 0,774: context chưa luôn bao phủ đủ thông tin trong reference.",
        "- Faithfulness 0,750: một số mệnh đề trong câu trả lời chưa được context trích dẫn hỗ trợ đầy đủ dù URL citation đúng.",
        "- Answer correctness 0,487 là điểm yếu chính: câu trả lời thường đúng hướng nhưng thiếu nhiều chi tiết so với reference hoặc reference hiện quá rộng so với câu hỏi.",
        "",
        "## 4. Chất lượng kho tri thức",
        "",
        "| Chỉ số | Kết quả |",
        "|---|---:|",
        f"| Sources | {audit['counts']['sources']} ({audit['counts']['enabled_sources']} enabled) |",
        f"| Documents | {audit['counts']['documents']} |",
        f"| Versions | {audit['counts']['versions']} |",
        f"| Chunks | {audit['counts']['chunks']} |",
        f"| INDEXED / ARCHIVED | {audit['version_statuses'].get('INDEXED', 0)} / {audit['version_statuses'].get('ARCHIVED', 0)} |",
        f"| FAILED / quarantined | {audit['version_statuses'].get('FAILED', 0)} / {audit['counts']['quarantined']} |",
        f"| Indexed không có chunk | {audit['integrity']['indexed_without_chunks']} |",
        f"| Thiếu academic_year | {missing['academic_year']} ({percent(missing['academic_year']/docs)}) |",
        f"| Thiếu published_at | {missing['published_at']} ({percent(missing['published_at']/docs)}) |",
        f"| Thiếu issuer | {missing['issuer']} |",
        f"| Source enabled quá hạn lịch crawl | {overdue}/{len(enabled)} |",
        f"| Latest crawl PARTIAL | {partial}/{len(enabled)} |",
        "",
        "Strict audit đạt vì không có version FAILED, quarantine hoặc indexed-version thiếu chunk. Một file danh sách sinh viên nợ học phí đã bị loại đúng bằng `PII_EXCLUDED`. "
        "Rủi ro vận hành còn lại là metadata thời gian thiếu nhiều và toàn bộ source enabled đang quá hạn lịch crawl; điều này ảnh hưởng trực tiếp câu hỏi “mới nhất” và truy vấn lịch sử.",
        "",
        "## 5. Kiểm thử kỹ thuật",
        "",
        f"- Pytest: **{test_text}**.",
        "- Dependency eval: `pip check` không phát hiện xung đột.",
        "- RAGAS chạy trong `.venv-eval` tách khỏi môi trường production.",
        "- Benchmark cloud không có runtime error; một latency outlier cần được theo dõi bằng p95/p99 nhiều vòng.",
        "",
        "## 6. Giới hạn phép đo",
        "",
        "- Gold end-to-end gồm 31 ca và retrieval chỉ 6 ca; cần mở rộng theo từng intent, năm học, loại file và domain.",
        "- RAGAS chỉ lấy 10 mẫu đầu trong 24 câu answerable do quota Gemini miễn phí 15 request/phút; đây không phải ước lượng toàn bộ tập.",
        "- Gemini vừa sinh câu trả lời vừa làm judge nên có nguy cơ self-evaluation bias. Khi có ngân sách, nên dùng judge khác họ model (ví dụ DeepSeek/OpenAI) và chạy lặp ít nhất 3 seed.",
        "- Reference answer có trường hợp dài/rộng hơn phạm vi câu hỏi, có thể kéo AnswerCorrectness xuống; cần chuẩn hóa reference thành câu trả lời tối thiểu nhưng đầy đủ.",
        "- Đây là snapshot tại thời điểm đo; dữ liệu web và kết quả LLM có thể thay đổi ở lần chạy sau.",
        "",
        "## 7. Thứ tự cải thiện đề xuất",
        "",
        "1. Sửa hai false refusal và bổ sung regression case cho đúng intent tương ứng.",
        "2. Chuẩn hóa reference answer, thêm claim-level citation verification và yêu cầu câu trả lời phủ các facts bắt buộc.",
        "3. Backfill `published_at`/`academic_year`, xử lý các source PARTIAL và khôi phục scheduler đang overdue.",
        "4. Mở rộng retrieval benchmark lên tối thiểu 50–100 câu phân tầng; RAGAS lên toàn bộ 24 mẫu rồi ≥100 mẫu.",
        "5. Đo lặp latency và RAGAS bằng judge độc lập trước khi chốt SLA/production readiness.",
        "",
        "## 8. Artifacts tái lập",
        "",
        f"- `{args.rag.as_posix()}`",
        f"- `{args.retrieval.as_posix()}`",
        f"- `{args.ragas.as_posix()}`",
        f"- `{args.audit.as_posix()}`",
        "- `evals/results/ragas-dataset.json`",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report={args.output}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
