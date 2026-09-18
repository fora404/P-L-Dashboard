import pandas as pd
import pytest

from pnl_pipeline.config import SHARED_FIXED_COST_EUR_PER_MONTH, all_marketplace_codes
from pnl_pipeline.europe import recompute_europe_aggregate

_RAW_ROW_FIELDS = [
    "financial_product_sales_ex_vat", "refunds_ex_vat", "direct_amazon_fees",
    "advertising_spend", "cogs", "estimated_freight", "estimated_freight_from_fallback",
    "other_fees", "fba_inbound_freight", "mfn_order_count", "mfn_shipping_credit_ex_vat",
    "mfn_estimated_dhl_cost", "mfn_shipping_gap",
]


def _row(marketplace, period, **overrides):
    row = {f: 0 for f in _RAW_ROW_FIELDS}
    row.update(marketplace=marketplace, period=period)
    row.update(overrides)
    return row


def test_europe_invalid_when_not_all_marketplaces_present():
    df = pd.DataFrame([
        _row("DE", "2026-08", financial_product_sales_ex_vat=200, refunds_ex_vat=-10,
             direct_amazon_fees=-20, cogs=-50),
    ])
    europe = recompute_europe_aggregate(df)
    row = europe.iloc[0]

    assert bool(row["europe_aggregate_valid"]) is False
    assert row["marketplaces_included"] == "DE"
    assert row["shared_fixed_cost"] is None
    assert row["fixed_cost_pct"] is None
    assert row["fully_loaded_contribution"] is None
    # Raw components are still summed and shown, just without fixed-cost fields.
    assert row["net_product_revenue"] == pytest.approx(190.00)


def test_europe_valid_and_applies_shared_fixed_cost_once_all_present():
    codes = all_marketplace_codes()
    rows = [
        _row(code, "2026-08", financial_product_sales_ex_vat=100, refunds_ex_vat=0,
             direct_amazon_fees=-10)
        for code in codes
    ]
    df = pd.DataFrame(rows)
    europe = recompute_europe_aggregate(df)
    row = europe.iloc[0]

    net_revenue = 100 * len(codes)
    assert bool(row["europe_aggregate_valid"]) is True
    assert row["marketplaces_included"] == ", ".join(sorted(codes))
    assert row["shared_fixed_cost"] == pytest.approx(-SHARED_FIXED_COST_EUR_PER_MONTH)
    expected_fixed_cost_pct = round(abs(SHARED_FIXED_COST_EUR_PER_MONTH) / net_revenue * 1000) / 10
    assert row["fixed_cost_pct"] == pytest.approx(expected_fixed_cost_pct)
    assert row["fully_loaded_contribution"] == pytest.approx(
        row["contribution_after_ads"] - SHARED_FIXED_COST_EUR_PER_MONTH
    )


def test_europe_aggregate_valid_is_global_not_per_period():
    codes = all_marketplace_codes()
    rows = [_row(code, "2026-07", financial_product_sales_ex_vat=100) for code in codes]
    # Period 2026-08 only has DE -- but since every code appeared SOMEWHERE
    # in the table (2026-07), the global flag stays True for every period,
    # matching the Apps Script original's global (not per-period) check.
    rows.append(_row("DE", "2026-08", financial_product_sales_ex_vat=50))
    df = pd.DataFrame(rows)

    europe = recompute_europe_aggregate(df)
    assert set(europe["europe_aggregate_valid"]) == {True}
