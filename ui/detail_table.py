"""Grouped P&L detail table -- hand-rolled HTML, per the project spec's
explicit fallback allowance (st.dataframe/Styler cannot interleave bold
subtotal rows with a section header row the way this design needs)."""

from __future__ import annotations

import html

import streamlit as st

from i18n import t
from ui.kpi import fmt_money, fmt_pct

# (field_key, i18n_row_key, kind, is_subtotal) -- kind in {"money", "pct", "count"}
_SECTIONS = [
    ("section_revenue", [
        ("financial_product_sales_ex_vat", "row_financial_product_sales", "money", False),
        ("refunds_ex_vat", "row_refunds", "money", False),
        ("net_product_revenue", "row_net_product_revenue", "money", True),
    ], False),
    ("section_amazon_fees", [
        ("direct_amazon_fees", "row_direct_amazon_fees", "money", False),
        ("advertising_spend", "row_advertising_spend", "money", False),
        ("other_fees", "row_other_fees", "money", False),
        ("fba_inbound_freight", "row_fba_inbound_freight", "money", False),
    ], False),
    ("section_cogs_freight", [
        ("cogs", "row_cogs", "money", False),
        ("estimated_freight", "row_estimated_freight", "money", False),
    ], False),
    ("section_mfn_shipping", [
        ("mfn_order_count", "row_mfn_order_count", "count", False),
        ("mfn_shipping_credit_ex_vat", "row_mfn_shipping_credit", "money", False),
        ("mfn_estimated_dhl_cost", "row_mfn_estimated_dhl_cost", "money", False),
        ("mfn_shipping_gap", "row_mfn_shipping_gap", "money", True),
    ], False),
    ("section_contribution", [
        ("contribution_before_ads", "row_contribution_before_ads", "money", True),
        ("payment_tacos_pct", "row_payment_tacos", "pct", False),
        ("contribution_after_ads", "row_contribution_after_ads", "money", True),
    ], False),
    ("section_shared_fixed_costs", [
        ("shared_fixed_cost", "row_shared_fixed_cost", "money", False),
        ("fixed_cost_pct", "row_fixed_cost_pct", "pct", False),
        ("fully_loaded_contribution", "row_fully_loaded_contribution", "money", True),
    ], True),
]


def _fmt_count(v) -> str:
    if v is None or v == "":
        return "—"
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return "—"


def _fmt_cell(value, kind: str) -> tuple[str, str]:
    """Returns (display_text, css_class)."""
    if value is None or value == "":
        return "—", "na"
    if kind == "money":
        text = fmt_money(value)
    elif kind == "pct":
        text = fmt_pct(value)
    else:
        text = _fmt_count(value)

    if kind != "money":
        # Percentages (e.g. TACoS) and counts are magnitudes, not profit/loss
        # -- color only money rows red/green, matching the original
        # reference UI's plain (uncolored) fmtPct/fmtCount treatment.
        return text, ""
    try:
        cls = "neg" if float(value) < 0 else ("pos" if float(value) > 0 else "")
    except (TypeError, ValueError):
        cls = ""
    return text, cls


def render_pnl_table(columns: list[tuple[str, dict]], lang: str, is_europe: bool) -> None:
    """`columns`: list of (column_label, metrics_dict) in display order --
    the caller (app.py) is responsible for putting the YTD column last."""
    col_labels = [html.escape(label) for label, _ in columns]

    rows_html = []
    for section_key, fields, europe_only in _SECTIONS:
        if europe_only and not is_europe:
            continue
        rows_html.append(
            f'<tr class="section-header"><td>{html.escape(t(section_key, lang))}</td>'
            + "".join(f"<td></td>" for _ in columns) + "</tr>"
        )
        for field_key, row_key, kind, is_subtotal in fields:
            row_cls = "subtotal" if is_subtotal else ""
            cells = []
            for _, metrics in columns:
                if europe_only and metrics is not None and not metrics.get("europe_aggregate_valid"):
                    cells.append(f'<td class="na">{html.escape(t("not_valid_europe", lang))}</td>')
                    continue
                value = metrics.get(field_key) if metrics else None
                text, cls = _fmt_cell(value, kind)
                cells.append(f'<td class="{cls}">{html.escape(text)}</td>')
            rows_html.append(
                f'<tr class="{row_cls}"><td>{html.escape(t(row_key, lang))}</td>{"".join(cells)}</tr>'
            )

    header_html = "<tr><th></th>" + "".join(f"<th>{lbl}</th>" for lbl in col_labels) + "</tr>"
    table_html = f'<table class="fora-pnl">{header_html}{"".join(rows_html)}</table>'
    st.markdown(f'<div class="scroll">{table_html}</div>', unsafe_allow_html=True)
