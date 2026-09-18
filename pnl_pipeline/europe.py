"""
All-marketplace ("All Europe") rollup. Direct Python port of
Google script/refresh.gs.txt's recomputeEuropeAggregate_().

The Europe aggregate is only valid once EVERY marketplace code in
config.all_marketplace_codes() has appeared with processed data — not just
every currently-"configured" one. A stub marketplace still counts as "not
yet included". This is a GLOBAL flag (computed once across the whole
monthly table), not per-period, matching the Apps Script original exactly:
even a period where every marketplace happens to have a row does not make
`europe_aggregate_valid` true if some other period is missing a marketplace
that has never appeared in the table at all.
"""

from __future__ import annotations

import pandas as pd

from .config import SHARED_FIXED_COST_EUR_PER_MONTH, all_marketplace_codes
from .pipeline import derive_metrics

# Raw components summed directly across marketplaces for each period. Note
# mfn_estimated_dhl_cost / mfn_shipping_gap are already-DERIVED per-
# marketplace values here (different marketplaces can have different DHL
# rates), summed as-is rather than recomputed from a blended rate.
_EUROPE_SUM_FIELDS = [
    "financial_product_sales_ex_vat", "refunds_ex_vat", "direct_amazon_fees",
    "advertising_spend", "cogs", "estimated_freight", "estimated_freight_from_fallback",
    "other_fees", "fba_inbound_freight", "mfn_order_count", "mfn_shipping_credit_ex_vat",
    "mfn_estimated_dhl_cost", "mfn_shipping_gap",
]


def recompute_europe_aggregate(monthly_marketplace: pd.DataFrame) -> pd.DataFrame:
    if monthly_marketplace.empty:
        return pd.DataFrame(columns=[
            "period", "financial_product_sales_ex_vat", "refunds_ex_vat", "net_product_revenue",
            "direct_amazon_fees", "advertising_spend", "cogs", "estimated_freight",
            "estimated_freight_from_fallback", "freight_estimate_on_estimate_pct", "other_fees",
            "fba_inbound_freight", "mfn_order_count", "mfn_shipping_credit_ex_vat",
            "mfn_estimated_dhl_cost", "mfn_shipping_gap", "contribution_before_ads",
            "shared_fixed_cost", "payment_tacos_pct", "contribution_after_ads", "fixed_cost_pct",
            "fully_loaded_contribution", "europe_aggregate_valid", "marketplaces_included",
        ])

    all_codes = set(all_marketplace_codes())
    present_codes = set(monthly_marketplace["marketplace"].unique())
    is_full_europe = all_codes <= present_codes
    included_list = ", ".join(sorted(present_codes))

    rows = []
    for period, group in monthly_marketplace.groupby("period"):
        sums = {f: (group[f].sum() if f in group.columns else 0) for f in _EUROPE_SUM_FIELDS}

        net_revenue = sums["financial_product_sales_ex_vat"] + sums["refunds_ex_vat"]

        derived = derive_metrics(
            {
                "financial_product_sales_ex_vat": sums["financial_product_sales_ex_vat"],
                "refunds_ex_vat": sums["refunds_ex_vat"],
                "direct_amazon_fees": sums["direct_amazon_fees"],
                "advertising_spend": sums["advertising_spend"],
                "cogs": sums["cogs"],
                "estimated_freight": sums["estimated_freight"],
                "estimated_freight_from_fallback": sums["estimated_freight_from_fallback"],
                "other_fees": sums["other_fees"],
                "fba_inbound_freight": sums["fba_inbound_freight"],
                "mfn_order_count": sums["mfn_order_count"],
                "mfn_shipping_credit_ex_vat": sums["mfn_shipping_credit_ex_vat"],
            },
            mkt_cfg=None,
            mfn_estimated_dhl_cost=sums["mfn_estimated_dhl_cost"],
            mfn_shipping_gap=sums["mfn_shipping_gap"],
        )

        fixed_cost_pct = (
            round(abs(SHARED_FIXED_COST_EUR_PER_MONTH) / net_revenue * 1000) / 10
            if (is_full_europe and net_revenue) else None
        )

        rows.append({
            "period": period,
            "financial_product_sales_ex_vat": sums["financial_product_sales_ex_vat"],
            "refunds_ex_vat": sums["refunds_ex_vat"],
            "net_product_revenue": net_revenue,
            "direct_amazon_fees": sums["direct_amazon_fees"],
            "advertising_spend": sums["advertising_spend"],
            "cogs": sums["cogs"],
            "estimated_freight": sums["estimated_freight"],
            "estimated_freight_from_fallback": sums["estimated_freight_from_fallback"],
            "freight_estimate_on_estimate_pct": derived["freight_estimate_on_estimate_pct"],
            "other_fees": sums["other_fees"],
            "fba_inbound_freight": sums["fba_inbound_freight"],
            "mfn_order_count": sums["mfn_order_count"],
            "mfn_shipping_credit_ex_vat": sums["mfn_shipping_credit_ex_vat"],
            "mfn_estimated_dhl_cost": sums["mfn_estimated_dhl_cost"],
            "mfn_shipping_gap": sums["mfn_shipping_gap"],
            "contribution_before_ads": derived["contribution_before_ads"],
            "shared_fixed_cost": -SHARED_FIXED_COST_EUR_PER_MONTH if is_full_europe else None,
            "payment_tacos_pct": derived["payment_tacos_pct"],
            "contribution_after_ads": derived["contribution_after_ads"],
            "fixed_cost_pct": fixed_cost_pct,
            "fully_loaded_contribution": (
                derived["contribution_after_ads"] - SHARED_FIXED_COST_EUR_PER_MONTH
                if is_full_europe else None
            ),
            "europe_aggregate_valid": is_full_europe,
            "marketplaces_included": included_list,
        })

    return pd.DataFrame(rows).sort_values("period").reset_index(drop=True)
