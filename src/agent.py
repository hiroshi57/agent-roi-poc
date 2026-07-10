"""対象業務: 見積書作成. 導入前(人手)/導入後(AI)の実行をシミュレートし、
比較用ログを生成する。実測データがあれば MetricsTracker.load_jsonl で置換する。
"""
from __future__ import annotations

import random

from .metrics.tracker import MetricsTracker

TASK = "見積書作成"


def simulate(n: int = 30, seed: int = 7) -> MetricsTracker:
    """導入前後の実行ログを決定的に生成.

    before: 人手。平均が長くエラーもそれなり。人間介入は定義上 100%(全部人手)。
    after : AI導入。処理時間短縮・エラー減。ただし一部で人間の確認/修正が入る。
    """
    rng = random.Random(seed)
    t = MetricsTracker(now_fn=lambda: "2026-07-09T00:00:00+00:00")
    for _ in range(n):
        # before: 平均 600 秒前後、15% エラー、人手なので介入100%
        dur = max(120, rng.gauss(600, 120))
        t.record("before", TASK, dur, had_error=rng.random() < 0.15, human_intervention=True)
    for _ in range(n):
        # after: 平均 180 秒前後、5% エラー、20% で人間の確認/修正
        dur = max(30, rng.gauss(180, 50))
        intervened = rng.random() < 0.20
        # 介入時は誤りを是正できるためエラーは出にくい
        err = (rng.random() < 0.05) and not intervened
        t.record("after", TASK, dur, had_error=err, human_intervention=intervened)
    return t
