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
    /* Cyberpunk -- same palette/treatment as the rest of the app, see
       Config > Display and templates.py's own cyberpunk block. */
    [data-theme="cyberpunk"] {
        --bg-primary: #060410; --bg-panel: #0a0d12; --bg-tertiary: #0d1117; --bg-hover: #131a24;
        --text-primary: #eaf6fa; --text-secondary: #7fa8b8; --text-muted: #45606e;
        --border-color: #16222e; --accent-blue: #4f8cff; --accent-cyan: #22d3ee; --accent-orange: #a78bfa; --accent-green: #ff1a8c; --accent-amber: #ffcb47;
    }
    [data-theme="cyberpunk"] body {
        background-image: radial-gradient(circle at 15% 0%, rgba(34, 211, 238, 0.05), transparent 45%),
                           radial-gradient(circle at 85% 100%, rgba(255, 26, 140, 0.04), transparent 45%),
                           repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.012) 0px, rgba(255, 255, 255, 0.012) 1px, transparent 1px, transparent 3px);
    }
    [data-theme="cyberpunk"] .head h1, [data-theme="cyberpunk"] .brand-text {
        text-shadow: 0 0 10px rgba(34, 211, 238, 0.35);
    }
    [data-theme="cyberpunk"] table {
        position: relative;
        border-radius: 4px;
    }
    [data-theme="cyberpunk"] table::before, [data-theme="cyberpunk"] table::after {
        content: ''; position: absolute; width: 0.6rem; height: 0.6rem; pointer-events: none;
    }
    [data-theme="cyberpunk"] table::before { top: -1px; left: -1px; border-top: 2px solid var(--accent-blue); border-left: 2px solid var(--accent-blue); }
    [data-theme="cyberpunk"] table::after { bottom: -1px; right: -1px; border-bottom: 2px solid var(--accent-blue); border-right: 2px solid var(--accent-blue); }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: var(--font-mono); background: var(--bg-primary); color: var(--text-primary); font-size: 13px; line-height: 1.5; min-height: 100vh; }
    .topbar { display: flex; align-items: center; justify-content: space-between; padding: 0.6rem 1rem; background: var(--bg-panel); border-bottom: 1px solid var(--border-color); }
    .topbar-left { display: flex; align-items: center; gap: 1.5rem; }
    .brand { display: flex; align-items: center; gap: 0.5rem; text-decoration: none; color: inherit; }
    .brand-icon { color: var(--accent-blue); width: 1.1rem; height: 1.1rem; }
    .brand-text { font-weight: 700; font-size: 0.9rem; letter-spacing: 0.05em; color: var(--accent-blue); }
    .brand-text span { color: #ffffff; }
    [data-theme="light"] .brand-text span { color: var(--text-primary); }
    [data-theme="cyberpunk"] .brand-text span { color: var(--text-primary); }
    .nav { display: flex; gap: 0.25rem; }
    .nav-link { color: var(--text-secondary); text-decoration: none; padding: 0.35rem 0.7rem; border-radius: 6px; font-size: 0.75rem; }
    .nav-link:hover { color: var(--text-primary); background: var(--bg-tertiary); }
    .nav-link.active { color: var(--text-primary); background: var(--bg-tertiary); }
    [data-theme="cyberpunk"] .nav-link { border-bottom: 2px solid transparent; }
    [data-theme="cyberpunk"] .nav-link.active { border-bottom-color: var(--accent-red); border-radius: 6px 6px 0 0; }
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

    .model-filter { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; margin-bottom: 0.75rem; }
    .model-filter .label { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-right: 0.2rem; }
    .model-chip { background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 999px; padding: 0.15rem 0.6rem; font-size: 0.7rem; cursor: pointer; user-select: none; }
    .model-chip.hidden-model { color: var(--text-muted); text-decoration: line-through; opacity: 0.6; border-style: dashed; }
    .model-chip .n { color: var(--text-muted); margin-left: 0.3rem; }

    /* Same "Filters | Priority" two-column layout and class names as the
       dashboard's own stat-pair, so the two pages read as one product. */
    .stat-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem; align-items: stretch; }
    @media (max-width: 900px) { .stat-pair { grid-template-columns: 1fr; } }
    .stat-card { background: var(--bg-panel); border: 1px solid var(--border-color); border-radius: 10px; padding: 0.5rem 0.6rem; }
    .stat-box { padding: 0.7rem 1rem; min-width: 0; }
    .stat-cap { font-size: 0.55rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
    .filters-box, .priority-card { display: flex; flex-direction: column; }
    .filters-head { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-bottom: 0.55rem; }
    .filters-title, .priority-title { margin: 0; }
    .filter-count { font-size: 0.72rem; color: var(--text-secondary); }
    .filter-count b { color: var(--text-primary); font-variant-numeric: tabular-nums; }
    .filter-checks { display: flex; flex-wrap: wrap; gap: 0.4rem 1.25rem; margin-bottom: 0.55rem; }
    .filter-check { display: flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: var(--text-secondary); cursor: pointer; }
    .filter-sliders { display: grid; grid-template-columns: max-content 1fr 4.5rem; gap: 0.45rem 0.75rem; align-items: center; }
    .filter-sliders .stat-cap { margin: 0; }
    .filter-sliders input[type="range"] { width: 100%; min-width: 0; }
    .slider-value { font-size: 0.75rem; color: var(--text-primary); text-align: right; white-space: nowrap; }
    .priority-head { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.55rem; flex-wrap: wrap; }
    .priority-hint { font-size: 0.65rem; color: var(--text-muted); }
    .priority-list { display: flex; flex-wrap: wrap; gap: 0.5rem; align-content: flex-start; max-height: 9rem; overflow-y: auto; }
    .priority-clear { margin-left: auto; background: transparent; border: none; color: var(--text-muted); font-size: 0.65rem; cursor: pointer; text-decoration: underline; }
    .priority-clear:hover { color: var(--text-primary); }
    .priority-dismiss { position: absolute; top: 2px; right: 3px; width: 1.1rem; height: 1.1rem; padding: 0; line-height: 1; border: none; border-radius: 50%; background: transparent; color: var(--text-muted); font-size: 0.95rem; cursor: pointer; }
    .priority-dismiss:hover { background: var(--bg-hover); color: var(--text-primary); }
    .priority-tag { background: var(--accent-amber); color: #1a1200; font-weight: 700; font-size: 0.62rem; padding: 0.05rem 0.35rem; border-radius: 4px; letter-spacing: 0.03em; }

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
    <button class="theme-toggle" id="theme-toggle" title="Cycle theme: dark / light / cyberpunk">&#9728;</button>
</header>

<div class="page">
    <div class="head">
        <div>
            <h1>RF log (temporary)</h1>
            <p class="note">Raw, un-deduplicated feed of everything rtl_433 decodes on 433/868 MHz -- separate from the device list. Diagnostic only: use it to see what turns up and decide what's worth building proper handling for.</p>
        </div>
        <div class="controls">
            <span class="count"><b id="count">0</b> shown <span id="count-total" style="color: var(--text-muted);"></span></span>
            <button class="btn on" id="pause-btn" onclick="togglePause()">Pause</button>
            <button class="btn" onclick="loadLog(true)">Refresh now</button>
        </div>
    </div>

    <div class="stat-pair">
        <div class="stat-card stat-box filters-box">
            <div class="filters-head">
                <span class="stat-cap filters-title">Filters</span>
                <span class="filter-count">All events <b id="count-events-all">0</b></span>
            </div>
            <div class="filter-checks">
                <label class="filter-check" title="Hides weather-station models (Nexus-TH, LaCrosse, Bresser, Auriol, Fine Offset, etc.)">
                    <input type="checkbox" id="hide-weather-toggle" onchange="toggleWeatherStations()">
                    Hide weather stations
                </label>
            </div>
            <div class="filter-sliders">
                <span class="stat-cap">RSSI &ge;</span>
                <input type="range" id="rssi-threshold" min="-100" max="0" value="-100" step="1" oninput="onRssiThresholdChange()">
                <span id="rssi-threshold-value" class="slider-value">-100 dBm</span>
            </div>
        </div>
        <div class="stat-card stat-box priority-card" id="priority-box">
            <div class="priority-head">
                <span style="color: #f5c518; font-size: 0.9rem;">&#9733;</span>
                <span class="stat-cap priority-title">TPMS</span>
                <span class="priority-hint">Tyre-pressure sensors seen recently &mdash; stay until dismissed</span>
                <button type="button" class="priority-clear" id="priority-clear-all" onclick="dismissAllTpms()" hidden>Dismiss all</button>
            </div>
            <div class="priority-list" id="priority-list"></div>
        </div>
    </div>

    <div class="model-filter" id="model-filter"><span class="label">Models (click to hide)</span></div>
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
        var saved = localStorage.getItem('bluewatch_theme');
        if (saved) document.documentElement.setAttribute('data-theme', saved);
    })();
    document.getElementById('theme-toggle').onclick = function() {
        var order = ['dark', 'light', 'cyberpunk'];
        var cur = document.documentElement.getAttribute('data-theme') || 'dark';
        var next = order[(order.indexOf(cur) + 1) % order.length];
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem('bluewatch_theme', next); } catch (e) {}
    };

    var paused = false;
    var lastMaxId = 0;
    var META_KEYS = {time:1, model:1, id:1, mic:1, protocol:1};

    // Hide-by-model filter (e.g. drop a common weather station like
    // Nexus-TH once you've seen enough of it) -- remembered per browser,
    // same as the theme choice. Chips are rebuilt from whatever models are
    // actually present each refresh, so new models just show up.
    var hiddenModels = {};
    try {
        var storedHidden = JSON.parse(localStorage.getItem('bluewatch_rf_hidden_models') || '[]');
        storedHidden.forEach(function(m) { hiddenModels[m] = true; });
    } catch (e) {}

    function saveHiddenModels() {
        try { localStorage.setItem('bluewatch_rf_hidden_models', JSON.stringify(Object.keys(hiddenModels))); } catch (e) {}
    }

    function toggleModel(model) {
        if (hiddenModels[model]) delete hiddenModels[model];
        else hiddenModels[model] = true;
        saveHiddenModels();
        renderFromCache();
    }

    // Same name patterns as classifier.py's rtl_433 weather-station match
    // (TYPE_SMART_HOME block) -- kept in sync by hand since this list is
    // small and rarely changes; matches loosely against the raw model
    // string rtl_433 reports, same as everywhere else on this page.
    var WEATHER_PATTERNS = [
        'lacrosse', 'la crosse', 'bresser', 'auriol', 'fineoffset', 'fine offset',
        'oregon-th', 'oregon scientific', 'nexus-th', 'wh1080', 'wh31', 'wh51',
        'wh65', 'wh80', 'wh90', 'wh45', 'ws80', 'ws90',
    ];

    function isWeatherModel(model) {
        var m = (model || '').toLowerCase();
        return WEATHER_PATTERNS.some(function(p) { return m.indexOf(p) !== -1; });
    }

    function toggleWeatherStations() {
        var checked = document.getElementById('hide-weather-toggle').checked;
        var models = {};
        lastEvents.forEach(function(e) { models[e.model || '?'] = true; });
        Object.keys(models).filter(isWeatherModel).forEach(function(m) {
            if (checked) hiddenModels[m] = true;
            else delete hiddenModels[m];
        });
        saveHiddenModels();
        renderFromCache();
    }

    var rssiFloor = -100;
    function onRssiThresholdChange() {
        rssiFloor = parseInt(document.getElementById('rssi-threshold').value, 10);
        document.getElementById('rssi-threshold-value').textContent = rssiFloor + ' dBm';
        renderFromCache();
    }

    // TPMS priority box -- separate from the model-hide filter above:
    // stays visible (doesn't scroll away in the table) until acknowledged,
    // same idea as the dashboard's own Priority box for watched devices.
    // Dismissed keys are in-memory only (reset on refresh) -- this page is
    // meant to be watched live, not treated as a persistent alert log.
    var dismissedTpms = {};

    function isTpmsModel(model) {
        return (model || '').toLowerCase().indexOf('tpms') !== -1;
    }

    function dismissTpms(key) {
        dismissedTpms[key] = true;
        renderPriorityBox();
    }

    function dismissAllTpms() {
        lastEvents.forEach(function(e) {
            if (isTpmsModel(e.model)) dismissedTpms[e.device_key || e.model] = true;
        });
        renderPriorityBox();
    }

    function renderPriorityBox() {
        var list = document.getElementById('priority-list');
        var clearBtn = document.getElementById('priority-clear-all');
        var latestByKey = {};
        lastEvents.forEach(function(e) {
            if (!isTpmsModel(e.model)) return;
            var key = e.device_key || e.model;
            if (dismissedTpms[key]) return;
            if (!latestByKey[key] || e.id > latestByKey[key].id) latestByKey[key] = e;
        });
        var cards = Object.keys(latestByKey).map(function(k) { return latestByKey[k]; })
            .sort(function(a, b) { return b.id - a.id; });

        clearBtn.hidden = cards.length < 2;
        if (!cards.length) {
            list.innerHTML = '<span style="font-size: 0.72rem; color: var(--text-muted);">None right now</span>';
            return;
        }
        list.innerHTML = cards.map(function(e) {
            var key = e.device_key || e.model;
            return '<div style="position:relative; display:flex; align-items:center; gap:0.4rem; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 6px; padding: 0.3rem 1.6rem 0.3rem 0.6rem; font-size: 0.75rem;">' +
                '<span class="priority-tag">TPMS</span>' +
                '<span>' + escapeHtml(e.model || '?') + '</span>' +
                '<span style="color: var(--text-muted); font-size: 0.68rem;">' + escapeHtml(e.timestamp || '') + '</span>' +
                '<button type="button" class="priority-dismiss" title="Dismiss" data-key="' + escapeHtml(key) + '">&times;</button>' +
                '</div>';
        }).join('');
    }

    // device_key/model come from RF-decoded data (not fully trusted --
    // a crafted transmission could in principle contain quote/angle-bracket
    // characters), so the dismiss button carries its key via a data
    // attribute (HTML-escaped above) rather than a string-built inline
    // onclick handler, and this single delegated listener reads it back.
    document.getElementById('priority-list').addEventListener('click', function(e) {
        var btn = e.target.closest('.priority-dismiss');
        if (btn) dismissTpms(btn.dataset.key);
    });

    // Same data-attribute + delegated-listener pattern for the model
    // chips -- model names are also RF-decoded, not trusted input.
    document.getElementById('model-filter').addEventListener('click', function(e) {
        var chip = e.target.closest('.model-chip');
        if (chip && chip.dataset.model !== undefined) toggleModel(chip.dataset.model);
    });

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

    var lastEvents = [];

    function renderFromCache() {
        var events = lastEvents;
        renderPriorityBox();
        var counts = {};
        events.forEach(function(e) { var m = e.model || '?'; counts[m] = (counts[m] || 0) + 1; });
        var models = Object.keys(counts).sort();
        var filterEl = document.getElementById('model-filter');
        var html = '<span class="label">Models (click to hide)</span>';
        models.forEach(function(m) {
            html += '<span class="model-chip' + (hiddenModels[m] ? ' hidden-model' : '') + '" data-model="' + escapeHtml(m) + '">' +
                escapeHtml(m) + '<span class="n">' + counts[m] + '</span></span>';
        });
        filterEl.innerHTML = html;

        var weatherModelsNow = models.filter(isWeatherModel);
        document.getElementById('hide-weather-toggle').checked =
            weatherModelsNow.length > 0 && weatherModelsNow.every(function(m) { return hiddenModels[m]; });

        document.getElementById('count-events-all').textContent = events.length;

        var visible = events.filter(function(e) {
            if (hiddenModels[e.model || '?']) return false;
            if (e.rssi != null && e.rssi < rssiFloor) return false;
            return true;
        });
        document.getElementById('count').textContent = visible.length;
        var totalEl = document.getElementById('count-total');
        totalEl.textContent = visible.length !== events.length ? ('of ' + events.length) : '';

        var tbody = document.getElementById('rows');
        if (!events.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty">No sub-GHz events yet -- waiting for rtl_433 / RTL-SDR.</td></tr>';
            return;
        }
        if (!visible.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty">Nothing matches the current filters -- click a chip above or lower the RSSI floor.</td></tr>';
            return;
        }
        var rowsHtml = '';
        for (var i = 0; i < visible.length; i++) {
            var e = visible[i];
            var isNew = e.id > lastMaxId && lastMaxId > 0;
            rowsHtml += '<tr' + (isNew ? ' class="is-new"' : '') + '>' +
                '<td class="t-time">' + escapeHtml(e.timestamp || '') + '</td>' +
                '<td class="t-model">' + escapeHtml(e.model || '?') + '</td>' +
                '<td class="t-key">' + escapeHtml(e.device_key || '') + '</td>' +
                '<td class="t-rssi">' + (e.rssi != null ? Number(e.rssi).toFixed(1) : '-') + '</td>' +
                '<td class="t-raw">' + fmtFields(e.raw || {}) + '</td>' +
                '</tr>';
        }
        tbody.innerHTML = rowsHtml;
    }

    function loadLog(force) {
        if (paused && !force) return;
        fetch('/api/rf-log?limit=300').then(function(r) { return r.json(); }).then(function(events) {
            var maxId = events.length ? events[0].id : lastMaxId;
            lastEvents = events;
            renderFromCache();
            lastMaxId = maxId;
        }).catch(function() {});
    }

    loadLog(true);
    setInterval(function() { loadLog(false); }, 4000);
</script>
</body>
</html>
"""
