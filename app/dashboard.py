from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .metrics import history, snapshot

router = APIRouter()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Observability Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', system-ui, -apple-system, sans-serif; background: #0b1120; color: #e2e8f0; min-height: 100vh; }
  .header { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-bottom: 1px solid #1e3a5f; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
  .header h1 { font-size: 1.25rem; font-weight: 600; color: #38bdf8; display: flex; align-items: center; gap: 10px; }
  .header h1 span { background: #1e3a5f; color: #94a3b8; font-size: 0.7rem; padding: 2px 10px; border-radius: 20px; font-weight: 400; }
  .header-right { display: flex; align-items: center; gap: 16px; font-size: 0.8rem; color: #64748b; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
  .status-dot.green { background: #22c55e; box-shadow: 0 0 8px #22c55e44; }
  .status-dot.red { background: #ef4444; box-shadow: 0 0 8px #ef444444; }
  .status-dot.yellow { background: #f59e0b; box-shadow: 0 0 8px #f59e0b44; }
  .content { padding: 16px 20px; max-width: 1440px; margin: 0 auto; }
  .summary-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 16px; }
  .summary-card { background: linear-gradient(135deg, #1e293b, #182334); border: 1px solid #1e3a5f; border-radius: 10px; padding: 14px 16px; }
  .summary-card .value { font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
  .summary-card .label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 12px; }
  .card { background: #1e293b; border: 1px solid #1e3a5f; border-radius: 10px; padding: 16px; transition: border-color 0.2s; }
  .card:hover { border-color: #2d5a8a; }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .card-header h2 { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
  .card-header .badge { font-size: 0.65rem; padding: 2px 8px; border-radius: 10px; background: #334155; color: #64748b; }
  .card canvas { width: 100% !important; height: 220px !important; }
  .empty-chart { display: flex; align-items: center; justify-content: center; height: 220px; color: #475569; font-size: 0.85rem; flex-direction: column; gap: 8px; }
  .empty-chart svg { opacity: 0.4; }
  .loading { display: flex; align-items: center; justify-content: center; height: 60vh; color: #64748b; font-size: 0.9rem; flex-direction: column; gap: 12px; }
  .spinner { width: 32px; height: 32px; border: 3px solid #1e3a5f; border-top: 3px solid #38bdf8; border-radius: 50%; animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (max-width: 640px) { .grid { grid-template-columns: 1fr; } .summary-row { grid-template-columns: repeat(2, 1fr); } .header { flex-direction: column; align-items: stretch; } }
</style>
</head>
<body>
<div class="header">
  <h1>Day 13 Observability Dashboard <span>Lab</span></h1>
  <div class="header-right">
    <span id="requestCount">0 requests</span>
    <span id="lastUpdate">updating...</span>
  </div>
</div>
<div class="content">
  <div id="summary" class="summary-row"></div>
  <div id="dashboard" class="grid"></div>
</div>
<script>
const COLORS = { p50: '#22d3ee', p95: '#f59e0b', p99: '#ef4444', good: '#22c55e', warn: '#f59e0b', bad: '#ef4444', purple: '#a78bfa', pink: '#f472b6' };
const CHARTS = {};

function fmt(ts) { return new Date(ts * 1000).toLocaleTimeString(); }
function sloColor(val, threshold, invert = false) {
  if (invert) return val <= threshold ? COLORS.good : COLORS.bad;
  return val >= threshold ? COLORS.good : COLORS.bad;
}

function createChart(id, type, labels, datasets, opts = {}) {
  if (CHARTS[id]) {
    CHARTS[id].data.labels = labels;
    datasets.forEach((ds, i) => { CHARTS[id].data.datasets[i].data = ds.data; if (ds.backgroundColor) CHARTS[id].data.datasets[i].backgroundColor = ds.backgroundColor; });
    CHARTS[id].update('none');
    return CHARTS[id];
  }
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  CHARTS[id] = new Chart(canvas, {
    type, data: { labels, datasets },
    options: { responsive: true, maintainAspectRatio: false, animation: false, interaction: { mode: 'index', intersect: false },
      scales: {
        x: { ticks: { color: '#64748b', maxTicksLimit: 10, font: { size: 10 } }, grid: { color: '#1e293b' } },
        y: { beginAtZero: true, ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: '#1e293b' } }
      },
      plugins: { legend: { labels: { color: '#94a3b8', boxWidth: 12, padding: 8, font: { size: 10 } } } },
      ...opts
    }
  });
  return CHARTS[id];
}

function buildSummary(data) {
  const el = document.getElementById('summary');
  el.innerHTML = `
    <div class="summary-card"><div class="value" style="color:${COLORS.p50}">${data.latency_p50}<span style="font-size:0.7rem;color:#64748b">ms</span></div><div class="label">Latency P50</div></div>
    <div class="summary-card"><div class="value" style="color:${COLORS.p95}">${data.latency_p95}<span style="font-size:0.7rem;color:#64748b">ms</span></div><div class="label">Latency P95</div></div>
    <div class="summary-card"><div class="value" style="color:${COLORS.p99}">${data.latency_p99}<span style="font-size:0.7rem;color:#64748b">ms</span></div><div class="label">Latency P99</div></div>
    <div class="summary-card"><div class="value" style="color:${sloColor(data.quality_avg, 0.75)}">${data.quality_avg}</div><div class="label">Quality Avg</div></div>
    <div class="summary-card"><div class="value" style="color:${COLORS.good}">${data.traffic}</div><div class="label">Total Requests</div></div>
    <div class="summary-card"><div class="value" style="color:${COLORS.warn}">$${data.total_cost_usd}</div><div class="label">Total Cost USD</div></div>
    <div class="summary-card"><div class="value" style="color:${Object.keys(data.error_breakdown).length ? COLORS.bad : COLORS.good}">${Object.keys(data.error_breakdown).length ? Object.values(data.error_breakdown).reduce((a,b)=>a+b,0) : 0}</div><div class="label">Errors</div></div>
    <div class="summary-card"><div class="value" style="color:${COLORS.purple}">${data.tokens_in_total}</div><div class="label">Tokens In</div></div>
  `;
  document.getElementById('requestCount').textContent = data.traffic + ' requests';
}

function buildPanels(data, hist) {
  const labels = hist.map(r => fmt(r.ts));
  const grid = document.getElementById('dashboard');
  const hasData = hist.length > 0;

  grid.innerHTML = `
    <div class="card"><div class="card-header"><h2>Latency P50 / P95 / P99</h2><span class="badge">ms</span></div><canvas id="c-latency"></canvas></div>
    <div class="card"><div class="card-header"><h2>Traffic</h2><span class="badge">cumulative</span></div><canvas id="c-traffic"></canvas></div>
    <div class="card"><div class="card-header"><h2>Error Rate</h2><span class="badge">breakdown</span></div>${hasData ? '<canvas id="c-errors"></canvas>' : '<div class="empty-chart"><svg width="32" height="32" fill="none" stroke="#475569" stroke-width="2"><circle cx="16" cy="16" r="14"/><path d="M16 10v8M16 22v0"/></svg>No errors recorded</div>'}</div>
    <div class="card"><div class="card-header"><h2>Cost per Request</h2><span class="badge">USD</span></div><canvas id="c-cost"></canvas></div>
    <div class="card"><div class="card-header"><h2>Tokens In / Out</h2><span class="badge">count</span></div><canvas id="c-tokens"></canvas></div>
    <div class="card"><div class="card-header"><h2>Quality Score</h2><span class="badge">${data.quality_avg >= 0.75 ? 'PASS ✓' : 'FAIL ✗'}</span></div><canvas id="c-quality"></canvas></div>
  `;

  if (!hasData) return;

  createChart('c-latency', 'line', labels, [
    { label: 'P50', data: hist.map(r => r.latency_p50), borderColor: COLORS.p50, backgroundColor: COLORS.p50 + '15', fill: true, tension: 0.3, pointRadius: 2 },
    { label: 'P95', data: hist.map(r => r.latency_p95), borderColor: COLORS.p95, borderDash: [4, 4], tension: 0.3, pointRadius: 2 },
    { label: 'P99', data: hist.map(r => r.latency_p99), borderColor: COLORS.p99, borderDash: [6, 3], tension: 0.3, pointRadius: 2 },
  ], { scales: { y: { title: { display: true, text: 'ms', color: '#64748b' } } } });

  createChart('c-traffic', 'line', labels, [
    { label: 'Requests', data: hist.map(r => r.traffic), borderColor: COLORS.good, backgroundColor: COLORS.good + '15', fill: true, tension: 0.1, stepped: true, pointRadius: 2 }
  ]);

  const errorTypes = [...new Set(hist.flatMap(r => Object.keys(r.error_breakdown || {})))];
  if (errorTypes.length) {
    createChart('c-errors', 'bar', labels, errorTypes.map(t => ({
      label: t, data: hist.map(r => r.error_breakdown?.[t] || 0), backgroundColor: COLORS.bad, borderRadius: 4
    })), { scales: { x: { stacked: true }, y: { stacked: true, title: { display: true, text: 'count', color: '#64748b' } } } });
  }

  createChart('c-cost', 'line', labels, [
    { label: 'Cost', data: hist.map(r => r.cost_usd), borderColor: COLORS.warn, backgroundColor: COLORS.warn + '15', fill: true, tension: 0.3, pointRadius: 2 }
  ], { scales: { y: { title: { display: true, text: 'USD', color: '#64748b' } } } });

  createChart('c-tokens', 'line', labels, [
    { label: 'In', data: hist.map(r => r.tokens_in), borderColor: COLORS.purple, backgroundColor: COLORS.purple + '15', fill: true, tension: 0.3, pointRadius: 2 },
    { label: 'Out', data: hist.map(r => r.tokens_out), borderColor: COLORS.pink, backgroundColor: COLORS.pink + '15', fill: true, tension: 0.3, pointRadius: 2 },
  ], { scales: { y: { title: { display: true, text: 'tokens', color: '#64748b' } } } });

  createChart('c-quality', 'line', labels, [
    { label: 'Score', data: hist.map(r => r.quality_score), borderColor: '#34d399', backgroundColor: '#34d399' + '15', fill: true, tension: 0.3, pointRadius: 2 },
  ], { scales: { y: { min: 0, max: 1, title: { display: true, text: 'score', color: '#64748b' } } } });
}

let loading = true;
async function refresh() {
  try {
    const [snapRes, histRes] = await Promise.all([fetch('/metrics'), fetch('/metrics/history')]);
    const data = await snapRes.json();
    const hist = await histRes.json();
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString() + ' | ' + hist.length + ' events';
    buildSummary(data);
    if (loading) { buildPanels(data, hist); loading = false; }
    else {
      const labels = hist.map(r => fmt(r.ts));
      const snap = data;
      Object.entries(CHARTS).forEach(([id, chart]) => {
        chart.data.labels = labels;
        if (id === 'c-latency') {
          chart.data.datasets[0].data = hist.map(r => r.latency_p50);
          chart.data.datasets[1].data = hist.map(r => r.latency_p95);
          chart.data.datasets[2].data = hist.map(r => r.latency_p99);
        } else if (id === 'c-traffic') chart.data.datasets[0].data = hist.map(r => r.traffic);
        else if (id === 'c-cost') chart.data.datasets[0].data = hist.map(r => r.cost_usd);
        else if (id === 'c-tokens') { chart.data.datasets[0].data = hist.map(r => r.tokens_in); chart.data.datasets[1].data = hist.map(r => r.tokens_out); }
        else if (id === 'c-quality') chart.data.datasets[0].data = hist.map(r => r.quality_score);
        else if (id === 'c-errors') {
          const errorTypes = [...new Set(hist.flatMap(r => Object.keys(r.error_breakdown || {})))];
          if (errorTypes.length) {
            chart.data.datasets = errorTypes.map(t => ({ label: t, data: hist.map(r => r.error_breakdown?.[t] || 0), backgroundColor: COLORS.bad, borderRadius: 4 }));
          }
        }
        chart.update('none');
      });
      document.querySelectorAll('.badge').forEach(b => {
        if (b.textContent.includes('PASS') || b.textContent.includes('FAIL'))
          b.textContent = snap.quality_avg >= 0.75 ? 'PASS ✓' : 'FAIL ✗';
      });
    }
  } catch (e) { console.error('refresh failed:', e); }
}

document.addEventListener('DOMContentLoaded', () => refresh());
setInterval(refresh, 10000);
</script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page() -> str:
    return DASHBOARD_HTML


@router.get("/metrics/history")
async def metrics_history() -> list[dict]:
    return history()
