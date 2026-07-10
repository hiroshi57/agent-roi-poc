import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from src.metrics import MetricsTracker  # noqa: E402


def test_record_and_by_mode():
    t = MetricsTracker(now_fn=lambda: "T")
    t.record("before", "見積書作成", 600, had_error=True, human_intervention=True)
    t.record("after", "見積書作成", 180, had_error=False, human_intervention=True)
    assert len(t.by_mode("before")) == 1
    assert len(t.by_mode("after")) == 1


def test_invalid_mode_raises():
    t = MetricsTracker()
    with pytest.raises(ValueError):
        t.record("during", "x", 1, False)


def test_save_and_load_roundtrip():
    t = MetricsTracker(now_fn=lambda: "T")
    t.record("before", "見積書作成", 600, True, True)
    t.record("after", "見積書作成", 120, False, False)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "sub", "runs.jsonl")
        t.save_jsonl(path)
        loaded = MetricsTracker.load_jsonl(path)
    assert len(loaded.runs) == 2
    assert loaded.runs[0].duration_sec == 600
    assert loaded.runs[1].human_intervention is False
