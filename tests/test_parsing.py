import os

from pnl_pipeline.parsing import file_md5, parse_amount, parse_period, read_csv_bytes

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_de_payment_report.csv")


def test_parse_amount_european_format():
    assert parse_amount("1.234,56") == 1234.56
    assert parse_amount("-12,50") == -12.50
    assert parse_amount("0,00") == 0.0
    assert parse_amount("") == 0.0
    assert parse_amount(None) == 0.0


def test_parse_period_valid():
    assert parse_period("31.07.2026 22:03:08 UTC") == "2026-07"
    assert parse_period("01.01.2026 00:00:00 UTC") == "2026-01"


def test_parse_period_invalid_returns_none():
    assert parse_period("not-a-date") is None
    assert parse_period("") is None
    assert parse_period(None) is None


def test_read_csv_bytes_skips_preamble_and_blank_rows():
    with open(FIXTURE_PATH, "rb") as f:
        raw = f.read()
    csv_data = read_csv_bytes(raw)

    assert csv_data["header"][0] == "Datum/Uhrzeit"
    assert csv_data["header"][-1] == "Freigabedatum der Transaktion"
    assert len(csv_data["header"]) == 29
    # 16 data rows (R1-R16); the trailing blank row must be filtered out.
    assert len(csv_data["rows"]) == 16


def test_file_md5_is_stable_and_content_sensitive():
    assert file_md5(b"hello") == file_md5(b"hello")
    assert file_md5(b"hello") != file_md5(b"world")
