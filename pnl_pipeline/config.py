"""
Amazon P&L Dashboard — configuration.

Direct Python port of Google script/config.gs.txt. All marketplace-specific
behaviour (raw report column names in the local language, advertising
line-item label(s), currency, schema quirks) lives HERE. pipeline.py /
mapping_master.py must not branch on a hard-coded marketplace name — they
read this config.

DE is the first validated marketplace (reconciled against an independent
pandas pipeline: 63,415 rows, 0 duplicates, 0 row-level mismatches, COGS
coverage A=919 / BOM=377 / B=5432 / C=51067 / NaN=84 — all matched exactly).
The other 8 are stubs (configured=False) until each is downloaded and
inspected the same way DE was. Do not assume another marketplace's report
has the same column names, language or advertising label as DE just because
it is also an Amazon Payment Report.
"""

MAPPING_MASTER_SPREADSHEET_ID = "1M9tz5aOvXBdBicA1csPauBd-K851FTyaoW6oFVfJEnY"

SHARED_FIXED_COST_EUR_PER_MONTH = 13084

# Taiwan -> Europe upstream freight leg. TEMPORARY pending confirmation on
# whether product cost already includes this leg (if so, this becomes a
# double-count and must be removed, with affected periods rerun). Applies to
# every order row's COGS regardless of resolution level or fulfilment
# channel (FBA + MFN both, legacy-30%-fallback rows included) — deliberate,
# not a bug. Rows whose COGS came from that fallback are
# "estimated-on-estimated" and must be surfaced as a share wherever this
# figure is shown.
FREIGHT_FALLBACK_PCT_OF_COGS = 0.05
LEGACY_COGS_FALLBACK_PCT_OF_SALES = 0.30

MARKETPLACES = {
    "DE": {
        "configured": True,
        "displayName": "Germany",
        "driveFolderId": "1lNO8avOU6gYAY3Vzuc9vzWHo-CSRw4CT",
        "mappingMasterLabel": "Amazon.de",
        "currency": "EUR",
        # Raw "Versand" column value identifying a merchant-fulfilled (MFN)
        # row (vs. "Amazon" for FBA).
        "mfnFulfilmentValue": "Verkäufer",
        # MFN outbound shipping cost estimate, EUR per unique MFN
        # order/shipment. TEMPORARY proxy — Payment has no shipment-level
        # ID, so distinct order_id is the closest available proxy (can only
        # undercount true shipments, never overcount). Per-marketplace by
        # design — different marketplaces will have different carrier rates.
        "mfnDhlCostPerShipmentEur": 4.00,
        "headerSkiprows": 9,  # informational only; header row is detected dynamically
        "delimiter": ",",
        # Raw column name -> canonical field name.
        "columnMap": {
            "Datum/Uhrzeit": "datetime",
            "Abrechnungsnummer": "settlement_id",
            "Typ": "txn_type",
            "Bestellnummer": "order_id",
            "SKU": "seller_sku",
            "Beschreibung": "description",
            "Menge": "qty",
            "Marketplace": "marketplace_domain",
            "Versand": "fulfilment",
            "Ort der Bestellung": "order_city",
            "Bundesland": "order_state",
            "Postleitzahl": "order_postcode",
            "Steuererhebungsmodell": "tax_collection_model",
            "Umsätze": "sales_ex_vat",  # CONFIRMED VAT-exclusive product sales, not gross
            "Produktumsatzsteuer": "product_vat",  # reconciliation only, never P&L revenue/cost
            "Gutschrift für Versandkosten": "shipping_credit",
            "Steuer auf Versandgutschrift": "shipping_credit_tax",
            "Gutschrift für Geschenkverpackung": "giftwrap_credit",
            "Steuer auf Geschenkverpackungsgutschriften": "giftwrap_credit_tax",
            "Rabatte aus Werbeaktionen": "promo_rebate",
            "Steuer auf Aktionsrabatte": "promo_rebate_tax",
            "Einbehaltene Steuer auf Marketplace": "marketplace_withheld_tax",
            "Verkaufsgebühren": "selling_fees",
            "Gebühren zu Versand durch Amazon": "fba_fees",
            "Andere Transaktionsgebühren": "other_transaction_fees",
            "Andere": "other_amount",
            "Gesamt": "total",
            "Transaktionsstatus": "txn_status",
            "Freigabedatum der Transaktion": "release_date",
        },
        "amountFields": [
            "sales_ex_vat", "product_vat", "shipping_credit", "shipping_credit_tax",
            "giftwrap_credit", "giftwrap_credit_tax", "promo_rebate", "promo_rebate_tax",
            "marketplace_withheld_tax", "selling_fees", "fba_fees", "other_transaction_fees",
            "other_amount", "total",
        ],
        "classification": {
            "orderTypes": ["Bestellung", "Bestellung_Wiedereinzug"],
            # One chargeback-refund row can carry negative Umsätze, negative
            # VAT and a selling-fee reversal; classify it as a refund.
            "refundTypes": ["Erstattung", "Erstattung_Wiedereinzug", "Erstattung durch Rückbuchung"],
            # Amount = the row's full `total` (Gesamt) — NOT just the
            # `Andere` column. On advertising rows, Gesamt is fully composed
            # of (other_transaction_fees + other_amount) for that same
            # single row; using only `Andere` would undercount ad spend.
            "advertising": [{"txnType": "Servicegebühr", "description": "Werbekosten"}],
            # Internal account transfers — excluded from every P&L metric.
            "transfers": [{"txnType": "Übertrag"}],
            # Amazon-generated inbound transportation charges (Europe->FC
            # inbound leg, incl. the Partnered Carrier Program) — kept as
            # separate actual signed FBA costs, never netted against the 5%
            # upstream estimate (different logistics leg).
            "fbaInboundFreight": [
                {"txnType": "Versand durch Amazon Lagergebühr",
                 "description": "Frachtkosten für den Transport zum Amazon-Versandzentrum"},
                {"txnType": "Versand durch Amazon Lagergebühr",
                 "description": "Gebühr für die Teilnahme am Amazon Transportpartner-Programm"},
            ],
            # Everything else not order/refund/advertising/transfer/
            # fbaInboundFreight buckets as "other_fee".
        },
    },

    "PL": {"configured": False},
    "BE": {"configured": False},
    "UK": {"configured": False},
    "ES": {"configured": False},
    "IT": {"configured": False},
    "FR": {"configured": False},
    "IE": {"configured": False},
    "NL": {
        "configured": False,
        "note": (
            'Notion task text names "Kosten van reclame" as the NL advertising '
            "description. Not yet confirmed against real NL Payment data — verify "
            "actual Typ/Beschreibung values from an NL file first, the same way "
            "DE's Werbekosten rule was confirmed from real data, not assumed."
        ),
    },
}


def configured_marketplace_codes() -> list[str]:
    return [code for code, cfg in MARKETPLACES.items() if cfg.get("configured")]


def all_marketplace_codes() -> list[str]:
    return list(MARKETPLACES.keys())
