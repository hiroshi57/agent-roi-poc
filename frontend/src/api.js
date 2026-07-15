const BASE = import.meta.env?.VITE_API || "http://localhost:8000";
const h = (t) => ({ "Content-Type": "application/json", "X-Tenant-Id": t });

export async function addRuns(t, project, runs) {
  return (await fetch(`${BASE}/v1/runs`, { method: "POST", headers: h(t), body: JSON.stringify({ project, runs }) })).json();
}
export async function roi(t, project) {
  return (await fetch(`${BASE}/v1/roi`, { method: "POST", headers: h(t), body: JSON.stringify({ project }) })).json();
}
export function reportUrl(project) { return `${BASE}/v1/report?project=${encodeURIComponent(project)}`; }
