"""The /crowd page: how many people are around right now, through the day,
compared with what is usual for the time. See crowd.py for the method."""

CROWD_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="cyberpunk">
<head>
<script>try { document.documentElement.setAttribute('data-theme', localStorage.getItem('bluewatch_theme') || 'cyberpunk'); } catch (e) {}</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BlueWatch - Crowd</title>
<style>
    :root {
        --bg-primary: #0d1117; --bg-panel: #161b22; --bg-tertiary: #1c232c; --bg-hover: #242c37;
        --text-primary: #e6edf3; --text-secondary: #a6afb9; --text-muted: #7d8590;
        --border-color: #30363d; --accent-blue: #2563eb; --accent-cyan: #38bdf8; --accent-red: #f85149; --accent-amber: #f59e0b;
        --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', Consolas, monospace;
    }
    [data-theme="light"] {
        --bg-primary: #f5f5f5; --bg-panel: #ffffff; --bg-tertiary: #ececec; --bg-hover: #dedede;
        --text-primary: #1a1a1a; --text-secondary: #555555; --text-muted: #888888; --border-color: #d0d0d0;
        --accent-cyan: #0284c7;
    }
    [data-theme="cyberpunk"] {
        --bg-primary: #060410; --bg-panel: #0a0d12; --bg-tertiary: #0d1117; --bg-hover: #131a24;
        --text-primary: #eaf6fa; --text-secondary: #7fa8b8; --text-muted: #45606e;
        --border-color: #16222e; --accent-blue: #4f8cff; --accent-cyan: #22d3ee; --accent-red: #ff1a8c; --accent-amber: #ffcb47;
    }
    [data-theme="cyberpunk"] body {
        background-image: radial-gradient(circle at 15% 0%, rgba(34, 211, 238, 0.05), transparent 45%),
                           radial-gradient(circle at 85% 100%, rgba(255, 26, 140, 0.04), transparent 45%),
                           repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.012) 0px, rgba(255, 255, 255, 0.012) 1px, transparent 1px, transparent 3px);
    }
    [data-theme="cyberpunk"] .head h1, [data-theme="cyberpunk"] .brand-text, [data-theme="cyberpunk"] .big {
        text-shadow: 0 0 10px rgba(34, 211, 238, 0.35);
    }
    [data-theme="cyberpunk"] .card { border-radius: 4px; position: relative; }
    [data-theme="cyberpunk"] .card::before { content: ''; position: absolute; top: -1px; left: -1px; width: 0.6rem; height: 0.6rem;
        border-top: 2px solid var(--accent-cyan); border-left: 2px solid var(--accent-cyan); }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: var(--font-mono); background: var(--bg-primary); color: var(--text-primary); font-size: 13px; line-height: 1.5; min-height: 100vh; }
    .topbar { display: flex; align-items: center; justify-content: space-between; padding: 0.6rem 1rem; background: var(--bg-panel); border-bottom: 1px solid var(--border-color); }
    .topbar-left { display: flex; align-items: center; gap: 1.5rem; }
    .brand { display: flex; align-items: center; gap: 0.5rem; text-decoration: none; color: inherit; }
    .brand-icon { color: var(--accent-blue); width: 1.1rem; height: 1.1rem; }
    .brand-text { font-weight: 700; font-size: 0.9rem; letter-spacing: 0.05em; color: var(--accent-blue); }
    .brand-text span { color: #ffffff; }
    [data-theme="light"] .brand-text span, [data-theme="cyberpunk"] .brand-text span { color: var(--text-primary); }
    .nav { display: flex; gap: 0.25rem; flex-wrap: wrap; }
    .nav-link { color: var(--text-secondary); text-decoration: none; padding: 0.35rem 0.7rem; border-radius: 6px; font-size: 0.75rem; }
    .nav-link:hover { color: var(--text-primary); background: var(--bg-tertiary); }
    .nav-link.active { color: var(--text-primary); background: var(--bg-tertiary); }
    [data-theme="cyberpunk"] .nav-link { border-bottom: 2px solid transparent; }
    [data-theme="cyberpunk"] .nav-link.active { border-bottom-color: var(--accent-red); border-radius: 6px 6px 0 0; }
    .theme-toggle { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 6px; padding: 0.25rem 0.5rem; cursor: pointer; font-family: var(--font-mono); }

    .page { padding: 1rem; max-width: 1400px; margin: 0 auto; }
    .head { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 0.75rem 1.5rem; margin-bottom: 1rem; }
    .head h1 { font-size: 1rem; font-weight: 700; }
    .note { color: var(--text-muted); font-size: 0.75rem; margin-top: 0.15rem; max-width: 60rem; }
    .btn { background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 6px; padding: 0.3rem 0.7rem; font-family: var(--font-mono); font-size: 0.72rem; cursor: pointer; }
    .btn:hover { background: var(--bg-hover); }
    .btn.on { color: var(--accent-cyan); border-color: var(--accent-cyan); }
    .controls { display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap; }
    .bucket { display: flex; align-items: center; gap: 0.6rem; font-size: 0.72rem; color: var(--text-secondary); }
    .bucket input { width: 7rem; accent-color: var(--accent-cyan); }
    .bucket-ticks { display: flex; justify-content: space-between; width: 7rem; font-size: 0.6rem; color: var(--text-muted); margin-top: -0.2rem; }
    .bucket-value { color: var(--accent-cyan); min-width: 3.2rem; font-variant-numeric: tabular-nums; }

    .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 0.75rem; }
    @media (max-width: 900px) { .cards { grid-template-columns: repeat(2, 1fr); } }
    .card { background: var(--bg-panel); border: 1px solid var(--border-color); border-radius: 10px; padding: 0.8rem 1rem; min-width: 0; }
    .cap { font-size: 0.6rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.06em; }
    .big { font-size: 2.4rem; font-weight: 700; line-height: 1.1; font-variant-numeric: tabular-nums; color: var(--accent-cyan); margin-top: 0.2rem; }
    .big.small { font-size: 1.7rem; color: var(--text-primary); }
    .sub { font-size: 0.7rem; color: var(--text-muted); margin-top: 0.2rem; }
    .sub b { color: var(--text-secondary); font-weight: 600; }
    .chart-card { padding: 0.8rem 1rem 0.6rem; }
    .chart-head { display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
    .legend { display: flex; gap: 1rem; font-size: 0.68rem; color: var(--text-secondary); }
    .legend i { display: inline-block; width: 1.1rem; height: 0; border-top: 2px solid; vertical-align: middle; margin-right: 0.35rem; }
    canvas { width: 100%; height: 320px; display: block; }
    .tip { position: fixed; pointer-events: none; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 6px; padding: 0.35rem 0.55rem; font-size: 0.7rem; display: none; z-index: 5; }
    .about { margin-top: 0.75rem; color: var(--text-muted); font-size: 0.72rem; max-width: 60rem; }
    .about p + p { margin-top: 0.4rem; }
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
            <a href="/crowd" class="nav-link active">Crowd</a>
            <a href="/rf" class="nav-link">RF log</a>
            <a href="/settings" class="nav-link">Config</a>
        </nav>
    </div>
    <button class="theme-toggle" id="theme-toggle" title="Cycle theme: dark / light / cyberpunk">&#9889;</button>
</header>

<div class="page">
    <div class="head">
        <div>
            <h1>Crowd</h1>
            <p class="note">Roughly how many people are around, counted from the phones BlueWatch hears. Totals only: nothing is kept about anyone.</p>
        </div>
        <div class="controls">
            <label class="bucket" title="How long each count looks back. 1 minute catches people passing by; 10 minutes shows who stays.">
                <span>Count per</span>
                <span>
                    <input type="range" id="bucket" min="0" max="2" step="1" value="1" oninput="setBucket(this.value)">
                    <span class="bucket-ticks"><span>1</span><span>5</span><span>10</span></span>
                </span>
                <span class="bucket-value" id="bucket-value">5 min</span>
            </label>
            <span>
                <button class="btn on" id="range-24h" onclick="setRange('24h')">24 hours</button>
                <button class="btn" id="range-7d" onclick="setRange('7d')">7 days</button>
            </span>
        </div>
    </div>

    <div class="cards">
        <div class="card"><div class="cap">People now</div><div class="big" id="people-now">&ndash;</div><div class="sub" id="people-sub">last 5 minutes</div></div>
        <div class="card"><div class="cap">Personal devices</div><div class="big small" id="devices-now">&ndash;</div><div class="sub">phones, watches, earbuds, wearables, tablets, laptops</div></div>
        <div class="card"><div class="cap">Usual for now</div><div class="big small" id="usual-now">&ndash;</div><div class="sub" id="usual-sub">median, same time, last 7 days</div></div>
        <div class="card"><div class="cap">Peak today</div><div class="big small" id="peak-today">&ndash;</div><div class="sub" id="peak-sub">highest 5-minute count since midnight</div></div>
    </div>

    <div class="card chart-card">
        <div class="chart-head">
            <span class="cap" id="chart-title">People, last 24 hours</span>
            <span class="legend">
                <span><i style="border-color: var(--accent-cyan);"></i>people</span>
                <span><i style="border-color: var(--text-muted); border-top-style: dashed;"></i>usual</span>
                <span><i style="border-color: var(--accent-red); opacity: 0.6;"></i>personal devices</span>
            </span>
        </div>
        <canvas id="chart"></canvas>
    </div>

    <div class="about">
        <p>How it works: for each minute, 5 minutes or 10 minutes (the slider) BlueWatch counts the phones it heard at <span id="floor">-80</span> dBm or louder (about the radar's outer ring). Phones change their Bluetooth address every 15 minutes or so; two phone addresses that never overlap and are about as loud are counted once. Trackers, TVs, beacons and unidentified devices are left out.</p>
        <p>It is an estimate. People without a phone, or with Bluetooth off, are not counted; people in the house next door are. The level matters less than the changes. Idea from ESP32-Paxcounter.</p>
    </div>
</div>
<div class="tip" id="tip"></div>

<script>
    function themeIcon() {
        var t = document.documentElement.getAttribute('data-theme');
        document.getElementById('theme-toggle').textContent = t === 'light' ? '\u263d' : (t === 'cyberpunk' ? '\u26a1' : '\u2600');
    }
    document.getElementById('theme-toggle').onclick = function() {
        var order = ['dark', 'light', 'cyberpunk'];
        var cur = document.documentElement.getAttribute('data-theme') || 'cyberpunk';
        var next = order[(order.indexOf(cur) + 1) % order.length];
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem('bluewatch_theme', next); } catch (e) {}
        themeIcon();
        draw();
    };
    themeIcon();

    var range = '24h';
    var BUCKETS = [1, 5, 10];
    var minutes = 5;
    try { minutes = parseInt(localStorage.getItem('bluewatch_crowd_minutes'), 10) || 5; } catch (e) {}
    if (BUCKETS.indexOf(minutes) < 0) minutes = 5;
    document.getElementById('bucket').value = BUCKETS.indexOf(minutes);

    function setBucket(i) {
        minutes = BUCKETS[parseInt(i, 10)] || 5;
        try { localStorage.setItem('bluewatch_crowd_minutes', String(minutes)); } catch (e) {}
        load();
    }
    var data = null;
    var points = [];

    function setRange(r) {
        range = r;
        document.getElementById('range-24h').classList.toggle('on', r === '24h');
        document.getElementById('range-7d').classList.toggle('on', r === '7d');
        document.getElementById('chart-title').textContent = r === '7d' ? 'People, last 7 days' : 'People, last 24 hours';
        load();
    }

    function text(id, value) { document.getElementById(id).textContent = (value === null || value === undefined) ? '–' : value; }

    async function load() {
        try {
            var r = await fetch('/api/crowd?range=' + range + '&minutes=' + minutes);
            if (!r.ok) return;
            data = await r.json();
        } catch (e) { return; }
        text('people-now', data.now.people);
        text('devices-now', data.now.devices);
        text('usual-now', data.usual_now);
        text('peak-today', data.peak_today);
        text('floor', data.rssi_floor);
        var span = minutes === 1 ? 'minute' : minutes + ' minutes';
        text('bucket-value', minutes + ' min');
        text('peak-sub', 'highest ' + (minutes === 1 ? '1-minute' : minutes + '-minute') + ' count since midnight');
        var sub = 'last ' + span;
        if (data.usual_now !== null && data.usual_now !== undefined) {
            var diff = data.now.people - data.usual_now;
            sub = diff === 0 ? 'as usual for this time' : (Math.abs(diff) + (diff > 0 ? ' more' : ' fewer') + ' than usual');
        }
        text('people-sub', sub);
        draw();
    }

    function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
    var usualAt = {};
    function parseBucket(b) { return new Date(b.replace(' ', 'T')).getTime(); }
    function hhmm(t) { var d = new Date(t); return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }

    function draw() {
        var canvas = document.getElementById('chart');
        var dpr = window.devicePixelRatio || 1;
        var w = canvas.clientWidth, h = canvas.clientHeight;
        canvas.width = w * dpr; canvas.height = h * dpr;
        var ctx = canvas.getContext('2d');
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, w, h);
        points = [];
        var font = '11px ' + cssVar('--font-mono');
        ctx.font = font;
        if (!data || !data.series.length) {
            ctx.fillStyle = cssVar('--text-muted');
            ctx.fillText('No counts yet. The first one is ready a few minutes after start.', 12, 24);
            return;
        }
        var end = Date.now(), start = end - (range === '7d' ? 7 : 1) * 86400000;
        var series = data.series.map(function(r) { return {t: parseBucket(r.bucket), people: r.people, devices: r.devices}; })
            .filter(function(p) { return p.t >= start; });
        usualAt = {};
        var usual = (data.usual_series || []).map(function(r) { return {t: parseBucket(r.t), v: r.v}; })
            .filter(function(p) { return p.t >= start; });
        usual.forEach(function(p) { usualAt[p.t] = p.v; });
        if (range !== '24h') usual = [];  // the week view shows usual in the tooltip only
        var maxV = 4;
        series.forEach(function(p) { maxV = Math.max(maxV, p.people, p.devices); });
        usual.forEach(function(p) { maxV = Math.max(maxV, p.v); });
        maxV = Math.ceil(maxV * 1.15);
        var L = 34, R = 10, T = 8, B = 22, pw = w - L - R, ph = h - T - B;
        var x = function(t) { return L + (t - start) / (end - start) * pw; };
        var y = function(v) { return T + ph - v / maxV * ph; };

        ctx.strokeStyle = cssVar('--border-color'); ctx.fillStyle = cssVar('--text-muted'); ctx.lineWidth = 1;
        var ticks = 4;
        for (var i = 0; i <= ticks; i++) {
            var v = Math.round(maxV * i / ticks), yy = Math.round(y(v)) + 0.5;
            ctx.beginPath(); ctx.moveTo(L, yy); ctx.lineTo(w - R, yy); ctx.stroke();
            ctx.fillText(String(v), 4, yy + 4);
        }
        var hourMs = 3600000, labelEvery = range === '7d' ? 24 * hourMs : 3 * hourMs;
        var first = new Date(start); first.setMinutes(0, 0, 0);
        for (var tt = first.getTime() + hourMs; tt < end; tt += hourMs) {
            var d = new Date(tt);
            if (range === '7d' ? d.getHours() !== 0 : d.getHours() % 3 !== 0) continue;
            var label = range === '7d' ? d.toLocaleDateString(undefined, {weekday: 'short', day: 'numeric'}) : hhmm(tt);
            ctx.fillText(label, x(tt) - ctx.measureText(label).width / 2, h - 6);
        }

        function line(pts, color, width, dash, alpha, fill) {
            if (!pts.length) return;
            ctx.save();
            ctx.globalAlpha = alpha; ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash);
            ctx.beginPath();
            var gap = Math.max(range === '7d' ? 30 : 15, 3 * data.bucket_minutes) * 60000, prev = null;
            pts.forEach(function(p) {
                if (prev && p[0] - prev > gap) ctx.moveTo(x(p[0]), y(p[1])); else if (!prev) ctx.moveTo(x(p[0]), y(p[1])); else ctx.lineTo(x(p[0]), y(p[1]));
                prev = p[0];
            });
            ctx.stroke();
            if (fill) {
                ctx.lineTo(x(pts[pts.length - 1][0]), y(0)); ctx.lineTo(x(pts[0][0]), y(0)); ctx.closePath();
                var g = ctx.createLinearGradient(0, T, 0, T + ph);
                g.addColorStop(0, color); g.addColorStop(1, 'transparent');
                ctx.globalAlpha = 0.18; ctx.fillStyle = g; ctx.fill();
            }
            ctx.restore();
        }
        line(series.map(function(p) { return [p.t, p.devices]; }), cssVar('--accent-red'), 1.2, [], 0.55, false);
        line(usual.map(function(p) { return [p.t, p.v]; }), cssVar('--text-muted'), 1.2, [4, 4], 1, false);
        line(series.map(function(p) { return [p.t, p.people]; }), cssVar('--accent-cyan'), 2, [], 1, true);
        points = series.map(function(p) { return {x: x(p.t), p: p}; });
    }

    var canvas = document.getElementById('chart'), tip = document.getElementById('tip');
    canvas.addEventListener('mousemove', function(e) {
        if (!points.length) return;
        var rect = canvas.getBoundingClientRect(), mx = e.clientX - rect.left, best = null;
        points.forEach(function(pt) { if (!best || Math.abs(pt.x - mx) < Math.abs(best.x - mx)) best = pt; });
        if (!best || Math.abs(best.x - mx) > 20) { tip.style.display = 'none'; return; }
        var d = new Date(best.p.t);
        var when = (range === '7d' ? d.toLocaleDateString(undefined, {weekday: 'short'}) + ' ' : '') + hhmm(best.p.t);
        var u = usualAt[best.p.t];
        tip.textContent = when + '  people ' + best.p.people + '  devices ' + best.p.devices + (u !== undefined ? '  usual ' + u : '');
        tip.style.display = 'block';
        tip.style.left = (e.clientX + 12) + 'px'; tip.style.top = (e.clientY + 12) + 'px';
    });
    canvas.addEventListener('mouseleave', function() { tip.style.display = 'none'; });
    window.addEventListener('resize', draw);

    load();
    setInterval(load, 60000);
</script>
</body>
</html>
"""
