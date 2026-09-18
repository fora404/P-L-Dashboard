"""KPI cards, Shared Fixed Costs banner, and the unconfigured-marketplace
placeholder. Rendered as HTML via st.markdown (unsafe_allow_html=True),
per the project spec's explicit allowance for the dark-card styling."""

from __future__ import annotations

import html

import streamlit as st

from i18n import t


def fmt_money(v) -> str:
    """European format, e.g. 1234.56 -> "1.234,56 €"; -1234.56 -> "-1.234,56 €"."""
    if v is None or v == "":
        return "—"
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    sign = "-" if n < 0 else ""
    s = f"{abs(n):,.2f}"
    s = s.replace(",", "⁠").replace(".", ",").replace("⁠", ".")
    return f"{sign}{s} €"


def fmt_pct(v) -> str:
    if v is None or v == "":
        return "—"
    try:
        return f"{float(v):.1f}%"
    except (TypeError, ValueError):
        return "—"


def fmt_count(v) -> str:
    if v is None or v == "":
        return "—"
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return "—"


def render_kpi_row(cards: list[dict]) -> None:
    """`cards`: list of {"label", "value", "note"?, "is_pct"?, "is_count"?, "accent"?}.

    IMPORTANT: every fragment concatenated into the final markdown string
    must be a single line with no bare/whitespace-only lines in between --
    CommonMark treats a whitespace-only line as ending a raw-HTML block, so
    a multi-line, indented template here would make everything after the
    first blank line (e.g. an empty optional "note") fall out of the HTML
    block and render as literal text instead of a styled card.
    """
    items_html = []
    for card in cards:
        raw_value = card["value"]
        if card.get("is_pct"):
            value_str = fmt_pct(raw_value)
        elif card.get("is_count"):
            value_str = fmt_count(raw_value)
        else:
            value_str = fmt_money(raw_value)
        try:
            neg = raw_value is not None and raw_value != "" and float(raw_value) < 0
        except (TypeError, ValueError):
            neg = False
        value_cls = "neg" if neg else ("pos" if (raw_value or 0) and not card.get("is_pct") and not card.get("is_count") else "")
        note_html = f'<div class="note">{html.escape(card["note"])}</div>' if card.get("note") else ""
        accent = card.get("accent") or "var(--fora-accent)"
        items_html.append(
            f'<div class="fora-kpi" style="border-top-color:{accent}">'
            f'<div class="label">{html.escape(card["label"])}</div>'
            f'<div class="value {value_cls}">{html.escape(value_str)}</div>'
            f"{note_html}</div>"
        )
    st.markdown(f'<div class="fora-kpi-grid">{"".join(items_html)}</div>', unsafe_allow_html=True)


def render_shared_fixed_costs_banner(metrics: dict, lang: str) -> None:
    from pnl_pipeline.config import SHARED_FIXED_COST_EUR_PER_MONTH

    is_valid = bool(metrics.get("europe_aggregate_valid"))
    title = html.escape(t("shared_fixed_costs_title", lang))
    if is_valid:
        body = html.escape(t("shared_fixed_costs_valid", lang))
        detail = (
            f'{t("row_shared_fixed_cost", lang)}: {fmt_money(metrics.get("shared_fixed_cost"))} &middot; '
            f'{t("row_fixed_cost_pct", lang)}: {fmt_pct(metrics.get("fixed_cost_pct"))}'
        )
        st.markdown(
            f'<div class="fora-banner"><b>{title}</b><br>{body}<br><small>{detail}</small></div>',
            unsafe_allow_html=True,
        )
    else:
        included = html.escape(metrics.get("marketplaces_included") or "—")
        body = html.escape(t("shared_fixed_costs_invalid", lang,
                              amount=f"{SHARED_FIXED_COST_EUR_PER_MONTH:,.0f}", included=included))
        st.markdown(
            f'<div class="fora-banner warn"><b>{title}</b><br>{body}</div>',
            unsafe_allow_html=True,
        )


def render_placeholder(marketplace_label: str, lang: str) -> None:
    title = html.escape(t("no_data_yet_title", lang))
    body = html.escape(t("no_data_yet_body", lang, marketplace=marketplace_label))
    st.markdown(
        f'<div class="fora-placeholder"><h3>{title}</h3><p>{body}</p></div>',
        unsafe_allow_html=True,
    )
