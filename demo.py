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


def _save(runs, path):
    from src.metrics import MetricsTracker
    tr = MetricsTracker()
    tr._runs.extend(runs)
    tr.save_jsonl(path)


if __name__ == "__main__":
    main()
