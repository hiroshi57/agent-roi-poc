import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import simulate  # noqa: E402
from src.metrics import (  # noqa: E402
    summarize, compare, wilson_ci, bootstrap_reduction_ci, mean, stdev,
)


def test_wilson_ci_bounds():
    lo, hi = wilson_ci(5, 20)
    assert 0.0 <= lo <= 0.25 <= hi <= 1.0
    # 全成功でも上限は1を超えない、下限は0未満にならない
    lo2, hi2 = wilson_ci(20, 20)
    assert lo2 >= 0.0 and hi2 <= 1.0
    assert wilson_ci(0, 0) == (0.0, 0.0)


def test_bootstrap_ci_ordering_and_contains_point():
    before = [600, 620, 580, 640, 590, 610]
    after = [180, 200, 160, 220, 190, 170]
    point, lo, hi = bootstrap_reduction_ci(before, after, n_boot=1000, seed=1)
    assert lo <= point <= hi
    assert point > 0            # 明らかに削減している
    assert lo > 0               # 有意に削減


def test_bootstrap_deterministic_with_seed():
    before, after = [600, 620, 580], [180, 200, 160]
    r1 = bootstrap_reduction_ci(before, after, seed=42)
    r2 = bootstrap_reduction_ci(before, after, seed=42)
    assert r1 == r2


def test_summarize_counts_interventions():
    t = simulate(n=40, seed=3)
    b = summarize(t.by_mode("before"))
    a = summarize(t.by_mode("after"))
    assert b.n == 40 and a.n == 40
    assert b.intervention_rate == 1.0        # before は全て人手
    assert 0.0 <= a.intervention_rate <= 1.0
    assert a.intervention_rate < b.intervention_rate


def test_compare_shows_time_saving():
    t = simulate(n=50, seed=7)
    c = compare(t.by_mode("before"), t.by_mode("after"))
    assert c.time_reduction_pct > 30         # AI導入で大幅短縮
    assert c.significant_time_saving is True  # CIが0をまたがない
    assert c.after.error_rate <= c.before.error_rate


def test_mean_stdev():
    assert mean([1, 2, 3]) == 2
    assert stdev([2, 2, 2]) == 0.0
    assert round(stdev([1, 2, 3]), 4) == 1.0
