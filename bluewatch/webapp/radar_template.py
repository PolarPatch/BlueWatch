"""The /radar page: a live signal radar of what is around right now.

Inspired by the radar view of Fieldwatch (https://github.com/OffGridPete/Fieldwatch,
MIT): distance from the centre comes from signal strength (RSSI); the angle of a
dot carries NO meaning (a single receiver cannot tell direction), it is only a
fixed, repeatable position per device so dots don't jump around.
"""

RADAR_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BlueWatch - Radar</title>
<style>
    :root {
        --bg-primary: #0d1117; --bg-panel: #161b22; --bg-tertiary: #1c232c; --bg-hover: #242c37;
        --text-primary: #e6edf3; --text-secondary: #a6afb9; --text-muted: #7d8590;
        --border-color: #30363d; --accent-blue: #2563eb; --accent-green: #3fb950;
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

    .radar-page { padding: 1rem; max-width: 1400px; margin: 0 auto; }
    .radar-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem 1.5rem; margin-bottom: 0.75rem; }
    .counts { display: flex; gap: 1.25rem; font-size: 0.85rem; color: var(--text-secondary); }
    .counts b { color: var(--text-primary); font-size: 1.15rem; margin-right: 0.3rem; font-variant-numeric: tabular-nums; }
    .controls { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem 1rem; }
    .controls label { display: flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: var(--text-secondary); cursor: pointer; }
    .controls select, .btn { background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: 6px; padding: 0.3rem 0.6rem; font-family: var(--font-mono); font-size: 0.72rem; cursor: pointer; }
    .btn:hover { background: var(--bg-hover); }
    .btn.on { color: #f59e0b; }

    .radar-wrap { position: relative; background: var(--bg-panel); border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden; }
    #radar { display: block; width: 100%; touch-action: none; cursor: crosshair; }
    .info { position: absolute; top: 0.75rem; right: 0.75rem; width: 15rem; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.7rem 0.8rem; font-size: 0.72rem; }
    .info .title { font-size: 0.85rem; font-weight: 700; margin-bottom: 0.35rem; padding-right: 1.2rem; word-break: break-word; }
    .info .row { display: flex; justify-content: space-between; gap: 0.5rem; color: var(--text-secondary); margin-top: 0.15rem; }
    .info .row b { color: var(--text-primary); font-weight: 500; text-align: right; word-break: break-all; }
    .info a { display: inline-block; margin-top: 0.5rem; color: var(--text-primary); }
    .info .close { position: absolute; top: 0.3rem; right: 0.4rem; background: none; border: none; color: var(--text-muted); font-size: 1rem; cursor: pointer; }
    .radar-foot { margin-top: 0.6rem; font-size: 0.72rem; color: var(--text-muted); }
    .legend { display: flex; flex-wrap: wrap; gap: 0.3rem 1rem; margin-top: 0.5rem; font-size: 0.7rem; color: var(--text-secondary); }
    .legend span { cursor: pointer; user-select: none; }
    .legend span.off { opacity: 0.35; }
    .legend i { display: inline-block; width: 0.6rem; height: 0.6rem; border-radius: 50%; margin-right: 0.35rem; vertical-align: baseline; }
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
            <a href="/radar" class="nav-link active">Radar</a>
            <a href="/settings" class="nav-link">Config</a>
        </nav>
    </div>
    <button class="theme-toggle" id="theme-toggle" title="Toggle light/dark mode">&#9728;</button>
</header>

<main class="radar-page">
    <div class="radar-head">
        <div class="counts">
            <span><b id="c-on">0</b>on air</span>
            <span><b id="c-ble">0</b>Bluetooth</span>
            <span><b id="c-lan">0</b>on the network</span>
        </div>
        <div class="controls">
            <select id="window" title="How far back devices count as present">
                <option value="60">last 1 min</option>
                <option value="300" selected>last 5 min</option>
                <option value="900">last 15 min</option>
                <option value="3600">last 1 h</option>
            </select>
            <label><input type="checkbox" id="hide-unknown"> Hide unknowns</label>
            <label><input type="checkbox" id="hide-random"> Hide random addresses</label>
            <button class="btn" id="btn-pause">Pause</button>
            <button class="btn" id="btn-zoom-out" title="Zoom out">&minus;</button>
            <button class="btn" id="btn-zoom-in" title="Zoom in">+</button>
            <button class="btn" id="btn-reset" title="Reset zoom">Reset</button>
        </div>
    </div>

    <div class="radar-wrap">
        <canvas id="radar"></canvas>
        <div class="info" id="info" hidden></div>
    </div>
    <div class="radar-foot" id="foot">Loading&hellip;</div>
    <div class="legend" id="legend"></div>
    <div class="radar-foot" style="margin-top: 0.9rem;">Distance from the centre is signal strength (rings: -40, -60, -80 and -100 dBm). The direction of a dot means nothing: one receiver cannot tell where a device is, so each dot just keeps a fixed angle.</div>
</main>

<script>
(function () {
    const canvas = document.getElementById('radar');
    const ctx = canvas.getContext('2d');
    const info = document.getElementById('info');

    // ----- theme -----
    function applyTheme(t) {
        document.documentElement.setAttribute('data-theme', t);
        document.getElementById('theme-toggle').textContent = t === 'light' ? '☽' : '☀';
        readTheme();
    }
    let theme = {};
    function readTheme() {
        const cs = getComputedStyle(document.documentElement);
        const v = n => cs.getPropertyValue(n).trim();
        theme = { panel: v('--bg-panel'), ring: v('--border-color'), text: v('--text-secondary'), textStrong: v('--text-primary'), muted: v('--text-muted') };
    }
    document.getElementById('theme-toggle').onclick = () => {
        const next = (document.documentElement.getAttribute('data-theme') === 'light') ? 'dark' : 'light';
        try { localStorage.setItem('bluewatch_theme', next); } catch (e) {}
        applyTheme(next);
    };
    let savedTheme = 'dark';
    try { savedTheme = localStorage.getItem('bluewatch_theme') || 'dark'; } catch (e) {}
    applyTheme(savedTheme);

    // ----- colors by type -----
    const TYPE_COLORS = {
        phone: '#5b6cf0', tablet: '#5b6cf0', tracker: '#b083c9', beacon: '#b083c9',
        smart: '#3fb9a5', vehicle: '#e0707a', tv: '#d9a441', speaker: '#4fb3e8', audio: '#4fb3e8',
        laptop: '#7c8cf8', computer: '#7c8cf8', watch: '#f472b6', wearable: '#f472b6', glasses: '#f472b6',
        network: '#9ca3af', printer: '#9ca3af', mesh: '#2dd4bf', gaming: '#f59e0b', lock: '#84cc16',
        flipper: '#f85149', drone: '#f85149', camera: '#f85149', skimmer: '#f85149', unknown: '#6e7681',
    };
    const colorFor = t => TYPE_COLORS[t] || '#6e7681';

    // ----- state -----
    let devices = [];
    let zoom = 1, paused = false, windowSec = 300;
    let selected = null;
    const hiddenTypes = new Set();
    let W = 0, H = 0, cx = 0, cy = 0, maxR = 0, dpr = 1;
    let drawn = [];
    const history = {};   // mac -> last RSSI readings (for the echo tail)

    // Fixed pseudo-angle per device (carries no meaning, see the note on the page).
    function angleOf(mac) {
        let h = 2166136261;
        for (let i = 0; i < mac.length; i++) { h ^= mac.charCodeAt(i); h = Math.imul(h, 16777619); }
        return ((h >>> 0) / 4294967296) * Math.PI * 2;
    }
    // Stronger signal = closer to the centre (same idea as Fieldwatch's RadarPlot).
    function radiusOf(rssi) {
        const t = Math.min(1, Math.max(0, (-30 - rssi) / 70));
        return maxR * (0.12 + t * 0.88) * zoom;
    }

    function visible() {
        return devices.filter(d => {
            if (d.rssi == null || d.lan) return false;
            if (hiddenTypes.has(d.type)) return false;
            if (document.getElementById('hide-unknown').checked && d.type === 'unknown' && !d.name && !d.vendor && !d.watched && !d.grouped) return false;
            if (document.getElementById('hide-random').checked && d.random) return false;
            return true;
        });
    }

    function resize() {
        const wrap = canvas.parentElement;
        dpr = window.devicePixelRatio || 1;
        W = wrap.clientWidth;
        H = Math.max(480, Math.min(window.innerHeight - 250, 820));
        canvas.width = Math.round(W * dpr);
        canvas.height = Math.round(H * dpr);
        canvas.style.height = H + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        cx = W / 2; cy = H / 2;
        maxR = Math.min(W, H) / 2 - 18;
    }
    window.addEventListener('resize', resize);

    // ----- drawing -----
    let sweep = 0, lastT = performance.now();

    function drawFrame(now) {
        const dt = Math.min(0.1, (now - lastT) / 1000);
        lastT = now;
        if (!paused) sweep = (sweep + dt * 0.7) % (Math.PI * 2);

        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = theme.panel;
        ctx.fillRect(0, 0, W, H);

        // rings + labels
        ctx.lineWidth = 1;
        ctx.font = '10px ui-monospace, Menlo, monospace';
        [-40, -60, -80, -100].forEach(dbm => {
            const r = radiusOf(dbm);
            if (r > maxR + 0.5) return;
            ctx.strokeStyle = theme.ring;
            ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
            ctx.fillStyle = theme.muted;
            ctx.textAlign = 'left';
            ctx.fillText(String(dbm), cx + 4, cy - r + 11);
        });
        ctx.strokeStyle = theme.ring;
        ctx.beginPath(); ctx.moveTo(cx - maxR, cy); ctx.lineTo(cx + maxR, cy); ctx.moveTo(cx, cy - maxR); ctx.lineTo(cx, cy + maxR); ctx.stroke();

        // sweep, modelled on Fieldwatch's: a ~37 degree wedge of about 16 fine radial
        // stripes with dark gaps, brightest at the leading edge and fading out behind it.
        // The leading edge is a solid bright line with a soft halo.
        const WEDGE = 0.64, STRIPES = 16, PITCH = WEDGE / STRIPES;
        for (let i = 0; i < STRIPES; i++) {
            const t = i / (STRIPES - 1);
            const a1 = sweep - i * PITCH, a0 = a1 - PITCH * 0.64;    // the gap between stripes stays dark
            const al = 0.06 + 0.72 * Math.pow(1 - t, 1.2);
            const rC = Math.round(96 - 60 * t), gC = Math.round(232 - 92 * t), bC = Math.round(128 - 58 * t);
            ctx.fillStyle = 'rgba(' + rC + ',' + gC + ',' + bC + ',' + al.toFixed(3) + ')';
            ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, maxR, a0, a1); ctx.closePath(); ctx.fill();
        }
        const ex = cx + Math.cos(sweep) * maxR, ey = cy + Math.sin(sweep) * maxR;
        ctx.strokeStyle = 'rgba(110,235,140,0.22)';
        ctx.lineWidth = 6;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke();
        ctx.strokeStyle = 'rgba(150,255,170,0.95)';
        ctx.lineWidth = 1.8;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke();

        // dots: bright when the beam has just painted them, glowing out until the
        // next pass (phosphor afterglow), an echo ring spreads out from each new hit,
        // and a short tail shows how the signal strength has moved
        const list = visible();
        drawn = [];
        list.forEach(d => {
            const r = radiusOf(d.rssi);
            if (r > maxR + 0.5) return;               // too weak for this zoom: leaves the disc
            const a = angleOf(d.mac);
            const ux = Math.cos(a), uy = Math.sin(a);
            const x = cx + ux * r, y = cy + uy * r;
            const onAir = d.age <= 90;
            const behind = (sweep - a + Math.PI * 2) % (Math.PI * 2);   // radians since the beam passed
            const glow = Math.exp(-behind / 2.4);
            let alpha = onAir ? 0.32 + 0.68 * glow : Math.max(0.16, (0.5 - (d.age - 90) / windowSec * 0.35)) * (0.6 + 0.4 * glow);
            const rad = 3.6 + (onAir ? 2 * Math.max(0, 1 - behind / 0.5) : 0);

            // tail (older readings along the same radius)
            const hist = history[d.mac];
            if (onAir && hist && hist.length > 1) {
                for (let k = 0; k < hist.length - 1; k++) {
                    const rr = radiusOf(hist[k]);
                    if (Math.abs(rr - r) < 1.5 || rr > maxR + 0.5) continue;
                    ctx.globalAlpha = 0.10 + 0.28 * (k / hist.length);
                    ctx.fillStyle = colorFor(d.type);
                    ctx.beginPath(); ctx.arc(cx + ux * rr, cy + uy * rr, 1.9, 0, Math.PI * 2); ctx.fill();
                }
            }
            // echo ring right after the beam hits
            if (onAir && behind < 1.0) {
                ctx.globalAlpha = 0.55 * (1 - behind);
                ctx.strokeStyle = colorFor(d.type);
                ctx.lineWidth = 1.2;
                ctx.beginPath(); ctx.arc(x, y, rad + 2 + 16 * behind, 0, Math.PI * 2); ctx.stroke();
            }

            ctx.globalAlpha = alpha;
            ctx.fillStyle = colorFor(d.type);
            ctx.beginPath(); ctx.arc(x, y, rad, 0, Math.PI * 2); ctx.fill();
            if (d.watched || d.alert) {
                ctx.strokeStyle = d.alert ? '#f85149' : '#f5c518';
                ctx.lineWidth = 1.6;
                ctx.beginPath(); ctx.arc(x, y, rad + 3, 0, Math.PI * 2); ctx.stroke();
            }
            ctx.globalAlpha = 1;
            drawn.push({ x, y, d, rad, onAir });
        });

        // selected marker
        if (selected) {
            const s = drawn.find(p => p.d.mac === selected);
            if (s) { ctx.strokeStyle = theme.textStrong; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(s.x, s.y, s.rad + 6, 0, Math.PI * 2); ctx.stroke(); }
        }

        // labels: name on the first line, RSSI smaller underneath; important and
        // strong first, skip whatever would overlap
        const placed = [];
        const maxLabels = Math.round(22 * zoom * zoom);
        const order = drawn.slice().sort((p, q) =>
            ((q.d.alert ? 2 : 0) + (q.d.watched ? 1 : 0)) - ((p.d.alert ? 2 : 0) + (p.d.watched ? 1 : 0)) || q.d.rssi - p.d.rssi);
        let count = 0;
        for (const p of order) {
            if (count >= maxLabels) break;
            if (!p.onAir && !p.d.alert && !p.d.watched && zoom < 1.5) continue;
            const text = p.d.name || p.d.vendor || p.d.type_label;
            const sub = p.d.rssi + ' dBm';
            ctx.font = '10px ui-monospace, Menlo, monospace';
            const w1 = ctx.measureText(text).width;
            ctx.font = '8px ui-monospace, Menlo, monospace';
            const w2 = ctx.measureText(sub).width;
            const w = Math.max(w1, w2), h = 20;
            const box = { x: p.x + 8, y: p.y - 7, w, h };
            if (placed.some(b => box.x < b.x + b.w + 3 && box.x + box.w + 3 > b.x && box.y < b.y + b.h + 1 && box.y + box.h + 1 > b.y)) continue;
            if (box.x + box.w > W - 4 || box.y < 2 || box.y + box.h > H - 2) continue;
            placed.push(box);
            ctx.globalAlpha = p.onAir ? 1 : 0.55;
            ctx.textAlign = 'left';
            ctx.font = '10px ui-monospace, Menlo, monospace';
            ctx.fillStyle = (p.d.alert || p.d.watched) ? theme.textStrong : theme.text;
            ctx.fillText(text, box.x, box.y + 9);
            ctx.font = '8px ui-monospace, Menlo, monospace';
            ctx.fillStyle = theme.muted;
            ctx.fillText(sub, box.x, box.y + 18);
            ctx.globalAlpha = 1;
            count++;
        }

        // YOU
        ctx.strokeStyle = '#3fb950';
        ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(cx - 8, cy); ctx.lineTo(cx + 8, cy); ctx.moveTo(cx, cy - 8); ctx.lineTo(cx, cy + 8); ctx.stroke();
        ctx.fillStyle = '#3fb950';
        ctx.beginPath(); ctx.arc(cx, cy, 3, 0, Math.PI * 2); ctx.fill();
        ctx.font = 'bold 10px ui-monospace, Menlo, monospace';
        ctx.textAlign = 'left';
        ctx.fillText('YOU', cx + 8, cy + 14);

        requestAnimationFrame(drawFrame);
    }

    // ----- data -----
    const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    function ago(sec) {
        if (sec < 5) return 'now';
        if (sec < 60) return sec + ' s ago';
        if (sec < 3600) return Math.round(sec / 60) + ' min ago';
        return Math.round(sec / 3600) + ' h ago';
    }

    function updateSummary() {
        const list = visible();
        const on = list.filter(d => d.age <= 90).length;
        document.getElementById('c-on').textContent = on;
        document.getElementById('c-ble').textContent = devices.filter(d => !d.lan && d.rssi != null).length;
        document.getElementById('c-lan').textContent = devices.filter(d => d.lan).length;
        document.getElementById('foot').textContent = on + ' on air · ' + list.length + ' in filter · dim = gone · click a dot · scroll or pinch to zoom' + (zoom > 1 ? ' · zoom ×' + zoom.toFixed(1) : '');

        const counts = {};
        devices.filter(d => !d.lan && d.rssi != null).forEach(d => { counts[d.type] = (counts[d.type] || 0) + 1; });
        const labels = {};
        devices.forEach(d => { labels[d.type] = d.type_label; });
        document.getElementById('legend').innerHTML = Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([t, n]) =>
            '<span data-type="' + esc(t) + '" class="' + (hiddenTypes.has(t) ? 'off' : '') + '"><i style="background:' + colorFor(t) + '"></i>' + esc(labels[t] || t) + ' ' + n + '</span>').join('');
        document.querySelectorAll('#legend span').forEach(el => {
            el.onclick = () => { const t = el.dataset.type; if (hiddenTypes.has(t)) hiddenTypes.delete(t); else hiddenTypes.add(t); updateSummary(); };
        });
    }

    async function load() {
        if (paused) return;
        try {
            const res = await fetch('/api/radar?window=' + windowSec);
            if (!res.ok) return;
            const data = await res.json();
            devices = data.devices || [];
            const seen = new Set();
            devices.forEach(d => {
                if (d.rssi == null) return;
                seen.add(d.mac);
                const h = history[d.mac] = history[d.mac] || [];
                h.push(d.rssi);
                if (h.length > 7) h.shift();
            });
            Object.keys(history).forEach(mac => { if (!seen.has(mac)) delete history[mac]; });
            updateSummary();
            if (selected) showInfo(selected);
        } catch (e) { console.error('Radar error:', e); }
    }

    // ----- info card -----
    function showInfo(mac) {
        const d = devices.find(x => x.mac === mac);
        if (!d) { info.hidden = true; selected = null; return; }
        selected = mac;
        info.hidden = false;
        info.innerHTML = '<button class="close" id="info-close" aria-label="Close">×</button>' +
            '<div class="title">' + esc(d.name || d.vendor || d.type_label) + '</div>' +
            '<div class="row"><span>Type</span><b>' + esc(d.type_label) + (d.alert ? ' (alert)' : '') + '</b></div>' +
            (d.vendor ? '<div class="row"><span>Vendor</span><b>' + esc(d.vendor) + '</b></div>' : '') +
            '<div class="row"><span>Address</span><b>' + esc(d.mac) + '</b></div>' +
            '<div class="row"><span>Signal</span><b>' + (d.rssi != null ? d.rssi + ' dBm' : '—') + '</b></div>' +
            '<div class="row"><span>Last seen</span><b>' + ago(d.age) + '</b></div>' +
            '<div class="row"><span>Sightings</span><b>' + d.sightings + '</b></div>' +
            '<a href="/all#device=' + encodeURIComponent(d.mac) + '">Open details</a>';
        document.getElementById('info-close').onclick = () => { info.hidden = true; selected = null; };
    }

    // ----- interaction -----
    canvas.addEventListener('click', ev => {
        const rect = canvas.getBoundingClientRect();
        const x = ev.clientX - rect.left, y = ev.clientY - rect.top;
        let best = null, bd = 12;
        drawn.forEach(p => { const d = Math.hypot(p.x - x, p.y - y); if (d < bd) { bd = d; best = p; } });
        if (best) showInfo(best.d.mac); else { info.hidden = true; selected = null; }
    });
    const setZoom = z => { zoom = Math.min(4, Math.max(1, z)); updateSummary(); };
    canvas.addEventListener('wheel', ev => { ev.preventDefault(); setZoom(zoom * (ev.deltaY < 0 ? 1.12 : 1 / 1.12)); }, { passive: false });
    canvas.addEventListener('dblclick', () => setZoom(1));
    const pointers = new Map();
    let pinchStart = null;
    canvas.addEventListener('pointerdown', ev => { pointers.set(ev.pointerId, ev); if (pointers.size === 2) { const [a, b] = [...pointers.values()]; pinchStart = { d: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY), z: zoom }; } });
    canvas.addEventListener('pointermove', ev => {
        if (!pointers.has(ev.pointerId)) return;
        pointers.set(ev.pointerId, ev);
        if (pointers.size === 2 && pinchStart) { const [a, b] = [...pointers.values()]; setZoom(pinchStart.z * Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY) / pinchStart.d); }
    });
    const endPointer = ev => { pointers.delete(ev.pointerId); if (pointers.size < 2) pinchStart = null; };
    canvas.addEventListener('pointerup', endPointer);
    canvas.addEventListener('pointercancel', endPointer);

    document.getElementById('btn-zoom-in').onclick = () => setZoom(zoom * 1.25);
    document.getElementById('btn-zoom-out').onclick = () => setZoom(zoom / 1.25);
    document.getElementById('btn-reset').onclick = () => setZoom(1);
    const pauseBtn = document.getElementById('btn-pause');
    pauseBtn.onclick = () => { paused = !paused; pauseBtn.textContent = paused ? 'Resume' : 'Pause'; pauseBtn.classList.toggle('on', paused); if (!paused) load(); };
    document.getElementById('window').onchange = ev => { windowSec = parseInt(ev.target.value, 10); load(); };
    document.getElementById('hide-unknown').onchange = updateSummary;
    document.getElementById('hide-random').onchange = updateSummary;

    resize();
    load();
    setInterval(load, 3000);
    requestAnimationFrame(drawFrame);
})();
</script>
</body>
</html>
"""
