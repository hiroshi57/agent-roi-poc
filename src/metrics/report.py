"""レポート出力(全機能). ROI比較+金額換算+有意差検定をMarkdownにまとめる."""
from __future__ import annotations

from typing import Dict, List, Optional

from .roi import MonetaryRoi
from .stats import RoiComparison


def render_markdown(cmp: RoiComparison, p_value: Optional[float] = None,
                    monetary: Optional[MonetaryRoi] = None,
                    task: str = "見積書作成") -> str:
    b, a = cmp.before, cmp.after
    lines = [
        f"# AIエージェント導入 ROIレポート({task})", "",
        f"- サンプル数: before={b.n}, after={a.n}",
        f"- 処理時間: {b.mean_duration:.0f}秒 → {a.mean_duration:.0f}秒",
        f"- **時間削減率: {cmp.time_reduction_pct:.1f}%** "
        f"(95%CI {cmp.time_reduction_ci[0]:.1f}〜{cmp.time_reduction_ci[1]:.1f}%)",
    ]
    if p_value is not None:
        sig = "有意(p<0.05)" if p_value < 0.05 else "有意差なし"
        lines.append(f"- 並べ替え検定 p値: {p_value} ({sig})")
    lines += [
        f"- エラー率変化: {cmp.error_rate_delta:+.1%}",
        f"- 人間介入率: before {b.intervention_rate:.0%} → after {a.intervention_rate:.0%}",
    ]
    if monetary is not None:
        m = monetary
        lines += ["", "## 金額換算ROI",
                  f"- 月間削減時間: {m.monthly_time_saved_hours:.1f}h",
                  f"- 月間純便益(AIコスト差引後): {m.monthly_net_saving_yen:,.0f}円",
                  f"- 年間純便益: {m.annual_net_saving_yen:,.0f}円",
                  f"- 年間ROI: {m.roi_percent:.0f}%  / 回収: {m.payback_months:.1f}ヶ月"]
    lines.append("")
    lines.append("> 注記: ROI数値は導入前後ログの実測に基づく。削減率は信頼区間つきで解釈すること。")
    return "\n".join(lines)


def compare_by_task(runs_before, runs_after) -> Dict[str, Dict]:
    """業務(task)別に before/after を突き合わせる(複数業務対応)."""
    from .stats import compare
    tasks = sorted({r.task for r in runs_before} | {r.task for r in runs_after})
    out: Dict[str, Dict] = {}
    for t in tasks:
        b = [r for r in runs_before if r.task == t]
        a = [r for r in runs_after if r.task == t]
        if b and a:
            out[t] = compare(b, a).as_dict()
    return out
