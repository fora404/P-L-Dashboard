"""Amazon P&L Dashboard -- Streamlit entry point.

Reads raw Amazon Payment Report CSVs from Google Drive + the Mapping
Master Sheet, runs the Python-ported pipeline (pnl_pipeline/), and renders
the dashboard. Data is cached until "Update Data" is clicked -- no
background polling.
"""

from __future__ import annotations

import streamlit as st

from i18n import month_label, t
from pnl_pipeline import config
from pnl_pipeline.run_pipeline import run_full_pipeline
from ui.charts import combo_chart, margin_meter
from ui.detail_table import render_pnl_table
from ui.kpi import render_placeholder, render_shared_fixed_costs_banner, render_kpi_row
from ui.metrics import build_period_options, contribution_margin_pct, get_period_range_metrics
from ui.styles import CSS

st.set_page_config(page_title="Amazon P&L Dashboard", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "selected_marketplace" not in st.session_state:
    st.session_state.selected_marketplace = "EUROPE"
if "selected_pill" not in st.session_state:
    st.session_state.selected_pill = None

lang = st.session_state.lang


@st.cache_data(show_spinner=False)
def load_data(refresh_key: int):
    return run_full_pipeline()


with st.spinner(t("loading", lang)):
    result = load_data(st.session_state.refresh_key)


# ---------------------------------------------------------------- sidebar --
with st.sidebar:
    st.markdown('<div class="fora-avatar">🧑‍💼</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fora-brand">{t("app_title", lang)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fora-subtitle">{t("app_subtitle", lang)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fora-section-label">{t("marketplace_section_label", lang)}</div>', unsafe_allow_html=True)

    if st.button("🌐 " + t("all_europe", lang), key="mkt_EUROPE", width="stretch",
                 type="primary" if st.session_state.selected_marketplace == "EUROPE" else "secondary"):
        st.session_state.selected_marketplace = "EUROPE"
        st.session_state.selected_pill = None

    if not result.monthly_europe.empty:
        latest_europe = result.monthly_europe.sort_values("period").iloc[-1]
        europe_val = (latest_europe.get("fully_loaded_contribution")
                      if latest_europe.get("europe_aggregate_valid") else latest_europe.get("contribution_after_ads"))
        cls = "pos" if (europe_val or 0) >= 0 else "neg"
        st.markdown(f'<div class="fora-mkt-value {cls}">{europe_val:+,.0f} €</div>', unsafe_allow_html=True)

    for code in config.all_marketplace_codes():
        mkt_cfg = config.MARKETPLACES[code]
        label = mkt_cfg.get("displayName", code)
        if st.button(label, key=f"mkt_{code}", width="stretch",
                     type="primary" if st.session_state.selected_marketplace == code else "secondary"):
            st.session_state.selected_marketplace = code
            st.session_state.selected_pill = None

        if not mkt_cfg.get("configured"):
            st.markdown(f'<div class="fora-mkt-value na">— {t("no_data_yet_title", lang)}</div>', unsafe_allow_html=True)
        else:
            df_mkt = result.monthly_marketplace[result.monthly_marketplace["marketplace"] == code]
            if not df_mkt.empty:
                latest = df_mkt.sort_values("period").iloc[-1]
                val = latest["contribution_after_ads"]
                cls = "pos" if val >= 0 else "neg"
                st.markdown(f'<div class="fora-mkt-value {cls}">{val:+,.0f} €</div>', unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🔄 " + t("update_data", lang), width="stretch"):
        st.session_state.refresh_key += 1
        st.cache_data.clear()
        st.rerun()

    if result.last_refresh_at:
        st.caption(t("last_refresh", lang, ts=result.last_refresh_at))
    else:
        st.caption(t("never_refreshed", lang))

    if result.warnings:
        with st.expander(f"⚠️ {t('warnings_title', lang)} ({len(result.warnings)})"):
            for w in result.warnings:
                st.caption(w)

    st.markdown(f'<div class="fora-footer">{t("footer_note", lang)}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------- main area --
selected = st.session_state.selected_marketplace
is_europe = selected == "EUROPE"
mkt_display_name = t("all_europe", lang) if is_europe else config.MARKETPLACES[selected].get("displayName", selected)

title_col, lang_col = st.columns([5, 1])
with title_col:
    st.markdown(f'<div style="font-size:22px;font-weight:700;">🌐 {mkt_display_name}</div>',
                unsafe_allow_html=True)
    breadcrumb_pill = st.session_state.selected_pill or ""
    breadcrumb_pill_label = (t(f"period_{breadcrumb_pill.lower()}", lang)
                              if breadcrumb_pill in ("YTD", "Q1", "Q2", "Q3", "Q4") else breadcrumb_pill)
    st.caption(f"{breadcrumb_pill_label} · 🌐 {mkt_display_name}" if breadcrumb_pill else f"🌐 {mkt_display_name}")
with lang_col:
    lang_cols = st.columns(2)
    if lang_cols[0].button("EN", key="lang_en", width="stretch",
                            type="primary" if lang == "en" else "secondary"):
        st.session_state.lang = "en"
        st.rerun()
    if lang_cols[1].button("中文", key="lang_zh", width="stretch",
                            type="primary" if lang == "zh" else "secondary"):
        st.session_state.lang = "zh"
        st.rerun()

if is_europe:
    df = result.monthly_europe
else:
    mkt_cfg = config.MARKETPLACES[selected]

    if not mkt_cfg.get("configured"):
        render_placeholder(mkt_cfg.get("displayName", selected), lang)
        st.stop()

    df = result.monthly_marketplace[result.monthly_marketplace["marketplace"] == selected]

if df.empty:
    st.info(t("no_data", lang))
    st.stop()

mkt_cfg_for_metrics = None if is_europe else config.MARKETPLACES[selected]
periods_available = sorted(df["period"].unique().tolist())
period_options = build_period_options(periods_available, lang)
year_periods = period_options.get("YTD", periods_available)

pill_keys = list(period_options.keys())
if st.session_state.selected_pill not in pill_keys:
    st.session_state.selected_pill = pill_keys[0] if pill_keys else None

if pill_keys:
    pill_cols = st.columns(len(pill_keys))
    for i, key in enumerate(pill_keys):
        pill_label = t(f"period_{key.lower()}", lang) if key in ("YTD", "Q1", "Q2", "Q3", "Q4") else key
        if pill_cols[i].button(pill_label, key=f"pill_{key}", width="stretch",
                                type="primary" if st.session_state.selected_pill == key else "secondary"):
            st.session_state.selected_pill = key
            st.rerun()

selected_periods = period_options.get(st.session_state.selected_pill, periods_available)
metrics = get_period_range_metrics(df, selected_periods, mkt_cfg=mkt_cfg_for_metrics, is_europe=is_europe)

if metrics is None:
    st.info(t("no_data", lang))
    st.stop()

is_europe_valid = bool(metrics.get("europe_aggregate_valid")) if is_europe else False
net_profit_value = metrics.get("fully_loaded_contribution") if is_europe_valid else metrics.get("contribution_after_ads")
net_profit_note = t("kpi_net_profit_note_europe", lang) if is_europe_valid else t("kpi_net_profit_note_marketplace", lang)

render_kpi_row([
    {"label": t("kpi_net_revenue", lang), "value": metrics.get("net_product_revenue"),
     "note": t("kpi_net_revenue_note", lang), "accent": "#e8a33d"},
    {"label": t("kpi_net_profit", lang), "value": net_profit_value, "note": net_profit_note,
     "accent": "#1e8e4a"},
    {"label": t("kpi_ads_spend", lang), "value": metrics.get("advertising_spend"),
     "accent": "#21396a"},
    {"label": t("kpi_mfn_orders", lang), "value": metrics.get("mfn_order_count"), "is_count": True,
     "accent": "#2aa8a0"},
    {"label": t("kpi_payment_tacos", lang), "value": metrics.get("payment_tacos_pct"), "is_pct": True,
     "accent": "#6b7a99"},
])

if is_europe:
    render_shared_fixed_costs_banner(metrics, lang)
else:
    st.caption(t("marketplace_fixed_cost_note", lang))

# ---- charts -----------------------------------------------------------
chart_col, meter_col = st.columns([2, 1])
with chart_col:
    header_col, badge_col = st.columns([4, 1])
    header_col.markdown(f'<div style="font-weight:700;margin-top:4px;">{t("chart_combo_title", lang)}</div>',
                         unsafe_allow_html=True)
    badge_col.markdown(f'<div class="fora-badge" style="float:right;">{t("chart_donut_title", lang)}</div>',
                        unsafe_allow_html=True)
    monthly_rows = []
    for p in year_periods:
        row_metrics = get_period_range_metrics(df, [p], mkt_cfg=mkt_cfg_for_metrics, is_europe=is_europe)
        if row_metrics:
            monthly_rows.append((p, row_metrics))
    chart_periods = [p for p, _ in monthly_rows]
    chart_revenue = [m["net_product_revenue"] for _, m in monthly_rows]
    chart_margin = [contribution_margin_pct(m, is_europe_valid=bool(m.get("europe_aggregate_valid"))) or 0
                    for _, m in monthly_rows]
    st.plotly_chart(combo_chart(chart_periods, chart_revenue, chart_margin, lang), width="stretch")

with meter_col:
    margin = contribution_margin_pct(metrics, is_europe_valid=is_europe_valid)
    st.plotly_chart(margin_meter(margin, lang), width="stretch")

# ---- detail table -------------------------------------------------------
detail_title_col, detail_badge_col = st.columns([4, 1])
detail_title_col.markdown(
    f'<div style="font-size:18px;font-weight:700;margin-top:8px;">'
    f'{t("detail_table_title", lang)} — {st.session_state.selected_pill or ""}</div>',
    unsafe_allow_html=True,
)
detail_badge_col.markdown(f'<div class="fora-badge" style="float:right;">{t("detail_view", lang)}</div>',
                           unsafe_allow_html=True)

table_columns = []
for p in selected_periods:
    m = get_period_range_metrics(df, [p], mkt_cfg=mkt_cfg_for_metrics, is_europe=is_europe)
    table_columns.append((month_label(p, lang), m))

ytd_metrics = get_period_range_metrics(df, year_periods, mkt_cfg=mkt_cfg_for_metrics, is_europe=is_europe)
table_columns.append((t("col_ytd", lang), ytd_metrics))

render_pnl_table(table_columns, lang, is_europe)
