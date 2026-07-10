"""導入前/後を比較できるログ設計. 1タスク実行 = 1レコード.

対象業務: 見積書作成(定型業務1つに限定)。
差別化の土台として human_intervention(人間介入)を全レコードで記録する。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class TaskRun:
    mode: str                    # "before"(人手) / "after"(AI導入)
    task: str                    # 例: "見積書作成"
    duration_sec: float          # 処理時間(秒)
    had_error: bool              # 成果物に誤りがあったか
    human_intervention: bool     # 人間の介入/修正が必要だったか
    ts: str = ""

    def as_dict(self):
        return asdict(self)


class MetricsTracker:
    def __init__(self, now_fn=None) -> None:
        self._runs: List[TaskRun] = []
        self._now = now_fn or (lambda: datetime.now(timezone.utc).isoformat())

    def record(self, mode: str, task: str, duration_sec: float,
               had_error: bool, human_intervention: bool = False) -> TaskRun:
        if mode not in ("before", "after"):
            raise ValueError("mode は before / after のいずれか")
        run = TaskRun(mode=mode, task=task, duration_sec=float(duration_sec),
                      had_error=bool(had_error), human_intervention=bool(human_intervention),
                      ts=self._now())
        self._runs.append(run)
        return run

    @property
    def runs(self) -> List[TaskRun]:
        return list(self._runs)

    def by_mode(self, mode: str) -> List[TaskRun]:
        return [r for r in self._runs if r.mode == mode]

    def save_jsonl(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for r in self._runs:
                f.write(json.dumps(r.as_dict(), ensure_ascii=False) + "\n")

    @classmethod
    def load_jsonl(cls, *paths: str) -> "MetricsTracker":
        t = cls()
        for path in paths:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        t._runs.append(TaskRun(**d))
        return t
