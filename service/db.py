"""永続化層(SQLite, 標準ライブラリ). 導入前後の実行ログ保存. テナント分離."""
from __future__ import annotations

import sqlite3
from typing import List

from src.metrics import TaskRun

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    project TEXT NOT NULL,
    mode TEXT NOT NULL,
    task TEXT NOT NULL,
    duration_sec REAL NOT NULL,
    had_error INTEGER NOT NULL,
    human_intervention INTEGER NOT NULL,
    ts TEXT NOT NULL
);
"""


class ServiceDB:
    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def add_runs(self, tenant_id: str, project: str, runs: List[TaskRun]) -> int:
        for r in runs:
            self.conn.execute(
                "INSERT INTO runs(tenant_id, project, mode, task, duration_sec, had_error, "
                "human_intervention, ts) VALUES (?,?,?,?,?,?,?,?)",
                (tenant_id, project, r.mode, r.task, r.duration_sec,
                 1 if r.had_error else 0, 1 if r.human_intervention else 0, r.ts))
        self.conn.commit()
        return len(runs)

    def get_runs(self, tenant_id: str, project: str, mode: str) -> List[TaskRun]:
        rows = self.conn.execute(
            "SELECT mode, task, duration_sec, had_error, human_intervention, ts FROM runs "
            "WHERE tenant_id=? AND project=? AND mode=?", (tenant_id, project, mode)).fetchall()
        return [TaskRun(mode=r["mode"], task=r["task"], duration_sec=r["duration_sec"],
                        had_error=bool(r["had_error"]), human_intervention=bool(r["human_intervention"]),
                        ts=r["ts"]) for r in rows]

    def close(self) -> None:
        self.conn.close()
