"""Dark sidebar / KPI card CSS, adapted from Google script/index.html.txt's
color conventions (green/red for positive/negative, muted warn/err boxes)
into the dark-sidebar layout the project spec calls for."""

CSS = """
<style>
:root {
    --fora-green: #1e8e4a;
    --fora-red: #c5221f;
    --fora-accent: #1a73e8;
}

section[data-testid="stSidebar"] {
    background-color: #14161a;
}
section[data-testid="stSidebar"] * {
    color: #e6e6e6;
}
section[data-testid="stSidebar"] .fora-brand {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 0;
}
section[data-testid="stSidebar"] .fora-subtitle {
    font-size: 12px;
    color: #9aa0a6;
    margin-bottom: 18px;
}
.fora-mkt-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 13px;
    margin-bottom: 2px;
}
.fora-mkt-row.active { background-color: #2b2f36; font-weight: 600; }
.fora-mkt-row.disabled { color: #5f6368 !important; }
.fora-mkt-value.pos { color: #34a853; }
.fora-mkt-value.neg { color: #f28b82; }

.fora-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin: 10px 0 18px;
}
.fora-kpi {
    background: var(--fora-kpi-bg, #fff);
    border: 1px solid var(--fora-kpi-border, #e3e3e0);
    border-left: 4px solid var(--fora-accent);
    border-radius: 8px;
    padding: 14px 16px;
}
.fora-kpi .label { font-size: 12px; color: #666; margin-bottom: 4px; }
.fora-kpi .value { font-size: 22px; font-weight: 700; }
.fora-kpi .value.pos { color: var(--fora-green); }
.fora-kpi .value.neg { color: var(--fora-red); }
.fora-kpi .note { font-size: 11px; color: #888; margin-top: 4px; }

.fora-banner {
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0 18px;
    font-size: 13px;
    background: #f1f6ff;
    border: 1px solid #cfe0fb;
    color: #1f3a63;
}
.fora-banner.warn { background: #fef7e0; border-color: #f0d68a; color: #6b4e00; }

.fora-placeholder {
    text-align: center;
    padding: 60px 20px;
    color: #888;
}

table.fora-pnl { border-collapse: collapse; width: 100%; font-size: 13px; }
table.fora-pnl th, table.fora-pnl td { padding: 6px 12px; text-align: right; white-space: nowrap; }
table.fora-pnl th:first-child, table.fora-pnl td:first-child { text-align: left; }
table.fora-pnl tr.section-header td { background: #f0f0ee; font-weight: 700; font-size: 12px; letter-spacing: .04em; }
table.fora-pnl tr.subtotal td { font-weight: 700; border-top: 1px solid #ccc; }
table.fora-pnl td.pos { color: var(--fora-green); }
table.fora-pnl td.neg { color: var(--fora-red); }
table.fora-pnl td.na { color: #aaa; }

.fora-pill-note { font-size: 11px; color: #999; margin: -6px 0 10px; }
</style>
"""
