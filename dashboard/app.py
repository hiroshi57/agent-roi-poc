"""ROI ダッシュボード. Streamlit があれば GUI、無ければ CLI レポートで動作."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.metrics import MetricsTracker, compare  # noqa: E402

BEFORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "before", "runs.jsonl")
AFTER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "after", "runs.jsonl")


def load_comparison():
    t = MetricsTracker.load_jsonl(BEFORE, AFTER)
    return compare(t.by_mode("before"), t.by_mode("after"))


def cli_report() -> str:
    c = load_comparison()
    b, a = c.before, c.after
    lines = [
        "=== AIエージェント導入 ROI レポート(見積書作成) ===",
        f"サンプル数: before={b.n}, after={a.n}",
        "",
        f"処理時間(平均): {b.mean_duration:.0f}秒 → {a.mean_duration:.0f}秒",
        f"  ★時間削減率: {c.time_reduction_pct:.1f}% "
        f"(95%CI: {c.time_reduction_ci[0]:.1f}〜{c.time_reduction_ci[1]:.1f}%) "
        f"{'★統計的に有意' if c.significant_time_saving else '(有意差なし)'}",
        "",
        f"エラー率: {b.error_rate:.1%} (CI {b.error_ci[0]:.1%}〜{b.error_ci[1]:.1%}) "
        f"→ {a.error_rate:.1%} (CI {a.error_ci[0]:.1%}〜{a.error_ci[1]:.1%})",
        f"  エラー率変化: {c.error_rate_delta:+.1%}",
        "",
        f"★人間介入率: before {b.intervention_rate:.1%} → after {a.intervention_rate:.1%} "
        f"(CI {a.intervention_ci[0]:.1%}〜{a.intervention_ci[1]:.1%})",
        "  ※AIの実効ROIは介入コスト込みで評価すべき指標",
    ]
    return "\n".join(lines)


def run_streamlit():  # pragma: no cover
    import streamlit as st

    c = load_comparison()
    st.title("AIエージェント導入 ROI ダッシュボード")
    st.caption("対象業務: 見積書作成")
    col1, col2, col3 = st.columns(3)
    col1.metric("時間削減率", f"{c.time_reduction_pct:.1f}%",
                help=f"95%CI {c.time_reduction_ci[0]:.1f}〜{c.time_reduction_ci[1]:.1f}%")
    col2.metric("エラー率変化", f"{c.error_rate_delta:+.1%}")
    col3.metric("人間介入率(after)", f"{c.after.intervention_rate:.1%}")
    st.subheader("処理時間")
    st.bar_chart({"平均処理時間(秒)": {"before": c.before.mean_duration, "after": c.after.mean_duration}})
    st.json(c.as_dict())


if __name__ == "__main__":
    try:
        import streamlit  # noqa: F401
        run_streamlit()
    except Exception:
        print(cli_report())
