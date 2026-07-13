"""金額換算ROI(全機能). 削減時間を金額に換算し、AI運用コストを差し引いた純便益を出す."""
from __future__ import annotations

from dataclasses import dataclass

from .stats import RoiComparison


@dataclass
class RoiInput:
    hourly_rate_yen: float       # 担当者の時間単価(円/h)
    monthly_volume: int          # 月間処理件数
    ai_monthly_cost_yen: float   # AIの月額運用コスト(円)


@dataclass
class MonetaryRoi:
    monthly_time_saved_hours: float
    monthly_gross_saving_yen: float   # 人件費削減(粗)
    monthly_net_saving_yen: float     # AIコスト差引後
    annual_net_saving_yen: float
    roi_percent: float                # 年間純便益 / 年間AIコスト
    payback_months: float             # 回収月数(初期コスト=月額と仮定した簡易版)

    def as_dict(self):
        return {k: round(v, 1) for k, v in self.__dict__.items()}


def compute_monetary_roi(cmp: RoiComparison, params: RoiInput) -> MonetaryRoi:
    # 1件あたり削減時間(秒->時間)
    saved_sec_each = max(0.0, cmp.before.mean_duration - cmp.after.mean_duration)
    saved_h_each = saved_sec_each / 3600
    monthly_saved_h = saved_h_each * params.monthly_volume
    gross = monthly_saved_h * params.hourly_rate_yen
    net = gross - params.ai_monthly_cost_yen
    annual_net = net * 12
    annual_ai_cost = params.ai_monthly_cost_yen * 12
    roi_pct = (annual_net / annual_ai_cost * 100) if annual_ai_cost > 0 else 0.0
    payback = (params.ai_monthly_cost_yen / net) if net > 0 else float("inf")
    return MonetaryRoi(
        monthly_time_saved_hours=monthly_saved_h,
        monthly_gross_saving_yen=gross,
        monthly_net_saving_yen=net,
        annual_net_saving_yen=annual_net,
        roi_percent=roi_pct,
        payback_months=payback,
    )
