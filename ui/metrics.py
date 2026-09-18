"""
UI-side aggregation helpers. Every KPI card, chart, and table column that
needs a range of periods (a single month / a quarter / YTD / All Europe)
goes through `get_period_range_metrics` -- filter to raw component columns,
sum them, call pnl_pipeline.pipeline.derive_metrics() once. Never sum or
average an already-derived percentage field directly.

`contribution_margin_pct` is a UI-only convenience ratio (used by the combo
chart and donut chart) with no Apps Script equivalent -- kept out of
pnl_pipeline/pipeline.py so that module stays a pure, unchanged port.
"""

from __future__ import annotations

import pandas as pd

from i18n import month_label
from pnl_pipeline.config import SHARED_FIXED_COST_EUR_PER_MONTH
from pnl_pipeline.pipeline import derive_metrics

_MARKETPLACE_RAW_FIELDS = [
    "financial_product_sales_ex_vat", "refunds_ex_vat", "direct_amazon_fees",
    "advertising_spend", "other_fees", "fba_inbound_freight", "transfers_excluded",
    "cogs", "estimated_freight", "estimated_freight_from_fallback",
    "mfn_order_count", "mfn_shipping_credit_ex_vat", "row_count",
]

_EUROPE_RAW_FIELDS = [
    "financial_product_sales_ex_vat", "refunds_ex_vat", "direct_amazon_fees",
    "advertising_spend", "cogs", "estimated_freight", "estimated_freight_from_fallback",
    "other_fees", "fba_inbound_freight", "mfn_order_count", "mfn_shipping_credit_ex_vat",
    "mfn_estimated_dhl_cost", "mfn_shipping_gap",
]


def get_period_range_metrics(df: pd.DataFrame, periods: list[str], mkt_cfg: dict | None = None,
                              is_europe: bool = False) -> dict | None:
    if df is None or df.empty:
        return None
    subset = df[df["period"].isin(periods)]
    if subset.empty:
        return None

    if is_europe:
        raw = {f: subset[f].sum() if f in subset.columns else 0 for f in _EUROPE_RAW_FIELDS}
        derived = derive_metrics(
            {k: v for k, v in raw.items() if k not in ("mfn_estimated_dhl_cost", "mfn_shipping_gap")},
            mkt_cfg=None,
            mfn_estimated_dhl_cost=raw["mfn_estimated_dhl_cost"],
            mfn_shipping_gap=raw["mfn_shipping_gap"],
        )
        merged = {**raw, **derived}
        net_revenue = derived["net_product_revenue"]
        is_full_europe = bool(subset["europe_aggregate_valid"].all()) if "europe_aggregate_valid" in subset else False
        if is_full_europe and net_revenue:
            merged["shared_fixed_cost"] = -SHARED_FIXED_COST_EUR_PER_MONTH
            merged["fixed_cost_pct"] = round(abs(SHARED_FIXED_COST_EUR_PER_MONTH) / net_revenue * 1000) / 10
            merged["fully_loaded_contribution"] = derived["contribution_after_ads"] - SHARED_FIXED_COST_EUR_PER_MONTH
        else:
            merged["shared_fixed_cost"] = None
            merged["fixed_cost_pct"] = None
            merged["fully_loaded_contribution"] = None
        merged["europe_aggregate_valid"] = is_full_europe
        merged["marketplaces_included"] = (
            subset["marketplaces_included"].iloc[-1] if "marketplaces_included" in subset.columns else ""
        )
        return merged

    raw = {f: subset[f].sum() if f in subset.columns else 0 for f in _MARKETPLACE_RAW_FIELDS}
    derived = derive_metrics(raw, mkt_cfg)
    return {**raw, **derived}


def contribution_margin_pct(metrics: dict, is_europe_valid: bool = False) -> float | None:
    net_revenue = metrics.get("net_product_revenue") or 0
    if not net_revenue:
        return None
    if is_europe_valid and metrics.get("fully_loaded_contribution") is not None:
        numerator = metrics["fully_loaded_contribution"]
    else:
        numerator = metrics.get("contribution_after_ads") or 0
    return round(numerator / net_revenue * 1000) / 10


def build_period_options(periods: list[str], lang: str = "en") -> dict[str, list[str]]:
    """Builds the YTD / Q1-Q4 / per-month pill options for the most recent
    year present in `periods`. Only quarters/months that actually have data
    are offered."""
    if not periods:
        return {}
    years = sorted({p.split("-")[0] for p in periods})
    latest_year = years[-1]
    year_periods = sorted(p for p in periods if p.startswith(latest_year))

    options: dict[str, list[str]] = {"YTD": year_periods}
    quarters = {"Q1": ["01", "02", "03"], "Q2": ["04", "05", "06"],
                "Q3": ["07", "08", "09"], "Q4": ["10", "11", "12"]}
    for q_key, months in quarters.items():
        q_periods = [p for p in year_periods if p.split("-")[1] in months]
        if q_periods:
            options[q_key] = q_periods
    for p in year_periods:
        options[month_label(p, lang)] = [p]
    return options
