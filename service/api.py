"""ROI計測 API(FastAPI). 実行ログ取込 -> 比較/金額ROI/有意差検定 -> HTMLレポート. テナント分離.
`uvicorn service.api:app --reload`
"""
from src.metrics import (
    MetricsTracker, compare, permutation_test, RoiInput, compute_monetary_roi, render_markdown,
)
from src.metrics.report import render_markdown as _rm  # noqa: F401
from .db import ServiceDB
from .report_html import build_html_report

DB = ServiceDB(":memory:")


def _roi(tenant: str, project: str, params: RoiInput | None = None) -> dict:
    before = DB.get_runs(tenant, project, "before")
    after = DB.get_runs(tenant, project, "after")
    if not before or not after:
        return {}
    cmp = compare(before, after)
    p = permutation_test([r.duration_sec for r in before], [r.duration_sec for r in after])
    result = {"comparison": cmp.as_dict(), "p_value": p}
    if params:
        result["monetary"] = compute_monetary_roi(cmp, params).as_dict()
    return result


def create_app():  # pragma: no cover
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel

    app = FastAPI(title="Agent ROI PoC", version="1.0.0")

    def tenant(x_tenant_id: str = Header(...)) -> str:
        if not x_tenant_id:
            raise HTTPException(401, "tenant required")
        return x_tenant_id

    class RunsIn(BaseModel):
        project: str
        runs: list

    class RoiQuery(BaseModel):
        project: str
        hourly_rate_yen: float = 3000
        monthly_volume: int = 500
        ai_monthly_cost_yen: float = 50000

    @app.post("/v1/runs")
    def add_runs(body: RunsIn, t: str = Depends(tenant)):
        tr = MetricsTracker()
        for r in body.runs:
            tr.record(r["mode"], r.get("task", "task"), r["duration_sec"],
                      r.get("had_error", False), r.get("human_intervention", False))
        return {"added": DB.add_runs(t, body.project, tr.runs)}

    @app.post("/v1/roi")
    def roi(body: RoiQuery, t: str = Depends(tenant)):
        r = _roi(t, body.project, RoiInput(body.hourly_rate_yen, body.monthly_volume, body.ai_monthly_cost_yen))
        if not r:
            raise HTTPException(404, "insufficient data (need before & after)")
        return r

    @app.get("/v1/report", response_class=HTMLResponse)
    def report(project: str, t: str = Depends(tenant)):
        before = DB.get_runs(t, project, "before")
        after = DB.get_runs(t, project, "after")
        if not before or not after:
            raise HTTPException(404, "insufficient data")
        cmp = compare(before, after)
        p = permutation_test([r.duration_sec for r in before], [r.duration_sec for r in after])
        monetary = compute_monetary_roi(cmp, RoiInput(3000, 500, 50000))
        return build_html_report(cmp, p, monetary, project)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


try:  # pragma: no cover
    app = create_app()
except Exception:
    app = None
