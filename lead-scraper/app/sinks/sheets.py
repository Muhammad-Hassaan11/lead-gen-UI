from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import gspread

from app.config import get_settings
from app.models import Lead
from app.utils.url import normalize_maps_url


HEADER_ROW = [
    "timestamp",
    "maps_url",
    "business_name",
    "address",
    "phone",
    "website",
    "emails",
    "facebook",
    "linkedin",
    "instagram",
    "twitter",
    "ceo_name",
    "ceo_linkedin",
    "source_pages",
    "status",
]

_RETRY_DELAYS_SEC = [1, 4, 16]
_client: gspread.Client | None = None


class SheetsPushError(RuntimeError):
    """Raised when a lead could not be pushed to Google Sheets."""


def _get_client() -> gspread.Client:
    global _client
    if _client is None:
        settings = get_settings()
        creds_path = _resolve_path(settings.google_creds_path)
        _client = gspread.service_account(filename=str(creds_path))
    return _client


def _get_worksheet() -> gspread.Worksheet:
    settings = get_settings()
    if not settings.google_sheet_id:
        raise SheetsPushError("GOOGLE_SHEET_ID is not set")

    spreadsheet = _get_client().open_by_key(settings.google_sheet_id)
    try:
        worksheet = spreadsheet.worksheet(settings.google_worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=settings.google_worksheet_name,
            rows=1000,
            cols=len(HEADER_ROW),
        )

    if not worksheet.row_values(1):
        worksheet.append_row(HEADER_ROW, value_input_option="RAW")

    return worksheet


def _already_pushed(maps_url: str) -> bool:
    normalized_url = _normalize_maps_url(maps_url)
    worksheet = _get_worksheet()

    for cell_value in worksheet.col_values(2)[1:]:
        if _normalize_maps_url(cell_value) == normalized_url:
            return True

    return False


def append_lead(lead: Lead) -> None:
    try:
        if _already_pushed(lead.maps_url):
            return
        row = _row_from_lead(lead)
    except SheetsPushError:
        raise
    except Exception as exc:
        raise SheetsPushError(f"Could not prepare Google Sheets push: {exc}") from exc

    for attempt in range(len(_RETRY_DELAYS_SEC) + 1):
        try:
            _get_worksheet().append_row(row, value_input_option="RAW")
            return
        except gspread.exceptions.APIError as exc:
            status_code = _api_status_code(exc)
            if status_code == 429 and attempt < len(_RETRY_DELAYS_SEC):
                time.sleep(_RETRY_DELAYS_SEC[attempt])
                continue
            raise SheetsPushError(f"Google Sheets push failed: {exc}") from exc
        except Exception as exc:
            raise SheetsPushError(f"Google Sheets push failed: {exc}") from exc


def _row_from_lead(lead: Lead) -> list[str]:
    return [
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        _normalize_maps_url(lead.maps_url),
        _cell(lead.business_name),
        _cell(lead.address),
        _cell(lead.phone),
        _cell(lead.website),
        _list_cell(lead.emails),
        _cell(lead.facebook),
        _cell(lead.linkedin),
        _cell(lead.instagram),
        _cell(lead.twitter),
        _cell(lead.ceo_name),
        _cell(lead.ceo_linkedin),
        _list_cell(lead.source_pages),
        _cell(lead.status),
    ]


def _api_status_code(exc: gspread.exceptions.APIError) -> int | None:
    response_status = getattr(exc.response, "status_code", None)
    if response_status is not None:
        return int(response_status)
    code = getattr(exc, "code", None)
    return int(code) if code is not None else None


def _normalize_maps_url(value: str | None) -> str:
    if not value:
        return ""

    try:
        return normalize_maps_url(value)
    except ValueError:
        return value.strip()


def _cell(value: object | None) -> str:
    return "" if value is None else str(value)


def _list_cell(values: list[str]) -> str:
    return ", ".join(values)


def _resolve_path(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    return Path.cwd() / expanded
