"""
Orchestrator that replaces the Apps Script's incremental refreshData().

Apps Script processes one file at a time and persists a per-file/per-period
manifest so it can resume across its 6-minute execution cap. Python has no
such cap, so on every "Update Data" click this re-reads every file for
every configured marketplace from scratch and sums directly into period
aggregates -- still doing whole-file MD5 dedup to skip byte-identical
re-uploads, and skipping unreadable/empty files with a warning rather than
aborting the whole run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

from . import config, drive_client, mapping_master, pipeline
from .europe import recompute_europe_aggregate
from .parsing import file_md5, read_csv_bytes

_MONTHLY_COLUMNS = [
    "marketplace", "period", "financial_product_sales_ex_vat", "refunds_ex_vat",
    "direct_amazon_fees", "advertising_spend", "other_fees", "fba_inbound_freight",
    "transfers_excluded", "cogs", "estimated_freight", "estimated_freight_from_fallback",
    "mfn_order_count", "mfn_shipping_credit_ex_vat", "row_count",
    "net_product_revenue", "mfn_estimated_dhl_cost", "mfn_shipping_gap",
    "freight_estimate_on_estimate_pct", "contribution_before_ads", "contribution_after_ads",
    "payment_tacos_pct",
]


@dataclass
class PipelineResult:
    monthly_marketplace: pd.DataFrame
    monthly_europe: pd.DataFrame
    data_quality: pd.DataFrame
    exceptions: pd.DataFrame
    warnings: list = field(default_factory=list)
    last_refresh_at: str = ""


def _process_marketplace(drive_service, code: str, cfg: dict, mm, warnings: list):
    """Downloads + processes every file in one marketplace's Drive folder.
    Returns (monthly_rows, dq_rows, exceptions_rows) for this marketplace."""
    try:
        files = drive_client.list_files_in_folder(drive_service, cfg["driveFolderId"])
    except Exception as e:  # noqa: BLE001 -- surface as a warning, never crash the whole refresh
        warnings.append(f"{code}: failed to list Drive folder ({e})")
        return [], [], []

    seen_md5: dict[str, str] = {}
    period_aggs: dict[str, list] = {}
    dq_by_period: dict[str, dict] = {}
    unmapped: dict[str, int] = {}

    for f in files:
        try:
            raw = drive_client.download_file_bytes(drive_service, f["id"])
        except Exception as e:  # noqa: BLE001
            warnings.append(f"{code}: failed to download {f['name']} ({e})")
            continue
        if not raw:
            warnings.append(f"{code}: {f['name']} is empty, skipped")
            continue

        md5 = file_md5(raw)
        if md5 in seen_md5:
            warnings.append(f"{code}: {f['name']} is a duplicate of {seen_md5[md5]}, skipped")
            continue
        seen_md5[md5] = f["name"]

        try:
            csv_data = read_csv_bytes(raw)
            if not csv_data["header"]:
                warnings.append(f"{code}: {f['name']} has no detectable header row, skipped")
                continue
            result = pipeline.process_file_rows(csv_data, code, cfg, mm)
        except Exception as e:  # noqa: BLE001
            warnings.append(f"{code}: failed to process {f['name']} ({e})")
            continue

        for period, agg in result.periods.items():
            period_aggs.setdefault(period, []).append(agg)
        for period, levels in result.data_quality.items():
            dest = dq_by_period.setdefault(period, {})
            for level, count in levels.items():
                dest[level] = dest.get(level, 0) + count
        for sku, count in result.unmapped_skus.items():
            unmapped[sku] = unmapped.get(sku, 0) + count

        unparsed = result.qa["rowCount"] - sum(a["row_count"] for a in result.periods.values())
        if unparsed:
            warnings.append(
                f"{code}: {f['name']} has {unparsed} row(s) with an unparseable date, "
                "excluded from every period aggregate"
            )
        if result.qa["reconMismatches"]:
            warnings.append(
                f"{code}: {f['name']} has {result.qa['reconMismatches']} "
                "row-level reconciliation mismatch(es)"
            )

    monthly_rows = []
    for period, aggs in period_aggs.items():
        summed = pipeline.aggregate_period_aggs(aggs)
        derived = pipeline.derive_metrics(summed, cfg)
        monthly_rows.append({"marketplace": code, "period": period, **summed, **derived})

    dq_rows = [
        {"marketplace": code, "period": period, "cogs_level": level, "rows": count}
        for period, levels in dq_by_period.items()
        for level, count in levels.items()
    ]
    exceptions_rows = [
        {"marketplace": code, "seller_sku": sku, "unresolved_order_rows": count}
        for sku, count in unmapped.items()
    ]
    return monthly_rows, dq_rows, exceptions_rows


def _empty_result(warnings: list[str]) -> PipelineResult:
    empty_monthly = pd.DataFrame(columns=_MONTHLY_COLUMNS)
    return PipelineResult(
        monthly_marketplace=empty_monthly,
        monthly_europe=recompute_europe_aggregate(empty_monthly),
        data_quality=pd.DataFrame(columns=["marketplace", "period", "cogs_level", "rows"]),
        exceptions=pd.DataFrame(columns=["marketplace", "seller_sku", "unresolved_order_rows"]),
        warnings=warnings,
        last_refresh_at="",
    )


def run_full_pipeline() -> PipelineResult:
    warnings: list[str] = []
    try:
        drive_service = drive_client.get_drive_service()
        gclient = drive_client.get_gspread_client()
    except Exception as e:  # noqa: BLE001 -- missing/invalid secrets, no network, etc.
        warnings.append(f"Could not authenticate to Google Drive/Sheets: {e}")
        return _empty_result(warnings)

    mm = None  # lazy-loaded on first configured marketplace that needs it
    monthly_rows: list[dict] = []
    dq_rows: list[dict] = []
    exceptions_rows: list[dict] = []

    for code in config.configured_marketplace_codes():
        cfg = config.MARKETPLACES[code]

        if mm is None:
            try:
                tabs = drive_client.read_mapping_master_tabs(gclient, config.MAPPING_MASTER_SPREADSHEET_ID)
                mm = mapping_master.load_mapping_master(tabs["sku_rows"], tabs["bom_rows"], tabs["cost_rows"])
            except Exception as e:  # noqa: BLE001
                warnings.append(f"Failed to load Mapping Master: {e}")
                break  # no marketplace can resolve COGS without it

        mkt_monthly, mkt_dq, mkt_exceptions = _process_marketplace(drive_service, code, cfg, mm, warnings)
        monthly_rows.extend(mkt_monthly)
        dq_rows.extend(mkt_dq)
        exceptions_rows.extend(mkt_exceptions)

    monthly_marketplace = (
        pd.DataFrame(monthly_rows, columns=_MONTHLY_COLUMNS).sort_values(["marketplace", "period"]).reset_index(drop=True)
        if monthly_rows else pd.DataFrame(columns=_MONTHLY_COLUMNS)
    )
    monthly_europe = recompute_europe_aggregate(monthly_marketplace)
    data_quality = pd.DataFrame(dq_rows, columns=["marketplace", "period", "cogs_level", "rows"])
    exceptions = pd.DataFrame(exceptions_rows, columns=["marketplace", "seller_sku", "unresolved_order_rows"])

    return PipelineResult(
        monthly_marketplace=monthly_marketplace,
        monthly_europe=monthly_europe,
        data_quality=data_quality,
        exceptions=exceptions,
        warnings=warnings,
        last_refresh_at=datetime.now(timezone.utc).isoformat(),
    )
