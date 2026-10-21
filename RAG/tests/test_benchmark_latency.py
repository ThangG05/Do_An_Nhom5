from scripts.benchmark_latency import summarize


def test_summarize_empty_results() -> None:
    assert summarize([]) is None


def test_summarize_sorted_percentiles() -> None:
    summary = summarize([300.0, 100.0, 200.0])
    assert summary == {"mean_ms": 200.0, "p50_ms": 200.0,
                       "p95_ms": 300.0, "p99_ms": 300.0, "max_ms": 300.0}
