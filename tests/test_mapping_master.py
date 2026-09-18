from pnl_pipeline.mapping_master import load_mapping_master

SKU_ROWS = [
    ["Marketplace", "Seller SKU", "Product Number / TIP-TOP Number", "Qty / Pack Multiplier"],
    ["Amazon.de", "SKU-A", "P-A", "1"],
    ["Amazon.de", "SKU-BAVG", "P-B-AVG", "1"],
    ["Amazon.de", "SKU-BCF", "P-B-CF", "1"],
    ["Amazon.de", "SKU-BOM", "P-BOM", "1"],
    # SKU-C deliberately absent -- exercises the "unmapped" path.
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


def _mm():
    return load_mapping_master(SKU_ROWS, BOM_ROWS, COST_ROWS)


def test_level_a_exact_period_actual():
    cogs, level = _mm().resolve_cogs("Amazon.de", "SKU-A", 2, "2026-08")
    assert (cogs, level) == (20.0, "A")


def test_level_b_2026_average():
    cogs, level = _mm().resolve_cogs("Amazon.de", "SKU-BAVG", 1, "2026-08")
    assert (cogs, level) == (12.0, "B")


def test_level_b_carry_forward():
    cogs, level = _mm().resolve_cogs("Amazon.de", "SKU-BCF", 3, "2026-08")
    assert (cogs, level) == (24.0, "B")


def test_level_bom_sums_components():
    # COMP1: 3.00/unit * qty 2 * effQty 1 = 6.00; COMP2: 4.00/unit * qty 1 * effQty 1 = 4.00
    cogs, level = _mm().resolve_cogs("Amazon.de", "SKU-BOM", 1, "2026-08")
    assert (cogs, level) == (10.0, "A/B (BOM)")


def test_unmapped_sku_is_unresolved():
    cogs, level = _mm().resolve_cogs("Amazon.de", "SKU-C", 5, "2026-08")
    assert (cogs, level) == (None, None)


def test_bom_unresolved_if_any_component_unresolved():
    bom_rows = BOM_ROWS + [["P-BOM", "COMP-MISSING", "1"]]
    mm = load_mapping_master(SKU_ROWS, bom_rows, COST_ROWS)
    cogs, level = mm.resolve_cogs("Amazon.de", "SKU-BOM", 1, "2026-08")
    assert (cogs, level) == (None, None)
