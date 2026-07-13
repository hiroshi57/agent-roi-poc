"""ROI 統計(差別化). 点推定だけでなく信頼区間つきで導入効果を提示する.

- 処理時間削減率: ブートストラップ信頼区間(percentile法)
- エラー率 / 人間介入率: 比率の Wilson score 信頼区間
これにより「たまたま速かっただけ」を排し、効果の確からしさを示せる。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Tuple

Z95 = 1.959963985  # 95% 両側


def mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def wilson_ci(successes: int, n: int, z: float = Z95) -> Tuple[float, float]:
    """比率の Wilson score 信頼区間(0-1)."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _reduction_pct(before: List[float], after: List[float]) -> float:
    mb = mean(before)
    return (mb - mean(after)) / mb * 100 if mb else 0.0


def bootstrap_reduction_ci(before: List[float], after: List[float],
                           n_boot: int = 2000, seed: int = 42,
                           alpha: float = 0.05) -> Tuple[float, float, float]:
    """処理時間削減率(%)の点推定とブートストラップ信頼区間を返す."""
    point = _reduction_pct(before, after)
    if not before or not after:
        return (point, point, point)
    rng = random.Random(seed)
    stats: List[float] = []
    nb, na = len(before), len(after)
    for _ in range(n_boot):
        rb = [before[rng.randrange(nb)] for _ in range(nb)]
        ra = [after[rng.randrange(na)] for _ in range(na)]
        stats.append(_reduction_pct(rb, ra))
    stats.sort()
    lo = stats[int((alpha / 2) * n_boot)]
    hi = stats[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return (point, lo, hi)


def permutation_test(before: List[float], after: List[float],
                     n_perm: int = 2000, seed: int = 42) -> float:
    """平均差の並べ替え検定. p値(before>afterという削減が偶然でない確率)を返す.

    CIを補完する仮説検定。両群をプールしてランダム分割し、観測された平均差以上が
    偶然生じる割合を p値とする(片側: before平均 > after平均)。
    """
    if not before or not after:
        return 1.0
    observed = mean(before) - mean(after)
    pooled = before + after
    nb = len(before)
    rng = random.Random(seed)
    count = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        diff = mean(pooled[:nb]) - mean(pooled[nb:])
        if diff >= observed:
            count += 1
    return round((count + 1) / (n_perm + 1), 4)   # +1平滑化


@dataclass
class ModeSummary:
    mode: str
    n: int
    mean_duration: float
    sd_duration: float
    error_rate: float
    error_ci: Tuple[float, float]
    intervention_rate: float
    intervention_ci: Tuple[float, float]

    def as_dict(self):
        return {
            "mode": self.mode, "n": self.n,
            "mean_duration": round(self.mean_duration, 2),
            "sd_duration": round(self.sd_duration, 2),
            "error_rate": round(self.error_rate, 4),
            "error_ci": [round(self.error_ci[0], 4), round(self.error_ci[1], 4)],
            "intervention_rate": round(self.intervention_rate, 4),
            "intervention_ci": [round(self.intervention_ci[0], 4), round(self.intervention_ci[1], 4)],
        }


def summarize(runs) -> ModeSummary:
    durations = [r.duration_sec for r in runs]
    n = len(runs)
    errors = sum(1 for r in runs if r.had_error)
    interventions = sum(1 for r in runs if r.human_intervention)
    mode = runs[0].mode if runs else "?"
    return ModeSummary(
        mode=mode, n=n,
        mean_duration=mean(durations), sd_duration=stdev(durations),
        error_rate=errors / n if n else 0.0, error_ci=wilson_ci(errors, n),
        intervention_rate=interventions / n if n else 0.0,
        intervention_ci=wilson_ci(interventions, n),
    )


@dataclass
class RoiComparison:
    before: ModeSummary
    after: ModeSummary
    time_reduction_pct: float
    time_reduction_ci: Tuple[float, float]
    error_rate_delta: float          # after - before(負なら改善)
    significant_time_saving: bool    # 削減率CIが 0 をまたがない

    def as_dict(self):
        return {
            "before": self.before.as_dict(),
            "after": self.after.as_dict(),
            "time_reduction_pct": round(self.time_reduction_pct, 2),
            "time_reduction_ci": [round(self.time_reduction_ci[0], 2), round(self.time_reduction_ci[1], 2)],
            "error_rate_delta": round(self.error_rate_delta, 4),
            "significant_time_saving": self.significant_time_saving,
        }


def compare(before_runs, after_runs, seed: int = 42) -> RoiComparison:
    b = summarize(before_runs)
    a = summarize(after_runs)
    point, lo, hi = bootstrap_reduction_ci(
        [r.duration_sec for r in before_runs],
        [r.duration_sec for r in after_runs], seed=seed,
    )
    return RoiComparison(
        before=b, after=a,
        time_reduction_pct=point, time_reduction_ci=(lo, hi),
        error_rate_delta=a.error_rate - b.error_rate,
        significant_time_saving=(lo > 0),
    )
