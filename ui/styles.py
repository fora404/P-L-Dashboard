"""Dark sidebar / KPI card CSS, styled toward the FORA CARE reference
mockup: deep-navy sidebar, pill-shaped filter buttons, top-bordered KPI
cards, and green/red money coloring."""

CSS = """
<style>
:root {
    --fora-navy: #152a4a;
    --fora-navy-light: #21396a;
    --fora-orange: #e8a33d;
    --fora-green: #1e8e4a;
    --fora-red: #c5221f;
    --fora-teal: #2aa8a0;
    --fora-slate: #6b7a99;
    --fora-accent: #21396a;
}

section[data-testid="stSidebar"] {
    background-color: var(--fora-navy);
}
section[data-testid="stSidebar"] * {
    color: #e8ecf3;
}
.fora-avatar {
    width: 56px; height: 56px; border-radius: 50%;
    background: rgba(255,255,255,0.12);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; margin: 4px auto 10px;
}
.fora-brand {
    font-size: 18px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0;
}
.fora-subtitle {
    font-size: 12px;
    color: #9aa7c0;
    text-align: center;
    margin-bottom: 16px;
}
.fora-section-label {
    font-size: 11px;
    letter-spacing: .06em;
    color: #7f8db0;
    margin: 6px 2px 4px;
    font-weight: 600;
}
.fora-footer {
    font-size: 11px;
    color: #6c7999;
    text-align: center;
    margin-top: 24px;
}

/* Sidebar marketplace/Europe buttons rendered as flat rows, not boxed buttons */
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    background: transparent;
    border: none;
    text-align: left;
    justify-content: flex-start;
    color: #e8ecf3;
    font-weight: 500;
    padding: 6px 10px;
    border-radius: 8px;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
    background: var(--fora-navy-light);
    color: #ffffff;
    font-weight: 700;
}
.fora-mkt-value { font-size: 12px; margin: -6px 0 4px 10px; }
.fora-mkt-value.pos { color: #6fe0a0; }
.fora-mkt-value.neg { color: #ff9a94; }
.fora-mkt-value.na { color: #5c6a89; }

/* Pill-style buttons everywhere by default (language toggle, time pills);
   the sidebar-scoped rules above override this back to flat rows there. */
div[data-testid="stButton"] button {
    border-radius: 999px;
    border: 1px solid #dfe3ea;
    background: #fff;
    color: #3c4256;
    font-weight: 600;
    padding: 6px 4px;
}
div[data-testid="stButton"] button[kind="primary"] {
    background: var(--fora-navy);
    color: #fff;
    border-color: var(--fora-navy);
}

.fora-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin: 6px 0 18px;
}
.fora-kpi {
    background: #fff;
    border: 1px solid #e9ebf0;
    border-top: 4px solid var(--fora-accent);
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 2px rgba(20,30,60,0.04);
}
.fora-kpi .label {
    font-size: 11px; font-weight: 700; letter-spacing: .04em;
    color: #7b869c; margin-bottom: 6px; text-transform: uppercase;
}
.fora-kpi .value { font-size: 24px; font-weight: 700; color: #1b2233; }
.fora-kpi .value.pos { color: var(--fora-green); }
.fora-kpi .value.neg { color: var(--fora-red); }
.fora-kpi .note { font-size: 11px; color: #94a0b8; margin-top: 4px; }

.fora-banner {
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0 18px;
    font-size: 13px;
    background: #f1f6ff;
    border: 1px solid #cfe0fb;
    color: #1f3a63;
    display: flex;
    align-items: center;
    gap: 10px;
}
.fora-banner .pin { font-size: 16px; }
.fora-banner.warn { background: #fef7e0; border-color: #f0d68a; color: #6b4e00; }

.fora-badge {
    display: inline-block;
    background: var(--fora-orange);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .03em;
    border-radius: 999px;
    padding: 3px 12px;
}

.fora-placeholder {
    text-align: center;
    padding: 60px 20px;
    color: #888;
}

table.fora-pnl { border-collapse: collapse; width: 100%; font-size: 13px; }
table.fora-pnl th, table.fora-pnl td { padding: 7px 12px; text-align: right; white-space: nowrap; }
table.fora-pnl th { color: #7b869c; font-weight: 600; font-size: 11px; text-transform: uppercase; }
table.fora-pnl th:first-child, table.fora-pnl td:first-child { text-align: left; color: #3c4256; }
table.fora-pnl tr.section-header td {
    background: #f4f6fa; color: #5c6785; font-weight: 700; font-size: 11px;
    letter-spacing: .06em; padding-top: 10px; padding-bottom: 10px;
}
table.fora-pnl tr.subtotal td { font-weight: 700; border-top: 1px solid #dfe3ea; color: #1b2233; }
table.fora-pnl td.pos { color: var(--fora-green); }
table.fora-pnl td.neg { color: var(--fora-red); }
table.fora-pnl td.na { color: #b3bccc; }

.scroll { overflow-x: auto; }
</style>
"""
