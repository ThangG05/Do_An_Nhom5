from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.rag.usage import (UsageCollector, activate, capture_deepseek_usage,
                           capture_gemini_usage, reset)


def test_records_each_provider_call_with_reported_counts():
    collector = UsageCollector(uuid4())
    token = activate(collector)
    try:
        capture_gemini_usage(SimpleNamespace(
            usage_metadata=SimpleNamespace(prompt_token_count=19,
                                           candidates_token_count=8,
                                           total_token_count=30),
            model_version="gemini-test"), "fallback")
        capture_deepseek_usage({"model": "deepseek-test", "usage": {
            "prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}}, "fallback")
    finally:
        reset(token)
    session = Mock()
    collector.attach(session)
    rows = session.add_all.call_args.args[0]
    assert [(row.call_index, row.total_tokens) for row in rows] == [(1, 30), (2, 7)]
    assert len({row.request_id for row in rows}) == 1
    assert rows[0].input_tokens == 19
    assert rows[0].output_tokens == 8


def test_missing_provider_usage_is_unknown_not_zero():
    collector = UsageCollector(uuid4())
    token = activate(collector)
    try:
        capture_deepseek_usage({"model": "deepseek-test"}, "fallback")
    finally:
        reset(token)
    assert collector.entries[0].usage_source == "missing"
    assert collector.entries[0].total_tokens is None


def test_anonymous_calls_are_not_assigned_to_user():
    collector = UsageCollector(None)
    token = activate(collector)
    try:
        capture_deepseek_usage({"usage": {"total_tokens": 4}}, "model")
    finally:
        reset(token)
    assert collector.entries == []
