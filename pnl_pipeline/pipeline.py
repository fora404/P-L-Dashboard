"""
Row-level classification + COGS resolution + per-period aggregation.
Direct Python port of Google script/pipeline.gs.txt.

DESIGN CHOICE vs. the Apps Script original: Apps Script processes and
persists ONE FILE AT A TIME (with a per-file/per-period manifest) purely to
work around its 6-minute execution cap and to allow incremental/resumable
runs. Python has no such cap, so run_pipeline.py re-reads every file fresh
on each refresh and sums directly into period aggregates via
`aggregate_period_aggs` below — the per-row CALCULATION rules in this module
are ported unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import FREIGHT_FALLBACK_PCT_OF_COGS, LEGACY_COGS_FALLBACK_PCT_OF_SALES
from .parsing import parse_amount, parse_period

# Raw component fields that get summed when combining multiple period
# aggregates (multiple files -> one marketplace-month, or multiple months ->
# a quarter/YTD/Europe rollup). Never sum/average anything NOT in this list
# (i.e. never sum already-derived percentage fields).
_SUMMABLE_FIELDS = [
    "financial_product_sales_ex_vat", "refunds_ex_vat", "direct_amazon_fees",
    "advertising_spend", "other_fees", "fba_inbound_freight", "transfers_excluded",
    "cogs", "estimated_freight", "estimated_freight_from_fallback",
    "mfn_order_count", "mfn_shipping_credit_ex_vat", "row_count",
]


def empty_period_agg() -> dict:
    return {
        "financial_product_sales_ex_vat": 0.0, "refunds_ex_vat": 0.0, "direct_amazon_fees": 0.0,
        "advertising_spend": 0.0, "other_fees": 0.0, "fba_inbound_freight": 0.0,
        "transfers_excluded": 0.0, "cogs": 0.0, "estimated_freight": 0.0,
        "estimated_freight_from_fallback": 0.0, "row_count": 0,
        "mfn_order_ids": set(),  # distinct MFN order_ids this period (dedup within one file)
        "mfn_shipping_credit_ex_vat": 0.0,
    }


def category_of(mkt_cfg: dict, txn_type, description) -> str:
    cls = mkt_cfg["classification"]

    for rule in cls["transfers"]:
        if txn_type == rule["txnType"]:
            return "transfer"

    for rule in cls["advertising"]:
        if txn_type == rule["txnType"] and description == rule["description"]:
            return "advertising"

    for rule in cls.get("fbaInboundFreight", []):
        if txn_type == rule["txnType"] and description == rule["description"]:
            return "fba_inbound_freight"

    if txn_type in cls["orderTypes"]:
        return "order"
    if txn_type in cls["refundTypes"]:
        return "refund"
    return "other_fee"


@dataclass
class ProcessFileResult:
    periods: dict = field(default_factory=dict)
    data_quality: dict = field(default_factory=dict)
    unmapped_skus: dict = field(default_factory=dict)
    qa: dict = field(default_factory=dict)


def _parse_qty(raw) -> float:
    """Mirrors the JS: qty = (row.qty !== null/undefined/'') ? parseFloat(row.qty) : 0."""
    if raw is None or raw == "":
        return 0.0
    try:
        v = float(raw)
        return v if v == v else 0.0  # guard against NaN
    except (TypeError, ValueError):
        return 0.0


def process_file_rows(csv_data: dict, mkt_code: str, mkt_cfg: dict, mm) -> ProcessFileResult:
    """Processes one already-read CSV ({header, rows}) for one marketplace."""
    header = csv_data["header"]
    col_idx = {h: i for i, h in enumerate(header)}

    periods: dict[str, dict] = {}
    data_quality: dict[str, dict] = {}
    unmapped_skus: dict[str, int] = {}
    row_count = 0
    raw_total_sum = 0.0
    transfers_total = 0.0
    recon_mismatches = 0
    periods_touched: set[str] = set()

    col_map = mkt_cfg["columnMap"]
    amount_fields = set(mkt_cfg["amountFields"])
    raw_col_names = list(col_map.keys())

    for raw_row in csv_data["rows"]:
        if not any(str(c).strip() != "" for c in raw_row):
            continue

        row = {}
        for raw_col in raw_col_names:
            canon = col_map[raw_col]
            i = col_idx.get(raw_col)
            v = raw_row[i] if (i is not None and i < len(raw_row)) else None
            row[canon] = parse_amount(v) if canon in amount_fields else v

        row_count += 1
        raw_total_sum += row.get("total") or 0

        cat = category_of(mkt_cfg, row.get("txn_type"), row.get("description"))
        period = parse_period(row.get("datetime"))
        if period is None:
            continue  # excluded from aggregates; still counted in row_count above
        periods_touched.add(period)

        if cat == "transfer":
            transfers_total += row.get("total") or 0

        # Reconciliation identity check (data-integrity QA only).
        component_sum = (
            (row.get("sales_ex_vat") or 0) + (row.get("product_vat") or 0)
            + (row.get("shipping_credit") or 0) + (row.get("shipping_credit_tax") or 0)
            + (row.get("giftwrap_credit") or 0) + (row.get("giftwrap_credit_tax") or 0)
            + (row.get("promo_rebate") or 0) + (row.get("promo_rebate_tax") or 0)
            + (row.get("marketplace_withheld_tax") or 0) + (row.get("selling_fees") or 0)
            + (row.get("fba_fees") or 0) + (row.get("other_transaction_fees") or 0)
            + (row.get("other_amount") or 0)
        )
        if round((row.get("total") or 0) - component_sum, 2) != 0:
            recon_mismatches += 1

        if period not in periods:
            periods[period] = empty_period_agg()
        agg = periods[period]
        agg["row_count"] += 1

        revenue = row.get("sales_ex_vat") if cat in ("order", "refund") else 0
        revenue = revenue or 0
        if revenue > 0:
            agg["financial_product_sales_ex_vat"] += revenue
        elif revenue < 0:
            agg["refunds_ex_vat"] += revenue

        direct_fee = (row.get("selling_fees") or 0) + (row.get("fba_fees") or 0)
        agg["direct_amazon_fees"] += direct_fee
        if cat == "advertising":
            agg["advertising_spend"] += row.get("total") or 0
        # Fee-only rows can hold their full total in the selling/FBA fee
        # components; subtract directFee so the residual (not the full
        # total) lands in Other Fees / FBA Inbound Freight, avoiding a
        # double count.
        if cat == "other_fee":
            agg["other_fees"] += (row.get("total") or 0) - direct_fee
        if cat == "fba_inbound_freight":
            agg["fba_inbound_freight"] += (row.get("total") or 0) - direct_fee
        if cat == "transfer":
            agg["transfers_excluded"] += row.get("total") or 0

        # MFN (merchant-fulfilled) outbound shipping metrics. Shipping
        # credit is summed across EVERY category for MFN-fulfilled rows
        # (not just 'order'), so a negative reversal on a refund row
        # correctly claws back an earlier credit. Distinct order_id is
        # tracked only on 'order' rows.
        if mkt_cfg.get("mfnFulfilmentValue") and row.get("fulfilment") == mkt_cfg["mfnFulfilmentValue"]:
            agg["mfn_shipping_credit_ex_vat"] += row.get("shipping_credit") or 0
            if cat == "order" and row.get("order_id"):
                agg["mfn_order_ids"].add(row["order_id"])

        if cat == "order":
            dq = data_quality.setdefault(period, {})
            qty = _parse_qty(row.get("qty"))
            if not row.get("seller_sku") or not qty:
                # Missing SKU/qty on an order row gets cogs=0 and level
                # "NaN" -- the 30% fallback is NEVER applied here (only for
                # SKU-present-but-unmappable rows, below).
                dq["NaN"] = dq.get("NaN", 0) + 1
            else:
                cogs, level = mm.resolve_cogs(mkt_cfg["mappingMasterLabel"], row["seller_sku"], qty, period)
                if cogs is None:
                    cogs = max(row.get("sales_ex_vat") or 0, 0) * LEGACY_COGS_FALLBACK_PCT_OF_SALES
                    level = "C"
                    unmapped_skus[row["seller_sku"]] = unmapped_skus.get(row["seller_sku"], 0) + 1
                dq[level] = dq.get(level, 0) + 1
                agg["cogs"] += cogs
                freight = abs(cogs) * FREIGHT_FALLBACK_PCT_OF_COGS
                agg["estimated_freight"] += freight
                # "estimated-on-estimated": this row's COGS itself came from
                # the legacy 30% fallback (level 'C'), so the freight
                # estimate is a percentage OF a percentage. Must be
                # surfaced as a share, not treated as an edge case.
                if level == "C":
                    agg["estimated_freight_from_fallback"] += freight

    for period_agg in periods.values():
        period_agg["mfn_order_count"] = len(period_agg["mfn_order_ids"])
        del period_agg["mfn_order_ids"]

    return ProcessFileResult(
        periods=periods,
        data_quality=data_quality,
        unmapped_skus=unmapped_skus,
        qa={
            "rowCount": row_count,
            "rawTotalSum": round(raw_total_sum, 2),
            "transfersTotal": round(transfers_total, 2),
            "reconMismatches": recon_mismatches,
            "periodsTouched": sorted(periods_touched),
        },
    )


def aggregate_period_aggs(aggs: list) -> dict:
    """Sums the raw component fields across N period-aggregate dicts.

    Used to combine: multiple files' contributions into one
    marketplace-month, multiple months into a quarter/YTD, or multiple
    marketplaces into an Europe row. Never average/sum already-derived
    percentage fields -- callers must always re-run derive_metrics() on the
    result of this function.
    """
    out = {field_name: 0 for field_name in _SUMMABLE_FIELDS}
    for agg in aggs:
        for field_name in _SUMMABLE_FIELDS:
            out[field_name] += agg.get(field_name) or 0
    return out


def derive_metrics(agg: dict, mkt_cfg: dict | None = None, *,
                    mfn_estimated_dhl_cost: float | None = None,
                    mfn_shipping_gap: float | None = None) -> dict:
    """Derives display metrics (net revenue, contribution, TACoS, ...) from
    a raw period aggregate. Matches Pipeline.gs's deriveMetrics_().

    `mfn_estimated_dhl_cost` / `mfn_shipping_gap` are optional overrides so
    this same function covers both the per-marketplace case (rate x count,
    computed internally from mkt_cfg) and a rollup case (Europe, a
    quarter/YTD spanning marketplaces with different rates) where the
    caller has already summed each marketplace's own derived values.
    """
    net_revenue = agg["financial_product_sales_ex_vat"] + agg["refunds_ex_vat"]

    if mfn_estimated_dhl_cost is None:
        rate = mkt_cfg.get("mfnDhlCostPerShipmentEur") if mkt_cfg else None
        mfn_estimated_dhl_cost = -((agg.get("mfn_order_count") or 0) * rate) if rate else 0.0

    mfn_shipping_credit_ex_vat = agg.get("mfn_shipping_credit_ex_vat") or 0
    if mfn_shipping_gap is None:
        mfn_shipping_gap = mfn_shipping_credit_ex_vat + mfn_estimated_dhl_cost

    # other_fees / fba_inbound_freight / mfn_shipping_gap are SIGNED terms
    # (credits increase contribution, charges reduce it). direct_amazon_fees
    # / cogs / estimated_freight remain unconditional costs (abs-subtracted).
    contribution_before_ads = (
        net_revenue
        - abs(agg.get("direct_amazon_fees") or 0)
        - abs(agg.get("cogs") or 0)
        - abs(agg.get("estimated_freight") or 0)
        + (agg.get("other_fees") or 0)
        + (agg.get("fba_inbound_freight") or 0)
        + mfn_shipping_gap
    )

    sales = agg.get("financial_product_sales_ex_vat") or 0
    tacos = round(abs(agg.get("advertising_spend") or 0) / sales * 1000) / 10 if sales else None

    contribution_after_ads = contribution_before_ads - abs(agg.get("advertising_spend") or 0)

    estimated_freight = agg.get("estimated_freight") or 0
    freight_estimate_on_estimate_pct = (
        round((agg.get("estimated_freight_from_fallback") or 0) / estimated_freight * 1000) / 10
        if estimated_freight else None
    )

    return {
        "net_product_revenue": net_revenue,
        "mfn_estimated_dhl_cost": mfn_estimated_dhl_cost,
        "mfn_shipping_gap": mfn_shipping_gap,
        "freight_estimate_on_estimate_pct": freight_estimate_on_estimate_pct,
        "contribution_before_ads": contribution_before_ads,
        "contribution_after_ads": contribution_after_ads,
        "payment_tacos_pct": tacos,
    }
