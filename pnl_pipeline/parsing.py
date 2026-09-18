"""
Shared parsing helpers. Direct Python port of Google script/ParseUtil.gs.txt.
No marketplace-specific logic here — only generic mechanics (European number
format, CSV framing, period extraction from a dd.mm.yyyy-style datetime
string). Marketplace differences belong in config.py.
"""

from __future__ import annotations

import csv
import hashlib
import io


def parse_amount(raw) -> float:
    """European "1.234,56" -> 1234.56. Empty/None -> 0."""
    if raw is None or raw == "":
        return 0.0
    s = str(raw).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_period(datetime_str) -> str | None:
    """"31.07.2026 22:03:08 UTC" -> "2026-07". None if unparseable.

    Caller must treat None as an exception (excluded from period aggregates
    but still counted in a row total), never silently drop the row.
    """
    if not datetime_str:
        return None
    date_part = str(datetime_str).replace(" UTC", "").strip().split(" ")[0]
    parts = date_part.split(".")
    if len(parts) != 3:
        return None
    dd, mm, yyyy = parts
    if len(yyyy) != 4 or len(mm) != 2:
        return None
    return f"{yyyy}-{mm}"


def read_csv_bytes(raw_bytes: bytes) -> dict:
    """Reads a Drive file's CSV content, strips a BOM if present,
    auto-detects comma vs semicolon delimiter from the first 20 lines, and
    returns {"header": [...], "rows": [[...], ...]} with `header` being the
    first row that has >=10 non-empty cells (Amazon Payment CSVs start with
    several free-text preamble lines before the real header row).
    """
    text = raw_bytes.decode("utf-8-sig")

    first_lines = "\n".join(text.split("\n")[:20])
    commas = first_lines.count(",")
    semicolons = first_lines.count(";")
    delimiter = ";" if semicolons > commas else ","

    all_rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))

    header_index = -1
    for i, row in enumerate(all_rows):
        non_empty = sum(1 for c in row if str(c).strip() != "")
        if non_empty >= 10:
            header_index = i
            break

    if header_index < 0:
        return {"header": [], "rows": [], "delimiter": delimiter}

    header = [str(h).strip() for h in all_rows[header_index]]
    rows = [
        r for r in all_rows[header_index + 1:]
        if any(str(c).strip() != "" for c in r)
    ]
    return {"header": header, "rows": rows, "delimiter": delimiter}


def file_md5(raw_bytes: bytes) -> str:
    """MD5 hex digest of a Drive file's bytes — used for whole-file
    duplicate detection (e.g. a "Copy of ..." re-upload with a different
    file ID/name but identical content)."""
    return hashlib.md5(raw_bytes).hexdigest()
