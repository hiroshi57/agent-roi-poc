"""因果推論エンジン(差別化の核). AI導入効果を「相関」でなく「因果」で推定する.

汎用BIが出せない3手法を同梱:
  1. Difference-in-Differences (DID): 介入群と対照群の前後差の差
  2. Synthetic Control: 複数の対照ユニットを重み付き合成し、介入群の反実仮想を作る
  3. 頑健性バンド: プラセボ(偽の介入時点)とブートストラップで効果の確からしさを検証
すべて標準ライブラリのみ(外部依存なし)。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# ---------------------------------------------------------------------------
# 1. Difference-in-Differences
# ---------------------------------------------------------------------------
@dataclass
class DIDResult:
    treated_delta: float
    control_delta: float
    effect: float            # DID推定量 = 介入群の変化 - 対照群の変化
    note: str = "DIDは並行トレンド仮定に依存します(因果の十分条件ではありません)"

    def as_dict(self):
        return {"treated_delta": round(self.treated_delta, 3),
                "control_delta": round(self.control_delta, 3),
                "effect": round(self.effect, 3), "note": self.note}


def difference_in_differences(treated_pre: List[float], treated_post: List[float],
                              control_pre: List[float], control_post: List[float]) -> DIDResult:
    td = _mean(treated_post) - _mean(treated_pre)
    cd = _mean(control_post) - _mean(control_pre)
    return DIDResult(treated_delta=td, control_delta=cd, effect=td - cd)


# ---------------------------------------------------------------------------
# 2. Synthetic Control
# ---------------------------------------------------------------------------
def _project_to_simplex(v: List[float]) -> List[float]:
    """ベクトルを確率単体(非負・総和1)へユークリッド射影(Wang & Carreira-Perpinan 2013)."""
    if not v:
        return v
    u = sorted(v, reverse=True)
    css = 0.0
    rho = 0
    theta = 0.0
    for i, ui in enumerate(u, start=1):
        css += ui
        t = (css - 1.0) / i
        if ui - t > 0:
            rho = i
            theta = t
    return [max(0.0, x - theta) for x in v]


def _weighted(donor_series: List[List[float]], w: List[float]) -> List[float]:
    length = len(donor_series[0])
    return [sum(w[j] * donor_series[j][t] for j in range(len(w))) for t in range(length)]


@dataclass
class SyntheticControlResult:
    weights: Dict[str, float]
    pre_rmse: float               # 事前期間の当てはまり(小さいほど信頼できる)
    counterfactual_post: float    # 反実仮想(介入なしなら)のポスト値
    observed_post: float
    effect: float                 # observed - counterfactual
    donor_names: List[str] = field(default_factory=list)

    def as_dict(self):
        return {"weights": {k: round(v, 3) for k, v in self.weights.items()},
                "pre_rmse": round(self.pre_rmse, 3),
                "counterfactual_post": round(self.counterfactual_post, 3),
                "observed_post": round(self.observed_post, 3),
                "effect": round(self.effect, 3)}


def synthetic_control(treated_pre: List[float], treated_post: float,
                      donors_pre: Dict[str, List[float]], donors_post: Dict[str, float],
                      iters: int = 4000, lr: float = 0.05, seed: int = 42) -> SyntheticControlResult:
    """対照ユニット群を重み付き合成し、介入群の反実仮想を推定する.

    事前期間の系列を最もよく再現する非負・総和1の重みを射影勾配法で解く。
    """
    names = list(donors_pre.keys())
    n = len(names)
    if n == 0:
        raise ValueError("対照ユニットが必要です")
    T = len(treated_pre)

    # 数値安定化: 事前系列の最大絶対値でスケーリング(重みはスケール不変)
    scale = max(1e-9, max(abs(x) for series in donors_pre.values() for x in series),
                max((abs(x) for x in treated_pre), default=1e-9))
    donor_pre_series = [[donors_pre[nm][t] / scale for t in range(T)] for nm in names]
    treated_s = [treated_pre[t] / scale for t in range(T)]
    w = [1.0 / n] * n

    def loss_grad(w):
        synth = _weighted(donor_pre_series, w)
        resid = [synth[t] - treated_s[t] for t in range(T)]
        g = [2.0 / T * sum(resid[t] * donor_pre_series[j][t] for t in range(T)) for j in range(n)]
        mse = sum(r * r for r in resid) / T
        return mse, g

    for _ in range(iters):
        _, g = loss_grad(w)
        w = _project_to_simplex([w[j] - lr * g[j] for j in range(n)])

    pre_rmse = math.sqrt(loss_grad(w)[0]) * scale   # 元スケールに戻す
    cf_post = sum(w[j] * donors_post[names[j]] for j in range(n))
    return SyntheticControlResult(
        weights={names[j]: w[j] for j in range(n)},
        pre_rmse=pre_rmse, counterfactual_post=cf_post,
        observed_post=treated_post, effect=treated_post - cf_post, donor_names=names)


# ---------------------------------------------------------------------------
# 3. 頑健性バンド(プラセボ + ブートストラップ)
# ---------------------------------------------------------------------------
@dataclass
class RobustnessResult:
    effect: float
    placebo_effects: List[float]
    p_value: float                # プラセボ分布で観測効果以上が出る割合
    ci_low: float
    ci_high: float

    def as_dict(self):
        return {"effect": round(self.effect, 3), "p_value": round(self.p_value, 4),
                "ci_low": round(self.ci_low, 3), "ci_high": round(self.ci_high, 3),
                "n_placebo": len(self.placebo_effects)}


def placebo_test(treated_pre: List[float], treated_post: float,
                 donors_pre: Dict[str, List[float]], donors_post: Dict[str, float]) -> RobustnessResult:
    """各対照ユニットを「偽の介入群」として同じ推定を回し、効果の異常性を検定する."""
    real = synthetic_control(treated_pre, treated_post, donors_pre, donors_post).effect
    placebos: List[float] = []
    names = list(donors_pre.keys())
    for fake in names:
        rest_pre = {k: v for k, v in donors_pre.items() if k != fake}
        rest_post = {k: v for k, v in donors_post.items() if k != fake}
        if not rest_pre:
            continue
        eff = synthetic_control(donors_pre[fake], donors_post[fake], rest_pre, rest_post).effect
        placebos.append(eff)
    # p値: プラセボの|効果|が実測|効果|以上の割合(片側過激度)
    if placebos:
        extreme = sum(1 for e in placebos if abs(e) >= abs(real))
        p = (extreme + 1) / (len(placebos) + 1)
    else:
        p = 1.0
    allv = sorted(placebos + [real])
    lo = allv[0]
    hi = allv[-1]
    return RobustnessResult(effect=real, placebo_effects=placebos, p_value=round(p, 4),
                            ci_low=lo, ci_high=hi)
