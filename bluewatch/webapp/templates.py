"""HTML templates for the BlueWatch web dashboard."""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BlueWatch</title>
    <style>
        :root {
            --bg-primary: #0d0d0d;
            --bg-secondary: #141414;
            --bg-tertiary: #1a1a1a;
            --bg-hover: #242424;
            --bg-panel: #111111;
            --text-primary: #e0e0e0;
            --text-secondary: #888888;
            --text-muted: #555555;
            --accent-red: #2563eb;
            --accent-orange: #ea580c;
            --accent-amber: #d97706;
            --accent-green: #16a34a;
            --accent-blue: #2563eb;
            --accent-cyan: #0891b2;
            --border-color: #2a2a2a;
            --border-active: #404040;
            --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', Consolas, monospace;
        }

        [data-theme="light"] {
            --bg-primary: #f5f5f5;
            --bg-secondary: #e8e8e8;
            --bg-tertiary: #ffffff;
            --bg-hover: #d8d8d8;
            --bg-panel: #efefef;
            --text-primary: #1a1a1a;
            --text-secondary: #555555;
            --text-muted: #888888;
            --border-color: #cccccc;
            --border-active: #999999;
        }

        [data-theme="light"] .type-phone { background: #dbeafe; color: #1d4ed8; }
        [data-theme="light"] .type-laptop { background: #ccfbf1; color: #0f766e; }
        [data-theme="light"] .type-audio { background: #f3e8ff; color: #7c3aed; }
        [data-theme="light"] .type-watch { background: #dcfce7; color: #15803d; }
        [data-theme="light"] .type-smart { background: #fef3c7; color: #b45309; }
        [data-theme="light"] .type-tv { background: #fce7f3; color: #be185d; }
        [data-theme="light"] .type-vehicle { background: #fef9c3; color: #a16207; }
        [data-theme="light"] .type-unknown { background: #e5e5e5; color: #555; }
        [data-theme="light"] .modal-overlay.active { background: rgba(0, 0, 0, 0.5); }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        /* Thin, subtle scrollbars */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--border-active); }
        * { scrollbar-width: thin; scrollbar-color: var(--border-color) transparent; }

        body {
            font-family: var(--font-mono);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            font-size: 13px;
            line-height: 1.5;
        }

        /* Top Bar */
        .topbar {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .topbar-left {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            color: inherit;
        }

        .brand-icon {
            color: var(--accent-blue);
            width: 1.1rem;
            height: 1.1rem;
        }

        .brand-text {
            font-weight: 700;
            font-size: 0.9rem;
            letter-spacing: 0.05em;
            
            color: var(--accent-blue);
        }

        .brand-text span {
            color: #ffffff;
        }

        .nav {
            display: flex;
            gap: 0.25rem;
        }

        .nav-link {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.75rem;
            padding: 0.4rem 0.75rem;
            border-radius: 3px;
            
            letter-spacing: 0.05em;
            transition: all 0.1s;
        }

        .nav-link:hover, .nav-link.active {
            color: var(--text-primary);
            background: var(--bg-tertiary);
        }

        .topbar-right {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .total-units {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .total-units-icon {
            color: var(--accent-blue);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.7rem;
            
            letter-spacing: 0.1em;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 6px var(--accent-green);
            animation: pulse 2s infinite;
        }

        .status-dot.scanning { background: var(--accent-amber); box-shadow: 0 0 6px var(--accent-amber); }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .timestamp {
            font-size: 0.7rem;
            color: var(--text-muted);
        }

        /* Main Layout */
        .main {
            display: grid;
            grid-template-columns: 320px 1fr;
            min-height: calc(100vh - 45px);
        }

        /* Sidebar */
        .sidebar {
            background: var(--bg-panel);
            border-right: 1px solid var(--border-color);
            padding: 1rem;
            overflow-y: auto;
            position: sticky;
            top: 45px;
            height: calc(100vh - 45px);
            align-self: start;
        }

        .panel {
            margin-bottom: 1.5rem;
        }

        .panel-header {
            font-size: 0.65rem;
            
            letter-spacing: 0.15em;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        .stat-grid {
            display: grid;
            gap: 0.5rem;
        }

        .stat-item {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .stat-label {
            font-size: 0.6rem;
            color: var(--text-secondary);

            letter-spacing: 0.05em;
        }

        .stat-value {
            font-size: 0.95rem;
            font-weight: 700;
        }

        .stat-value.red { color: var(--accent-red); }
        .stat-value.amber { color: var(--accent-amber); }
        .stat-value.green { color: var(--accent-green); }
        .stat-value.blue { color: var(--accent-blue); }

        /* Filters */
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .category-node {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.35rem 0.5rem;
            border-radius: 3px;
            cursor: grab;
            font-size: 0.78rem;
        }
        .category-node:hover { background: var(--bg-tertiary); }
        .category-node.active { background: var(--bg-tertiary); box-shadow: inset 2px 0 0 var(--accent-blue); }
        .category-node.category-drop-target { outline: 2px dashed var(--accent-blue); outline-offset: -2px; }
        .category-children { margin-left: 1.1rem; border-left: 1px solid var(--border-color); }
        .category-label { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .category-delete {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.9rem;
            line-height: 1;
            padding: 0 0.25rem;
        }
        .category-delete:hover { color: var(--accent-red); }

        .filter-btn {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 0.75rem;
            padding: 0.5rem 0.75rem;
            text-align: left;
            cursor: pointer;
            border-radius: 3px;
            transition: all 0.1s;
            display: flex;
            justify-content: space-between;
        }

        .filter-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }

        .filter-btn.active {
            background: var(--bg-tertiary);
            border-color: var(--accent-red);
            color: var(--text-primary);
        }

        .filter-count {
            color: var(--text-muted);
            font-size: 0.7rem;
        }

        /* Content Area */
        .content {
            padding: 1rem;
            overflow-y: auto;
        }

        /* Search Bar */
        .search-bar {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .search-input {
            flex: 1;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 0.6rem 0.75rem;
            color: var(--text-primary);
            font-family: var(--font-mono);
            font-size: 0.8rem;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--accent-red);
        }

        .search-input::placeholder { color: var(--text-muted); }

        .form-input {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 0.6rem 0.75rem;
            color: var(--text-primary);
            font-family: var(--font-mono);
            font-size: 0.8rem;
            width: 100%;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-red);
        }

        .kbd {
            display: inline-block;
            padding: 0.15rem 0.4rem;
            font-size: 0.65rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 2px;
            color: var(--text-muted);
        }

        .btn {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 0.7rem;
            padding: 0.6rem 1rem;
            cursor: pointer;
            border-radius: 3px;
            
            letter-spacing: 0.05em;
            transition: all 0.1s;
        }

        .btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
            border-color: var(--border-active);
        }

        .btn-primary {
            background: var(--accent-red);
            border-color: var(--accent-red);
            color: white;
        }

        .btn-primary:hover {
            background: #1d4ed8;
        }

        /* Device Table */
        .table-container {
            background: var(--bg-panel);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            overflow: hidden;
        }

        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border-color);
        }

        .table-title {
            font-size: 0.7rem;
            
            letter-spacing: 0.1em;
            color: var(--text-secondary);
        }

        .table-actions {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            align-items: center;
        }

        .selected-summary {
            color: var(--accent-amber);
        }

        .device-table {
            width: 100%;
            border-collapse: collapse;
        }

        .device-table th {
            text-align: left;
            padding: 0.6rem 0.75rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 0.65rem;
            font-weight: 600;

            letter-spacing: 0.1em;
            color: var(--text-muted);
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
        }

        .device-table th.select-col,
        .device-table td.select-col {
            width: 34px;
            padding: 0.4rem 0.5rem;
            text-align: center;
        }

        .row-select-checkbox {
            accent-color: var(--accent-red);
            cursor: pointer;
        }

        .device-table th.sortable {
            cursor: pointer;
            user-select: none;
            transition: color 0.1s ease, background 0.1s ease;
        }

        .device-table th.sortable:hover {
            color: var(--text-primary);
            background: var(--bg-tertiary);
        }

        .device-table th.sortable.active {
            color: var(--text-primary);
            background: var(--bg-tertiary);
        }

        .sort-indicator {
            margin-left: 0.35rem;
            font-size: 0.6rem;
            opacity: 0.7;
        }

        .device-table td {
            padding: 0.6rem 0.75rem;
            font-size: 0.8rem;
            border-bottom: 1px solid var(--border-color);
            vertical-align: middle;
        }

        .device-table tr:hover {
            background: var(--bg-hover);
        }

        .device-table tr.selected {
            background: rgba(220, 38, 38, 0.15);
        }

        .device-table tr.selected:hover {
            background: rgba(220, 38, 38, 0.22);
        }

        .device-table tr:last-child td { border-bottom: none; }

        .device-table tr { cursor: pointer; user-select: none; }

        .bulk-select {
            min-width: 140px;
            font-size: 0.7rem;
            padding: 0.4rem 0.5rem;
        }

        .pagination-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.75rem;
            padding: 0.65rem 0.9rem;
            border-top: 1px solid var(--border-color);
            background: var(--bg-tertiary);
            flex-wrap: wrap;
        }

        .pagination-left,
        .pagination-right {
            display: flex;
            align-items: center;
            gap: 0.45rem;
        }

        .pagination-center {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            flex-wrap: wrap;
            justify-content: center;
        }

        .page-numbers {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            flex-wrap: wrap;
        }

        .page-number-btn {
            min-width: 2rem;
            padding: 0.35rem 0.45rem;
            font-size: 0.7rem;
            line-height: 1;
        }

        .page-number-btn.active {
            background: var(--accent-red);
            border-color: var(--accent-red);
            color: #fff;
        }

        .page-ellipsis {
            color: var(--text-muted);
            font-size: 0.75rem;
            padding: 0 0.1rem;
        }

        /* Device Type Badge */
        .identity-badge {
            display: inline-block;
            padding: 0.05rem 0.4rem;
            border-radius: 8px;
            font-size: 0.65rem;
            background: var(--accent-blue);
            color: white;
        }

        .type-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.2rem 0.5rem;
            border-radius: 2px;
            font-size: 0.7rem;
            font-weight: 500;

            letter-spacing: 0.05em;
        }

        .type-phone { background: #1e3a5f; color: #60a5fa; }
        .type-laptop { background: #1a3a3a; color: #5eead4; }
        .type-audio { background: #3a1e3a; color: #c084fc; }
        .type-watch { background: #1e3a2e; color: #4ade80; }
        .type-smart { background: #3a2e1e; color: #fbbf24; }
        .type-tv { background: #3a1e2e; color: #f472b6; }
        .type-vehicle { background: #3a3a1e; color: #facc15; }
        .type-unknown { background: #2a2a2a; color: #888; }

        .mac-addr {
            font-size: 0.75rem;
            color: var(--text-secondary);
            letter-spacing: 0.02em;
        }

        .vendor-name {
            color: var(--text-muted);
            font-size: 0.75rem;
        }

        .device-name {
            color: var(--text-primary);
        }

        .sighting-count {
            font-size: 0.8rem;
            color: var(--accent-amber);
        }

        .last-seen {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .last-seen.recent {
            color: var(--accent-green);
        }

        .watched-star {
            color: var(--accent-amber);
            margin-right: 0.25rem;
        }

        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.15s;
        }

        .modal-overlay.active {
            opacity: 1;
            pointer-events: all;
        }

        .modal {
            background: var(--bg-panel);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            width: 90%;
            max-width: 700px;
            max-height: 85vh;
            overflow-y: auto;
        }

        .modal-header {
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-tertiary);
        }

        .modal-title {
            font-size: 0.8rem;
            
            letter-spacing: 0.1em;
        }

        .modal-close {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 1.25rem;
            line-height: 1;
        }

        .modal-close:hover { color: var(--text-primary); }

        .modal-body {
            padding: 1rem;
        }

        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.15rem 1rem;
            margin-bottom: 1rem;
        }

        .detail-item {
            padding: 0.35rem 0;
            border-bottom: 1px solid var(--border-color);
        }

        .detail-item.full { grid-column: 1 / -1; }

        .detail-label {
            font-size: 0.6rem;
            
            letter-spacing: 0.1em;
            color: var(--text-muted);
            margin-bottom: 0.15rem;
        }

        .detail-value {
            font-size: 0.85rem;
            color: var(--text-primary);
            word-break: break-all;
        }

        .detail-value.mono { font-family: var(--font-mono); }
        .detail-value.highlight { color: var(--accent-amber); }

        /* Editable fields (Identifier/Type/Vendor OUI/Group) inside the
        detail grid -- flattened to look like plain text (no visible
        box/border/background), matching Address's plain label+value
        look, while staying fully editable underneath. */
        .detail-item .form-input {
            border: none;
            background: transparent;
            padding: 0;
            width: auto;
            max-width: 100%;
        }
        .detail-item select.form-input { cursor: pointer; }

        /* Heatmaps */
        .heatmap-section {
            margin-top: 1rem;
        }

        .heatmap-title {
            font-size: 0.65rem;

            letter-spacing: 0.1em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }

        /* Two sections side by side instead of stacked -- compresses the
        modal's overall height noticeably on the wider layout above. */
        .heatmap-grid-2col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0 1.25rem;
        }
        .heatmap-grid-2col .heatmap-section { margin-top: 1rem; }
        @media (max-width: 640px) {
            .heatmap-grid-2col { grid-template-columns: 1fr; }
        }

        .dwell-stat-card {
            padding: 0.2rem 0;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }
        .dwell-stat-value { font-size: 1.15rem; font-weight: 700; line-height: 1; }
        .dwell-stat-label {
            font-size: 0.55rem;
            letter-spacing: 0.08em;
            color: var(--text-muted);
        }

        .heatmap {
            font-size: 0.8rem;
        }

        .heatmap-labels {
            color: var(--text-muted);
            font-size: 0.65rem;
            margin-bottom: 0.25rem;
        }

        .activity-grid {
            display: grid;
            gap: 3px;
        }

        .activity-grid.hourly {
            grid-template-columns: repeat(24, 1fr);
        }

        .activity-grid.daily {
            grid-template-columns: repeat(7, 1fr);
        }

        .activity-cell {
            aspect-ratio: 1;
            max-height: 26px;
            border-radius: 2px;
            background: var(--bg-hover);
            cursor: pointer;
            transition: opacity 0.1s;
        }

        .activity-cell:hover { opacity: 0.8; }
        .activity-cell.l1 { background: rgba(220, 38, 38, 0.25); }
        .activity-cell.l2 { background: rgba(220, 38, 38, 0.5); }
        .activity-cell.l3 { background: rgba(220, 38, 38, 0.75); }
        .activity-cell.l4 { background: var(--accent-red); }

        .activity-labels {
            display: grid;
            gap: 3px;
            margin-top: 2px;
            font-size: 0.55rem;
            color: var(--text-muted);
            text-align: center;
        }

        .activity-labels.hourly { grid-template-columns: repeat(24, 1fr); }
        .activity-labels.daily { grid-template-columns: repeat(7, 1fr); }

        /* Timeline Chart */
        .timeline-chart {
            display: flex;
            align-items: flex-end;
            gap: 2px;
            height: 50px;
            padding: 0.5rem 0;
        }

        .timeline-bar {
            flex: 1;
            min-width: 3px;
            background: var(--accent-red);
            border-radius: 1px 1px 0 0;
            transition: background 0.1s;
            cursor: pointer;
            opacity: 0.7;
        }

        .timeline-bar:hover {
            opacity: 1;
            background: var(--accent-orange);
        }

        .timeline-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.6rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }

        /* RSSI Chart */
        .rssi-chart {
            position: relative;
            height: 70px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 0.5rem;
            overflow: hidden;
        }

        .rssi-chart svg { width: 100%; height: 100%; }
        .rssi-line { fill: none; stroke: #ffffff; stroke-width: 1.5; }
        .rssi-area { fill: url(#rssiGradient); }
        .rssi-label { font-size: 0.55rem; fill: var(--text-muted); }

        /* Action Buttons in Modal */
        .btn-watch {
            background: transparent;
            border: 1px solid var(--accent-amber);
            color: var(--accent-amber);
            padding: 0.3rem 0.7rem;
            font-size: 0.65rem;
        }

        .btn-watch.active {
            background: var(--accent-amber);
            color: #000;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 0.75rem;
            font-size: 0.65rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            background: var(--bg-secondary);
        }

        .footer a { color: var(--accent-red); text-decoration: none; }
        .footer a:hover { text-decoration: underline; }

        .theme-toggle {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 0.75rem;
            padding: 0.3rem 0.5rem;
            cursor: pointer;
            border-radius: 3px;
            transition: all 0.1s;
        }

        .theme-toggle:hover {
            color: var(--text-primary);
            border-color: var(--border-active);
        }

        /* Responsive */
        @media (max-width: 900px) {
            .main { grid-template-columns: 1fr; }
            .sidebar { display: none; }
        }
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
                <a href="/all" class="nav-link active">All devices</a>
                <a href="/settings" class="nav-link">Config</a>
            </nav>
        </div>
        <div class="topbar-right">
            <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle light/dark mode">☀</button>
        </div>
    </header>

    <div class="main">
        <aside class="sidebar">
            <div class="panel" id="categories-panel">
                <div class="panel-header">Categories</div>
                <button class="filter-btn" id="all-devices-btn" onclick="showAllDevices()" style="width: 100%; justify-content: flex-start; gap: 0.4rem; margin-bottom: 0.5rem;">All devices <span id="count-all" class="filter-count" style="color: inherit; font-size: inherit;">--</span></button>
                <label style="display: flex; align-items: center; gap: 0.4rem; padding: 0 0.75rem 0.25rem; font-size: 0.75rem; color: var(--text-secondary); cursor: pointer;" title="Hides devices BlueWatch has already identified with a known Class (e.g. Tracker, Phone) -- independent of whether they've been filed into a Group.">
                    <input type="checkbox" id="hide-classified-toggle" onchange="toggleHideClassified()">
                    Hide classified devices
                </label>
                <label style="display: flex; align-items: center; gap: 0.4rem; padding: 0 0.75rem 0.5rem; font-size: 0.75rem; color: var(--text-secondary); cursor: pointer;" title="Hides devices already sorted into a category folder -- independent of whether their Class is known.">
                    <input type="checkbox" id="hide-grouped-toggle" onchange="toggleHideGrouped()">
                    Hide grouped devices
                </label>
                <div style="padding: 0 0.75rem 0.5rem;">
                    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem;">
                        <span>First seen within</span>
                        <span id="first-seen-slider-value">off</span>
                    </div>
                    <input type="range" id="first-seen-slider" min="1" max="7" step="1" value="1" oninput="onFirstSeenSliderChange()" style="width: 100%;">
                </div>
                <div id="categories-tree" style="padding: 0.5rem;"></div>
                <div style="padding: 0.5rem; display: flex; gap: 0.4rem;">
                    <input type="text" class="search-input" id="new-category-name" placeholder="New category name" style="font-size: 0.75rem; flex: 1;">
                    <button class="btn btn-primary" onclick="createCategory()">+</button>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">Date Range Query</div>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <input type="datetime-local" class="search-input" id="search-start" style="font-size: 0.7rem;">
                    <input type="datetime-local" class="search-input" id="search-end" style="font-size: 0.7rem;">
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn" style="flex:1;" onclick="clearDateFilters()">Clear</button>
                        <button class="btn btn-primary" style="flex:1;" onclick="searchByDateRange()">Query</button>
                    </div>
                    <input type="text" class="search-input" id="search" placeholder="Search MAC, vendor, or identifier..." style="font-size: 0.75rem;">
                </div>
            </div>

        </aside>

        <main class="content">
            <div class="table-container" id="priority-box" style="margin-bottom: 0.75rem; padding: 0.6rem 0.75rem; display: none;">
                <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.4rem;">
                    <span style="color: #f5c518; font-size: 0.9rem;">★</span>
                    <span class="table-title" style="font-size: 0.8rem;">Priority</span>
                    <span style="font-size: 0.7rem; color: var(--text-muted);">watched devices and type alerts &mdash; always shown, ignores filters</span>
                </div>
                <div id="priority-list" style="display: flex; flex-wrap: wrap; gap: 0.5rem;"></div>
            </div>
            <div class="table-container" id="devices-container">
                <div class="table-header">
                    <span class="table-title">Identified Targets <span id="selected-count" class="selected-summary" style="display: none;">· 0 selected</span></span>
                    <div class="table-actions">
                        <span style="font-size: 0.7rem; color: var(--text-muted);">
                            <span id="visible-count">--</span> targets
                        </span>
                        <select class="form-input bulk-select" id="bulk-group-select">
                            <option value="">Assign group...</option>
                        </select>
                        <button class="btn" id="bulk-group-apply" onclick="applyBulkGroup()">Assign Group</button>
                        <select class="form-input bulk-select" id="bulk-watch-select">
                            <option value="">Watch...</option>
                            <option value="on">Watch ON</option>
                            <option value="off">Watch OFF</option>
                        </select>
                        <button class="btn" id="bulk-watch-apply" onclick="applyBulkWatch()">Apply Watch</button>
                        <button class="btn" id="bulk-merge-apply" onclick="applyBulkMerge()" title="Cluster the selected MAC-rotation siblings into one device">Merge as One Device</button>
                        <button class="btn" id="clear-selection-btn" onclick="clearSelection()">Clear Selection</button>
                        <button class="btn" onclick="resetSort()">Reset Sort</button>
                    </div>
                </div>
                <table class="device-table">
                    <thead>
                        <tr>
                            <th class="select-col"><input type="checkbox" id="select-all-checkbox" class="row-select-checkbox" aria-label="Select all rows"></th>
                            <th class="sortable" data-sort="class">Class<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="vendor">Vendor<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="mac">Address<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="identifier">Identifier<span class="sort-indicator"></span></th>
                            <th>RSSI</th>
                            <th class="sortable" data-sort="sightings">Sightings<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="last_seen">Last seen<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="group">Group<span class="sort-indicator"></span></th>
                        </tr>
                    </thead>
                    <tbody id="device-list">
                        <tr><td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-muted);">Initializing scanner...</td></tr>
                    </tbody>
                </table>
                <div class="pagination-bar">
                    <div class="pagination-left">
                        <span id="page-info" style="font-size: 0.7rem; color: var(--text-muted);">Page --/--</span>
                    </div>
                    <div class="pagination-center">
                        <button class="btn" id="prev-page-btn" onclick="changePage(-1)">Prev</button>
                        <div class="page-numbers" id="page-numbers"></div>
                        <button class="btn" id="next-page-btn" onclick="changePage(1)">Next</button>
                    </div>
                    <div class="pagination-right">
                        <span style="font-size: 0.7rem; color: var(--text-muted);">Rows/page</span>
                        <select class="form-input bulk-select" id="page-size-select" onchange="changePageSize(this.value)">
                            <option value="25">25</option>
                            <option value="50" selected>50</option>
                            <option value="100">100</option>
                            <option value="150">150</option>
                            <option value="250">250</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="table-container" id="name-groups-container" style="display: none;">
                <div class="table-header">
                    <span class="table-title">Devices Sharing a Name <span id="name-groups-count" class="selected-summary" style="display: none;"></span></span>
                    <span style="font-size: 0.7rem; color: var(--text-muted);">
                        Identical advertised name across multiple MACs — likely MAC randomization.
                    </span>
                </div>
                <div id="name-groups-list" style="padding: 0.5rem 1rem 1rem;">
                    <div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading...</div>
                </div>
            </div>
        </main>
    </div>


    <!-- Target Detail Modal -->
    <div class="modal-overlay" id="device-modal">
        <div class="modal">
            <div class="modal-header">
                <span class="modal-title">Device Details</span>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <button class="btn" id="scan-unit-btn" onclick="scanUnit(currentDeviceMac)" title="Actively contact this device to ask what it supports (BLE GATT services / Classic SDP records). Unlike the rest of BlueWatch, this connects to the device rather than only listening.">Scan Unit</button>
                    <button class="btn btn-watch" id="watch-btn" onclick="toggleWatch(currentDeviceMac)"></button>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
            </div>
            <div class="modal-body" id="modal-content">
                <!-- Dynamic content -->
            </div>
        </div>
    </div>

    <!-- Shortcuts Modal -->
    <div class="modal-overlay" id="shortcuts-modal">
        <div class="modal" style="max-width: 400px;">
            <div class="modal-header">
                <span class="modal-title">Keyboard Shortcuts</span>
                <button class="modal-close" onclick="closeShortcutsModal()">&times;</button>
            </div>
            <div class="modal-body" style="padding: 1rem;">
                <div style="display: grid; gap: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">/</span><span style="color: var(--text-secondary);">Focus search</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">r</span><span style="color: var(--text-secondary);">Refresh devices</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">Esc</span><span style="color: var(--text-secondary);">Close modal</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">w</span><span style="color: var(--text-secondary);">Toggle watch (in modal)</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">1</span><span style="color: var(--text-secondary);">Show all devices</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">2</span><span style="color: var(--text-secondary);">Show watched only</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">3</span><span style="color: var(--text-secondary);">Filter phones</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">4</span><span style="color: var(--text-secondary);">Filter laptops</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0;"><span class="kbd">5</span><span style="color: var(--text-secondary);">Filter audio</span></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            const btn = document.getElementById('theme-toggle');
            if (btn) btn.textContent = theme === 'light' ? '☽' : '☀';
        }

        function toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            localStorage.setItem('bluewatch_theme', next);
            applyTheme(next);
        }

        applyTheme(localStorage.getItem('bluewatch_theme') || 'dark');

        const PAGE_SIZE_OPTIONS = [25, 50, 100, 150, 250];
        const PAGE_SIZE_STORAGE_KEY = 'bluewatch_page_size_v2';

        function normalizePageSize(value) {
            const parsed = Number.parseInt(value, 10);
            if (!Number.isFinite(parsed)) return 50;
            if (PAGE_SIZE_OPTIONS.includes(parsed)) return parsed;
            return 50;
        }

        let allDevices = [];
        let currentFilter = 'all';
        let currentGroupId = null;
        let hideClassified = localStorage.getItem('bluewatch_hide_classified') === 'true';
        let hideGrouped = localStorage.getItem('bluewatch_hide_grouped') === 'true';
        let dateFilteredDevices = null;
        let compactView = localStorage.getItem('bluewatch_compact_view') === 'true';
        let screenshotMode = localStorage.getItem('bluewatch_screenshot_mode') === 'true';
        let clickToOpen = localStorage.getItem('bluewatch_click_to_open') === 'true';
        const defaultSortState = { column: 'last_seen', direction: 'desc' };
        let sortState = { ...defaultSortState };
        let selectedMacs = new Set();
        let lastSelectedIndex = null;
        let currentVisibleDevices = [];
        let rowClickTimer = null;
        let searchDebounceTimer = null;
        let pagination = {
            page: 1,
            pageSize: normalizePageSize(localStorage.getItem(PAGE_SIZE_STORAGE_KEY)),
            totalPages: 1,
            totalMatching: 0,
            hasPrev: false,
            hasNext: false,
        };

        function getServerSortDirection() {
            return sortState.direction;
        }

        function buildDevicesUrl() {
            const params = new URLSearchParams();
            params.set('page', pagination.page);
            params.set('page_size', pagination.pageSize);
            params.set('filter', currentFilter);
            if (hideClassified || hideGrouped) {
                if (hideClassified) params.set('hide_classified', '1');
                if (hideGrouped) params.set('hide_grouped', '1');
            } else if (currentGroupId !== null) {
                params.set('group_id', currentGroupId);
            }
            params.set('sort', sortState.column);
            params.set('direction', getServerSortDirection());

            const searchInput = document.getElementById('search');
            const searchTerm = searchInput ? searchInput.value.trim() : '';
            if (searchTerm) params.set('search', searchTerm);

            const firstSeenLevel = parseInt(document.getElementById('first-seen-slider').value, 10);
            if (firstSeenLevel > 1) {
                params.set('first_seen', FIRST_SEEN_LEVELS[firstSeenLevel - 2]);
            }

            return '/api/devices?' + params.toString();
        }

        // Levels 1-6 on the "First seen within" slider. Untouched (the
        // default) applies no filter at all -- only once the operator
        // actually drags it does it start narrowing to "first seen within
        // this window", same spirit as the Sightings/RSSI sliders but
        // those have a naturally permissive end (1 sighting / -100 dBm
        // effectively shows everyone); first-seen has no such end since
        // even the loosest window (30d) would hide long-established
        // devices, so it stays off until deliberately touched.
        const FIRST_SEEN_LEVELS = ['6h', '12h', '24h', '48h', '7d', '30d'];
        const FIRST_SEEN_LABELS = ['off', '6h', '12h', '24h', '48h', 'this week', 'this month'];

        function onFirstSeenSliderChange() {
            const level = parseInt(document.getElementById('first-seen-slider').value, 10);
            document.getElementById('first-seen-slider-value').textContent = FIRST_SEEN_LABELS[level - 1];
            pagination.page = 1;
            refreshDevices();
        }

        function queueDeviceRefresh(resetPage = false) {
            if (resetPage) pagination.page = 1;
            if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                searchDebounceTimer = null;
                refreshDevices();
            }, 250);
        }

        function toggleViewMode() {
            compactView = !compactView;
            localStorage.setItem('bluewatch_compact_view', compactView);
            updateViewToggle();
            renderDevices();
        }

        function updateViewToggle() {
            const btn = document.getElementById('view-toggle');
            if (btn) {
                btn.innerHTML = compactView ? '◫ Detailed View' : '☰ Compact View';
            }
        }

        function toggleScreenshotMode() {
            screenshotMode = !screenshotMode;
            localStorage.setItem('bluewatch_screenshot_mode', screenshotMode);
            updateScreenshotToggle();
            renderDevices();
        }

        function updateScreenshotToggle() {
            const btn = document.getElementById('screenshot-toggle');
            if (btn) {
                btn.innerHTML = screenshotMode ? '📷 Screenshot Mode ON' : '📷 Screenshot Mode';
                btn.style.background = screenshotMode ? 'var(--accent-red)' : '';
                btn.style.color = screenshotMode ? 'white' : '';
            }
        }

        function toggleClickToOpen() {
            clickToOpen = !clickToOpen;
            localStorage.setItem('bluewatch_click_to_open', clickToOpen);
            updateClickToOpenToggle();
        }

        function updateClickToOpenToggle() {
            const btn = document.getElementById('click-to-open-toggle');
            if (btn) {
                btn.innerHTML = clickToOpen ? '👆 Click to Open ON' : '👆 Click to Open';
                btn.style.background = clickToOpen ? 'var(--accent-blue)' : '';
                btn.style.color = clickToOpen ? 'white' : '';
            }
        }

        let nameGroupsActive = false;

        function toggleNameGroups() {
            nameGroupsActive = !nameGroupsActive;
            const devicesEl = document.getElementById('devices-container');
            const groupsEl = document.getElementById('name-groups-container');
            if (devicesEl) devicesEl.style.display = nameGroupsActive ? 'none' : '';
            if (groupsEl) groupsEl.style.display = nameGroupsActive ? '' : 'none';
            const btn = document.getElementById('name-groups-toggle');
            if (btn) {
                btn.innerHTML = nameGroupsActive ? '🔗 Group by Name ON' : '🔗 Group by Name';
                btn.style.background = nameGroupsActive ? 'var(--accent-blue)' : '';
                btn.style.color = nameGroupsActive ? 'white' : '';
            }
            if (nameGroupsActive) loadNameGroups();
        }

        async function loadNameGroups() {
            const container = document.getElementById('name-groups-list');
            const countEl = document.getElementById('name-groups-count');
            if (!container) return;
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading...</div>';
            try {
                const response = await fetch('/api/name-groups');
                const data = await response.json();
                const groups = data.groups || [];
                if (countEl) {
                    countEl.style.display = '';
                    countEl.textContent = '· ' + groups.length + ' name' + (groups.length === 1 ? '' : 's');
                }
                if (groups.length === 0) {
                    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">No names are shared across multiple addresses.</div>';
                    return;
                }
                container.innerHTML = groups.map(renderNameGroup).join('');
            } catch (error) {
                container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Error loading name groups</div>';
            }
        }

        function renderNameGroup(g) {
            const name = obfuscateName(g.name) || '(unnamed)';
            const { text: lastSeen, tooltip: lastSeenTooltip } = formatLastSeen(g.last_seen);
            const vendor = g.vendor ? ' · ' + g.vendor : '';
            const randomized = g.randomized_count > 0
                ? '<span title="' + g.randomized_count + ' of ' + g.device_count + ' addresses are randomized" style="font-size: 0.65rem; color: var(--accent-amber); border: 1px solid var(--accent-amber); border-radius: 3px; padding: 0 0.3rem; margin-left: 0.5rem;">' + g.randomized_count + ' randomized</span>'
                : '';
            const members = (g.macs || []).map(mac => {
                const shownMac = isMacOSUUID(mac) ? obfuscateMAC(mac).substring(0, 13) + '...' : obfuscateMAC(mac);
                return '<div onclick="showDevice(\\'' + mac + '\\')" title="' + mac + '" style="font-family: monospace; font-size: 0.72rem; color: var(--text-secondary); padding: 0.25rem 0.5rem; border-bottom: 1px solid var(--border-color); cursor: pointer;">' + shownMac + '</div>';
            }).join('');
            return '<div style="margin-bottom: 1rem; border: 1px solid var(--border-color); border-radius: 6px; overflow: hidden;">' +
                '<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0.75rem; background: var(--bg-tertiary);">' +
                '<div style="min-width: 0;">' +
                '<span style="font-size: 0.85rem; color: var(--text-primary); font-weight: 600;">' + (g.type_icon || '') + ' ' + name + '</span>' + randomized +
                '<div style="font-size: 0.65rem; color: var(--text-muted);">' + g.device_count + ' addresses' + vendor + ' · ' + g.total_sightings + ' sightings · last seen <span title="' + lastSeenTooltip + '">' + lastSeen + '</span></div>' +
                '</div>' +
                '<span style="font-size: 1.1rem; font-weight: 700; color: var(--accent-blue); margin-left: 0.75rem;">' + g.device_count + '</span>' +
                '</div>' + members + '</div>';
        }

        function isMacOSUUID(addr) {
            return /^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$/.test(addr);
        }

        // Demo Mode: full redaction for public screenshots (all MACs zeroed,
        // names/vendors/categories swapped for generic placeholders) -- a
        // stronger version of Screenshot Mode's partial masking. Enable via
        // the browser console: localStorage.setItem('bluewatch_demo_mode','true'); location.reload();
        let demoMode = localStorage.getItem('bluewatch_demo_mode') === 'true' || new URLSearchParams(window.location.search).get('demo') === '1';
        const DEMO_NAMES = ['Guest Phone', 'Kitchen Speaker', 'Smart Plug', 'Wireless Headset', 'Fitness Tracker', 'Smart TV', 'Tablet', 'Car Bluetooth', 'IoT Sensor', 'Robot Vacuum', 'Doorbell Camera', 'Smart Watch', 'Bluetooth Mouse', 'Game Controller', 'E-bike Lock'];
        let demoNameCounter = 0;

        function obfuscateMAC(mac) {
            if (demoMode) return mac ? '00:00:00:00:00:00' : mac;
            if (!screenshotMode || !mac) return mac;
            // Handle macOS UUID-format addresses
            if (isMacOSUUID(mac)) {
                return mac.substring(0, 8) + '-XXXX-XXXX-XXXX-XXXXXXXXXXXX';
            }
            // Show first 2 octets, hide the rest: AA:BB:XX:XX:XX:XX
            const parts = mac.split(':');
            if (parts.length === 6) {
                return parts[0] + ':' + parts[1] + ':XX:XX:XX:XX';
            }
            return mac.substring(0, 5) + ':XX:XX:XX:XX';
        }

        function obfuscateName(name) {
            if (demoMode) return name ? DEMO_NAMES[(demoNameCounter++) % DEMO_NAMES.length] : name;
            if (!screenshotMode || !name) return name;
            // Show first 2 chars, then asterisks
            if (name.length <= 2) return '**';
            return name.substring(0, 2) + '*'.repeat(Math.min(name.length - 2, 8));
        }

        function showShortcutsModal() {
            document.getElementById('shortcuts-modal').classList.add('active');
        }

        function closeShortcutsModal() {
            document.getElementById('shortcuts-modal').classList.remove('active');
        }

        // Only the newest request may update the screen: a slower, older
        // request (e.g. the live "active now" refresh) finishing after the one
        // for the category just clicked used to put the full list back.
        let devicesRefreshSeq = 0;
        async function refreshDevices() {
            const seq = ++devicesRefreshSeq;
            try {
                const response = await fetch(buildDevicesUrl());
                const data = await response.json();
                if (seq !== devicesRefreshSeq) return;
                allDevices = data.devices || [];
                const knownMacs = new Set(allDevices.map(d => d.mac));
                selectedMacs = new Set([...selectedMacs].filter(mac => knownMacs.has(mac)));
                pagination.page = data.page || pagination.page;
                pagination.pageSize = data.page_size || pagination.pageSize;
                pagination.totalPages = data.total_pages || 1;
                pagination.totalMatching = data.total_matching || 0;
                pagination.hasPrev = !!data.has_prev;
                pagination.hasNext = !!data.has_next;
                localStorage.setItem(PAGE_SIZE_STORAGE_KEY, String(pagination.pageSize));
                updateStats(data);
                updateFilterCounts(data.filter_counts);
                updatePaginationUI();
                if (!dateFilteredDevices) renderDevices();
                updateSelectionUI();
            } catch (error) {
                console.error('Scan error:', error);
            }
        }

        function updateStats(data) {
            // (Total units seen was removed from the header -- data.total
            // is still returned by the API but nothing displays it now.)
        }

        // ==================== Live sighting stream (SSE) ====================
        // /api/live-events pushes the instant a device is upserted from a
        // scan (daemon.py, right after db.upsert_device()) -- rather than
        // waiting up to the poll interval (setInterval(refreshDevices,...)
        // below) to notice it. Deliberately does NOT merge the pushed
        // device into allDevices client-side (that array is one server-
        // computed page under the current filter/sort -- blindly inserting
        // a device risks putting it somewhere it doesn't belong, e.g. past
        // a filter that would exclude it). Instead each push triggers a
        // debounced real refresh -- coalesces a burst of many devices from
        // one scan cycle into a single fetch instead of one per device --
        // so what's on screen is always server-truth, just fetched near-
        // instantly instead of on the next scheduled tick.
        let liveEventSource = null;
        let liveRefreshDebounce = null;
        function startLiveEventStream() {
            if (liveEventSource) return;
            liveEventSource = new EventSource('/api/live-events');
            liveEventSource.onmessage = () => {
                clearTimeout(liveRefreshDebounce);
                liveRefreshDebounce = setTimeout(() => {
                    refreshDevices();
                    loadPriorityDevices();
                }, 200);
            };
            // EventSource reconnects on its own after a drop/server
            // restart -- nothing to do here beyond letting it retry.
        }

        // ==================== Priority box (watched + type alerts) ====================
        // Always-visible box that surfaces watched devices and devices whose
        // type is on the Type-Based Alerts list (Config > Alerts), ignoring
        // whatever filters are active in the main table below -- so e.g. a
        // brand-new drone MAC still jumps out even if "Hide categorized" or
        // a First Seen filter would otherwise hide it.
        async function loadPriorityDevices() {
            try {
                const res = await fetch('/api/devices/priority');
                const data = await res.json();
                renderPriorityBox(data.devices || []);
            } catch (e) {
                console.error('Failed to load priority devices:', e);
            }
        }

        function renderPriorityBox(devices) {
            const box = document.getElementById('priority-box');
            const list = document.getElementById('priority-list');
            if (!box || !list) return;
            if (devices.length === 0) {
                box.style.display = 'none';
                return;
            }
            box.style.display = '';
            list.innerHTML = devices.map(d => {
                const name = obfuscateName(d.friendly_name || d.vendor || d.mac);
                const badge = d.reason === 'watched'
                    ? '<span style="color:#f5c518;" title="Watched device">★</span>'
                    : '<span style="color:#f59e0b; font-size:0.6rem; font-weight:600; letter-spacing:0.03em;" title="Type alert: ' + escapeHtml(d.type_label) + '">ALERT</span>';
                return '<div onclick="showDevice(\\'' + d.mac + '\\')" style="cursor:pointer; display:flex; align-items:center; gap:0.4rem; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 0.3rem 0.6rem; font-size: 0.75rem;">'
                    + badge
                    + '<span class="type-badge ' + getTypeClass(d.device_type) + '" style="font-size:0.65rem; padding:0.1rem 0.35rem;">' + d.type_icon + '</span>'
                    + '<span>' + escapeHtml(name) + '</span>'
                    + '</div>';
            }).join('');
        }

        // ==================== Categories (sidebar tree) ====================
        let categoriesCache = [];

        async function loadCategories() {
            try {
                const res = await fetch('/api/groups');
                const data = await res.json();
                categoriesCache = data.groups || [];
                cachedGroups = categoriesCache;  // single source of truth -- see loadGroupsForDevice/loadGroupsForBulkSelect
                renderCategoryTree();
            } catch (e) {
                console.error('Failed to load categories:', e);
            }
        }

        function groupOptionLabel(g) {
            if (g.parent_id) {
                const parent = cachedGroups.find(p => p.id === g.parent_id);
                return (parent ? parent.name + ' › ' : '') + g.name;
            }
            return g.name;
        }

        function renderCategoryTree() {
            const el = document.getElementById('categories-tree');
            if (!el) return;
            const topLevel = categoriesCache.filter(g => !g.parent_id);
            if (topLevel.length === 0) {
                el.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-muted); padding: 0.5rem 0.25rem;">No categories yet</div>';
                return;
            }
            el.innerHTML = topLevel.map(g => renderCategoryNode(g)).join('');
        }

        function renderCategoryNode(group) {
            const children = categoriesCache.filter(g => g.parent_id === group.id);
            const childrenHtml = children.length
                ? '<div class="category-children">' + children.map(c => renderCategoryNode(c)).join('') + '</div>'
                : '';
            const isActive = currentGroupId === group.id;
            return (
                '<div class="category-node' + (isActive ? ' active' : '') + '" draggable="true" data-id="' + group.id + '" ' +
                'ondragstart="onCategoryDragStart(event, ' + group.id + ')" ' +
                'ondragover="onCategoryDragOver(event)" ' +
                'ondragleave="onCategoryDragLeave(event)" ' +
                'ondrop="onCategoryDrop(event, ' + group.id + ')">' +
                '<span class="category-label" style="color:' + (group.color || '#3b82f6') + '" onclick="selectCategory(' + group.id + ')" title="Click to show only this category\\'s devices, drag onto another category to nest it as a subcategory">' +
                (group.icon || '📁') + ' ' + escapeHtml(obfuscateName(group.name)) +
                '</span>' +
                '<button class="category-delete" onclick="deleteCategory(' + group.id + ')" title="Delete category">×</button>' +
                '</div>' + childrenHtml
            );
        }

        function selectCategory(groupId) {
            currentGroupId = (currentGroupId === groupId) ? null : groupId;
            currentFilter = 'all';
            // Picking a specific category and hiding all categorized devices
            // are contradictory -- the category selection wins, and the
            // checkbox unchecking itself makes that visible instead of the
            // click silently doing nothing.
            setHideClassified(false);
            setHideGrouped(false);
            const allBtn = document.getElementById('all-devices-btn');
            if (allBtn) allBtn.classList.remove('active');
            renderCategoryTree();
            selectedMacs.clear();
            lastSelectedIndex = null;
            pagination.page = 1;
            refreshDevices();
        }

        function showAllDevices() {
            currentGroupId = '__all__';
            currentFilter = 'all';
            setHideClassified(false);
            setHideGrouped(false);
            renderCategoryTree();
            selectedMacs.clear();
            lastSelectedIndex = null;
            pagination.page = 1;
            refreshDevices();
        }

        function setHideClassified(value) {
            hideClassified = value;
            localStorage.setItem('bluewatch_hide_classified', hideClassified);
            const checkbox = document.getElementById('hide-classified-toggle');
            if (checkbox) checkbox.checked = value;
        }

        function toggleHideClassified() {
            const checkbox = document.getElementById('hide-classified-toggle');
            setHideClassified(checkbox ? checkbox.checked : false);
            selectedMacs.clear();
            lastSelectedIndex = null;
            pagination.page = 1;
            refreshDevices();
        }

        function setHideGrouped(value) {
            hideGrouped = value;
            localStorage.setItem('bluewatch_hide_grouped', hideGrouped);
            const checkbox = document.getElementById('hide-grouped-toggle');
            if (checkbox) checkbox.checked = value;
        }

        function toggleHideGrouped() {
            const checkbox = document.getElementById('hide-grouped-toggle');
            setHideGrouped(checkbox ? checkbox.checked : false);
            selectedMacs.clear();
            lastSelectedIndex = null;
            pagination.page = 1;
            refreshDevices();
        }

        function escapeHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }

        // Apple Continuity "Nearby Info" live activity snapshot (screen
        // on/idle/driving, etc.) -- only shown when the device has ever
        // produced one (Apple devices only) and it's recent enough to
        // still reflect current state rather than something stale from
        // long before the device was last even seen.
        function appleActivityHtml(d) {
            if (!d.apple_activity || !d.apple_activity_at) return '';
            const ageMs = Date.now() - new Date(d.apple_activity_at).getTime();
            if (ageMs > 5 * 60 * 1000) return '';
            const a = d.apple_activity;
            let screenLabel = 'unknown';
            let screenColor = 'var(--text-muted)';
            if (a.screen_on === true) { screenLabel = 'on'; screenColor = '#16a34a'; }
            else if (a.screen_on === false) { screenLabel = 'off'; screenColor = '#555'; }
            let line = 'Screen: <span style="color:' + screenColor + ';">' + screenLabel + '</span> — ' + escapeHtml(a.activity || '');
            const extras = [];
            if (a.wifi_on === true) extras.push('WiFi on');
            if (a.watch_locked === true) extras.push('Watch locked');
            if (a.airdrop_receiving === true) extras.push('AirDrop on');
            if (extras.length) line += ' (' + extras.join(', ') + ')';
            return '<div class="detail-item full"><div class="detail-label">Apple Activity (live)</div><div class="detail-value" style="font-size:0.8rem;">' + line + '</div></div>';
        }

        // Samsung VD-family power state (TV/AV/monitor/fridge) -- same
        // live/recent-only treatment as appleActivityHtml above.
        function samsungStatusHtml(d) {
            if (!d.samsung_status || !d.samsung_status_at) return '';
            const ageMs = Date.now() - new Date(d.samsung_status_at).getTime();
            if (ageMs > 5 * 60 * 1000) return '';
            const s = d.samsung_status;
            const powerColors = { on: '#16a34a', standby: '#d97706', off: '#555' };
            const color = powerColors[s.power] || 'var(--text-muted)';
            const line = escapeHtml(s.device_class || 'device') + ': <span style="color:' + color + ';">' + escapeHtml(s.power || 'unknown') + '</span>';
            return '<div class="detail-item full"><div class="detail-label">Samsung Status (live)</div><div class="detail-value" style="font-size:0.8rem;">' + line + '</div></div>';
        }

        // Fast Pair Battery Notification (earbuds/case) -- same
        // live/recent-only treatment as appleActivityHtml above.
        function fastpairBatteryHtml(d) {
            if (!d.fastpair_battery || !d.fastpair_battery_at) return '';
            const ageMs = Date.now() - new Date(d.fastpair_battery_at).getTime();
            if (ageMs > 5 * 60 * 1000) return '';
            const b = d.fastpair_battery;
            const labels = { left: 'L', right: 'R', case: 'Case' };
            const parts = [];
            for (const key of ['left', 'right', 'case']) {
                const comp = b[key];
                if (!comp) continue;
                let seg = labels[key] + ' ' + (comp.pct === null || comp.pct === undefined ? '?' : comp.pct + '%');
                if (comp.charging) seg += '⚡';
                parts.push(seg);
            }
            if (!parts.length) return '';
            return '<div class="detail-item full"><div class="detail-label">Battery (live)</div><div class="detail-value" style="font-size:0.8rem;">' + parts.join(' · ') + '</div></div>';
        }

        // ASTM F3411/OpenDroneID Remote ID -- same live/recent-only
        // treatment as appleActivityHtml above. Only one ASTM message
        // type arrives per advertisement (Basic ID, Location, Self ID,
        // System, or Operator ID), so this renders whatever the most
        // recent sighting happened to carry, not an accumulated picture.
        function droneStateHtml(d) {
            if (!d.drone_state || !d.drone_state_at) return '';
            const ageMs = Date.now() - new Date(d.drone_state_at).getTime();
            if (ageMs > 5 * 60 * 1000) return '';
            const s = d.drone_state;
            const parts = [];
            if (s.uas_id) parts.push('UAS ID ' + escapeHtml(s.uas_id) + (s.ua_type ? ' (' + escapeHtml(s.ua_type) + ')' : ''));
            if (s.latitude !== undefined && s.longitude !== undefined) {
                let pos = 'Position ' + s.latitude + ', ' + s.longitude;
                if (s.altitude_m !== undefined) pos += ' @ ' + s.altitude_m + 'm';
                parts.push(pos);
            }
            if (s.status) parts.push('Status: ' + escapeHtml(s.status));
            if (s.self_id) parts.push('"' + escapeHtml(s.self_id) + '"');
            if (s.operator_latitude !== undefined && s.operator_longitude !== undefined) {
                parts.push('Operator @ ' + s.operator_latitude + ', ' + s.operator_longitude);
            }
            if (s.operator_id) parts.push('Operator ID ' + escapeHtml(s.operator_id));
            if (!parts.length) return '';
            return '<div class="detail-item full"><div class="detail-label">Drone Remote ID (live)</div><div class="detail-value" style="font-size:0.8rem;">' + parts.join(' · ') + '</div></div>';
        }

        async function createCategory() {
            const input = document.getElementById('new-category-name');
            const name = (input.value || '').trim();
            if (!name) return;
            try {
                await fetch('/api/groups', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, color: '#3b82f6', icon: '📁' }),
                });
                input.value = '';
                await loadCategories();
            } catch (e) {
                console.error('Failed to create category:', e);
            }
        }

        async function deleteCategory(groupId) {
            if (!confirm('Delete this category? Devices in it revert to Unknown; subcategories are promoted to top-level.')) return;
            try {
                await fetch('/api/groups/' + groupId, { method: 'DELETE' });
                await loadCategories();
            } catch (e) {
                console.error('Failed to delete category:', e);
            }
        }

        let draggedCategoryId = null;
        let draggedDeviceMac = null;

        function onCategoryDragStart(event, groupId) {
            draggedCategoryId = groupId;
            draggedDeviceMac = null;
            event.dataTransfer.effectAllowed = 'move';
        }

        function onDeviceDragStart(event, mac) {
            draggedDeviceMac = mac;
            draggedCategoryId = null;
            event.dataTransfer.effectAllowed = 'move';
        }

        function onCategoryDragOver(event) {
            event.preventDefault();
            event.currentTarget.classList.add('category-drop-target');
        }

        function onCategoryDragLeave(event) {
            event.currentTarget.classList.remove('category-drop-target');
        }

        async function onCategoryDrop(event, targetGroupId) {
            event.preventDefault();
            event.stopPropagation();
            event.currentTarget.classList.remove('category-drop-target');

            if (draggedDeviceMac !== null) {
                const mac = draggedDeviceMac;
                draggedDeviceMac = null;
                try {
                    await fetch('/api/device/' + encodeURIComponent(mac) + '/group', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ group_id: targetGroupId }),
                    });
                    await refreshDevices();
                } catch (e) {
                    console.error('Failed to assign device to category:', e);
                }
                return;
            }

            if (draggedCategoryId === null || draggedCategoryId === targetGroupId) return;
            try {
                const res = await fetch('/api/groups/' + draggedCategoryId + '/reparent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ parent_id: targetGroupId }),
                });
                if (!res.ok) {
                    const err = await res.json();
                    alert(err.error || 'Could not nest that category there');
                }
                draggedCategoryId = null;
                await loadCategories();
            } catch (e) {
                console.error('Failed to reparent category:', e);
            }
        }

        function updateFilterCounts(serverCounts = null) {
            const counts = serverCounts || { all: 0, watched: 0, phone: 0, laptop: 0, audio: 0, smart: 0, unknown: 0 };
            if (!serverCounts) {
                allDevices.forEach(d => {
                    counts.all++;
                    if (d.watched) counts.watched++;
                    if (d.device_type === 'phone') counts.phone++;
                    else if (d.device_type === 'laptop' || d.device_type === 'computer') counts.laptop++;
                    else if (d.device_type === 'audio' || d.device_type === 'speaker') counts.audio++;
                    else if (d.device_type === 'smart') counts.smart++;
                    else if (d.device_type === 'unknown') counts.unknown++;
                });
            }
            Object.keys(counts).forEach(k => {
                const el = document.getElementById('count-' + k);
                if (el) el.textContent = counts[k];
            });
        }

        async function searchByDateRange() {
            const startInput = document.getElementById('search-start').value;
            const endInput = document.getElementById('search-end').value;
            if (!startInput && !endInput) { clearDateFilters(); return; }
            try {
                let url = '/api/search?';
                if (startInput) url += 'start=' + encodeURIComponent(startInput) + '&';
                if (endInput) url += 'end=' + encodeURIComponent(endInput);
                const response = await fetch(url);
                const data = await response.json();
                if (!response.ok) {
                    alert('Date query failed: ' + (data.error || response.status));
                    return;
                }
                dateFilteredDevices = data.devices || [];
                selectedMacs.clear();
                lastSelectedIndex = null;
                updatePaginationUI();
                renderDevices();
                if (dateFilteredDevices.length === 0) {
                    alert('No devices had a sighting in that date range.');
                }
            } catch (error) {
                console.error('Query error:', error);
                alert('Date query failed: ' + error.message);
            }
        }

        function clearDateFilters() {
            document.getElementById('search-start').value = '';
            document.getElementById('search-end').value = '';
            dateFilteredDevices = null;
            updatePaginationUI();
            refreshDevices();
        }

        function resetSort() {
            sortState = { ...defaultSortState };
            updateSortIndicators();
            if (dateFilteredDevices !== null) {
                renderDevices();
                return;
            }
            pagination.page = 1;
            refreshDevices();
        }

        function setSort(column) {
            if (sortState.column === column) {
                sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
            } else {
                sortState.column = column;
                sortState.direction = 'asc';
            }
            updateSortIndicators();
            if (dateFilteredDevices !== null) {
                renderDevices();
                return;
            }
            pagination.page = 1;
            refreshDevices();
        }

        function updatePaginationUI() {
            const pageInfo = document.getElementById('page-info');
            const prevBtn = document.getElementById('prev-page-btn');
            const nextBtn = document.getElementById('next-page-btn');
            const pageNumbers = document.getElementById('page-numbers');
            const pageSizeSelect = document.getElementById('page-size-select');
            if (!pageInfo || !prevBtn || !nextBtn || !pageNumbers) return;
            if (pageSizeSelect) {
                pageSizeSelect.value = String(pagination.pageSize);
            }

            const paginationCenter = document.querySelector('.pagination-center');
            const paginationRight = document.querySelector('.pagination-right');

            if (dateFilteredDevices !== null) {
                pageInfo.textContent = 'Date range query — showing all ' + dateFilteredDevices.length + ' matching devices (no paging)';
                if (paginationCenter) paginationCenter.style.display = 'none';
                if (paginationRight) paginationRight.style.display = 'none';
                return;
            }

            if (paginationCenter) paginationCenter.style.display = '';
            if (paginationRight) paginationRight.style.display = '';
            pageInfo.textContent = 'Page ' + pagination.page + '/' + Math.max(1, pagination.totalPages);
            prevBtn.disabled = !pagination.hasPrev;
            nextBtn.disabled = !pagination.hasNext;
            if (pageSizeSelect) pageSizeSelect.disabled = false;
            renderPageNumbers(pageNumbers);
        }

        function getPageTokens(totalPages, currentPage) {
            if (totalPages <= 7) {
                return Array.from({ length: totalPages }, (_, i) => i + 1);
            }

            const tokens = [1];
            let start = Math.max(2, currentPage - 1);
            let end = Math.min(totalPages - 1, currentPage + 1);

            if (currentPage <= 3) {
                start = 2;
                end = 4;
            } else if (currentPage >= totalPages - 2) {
                start = totalPages - 3;
                end = totalPages - 1;
            }

            if (start > 2) tokens.push('…');
            for (let page = start; page <= end; page++) tokens.push(page);
            if (end < totalPages - 1) tokens.push('…');
            tokens.push(totalPages);

            return tokens;
        }

        function renderPageNumbers(container) {
            const totalPages = Math.max(1, pagination.totalPages);
            const currentPage = Math.min(Math.max(1, pagination.page), totalPages);
            const tokens = getPageTokens(totalPages, currentPage);

            container.innerHTML = tokens.map(token => {
                if (typeof token !== 'number') {
                    return '<span class="page-ellipsis">' + token + '</span>';
                }

                const activeClass = token === currentPage ? ' active' : '';
                return (
                    '<button class="btn page-number-btn' + activeClass + '"' +
                    ' onclick="goToPage(' + token + ')">' +
                    token +
                    '</button>'
                );
            }).join('');
        }

        function goToPage(page) {
            if (dateFilteredDevices !== null) return;
            const targetPage = Math.max(1, Math.min(page, pagination.totalPages));
            if (targetPage === pagination.page) return;
            pagination.page = targetPage;
            selectedMacs.clear();
            lastSelectedIndex = null;
            refreshDevices();
        }

        function changePage(delta) {
            if (dateFilteredDevices !== null) return;
            const nextPage = pagination.page + delta;
            goToPage(nextPage);
        }

        function changePageSize(value) {
            const nextPageSize = normalizePageSize(value);
            if (nextPageSize === pagination.pageSize) return;
            pagination.pageSize = nextPageSize;
            localStorage.setItem(PAGE_SIZE_STORAGE_KEY, String(nextPageSize));
            pagination.page = 1;
            selectedMacs.clear();
            lastSelectedIndex = null;

            if (dateFilteredDevices !== null) {
                updatePaginationUI();
                return;
            }
            refreshDevices();
        }

        function updateSortIndicators() {
            document.querySelectorAll('.device-table th.sortable').forEach(th => {
                const indicator = th.querySelector('.sort-indicator');
                if (!indicator) return;
                const isActive = th.dataset.sort === sortState.column;
                th.classList.toggle('active', isActive);
                if (!isActive) {
                    indicator.textContent = '';
                } else {
                    indicator.textContent = sortState.direction === 'asc' ? '▲' : '▼';
                }
            });
        }

        function getSortValue(device, column) {
            switch (column) {
                case 'class':
                    return (device.type_label || device.device_type || '').toLowerCase();
                case 'mac':
                    return (device.mac || '').toLowerCase();
                case 'vendor':
                    return (device.vendor || '').toLowerCase();
                case 'identifier':
                    return (device.friendly_name || '').toLowerCase();
                case 'sightings':
                    return Number.isFinite(device.total_sightings) ? device.total_sightings : -1;
                case 'last_seen':
                    // Raw timestamp (ms since epoch) so normal asc/desc sorting is
                    // intuitive: desc = highest timestamp = most recent first.
                    // Undated devices sort as the oldest possible value.
                    return device.last_seen ? new Date(device.last_seen).getTime() : Number.NEGATIVE_INFINITY;
                case 'group':
                    return (device.group_name || '').toLowerCase();
                default:
                    return '';
            }
        }

        function applySort(devices) {
            const sorted = [...devices];
            const direction = sortState.direction === 'asc' ? 1 : -1;
            sorted.sort((a, b) => {
                const aVal = getSortValue(a, sortState.column);
                const bVal = getSortValue(b, sortState.column);
                if (aVal < bVal) return -1 * direction;
                if (aVal > bVal) return 1 * direction;
                return 0;
            });
            return sorted;
        }

        function updateSelectionUI() {
            const selectedCount = selectedMacs.size;
            const summary = document.getElementById('selected-count');
            if (summary) {
                if (selectedCount > 0) {
                    summary.style.display = 'inline';
                    summary.textContent = '· ' + selectedCount + ' selected';
                } else {
                    summary.style.display = 'none';
                    summary.textContent = '';
                }
            }

            updateSelectAllCheckbox();
            updateBulkActionState();
        }

        function updateSelectAllCheckbox() {
            const checkbox = document.getElementById('select-all-checkbox');
            if (!checkbox) return;
            if (!currentVisibleDevices || currentVisibleDevices.length === 0) {
                checkbox.checked = false;
                checkbox.indeterminate = false;
                checkbox.disabled = true;
                return;
            }
            checkbox.disabled = false;
            const selectedVisibleCount = currentVisibleDevices.filter(d => selectedMacs.has(d.mac)).length;
            checkbox.checked = selectedVisibleCount > 0 && selectedVisibleCount === currentVisibleDevices.length;
            checkbox.indeterminate = selectedVisibleCount > 0 && selectedVisibleCount < currentVisibleDevices.length;
        }

        function updateBulkActionState() {
            const hasSelection = selectedMacs.size > 0;
            const bulkGroupSelect = document.getElementById('bulk-group-select');
            const bulkGroupApply = document.getElementById('bulk-group-apply');
            const bulkWatchSelect = document.getElementById('bulk-watch-select');
            const bulkWatchApply = document.getElementById('bulk-watch-apply');
            const clearBtn = document.getElementById('clear-selection-btn');

            if (bulkGroupSelect) bulkGroupSelect.disabled = !hasSelection;
            if (bulkGroupApply) bulkGroupApply.disabled = !hasSelection;
            if (bulkWatchSelect) bulkWatchSelect.disabled = !hasSelection;
            if (bulkWatchApply) bulkWatchApply.disabled = !hasSelection;
            if (clearBtn) clearBtn.disabled = !hasSelection;
        }

        function clearSelection() {
            selectedMacs.clear();
            lastSelectedIndex = null;
            renderDevices();
        }

        function toggleSelectAllVisible() {
            if (!currentVisibleDevices || currentVisibleDevices.length === 0) return;
            const allSelected = currentVisibleDevices.every(d => selectedMacs.has(d.mac));
            if (allSelected) {
                currentVisibleDevices.forEach(d => selectedMacs.delete(d.mac));
            } else {
                currentVisibleDevices.forEach(d => selectedMacs.add(d.mac));
            }
            renderDevices();
        }

        function toggleRowCheckbox(event, mac, index) {
            event.stopPropagation();
            if (event.target.checked) {
                selectedMacs.add(mac);
            } else {
                selectedMacs.delete(mac);
            }
            lastSelectedIndex = index;
            renderDevices();
        }

        function handleRowClick(event, mac, index) {
            if (event.target && event.target.closest('input.row-select-checkbox')) return;
            const isCtrl = event.ctrlKey || event.metaKey;
            const isShift = event.shiftKey;

            if (isShift && lastSelectedIndex !== null && currentVisibleDevices.length > 0) {
                const start = Math.max(0, Math.min(lastSelectedIndex, index));
                const end = Math.min(currentVisibleDevices.length - 1, Math.max(lastSelectedIndex, index));
                if (!isCtrl) selectedMacs.clear();
                for (let i = start; i <= end; i++) {
                    selectedMacs.add(currentVisibleDevices[i].mac);
                }
            } else if (isCtrl) {
                if (selectedMacs.has(mac)) {
                    selectedMacs.delete(mac);
                } else {
                    selectedMacs.add(mac);
                }
            } else {
                if (selectedMacs.has(mac)) {
                    selectedMacs.delete(mac);
                } else {
                    selectedMacs.clear();
                    selectedMacs.add(mac);
                }
            }

            lastSelectedIndex = index;
            // Delay renderDevices so the dblclick event can fire on the original
            // <tr> element before innerHTML replaces it. Without this delay,
            // the first click destroys the row and dblclick never fires.
            if (rowClickTimer) clearTimeout(rowClickTimer);
            rowClickTimer = setTimeout(() => { rowClickTimer = null; renderDevices(); }, 250);
        }

        function getContrastColor(hexColor) {
            if (!hexColor) return 'var(--text-primary)';
            // Remove # if present
            const hex = hexColor.replace('#', '');
            // Parse RGB values
            const r = parseInt(hex.substr(0, 2), 16);
            const g = parseInt(hex.substr(2, 2), 16);
            const b = parseInt(hex.substr(4, 2), 16);
            // Calculate relative luminance
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            // Return black for light backgrounds, white for dark
            return luminance > 0.5 ? '#000000' : '#ffffff';
        }

        function renderDevices() {
            const tbody = document.getElementById('device-list');
            const sourceDevices = dateFilteredDevices !== null ? dateFilteredDevices : allDevices;
            let visibleDevices = sourceDevices;

            if (dateFilteredDevices !== null) {
                const searchTerm = document.getElementById('search').value.toLowerCase();
                visibleDevices = sourceDevices.filter(d => {
                    if (currentFilter === 'watched') {
                        if (!d.watched) return false;
                    } else if (currentFilter === 'laptop') {
                        if (d.device_type !== 'laptop' && d.device_type !== 'computer') return false;
                    } else if (currentFilter !== 'all' && d.device_type !== currentFilter) {
                        return false;
                    }
                    if (searchTerm) {
                        const searchable = [d.mac, d.vendor, d.friendly_name].join(' ').toLowerCase();
                        if (!searchable.includes(searchTerm)) return false;
                    }
                    return true;
                });
                visibleDevices = applySort(visibleDevices);
                document.getElementById('visible-count').textContent = visibleDevices.length;
            } else {
                document.getElementById('visible-count').textContent = pagination.totalMatching || visibleDevices.length;
            }

            currentVisibleDevices = visibleDevices;

            if (visibleDevices.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-muted);">No targets match criteria</td></tr>';
                updateSelectionUI();
                return;
            }

            tbody.innerHTML = visibleDevices.map((d, index) => {
                const typeClass = getTypeClass(d.device_type);
                const { text: lastSeen, tooltip: lastSeenTooltip } = formatLastSeen(d.last_seen);
                const isRecent = isRecentlySeen(d.last_seen);
                const watchedStar = d.watched ? '<span class="watched-star">★</span>' : '';
                const isSelected = selectedMacs.has(d.mac);
                const rowClass = isSelected ? 'selected' : '';
                const checkedAttr = isSelected ? 'checked' : '';

                // Build group pill HTML -- clickable, jumps into that
                // category's list view (same as clicking it in the sidebar).
                let groupHtml = '—';
                if (d.group_name && d.group_color) {
                    const textColor = getContrastColor(d.group_color);
                    groupHtml = '<span onclick="event.stopPropagation(); selectCategory(' + d.group_id + ');" style="cursor: pointer; background: ' + d.group_color + '; color: ' + textColor + '; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.7rem; font-weight: 500;" title="View this category">' + obfuscateName(d.group_name) + '</span>';
                } else if (d.group_name) {
                    groupHtml = '<span onclick="event.stopPropagation(); selectCategory(' + d.group_id + ');" style="cursor: pointer; background: var(--bg-tertiary); color: var(--text-secondary); padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.7rem;" title="View this category">' + obfuscateName(d.group_name) + '</span>';
                }

                if (compactView) {
                    // Compact: Type, Name/MAC, Sightings, Last Seen, Group
                    const rawDisplayName = d.friendly_name || d.vendor || d.mac;
                    let displayName = d.friendly_name ? obfuscateName(rawDisplayName) : (d.vendor ? rawDisplayName : obfuscateMAC(rawDisplayName));
                    if (d.identity_mac_count > 1) {
                        displayName += ' <span class="identity-badge" title="' + d.identity_mac_count + ' MAC addresses clustered as one device (rotation)">×' + d.identity_mac_count + '</span>';
                    }
                    // Truncate long macOS UUID addresses in compact view
                    if (!d.friendly_name && !d.vendor && isMacOSUUID(d.mac)) {
                        displayName = displayName.substring(0, 13) + '...';
                    }
                    return '<tr class="' + rowClass + '" draggable="true" ondragstart="onDeviceDragStart(event, \\'' + d.mac + '\\')" onclick="handleRowClick(event, \\'' + d.mac + '\\', ' + index + ')" ondblclick="showDevice(\\'' + d.mac + '\\')" style="height: auto;">' +
                        '<td class="select-col"><input type="checkbox" class="row-select-checkbox" ' + checkedAttr + ' onclick="toggleRowCheckbox(event, \\'' + d.mac + '\\', ' + index + ')"></td>' +
                        '<td style="padding: 0.4rem 0.5rem;"><span class="type-badge ' + typeClass + '" style="font-size: 0.65rem; padding: 0.15rem 0.4rem;">' + watchedStar + d.type_icon + '</span></td>' +
                        '<td colspan="3" style="padding: 0.4rem 0.5rem; font-size: 0.75rem;">' + displayName + '</td>' +
                        '<td style="padding: 0.4rem 0.5rem; font-size: 0.7rem;">' + (d.last_rssi != null ? d.last_rssi + ' dBm' : '—') + '</td>' +
                        '<td style="padding: 0.4rem 0.5rem; font-size: 0.7rem;">' + d.total_sightings + '</td>' +
                        '<td style="padding: 0.4rem 0.5rem; font-size: 0.7rem;" class="' + (isRecent ? 'recent' : '') + '" title="Last seen: ' + lastSeenTooltip + (d.first_seen ? ' \\u2022 First seen: ' + new Date(d.first_seen).toLocaleString() : '') + '">' + lastSeen + '</td>' +
                        '<td style="padding: 0.4rem 0.5rem; font-size: 0.7rem;">' + groupHtml + '</td>' +
                        '</tr>';
                }

                return '<tr class="' + rowClass + '" draggable="true" ondragstart="onDeviceDragStart(event, \\'' + d.mac + '\\')" onclick="handleRowClick(event, \\'' + d.mac + '\\', ' + index + ')" ondblclick="showDevice(\\'' + d.mac + '\\')">' +
                    '<td class="select-col"><input type="checkbox" class="row-select-checkbox" ' + checkedAttr + ' onclick="toggleRowCheckbox(event, \\'' + d.mac + '\\', ' + index + ')"></td>' +
                    '<td><span class="type-badge ' + typeClass + '">' + watchedStar + d.type_icon + ' ' + d.type_label + '</span></td>' +
                    '<td class="vendor-name">' + (d.vendor ? obfuscateName(d.vendor) : '—') + '</td>' +
                    '<td class="mac-addr" title="' + d.mac + '">' + (isMacOSUUID(d.mac) ? obfuscateMAC(d.mac).substring(0, 13) + '...' : obfuscateMAC(d.mac)) +
                    (d.name_conflict_at ? ' <span class="name-conflict-badge" style="color: var(--accent-red, #dc2626);" title="Possible spoofing: this MAC previously advertised a different name (now: ' + escapeHtml(d.name_conflict_name || '') + ')">⚠</span>' : '') +
                    '</td>' +
                    '<td class="device-name">' + (d.friendly_name ? obfuscateName(d.friendly_name) : '—') +
                    (d.identity_mac_count > 1 ? ' <span class="identity-badge" title="' + d.identity_mac_count + ' MAC addresses clustered as one device (rotation)">×' + d.identity_mac_count + '</span>' : '') +
                    '</td>' +
                    '<td class="rssi-value">' + (d.last_rssi != null ? d.last_rssi + ' dBm' : '—') + '</td>' +
                    '<td class="sighting-count">' + d.total_sightings + '</td>' +
                    '<td class="last-seen ' + (isRecent ? 'recent' : '') + '" title="Last seen: ' + lastSeenTooltip + (d.first_seen ? ' \\u2022 First seen: ' + new Date(d.first_seen).toLocaleString() : '') + '">' + lastSeen + '</td>' +
                    '<td class="group-name">' + groupHtml + '</td>' +
                    '</tr>';
            }).join('');
            updateSelectionUI();
        }

        function getTypeClass(type) {
            const classes = { phone: 'type-phone', laptop: 'type-laptop', computer: 'type-laptop', tablet: 'type-phone', smart: 'type-smart', audio: 'type-audio', speaker: 'type-audio', watch: 'type-watch', wearable: 'type-watch', tv: 'type-tv', vehicle: 'type-vehicle' };
            return classes[type] || 'type-unknown';
        }

        function formatLastSeen(isoString) {
            if (!isoString) return { text: '—', tooltip: '' };
            const date = new Date(isoString);
            const now = new Date();
            const tooltip = date.toLocaleString();
            const diffMins = Math.floor((now - date) / 60000);
            let text;
            if (diffMins < 1) text = 'NOW';
            else if (diffMins < 60) text = diffMins + 'm ago';
            else if (diffMins < 1440) {
                const h = Math.floor(diffMins / 60);
                const m = diffMins % 60;
                text = m > 0 ? h + 'h ' + m + 'm ago' : h + 'h ago';
            } else {
                const diffDays = Math.floor(diffMins / 1440);
                if (diffDays === 1) text = 'Yesterday ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                else if (diffDays < 7) text = diffDays + 'd ago';
                else text = date.toLocaleDateString();
            }
            return { text, tooltip };
        }

        function isRecentlySeen(isoString) {
            if (!isoString) return false;
            return (new Date() - new Date(isoString)) < 600000;
        }

        async function showDevice(mac) {
            // Cancel any pending single-click re-render so it doesn't
            // disrupt the modal that the double-click is about to open.
            if (rowClickTimer) { clearTimeout(rowClickTimer); rowClickTimer = null; }
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac));
                const data = await response.json();
                renderModal(data);
                document.getElementById('device-modal').classList.add('active');
            } catch (error) { console.error('Error:', error); }
        }

        let currentDeviceMac = null;
        let liveSignalPollTimer = null;

        function renderModal(data) {
            const d = data.device;
            currentDeviceMac = d.mac;
            const content = document.getElementById('modal-content');

            const proximityColors = { immediate: '#16a34a', near: '#d97706', far: '#ea580c', remote: '#dc2626', unknown: '#555' };
            const proximityZone = data.proximity_zone || 'unknown';
            const proximityColor = proximityColors[proximityZone] || '#555';

            const watchBtn = document.getElementById('watch-btn');
            if (watchBtn) {
                watchBtn.textContent = d.watched ? '★ Watching' : '☆ Watch';
                watchBtn.className = d.watched ? 'btn btn-watch active' : 'btn btn-watch';
            }
            const scanBtn = document.getElementById('scan-unit-btn');
            if (scanBtn) { scanBtn.disabled = false; scanBtn.textContent = 'Scan Unit'; }

            content.innerHTML = '<div class="detail-grid">' +
                '<div class="detail-item"><div class="detail-label">Address</div><div class="detail-value mono" style="font-size:' + (isMacOSUUID(d.mac) ? '0.65rem' : '0.85rem') + '; word-break: break-all;">' + obfuscateMAC(d.mac) + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">Identifier' + (d.identity_mac_count > 1 ? ' <span class="identity-badge" title="' + d.identity_mac_count + ' MAC addresses clustered as one device (rotation)">×' + d.identity_mac_count + '</span>' : '') + '</div><input class="form-input" id="device-identifier" value="' + escapeHtml(d.friendly_name || '') + '" placeholder="No identifier -- set manually" style="font-size: 0.85rem;" onchange="setDeviceName(\\'' + d.mac + '\\', this.value)"></div>' +
                (d.name_conflict_at ? '<div class="detail-item full" style="border-color: var(--accent-red, #dc2626);"><div class="detail-label" style="color: var(--accent-red, #dc2626);">⚠ Possible Spoofing</div><div class="detail-value">This MAC previously advertised a different name. Now seen as: "' + escapeHtml(d.name_conflict_name || '') + '" (at ' + new Date(d.name_conflict_at).toLocaleString() + ')</div></div>' : '') +
                '<div class="detail-item"><div class="detail-label">Type</div><select class="form-input" id="device-type" onchange="setDeviceType(\\'' + d.mac + '\\', this.value)" style="font-size: 0.8rem;"></select></div>' +
                '<div class="detail-item"><div class="detail-label">Vendor OUI</div><input class="form-input" id="device-vendor" value="' + escapeHtml(d.vendor || '') + '" placeholder="Unknown -- set manually" style="font-size: 0.85rem;" onchange="setDeviceVendor(\\'' + d.mac + '\\', this.value)"></div>' +
                '<div class="detail-item"><div class="detail-label">Proximity</div><div class="detail-value" style="color: ' + proximityColor + '; ">' + proximityZone + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">Sightings</div><div class="detail-value highlight">' + d.total_sightings + '</div></div>' +
                appleActivityHtml(d) +
                samsungStatusHtml(d) +
                fastpairBatteryHtml(d) +
                droneStateHtml(d) +
                '<div class="detail-item"' + (d.identity_mac_count > 1 && d.identity_first_seen ? ' title="Earliest sighting across all ' + d.identity_mac_count + ' rotated addresses clustered under this identity"' : '') + '><div class="detail-label">First seen</div><div class="detail-value mono">' + (d.identity_mac_count > 1 && d.identity_first_seen ? new Date(d.identity_first_seen).toLocaleString() : (d.first_seen ? new Date(d.first_seen).toLocaleString() : '—')) + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">Last seen</div><div class="detail-value mono">' + (d.last_seen ? new Date(d.last_seen).toLocaleString() : '—') + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">Activity Pattern</div><div class="detail-value">' + (data.pattern || 'Insufficient data') + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">BLE Services</div><div class="detail-value mono" style="font-size:0.75rem;">' + (data.uuid_names && data.uuid_names.length > 0 ? data.uuid_names.join(', ') : '—') + '</div></div>' +
                '<div class="detail-item full"><div class="detail-label">Assign to Group</div><select class="form-input" id="device-group" onchange="setDeviceGroup(\\'' + d.mac + '\\', this.value)" style="font-size: 0.8rem;"><option value="">No group</option></select></div>' +
                '<div class="detail-item full"><div class="detail-label">Notes</div><textarea class="form-input" id="device-notes" rows="2" style="font-size: 0.8rem; resize: vertical;" placeholder="Add notes...">' + (d.notes || '') + '</textarea><button class="btn" style="margin-top: 0.35rem; padding: 0.3rem 0.6rem; display: block;" onclick="saveNotes(\\'' + d.mac + '\\')">Save Notes</button></div>' +
                '</div>' +
                '<div class="heatmap-grid-2col">' +
                '<div class="heatmap-section" id="live-signal-section">' +
                '<div class="heatmap-title">Live Signal</div>' +
                '<div class="rssi-chart" id="live-signal-chart" style="height: 90px;"></div>' +
                '<div style="display: flex; justify-content: space-between; align-items: baseline; font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">' +
                '<span style="display: flex; align-items: baseline; gap: 0.3rem;"><span id="live-signal-rssi" style="font-weight: 400; color: var(--text-primary);">—</span><span id="live-signal-trend" style="font-family: monospace; font-weight: 700;"></span><span id="live-signal-avg">avg —</span></span>' +
                '<span id="live-signal-footer">first — · last —</span>' +
                '</div>' +
                '<div style="margin-top: 0.35rem;">' +
                '<div style="display: flex; justify-content: space-between; font-size: 0.65rem; color: var(--text-muted); margin-bottom: 0.15rem;">' +
                '<span>Presence (last 15 min)</span><span id="live-signal-presence-pct">0%</span>' +
                '</div>' +
                '<div id="live-signal-presence-track" style="height: 10px;"></div>' +
                '</div></div>' +
                '<div class="heatmap-section" id="rssi-section">' +
                '<div class="heatmap-title">Signal History (7d)</div>' +
                '<div class="rssi-chart" id="rssi-chart" style="height: 90px;"><div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding-top: 1.5rem;">Loading...</div></div>' +
                '</div>' +
                '</div>' +
                '<div class="heatmap-section" id="scan-unit-section" hidden>' +
                '<div class="heatmap-title">Scan Unit Result</div>' +
                '<div id="scan-unit-result" style="font-size: 0.75rem; font-family: monospace; white-space: pre-wrap; word-break: break-all; max-height: 300px; overflow-y: auto;"></div>' +
                '</div>' +
                '<div class="heatmap-grid-2col">' +
                '<div class="heatmap-section">' +
                '<div class="heatmap-title">Time Nearby (30d)</div>' +
                '<div id="dwell-stats" class="heatmap" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;"><div style="color: var(--text-muted);">Loading...</div></div>' +
                '</div>' +
                '<div class="heatmap-section">' +
                '<div class="heatmap-title">Daily Activity</div>' +
                '<div class="heatmap">' + renderDailyHeatmap(data.daily_data) + '</div>' +
                '</div>' +
                '<div class="heatmap-section">' +
                '<div class="heatmap-title">Hourly Activity (30d)</div>' +
                '<div class="heatmap">' + renderHourlyHeatmap(data.hourly_data) + '</div>' +
                '</div>' +
                '<div class="heatmap-section">' +
                '<div class="heatmap-title">Timeline (30d)</div>' +
                renderTimeline(data.timeline) +
                '</div>' +
                '</div>' +
                (d.identity_id ? (
                    '<div class="heatmap-section">' +
                    '<div class="heatmap-title">Linked Addresses (' + (d.identity_mac_count || 1) + ')</div>' +
                    '<div id="identity-macs" class="heatmap">Loading...</div>' +
                    '</div>'
                ) : '') +
                '';

            loadRssiChart(d.mac);
            startLiveSignalPolling(d.mac);
            loadDwellStats(d.mac);
            loadGroupsForDevice(d.group_id);
            loadDeviceTypes(d.device_type);
            if (d.identity_id) loadIdentityMacs(d.identity_id, d.mac);
        }

        async function loadIdentityMacs(identityId, currentMac) {
            const el = document.getElementById('identity-macs');
            if (!el) return;
            try {
                const res = await fetch('/api/identity/' + identityId + '/macs');
                const data = await res.json();
                el.innerHTML = (data.macs || []).map(m =>
                    '<div style="display:flex; justify-content:space-between; align-items:center; padding:0.3rem 0; border-bottom:1px solid var(--border-color); font-size:0.75rem; gap:0.5rem;">' +
                    '<span class="mono">' + m.mac + (m.mac === currentMac ? ' (current)' : '') + '</span>' +
                    '<span style="color:var(--text-muted);">first ' + (m.first_seen ? new Date(m.first_seen).toLocaleString() : '—') + '</span>' +
                    '<span style="color:var(--text-muted);">last ' + (m.last_seen ? new Date(m.last_seen).toLocaleString() : '—') + '</span>' +
                    '<span style="color:var(--text-muted);">' + m.total_sightings + ' sightings</span>' +
                    '<button class="btn" style="padding:0.1rem 0.4rem; font-size:0.65rem;" onclick="unmergeAndRefresh(\\'' + m.mac + '\\')">Unmerge</button>' +
                    '</div>'
                ).join('');
            } catch (e) {
                el.textContent = 'Failed to load';
            }
        }

        async function unmergeAndRefresh(mac) {
            await fetch('/api/device/' + encodeURIComponent(mac) + '/unmerge', { method: 'POST' });
            await refreshDevices();
            showDevice(mac);
        }

        let cachedGroups = [];

        async function loadGroupsForDevice(currentGroupId) {
            const select = document.getElementById('device-group');
            if (!select) return;

            // Use cached groups if available
            if (cachedGroups.length === 0) {
                try {
                    const response = await fetch('/api/groups');
                    const data = await response.json();
                    cachedGroups = data.groups || [];
                } catch (error) { return; }
            }

            select.innerHTML = '<option value="">No group</option>' +
                cachedGroups.map(g => '<option value="' + g.id + '"' + (g.id === currentGroupId ? ' selected' : '') + '>' + groupOptionLabel(g) + '</option>').join('');
        }

        async function loadGroupsForBulkSelect() {
            const select = document.getElementById('bulk-group-select');
            if (!select) return;

            if (cachedGroups.length === 0) {
                try {
                    const response = await fetch('/api/groups');
                    const data = await response.json();
                    cachedGroups = data.groups || [];
                } catch (error) {
                    return;
                }
            }

            select.innerHTML = '<option value="">Assign group...</option>' +
                '<option value="__none__">No group</option>' +
                cachedGroups.map(g => '<option value="' + g.id + '">' + groupOptionLabel(g) + '</option>').join('');
        }

        async function setDeviceVendor(mac, vendor) {
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/vendor', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ vendor: vendor })
                });
                refreshDevices();
            } catch (error) { console.error('Error setting vendor:', error); }
        }

        async function setDeviceName(mac, name) {
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/name', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                refreshDevices();
            } catch (error) { console.error('Error setting identifier:', error); }
        }

        async function scanUnit(mac) {
            const btn = document.getElementById('scan-unit-btn');
            const section = document.getElementById('scan-unit-section');
            const result = document.getElementById('scan-unit-result');
            btn.disabled = true;
            btn.textContent = 'Scanning...';
            section.hidden = false;
            result.textContent = 'Actively contacting device, this may take up to 30 seconds (longer if the adapter is mid-scan and needs a retry)...';
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/scan', { method: 'POST' });
                const data = await response.json();
                if (!data.ok) {
                    result.textContent = 'Scan failed: ' + (data.error || 'unknown error');
                } else if (data.bt_type === 'classic' || data.records) {
                    if (!data.records || data.records.length === 0) {
                        result.textContent = 'Connected, but no SDP service records advertised.';
                    } else {
                        result.textContent = data.records.map((r, i) =>
                            'Service ' + (i + 1) + ':\\n' +
                            Object.entries(r).map(([k, v]) => '  ' + k + ': ' + v).join('\\n')
                        ).join('\\n\\n');
                    }
                } else {
                    let lines = [];
                    if (data.device_info && Object.keys(data.device_info).length > 0) {
                        lines.push('Device Information:');
                        for (const [k, v] of Object.entries(data.device_info)) {
                            lines.push('  ' + k + ': ' + v);
                        }
                        lines.push('');
                    }
                    lines.push('GATT Services (' + data.services.length + '):');
                    for (const svc of data.services) {
                        lines.push('  ' + svc.uuid + (svc.description ? ' (' + svc.description + ')' : ''));
                        for (const c of svc.characteristics) {
                            lines.push('    ' + c.uuid + ' [' + c.properties.join(', ') + ']' + (c.value ? ' = ' + c.value : ''));
                        }
                    }
                    result.textContent = lines.join('\\n');
                }

                if (data.applied && Object.keys(data.applied).length > 0) {
                    const appliedLines = ['Auto-filled from scan (fields that were empty):'];
                    for (const [k, v] of Object.entries(data.applied)) {
                        appliedLines.push('  ' + k + ': ' + v);
                    }
                    result.textContent = appliedLines.join('\\n') + '\\n\\n' + result.textContent;
                }

                if (data.ok) {
                    // Re-fetch the device from scratch rather than trust
                    // the scan response's partial "applied" set -- this
                    // guarantees the visible Type/Vendor/Identifier fields
                    // always match what actually landed in the database,
                    // with no separate save step for the operator.
                    try {
                        const freshResp = await fetch('/api/device/' + encodeURIComponent(mac));
                        const fresh = await freshResp.json();
                        const d = fresh.device;
                        const vendorInput = document.getElementById('device-vendor');
                        if (vendorInput) vendorInput.value = d.vendor || '';
                        const idInput = document.getElementById('device-identifier');
                        if (idInput) idInput.value = d.friendly_name || '';
                        await loadDeviceTypes(d.device_type);
                    } catch (e) { /* non-fatal -- scan result itself still shown */ }
                    refreshDevices();
                }
            } catch (error) {
                result.textContent = 'Scan failed: ' + error;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Scan Unit';
            }
        }

        let cachedDeviceTypes = [];

        async function loadDeviceTypes(currentType) {
            const select = document.getElementById('device-type');
            if (!select) return;

            if (cachedDeviceTypes.length === 0) {
                try {
                    const response = await fetch('/api/device-types');
                    const data = await response.json();
                    cachedDeviceTypes = data.types || [];
                } catch (error) { return; }
            }

            select.innerHTML = cachedDeviceTypes.map(t =>
                '<option value="' + t.value + '"' + (t.value === currentType ? ' selected' : '') + '>' + t.icon + ' ' + t.label + '</option>'
            ).join('');
        }

        async function setDeviceType(mac, deviceType) {
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/type', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_type: deviceType })
                });
                refreshDevices();
            } catch (error) { console.error('Error setting device type:', error); }
        }

        async function setDeviceGroup(mac, groupId) {
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/group', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ group_id: groupId ? parseInt(groupId) : null })
                });
                refreshDevices();
            } catch (error) { console.error('Error setting group:', error); }
        }

        async function applyBulkMerge() {
            const macs = Array.from(selectedMacs);
            if (macs.length < 2) {
                alert('Select at least 2 devices to merge as one.');
                return;
            }
            const deviceMap = new Map(allDevices.map(d => [d.mac, d]));
            const names = new Set(macs.map(m => (deviceMap.get(m) || {}).friendly_name).filter(Boolean));
            let name;
            if (names.size === 1) {
                name = [...names][0];
            } else {
                name = prompt(
                    names.size > 1
                        ? 'Selected devices have different names (' + [...names].join(', ') + '). Name for the merged device:'
                        : 'Name for the merged device:',
                    ''
                );
                if (!name) return;
            }
            try {
                await fetch('/api/devices/merge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ macs, name }),
                });
                clearSelection();
                await refreshDevices();
            } catch (error) {
                console.error('Error merging devices:', error);
            }
        }

        async function applyBulkGroup() {
            const select = document.getElementById('bulk-group-select');
            if (!select || !select.value) return;
            if (selectedMacs.size === 0) return;

            const groupValue = select.value;
            const groupId = groupValue === '__none__' ? null : parseInt(groupValue);
            const macs = Array.from(selectedMacs);

            try {
                await Promise.all(macs.map(mac =>
                    fetch('/api/device/' + encodeURIComponent(mac) + '/group', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ group_id: groupId })
                    })
                ));
                refreshDevices();
            } catch (error) {
                console.error('Error applying bulk group:', error);
            }
        }

        async function applyBulkWatch() {
            const select = document.getElementById('bulk-watch-select');
            if (!select || !select.value) return;
            if (selectedMacs.size === 0) return;

            const desired = select.value;
            const deviceMap = new Map(allDevices.map(d => [d.mac, d]));
            const macs = Array.from(selectedMacs);
            const requests = [];

            macs.forEach(mac => {
                const device = deviceMap.get(mac);
                if (!device) return;
                if (desired === 'on' && !device.watched) {
                    requests.push(fetch('/api/device/' + encodeURIComponent(mac) + '/watch', { method: 'POST' }));
                }
                if (desired === 'off' && device.watched) {
                    requests.push(fetch('/api/device/' + encodeURIComponent(mac) + '/watch', { method: 'POST' }));
                }
            });

            try {
                await Promise.all(requests);
                refreshDevices();
            } catch (error) {
                console.error('Error applying bulk watch:', error);
            }
        }

        async function loadDwellStats(mac) {
            const container = document.getElementById('dwell-stats');
            if (!container) return;
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/dwell?days=30');
                const data = await response.json();
                container.innerHTML =
                    '<div class="dwell-stat-card"><div class="dwell-stat-value" style="color: var(--accent-amber);">' + Math.round(data.total_minutes) + '</div><div class="dwell-stat-label">TOTAL MIN</div></div>' +
                    '<div class="dwell-stat-card"><div class="dwell-stat-value" style="color: var(--accent-green);">' + data.session_count + '</div><div class="dwell-stat-label">SESSIONS</div></div>' +
                    '<div class="dwell-stat-card"><div class="dwell-stat-value" style="color: var(--accent-blue);">' + Math.round(data.avg_session_minutes) + '</div><div class="dwell-stat-label">AVG MIN</div></div>' +
                    '<div class="dwell-stat-card"><div class="dwell-stat-value" style="color: var(--accent-red);">' + Math.round(data.longest_session_minutes) + '</div><div class="dwell-stat-label">LONGEST</div></div>';
            } catch (error) {
                container.innerHTML = '<div style="color: var(--text-muted);">Error loading data</div>';
            }
        }

        let correlationMac = null;

        function reloadCorrelated() {
            if (correlationMac) loadCorrelatedDevices(correlationMac);
        }

        async function loadCorrelatedDevices(mac) {
            correlationMac = mac;
            const container = document.getElementById('correlated-devices');
            if (!container) return;
            const gapEl = document.getElementById('corr-gap');
            const edgeEl = document.getElementById('corr-edge');
            const gap = Math.max(1, parseInt(gapEl && gapEl.value) || 15);
            const edge = Math.max(1, parseInt(edgeEl && edgeEl.value) || 5);
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/correlation?days=30&gap=' + gap + '&edge=' + edge);
                const data = await response.json();
                if (!data.correlated_devices || data.correlated_devices.length === 0) {
                    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.75rem;">No correlated devices found</div>';
                    return;
                }
                container.innerHTML = data.correlated_devices.slice(0, 5).map(c => {
                    const rawPrimaryName = c.friendly_name || c.vendor || 'Unknown';
                    const primaryName = c.friendly_name ? obfuscateName(rawPrimaryName) : rawPrimaryName;
                    const rawSecondaryInfo = c.friendly_name ? (c.vendor || c.mac) : c.mac;
                    const secondaryInfo = (c.friendly_name && c.vendor) ? rawSecondaryInfo : obfuscateMAC(rawSecondaryInfo);
                    const corrBar = '<div style="background: var(--accent-red); height: 4px; width: ' + c.correlation_score + '%; border-radius: 2px;"></div>';
                    const syncedEdges = (c.synced_arrivals || 0) + (c.synced_departures || 0);
                    const syncLine = syncedEdges > 0
                        ? '<div style="font-size: 0.65rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">⇄ ' + (c.synced_arrivals || 0) + ' arrivals / ' + (c.synced_departures || 0) + ' departures in sync</div>'
                        : '';
                    const corrTitle = 'Correlation ' + c.correlation_score + '% (co-presence ' + (c.cooccurrence_score != null ? c.cooccurrence_score : 0) + '%, transition sync ' + (c.transition_score != null ? c.transition_score : 0) + '%)';
                    return '<div title="' + corrTitle + '" style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color); cursor: pointer;" onclick="showDevice(\\'' + c.mac + '\\')">' +
                        '<div style="flex: 1; min-width: 0;">' +
                        '<div style="font-size: 0.8rem; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">' + primaryName + '</div>' +
                        '<div style="font-size: 0.65rem; color: var(--text-muted); font-family: var(--font-mono); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">' + secondaryInfo + '</div>' +
                        syncLine +
                        '</div>' +
                        '<div style="display: flex; align-items: center; gap: 0.5rem; margin-left: 0.5rem;">' +
                        '<div style="width: 50px;">' + corrBar + '</div>' +
                        '<span style="font-size: 0.7rem; color: var(--accent-amber); min-width: 32px; text-align: right;">' + c.correlation_score + '%</span>' +
                        '</div></div>';
                }).join('');
            } catch (error) {
                container.innerHTML = '<div style="color: var(--text-muted);">Error loading data</div>';
            }
        }

        function formatPing(seconds) {
            if (seconds == null) return 'n/a';
            if (seconds >= 90) return '~' + Math.round(seconds / 60) + 'm';
            return '~' + Math.round(seconds) + 's';
        }

        async function loadRotationCandidates(mac) {
            const container = document.getElementById('rotation-candidates');
            if (!container) return;
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/rotation?days=7');
                const data = await response.json();
                const candidates = data.candidates || [];
                const t = data.target;
                let html = '';
                if (t) {
                    html += '<div style="font-size: 0.65rem; color: var(--text-muted); margin-bottom: 0.4rem;">This device: RSSI ' + t.mean_rssi + '±' + t.rssi_stddev + ' dBm · ping ' + formatPing(t.ping_interval_seconds) + '</div>';
                }
                if (candidates.length === 0) {
                    html += '<div style="color: var(--text-muted); font-size: 0.75rem;">No likely rotation siblings found</div>';
                    container.innerHTML = html;
                    return;
                }
                html += candidates.map(c => {
                    const rawPrimary = c.friendly_name || c.vendor || c.mac;
                    const primaryName = c.friendly_name ? obfuscateName(rawPrimary) : (c.vendor ? rawPrimary : obfuscateMAC(c.mac));
                    const overlapPct = Math.round((c.overlap_ratio || 0) * 100);
                    const detail = 'RSSI ' + c.mean_rssi + '±' + c.rssi_stddev + ' (Δ' + c.rssi_delta + ') · ping ' + formatPing(c.ping_interval_seconds) + ' · ' + overlapPct + '% overlap';
                    const nameBadge = c.name_match ? ' <span style="font-size: 0.6rem; color: var(--accent-amber); border: 1px solid var(--accent-amber); border-radius: 3px; padding: 0 0.25rem; vertical-align: middle;">name match</span>' : '';
                    const bar = '<div style="background: var(--accent-amber); height: 4px; width: ' + c.confidence + '%; border-radius: 2px;"></div>';
                    const title = 'Confidence ' + c.confidence + '% — ' + (c.name_match ? 'shares this device\\'s advertised name, plus ' : '') + 'similar signal strength, non-overlapping presence, similar ping cadence. Heuristic, not definitive.';
                    return '<div title="' + title + '" style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color); cursor: pointer;" onclick="showDevice(\\'' + c.mac + '\\')">' +
                        '<div style="flex: 1; min-width: 0;">' +
                        '<div style="font-size: 0.8rem; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">' + primaryName + nameBadge + '</div>' +
                        '<div style="font-size: 0.65rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">' + detail + '</div>' +
                        '</div>' +
                        '<div style="display: flex; align-items: center; gap: 0.5rem; margin-left: 0.5rem;">' +
                        '<div style="width: 50px;">' + bar + '</div>' +
                        '<span style="font-size: 0.7rem; color: var(--accent-amber); min-width: 32px; text-align: right;">' + c.confidence + '%</span>' +
                        '</div></div>';
                }).join('');
                container.innerHTML = html;
            } catch (error) {
                container.innerHTML = '<div style="color: var(--text-muted);">Error loading data</div>';
            }
        }

        async function saveNotes(mac) {
            const notes = document.getElementById('device-notes').value;
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/notes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: notes })
                });
            } catch (error) { console.error('Error:', error); }
        }

        function renderHourlyHeatmap(hourlyData) {
            if (!hourlyData || Object.keys(hourlyData).length === 0) return '<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding: 1rem 0;">No data</div>';
            var offset = -(new Date().getTimezoneOffset() / 60);
            var shifted = {};
            for (var h in hourlyData) {
                var localHour = ((parseInt(h) + offset) % 24 + 24) % 24;
                shifted[localHour] = (shifted[localHour] || 0) + hourlyData[h];
            }
            var max = Math.max(...Object.values(shifted), 1);
            var cells = '';
            var labels = '';
            for (var i = 0; i < 24; i++) {
                var count = shifted[i] || 0;
                var level = count === 0 ? 0 : Math.ceil((count / max) * 4);
                var label = i < 10 ? '0' + i : '' + i;
                cells += '<div class="activity-cell l' + level + '" title="' + label + ':00 — ' + count + ' sightings"></div>';
                labels += '<span>' + (i % 6 === 0 ? label : '') + '</span>';
            }
            return '<div class="activity-grid hourly">' + cells + '</div><div class="activity-labels hourly">' + labels + '</div>';
        }

        function renderDailyHeatmap(dailyData) {
            if (!dailyData || Object.keys(dailyData).length === 0) return '<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding: 1rem 0;">No data</div>';
            var days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            var max = Math.max(...Object.values(dailyData), 1);
            var cells = '';
            var labels = '';
            for (var d = 0; d < 7; d++) {
                var count = dailyData[d] || dailyData[String(d)] || 0;
                var level = count === 0 ? 0 : Math.ceil((count / max) * 4);
                cells += '<div class="activity-cell l' + level + '" title="' + days[d] + ' — ' + count + ' sightings"></div>';
                labels += '<span>' + days[d] + '</span>';
            }
            return '<div class="activity-grid daily">' + cells + '</div><div class="activity-labels daily">' + labels + '</div>';
        }

        function renderTimeline(timeline) {
            if (!timeline || timeline.length === 0) return '<div style="color: var(--text-muted); font-size: 0.75rem;">No data</div>';
            const maxCount = Math.max(...timeline.map(d => d.count));
            const bars = timeline.map(d => {
                const height = maxCount > 0 ? (d.count / maxCount * 100) : 0;
                const date = new Date(d.date);
                const tooltip = date.toLocaleDateString() + ': ' + d.count + ' sightings';
                return '<div class="timeline-bar" style="height: ' + height + '%" title="' + tooltip + '"></div>';
            }).join('');
            const firstDate = new Date(timeline[0].date);
            const lastDate = new Date(timeline[timeline.length - 1].date);
            const formatDate = (d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            return '<div class="timeline-chart">' + bars + '</div><div class="timeline-labels"><span>' + formatDate(firstDate) + '</span><span>' + formatDate(lastDate) + '</span></div>';
        }

        async function loadRssiChart(mac) {
            const container = document.getElementById('rssi-chart');
            if (!container) return;
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/rssi?days=7');
                const data = await response.json();
                if (!data.rssi_history || data.rssi_history.length < 2) {
                    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding-top: 1.5rem;">Insufficient data</div>';
                    return;
                }
                renderRssiChart(container, data.rssi_history);
            } catch (error) {
                container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding-top: 1.5rem;">Error</div>';
            }
        }

        function renderRssiChart(container, rssiData) {
            // The long-term counterpart to renderLiveSignalChart's fixed
            // -30/-100 live scale (Fieldwatch's own device-history views
            // use a similarly settled, gridded look, just auto-scaled to
            // this device's actual multi-day range rather than a fixed
            // live window -- no "current reading" dot or trend arrow here,
            // this is a static historical read, not a live one).
            const width = container.clientWidth - 20;
            const height = 50;
            const padding = { left: 30, right: 10, top: 6, bottom: 15 };
            const rssiValues = rssiData.map(d => d.rssi);
            const dataMin = Math.min(...rssiValues);
            const dataMax = Math.max(...rssiValues);
            // A little headroom so the line never touches the frame, then
            // snapped to 5 dBm so gridline labels land on round numbers.
            const minRssi = Math.floor((dataMin - 3) / 5) * 5;
            const maxRssi = Math.ceil((dataMax + 3) / 5) * 5;
            const range = (maxRssi - minRssi) || 10;
            const xScale = (i) => padding.left + (i / (rssiData.length - 1)) * (width - padding.left - padding.right);
            const yScale = (rssi) => padding.top + (1 - (rssi - minRssi) / range) * (height - padding.top - padding.bottom);
            const linePath = rssiData.map((d, i) => (i === 0 ? 'M' : 'L') + xScale(i) + ',' + yScale(d.rssi)).join(' ');
            const areaPath = linePath + ' L' + xScale(rssiData.length - 1) + ',' + (height - padding.bottom) + ' L' + padding.left + ',' + (height - padding.bottom) + ' Z';
            const firstTime = new Date(rssiData[0].timestamp);
            const lastTime = new Date(rssiData[rssiData.length - 1].timestamp);
            const formatTime = (d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            // 4 evenly-spaced horizontal gridlines across the device's own
            // observed range, plus 3 dashed vertical time dividers --
            // same "quartered grid" language as the live chart, just
            // scaled to this device's real history instead of a fixed
            // -30/-100 window.
            let grid = '';
            for (let i = 0; i <= 3; i++) {
                const dbm = Math.round(minRssi + range * i / 3);
                const y = yScale(dbm);
                grid += '<line x1="' + padding.left + '" y1="' + y + '" x2="' + width + '" y2="' + y + '" stroke="var(--border-color)" stroke-width="1" opacity="' + (i === 0 || i === 3 ? '1' : '0.6') + '" stroke-dasharray="' + (i === 0 || i === 3 ? 'none' : '3,4') + '"/>';
                grid += '<text x="2" y="' + (y + 3) + '" class="rssi-label" font-size="8">' + dbm + '</text>';
            }
            grid += '<line x1="' + padding.left + '" y1="' + padding.top + '" x2="' + padding.left + '" y2="' + (height - padding.bottom) + '" stroke="var(--border-color)" stroke-width="1.2"/>';
            for (let c = 1; c < 4; c++) {
                const x = padding.left + (width - padding.left - padding.right) * c / 4;
                grid += '<line x1="' + x + '" y1="' + padding.top + '" x2="' + x + '" y2="' + (height - padding.bottom) + '" stroke="var(--border-color)" stroke-width="0.75" stroke-dasharray="3,5" opacity="0.5"/>';
            }

            container.innerHTML = '<svg viewBox="0 0 ' + width + ' ' + height + '" preserveAspectRatio="none">' +
                '<defs><linearGradient id="rssiGradient" x1="0%" y1="0%" x2="0%" y2="100%">' +
                '<stop offset="0%" style="stop-color: #ffffff; stop-opacity: 0.25"/>' +
                '<stop offset="100%" style="stop-color: #ffffff; stop-opacity: 0.03"/>' +
                '</linearGradient></defs>' +
                grid +
                '<path class="rssi-area" d="' + areaPath + '"/>' +
                '<path class="rssi-line" d="' + linePath + '" style="stroke: #ffffff;"/>' +
                '<text class="rssi-label" x="' + padding.left + '" y="' + (height - 2) + '">' + formatTime(firstTime) + '</text>' +
                '<text class="rssi-label" x="' + (width - padding.right) + '" y="' + (height - 2) + '" text-anchor="end">' + formatTime(lastTime) + '</text>' +
                '</svg>';
        }

        async function toggleWatch(mac) {
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/watch', { method: 'POST' });
                const data = await response.json();
                const btn = document.getElementById('watch-btn');
                if (data.watched) {
                    btn.textContent = '★ Watching';
                    btn.className = 'btn btn-watch active';
                } else {
                    btn.textContent = '☆ Watch';
                    btn.className = 'btn btn-watch';
                }
                refreshDevices();
            } catch (error) { console.error('Error:', error); }
        }

        // Live Signal panel -- polls a short recent window while the
        // Device Details modal is open, for a Fieldwatch-style "signal
        // trend + presence" view (OffGridPete/Fieldwatch, MIT licensed,
        // reimplemented against BlueWatch's own sightings data). Started
        // from renderModal(), stopped from closeModal() so the timer
        // never outlives the modal it's updating.
        const LIVE_SIGNAL_WINDOW_MINUTES = 15;
        const LIVE_SIGNAL_POLL_MS = 1000;

        function startLiveSignalPolling(mac) {
            stopLiveSignalPolling();
            fetchAndRenderLiveSignal(mac);
            liveSignalPollTimer = setInterval(function() {
                if (mac !== currentDeviceMac) { stopLiveSignalPolling(); return; }
                fetchAndRenderLiveSignal(mac);
            }, LIVE_SIGNAL_POLL_MS);
        }

        function stopLiveSignalPolling() {
            if (liveSignalPollTimer) { clearInterval(liveSignalPollTimer); liveSignalPollTimer = null; }
        }

        function formatDurationCompact(seconds) {
            // "1h 10m" / "14s" style -- matches Fieldwatch's own
            // "first Xh Xm · last Xs" card footer.
            seconds = Math.max(0, Math.round(seconds));
            if (seconds < 60) return seconds + "s";
            const mins = Math.floor(seconds / 60);
            if (mins < 60) return mins + "m";
            const hrs = Math.floor(mins / 60);
            const remMins = mins % 60;
            return hrs + "h" + (remMins ? " " + remMins + "m" : "");
        }

        async function fetchAndRenderLiveSignal(mac) {
            const rssiEl = document.getElementById("live-signal-rssi");
            const trendEl = document.getElementById("live-signal-trend");
            const avgEl = document.getElementById("live-signal-avg");
            const footerEl = document.getElementById("live-signal-footer");
            const chartEl = document.getElementById("live-signal-chart");
            const pctEl = document.getElementById("live-signal-presence-pct");
            const trackEl = document.getElementById("live-signal-presence-track");
            if (!rssiEl) return; // modal closed mid-flight

            let data;
            try {
                const response = await fetch("/api/device/" + encodeURIComponent(mac) + "/live-signal?minutes=" + LIVE_SIGNAL_WINDOW_MINUTES);
                data = await response.json();
            } catch (error) {
                return; // transient -- next poll tick retries
            }
            if (mac !== currentDeviceMac) return; // modal switched devices while this was in flight

            if (data.current_rssi === null || data.current_rssi === undefined) {
                rssiEl.textContent = "—";
                rssiEl.style.color = "var(--text-muted)";
                if (trendEl) trendEl.textContent = "";
            } else {
                const rssi = data.current_rssi;
                rssiEl.textContent = rssi + " dBm";
                rssiEl.style.color = "#ffffff";
                if (trendEl) {
                    // Trend arrow: last sample vs. the average of the
                    // previous few -- same idea as Fieldwatch's RssiTrend
                    // (>>/>/=/</<<), just derived here instead of carried
                    // from the API. White throughout, matching the
                    // reference card exactly -- no quality-color coding.
                    const s = data.sightings || [];
                    if (s.length >= 4) {
                        const prevWindow = s.slice(-4, -1);
                        const prevAvg = prevWindow.reduce((a, x) => a + x.rssi, 0) / prevWindow.length;
                        const delta = rssi - prevAvg;
                        let mark = "=";
                        if (delta >= 8) mark = "»";
                        else if (delta >= 3) mark = "›";
                        else if (delta <= -8) mark = "«";
                        else if (delta <= -3) mark = "‹";
                        trendEl.textContent = mark;
                        trendEl.style.color = "#ffffff";
                    } else {
                        trendEl.textContent = "";
                    }
                }
            }

            if (pctEl) pctEl.textContent = (data.presence_pct || 0) + "%";
            if (trackEl) renderPresenceTrack(trackEl, data.sightings || [], LIVE_SIGNAL_WINDOW_MINUTES);

            const s = data.sightings || [];
            if (avgEl) {
                if (s.length) {
                    const avg = Math.round(s.reduce((a, x) => a + x.rssi, 0) / s.length);
                    avgEl.textContent = "avg " + avg;
                } else {
                    avgEl.textContent = "avg —";
                }
            }
            if (footerEl) {
                if (s.length) {
                    const firstTs = new Date(s[0].timestamp).getTime();
                    const firstAgo = (Date.now() - firstTs) / 1000;
                    const lastAgo = data.last_seen_seconds_ago;
                    footerEl.textContent = "first " + formatDurationCompact(firstAgo)
                        + " · last " + (lastAgo == null ? "—" : formatDurationCompact(lastAgo));
                } else {
                    footerEl.textContent = "no signal in the last " + LIVE_SIGNAL_WINDOW_MINUTES + " min";
                }
            }

            if (chartEl) {
                if (data.sightings && data.sightings.length >= 2) {
                    renderLiveSignalChart(chartEl, data.sightings);
                } else {
                    chartEl.innerHTML = '<div style="color: var(--text-muted); font-size: 0.7rem; text-align: center; padding-top: 1rem;">Not enough recent data yet</div>';
                }
            }
        }

        function renderLiveSignalChart(container, sightings) {
            const width = container.clientWidth - 20 || 200;
            const height = container.clientHeight || 64;
            const padding = { left: 28, right: 6, top: 8, bottom: 14 };
            // Fixed y-axis (unlike renderRssiChart's auto-scaled one) so the
            // chart doesn't visibly rescale/jitter on every 3s poll tick as
            // new points trickle in -- matches the -30/-50/-70/-100 dBm
            // scale and gridline layout of Fieldwatch's own Signal trend
            // graph (Sparkline() in its Widgets.kt).
            const minRssi = -100, maxRssi = -30;
            const majorTicks = [-30, -50, -70, -100];
            const minorTicks = [-40, -60, -80, -90];
            const xScale = (i) => padding.left + (i / (sightings.length - 1)) * (width - padding.left - padding.right);
            const yScale = (rssi) => {
                const clamped = Math.max(minRssi, Math.min(maxRssi, rssi));
                return padding.top + (1 - (clamped - minRssi) / (maxRssi - minRssi)) * (height - padding.top - padding.bottom);
            };
            const lastRssi = sightings[sightings.length - 1].rssi;
            const lineColor = "#ffffff";  // matches the reference card exactly -- no quality-color coding
            const linePath = sightings.map((s, i) => (i === 0 ? "M" : "L") + xScale(i) + "," + yScale(s.rssi)).join(" ");
            const areaPath = linePath + " L" + xScale(sightings.length - 1) + "," + (height - padding.bottom) + " L" + padding.left + "," + (height - padding.bottom) + " Z";

            let grid = "";
            majorTicks.forEach((dbm) => {
                const y = yScale(dbm);
                grid += '<line x1="' + padding.left + '" y1="' + y + '" x2="' + width + '" y2="' + y + '" stroke="var(--border-color)" stroke-width="1"/>';
                grid += '<text x="2" y="' + (y + 3) + '" class="rssi-label" font-size="8">' + dbm + "</text>";
            });
            minorTicks.forEach((dbm) => {
                const y = yScale(dbm);
                grid += '<line x1="' + padding.left + '" y1="' + y + '" x2="' + width + '" y2="' + y + '" stroke="var(--border-color)" stroke-width="0.75" stroke-dasharray="3,4" opacity="0.6"/>';
            });
            grid += '<line x1="' + padding.left + '" y1="' + yScale(-30) + '" x2="' + padding.left + '" y2="' + yScale(-100) + '" stroke="var(--border-color)" stroke-width="1.2"/>';
            // Three vertical dashed dividers across the time axis, same
            // "quartered" look as Fieldwatch's own gridlines.
            for (let c = 1; c < 4; c++) {
                const x = padding.left + (width - padding.left - padding.right) * c / 4;
                grid += '<line x1="' + x + '" y1="' + yScale(-30) + '" x2="' + x + '" y2="' + yScale(-100) + '" stroke="var(--border-color)" stroke-width="0.75" stroke-dasharray="3,5" opacity="0.5"/>';
            }

            const lastX = xScale(sightings.length - 1);
            const lastY = yScale(lastRssi);

            container.innerHTML = '<svg viewBox="0 0 ' + width + " " + height + '" preserveAspectRatio="none">' +
                '<defs><linearGradient id="liveSignalGradient" x1="0%" y1="0%" x2="0%" y2="100%">' +
                '<stop offset="0%" style="stop-color: ' + lineColor + '; stop-opacity: 0.3"/>' +
                '<stop offset="100%" style="stop-color: ' + lineColor + '; stop-opacity: 0.05"/>' +
                "</linearGradient></defs>" +
                grid +
                '<path class="rssi-area" d="' + areaPath + '" style="fill: url(#liveSignalGradient); stroke: none;"/>' +
                '<path class="rssi-line" d="' + linePath + '" style="stroke: ' + lineColor + ';"/>' +
                '<circle cx="' + lastX + '" cy="' + lastY + '" r="3.4" fill="' + lineColor + '"/>' +
                "</svg>";
        }

        function renderPresenceTrack(container, sightings, windowMinutes) {
            // Fieldwatch-style presence track (PresenceTrack() in its
            // Widgets.kt): actual time SPANS the device was present within
            // the window, not just a single aggregate percentage -- groups
            // consecutive sightings less than 45s apart (3x the poll
            // cadence) into one continuous span so brief gaps between
            // individual adverts don't fragment into dozens of slivers.
            const width = container.clientWidth || 260;
            const height = container.clientHeight || 16;
            if (!sightings.length) {
                container.innerHTML = '<svg viewBox="0 0 ' + width + " " + height + '"><rect width="' + width + '" height="' + height + '" rx="3" fill="var(--bg-tertiary)"/></svg>';
                return;
            }
            const windowMs = windowMinutes * 60 * 1000;
            const now = Date.now();
            const start = now - windowMs;
            const GAP_MS = 45000;
            const spans = [];
            let spanStart = null, prevTs = null;
            sightings.forEach((s) => {
                const ts = new Date(s.timestamp).getTime();
                if (spanStart === null) {
                    spanStart = ts;
                } else if (ts - prevTs > GAP_MS) {
                    spans.push([spanStart, prevTs]);
                    spanStart = ts;
                }
                prevTs = ts;
            });
            if (spanStart !== null) spans.push([spanStart, prevTs]);

            const xOf = (ts) => ((Math.max(start, Math.min(now, ts)) - start) / windowMs) * width;
            let bars = '<rect width="' + width + '" height="' + height + '" rx="3" fill="var(--bg-tertiary)"/>';
            spans.forEach(([a, b]) => {
                const x1 = xOf(a), x2 = xOf(b);
                const w = Math.max(2, x2 - x1);
                bars += '<rect x="' + x1 + '" y="' + (height * 0.15) + '" width="' + w + '" height="' + (height * 0.7) + '" rx="1.5" fill="var(--accent-blue)" opacity="0.85"/>';
            });
            container.innerHTML = '<svg viewBox="0 0 ' + width + " " + height + '" preserveAspectRatio="none">' + bars + "</svg>";
        }

        function closeModal() {
            stopLiveSignalPolling();
            document.getElementById('device-modal').classList.remove('active');
        }

        function csvField(val) {
            const s = String(val);
            if (s.includes(',') || s.includes('"') || s.includes('\\n')) {
                return '"' + s.replace(/"/g, '""') + '"';
            }
            return s;
        }

        document.querySelectorAll('.device-table th.sortable').forEach(th => {
            th.addEventListener('click', () => setSort(th.dataset.sort));
        });

        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', toggleSelectAllVisible);
        }

        document.getElementById('search').addEventListener('input', () => {
            if (dateFilteredDevices !== null) {
                renderDevices();
                return;
            }
            selectedMacs.clear();
            lastSelectedIndex = null;
            queueDeviceRefresh(true);
        });
        document.getElementById('device-modal').addEventListener('click', (e) => { if (e.target.id === 'device-modal') closeModal(); });
        document.getElementById('shortcuts-modal').addEventListener('click', (e) => { if (e.target.id === 'shortcuts-modal') closeShortcutsModal(); });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in input/textarea
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            const modalActive = document.getElementById('device-modal').classList.contains('active');

            if (e.key === 'Escape') {
                closeModal();
                closeShortcutsModal();
            } else if (e.key === 'r' || e.key === 'R') {
                // Refresh
                refreshDevices();
            } else if (e.key === '/') {
                // Focus search
                e.preventDefault();
                document.getElementById('search').focus();
            } else if (e.key === 'w' && modalActive && currentDeviceMac) {
                // Toggle watch on current device
                toggleWatch(currentDeviceMac);
            } else if (e.key === '1') {
                document.querySelector('[data-filter="all"]').click();
            } else if (e.key === '2') {
                document.querySelector('[data-filter="watched"]').click();
            } else if (e.key === '3') {
                document.querySelector('[data-filter="phone"]').click();
            } else if (e.key === '4') {
                document.querySelector('[data-filter="laptop"]').click();
            } else if (e.key === '5') {
                document.querySelector('[data-filter="audio"]').click();
            } else if (e.key === '?') {
                showShortcutsModal();
            }
        });

        function toDatetimeLocalValue(date) {
            const pad = n => String(n).padStart(2, '0');
            return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) +
                'T' + pad(date.getHours()) + ':' + pad(date.getMinutes());
        }

        (function initDateRangeDefaults() {
            const startEl = document.getElementById('search-start');
            const endEl = document.getElementById('search-end');
            if (!startEl || !endEl) return;
            const now = new Date();
            const anHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
            startEl.value = toDatetimeLocalValue(anHourAgo);
            endEl.value = toDatetimeLocalValue(now);
        })();

        (function initHideCategorized() {
            const classCb = document.getElementById('hide-classified-toggle');
            if (classCb) classCb.checked = hideClassified;
            const groupCb = document.getElementById('hide-grouped-toggle');
            if (groupCb) groupCb.checked = hideGrouped;
        })();

        updateViewToggle();
        updateSortIndicators();
        loadGroupsForBulkSelect();
        loadCategories();
        updateSelectionUI();
        updatePaginationUI();
        refreshDevices();
        setInterval(refreshDevices, 10000);
        loadPriorityDevices();
        setInterval(loadPriorityDevices, 10000);
        startLiveEventStream();
    </script>
</body>
</html>
"""

SETTINGS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BlueWatch</title>
    <style>
        :root {
            --bg-primary: #0d0d0d;
            --bg-secondary: #141414;
            --bg-tertiary: #1a1a1a;
            --bg-hover: #242424;
            --text-primary: #e0e0e0;
            --text-secondary: #888888;
            --text-muted: #555555;
            --accent-red: #2563eb;
            --accent-blue: #2563eb;
            --accent-green: #16a34a;
            --border-color: #2a2a2a;
            --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: var(--font-mono); background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; font-size: 13px; }

        .topbar { background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); padding: 0.5rem 1rem; display: flex; justify-content: space-between; align-items: center; }
        .topbar-left { display: flex; align-items: center; gap: 1.5rem; }
        .brand { display: flex; align-items: center; gap: 0.5rem; text-decoration: none; color: inherit; }
        .brand-icon { color: var(--accent-blue); width: 1.1rem; height: 1.1rem; }
        .brand-text { font-weight: 700; font-size: 0.9rem; letter-spacing: 0.05em;  color: var(--accent-blue); }
        .brand-text span { color: #ffffff; }
        .nav { display: flex; gap: 0.25rem; }
        .nav-link { color: var(--text-secondary); text-decoration: none; font-size: 0.75rem; padding: 0.4rem 0.75rem; border-radius: 3px;  letter-spacing: 0.05em; transition: all 0.1s; }
        .nav-link:hover, .nav-link.active { color: var(--text-primary); background: var(--bg-tertiary); }

        [data-theme="light"] { --bg-primary: #f5f5f5; --bg-secondary: #e8e8e8; --bg-tertiary: #ffffff; --bg-hover: #d8d8d8; --text-primary: #1a1a1a; --text-secondary: #555555; --text-muted: #888888; --accent-red: #2563eb; --accent-green: #16a34a; --border-color: #cccccc; }

        .theme-toggle { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); font-family: var(--font-mono); font-size: 0.75rem; padding: 0.3rem 0.5rem; cursor: pointer; border-radius: 3px; transition: all 0.1s; }
        .theme-toggle:hover { color: var(--text-primary); border-color: var(--border-active, #999); }

        .config-nav { background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); display: flex; justify-content: center; gap: 0; }
        .config-nav a { color: var(--text-muted); text-decoration: none; font-size: 0.7rem; padding: 0.75rem 1.25rem;  letter-spacing: 0.1em; border-bottom: 2px solid transparent; transition: all 0.15s; }
        .config-nav a:hover { color: var(--text-secondary); }
        .config-nav a.active { color: var(--text-primary); border-bottom-color: var(--accent-red); }

        .main { max-width: 700px; margin: 0 auto; padding: 2rem 1rem; }
        .page-header { margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color); }
        .page-title { font-size: 0.75rem;  letter-spacing: 0.15em; color: var(--text-muted); margin-bottom: 0.5rem; }
        .page-heading { font-size: 1.25rem; font-weight: 700; }

        .panel { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 1.5rem; }
        .panel-header { padding: 0.75rem 1rem; background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color); font-size: 0.7rem;  letter-spacing: 0.1em; color: var(--text-secondary); }
        .panel-body { padding: 1rem; }

        .form-group { margin-bottom: 1rem; }
        .form-label { display: block; font-size: 0.7rem;  letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 0.5rem; }
        .form-input { width: 100%; padding: 0.6rem 0.75rem; border: 1px solid var(--border-color); border-radius: 3px; background: var(--bg-tertiary); color: var(--text-primary); font-family: var(--font-mono); font-size: 0.8rem; }
        .form-input:focus { outline: none; border-color: var(--accent-red); }

        .form-check { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.75rem; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 3px; margin-bottom: 0.5rem; cursor: pointer; }
        .form-check:hover { border-color: var(--accent-red); }
        .form-check input { width: 16px; height: 16px; accent-color: var(--accent-red); margin-top: 2px; }
        .form-check-label { font-size: 0.8rem; }
        .form-check-desc { font-size: 0.7rem; color: var(--text-muted); margin-top: 0.25rem; }

        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .form-hint { font-size: 0.7rem; color: var(--text-muted); margin-top: 0.25rem; }

        .btn { padding: 0.6rem 1.25rem; border-radius: 3px; font-family: var(--font-mono); font-size: 0.7rem; font-weight: 500; cursor: pointer; border: 1px solid var(--border-color); background: var(--bg-tertiary); color: var(--text-secondary);  letter-spacing: 0.05em; text-decoration: none; display: inline-block; transition: all 0.1s; }
        .btn:hover { background: var(--bg-hover); color: var(--text-primary); }
        .btn-primary { background: var(--accent-red); border-color: var(--accent-red); color: white; }
        .btn-primary:hover { background: #1d4ed8; }

        .btn-row { display: flex; gap: 0.75rem; margin-top: 1.5rem; }

        .status-msg { padding: 0.75rem 1rem; border-radius: 3px; font-size: 0.8rem; margin-bottom: 1rem; display: none; border: 1px solid; }
        .status-msg.success { background: rgba(22, 163, 74, 0.1); color: var(--accent-green); border-color: var(--accent-green); display: block; }
        .status-msg.error { background: rgba(220, 38, 38, 0.1); color: var(--accent-red); border-color: var(--accent-red); display: block; }

        .config-tab { display: none; }

        .footer { text-align: center; padding: 1.5rem; font-size: 0.65rem; color: var(--text-muted); border-top: 1px solid var(--border-color); }
        .footer a { color: var(--accent-red); text-decoration: none; }
    </style>
</head>
<body>
    <header class="topbar">
        <div class="topbar-left">
            <a href="/" class="brand"><svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7 7 10 10-5 5V2l5 5L7 17"/></svg><span class="brand-text">Blue<span>Watch</span></span></a>
            <nav class="nav">
                <a href="/" class="nav-link">Dashboard</a>
                <a href="/all" class="nav-link">All devices</a>
                <a href="/settings" class="nav-link active">Config</a>
            </nav>
        </div>
        <div><button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle light/dark mode">☀</button></div>
    </header>

    <nav class="config-nav">
        <a href="#alerts" data-tab="alerts" class="active" onclick="switchTab('alerts')">Alerts</a>
        <a href="#operations" data-tab="operations" onclick="switchTab('operations')">Operations</a>
        <a href="#groups" data-tab="groups" onclick="switchTab('groups')">Groups</a>
        <a href="#classes" data-tab="classes" onclick="switchTab('classes')">Classes</a>
        <a href="#security" data-tab="security" onclick="switchTab('security')">Security</a>
        <a href="#wigle" data-tab="wigle" onclick="switchTab('wigle')">WiGLE</a>
        <a href="#fastpair" data-tab="fastpair" onclick="switchTab('fastpair')">Fast Pair</a>
        <a href="#esp32" data-tab="esp32" onclick="switchTab('esp32')">ESP32 Scanner</a>
        <a href="#export" data-tab="export" onclick="switchTab('export')">Export</a>
        <a href="#about" data-tab="about" onclick="switchTab('about')">About</a>
    </nav>

    <main class="main">
        <div id="status-msg" class="status-msg"></div>

        <!-- Alerts Tab -->
        <div class="config-tab" id="tab-alerts">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">Alert Configuration</h1>
            </div>

            <form id="settings-form">
                <div class="panel">
                    <div class="panel-header">Push Notification Channel (ntfy.sh)</div>
                    <div class="panel-body">
                        <div class="form-group">
                            <label class="form-label">Topic Identifier</label>
                            <input type="text" class="form-input" id="ntfy_topic" placeholder="e.g., bluewatch-ops-alerts">
                        </div>
                        <label class="form-check">
                            <input type="checkbox" id="ntfy_enabled">
                            <div>
                                <div class="form-check-label">Enable Push Notifications</div>
                                <div class="form-check-desc">Route alerts through ntfy.sh service</div>
                            </div>
                        </label>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">Alert Triggers</div>
                    <div class="panel-body">
                        <label class="form-check">
                            <input type="checkbox" id="notify_new_device">
                            <div>
                                <div class="form-check-label">New Target Acquired</div>
                                <div class="form-check-desc">Alert on first contact with unknown device</div>
                            </div>
                        </label>
                        <div id="new-device-threshold-field" style="display: none; margin: 0.5rem 0 0.5rem 2rem;">
                            <label class="form-label">Persistence Threshold (min)</label>
                            <input type="number" class="form-input" id="new_device_threshold_minutes" value="0" min="0" max="1440" style="width: 120px;">
                            <div class="form-hint">0 = immediate alert, &gt;0 = alert after device persists this long</div>
                        </div>
                        <label class="form-check">
                            <input type="checkbox" id="notify_watched_return">
                            <div>
                                <div class="form-check-label">Watched Target Returns</div>
                                <div class="form-check-desc">Alert when monitored target re-enters range</div>
                            </div>
                        </label>
                        <label class="form-check">
                            <input type="checkbox" id="notify_watched_leave">
                            <div>
                                <div class="form-check-label">Watched Target Departs</div>
                                <div class="form-check-desc">Alert when monitored target exits range</div>
                            </div>
                        </label>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">Watched Devices</div>
                    <div class="panel-body">
                        <div class="form-hint" style="margin-bottom: 0.5rem;">Every device currently marked as a Watched target (Device of Interest) -- these are what trigger the "Watched Target Returns/Departs" alerts above. Remove one here to stop watching it, same as un-watching it from its device detail page.</div>
                        <div id="watched-devices-list" style="display: flex; flex-direction: column; gap: 0.5rem;">Loading...</div>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">Type-Based Alerts</div>
                    <div class="panel-body">
                        <div class="form-hint" style="margin-bottom: 0.5rem;">Alert immediately whenever a device of one of these types is detected, regardless of whether it's been categorized -- e.g. a Flipper Zero nearby is worth knowing about every time it reappears, not just once.</div>
                        <div id="type-alert-types" style="display: flex; flex-wrap: wrap; gap: 0.5rem 1.5rem;">Loading...</div>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">Detection Thresholds</div>
                    <div class="panel-body">
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Absence Threshold (min)</label>
                                <input type="number" class="form-input" id="watched_absence_minutes" value="30" min="1" max="1440">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Return Threshold (min)</label>
                                <input type="number" class="form-input" id="watched_return_minutes" value="5" min="1" max="60">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="btn-row">
                    <button type="submit" class="btn btn-primary">Save Configuration</button>
                    <a href="/" class="btn">Cancel</a>
                </div>
            </form>
        </div>

        <!-- Operations Tab -->
        <div class="config-tab" id="tab-operations">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">Operations</h1>
            </div>

            <form id="operations-form">
                <div class="panel">
                    <div class="panel-header">Heartbeat Check-In</div>
                    <div class="panel-body">
                        <div class="form-group">
                            <label class="form-label">Heartbeat URL</label>
                            <input type="url" class="form-input" id="heartbeat_url" placeholder="e.g., https://uptime.example.com/api/push/abc123">
                            <div class="form-hint">POST JSON payload with hostname, uptime, device count. Leave empty to disable.</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Interval (seconds)</label>
                            <input type="number" class="form-input" id="heartbeat_interval" value="300" min="30" max="86400" style="width: 160px;">
                            <div class="form-hint">How often to send heartbeat pings (default: 300s / 5 min)</div>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">Web Server</div>
                    <div class="panel-body">
                        <div class="form-group">
                            <label class="form-label">Port</label>
                            <input type="number" class="form-input" id="web_port" placeholder="8080" min="1" max="65535" style="width: 160px;">
                            <div class="form-hint">Change the dashboard's port if 8080 conflicts with another device on the network. Takes effect on the next restart of the bluewatch service (systemctl restart bluewatch) -- saving alone doesn't rebind it live. Leave empty for the default (8080).</div>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">Storage Rotation</div>
                    <div class="panel-body">
                        <div class="form-group">
                            <label class="form-label">Prune Sightings Older Than (days)</label>
                            <input type="number" class="form-input" id="prune_days" value="0" min="0" max="3650" style="width: 160px;">
                            <div class="form-hint">Automatically prune records older than this many days. 0 = keep forever.</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Only Prune Devices With Fewer Than (sightings)</label>
                            <input type="number" class="form-input" id="prune_min_sightings" value="0" min="0" max="1000000" style="width: 160px;">
                            <div class="form-hint">When set above 0, pruning removes whole stale devices (and their sightings) that are both older than the age limit and have fewer than this many total sightings. Watched devices and devices assigned to any category are never pruned. 0 = prune old sightings by age only, keeping device records.</div>
                        </div>
                    </div>
                </div>

                <div class="btn-row">
                    <button type="submit" class="btn btn-primary">Save Configuration</button>
                    <a href="/" class="btn">Cancel</a>
                </div>
            </form>
        </div>

        <!-- Groups Tab -->
        <div class="config-tab" id="tab-groups">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">Device Groups</h1>
            </div>

            <div class="panel">
                <div class="panel-header">Device Groups</div>
                <div class="panel-body">
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;">Organize targets into custom groups for easier tracking</p>
                    <div id="groups-list" style="margin-bottom: 1rem;"></div>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="text" class="form-input" id="new-group-name" placeholder="New group name" style="flex: 1;">
                        <input type="color" id="new-group-color" value="#3b82f6" style="width: 40px; height: 38px; border: 1px solid var(--border-color); background: var(--bg-tertiary); cursor: pointer;">
                        <button type="button" class="btn btn-primary" onclick="createGroup()">Add Group</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Classes Tab -->
        <div class="config-tab" id="tab-classes">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">Device Classes</h1>
            </div>

            <div class="panel">
                <div class="panel-header">Custom Classes</div>
                <div class="panel-body">
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;">BlueWatch ships with a set of built-in device classes (Phone, Watch, Camera, etc.) that the automatic classifier assigns. Add your own here for anything that doesn't fit -- e.g. a "Lawnmower" class for a robotic mower -- and it becomes selectable in every device's Type dropdown, same as a built-in one. Built-in classes can't be edited or removed here.</p>
                    <div id="custom-types-list" style="display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem;">Loading...</div>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="text" class="form-input" id="new-type-icon" placeholder="[MOW]" style="width: 90px;" maxlength="12">
                        <input type="text" class="form-input" id="new-type-label" placeholder="New class name, e.g. Lawnmower" style="flex: 1;">
                        <button type="button" class="btn btn-primary" onclick="createCustomType()">Add Class</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Security Tab -->
        <div class="config-tab" id="tab-security">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">Access Control</h1>
            </div>

            <div class="panel">
                <div class="panel-header">Access Control</div>
                <div class="panel-body">
                    <label class="form-check">
                        <input type="checkbox" id="auth_enabled">
                        <div>
                            <div class="form-check-label">Enable Authentication</div>
                            <div class="form-check-desc">Require login to access the dashboard</div>
                        </div>
                    </label>
                    <div id="auth-fields" style="display: none; margin-top: 1rem;">
                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <input type="text" class="form-input" id="auth_username" autocomplete="username">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-input" id="auth_password" autocomplete="new-password" placeholder="Enter new password">
                        </div>
                    </div>
                    <div class="btn-row" style="margin-top: 1rem;">
                        <button type="button" class="btn btn-primary" onclick="saveAuthSettings()">Update Access Control</button>
                        <button type="button" class="btn" onclick="logout()" id="logout-btn" style="display: none;">Logout</button>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">Identity Resolving Keys (IRK)</div>
                <div class="panel-body">
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;">Add an IRK from one of your own devices to cryptographically resolve its privacy-randomized address across rotations -- proof, not a name-matching guess. Only works for devices you hold the key for; there's no way to resolve a stranger's randomized address.</p>
                    <div id="irk-keys-list" style="margin-bottom: 1rem;"></div>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="text" class="form-input" id="new-irk-label" placeholder="Label (e.g. My Phone)" style="flex: 1;">
                        <input type="text" class="form-input" id="new-irk-hex" placeholder="IRK (32 hex chars)" style="flex: 2;">
                        <button type="button" class="btn btn-primary" onclick="createIrkKey()">Add</button>
                    </div>
                </div>
            </div>

        </div>

        <!-- WiGLE Tab -->
        <div class="config-tab" id="tab-wigle">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">WiGLE Vendor Lookup</h1>
            </div>

            <div class="panel">
                <div class="panel-header">WiGLE Vendor Lookup</div>
                <div class="panel-body">
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;">Fills in a vendor/name for devices our own OUI lookups can't identify, using WiGLE.net's crowdsourced Bluetooth database. Only ever reads a device's recorded name -- never its location history. Free-tier quota is small, so at most 1 new lookup is spent per scan cycle. This key lives only in this instance's database, not in the source code, so it's never carried along into a fork or shared copy of this project.</p>
                    <div id="wigle-status" style="font-size: 0.8rem; margin-bottom: 1rem; color: var(--text-muted);">Loading...</div>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="text" class="form-input" id="wigle-api-name" placeholder="API Name" style="flex: 1;">
                        <input type="password" class="form-input" id="wigle-api-token" placeholder="API Token" style="flex: 1;">
                        <button type="button" class="btn btn-primary" onclick="saveWigleSettings()">Save</button>
                        <button type="button" class="btn" id="wigle-clear-btn" onclick="clearWigleSettings()" style="display: none;">Clear</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Fast Pair Tab -->
        <div class="config-tab" id="tab-fastpair">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">Fast Pair Verification</h1>
            </div>

            <div class="panel">
                <div class="panel-header">Fast Pair Anti-Spoof Verification</div>
                <div class="panel-body">
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.75rem;">Fast Pair is Google's Bluetooth pairing protocol, used by many earbuds, speakers, and Android accessories to announce what they are. BlueWatch already identifies Fast Pair devices for free, automatically, with no setup -- it looks up the Model ID each device broadcasts in a bundled offline database of ~2,900 known devices.</p>
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;">The toggle below is a separate, optional extra: a genuine Fast Pair device holds a secret key proving it really is the Model ID it claims to be. When enabled, "Scan Unit" can challenge a device to prove this, catching a spoofed or cloned advertisement pretending to be a device it isn't. This check only works for Model IDs you've manually added a verification key for (see below) -- it changes nothing about the free identification above, which keeps working regardless.</p>
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                        <input type="checkbox" id="fastpair-enabled" onchange="saveFastpairSettings()">
                        <label for="fastpair-enabled" style="font-size: 0.85rem;">Enable the extra spoof-check challenge in Scan Unit</label>
                    </div>
                    <details style="font-size: 0.75rem; color: var(--text-muted);">
                        <summary style="cursor: pointer;">How do I add a verification key for a device?</summary>
                        <p style="margin-top: 0.5rem;">Google does not publish a self-service API for looking up a device model's Anti-Spoofing Public Key -- this spoof-check only works for models you've added by hand to the local key file on the BlueWatch host (<code>fastpair_keys.json</code> under its data directory), mapping a 3-byte Model ID to its 64-byte public key from a source you trust. Without an entry there for a given device, BlueWatch simply skips the check for it (the free name/manufacturer identification still applies).</p>
                    </details>
                </div>
            </div>
        </div>

        <!-- ESP32 Scanner Tab -->
        <div class="config-tab" id="tab-esp32">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">ESP32 Scanner</h1>
            </div>

            <div class="panel">
                <div class="panel-header">Second BLE Radio (ESP32-S3)</div>
                <div class="panel-body">
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;">If you have an ESP32-S3 flashed with <a href="https://github.com/blesploit/esp32-firmware" target="_blank" rel="noopener" style="color: var(--accent-blue);">blesploit's observer firmware</a>, plug it into a USB port on this host. It appears as a USB-Ethernet device and exposes a raw BLE advertisement feed over WebSocket -- BlueWatch runs it purely as an independent second radio (passive observation only, no connecting/cloning), so it keeps listening continuously even while the built-in adapter is busy with a Scan Unit poll.</p>
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                        <input type="checkbox" id="esp32-enabled" onchange="saveEsp32Settings()">
                        <label for="esp32-enabled" style="font-size: 0.85rem;">Enable ESP32 second scanner</label>
                    </div>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <label for="esp32-host" style="font-size: 0.8rem; color: var(--text-muted); white-space: nowrap;">Host / IP</label>
                        <input type="text" class="form-input" id="esp32-host" placeholder="192.168.5.1" style="max-width: 12rem;" onchange="saveEsp32Settings()">
                    </div>
                </div>
            </div>
        </div>

        <!-- Export Tab -->
        <div class="config-tab" id="tab-export">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">Export</h1>
            </div>

            <div class="panel">
                <div class="panel-header">Export Devices</div>
                <div class="panel-body">
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;">Download every known device (every category included) as a single file.</p>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <select class="form-input" id="export-format" aria-label="Export format" style="max-width: 10rem;">
                            <option value="csv" selected>CSV</option>
                            <option value="json">JSON</option>
                        </select>
                        <button type="button" class="btn btn-primary" id="export-btn" onclick="exportData()">Export</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- About Tab -->
        <div class="config-tab" id="tab-about">
            <div class="page-header">
                <div class="page-title">System Configuration</div>
                <h1 class="page-heading">About</h1>
            </div>

            <div class="panel">
                <div class="panel-body" style="text-align: center; padding: 2rem 1.5rem;">
                    <img src="/assets/logo.png" alt="BlueWatch logo" style="width: 260px; height: 260px; margin-bottom: 1.5rem;">
                    <p style="font-size: 0.85rem; line-height: 1.6; color: var(--text-secondary); max-width: 560px; margin: 0 auto 1rem;">
                        BlueWatch passively detects Bluetooth devices (BLE and Classic) in your area and helps you tell them apart from the noise: categorize the devices you already know, and BlueWatch surfaces the moment something new enters range instead of burying it under dozens of familiar devices.
                    </p>
                    <p style="font-size: 0.85rem; line-height: 1.6; color: var(--text-secondary); max-width: 560px; margin: 0 auto 1.5rem;">
                        Forked from <a href="https://github.com/dannymcc/bluehood" target="_blank" rel="noopener" style="color: var(--accent-blue);">bluehood</a> by Danny McClelland (MIT licensed), since grown into its own project.
                    </p>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 1.25rem;">
                        Questions or interest? <a href="mailto:p0larpatch@proton.me" style="color: var(--accent-blue);">p0larpatch@proton.me</a>
                    </p>
                    <a href="https://github.com/PolarPatch/BlueWatch" target="_blank" rel="noopener" class="btn btn-primary" style="display: inline-block; text-decoration: none;">View on GitHub</a>
                </div>
            </div>
        </div>
    </main>

    

    <script>
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            const btn = document.getElementById('theme-toggle');
            if (btn) btn.textContent = theme === 'light' ? '☽' : '☀';
        }
        function toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            localStorage.setItem('bluewatch_theme', next);
            applyTheme(next);
        }
        applyTheme(localStorage.getItem('bluewatch_theme') || 'dark');

        function switchTab(tab) {
            document.querySelectorAll('.config-tab').forEach(function(t) { t.style.display = 'none'; });
            document.querySelectorAll('.config-nav a').forEach(function(a) { a.classList.remove('active'); });
            var tabEl = document.getElementById('tab-' + tab);
            if (tabEl) tabEl.style.display = 'block';
            var navEl = document.querySelector('[data-tab="' + tab + '"]');
            if (navEl) navEl.classList.add('active');
            history.replaceState(null, '', '#' + tab);
        }

        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                const data = await response.json();
                document.getElementById('ntfy_topic').value = data.ntfy_topic || '';
                document.getElementById('ntfy_enabled').checked = data.ntfy_enabled;
                document.getElementById('notify_new_device').checked = data.notify_new_device;
                document.getElementById('new_device_threshold_minutes').value = data.new_device_threshold_minutes || 0;
                document.getElementById('new-device-threshold-field').style.display = data.notify_new_device ? 'block' : 'none';
                document.getElementById('notify_watched_return').checked = data.notify_watched_return;
                document.getElementById('notify_watched_leave').checked = data.notify_watched_leave;
                document.getElementById('watched_absence_minutes').value = data.watched_absence_minutes;
                document.getElementById('watched_return_minutes').value = data.watched_return_minutes;
                document.getElementById('heartbeat_url').value = data.heartbeat_url || '';
                document.getElementById('heartbeat_interval').value = data.heartbeat_interval || 300;
                document.getElementById('prune_days').value = data.prune_days || 0;
                document.getElementById('prune_min_sightings').value = data.prune_min_sightings || 0;
                document.getElementById('web_port').value = data.web_port || '';

                const typesResp = await fetch('/api/device-types');
                const typesData = await typesResp.json();
                const selectedTypes = new Set(data.type_alert_types || []);
                document.getElementById('type-alert-types').innerHTML = typesData.types.map(function(t) {
                    return '<label class="form-check" style="flex: 0 0 auto;">'
                        + '<input type="checkbox" class="type-alert-checkbox" value="' + t.value + '"' + (selectedTypes.has(t.value) ? ' checked' : '') + '>'
                        + '<div><div class="form-check-label">' + t.icon + ' ' + t.label + '</div></div>'
                        + '</label>';
                }).join('');
            } catch (error) { showStatus('Error loading configuration', 'error'); }
        }

        async function loadWatchedDevices() {
            const el = document.getElementById('watched-devices-list');
            if (!el) return;
            try {
                const response = await fetch('/api/devices?filter=watched&page_size=250&sort=last_seen&direction=desc');
                const data = await response.json();
                const devices = data.devices || [];
                el.textContent = '';
                if (devices.length === 0) {
                    var empty = document.createElement('div');
                    empty.className = 'form-hint';
                    empty.textContent = 'No devices are currently watched.';
                    el.appendChild(empty);
                    return;
                }
                devices.forEach(function(d) {
                    const name = d.friendly_name || d.vendor || d.mac;
                    var row = document.createElement('div');
                    row.style.cssText = 'display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.4rem 0.6rem; background: var(--bg-secondary); border-radius: 6px;';
                    var info = document.createElement('div');
                    info.style.cssText = 'min-width: 0;';
                    var nameLine = document.createElement('div');
                    nameLine.style.cssText = 'font-size: 0.85rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;';
                    nameLine.textContent = (d.type_icon || '') + ' ' + name;
                    var macLine = document.createElement('div');
                    macLine.style.cssText = 'font-size: 0.7rem; color: var(--text-muted);';
                    macLine.textContent = d.mac;
                    info.appendChild(nameLine);
                    info.appendChild(macLine);
                    var removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.className = 'btn';
                    removeBtn.style.cssText = 'flex: 0 0 auto;';
                    removeBtn.textContent = 'Remove';
                    removeBtn.addEventListener('click', function() { unwatchDevice(d.mac); });
                    row.appendChild(info);
                    row.appendChild(removeBtn);
                    el.appendChild(row);
                });
            } catch (error) {
                el.textContent = '';
                var errEl = document.createElement('div');
                errEl.className = 'form-hint';
                errEl.textContent = 'Error loading watched devices.';
                el.appendChild(errEl);
            }
        }

        async function unwatchDevice(mac) {
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/watch', { method: 'POST' });
                if (response.ok) {
                    showStatus('Removed from watched devices', 'success');
                    loadWatchedDevices();
                } else {
                    showStatus('Error removing watched device', 'error');
                }
            } catch (error) { showStatus('Error removing watched device', 'error'); }
        }

        function gatherAllSettings() {
            return {
                ntfy_topic: document.getElementById('ntfy_topic').value,
                ntfy_enabled: document.getElementById('ntfy_enabled').checked,
                notify_new_device: document.getElementById('notify_new_device').checked,
                type_alert_types: Array.from(document.querySelectorAll('.type-alert-checkbox:checked')).map(function(el) { return el.value; }),
                new_device_threshold_minutes: parseInt(document.getElementById('new_device_threshold_minutes').value) || 0,
                notify_watched_return: document.getElementById('notify_watched_return').checked,
                notify_watched_leave: document.getElementById('notify_watched_leave').checked,
                watched_absence_minutes: parseInt(document.getElementById('watched_absence_minutes').value),
                watched_return_minutes: parseInt(document.getElementById('watched_return_minutes').value),
                heartbeat_url: document.getElementById('heartbeat_url').value,
                heartbeat_interval: parseInt(document.getElementById('heartbeat_interval').value) || 300,
                prune_days: parseInt(document.getElementById('prune_days').value) || 0,
                prune_min_sightings: parseInt(document.getElementById('prune_min_sightings').value) || 0,
                web_port: document.getElementById('web_port').value,
            };
        }

        async function saveSettings(e) {
            e.preventDefault();
            try {
                const response = await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(gatherAllSettings()) });
                if (response.ok) {
                    showStatus('Configuration saved', 'success');
                } else {
                    const err = await response.json().catch(() => ({}));
                    showStatus(err.error || 'Error saving configuration', 'error');
                }
            } catch (error) { showStatus('Error saving configuration', 'error'); }
        }

        async function saveOperations(e) {
            e.preventDefault();
            try {
                const response = await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(gatherAllSettings()) });
                if (response.ok) {
                    showStatus('Configuration saved', 'success');
                } else {
                    const err = await response.json().catch(() => ({}));
                    showStatus(err.error || 'Error saving configuration', 'error');
                }
            } catch (error) { showStatus('Error saving configuration', 'error'); }
        }

        function showStatus(message, type) {
            const el = document.getElementById('status-msg');
            el.textContent = message;
            el.className = 'status-msg ' + type;
            if (type === 'success') setTimeout(function() { el.className = 'status-msg'; }, 3000);
        }

        async function loadAuthStatus() {
            try {
                const response = await fetch('/api/auth/status');
                const data = await response.json();
                document.getElementById('auth_enabled').checked = data.auth_enabled;
                document.getElementById('auth_username').value = data.username || '';
                document.getElementById('auth-fields').style.display = data.auth_enabled ? 'block' : 'none';
                document.getElementById('logout-btn').style.display = data.authenticated && data.auth_enabled ? 'inline-block' : 'none';
            } catch (error) { console.error('Error loading auth status'); }
        }

        document.getElementById('notify_new_device').addEventListener('change', function(e) {
            document.getElementById('new-device-threshold-field').style.display = e.target.checked ? 'block' : 'none';
        });

        document.getElementById('auth_enabled').addEventListener('change', function(e) {
            document.getElementById('auth-fields').style.display = e.target.checked ? 'block' : 'none';
        });

        async function saveAuthSettings() {
            const enabled = document.getElementById('auth_enabled').checked;
            const username = document.getElementById('auth_username').value;
            const password = document.getElementById('auth_password').value;

            if (enabled && (!username || !password)) {
                showStatus('Username and password required', 'error');
                return;
            }

            try {
                const response = await fetch('/api/auth/setup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: enabled, username: username, password: password })
                });
                if (response.ok) {
                    showStatus('Access control updated', 'success');
                    document.getElementById('auth_password').value = '';
                    loadAuthStatus();
                } else {
                    const data = await response.json();
                    showStatus(data.error || 'Error updating access control', 'error');
                }
            } catch (error) { showStatus('Error updating access control', 'error'); }
        }

        async function logout() {
            try {
                await fetch('/api/auth/logout', { method: 'POST' });
                window.location.href = '/login';
            } catch (error) { console.error('Logout error'); }
        }

        async function loadGroups() {
            try {
                const response = await fetch('/api/groups');
                const data = await response.json();
                const container = document.getElementById('groups-list');
                if (!data.groups || data.groups.length === 0) {
                    container.textContent = '';
                    var empty = document.createElement('div');
                    empty.style.cssText = 'color: var(--text-muted); font-size: 0.75rem; text-align: center; padding: 1rem;';
                    empty.textContent = 'No groups created yet';
                    container.appendChild(empty);
                    return;
                }
                container.textContent = '';
                data.groups.forEach(function(g) {
                    var row = document.createElement('div');
                    row.style.cssText = 'display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem; background: var(--bg-tertiary); border-radius: 3px; margin-bottom: 0.5rem;';
                    var swatch = document.createElement('div');
                    swatch.style.cssText = 'width: 12px; height: 12px; border-radius: 2px; background: ' + g.color + ';';
                    var name = document.createElement('span');
                    name.style.cssText = 'flex: 1; font-size: 0.85rem;';
                    name.textContent = g.name;
                    var renameBtn = document.createElement('button');
                    renameBtn.className = 'btn';
                    renameBtn.style.cssText = 'padding: 0.25rem 0.5rem; font-size: 0.7rem;';
                    renameBtn.textContent = 'Rename';
                    renameBtn.addEventListener('click', function() { renameGroup(g); });
                    var btn = document.createElement('button');
                    btn.className = 'btn';
                    btn.style.cssText = 'padding: 0.25rem 0.5rem; font-size: 0.7rem;';
                    btn.textContent = 'Delete';
                    btn.addEventListener('click', function() { deleteGroup(g.id); });
                    row.appendChild(swatch);
                    row.appendChild(name);
                    row.appendChild(renameBtn);
                    row.appendChild(btn);
                    container.appendChild(row);
                });
            } catch (error) { console.error('Error loading groups'); }
        }

        async function createGroup() {
            const name = document.getElementById('new-group-name').value.trim();
            const color = document.getElementById('new-group-color').value;
            if (!name) { showStatus('Group name required', 'error'); return; }

            try {
                const response = await fetch('/api/groups', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name, color: color, icon: String.fromCodePoint(128193) })
                });
                if (response.ok) {
                    document.getElementById('new-group-name').value = '';
                    loadGroups();
                    showStatus('Group created', 'success');
                } else {
                    showStatus('Error creating group', 'error');
                }
            } catch (error) { showStatus('Error creating group', 'error'); }
        }

        async function loadCustomTypes() {
            try {
                const response = await fetch('/api/custom-types');
                const data = await response.json();
                const container = document.getElementById('custom-types-list');
                if (!container) return;
                container.textContent = '';
                if (!data.types || data.types.length === 0) {
                    var empty = document.createElement('div');
                    empty.style.cssText = 'color: var(--text-muted); font-size: 0.75rem; text-align: center; padding: 1rem;';
                    empty.textContent = 'No custom classes yet';
                    container.appendChild(empty);
                    return;
                }
                data.types.forEach(function(t) {
                    var row = document.createElement('div');
                    row.style.cssText = 'display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem; background: var(--bg-tertiary); border-radius: 3px;';
                    var icon = document.createElement('span');
                    icon.style.cssText = 'font-family: monospace; font-size: 0.8rem; color: var(--text-muted); min-width: 3rem;';
                    icon.textContent = t.icon;
                    var label = document.createElement('span');
                    label.style.cssText = 'flex: 1; font-size: 0.85rem;';
                    label.textContent = t.label;
                    var renameBtn = document.createElement('button');
                    renameBtn.className = 'btn';
                    renameBtn.style.cssText = 'padding: 0.25rem 0.5rem; font-size: 0.7rem;';
                    renameBtn.textContent = 'Edit';
                    renameBtn.addEventListener('click', function() { editCustomType(t); });
                    var delBtn = document.createElement('button');
                    delBtn.className = 'btn';
                    delBtn.style.cssText = 'padding: 0.25rem 0.5rem; font-size: 0.7rem;';
                    delBtn.textContent = 'Delete';
                    delBtn.addEventListener('click', function() { deleteCustomType(t.key); });
                    row.appendChild(icon);
                    row.appendChild(label);
                    row.appendChild(renameBtn);
                    row.appendChild(delBtn);
                    container.appendChild(row);
                });
            } catch (error) { console.error('Error loading custom classes'); }
        }

        async function createCustomType() {
            const icon = document.getElementById('new-type-icon').value.trim() || '[???]';
            const label = document.getElementById('new-type-label').value.trim();
            if (!label) { showStatus('Class name required', 'error'); return; }

            try {
                const response = await fetch('/api/custom-types', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ icon: icon, label: label })
                });
                if (response.ok) {
                    document.getElementById('new-type-icon').value = '';
                    document.getElementById('new-type-label').value = '';
                    loadCustomTypes();
                    showStatus('Class created', 'success');
                } else {
                    const err = await response.json().catch(() => ({}));
                    showStatus(err.error || 'Error creating class', 'error');
                }
            } catch (error) { showStatus('Error creating class', 'error'); }
        }

        async function editCustomType(t) {
            const newLabel = prompt('Class name', t.label);
            if (newLabel === null) return;
            const trimmedLabel = newLabel.trim();
            if (!trimmedLabel) return;
            const newIcon = prompt('Icon', t.icon);
            if (newIcon === null) return;
            const trimmedIcon = newIcon.trim() || '[???]';
            try {
                const response = await fetch('/api/custom-types/' + encodeURIComponent(t.key), {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ icon: trimmedIcon, label: trimmedLabel })
                });
                if (response.ok) { loadCustomTypes(); showStatus('Class updated', 'success'); }
                else { showStatus('Error updating class', 'error'); }
            } catch (error) { showStatus('Error updating class', 'error'); }
        }

        async function deleteCustomType(key) {
            if (!confirm('Delete this class? Devices already set to it keep the raw value but show as Unknown until reassigned.')) return;
            try {
                const response = await fetch('/api/custom-types/' + encodeURIComponent(key), { method: 'DELETE' });
                if (response.ok) { loadCustomTypes(); showStatus('Class deleted', 'success'); }
                else { showStatus('Error deleting class', 'error'); }
            } catch (error) { showStatus('Error deleting class', 'error'); }
        }

        async function loadIrkKeys() {
            try {
                const response = await fetch('/api/irk-keys');
                const data = await response.json();
                const container = document.getElementById('irk-keys-list');
                if (!container) return;
                if (!data.irk_keys || data.irk_keys.length === 0) {
                    container.textContent = '';
                    var empty = document.createElement('div');
                    empty.style.cssText = 'color: var(--text-muted); font-size: 0.75rem; text-align: center; padding: 1rem;';
                    empty.textContent = 'No IRKs configured yet';
                    container.appendChild(empty);
                    return;
                }
                container.textContent = '';
                data.irk_keys.forEach(function(k) {
                    var row = document.createElement('div');
                    row.style.cssText = 'display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem; background: var(--bg-tertiary); border-radius: 3px; margin-bottom: 0.5rem;';
                    var name = document.createElement('span');
                    name.style.cssText = 'flex: 1; font-size: 0.85rem;';
                    name.textContent = k.label + '  ';
                    var maskedSpan = document.createElement('span');
                    maskedSpan.style.cssText = 'color: var(--text-muted); font-size: 0.75rem;';
                    maskedSpan.textContent = k.irk_masked;
                    name.appendChild(maskedSpan);
                    var btn = document.createElement('button');
                    btn.className = 'btn';
                    btn.style.cssText = 'padding: 0.25rem 0.5rem; font-size: 0.7rem;';
                    btn.textContent = 'Delete';
                    btn.addEventListener('click', function() { deleteIrkKey(k.id); });
                    row.appendChild(name);
                    row.appendChild(btn);
                    container.appendChild(row);
                });
            } catch (error) { console.error('Error loading IRK keys'); }
        }

        async function createIrkKey() {
            const label = document.getElementById('new-irk-label').value.trim();
            const irk = document.getElementById('new-irk-hex').value.trim();
            if (!label || !irk) { showStatus('Label and IRK are both required', 'error'); return; }
            try {
                const response = await fetch('/api/irk-keys', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ label: label, irk: irk })
                });
                if (response.ok) {
                    document.getElementById('new-irk-label').value = '';
                    document.getElementById('new-irk-hex').value = '';
                    loadIrkKeys();
                    showStatus('IRK added', 'success');
                } else {
                    const err = await response.json().catch(() => ({}));
                    showStatus(err.error || 'Error adding IRK', 'error');
                }
            } catch (error) { showStatus('Error adding IRK', 'error'); }
        }

        async function deleteIrkKey(id) {
            if (!confirm('Delete this IRK?')) return;
            try {
                const response = await fetch('/api/irk-keys/' + id, { method: 'DELETE' });
                if (response.ok) { loadIrkKeys(); showStatus('IRK deleted', 'success'); }
                else { showStatus('Error deleting IRK', 'error'); }
            } catch (error) { showStatus('Error deleting IRK', 'error'); }
        }

        async function loadWigleSettings() {
            const statusEl = document.getElementById('wigle-status');
            const clearBtn = document.getElementById('wigle-clear-btn');
            if (!statusEl) return;
            try {
                const response = await fetch('/api/wigle-settings');
                const data = await response.json();
                if (data.configured) {
                    statusEl.textContent = 'Configured -- ' + data.api_name_masked + ' / ' + data.api_token_masked;
                    statusEl.style.color = 'var(--accent-green)';
                    if (clearBtn) clearBtn.style.display = '';
                } else {
                    statusEl.textContent = 'Not configured';
                    statusEl.style.color = 'var(--text-muted)';
                    if (clearBtn) clearBtn.style.display = 'none';
                }
            } catch (error) {
                statusEl.textContent = 'Error loading status';
            }
        }

        async function saveWigleSettings() {
            const apiName = document.getElementById('wigle-api-name').value.trim();
            const apiToken = document.getElementById('wigle-api-token').value.trim();
            if (!apiName || !apiToken) { showStatus('API Name and API Token are both required', 'error'); return; }
            try {
                const response = await fetch('/api/wigle-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_name: apiName, api_token: apiToken })
                });
                if (response.ok) {
                    document.getElementById('wigle-api-name').value = '';
                    document.getElementById('wigle-api-token').value = '';
                    loadWigleSettings();
        loadFastpairSettings();
        loadEsp32Settings();
        loadWatchedDevices();
                    showStatus('WiGLE credentials saved', 'success');
                } else {
                    const err = await response.json().catch(() => ({}));
                    showStatus(err.error || 'Error saving WiGLE credentials', 'error');
                }
            } catch (error) { showStatus('Error saving WiGLE credentials', 'error'); }
        }

        async function clearWigleSettings() {
            if (!confirm('Remove the saved WiGLE credentials?')) return;
            try {
                const response = await fetch('/api/wigle-settings', { method: 'DELETE' });
                if (response.ok) { loadWigleSettings(); showStatus('WiGLE credentials cleared', 'success'); }
                else { showStatus('Error clearing WiGLE credentials', 'error'); }
            } catch (error) { showStatus('Error clearing WiGLE credentials', 'error'); }
        }

        async function loadFastpairSettings() {
            const enabledBox = document.getElementById('fastpair-enabled');
            if (!enabledBox) return;
            try {
                const response = await fetch('/api/fastpair-settings');
                const data = await response.json();
                enabledBox.checked = !!data.enabled;
            } catch (error) { /* leave checkbox as-is */ }
        }

        async function saveFastpairSettings() {
            const enabled = document.getElementById('fastpair-enabled').checked;
            try {
                const response = await fetch('/api/fastpair-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: enabled })
                });
                if (response.ok) {
                    showStatus('Fast Pair settings saved', 'success');
                } else {
                    const err = await response.json().catch(() => ({}));
                    showStatus(err.error || 'Error saving Fast Pair settings', 'error');
                }
            } catch (error) { showStatus('Error saving Fast Pair settings', 'error'); }
        }

        async function loadEsp32Settings() {
            const enabledBox = document.getElementById('esp32-enabled');
            if (!enabledBox) return;
            try {
                const response = await fetch('/api/esp32-scanner-settings');
                const data = await response.json();
                enabledBox.checked = !!data.enabled;
                document.getElementById('esp32-host').value = data.host || '192.168.5.1';
            } catch (error) { /* leave fields as-is */ }
        }

        async function saveEsp32Settings() {
            const enabled = document.getElementById('esp32-enabled').checked;
            const host = document.getElementById('esp32-host').value;
            try {
                const response = await fetch('/api/esp32-scanner-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: enabled, host: host })
                });
                if (response.ok) {
                    showStatus('ESP32 scanner settings saved', 'success');
                } else {
                    const err = await response.json().catch(() => ({}));
                    showStatus(err.error || 'Error saving ESP32 scanner settings', 'error');
                }
            } catch (error) { showStatus('Error saving ESP32 scanner settings', 'error'); }
        }

        async function renameGroup(g) {
            const newName = prompt('Rename group', g.name);
            if (newName === null) return;
            const trimmed = newName.trim();
            if (!trimmed || trimmed === g.name) return;
            try {
                const response = await fetch('/api/groups/' + g.id, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: trimmed, color: g.color, icon: g.icon, parent_id: g.parent_id })
                });
                if (response.ok) { loadGroups(); showStatus('Group renamed', 'success'); }
                else { showStatus('Error renaming group', 'error'); }
            } catch (error) { showStatus('Error renaming group', 'error'); }
        }

        async function deleteGroup(id) {
            if (!confirm('Delete this group?')) return;
            try {
                const response = await fetch('/api/groups/' + id, { method: 'DELETE' });
                if (response.ok) { loadGroups(); showStatus('Group deleted', 'success'); }
                else { showStatus('Error deleting group', 'error'); }
            } catch (error) { showStatus('Error deleting group', 'error'); }
        }

        function exportData() {
            const exportBtn = document.getElementById('export-btn');
            const originalLabel = exportBtn ? exportBtn.textContent : null;
            try {
                const formatSelect = document.getElementById('export-format');
                const exportFormat = formatSelect ? formatSelect.value : 'csv';

                // POST through a hidden form + iframe so the page is never navigated away.
                let iframe = document.getElementById('export-sink');
                if (!iframe) {
                    iframe = document.createElement('iframe');
                    iframe.id = 'export-sink';
                    iframe.name = 'export-sink';
                    iframe.style.display = 'none';
                    document.body.appendChild(iframe);
                }
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/api/devices/export';
                form.target = 'export-sink';
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'format';
                input.value = exportFormat;
                form.appendChild(input);
                document.body.appendChild(form);
                if (exportBtn) { exportBtn.disabled = true; exportBtn.textContent = 'Exporting...'; }
                form.submit();
                setTimeout(() => {
                    if (form.parentNode) document.body.removeChild(form);
                    if (exportBtn) { exportBtn.disabled = false; exportBtn.textContent = originalLabel; }
                }, 2000);
            } catch (error) {
                console.error('Export error:', error);
                alert('Export failed. Please try again.');
                if (exportBtn) { exportBtn.disabled = false; exportBtn.textContent = originalLabel; }
            }
        }

        document.getElementById('settings-form').addEventListener('submit', saveSettings);
        document.getElementById('operations-form').addEventListener('submit', saveOperations);

        // Tab routing: read hash on load, default to alerts
        var hash = window.location.hash.replace('#', '') || 'alerts';
        switchTab(['alerts', 'operations', 'groups', 'classes', 'security', 'wigle', 'fastpair', 'esp32', 'export', 'about'].indexOf(hash) !== -1 ? hash : 'alerts');

        loadSettings();
        loadAuthStatus();
        loadGroups();
        loadCustomTypes();
        loadIrkKeys();
        loadWigleSettings();
        loadFastpairSettings();
        loadEsp32Settings();
        loadWatchedDevices();
    </script>
</body>
</html>
"""

ABOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BlueWatch</title>
    <style>
        :root {
            --bg-primary: #0d0d0d;
            --bg-secondary: #141414;
            --bg-tertiary: #1a1a1a;
            --text-primary: #e0e0e0;
            --text-secondary: #888888;
            --text-muted: #555555;
            --accent-red: #2563eb;
            --accent-blue: #2563eb;
            --accent-amber: #d97706;
            --border-color: #2a2a2a;
            --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: var(--font-mono); background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; font-size: 13px; }

        .topbar { background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); padding: 0.5rem 1rem; display: flex; justify-content: space-between; align-items: center; }
        .topbar-left { display: flex; align-items: center; gap: 1.5rem; }
        .brand { display: flex; align-items: center; gap: 0.5rem; text-decoration: none; color: inherit; }
        .brand-icon { color: var(--accent-blue); width: 1.1rem; height: 1.1rem; }
        .brand-text { font-weight: 700; font-size: 0.9rem; letter-spacing: 0.05em;  color: var(--accent-blue); }
        .brand-text span { color: #ffffff; }
        .nav { display: flex; gap: 0.25rem; }
        .nav-link { color: var(--text-secondary); text-decoration: none; font-size: 0.75rem; padding: 0.4rem 0.75rem; border-radius: 3px;  letter-spacing: 0.05em; transition: all 0.1s; }
        .nav-link:hover, .nav-link.active { color: var(--text-primary); background: var(--bg-tertiary); }

        [data-theme="light"] { --bg-primary: #f5f5f5; --bg-secondary: #e8e8e8; --bg-tertiary: #ffffff; --bg-hover: #d8d8d8; --text-primary: #1a1a1a; --text-secondary: #555555; --text-muted: #888888; --accent-red: #2563eb; --accent-amber: #d97706; --border-color: #cccccc; }

        .theme-toggle { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); font-family: var(--font-mono); font-size: 0.75rem; padding: 0.3rem 0.5rem; cursor: pointer; border-radius: 3px; transition: all 0.1s; }
        .theme-toggle:hover { color: var(--text-primary); border-color: var(--border-active, #999); }

        .main { max-width: 800px; margin: 0 auto; padding: 2rem 1rem; }

        .hero { text-align: center; margin-bottom: 2.5rem; padding: 2rem; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 4px; }
        .hero-icon { color: var(--accent-red); font-size: 2.5rem; margin-bottom: 1rem; }
        .hero-title { font-size: 1.5rem; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 0.5rem; }
        .hero-title span { color: var(--accent-red); }
        .hero-tagline { font-size: 0.8rem; color: var(--text-muted);  letter-spacing: 0.15em; }

        .panel { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 1.5rem; }
        .panel-header { padding: 0.75rem 1rem; background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color); font-size: 0.7rem;  letter-spacing: 0.1em; color: var(--accent-red); }
        .panel-body { padding: 1rem; }
        .panel-body p { color: var(--text-secondary); line-height: 1.8; margin-bottom: 0.75rem; font-size: 0.85rem; }
        .panel-body p:last-child { margin-bottom: 0; }
        .panel-body a { color: var(--accent-red); text-decoration: none; }
        .panel-body a:hover { text-decoration: underline; }

        .capability-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
        .capability { background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 3px; padding: 1rem; text-align: center; }
        .capability-icon { font-size: 1.25rem; margin-bottom: 0.5rem; }
        .capability-name { font-size: 0.7rem; font-weight: 600;  letter-spacing: 0.05em; margin-bottom: 0.25rem; }
        .capability-desc { font-size: 0.65rem; color: var(--text-muted); }

        .warning { background: rgba(220, 38, 38, 0.1); border: 1px solid var(--accent-red); border-radius: 3px; padding: 1rem; margin-top: 1rem; }
        .warning-title { color: var(--accent-red); font-size: 0.7rem;  letter-spacing: 0.1em; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
        .warning p { color: var(--text-secondary); font-size: 0.8rem; line-height: 1.6; }

        .version { text-align: center; padding: 1.5rem; color: var(--text-muted); font-size: 0.75rem; letter-spacing: 0.1em; }

        .footer { text-align: center; padding: 1.5rem; font-size: 0.65rem; color: var(--text-muted); border-top: 1px solid var(--border-color); }
        .footer a { color: var(--accent-red); text-decoration: none; }

        @media (max-width: 600px) { .capability-grid { grid-template-columns: repeat(2, 1fr); } }
    </style>
</head>
<body>
    <header class="topbar">
        <div class="topbar-left">
            <a href="/" class="brand"><svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7 7 10 10-5 5V2l5 5L7 17"/></svg><span class="brand-text">Blue<span>Watch</span></span></a>
            <nav class="nav">
                <a href="/" class="nav-link">Dashboard</a>
                <a href="/all" class="nav-link">All devices</a>
                <a href="/settings" class="nav-link">Config</a>
            </nav>
        </div>
        <div><button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle light/dark mode">☀</button></div>
    </header>

    <main class="main">
        <div class="hero">
            <div class="hero-icon">◉</div>
            <h1 class="hero-title">BLUE<span>HOOD</span></h1>
            <p class="hero-tagline">Bluetooth Reconnaissance Framework</p>
        </div>

        <div class="panel">
            <div class="panel-header">Mission Brief</div>
            <div class="panel-body">
                <p>BlueWatch is a passive Bluetooth reconnaissance tool designed for authorized security assessments and research. It enables operators to identify, classify, and track Bluetooth-enabled devices within radio range.</p>
                <p>Developed in response to the <a href="https://whisperpair.eu/">WhisperPair vulnerability</a> (CVE-2025-36911), this framework demonstrates the surveillance potential of Bluetooth metadata collection.</p>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">Capabilities</div>
            <div class="panel-body">
                <div class="capability-grid">
                    <div class="capability">
                        <div class="capability-icon">📡</div>
                        <div class="capability-name">Dual-Mode Scan</div>
                        <div class="capability-desc">BLE + Classic BT</div>
                    </div>
                    <div class="capability">
                        <div class="capability-icon">🔍</div>
                        <div class="capability-name">OUI Lookup</div>
                        <div class="capability-desc">Vendor identification</div>
                    </div>
                    <div class="capability">
                        <div class="capability-icon">📊</div>
                        <div class="capability-name">Pattern Intel</div>
                        <div class="capability-desc">Behavioral analysis</div>
                    </div>
                    <div class="capability">
                        <div class="capability-icon">🔔</div>
                        <div class="capability-name">Alert System</div>
                        <div class="capability-desc">Push notifications</div>
                    </div>
                    <div class="capability">
                        <div class="capability-icon">⭐</div>
                        <div class="capability-name">Target Watch</div>
                        <div class="capability-desc">Priority tracking</div>
                    </div>
                    <div class="capability">
                        <div class="capability-icon">🔐</div>
                        <div class="capability-name">MAC Filter</div>
                        <div class="capability-desc">Randomized detection</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">Legal Notice</div>
            <div class="panel-body">
                <div class="warning">
                    <div class="warning-title">⚠ Authorization Required</div>
                    <p>This tool is intended for authorized security testing, research, and educational purposes only. Operators must ensure compliance with applicable laws and obtain proper authorization before deployment. Unauthorized surveillance of Bluetooth devices may violate privacy laws in your jurisdiction.</p>
                </div>
            </div>
        </div>

        <div class="version">v0.5.0 // BUILD 2026.01</div>
    </main>

    

    <script>
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            const btn = document.getElementById('theme-toggle');
            if (btn) btn.textContent = theme === 'light' ? '☽' : '☀';
        }
        function toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            localStorage.setItem('bluewatch_theme', next);
            applyTheme(next);
        }
        applyTheme(localStorage.getItem('bluewatch_theme') || 'dark');
    </script>
</body>
</html>
"""

LIVE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BlueWatch - Live</title>
    <style>
        :root {
            --bg-primary: #0d0d0d;
            --bg-secondary: #141414;
            --bg-tertiary: #1a1a1a;
            --bg-hover: #242424;
            --bg-panel: #111111;
            --text-primary: #e0e0e0;
            --text-secondary: #888888;
            --text-muted: #555555;
            --accent-red: #2563eb;
            --accent-orange: #ea580c;
            --accent-amber: #d97706;
            --accent-green: #16a34a;
            --accent-blue: #2563eb;
            --accent-cyan: #0891b2;
            --border-color: #2a2a2a;
            --border-active: #404040;
            --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', Consolas, monospace;
        }

        [data-theme="light"] {
            --bg-primary: #f5f5f5;
            --bg-secondary: #e8e8e8;
            --bg-tertiary: #ffffff;
            --bg-hover: #d8d8d8;
            --bg-panel: #efefef;
            --text-primary: #1a1a1a;
            --text-secondary: #555555;
            --text-muted: #888888;
            --border-color: #cccccc;
            --border-active: #999999;
        }

        [data-theme="light"] .type-phone { background: #dbeafe; color: #1d4ed8; }
        [data-theme="light"] .type-laptop { background: #ccfbf1; color: #0f766e; }
        [data-theme="light"] .type-audio { background: #f3e8ff; color: #7c3aed; }
        [data-theme="light"] .type-watch { background: #dcfce7; color: #15803d; }
        [data-theme="light"] .type-smart { background: #fef3c7; color: #b45309; }
        [data-theme="light"] .type-tv { background: #fce7f3; color: #be185d; }
        [data-theme="light"] .type-vehicle { background: #fef9c3; color: #a16207; }
        [data-theme="light"] .type-unknown { background: #e5e5e5; color: #555; }
        [data-theme="light"] .modal-overlay.active { background: rgba(0, 0, 0, 0.5); }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        /* Thin, subtle scrollbars */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--border-active); }
        * { scrollbar-width: thin; scrollbar-color: var(--border-color) transparent; }

        body {
            font-family: var(--font-mono);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            font-size: 13px;
            line-height: 1.5;
        }

        /* Top Bar */
        .topbar {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .topbar-left {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            color: inherit;
        }

        .brand-icon {
            color: var(--accent-blue);
            width: 1.1rem;
            height: 1.1rem;
        }

        .brand-text {
            font-weight: 700;
            font-size: 0.9rem;
            letter-spacing: 0.05em;
            
            color: var(--accent-blue);
        }

        .brand-text span {
            color: #ffffff;
        }

        .nav {
            display: flex;
            gap: 0.25rem;
        }

        .nav-link {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.75rem;
            padding: 0.4rem 0.75rem;
            border-radius: 3px;
            
            letter-spacing: 0.05em;
            transition: all 0.1s;
        }

        .nav-link:hover, .nav-link.active {
            color: var(--text-primary);
            background: var(--bg-tertiary);
        }

        .topbar-right {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .total-units {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .total-units-icon {
            color: var(--accent-blue);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.7rem;
            
            letter-spacing: 0.1em;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 6px var(--accent-green);
            animation: pulse 2s infinite;
        }

        .status-dot.scanning { background: var(--accent-amber); box-shadow: 0 0 6px var(--accent-amber); }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .timestamp {
            font-size: 0.7rem;
            color: var(--text-muted);
        }

        /* Main Layout */
        .main {
            display: grid;
            grid-template-columns: 320px 1fr;
            min-height: calc(100vh - 45px);
        }

        /* Sidebar */
        .sidebar {
            background: var(--bg-panel);
            border-right: 1px solid var(--border-color);
            padding: 1rem;
            overflow-y: auto;
            position: sticky;
            top: 45px;
            height: calc(100vh - 45px);
            align-self: start;
        }

        .panel {
            margin-bottom: 1.5rem;
        }

        .panel-header {
            font-size: 0.65rem;
            
            letter-spacing: 0.15em;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        .stat-grid {
            display: grid;
            gap: 0.5rem;
        }

        .stat-item {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .stat-label {
            font-size: 0.6rem;
            color: var(--text-secondary);

            letter-spacing: 0.05em;
        }

        .stat-value {
            font-size: 0.95rem;
            font-weight: 700;
        }

        .stat-value.red { color: var(--accent-red); }
        .stat-value.amber { color: var(--accent-amber); }
        .stat-value.green { color: var(--accent-green); }
        .stat-value.blue { color: var(--accent-blue); }

        /* Filters */
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .category-node {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.35rem 0.5rem;
            border-radius: 3px;
            cursor: grab;
            font-size: 0.78rem;
        }
        .category-node:hover { background: var(--bg-tertiary); }
        .category-node.active { background: var(--bg-tertiary); box-shadow: inset 2px 0 0 var(--accent-blue); }
        .category-node.category-drop-target { outline: 2px dashed var(--accent-blue); outline-offset: -2px; }
        .category-children { margin-left: 1.1rem; border-left: 1px solid var(--border-color); }
        .category-label { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .category-delete {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.9rem;
            line-height: 1;
            padding: 0 0.25rem;
        }
        .category-delete:hover { color: var(--accent-red); }

        .filter-btn {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 0.75rem;
            padding: 0.5rem 0.75rem;
            text-align: left;
            cursor: pointer;
            border-radius: 3px;
            transition: all 0.1s;
            display: flex;
            justify-content: space-between;
        }

        .filter-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }

        .filter-btn.active {
            background: var(--bg-tertiary);
            border-color: var(--accent-red);
            color: var(--text-primary);
        }

        .filter-count {
            color: var(--text-muted);
            font-size: 0.7rem;
        }

        /* Content Area */
        .content {
            padding: 1rem;
            overflow-y: auto;
        }

        /* Search Bar */
        .search-bar {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .search-input {
            flex: 1;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 0.6rem 0.75rem;
            color: var(--text-primary);
            font-family: var(--font-mono);
            font-size: 0.8rem;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--accent-red);
        }

        .search-input::placeholder { color: var(--text-muted); }

        .form-input {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 0.6rem 0.75rem;
            color: var(--text-primary);
            font-family: var(--font-mono);
            font-size: 0.8rem;
            width: 100%;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-red);
        }

        .kbd {
            display: inline-block;
            padding: 0.15rem 0.4rem;
            font-size: 0.65rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 2px;
            color: var(--text-muted);
        }

        .btn {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 0.7rem;
            padding: 0.6rem 1rem;
            cursor: pointer;
            border-radius: 3px;
            
            letter-spacing: 0.05em;
            transition: all 0.1s;
        }

        .btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
            border-color: var(--border-active);
        }

        .btn-primary {
            background: var(--accent-red);
            border-color: var(--accent-red);
            color: white;
        }

        .btn-primary:hover {
            background: #1d4ed8;
        }

        /* Live stats */
        .stat-card { background: var(--bg-panel); border: 1px solid var(--border-color); border-radius: 4px; padding: 0.5rem 0.6rem; }
        .stat-sub { font-size: 0.6rem; color: var(--text-secondary); margin-top: 0.15rem; }
        /* No bulk-select/merge toolbar on the live dashboard -- the checkbox
           column it drove has nothing left to trigger. */
        .select-col { display: none; }

        /* Device Table */
        .table-container {
            background: var(--bg-panel);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            overflow: hidden;
        }

        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border-color);
        }

        .table-title {
            font-size: 0.7rem;
            
            letter-spacing: 0.1em;
            color: var(--text-secondary);
        }

        .table-actions {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            align-items: center;
        }

        .selected-summary {
            color: var(--accent-amber);
        }

        .device-table {
            width: 100%;
            border-collapse: collapse;
        }

        .device-table th {
            text-align: left;
            padding: 0.6rem 0.75rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 0.65rem;
            font-weight: 600;

            letter-spacing: 0.1em;
            color: var(--text-muted);
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
        }

        .device-table th.select-col,
        .device-table td.select-col {
            width: 34px;
            padding: 0.4rem 0.5rem;
            text-align: center;
        }

        .row-select-checkbox {
            accent-color: var(--accent-red);
            cursor: pointer;
        }

        .device-table th.sortable {
            cursor: pointer;
            user-select: none;
            transition: color 0.1s ease, background 0.1s ease;
        }

        .device-table th.sortable:hover {
            color: var(--text-primary);
            background: var(--bg-tertiary);
        }

        .device-table th.sortable.active {
            color: var(--text-primary);
            background: var(--bg-tertiary);
        }

        .sort-indicator {
            margin-left: 0.35rem;
            font-size: 0.6rem;
            opacity: 0.7;
        }

        .device-table td {
            padding: 0.6rem 0.75rem;
            font-size: 0.8rem;
            border-bottom: 1px solid var(--border-color);
            vertical-align: middle;
        }

        .device-table tr:hover {
            background: var(--bg-hover);
        }

        .device-table tr.selected {
            background: rgba(220, 38, 38, 0.15);
        }

        .device-table tr.selected:hover {
            background: rgba(220, 38, 38, 0.22);
        }

        .device-table tr:last-child td { border-bottom: none; }

        .device-table tr { cursor: pointer; user-select: none; }

        .bulk-select {
            min-width: 140px;
            font-size: 0.7rem;
            padding: 0.4rem 0.5rem;
        }

        .pagination-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.75rem;
            padding: 0.65rem 0.9rem;
            border-top: 1px solid var(--border-color);
            background: var(--bg-tertiary);
            flex-wrap: wrap;
        }

        .pagination-left,
        .pagination-right {
            display: flex;
            align-items: center;
            gap: 0.45rem;
        }

        .pagination-center {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            flex-wrap: wrap;
            justify-content: center;
        }

        .page-numbers {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            flex-wrap: wrap;
        }

        .page-number-btn {
            min-width: 2rem;
            padding: 0.35rem 0.45rem;
            font-size: 0.7rem;
            line-height: 1;
        }

        .page-number-btn.active {
            background: var(--accent-red);
            border-color: var(--accent-red);
            color: #fff;
        }

        .page-ellipsis {
            color: var(--text-muted);
            font-size: 0.75rem;
            padding: 0 0.1rem;
        }

        /* Device Type Badge */
        .identity-badge {
            display: inline-block;
            padding: 0.05rem 0.4rem;
            border-radius: 8px;
            font-size: 0.65rem;
            background: var(--accent-blue);
            color: white;
        }

        .type-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.2rem 0.5rem;
            border-radius: 2px;
            font-size: 0.7rem;
            font-weight: 500;

            letter-spacing: 0.05em;
        }

        .type-phone { background: #1e3a5f; color: #60a5fa; }
        .type-laptop { background: #1a3a3a; color: #5eead4; }
        .type-audio { background: #3a1e3a; color: #c084fc; }
        .type-watch { background: #1e3a2e; color: #4ade80; }
        .type-smart { background: #3a2e1e; color: #fbbf24; }
        .type-tv { background: #3a1e2e; color: #f472b6; }
        .type-vehicle { background: #3a3a1e; color: #facc15; }
        .type-unknown { background: #2a2a2a; color: #888; }

        .mac-addr {
            font-size: 0.75rem;
            color: var(--text-secondary);
            letter-spacing: 0.02em;
        }

        .vendor-name {
            color: var(--text-muted);
            font-size: 0.75rem;
        }

        .device-name {
            color: var(--text-primary);
        }

        .sighting-count {
            font-size: 0.8rem;
            color: var(--accent-amber);
        }

        .last-seen {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .last-seen.recent {
            color: var(--accent-green);
        }

        .watched-star {
            color: var(--accent-amber);
            margin-right: 0.25rem;
        }

        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.15s;
        }

        .modal-overlay.active {
            opacity: 1;
            pointer-events: all;
        }

        .modal {
            background: var(--bg-panel);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            width: 90%;
            max-width: 700px;
            max-height: 85vh;
            overflow-y: auto;
        }

        .modal-header {
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-tertiary);
        }

        .modal-title {
            font-size: 0.8rem;
            
            letter-spacing: 0.1em;
        }

        .modal-close {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 1.25rem;
            line-height: 1;
        }

        .modal-close:hover { color: var(--text-primary); }

        .modal-body {
            padding: 1rem;
        }

        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.15rem 1rem;
            margin-bottom: 1rem;
        }

        .detail-item {
            padding: 0.35rem 0;
            border-bottom: 1px solid var(--border-color);
        }

        .detail-item.full { grid-column: 1 / -1; }

        .detail-label {
            font-size: 0.6rem;
            
            letter-spacing: 0.1em;
            color: var(--text-muted);
            margin-bottom: 0.15rem;
        }

        .detail-value {
            font-size: 0.85rem;
            color: var(--text-primary);
            word-break: break-all;
        }

        .detail-value.mono { font-family: var(--font-mono); }
        .detail-value.highlight { color: var(--accent-amber); }

        /* Editable fields (Identifier/Type/Vendor OUI/Group) inside the
        detail grid -- flattened to look like plain text (no visible
        box/border/background), matching Address's plain label+value
        look, while staying fully editable underneath. */
        .detail-item .form-input {
            border: none;
            background: transparent;
            padding: 0;
            width: auto;
            max-width: 100%;
        }
        .detail-item select.form-input { cursor: pointer; }

        /* Heatmaps */
        .heatmap-section {
            margin-top: 1rem;
        }

        .heatmap-title {
            font-size: 0.65rem;

            letter-spacing: 0.1em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }

        /* Two sections side by side instead of stacked -- compresses the
        modal's overall height noticeably on the wider layout above. */
        .heatmap-grid-2col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0 1.25rem;
        }
        .heatmap-grid-2col .heatmap-section { margin-top: 1rem; }
        @media (max-width: 640px) {
            .heatmap-grid-2col { grid-template-columns: 1fr; }
        }

        .dwell-stat-card {
            padding: 0.2rem 0;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }
        .dwell-stat-value { font-size: 1.15rem; font-weight: 700; line-height: 1; }
        .dwell-stat-label {
            font-size: 0.55rem;
            letter-spacing: 0.08em;
            color: var(--text-muted);
        }

        .heatmap {
            font-size: 0.8rem;
        }

        .heatmap-labels {
            color: var(--text-muted);
            font-size: 0.65rem;
            margin-bottom: 0.25rem;
        }

        .activity-grid {
            display: grid;
            gap: 3px;
        }

        .activity-grid.hourly {
            grid-template-columns: repeat(24, 1fr);
        }

        .activity-grid.daily {
            grid-template-columns: repeat(7, 1fr);
        }

        .activity-cell {
            aspect-ratio: 1;
            max-height: 26px;
            border-radius: 2px;
            background: var(--bg-hover);
            cursor: pointer;
            transition: opacity 0.1s;
        }

        .activity-cell:hover { opacity: 0.8; }
        .activity-cell.l1 { background: rgba(220, 38, 38, 0.25); }
        .activity-cell.l2 { background: rgba(220, 38, 38, 0.5); }
        .activity-cell.l3 { background: rgba(220, 38, 38, 0.75); }
        .activity-cell.l4 { background: var(--accent-red); }

        .activity-labels {
            display: grid;
            gap: 3px;
            margin-top: 2px;
            font-size: 0.55rem;
            color: var(--text-muted);
            text-align: center;
        }

        .activity-labels.hourly { grid-template-columns: repeat(24, 1fr); }
        .activity-labels.daily { grid-template-columns: repeat(7, 1fr); }

        /* Timeline Chart */
        .timeline-chart {
            display: flex;
            align-items: flex-end;
            gap: 2px;
            height: 50px;
            padding: 0.5rem 0;
        }

        .timeline-bar {
            flex: 1;
            min-width: 3px;
            background: var(--accent-red);
            border-radius: 1px 1px 0 0;
            transition: background 0.1s;
            cursor: pointer;
            opacity: 0.7;
        }

        .timeline-bar:hover {
            opacity: 1;
            background: var(--accent-orange);
        }

        .timeline-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.6rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }

        /* RSSI Chart */
        .rssi-chart {
            position: relative;
            height: 70px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 0.5rem;
            overflow: hidden;
        }

        .rssi-chart svg { width: 100%; height: 100%; }
        .rssi-line { fill: none; stroke: #ffffff; stroke-width: 1.5; }
        .rssi-area { fill: url(#rssiGradient); }
        .rssi-label { font-size: 0.55rem; fill: var(--text-muted); }

        /* Action Buttons in Modal */
        .btn-watch {
            background: transparent;
            border: 1px solid var(--accent-amber);
            color: var(--accent-amber);
            padding: 0.3rem 0.7rem;
            font-size: 0.65rem;
        }

        .btn-watch.active {
            background: var(--accent-amber);
            color: #000;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 0.75rem;
            font-size: 0.65rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            background: var(--bg-secondary);
        }

        .footer a { color: var(--accent-red); text-decoration: none; }
        .footer a:hover { text-decoration: underline; }

        .theme-toggle {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 0.75rem;
            padding: 0.3rem 0.5rem;
            cursor: pointer;
            border-radius: 3px;
            transition: all 0.1s;
        }

        .theme-toggle:hover {
            color: var(--text-primary);
            border-color: var(--border-active);
        }

        /* Responsive */
        @media (max-width: 900px) {
            .main { grid-template-columns: 1fr; }
            .sidebar { display: none; }
        }
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
                <a href="/" class="nav-link active">Dashboard</a>
                <a href="/all" class="nav-link">All devices</a>
                <a href="/settings" class="nav-link">Config</a>
            </nav>
        </div>
        <div class="topbar-right">
            <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle light/dark mode">☀</button>
        </div>
    </header>

    <div class="main">
        <aside class="sidebar">
            <div class="panel" id="categories-panel">
                <div class="panel-header">Categories</div>
                <div id="categories-tree" style="padding: 0.5rem;"></div>
                <div style="padding: 0.5rem; display: flex; gap: 0.4rem;">
                    <input type="text" class="search-input" id="new-category-name" placeholder="New category name" style="font-size: 0.75rem; flex: 1;">
                    <button class="btn btn-primary" onclick="createCategory()">+</button>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">Date Range Query</div>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <input type="datetime-local" class="search-input" id="search-start" style="font-size: 0.7rem;">
                    <input type="datetime-local" class="search-input" id="search-end" style="font-size: 0.7rem;">
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn" style="flex:1;" onclick="clearDateFilters()">Clear</button>
                        <button class="btn btn-primary" style="flex:1;" onclick="searchByDateRange()">Query</button>
                    </div>
                    <input type="text" class="search-input" id="search" placeholder="Search MAC, vendor, or identifier..." style="font-size: 0.75rem;">
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">Scan Unit (Batch)</div>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <button class="btn btn-primary" id="batch-scan-btn" onclick="startBatchScan()" style="width: 100%; font-size: 0.75rem;" title="Runs Scan Unit (active GATT read) against every currently-visible Unknown device, one at a time, with a short timeout per device -- most will not answer (out of range, or an iPhone ignoring the connection), so this moves on fast rather than waiting out the full single-scan timeout on each.">⚡ Scan Unknown Devices</button>
                    <div id="batch-scan-progress" hidden>
                        <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.35rem;">
                            <span id="batch-scan-status" style="font-size: 0.7rem; color: var(--text-secondary);">Scanning...</span>
                            <button class="btn" id="batch-scan-cancel-btn" onclick="cancelBatchScan()" style="font-size: 0.65rem; padding: 0.2rem 0.5rem;">Cancel</button>
                        </div>
                        <div style="background: var(--bg-tertiary); border-radius: 3px; height: 5px; overflow: hidden;">
                            <div id="batch-scan-bar" style="background: var(--accent-blue); height: 100%; width: 0%; transition: width 0.2s;"></div>
                        </div>
                        <div id="batch-scan-log" style="margin-top: 0.4rem; font-size: 0.65rem; color: var(--text-muted); max-height: 8rem; overflow-y: auto;"></div>
                    </div>
                </div>
            </div>

        </aside>

        <main class="content">
            <div class="stat-card" style="display: flex; align-items: center; justify-content: space-between; gap: 2rem; margin-bottom: 0.75rem;">
                <div style="display: flex; gap: 2rem;">
                    <div><div class="stat-label">ACTIVE NOW</div><div class="stat-value" id="stat-active-now">--</div></div>
                    <div><div class="stat-label">ALL KNOWN DEVICES</div><div class="stat-value" id="stat-total-devices">--</div></div>
                    <div><div class="stat-label">NEW TODAY (INC. MAC-CHANGE)</div><div class="stat-value" id="stat-new-today">--</div></div>
                    <div><div class="stat-label">NEW TODAY (FIXED)</div><div class="stat-value" id="stat-new-today-fixed">--</div></div>
                </div>
                <div style="border-left: 1px solid var(--border-color); padding-left: 2rem;">
                    <div class="stat-label" style="margin-bottom: 0.35rem;">MOST SEEN (ACTIVE)</div>
                    <div id="most-seen-list" style="display: flex; gap: 1.5rem; flex-wrap: wrap;">--</div>
                </div>
            </div>
            <div class="stat-card" style="margin-bottom: 0.75rem;">
                <div style="display: flex; align-items: center; gap: 1.25rem; margin-bottom: 0.6rem;">
                    <span class="stat-label">FILTERS</span>
                    <button class="filter-btn" id="all-devices-btn" onclick="showAllDevices()" style="gap: 0.4rem; padding: 0.3rem 0.6rem;">All devices <span id="count-all" class="filter-count" style="color: inherit; font-size: inherit;">--</span></button>
                </div>
                <div style="display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap;">
                    <label style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: var(--text-secondary); cursor: pointer;" title="Hides devices BlueWatch has already identified with a known Class (e.g. Tracker, Phone) -- independent of whether they've been filed into a Group.">
                        <input type="checkbox" id="hide-classified-toggle" onchange="toggleHideClassified()">
                        Hide classified
                    </label>
                    <label style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: var(--text-secondary); cursor: pointer;" title="Hides devices already sorted into a category folder -- independent of whether their Class is known.">
                        <input type="checkbox" id="hide-grouped-toggle" onchange="toggleHideGrouped()">
                        Hide grouped
                    </label>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="stat-label">First seen within</span>
                        <input type="range" id="first-seen-slider" min="1" max="7" step="1" value="1" oninput="onFirstSeenSliderChange()" style="width: 120px;">
                        <span id="first-seen-slider-value" style="font-size: 0.75rem; color: var(--text-primary); min-width: 4rem;">off</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="stat-label">Sightings &ge;</span>
                        <input type="range" id="sightings-threshold" min="1" max="50" value="1" step="1" oninput="onSightingsThresholdChange()" style="width: 140px;">
                        <span id="sightings-threshold-value" style="font-size: 0.75rem; color: var(--text-primary); min-width: 2.5rem;">1</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="stat-label">RSSI &ge;</span>
                        <input type="range" id="rssi-threshold" min="-100" max="-20" value="-100" step="1" oninput="onRssiThresholdChange()" style="width: 160px;">
                        <span id="rssi-threshold-value" style="font-size: 0.75rem; color: var(--text-primary); min-width: 4.5rem;">-100 dBm</span>
                    </div>
                </div>
            </div>
            <div class="table-container" id="priority-box" style="margin-bottom: 0.75rem; padding: 0.6rem 0.75rem; display: none;">
                <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.4rem;">
                    <span style="color: #f5c518; font-size: 0.9rem;">★</span>
                    <span class="table-title" style="font-size: 0.8rem;">Priority</span>
                    <span style="font-size: 0.7rem; color: var(--text-muted);">watched devices and type alerts &mdash; always shown, ignores filters</span>
                </div>
                <div id="priority-list" style="display: flex; flex-wrap: wrap; gap: 0.5rem;"></div>
            </div>
            <div class="table-container" id="devices-container">
                <table class="device-table">
                    <thead>
                        <tr>
                            <th class="select-col"><input type="checkbox" id="select-all-checkbox" class="row-select-checkbox" aria-label="Select all rows"></th>
                            <th class="sortable" data-sort="class">Class<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="vendor">Vendor<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="mac">Address<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="identifier">Identifier<span class="sort-indicator"></span></th>
                            <th>RSSI</th>
                            <th class="sortable" data-sort="sightings">Sightings<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="last_seen">Last seen<span class="sort-indicator"></span></th>
                            <th class="sortable" data-sort="group">Group<span class="sort-indicator"></span></th>
                        </tr>
                    </thead>
                    <tbody id="device-list">
                        <tr><td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-muted);">Initializing scanner...</td></tr>
                    </tbody>
                </table>
                <div class="pagination-bar">
                    <div class="pagination-left">
                        <span id="page-info" style="font-size: 0.7rem; color: var(--text-muted);">Page --/--</span>
                    </div>
                    <div class="pagination-center">
                        <button class="btn" id="prev-page-btn" onclick="changePage(-1)">Prev</button>
                        <div class="page-numbers" id="page-numbers"></div>
                        <button class="btn" id="next-page-btn" onclick="changePage(1)">Next</button>
                    </div>
                    <div class="pagination-right">
                        <span style="font-size: 0.7rem; color: var(--text-muted);">Rows/page</span>
                        <select class="form-input bulk-select" id="page-size-select" onchange="changePageSize(this.value)">
                            <option value="25">25</option>
                            <option value="50" selected>50</option>
                            <option value="100">100</option>
                            <option value="150">150</option>
                            <option value="250">250</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="table-container" id="name-groups-container" style="display: none;">
                <div class="table-header">
                    <span class="table-title">Devices Sharing a Name <span id="name-groups-count" class="selected-summary" style="display: none;"></span></span>
                    <span style="font-size: 0.7rem; color: var(--text-muted);">
                        Identical advertised name across multiple MACs — likely MAC randomization.
                    </span>
                </div>
                <div id="name-groups-list" style="padding: 0.5rem 1rem 1rem;">
                    <div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading...</div>
                </div>
            </div>
        </main>
    </div>


    <!-- Target Detail Modal -->
    <div class="modal-overlay" id="device-modal">
        <div class="modal">
            <div class="modal-header">
                <span class="modal-title">Device Details</span>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <button class="btn" id="scan-unit-btn" onclick="scanUnit(currentDeviceMac)" title="Actively contact this device to ask what it supports (BLE GATT services / Classic SDP records). Unlike the rest of BlueWatch, this connects to the device rather than only listening.">Scan Unit</button>
                    <button class="btn btn-watch" id="watch-btn" onclick="toggleWatch(currentDeviceMac)"></button>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
            </div>
            <div class="modal-body" id="modal-content">
                <!-- Dynamic content -->
            </div>
        </div>
    </div>

    <!-- Shortcuts Modal -->
    <div class="modal-overlay" id="shortcuts-modal">
        <div class="modal" style="max-width: 400px;">
            <div class="modal-header">
                <span class="modal-title">Keyboard Shortcuts</span>
                <button class="modal-close" onclick="closeShortcutsModal()">&times;</button>
            </div>
            <div class="modal-body" style="padding: 1rem;">
                <div style="display: grid; gap: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">/</span><span style="color: var(--text-secondary);">Focus search</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">r</span><span style="color: var(--text-secondary);">Refresh devices</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">Esc</span><span style="color: var(--text-secondary);">Close modal</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">w</span><span style="color: var(--text-secondary);">Toggle watch (in modal)</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">1</span><span style="color: var(--text-secondary);">Show all devices</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">2</span><span style="color: var(--text-secondary);">Show watched only</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">3</span><span style="color: var(--text-secondary);">Filter phones</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color);"><span class="kbd">4</span><span style="color: var(--text-secondary);">Filter laptops</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0;"><span class="kbd">5</span><span style="color: var(--text-secondary);">Filter audio</span></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            const btn = document.getElementById('theme-toggle');
            if (btn) btn.textContent = theme === 'light' ? '☽' : '☀';
        }

        function toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            localStorage.setItem('bluewatch_theme', next);
            applyTheme(next);
        }

        applyTheme(localStorage.getItem('bluewatch_theme') || 'dark');

        const PAGE_SIZE_OPTIONS = [25, 50, 100, 150, 250];
        const PAGE_SIZE_STORAGE_KEY = 'bluewatch_page_size_v2';

        function normalizePageSize(value) {
            const parsed = Number.parseInt(value, 10);
            if (!Number.isFinite(parsed)) return 50;
            if (PAGE_SIZE_OPTIONS.includes(parsed)) return parsed;
            return 50;
        }

        let allDevices = [];
        let currentFilter = 'all';
        let currentGroupId = null;
        let hideClassified = localStorage.getItem('bluewatch_hide_classified') === 'true';
        let hideGrouped = localStorage.getItem('bluewatch_hide_grouped') === 'true';
        let rssiThreshold = -100;
        let sightingsThreshold = 1;
        let dateFilteredDevices = null;
        let compactView = localStorage.getItem('bluewatch_compact_view') === 'true';
        let screenshotMode = localStorage.getItem('bluewatch_screenshot_mode') === 'true';
        let clickToOpen = localStorage.getItem('bluewatch_click_to_open') === 'true';
        const defaultSortState = { column: 'last_seen', direction: 'desc' };
        let sortState = { ...defaultSortState };
        let selectedMacs = new Set();
        let lastSelectedIndex = null;
        let currentVisibleDevices = [];
        let rowClickTimer = null;
        let searchDebounceTimer = null;
        let pagination = {
            page: 1,
            pageSize: normalizePageSize(localStorage.getItem(PAGE_SIZE_STORAGE_KEY)),
            totalPages: 1,
            totalMatching: 0,
            hasPrev: false,
            hasNext: false,
        };

        function getServerSortDirection() {
            return sortState.direction;
        }

        function buildDevicesUrl() {
            const params = new URLSearchParams();
            params.set('page', pagination.page);
            params.set('page_size', pagination.pageSize);
            params.set('filter', currentFilter);
            // A specific category is a deliberate historical browse (same as
            // /all), not a "what's nearby right now" query -- only the
            // default/All-devices/hide-categorized views stay live-windowed.
            const hidingAnything = hideClassified || hideGrouped;
            const viewingSpecificCategory = !hidingAnything && currentGroupId !== null && currentGroupId !== '__all__';
            if (!viewingSpecificCategory) {
                params.set('active_within', '60');
            }
            if (hidingAnything) {
                if (hideClassified) params.set('hide_classified', '1');
                if (hideGrouped) params.set('hide_grouped', '1');
            } else if (currentGroupId !== null) {
                params.set('group_id', currentGroupId);
            }
            params.set('sort', sortState.column);
            params.set('direction', getServerSortDirection());

            const searchInput = document.getElementById('search');
            const searchTerm = searchInput ? searchInput.value.trim() : '';
            if (searchTerm) params.set('search', searchTerm);

            const firstSeenLevel = parseInt(document.getElementById('first-seen-slider').value, 10);
            if (firstSeenLevel > 1) {
                params.set('first_seen', FIRST_SEEN_LEVELS[firstSeenLevel - 2]);
            }

            return '/api/devices?' + params.toString();
        }

        // Levels 1-6 on the "First seen within" slider. Untouched (the
        // default) applies no filter at all -- only once the operator
        // actually drags it does it start narrowing to "first seen within
        // this window", same spirit as the Sightings/RSSI sliders but
        // those have a naturally permissive end (1 sighting / -100 dBm
        // effectively shows everyone); first-seen has no such end since
        // even the loosest window (30d) would hide long-established
        // devices, so it stays off until deliberately touched.
        const FIRST_SEEN_LEVELS = ['6h', '12h', '24h', '48h', '7d', '30d'];
        const FIRST_SEEN_LABELS = ['off', '6h', '12h', '24h', '48h', 'this week', 'this month'];

        function onFirstSeenSliderChange() {
            const level = parseInt(document.getElementById('first-seen-slider').value, 10);
            document.getElementById('first-seen-slider-value').textContent = FIRST_SEEN_LABELS[level - 1];
            pagination.page = 1;
            refreshDevices();
        }

        async function loadLiveStats() {
            try {
                const response = await fetch('/api/live-stats?window=60');
                const data = await response.json();
                document.getElementById('stat-active-now').textContent = data.active_now ?? '--';
                document.getElementById('stat-total-devices').textContent = data.total_devices ?? '--';
                document.getElementById('stat-new-today').textContent = data.new_today ?? '--';
                document.getElementById('stat-new-today-fixed').textContent = data.new_today_fixed ?? '--';
                const listEl = document.getElementById('most-seen-list');
                const items = data.most_seen || [];
                if (items.length === 0) {
                    listEl.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;">No data yet</span>';
                } else {
                    listEl.innerHTML = items.map(function(d) {
                        const name = obfuscateName(d.friendly_name || d.vendor || d.mac);
                        return '<div style="min-width: 80px; max-width: 150px;">' +
                            '<div style="font-size: 0.8rem; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="' + escapeHtml(name) + '">' + escapeHtml(name) + '</div>' +
                            '<div style="font-size: 0.6rem; color: var(--text-muted);">' + d.total_sightings + ' sightings</div>' +
                            '</div>';
                    }).join('');
                }
            } catch (error) { console.error('Error loading live stats:', error); }
        }

        function queueDeviceRefresh(resetPage = false) {
            if (resetPage) pagination.page = 1;
            if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                searchDebounceTimer = null;
                refreshDevices();
            }, 250);
        }

        function toggleViewMode() {
            compactView = !compactView;
            localStorage.setItem('bluewatch_compact_view', compactView);
            updateViewToggle();
            renderDevices();
        }

        function updateViewToggle() {
            const btn = document.getElementById('view-toggle');
            if (btn) {
                btn.innerHTML = compactView ? '◫ Detailed View' : '☰ Compact View';
            }
        }

        function toggleScreenshotMode() {
            screenshotMode = !screenshotMode;
            localStorage.setItem('bluewatch_screenshot_mode', screenshotMode);
            updateScreenshotToggle();
            renderDevices();
        }

        function updateScreenshotToggle() {
            const btn = document.getElementById('screenshot-toggle');
            if (btn) {
                btn.innerHTML = screenshotMode ? '📷 Screenshot Mode ON' : '📷 Screenshot Mode';
                btn.style.background = screenshotMode ? 'var(--accent-red)' : '';
                btn.style.color = screenshotMode ? 'white' : '';
            }
        }

        function toggleClickToOpen() {
            clickToOpen = !clickToOpen;
            localStorage.setItem('bluewatch_click_to_open', clickToOpen);
            updateClickToOpenToggle();
        }

        function updateClickToOpenToggle() {
            const btn = document.getElementById('click-to-open-toggle');
            if (btn) {
                btn.innerHTML = clickToOpen ? '👆 Click to Open ON' : '👆 Click to Open';
                btn.style.background = clickToOpen ? 'var(--accent-blue)' : '';
                btn.style.color = clickToOpen ? 'white' : '';
            }
        }

        let nameGroupsActive = false;

        function toggleNameGroups() {
            nameGroupsActive = !nameGroupsActive;
            const devicesEl = document.getElementById('devices-container');
            const groupsEl = document.getElementById('name-groups-container');
            if (devicesEl) devicesEl.style.display = nameGroupsActive ? 'none' : '';
            if (groupsEl) groupsEl.style.display = nameGroupsActive ? '' : 'none';
            const btn = document.getElementById('name-groups-toggle');
            if (btn) {
                btn.innerHTML = nameGroupsActive ? '🔗 Group by Name ON' : '🔗 Group by Name';
                btn.style.background = nameGroupsActive ? 'var(--accent-blue)' : '';
                btn.style.color = nameGroupsActive ? 'white' : '';
            }
            if (nameGroupsActive) loadNameGroups();
        }

        async function loadNameGroups() {
            const container = document.getElementById('name-groups-list');
            const countEl = document.getElementById('name-groups-count');
            if (!container) return;
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading...</div>';
            try {
                const response = await fetch('/api/name-groups');
                const data = await response.json();
                const groups = data.groups || [];
                if (countEl) {
                    countEl.style.display = '';
                    countEl.textContent = '· ' + groups.length + ' name' + (groups.length === 1 ? '' : 's');
                }
                if (groups.length === 0) {
                    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">No names are shared across multiple addresses.</div>';
                    return;
                }
                container.innerHTML = groups.map(renderNameGroup).join('');
            } catch (error) {
                container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Error loading name groups</div>';
            }
        }

        function renderNameGroup(g) {
            const name = obfuscateName(g.name) || '(unnamed)';
            const { text: lastSeen, tooltip: lastSeenTooltip } = formatLastSeen(g.last_seen);
            const vendor = g.vendor ? ' · ' + g.vendor : '';
            const randomized = g.randomized_count > 0
                ? '<span title="' + g.randomized_count + ' of ' + g.device_count + ' addresses are randomized" style="font-size: 0.65rem; color: var(--accent-amber); border: 1px solid var(--accent-amber); border-radius: 3px; padding: 0 0.3rem; margin-left: 0.5rem;">' + g.randomized_count + ' randomized</span>'
                : '';
            const members = (g.macs || []).map(mac => {
                const shownMac = isMacOSUUID(mac) ? obfuscateMAC(mac).substring(0, 13) + '...' : obfuscateMAC(mac);
                return '<div onclick="showDevice(\\'' + mac + '\\')" title="' + mac + '" style="font-family: monospace; font-size: 0.72rem; color: var(--text-secondary); padding: 0.25rem 0.5rem; border-bottom: 1px solid var(--border-color); cursor: pointer;">' + shownMac + '</div>';
            }).join('');
            return '<div style="margin-bottom: 1rem; border: 1px solid var(--border-color); border-radius: 6px; overflow: hidden;">' +
                '<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0.75rem; background: var(--bg-tertiary);">' +
                '<div style="min-width: 0;">' +
                '<span style="font-size: 0.85rem; color: var(--text-primary); font-weight: 600;">' + (g.type_icon || '') + ' ' + name + '</span>' + randomized +
                '<div style="font-size: 0.65rem; color: var(--text-muted);">' + g.device_count + ' addresses' + vendor + ' · ' + g.total_sightings + ' sightings · last seen <span title="' + lastSeenTooltip + '">' + lastSeen + '</span></div>' +
                '</div>' +
                '<span style="font-size: 1.1rem; font-weight: 700; color: var(--accent-blue); margin-left: 0.75rem;">' + g.device_count + '</span>' +
                '</div>' + members + '</div>';
        }

        function isMacOSUUID(addr) {
            return /^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$/.test(addr);
        }

        // Demo Mode: full redaction for public screenshots (all MACs zeroed,
        // names/vendors/categories swapped for generic placeholders) -- a
        // stronger version of Screenshot Mode's partial masking. Enable via
        // the browser console: localStorage.setItem('bluewatch_demo_mode','true'); location.reload();
        let demoMode = localStorage.getItem('bluewatch_demo_mode') === 'true' || new URLSearchParams(window.location.search).get('demo') === '1';
        const DEMO_NAMES = ['Guest Phone', 'Kitchen Speaker', 'Smart Plug', 'Wireless Headset', 'Fitness Tracker', 'Smart TV', 'Tablet', 'Car Bluetooth', 'IoT Sensor', 'Robot Vacuum', 'Doorbell Camera', 'Smart Watch', 'Bluetooth Mouse', 'Game Controller', 'E-bike Lock'];
        let demoNameCounter = 0;

        function obfuscateMAC(mac) {
            if (demoMode) return mac ? '00:00:00:00:00:00' : mac;
            if (!screenshotMode || !mac) return mac;
            // Handle macOS UUID-format addresses
            if (isMacOSUUID(mac)) {
                return mac.substring(0, 8) + '-XXXX-XXXX-XXXX-XXXXXXXXXXXX';
            }
            // Show first 2 octets, hide the rest: AA:BB:XX:XX:XX:XX
            const parts = mac.split(':');
            if (parts.length === 6) {
                return parts[0] + ':' + parts[1] + ':XX:XX:XX:XX';
            }
            return mac.substring(0, 5) + ':XX:XX:XX:XX';
        }

        function obfuscateName(name) {
            if (demoMode) return name ? DEMO_NAMES[(demoNameCounter++) % DEMO_NAMES.length] : name;
            if (!screenshotMode || !name) return name;
            // Show first 2 chars, then asterisks
            if (name.length <= 2) return '**';
            return name.substring(0, 2) + '*'.repeat(Math.min(name.length - 2, 8));
        }

        function showShortcutsModal() {
            document.getElementById('shortcuts-modal').classList.add('active');
        }

        function closeShortcutsModal() {
            document.getElementById('shortcuts-modal').classList.remove('active');
        }

        // Only the newest request may update the screen: a slower, older
        // request (e.g. the live "active now" refresh) finishing after the one
        // for the category just clicked used to put the full list back.
        let devicesRefreshSeq = 0;
        async function refreshDevices() {
            const seq = ++devicesRefreshSeq;
            try {
                const response = await fetch(buildDevicesUrl());
                const data = await response.json();
                if (seq !== devicesRefreshSeq) return;
                allDevices = data.devices || [];
                const knownMacs = new Set(allDevices.map(d => d.mac));
                selectedMacs = new Set([...selectedMacs].filter(mac => knownMacs.has(mac)));
                pagination.page = data.page || pagination.page;
                pagination.pageSize = data.page_size || pagination.pageSize;
                pagination.totalPages = data.total_pages || 1;
                pagination.totalMatching = data.total_matching || 0;
                pagination.hasPrev = !!data.has_prev;
                pagination.hasNext = !!data.has_next;
                localStorage.setItem(PAGE_SIZE_STORAGE_KEY, String(pagination.pageSize));
                updateStats(data);
                updateFilterCounts(data.filter_counts);
                updatePaginationUI();
                if (!dateFilteredDevices) renderDevices();
                updateSelectionUI();
            } catch (error) {
                console.error('Scan error:', error);
            }
        }

        // ==================== Batch Scan Unit ====================
        let batchScanPollTimer = null;

        async function startBatchScan() {
            const macs = currentVisibleDevices.map(d => d.mac);
            if (macs.length === 0) {
                alert('No devices match the current filters to scan.');
                return;
            }
            if (macs.length > 200) {
                alert('Too many devices to batch-scan at once (' + macs.length + ', max 200) -- narrow the filters first (e.g. First seen within, or a higher Sightings threshold).');
                return;
            }
            if (!confirm('Actively connect to ' + macs.length + ' device(s) one at a time to try to identify them? Most will not answer (out of range, or a phone ignoring the connection) -- this may take a few minutes.')) {
                return;
            }

            const btn = document.getElementById('batch-scan-btn');
            btn.disabled = true;
            const panel = document.getElementById('batch-scan-progress');
            panel.hidden = false;
            document.getElementById('batch-scan-bar').style.width = '0%';
            document.getElementById('batch-scan-log').textContent = '';
            document.getElementById('batch-scan-status').textContent = 'Starting...';

            try {
                const response = await fetch('/api/scan-unit/batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ macs: macs })
                });
                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    document.getElementById('batch-scan-status').textContent = err.error || 'Failed to start batch scan';
                    btn.disabled = false;
                    return;
                }
            } catch (error) {
                document.getElementById('batch-scan-status').textContent = 'Failed to start batch scan';
                btn.disabled = false;
                return;
            }

            batchScanPollTimer = setInterval(pollBatchScan, 1000);
            pollBatchScan();
        }

        async function pollBatchScan() {
            let data;
            try {
                const response = await fetch('/api/scan-unit/batch');
                data = await response.json();
            } catch (error) {
                return;
            }

            const total = data.total || 0;
            const completed = data.completed || 0;
            const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
            document.getElementById('batch-scan-bar').style.width = pct + '%';

            const statusEl = document.getElementById('batch-scan-status');
            if (data.running) {
                statusEl.textContent = 'Scanning ' + completed + ' / ' + total + (data.current_mac ? ' -- currently ' + data.current_mac : '');
            } else {
                clearInterval(batchScanPollTimer);
                batchScanPollTimer = null;
                document.getElementById('batch-scan-btn').disabled = false;
                const identified = (data.results || []).filter(r => r.ok && r.applied && Object.keys(r.applied).length > 0).length;
                statusEl.textContent = 'Done: ' + completed + ' scanned, ' + identified + ' identified something new.';
                if (identified > 0) refreshDevices();
            }

            const logEl = document.getElementById('batch-scan-log');
            logEl.textContent = '';
            (data.results || []).slice().reverse().slice(0, 20).forEach(r => {
                const line = document.createElement('div');
                if (r.ok && r.applied && Object.keys(r.applied).length > 0) {
                    line.style.color = 'var(--accent-green, #22c55e)';
                    line.textContent = r.mac + ': identified (' + Object.entries(r.applied).map(([k, v]) => k + '=' + v).join(', ') + ')';
                } else if (r.ok) {
                    line.textContent = r.mac + ': connected, nothing new to add';
                } else {
                    line.textContent = r.mac + ': ' + (r.error || 'failed');
                }
                logEl.appendChild(line);
            });
        }

        async function cancelBatchScan() {
            try {
                await fetch('/api/scan-unit/batch', { method: 'DELETE' });
            } catch (error) { /* best-effort */ }
        }

        function updateStats(data) {
            // (Total units seen was removed from the header -- data.total
            // is still returned by the API but nothing displays it now.)
        }

        // ==================== Live sighting stream (SSE) ====================
        // /api/live-events pushes the instant a device is upserted from a
        // scan (daemon.py, right after db.upsert_device()) -- rather than
        // waiting up to the poll interval (setInterval(refreshDevices,...)
        // below) to notice it. Deliberately does NOT merge the pushed
        // device into allDevices client-side (that array is one server-
        // computed page under the current filter/sort -- blindly inserting
        // a device risks putting it somewhere it doesn't belong, e.g. past
        // a filter that would exclude it). Instead each push triggers a
        // debounced real refresh -- coalesces a burst of many devices from
        // one scan cycle into a single fetch instead of one per device --
        // so what's on screen is always server-truth, just fetched near-
        // instantly instead of on the next scheduled tick.
        let liveEventSource = null;
        let liveRefreshDebounce = null;
        function startLiveEventStream() {
            if (liveEventSource) return;
            liveEventSource = new EventSource('/api/live-events');
            liveEventSource.onmessage = () => {
                clearTimeout(liveRefreshDebounce);
                liveRefreshDebounce = setTimeout(() => {
                    refreshDevices();
                    loadPriorityDevices();
                }, 200);
            };
            // EventSource reconnects on its own after a drop/server
            // restart -- nothing to do here beyond letting it retry.
        }

        // ==================== Priority box (watched + type alerts) ====================
        // Always-visible box that surfaces watched devices and devices whose
        // type is on the Type-Based Alerts list (Config > Alerts), ignoring
        // whatever filters are active in the main table below -- so e.g. a
        // brand-new drone MAC still jumps out even if "Hide categorized" or
        // a First Seen filter would otherwise hide it.
        async function loadPriorityDevices() {
            try {
                const res = await fetch('/api/devices/priority');
                const data = await res.json();
                renderPriorityBox(data.devices || []);
            } catch (e) {
                console.error('Failed to load priority devices:', e);
            }
        }

        function renderPriorityBox(devices) {
            const box = document.getElementById('priority-box');
            const list = document.getElementById('priority-list');
            if (!box || !list) return;
            if (devices.length === 0) {
                box.style.display = 'none';
                return;
            }
            box.style.display = '';
            list.innerHTML = devices.map(d => {
                const name = obfuscateName(d.friendly_name || d.vendor || d.mac);
                const badge = d.reason === 'watched'
                    ? '<span style="color:#f5c518;" title="Watched device">★</span>'
                    : '<span style="color:#f59e0b; font-size:0.6rem; font-weight:600; letter-spacing:0.03em;" title="Type alert: ' + escapeHtml(d.type_label) + '">ALERT</span>';
                return '<div onclick="showDevice(\\'' + d.mac + '\\')" style="cursor:pointer; display:flex; align-items:center; gap:0.4rem; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 0.3rem 0.6rem; font-size: 0.75rem;">'
                    + badge
                    + '<span class="type-badge ' + getTypeClass(d.device_type) + '" style="font-size:0.65rem; padding:0.1rem 0.35rem;">' + d.type_icon + '</span>'
                    + '<span>' + escapeHtml(name) + '</span>'
                    + '</div>';
            }).join('');
        }

        // ==================== Categories (sidebar tree) ====================
        let categoriesCache = [];

        async function loadCategories() {
            try {
                const res = await fetch('/api/groups');
                const data = await res.json();
                categoriesCache = data.groups || [];
                cachedGroups = categoriesCache;  // single source of truth -- see loadGroupsForDevice/loadGroupsForBulkSelect
                renderCategoryTree();
            } catch (e) {
                console.error('Failed to load categories:', e);
            }
        }

        function groupOptionLabel(g) {
            if (g.parent_id) {
                const parent = cachedGroups.find(p => p.id === g.parent_id);
                return (parent ? parent.name + ' › ' : '') + g.name;
            }
            return g.name;
        }

        function renderCategoryTree() {
            const el = document.getElementById('categories-tree');
            if (!el) return;
            const topLevel = categoriesCache.filter(g => !g.parent_id);
            if (topLevel.length === 0) {
                el.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-muted); padding: 0.5rem 0.25rem;">No categories yet</div>';
                return;
            }
            el.innerHTML = topLevel.map(g => renderCategoryNode(g)).join('');
        }

        function renderCategoryNode(group) {
            const children = categoriesCache.filter(g => g.parent_id === group.id);
            const childrenHtml = children.length
                ? '<div class="category-children">' + children.map(c => renderCategoryNode(c)).join('') + '</div>'
                : '';
            const isActive = currentGroupId === group.id;
            return (
                '<div class="category-node' + (isActive ? ' active' : '') + '" draggable="true" data-id="' + group.id + '" ' +
                'ondragstart="onCategoryDragStart(event, ' + group.id + ')" ' +
                'ondragover="onCategoryDragOver(event)" ' +
                'ondragleave="onCategoryDragLeave(event)" ' +
                'ondrop="onCategoryDrop(event, ' + group.id + ')">' +
                '<span class="category-label" style="color:' + (group.color || '#3b82f6') + '" onclick="selectCategory(' + group.id + ')" title="Click to show only this category\\'s devices, drag onto another category to nest it as a subcategory">' +
                (group.icon || '📁') + ' ' + escapeHtml(obfuscateName(group.name)) +
                '</span>' +
                '<button class="category-delete" onclick="deleteCategory(' + group.id + ')" title="Delete category">×</button>' +
                '</div>' + childrenHtml
            );
        }

        function selectCategory(groupId) {
            currentGroupId = (currentGroupId === groupId) ? null : groupId;
            currentFilter = 'all';
            // Picking a specific category and hiding all categorized devices
            // are contradictory -- the category selection wins, and the
            // checkbox unchecking itself makes that visible instead of the
            // click silently doing nothing.
            setHideClassified(false);
            setHideGrouped(false);
            const allBtn = document.getElementById('all-devices-btn');
            if (allBtn) allBtn.classList.remove('active');
            renderCategoryTree();
            selectedMacs.clear();
            lastSelectedIndex = null;
            pagination.page = 1;
            refreshDevices();
        }

        function showAllDevices() {
            currentGroupId = '__all__';
            currentFilter = 'all';
            setHideClassified(false);
            setHideGrouped(false);
            renderCategoryTree();
            selectedMacs.clear();
            lastSelectedIndex = null;
            pagination.page = 1;
            refreshDevices();
        }

        function setHideClassified(value) {
            hideClassified = value;
            localStorage.setItem('bluewatch_hide_classified', hideClassified);
            const checkbox = document.getElementById('hide-classified-toggle');
            if (checkbox) checkbox.checked = value;
        }

        function toggleHideClassified() {
            const checkbox = document.getElementById('hide-classified-toggle');
            setHideClassified(checkbox ? checkbox.checked : false);
            selectedMacs.clear();
            lastSelectedIndex = null;
            pagination.page = 1;
            refreshDevices();
        }

        function setHideGrouped(value) {
            hideGrouped = value;
            localStorage.setItem('bluewatch_hide_grouped', hideGrouped);
            const checkbox = document.getElementById('hide-grouped-toggle');
            if (checkbox) checkbox.checked = value;
        }

        function toggleHideGrouped() {
            const checkbox = document.getElementById('hide-grouped-toggle');
            setHideGrouped(checkbox ? checkbox.checked : false);
            selectedMacs.clear();
            lastSelectedIndex = null;
            pagination.page = 1;
            refreshDevices();
        }

        function onRssiThresholdChange() {
            const slider = document.getElementById('rssi-threshold');
            rssiThreshold = parseInt(slider.value, 10);
            document.getElementById('rssi-threshold-value').textContent = rssiThreshold + ' dBm';
            renderDevices();
        }

        function onSightingsThresholdChange() {
            const slider = document.getElementById('sightings-threshold');
            sightingsThreshold = parseInt(slider.value, 10);
            document.getElementById('sightings-threshold-value').textContent = sightingsThreshold;
            renderDevices();
        }

        function escapeHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }

        // Apple Continuity "Nearby Info" live activity snapshot (screen
        // on/idle/driving, etc.) -- only shown when the device has ever
        // produced one (Apple devices only) and it's recent enough to
        // still reflect current state rather than something stale from
        // long before the device was last even seen.
        function appleActivityHtml(d) {
            if (!d.apple_activity || !d.apple_activity_at) return '';
            const ageMs = Date.now() - new Date(d.apple_activity_at).getTime();
            if (ageMs > 5 * 60 * 1000) return '';
            const a = d.apple_activity;
            let screenLabel = 'unknown';
            let screenColor = 'var(--text-muted)';
            if (a.screen_on === true) { screenLabel = 'on'; screenColor = '#16a34a'; }
            else if (a.screen_on === false) { screenLabel = 'off'; screenColor = '#555'; }
            let line = 'Screen: <span style="color:' + screenColor + ';">' + screenLabel + '</span> — ' + escapeHtml(a.activity || '');
            const extras = [];
            if (a.wifi_on === true) extras.push('WiFi on');
            if (a.watch_locked === true) extras.push('Watch locked');
            if (a.airdrop_receiving === true) extras.push('AirDrop on');
            if (extras.length) line += ' (' + extras.join(', ') + ')';
            return '<div class="detail-item full"><div class="detail-label">Apple Activity (live)</div><div class="detail-value" style="font-size:0.8rem;">' + line + '</div></div>';
        }

        // Samsung VD-family power state (TV/AV/monitor/fridge) -- same
        // live/recent-only treatment as appleActivityHtml above.
        function samsungStatusHtml(d) {
            if (!d.samsung_status || !d.samsung_status_at) return '';
            const ageMs = Date.now() - new Date(d.samsung_status_at).getTime();
            if (ageMs > 5 * 60 * 1000) return '';
            const s = d.samsung_status;
            const powerColors = { on: '#16a34a', standby: '#d97706', off: '#555' };
            const color = powerColors[s.power] || 'var(--text-muted)';
            const line = escapeHtml(s.device_class || 'device') + ': <span style="color:' + color + ';">' + escapeHtml(s.power || 'unknown') + '</span>';
            return '<div class="detail-item full"><div class="detail-label">Samsung Status (live)</div><div class="detail-value" style="font-size:0.8rem;">' + line + '</div></div>';
        }

        // Fast Pair Battery Notification (earbuds/case) -- same
        // live/recent-only treatment as appleActivityHtml above.
        function fastpairBatteryHtml(d) {
            if (!d.fastpair_battery || !d.fastpair_battery_at) return '';
            const ageMs = Date.now() - new Date(d.fastpair_battery_at).getTime();
            if (ageMs > 5 * 60 * 1000) return '';
            const b = d.fastpair_battery;
            const labels = { left: 'L', right: 'R', case: 'Case' };
            const parts = [];
            for (const key of ['left', 'right', 'case']) {
                const comp = b[key];
                if (!comp) continue;
                let seg = labels[key] + ' ' + (comp.pct === null || comp.pct === undefined ? '?' : comp.pct + '%');
                if (comp.charging) seg += '⚡';
                parts.push(seg);
            }
            if (!parts.length) return '';
            return '<div class="detail-item full"><div class="detail-label">Battery (live)</div><div class="detail-value" style="font-size:0.8rem;">' + parts.join(' · ') + '</div></div>';
        }

        // ASTM F3411/OpenDroneID Remote ID -- same live/recent-only
        // treatment as appleActivityHtml above. Only one ASTM message
        // type arrives per advertisement (Basic ID, Location, Self ID,
        // System, or Operator ID), so this renders whatever the most
        // recent sighting happened to carry, not an accumulated picture.
        function droneStateHtml(d) {
            if (!d.drone_state || !d.drone_state_at) return '';
            const ageMs = Date.now() - new Date(d.drone_state_at).getTime();
            if (ageMs > 5 * 60 * 1000) return '';
            const s = d.drone_state;
            const parts = [];
            if (s.uas_id) parts.push('UAS ID ' + escapeHtml(s.uas_id) + (s.ua_type ? ' (' + escapeHtml(s.ua_type) + ')' : ''));
            if (s.latitude !== undefined && s.longitude !== undefined) {
                let pos = 'Position ' + s.latitude + ', ' + s.longitude;
                if (s.altitude_m !== undefined) pos += ' @ ' + s.altitude_m + 'm';
                parts.push(pos);
            }
            if (s.status) parts.push('Status: ' + escapeHtml(s.status));
            if (s.self_id) parts.push('"' + escapeHtml(s.self_id) + '"');
            if (s.operator_latitude !== undefined && s.operator_longitude !== undefined) {
                parts.push('Operator @ ' + s.operator_latitude + ', ' + s.operator_longitude);
            }
            if (s.operator_id) parts.push('Operator ID ' + escapeHtml(s.operator_id));
            if (!parts.length) return '';
            return '<div class="detail-item full"><div class="detail-label">Drone Remote ID (live)</div><div class="detail-value" style="font-size:0.8rem;">' + parts.join(' · ') + '</div></div>';
        }

        async function createCategory() {
            const input = document.getElementById('new-category-name');
            const name = (input.value || '').trim();
            if (!name) return;
            try {
                await fetch('/api/groups', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, color: '#3b82f6', icon: '📁' }),
                });
                input.value = '';
                await loadCategories();
            } catch (e) {
                console.error('Failed to create category:', e);
            }
        }

        async function deleteCategory(groupId) {
            if (!confirm('Delete this category? Devices in it revert to Unknown; subcategories are promoted to top-level.')) return;
            try {
                await fetch('/api/groups/' + groupId, { method: 'DELETE' });
                await loadCategories();
            } catch (e) {
                console.error('Failed to delete category:', e);
            }
        }

        let draggedCategoryId = null;
        let draggedDeviceMac = null;

        function onCategoryDragStart(event, groupId) {
            draggedCategoryId = groupId;
            draggedDeviceMac = null;
            event.dataTransfer.effectAllowed = 'move';
        }

        function onDeviceDragStart(event, mac) {
            draggedDeviceMac = mac;
            draggedCategoryId = null;
            event.dataTransfer.effectAllowed = 'move';
        }

        function onCategoryDragOver(event) {
            event.preventDefault();
            event.currentTarget.classList.add('category-drop-target');
        }

        function onCategoryDragLeave(event) {
            event.currentTarget.classList.remove('category-drop-target');
        }

        async function onCategoryDrop(event, targetGroupId) {
            event.preventDefault();
            event.stopPropagation();
            event.currentTarget.classList.remove('category-drop-target');

            if (draggedDeviceMac !== null) {
                const mac = draggedDeviceMac;
                draggedDeviceMac = null;
                try {
                    await fetch('/api/device/' + encodeURIComponent(mac) + '/group', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ group_id: targetGroupId }),
                    });
                    await refreshDevices();
                } catch (e) {
                    console.error('Failed to assign device to category:', e);
                }
                return;
            }

            if (draggedCategoryId === null || draggedCategoryId === targetGroupId) return;
            try {
                const res = await fetch('/api/groups/' + draggedCategoryId + '/reparent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ parent_id: targetGroupId }),
                });
                if (!res.ok) {
                    const err = await res.json();
                    alert(err.error || 'Could not nest that category there');
                }
                draggedCategoryId = null;
                await loadCategories();
            } catch (e) {
                console.error('Failed to reparent category:', e);
            }
        }

        function updateFilterCounts(serverCounts = null) {
            const counts = serverCounts || { all: 0, watched: 0, phone: 0, laptop: 0, audio: 0, smart: 0, unknown: 0 };
            if (!serverCounts) {
                allDevices.forEach(d => {
                    counts.all++;
                    if (d.watched) counts.watched++;
                    if (d.device_type === 'phone') counts.phone++;
                    else if (d.device_type === 'laptop' || d.device_type === 'computer') counts.laptop++;
                    else if (d.device_type === 'audio' || d.device_type === 'speaker') counts.audio++;
                    else if (d.device_type === 'smart') counts.smart++;
                    else if (d.device_type === 'unknown') counts.unknown++;
                });
            }
            Object.keys(counts).forEach(k => {
                const el = document.getElementById('count-' + k);
                if (el) el.textContent = counts[k];
            });
        }

        async function searchByDateRange() {
            const startInput = document.getElementById('search-start').value;
            const endInput = document.getElementById('search-end').value;
            if (!startInput && !endInput) { clearDateFilters(); return; }
            try {
                let url = '/api/search?';
                if (startInput) url += 'start=' + encodeURIComponent(startInput) + '&';
                if (endInput) url += 'end=' + encodeURIComponent(endInput);
                const response = await fetch(url);
                const data = await response.json();
                if (!response.ok) {
                    alert('Date query failed: ' + (data.error || response.status));
                    return;
                }
                dateFilteredDevices = data.devices || [];
                selectedMacs.clear();
                lastSelectedIndex = null;
                updatePaginationUI();
                renderDevices();
                if (dateFilteredDevices.length === 0) {
                    alert('No devices had a sighting in that date range.');
                }
            } catch (error) {
                console.error('Query error:', error);
                alert('Date query failed: ' + error.message);
            }
        }

        function clearDateFilters() {
            document.getElementById('search-start').value = '';
            document.getElementById('search-end').value = '';
            dateFilteredDevices = null;
            updatePaginationUI();
            refreshDevices();
        }

        function resetSort() {
            sortState = { ...defaultSortState };
            updateSortIndicators();
            if (dateFilteredDevices !== null) {
                renderDevices();
                return;
            }
            pagination.page = 1;
            refreshDevices();
        }

        function setSort(column) {
            if (sortState.column === column) {
                sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
            } else {
                sortState.column = column;
                sortState.direction = 'asc';
            }
            updateSortIndicators();
            if (dateFilteredDevices !== null) {
                renderDevices();
                return;
            }
            pagination.page = 1;
            refreshDevices();
        }

        function updatePaginationUI() {
            const pageInfo = document.getElementById('page-info');
            const prevBtn = document.getElementById('prev-page-btn');
            const nextBtn = document.getElementById('next-page-btn');
            const pageNumbers = document.getElementById('page-numbers');
            const pageSizeSelect = document.getElementById('page-size-select');
            if (!pageInfo || !prevBtn || !nextBtn || !pageNumbers) return;
            if (pageSizeSelect) {
                pageSizeSelect.value = String(pagination.pageSize);
            }

            const paginationCenter = document.querySelector('.pagination-center');
            const paginationRight = document.querySelector('.pagination-right');

            if (dateFilteredDevices !== null) {
                pageInfo.textContent = 'Date range query — showing all ' + dateFilteredDevices.length + ' matching devices (no paging)';
                if (paginationCenter) paginationCenter.style.display = 'none';
                if (paginationRight) paginationRight.style.display = 'none';
                return;
            }

            if (paginationCenter) paginationCenter.style.display = '';
            if (paginationRight) paginationRight.style.display = '';
            pageInfo.textContent = 'Page ' + pagination.page + '/' + Math.max(1, pagination.totalPages);
            prevBtn.disabled = !pagination.hasPrev;
            nextBtn.disabled = !pagination.hasNext;
            if (pageSizeSelect) pageSizeSelect.disabled = false;
            renderPageNumbers(pageNumbers);
        }

        function getPageTokens(totalPages, currentPage) {
            if (totalPages <= 7) {
                return Array.from({ length: totalPages }, (_, i) => i + 1);
            }

            const tokens = [1];
            let start = Math.max(2, currentPage - 1);
            let end = Math.min(totalPages - 1, currentPage + 1);

            if (currentPage <= 3) {
                start = 2;
                end = 4;
            } else if (currentPage >= totalPages - 2) {
                start = totalPages - 3;
                end = totalPages - 1;
            }

            if (start > 2) tokens.push('…');
            for (let page = start; page <= end; page++) tokens.push(page);
            if (end < totalPages - 1) tokens.push('…');
            tokens.push(totalPages);

            return tokens;
        }

        function renderPageNumbers(container) {
            const totalPages = Math.max(1, pagination.totalPages);
            const currentPage = Math.min(Math.max(1, pagination.page), totalPages);
            const tokens = getPageTokens(totalPages, currentPage);

            container.innerHTML = tokens.map(token => {
                if (typeof token !== 'number') {
                    return '<span class="page-ellipsis">' + token + '</span>';
                }

                const activeClass = token === currentPage ? ' active' : '';
                return (
                    '<button class="btn page-number-btn' + activeClass + '"' +
                    ' onclick="goToPage(' + token + ')">' +
                    token +
                    '</button>'
                );
            }).join('');
        }

        function goToPage(page) {
            if (dateFilteredDevices !== null) return;
            const targetPage = Math.max(1, Math.min(page, pagination.totalPages));
            if (targetPage === pagination.page) return;
            pagination.page = targetPage;
            selectedMacs.clear();
            lastSelectedIndex = null;
            refreshDevices();
        }

        function changePage(delta) {
            if (dateFilteredDevices !== null) return;
            const nextPage = pagination.page + delta;
            goToPage(nextPage);
        }

        function changePageSize(value) {
            const nextPageSize = normalizePageSize(value);
            if (nextPageSize === pagination.pageSize) return;
            pagination.pageSize = nextPageSize;
            localStorage.setItem(PAGE_SIZE_STORAGE_KEY, String(nextPageSize));
            pagination.page = 1;
            selectedMacs.clear();
            lastSelectedIndex = null;

            if (dateFilteredDevices !== null) {
                updatePaginationUI();
                return;
            }
            refreshDevices();
        }

        function updateSortIndicators() {
            document.querySelectorAll('.device-table th.sortable').forEach(th => {
                const indicator = th.querySelector('.sort-indicator');
                if (!indicator) return;
                const isActive = th.dataset.sort === sortState.column;
                th.classList.toggle('active', isActive);
                if (!isActive) {
                    indicator.textContent = '';
                } else {
                    indicator.textContent = sortState.direction === 'asc' ? '▲' : '▼';
                }
            });
        }

        function getSortValue(device, column) {
            switch (column) {
                case 'class':
                    return (device.type_label || device.device_type || '').toLowerCase();
                case 'mac':
                    return (device.mac || '').toLowerCase();
                case 'vendor':
                    return (device.vendor || '').toLowerCase();
                case 'identifier':
                    return (device.friendly_name || '').toLowerCase();
                case 'sightings':
                    return Number.isFinite(device.total_sightings) ? device.total_sightings : -1;
                case 'last_seen':
                    // Raw timestamp (ms since epoch) so normal asc/desc sorting is
                    // intuitive: desc = highest timestamp = most recent first.
                    // Undated devices sort as the oldest possible value.
                    return device.last_seen ? new Date(device.last_seen).getTime() : Number.NEGATIVE_INFINITY;
                case 'group':
                    return (device.group_name || '').toLowerCase();
                default:
                    return '';
            }
        }

        function applySort(devices) {
            const sorted = [...devices];
            const direction = sortState.direction === 'asc' ? 1 : -1;
            sorted.sort((a, b) => {
                const aVal = getSortValue(a, sortState.column);
                const bVal = getSortValue(b, sortState.column);
                if (aVal < bVal) return -1 * direction;
                if (aVal > bVal) return 1 * direction;
                return 0;
            });
            return sorted;
        }

        function updateSelectionUI() {
            const selectedCount = selectedMacs.size;
            const summary = document.getElementById('selected-count');
            if (summary) {
                if (selectedCount > 0) {
                    summary.style.display = 'inline';
                    summary.textContent = '· ' + selectedCount + ' selected';
                } else {
                    summary.style.display = 'none';
                    summary.textContent = '';
                }
            }

            updateSelectAllCheckbox();
            updateBulkActionState();
        }

        function updateSelectAllCheckbox() {
            const checkbox = document.getElementById('select-all-checkbox');
            if (!checkbox) return;
            if (!currentVisibleDevices || currentVisibleDevices.length === 0) {
                checkbox.checked = false;
                checkbox.indeterminate = false;
                checkbox.disabled = true;
                return;
            }
            checkbox.disabled = false;
            const selectedVisibleCount = currentVisibleDevices.filter(d => selectedMacs.has(d.mac)).length;
            checkbox.checked = selectedVisibleCount > 0 && selectedVisibleCount === currentVisibleDevices.length;
            checkbox.indeterminate = selectedVisibleCount > 0 && selectedVisibleCount < currentVisibleDevices.length;
        }

        function updateBulkActionState() {
            const hasSelection = selectedMacs.size > 0;
            const bulkGroupSelect = document.getElementById('bulk-group-select');
            const bulkGroupApply = document.getElementById('bulk-group-apply');
            const bulkWatchSelect = document.getElementById('bulk-watch-select');
            const bulkWatchApply = document.getElementById('bulk-watch-apply');
            const clearBtn = document.getElementById('clear-selection-btn');

            if (bulkGroupSelect) bulkGroupSelect.disabled = !hasSelection;
            if (bulkGroupApply) bulkGroupApply.disabled = !hasSelection;
            if (bulkWatchSelect) bulkWatchSelect.disabled = !hasSelection;
            if (bulkWatchApply) bulkWatchApply.disabled = !hasSelection;
            if (clearBtn) clearBtn.disabled = !hasSelection;
        }

        function clearSelection() {
            selectedMacs.clear();
            lastSelectedIndex = null;
            renderDevices();
        }

        function toggleSelectAllVisible() {
            if (!currentVisibleDevices || currentVisibleDevices.length === 0) return;
            const allSelected = currentVisibleDevices.every(d => selectedMacs.has(d.mac));
            if (allSelected) {
                currentVisibleDevices.forEach(d => selectedMacs.delete(d.mac));
            } else {
                currentVisibleDevices.forEach(d => selectedMacs.add(d.mac));
            }
            renderDevices();
        }

        function toggleRowCheckbox(event, mac, index) {
            event.stopPropagation();
            if (event.target.checked) {
                selectedMacs.add(mac);
            } else {
                selectedMacs.delete(mac);
            }
            lastSelectedIndex = index;
            renderDevices();
        }

        function handleRowClick(event, mac, index) {
            if (event.target && event.target.closest('input.row-select-checkbox')) return;
            const isCtrl = event.ctrlKey || event.metaKey;
            const isShift = event.shiftKey;

            if (isShift && lastSelectedIndex !== null && currentVisibleDevices.length > 0) {
                const start = Math.max(0, Math.min(lastSelectedIndex, index));
                const end = Math.min(currentVisibleDevices.length - 1, Math.max(lastSelectedIndex, index));
                if (!isCtrl) selectedMacs.clear();
                for (let i = start; i <= end; i++) {
                    selectedMacs.add(currentVisibleDevices[i].mac);
                }
            } else if (isCtrl) {
                if (selectedMacs.has(mac)) {
                    selectedMacs.delete(mac);
                } else {
                    selectedMacs.add(mac);
                }
            } else {
                if (selectedMacs.has(mac)) {
                    selectedMacs.delete(mac);
                } else {
                    selectedMacs.clear();
                    selectedMacs.add(mac);
                }
            }

            lastSelectedIndex = index;
            // Delay renderDevices so the dblclick event can fire on the original
            // <tr> element before innerHTML replaces it. Without this delay,
            // the first click destroys the row and dblclick never fires.
            if (rowClickTimer) clearTimeout(rowClickTimer);
            rowClickTimer = setTimeout(() => { rowClickTimer = null; renderDevices(); }, 250);
        }

        function getContrastColor(hexColor) {
            if (!hexColor) return 'var(--text-primary)';
            // Remove # if present
            const hex = hexColor.replace('#', '');
            // Parse RGB values
            const r = parseInt(hex.substr(0, 2), 16);
            const g = parseInt(hex.substr(2, 2), 16);
            const b = parseInt(hex.substr(4, 2), 16);
            // Calculate relative luminance
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            // Return black for light backgrounds, white for dark
            return luminance > 0.5 ? '#000000' : '#ffffff';
        }

        function renderDevices() {
            const tbody = document.getElementById('device-list');
            const sourceDevices = dateFilteredDevices !== null ? dateFilteredDevices : allDevices;
            // Devices with no recent RSSI reading are never hidden by the
            // threshold -- the slider filters by signal strength, not by
            // whether we happen to have a fresh reading.
            let visibleDevices = sourceDevices.filter(d =>
                (d.last_rssi == null || d.last_rssi >= rssiThreshold) &&
                (d.total_sightings == null || d.total_sightings >= sightingsThreshold)
            );

            if (dateFilteredDevices !== null) {
                const searchTerm = document.getElementById('search').value.toLowerCase();
                visibleDevices = sourceDevices.filter(d => {
                    if (currentFilter === 'watched') {
                        if (!d.watched) return false;
                    } else if (currentFilter === 'laptop') {
                        if (d.device_type !== 'laptop' && d.device_type !== 'computer') return false;
                    } else if (currentFilter !== 'all' && d.device_type !== currentFilter) {
                        return false;
                    }
                    if (searchTerm) {
                        const searchable = [d.mac, d.vendor, d.friendly_name].join(' ').toLowerCase();
                        if (!searchable.includes(searchTerm)) return false;
                    }
                    return true;
                });
                visibleDevices = applySort(visibleDevices);
            }

            currentVisibleDevices = visibleDevices;

            if (visibleDevices.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-muted);">No targets match criteria</td></tr>';
                updateSelectionUI();
                return;
            }

            tbody.innerHTML = visibleDevices.map((d, index) => {
                const typeClass = getTypeClass(d.device_type);
                const { text: lastSeen, tooltip: lastSeenTooltip } = formatLastSeen(d.last_seen);
                const isRecent = isRecentlySeen(d.last_seen);
                const watchedStar = d.watched ? '<span class="watched-star">★</span>' : '';
                const isSelected = selectedMacs.has(d.mac);
                const rowClass = isSelected ? 'selected' : '';
                const checkedAttr = isSelected ? 'checked' : '';

                // Build group pill HTML -- clickable, jumps into that
                // category's list view (same as clicking it in the sidebar).
                let groupHtml = '—';
                if (d.group_name && d.group_color) {
                    const textColor = getContrastColor(d.group_color);
                    groupHtml = '<span onclick="event.stopPropagation(); selectCategory(' + d.group_id + ');" style="cursor: pointer; background: ' + d.group_color + '; color: ' + textColor + '; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.7rem; font-weight: 500;" title="View this category">' + obfuscateName(d.group_name) + '</span>';
                } else if (d.group_name) {
                    groupHtml = '<span onclick="event.stopPropagation(); selectCategory(' + d.group_id + ');" style="cursor: pointer; background: var(--bg-tertiary); color: var(--text-secondary); padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.7rem;" title="View this category">' + obfuscateName(d.group_name) + '</span>';
                }

                if (compactView) {
                    // Compact: Type, Name/MAC, Sightings, Last Seen, Group
                    const rawDisplayName = d.friendly_name || d.vendor || d.mac;
                    let displayName = d.friendly_name ? obfuscateName(rawDisplayName) : (d.vendor ? rawDisplayName : obfuscateMAC(rawDisplayName));
                    if (d.identity_mac_count > 1) {
                        displayName += ' <span class="identity-badge" title="' + d.identity_mac_count + ' MAC addresses clustered as one device (rotation)">×' + d.identity_mac_count + '</span>';
                    }
                    // Truncate long macOS UUID addresses in compact view
                    if (!d.friendly_name && !d.vendor && isMacOSUUID(d.mac)) {
                        displayName = displayName.substring(0, 13) + '...';
                    }
                    return '<tr class="' + rowClass + '" draggable="true" ondragstart="onDeviceDragStart(event, \\'' + d.mac + '\\')" onclick="handleRowClick(event, \\'' + d.mac + '\\', ' + index + ')" ondblclick="showDevice(\\'' + d.mac + '\\')" style="height: auto;">' +
                        '<td class="select-col"><input type="checkbox" class="row-select-checkbox" ' + checkedAttr + ' onclick="toggleRowCheckbox(event, \\'' + d.mac + '\\', ' + index + ')"></td>' +
                        '<td style="padding: 0.4rem 0.5rem;"><span class="type-badge ' + typeClass + '" style="font-size: 0.65rem; padding: 0.15rem 0.4rem;">' + watchedStar + d.type_icon + '</span></td>' +
                        '<td colspan="3" style="padding: 0.4rem 0.5rem; font-size: 0.75rem;">' + displayName + '</td>' +
                        '<td style="padding: 0.4rem 0.5rem; font-size: 0.7rem;">' + (d.last_rssi != null ? d.last_rssi + ' dBm' : '—') + '</td>' +
                        '<td style="padding: 0.4rem 0.5rem; font-size: 0.7rem;">' + d.total_sightings + '</td>' +
                        '<td style="padding: 0.4rem 0.5rem; font-size: 0.7rem;" class="' + (isRecent ? 'recent' : '') + '" title="Last seen: ' + lastSeenTooltip + (d.first_seen ? ' \\u2022 First seen: ' + new Date(d.first_seen).toLocaleString() : '') + '">' + lastSeen + '</td>' +
                        '<td style="padding: 0.4rem 0.5rem; font-size: 0.7rem;">' + groupHtml + '</td>' +
                        '</tr>';
                }

                return '<tr class="' + rowClass + '" draggable="true" ondragstart="onDeviceDragStart(event, \\'' + d.mac + '\\')" onclick="handleRowClick(event, \\'' + d.mac + '\\', ' + index + ')" ondblclick="showDevice(\\'' + d.mac + '\\')">' +
                    '<td class="select-col"><input type="checkbox" class="row-select-checkbox" ' + checkedAttr + ' onclick="toggleRowCheckbox(event, \\'' + d.mac + '\\', ' + index + ')"></td>' +
                    '<td><span class="type-badge ' + typeClass + '">' + watchedStar + d.type_icon + ' ' + d.type_label + '</span></td>' +
                    '<td class="vendor-name">' + (d.vendor ? obfuscateName(d.vendor) : '—') + '</td>' +
                    '<td class="mac-addr" title="' + d.mac + '">' + (isMacOSUUID(d.mac) ? obfuscateMAC(d.mac).substring(0, 13) + '...' : obfuscateMAC(d.mac)) +
                    (d.name_conflict_at ? ' <span class="name-conflict-badge" style="color: var(--accent-red, #dc2626);" title="Possible spoofing: this MAC previously advertised a different name (now: ' + escapeHtml(d.name_conflict_name || '') + ')">⚠</span>' : '') +
                    '</td>' +
                    '<td class="device-name">' + (d.friendly_name ? obfuscateName(d.friendly_name) : '—') +
                    (d.identity_mac_count > 1 ? ' <span class="identity-badge" title="' + d.identity_mac_count + ' MAC addresses clustered as one device (rotation)">×' + d.identity_mac_count + '</span>' : '') +
                    '</td>' +
                    '<td class="rssi-value">' + (d.last_rssi != null ? d.last_rssi + ' dBm' : '—') + '</td>' +
                    '<td class="sighting-count">' + d.total_sightings + '</td>' +
                    '<td class="last-seen ' + (isRecent ? 'recent' : '') + '" title="Last seen: ' + lastSeenTooltip + (d.first_seen ? ' \\u2022 First seen: ' + new Date(d.first_seen).toLocaleString() : '') + '">' + lastSeen + '</td>' +
                    '<td class="group-name">' + groupHtml + '</td>' +
                    '</tr>';
            }).join('');
            updateSelectionUI();
        }

        function getTypeClass(type) {
            const classes = { phone: 'type-phone', laptop: 'type-laptop', computer: 'type-laptop', tablet: 'type-phone', smart: 'type-smart', audio: 'type-audio', speaker: 'type-audio', watch: 'type-watch', wearable: 'type-watch', tv: 'type-tv', vehicle: 'type-vehicle' };
            return classes[type] || 'type-unknown';
        }

        function formatLastSeen(isoString) {
            if (!isoString) return { text: '—', tooltip: '' };
            const date = new Date(isoString);
            const now = new Date();
            const tooltip = date.toLocaleString();
            const diffMins = Math.floor((now - date) / 60000);
            let text;
            if (diffMins < 1) text = 'NOW';
            else if (diffMins < 60) text = diffMins + 'm ago';
            else if (diffMins < 1440) {
                const h = Math.floor(diffMins / 60);
                const m = diffMins % 60;
                text = m > 0 ? h + 'h ' + m + 'm ago' : h + 'h ago';
            } else {
                const diffDays = Math.floor(diffMins / 1440);
                if (diffDays === 1) text = 'Yesterday ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                else if (diffDays < 7) text = diffDays + 'd ago';
                else text = date.toLocaleDateString();
            }
            return { text, tooltip };
        }

        function isRecentlySeen(isoString) {
            if (!isoString) return false;
            return (new Date() - new Date(isoString)) < 600000;
        }

        async function showDevice(mac) {
            // Cancel any pending single-click re-render so it doesn't
            // disrupt the modal that the double-click is about to open.
            if (rowClickTimer) { clearTimeout(rowClickTimer); rowClickTimer = null; }
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac));
                const data = await response.json();
                renderModal(data);
                document.getElementById('device-modal').classList.add('active');
            } catch (error) { console.error('Error:', error); }
        }

        let currentDeviceMac = null;
        let liveSignalPollTimer = null;

        function renderModal(data) {
            const d = data.device;
            currentDeviceMac = d.mac;
            const content = document.getElementById('modal-content');

            const proximityColors = { immediate: '#16a34a', near: '#d97706', far: '#ea580c', remote: '#dc2626', unknown: '#555' };
            const proximityZone = data.proximity_zone || 'unknown';
            const proximityColor = proximityColors[proximityZone] || '#555';

            const watchBtn = document.getElementById('watch-btn');
            if (watchBtn) {
                watchBtn.textContent = d.watched ? '★ Watching' : '☆ Watch';
                watchBtn.className = d.watched ? 'btn btn-watch active' : 'btn btn-watch';
            }
            const scanBtn = document.getElementById('scan-unit-btn');
            if (scanBtn) { scanBtn.disabled = false; scanBtn.textContent = 'Scan Unit'; }

            content.innerHTML = '<div class="detail-grid">' +
                '<div class="detail-item"><div class="detail-label">Address</div><div class="detail-value mono" style="font-size:' + (isMacOSUUID(d.mac) ? '0.65rem' : '0.85rem') + '; word-break: break-all;">' + obfuscateMAC(d.mac) + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">Identifier' + (d.identity_mac_count > 1 ? ' <span class="identity-badge" title="' + d.identity_mac_count + ' MAC addresses clustered as one device (rotation)">×' + d.identity_mac_count + '</span>' : '') + '</div><input class="form-input" id="device-identifier" value="' + escapeHtml(d.friendly_name || '') + '" placeholder="No identifier -- set manually" style="font-size: 0.85rem;" onchange="setDeviceName(\\'' + d.mac + '\\', this.value)"></div>' +
                (d.name_conflict_at ? '<div class="detail-item full" style="border-color: var(--accent-red, #dc2626);"><div class="detail-label" style="color: var(--accent-red, #dc2626);">⚠ Possible Spoofing</div><div class="detail-value">This MAC previously advertised a different name. Now seen as: "' + escapeHtml(d.name_conflict_name || '') + '" (at ' + new Date(d.name_conflict_at).toLocaleString() + ')</div></div>' : '') +
                '<div class="detail-item"><div class="detail-label">Type</div><select class="form-input" id="device-type" onchange="setDeviceType(\\'' + d.mac + '\\', this.value)" style="font-size: 0.8rem;"></select></div>' +
                '<div class="detail-item"><div class="detail-label">Vendor OUI</div><input class="form-input" id="device-vendor" value="' + escapeHtml(d.vendor || '') + '" placeholder="Unknown -- set manually" style="font-size: 0.85rem;" onchange="setDeviceVendor(\\'' + d.mac + '\\', this.value)"></div>' +
                '<div class="detail-item"><div class="detail-label">Proximity</div><div class="detail-value" style="color: ' + proximityColor + '; ">' + proximityZone + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">Sightings</div><div class="detail-value highlight">' + d.total_sightings + '</div></div>' +
                appleActivityHtml(d) +
                samsungStatusHtml(d) +
                fastpairBatteryHtml(d) +
                droneStateHtml(d) +
                '<div class="detail-item"' + (d.identity_mac_count > 1 && d.identity_first_seen ? ' title="Earliest sighting across all ' + d.identity_mac_count + ' rotated addresses clustered under this identity"' : '') + '><div class="detail-label">First seen</div><div class="detail-value mono">' + (d.identity_mac_count > 1 && d.identity_first_seen ? new Date(d.identity_first_seen).toLocaleString() : (d.first_seen ? new Date(d.first_seen).toLocaleString() : '—')) + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">Last seen</div><div class="detail-value mono">' + (d.last_seen ? new Date(d.last_seen).toLocaleString() : '—') + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">Activity Pattern</div><div class="detail-value">' + (data.pattern || 'Insufficient data') + '</div></div>' +
                '<div class="detail-item"><div class="detail-label">BLE Services</div><div class="detail-value mono" style="font-size:0.75rem;">' + (data.uuid_names && data.uuid_names.length > 0 ? data.uuid_names.join(', ') : '—') + '</div></div>' +
                '<div class="detail-item full"><div class="detail-label">Assign to Group</div><select class="form-input" id="device-group" onchange="setDeviceGroup(\\'' + d.mac + '\\', this.value)" style="font-size: 0.8rem;"><option value="">No group</option></select></div>' +
                '<div class="detail-item full"><div class="detail-label">Notes</div><textarea class="form-input" id="device-notes" rows="2" style="font-size: 0.8rem; resize: vertical;" placeholder="Add notes...">' + (d.notes || '') + '</textarea><button class="btn" style="margin-top: 0.35rem; padding: 0.3rem 0.6rem; display: block;" onclick="saveNotes(\\'' + d.mac + '\\')">Save Notes</button></div>' +
                '</div>' +
                '<div class="heatmap-grid-2col">' +
                '<div class="heatmap-section" id="live-signal-section">' +
                '<div class="heatmap-title">Live Signal</div>' +
                '<div class="rssi-chart" id="live-signal-chart" style="height: 90px;"></div>' +
                '<div style="display: flex; justify-content: space-between; align-items: baseline; font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">' +
                '<span style="display: flex; align-items: baseline; gap: 0.3rem;"><span id="live-signal-rssi" style="font-weight: 400; color: var(--text-primary);">—</span><span id="live-signal-trend" style="font-family: monospace; font-weight: 700;"></span><span id="live-signal-avg">avg —</span></span>' +
                '<span id="live-signal-footer">first — · last —</span>' +
                '</div>' +
                '<div style="margin-top: 0.35rem;">' +
                '<div style="display: flex; justify-content: space-between; font-size: 0.65rem; color: var(--text-muted); margin-bottom: 0.15rem;">' +
                '<span>Presence (last 15 min)</span><span id="live-signal-presence-pct">0%</span>' +
                '</div>' +
                '<div id="live-signal-presence-track" style="height: 10px;"></div>' +
                '</div></div>' +
                '<div class="heatmap-section" id="rssi-section">' +
                '<div class="heatmap-title">Signal History (7d)</div>' +
                '<div class="rssi-chart" id="rssi-chart" style="height: 90px;"><div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding-top: 1.5rem;">Loading...</div></div>' +
                '</div>' +
                '</div>' +
                '<div class="heatmap-section" id="scan-unit-section" hidden>' +
                '<div class="heatmap-title">Scan Unit Result</div>' +
                '<div id="scan-unit-result" style="font-size: 0.75rem; font-family: monospace; white-space: pre-wrap; word-break: break-all; max-height: 300px; overflow-y: auto;"></div>' +
                '</div>' +
                '<div class="heatmap-grid-2col">' +
                '<div class="heatmap-section">' +
                '<div class="heatmap-title">Time Nearby (30d)</div>' +
                '<div id="dwell-stats" class="heatmap" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;"><div style="color: var(--text-muted);">Loading...</div></div>' +
                '</div>' +
                '<div class="heatmap-section">' +
                '<div class="heatmap-title">Daily Activity</div>' +
                '<div class="heatmap">' + renderDailyHeatmap(data.daily_data) + '</div>' +
                '</div>' +
                '<div class="heatmap-section">' +
                '<div class="heatmap-title">Hourly Activity (30d)</div>' +
                '<div class="heatmap">' + renderHourlyHeatmap(data.hourly_data) + '</div>' +
                '</div>' +
                '<div class="heatmap-section">' +
                '<div class="heatmap-title">Timeline (30d)</div>' +
                renderTimeline(data.timeline) +
                '</div>' +
                '</div>' +
                (d.identity_id ? (
                    '<div class="heatmap-section">' +
                    '<div class="heatmap-title">Linked Addresses (' + (d.identity_mac_count || 1) + ')</div>' +
                    '<div id="identity-macs" class="heatmap">Loading...</div>' +
                    '</div>'
                ) : '') +
                '';

            loadRssiChart(d.mac);
            startLiveSignalPolling(d.mac);
            loadDwellStats(d.mac);
            loadGroupsForDevice(d.group_id);
            loadDeviceTypes(d.device_type);
            if (d.identity_id) loadIdentityMacs(d.identity_id, d.mac);
        }

        async function loadIdentityMacs(identityId, currentMac) {
            const el = document.getElementById('identity-macs');
            if (!el) return;
            try {
                const res = await fetch('/api/identity/' + identityId + '/macs');
                const data = await res.json();
                el.innerHTML = (data.macs || []).map(m =>
                    '<div style="display:flex; justify-content:space-between; align-items:center; padding:0.3rem 0; border-bottom:1px solid var(--border-color); font-size:0.75rem; gap:0.5rem;">' +
                    '<span class="mono">' + m.mac + (m.mac === currentMac ? ' (current)' : '') + '</span>' +
                    '<span style="color:var(--text-muted);">first ' + (m.first_seen ? new Date(m.first_seen).toLocaleString() : '—') + '</span>' +
                    '<span style="color:var(--text-muted);">last ' + (m.last_seen ? new Date(m.last_seen).toLocaleString() : '—') + '</span>' +
                    '<span style="color:var(--text-muted);">' + m.total_sightings + ' sightings</span>' +
                    '<button class="btn" style="padding:0.1rem 0.4rem; font-size:0.65rem;" onclick="unmergeAndRefresh(\\'' + m.mac + '\\')">Unmerge</button>' +
                    '</div>'
                ).join('');
            } catch (e) {
                el.textContent = 'Failed to load';
            }
        }

        async function unmergeAndRefresh(mac) {
            await fetch('/api/device/' + encodeURIComponent(mac) + '/unmerge', { method: 'POST' });
            await refreshDevices();
            showDevice(mac);
        }

        let cachedGroups = [];

        async function loadGroupsForDevice(currentGroupId) {
            const select = document.getElementById('device-group');
            if (!select) return;

            // Use cached groups if available
            if (cachedGroups.length === 0) {
                try {
                    const response = await fetch('/api/groups');
                    const data = await response.json();
                    cachedGroups = data.groups || [];
                } catch (error) { return; }
            }

            select.innerHTML = '<option value="">No group</option>' +
                cachedGroups.map(g => '<option value="' + g.id + '"' + (g.id === currentGroupId ? ' selected' : '') + '>' + groupOptionLabel(g) + '</option>').join('');
        }

        async function loadGroupsForBulkSelect() {
            const select = document.getElementById('bulk-group-select');
            if (!select) return;

            if (cachedGroups.length === 0) {
                try {
                    const response = await fetch('/api/groups');
                    const data = await response.json();
                    cachedGroups = data.groups || [];
                } catch (error) {
                    return;
                }
            }

            select.innerHTML = '<option value="">Assign group...</option>' +
                '<option value="__none__">No group</option>' +
                cachedGroups.map(g => '<option value="' + g.id + '">' + groupOptionLabel(g) + '</option>').join('');
        }

        async function setDeviceVendor(mac, vendor) {
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/vendor', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ vendor: vendor })
                });
                refreshDevices();
            } catch (error) { console.error('Error setting vendor:', error); }
        }

        async function setDeviceName(mac, name) {
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/name', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                refreshDevices();
            } catch (error) { console.error('Error setting identifier:', error); }
        }

        async function scanUnit(mac) {
            const btn = document.getElementById('scan-unit-btn');
            const section = document.getElementById('scan-unit-section');
            const result = document.getElementById('scan-unit-result');
            btn.disabled = true;
            btn.textContent = 'Scanning...';
            section.hidden = false;
            result.textContent = 'Actively contacting device, this may take up to 30 seconds (longer if the adapter is mid-scan and needs a retry)...';
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/scan', { method: 'POST' });
                const data = await response.json();
                if (!data.ok) {
                    result.textContent = 'Scan failed: ' + (data.error || 'unknown error');
                } else if (data.bt_type === 'classic' || data.records) {
                    if (!data.records || data.records.length === 0) {
                        result.textContent = 'Connected, but no SDP service records advertised.';
                    } else {
                        result.textContent = data.records.map((r, i) =>
                            'Service ' + (i + 1) + ':\\n' +
                            Object.entries(r).map(([k, v]) => '  ' + k + ': ' + v).join('\\n')
                        ).join('\\n\\n');
                    }
                } else {
                    let lines = [];
                    if (data.device_info && Object.keys(data.device_info).length > 0) {
                        lines.push('Device Information:');
                        for (const [k, v] of Object.entries(data.device_info)) {
                            lines.push('  ' + k + ': ' + v);
                        }
                        lines.push('');
                    }
                    lines.push('GATT Services (' + data.services.length + '):');
                    for (const svc of data.services) {
                        lines.push('  ' + svc.uuid + (svc.description ? ' (' + svc.description + ')' : ''));
                        for (const c of svc.characteristics) {
                            lines.push('    ' + c.uuid + ' [' + c.properties.join(', ') + ']' + (c.value ? ' = ' + c.value : ''));
                        }
                    }
                    result.textContent = lines.join('\\n');
                }

                if (data.applied && Object.keys(data.applied).length > 0) {
                    const appliedLines = ['Auto-filled from scan (fields that were empty):'];
                    for (const [k, v] of Object.entries(data.applied)) {
                        appliedLines.push('  ' + k + ': ' + v);
                    }
                    result.textContent = appliedLines.join('\\n') + '\\n\\n' + result.textContent;
                }

                if (data.ok) {
                    // Re-fetch the device from scratch rather than trust
                    // the scan response's partial "applied" set -- this
                    // guarantees the visible Type/Vendor/Identifier fields
                    // always match what actually landed in the database,
                    // with no separate save step for the operator.
                    try {
                        const freshResp = await fetch('/api/device/' + encodeURIComponent(mac));
                        const fresh = await freshResp.json();
                        const d = fresh.device;
                        const vendorInput = document.getElementById('device-vendor');
                        if (vendorInput) vendorInput.value = d.vendor || '';
                        const idInput = document.getElementById('device-identifier');
                        if (idInput) idInput.value = d.friendly_name || '';
                        await loadDeviceTypes(d.device_type);
                    } catch (e) { /* non-fatal -- scan result itself still shown */ }
                    refreshDevices();
                }
            } catch (error) {
                result.textContent = 'Scan failed: ' + error;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Scan Unit';
            }
        }

        let cachedDeviceTypes = [];

        async function loadDeviceTypes(currentType) {
            const select = document.getElementById('device-type');
            if (!select) return;

            if (cachedDeviceTypes.length === 0) {
                try {
                    const response = await fetch('/api/device-types');
                    const data = await response.json();
                    cachedDeviceTypes = data.types || [];
                } catch (error) { return; }
            }

            select.innerHTML = cachedDeviceTypes.map(t =>
                '<option value="' + t.value + '"' + (t.value === currentType ? ' selected' : '') + '>' + t.icon + ' ' + t.label + '</option>'
            ).join('');
        }

        async function setDeviceType(mac, deviceType) {
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/type', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_type: deviceType })
                });
                refreshDevices();
            } catch (error) { console.error('Error setting device type:', error); }
        }

        async function setDeviceGroup(mac, groupId) {
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/group', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ group_id: groupId ? parseInt(groupId) : null })
                });
                refreshDevices();
            } catch (error) { console.error('Error setting group:', error); }
        }

        async function applyBulkMerge() {
            const macs = Array.from(selectedMacs);
            if (macs.length < 2) {
                alert('Select at least 2 devices to merge as one.');
                return;
            }
            const deviceMap = new Map(allDevices.map(d => [d.mac, d]));
            const names = new Set(macs.map(m => (deviceMap.get(m) || {}).friendly_name).filter(Boolean));
            let name;
            if (names.size === 1) {
                name = [...names][0];
            } else {
                name = prompt(
                    names.size > 1
                        ? 'Selected devices have different names (' + [...names].join(', ') + '). Name for the merged device:'
                        : 'Name for the merged device:',
                    ''
                );
                if (!name) return;
            }
            try {
                await fetch('/api/devices/merge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ macs, name }),
                });
                clearSelection();
                await refreshDevices();
            } catch (error) {
                console.error('Error merging devices:', error);
            }
        }

        async function applyBulkGroup() {
            const select = document.getElementById('bulk-group-select');
            if (!select || !select.value) return;
            if (selectedMacs.size === 0) return;

            const groupValue = select.value;
            const groupId = groupValue === '__none__' ? null : parseInt(groupValue);
            const macs = Array.from(selectedMacs);

            try {
                await Promise.all(macs.map(mac =>
                    fetch('/api/device/' + encodeURIComponent(mac) + '/group', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ group_id: groupId })
                    })
                ));
                refreshDevices();
            } catch (error) {
                console.error('Error applying bulk group:', error);
            }
        }

        async function applyBulkWatch() {
            const select = document.getElementById('bulk-watch-select');
            if (!select || !select.value) return;
            if (selectedMacs.size === 0) return;

            const desired = select.value;
            const deviceMap = new Map(allDevices.map(d => [d.mac, d]));
            const macs = Array.from(selectedMacs);
            const requests = [];

            macs.forEach(mac => {
                const device = deviceMap.get(mac);
                if (!device) return;
                if (desired === 'on' && !device.watched) {
                    requests.push(fetch('/api/device/' + encodeURIComponent(mac) + '/watch', { method: 'POST' }));
                }
                if (desired === 'off' && device.watched) {
                    requests.push(fetch('/api/device/' + encodeURIComponent(mac) + '/watch', { method: 'POST' }));
                }
            });

            try {
                await Promise.all(requests);
                refreshDevices();
            } catch (error) {
                console.error('Error applying bulk watch:', error);
            }
        }

        async function loadDwellStats(mac) {
            const container = document.getElementById('dwell-stats');
            if (!container) return;
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/dwell?days=30');
                const data = await response.json();
                container.innerHTML =
                    '<div class="dwell-stat-card"><div class="dwell-stat-value" style="color: var(--accent-amber);">' + Math.round(data.total_minutes) + '</div><div class="dwell-stat-label">TOTAL MIN</div></div>' +
                    '<div class="dwell-stat-card"><div class="dwell-stat-value" style="color: var(--accent-green);">' + data.session_count + '</div><div class="dwell-stat-label">SESSIONS</div></div>' +
                    '<div class="dwell-stat-card"><div class="dwell-stat-value" style="color: var(--accent-blue);">' + Math.round(data.avg_session_minutes) + '</div><div class="dwell-stat-label">AVG MIN</div></div>' +
                    '<div class="dwell-stat-card"><div class="dwell-stat-value" style="color: var(--accent-red);">' + Math.round(data.longest_session_minutes) + '</div><div class="dwell-stat-label">LONGEST</div></div>';
            } catch (error) {
                container.innerHTML = '<div style="color: var(--text-muted);">Error loading data</div>';
            }
        }

        let correlationMac = null;

        function reloadCorrelated() {
            if (correlationMac) loadCorrelatedDevices(correlationMac);
        }

        async function loadCorrelatedDevices(mac) {
            correlationMac = mac;
            const container = document.getElementById('correlated-devices');
            if (!container) return;
            const gapEl = document.getElementById('corr-gap');
            const edgeEl = document.getElementById('corr-edge');
            const gap = Math.max(1, parseInt(gapEl && gapEl.value) || 15);
            const edge = Math.max(1, parseInt(edgeEl && edgeEl.value) || 5);
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/correlation?days=30&gap=' + gap + '&edge=' + edge);
                const data = await response.json();
                if (!data.correlated_devices || data.correlated_devices.length === 0) {
                    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.75rem;">No correlated devices found</div>';
                    return;
                }
                container.innerHTML = data.correlated_devices.slice(0, 5).map(c => {
                    const rawPrimaryName = c.friendly_name || c.vendor || 'Unknown';
                    const primaryName = c.friendly_name ? obfuscateName(rawPrimaryName) : rawPrimaryName;
                    const rawSecondaryInfo = c.friendly_name ? (c.vendor || c.mac) : c.mac;
                    const secondaryInfo = (c.friendly_name && c.vendor) ? rawSecondaryInfo : obfuscateMAC(rawSecondaryInfo);
                    const corrBar = '<div style="background: var(--accent-red); height: 4px; width: ' + c.correlation_score + '%; border-radius: 2px;"></div>';
                    const syncedEdges = (c.synced_arrivals || 0) + (c.synced_departures || 0);
                    const syncLine = syncedEdges > 0
                        ? '<div style="font-size: 0.65rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">⇄ ' + (c.synced_arrivals || 0) + ' arrivals / ' + (c.synced_departures || 0) + ' departures in sync</div>'
                        : '';
                    const corrTitle = 'Correlation ' + c.correlation_score + '% (co-presence ' + (c.cooccurrence_score != null ? c.cooccurrence_score : 0) + '%, transition sync ' + (c.transition_score != null ? c.transition_score : 0) + '%)';
                    return '<div title="' + corrTitle + '" style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color); cursor: pointer;" onclick="showDevice(\\'' + c.mac + '\\')">' +
                        '<div style="flex: 1; min-width: 0;">' +
                        '<div style="font-size: 0.8rem; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">' + primaryName + '</div>' +
                        '<div style="font-size: 0.65rem; color: var(--text-muted); font-family: var(--font-mono); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">' + secondaryInfo + '</div>' +
                        syncLine +
                        '</div>' +
                        '<div style="display: flex; align-items: center; gap: 0.5rem; margin-left: 0.5rem;">' +
                        '<div style="width: 50px;">' + corrBar + '</div>' +
                        '<span style="font-size: 0.7rem; color: var(--accent-amber); min-width: 32px; text-align: right;">' + c.correlation_score + '%</span>' +
                        '</div></div>';
                }).join('');
            } catch (error) {
                container.innerHTML = '<div style="color: var(--text-muted);">Error loading data</div>';
            }
        }

        function formatPing(seconds) {
            if (seconds == null) return 'n/a';
            if (seconds >= 90) return '~' + Math.round(seconds / 60) + 'm';
            return '~' + Math.round(seconds) + 's';
        }

        async function loadRotationCandidates(mac) {
            const container = document.getElementById('rotation-candidates');
            if (!container) return;
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/rotation?days=7');
                const data = await response.json();
                const candidates = data.candidates || [];
                const t = data.target;
                let html = '';
                if (t) {
                    html += '<div style="font-size: 0.65rem; color: var(--text-muted); margin-bottom: 0.4rem;">This device: RSSI ' + t.mean_rssi + '±' + t.rssi_stddev + ' dBm · ping ' + formatPing(t.ping_interval_seconds) + '</div>';
                }
                if (candidates.length === 0) {
                    html += '<div style="color: var(--text-muted); font-size: 0.75rem;">No likely rotation siblings found</div>';
                    container.innerHTML = html;
                    return;
                }
                html += candidates.map(c => {
                    const rawPrimary = c.friendly_name || c.vendor || c.mac;
                    const primaryName = c.friendly_name ? obfuscateName(rawPrimary) : (c.vendor ? rawPrimary : obfuscateMAC(c.mac));
                    const overlapPct = Math.round((c.overlap_ratio || 0) * 100);
                    const detail = 'RSSI ' + c.mean_rssi + '±' + c.rssi_stddev + ' (Δ' + c.rssi_delta + ') · ping ' + formatPing(c.ping_interval_seconds) + ' · ' + overlapPct + '% overlap';
                    const nameBadge = c.name_match ? ' <span style="font-size: 0.6rem; color: var(--accent-amber); border: 1px solid var(--accent-amber); border-radius: 3px; padding: 0 0.25rem; vertical-align: middle;">name match</span>' : '';
                    const bar = '<div style="background: var(--accent-amber); height: 4px; width: ' + c.confidence + '%; border-radius: 2px;"></div>';
                    const title = 'Confidence ' + c.confidence + '% — ' + (c.name_match ? 'shares this device\\'s advertised name, plus ' : '') + 'similar signal strength, non-overlapping presence, similar ping cadence. Heuristic, not definitive.';
                    return '<div title="' + title + '" style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color); cursor: pointer;" onclick="showDevice(\\'' + c.mac + '\\')">' +
                        '<div style="flex: 1; min-width: 0;">' +
                        '<div style="font-size: 0.8rem; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">' + primaryName + nameBadge + '</div>' +
                        '<div style="font-size: 0.65rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">' + detail + '</div>' +
                        '</div>' +
                        '<div style="display: flex; align-items: center; gap: 0.5rem; margin-left: 0.5rem;">' +
                        '<div style="width: 50px;">' + bar + '</div>' +
                        '<span style="font-size: 0.7rem; color: var(--accent-amber); min-width: 32px; text-align: right;">' + c.confidence + '%</span>' +
                        '</div></div>';
                }).join('');
                container.innerHTML = html;
            } catch (error) {
                container.innerHTML = '<div style="color: var(--text-muted);">Error loading data</div>';
            }
        }

        async function saveNotes(mac) {
            const notes = document.getElementById('device-notes').value;
            try {
                await fetch('/api/device/' + encodeURIComponent(mac) + '/notes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: notes })
                });
            } catch (error) { console.error('Error:', error); }
        }

        function renderHourlyHeatmap(hourlyData) {
            if (!hourlyData || Object.keys(hourlyData).length === 0) return '<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding: 1rem 0;">No data</div>';
            var offset = -(new Date().getTimezoneOffset() / 60);
            var shifted = {};
            for (var h in hourlyData) {
                var localHour = ((parseInt(h) + offset) % 24 + 24) % 24;
                shifted[localHour] = (shifted[localHour] || 0) + hourlyData[h];
            }
            var max = Math.max(...Object.values(shifted), 1);
            var cells = '';
            var labels = '';
            for (var i = 0; i < 24; i++) {
                var count = shifted[i] || 0;
                var level = count === 0 ? 0 : Math.ceil((count / max) * 4);
                var label = i < 10 ? '0' + i : '' + i;
                cells += '<div class="activity-cell l' + level + '" title="' + label + ':00 — ' + count + ' sightings"></div>';
                labels += '<span>' + (i % 6 === 0 ? label : '') + '</span>';
            }
            return '<div class="activity-grid hourly">' + cells + '</div><div class="activity-labels hourly">' + labels + '</div>';
        }

        function renderDailyHeatmap(dailyData) {
            if (!dailyData || Object.keys(dailyData).length === 0) return '<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding: 1rem 0;">No data</div>';
            var days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            var max = Math.max(...Object.values(dailyData), 1);
            var cells = '';
            var labels = '';
            for (var d = 0; d < 7; d++) {
                var count = dailyData[d] || dailyData[String(d)] || 0;
                var level = count === 0 ? 0 : Math.ceil((count / max) * 4);
                cells += '<div class="activity-cell l' + level + '" title="' + days[d] + ' — ' + count + ' sightings"></div>';
                labels += '<span>' + days[d] + '</span>';
            }
            return '<div class="activity-grid daily">' + cells + '</div><div class="activity-labels daily">' + labels + '</div>';
        }

        function renderTimeline(timeline) {
            if (!timeline || timeline.length === 0) return '<div style="color: var(--text-muted); font-size: 0.75rem;">No data</div>';
            const maxCount = Math.max(...timeline.map(d => d.count));
            const bars = timeline.map(d => {
                const height = maxCount > 0 ? (d.count / maxCount * 100) : 0;
                const date = new Date(d.date);
                const tooltip = date.toLocaleDateString() + ': ' + d.count + ' sightings';
                return '<div class="timeline-bar" style="height: ' + height + '%" title="' + tooltip + '"></div>';
            }).join('');
            const firstDate = new Date(timeline[0].date);
            const lastDate = new Date(timeline[timeline.length - 1].date);
            const formatDate = (d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            return '<div class="timeline-chart">' + bars + '</div><div class="timeline-labels"><span>' + formatDate(firstDate) + '</span><span>' + formatDate(lastDate) + '</span></div>';
        }

        async function loadRssiChart(mac) {
            const container = document.getElementById('rssi-chart');
            if (!container) return;
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/rssi?days=7');
                const data = await response.json();
                if (!data.rssi_history || data.rssi_history.length < 2) {
                    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding-top: 1.5rem;">Insufficient data</div>';
                    return;
                }
                renderRssiChart(container, data.rssi_history);
            } catch (error) {
                container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; padding-top: 1.5rem;">Error</div>';
            }
        }

        function renderRssiChart(container, rssiData) {
            // The long-term counterpart to renderLiveSignalChart's fixed
            // -30/-100 live scale (Fieldwatch's own device-history views
            // use a similarly settled, gridded look, just auto-scaled to
            // this device's actual multi-day range rather than a fixed
            // live window -- no "current reading" dot or trend arrow here,
            // this is a static historical read, not a live one).
            const width = container.clientWidth - 20;
            const height = 50;
            const padding = { left: 30, right: 10, top: 6, bottom: 15 };
            const rssiValues = rssiData.map(d => d.rssi);
            const dataMin = Math.min(...rssiValues);
            const dataMax = Math.max(...rssiValues);
            // A little headroom so the line never touches the frame, then
            // snapped to 5 dBm so gridline labels land on round numbers.
            const minRssi = Math.floor((dataMin - 3) / 5) * 5;
            const maxRssi = Math.ceil((dataMax + 3) / 5) * 5;
            const range = (maxRssi - minRssi) || 10;
            const xScale = (i) => padding.left + (i / (rssiData.length - 1)) * (width - padding.left - padding.right);
            const yScale = (rssi) => padding.top + (1 - (rssi - minRssi) / range) * (height - padding.top - padding.bottom);
            const linePath = rssiData.map((d, i) => (i === 0 ? 'M' : 'L') + xScale(i) + ',' + yScale(d.rssi)).join(' ');
            const areaPath = linePath + ' L' + xScale(rssiData.length - 1) + ',' + (height - padding.bottom) + ' L' + padding.left + ',' + (height - padding.bottom) + ' Z';
            const firstTime = new Date(rssiData[0].timestamp);
            const lastTime = new Date(rssiData[rssiData.length - 1].timestamp);
            const formatTime = (d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            // 4 evenly-spaced horizontal gridlines across the device's own
            // observed range, plus 3 dashed vertical time dividers --
            // same "quartered grid" language as the live chart, just
            // scaled to this device's real history instead of a fixed
            // -30/-100 window.
            let grid = '';
            for (let i = 0; i <= 3; i++) {
                const dbm = Math.round(minRssi + range * i / 3);
                const y = yScale(dbm);
                grid += '<line x1="' + padding.left + '" y1="' + y + '" x2="' + width + '" y2="' + y + '" stroke="var(--border-color)" stroke-width="1" opacity="' + (i === 0 || i === 3 ? '1' : '0.6') + '" stroke-dasharray="' + (i === 0 || i === 3 ? 'none' : '3,4') + '"/>';
                grid += '<text x="2" y="' + (y + 3) + '" class="rssi-label" font-size="8">' + dbm + '</text>';
            }
            grid += '<line x1="' + padding.left + '" y1="' + padding.top + '" x2="' + padding.left + '" y2="' + (height - padding.bottom) + '" stroke="var(--border-color)" stroke-width="1.2"/>';
            for (let c = 1; c < 4; c++) {
                const x = padding.left + (width - padding.left - padding.right) * c / 4;
                grid += '<line x1="' + x + '" y1="' + padding.top + '" x2="' + x + '" y2="' + (height - padding.bottom) + '" stroke="var(--border-color)" stroke-width="0.75" stroke-dasharray="3,5" opacity="0.5"/>';
            }

            container.innerHTML = '<svg viewBox="0 0 ' + width + ' ' + height + '" preserveAspectRatio="none">' +
                '<defs><linearGradient id="rssiGradient" x1="0%" y1="0%" x2="0%" y2="100%">' +
                '<stop offset="0%" style="stop-color: #ffffff; stop-opacity: 0.25"/>' +
                '<stop offset="100%" style="stop-color: #ffffff; stop-opacity: 0.03"/>' +
                '</linearGradient></defs>' +
                grid +
                '<path class="rssi-area" d="' + areaPath + '"/>' +
                '<path class="rssi-line" d="' + linePath + '" style="stroke: #ffffff;"/>' +
                '<text class="rssi-label" x="' + padding.left + '" y="' + (height - 2) + '">' + formatTime(firstTime) + '</text>' +
                '<text class="rssi-label" x="' + (width - padding.right) + '" y="' + (height - 2) + '" text-anchor="end">' + formatTime(lastTime) + '</text>' +
                '</svg>';
        }

        async function toggleWatch(mac) {
            try {
                const response = await fetch('/api/device/' + encodeURIComponent(mac) + '/watch', { method: 'POST' });
                const data = await response.json();
                const btn = document.getElementById('watch-btn');
                if (data.watched) {
                    btn.textContent = '★ Watching';
                    btn.className = 'btn btn-watch active';
                } else {
                    btn.textContent = '☆ Watch';
                    btn.className = 'btn btn-watch';
                }
                refreshDevices();
            } catch (error) { console.error('Error:', error); }
        }

        // Live Signal panel -- polls a short recent window while the
        // Device Details modal is open, for a Fieldwatch-style "signal
        // trend + presence" view (OffGridPete/Fieldwatch, MIT licensed,
        // reimplemented against BlueWatch's own sightings data). Started
        // from renderModal(), stopped from closeModal() so the timer
        // never outlives the modal it's updating.
        const LIVE_SIGNAL_WINDOW_MINUTES = 15;
        const LIVE_SIGNAL_POLL_MS = 1000;

        function startLiveSignalPolling(mac) {
            stopLiveSignalPolling();
            fetchAndRenderLiveSignal(mac);
            liveSignalPollTimer = setInterval(function() {
                if (mac !== currentDeviceMac) { stopLiveSignalPolling(); return; }
                fetchAndRenderLiveSignal(mac);
            }, LIVE_SIGNAL_POLL_MS);
        }

        function stopLiveSignalPolling() {
            if (liveSignalPollTimer) { clearInterval(liveSignalPollTimer); liveSignalPollTimer = null; }
        }

        function formatDurationCompact(seconds) {
            // "1h 10m" / "14s" style -- matches Fieldwatch's own
            // "first Xh Xm · last Xs" card footer.
            seconds = Math.max(0, Math.round(seconds));
            if (seconds < 60) return seconds + "s";
            const mins = Math.floor(seconds / 60);
            if (mins < 60) return mins + "m";
            const hrs = Math.floor(mins / 60);
            const remMins = mins % 60;
            return hrs + "h" + (remMins ? " " + remMins + "m" : "");
        }

        async function fetchAndRenderLiveSignal(mac) {
            const rssiEl = document.getElementById("live-signal-rssi");
            const trendEl = document.getElementById("live-signal-trend");
            const avgEl = document.getElementById("live-signal-avg");
            const footerEl = document.getElementById("live-signal-footer");
            const chartEl = document.getElementById("live-signal-chart");
            const pctEl = document.getElementById("live-signal-presence-pct");
            const trackEl = document.getElementById("live-signal-presence-track");
            if (!rssiEl) return; // modal closed mid-flight

            let data;
            try {
                const response = await fetch("/api/device/" + encodeURIComponent(mac) + "/live-signal?minutes=" + LIVE_SIGNAL_WINDOW_MINUTES);
                data = await response.json();
            } catch (error) {
                return; // transient -- next poll tick retries
            }
            if (mac !== currentDeviceMac) return; // modal switched devices while this was in flight

            if (data.current_rssi === null || data.current_rssi === undefined) {
                rssiEl.textContent = "—";
                rssiEl.style.color = "var(--text-muted)";
                if (trendEl) trendEl.textContent = "";
            } else {
                const rssi = data.current_rssi;
                rssiEl.textContent = rssi + " dBm";
                rssiEl.style.color = "#ffffff";
                if (trendEl) {
                    // Trend arrow: last sample vs. the average of the
                    // previous few -- same idea as Fieldwatch's RssiTrend
                    // (>>/>/=/</<<), just derived here instead of carried
                    // from the API. White throughout, matching the
                    // reference card exactly -- no quality-color coding.
                    const s = data.sightings || [];
                    if (s.length >= 4) {
                        const prevWindow = s.slice(-4, -1);
                        const prevAvg = prevWindow.reduce((a, x) => a + x.rssi, 0) / prevWindow.length;
                        const delta = rssi - prevAvg;
                        let mark = "=";
                        if (delta >= 8) mark = "»";
                        else if (delta >= 3) mark = "›";
                        else if (delta <= -8) mark = "«";
                        else if (delta <= -3) mark = "‹";
                        trendEl.textContent = mark;
                        trendEl.style.color = "#ffffff";
                    } else {
                        trendEl.textContent = "";
                    }
                }
            }

            if (pctEl) pctEl.textContent = (data.presence_pct || 0) + "%";
            if (trackEl) renderPresenceTrack(trackEl, data.sightings || [], LIVE_SIGNAL_WINDOW_MINUTES);

            const s = data.sightings || [];
            if (avgEl) {
                if (s.length) {
                    const avg = Math.round(s.reduce((a, x) => a + x.rssi, 0) / s.length);
                    avgEl.textContent = "avg " + avg;
                } else {
                    avgEl.textContent = "avg —";
                }
            }
            if (footerEl) {
                if (s.length) {
                    const firstTs = new Date(s[0].timestamp).getTime();
                    const firstAgo = (Date.now() - firstTs) / 1000;
                    const lastAgo = data.last_seen_seconds_ago;
                    footerEl.textContent = "first " + formatDurationCompact(firstAgo)
                        + " · last " + (lastAgo == null ? "—" : formatDurationCompact(lastAgo));
                } else {
                    footerEl.textContent = "no signal in the last " + LIVE_SIGNAL_WINDOW_MINUTES + " min";
                }
            }

            if (chartEl) {
                if (data.sightings && data.sightings.length >= 2) {
                    renderLiveSignalChart(chartEl, data.sightings);
                } else {
                    chartEl.innerHTML = '<div style="color: var(--text-muted); font-size: 0.7rem; text-align: center; padding-top: 1rem;">Not enough recent data yet</div>';
                }
            }
        }

        function renderLiveSignalChart(container, sightings) {
            const width = container.clientWidth - 20 || 200;
            const height = container.clientHeight || 64;
            const padding = { left: 28, right: 6, top: 8, bottom: 14 };
            // Fixed y-axis (unlike renderRssiChart's auto-scaled one) so the
            // chart doesn't visibly rescale/jitter on every 3s poll tick as
            // new points trickle in -- matches the -30/-50/-70/-100 dBm
            // scale and gridline layout of Fieldwatch's own Signal trend
            // graph (Sparkline() in its Widgets.kt).
            const minRssi = -100, maxRssi = -30;
            const majorTicks = [-30, -50, -70, -100];
            const minorTicks = [-40, -60, -80, -90];
            const xScale = (i) => padding.left + (i / (sightings.length - 1)) * (width - padding.left - padding.right);
            const yScale = (rssi) => {
                const clamped = Math.max(minRssi, Math.min(maxRssi, rssi));
                return padding.top + (1 - (clamped - minRssi) / (maxRssi - minRssi)) * (height - padding.top - padding.bottom);
            };
            const lastRssi = sightings[sightings.length - 1].rssi;
            const lineColor = "#ffffff";  // matches the reference card exactly -- no quality-color coding
            const linePath = sightings.map((s, i) => (i === 0 ? "M" : "L") + xScale(i) + "," + yScale(s.rssi)).join(" ");
            const areaPath = linePath + " L" + xScale(sightings.length - 1) + "," + (height - padding.bottom) + " L" + padding.left + "," + (height - padding.bottom) + " Z";

            let grid = "";
            majorTicks.forEach((dbm) => {
                const y = yScale(dbm);
                grid += '<line x1="' + padding.left + '" y1="' + y + '" x2="' + width + '" y2="' + y + '" stroke="var(--border-color)" stroke-width="1"/>';
                grid += '<text x="2" y="' + (y + 3) + '" class="rssi-label" font-size="8">' + dbm + "</text>";
            });
            minorTicks.forEach((dbm) => {
                const y = yScale(dbm);
                grid += '<line x1="' + padding.left + '" y1="' + y + '" x2="' + width + '" y2="' + y + '" stroke="var(--border-color)" stroke-width="0.75" stroke-dasharray="3,4" opacity="0.6"/>';
            });
            grid += '<line x1="' + padding.left + '" y1="' + yScale(-30) + '" x2="' + padding.left + '" y2="' + yScale(-100) + '" stroke="var(--border-color)" stroke-width="1.2"/>';
            // Three vertical dashed dividers across the time axis, same
            // "quartered" look as Fieldwatch's own gridlines.
            for (let c = 1; c < 4; c++) {
                const x = padding.left + (width - padding.left - padding.right) * c / 4;
                grid += '<line x1="' + x + '" y1="' + yScale(-30) + '" x2="' + x + '" y2="' + yScale(-100) + '" stroke="var(--border-color)" stroke-width="0.75" stroke-dasharray="3,5" opacity="0.5"/>';
            }

            const lastX = xScale(sightings.length - 1);
            const lastY = yScale(lastRssi);

            container.innerHTML = '<svg viewBox="0 0 ' + width + " " + height + '" preserveAspectRatio="none">' +
                '<defs><linearGradient id="liveSignalGradient" x1="0%" y1="0%" x2="0%" y2="100%">' +
                '<stop offset="0%" style="stop-color: ' + lineColor + '; stop-opacity: 0.3"/>' +
                '<stop offset="100%" style="stop-color: ' + lineColor + '; stop-opacity: 0.05"/>' +
                "</linearGradient></defs>" +
                grid +
                '<path class="rssi-area" d="' + areaPath + '" style="fill: url(#liveSignalGradient); stroke: none;"/>' +
                '<path class="rssi-line" d="' + linePath + '" style="stroke: ' + lineColor + ';"/>' +
                '<circle cx="' + lastX + '" cy="' + lastY + '" r="3.4" fill="' + lineColor + '"/>' +
                "</svg>";
        }

        function renderPresenceTrack(container, sightings, windowMinutes) {
            // Fieldwatch-style presence track (PresenceTrack() in its
            // Widgets.kt): actual time SPANS the device was present within
            // the window, not just a single aggregate percentage -- groups
            // consecutive sightings less than 45s apart (3x the poll
            // cadence) into one continuous span so brief gaps between
            // individual adverts don't fragment into dozens of slivers.
            const width = container.clientWidth || 260;
            const height = container.clientHeight || 16;
            if (!sightings.length) {
                container.innerHTML = '<svg viewBox="0 0 ' + width + " " + height + '"><rect width="' + width + '" height="' + height + '" rx="3" fill="var(--bg-tertiary)"/></svg>';
                return;
            }
            const windowMs = windowMinutes * 60 * 1000;
            const now = Date.now();
            const start = now - windowMs;
            const GAP_MS = 45000;
            const spans = [];
            let spanStart = null, prevTs = null;
            sightings.forEach((s) => {
                const ts = new Date(s.timestamp).getTime();
                if (spanStart === null) {
                    spanStart = ts;
                } else if (ts - prevTs > GAP_MS) {
                    spans.push([spanStart, prevTs]);
                    spanStart = ts;
                }
                prevTs = ts;
            });
            if (spanStart !== null) spans.push([spanStart, prevTs]);

            const xOf = (ts) => ((Math.max(start, Math.min(now, ts)) - start) / windowMs) * width;
            let bars = '<rect width="' + width + '" height="' + height + '" rx="3" fill="var(--bg-tertiary)"/>';
            spans.forEach(([a, b]) => {
                const x1 = xOf(a), x2 = xOf(b);
                const w = Math.max(2, x2 - x1);
                bars += '<rect x="' + x1 + '" y="' + (height * 0.15) + '" width="' + w + '" height="' + (height * 0.7) + '" rx="1.5" fill="var(--accent-blue)" opacity="0.85"/>';
            });
            container.innerHTML = '<svg viewBox="0 0 ' + width + " " + height + '" preserveAspectRatio="none">' + bars + "</svg>";
        }

        function closeModal() {
            stopLiveSignalPolling();
            document.getElementById('device-modal').classList.remove('active');
        }

        function csvField(val) {
            const s = String(val);
            if (s.includes(',') || s.includes('"') || s.includes('\\n')) {
                return '"' + s.replace(/"/g, '""') + '"';
            }
            return s;
        }

        document.querySelectorAll('.device-table th.sortable').forEach(th => {
            th.addEventListener('click', () => setSort(th.dataset.sort));
        });

        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', toggleSelectAllVisible);
        }

        document.getElementById('search').addEventListener('input', () => {
            if (dateFilteredDevices !== null) {
                renderDevices();
                return;
            }
            selectedMacs.clear();
            lastSelectedIndex = null;
            queueDeviceRefresh(true);
        });
        document.getElementById('device-modal').addEventListener('click', (e) => { if (e.target.id === 'device-modal') closeModal(); });
        document.getElementById('shortcuts-modal').addEventListener('click', (e) => { if (e.target.id === 'shortcuts-modal') closeShortcutsModal(); });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in input/textarea
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            const modalActive = document.getElementById('device-modal').classList.contains('active');

            if (e.key === 'Escape') {
                closeModal();
                closeShortcutsModal();
            } else if (e.key === 'r' || e.key === 'R') {
                // Refresh
                refreshDevices();
            } else if (e.key === '/') {
                // Focus search
                e.preventDefault();
                document.getElementById('search').focus();
            } else if (e.key === 'w' && modalActive && currentDeviceMac) {
                // Toggle watch on current device
                toggleWatch(currentDeviceMac);
            } else if (e.key === '1') {
                document.querySelector('[data-filter="all"]').click();
            } else if (e.key === '2') {
                document.querySelector('[data-filter="watched"]').click();
            } else if (e.key === '3') {
                document.querySelector('[data-filter="phone"]').click();
            } else if (e.key === '4') {
                document.querySelector('[data-filter="laptop"]').click();
            } else if (e.key === '5') {
                document.querySelector('[data-filter="audio"]').click();
            } else if (e.key === '?') {
                showShortcutsModal();
            }
        });

        function toDatetimeLocalValue(date) {
            const pad = n => String(n).padStart(2, '0');
            return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) +
                'T' + pad(date.getHours()) + ':' + pad(date.getMinutes());
        }

        (function initDateRangeDefaults() {
            const startEl = document.getElementById('search-start');
            const endEl = document.getElementById('search-end');
            if (!startEl || !endEl) return;
            const now = new Date();
            const anHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
            startEl.value = toDatetimeLocalValue(anHourAgo);
            endEl.value = toDatetimeLocalValue(now);
        })();

        (function initHideCategorized() {
            const classCb = document.getElementById('hide-classified-toggle');
            if (classCb) classCb.checked = hideClassified;
            const groupCb = document.getElementById('hide-grouped-toggle');
            if (groupCb) groupCb.checked = hideGrouped;
        })();

        updateViewToggle();
        updateSortIndicators();
        loadGroupsForBulkSelect();
        loadCategories();
        updateSelectionUI();
        updatePaginationUI();
        refreshDevices();
        loadLiveStats();
        setInterval(refreshDevices, 3000);
        loadPriorityDevices();
        setInterval(loadPriorityDevices, 5000);
        setInterval(loadLiveStats, 3000);
        startLiveEventStream();
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BlueWatch</title>
    <style>
        :root {
            --bg-primary: #0d0d0d;
            --bg-secondary: #141414;
            --bg-tertiary: #1a1a1a;
            --text-primary: #e0e0e0;
            --text-secondary: #888888;
            --text-muted: #555555;
            --accent-red: #2563eb;
            --border-color: #2a2a2a;
            --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: var(--font-mono); background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; display: flex; align-items: center; justify-content: center; }

        .login-container { width: 100%; max-width: 380px; padding: 1rem; }

        .login-box { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 4px; padding: 2rem; }

        .login-header { text-align: center; margin-bottom: 2rem; }
        .login-icon { color: var(--accent-red); font-size: 2rem; margin-bottom: 0.75rem; }
        .login-title { font-size: 1.25rem; font-weight: 700; letter-spacing: 0.1em; }
        .login-title span { color: var(--accent-red); }
        .login-subtitle { font-size: 0.7rem; color: var(--text-muted);  letter-spacing: 0.15em; margin-top: 0.5rem; }

        .form-group { margin-bottom: 1rem; }
        .form-label { display: block; font-size: 0.65rem;  letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 0.5rem; }
        .form-input { width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 3px; background: var(--bg-tertiary); color: var(--text-primary); font-family: var(--font-mono); font-size: 0.9rem; }
        .form-input:focus { outline: none; border-color: var(--accent-red); }

        .btn { width: 100%; padding: 0.75rem; border: none; border-radius: 3px; background: var(--accent-red); color: white; font-family: var(--font-mono); font-size: 0.8rem; font-weight: 600;  letter-spacing: 0.1em; cursor: pointer; transition: background 0.1s; }
        .btn:hover { background: #1d4ed8; }

        .error-msg { background: rgba(220, 38, 38, 0.1); border: 1px solid var(--accent-red); border-radius: 3px; padding: 0.75rem; margin-bottom: 1rem; color: var(--accent-red); font-size: 0.8rem; text-align: center; display: none; }
        .error-msg.show { display: block; }

        [data-theme="light"] { --bg-primary: #f5f5f5; --bg-secondary: #e8e8e8; --bg-tertiary: #ffffff; --text-primary: #1a1a1a; --text-secondary: #555555; --text-muted: #888888; --accent-red: #2563eb; --border-color: #cccccc; }

        .theme-toggle { position: fixed; top: 1rem; right: 1rem; background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); font-family: var(--font-mono); font-size: 0.75rem; padding: 0.3rem 0.5rem; cursor: pointer; border-radius: 3px; transition: all 0.1s; }
        .theme-toggle:hover { color: var(--text-primary); border-color: var(--border-active, #999); }
    </style>
</head>
<body>
    <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle light/dark mode">☀</button>
    <div class="login-container">
        <div class="login-box">
            <div class="login-header">
                <div class="login-icon">◉</div>
                <h1 class="login-title">BLUE<span>HOOD</span></h1>
                <p class="login-subtitle">Authentication Required</p>
            </div>

            <div class="error-msg" id="error-msg">Invalid credentials</div>

            <form id="login-form">
                <div class="form-group">
                    <label class="form-label">Username</label>
                    <input type="text" class="form-input" id="username" name="username" autocomplete="username" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" class="form-input" id="password" name="password" autocomplete="current-password" required>
                </div>
                <button type="submit" class="btn">Authenticate</button>
            </form>
        </div>
    </div>

    <script>
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            const btn = document.getElementById('theme-toggle');
            if (btn) btn.textContent = theme === 'light' ? '☽' : '☀';
        }
        function toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            localStorage.setItem('bluewatch_theme', next);
            applyTheme(next);
        }
        applyTheme(localStorage.getItem('bluewatch_theme') || 'dark');

        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                if (response.ok) {
                    window.location.href = '/';
                } else {
                    document.getElementById('error-msg').classList.add('show');
                }
            } catch (error) {
                document.getElementById('error-msg').classList.add('show');
            }
        });
    </script>
</body>
</html>
"""
