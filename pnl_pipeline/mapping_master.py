"""
Reads the P&L Mapping Master data (SKU_MAPPING_MASTER, BOM, COST_HISTORY)
and resolves COGS. Direct Python port of
Google script/MappingMaster.gs.txt — do not "improve" the resolution order
here without re-validating against real DE data first (63,415 rows,
0 discrepancies against the original pandas reference).

Each `*_rows` argument is a list-of-lists exactly as returned by a Google
Sheets read (row 0 = header, values as raw strings) — see drive_client.py's
read_mapping_master_tabs().
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from dateutil import parser as dateutil_parser

_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


def _header_index(header: list) -> dict:
    return {str(h).strip(): i for i, h in enumerate(header)}


def _norm(v) -> Optional[str]:
    if v is None or v == "":
        return None
    return str(v).strip()


def _norm_period_cell(v) -> Optional[str]:
    """COST_HISTORY's "Period" column is a plain string in the source
    ("2025-10", "2026-current") and the resolver depends on EXACT string
    equality against it. A spreadsheet read can hand back a cell that a
    sheet UI reformatted into a date-looking string — defend by reformatting
    anything that looks date-like back to "YYYY-MM"; leave the literal
    "2026-current" (and any other non-date text) untouched.
    """
    s = _norm(v)
    if s is None:
        return None
    if _PERIOD_RE.match(s) or s == "2026-current":
        return s
    try:
        parsed = dateutil_parser.parse(s)
        return f"{parsed.year:04d}-{parsed.month:02d}"
    except (ValueError, OverflowError):
        # Not date-like and not "YYYY-MM" — leave as-is rather than crash;
        # it simply will not match any period lookup.
        return s


def _load_sku_mapping(rows: list) -> dict:
    if not rows:
        return {}
    idx = _header_index(rows[0])
    out = {}
    for r in rows[1:]:
        seller_sku = _norm(r[idx["Seller SKU"]]) if idx["Seller SKU"] < len(r) else None
        if not seller_sku:
            continue
        marketplace = _norm(r[idx["Marketplace"]]) if idx["Marketplace"] < len(r) else None
        qty_mult_raw = r[idx["Qty / Pack Multiplier"]] if idx["Qty / Pack Multiplier"] < len(r) else None
        try:
            qty_mult = float(qty_mult_raw) if qty_mult_raw not in (None, "") else 1.0
        except (TypeError, ValueError):
            qty_mult = 1.0
        pn_idx = idx["Product Number / TIP-TOP Number"]
        product_number = _norm(r[pn_idx]) if pn_idx < len(r) else None
        out[f"{marketplace}||{seller_sku}"] = {
            "productNumber": product_number,
            "qtyMultiplier": qty_mult,
        }
    return out


def _load_bom(rows: list) -> dict:
    if not rows:
        return {}
    idx = _header_index(rows[0])
    out: dict[str, list] = {}
    for r in rows[1:]:
        pn_idx = idx["Product Number / TIP-TOP Number"]
        pn = _norm(r[pn_idx]) if pn_idx < len(r) else None
        if not pn:
            continue
        comp_idx = idx["BOM Component P/N"]
        qty_idx = idx["Qty"]
        component_pn = _norm(r[comp_idx]) if comp_idx < len(r) else None
        qty_raw = r[qty_idx] if qty_idx < len(r) else None
        try:
            qty = float(qty_raw) if qty_raw not in (None, "") else 0.0
        except (TypeError, ValueError):
            qty = 0.0
        out.setdefault(pn, []).append({"componentPn": component_pn, "qty": qty})
    return out


def _load_cost_history(rows: list) -> dict:
    if not rows:
        return {}
    idx = _header_index(rows[0])
    out: dict[str, list] = {}
    for r in rows[1:]:
        sku_idx = idx["Seller SKU"]
        sku = r[sku_idx] if sku_idx < len(r) else None
        if sku is None or sku == "":
            continue
        pn_idx = idx["Associated Product Number"]
        pn = _norm(r[pn_idx]) if pn_idx < len(r) else None
        if not pn:
            continue
        cost_idx = idx["SKU Configuration Cost"]
        cost_raw = r[cost_idx] if cost_idx < len(r) else None
        try:
            cost = float(cost_raw) if cost_raw not in (None, "") else None
        except (TypeError, ValueError):
            cost = None
        period_idx = idx["Period"]
        period = _norm_period_cell(r[period_idx]) if period_idx < len(r) else None
        status_idx = idx["Cost Status"]
        cost_status = _norm(r[status_idx]) if status_idx < len(r) else None
        out.setdefault(pn, []).append({
            "period": period,
            "cost": cost,
            "costStatus": cost_status,
        })
    return out


def _resolve_unit_cost(cost_by_pn: dict, product_number: str, period: str):
    """Returns (unit_cost, level) or (None, None).

    Resolution order (must match mapping_master.py / MappingMaster.gs
    exactly):
      1. exact month match, Cost Status == 'Actual'                -> 'A'
      2. 2026 period, Cost Status == 'Average' (2026 Average Cost)  -> 'B'
      3. carry-forward from most recent PRIOR 'Actual' month only   -> 'B'
      4. unresolved
    """
    rows = cost_by_pn.get(product_number)
    if not rows:
        return None, None

    for row in rows:
        if row["period"] == period and row["costStatus"] == "Actual" and row["cost"] is not None:
            return row["cost"], "A"

    if str(period).startswith("2026"):
        for row in rows:
            if row["costStatus"] == "Average" and row["cost"] is not None:
                return row["cost"], "B"

    best = None
    for row in rows:
        if (row["costStatus"] == "Actual" and row["cost"] is not None and row["period"]
                and row["period"] < period and row["period"] != "2026-current"):
            if best is None or row["period"] > best["period"]:
                best = row
    if best:
        return best["cost"], "B"

    return None, None


def _resolve_cogs(sku_map: dict, bom: dict, cost_by_pn: dict, mkt_label: str,
                   seller_sku: str, qty: float, period: str):
    """Returns (cogs, level) or (None, None) if unresolved.

    Caller (pipeline.py) applies the Level-C 30% fallback when this returns
    None — this function only ever returns level 'A' / 'B' / "A/B (BOM)".
    """
    sku_row = sku_map.get(f"{mkt_label}||{seller_sku}")
    if not sku_row or not sku_row["productNumber"]:
        return None, None

    pn = sku_row["productNumber"]
    eff_qty = qty * sku_row["qtyMultiplier"]

    components = bom.get(pn)
    if components:
        total = 0.0
        for comp in components:
            unit_cost, _level = _resolve_unit_cost(cost_by_pn, comp["componentPn"], period)
            if unit_cost is None:
                return None, None  # any unresolved component -> whole BOM unresolved
            total += unit_cost * comp["qty"] * eff_qty
        return total, "A/B (BOM)"

    unit_cost, level = _resolve_unit_cost(cost_by_pn, pn, period)
    if unit_cost is None:
        return None, None
    return unit_cost * eff_qty, level


@dataclass
class MappingMaster:
    sku_map: dict
    bom: dict
    cost_by_pn: dict

    def resolve_cogs(self, mkt_label: str, seller_sku: str, qty: float, period: str):
        return _resolve_cogs(self.sku_map, self.bom, self.cost_by_pn, mkt_label, seller_sku, qty, period)


def load_mapping_master(sku_rows: list, bom_rows: list, cost_rows: list) -> MappingMaster:
    return MappingMaster(
        sku_map=_load_sku_mapping(sku_rows),
        bom=_load_bom(bom_rows),
        cost_by_pn=_load_cost_history(cost_rows),
    )
