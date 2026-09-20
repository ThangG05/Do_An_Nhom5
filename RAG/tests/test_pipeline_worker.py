import asyncio

from app.knowledge.pipeline_worker import RAG_ROOT, _run_module, _safe_stage_diagnostic, next_pipeline_failure


def test_pipeline_failure_retries_then_becomes_terminal() -> None:
    assert next_pipeline_failure(0, 3) == (1, "RETRYING")
    assert next_pipeline_failure(2, 3) == (3, "RETRYING")
    assert next_pipeline_failure(3, 3) == (4, "FAILED")


def test_stage_diagnostic_keeps_aggregate_and_drops_urls() -> None:
    output = (
        b"ocr_failed url=https://example.test/private.pdf error=TimeoutError\n"
        b"pipeline=complete chunked_versions=2 index_failed=1\n"
        b"index_error_types=EmbeddingError:1\n"
    )
    diagnostic = _safe_stage_diagnostic(output)
    assert diagnostic == (
        "pipeline=complete chunked_versions=2 index_failed=1 | "
        "index_error_types=EmbeddingError:1"
    )
    assert "https://" not in diagnostic


def test_pipeline_stage_runs_from_rag_root(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class CompletedProcess:
        returncode = 0

        async def communicate(self):
            return b"pipeline=complete", b""

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured["args"] = args
        captured["cwd"] = kwargs.get("cwd")
        return CompletedProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    assert asyncio.run(_run_module("scripts.process_source", "--source-id", "test")) == 0
    assert captured["cwd"] == str(RAG_ROOT)
    assert (RAG_ROOT / "scripts" / "process_source.py").is_file()
