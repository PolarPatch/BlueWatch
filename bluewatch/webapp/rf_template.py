"""The /rf page: a temporary, raw firehose view of everything rtl_433
decodes on 433/868 MHz -- every event, un-deduplicated, independent of
the devices table. Purely diagnostic: it exists so the operator can see
what actually gets picked up before deciding what deserves proper
handling. Receive-only, same as everything sub-GHz in this project."""

RF_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BlueWatch - RF log</title>
<style>
    :root {
        --bg-primary: #0d1117; --bg-panel: #161b22; --bg-tertiary: #1c232c; --bg-hover: #242c37;
        --text-primary: #e6edf3; --text-secondary: #a6afb9; --text-muted: #7d8590;
        --border-color: #30363d; --accent-blue: #2563eb; --accent-green: #3fb950; --accent-amber: #f59e0b;
        --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', Consolas, monospace;
    }
    [data-theme="light"] {
        --bg-primary: #f5f5f5; --bg-panel: #ffffff; --bg-tertiary: #ececec; --bg-hover: #dedede;
        --text-primary: #1a1a1a; --text-secondary: #555555; --text-muted: #888888; --border-color: #d0d0d0;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: var(--font-mono); background: var(--bg-primary); color: var(--text-primary); font-size: 13px; line-height: 1.5; min-height: 100vh; }
    .topbar { display: flex; align-items: center; justify-content: space-between; padding: 0.6rem 1rem; background: var(--bg-panel); border-bottom: 1px solid var(--border-color); }
    .topbar-left { display: flex; align-items: center; gap: 1.5rem; }
    .brand { display: flex; align-items: center; gap: 0.5rem; text-decoration: none; color: inherit; }
    .brand-icon { color: var(--accent-blue); width: 1.1rem; height: 1.1rem; }
    .brand-text { font-weight: 700; font-size: 0.9rem; letter-spacing: 0.05em; color: var(--accent-blue); }
    .brand-text span { color: #ffffff; }
    [data-theme="light"] .brand-text span { color: var(--text-primary); }
    .nav { display: flex; gap: 0.25rem; }
    .nav-link { color: var(--text-secondary); text-decoration: none; padding: 0.35rem 0.7rem; border-radius: 6px; font-size: 0.75rem; }
    .nav-link:hover { color: var(--text-primary); background: var(--bg-tertiary); }
    .nav-link.active { color: var(--text-primary); background: var(--bg-tertiary); }
    .theme-toggle { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 6px; padding: 0.25rem 0.5rem; cursor: pointer; font-family: var(--font-mono); }

    .page { padding: 1rem; max-width: 1400px; margin: 0 auto; }
    .head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem 1.5rem; margin-bottom: 0.75rem; }
    .head h1 { font-size: 1rem; font-weight: 700; }
    .note { color: var(--text-muted); font-size: 0.75rem; margin-top: 0.15rem; max-width: 60rem; }
    .controls { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem 1rem; }
    .controls label { display: flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: var(--text-secondary); cursor: pointer; }
    .controls select, .btn { background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: 6px; padding: 0.3rem 0.6rem; font-family: var(--font-mono); font-size: 0.72rem; cursor: pointer; }
    .btn:hover { background: var(--bg-hover); }
    .btn.on { color: var(--accent-amber); border-color: var(--accent-amber); }
    .count { color: var(--text-secondary); font-size: 0.8rem; }
    .count b { color: var(--text-primary); font-variant-numeric: tabular-nums; }

    table { width: 100%; border-collapse: collapse; background: var(--bg-panel); border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
    thead th { text-align: left; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--border-color); background: var(--bg-tertiary); position: sticky; top: 0; }
    tbody td { padding: 0.45rem 0.7rem; border-bottom: 1px solid var(--border-color); vertical-align: top; font-size: 0.78rem; }
    tbody tr:last-child td { border-bottom: none; }
    tbody tr:hover { background: var(--bg-hover); }
    tbody tr.is-new { animation: flash 1.5s ease-out; }
    @keyframes flash { from { background: rgba(63,185,80,0.25); } to { background: transparent; } }
    .t-time { white-space: nowrap; color: var(--text-secondary); }
    .t-model { font-weight: 600; }
    .t-key { color: var(--text-muted); font-size: 0.72rem; }
    .t-rssi { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .t-raw { color: var(--text-secondary); font-size: 0.72rem; word-break: break-all; max-width: 40rem; }
    .table-wrap { max-height: 78vh; overflow: auto; border-radius: 8px; }
    .empty { padding: 2rem; text-align: center; color: var(--text-muted); }
</style>
</head>
<body>
<header class="topbar">
    <div class="topbar-left">
        <a href="/" class="brand">
            <svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7 7 10 10-5 5V2l5 5L7 17"/></svg>
            <span class="brand-text">Blue<span>Watch</span></span>
        </a>
        <nav class="nav">
            <a href="/" class="nav-link">Dashboard</a>
            <a href="/all" class="nav-link">All devices</a>
            <a href="/radar" class="nav-link">Radar</a>
            <a href="/rf" class="nav-link active">RF log</a>
            <a href="/settings" class="nav-link">Config</a>
        </nav>
    </div>
    <button class="theme-toggle" id="theme-toggle" title="Toggle light/dark mode">&#9728;</button>
</header>

<div class="page">
    <div class="head">
        <div>
            <h1>RF log (temporary)</h1>
            <p class="note">Raw, un-deduplicated feed of everything rtl_433 decodes on 433/868 MHz -- separate from the device list. Diagnostic only: use it to see what turns up and decide what's worth building proper handling for.</p>
        </div>
        <div class="controls">
            <span class="count"><b id="count">0</b> events</span>
            <button class="btn on" id="pause-btn" onclick="togglePause()">Pause</button>
            <button class="btn" onclick="loadLog(true)">Refresh now</button>
        </div>
    </div>
    <div class="table-wrap">
        <table>
            <thead>
                <tr><th>Time</th><th>Model</th><th>Key</th><th>RSSI</th><th>Decoded fields</th></tr>
            </thead>
            <tbody id="rows"><tr><td colspan="5" class="empty">Loading...</td></tr></tbody>
        </table>
    </div>
</div>

<script>
    (function() {
        var saved = localStorage.getItem('theme');
        if (saved) document.documentElement.setAttribute('data-theme', saved);
    })();
    document.getElementById('theme-toggle').onclick = function() {
        var cur = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', cur);
        try { localStorage.setItem('theme', cur); } catch (e) {}
    };

    var paused = false;
    var lastMaxId = 0;
    var META_KEYS = {time:1, model:1, id:1, mic:1, protocol:1};

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function fmtFields(raw) {
        var parts = [];
        for (var k in raw) {
            if (!raw.hasOwnProperty(k) || META_KEYS[k]) continue;
            var v = raw[k];
            if (v === null || v === undefined || typeof v === 'object') continue;
            parts.push(escapeHtml(k) + '=' + escapeHtml(v));
        }
        return parts.join(' &middot; ') || '<span style="color:var(--text-muted)">(no extra fields)</span>';
    }

    function togglePause() {
        paused = !paused;
        var b = document.getElementById('pause-btn');
        b.textContent = paused ? 'Resume' : 'Pause';
        b.classList.toggle('on', !paused);
    }

    function loadLog(force) {
        if (paused && !force) return;
        fetch('/api/rf-log?limit=300').then(function(r) { return r.json(); }).then(function(events) {
            document.getElementById('count').textContent = events.length;
            var tbody = document.getElementById('rows');
            if (!events.length) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty">No sub-GHz events yet -- waiting for rtl_433 / RTL-SDR.</td></tr>';
                return;
            }
            var maxId = events[0].id;
            var html = '';
            for (var i = 0; i < events.length; i++) {
                var e = events[i];
                var isNew = e.id > lastMaxId && lastMaxId > 0;
                html += '<tr' + (isNew ? ' class="is-new"' : '') + '>' +
                    '<td class="t-time">' + escapeHtml(e.timestamp || '') + '</td>' +
                    '<td class="t-model">' + escapeHtml(e.model || '?') + '</td>' +
                    '<td class="t-key">' + escapeHtml(e.device_key || '') + '</td>' +
                    '<td class="t-rssi">' + (e.rssi != null ? Number(e.rssi).toFixed(1) : '-') + '</td>' +
                    '<td class="t-raw">' + fmtFields(e.raw || {}) + '</td>' +
                    '</tr>';
            }
            tbody.innerHTML = html;
            lastMaxId = maxId;
        }).catch(function() {});
    }

    loadLog(true);
    setInterval(function() { loadLog(false); }, 4000);
</script>
</body>
</html>
"""
