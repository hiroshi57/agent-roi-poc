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

    # ★差別化: 因果推論(合成対照法) — 相関でなく因果でROIを主張
    from src.causal import synthetic_control, placebo_test
    print("\n=== 因果推論: 合成対照法(Synthetic Control) ===")
    donors_pre = {"部門A": [40, 42, 44, 46], "部門B": [38, 39, 40, 41], "部門C": [50, 49, 48, 47]}
    donors_post = {"部門A": 47, "部門B": 42, "部門C": 46}
    treated_pre = [41, 42, 43, 44]   # AI導入部門の導入前スコア推移
    sc = synthetic_control(treated_pre, treated_post=62.0, donors_pre=donors_pre, donors_post=donors_post)
    print(f"  反実仮想(導入しなければ): {sc.counterfactual_post:.1f} / 実測: {sc.observed_post:.1f}")
    print(f"  ★因果効果: +{sc.effect:.1f} (事前当てはまりRMSE={sc.pre_rmse:.2f})")
    pb = placebo_test(treated_pre, 62.0, donors_pre, donors_post)
    print(f"  プラセボ検定 p値: {pb.p_value}(偽の介入では同等効果が出にくい=因果の裏づけ)")


def _save(runs, path):
    from src.metrics import MetricsTracker
    tr = MetricsTracker()
    tr._runs.extend(runs)
    tr.save_jsonl(path)


if __name__ == "__main__":
    main()
