import React, { useState } from "react";
import RoiDashboard from "./screens/RoiDashboard.jsx";
import RunLogInput from "./screens/RunLogInput.jsx";
import { addRuns, roi, reportUrl } from "./api.js";

const TENANT = "demo-tenant";
const DEMO = {
  comparison: {
    time_reduction_pct: 70.3, time_reduction_ci: [66.3, 73.8],
    after: { intervention_rate: 0.37 }, error_rate_delta: -0.23,
  },
  p_value: 0.0005,
  monetary: { monthly_net_saving_yen: 123359, annual_net_saving_yen: 1480308, roi_percent: 247, payback_months: 0.4 },
};

export default function App() {
  const [data, setData] = useState(DEMO);
  const [busy, setBusy] = useState(false);

  const run = async (project, runs) => {
    setBusy(true);
    try {
      await addRuns(TENANT, project, runs);
      setData(await roi(TENANT, project));
    } catch (e) {
      alert("バックエンド未起動の可能性: " + e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="wrap">
      <h1>AIエージェント導入 ROI PoC</h1>
      <RunLogInput onSubmit={run} busy={busy} />
      <RoiDashboard data={data} onOpenReport={() => window.open(reportUrl("見積書作成"), "_blank")} />
    </div>
  );
}
