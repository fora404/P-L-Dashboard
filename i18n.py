"""EN/中文 string table for every UI-facing label. Keeping all copy here
means the language toggle never has to touch layout code."""

from __future__ import annotations

STRINGS = {
    "en": {
        "app_title": "FORA CARE",
        "app_subtitle": "Amazon P&L Dashboard",
        "all_europe": "All Europe",
        "update_data": "Update Data",
        "updating": "Updating...",
        "loading": "Pulling latest data from Google Drive...",
        "last_refresh": "Last data refresh: {ts}",
        "never_refreshed": "No refresh has run yet — click Update Data.",
        "no_data_yet_title": "No data yet",
        "no_data_yet_body": (
            "{marketplace}'s Drive folder and column mapping have not been "
            "configured yet. Once added to pnl_pipeline/config.py, this view "
            "will populate automatically — no dashboard changes needed."
        ),
        "period_ytd": "YTD",
        "period_q1": "Q1",
        "period_q2": "Q2",
        "period_q3": "Q3",
        "period_q4": "Q4",
        "kpi_net_revenue": "Net Revenue",
        "kpi_net_profit": "Net Profit",
        "kpi_ads_spend": "Ads Spend",
        "kpi_mfn_orders": "MFN Orders",
        "kpi_payment_tacos": "Payment TACoS",
        "kpi_net_profit_note_marketplace": "Contribution After Ads",
        "kpi_net_profit_note_europe": "Fully Loaded Contribution (all Europe)",
        "shared_fixed_costs_title": "Shared Fixed Costs",
        "shared_fixed_costs_valid": (
            "Salaries and warehouse costs are fixed and deducted once, here, "
            "not split per marketplace."
        ),
        "shared_fixed_costs_invalid": (
            "Shared Fixed Costs (€{amount}/month) only apply once every "
            "marketplace has data. Currently included: {included}."
        ),
        "marketplace_fixed_cost_note": (
            "Shared Fixed Costs are deliberately excluded here — they only apply "
            "at the All Europe level, never per marketplace."
        ),
        "chart_combo_title": "Monthly trend",
        "chart_donut_title": "Contribution Margin",
        "detail_table_title": "P&L Detail",
        "detail_view": "Detail View",
        "col_ytd": "YTD",
        "section_revenue": "REVENUE",
        "section_amazon_fees": "AMAZON FEES",
        "section_cogs_freight": "COGS & FREIGHT",
        "section_mfn_shipping": "MFN SHIPPING",
        "section_contribution": "CONTRIBUTION",
        "section_shared_fixed_costs": "SHARED FIXED COSTS",
        "row_financial_product_sales": "Financial Product Sales ex VAT",
        "row_refunds": "Refunds ex VAT",
        "row_net_product_revenue": "Net Product Revenue",
        "row_direct_amazon_fees": "Direct Amazon Fees",
        "row_advertising_spend": "Advertising Spend",
        "row_other_fees": "Other Fees",
        "row_fba_inbound_freight": "FBA Inbound Freight",
        "row_cogs": "COGS",
        "row_estimated_freight": "Estimated Upstream Freight",
        "row_mfn_order_count": "MFN Order Count",
        "row_mfn_shipping_credit": "MFN Shipping Credit ex VAT",
        "row_mfn_estimated_dhl_cost": "MFN Estimated DHL Cost",
        "row_mfn_shipping_gap": "MFN Shipping Gap",
        "row_contribution_before_ads": "Contribution Before Ads",
        "row_payment_tacos": "Payment TACoS",
        "row_contribution_after_ads": "Contribution After Ads",
        "row_shared_fixed_cost": "Shared Fixed Cost",
        "row_fixed_cost_pct": "Fixed Cost %",
        "row_fully_loaded_contribution": "Fully Loaded Contribution",
        "not_valid_europe": "N/A — not yet full Europe",
        "estimated_on_estimated": "{pct}% is \"estimated-on-estimated\" (from the 30% cost fallback)",
        "no_data": "No processed data yet. Click Update Data to run the pipeline.",
        "warnings_title": "Some source files did not process cleanly",
    },
    "zh": {
        "app_title": "FORA CARE",
        "app_subtitle": "Amazon 损益仪表盘",
        "all_europe": "全欧洲",
        "update_data": "更新数据",
        "updating": "正在更新...",
        "loading": "正在从 Google Drive 拉取最新数据...",
        "last_refresh": "上次更新数据：{ts}",
        "never_refreshed": "尚未运行过更新，请点击「更新数据」。",
        "no_data_yet_title": "暂无数据",
        "no_data_yet_body": (
            "{marketplace} 的 Drive 文件夹和字段映射尚未配置。配置完成后（编辑 "
            "pnl_pipeline/config.py），此页面会自动显示数据，无需修改仪表盘代码。"
        ),
        "period_ytd": "YTD",
        "period_q1": "Q1",
        "period_q2": "Q2",
        "period_q3": "Q3",
        "period_q4": "Q4",
        "kpi_net_revenue": "净收入",
        "kpi_net_profit": "净利润",
        "kpi_ads_spend": "广告花费",
        "kpi_mfn_orders": "MFN 订单量",
        "kpi_payment_tacos": "Payment TACoS",
        "kpi_net_profit_note_marketplace": "广告后贡献利润",
        "kpi_net_profit_note_europe": "全欧洲完全负担后贡献利润",
        "shared_fixed_costs_title": "共同固定成本",
        "shared_fixed_costs_valid": "工资和仓库费用是固定成本，只在这里统一扣除一次，不按站点单独分摊。",
        "shared_fixed_costs_invalid": (
            "共同固定成本（每月 €{amount}）只在所有站点都有数据后才会计入。当前已包含："
            "{included}。"
        ),
        "marketplace_fixed_cost_note": "此处不计入共同固定成本——它只在「全欧洲」层级统一扣除，不会分摊到单个站点。",
        "chart_combo_title": "月度趋势",
        "chart_donut_title": "贡献利润率",
        "detail_table_title": "P&L 明细",
        "detail_view": "查看明细",
        "col_ytd": "YTD",
        "section_revenue": "收入",
        "section_amazon_fees": "AMAZON 费用",
        "section_cogs_freight": "成本与运费",
        "section_mfn_shipping": "MFN 物流",
        "section_contribution": "贡献利润",
        "section_shared_fixed_costs": "共同固定成本",
        "row_financial_product_sales": "产品销售额（不含税）",
        "row_refunds": "退款（不含税）",
        "row_net_product_revenue": "净产品收入",
        "row_direct_amazon_fees": "Amazon 直接费用",
        "row_advertising_spend": "广告花费",
        "row_other_fees": "其他费用",
        "row_fba_inbound_freight": "FBA 入库运费",
        "row_cogs": "产品成本 (COGS)",
        "row_estimated_freight": "预估上游运费",
        "row_mfn_order_count": "MFN 订单数",
        "row_mfn_shipping_credit": "MFN 运费返还（不含税）",
        "row_mfn_estimated_dhl_cost": "MFN 预估 DHL 成本",
        "row_mfn_shipping_gap": "MFN 运费缺口",
        "row_contribution_before_ads": "广告前贡献利润",
        "row_payment_tacos": "Payment TACoS",
        "row_contribution_after_ads": "广告后贡献利润",
        "row_shared_fixed_cost": "共同固定成本",
        "row_fixed_cost_pct": "固定成本占比",
        "row_fully_loaded_contribution": "完全负担后贡献利润",
        "not_valid_europe": "暂不适用 — 尚未覆盖全部欧洲站点",
        "estimated_on_estimated": "其中 {pct}% 属于「估算之上的估算」（来自 30% 成本兜底）",
        "no_data": "暂无处理过的数据，请点击「更新数据」运行流水线。",
        "warnings_title": "部分源文件处理时出现问题",
    },
}

_MONTH_ABBR = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "zh": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    table = STRINGS.get(lang, STRINGS["en"])
    template = table.get(key, STRINGS["en"].get(key, key))
    return template.format(**kwargs) if kwargs else template


def month_label(period: str, lang: str = "en") -> str:
    """"2026-08" -> "Aug" (en) / "8月" (zh)."""
    try:
        month = int(period.split("-")[1])
    except (IndexError, ValueError):
        return period
    return _MONTH_ABBR.get(lang, _MONTH_ABBR["en"])[month - 1]
