"""CSV serializer with Excel-friendly defaults (UTF-8 BOM, CRLF, full quoting)."""
from __future__ import annotations

import csv
import io

from app.jobs import Lead

COLUMNS = [
    "Business Name",
    "Address",
    "Phone",
    "Website",
    "Emails",
    "Facebook",
    "Source URL",
    "Status",
    "Error",
]


def leads_to_csv(leads: list[Lead]) -> bytes:
    """Return UTF-8 BOM + CRLF CSV bytes. Opens cleanly in Excel and Sheets."""
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    writer.writerow(COLUMNS)
    for l in leads:
        writer.writerow([
            l.business_name or "",
            l.address or "",
            l.phone or "",
            l.website or "",
            "; ".join(l.emails),
            l.facebook or "",
            l.source_url,
            l.status,
            l.error or "",
        ])
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")
