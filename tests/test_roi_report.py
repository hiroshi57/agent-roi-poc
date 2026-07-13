import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import simulate  # noqa: E402
from src.metrics import (  # noqa: E402
    compare, permutation_test, RoiInput, compute_monetary_roi, render_markdown, compare_by_task,
)


def _cmp(n=50, seed=7):
    t = simulate(n=n, seed=seed)
    return compare(t.by_mode("before"), t.by_mode("after")), t


# --- 並べ替え検定 ---
def test_permutation_test_significant_for_large_effect():
    before = [600, 620, 580, 640, 590, 610, 605, 595]
    after = [180, 200, 160, 220, 190, 170, 185, 195]
    p = permutation_test(before, after, n_perm=1000, seed=1)
    assert p < 0.05                      # 明確な削減は有意


def test_permutation_test_not_significant_for_no_effect():
    a = [100, 110, 90, 105, 95]
    b = [102, 108, 92, 104, 96]
    p = permutation_test(a, b, n_perm=1000, seed=1)
    assert p > 0.05                      # 差がなければ有意でない


def test_permutation_deterministic():
    assert permutation_test([5, 6, 7], [1, 2, 3], seed=9) == permutation_test([5, 6, 7], [1, 2, 3], seed=9)


# --- 金額換算ROI ---
def test_monetary_roi_positive_when_time_saved():
    cmp, _ = _cmp()
    roi = compute_monetary_roi(cmp, RoiInput(hourly_rate_yen=3000, monthly_volume=500,
                                             ai_monthly_cost_yen=50000))
    assert roi.monthly_time_saved_hours > 0
    assert roi.monthly_net_saving_yen > 0
    assert roi.roi_percent > 0
    assert roi.payback_months > 0


def test_monetary_roi_zero_ai_cost_handles_gracefully():
    cmp, _ = _cmp()
    roi = compute_monetary_roi(cmp, RoiInput(3000, 100, 0))
    assert roi.roi_percent == 0.0        # ゼロ除算回避


# --- レポート/業務別 ---
def test_render_markdown_contains_sections():
    cmp, _ = _cmp()
    roi = compute_monetary_roi(cmp, RoiInput(3000, 100, 50000))
    md = render_markdown(cmp, p_value=0.01, monetary=roi)
    assert "ROIレポート" in md
    assert "金額換算ROI" in md
    assert "並べ替え検定" in md


def test_compare_by_task_multi_task():
    from src.metrics import MetricsTracker
    t = MetricsTracker(now_fn=lambda: "T")
    for _ in range(5):
        t.record("before", "見積書作成", 600, False, True)
        t.record("after", "見積書作成", 200, False, False)
        t.record("before", "請求書作成", 300, False, True)
        t.record("after", "請求書作成", 120, False, False)
    result = compare_by_task(t.by_mode("before"), t.by_mode("after"))
    assert set(result) == {"見積書作成", "請求書作成"}
    assert result["見積書作成"]["time_reduction_pct"] > 0
