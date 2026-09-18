import os

import pytest

from pnl_pipeline.config import MARKETPLACES
from pnl_pipeline.mapping_master import load_mapping_master
from pnl_pipeline.parsing import read_csv_bytes
from pnl_pipeline.pipeline import category_of, derive_metrics, process_file_rows

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_de_payment_report.csv")

SKU_ROWS = [
    ["Marketplace", "Seller SKU", "Product Number / TIP-TOP Number", "Qty / Pack Multiplier"],
    ["Amazon.de", "SKU-A", "P-A", "1"],
    ["Amazon.de", "SKU-BAVG", "P-B-AVG", "1"],
    ["Amazon.de", "SKU-BCF", "P-B-CF", "1"],
    ["Amazon.de", "SKU-BOM", "P-BOM", "1"],
]
BOM_ROWS = [
    ["Product Number / TIP-TOP Number", "BOM Component P/N", "Qty"],
    ["P-BOM", "COMP1", "2"],
    ["P-BOM", "COMP2", "1"],
]
COST_ROWS = [
    ["Seller SKU", "Associated Product Number", "Period", "SKU Configuration Cost", "Cost Status"],
    ["SKU-A", "P-A", "2026-08", "10.00", "Actual"],
    ["SKU-BAVG", "P-B-AVG", "2026-current", "12.00", "Average"],
    ["SKU-BCF", "P-B-CF", "2026-06", "8.00", "Actual"],
    ["COMP1", "COMP1", "2026-08", "3.00", "Actual"],
    ["COMP2", "COMP2", "2026-08", "4.00", "Actual"],
]


@pytest.fixture(scope="module")
def result():
    de_cfg = MARKETPLACES["DE"]
    mm = load_mapping_master(SKU_ROWS, BOM_ROWS, COST_ROWS)
    with open(FIXTURE_PATH, "rb") as f:
        csv_data = read_csv_bytes(f.read())
    return process_file_rows(csv_data, "DE", de_cfg, mm)


def test_category_of_priority_order():
    de_cfg = MARKETPLACES["DE"]
    assert category_of(de_cfg, "Übertrag", "") == "transfer"
    assert category_of(de_cfg, "Servicegebühr", "Werbekosten") == "advertising"
    assert category_of(de_cfg, "Versand durch Amazon Lagergebühr",
                        "Frachtkosten für den Transport zum Amazon-Versandzentrum") == "fba_inbound_freight"
    assert category_of(de_cfg, "Bestellung", "") == "order"
    assert category_of(de_cfg, "Erstattung", "") == "refund"
    assert category_of(de_cfg, "Anpassung", "") == "other_fee"


def test_file_level_qa(result):
    # 16 non-blank rows total (R1-R16); the unparseable-date row (R15) still
    # counts here even though it's excluded from every period aggregate.
    assert result.qa["rowCount"] == 16
    assert result.qa["reconMismatches"] == 1  # only R16 (deliberate mismatch)
    assert result.qa["periodsTouched"] == ["2026-08"]


def test_period_present(result):
    assert list(result.periods.keys()) == ["2026-08"]


def test_revenue_and_refunds(result):
    agg = result.periods["2026-08"]
    assert agg["financial_product_sales_ex_vat"] == pytest.approx(182.00)
    assert agg["refunds_ex_vat"] == pytest.approx(-25.00)


def test_direct_amazon_fees_unconditional_every_row(result):
    agg = result.periods["2026-08"]
    assert agg["direct_amazon_fees"] == pytest.approx(-29.00)


def test_advertising_uses_full_total_not_just_andere(result):
    agg = result.periods["2026-08"]
    assert agg["advertising_spend"] == pytest.approx(-10.00)


def test_other_fee_and_fba_inbound_freight_subtract_direct_fee(result):
    agg = result.periods["2026-08"]
    assert agg["other_fees"] == pytest.approx(-5.00)
    assert agg["fba_inbound_freight"] == pytest.approx(-12.00)


def test_transfers_excluded_but_tracked(result):
    agg = result.periods["2026-08"]
    assert agg["transfers_excluded"] == pytest.approx(100.00)


def test_cogs_across_all_resolution_levels(result):
    agg = result.periods["2026-08"]
    # R1 (A,20) + R2 (B,12) + R3 (B,24) + R4 (BOM,10) + R5 (C,15) + R12 (A,10)
    # + R13 (B,12) + R16 (A,10); R6 (NaN) contributes 0.
    assert agg["cogs"] == pytest.approx(113.00)


def test_estimated_freight_and_fallback_share(result):
    agg = result.periods["2026-08"]
    assert agg["estimated_freight"] == pytest.approx(5.65)
    # Only R5 (the level-C fallback row) contributes to the
    # "estimated-on-estimated" bucket: 15.00 * 0.05 = 0.75.
    assert agg["estimated_freight_from_fallback"] == pytest.approx(0.75)


def test_mfn_order_dedup_and_shipping_gap_clawback(result):
    agg = result.periods["2026-08"]
    # R12 and R13 share order_id MFN-1 -> counts once, not twice.
    assert agg["mfn_order_count"] == 1
    # R12 (+4.00) + R13 (0) + R14 refund clawback (-4.00) = 0.00
    assert agg["mfn_shipping_credit_ex_vat"] == pytest.approx(0.00)


def test_row_count_excludes_unparseable_date_row(result):
    agg = result.periods["2026-08"]
    # 15 rows carry a parseable date (R1-R14, R16); R15 is excluded entirely.
    assert agg["row_count"] == 15


def test_data_quality_levels(result):
    dq = result.data_quality["2026-08"]
    assert dq == {"A": 3, "B": 3, "A/B (BOM)": 1, "C": 1, "NaN": 1}


def test_unmapped_skus_exceptions(result):
    assert result.unmapped_skus == {"SKU-C": 1}


def test_derive_metrics_end_to_end(result):
    de_cfg = MARKETPLACES["DE"]
    derived = derive_metrics(result.periods["2026-08"], de_cfg)

    assert derived["net_product_revenue"] == pytest.approx(157.00)
    assert derived["mfn_estimated_dhl_cost"] == pytest.approx(-4.00)
    assert derived["mfn_shipping_gap"] == pytest.approx(-4.00)
    assert derived["contribution_before_ads"] == pytest.approx(-11.65)
    assert derived["payment_tacos_pct"] == pytest.approx(5.5)
    assert derived["contribution_after_ads"] == pytest.approx(-21.65)
    assert derived["freight_estimate_on_estimate_pct"] == pytest.approx(13.3)
