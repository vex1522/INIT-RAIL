async function runPipeline() {
  const btn = document.getElementById('run-btn');
  const log = document.getElementById('log-output');
  const spinner = document.getElementById('spinner');

  if (btn) btn.disabled = true;
  if (spinner) spinner.style.display = 'inline-block';
  if (log) log.textContent = 'Starting pipeline...\n';

  try {
    const res = await fetch('/run', { method: 'POST' });
    const data = await res.json();

    if (res.status === 409) {
      if (log) log.textContent = 'Pipeline already running. Please wait.';
      return;
    }

    if (log) {
      log.textContent = '-- STDOUT --\n' + (data.stdout || '(empty)');
      log.textContent += '\n-- STDERR --\n' + (data.stderr || '(none)');
      log.scrollTop = log.scrollHeight;
    }

    pollStatus();
    loadDashboardStats();
  } catch (err) {
    if (log) log.textContent = 'Request failed: ' + err.message;
  } finally {
    if (btn) btn.disabled = false;
    if (spinner) spinner.style.display = 'none';
  }
}

async function pollStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    updateStatusCards(data.files);
  } catch (_) {}
}

function updateStatusCards(files) {
  if (!files) return;
  files.forEach(f => {
    const badge = document.getElementById('badge-' + f.key);
    const link = document.getElementById('link-' + f.key);
    if (badge) {
      badge.textContent = f.exists ? 'Ready' : 'Missing';
      badge.className = 'badge ' + (f.exists ? 'badge-ready' : 'badge-missing');
    }
    if (link) link.style.display = f.exists ? 'inline' : 'none';
  });
}

function switchChart(btn) {
  document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const key = btn.dataset.chart;
  const iframe = document.getElementById('chart-iframe');
  const img = document.getElementById('chart-img');
  if (!iframe || !img) return;
  if (key === 'static_dashboard') {
    iframe.style.display = 'none';
    img.style.display = 'block';
  } else {
    img.style.display = 'none';
    iframe.style.display = 'block';
    iframe.src = `/outputs/${key}.html`;
  }
}

async function loadDashboardStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const d = await res.json();
    const total = document.getElementById('stat-total');
    const avgPass = document.getElementById('stat-avg-pass');
    const avgDelay = document.getElementById('stat-avg-delay');
    const routes = document.getElementById('stat-routes');
    if (total) total.textContent = d.total_records?.toLocaleString() ?? '-';
    if (avgPass) avgPass.textContent = d.avg_passengers?.toFixed(0) ?? '-';
    if (avgDelay) avgDelay.textContent = d.avg_delay?.toFixed(1) ?? '-';
    if (routes) routes.textContent = d.total_routes ?? '-';

    const tbody = document.getElementById('routes-tbody');
    if (tbody && d.top10_routes?.length) {
      tbody.innerHTML = d.top10_routes.map((r, i) => `
        <tr>
          <td><span class="rank-badge">${i + 1}</span></td>
          <td><b>${r.route_id}</b></td>
          <td>${Number(r.avg_passengers).toFixed(0)}</td>
          <td>${Number(r.avg_delay).toFixed(1)}</td>
          <td><span class="score-pill">${Number(r.efficiency_score).toFixed(2)}</span></td>
          <td><span class="load-badge load-${r.peak_load?.toLowerCase()}">${r.peak_load}</span></td>
        </tr>`).join('');
    }
  } catch (_) {}
}

async function runPresetQuery() {
  const key = document.getElementById('preset-query')?.value;
  if (!key) return;
  await executeQuery({ preset: key });
}

async function runCustomQuery() {
  const filter = document.getElementById('custom-query')?.value.trim();
  if (!filter) return;
  await executeQuery({ filter });
}

async function executeQuery(payload) {
  const loading = document.getElementById('query-loading');
  const panel = document.getElementById('query-result');
  if (loading) loading.style.display = 'block';
  if (panel) panel.style.display = 'none';
  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    renderQueryResult(data);
  } catch (e) {
    alert('Query failed: ' + e.message);
  } finally {
    if (loading) loading.style.display = 'none';
  }
}

function renderQueryResult(data) {
  const panel = document.getElementById('query-result');
  if (!panel) return;
  panel.style.display = 'block';
  document.getElementById('result-title').textContent = data.title || 'Results';
  document.getElementById('result-count').textContent = `${data.rows?.length ?? 0} rows`;

  const chartWrap = document.getElementById('result-chart-wrap');
  if (data.chart_url) {
    document.getElementById('result-chart').src = data.chart_url;
    chartWrap.style.display = 'block';
  } else {
    chartWrap.style.display = 'none';
  }

  if (data.columns && data.rows) {
    document.getElementById('result-thead').innerHTML =
      '<tr>' + data.columns.map(c => `<th>${c}</th>`).join('') + '</tr>';
    document.getElementById('result-tbody').innerHTML =
      data.rows.map(row =>
        '<tr>' + data.columns.map(c => `<td>${row[c] ?? '-'}</td>`).join('') + '</tr>'
      ).join('');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  pollStatus();
  if (document.getElementById('routes-tbody')) loadDashboardStats();
});
