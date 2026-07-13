"""デモ(APIキー不要). サンプルログ生成 -> 保存 -> ROIレポート. `python demo.py`"""
import os

from src import simulate
from dashboard.app import cli_report, BEFORE, AFTER


def main():
    t = simulate(n=30, seed=7)
    t_before = t.__class__()
    # before/after を別ファイルへ保存(導入前/後を比較できるログ設計)
    _save(t.by_mode("before"), BEFORE)
    _save(t.by_mode("after"), AFTER)
    print(f"ログ保存: {BEFORE} / {AFTER}\n")
    print(cli_report())

    # 全機能: 有意差検定(p値) + 金額換算ROI
    from src.metrics import (compare, permutation_test, RoiInput, compute_monetary_roi)
    c = compare(t.by_mode("before"), t.by_mode("after"))
    p = permutation_test([r.duration_sec for r in t.by_mode("before")],
                         [r.duration_sec for r in t.by_mode("after")])
    roi = compute_monetary_roi(c, RoiInput(hourly_rate_yen=3000, monthly_volume=500,
                                           ai_monthly_cost_yen=50000))
    print("\n=== 有意差検定 + 金額換算ROI ===")
    print(f"  並べ替え検定 p値: {p} ({'有意' if p < 0.05 else '有意差なし'})")
    print(f"  月間純便益: {roi.monthly_net_saving_yen:,.0f}円 / 年間ROI: {roi.roi_percent:.0f}% "
          f"/ 回収: {roi.payback_months:.1f}ヶ月")


def _save(runs, path):
    from src.metrics import MetricsTracker
    tr = MetricsTracker()
    tr._runs.extend(runs)
    tr.save_jsonl(path)


if __name__ == "__main__":
    main()
