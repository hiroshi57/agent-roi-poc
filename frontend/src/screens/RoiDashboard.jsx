import React from "react";

// ROIダッシュボード: 削減率(CI)・p値・金額ROI・人間介入率。
export default function RoiDashboard({ data, onOpenReport }) {
  if (!data) return <div className="card">まだ結果がありません。</div>;
  const cmp = data.comparison;
  const m = data.monetary;
  return (
    <div className="card">
      <h2>ROI サマリ</h2>
      <div className="metrics">
        <div className="metric"><div>時間削減率</div>
          <div className="val">{cmp.time_reduction_pct}%</div>
          <small>95%CI {cmp.time_reduction_ci[0]}〜{cmp.time_reduction_ci[1]}%</small></div>
        <div className="metric"><div>並べ替え検定 p値</div>
          <div className="val">{data.p_value}</div>
          <small>{data.p_value < 0.05 ? "有意" : "有意差なし"}</small></div>
        <div className="metric"><div>人間介入率(after)</div>
          <div className="val">{Math.round(cmp.after.intervention_rate * 100)}%</div></div>
      </div>
      {m && (
        <>
          <h3>金額換算ROI</h3>
          <ul>
            <li>月間純便益: {m.monthly_net_saving_yen.toLocaleString()}円</li>
            <li>年間ROI: {m.roi_percent}% / 回収 {m.payback_months}ヶ月</li>
          </ul>
        </>
      )}
      {onOpenReport && <button className="primary" onClick={onOpenReport}>HTMLレポートを開く</button>}
    </div>
  );
}
