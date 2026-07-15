"""ROI HTMLレポート(標準ライブラリのみ)."""
from __future__ import annotations

import html
from typing import Optional

from src.metrics.roi import MonetaryRoi
from src.metrics.stats import RoiComparison


def build_html_report(cmp: RoiComparison, p_value: Optional[float] = None,
                      monetary: Optional[MonetaryRoi] = None, project: str = "見積書作成") -> str:
    b, a = cmp.before, cmp.after
    sig = ("有意(p<0.05)" if (p_value is not None and p_value < 0.05) else "有意差なし")
    money = ""
    if monetary is not None:
        m = monetary
        money = (f"<h2>金額換算ROI</h2><ul>"
                 f"<li>月間削減時間: {m.monthly_time_saved_hours:.1f}h</li>"
                 f"<li>月間純便益(AIコスト差引後): {m.monthly_net_saving_yen:,.0f}円</li>"
                 f"<li>年間純便益: {m.annual_net_saving_yen:,.0f}円</li>"
                 f"<li>年間ROI: {m.roi_percent:.0f}% / 回収 {m.payback_months:.1f}ヶ月</li></ul>")
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<title>AI導入ROIレポート</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;color:#1a1a2e}}
h1{{color:#0a7d5a}} .big{{font-size:36px;color:#0a7d5a;font-weight:bold}}
ul{{line-height:1.7}} .note{{color:#a15;font-size:13px}}</style></head><body>
<h1>AIエージェント導入 ROIレポート（{html.escape(project)}）</h1>
<p>サンプル数: before={b.n}, after={a.n}</p>
<p>処理時間: {b.mean_duration:.0f}秒 → {a.mean_duration:.0f}秒</p>
<p>時間削減率: <span class="big">{cmp.time_reduction_pct:.1f}%</span>
 (95%CI {cmp.time_reduction_ci[0]:.1f}〜{cmp.time_reduction_ci[1]:.1f}%)</p>
<p>並べ替え検定 p値: {p_value} ({sig})</p>
<p>エラー率変化: {cmp.error_rate_delta:+.1%} / 人間介入率: before {b.intervention_rate:.0%} → after {a.intervention_rate:.0%}</p>
{money}
<p class="note">※ROI数値は導入前後ログの実測に基づく。削減率は信頼区間つきで解釈すること。</p>
</body></html>"""
