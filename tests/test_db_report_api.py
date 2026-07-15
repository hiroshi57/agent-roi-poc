import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from service.db import ServiceDB  # noqa: E402
from service.report_html import build_html_report  # noqa: E402
from src.metrics import MetricsTracker, compare, compute_monetary_roi, RoiInput  # noqa: E402
from src import simulate  # noqa: E402


def _seed_db():
    db = ServiceDB(":memory:")
    t = simulate(n=40, seed=7)
    db.add_runs("t-a", "見積書作成", t.runs)
    return db


def test_runs_roundtrip():
    db = _seed_db()
    before = db.get_runs("t-a", "見積書作成", "before")
    after = db.get_runs("t-a", "見積書作成", "after")
    assert len(before) == 40 and len(after) == 40


def test_tenant_isolation():
    db = _seed_db()
    assert db.get_runs("t-b", "見積書作成", "before") == []   # 越境不可


def test_html_report_sections():
    t = simulate(n=40, seed=7)
    cmp = compare(t.by_mode("before"), t.by_mode("after"))
    monetary = compute_monetary_roi(cmp, RoiInput(3000, 500, 50000))
    html = build_html_report(cmp, 0.001, monetary, "見積書作成")
    assert "ROIレポート" in html and "金額換算ROI" in html and "並べ替え検定" in html
    assert "見積書作成" in html


def test_html_report_escapes():
    t = simulate(n=10, seed=1)
    cmp = compare(t.by_mode("before"), t.by_mode("after"))
    html = build_html_report(cmp, 0.5, None, "<b>x</b>")
    assert "<b>x</b>" not in html and "&lt;b&gt;" in html


def test_api_e2e_and_tenant_isolation():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from service.api import create_app
    c = TestClient(create_app())
    ha, hb = {"X-Tenant-Id": "t-a"}, {"X-Tenant-Id": "t-b"}
    runs = []
    for _ in range(20):
        runs.append({"mode": "before", "task": "見積書作成", "duration_sec": 600, "human_intervention": True})
        runs.append({"mode": "after", "task": "見積書作成", "duration_sec": 180})
    assert c.post("/v1/runs", json={"project": "見積書作成", "runs": runs}, headers=ha).json()["added"] == 40
    assert c.get("/v1/report?project=見積書作成", headers=hb).status_code == 404   # 越境不可
    roi = c.post("/v1/roi", json={"project": "見積書作成"}, headers=ha).json()
    assert roi["comparison"]["time_reduction_pct"] > 0
    r = c.get("/v1/report?project=見積書作成", headers=ha)
    assert r.status_code == 200 and "ROIレポート" in r.text
