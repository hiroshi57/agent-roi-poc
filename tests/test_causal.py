import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.causal import (  # noqa: E402
    difference_in_differences, synthetic_control, placebo_test,
)
from src.causal.estimator import _project_to_simplex  # noqa: E402


# --- DID ---
def test_did_effect():
    r = difference_in_differences(
        treated_pre=[40, 42, 38], treated_post=[62, 60, 64],
        control_pre=[40, 41, 39], control_post=[45, 46, 44])
    assert round(r.treated_delta) == 22
    assert round(r.control_delta) == 5
    assert round(r.effect) == 17


# --- 単体射影 ---
def test_simplex_projection_valid():
    w = _project_to_simplex([0.5, 0.9, -0.3, 0.2])
    assert abs(sum(w) - 1.0) < 1e-9
    assert all(x >= 0 for x in w)


def test_simplex_projection_already_simplex():
    w = _project_to_simplex([0.2, 0.3, 0.5])
    assert abs(sum(w) - 1.0) < 1e-9


# --- Synthetic Control ---
def test_synthetic_control_recovers_effect():
    # 介入群の事前 = donorAとdonorBの平均に一致する構成にする
    donors_pre = {"A": [10, 12, 14, 16], "B": [20, 22, 24, 26], "C": [50, 40, 30, 20]}
    treated_pre = [15, 17, 19, 21]  # = (A+B)/2
    donors_post = {"A": 18, "B": 28, "C": 10}
    # 反実仮想(介入なし)は (18+28)/2 = 23 付近。実測が33なら効果+10
    r = synthetic_control(treated_pre, treated_post=33.0,
                          donors_pre=donors_pre, donors_post=donors_post)
    assert r.pre_rmse < 1.0                    # 事前当てはまり良好
    assert 20 <= r.counterfactual_post <= 26   # A,Bの合成に収束
    assert r.effect > 5                        # 明確な正の効果
    assert abs(sum(r.weights.values()) - 1.0) < 1e-6
    assert all(w >= -1e-9 for w in r.weights.values())


def test_synthetic_control_downweights_bad_donor():
    donors_pre = {"good": [15, 17, 19, 21], "bad": [1, 2, 3, 99]}
    treated_pre = [15, 17, 19, 21]
    donors_post = {"good": 23, "bad": 0}
    r = synthetic_control(treated_pre, 30.0, donors_pre, donors_post)
    assert r.weights["good"] > r.weights["bad"]   # 似ているドナーに重みが寄る


def test_placebo_test_detects_real_effect():
    donors_pre = {"A": [10, 12, 14, 16], "B": [20, 22, 24, 26], "C": [30, 31, 32, 33]}
    donors_post = {"A": 18, "B": 28, "C": 34}
    treated_pre = [15, 17, 19, 21]
    r = placebo_test(treated_pre, treated_post=40.0,
                     donors_pre=donors_pre, donors_post=donors_post)
    assert r.effect > 0
    assert 0.0 <= r.p_value <= 1.0
    assert len(r.placebo_effects) == 3
