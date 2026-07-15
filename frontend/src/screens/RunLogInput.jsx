import React, { useState } from "react";

// 実行ログ入力画面: 導入前/後の実行を記録して診断。
export default function RunLogInput({ onSubmit, busy }) {
  const [beforeSec, setBeforeSec] = useState(600);
  const [afterSec, setAfterSec] = useState(180);
  const [count, setCount] = useState(20);

  const submit = () => {
    const runs = [];
    for (let i = 0; i < count; i++) {
      runs.push({ mode: "before", task: "見積書作成", duration_sec: Number(beforeSec), human_intervention: true });
      runs.push({ mode: "after", task: "見積書作成", duration_sec: Number(afterSec) });
    }
    onSubmit("見積書作成", runs);
  };

  return (
    <div className="card">
      <h2>実行ログ入力（見積書作成）</h2>
      <label>導入前 平均秒<input type="number" value={beforeSec} onChange={(e) => setBeforeSec(e.target.value)} /></label>
      <label>導入後 平均秒<input type="number" value={afterSec} onChange={(e) => setAfterSec(e.target.value)} /></label>
      <label>件数<input type="number" value={count} onChange={(e) => setCount(Number(e.target.value))} /></label>
      <button className="primary" disabled={busy} onClick={submit}>{busy ? "計測中..." : "ROIを計測"}</button>
    </div>
  );
}
